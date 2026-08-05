"""Bounded LLM fill — may only emit code inside a frozen InventionPlan."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional, Protocol

from linguini.forge.purpose import ForgePurpose
from linguini.invent.codegen import generate_from_plan, generate_tests_from_plan
from linguini.invent.lint import lint_source
from linguini.invent.plan import InventionPlan
from linguini.sandbox.policy import SandboxPolicy


@dataclass
class FillResult:
    source: str
    test_source: str
    backend: str
    repaired: bool = False
    refused: bool = False
    reason: str = ""
    raw: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "repaired": self.repaired,
            "refused": self.refused,
            "reason": self.reason,
        }


class CodegenBackend(Protocol):
    name: str

    def fill(
        self,
        plan: InventionPlan,
        purpose: ForgePurpose,
        *,
        previous_error: str = "",
    ) -> tuple[str, str]:
        """Return (source, test_source)."""
        ...


class TemplateBackend:
    """Deterministic stitch — default offline backend."""

    name = "template"

    def fill(
        self,
        plan: InventionPlan,
        purpose: ForgePurpose,
        *,
        previous_error: str = "",
    ) -> tuple[str, str]:
        _ = previous_error
        source = generate_from_plan(plan, tool_name=plan.name)
        tests = generate_tests_from_plan(plan, purpose)
        return source, tests


class OpenAICompatibleBackend:
    """Optional OpenAI-compatible chat API; output must be JSON {source, tests}."""

    name = "openai_compatible"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("LINGUINI_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.base_url = (base_url or os.environ.get("LINGUINI_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.environ.get("LINGUINI_LLM_MODEL") or "gpt-4o-mini"

    def fill(
        self,
        plan: InventionPlan,
        purpose: ForgePurpose,
        *,
        previous_error: str = "",
    ) -> tuple[str, str]:
        if not self.api_key:
            # Fall back silently to template if no key
            return TemplateBackend().fill(plan, purpose, previous_error=previous_error)

        plan.assert_frozen()
        system = (
            "You invent a Python native tool for Linguini. "
            "Return ONLY JSON with keys source and tests. "
            "source must define run(text='', input='', **kwargs). "
            "You MUST only import modules from allowed_imports / pip_deps. "
            "You MUST NOT add MCP tools outside mcp_tools. "
            "You MUST set novel=True on the returned dict. "
            "Do not use subprocess, socket, or filesystem writes."
        )
        user = {
            "purpose": purpose.to_dict(),
            "plan": plan.to_dict(),
            "previous_error": previous_error,
            "forbidden": ["subprocess", "socket", "ctypes", "os.system", "pip install"],
        }
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user)},
            ],
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 — explicit LLM opt-in
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            source = str(parsed.get("source") or "")
            tests = str(parsed.get("tests") or "")
            if not source:
                raise ValueError("LLM returned empty source")
            if not tests:
                tests = generate_tests_from_plan(plan, purpose)
            return source, tests
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError, json.JSONDecodeError):
            return TemplateBackend().fill(plan, purpose, previous_error=previous_error)


def get_backend(use_llm: bool = False) -> CodegenBackend:
    if use_llm or os.environ.get("LINGUINI_USE_LLM", "").lower() in {"1", "true", "yes"}:
        return OpenAICompatibleBackend()
    return TemplateBackend()


def bounded_fill(
    plan: InventionPlan,
    purpose: ForgePurpose,
    *,
    use_llm: bool = False,
    policy: SandboxPolicy | None = None,
    max_repairs: int = 1,
) -> FillResult:
    """
    Fill source within frozen plan bounds.

    Lint after codegen; on failure repair once inside same plan, then refuse.
    """
    plan.assert_frozen()
    policy = policy or SandboxPolicy()
    backend = get_backend(use_llm=use_llm)
    source, tests = backend.fill(plan, purpose)
    lint = lint_source(source, plan, policy=policy)
    if lint.ok:
        return FillResult(source=source, test_source=tests, backend=backend.name, reason="lint ok")

    if max_repairs < 1:
        return FillResult(
            source=source,
            test_source=tests,
            backend=backend.name,
            refused=True,
            reason="; ".join(lint.violations),
        )

    # Repair once: re-fill with error context, still same frozen plan
    source2, tests2 = backend.fill(plan, purpose, previous_error="; ".join(lint.violations))
    # If LLM still violates, fall back to deterministic template stitch
    lint2 = lint_source(source2, plan, policy=policy)
    if not lint2.ok:
        source2 = generate_from_plan(plan, tool_name=plan.name)
        tests2 = generate_tests_from_plan(plan, purpose)
        lint2 = lint_source(source2, plan, policy=policy)
        if not lint2.ok:
            return FillResult(
                source=source2,
                test_source=tests2,
                backend=backend.name,
                repaired=True,
                refused=True,
                reason="; ".join(lint2.violations),
            )
    return FillResult(
        source=source2,
        test_source=tests2,
        backend=backend.name,
        repaired=True,
        reason="repaired within plan bounds",
    )


def strip_fences(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:python)?\n([\s\S]*?)\n```$", text)
    return m.group(1) if m else text

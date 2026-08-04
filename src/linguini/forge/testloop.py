"""Purpose-driven unit-test loop — persist only on green."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from typing import Sequence

from linguini.forge.codegen import (
    generate_pytest_source,
    generate_tool_source,
    repair_source,
)
from linguini.forge.purpose import ForgePurpose
from linguini.sandbox.policy import SandboxPolicy
from linguini.sandbox.runner import static_scan


@dataclass
class TestLoopResult:
    ok: bool
    attempts: int = 0
    source: str = ""
    test_source: str = ""
    stdout: str = ""
    stderr: str = ""
    violations: list[str] = field(default_factory=list)
    work_dir: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "attempts": self.attempts,
            "violations": list(self.violations),
            "stdout": self.stdout[-4000:],
            "stderr": self.stderr[-4000:],
        }


def _run_pytest(work: Path, policy: SandboxPolicy) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(work / "test_native.py")],
        cwd=str(work),
        capture_output=True,
        text=True,
        timeout=policy.pytest_timeout_s,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_test_loop(
    purpose: ForgePurpose,
    *,
    tool_name: str,
    max_repairs: int = 3,
    policy: SandboxPolicy | None = None,
    initial_source: str | None = None,
    chain_steps: Sequence[str] | None = None,
) -> TestLoopResult:
    policy = policy or SandboxPolicy()
    source = initial_source or generate_tool_source(
        purpose, tool_name=tool_name, chain_steps=chain_steps
    )
    test_source = generate_pytest_source(purpose, module_filename="TOOL_MODULE.py")

    with tempfile.TemporaryDirectory(prefix="linguini_forge_") as tmp:
        work = Path(tmp)
        for attempt in range(max_repairs + 1):
            violations = static_scan(source, policy)
            if violations:
                if attempt >= max_repairs:
                    return TestLoopResult(
                        ok=False,
                        attempts=attempt + 1,
                        source=source,
                        test_source=test_source,
                        violations=violations,
                        work_dir=str(work),
                    )
                source = repair_source(
                    purpose,
                    tool_name=tool_name,
                    stderr="; ".join(violations),
                    chain_steps=chain_steps,
                )
                continue

            (work / "TOOL_MODULE.py").write_text(source, encoding="utf-8")
            (work / "test_native.py").write_text(test_source, encoding="utf-8")
            code, out, err = _run_pytest(work, policy)
            if code == 0:
                return TestLoopResult(
                    ok=True,
                    attempts=attempt + 1,
                    source=source,
                    test_source=test_source,
                    stdout=out,
                    stderr=err,
                    work_dir=str(work),
                )
            if attempt >= max_repairs:
                return TestLoopResult(
                    ok=False,
                    attempts=attempt + 1,
                    source=source,
                    test_source=test_source,
                    stdout=out,
                    stderr=err,
                    work_dir=str(work),
                )
            source = repair_source(
                purpose,
                tool_name=tool_name,
                stderr=err or out,
                chain_steps=chain_steps,
            )
        return TestLoopResult(ok=False, source=source, test_source=test_source)

"""Fail-closed sandbox policy for forged native tools."""

from __future__ import annotations

from dataclasses import dataclass, field


DEFAULT_ALLOWED_IMPORTS = frozenset(
    {
        "__future__",
        "json",
        "re",
        "math",
        "typing",
        "dataclasses",
        "collections",
        "functools",
        "itertools",
        "string",
        "hashlib",
        "linguini",
        "linguini.suite",
        "linguini.suite.nlp",
        "linguini.ir",
        "linguini.ir.batch",
        "linguini.invent",
        "linguini.invent.adapters",
        "linguini.invent.adapters.mcp_proxy",
        "linguini.invent.adapters.lib_proxy",
        "linguini.invent.adapters.node_proxy",
        "bs4",
        "yaml",
        "pydantic",
        "bleach",
        "jsonschema",
        "networkx",
        "dateutil",
        "mistune",
    }
)

BANNED_NAME_FRAGMENTS = (
    "socket",
    "subprocess",
    "requests",
    "urllib",
    "http.client",
    "os.system",
    "pathlib",
    "shutil",
    "ctypes",
    "importlib",
)


@dataclass
class SandboxPolicy:
    allow_network: bool = False
    allow_subprocess: bool = False
    allow_filesystem_write: bool = False
    allow_pip_install: bool = True
    allow_npm_install: bool = True
    # Open mode: install packages beyond curated catalogs (still name-sanitized,
    # isolated under .linguini/forge_venv|forge_node, verify-always before persist).
    allow_open_pip: bool = False
    allow_open_npm: bool = False
    allowed_imports: frozenset[str] = DEFAULT_ALLOWED_IMPORTS
    allow_mcp_servers: list[str] = field(default_factory=list)
    pytest_timeout_s: float = 30.0

    def import_allowed(self, module: str) -> bool:
        root = module.split(".")[0]
        if root in self.allowed_imports or module in self.allowed_imports:
            return True
        if module.startswith("linguini."):
            return True
        return False

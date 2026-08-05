"""Call allowlisted / forge_node npm modules from invented natives (cross-runtime)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def forge_node_dir(root: Path | str | None = None) -> Path:
    if root is None:
        root = os.environ.get("LINGUINI_ROOT", ".")
    return Path(root) / ".linguini" / "forge_node"


def call_node(
    module: str,
    *,
    code: str,
    root: Path | str | None = None,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """
    Run a small Node snippet with NODE_PATH pointing at forge_node/node_modules.

    `code` must assign to globalThis.__linguini_out (JSON-serializable).
    """
    node = shutil.which("node")
    if not node:
        return {"ok": False, "error": "node not found on PATH", "module": module}

    ndir = forge_node_dir(root)
    modules = ndir / "node_modules"
    env = os.environ.copy()
    env["NODE_PATH"] = str(modules)

    wrapper = f"""
const path = require('path');
try {{
  require.resolve({module!r});
}} catch (e) {{
  console.log(JSON.stringify({{ok:false, error: String(e), module: {module!r}}}));
  process.exit(0);
}}
{code}
if (typeof globalThis.__linguini_out === 'undefined') {{
  globalThis.__linguini_out = {{ok:false, error:'__linguini_out not set'}};
}}
console.log(JSON.stringify(globalThis.__linguini_out));
"""
    proc = subprocess.run(
        [node, "-e", wrapper],
        cwd=str(ndir),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
        env=env,
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "error": proc.stderr[-1500:] or proc.stdout[-1500:] or "node failed",
            "module": module,
        }
    line = (proc.stdout or "").strip().splitlines()
    if not line:
        return {"ok": False, "error": "empty node output", "module": module}
    try:
        return json.loads(line[-1])
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid json from node", "raw": line[-1][:500]}


def markdown_to_text(md: str, *, root: Path | str | None = None) -> dict[str, Any]:
    """Use npm `marked` in forge_node to convert markdown → HTML text extract."""
    code = f"""
const {{ marked }} = require('marked');
const html = marked.parse({md!r});
const text = String(html).replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim();
globalThis.__linguini_out = {{ok:true, html, text, engine:'marked'}};
"""
    return call_node("marked", code=code, root=root)


def cheerio_to_text(html: str, *, root: Path | str | None = None) -> dict[str, Any]:
    """Use npm `cheerio` to extract text from HTML."""
    code = f"""
const cheerio = require('cheerio');
const $ = cheerio.load({html!r});
const text = $('body').text().replace(/\\s+/g, ' ').trim() || $.root().text().replace(/\\s+/g, ' ').trim();
const links = $('a').map((i, el) => $(el).attr('href')).get().filter(Boolean).slice(0, 20);
globalThis.__linguini_out = {{ok:true, text, links, engine:'cheerio'}};
"""
    return call_node("cheerio", code=code, root=root)


def html_to_markdown(html: str, *, root: Path | str | None = None) -> dict[str, Any]:
    """Use npm `turndown` to convert HTML → markdown."""
    code = f"""
const TurndownService = require('turndown');
const td = new TurndownService();
const markdown = td.turndown({html!r});
const text = String(markdown).replace(/[#*_`\\[\\]]+/g, ' ').replace(/\\s+/g, ' ').trim();
globalThis.__linguini_out = {{ok:true, markdown, text, engine:'turndown'}};
"""
    return call_node("turndown", code=code, root=root)

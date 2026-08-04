"""Run all example scripts in order."""

from __future__ import annotations

import runpy
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE / "_workspace"
SCRIPTS = [
    "01_create_novel_tool.py",
    "02_use_novel_tool.py",
    "03_wrap_chain_as_native.py",
    "04_leanback_vs_forge.py",
    "05_create_and_reuse_pipeline.py",
]


def _reset_workspace() -> None:
    ling_dir = WORKSPACE / ".linguini"
    if ling_dir.exists():
        # ignore_errors: OneDrive/Windows can lock dirs briefly
        shutil.rmtree(ling_dir, ignore_errors=True)
        native = ling_dir / "native_tools"
        if native.exists():
            for p in native.glob("*"):
                try:
                    p.unlink()
                except OSError:
                    pass
    WORKSPACE.mkdir(parents=True, exist_ok=True)


def main() -> int:
    sys.path.insert(0, str(HERE))
    _reset_workspace()
    failed = []
    for name in SCRIPTS:
        print("\n" + "#" * 60)
        print(f"# {name}")
        print("#" * 60)
        path = HERE / name
        try:
            runpy.run_path(str(path), run_name="__main__")
        except SystemExit as exc:
            code = int(exc.code or 0) if isinstance(exc.code, int) or exc.code is None else 1
            if code != 0:
                failed.append(name)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR in {name}: {exc}")
            failed.append(name)
    if failed:
        print(f"\nFAILED: {failed}")
        return 1
    print("\nAll examples OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

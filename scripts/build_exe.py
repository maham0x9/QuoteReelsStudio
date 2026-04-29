"""Build a Windows ``QuoteReelsStudio.exe`` with PyInstaller.

Run from the project root:

    python scripts/build_exe.py

The resulting binary lands in ``dist/QuoteReelsStudio/``.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    spec = root / "QuoteReelsStudio.spec"
    if not spec.exists():
        print(f"Missing PyInstaller spec at {spec}", file=sys.stderr)
        return 1
    if shutil.which("pyinstaller") is None:
        print("pyinstaller is not installed. Run: pip install pyinstaller", file=sys.stderr)
        return 1
    cmd = ["pyinstaller", "--noconfirm", "--clean", str(spec)]
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(root))


if __name__ == "__main__":
    raise SystemExit(main())

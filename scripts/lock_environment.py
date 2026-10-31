"""Record this tested Windows/Python 3.12 environment, not a universal lock."""

import subprocess
import sys
from pathlib import Path

lines = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True).splitlines()
lines = [s for s in lines if s and not s.startswith(("#", "-e "))]
lines = [s + '; sys_platform == "win32"' if s.lower().startswith("pywin32==") else s for s in lines]
text = (
    "# Tested Windows / CPython 3.12 environment, 2026-10-31.\n# Install this file, then pip install --no-deps .\n"
    + "\n".join(lines)
    + "\n"
)
Path("requirements-windows-py312.lock.txt").write_text(text, encoding="utf-8")
print(f"Recorded {len(lines)} exact dependency versions")

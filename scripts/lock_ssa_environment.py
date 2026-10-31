"""Record extension dependencies separately, preserving the beta lock snapshot."""

import subprocess
import sys
from pathlib import Path

target = Path("requirements-ssa-windows-py312.lock.txt")
if target.exists():
    raise SystemExit(
        "SSA snapshot already exists; choose a new versioned filename for a new environment"
    )
lines = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True).splitlines()
lines = [s for s in lines if s and not s.startswith(("#", "-e "))]
lines = [s + '; sys_platform == "win32"' if s.lower().startswith("pywin32==") else s for s in lines]
target.write_text(
    "# SSA/publication extension tested on Windows / CPython 3.12, 2026-10-31.\n# Platform-specific development snapshot; resolve pyproject.toml on other platforms.\n"
    + "\n".join(lines)
    + "\n",
    encoding="utf-8",
)
print(f"Recorded {len(lines)} extension environment pins without changing the beta snapshot")

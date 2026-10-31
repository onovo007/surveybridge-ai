"""Synchronize repository discovery copies from the canonical skill."""

import argparse
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
source = (root / "skills/surveybridge/SKILL.md").read_bytes()
for name in (".agents", ".claude"):
    destination = root / name / "skills/surveybridge/SKILL.md"
    if args.check:
        if not destination.exists() or destination.read_bytes() != source:
            raise SystemExit(f"Skill copy differs: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source)
print("Skill copies match canonical source")

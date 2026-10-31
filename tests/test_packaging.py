import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_skill_copies_and_manifest_paths():
    canonical = (ROOT / "skills/surveybridge/SKILL.md").read_bytes()
    assert canonical.startswith(b"---\nname: surveybridge\n")
    for base in [".agents", ".claude"]:
        assert (ROOT / base / "skills/surveybridge/SKILL.md").read_bytes() == canonical
    manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
    for field in ["skills", "mcpServers"]:
        value = manifest[field]
        assert value.startswith("./") and ".." not in value
        assert (ROOT / value).exists()
    assert json.loads((ROOT / ".mcp.json").read_text()) == json.loads(
        (ROOT / "mcp.json").read_text()
    )

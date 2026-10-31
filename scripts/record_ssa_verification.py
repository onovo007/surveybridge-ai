"""Publish sanitized test evidence, not host account/configuration or raw model events."""

import json
from pathlib import Path

out = Path("examples/verification/ssa")
out.mkdir(parents=True, exist_ok=True)
text = Path(".tmp/codex-host-result.txt").read_text(encoding="utf-8")
(out / "codex_host_result.md").write_text(text, encoding="utf-8")
calls = []
for line in Path(".tmp/codex-host-events.jsonl").read_text(encoding="utf-8").splitlines():
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    item = event.get("item", {})
    if item.get("type") == "mcp_tool_call" and event.get("type") == "item.completed":
        calls.append({k: item.get(k) for k in ("server", "tool", "status")})
assert {c["tool"] for c in calls} == {
    "surveybridge_healthcheck",
    "surveybridge_list_countries",
    "surveybridge_get_report_metadata",
} and all(c["status"] == "completed" for c in calls), calls
report = {
    "codex": {
        "status": "passed",
        "mode": "ephemeral read-only natural-language host session",
        "calls": calls,
        "approval_scope": "invocation-only allowlist of three public read tools; no persistent settings changed",
    },
    "claude": {
        "status": "blocked",
        "evidence": "claude auth status: loggedIn=false, authMethod=none",
        "claim": "No natural-language success claimed",
    },
    "github_ci": {
        "status": "blocked",
        "evidence": "Publishing OAuth token lacks workflow scope; ci/validation.yml remains inactive template",
    },
}
(out / "host_verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))

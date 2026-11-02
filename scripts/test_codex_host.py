"""Ephemeral Codex host test, using argument arrays and no settings changes."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
prompt = (
    "This is a read-only SurveyBridge host integration test. Use only the configured surveybridge MCP server to check its version, "
    "discover Sub-Saharan Africa country coverage, and verify the official Nigeria report at https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf "
    "including optional PDF metadata verification. Report the source-backed title, catalog/cover dates, fieldwork dates and whether API observations "
    "are established. Explain disagreements and scientific limitations. Do not extract estimates, run shell commands, edit files, publish, "
    "or invoke other servers. Use surveybridge_healthcheck, surveybridge_list_countries with region ssa, and surveybridge_get_report_metadata. "
    "Return a concise result with official source URLs."
)
command = [
    shutil.which("codex") or "codex",
    "exec",
    "--ephemeral",
    "--sandbox",
    "read-only",
    "--json",
]
approved_tools = [
    "surveybridge_healthcheck",
    "surveybridge_list_countries",
    "surveybridge_get_report_metadata",
]
command.extend(["-c", "mcp_servers.surveybridge.enabled_tools=" + json.dumps(approved_tools)])
for tool in approved_tools:
    command.extend(["-c", f'mcp_servers.surveybridge.tools.{tool}.approval_mode="approve"'])
for key, value in {
    "command": Path(sys.executable).as_posix(),
    "args": ["-m", "surveybridge.mcp_server"],
}.items():
    command.extend(["-c", f"mcp_servers.surveybridge.{key}={json.dumps(value)}"])
env_config = (
    "mcp_servers.surveybridge.env={SURVEYBRIDGE_WORKSPACE="
    + json.dumps((root / ".surveybridge").as_posix())
    + ",SURVEYBRIDGE_OUTPUT_ROOT="
    + json.dumps((root / ".tmp/host-output").as_posix())
    + "}"
)
command.extend(["-c", env_config, "-o", str(root / ".tmp/codex-host-result.txt"), prompt])
with (
    (root / ".tmp/codex-host-events.jsonl").open("w", encoding="utf-8") as stdout,
    (root / ".tmp/codex-host-stderr.txt").open("w", encoding="utf-8") as stderr,
):
    try:
        result = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr, timeout=240)
        print("Codex host exit code:", result.returncode)
    except subprocess.TimeoutExpired:
        print("Codex host test timed out; inspect local logs; no success claimed")
        raise SystemExit(1) from None

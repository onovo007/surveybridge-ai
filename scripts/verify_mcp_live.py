"""Exercise all seven tools over actual stdio against the public DHS API."""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "SURVEYBRIDGE_WORKSPACE": str(root / ".surveybridge"),
        "SURVEYBRIDGE_OUTPUT_ROOT": str(root / "examples/verification/mcp-outputs"),
    }
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "surveybridge.mcp_server"], env=env
    )
    report = []
    async with (
        stdio_client(params) as streams,
        ClientSession(*streams, read_timeout_seconds=120) as session,
    ):
        initialized = await session.initialize()
        tools = await session.list_tools()
        assert len(tools.tools) == 7

        async def call(name, arguments):
            result = await session.call_tool(name, arguments)
            data = result.structured_content
            assert data is not None and data["status"] == "ok", result
            report.append(
                {
                    "tool": name,
                    "status": data["status"],
                    "source_pages": len(data["source"]),
                    "warning_count": len(data["warnings"]),
                    "truncated": data["truncated"],
                }
            )
            return data["data"]

        await call("surveybridge_healthcheck", {})
        await call("surveybridge_list_countries", {"query": "Nigeria"})
        await call("surveybridge_list_surveys", {"country_ids": ["NG", "KE", "UG", "TZ"]})
        candidates = await call("surveybridge_search_indicators", {"query": "DPT 3"})
        assert any(i["id"] == "CH_VACC_C_DP3" for i in candidates)
        extract = await call(
            "surveybridge_get_indicator_series",
            {"indicator_id": "CH_VACC_C_DP3", "country_ids": ["NG", "KE", "UG", "TZ"]},
        )
        assert extract["observation_count"] == 26
        await call("surveybridge_assess_comparability", {"project_id": extract["project_id"]})
        await call(
            "surveybridge_export_project",
            {"project_id": extract["project_id"], "output_dir": "dpt3-" + uuid.uuid4().hex[:8]},
        )
    result = {
        "sdk_version": "2.3.0",
        "server_name": initialized.server_info.name,
        "mode": "public API with response cache",
        "tools": report,
    }
    out = root / "examples/verification/mcp_live.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def test_stdio_handshake_tools_and_validation(service, project):
    # Prime exact queries with mock-transport fixtures; the child must remain offline.
    service.list_countries()
    service.search_indicators("DPT 3")
    service.list_surveys(["NG", "KE", "UG", "TZ"])

    async def run():
        env = {
            **os.environ,
            "SURVEYBRIDGE_WORKSPACE": str(service.settings.workspace),
            "SURVEYBRIDGE_OUTPUT_ROOT": str(service.settings.output_root),
            "SURVEYBRIDGE_OFFLINE": "1",
        }
        params = StdioServerParameters(
            command=os.getenv("SURVEYBRIDGE_TEST_PYTHON", sys.executable),
            args=["-m", "surveybridge.mcp_server"],
            env=env,
        )
        async with (
            stdio_client(params) as streams,
            ClientSession(*streams, read_timeout_seconds=10) as session,
        ):
            initialized = await session.initialize()
            assert initialized.server_info.name == "SurveyBridge AI"
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            assert names.issuperset(
                {
                    "surveybridge_healthcheck",
                    "surveybridge_list_countries",
                    "surveybridge_list_surveys",
                    "surveybridge_search_indicators",
                    "surveybridge_get_indicator_series",
                    "surveybridge_assess_comparability",
                    "surveybridge_export_project",
                }
            )
            result = await session.call_tool("surveybridge_healthcheck", {})
            assert result.structured_content is not None, result
            assert result.structured_content["status"] == "ok"
            assert result.structured_content["data"]["version"] == "0.1.0"
            invalid = await session.call_tool(
                "surveybridge_assess_comparability", {"project_id": "../../escape"}
            )
            assert invalid.structured_content["status"] == "error"
            calls = [
                ("surveybridge_list_countries", {}),
                ("surveybridge_search_indicators", {"query": "DPT 3"}),
                ("surveybridge_list_surveys", {"country_ids": ["NG", "KE", "UG", "TZ"]}),
                (
                    "surveybridge_get_indicator_series",
                    {"indicator_id": "CH_VACC_C_DP3", "country_ids": ["NG", "KE", "UG", "TZ"]},
                ),
                ("surveybridge_assess_comparability", {"project_id": project["project_id"]}),
                (
                    "surveybridge_export_project",
                    {"project_id": project["project_id"], "output_dir": "mcp-export"},
                ),
            ]
            for name, arguments in calls:
                result = await session.call_tool(name, arguments)
                assert result.structured_content["status"] == "ok", (name, result)
            assert (service.settings.output_root / "mcp-export" / "provenance.json").is_file()

    asyncio.run(asyncio.wait_for(run(), timeout=30))

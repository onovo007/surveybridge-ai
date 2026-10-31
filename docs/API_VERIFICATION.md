# Official API and integration verification

Verification date: **31 October 2026 (America/New_York)**. Source responses have their actual UTC timestamps in the demonstration provenance manifest. Requests used no credentials and no restricted endpoints.

## DHS documentation

Official entry: <https://api.dhsprogram.com/>. Its current site loads documentation fragments from `html/`; the `#/` links alone return the navigation shell to a static reader. Retrieved API response evidence is archived in `docs/evidence/`. Downloaded documentation fragments are retained locally for verification and excluded from distribution; follow the official links for the full current documents.

- [Basics](https://api.dhsprogram.com/html/introapi.cfm)
- [Countries](https://api.dhsprogram.com/html/api-countries.cfm)
- [Surveys](https://api.dhsprogram.com/html/api-surveys.cfm)
- [Indicators](https://api.dhsprogram.com/html/api-indicators.cfm)
- [Data](https://api.dhsprogram.com/html/api-data.cfm)
- [Advanced queries and pagination](https://api.dhsprogram.com/html/api-advancedqueries.cfm)
- [Terms](https://api.dhsprogram.com/html/terms.cfm)
- [Source data field descriptions](https://api.dhsprogram.com/rest/dhs/data/fields?f=json)

The verified aggregate root is `https://api.dhsprogram.com/rest/dhs`. Supported endpoints in v0.1 are `countries`, `surveys`, `indicators`, `data`. Catalog calls responded HTTP 200 anonymously. A bare `data?f=json&perpage=1` returned HTTP 400; the docs require at least one of `countryIds`, `indicatorIds`, `surveyIds`. Filtered data calls succeeded.

Implemented query keys: `countryIds`, `indicatorIds`, `surveyYearStart`, `surveyYearEnd`, `breakdown`; survey catalog also uses `surveyStatus=completed`. Bounds are inclusive. IDs are comma-separated; breakdown is `national` (default), `subnational`, `background`, or `all`. Search is local, over the complete paginated indicator catalog. The connector does not claim undocumented full-text API search.

Response structure actually observed:

```json
{"TotalPages":1,"Data":[{"DataId":797722,"IndicatorId":"CH_VACC_C_DP3","SurveyId":"KE2022DHS","SurveyYear":2022,"Value":89.2,"CILow":"","CIHigh":""}],"RecordsReturned":26,"Page":"1","RecordCount":26}
```

The displayed data row is an excerpt, not the entire 26-row response. Complete source records are archived; optional/empty values are preserved in raw form. `Page` can be a numeric string, `SurveyYear` differs in type between endpoints, and CIs can be empty strings. `MeasurementType`, `Definition` and `Denominator` come from indicator metadata, not invented observation fields. All original record fields survive under `raw`.

Pagination uses `page` and `perpage`. Documentation states default 100, anonymous maximum 1,000 (indicators exception 3,000), authenticated maximum 5,000. An exploratory catalog call at 5,000 returned 4,655 records; this permissiveness conflicts with the documented anonymous limit and is **not used by the connector**. Implemented calls request 1,000 and traverse actual pages. Real full indicator search traversed five pages. Metadata samples and the complete exploratory catalog remain available for audit.

There are several DPT3 candidates: `CH_VACS_C_DP3` (vaccination by source of information), `CH_VACC_C_DP3` (vaccinations), `CH_VAC1_C_DP3` (within first year). The demonstration selects `CH_VACC_C_DP3`; `CH_VACC_C_BCG` and `CH_VACC_C_MSL` were also confirmed by catalog search before retrieval. Each returned 26 national observations for NG, KE, UG, TZ; total 78. The source catalog denominator permits ages 12–23 or 24–35 months, so survey-specific population equivalence remains unverified.

The source's field guide says CI fields are supplied only for maternal mortality ratio and HIV prevalence indicators. All demonstration CIs were blank and remain null; no CI construction is attempted. The completed survey catalog returned 53 rounds across multiple survey types. It is broader than indicator coverage; absent records are documented rather than filled with zero. Latest DPT3 observations are KE2022DHS, NG2024DHS, TZ2022DHS and UG2016DHS in this extract; do not infer that a later round is available in this API.

Access terms require attribution. `info/citation?f=json` was retrieved for verification only; it is not an arbitrary endpoint exposed through tools. The software includes the official citation and independence statement in every bundle. Optional partner keys are not required for public data and are not supported by v0.1.

## Official Python MCP SDK

Reviewed [official SDK](https://github.com/modelcontextprotocol/python-sdk), [current v2 docs](https://py.sdk.modelcontextprotocol.io/), [migration guide](https://py.sdk.modelcontextprotocol.io/migration/), and [structured outputs](https://py.sdk.modelcontextprotocol.io/servers/structured-output/). Installed official `mcp==2.3.0`, which uses `from mcp.server import MCPServer`; FastMCP is the v1 name. Pydantic result models publish output schemas and populate structured results. Local stdio is used; diagnostics go to stderr. Telemetry is disabled with `OTEL_SDK_DISABLED=true` before SDK import. The real SDK subprocess tests verify protocol behavior; no inference from decorator presence alone.

## Agent host conventions

Reviewed [OpenAI skills](https://learn.chatgpt.com/docs/build-skills), [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), and [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference).

Canonical skill has required YAML `name` and `description`. Repository copies use `.agents/skills/surveybridge/` (Codex) and `.claude/skills/surveybridge/` (Claude); plugin packaging uses root `skills/`. Claude uses `.claude-plugin/plugin.json` and root `.mcp.json`. The portable OpenAI package has root `plugin.json`, `mcp.json`, and `skills/`; `.codex-plugin/plugin.json` is included as a compatibility fallback with relative paths. The portable manifest schema is archived and validated. Install the Python executable first; plugin metadata does not bundle a Python interpreter or dependencies.

Host validation and actual test results are in BUILD_REPORT.md. Natural-language behavior inside a logged-in Codex/Claude model session has not been inferred from a successful SDK handshake.

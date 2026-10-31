# Implementation decisions — 31 October 2026

The supplied ARCHITECTURE.md and PRD.md are technical references; CODEX_MASTER_PROMPT.md is an execution guide. Their instructions were applied within the user's requested project scope. The three original documents are unchanged.

| Requirement or ambiguity | Implemented decision |
|---|---|
| Missing ACCEPTANCE_TESTS.md, DATA_ACCESS_POLICY.md and skill cited by execution guide | Created from supplied requirements; no pre-existing policy was assumed |
| FastMCP architecture versus current official SDK | Official SDK 2.3.0 `MCPServer`, the documented v2 successor to FastMCP; no third-party FastMCP dependency |
| Project IDs used by tools without a project-creation tool | Series retrieval creates and returns a persistent immutable project snapshot; optional project_id appends an indicator into a new snapshot |
| Multiple indicators in a research project | Preserve separate indicator series; block equivalent-series pooling across indicators; allow indicator-specific assessment and transparent exports |
| API query search support unspecified | Search locally over paginated indicator catalog; do not invent server-side text-search filters |
| Exact source pagination | Use `Page`, `TotalPages`, `RecordCount`, `RecordsReturned`, `Data`; cap requests to 1,000 rows/page and 100 pages by default; fail incomplete/inconsistent extracts |
| Documentation says indicators max 3,000 anonymously, while exploratory live call returned 4,655 at perpage=5,000 | Do not rely on undocumented permissiveness; implemented connector uses conservative 1,000-row pages |
| Country metadata IDs | Validate against official DHS catalog; do not assume ISO equivalence |
| Survey availability versus indicator availability | Catalog lists completed surveys, including other types and rounds with no indicator data; export explicit availability by survey/indicator and requested breakdown |
| Block comparison but still allow export | Export preserves evidence and findings for review; automatic equivalent-series interpretation remains blocked; no pooled or causal results generated |
| Output formats | Core JSON, dictionaries, raw archives and scientific warnings always exported; selected rich formats add observation CSV, workbook and/or notebook |
| API base configurable versus domain allowlist | Settings accepts the verified official HTTPS aggregate root only; mock transports support testing; no caller-selected origins or redirects |
| Excel export dependencies | Follow supplied Python/openpyxl architecture; no commercial or host-specific spreadsheet runtime required by the installed package |
| Credentials and telemetry | No API keys, restricted endpoints or analytics; SDK telemetry explicitly disabled |
| License unspecified | MIT for original project code, with explicit exclusion of third-party source data/documentation from relicensing |
| Persistent storage | Operator-configured local workspace and output root; no database service; users select absolute paths in host registrations |
| Version lock | Package has compatible dependency bounds; a complete Windows/Python 3.12 tested-environment snapshot is supplied separately; CI resolves compatible versions per platform |
| Scientific validity | Shared definitions permit descriptive review only; alternative age groups, missing CI, asynchronous rounds and survey-specific equivalence stay visible |
| 14-day target and external success metrics | No elapsed-sprint or beta-tester claims; local implementation and actual verification reported independently of future release gates |

No proprietary Quantium code was imported. The package performs deterministic transformations and uses public aggregated observations only. GitHub/PyPI publication and external beta validation are recorded separately from local package functionality.

# SurveyBridge AI v0.1

**Quantium Insights LLC · public DHS aggregate research for Python, Codex and Claude Code**

Discover official country, survey and indicator metadata; retrieve public aggregated DHS estimates; flag comparison risks; export auditable CSV, JSON, Excel and executable notebooks. The local MCP server exposes seven research tools through the current official Python MCP SDK. No AI API key is required by this package.

Status: **tested beta**, distributed through [GitHub](https://github.com/onovo007/surveybridge-ai). See [the build report](docs/BUILD_REPORT.md) for executed checks and remaining release gates. A 14-day sprint is a development target; external beta testing and cross-platform validation are not assumed complete.

Public source installation:

```sh
python -m pip install "git+https://github.com/onovo007/surveybridge-ai.git@v0.1.0-beta.1"
```

Git is required for this command. Prebuilt wheels are available from the [beta release](https://github.com/onovo007/surveybridge-ai/releases/tag/v0.1.0-beta.1).

## Install from this checkout

Python 3.11+ required. Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\surveybridge.exe healthcheck
```

macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/surveybridge healthcheck
```

For a built wheel, use `python -m pip install /path/to/surveybridge_ai-0.1.0-py3-none-any.whl`. This does not require PyPI publication of SurveyBridge; dependencies require internet or a prepared wheelhouse. See [installation and MCP registration](docs/INSTALLATION.md), including absolute executable paths and skills.

## Research workflow

```sh
surveybridge countries --query Nigeria
surveybridge surveys NG,KE,UG,TZ
surveybridge indicators "DPT 3"
surveybridge series CH_VACC_C_DP3 NG,KE,UG,TZ
surveybridge assess PROJECT_ID_FROM_SERIES
surveybridge export PROJECT_ID_FROM_SERIES my-study
```

`series` returns a persistent project ID. An optional `--project-id` adds another indicator to a new immutable snapshot with matching country/year/breakdown scope. `--from-year`, `--to-year`, and `--breakdown national|subnational|background|all` are supported. Search is token-based over the full cached official catalog; aliases such as “DTP3” may need the catalog wording “DPT 3”.

Exports are restricted to a new directory under `SURVEYBRIDGE_OUTPUT_ROOT` (default `./outputs`). Existing outputs are never silently overwritten. Set `SURVEYBRIDGE_WORKSPACE` to an absolute path for persistent cache/projects when launching from an agent host. `SURVEYBRIDGE_OFFLINE=1` uses exact cached queries, retaining original retrieval dates.

## MCP tools

| Tool | Purpose |
|---|---|
| `surveybridge_healthcheck` | Local version/configuration; does not claim remote availability |
| `surveybridge_list_countries` | Official DHS IDs and country metadata |
| `surveybridge_list_surveys` | Completed rounds, survey types and fieldwork dates |
| `surveybridge_search_indicators` | Exact IDs, definitions, units and denominators |
| `surveybridge_get_indicator_series` | Source-traceable observations and persistent project ID |
| `surveybridge_assess_comparability` | Metadata-based block/caution checks |
| `surveybridge_export_project` | Documented local CSV/JSON/XLSX/notebook bundle |

Every successful application response follows `{status,data,warnings,source,truncated,pagination}`. SDK input-schema errors follow MCP's protocol error contract. The series response contains at most 500 rows; the project and export contain all retrieved rows. Queries exceeding the bounded page budget fail instead of silently saving partial data.

## Scientific interpretation

The package preserves nulls, zeros, survey labels, fieldwork periods, indicator definitions, units, disaggregation, source denominators, original rows and response bytes. It does not fabricate confidence intervals, interpolate annual observations, estimate from microdata or infer causality. A common catalog ID does not establish survey-specific equivalence. Blocks prevent automated equivalent-series interpretation; blocked extracts remain exportable for source review, with warnings.

The [four-country demonstration](examples/four_country_immunization.md) contains **78 retrieved observations**, three separate indicators and complete outputs. It reproduces normalization offline from original responses and verifies every archived record. Latest survey rounds differ by country; they do not support a contemporaneous ranking. Publication requires review of original survey reports, particularly the possible 12–23 versus 24–35 month denominator.

## Develop and verify

```sh
python -m pytest -q
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python scripts/sync_skills.py --check
python -m build
```

Tests run without DHS connectivity. HTTP mocks test failures and paging; actual archived DHS responses support regression tests; an SDK client starts the real stdio server and exercises all seven tools offline. The supplied [CI template](ci/README.md) targets Windows/macOS/Linux and Python 3.11–3.13. GitHub rejected workflow publication because the OAuth token lacks workflow permission; activation and remote validation remain outstanding.

See [API verification](docs/API_VERIFICATION.md), [engineering decisions](docs/DECISIONS.md), [data-access policy](DATA_ACCESS_POLICY.md), [acceptance tests](ACCEPTANCE_TESTS.md), [release notes](docs/RELEASE_NOTES.md), and [v0.2 roadmap](docs/ROADMAP.md).

## Attribution and license

The DHS Program Indicator Data API, The Demographic and Health Surveys (DHS) Program. ICF. Originally funded by the United States Agency for International Development (USAID). Available from [api.dhsprogram.com](https://api.dhsprogram.com/). Access dates are recorded in each bundle's provenance manifest.

SurveyBridge AI is independent of The DHS Program. Original SurveyBridge code is MIT licensed. Source data and official documentation retain their own terms; see [LICENSE](LICENSE). Restricted individual-level DHS datasets are outside v0.1.

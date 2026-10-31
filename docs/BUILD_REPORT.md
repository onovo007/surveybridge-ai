# SurveyBridge AI v0.1 build report

Date: **31 October 2026 (America/New_York)**. Status: **tested beta**. The package, CLI, seven-tool MCP server, skills, research exports and real four-country demonstration are implemented. GitHub publication was authorized to `onovo007/surveybridge-ai`. Remote CI, external installations and researcher beta validation remain separate release gates.

## Components created

- `src/surveybridge/`: official DHS client, typed models, local settings, cache/integrity utilities, structured stderr logging, shared research service, normalization, comparability, provenance/export services, Typer CLI and official SDK v2 stdio server.
- `pyproject.toml`, source manifest, MIT license and tested-environment version snapshot: installable Python package and build configuration.
- `skills/surveybridge/SKILL.md`, matching `.agents/` and `.claude/` discovery copies, Claude/Codex/portable plugin manifests and MCP configuration examples.
- `tests/`: deterministic HTTP failure/pagination/cache tests, archived-source normalization and scientific checks, output integrity/safety tests, CLI tests and real MCP subprocess tests.
- `ci/validation.yml`: nine-job Windows/macOS/Linux × Python 3.11/3.12/3.13 validation/build matrix using current documented GitHub Actions major versions. Supplied as an inactive template because the publishing token lacks workflow permission; see ci/README.md.
- `docs/`: verified API behavior, decisions, installation, release notes, limitations, roadmap and this report. `ACCEPTANCE_TESTS.md` and `DATA_ACCESS_POLICY.md` fill missing references from the master prompt.
- `examples/outputs/four-country-immunization-v01/`: complete research bundle; `examples/verification/` contains executed notebook and MCP live verification report. Initial and replay working artifacts remain local and are excluded from distribution.

The three supplied specifications were read in full before implementation and remain unchanged. No proprietary code or unrelated user files were modified. `.gitattributes` prevents Git line-ending conversion of checksum-addressed research archives.

## Commands and observed results

Environment: Windows, CPython **3.12.4**, project-local `.venv`; official **mcp 2.3.0**. Complete tested development dependency versions are in `requirements-windows-py312.lock.txt` (85 pins when recorded, including platform-specific development dependencies). The package itself uses compatible bounds for cross-platform resolution.

| Command / check | Actual result |
|---|---|
| `python scripts/verify_api.py` plus documentation/schema/catalog calls | Anonymous catalogs returned HTTP 200; unfiltered data returned required-filter HTTP 400; filtered aggregates succeeded |
| `python -m pip install --no-build-isolation --no-deps -e .` | Editable package installed; CLI healthcheck returned version 0.1.0 |
| `python -m pytest -q` | **37 passed in 5.62s** in the final complete regression run, launching the MCP subprocess from the freshly installed wheel |
| `python -m ruff check src tests scripts` | Passed; no remaining lint violations |
| `python -m ruff format --check src tests scripts` | Passed for formatted source/test/scripts |
| `python scripts/sync_skills.py --check` | Canonical and repository discovery copies match |
| Bundled skill-creator `quick_validate.py skills/surveybridge` | **Skill is valid!** |
| `claude plugin validate .` | **Validation passed** against the installed host validator |
| `jsonschema.validate(plugin.json, published portable schema)` | Passed; official linked schema archived under docs/evidence |
| `python scripts/run_demo.py` | Live extraction: 26 DPT3 + 26 BCG + 26 measles = **78 observations** across four countries |
| `python scripts/run_demo.py --replay ... --output offline-replay-verification` | Rebuilt all 78 observations and complete bundle offline |
| `python scripts/execute_notebook.py` | Final versioned notebook executed **3 code cells, 0 errors**; hash verification and raw-to-normalized reconstruction passed |
| `python scripts/verify_mcp_live.py` | Real stdio handshake, exact seven tools, and **all seven tool calls status=ok** using public API/cache; search read five catalog pages |
| Workbook inspection with openpyxl | 78 data rows, eight sheets, source estimates as numeric cells, source precision, frozen/filterable observation table and wrapped scientific notes |
| `python -m build --no-isolation` | Built pure-Python wheel and source distribution |
| Fresh `.tmp/install-venv` wheel install with dependency resolution | Installed successfully, final wheel reinstalled after source changes; `pip check`: **No broken requirements found**; CLI healthcheck returned 0.1.0 |
| Final bundle/archive inspection | All **24** manifest checksums verified; source archive contains required docs/skills and excludes local environments and working replay artifacts |

MCP tests use a real subprocess and official SDK client, seed its exact cache through fixture transports, then force the child offline. They cover all tools, output schemas, extraction, assessment, export and invalid-project errors. The independent live MCP report is `examples/verification/mcp_live.json`. The health tool intentionally reports `remote_checked=false`; the live connector and extraction provide remote evidence.

Windows sandbox restrictions required a workspace-local temporary directory for pip/build and execution outside the restricted sandbox for stdio subprocess pipes and local Jupyter sockets. These are development-host constraints, not silently skipped checks. Initial defects—a Windows directory replacement failure and unstructured generic MCP output—were fixed and the relevant tests passed. Jupyter emitted Windows selector/TCP transport warnings; execution completed with no notebook errors. The server itself uses stdio and opens no listening port.

## Source verification and scientific results

Four live API families were verified: `countries`, `surveys`, `indicators`, `data`. The implemented connector uses only these allowlisted aggregate endpoints. No credentials, restricted records or protected ZIP files were requested. It uses documented `page`/`perpage`, validates page/record counts, retries 429/5xx/timeouts within a budget, caches exact response bytes with original retrieval timestamps, and refuses partial projects after pagination limits.

Official metadata confirmed three similarly named DPT3 candidates. The demo selects the general vaccinations series `CH_VACC_C_DP3`, alongside verified `CH_VACC_C_BCG` and `CH_VACC_C_MSL`. The completed survey catalog contains 53 survey records; each selected indicator has 26 national observations. Complete source records, IDs, URLs, UTC timestamps and SHA-256 hashes are retained and verified before export.

Latest retrieved DPT3 source values: Nigeria NG2024DHS **53.4%**, Kenya KE2022DHS **89.2%**, Uganda UG2016DHS **78.6%**, Tanzania TZ2022DHS **90.0%**. They refer to different survey periods; no same-year ranking is justified. All 78 demonstration confidence intervals are absent in the source and remain null. There is no imputation, annual interpolation, reconstructed sample size, invented interval, causal claim or significance test.

The catalog permits ages “12–23 [or 24–35] months.” Automated checks cannot establish survey-specific age, questionnaire, vaccination formulation/ascertainment or geography equivalence. These cautions are present in the notebook, workbook and reports. Combining different indicators blocks equivalent-series pooling; the export includes separate indicator-specific assessments for descriptive review. Empty survey/indicator cells mean no API record in the requested breakdown, not zero vaccination coverage.

## Research artifacts

The final bundle contains observations CSV/JSON, country/survey catalogs, indicator and field dictionaries, survey/indicator availability, overall and indicator-specific comparability reports, quality assessment, limitations, raw response snapshots, original project snapshot, SHA-256 manifest, source attribution, formatted Excel workbook and executable notebook. The executed verification notebook is kept outside the source bundle to retain stable checksums. Raw/normalized integrity checks reject tampered values, source URLs and records.

## Remaining release gates and next priorities

1. Activate and inspect the nine-job CI matrix after granting GitHub workflow permission. The repository and beta distributions use the approved `onovo007/surveybridge-ai` destination; PyPI publication is not claimed.
2. Perform a fresh researcher installation on each OS and verify a natural-language workflow inside logged-in Codex and Claude Code sessions. SDK protocol tests and host manifest validation pass; full model-session behavior remains unverified.
3. Review vaccination populations/definitions against original survey reports, recruit the ten beta testers requested by PRD and add two further scientific examples. These external acceptance criteria are not replaced by unit tests.

The user approved public publication to `onovo007/surveybridge-ai`. GitHub created the public repository but rejected the initial full-tree push: the OAuth token lacks `workflow` scope for `.github/workflows/ci.yml`. An SSH check found no authorized key. The initial full implementation commit is preserved locally on `local/full-mvp`; the publication history starts from a tree with the inactive workflow template under `ci/`. This respects GitHub's workflow restriction and permits source/distribution publication without claiming CI execution. No account credentials or scopes were changed. See ci/README.md for the interactive authorization and activation steps. Demo provenance `git_sha` remains null because source extraction occurred before the first commit. PyPI publication and plugin marketplace listing were not attempted.

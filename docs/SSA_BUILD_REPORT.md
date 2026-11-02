# SSA/publication extension build report

## Release checks 2 November 2026

The internal scientific integrity and methods review is complete for the scoped discovery/extraction workflow. All 837 regional observations and the original 78 observations reconstruct from archived sources. CSV values, nulls and identities agree with JSON; all 16 regional output hashes, 24 beta output hashes and 25 archived source-code hashes are verified. The archive's source-code hashes are checked against commit `4db6edf`, not rewritten to describe newer code. One current code file differs because of the checkpoint robustness fix below. The original bundles remain unchanged. See [scientific review](SCIENTIFIC_RELEASE_REVIEW.md) and the new evidence under `examples/verification/release-2026-11-02/`.

Official vaccination, antenatal-care and HIV guidance was retrieved with HTTP 200. Review documented vaccination age/ascertainment differences, DHS-8 antenatal population and recall changes, and HIV algorithm changes. All three unrestricted regional comparison blocks remain. No PDF table estimates or harmonized outcomes are certified. This is an internal implementation review; independent researcher acceptance remains an original final release criterion.

A fresh regression run exposed intermittent Windows PermissionError during atomic checkpoint replacement. Added six bounded replacement attempts, plus two deterministic tests verifying recovery and persistent-failure preservation of the prior file. The expanded suite now passes **59 tests in 10.95s**, retaining the original 37 and preceding 20 extension tests. Lint, format (50 files), skill synchronization and dependency consistency passed. Standard output safety and existing no-overwrite exports are preserved.

The source archive now excludes the ignored first SSA working bundle while preserving the committed review bundle. CI action versions were verified against official repositories and pinned to commit hashes. The prepared nine-job workflow also runs the offline scientific integrity audit. A local `.github/workflows/ci.yml` is prepared but is not claimed active remotely until authorization, publication and successful execution are observed.

An eleven-page Word concept note covers objectives, architecture, methods, evidence, use cases, target audiences, positioning, proposed launch messaging and adoption measurement. It was rendered with Microsoft Word after the packaged renderer reported missing LibreOffice, and every page was visually checked. It does not claim that outreach or usage measurements have occurred.

Fresh post-fix wheel and source builds succeeded in a new output directory. Archive inspection confirmed the local working bundle is excluded and required reference data, skills, review documents and the committed regional example are present. A new isolated environment installed the wheel with report/chart extras, passed `pip check` and CLI healthcheck, and supplied MCP subprocesses for **59 passing tests in 11.39s**. Separate build hashes and final document hash are recorded in `distribution_review.json` and `release_checks.json`.

A fresh live CLI request through that installed wheel verified PR166 again on 2 November 2026 using a separate cache. It returned `OFFICIAL_PDF_VERIFIED_NO_ESTIMATES_EXTRACTED`, catalog July 2026, cover June 2026, survey NG2025DHS and literal fieldwork 8 December 2025 to 15 February 2026. Its API-pending state explicitly uses the survey catalog's any-indicator scope, not a selected-indicator retrieval. The factual metadata, URLs, times and hashes are preserved in `pr166_live_metadata.json`; no full PDF was stored in the evidence directory.

GitHub workflow authorization is now verified. The active workflow was published in commit `3c682b2`. Both the [push run](https://github.com/onovo007/surveybridge-ai/actions/runs/41405197555) and [PR run](https://github.com/onovo007/surveybridge-ai/actions/runs/41405197815) passed all nine combinations of Windows/macOS/Linux and Python 3.11–3.13. Each push-run log confirms 59 passing tests; all jobs also passed dependency checks, lint, formatting, skill synchronization, scientific integrity audit and package builds. Sanitized remote evidence is recorded in `github_ci.json`. This demonstrates CI portability, not independent first-user acceptance.

Claude Code sign-in is now verified and its natural-language host check passed. The native host loaded `surveybridge:surveybridge`, called healthcheck, discovered 42 SSA countries and verified PR166 with the optional PDF check. All three MCP calls completed with source-backed dates and no extracted estimates. The initial response added an unsupported seasonality inference and overinterpreted source labels; the canonical skill was strengthened, synchronized and retested. The accepted rerun preserves literal dates and naming differences without inventing their methodological meaning. Sanitized evidence is in `claude_host_verification.json` and `claude_host_result.md`; credentials, account details and raw host events are not published.

The scientific review and host checks are complete for the scoped metadata/extraction workflow. PR #1 can become ready for review after refreshed checks pass on the final evidence commit. External researcher acceptance remains a separate final release requirement. No merge or final release is claimed. Earlier historical sections retain the blockers as they stood on 31 October.

## Historical extension verification 31 October 2026

Status: development extension prepared for draft PR review. No final release or merge is claimed. Original specifications, beta tag, original dependency snapshot and validated four-country outputs are preserved.

**Pull request:** [onovo007/surveybridge-ai#1](https://github.com/onovo007/surveybridge-ai/pull/1), open and draft, `feat/ssa-coverage` → `main`. Remote inspection returned an empty status-check rollup and “no checks reported”; the repository has zero active GitHub Actions workflows.

| Verification scope | Current evidence |
|---|---|
| Locally verified | 57 tests, fresh development-wheel MCP, CLI/dependency checks, notebook execution, source/output hashes, skills/plugins and Codex natural-language metadata session |
| Remote verified | Public official source retrieval and metadata checks; normal feature-branch push; open draft PR #1 with main unchanged |
| Unverified / blocked | Remote CI execution, Claude natural-language session while logged out, independent researcher acceptance and survey-specific scientific equivalence |

## Implemented scope

- Versioned UN M49 reference and `SSACountryResolver`, joining current official ISO3 metadata and survey records; unmatched/ambiguous codes remain explicit.
- Backward-compatible regional country/survey/series selectors, public DHS publication API adapter, official country catalog fallback, precise date semantics and exact survey-number joins.
- `surveybridge_list_publications` and `surveybridge_get_report_metadata`, plus checkpointed regional-run/export tools: eleven MCP tools in total, retaining the original seven names/calls.
- CLI publication/latest-survey/report/regional-run/export commands; country overrides, explicit indicators, year filters and operator-controlled caps.
- Serial country/indicator batches, bounded retry/cache/paging, atomic checkpoints, resume skipping successful tasks, and separate failed/pending/no-data/missing-estimate states.
- Separate SSA/publication outputs, lineage, source-project archives, checksums, source-code hashes and executable local notebook with record-count coverage chart.
- Updated canonical Codex/Claude skill and synchronized discovery copies; additive architecture/PRD documents, installation guide, policy and CI template updates.

## Actual source results

The live integration run dynamically resolved **42 DHS-covered SSA countries**, **276 survey records** and **1,321 official publication metadata records** from the checked sources. The UN reference contains 53 countries/areas; 11 ISO3 codes have no matching DHS country metadata in this snapshot. These are discovered counts, not permanently coded coverage promises.

The requested indicators were verified through official catalog search before extraction:

| Family | Official indicator | Retrieved API records |
|---|---|---:|
| Childhood immunization | CH_VACC_C_DP3 | 170 |
| Maternal health | RH_ANCP_W_SKP | 593 |
| HIV prevalence | HA_HIVP_B_HIV | 74 |

All **126 country/indicator tasks completed**, with **0 failed and 0 pending**, producing **837 observations**. The survey×indicator matrix has 455 observed cells and 373 available-survey/no-selected-indicator cells; observed cells may contain multiple population strata. No estimates were missing within the returned records. Source confidence fields were retained where supplied; none were invented. Cabo Verde and Equatorial Guinea remain supported catalog countries despite zero returned observations for these three selected indicators.

Publication traversal recorded successful refresh checks for all 42 selected countries. This is completeness relative to checked official sources and configured traversal, not a claim that every report or every publisher has been captured. Report-only, unmatched and unknown-date cases remain explicit. Latest known releases are selected among dated core survey reports; newer supplementary materials do not silently become the latest survey report.

PR166 is verified as an official Nigeria Mini-DHS 2025–26 Key Indicators Report. Catalog publication date July 2026 and PDF cover June 2026 are preserved separately. Official survey number 636 joins NG2025DHS, which the API still labels Ongoing. Exact PDF fieldwork days differ from the API's first-of-month field values and remain separately recorded. **No PDF estimates were extracted.** See SSA_API_VERIFICATION.md and the source-backed Nigeria/Congo/Rwanda fixtures.

## Verification evidence

The original 37-test suite was rerun before and after extension. One initial Windows/OneDrive directory-rename failure was reproduced; bounded PermissionError retry was added without changing no-overwrite behavior, and the original suite then passed all 37 tests. The only intentional change to an existing test assertion allows additive MCP tools while preserving every original tool assertion and call.

The expanded deterministic suite passed **57 tests in 10.77s** in the final run, with MCP subprocesses launched from the freshly installed development wheel. It covers ISO3/name mismatches, missing country/survey coverage, duplicate pages, missing API publications, ambiguous matches, invalid report links, revised/preliminary lineage, PDF verification refusal to extract estimates, interrupted requests, resume idempotence, output hashes and real stdio calls to the additional tools. Full source-backed fixtures include PR166, PR167 and FR401.

Ruff lint/format and skill synchronization passed. The Claude plugin manifest validator passed. The skill front matter was validated using UTF-8 mode on Windows. New development wheel/source builds use `dist/ssa-development/`; the original beta distributions were not overwritten. A new isolated wheel environment installed the report/chart extras, passed `pip check`, returned a working CLI healthcheck and supplied the server for the final regression run. The extension dependency snapshot is separate (`requirements-ssa-windows-py312.lock.txt`, 93 pins when recorded), and is not a universal multi-platform lock.

The regional notebook executed **3 code cells with 0 errors**, independently verifying archived project lineage and all exported checksums before displaying a coverage chart. The chart was visually inspected. Final checks verified **16 SSA output checksums, 25 source-code hashes and all 24 preserved beta output checksums**. Executed copies and sanitized host evidence are under `examples/verification/ssa/`; the checksum-addressed source bundle is separate at `examples/outputs/ssa-publications-review-2026-10-31/`.

An ephemeral **Codex natural-language host test passed**, calling the three allowlisted public read tools (four calls, including a repeated country check), discovering 42 countries and verifying PR166's metadata/date disagreements through MCP. The first host attempt was blocked by default approval policy; the successful retry used documented invocation-only per-tool approval, without changing persistent settings. The final natural-language response and sanitized tool statuses are preserved. This independently validates the metadata workflow, not researcher acceptance of every analytical interpretation.

## Scientific limits and release gates

All three cross-SSA comparison reports block unrestricted pooled comparison because different survey designs are present. The antenatal series additionally contains multiple population strata despite the national API breakdown. Counts of records are data coverage, not population-health comparisons. Survey-specific questionnaire, age group, timing, geography, vaccination formulation and mini-DHS design still require scientific review. Preliminary/final/API versions are linked and retained; numerical reconciliation, supersession and PDF extraction are not guessed.

Claude Code reports `loggedIn=false`; its natural-language test is blocked and no success is claimed. GitHub authentication lacks `workflow` scope; the complete nine-job workflow remains an inactive template and no passing remote CI run is claimed. External researcher review remains outstanding. These gates prevent a comprehensive final release or merge; the authorized PR is prepared as a draft for review. No credentials, proprietary code, restricted records or full PDFs are included.

The checkout initially had no SSA branch, so `feat/ssa-coverage` was created from existing main while preserving main/tags and user-provided documents. All changes use new commits and a normal branch push; no history rewriting or force push is used. The original four-country output hashes are rechecked before publication.

# SurveyBridge AI v0.1: Sub-Saharan Africa Expansion and GitHub Release Gate

## Context
The existing beta reportedly has 37 passing tests, seven MCP tools, 78 live DHS observations across four countries, reproducible exports, skills, a wheel, and CI files. Treat these as reported results and independently re-run checks before release.

## Mission
Expand geographic discovery and query coverage to **all Sub-Saharan African countries with available DHS surveys** from the earliest accessible survey round to the most recent, without assuming that each country has every indicator or survey type. Preserve existing functionality and tests. Do not replace the four-country example; keep it as a regression fixture.

## Geographic classification
- Use a versioned UN M49 Sub-Saharan Africa country/area classification as geographic reference; record source URL, retrieval date, and classification version. Do not equate Sub-Saharan Africa with the entire African continent.
- Match by ISO 3166-1 alpha-3 code to official DHS country metadata. Where DHS does not expose ISO3 directly, create an explicit, testable, documented crosswalk. Do not fuzzy-match names silently.
- Include a country in the **supported DHS coverage set** only if it belongs to the reference SSA list and the live DHS catalog confirms one or more survey records. Record surveys with zero observations for a requested indicator as available-survey/no-indicator-data, not absent-country.
- Do not hard-code a total number of eligible countries. Report discovered count, source date and unmatched codes. Never treat the current eligible list as permanent.
- Handle country renames, legacy names, code mismatches, newly published surveys and metadata revisions without silent omissions.

## API behavior and scope
- Use the **official DHS public aggregated-data API**, not scraping of restricted microdata portals.
- Support `region=ssa` / `--region ssa`, `--countries` override, `--all-available-rounds`, `--from-year`, `--to-year`, and `--indicator-ids` in CLI; expose equivalent optional selectors in MCP tools while retaining old signatures if possible.
- Discover and list all eligible SSA countries and their survey rounds BEFORE requesting indicator series.
- Execute indicator retrieval in bounded country or survey batches, using verified API pagination, bounded concurrency, caching, backoff for 429/5xx, checkpoint/resume and progress counts.
- Do not bulk-download all indicators by default. Only retrieve explicitly requested indicator IDs or an approved, documented indicator set.
- Make resource caps configurable; warn if the user requests a huge job. Complete partial jobs honestly and save resumption state.
- Preserve existing response schemas unless versioned; update the CLI, MCP clients and docs together.

## Required analytical outputs
1. `ssa_country_catalog.csv`: official and normalized country IDs, ISO3, country names and classification status.
2. `ssa_survey_coverage.csv`: one row per eligible country/survey round, year, survey ID, survey type and metadata provenance.
3. `ssa_indicator_availability.csv`: country x survey x selected indicator availability, with explicit no-data statuses.
4. `ssa_observations.csv`: values, all available confidence bounds, sources, retrieval time, original survey and indicator references.
5. `ssa_comparability_report.md` and `.json`: unit, population, definition, period, disaggregation and missingness risks.
6. `ssa_run_manifest.json`: filters, country count, matched/unmatched, source URLs, timestamp, software version, completeness, page counts, checksums and exceptions.
7. `ssa_analysis.ipynb`: reproducible descriptive summaries and charts from local exported files; no data fabrication, imputed years or unsupported significance claims.
8. `ssa_summary.md`: readable coverage overview including per-country, per-survey and per-indicator totals and failures.

## Scientific safeguards
- DHS rounds are repeated cross-sectional survey records, not continuous annual surveillance.
- Don't interpolate missing survey years, replace null uncertainty with guesses, or infer temporal trends from differing survey definitions without warnings.
- Use official metadata; comparability is not proven by an identical indicator label alone.
- Distinguish no survey, survey exists but selected indicator absent, missing estimate, and API retrieval failure.
- Never infer a point estimate from a blank API field.
- Keep old four-country results as a reproducibility regression test.

## Implementation tasks
1. Inspect the existing repository and read `docs/BUILD_REPORT.md`, `docs/INSTALLATION.md`, examples and tests. Preserve all original files and working APIs; make changes through new commits. Do not rewrite history or discard user changes.
2. Verify official DHS country/survey API documentation and the current M49 geographical classification.
3. Implement `SSACountryResolver` and documented ISO3-DHS crosswalk plus tests.
4. Extend catalog and indicator services to accept regional selection; preserve original signatures or offer backwards-compatible wrappers.
5. Implement safe batching, resumable requests, caching, progress and partial-result handling.
6. Export the coverage matrix, observation set and reproducibility manifest.
7. Run existing 37 tests plus new SSA tests; add fixtures for a DHS country with no requested indicator, mismatched country code, duplicate page, mixed survey rounds and intermittent network failure.
8. Add real integration smoke tests showing the discovered SSA country count and at least three indicator families (immunization, maternal health and HIV), while making sure indicator IDs and availability are verified from the live API.
9. Update skill instructions, README, examples, CLI help and MCP schemas to show SSA workflows.
10. Build and test wheel from a clean install, execute notebook, verify export hashes, run Codex and Claude natural-language tests where access exists.

## GitHub release instructions
- Ask for / use the exact owner and repository destination before any remote push. Do not assume repository ownership from a local folder or guess a remote URL.
- Create a feature branch `feat/ssa-coverage` and commit changes with meaningful messages. Preserve existing main branch and tags.
- Push only after remote and authentication are verified and authorized. Do not force-push.
- Open a pull request to main and run remote CI; fix failures, obtain review and merge per repository rules.
- Public release is blocked until GitHub CI passes, fresh-wheel MCP handshake passes, host-level Claude/Codex tests are documented, and at least one independent researcher or independent test session confirms the workflow. If some tests cannot be done, label pre-release accurately rather than claiming final release.
- Do not commit credentials, proprietary Quantium code, private datasets or downloaded restricted DHS microdata.

## Deliverable report
Report actual countries with DHS coverage, total surveyed rounds, requested indicators, total observations, missingness categories, API errors, fully/partially completed batches, test counts, exact CI status and PR URL. Explicitly distinguish locally verified, remote verified, and unverified claims.

## Start immediately
Read the existing beta, implement the region resolver and survey coverage discovery first. Do not discard the existing four-country proof of concept or expand into full microdata scraping, Bayesian forecasting or hosted accounts during this sprint.

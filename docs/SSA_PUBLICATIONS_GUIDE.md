# SSA and official report discovery — development branch

The original four-country bundle and beta interfaces remain intact. This extension adds region discovery, publication-first metadata and checkpointed multi-country extraction. The original architecture/PRD are preserved; see [architecture extension](ARCHITECTURE_SSA_PUBLICATIONS.md) and [requirements extension](PRD_SSA_PUBLICATIONS.md).

## Install and select sources

Install the branch locally with `python -m pip install -e '.[reports,analysis,dev]'`. The reports extra enables optional bounded PDF front-matter verification; analysis supplies matplotlib for the regional notebook. Neither extra enables numerical PDF extraction.

```sh
surveybridge countries --region ssa
surveybridge surveys --region ssa
surveybridge latest-surveys --region ssa
surveybridge publications --region ssa --countries NG,CG,RW
surveybridge report https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf --verify-pdf
surveybridge ssa-run --region ssa --indicator-ids CH_VACC_C_DP3,RH_ANCP_W_SKP,HA_HIVP_B_HIV --all-available-rounds --max-tasks 20
surveybridge ssa-run --run-id RETURNED_RUN_ID --max-tasks 20
surveybridge ssa-export RETURNED_RUN_ID ssa-research-run
```

Indicator IDs in this example were found in the official catalog; discovery never selects all indicators by default. Explicit countries override the regional set. Old positional commands such as `surveybridge series CH_VACC_C_DP3 NG,KE,UG,TZ` still work. Optional `--from-year`/`--to-year` limit principal survey years; `--publication-year` and `--fieldwork-year` apply different filters. `--publication-type` matches source document-type text. `--indicator-category` requires an exact official topic selector label; it is a publication-topic filter, not evidence that a numeric estimate exists. Unknown dates cannot satisfy a date filter and are reported as excluded/unknown.

SSA uses the packaged `UN-M49-2026-10-31` reference (sub-region 202), whose URL, retrieval time and source HTML hash are recorded. Current DHS `ISO3_CountryCode` supplies the exact join; unsupported/ambiguous codes remain explicit. No fuzzy country matching or fixed eligible total is used. Reviewed legacy display-name aliases apply only when joining the separate official website selector and are recorded in the source code. Regenerate a *new versioned* reference after reviewing future UN revisions; the reference does not silently change at runtime.

## Publication-first behavior

The API publication adapter retains canonical survey IDs and source rows. Its schema currently omits publication dates and can lag the public site. The public publication-search country selector provides official country query IDs; country-scoped pages and their “show all” links supply historic and current metadata. New core reports are cross-referenced by their official survey-page number against API SurveyNum, with unmatched/ambiguous links retained. Existing API records and source histories are enriched, not replaced by title guesses. Supplementary publications are retained as metadata; lack of a survey join stays explicit.

Search follows only validated official public URLs. It never accesses gated data downloads. Web/page byte budgets, retry limits, request limits and exact-query caching bound resource use. The default request cap is 500 new HTTP requests per discovery service, and extraction runs at concurrency one. Set `SURVEYBRIDGE_MAX_WEB_REQUESTS` (maximum 2000), `SURVEYBRIDGE_MAX_BATCH_TASKS` (maximum 5000), `SURVEYBRIDGE_WORKSPACE`, and `SURVEYBRIDGE_OUTPUT_ROOT` as needed. `max_tasks` limits attempted country/indicator tasks per invocation; checkpoint/resume skips successful tasks. Increase caps deliberately for large jobs. Completed, failed and pending tasks remain separate. `refresh_publications=true` retries metadata discovery while reusing successful cached pages.

`SURVEYBRIDGE_OFFLINE=1` uses exact cached API/web metadata and never fetches report bodies. Online metadata cache lifetime is 24 hours; original retrieval times remain unchanged. Last successful country refresh, errors, limits and source-specific completeness are exported. Incremental joins deduplicate report identity and checkpoints prevent duplicate successful extraction tasks. No schedule or background polling is installed.

## PR166 verification

The direct official PDF is accessible from this environment even though one web-fetch service returned HTTP 403. Its title/front matter identify a Nigeria Mini-DHS 2025–26 Key Indicators Report. The methods state fieldwork from 8 December 2025 to 15 February 2026. The PDF cover says June 2026; the official publication page says July 2026. Both month-precision dates are preserved. The official page links survey number 636, which maps to NG2025DHS; the API still marks that survey Ongoing and the API publication catalog omits PR166. The report must remain visible despite that metadata disagreement. Verification evidence and source hashes are saved separately; full PDFs are not redistributed.

No estimates are extracted from PR166. PDF-table extraction remains a gated future capability requiring page/table/row/column/denominator/unit lineage and independent validation. Preliminary/final/API records are never pooled as independent estimates. Current lineage labels multiple versions `needs_reconciliation` unless authoritative evidence establishes a stronger relationship. A final report's existence does not automatically establish that every preliminary estimate is superseded.

## Outputs and interpretation

The new bundle contains `ssa_country_catalog.csv`, `ssa_survey_coverage.csv`, `ssa_indicator_availability.csv`, `ssa_observations.csv/.json`, comparability reports, `ssa_publication_catalog.csv`, `latest_survey_releases.csv`, `report_api_coverage_gaps.csv`, `publication_lineage.json`, source project archives, run manifest, local notebook and summary. Output directories must be new; the existing validated beta bundle is unchanged.

Availability distinguishes no matching DHS country/survey, known survey without requested indicator, missing estimate, API failure, pending request and observed record. Report metadata-only does not imply a verified downloadable PDF. Dataset access remains unknown unless a source explicitly establishes restriction. Reports described as API-pending are absent for the checked scope; this does not promise future publication. Latest known releases rank verified catalog dates, not survey principal years; unknown-date records and refresh failures limit completeness claims.

The notebook checks hashes and archived source lineage, then charts counts of retrieved records per country. These counts describe coverage, not health outcome trends. Survey-specific questionnaire, vaccination definitions, age populations, geographic coverage, mini-DHS design and timing require review before comparing estimates. Missing years and confidence bounds remain missing.

## Release gate

This branch is prepared for review, not a comprehensive final release. Remote CI, fresh-wheel MCP and notebook checks, documented host-level tests and independent acceptance must be recorded separately. The existing OAuth workflow-scope restriction remains relevant; an inactive CI template is not a passing workflow run. The PR stays draft while required gates are unresolved.

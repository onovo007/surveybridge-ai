# SurveyBridge AI: Latest Mini-DHS and Preliminary Report Expansion

## ADDENDUM: Include newly released mini-DHS, Key Indicators and preliminary reports across SSA

**High-priority requirement added October 31, 2026.** Preserve all sections above. Expand survey discovery beyond API-published indicator observations to include newly published official DHS Program reports, even when their results have not yet appeared in the aggregated indicator API.

**User-supplied Nigeria example:** https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf

Treat this exact link as a required discovery and regression-test candidate. First verify its title, country, fieldwork period, survey classification, publication date, tables, and official document identifier directly from the PDF or DHS publication metadata. Do not assume the report's contents, call it a mini-DHS, or extract numeric values until verification succeeds. If access is blocked, record `SOURCE_UNVERIFIED` with the URL and error and make it easy to re-run the check locally.

### New product behavior

1. Discover **all eligible survey publications** for every dynamically identified DHS-covered SSA country using the official DHS `publications` endpoint, DHS publication search/catalog, and official country survey pages. Use actual published document types and metadata instead of imposing unofficial categories.
2. Recognize **Key Indicators Reports (KIR), preliminary reports (PR), mini-DHS or abbreviated surveys where officially identified, final reports (FR), and relevant indicator reports**. Include official follow-up releases and country-led survey publications only where verifiable and clearly attributed.
3. Include both historic and newest reports. Use publication date, survey fieldwork date and survey year as distinct fields. A late-published report should appear under its real fieldwork period in survey trends and under its publication date in release monitoring.
4. Cross-reference surveys to publications by canonical survey ID where available; otherwise use carefully documented matching on country, fieldwork dates, survey title and source reference. Flag ambiguous matches for review.
5. Distinguish four separate source states:
   - `API_INDICATOR_AVAILABLE`
   - `OFFICIAL_REPORT_AVAILABLE_API_PENDING`
   - `REPORT_METADATA_ONLY`
   - `DATASET_RESTRICTED_OR_UNAVAILABLE`
   Multiple states may apply to the same survey.
6. Add a **publication-first discovery fallback** when the API catalog is behind the newly posted report. Do not silently omit a country or survey because a newer report has no API indicator observations.
7. Add `surveybridge_list_publications` and `surveybridge_get_report_metadata` MCP tools, retaining existing seven tools and their signatures. Report-only discovery must not pretend to retrieve numerical indicator data.
8. **Optional PDF-table extraction, carefully gated:** only for downloadable, publicly accessible official reports where terms permit it and validated table structure supports high-confidence extraction. Do not require PDF extraction to complete v0.1. If introduced, use tested PDF parsing and human-verifiable page/table references; never fill missing cells by LLM guessing.
9. Any report-derived value must include `country`, `survey_id` if known, `report_id`, `report_type`, `source_url`, `source_page`, `table_id`, `row_label`, `column_label`, `denominator_definition` if present, `unit`, `survey_fieldwork_period`, `publication_date`, `retrieved_at_utc`, `extraction_method`, and `verification_status`.
10. Do not merge a preliminary report estimate with an eventual final-report or API estimate as independent observations. Link their lineage and identify `superseded`, `revised`, or `needs_reconciliation` where supported by evidence. Default to displaying the most authoritative verified estimate, with the preliminary historical value preserved separately.
11. If a mini-DHS differs in design or coverage from a standard DHS, flag methodological comparability. Never claim national or state representativeness, survey design equivalence, or matching vaccination definitions without supporting documentation.
12. Add a `latest-surveys --region ssa` discovery view and exports: `ssa_publication_catalog.csv`, `latest_survey_releases.csv`, `report_api_coverage_gaps.csv`, `publication_lineage.json`. Provide filters for country, publication type, publication year, fieldwork year and indicator category.
13. Document update frequency, last successful official catalog refresh, API delays, transient errors and source-specific completeness. Incremental sync should be idempotent and not generate duplicates.
14. Add integration and fixture tests for Nigeria's supplied PR166 URL, plus at least two other SSA countries with reports in different publication categories. Test a report lacking API observations, an invalid PDF link, a revised final report, an ambiguous survey match and a PDF with a complex table. Expected behavior is explicit warnings, not invented data.
15. In user-facing prompts, permit: "Find the latest mini-DHS and preliminary DHS results for all Sub-Saharan African countries, including surveys that are not yet present in the DHS indicator API. Provide official report links, availability status, and verified indicator extracts where supported."

### Implementation and release instructions

- First update the architecture, PRD, `SKILL.md`, CLI, MCP schemas and documentation to include publication discovery.
- Implement **metadata discovery and links first**, with source-backed verification and no scraping of protected content. PDF indicator extraction is a separately gated follow-on capability, not a prerequisite for a safe release.
- Keep the four-country regression test and SSA discovery tests. Add new publication-based fixtures and re-run all existing tests.
- Do not overwrite original documents, example extracts, validated outputs or existing files. Add new modules and preserve backward compatibility.
- Do not publish the GitHub release as fully comprehensive if the PR166 source or official publication catalog cannot be verified. Report the limitation explicitly.
- Validate DHS source terms before caching or redistributing any full report/PDF; reference official URLs wherever possible.

### Additional acceptance gate

For every DHS-covered SSA country, the report must show: latest known published survey/report (if available), exact survey and publication dates where verified, type, official URL, whether API observations exist, any unmatched report, and last checked date. Do not make unsupported claims that all reports or values have been retrieved.

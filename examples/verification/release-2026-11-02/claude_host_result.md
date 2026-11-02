Read-only integration test complete. Three MCP tools called; no estimates extracted, no files written, no shell used.

## 1. Health check
`surveybridge_healthcheck` → `status: ok`, version `0.1.0`, transport `stdio`, `offline: false`, configured source `https://api.dhsprogram.com/rest/dhs`.

Limit: `remote_checked: false`. This reports **local server version and config only** — it does not assert that the DHS API is reachable or current.

## 2. SSA country discovery
`surveybridge_list_countries(region="ssa")` → **42** countries with `DHS_SURVEY_CONFIRMED` status, all matched via `official_ISO3_CountryCode`.

- Reference: UN M49 version `UN-M49-2026-10-31`, selection "Sub-region Code = 202", retrieved 2026-10-31 (<https://unstats.un.org/unsd/methodology/m49/overview/>)
- DHS metadata retrieved 2026-11-02T07:23:05Z from `api.dhsprogram.com/rest/dhs/countries` and `/surveys?surveyStatus=all` (both cache hits)
- **11 unmatched M49 SSA codes** (no DHS country match): ATF, DJI, GNB, IOT, MUS, MYT, REU, SHN, SOM, SSD, SYC
- **1 unmapped DHS code**: `OS`
- DHS country IDs are not ISO codes — e.g. Burundi `BU`, Botswana `BT`, Equatorial Guinea `EK`, Liberia `LB`, Madagascar `MD`, Namibia `NM`, Niger `NI`

42 is the count discovered at this retrieval date under this M49 version, not a fixed SSA total. "No DHS country match" means no match in the checked DHS metadata — it is not evidence that no survey or report exists.

## 3. Nigeria PR166 verification (`verify_pdf=true`)

**Official sources** (all retrieved 2026-11-02):
- PDF: <https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf> (sha256 `6917a48d…`, 07:24:57Z)
- Catalog detail: <https://dhsprogram.com/publications/publication-PR166-Preliminary-Reports-Key-Indicators-Reports.cfm> (07:23:08Z)
- Publication search: <https://dhsprogram.com/publications/Publication-Search.cfm?pubid1=PR166&shareurl=yes> (07:23:07Z)

**Title:** `Nigeria Mini DHS 2025-26 - Key Indicators Report (English)`
**Type:** Preliminary Reports/Key Indicators Reports
**Authors:** National Population Commission, Abuja, Nigeria, and ICF, Rockville, Maryland, USA
**Survey join:** `NG2025DHS`, survey_year 2025, `match_status: official_survey_number_join`
**PDF verification:** `OFFICIAL_PDF_VERIFIED_NO_ESTIMATES_EXTRACTED`; 40 pages; `pypdf_front_matter_structure`; `official_mini_design_label: true`; `numeric_estimates_extracted: false`

### Disagreements — preserved, not reconciled

| Field | Catalog / API | PDF | Status |
|---|---|---|---|
| Publication date | `2026-07` ("July 2026", month precision) | cover date `2026-06` (month precision) | Both retained; server warning issued |
| Survey name | "Nigeria Interim DHS, 2025" (catalog) | title says "Mini DHS 2025-26"; `official_mini_design_label: true` | Distinct labels retained |
| Fieldwork start | `2025-12-01` | `2025-12-08` | Both retained |
| Fieldwork end | `2026-02-01` | `2026-02-15` | Both retained |

The explicit, literal fieldwork dates are the PDF front-matter sentence: **2025-12-08 to 2026-02-15** (`method: literal_fieldwork_sentence_front_matter`). The API values are formatted as full dates but fall on the first of the month; that formatting does not establish those as actual fieldwork days, and no methodological precision should be read into them. The "Interim" vs "Mini" label difference is a difference in source labels only — it does not by itself establish a survey-design conflict, which would need the report's own methods section to resolve. Reconciliation of the date pairs is unsupported by this evidence: treat as **needs_reconciliation**.

### API availability scope
- `source_states: ["OFFICIAL_REPORT_AVAILABLE_API_PENDING"]`
- `api_availability_scope: survey_catalog_any_indicator_not_requested_indicator`
- Warning: "Official report exists while API survey status is not Completed"

**Scope statement:** availability here is **survey-wide catalog metadata**, not a check of any specific indicator — no indicator was requested in this test. So this says the official report is public while the API survey round is not yet marked Completed; it says nothing about whether any particular indicator is retrievable. This is not `DATASET_RESTRICTED_OR_UNAVAILABLE` — dataset access was not checked and unknown access is not a confirmed restriction.

## Scientific limits
- No numeric estimates were extracted and PDF-table extraction is disabled in this extension. For PR166 figures, consult the official page/table directly at the PDF URL above; the server flags that complex tables need independent page/table/denominator validation.
- "Latest known" status reflects only the sources checked at the timestamps above — not complete surveillance of all publishers. An absent API entry does not prove a survey or report does not exist.
- The PR166 Key Indicators Report is a preliminary/interim release. If a final or revised Nigeria report later appears for `NG2025DHS`, it must stay linked to this survey and report ID — successive versions are not independent observations.
- Comparability was not assessed (no project created, by design of this read-only test). Any cross-round or cross-country use requires verifying populations, questionnaire, coverage and fieldwork dates in the original reports.

Source attribution: The DHS Program (ICF) and National Population Commission, Nigeria, via public aggregated DHS metadata.
# SSA/publication source verification — 31 October 2026

Official references: [DHS publications API](https://api.dhsprogram.com/html/api-publications.cfm), [publication fields](https://api.dhsprogram.com/rest/dhs/publications/fields?f=json), [country fields](https://api.dhsprogram.com/rest/dhs/countries/fields?f=json), [public publication search](https://dhsprogram.com/publications/Publication-Search.cfm), [UN M49](https://unstats.un.org/unsd/methodology/m49/overview/).

Anonymous API probes succeeded. The country catalog has `ISO3_CountryCode`; therefore the SSA resolver uses that explicit field, not inferred ISO2/DHS-code equality or fuzzy names. The current UN reference contains 53 SSA countries/areas. Intersecting its sub-region code 202 with official DHS countries and at least one survey record yields 42 eligible countries in this source snapshot. Eligibility is discovered at runtime. Unmatched ISO3 codes are exported; a country with a known survey but no requested indicator remains a supported country.

The survey API accepts `surveyStatus=all` and returned 477 worldwide records; the SSA selection contains 276, including ongoing records. The existing beta's explicit-country survey call retains its completed-survey behavior; regional discovery includes all statuses to expose newly posted reports. Principal survey year, survey label and fieldwork dates remain distinct.

The `publications` endpoint returned 962 records worldwide. Actual fields are `PublicationId`, `PublicationTitle`, `PublicationDescription`, `DHS_CountryCode`, `SurveyId`, `SurveyYear`, `SurveyType`, `PublicationURL`, `ThumbnailURL`, `PublicationSize`. It does **not** supply a publication date in this response. Supported country/survey/year filters follow official docs; publication type/year/topic filtering is done against source-backed web metadata rather than invented API parameters. Existing bounded paging/count validation applies; repeated page bodies are rejected.

The public search form exposes `country1`, `topic1`, `pubid1`, `shareurl`, `showall` and `PubTypeLogID` parameters. Country selector IDs come from the actual form; exact names and explicitly reviewed legacy aliases join this separate selector to the ISO3-resolved DHS country list. Country-scoped “show all” links are followed with semantic deduplication and request caps. Links that lose the country scope are not used as evidence for that country. A changed/empty unexpected page produces SOURCE_UNVERIFIED. These are public catalog pages, not restricted microdata portals.

Core report detail pages expose document type, countries, survey link, publication date and report ID. The survey link's numeric ID joins to official `SurveyNum`; unmatched/ambiguous joins stay explicit. Publication dates like `07/2026` or `July 2026` are stored as `2026-07` with month precision. No first day is invented. Source URL, source page hash, original factual metadata, retrieval time and match method are retained. Metadata from supplementary publications is retained without claiming a survey join or a verified downloadable PDF.

## Mandatory Nigeria case

Both [PR166's official catalog page](https://dhsprogram.com/publications/publication-PR166-Preliminary-Reports-Key-Indicators-Reports.cfm) and the [exact supplied PDF](https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf) returned HTTP 200 to the direct client. A separate web retrieval service returned HTTP 403, which did not establish that the source was universally inaccessible.

The catalog identifies a Nigeria Mini DHS 2025–26 Key Indicators Report, publication July 2026, and links survey number 636 (“Nigeria Interim DHS, 2025”). That number maps to `NG2025DHS`, still marked Ongoing in the API; PR166 is missing from the aggregate publication catalog. PDF page 3 carries June 2026, and page 5 explicitly gives fieldwork 8 December 2025–15 February 2026. These differ in precision from API fieldwork values 1 December 2025–1 February 2026; the explicit PDF dates are preserved separately. The cover/title page was visually rendered and inspected as well as parsed.

The PDF has 40 pages and SHA-256 `6917a48ddb5ff5054818e8089d7a5b77e0d2e41f0869fe81e0c7a2ae6e1bee87`. Front-matter verification records the mini-DHS label and date evidence; it does not validate or extract estimate tables. No full PDF is distributed. The metadata fixture retains URLs, facts, hashes and discrepancies.

Additional source-backed regression cases are Congo `PR167` (Key Indicators, August 2026) and Rwanda `FR401` (final report, August 2026). These cover multiple report categories in different SSA countries. Multiple report versions remain separate and linked; supersession or numerical equivalence is not inferred from filenames or dates.

## Source completeness and access terms

The integration run checked the API catalog and country-scoped public catalogs for every selected country and recorded per-country refresh outcomes. “Scan complete” means the configured source traversal completed; it does not guarantee that all country-led publications are indexed or accessible. Record-level unknown dates, unmatched surveys and unverified downloads remain visible. No source-check success is converted into a claim of methodological comparability.

Official API terms and attribution were reviewed. Optional public PDF bytes are processed in memory, bounded by byte/page limits, and not cached or redistributed; only factual metadata and hashes are exported. Protected data downloads, authentication and ZIP extraction remain outside scope. A restricted dataset state is used only if evidence confirms restriction; unknown access remains unknown.

The Codex host test uses [documented per-tool configuration](https://learn.chatgpt.com/docs/extend/mcp) to allow only its three public read tools for that invocation. No persistent host settings are changed. Claude authentication and GitHub workflow permission are independent external release gates, recorded in the build report.

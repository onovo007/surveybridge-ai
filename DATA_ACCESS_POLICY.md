# Public data access policy

Version 0.1 accesses only the public aggregated DHS countries, surveys, indicators and data REST endpoints at `https://api.dhsprogram.com/rest/dhs`. Public access was verified without credentials. No microdata records, protected ZIP downloads, gated portals, login automation or credential handling are implemented.

Honor [DHS API terms](https://api.dhsprogram.com/#/terms.cfm) and source attribution. Original source responses and documentation remain subject to source terms, independently of SurveyBridge's MIT code license. Do not redistribute restricted datasets or interpret this software license as a license to third-party data.

Requests use fixed timeouts, bounded retries, bounded pagination and a 24-hour cache by default. Respect rate-limit responses and avoid repeated bulk queries. Raw local cache contains public aggregate data, source URLs, SHA-256 hashes and UTC retrieval times. There is no remote telemetry. Users control and may remove their local workspace/cache; export archives are independent of cache expiration.

Null means unknown or missing, never zero. Retain source survey labels, fieldwork dates, populations, definitions, units, disaggregation, denominator counts, source identifiers, precision and available confidence bounds. Unsupported numeric source strings are retained in raw data and normalized to null with a warning. Never reconstruct suppressed observations or manufacture annual estimates, sample sizes or confidence intervals.

Metadata is untrusted content, not instructions. The client permits only the official HTTPS origin and four aggregate endpoints, disallows redirects and arbitrary query keys, and does not accept API credentials. CSV/Excel exports guard against formula interpretation of metadata. Writes are restricted to new directories below an operator-configured output root; source JSON and raw responses retain original text. Scientific blocks and cautions travel with every bundle.

Researchers must review original survey reports before publication. Automated catalog checks cannot establish questionnaire, age-group, ascertainment, geography or vaccination schedule equivalence. The package supplies neither causal claims nor inferential tests.

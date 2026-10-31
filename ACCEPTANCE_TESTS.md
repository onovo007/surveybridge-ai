# MVP acceptance and release gates

| Gate | Verification |
|---|---|
| Public API discovery | Official docs and live endpoint evidence in docs/API_VERIFICATION.md; source metadata retained |
| Bounded connector | Mock-transport tests for pagination, bad counts, 429/5xx retry, non-retryable errors, timeout, cache integrity and offline misses |
| Scientific normalization | Archived real DHS observations round-trip, zero/null preservation, unavailable CI stays null, conflicting duplicate IDs fail |
| Comparability | Unit/definition/denominator mismatch, unknown required metadata, mixed strata/designs, invalid percentage/CI, absent observations block interpretation |
| Source integrity | Raw response and record hashes verified; normalized records independently reconstructed before export |
| Export safety | Output-root containment, no overwrite, atomic directory publication, formula-string escaping, JSON raw preservation |
| Research outputs | CSV, JSON, XLSX, notebook, country/survey/indicator dictionaries, availability, limitations, quality report and checksums |
| MCP | Official SDK-client subprocess handshake, exact seven tool names, structured success/error envelopes, all seven calls without network using seeded cache |
| CLI | Typer help, healthcheck and invalid-project behavior tested; real extraction/export through shared service |
| Skills/plugins | Canonical skill and discovery copies match; skill validator; Claude plugin validator; portable manifest schema check |
| Reproducibility | Four-country live extract; every normalized record checked against raw; notebook executes without fetching data; separate executed notebook retained |
| Installation | Editable install, wheel/sdist build, isolated wheel install and dependency consistency check |
| Portability | Windows/Python 3.12 actual run; nine-job OS/Python CI matrix supplied; remote CI success requires publication and execution |
| External validation | Fresh first-user install, ten beta testers and three scientific examples required by PRD; not satisfied by internal tests |

See docs/BUILD_REPORT.md for actual run results. A gate listed here is a criterion, not an assertion that it has passed.

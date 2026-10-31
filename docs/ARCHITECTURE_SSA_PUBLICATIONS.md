# SSA and publication discovery architecture — unreleased extension

This document extends the original ARCHITECTURE.md without replacing it. The supplied SSA specification and latest-report addendum are references authorized by the user's implementation request. Existing seven tools, project snapshots and validated four-country outputs remain supported.

Add a versioned UN M49 SSA reference and exact ISO3-to-DHS matching, regional catalog discovery, a publication metadata adapter, report verification, resumable explicit-indicator extraction and an additive research bundle. Discovery joins current survey records and public official publication metadata before requesting estimates. Publication-only candidates remain visible even if survey/API indexing lags.

Publication dates, principal survey years and fieldwork dates are separate. Canonical survey IDs are used when supplied; otherwise exact country/year/type candidates are presented with match evidence and ambiguity flags. A report title containing preliminary, key indicators or mini-DHS is never taken as evidence of equivalent survey design. Preliminary/final/API sources retain separate lineage; no report values are synthesized or merged as independent observations.

New MCP tools: `surveybridge_list_publications`, `surveybridge_get_report_metadata`. Regional selectors on existing tools are optional and backward compatible. Resumable batch extraction and publication discovery are also available through additive tools/CLI commands. Original result-envelope fields remain unchanged; new detail is nested in data. Partial jobs carry explicit failed/pending task states and export completeness warnings.

Official public links and metadata are the release scope. Downloadable PDF verification is bounded, optional and local; full PDFs are not redistributed. Automated PDF numeric extraction is deferred until table-level scientific validation can be demonstrated. SOURCE_UNVERIFIED records preserve URLs/errors rather than inventing values. Unknown dataset access is not treated as confirmed restriction.

New release requires source verification, preserved regression tests, expanded fixtures, fresh-wheel MCP handshake, notebook execution, host-session evidence where accessible, independent validation, and passing remote CI. A draft PR can expose incomplete verification honestly without a final release or merge.

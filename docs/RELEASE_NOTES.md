# Unreleased SSA and publication extension

Publication-first discovery covers DHS-covered SSA countries using official metadata and versioned UN M49 classification. Adds four MCP tools, checkpointed regional extraction, report/API availability and publication lineage exports. Nigeria PR166, Congo PR167 and Rwanda FR401 have source-backed metadata fixtures. Numerical PDF-table extraction remains disabled.

The recorded example contains 837 public API observations from 126 completed tasks across 42 eligible countries; counts describe a source snapshot. An internal scientific review validates archived lineage and preserves all three unrestricted SSA comparison blocks. Independent researcher acceptance remains outstanding.

Release checks on 2 November 2026 add bounded Windows checkpoint-lock recovery, two failure/recovery tests, a repeatable integrity audit, a signed-in Claude host probe, packaging exclusion for the local working bundle and a comprehensive Word concept note. The deterministic suite passes 59 tests. GitHub workflow access is authorized, and both initial push/PR validation matrices passed all nine OS/Python combinations. The signed-in Claude skill and three-tool metadata workflow passed after tightening guidance against unsupported interpretation of seasonality, date precision and survey labels. Independent researcher acceptance remains outstanding. This section is not a published release announcement.

# v0.1.0 — GitHub beta, 31 October 2026

Initial implementation by Quantium Insights LLC: official DHS aggregated REST connector; typed country, survey, indicator and observation metadata; bounded paging and retry; exact-response caching; persistent research snapshots; conservative comparability findings; Typer CLI; seven official Python SDK v2 MCP tools; Codex/Claude skills and plugin metadata; documented exports with raw records, checksums and offline notebooks; automated tests and a cross-platform CI definition.

The real demonstration contains 78 DPT3, BCG and measles observations across Nigeria, Kenya, Uganda and Tanzania. Values, survey IDs, principal years and original records are preserved. No confidence intervals were created.

## Known limitations

- No restricted microdata, complex survey estimation, MICS, IPUMS, DHIS2, causal inference or forecasting.
- Catalog metadata cannot certify survey-specific age groups, questionnaires, vaccine formulation, ascertainment or geography; source-report review remains necessary.
- CIs are often absent; null is preserved. No annual interpolation or statistical significance testing.
- Different indicators and mixed strata/designs block equivalent-series interpretation. Exports retain blocked evidence for review.
- Search uses catalog text, not a clinical terminology ontology; “DPT 3” matches the source wording.
- MCP series returns at most 500 rows; complete data are in the project/export. Page-budget failures require narrower queries.
- Cache is local and expires after 24 hours for online reuse; it is not a multi-process database or a live surveillance store.
- Dependency environment snapshot was produced on Windows/Python 3.12. macOS/Linux and other supported Python versions require CI confirmation.
- Host schema/configuration and stdio behavior are tested separately from natural-language orchestration; model-session acceptance testing remains outstanding.
- GitHub Actions activation is blocked by the publishing OAuth token's missing workflow scope; the complete inactive template and activation steps are under `ci/`.
- PyPI publication, external first-user installation, ten beta testers and two additional scientific examples remain release activities.

See BUILD_REPORT.md for exact verification evidence and unresolved blockers.

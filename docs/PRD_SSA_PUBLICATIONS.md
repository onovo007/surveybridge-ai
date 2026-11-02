# SSA and latest-survey requirements — unreleased extension

Extends PRD.md while preserving the original file and acceptance history.

- Dynamically resolve UN M49 Sub-Saharan Africa against official DHS countries and survey records. Preserve unmatched areas and exact crosswalk evidence. Country totals are discovered, never a fixed eligibility assumption.
- List all eligible survey rounds and official publications before retrieving explicitly selected indicator IDs. Support country override, year ranges, all available rounds and regional selectors.
- Include official preliminary, key indicator, final and other report types as supplied by the catalog. Mini-DHS identification requires explicit official evidence. Display latest publications separately from latest fieldwork.
- Verify the mandatory Nigeria URL https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf or expose SOURCE_UNVERIFIED with its actual access failure and a rerunnable check. No numeric values from an inaccessible report.
- Distinguish API observations, verified official report awaiting requested API indicators, metadata-only reports, unknown access, retrieval failures and confirmed dataset restrictions. These states describe specific requested indicators/source checks, not universal survey availability.
- Export SSA country/survey/indicator coverage, observations, publication catalog, latest known releases, report/API gaps, lineage, comparability, run completeness, local notebook and source checksums to a new directory only.
- Use bounded serial/concurrent batches, cache, retry, checkpoints and resume. Never silently mark failed or pending requests as no-data. Incremental metadata joins deduplicate stable source IDs and flag conflicting revisions.
- Keep every original regression test; additive MCP discovery requires updating only the exact-tool-list assertion to allow additional tools. Retain all original tool names and calls. Document every unverified release gate; open a draft PR if any remain.

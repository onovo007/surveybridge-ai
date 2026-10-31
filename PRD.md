# SurveyBridge AI v0.1 Product Requirements

## Intended users
Public health epidemiologists, students, Ministries of Health, NGOs, survey analysts and AI coding-agent users.

## Main scenario
“Across all available DHS rounds, compare Nigeria, Kenya, Uganda and Tanzania on childhood immunization indicators. Show missing years, warn where indicator definitions differ, and export a reproducible notebook and data dictionary.”

## P0 features
1. Public DHS country/survey/indicator catalog discovery.
2. Public aggregate indicator series retrieval with robust paging, bounded retries and local cache.
3. Country, survey year, indicator and disaggregation filters.
4. Original source metadata and provenance captured for each observation.
5. Null-aware normalization, duplicate handling and comparability warnings.
6. CSV, JSON, Excel and runnable notebook with local input data.
7. Local MCP server and CLI using same application services.
8. Reusable Claude Code and Codex skills, sample task and concise documentation.
9. Tests and CI.

## P1 after launch
Convenient batch extraction; user interface; WHO/World Bank context; indicator ontology; further visualizations.

## P2 future
Authorized local microdata and complex-survey methods; MICS and IPUMS interoperability; model-based estimation; forecasting; institutional hosting.

## Nonfunctional goals
Every reported number traceable to original public API record; no invented confidence bounds; no protected data scraping; reproducible offline demo; Windows support; no automatic telemetry; warnings always exported.

## Success measurement
At least 10 external beta testers; a successful full first-user install; three reproducible scientific examples; zero critical scientific/source-misrepresentation and security issues before public release.

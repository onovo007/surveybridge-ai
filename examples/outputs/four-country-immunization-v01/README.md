# SurveyBridge research bundle

The DHS Program Indicator Data API, The Demographic and Health Surveys (DHS) Program. ICF. Originally funded by the United States Agency for International Development (USAID). Available from https://api.dhsprogram.com/. See fetch_dates for access times. SurveyBridge AI is independent of The DHS Program.

Read limitations.md and comparability_report.md before use. observations.json preserves numeric types, nulls, and original records. Blank CSV cells represent nulls. CSV/Excel strings starting with formula characters receive a leading apostrophe; JSON/raw snapshots retain the source text. raw/ contains exact response bytes. provenance.json hashes all other bundle files except itself; SHA256SUMS includes provenance.json. Run analysis.ipynb from this directory with the installed SurveyBridge Python environment. The notebook verifies hashes and rebuilds normalization from archived responses without network access.

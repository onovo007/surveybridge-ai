# SSA research run

The DHS Program Indicator Data API, The Demographic and Health Surveys (DHS) Program. ICF. Originally funded by the United States Agency for International Development (USAID). Available from https://api.dhsprogram.com/. See fetch_dates for access times. SurveyBridge AI is independent of The DHS Program.

```json
{
  "countries": 42,
  "survey_rounds": 276,
  "observations": 837,
  "publications": 1321,
  "country_totals": {
    "AO": 15,
    "BF": 27,
    "BJ": 19,
    "BT": 4,
    "BU": 14,
    "CD": 14,
    "CF": 3,
    "CG": 9,
    "CI": 19,
    "CM": 24,
    "CV": 0,
    "EK": 0,
    "ER": 7,
    "ET": 21,
    "GA": 14,
    "GH": 34,
    "GM": 9,
    "GN": 21,
    "KE": 33,
    "KM": 7,
    "LB": 30,
    "LS": 18,
    "MD": 28,
    "ML": 34,
    "MR": 8,
    "MW": 35,
    "MZ": 23,
    "NG": 31,
    "NI": 19,
    "NM": 17,
    "RW": 44,
    "SL": 18,
    "SN": 59,
    "ST": 5,
    "SZ": 5,
    "TD": 13,
    "TG": 14,
    "TZ": 39,
    "UG": 36,
    "ZA": 9,
    "ZM": 32,
    "ZW": 26
  },
  "indicator_totals": {
    "CH_VACC_C_DP3": 170,
    "RH_ANCP_W_SKP": 593,
    "HA_HIVP_B_HIV": 74
  },
  "missing_estimates": 0,
  "availability_statuses": {
    "AVAILABLE_SURVEY_NO_INDICATOR_DATA": 373,
    "OBSERVED": 455
  },
  "completeness": {
    "completed": 126,
    "failed": 0,
    "indicator_extraction_complete": true,
    "pending": 0,
    "publication_discovery_complete": true,
    "tasks_total": 126
  },
  "exceptions": [],
  "warnings": [
    "Cross-survey comparability remains unverified; inspect per-indicator blocks, survey designs and population strata before comparing estimates",
    "Official report exists while API survey status is not Completed",
    "PDF cover date 2026-06 differs from catalog publication date 2026-07; both preserved"
  ]
}
```

Latest known report means latest dated record in the checked sources, not guaranteed latest in existence. Catalog dates can differ from PDF cover dates. Empty bounds are null, not estimated. No annual interpolation or causal/significance claims. Inspect country refresh errors, unmatched reports, and the comparison report before interpretation.

# Four-country childhood immunization demonstration

The implemented connector retrieved public national DHS aggregates on 31 October 2026 for Nigeria (`NG`), Kenya (`KE`), Uganda (`UG`) and Tanzania (`TZ`). Indicator IDs were selected from the official live catalog, not inferred from names:

| Indicator | Official ID | Retrieved observations |
|---|---|---:|
| DPT 3 vaccination received | CH_VACC_C_DP3 | 26 |
| BCG vaccination received | CH_VACC_C_BCG | 26 |
| Measles vaccination received | CH_VACC_C_MSL | 26 |

The complete [research bundle](outputs/four-country-immunization-v01/README.md) includes 78 source observations, original response snapshots, metadata catalogs, data dictionary, quality/availability/comparability reports, CSV, JSON, Excel, provenance and notebook. The [executed notebook](verification/analysis.executed.ipynb) is separate so original bundle hashes remain stable.

## Available DPT3 rounds

| Country | Principal survey years in the returned series |
|---|---|
| Nigeria | 1990, 2003, 2008, 2013, 2018, 2024 |
| Kenya | 1989, 1993, 1998, 2003, 2008, 2014, 2022 |
| Uganda | 1988, 1995, 2000, 2006, 2011, 2016 |
| Tanzania | 1992, 1996, 1999, 2004, 2010, 2015, 2022 |

Use `survey_year_label` and `survey_catalog.csv` for multi-year fieldwork (for example, Kenya 2008–09 and Tanzania 2015–16). Principal year is the API's field, not an imputed interview date. The broader completed catalog contains 53 surveys, including non-DHS types and rounds lacking these indicator records. `availability.csv` reports coverage at that survey/indicator grain; it does not invent records for inter-survey years.

## Latest retrieved DPT3 estimate per country

| Country | Survey ID | Value (%) | Original DataId |
|---|---|---:|---:|
| Nigeria | NG2024DHS | 53.4 | 713192 |
| Kenya | KE2022DHS | 89.2 | 797722 |
| Uganda | UG2016DHS | 78.6 | 765627 |
| Tanzania | TZ2022DHS | 90.0 | 616389 |

These are source values at different times, not a same-year ranking. Each value is verified against its original `Value`, `SurveyId`, `SurveyYear` and record hash in the exported raw responses. No confidence bounds are available for these observations. The denominator's “12–23 [or 24–35] months” wording means age equivalence requires survey-report review. The common indicator ID is insufficient to certify comparability.

Descriptive within-country differences can be inspected at observed rounds, but vaccine formulation, source of vaccination information, geography and age definitions must be checked before interpreting change. No significance tests, pooled indicators, causal conclusions or interpolated annual series are generated. The combined project blocks pooling across different indicators; assess each separately for descriptive review.

## Reproduce

With SurveyBridge installed:

```sh
python scripts/run_demo.py --output another-live-run
python scripts/run_demo.py --replay examples/outputs/four-country-immunization-v01/project.json --output offline-replay
```

Open `analysis.ipynb` from a bundle using the installed environment. The notebook checks every manifest checksum, verifies original records against response bytes, rebuilds normalized observations, and prints scientific warnings. It loads local files only. Output directories must be new.

Source: The DHS Program Indicator Data API, The Demographic and Health Surveys (DHS) Program, ICF. [Official API](https://api.dhsprogram.com/). Exact source URLs and UTC access times are in `provenance.json`.

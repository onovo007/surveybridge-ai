# Scientific release review 2 November 2026

## Decision and scope

The implemented workflow is scientifically acceptable for discovering official DHS publications, retrieving public aggregate observations, documenting availability and exporting source review bundles. The audit reproduced 837 SSA observations from 126 archived projects and the original 78 immunization observations. It did not establish that estimates from different surveys are equivalent. All three unrestricted SSA comparison blocks remain in force. A software review completed by the implementation agent is not independent human peer review.

This decision supports a scoped release candidate after engineering and host checks pass. It does not approve pooled SSA estimates, country outcome rankings, significance tests, annual interpolation or numerical extraction from report tables. Researchers must review survey-specific methods before publishing comparisons. External researcher acceptance remains a separate final release requirement from the original specifications.

## Verified data integrity

`scripts/review_scientific_release.py` checks every archived source response and catalog record hash, reconstructs normalization, checks all regional observations against child projects, rejects duplicate identities, and compares CSV values, confidence bounds, denominators, nulls and identifiers against JSON. It checks percentage ranges, confidence interval ordering and nonnegative source denominators. It also verifies 16 SSA output checksums, 25 source-code hashes and all 24 original beta output checksums. It refuses to overwrite its evidence file.

The recorded run found 837 SSA observations: 170 DPT3, 593 antenatal care and 74 HIV prevalence records. Of these, 74 have complete source confidence intervals. No estimate is missing and no true zero occurs in this particular retrieved set; deterministic regression tests separately cover null and zero behavior. These are counts of retrieved records, not sample sizes or independent estimates for meta-analysis. Some surveys contribute multiple strata.

Evidence: `examples/verification/release-2026-11-02/scientific_integrity_review.json` and `scientific_integrity_review_post_fix.json`. The latter verifies recorded source-code hashes against archived commit `4db6edf` and explicitly identifies the subsequent checkpoint-lock fix in `utils/cache.py`. Existing validated bundles were read, not changed. Successful reconstruction demonstrates fidelity to archived responses, not that the source publisher's estimates are error-free.

## Indicator interpretation

### Childhood vaccination

The DHS vaccination guide distinguishes ages, timing and ascertainment methods. The catalog's DPT3 denominator explicitly permits 12–23 or 24–35 months; shared indicator IDs therefore cannot establish a common population. Cards, caregiver reports, appropriate-age vaccination and vaccination before the survey are distinct concepts. Vaccine combinations and national schedules also require report review. The original Nigeria, Kenya, Uganda and Tanzania bundle remains a descriptive extraction demonstration, with its 78 source observations preserved. It is not a contemporaneous country ranking or a verified harmonized trend.

Official source: [DHS vaccination guidance](https://dhsprogram.com/data/Guide-to-DHS-Statistics/Vaccination.htm).

### Antenatal care

The official guide identifies a DHS-8 change in recall period from five to two years, expansion of pregnancy outcome populations, and changes in provider categories. The 593 API records must be separated by population stratum, recall window, country definition of skilled provider and survey round before comparison. The national endpoint does not remove population strata. The existing assessment correctly blocks the mixed regional extraction; users must not infer that selecting the same catalog ID resolves these changes.

Official source: [DHS antenatal care guidance](https://dhsprogram.com/data/Guide-to-DHS-Statistics/Antenatal_Care.htm).

### HIV prevalence

The official guidance distinguishes age and sex populations and documents changes in testing algorithms starting in 2015. Test participation, sample weighting, eligible ages and survey coverage affect interpretation. The 74 source-provided confidence intervals do not authorize causal inference or treating survey rounds as independent annual surveillance. The export retains original intervals; it does not calculate new ones.

Official source: [DHS HIV prevalence guidance](https://dhsprogram.com/data/Guide-to-DHS-Statistics/HIV_Prevalence.htm).

The three guide pages were retrieved successfully by the direct public client on 2 November 2026. Retrieval times and content hashes are in `method_sources.json` alongside the integrity evidence. A separate browsing service returned 403; that response did not prevent direct source review.

## Nigeria PR166 and publication history

The source-backed PR166 fixture and archived verification establish an official Nigeria Mini DHS 2025–26 Key Indicators Report. Catalog July 2026 and cover June 2026 are distinct publication evidence. PDF fieldwork 8 December 2025 to 15 February 2026 and API first-of-month dates are preserved separately. Official survey number 636 maps to NG2025DHS; the API's Ongoing label does not invalidate the existence of the official report. PR166's absence from the aggregate publication catalog demonstrates the need for publication-first discovery.

The software verifies bounded PDF front matter only. No report-derived estimate is presented as an API observation, final estimate or validated table extraction. Preliminary and final report versions remain separate; shared survey linkage does not infer numerical agreement or supersession. The global catalog's report-type label is metadata, not proof that every estimate inside a report has a particular finality.

Sources: [official catalog](https://dhsprogram.com/publications/publication-PR166-Preliminary-Reports-Key-Indicators-Reports.cfm), [official PDF](https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf), `docs/SSA_API_VERIFICATION.md`, source-backed fixtures PR166, PR167 and FR401.

## Coverage and release acceptance

The recorded snapshot resolves 42 DHS-covered SSA countries, 276 survey records and 1,321 publication metadata records. These counts describe the checked sources at recorded retrieval times; they are not permanent eligibility constants or a guarantee of every report in existence. No selected indicator observations is distinct from no survey, failed request, restricted microdata or a zero estimate. Metadata-only and unmatched reports remain visible.

Ready-for-review scientific scope is aggregate discovery, faithful extraction, metadata verification and reproducibility. Engineering acceptance still requires passing remote CI and the Claude Code natural-language test. A final production release additionally requires independent researcher acceptance as specified in the project documents. The PR must remain draft while the engineering checks are blocked; resolving them permits review of a scoped release candidate, not a claim that independent researcher acceptance has occurred.

## Host and CI verification completed

Both initial nine-job GitHub matrices passed after workflow authorization. The signed-in native Claude session loaded the skill and completed health, SSA-country and PR166 metadata calls. Review identified an unnecessary seasonality inference and an overinterpretation of mini/interim naming in its first response. The skill now explicitly prohibits inferring seasonality, methodological date precision or design conflict from these labels and values alone. A second host session passed with those unsupported interpretations removed. Evidence is under `examples/verification/release-2026-11-02/`. This completes the internal scoped host review; it does not change the external researcher acceptance requirement or authorize analytical comparisons previously blocked.

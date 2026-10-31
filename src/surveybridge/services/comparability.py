"""Conservative metadata checks; no imputation or inferential statistics."""

from surveybridge.models import ComparabilityFinding


def assess(project, indicator_ids=None):
    rows = project["observations"]
    if indicator_ids is not None:
        available = {r["id"] for r in project["indicators"]}
        if not indicator_ids or set(indicator_ids) - available:
            raise ValueError("Select indicator IDs present in this project")
        rows = [r for r in rows if r["indicator_id"] in indicator_ids]
    findings = []

    def add(severity, attribute, explanation, evidence, recommendation, keys=None):
        findings.append(
            ComparabilityFinding(
                severity=severity,
                affected_keys=keys or sorted({r["indicator_id"] for r in rows}),
                attribute=attribute,
                explanation=explanation,
                evidence=evidence,
                recommendation=recommendation,
            ).model_dump()
        )

    add(
        "caution",
        "design",
        "Repeated cross-sectional surveys do not constitute annual surveillance or causal evidence.",
        [],
        "Compare descriptively at observed survey rounds; do not interpolate missing years or infer significance.",
    )
    if not rows:
        add(
            "block",
            "availability",
            "No observations satisfy the request.",
            [],
            "Change filters or choose another catalog indicator.",
        )
    for field in ("unit", "definition", "denominator", "survey_year"):
        missing = [r["source_row_id"] for r in rows if r[field] is None]
        if missing:
            add(
                "block",
                field,
                f"Required comparison metadata {field} is missing.",
                missing,
                "Consult original survey documentation before comparing.",
            )
    indicators = sorted({r["indicator_id"] for r in rows})
    if len(indicators) > 1:
        add(
            "block",
            "indicator_id",
            "Different indicators must not be pooled as equivalent estimates.",
            indicators,
            "Keep indicator-specific series separate; review definitions before any harmonization.",
        )
    for indicator_id in indicators:
        group = [r for r in rows if r["indicator_id"] == indicator_id]
        for field in ("unit", "definition", "denominator"):
            values = sorted({str(r[field]) for r in group})
            if len(values) > 1:
                add(
                    "block",
                    field,
                    f"Conflicting {field} within an indicator.",
                    values,
                    "Resolve source metadata conflict before comparison.",
                    [indicator_id],
                )
        meta = " ".join(str(group[0].get(f) or "") for f in ("definition", "denominator"))
        if any(token in meta.lower() for token in ("[or", "(or", "24-35")):
            add(
                "caution",
                "population",
                "Catalog allows alternative age populations; survey-specific age equivalence is unverified.",
                [meta],
                "Check each survey report's vaccination denominator and age group before interpreting differences.",
                [indicator_id],
            )
        strata = {
            (
                r["breakdown_type"],
                r["breakdown_value"],
                r["by_variable_id"],
                r["region_id"],
                r["is_total"],
            )
            for r in group
        }
        if len(strata) > 1:
            add(
                "block",
                "disaggregation",
                "Multiple strata or geographies cannot be compared as one national series.",
                [str(s) for s in sorted(strata, key=str)],
                "Separate matching strata and review geography changes.",
                [indicator_id],
            )
        if any(r["value"] is None for r in group):
            add(
                "caution",
                "value",
                "Missing observations are present.",
                [],
                "Retain nulls and exclude from numeric comparisons.",
                [indicator_id],
            )
        if any(
            r["unit"] == "Percent" and r["value"] is not None and not 0 <= r["value"] <= 100
            for r in group
        ):
            add(
                "block",
                "range",
                "A percentage lies outside 0-100.",
                [],
                "Review the source; do not report this value.",
                [indicator_id],
            )
    for row in rows:
        lo, hi = row["lower_ci"], row["upper_ci"]
        if (
            lo is not None
            and hi is not None
            and (lo > hi or (row["value"] is not None and not lo <= row["value"] <= hi))
        ):
            add(
                "block",
                "confidence_interval",
                "Invalid source confidence interval.",
                [row["source_row_id"]],
                "Review source before interpretation.",
            )
    if any(r["lower_ci"] is None or r["upper_ci"] is None for r in rows):
        add(
            "caution",
            "confidence_interval",
            "Source confidence intervals are incomplete or absent.",
            [],
            "Do not invent confidence bounds or significance tests.",
        )
    if len({r["survey_year"] for r in rows}) > 1:
        add(
            "caution",
            "timing",
            "Estimates refer to different survey years and fieldwork periods.",
            sorted({str(r["survey_year_label"]) for r in rows}),
            "Show survey labels and fieldwork dates; avoid a same-year ranking.",
        )
    survey_map = {s["id"]: s for s in project["surveys"]}
    missing_surveys = sorted({r["source_survey_id"] for r in rows} - set(survey_map))
    if missing_surveys:
        add(
            "block",
            "survey_metadata",
            "Observation survey metadata is absent.",
            missing_surveys,
            "Retrieve the missing survey catalog records.",
        )
    if any(
        not survey_map.get(r["source_survey_id"], {}).get("fieldwork_start")
        or not survey_map.get(r["source_survey_id"], {}).get("fieldwork_end")
        for r in rows
    ):
        add(
            "caution",
            "fieldwork",
            "Some fieldwork dates are missing.",
            [],
            "Consult survey reports for exact periods.",
        )
    if len({r["survey_type"] for r in rows}) > 1:
        add(
            "block",
            "survey_type",
            "Different survey designs are present.",
            [],
            "Compare matching survey types separately.",
        )
    add(
        "caution",
        "definitions",
        "Shared catalog metadata does not verify survey-specific questionnaire, vaccine formulation, ascertainment or geographic coverage equivalence.",
        [],
        "Review source survey reports before publication; retain these limitations with estimates.",
    )
    return {
        "comparison_allowed": not any(f["severity"] == "block" for f in findings),
        "publication_comparability_verified": False,
        "findings": findings,
    }

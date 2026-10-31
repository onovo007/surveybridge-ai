"""Null-aware aggregate normalization and deterministic duplicate handling."""

import math

from surveybridge.models import Observation
from surveybridge.services.catalog import nullable


def number(value, warnings, field):
    if nullable(value) is None:
        return None
    try:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError
        return result
    except (TypeError, ValueError):
        warnings.append(f"Non-numeric source {field} retained in raw record; normalized to null")
        return None


def normalize(records, metadata):
    output, seen, duplicate_count = [], {}, 0
    for record in records:
        raw = record["raw"]
        key = str(raw["DataId"])
        if key in seen:
            if seen[key] != record["source_record_hash"]:
                raise ValueError(f"Conflicting source records for DataId {key}")
            duplicate_count += 1
            continue
        seen[key] = record["source_record_hash"]
        meta = metadata[raw["IndicatorId"]]
        warnings = []
        values = {
            name: number(raw.get(source), warnings, source)
            for name, source in {
                "value": "Value",
                "lower_ci": "CILow",
                "upper_ci": "CIHigh",
                "denominator_weighted": "DenominatorWeighted",
                "denominator_unweighted": "DenominatorUnweighted",
            }.items()
        }
        if values["value"] is None:
            warnings.append("Missing estimate; never interpret as zero")
        if values["lower_ci"] is None or values["upper_ci"] is None:
            warnings.append("Source does not provide a complete confidence interval")
        output.append(
            Observation(
                **record,
                source_row_id=key,
                source_country_id=raw["DHS_CountryCode"],
                source_country_name=raw["CountryName"],
                source_survey_id=raw["SurveyId"],
                survey_year=int(raw["SurveyYear"])
                if nullable(raw.get("SurveyYear")) is not None
                else None,
                survey_year_label=nullable(raw.get("SurveyYearLabel")),
                survey_type=nullable(raw.get("SurveyType")),
                indicator_id=raw["IndicatorId"],
                indicator_label=raw["Indicator"],
                unit=meta.unit,
                breakdown_type=nullable(raw.get("CharacteristicCategory")),
                breakdown_value=nullable(raw.get("CharacteristicLabel")),
                characteristic_id=str(raw["CharacteristicId"])
                if nullable(raw.get("CharacteristicId")) is not None
                else None,
                by_variable_id=str(raw["ByVariableId"])
                if nullable(raw.get("ByVariableId")) is not None
                else None,
                by_variable_label=nullable(raw.get("ByVariableLabel")),
                region_id=nullable(raw.get("RegionId")),
                is_total=bool(int(raw["IsTotal"]))
                if nullable(raw.get("IsTotal")) is not None
                else None,
                is_preferred=bool(int(raw["IsPreferred"]))
                if nullable(raw.get("IsPreferred")) is not None
                else None,
                definition=meta.definition,
                denominator=meta.denominator,
                precision=int(raw["Precision"])
                if nullable(raw.get("Precision")) is not None
                else None,
                warnings=warnings,
                **values,
            ).model_dump()
        )
    output.sort(
        key=lambda r: (
            r["source_country_id"],
            r["survey_year"] or 0,
            r["source_survey_id"],
            r["indicator_id"],
            r["source_row_id"],
        )
    )
    return output, duplicate_count

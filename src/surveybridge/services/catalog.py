"""Catalog validation and normalization shared by every interface."""

import re

from surveybridge.models import Country, Indicator, Survey


def nullable(value):
    return None if value is None or value == "" else value


def year_filters(from_year=None, to_year=None):
    for year in (from_year, to_year):
        if year is not None and (isinstance(year, bool) or not 1900 <= year <= 2100):
            raise ValueError("Years must be between 1900 and 2100")
    if from_year is not None and to_year is not None and from_year > to_year:
        raise ValueError("from_year must not exceed to_year")
    return {
        k: v
        for k, v in {"surveyYearStart": from_year, "surveyYearEnd": to_year}.items()
        if v is not None
    }


def country_codes(values):
    if not values or len(values) > 100 or any(not re.fullmatch(r"[A-Z]{2}", v) for v in values):
        raise ValueError("Supply 1-100 two-letter uppercase DHS country IDs")
    return sorted(set(values))


def country(record):
    raw = record["raw"]
    return Country(**record, id=raw["DHS_CountryCode"], name=raw["CountryName"])


def survey(record):
    raw = record["raw"]
    return Survey(
        **record,
        id=raw["SurveyId"],
        country_id=raw["DHS_CountryCode"],
        year=int(raw["SurveyYear"]) if nullable(raw.get("SurveyYear")) is not None else None,
        year_label=nullable(raw.get("SurveyYearLabel")),
        survey_type=nullable(raw.get("SurveyType")),
        fieldwork_start=nullable(raw.get("FieldworkStart")),
        fieldwork_end=nullable(raw.get("FieldworkEnd")),
    )


def indicator(record):
    raw = record["raw"]
    return Indicator(
        **record,
        id=raw["IndicatorId"],
        label=raw["Label"],
        definition=nullable(raw.get("Definition")),
        denominator=nullable(raw.get("Denominator")),
        unit=nullable(raw.get("MeasurementType")),
    )

"""Exact UN M49 SSA classification and source-provided DHS ISO3 joins."""

import json
from importlib.resources import files

from surveybridge.utils.cache import canonical, digest


class SSACountryResolver:
    def __init__(self, reference=None, crosswalk=None):
        self.reference = reference or json.loads(
            files("surveybridge.data")
            .joinpath("un_m49_ssa_2026-10-31.json")
            .read_text(encoding="utf-8")
        )
        self.crosswalk = crosswalk or {}

    def resolve(self, countries, surveys):
        reference = {r["iso3"]: r for r in self.reference["countries"]}
        by_iso3 = {}
        for record in countries:
            raw = record["raw"]
            iso3 = raw.get("ISO3_CountryCode") or self.crosswalk.get(raw["DHS_CountryCode"])
            if iso3 in reference:
                by_iso3.setdefault(iso3, []).append(record)
        survey_ids = {r["raw"]["DHS_CountryCode"] for r in surveys}
        rows, eligible, unmatched = [], [], []
        for iso3, area in sorted(reference.items()):
            matches = by_iso3.get(iso3, [])
            if not matches:
                unmatched.append(iso3)
                rows.append(
                    {
                        **area,
                        "country_id": None,
                        "country_name": area["un_name"],
                        "classification_status": "NO_DHS_COUNTRY_MATCH",
                    }
                )
                continue
            if len(matches) != 1:
                raise ValueError(
                    f"Ambiguous DHS ISO3 match for {iso3}; explicit reviewed crosswalk required"
                )
            record = matches[0]
            raw = record["raw"]
            country_id = raw["DHS_CountryCode"]
            supported = country_id in survey_ids
            rows.append(
                {
                    **area,
                    "country_id": country_id,
                    "country_name": raw["CountryName"],
                    "classification_status": "DHS_SURVEY_CONFIRMED"
                    if supported
                    else "DHS_COUNTRY_NO_SURVEY",
                    "match_method": "official_ISO3_CountryCode"
                    if raw.get("ISO3_CountryCode")
                    else "reviewed_crosswalk",
                    "source_url": record["source_url"],
                    "retrieved_utc": record["retrieved_utc"],
                    "source_record_hash": record["source_record_hash"],
                }
            )
            if supported:
                eligible.append(country_id)
        return {
            "country_ids": sorted(eligible),
            "country_count": len(eligible),
            "countries": rows,
            "unmatched_iso3": unmatched,
            "classification": {k: v for k, v in self.reference.items() if k != "countries"},
            "reference_hash": digest(canonical(self.reference)),
            "unmapped_dhs_codes": sorted(
                r["raw"]["DHS_CountryCode"]
                for r in countries
                if not r["raw"].get("ISO3_CountryCode")
                and r["raw"]["DHS_CountryCode"] not in self.crosswalk
            ),
        }

"""SSA survey and publication-first discovery with explicit source completeness."""

import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlencode, urlsplit

from surveybridge.clients.dhs import DHSError
from surveybridge.clients.official_web import OfficialWebClient, official_url
from surveybridge.geography import SSACountryResolver
from surveybridge.models import Result
from surveybridge.services.catalog import country, country_codes, survey, year_filters
from surveybridge.services.publication_html import (
    CatalogHTML,
    DetailHTML,
    publication_date,
    report_code,
)
from surveybridge.utils.cache import canonical, digest

SEARCH = "https://dhsprogram.com/publications/Publication-Search.cfm"
# Exact reviewed legacy display-name aliases, never fuzzy matching.
COUNTRY_ALIASES = {
    "Côte d'Ivoire": "Cote d'Ivoire",
    "Côte d’Ivoire": "Cote d'Ivoire",
    "Cabo Verde": "Cape Verde",
    "Eswatini": "Swaziland",
    "São Tomé and Príncipe": "Sao Tome and Principe",
}


def source_meta(record):
    return {
        k: record[k]
        for k in ("source_url", "retrieved_utc", "source_response_hash", "source_record_hash")
    }


def source_state(report, api_present=None, error=False):
    states = []
    if error:
        return ["API_RETRIEVAL_FAILED"]
    if api_present is True:
        states.append("API_INDICATOR_AVAILABLE")
    if report.get("download_verified") and api_present is False:
        states.append("OFFICIAL_REPORT_AVAILABLE_API_PENDING")
    if not report.get("download_verified"):
        states.append("REPORT_METADATA_ONLY")
    if report.get("dataset_access") == "restricted_or_unavailable_confirmed":
        states.append("DATASET_RESTRICTED_OR_UNAVAILABLE")
    return states


class DiscoveryService:
    def __init__(self, research, web=None):
        self.research = research
        self.client, self.settings = research.client, research.settings
        self.web = web or OfficialWebClient(self.settings)

    def selection(self, country_ids=None, region=None, from_year=None, to_year=None):
        years = year_filters(from_year, to_year)
        if region not in {None, "ssa"}:
            raise ValueError("Supported region is ssa")
        cp, sp = [], []
        countries, cp = self.client.fetch("countries")
        surveys, sp = self.client.fetch("surveys", {"surveyStatus": "all"})
        resolved = SSACountryResolver().resolve(countries, surveys) if region == "ssa" else None
        ids = (
            country_codes(country_ids)
            if country_ids is not None
            else resolved["country_ids"]
            if resolved
            else None
        )
        if ids is None:
            raise ValueError("Supply country_ids or region=ssa")
        known = {r["raw"]["DHS_CountryCode"] for r in countries}
        if set(ids) - known:
            raise ValueError("Unknown DHS country IDs")
        # Explicit countries override the regional selection, including non-SSA countries.
        selected_surveys = [
            r
            for r in surveys
            if r["raw"]["DHS_CountryCode"] in ids
            and (from_year is None or int(r["raw"]["SurveyYear"]) >= from_year)
            and (to_year is None or int(r["raw"]["SurveyYear"]) <= to_year)
        ]
        return {
            "country_ids": ids,
            "countries": [
                country(r).model_dump() for r in countries if r["raw"]["DHS_CountryCode"] in ids
            ],
            "surveys": [survey(r).model_dump() for r in selected_surveys],
            "all_surveys": [survey(r).model_dump() for r in surveys],
            "classification": resolved,
            "sources": self.research.sources(cp + sp),
            "year_filters": years,
            "selection_mode": "explicit_country_override"
            if country_ids is not None
            else "region_ssa",
        }

    def list_publications(
        self,
        country_ids=None,
        region="ssa",
        from_year=None,
        to_year=None,
        publication_type=None,
        publication_year=None,
        fieldwork_year=None,
        indicator_category=None,
        include_web=True,
        limit=500,
        return_all=False,
    ):
        self.research._limit(limit)
        selection = self.selection(country_ids, region, from_year, to_year)
        ids = selection["country_ids"]
        records, pages = (
            self.client.fetch("publications", {"countryIds": ",".join(ids)}) if ids else ([], [])
        )
        survey_map = {s["id"]: s for s in selection["all_surveys"]}
        reports, warnings, checks, sources = (
            {},
            [],
            [],
            selection["sources"] + self.research.sources(pages),
        )
        for record in records:
            raw = record["raw"]
            if raw.get("DHS_CountryCode") not in ids:
                raise ValueError("Publication endpoint returned an unrequested country")
            code = report_code(raw.get("PublicationURL", ""))
            key = (code, raw.get("PublicationURL"))
            reports[key] = {
                "report_id": code,
                "publication_id": str(raw["PublicationId"]),
                "title": raw.get("PublicationDescription") or raw.get("PublicationTitle"),
                "report_type": raw.get("PublicationTitle"),
                "country_id": raw["DHS_CountryCode"],
                "survey_id": raw.get("SurveyId") or None,
                "survey_year": int(raw["SurveyYear"]) if raw.get("SurveyYear") else None,
                "survey_type": raw.get("SurveyType"),
                "source_url": raw.get("PublicationURL"),
                "catalog_url": None,
                "publication_date": None,
                "publication_date_precision": None,
                "fieldwork_start": survey_map.get(raw.get("SurveyId"), {}).get("fieldwork_start"),
                "fieldwork_end": survey_map.get(raw.get("SurveyId"), {}).get("fieldwork_end"),
                "match_status": "canonical_api_survey_id"
                if raw.get("SurveyId") in survey_map
                else "unmatched_api_survey_id",
                "download_verified": False,
                "verification_status": "OFFICIAL_API_METADATA",
                "dataset_access": "unknown_not_queried",
                "source_history": [
                    {"kind": "aggregate_publication_catalog", **source_meta(record), "raw": raw}
                ],
                "warnings": [],
            }
        if include_web and ids:
            self._web_catalog(selection, reports, checks, sources, warnings, indicator_category)
        elif ids:
            checks = [{"country_id": c, "status": "WEB_DISCOVERY_NOT_REQUESTED"} for c in ids]
        rows = list(reports.values())
        for row in rows:
            s = survey_map.get(row.get("survey_id"), {})
            api_present = bool(s["raw"].get("IndicatorData")) if s else None
            row["api_availability_scope"] = "survey_catalog_any_indicator_not_requested_indicator"
            row["source_states"] = source_state(row, api_present)
            row["api_indicator_catalog_flag"] = api_present
            row["is_mini_dhs"] = bool(
                re.search(r"mini[\s-]*(?:dhs|demographic)", row.get("title") or "", re.I)
            )
            if row["is_mini_dhs"]:
                row["warnings"].append(
                    "Officially named abbreviated survey; verify design and coverage before comparison"
                )
        excluded_unknown_date = 0
        filtered = []
        for row in rows:
            if (
                publication_type
                and publication_type.casefold() not in (row.get("report_type") or "").casefold()
            ):
                continue
            if publication_year is not None and (row.get("publication_date") or "")[:4] != str(
                publication_year
            ):
                excluded_unknown_date += row.get("publication_date") is None
                continue
            if fieldwork_year is not None and not (
                row.get("fieldwork_start")
                and row.get("fieldwork_end")
                and row["fieldwork_start"][:4] <= str(fieldwork_year) <= row["fieldwork_end"][:4]
            ):
                continue
            if from_year is not None and (
                row.get("survey_year") is None or row["survey_year"] < from_year
            ):
                continue
            if to_year is not None and (
                row.get("survey_year") is None or row["survey_year"] > to_year
            ):
                continue
            if indicator_category and not row.get("official_topic_match"):
                continue
            filtered.append(row)
        rows = sorted(
            filtered,
            key=lambda r: (
                r.get("publication_date") or "",
                r.get("report_id") or "",
                r.get("source_url") or "",
            ),
            reverse=True,
        )
        if excluded_unknown_date:
            warnings.append(
                f"Publication-year filter excluded {excluded_unknown_date} records with unknown publication dates"
            )
        complete = (
            include_web
            and all(c["status"] == "checked" for c in checks)
            and len(checks) == len(ids)
        )
        if not complete:
            warnings.append(
                "Source discovery incomplete; inspect per-country refresh failures and caps"
            )
        data = {
            "publications": rows if return_all else rows[:limit],
            "country_checks": checks,
            "selection": selection,
            "latest_by_country": latest_by_country(rows, ids),
            "lineage": lineage(rows),
            "source_completeness": {
                "api_catalog_complete": True,
                "official_web_scan_complete": complete,
                "claim": "Known records from checked official sources; no guarantee that all country-led releases are indexed",
                "last_checked_utc": datetime.now(UTC).isoformat(),
            },
        }
        return Result(
            data=data,
            warnings=warnings,
            source=sources,
            truncated=not return_all and len(rows) > limit,
            pagination={
                "matched": len(rows),
                "returned": len(rows) if return_all else min(len(rows), limit),
            },
        )

    def _web_catalog(self, selection, reports, checks, sources, warnings, indicator_category):
        try:
            body, src = self.web.get(SEARCH)
            index = CatalogHTML(SEARCH)
            index.feed(body.decode("utf-8", errors="replace"))
            if not index.options:
                raise DHSError("Official publication country selector schema changed")
            sources.append(src)
            topic = None
            if indicator_category:
                options = index.options_by_select.get("topic1", {})
                matched = [
                    v
                    for k, v in options.items()
                    if k.casefold() == indicator_category.casefold() and v
                ]
                if len(matched) != 1:
                    raise ValueError(
                        "Unknown official publication topic; choose an exact topic label from the official publication-search selector"
                    )
                topic = matched[0]
        except (ValueError, DHSError) as exc:
            checks.extend(
                {"country_id": c, "status": "SOURCE_UNVERIFIED", "error": str(exc)}
                for c in selection["country_ids"]
            )
            return
        for c in selection["countries"]:
            name = COUNTRY_ALIASES.get(c["name"], c["name"])
            country_number = index.options.get(c["name"]) or index.options.get(name)
            if not country_number:
                checks.append(
                    {
                        "country_id": c["id"],
                        "status": "UNMATCHED_OFFICIAL_COUNTRY_SELECTOR",
                        "country_name": c["name"],
                    }
                )
                continue
            params = {"country1": country_number, "shareurl": "yes"}
            if topic:
                params["topic1"] = topic
            url = SEARCH + "?" + urlencode(params)
            queue, visited, count, error = [url], set(), 0, None
            while queue:
                current = queue.pop(0)
                query = {k.lower(): v for k, v in parse_qs(urlsplit(current).query).items()}
                signature = (
                    tuple(query.get("country1", [])),
                    tuple(query.get("pubtypelogid", [])),
                    tuple(query.get("showall", [])),
                    tuple(query.get("topic1", [])),
                )
                if signature in visited:
                    continue
                visited.add(signature)
                try:
                    body, src = self.web.get(current)
                    parser = CatalogHTML(current)
                    parser.feed(body.decode("utf-8", errors="replace"))
                    if not parser.rows and not any(
                        s in body.decode("utf-8", errors="replace").lower()
                        for s in ("no results", "no publications", "no records", "no documents")
                    ):
                        raise DHSError(
                            "Official country publication page has no recognized results or explicit empty state"
                        )
                    sources.append(src)
                    for follow in parser.follow:
                        follow_query = {
                            k.lower(): v for k, v in parse_qs(urlsplit(follow).query).items()
                        }
                        if follow_query.get("country1") == [country_number]:
                            queue.append(follow)
                    for row in parser.rows:
                        existing_keys = [
                            k
                            for k in reports
                            if k[0] == row["report_id"] and reports[k]["country_id"] == c["id"]
                        ]
                        key = (
                            existing_keys[0]
                            if existing_keys
                            else (row["report_id"], row["catalog_url"])
                        )
                        old = reports.get(key, {})
                        if old and old.get("catalog_url") == row["catalog_url"]:
                            continue
                        record = {
                            **old,
                            **row,
                            "country_id": c["id"],
                            "source_url": old.get("source_url"),
                            "source_history": old.get("source_history", [])
                            + [
                                {
                                    "kind": "official_publication_search",
                                    **src,
                                    "record_hash": digest(canonical(row)),
                                    "metadata": row,
                                }
                            ],
                            "download_verified": old.get("download_verified", False),
                            "verification_status": "OFFICIAL_CATALOG_METADATA",
                            "dataset_access": "unknown_not_queried",
                            "warnings": old.get("warnings", []),
                        }
                        core_report = any(
                            t in (row.get("report_type") or "").casefold()
                            for t in ("final report", "preliminary", "key indicator", "interim")
                        )
                        if core_report and (not old or not record.get("survey_id")):
                            record = self._detail(
                                record, selection["all_surveys"], verify_pdf=False
                            )
                        if indicator_category:
                            record["official_topic_match"] = indicator_category
                        reports[key] = record
                        count += 1
                except (DHSError, ValueError) as exc:
                    error = str(exc)
                    break
            checks.append(
                {
                    "country_id": c["id"],
                    "status": "checked" if error is None else "SOURCE_UNVERIFIED",
                    "pages": len(visited),
                    "new_or_enriched_records": count,
                    "error": error,
                    "last_successful_refresh_utc": datetime.now(UTC).isoformat()
                    if error is None
                    else None,
                }
            )
        if any(c["status"] != "checked" for c in checks):
            warnings.append(
                "Some country catalogs were not fully checked; no absent-country conclusion is justified"
            )

    def _detail(self, report, surveys, verify_pdf=False):
        report = dict(report)
        report.setdefault("warnings", [])
        if report.get("catalog_url"):
            body, src = self.web.get(report["catalog_url"])
            parser = DetailHTML(report["catalog_url"])
            parser.feed(body.decode("utf-8", errors="replace"))
            code = parser.fields.get("Publication ID")
            if code and code.upper() != report["report_id"]:
                raise DHSError("Official detail page report ID disagrees with requested report")
            pdfs = [
                u
                for u in parser.links
                if urlsplit(u).path.lower().endswith(".pdf")
                and report_code(u) == report["report_id"]
            ]
            if pdfs:
                report["source_url"] = official_url(pdfs[0])
            date, precision = publication_date(parser.fields.get("Publication Date"))
            if date:
                report.update(publication_date=date, publication_date_precision=precision)
            report["report_type"] = parser.fields.get("Document Type") or report.get("report_type")
            links = [re.search(r"survey-display-(\d+)\.cfm", u, re.I) for u in parser.links]
            numbers = {int(m[1]) for m in links if m}
            matches = [
                s
                for s in surveys
                if s["raw"].get("SurveyNum") in numbers
                and s["country_id"] == report.get("country_id")
            ]
            if len(matches) == 1:
                s = matches[0]
                report.update(
                    survey_id=s["id"],
                    survey_year=s["year"],
                    survey_type=s["survey_type"],
                    fieldwork_start=s["fieldwork_start"],
                    fieldwork_end=s["fieldwork_end"],
                    match_status="official_survey_number_join",
                )
                if s["raw"].get("SurveyStatus", "").lower() != "completed":
                    report["warnings"].append(
                        "Official report exists while API survey status is not Completed"
                    )
            elif not report.get("survey_id"):
                report.update(
                    survey_id=None, match_status="ambiguous" if len(matches) > 1 else "unmatched"
                )
            report.setdefault("source_history", []).append(
                {"kind": "official_publication_detail", **src, "metadata": parser.fields}
            )
        if verify_pdf and report.get("source_url"):
            try:
                body, src = self.web.get(report["source_url"], pdf=True)
                from surveybridge.services.report_verification import inspect_pdf

                report["pdf_verification"] = inspect_pdf(body)
                report["download_verified"] = True
                report["verification_status"] = "OFFICIAL_PDF_VERIFIED_NO_ESTIMATES_EXTRACTED"
                report.setdefault("source_history", []).append({"kind": "official_pdf", **src})
                cover_date = report["pdf_verification"].get("cover_date")
                if (
                    cover_date
                    and report.get("publication_date")
                    and cover_date != report["publication_date"]
                ):
                    report["warnings"].append(
                        f"PDF cover date {cover_date} differs from catalog publication date {report['publication_date']}; both preserved"
                    )
            except (DHSError, ValueError, ImportError) as exc:
                report["verification_status"] = "SOURCE_UNVERIFIED"
                report["warnings"].append(str(exc))
        return report

    def get_report_metadata(self, report_url, verify_pdf=False):
        official_url(report_url)
        code = report_code(report_url)
        if code is None:
            raise ValueError(
                "Supply a public DHS publication or PDF URL containing its report identifier"
            )
        selection = self.selection(region="ssa")
        search = SEARCH + "?" + urlencode({"pubid1": code, "shareurl": "yes"})
        base = {
            "report_id": code,
            "source_url": report_url if report_url.lower().endswith(".pdf") else None,
            "catalog_url": report_url if not report_url.lower().endswith(".pdf") else None,
            "source_history": [],
            "warnings": [],
            "country_id": None,
        }
        try:
            body, src = self.web.get(search)
            parser = CatalogHTML(search)
            parser.feed(body.decode("utf-8", errors="replace"))
            candidates = [r for r in parser.rows if r["report_id"] == code]
            if len({r["catalog_url"] for r in candidates}) == 1:
                base.update(candidates[0])
            if base.get("catalog_url"):
                # Establish country from the exact official country-page ID, not report-title guesses.
                body, _ = self.web.get(base["catalog_url"])
                detail = DetailHTML(base["catalog_url"])
                detail.feed(body.decode("utf-8", errors="replace"))
                country_name = detail.fields.get("Country(s)")
                matches = [
                    c["id"]
                    for c in selection["countries"]
                    if c["name"] == country_name or COUNTRY_ALIASES.get(c["name"]) == country_name
                ]
                if len(matches) == 1:
                    base["country_id"] = matches[0]
                base["source_history"].append({"kind": "official_report_search", **src})
            report = self._detail(base, selection["all_surveys"], verify_pdf)
        except (DHSError, ValueError) as exc:
            report = {**base, "verification_status": "SOURCE_UNVERIFIED", "warnings": [str(exc)]}
        survey_map = {s["id"]: s for s in selection["all_surveys"]}
        linked = survey_map.get(report.get("survey_id"))
        flag = bool(linked["raw"].get("IndicatorData")) if linked else None
        report["source_states"] = source_state(report, flag)
        report["api_availability_scope"] = "survey_catalog_any_indicator_not_requested_indicator"
        return Result(data=report, warnings=report["warnings"], source=report["source_history"])


def latest_by_country(reports, country_ids):
    result = []
    for country_id in country_ids:
        group = [r for r in reports if r["country_id"] == country_id]
        dated = [
            r
            for r in group
            if r.get("publication_date")
            and any(
                t in (r.get("report_type") or "").casefold()
                for t in ("final", "preliminary", "key indicator", "interim")
            )
        ]
        latest = (
            max(dated, key=lambda r: (r["publication_date"], r.get("report_id") or ""))
            if dated
            else None
        )
        result.append(
            {
                "country_id": country_id,
                "latest_known_report": latest,
                "publication_records": len(group),
                "unknown_publication_dates": sum(not r.get("publication_date") for r in group),
                "latest_fieldwork_end": max(
                    (r.get("fieldwork_end") or "" for r in group), default=""
                )
                or None,
            }
        )
    return result


def lineage(reports):
    groups = {}
    for r in reports:
        key = r.get("survey_id") or f"unmatched:{r['country_id']}:{r['report_id']}"
        groups.setdefault(key, []).append(
            {
                "report_id": r["report_id"],
                "source_url": r.get("source_url"),
                "report_type": r.get("report_type"),
                "publication_date": r.get("publication_date"),
                "source_states": r.get("source_states"),
                "estimate_extraction": "not_performed",
            }
        )
    return {
        key: {
            "sources": values,
            "relationship": "needs_reconciliation" if len(values) > 1 else "single_source",
            "estimate_preference": "No report-derived estimates; never count versions as independent observations",
        }
        for key, values in groups.items()
    }

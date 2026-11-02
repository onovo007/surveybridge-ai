"""Persistent research projects shared across CLI invocations and MCP sessions."""

import json
import re
import uuid

from surveybridge import __version__
from surveybridge.clients.dhs import DHSClient
from surveybridge.config import Settings
from surveybridge.models import Result
from surveybridge.services.catalog import country, country_codes, indicator, survey, year_filters
from surveybridge.services.comparability import assess
from surveybridge.services.series import normalize
from surveybridge.utils.cache import atomic_json


class ResearchService:
    def __init__(self, settings: Settings | None = None, client=None):
        self.settings = settings or Settings()
        self.client = client or DHSClient(self.settings)

    def close(self):
        self.client.close()

    def list_publications(self, **kwargs):
        from surveybridge.services.discovery import DiscoveryService

        discovery = DiscoveryService(self)
        try:
            return discovery.list_publications(**kwargs)
        finally:
            discovery.web.close()

    def get_report_metadata(self, report_url, verify_pdf=False):
        from surveybridge.services.discovery import DiscoveryService

        discovery = DiscoveryService(self)
        try:
            return discovery.get_report_metadata(report_url, verify_pdf)
        finally:
            discovery.web.close()

    def run_regional_project(self, **kwargs):
        from surveybridge.services.regional import RegionalService

        return RegionalService(self).run(**kwargs)

    def export_regional_project(self, run_id, output_dir):
        from surveybridge.services.regional import RegionalService
        from surveybridge.services.regional_export import export_regional

        run = RegionalService(self).load(run_id)
        path = export_regional(run, output_dir, self.settings)
        return Result(
            data={"run_id": run_id, "path": str(path), "completeness": run["completeness"]},
            warnings=run["warnings"],
        )

    @staticmethod
    def sources(pages):
        return [{k: v for k, v in page.items() if k != "body_hex"} for page in pages]

    def healthcheck(self):
        return Result(
            data={
                "version": __version__,
                "transport": "stdio",
                "remote_checked": False,
                "offline": self.settings.offline,
                "source": self.settings.base_url,
            }
        )

    def list_countries(self, query=None, limit=100, region=None):
        if region is not None:
            from surveybridge.services.discovery import DiscoveryService

            discovery = DiscoveryService(self)
            try:
                selected = discovery.selection(region=region)
            finally:
                discovery.web.close()
            rows = [
                r
                for r in selected["classification"]["countries"]
                if r["country_id"] in selected["country_ids"]
            ]
            if query:
                rows = [
                    r
                    for r in rows
                    if query.casefold() in (r["country_name"] + " " + r["country_id"]).casefold()
                ]
            self._limit(limit)
            return Result(
                data=rows[:limit],
                source=selected["sources"],
                truncated=len(rows) > limit,
                pagination={
                    "matched": len(rows),
                    "returned": min(len(rows), limit),
                    "classification": selected["classification"],
                },
            )
        self._limit(limit)
        records, pages = self.client.fetch("countries")
        rows = [country(r).model_dump() for r in records]
        if query:
            rows = [r for r in rows if query.casefold() in (r["id"] + " " + r["name"]).casefold()]
        return Result(
            data=rows[:limit],
            source=self.sources(pages),
            truncated=len(rows) > limit,
            pagination={"matched": len(rows), "returned": min(len(rows), limit)},
        )

    def _countries(self, ids):
        ids = country_codes(ids)
        records, pages = self.client.fetch("countries", {"countryIds": ",".join(ids)})
        rows = [country(r).model_dump() for r in records]
        if set(ids) != {r["id"] for r in rows}:
            raise ValueError("Unknown or unavailable DHS country ID")
        return ids, rows, pages

    def list_surveys(self, country_ids=None, from_year=None, to_year=None, region=None):
        if region is not None:
            from surveybridge.services.discovery import DiscoveryService

            discovery = DiscoveryService(self)
            try:
                selected = discovery.selection(country_ids, region, from_year, to_year)
            finally:
                discovery.web.close()
            return Result(
                data=selected["surveys"],
                source=selected["sources"],
                pagination={
                    "returned": len(selected["surveys"]),
                    "selection_mode": selected["selection_mode"],
                },
            )
        years = year_filters(from_year, to_year)
        ids, _, cp = self._countries(country_ids)
        records, pages = self.client.fetch(
            "surveys", {"countryIds": ",".join(ids), "surveyStatus": "completed", **years}
        )
        rows = [survey(r).model_dump() for r in records]
        return Result(
            data=rows, source=self.sources(cp + pages), pagination={"returned": len(rows)}
        )

    def search_indicators(self, query, limit=20):
        self._limit(limit)
        if not query or not query.strip() or len(query) > 200:
            raise ValueError("Supply an indicator search query of 1-200 characters")
        records, pages = self.client.fetch("indicators")
        words = query.casefold().split()
        rows = [indicator(r).model_dump() for r in records]
        rows = [
            r
            for r in rows
            if all(
                w
                in " ".join(
                    str(r[k] or "") for k in ("id", "label", "definition", "denominator")
                ).casefold()
                for w in words
            )
        ]
        return Result(
            data=rows[:limit],
            source=self.sources(pages),
            truncated=len(rows) > limit,
            pagination={"matched": len(rows), "returned": min(len(rows), limit)},
        )

    @staticmethod
    def _limit(limit):
        if isinstance(limit, bool) or not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")

    def load(self, project_id):
        if not re.fullmatch(r"[a-f0-9]{32}", project_id):
            raise ValueError("Invalid project ID")
        path = self.settings.workspace / "projects" / f"{project_id}.json"
        if not path.is_file():
            raise ValueError("Project not found in this workspace")
        return json.loads(path.read_text(encoding="utf-8"))

    def get_indicator_series(
        self,
        indicator_id,
        country_ids=None,
        from_year=None,
        to_year=None,
        breakdown="national",
        project_id=None,
        region=None,
    ):
        if region is not None:
            from surveybridge.services.discovery import DiscoveryService

            discovery = DiscoveryService(self)
            try:
                country_ids = discovery.selection(country_ids, region)["country_ids"]
            finally:
                discovery.web.close()
        if not re.fullmatch(r"[A-Za-z0-9_]{1,80}", indicator_id):
            raise ValueError("Invalid indicator ID; select one from the official catalog")
        if breakdown not in {"national", "subnational", "background", "all"}:
            raise ValueError("Unsupported DHS breakdown")
        years = year_filters(from_year, to_year)
        ids, countries, cp = self._countries(country_ids)
        ir, ip = self.client.fetch("indicators", {"indicatorIds": indicator_id})
        indicators = [indicator(r) for r in ir]
        if len(indicators) != 1 or indicators[0].id != indicator_id:
            raise ValueError("Indicator ID not found uniquely in the official catalog")
        sr, sp = self.client.fetch(
            "surveys", {"countryIds": ",".join(ids), "surveyStatus": "completed", **years}
        )
        params = {
            "indicatorIds": indicator_id,
            "countryIds": ",".join(ids),
            "breakdown": breakdown,
            **years,
        }
        records, pages = self.client.fetch("data", params)
        if any(
            r["raw"].get("IndicatorId") != indicator_id
            or r["raw"].get("DHS_CountryCode") not in ids
            for r in records
        ):
            raise ValueError("Source returned records outside requested country/indicator filters")
        rows, duplicates = normalize(records, {i.id: i for i in indicators})
        if any(
            (
                from_year is not None
                and r["survey_year"] is not None
                and r["survey_year"] < from_year
            )
            or (to_year is not None and r["survey_year"] is not None and r["survey_year"] > to_year)
            for r in rows
        ):
            raise ValueError("Source returned observations outside requested years")
        project = {
            "project_id": uuid.uuid4().hex,
            "queries": [params],
            "countries": countries,
            "indicators": [i.model_dump() for i in indicators],
            "surveys": [survey(r).model_dump() for r in sr],
            "observations": rows,
            "pages": cp + ip + sp + pages,
            "transformations": [
                "Empty source fields mapped to null; numeric zero preserved; original rows retained.",
                f"Removed {duplicates} exact repeated DataIds; conflicting duplicates fail extraction.",
            ],
        }
        if project_id:
            existing = self.load(project_id)
            if any(
                q["countryIds"] != params["countryIds"]
                or q.get("surveyYearStart") != params.get("surveyYearStart")
                or q.get("surveyYearEnd") != params.get("surveyYearEnd")
                or q["breakdown"] != breakdown
                for q in existing["queries"]
            ):
                raise ValueError("Append requires identical country/year/breakdown scope")
            if indicator_id in {i["id"] for i in existing["indicators"]}:
                raise ValueError(
                    "Indicator already exists in project; retrieve into a new project to refresh"
                )
            for field in ("queries", "indicators", "observations", "pages", "transformations"):
                project[field] = existing[field] + project[field]
            # Append creates a new immutable snapshot, preserving original projects.
        project["assessment"] = assess(project)
        atomic_json(self.settings.workspace / "projects" / f"{project['project_id']}.json", project)
        warnings = [f["explanation"] for f in project["assessment"]["findings"]]
        return Result(
            data={
                "project_id": project["project_id"],
                "observation_count": len(project["observations"]),
                "observations": project["observations"][:500],
                "assessment": project["assessment"],
            },
            warnings=warnings,
            source=self.sources(project["pages"]),
            truncated=len(project["observations"]) > 500,
            pagination={
                "stored": len(project["observations"]),
                "returned": min(len(project["observations"]), 500),
            },
        )

    def assess_comparability(self, project_id, indicator_ids=None):
        project = self.load(project_id)
        report = assess(project, indicator_ids)
        return Result(
            status="ok" if report["comparison_allowed"] else "blocked",
            data=report,
            warnings=[f["explanation"] for f in report["findings"]],
            source=self.sources(project["pages"]),
        )

    def export_project(self, project_id, output_dir, formats=None):
        from surveybridge.services.export import export_project

        project = self.load(project_id)
        path = export_project(
            project, output_dir, formats or ["csv", "json", "xlsx", "notebook"], self.settings
        )
        return Result(
            data={"project_id": project_id, "path": str(path)},
            warnings=[f["explanation"] for f in project["assessment"]["findings"]],
            source=self.sources(project["pages"]),
        )

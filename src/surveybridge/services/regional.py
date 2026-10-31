"""Checkpointed explicit-indicator regional research; failed requests never become no-data."""

import json
import re
import uuid
from datetime import UTC, datetime

from surveybridge.models import Result
from surveybridge.services.catalog import year_filters
from surveybridge.services.discovery import (
    DiscoveryService,
    latest_by_country,
    lineage,
    source_state,
)
from surveybridge.utils.cache import atomic_json, canonical, digest

PR166 = "https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf"


class RegionalService:
    def __init__(self, research):
        self.research = research
        self.settings = research.settings

    def load(self, run_id):
        if not re.fullmatch(r"[a-f0-9]{32}", run_id):
            raise ValueError("Invalid regional run ID")
        path = self.settings.workspace / "regional-runs" / f"{run_id}.json"
        if not path.is_file():
            raise ValueError("Regional run not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, run):
        run["updated_utc"] = datetime.now(UTC).isoformat()
        atomic_json(self.settings.workspace / "regional-runs" / f"{run['run_id']}.json", run)

    def run(
        self,
        indicator_ids=None,
        country_ids=None,
        region="ssa",
        from_year=None,
        to_year=None,
        all_available_rounds=True,
        run_id=None,
        max_tasks=None,
        include_publications=True,
        refresh_publications=False,
    ):
        year_filters(from_year, to_year)
        if not all_available_rounds and from_year is None and to_year is None and not run_id:
            raise ValueError("Choose all_available_rounds or an explicit year range")
        if indicator_ids is not None and (
            len(indicator_ids) > 100
            or len(set(indicator_ids)) != len(indicator_ids)
            or any(not re.fullmatch(r"[A-Za-z0-9_]{1,80}", i) for i in indicator_ids)
        ):
            raise ValueError(
                "Supply at most 100 distinct official indicator IDs; no implicit indicator set"
            )
        budget = max_tasks if max_tasks is not None else self.settings.max_batch_tasks
        if not 1 <= budget <= self.settings.max_batch_tasks:
            raise ValueError("max_tasks exceeds configured per-invocation budget")
        if run_id:
            run = self.load(run_id)
            if indicator_ids is not None and indicator_ids != run["filters"]["indicator_ids"]:
                raise ValueError("Resume indicator filters differ from checkpoint")
            if country_ids is not None and sorted(country_ids) != sorted(
                run["selection"]["country_ids"]
            ):
                raise ValueError("Resume country filters differ from checkpoint")
            for field, value in (("from_year", from_year), ("to_year", to_year)):
                if value is not None and value != run["filters"][field]:
                    raise ValueError("Resume year filters differ from checkpoint")
        else:
            discovery = DiscoveryService(self.research)
            try:
                selection = discovery.selection(country_ids, region, from_year, to_year)
            finally:
                discovery.web.close()
            requested = indicator_ids or []
            # Verify every exact identifier before beginning a potentially large extraction.
            for indicator_id in requested:
                records, _ = self.research.client.fetch(
                    "indicators", {"indicatorIds": indicator_id}
                )
                if len(records) != 1 or records[0]["raw"].get("IndicatorId") != indicator_id:
                    raise ValueError(f"Official catalog does not uniquely contain {indicator_id}")
            run = {
                "run_id": uuid.uuid4().hex,
                "created_utc": datetime.now(UTC).isoformat(),
                "filters": {
                    "region": region,
                    "indicator_ids": requested,
                    "country_ids": country_ids,
                    "from_year": from_year,
                    "to_year": to_year,
                    "all_available_rounds": all_available_rounds,
                },
                "selection": selection,
                "tasks": [],
                "publications": None,
                "warnings": [],
                "completeness": {},
                "execution": {
                    "concurrency": 1,
                    "batch_grain": "one_country_one_indicator",
                    "max_tasks_per_invocation": budget,
                },
            }
            for country_id in selection["country_ids"]:
                for indicator_id in requested:
                    run["tasks"].append(
                        {
                            "country_id": country_id,
                            "indicator_id": indicator_id,
                            "status": "pending",
                            "attempts": 0,
                            "project_id": None,
                            "error": None,
                        }
                    )
            run["selection_hash"] = digest(canonical(selection))
            self.save(run)
        if include_publications and (run["publications"] is None or refresh_publications):
            discovery = DiscoveryService(self.research)
            try:
                result = discovery.list_publications(
                    country_ids=run["selection"]["country_ids"], region=region, return_all=True
                )
                run["publications"] = {
                    "data": result.data,
                    "warnings": result.warnings,
                    "source": result.source,
                }
                if "NG" in run["selection"]["country_ids"]:
                    verified = discovery.get_report_metadata(PR166, verify_pdf=True)
                    report = verified.data
                    reports = run["publications"]["data"]["publications"]
                    matches = [
                        r for r in reports if r["report_id"] == "PR166" and r["country_id"] == "NG"
                    ]
                    if matches:
                        matches[0].update(report)
                    else:
                        reports.append(report)
                    run["mandatory_report_verification"] = report
                self.save(run)
            finally:
                discovery.web.close()
        attempted = 0
        for task in run["tasks"]:
            if task["status"] == "completed":
                continue
            if attempted >= budget:
                break
            attempted += 1
            task["attempts"] += 1
            task["status"], task["error"] = "running", None
            self.save(run)
            try:
                result = self.research.get_indicator_series(
                    task["indicator_id"],
                    [task["country_id"]],
                    from_year=run["filters"]["from_year"],
                    to_year=run["filters"]["to_year"],
                )
                task.update(
                    status="completed",
                    project_id=result.data["project_id"],
                    observation_count=result.data["observation_count"],
                )
            except (RuntimeError, ValueError, OSError, KeyError) as exc:
                task.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            self.save(run)
        complete = sum(t["status"] == "completed" for t in run["tasks"])
        failed = sum(t["status"] == "failed" for t in run["tasks"])
        run["completeness"] = {
            "tasks_total": len(run["tasks"]),
            "completed": complete,
            "failed": failed,
            "pending": len(run["tasks"]) - complete - failed,
            "indicator_extraction_complete": complete == len(run["tasks"]),
            "publication_discovery_complete": bool(
                run["publications"]
                and run["publications"]["data"]["source_completeness"]["official_web_scan_complete"]
            ),
        }
        run["warnings"] = (
            list(run["publications"]["warnings"])
            if run["publications"]
            else ["Publication discovery not requested"]
        )
        if complete != len(run["tasks"]):
            run["warnings"].append(
                "PARTIAL EXTRACTION: failed/pending tasks are not evidence of absent observations; resume this run"
            )
        if not run["filters"]["indicator_ids"]:
            run["warnings"].append(
                "Metadata-only discovery: numerical indicator availability was not tested"
            )
        if (
            run.get("mandatory_report_verification", {}).get("verification_status")
            == "SOURCE_UNVERIFIED"
        ):
            run["warnings"].append(
                "Mandatory PR166 verification incomplete; comprehensive release gate not met"
            )
        run["warnings"].append(
            "Cross-survey comparability remains unverified; inspect per-indicator blocks, survey designs and population strata before comparing estimates"
        )
        run["warnings"].extend(run.get("mandatory_report_verification", {}).get("warnings", []))
        self.save(run)
        return Result(
            data={
                "run_id": run["run_id"],
                "country_count": len(run["selection"]["country_ids"]),
                "survey_rounds": len(run["selection"]["surveys"]),
                "progress": run["completeness"],
                "requested_indicator_ids": run["filters"]["indicator_ids"],
                "observation_count": sum(
                    t.get("observation_count", 0)
                    for t in run["tasks"]
                    if t["status"] == "completed"
                ),
            },
            warnings=run["warnings"],
            source=run["selection"]["sources"],
        )

    def materialize(self, run):
        projects, rows, availability = [], [], []
        for task in run["tasks"]:
            if task["status"] == "completed":
                project = self.research.load(task["project_id"])
                from surveybridge.services.provenance import verify_project

                verify_project(project)
                projects.append(project)
                rows.extend(project["observations"])
            else:
                project = None
            for s in run["selection"]["surveys"]:
                if s["country_id"] != task["country_id"]:
                    continue
                observations = [
                    r
                    for r in (project["observations"] if project else [])
                    if r["source_survey_id"] == s["id"]
                ]
                if task["status"] != "completed":
                    status = (
                        "API_RETRIEVAL_FAILED" if task["status"] == "failed" else "PENDING_REQUEST"
                    )
                elif not observations:
                    status = "AVAILABLE_SURVEY_NO_INDICATOR_DATA"
                elif all(r["value"] is None for r in observations):
                    status = "MISSING_ESTIMATE"
                else:
                    status = "OBSERVED"
                availability.append(
                    {
                        "country_id": s["country_id"],
                        "survey_id": s["id"],
                        "survey_year": s["year"],
                        "survey_year_label": s["year_label"],
                        "survey_type": s["survey_type"],
                        "indicator_id": task["indicator_id"],
                        "status": status,
                        "records": len(observations),
                        "missing_estimates": sum(r["value"] is None for r in observations),
                        "error": task["error"],
                    }
                )
        publications = run["publications"]["data"]["publications"] if run["publications"] else []
        for report in publications:
            statuses = [
                a
                for a in availability
                if a["country_id"] == report.get("country_id")
                and a["survey_id"] == report.get("survey_id")
            ]
            if statuses:
                error = any(
                    a["status"] in {"API_RETRIEVAL_FAILED", "PENDING_REQUEST"} for a in statuses
                )
                present = any(a["records"] > 0 for a in statuses)
                report["source_states"] = source_state(report, present, error)
                report["api_availability_scope"] = "requested_indicator_ids_only"
            report["indicator_availability"] = statuses
        return {
            "projects": projects,
            "observations": rows,
            "availability": availability,
            "publications": publications,
            "latest": latest_by_country(publications, run["selection"]["country_ids"]),
            "lineage": lineage(publications),
        }

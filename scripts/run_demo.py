"""Build a real four-country childhood immunization bundle, or replay it offline."""

import argparse
import json
from pathlib import Path

from surveybridge.config import Settings
from surveybridge.services.application import ResearchService
from surveybridge.services.export import export_project
from surveybridge.services.provenance import verify_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="four-country-immunization")
    parser.add_argument("--replay", type=Path, help="Archived project.json; no remote requests")
    args = parser.parse_args()
    settings = Settings(output_root=Path("examples/outputs").resolve())
    if args.replay:
        project = json.loads(args.replay.read_text(encoding="utf-8"))
    else:
        service = ResearchService(settings)
        try:
            countries = ["NG", "KE", "UG", "TZ"]
            project_id = None
            for query, wanted in [
                ("DPT 3", "CH_VACC_C_DP3"),
                ("BCG", "CH_VACC_C_BCG"),
                ("Measles", "CH_VACC_C_MSL"),
            ]:
                catalog = service.search_indicators(query, limit=100)
                if wanted not in {r["id"] for r in catalog.data}:
                    raise RuntimeError("Expected demo indicator not found in live official catalog")
                result = service.get_indicator_series(wanted, countries, project_id=project_id)
                project_id = result.data["project_id"]
                print(
                    json.dumps(
                        {
                            "indicator": wanted,
                            "project_id": project_id,
                            "cumulative_observations": result.data["observation_count"],
                        }
                    )
                )
            project = service.load(project_id)
        finally:
            service.close()
    assert verify_project(project)
    assert {r["source_country_id"] for r in project["observations"]} == {"NG", "KE", "UG", "TZ"}
    for row in project["observations"]:
        assert row["value"] == row["raw"]["Value"]
        assert row["survey_year"] == row["raw"]["SurveyYear"]
    path = export_project(project, args.output, ["csv", "json", "xlsx", "notebook"], settings)
    latest = []
    for country in project["countries"]:
        group = [
            r
            for r in project["observations"]
            if r["source_country_id"] == country["id"] and r["indicator_id"] == "CH_VACC_C_DP3"
        ]
        row = max(group, key=lambda r: r["survey_year"])
        latest.append(
            {
                k: row[k]
                for k in [
                    "source_country_name",
                    "source_survey_id",
                    "survey_year_label",
                    "value",
                    "unit",
                    "source_row_id",
                ]
            }
        )
    print(
        json.dumps(
            {
                "bundle": str(path),
                "observations": len(project["observations"]),
                "latest_DPT3": latest,
                "note": "Latest rounds differ in time; this is not a same-year ranking. Age equivalence is unverified.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

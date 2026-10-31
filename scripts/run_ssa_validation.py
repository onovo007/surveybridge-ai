"""Live validation of SSA metadata and three verified indicator families; new output only."""

import argparse
import json
from pathlib import Path

from surveybridge.config import Settings
from surveybridge.services.application import ResearchService
from surveybridge.services.regional import RegionalService

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--run-id")
parser.add_argument("--output", default="ssa-publications-2026-10-31")
parser.add_argument("--refresh-publications", action="store_true")
args = parser.parse_args()
settings = Settings(output_root=Path("examples/outputs").resolve(), max_web_requests=1200)
service = ResearchService(settings)
try:
    indicators = ["CH_VACC_C_DP3", "RH_ANCP_W_SKP", "HA_HIVP_B_HIV"]
    if not args.run_id:
        for query, wanted in zip(
            ["DPT 3", "Antenatal care", "HIV prevalence"], indicators, strict=True
        ):
            candidates = service.search_indicators(query, limit=100)
            assert wanted in {i["id"] for i in candidates.data}, wanted
    result = service.run_regional_project(
        indicator_ids=None if args.run_id else indicators,
        region="ssa",
        run_id=args.run_id,
        max_tasks=200,
        refresh_publications=args.refresh_publications,
    )
    run_id = result.data["run_id"]
    Path(".tmp/ssa-live-run-id.txt").write_text(run_id, encoding="utf-8")
    print(result.model_dump_json(indent=2), flush=True)
    exported = service.export_regional_project(run_id, args.output)
    run = RegionalService(service).load(run_id)
    report = {
        "run_id": run_id,
        "progress": run["completeness"],
        "output": exported.data["path"],
        "mandatory_case": run.get("mandatory_report_verification"),
        "warnings": run["warnings"],
    }
    Path(".tmp/ssa-live-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(exported.model_dump_json(indent=2), flush=True)
finally:
    service.close()

"""Audit immutable demonstrations offline; this does not certify survey equivalence."""

import argparse
import csv
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from surveybridge.services.provenance import verify_project
from surveybridge.utils.cache import digest


def review(root, source_revision="4db6edf"):
    bundle = root / "examples/outputs/ssa-publications-review-2026-10-31"
    manifest = json.loads((bundle / "ssa_run_manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["checksums"].items():
        if digest((bundle / name).read_bytes()) != expected:
            raise ValueError(f"SSA output checksum mismatch: {name}")
    current_differences = []
    for name, expected in manifest["source_code_sha256"].items():
        if digest((root / "src/surveybridge" / name).read_bytes()) != expected:
            current_differences.append(name)
        archived = subprocess.run(
            ["git", "show", f"{source_revision}:src/surveybridge/{name}"],
            cwd=root,
            capture_output=True,
            check=True,
            timeout=15,
        ).stdout
        if digest(archived) != expected:
            raise ValueError(f"Recorded run source code hash differs from revision: {name}")
    projects = json.loads((bundle / "ssa_source_projects.json").read_text(encoding="utf-8"))
    for project in projects:
        verify_project(project)
    rows = json.loads((bundle / "ssa_observations.json").read_text(encoding="utf-8"))

    def order(r):
        return (r["indicator_id"], r["source_country_id"], r["source_row_id"])

    if sorted(rows, key=order) != sorted(
        [r for project in projects for r in project["observations"]], key=order
    ):
        raise ValueError("Regional observations differ from archived projects")
    keys = [order(r) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate observation identities")
    with (bundle / "ssa_observations.csv").open(encoding="utf-8-sig", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    if len(csv_rows) != len(rows):
        raise ValueError("CSV row count differs")
    for raw, exported in zip(rows, csv_rows, strict=True):
        for field in (
            "value",
            "lower_ci",
            "upper_ci",
            "denominator_weighted",
            "denominator_unweighted",
        ):
            value = exported[field]
            if (None if value == "" else float(value)) != raw[field]:
                raise ValueError(f"CSV numeric/null mismatch: {field}")
        for field in ("source_row_id", "source_survey_id", "source_country_id", "indicator_id"):
            if exported[field] != raw[field]:
                raise ValueError(f"CSV identity mismatch: {field}")
    for row in rows:
        value, lo, hi = row["value"], row["lower_ci"], row["upper_ci"]
        if row["unit"] == "Percent" and value is not None and not 0 <= value <= 100:
            raise ValueError("Percentage outside 0 to 100")
        if lo is not None and hi is not None:
            if lo > hi or (value is not None and not lo <= value <= hi):
                raise ValueError("Invalid confidence interval")
        for field in ("denominator_weighted", "denominator_unweighted"):
            if row[field] is not None and row[field] < 0:
                raise ValueError("Negative source denominator")
    comparisons = json.loads((bundle / "ssa_comparability_report.json").read_text(encoding="utf-8"))
    if any(
        c["comparison_allowed"] or c["publication_comparability_verified"]
        for c in comparisons.values()
    ):
        raise ValueError("Mixed SSA demonstrations must retain comparison blocks")
    beta = root / "examples/outputs/four-country-immunization-v01"
    provenance = json.loads((beta / "provenance.json").read_text(encoding="utf-8"))
    for name, expected in provenance["output_checksums"].items():
        if digest((beta / name).read_bytes()) != expected:
            raise ValueError(f"Original beta checksum mismatch: {name}")
    beta_project = json.loads((beta / "project.json").read_text(encoding="utf-8"))
    verify_project(beta_project)
    return {
        "reviewed_utc": datetime.now(UTC).isoformat(),
        "scope": "Offline scientific data integrity and interpretation safeguards",
        "ssa_output_hashes_verified": len(manifest["checksums"]),
        "source_code_hashes_verified": len(manifest["source_code_sha256"]),
        "archived_source_revision": source_revision,
        "current_source_files_changed_since_run": current_differences,
        "original_beta_output_hashes_verified": len(provenance["output_checksums"]),
        "source_projects_reconstructed": len(projects),
        "ssa_observations_verified": len(rows),
        "original_beta_observations_verified": len(beta_project["observations"]),
        "csv_numeric_null_identity_checks": "passed",
        "indicator_counts": dict(Counter(r["indicator_id"] for r in rows)),
        "true_zero_observations": sum(r["value"] == 0 for r in rows),
        "missing_estimates": sum(r["value"] is None for r in rows),
        "complete_source_confidence_intervals": sum(
            r["lower_ci"] is not None and r["upper_ci"] is not None for r in rows
        ),
        "comparison_decision": "All three unrestricted SSA comparisons remain blocked",
        "acceptance": "Suitable for public aggregate discovery, extraction and source review",
        "not_certified": "Survey-specific equivalence, causal effects, pooled estimates or independent human peer review",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = review(Path(__file__).resolve().parents[1])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))

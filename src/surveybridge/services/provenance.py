"""Export lineage and verification of original public records."""

import subprocess

from surveybridge import __version__
from surveybridge.models import ProvenanceManifest
from surveybridge.utils.cache import canonical, digest

CITATION = (
    "The DHS Program Indicator Data API, The Demographic and Health Surveys (DHS) Program. "
    "ICF. Originally funded by the United States Agency for International Development (USAID). "
    "Available from https://api.dhsprogram.com/. See fetch_dates for access times. "
    "SurveyBridge AI is independent of The DHS Program."
)


def verify_project(project):
    page_map = {}
    source_pages = set()
    for p in project["pages"]:
        body = bytes.fromhex(p["body_hex"])
        if digest(body) != p["sha256"]:
            raise ValueError("Raw response checksum mismatch")
        import json

        page_map[p["sha256"]] = json.loads(body)["Data"]
        source_pages.add((p["sha256"], p["url"], p["retrieved_utc"]))
    for collection in ("observations", "countries", "surveys", "indicators"):
        for r in project[collection]:
            if digest(canonical(r["raw"])) != r["source_record_hash"]:
                raise ValueError("Source row checksum mismatch")
            if r["raw"] not in page_map.get(r["source_response_hash"], []):
                raise ValueError("Source row not found in archived response")
            if (r["source_response_hash"], r["source_url"], r["retrieved_utc"]) not in source_pages:
                raise ValueError("Source URL or retrieval time does not match archived response")
    # Validate the normalized view too: a valid raw row cannot justify a modified estimate.
    from surveybridge.services.catalog import country, indicator, survey
    from surveybridge.services.series import normalize

    source_fields = (
        "raw",
        "source_url",
        "retrieved_utc",
        "source_response_hash",
        "source_record_hash",
    )
    for collection, parser in (
        ("countries", country),
        ("surveys", survey),
        ("indicators", indicator),
    ):
        for row in project[collection]:
            rebuilt = parser({k: row[k] for k in source_fields}).model_dump()
            if rebuilt != row:
                raise ValueError("Normalized catalog metadata does not reproduce from source")
    from surveybridge.models import Indicator

    rebuilt, _ = normalize(
        [{k: row[k] for k in source_fields} for row in project["observations"]],
        {r["id"]: Indicator(**r) for r in project["indicators"]},
    )
    if sorted(rebuilt, key=lambda r: r["source_row_id"]) != sorted(
        project["observations"], key=lambda r: r["source_row_id"]
    ):
        raise ValueError("Normalized observations do not reproduce from source")
    return True


def manifest(project, checksums):
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=3, check=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        sha = None
    return ProvenanceManifest(
        release_version=__version__,
        git_sha=sha,
        project_id=project["project_id"],
        query_filters={"queries": project["queries"]},
        source_endpoints=sorted({p["url"] for p in project["pages"]}),
        fetch_dates=sorted({p["retrieved_utc"] for p in project["pages"]}),
        raw_response_hashes=sorted({p["sha256"] for p in project["pages"]}),
        source_row_ids=[r["source_row_id"] for r in project["observations"]],
        output_checksums=checksums,
        warnings=[f["explanation"] for f in project["assessment"]["findings"]],
        transformation_history=project["transformations"],
        citation=CITATION,
    ).model_dump()

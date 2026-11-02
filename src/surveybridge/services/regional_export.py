"""Separate, auditable SSA research bundles; validated beta outputs are never touched."""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path

import nbformat

from surveybridge import __version__
from surveybridge.services.comparability import assess
from surveybridge.services.export import write_csv
from surveybridge.services.provenance import CITATION
from surveybridge.utils.cache import canonical, digest


def export_regional(run, output_dir, settings):
    from surveybridge.services.application import ResearchService
    from surveybridge.services.regional import RegionalService

    research = ResearchService(settings)
    try:
        material = RegionalService(research).materialize(run)
    finally:
        research.close()
    root = settings.output_root.resolve()
    candidate = Path(output_dir)
    target = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if target == root or not target.is_relative_to(root):
        raise ValueError("SSA output must be a new directory below the output root")
    if target.exists():
        raise FileExistsError("SSA output already exists; choose a new directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".ssa-", dir=target.parent))
    try:
        _write(stage, run, material)
        lock = target.parent / f".{target.name}.export.lock"
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        try:
            if target.exists():
                raise FileExistsError("SSA output already exists")
            for attempt in range(6):
                try:
                    os.rename(stage, target)
                    break
                except PermissionError:
                    if attempt == 5 or target.exists():
                        raise
                    time.sleep(0.05 * (attempt + 1))
        finally:
            lock.unlink()
    finally:
        if stage.exists():
            if not stage.resolve().is_relative_to(root):
                raise ValueError("Temporary SSA export escaped output root")
            shutil.rmtree(stage)
    return target


def _write(stage, run, data):
    def js(name, value):
        (stage / name).write_bytes(canonical(value))

    selected = run["selection"]
    catalog = (
        selected["classification"]["countries"]
        if selected["classification"]
        else selected["countries"]
    )
    write_csv(
        stage / "ssa_country_catalog.csv",
        catalog,
        sorted({k for r in catalog for k in r}) if catalog else [],
    )
    write_csv(stage / "ssa_survey_coverage.csv", selected["surveys"])
    write_csv(stage / "ssa_indicator_availability.csv", data["availability"])
    write_csv(stage / "ssa_observations.csv", data["observations"])
    js("ssa_observations.json", data["observations"])
    publication_fields = sorted({k for r in data["publications"] for k in r})
    write_csv(
        stage / "ssa_publication_catalog.csv",
        [{k: r.get(k) for k in publication_fields} for r in data["publications"]],
        publication_fields,
    )
    latest = [
        {
            "country_id": r["country_id"],
            "report_id": (r["latest_known_report"] or {}).get("report_id"),
            "publication_date": (r["latest_known_report"] or {}).get("publication_date"),
            "date_precision": (r["latest_known_report"] or {}).get("publication_date_precision"),
            "survey_id": (r["latest_known_report"] or {}).get("survey_id"),
            "source_url": (r["latest_known_report"] or {}).get("source_url"),
            "report_type": (r["latest_known_report"] or {}).get("report_type"),
            "source_states": (r["latest_known_report"] or {}).get("source_states"),
            "fieldwork_start": (r["latest_known_report"] or {}).get("fieldwork_start"),
            "fieldwork_end": (r["latest_known_report"] or {}).get("fieldwork_end"),
            "latest_fieldwork_end": r["latest_fieldwork_end"],
            "unknown_publication_dates": r["unknown_publication_dates"],
            "last_checked_utc": run["updated_utc"],
        }
        for r in data["latest"]
    ]
    write_csv(stage / "latest_survey_releases.csv", latest)
    gaps = [
        r
        for r in data["publications"]
        if not any(a["records"] > 0 for a in r.get("indicator_availability", []))
    ]
    write_csv(
        stage / "report_api_coverage_gaps.csv",
        [{k: r.get(k) for k in publication_fields} for r in gaps],
        publication_fields,
    )
    js("publication_lineage.json", data["lineage"])
    js("ssa_regional_run.json", run)
    js("ssa_source_projects.json", data["projects"])
    composite = {
        "observations": data["observations"],
        "surveys": selected["surveys"],
        "indicators": [i for p in data["projects"] for i in p["indicators"]],
    }
    available = {i["id"] for i in composite["indicators"]}
    checks = {
        i: assess(composite, [i])
        if i in available
        else {
            "comparison_allowed": False,
            "publication_comparability_verified": False,
            "findings": [
                {
                    "severity": "block",
                    "explanation": "No successfully retrieved project for requested indicator; failures are not no-data evidence.",
                    "recommendation": "Resume failed or pending tasks before comparison.",
                }
            ],
        }
        for i in run["filters"]["indicator_ids"]
    }
    js("ssa_comparability_report.json", checks)
    markdown = "# SSA comparability\n\n" + "\n\n".join(
        f"## {i}\n\n"
        + "\n".join(
            f"- {f['severity']}: {f['explanation']} {f['recommendation']}" for f in c["findings"]
        )
        for i, c in checks.items()
    )
    markdown += "\n\nReport-derived numerical extraction is disabled. Preliminary/final/API sources are linked, not pooled. Survey-specific population and design equivalence remain unverified.\n"
    (stage / "ssa_comparability_report.md").write_text(markdown, encoding="utf-8")
    country_counts = {
        c: sum(r["source_country_id"] == c for r in data["observations"])
        for c in selected["country_ids"]
    }
    indicator_counts = {
        i: sum(r["indicator_id"] == i for r in data["observations"])
        for i in run["filters"]["indicator_ids"]
    }
    summary = {
        "countries": len(selected["country_ids"]),
        "survey_rounds": len(selected["surveys"]),
        "observations": len(data["observations"]),
        "publications": len(data["publications"]),
        "country_totals": country_counts,
        "indicator_totals": indicator_counts,
        "missing_estimates": sum(r["value"] is None for r in data["observations"]),
        "availability_statuses": {
            s: sum(a["status"] == s for a in data["availability"])
            for s in sorted({a["status"] for a in data["availability"]})
        },
        "completeness": run["completeness"],
        "exceptions": [t for t in run["tasks"] if t["error"]],
        "warnings": run["warnings"],
    }
    js("ssa_summary.json", summary)
    (stage / "ssa_summary.md").write_text(
        "# SSA research run\n\n"
        + CITATION
        + "\n\n```json\n"
        + json.dumps(summary, indent=2)
        + "\n```\n\n"
        "Latest known report means latest dated record in the checked sources, not guaranteed latest in existence. Catalog dates can differ from PDF cover dates. "
        "Empty bounds are null, not estimated. No annual interpolation or causal/significance claims. Inspect country refresh errors, unmatched reports, and the comparison report before interpretation.\n",
        encoding="utf-8",
    )
    nb = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_markdown_cell(
                "# SSA publication and aggregate coverage\n\n"
                + CITATION
                + "\n\nCounts describe retrieved records, not population health trends. Read ssa_summary.md and ssa_comparability_report.md. Report tables are not automatically extracted."
            ),
            nbformat.v4.new_code_cell(
                "from pathlib import Path\nimport json, hashlib\nimport pandas as pd\nroot = Path.cwd()\nmanifest = json.loads((root/'ssa_run_manifest.json').read_text(encoding='utf-8'))\nfor name, sha in manifest['checksums'].items():\n    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == sha, name\nfrom surveybridge.services.provenance import verify_project\nprojects = json.loads((root/'ssa_source_projects.json').read_text(encoding='utf-8'))\nfor project in projects:\n    assert verify_project(project)\nrecords = json.loads((root/'ssa_observations.json').read_text(encoding='utf-8'))\nassert sorted(records, key=lambda r:r['source_row_id']) == sorted([r for p in projects for r in p['observations']], key=lambda r:r['source_row_id'])\nprint('All archived project lineages and exported checksums verified')"
            ),
            nbformat.v4.new_code_cell(
                "summary = json.loads((root/'ssa_summary.json').read_text(encoding='utf-8'))\nprint(summary['completeness'])\nprint(summary['warnings'])\nprint(summary['availability_statuses'])\nlatest = pd.read_csv(root/'latest_survey_releases.csv')\ndisplay(latest)"
            ),
            nbformat.v4.new_code_cell(
                "import matplotlib.pyplot as plt\ncounts = pd.Series(summary['country_totals']).sort_values()\nif not counts.empty:\n    ax = counts.plot.barh(figsize=(9, max(4, len(counts)*0.22)))\n    ax.set_xlabel('Retrieved API observation records across requested indicators and survey rounds')\n    ax.set_ylabel('DHS country code')\n    ax.set_title('Data coverage — not a comparison of health outcomes')\n    plt.tight_layout()\n    plt.show()\n# No report estimate extraction, annual interpolation, pooled indicators or significance tests."
            ),
        ],
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
    )
    nbformat.write(nb, stage / "ssa_analysis.ipynb")
    checksums = {
        p.relative_to(stage).as_posix(): digest(p.read_bytes())
        for p in stage.rglob("*")
        if p.is_file()
    }
    sources = selected["sources"] + (run["publications"]["source"] if run["publications"] else [])
    for project in data["projects"]:
        sources.extend({k: v for k, v in p.items() if k != "body_hex"} for p in project["pages"])
    js(
        "ssa_run_manifest.json",
        {
            "software_version": __version__,
            "source_code_sha256": {
                p.relative_to(Path(__file__).resolve().parents[1]).as_posix(): digest(
                    p.read_bytes()
                )
                for p in Path(__file__).resolve().parents[1].rglob("*.py")
            },
            "run_id": run["run_id"],
            "filters": run["filters"],
            "country_count": len(selected["country_ids"]),
            "classification": selected["classification"],
            "updated_utc": run["updated_utc"],
            "completeness": run["completeness"],
            "exceptions": summary["exceptions"],
            "sources": sources,
            "source_page_count": len(sources),
            "checksums": checksums,
            "citation": CITATION,
            "scientific_warnings": run["warnings"],
        },
    )

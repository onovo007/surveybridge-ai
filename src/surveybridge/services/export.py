"""Atomic, no-overwrite research bundles restricted to an operator-configured root."""

import csv
import json
import os
import shutil
import tempfile
from pathlib import Path

import nbformat
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from surveybridge.models import Observation
from surveybridge.services.comparability import assess
from surveybridge.services.provenance import CITATION, manifest, verify_project
from surveybridge.utils.cache import canonical, digest


def flat(rows):
    return [
        {
            k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
            for k, v in row.items()
        }
        for row in rows
    ]


def safe_cell(value):
    # Prevent spreadsheet formula interpretation of untrusted API metadata in CSV/XLSX.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def write_csv(path, rows, fields=None):
    rows = flat(rows)
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: safe_cell(v) for k, v in row.items()} for row in rows)


def gap_table(project):
    rows = project["observations"]
    result = []
    for s in project["surveys"]:
        for i in project["indicators"]:
            found = [
                r for r in rows if r["source_survey_id"] == s["id"] and r["indicator_id"] == i["id"]
            ]
            result.append(
                {
                    "survey_id": s["id"],
                    "country_id": s["country_id"],
                    "survey_year": s["year"],
                    "survey_year_label": s["year_label"],
                    "survey_type": s["survey_type"],
                    "indicator_id": i["id"],
                    "source_record_count": len(found),
                    "nonmissing_estimate_count": sum(r["value"] is not None for r in found),
                    "status": "observed" if found else "no_record_in_requested_breakdown",
                }
            )
    return result


def presentation_rows(project):
    presentation = [
        "source_country_name",
        "source_country_id",
        "source_survey_id",
        "survey_year_label",
        "survey_year",
        "indicator_label",
        "indicator_id",
        "value",
        "unit",
        "lower_ci",
        "upper_ci",
        "denominator",
        "denominator_weighted",
        "denominator_unweighted",
        "breakdown_type",
        "breakdown_value",
    ]
    rows = [
        {k: row[k] for k in presentation + [k for k in row if k not in presentation]}
        for row in project["observations"]
    ]
    return rows


def export_project(project, output_dir, formats, settings):
    if not formats or set(formats) - {"csv", "json", "xlsx", "notebook"}:
        raise ValueError("formats must contain csv, json, xlsx and/or notebook")
    root = settings.output_root.resolve()
    requested = Path(output_dir)
    target = (requested if requested.is_absolute() else root / requested).resolve()
    if target == root or not target.is_relative_to(root):
        raise ValueError("Export must be a new directory below SURVEYBRIDGE_OUTPUT_ROOT")
    if target.exists():
        raise FileExistsError("Output already exists; choose a new directory")
    verify_project(project)
    project["assessment"] = assess(project)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".surveybridge-", dir=target.parent))
    try:
        _write_bundle(stage, project, formats)
        # A sibling exclusive lock works on Windows, where replacing even an empty
        # destination directory is forbidden. Other exports cannot claim this name.
        lock = target.parent / f".{target.name}.export.lock"
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        try:
            if target.exists():
                raise FileExistsError("Output already exists; choose a new directory")
            os.rename(stage, target)
        finally:
            lock.unlink()
    finally:
        if stage.exists():
            if not stage.resolve().is_relative_to(root):
                raise ValueError("Temporary export escaped output root")
            shutil.rmtree(stage)
    return target


def _write_bundle(stage, project, formats):
    def write_json(name, value):
        (stage / name).write_bytes(canonical(value))

    rows = presentation_rows(project)
    assessment = project["assessment"]
    gaps = gap_table(project)
    dictionary = [
        {
            "field": name,
            "type": str(field.annotation),
            "description": {
                "value": "Official estimate; null means missing, zero remains zero. No imputation.",
                "survey_year": "DHS principal survey year; see survey_year_label and fieldwork dates.",
                "unit": "Official indicator MeasurementType; NumberScale is preserved in indicator raw metadata.",
                "source_record_hash": "SHA-256 of canonical JSON original record.",
                "source_response_hash": "SHA-256 of original response bytes under raw/.",
                "raw": "Unmodified original API record.",
                "denominator": "Catalog population definition, not an estimate or sample count.",
                "denominator_weighted": "Source weighted denominator; not independent observations.",
                "denominator_unweighted": "Source unweighted denominator, when supplied.",
                "lower_ci": "Source CILow only; null if absent; never estimated.",
                "upper_ci": "Source CIHigh only; null if absent; never estimated.",
            }.get(
                name,
                "Normalized source metadata; see raw record and official DHS data/fields documentation.",
            ),
        }
        for name, field in Observation.model_fields.items()
    ]
    # Essential local inputs are always included, even when selecting a single rich format.
    write_json("observations.json", rows)
    write_json("project.json", project)
    write_json("comparability_report.json", assessment)
    write_json(
        "comparability_by_indicator.json",
        {i["id"]: assess(project, [i["id"]]) for i in project["indicators"]},
    )
    write_json(
        "quality_assessment.json",
        {
            "observations": len(rows),
            "missing_values": sum(r["value"] is None for r in rows),
            "missing_confidence_intervals": sum(
                r["lower_ci"] is None or r["upper_ci"] is None for r in rows
            ),
            "missing_survey_indicator_pairs": sum(g["source_record_count"] == 0 for g in gaps),
            "raw_lineage_verified": True,
            "publication_comparability_verified": False,
        },
    )
    write_csv(stage / "indicator_dictionary.csv", project["indicators"])
    write_csv(stage / "survey_catalog.csv", project["surveys"])
    write_csv(stage / "country_catalog.csv", project["countries"])
    write_csv(stage / "data_dictionary.csv", dictionary)
    write_csv(stage / "availability.csv", gaps)
    if "csv" in formats:
        write_csv(
            stage / "observations.csv",
            rows,
            list(rows[0]) if rows else list(Observation.model_fields),
        )
    report = "# Comparability assessment\n\n" + "\n\n".join(
        f"**{f['severity'].upper()} — {f['attribute']}**: {f['explanation']} {f['recommendation']}\nEvidence: {json.dumps(f['evidence'], ensure_ascii=False)}"
        for f in assessment["findings"]
    )
    (stage / "comparability_report.md").write_text(report + "\n", encoding="utf-8")
    (stage / "limitations.md").write_text(
        "# Scientific limitations\n\nAggregated public DHS indicators, not microdata. No imputation, pooled estimates, causal inference, "
        "confidence interval construction or significance testing. Survey gaps represent absent API records in the requested breakdown; "
        "they do not establish that a survey never collected the measure. Years without surveys are unobserved, not zeros. "
        "See availability.csv for completed survey rounds and survey_catalog.csv for fieldwork dates. "
        "A shared catalog definition is insufficient to certify survey-specific comparability.\n\n"
        + report,
        encoding="utf-8",
    )
    (stage / "README.md").write_text(
        "# SurveyBridge research bundle\n\n"
        + CITATION
        + "\n\nRead limitations.md and comparability_report.md before use. "
        "observations.json preserves numeric types, nulls, and original records. Blank CSV cells represent nulls. "
        "CSV/Excel strings starting with formula characters receive a leading apostrophe; JSON/raw snapshots retain the source text. "
        "raw/ contains exact response bytes. provenance.json hashes all other bundle files except itself; SHA256SUMS includes provenance.json. "
        "Run analysis.ipynb from this directory with the installed SurveyBridge Python environment. "
        "The notebook verifies hashes and rebuilds normalization from archived responses without network access.\n",
        encoding="utf-8",
    )
    raw_dir = stage / "raw"
    raw_dir.mkdir()
    for p in project["pages"]:
        (raw_dir / f"{p['sha256']}.json").write_bytes(bytes.fromhex(p["body_hex"]))
    if "xlsx" in formats:
        wb = Workbook()
        wb.remove(wb.active)
        for title, table in {
            "Observations": rows,
            "Indicators": project["indicators"],
            "Surveys": project["surveys"],
            "Availability": gaps,
            "Data dictionary": dictionary,
            "Comparability": assessment["findings"],
            "Source pages": [
                {k: v for k, v in p.items() if k != "body_hex"} for p in project["pages"]
            ],
        }.items():
            ws = wb.create_sheet(title)
            table = flat(table)
            if table:
                ws.append(list(table[0]))
                for row in table:
                    ws.append([safe_cell(v) for v in row.values()])
                for cell in ws[1]:
                    cell.font = Font(color="FFFFFF", bold=True)
                    cell.fill = PatternFill("solid", fgColor="164B63")
                ws.freeze_panes = "A2"
                ws.auto_filter.ref = ws.dimensions
                for col in range(1, len(table[0]) + 1):
                    ws.column_dimensions[get_column_letter(col)].width = min(
                        55, max(16, len(str(ws.cell(1, col).value)) + 2)
                    )
                if title == "Observations":
                    ws.column_dimensions["A"].width = 22
                    ws.column_dimensions["F"].width = 34
                    for row_index, source in enumerate(rows, start=2):
                        for field in ("value", "lower_ci", "upper_ci"):
                            col_index = list(table[0]).index(field) + 1
                            ws.cell(row_index, col_index).number_format = (
                                "0"
                                if source["precision"] == 0
                                else "0." + "0" * min(source["precision"] or 1, 6)
                            )
        notes = wb.create_sheet("Read first")
        notes.append(["Source", CITATION])
        notes.append(["Comparison allowed by automated checks", assessment["comparison_allowed"]])
        notes.append(["Publication comparability verified", False])
        for finding in assessment["findings"]:
            notes.append([finding["severity"], safe_cell(finding["explanation"])])
        notes.column_dimensions["A"].width = 43
        notes.column_dimensions["B"].width = 105
        for row in notes:
            notes.row_dimensions[row[0].row].height = 48
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        wb.save(stage / "surveybridge_analysis.xlsx")
    if "notebook" in formats:
        notebook = nbformat.v4.new_notebook(
            cells=[
                nbformat.v4.new_markdown_cell(
                    "# DHS aggregate immunization research\n\n"
                    + CITATION
                    + "\n\nRead limitations.md. Survey-specific comparability is unverified. No interpolation or inference."
                ),
                nbformat.v4.new_code_cell(
                    "from pathlib import Path\nimport json, hashlib\nimport pandas as pd\nroot = Path.cwd()\nmanifest = json.loads((root / 'provenance.json').read_text(encoding='utf-8'))\nfor name, expected in manifest['output_checksums'].items():\n    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name\nproject = json.loads((root / 'project.json').read_text(encoding='utf-8'))\nfrom surveybridge.services.provenance import verify_project\nassert verify_project(project)\nprint('All archived response and output hashes verified')"
                ),
                nbformat.v4.new_code_cell(
                    "from surveybridge.services.series import normalize\nfrom surveybridge.models import Indicator\nsource_records = []\nfor page in project['pages']:\n    if '/data?' not in page['url']:\n        continue\n    for raw in json.loads(bytes.fromhex(page['body_hex']))['Data']:\n        from surveybridge.utils.cache import canonical, digest\n        source_records.append(dict(raw=raw, source_url=page['url'], retrieved_utc=page['retrieved_utc'], source_response_hash=page['sha256'], source_record_hash=digest(canonical(raw))))\nrebuilt, _ = normalize(source_records, {i['id']: Indicator(**i) for i in project['indicators']})\nexpected = sorted(project['observations'], key=lambda r: r['source_row_id'])\nassert sorted(rebuilt, key=lambda r: r['source_row_id']) == expected\ndf = pd.DataFrame(json.loads((root / 'observations.json').read_text(encoding='utf-8')))\nprint('Every normalized observation reproduced from original API records')\ndf[['source_country_name', 'source_survey_id', 'survey_year_label', 'indicator_id', 'value', 'unit']]"
                ),
                nbformat.v4.new_code_cell(
                    "report = json.loads((root / 'comparability_report.json').read_text(encoding='utf-8'))\nfor finding in report['findings']:\n    print(finding['severity'].upper(), finding['explanation'])\nby_indicator = json.loads((root / 'comparability_by_indicator.json').read_text(encoding='utf-8'))\nfor indicator_id, check in by_indicator.items():\n    print(indicator_id, 'Descriptive source table; publication comparability unverified')\n    if not check['comparison_allowed']:\n        print('BLOCKED: review indicator-specific findings before comparison')\n        continue\n    subset = df[df.indicator_id == indicator_id]\n    display(subset[['source_country_name', 'source_survey_id', 'survey_year_label', 'value', 'unit']])\n# Keep indicators separate. No annual interpolation, pooling, confidence intervals or significance tests."
                ),
            ],
            metadata={
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
            },
        )
        nbformat.write(notebook, stage / "analysis.ipynb")
    checksums = {
        p.relative_to(stage).as_posix(): digest(p.read_bytes())
        for p in sorted(stage.rglob("*"))
        if p.is_file()
    }
    write_json("provenance.json", manifest(project, checksums))
    checksums["provenance.json"] = digest((stage / "provenance.json").read_bytes())
    (stage / "SHA256SUMS").write_text(
        "".join(f"{sha}  {name}\n" for name, sha in sorted(checksums.items())), encoding="utf-8"
    )

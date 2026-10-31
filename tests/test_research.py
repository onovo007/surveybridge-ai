import copy
import json

import nbformat
import pytest
from openpyxl import load_workbook

from surveybridge.models import Indicator
from surveybridge.services.comparability import assess
from surveybridge.services.export import export_project
from surveybridge.services.provenance import verify_project
from surveybridge.services.series import normalize
from surveybridge.utils.cache import digest


def test_real_archived_rows_roundtrip(project):
    assert verify_project(project)
    assert len(project["observations"]) > 20
    for r in project["observations"]:
        assert r["value"] == r["raw"]["Value"]
        assert r["lower_ci"] is None and r["upper_ci"] is None
        assert r["survey_year"] == r["raw"]["SurveyYear"]
    latest = {
        c: max(
            (r for r in project["observations"] if r["source_country_id"] == c),
            key=lambda r: r["survey_year"],
        )
        for c in ["NG", "KE", "UG", "TZ"]
    }
    assert latest["NG"]["value"] == 53.4
    assert latest["KE"]["value"] == 89.2
    assert not project["assessment"]["publication_comparability_verified"]
    assert any(f["attribute"] == "population" for f in project["assessment"]["findings"])


def test_null_zero_and_conflicting_duplicates(project):
    first = copy.deepcopy(project["observations"][0])
    meta = {r["id"]: Indicator(**r) for r in project["indicators"]}
    rec = {
        k: first[k]
        for k in [
            "raw",
            "source_url",
            "retrieved_utc",
            "source_response_hash",
            "source_record_hash",
        ]
    }
    rec["raw"]["Value"] = 0
    rows, duplicates = normalize([rec, rec], meta)
    assert rows[0]["value"] == 0 and duplicates == 1
    rec["raw"]["Value"] = ""
    assert normalize([rec], meta)[0][0]["value"] is None
    rec["raw"]["Value"] = "(suppressed)"
    assert normalize([rec], meta)[0][0]["value"] is None
    other = copy.deepcopy(rec)
    other["source_record_hash"] = "conflict"
    with pytest.raises(ValueError, match="Conflicting"):
        normalize([rec, other], meta)


@pytest.mark.parametrize(
    "field,value",
    [
        ("unit", None),
        ("denominator", None),
        ("value", 101),
        ("breakdown_value", "Urban"),
        ("survey_type", "MIS"),
        ("lower_ci", 100),
    ],
)
def test_blocks_unsupported_comparisons(project, field, value):
    project["observations"][0][field] = value
    if field == "lower_ci":
        project["observations"][0]["upper_ci"] = 10
    assert assess(project)["comparison_allowed"] is False


def test_no_data_blocks(project):
    project["observations"] = []
    assert not assess(project)["comparison_allowed"]


def test_catalog_and_input_validation(service):
    assert service.list_countries(query="nigeria").data[0]["id"] == "NG"
    assert service.search_indicators("DPT 3").data[0]["id"] == "CH_VACC_C_DP3"
    assert service.list_surveys(["NG"], 2000, 2025).data
    for countries in [["ZZ"], [], ["Nigeria"], ["ng"]]:
        with pytest.raises(ValueError):
            service.get_indicator_series("CH_VACC_C_DP3", countries)
    with pytest.raises(ValueError):
        service.list_surveys(["NG"], 2024, 2000)
    with pytest.raises(ValueError):
        service.load("../../secret")
    with pytest.raises(ValueError):
        service.get_indicator_series("made_up_indicator", ["NG"])


def test_bundle_integrity_and_xlsx(project, settings):
    path = export_project(project, "study", ["csv", "json", "xlsx", "notebook"], settings)
    manifest = json.loads((path / "provenance.json").read_text())
    assert all(
        digest((path / name).read_bytes()) == sha
        for name, sha in manifest["output_checksums"].items()
    )
    nbformat.validate(nbformat.read(path / "analysis.ipynb", as_version=4))
    wb = load_workbook(path / "surveybridge_analysis.xlsx")
    assert wb["Observations"].max_row == len(project["observations"]) + 1
    assert wb["Observations"].freeze_panes == "A2"
    assert wb["Read first"]["B3"].value is False
    for filename in ["availability.csv", "data_dictionary.csv", "limitations.md", "SHA256SUMS"]:
        assert (path / filename).is_file()
    with pytest.raises(FileExistsError):
        export_project(project, "study", ["json"], settings)
    with pytest.raises(ValueError, match="below"):
        export_project(project, "../escape", ["json"], settings)
    with pytest.raises(ValueError):
        export_project(project, "new", ["html"], settings)


def test_tampered_raw_data_prevents_export(project, settings):
    project["observations"][0]["raw"]["Value"] = 999
    with pytest.raises(ValueError, match="checksum"):
        export_project(project, "tampered", ["json"], settings)


def test_tampered_normalized_value_and_url(project, settings):
    original = project["observations"][0]["value"]
    project["observations"][0]["value"] = 99.99
    with pytest.raises(ValueError, match="do not reproduce"):
        export_project(project, "tampered-view", ["json"], settings)
    project["observations"][0]["value"] = original
    project["observations"][0]["source_url"] = "https://evil.example/fake"
    with pytest.raises(ValueError, match="Source URL"):
        verify_project(project)


def test_formula_strings_are_text_and_json_unmodified(tmp_path):
    import csv

    from surveybridge.services.export import safe_cell, write_csv

    path = tmp_path / "injection.csv"
    source = [{"label": '=HYPERLINK("https://evil.example")', "value": 0, "missing": None}]
    write_csv(path, source)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["label"].startswith("'=")
    assert row["value"] == "0" and row["missing"] == ""
    assert source[0]["label"].startswith("=")
    assert safe_cell(-10) == -10


@pytest.mark.parametrize(
    "field,value",
    [
        ("definition", "Different population"),
        ("denominator", "Different population"),
        ("unit", "Rate"),
        ("by_variable_id", "1"),
    ],
)
def test_conflicting_metadata_blocks(project, field, value):
    project["observations"][0][field] = value
    assert not assess(project)["comparison_allowed"]


def test_indicator_selection_and_project_append_scope(service, project):
    with pytest.raises(ValueError):
        service.assess_comparability(project["project_id"], ["unknown"])
    with pytest.raises(ValueError, match="already exists"):
        service.get_indicator_series(
            "CH_VACC_C_DP3", ["NG", "KE", "UG", "TZ"], project_id=project["project_id"]
        )


def test_export_failure_leaves_no_partial_directory(project, settings, monkeypatch):
    from surveybridge.services import export

    def fail(*args):
        raise RuntimeError("simulated disk failure")

    monkeypatch.setattr(export, "_write_bundle", fail)
    with pytest.raises(RuntimeError):
        export_project(project, "failed", ["json"], settings)
    assert not (settings.output_root / "failed").exists()
    assert not list(settings.output_root.glob(".surveybridge-*"))

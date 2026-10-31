import copy
import json
from pathlib import Path

import httpx
import pytest

from surveybridge.clients.dhs import DHSClient, DHSError
from surveybridge.clients.official_web import OfficialWebClient, official_url
from surveybridge.geography import SSACountryResolver
from surveybridge.services.application import ResearchService
from surveybridge.services.discovery import (
    DiscoveryService,
    latest_by_country,
    lineage,
    source_state,
)
from surveybridge.services.publication_html import CatalogHTML, publication_date
from surveybridge.services.regional import RegionalService
from surveybridge.utils.cache import canonical, digest


def record(raw):
    return {
        "raw": raw,
        "source_url": "https://api.dhsprogram.com/rest/dhs/countries?f=json",
        "retrieved_utc": "2026-10-31T00:00:00+00:00",
        "source_response_hash": "fixture",
        "source_record_hash": digest(canonical(raw)),
    }


def test_resolver_uses_iso3_not_africa_region():
    countries = [
        record(
            {"DHS_CountryCode": "ZA", "ISO3_CountryCode": "ZAF", "CountryName": "Renamed display"}
        ),
        record({"DHS_CountryCode": "SD", "ISO3_CountryCode": "SDN", "CountryName": "Sudan"}),
        record({"DHS_CountryCode": "NG", "ISO3_CountryCode": "NGA", "CountryName": "Nigeria"}),
    ]
    result = SSACountryResolver().resolve(
        countries, [record({"DHS_CountryCode": "ZA"}), record({"DHS_CountryCode": "SD"})]
    )
    assert result["country_ids"] == ["ZA"]
    assert any(
        r["classification_status"] == "DHS_COUNTRY_NO_SURVEY" and r["country_id"] == "NG"
        for r in result["countries"]
    )
    assert result["classification"]["source_url"].startswith("https://unstats.un.org/")


def test_missing_duplicate_iso3_and_explicit_crosswalk():
    countries = [record({"DHS_CountryCode": "ZZ", "CountryName": "Nigeria"})]
    assert (
        "ZZ"
        in SSACountryResolver().resolve(countries, [record({"DHS_CountryCode": "ZZ"})])[
            "unmapped_dhs_codes"
        ]
    )
    assert SSACountryResolver(crosswalk={"ZZ": "NGA"}).resolve(
        countries, [record({"DHS_CountryCode": "ZZ"})]
    )["country_ids"] == ["ZZ"]
    countries = [
        record({"DHS_CountryCode": c, "ISO3_CountryCode": "NGA", "CountryName": c})
        for c in ["NG", "ZZ"]
    ]
    with pytest.raises(ValueError, match="Ambiguous"):
        SSACountryResolver().resolve(countries, [])


def catalog_html():
    return """<select name="country1"><option value="30">Nigeria</option></select><select name="topic1"><option value="32">Child Health</option></select>
    <table><tr><td>PR166</td><td><a href="/publications/publication-PR166-reports.cfm">Nigeria Mini DHS 2025-26</a></td><td>07/2026</td><td>Preliminary Reports/Key Indicators Reports</td><td>No</td></tr></table>"""


def detail_html():
    return """<dl><dt>Document Type</dt><dd>Preliminary Reports/Key Indicators Reports</dd><dt>Country(s)</dt><dd>Nigeria</dd><dt>Publication ID</dt><dd>PR166</dd>
    <dt>Publication Date</dt><dd>July 2026</dd><dt>Survey</dt><dd><a href="/methodology/survey/survey-display-636.cfm">Nigeria Interim DHS, 2025</a></dd></dl><a href="/pubs/pdf/PR166/PR166.pdf">Download</a>"""


def test_catalog_parser_preserves_precision_and_type():
    parser = CatalogHTML("https://dhsprogram.com/publications/Publication-Search.cfm")
    parser.feed(catalog_html())
    assert parser.rows[0]["publication_date"] == "2026-07"
    assert parser.options["Nigeria"] == "30"
    assert parser.options_by_select["topic1"]["Child Health"] == "32"
    assert publication_date("unknown") == (None, None)


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/pubs/pdf/A1/A1.pdf",
        "http://dhsprogram.com/pubs/pdf/A1/A1.pdf",
        "https://dhsprogram.com/data/download/",
        "https://dhsprogram.com/pubs/pdf/%2e%2e/private",
    ],
)
def test_official_url_restrictions(url):
    with pytest.raises(ValueError):
        official_url(url)


def test_web_redirect_and_invalid_pdf(settings):
    web = OfficialWebClient(
        settings,
        httpx.MockTransport(
            lambda r: httpx.Response(302, headers={"Location": "https://evil.example/fake"})
        ),
    )
    with pytest.raises(ValueError):
        web.get("https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf", pdf=True)
    web.close()
    web = OfficialWebClient(
        settings, httpx.MockTransport(lambda r: httpx.Response(200, text="not a PDF"))
    )
    with pytest.raises(DHSError, match="did not return"):
        web.get("https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf", pdf=True)
    web.close()


@pytest.fixture
def regional_service(settings, source_payloads):
    payloads = copy.deepcopy(source_payloads)
    for row in payloads["countries"]:
        row["ISO3_CountryCode"] = {"NG": "NGA", "KE": "KEN", "TZ": "TZA", "UG": "UGA"}[
            row["DHS_CountryCode"]
        ]
    payloads["publications"] = []
    payloads["surveys"].append(
        {
            "SurveyId": "NG2025DHS",
            "DHS_CountryCode": "NG",
            "SurveyYear": "2025",
            "SurveyType": "DHS",
            "SurveyStatus": "Ongoing",
            "CountryName": "Nigeria",
            "SurveyNum": 636,
            "IndicatorData": 0,
            "FieldworkStart": "2025-12-01",
            "FieldworkEnd": "2026-02-01",
            "SurveyYearLabel": "2025-26",
        }
    )

    def handler(request):
        endpoint = request.url.path.rsplit("/", 1)[-1]
        rows = payloads[endpoint]
        p = request.url.params
        if p.get("countryIds"):
            rows = [r for r in rows if r["DHS_CountryCode"] in p["countryIds"].split(",")]
        if p.get("indicatorIds"):
            rows = [r for r in rows if r["IndicatorId"] in p["indicatorIds"].split(",")]
        return httpx.Response(
            200,
            json={
                "Data": rows,
                "Page": "1",
                "TotalPages": 1,
                "RecordCount": len(rows),
                "RecordsReturned": len(rows),
            },
        )

    service = ResearchService(settings, DHSClient(settings, httpx.MockTransport(handler)))
    yield service
    service.close()


def test_report_missing_from_api_matches_official_survey_number(regional_service):
    web = OfficialWebClient(
        regional_service.settings,
        httpx.MockTransport(
            lambda r: httpx.Response(
                200, text=detail_html() if "publication-PR166" in r.url.path else catalog_html()
            )
        ),
    )
    result = DiscoveryService(regional_service, web).list_publications(country_ids=["NG"])
    report = result.data["publications"][0]
    assert report["report_id"] == "PR166" and report["survey_id"] == "NG2025DHS"
    assert report["match_status"] == "official_survey_number_join"
    assert report["is_mini_dhs"] and "REPORT_METADATA_ONLY" in report["source_states"]
    assert report["api_indicator_catalog_flag"] is False
    assert any("not Completed" in w for w in report["warnings"])
    web.close()


def test_ambiguous_match_not_fabricated(regional_service):
    d = DiscoveryService(
        regional_service,
        OfficialWebClient(
            regional_service.settings,
            httpx.MockTransport(lambda r: httpx.Response(200, text=detail_html())),
        ),
    )
    s = next(s for s in d.selection(["NG"], "ssa")["surveys"] if s["id"] == "NG2025DHS")
    other = copy.deepcopy(s)
    other["id"] = "ambiguous"
    result = d._detail(
        {
            "report_id": "PR166",
            "catalog_url": "https://dhsprogram.com/publications/publication-PR166-reports.cfm",
            "country_id": "NG",
        },
        [s, other],
    )
    assert result["survey_id"] is None and result["match_status"] == "ambiguous"
    d.web.close()


def test_lineage_preserves_preliminary_revised_final():
    reports = [
        {
            "report_id": code,
            "survey_id": "NG2025DHS",
            "country_id": "NG",
            "publication_date": date,
            "report_type": kind,
        }
        for code, date, kind in [
            ("PR166", "2026-07", "Preliminary"),
            ("FR999", "2027-01", "Final"),
            ("FR999R", "2027-03", "Revised final"),
        ]
    ]
    group = lineage(reports)["NG2025DHS"]
    assert len(group["sources"]) == 3 and group["relationship"] == "needs_reconciliation"
    assert latest_by_country(reports, ["NG"])[0]["latest_known_report"]["report_id"] == "FR999R"
    assert source_state({"download_verified": True}, False) == [
        "OFFICIAL_REPORT_AVAILABLE_API_PENDING"
    ]
    assert source_state({}, error=True) == ["API_RETRIEVAL_FAILED"]


def test_resume_idempotent_and_survey_no_indicator_distinct(regional_service):
    manager = RegionalService(regional_service)
    result = manager.run(
        indicator_ids=["CH_VACC_C_DP3"],
        country_ids=["NG", "KE"],
        max_tasks=1,
        include_publications=False,
    )
    assert result.data["progress"]["completed"] == 1 and result.data["progress"]["pending"] == 1
    run_id = result.data["run_id"]
    assert manager.run(run_id=run_id, max_tasks=1, include_publications=False).data["progress"][
        "indicator_extraction_complete"
    ]
    run = manager.load(run_id)
    before = [(t["project_id"], t["attempts"]) for t in run["tasks"]]
    manager.run(run_id=run_id, include_publications=False)
    assert before == [(t["project_id"], t["attempts"]) for t in manager.load(run_id)["tasks"]]
    assert any(
        a["status"] == "AVAILABLE_SURVEY_NO_INDICATOR_DATA"
        for a in manager.materialize(run)["availability"]
    )
    with pytest.raises(ValueError, match="differ"):
        manager.run(run_id=run_id, indicator_ids=["different"], include_publications=False)


def test_failure_does_not_become_no_data_and_can_resume(regional_service, monkeypatch):
    original = regional_service.get_indicator_series

    def fail(*args, **kwargs):
        raise DHSError("intermittent fixture failure")

    monkeypatch.setattr(regional_service, "get_indicator_series", fail)
    manager = RegionalService(regional_service)
    result = manager.run(
        indicator_ids=["CH_VACC_C_DP3"], country_ids=["NG"], include_publications=False
    )
    run = manager.load(result.data["run_id"])
    assert result.data["progress"]["failed"] == 1
    assert all(
        a["status"] == "API_RETRIEVAL_FAILED" for a in manager.materialize(run)["availability"]
    )
    monkeypatch.setattr(regional_service, "get_indicator_series", original)
    assert (
        manager.run(run_id=run["run_id"], include_publications=False).data["progress"]["completed"]
        == 1
    )


def test_duplicate_page_rejected(settings):
    def handler(req):
        return httpx.Response(
            200,
            json={
                "Data": [{"same": 1}],
                "Page": req.url.params["page"],
                "TotalPages": 2,
                "RecordCount": 2,
                "RecordsReturned": 1,
            },
        )

    with (
        DHSClient(settings, httpx.MockTransport(handler)) as client,
        pytest.raises(DHSError, match="Repeated"),
    ):
        client.fetch("countries")


def test_regional_bundle_hashes_no_overwrite(regional_service):
    result = RegionalService(regional_service).run(
        indicator_ids=["CH_VACC_C_DP3"], country_ids=["NG"], include_publications=False
    )
    exported = regional_service.export_regional_project(result.data["run_id"], "regional-test")
    path = Path(exported.data["path"])
    manifest = json.loads((path / "ssa_run_manifest.json").read_text(encoding="utf-8"))
    assert all(
        digest((path / name).read_bytes()) == sha for name, sha in manifest["checksums"].items()
    )
    assert (path / "ssa_analysis.ipynb").exists()
    with pytest.raises(FileExistsError):
        regional_service.export_regional_project(result.data["run_id"], "regional-test")


def test_verified_three_country_publication_cases():
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/ssa/verified_publication_cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert {r["country_id"] for r in fixture["cases"]} == {"NG", "CG", "RW"}
    assert len({r["report_type"] for r in fixture["cases"]}) >= 2
    report = fixture["PR166_verification"]
    assert report["survey_id"] == "NG2025DHS" and report["publication_date"] == "2026-07"
    assert report["pdf_verification"]["cover_date"] == "2026-06"
    assert report["pdf_verification"]["fieldwork_sentence"]["start"] == "2025-12-08"
    assert not report["pdf_verification"]["numeric_estimates_extracted"]


def test_pdf_complex_layout_never_emits_estimates():
    import io

    pytest.importorskip("pypdf")
    from pypdf import PdfWriter

    from surveybridge.services.report_verification import inspect_pdf

    writer = PdfWriter()
    writer.add_blank_page(width=900, height=600)
    stream = io.BytesIO()
    writer.write(stream)
    report = inspect_pdf(stream.getvalue())
    assert not report["numeric_estimates_extracted"] and report["cover_date"] is None
    assert "extraction disabled" in report["tables"]
    with pytest.raises(ValueError, match="could not be verified"):
        inspect_pdf(b"%PDF-invalid")


def test_publication_failures_preserve_country_refresh_state(regional_service):
    web = OfficialWebClient(
        regional_service.settings, httpx.MockTransport(lambda r: httpx.Response(403))
    )
    result = DiscoveryService(regional_service, web).list_publications(country_ids=["NG"])
    assert not result.data["source_completeness"]["official_web_scan_complete"]
    assert result.data["country_checks"][0]["status"] == "SOURCE_UNVERIFIED"
    web.close()


def test_web_retry_cache_and_caps(settings):
    settings.retries = 1
    calls, waits = [], []

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "1"})
            if len(calls) == 1
            else httpx.Response(200, text="catalog")
        )

    web = OfficialWebClient(settings, httpx.MockTransport(handler), sleep=waits.append)
    body, source = web.get("https://dhsprogram.com/publications/index.cfm")
    again, cached = web.get("https://dhsprogram.com/publications/index.cfm")
    assert body == again and source == cached and waits == [1]
    settings.max_web_requests = 1
    with pytest.raises(DHSError, match="cap"):
        web.get("https://dhsprogram.com/publications/another.cfm")
    web.close()


def test_additive_tools_real_stdio_offline(regional_service):
    import asyncio
    import os
    import sys

    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    web = OfficialWebClient(
        regional_service.settings,
        httpx.MockTransport(
            lambda r: httpx.Response(
                200, text=detail_html() if "publication-PR166" in r.url.path else catalog_html()
            )
        ),
    )
    discovery = DiscoveryService(regional_service, web)
    discovery.list_publications(country_ids=["NG"])
    discovery.get_report_metadata("https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf")
    regional_service.get_indicator_series("CH_VACC_C_DP3", ["NG"])
    web.close()

    async def run():
        env = {
            **os.environ,
            "SURVEYBRIDGE_WORKSPACE": str(regional_service.settings.workspace),
            "SURVEYBRIDGE_OUTPUT_ROOT": str(regional_service.settings.output_root),
            "SURVEYBRIDGE_OFFLINE": "1",
        }
        params = StdioServerParameters(
            command=os.getenv("SURVEYBRIDGE_TEST_PYTHON", sys.executable),
            args=["-m", "surveybridge.mcp_server"],
            env=env,
        )
        async with (
            stdio_client(params) as streams,
            ClientSession(*streams, read_timeout_seconds=20) as session,
        ):
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            assert len(tools) == 11
            for name, arguments in [
                ("surveybridge_list_countries", {"region": "ssa"}),
                ("surveybridge_list_publications", {"country_ids": ["NG"]}),
                (
                    "surveybridge_get_report_metadata",
                    {"report_url": "https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf"},
                ),
            ]:
                result = await session.call_tool(name, arguments)
                assert result.structured_content["status"] == "ok", result
            result = await session.call_tool(
                "surveybridge_run_regional_project",
                {
                    "country_ids": ["NG"],
                    "indicator_ids": ["CH_VACC_C_DP3"],
                    "include_publications": False,
                },
            )
            assert result.structured_content["status"] == "ok", result
            run_id = result.structured_content["data"]["run_id"]
            result = await session.call_tool(
                "surveybridge_export_regional_project",
                {"run_id": run_id, "output_dir": "stdio-regional"},
            )
            assert result.structured_content["status"] == "ok", result

    asyncio.run(asyncio.wait_for(run(), timeout=45))

import json
from pathlib import Path

import httpx
import pytest

from surveybridge.clients.dhs import DHSClient
from surveybridge.config import Settings
from surveybridge.services.application import ResearchService

EVIDENCE = Path(__file__).resolve().parents[1] / "docs" / "evidence"


@pytest.fixture
def settings(tmp_path):
    return Settings(workspace=tmp_path / "state", output_root=tmp_path / "outputs", retries=0)


@pytest.fixture
def source_payloads():
    catalog = json.loads((EVIDENCE / "indicator_catalog.json").read_text())
    return {
        "countries": [
            {"DHS_CountryCode": c, "CountryName": n}
            for c, n in [("NG", "Nigeria"), ("KE", "Kenya"), ("UG", "Uganda"), ("TZ", "Tanzania")]
        ],
        "surveys": json.loads((EVIDENCE / "surveys-four-country.json").read_text())["Data"],
        "indicators": [
            r for r in catalog["Data"] if r["IndicatorId"] in {"CH_VACC_C_DP3", "CH_VACC_C_MSL"}
        ],
        "data": json.loads((EVIDENCE / "data-immunization.json").read_text())["Data"],
    }


@pytest.fixture
def service(settings, source_payloads):
    def handler(request):
        endpoint = request.url.path.rsplit("/", 1)[-1]
        rows = source_payloads[endpoint]
        params = request.url.params
        if params.get("indicatorIds"):
            rows = [r for r in rows if r.get("IndicatorId") in params["indicatorIds"].split(",")]
        if params.get("countryIds"):
            rows = [r for r in rows if r.get("DHS_CountryCode") in params["countryIds"].split(",")]
        if params.get("surveyYearStart"):
            rows = [r for r in rows if int(r["SurveyYear"]) >= int(params["surveyYearStart"])]
        if params.get("surveyYearEnd"):
            rows = [r for r in rows if int(r["SurveyYear"]) <= int(params["surveyYearEnd"])]
        return httpx.Response(
            200,
            json={
                "Data": rows,
                "TotalPages": 1,
                "Page": "1",
                "RecordCount": len(rows),
                "RecordsReturned": len(rows),
            },
        )

    client = DHSClient(settings, transport=httpx.MockTransport(handler))
    result = ResearchService(settings, client=client)
    yield result
    result.close()


@pytest.fixture
def project(service):
    result = service.get_indicator_series("CH_VACC_C_DP3", ["NG", "KE", "UG", "TZ"])
    return service.load(result.data["project_id"])

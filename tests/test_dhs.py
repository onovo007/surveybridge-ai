import json

import httpx
import pytest

from surveybridge.clients.dhs import DHSClient, DHSError
from surveybridge.config import Settings


def payload(rows=None, page=1, total=1, count=None):
    rows = rows if rows is not None else [{"id": page}]
    return {
        "Data": rows,
        "Page": str(page),
        "TotalPages": total,
        "RecordCount": len(rows) if count is None else count,
        "RecordsReturned": len(rows),
    }


def test_pages_cache_and_original_timestamps(settings):
    calls = []

    def handler(req):
        page = int(req.url.params["page"])
        calls.append(page)
        return httpx.Response(200, json=payload(page=page, total=2, count=2))

    with DHSClient(settings, httpx.MockTransport(handler)) as client:
        rows, pages = client.fetch("countries")
        again, cached = client.fetch("countries")
    assert calls == [1, 2]
    assert len(rows) == 2
    assert again == rows
    assert all(p["cache_hit"] for p in cached)
    assert pages[0]["retrieved_utc"] == cached[0]["retrieved_utc"]


@pytest.mark.parametrize("code", [429, 500, 503])
def test_retry_after(settings, code):
    settings.retries = 2
    waits, calls = [], []

    def handler(req):
        calls.append(req)
        return (
            httpx.Response(code, headers={"Retry-After": "2"})
            if len(calls) == 1
            else httpx.Response(200, json=payload())
        )

    with DHSClient(settings, httpx.MockTransport(handler), sleep=waits.append) as client:
        rows, _ = client.fetch("countries")
    assert len(calls) == 2 and waits == [2]
    assert len(rows) == 1


def test_http_date_retry_and_timeout(settings):
    settings.retries = 1
    waits, calls = [], []

    def handler(req):
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ReadTimeout("test")
        return httpx.Response(200, json=payload())

    with DHSClient(settings, httpx.MockTransport(handler), sleep=waits.append) as client:
        client.fetch("countries")
    assert waits == [1]


def test_nonretryable_redirect_and_bad_json(settings):
    for response in [
        httpx.Response(403),
        httpx.Response(302, headers={"Location": "https://evil.example"}),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"wrong": []}),
    ]:
        with (
            DHSClient(
                settings, httpx.MockTransport(lambda r, response=response: response)
            ) as client,
            pytest.raises(DHSError),
        ):
            client.fetch("countries")


def test_pagination_bound_fails_without_partial_extract(settings):
    settings.max_pages = 1
    with (
        DHSClient(
            settings,
            httpx.MockTransport(lambda r: httpx.Response(200, json=payload(total=2, count=2))),
        ) as client,
        pytest.raises(DHSError, match="Pagination limit"),
    ):
        client.fetch("countries")


@pytest.mark.parametrize(
    "body", [payload(page=2), payload(count=9), {"Data": [], "Page": 1}, payload(total=-1)]
)
def test_malformed_pagination(settings, body):
    with (
        DHSClient(
            settings, httpx.MockTransport(lambda r: httpx.Response(200, json=body))
        ) as client,
        pytest.raises(DHSError),
    ):
        client.fetch("countries")


def test_offline_cache_miss_and_corruption(settings):
    settings.offline = True
    with DHSClient(settings) as client, pytest.raises(DHSError, match="Offline"):
        client.fetch("countries")
    settings.offline = False
    with DHSClient(
        settings, httpx.MockTransport(lambda r: httpx.Response(200, json=payload()))
    ) as client:
        client.fetch("countries")
        path = next((settings.workspace / "cache").glob("*.json"))
        item = json.loads(path.read_text())
        item["body_hex"] = b"changed".hex()
        path.write_text(json.dumps(item))
        with pytest.raises(ValueError, match="integrity"):
            client.fetch("countries")


def test_origin_endpoint_and_filter_restrictions(settings):
    with pytest.raises(ValueError):
        Settings(base_url="https://evil.example")
    with DHSClient(settings) as client:
        for endpoint, params in [
            ("datasets", {}),
            ("../countries", {}),
            ("countries", {"apiKey": "secret"}),
            ("data", {}),
        ]:
            with pytest.raises(ValueError):
                client.fetch(endpoint, params)

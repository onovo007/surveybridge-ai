"""Verified DHS REST adapter. No authentication, redirects or protected endpoints."""

import json
import logging
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

from surveybridge.config import Settings
from surveybridge.utils.cache import ResponseCache, canonical, digest

log = logging.getLogger(__name__)
ENDPOINTS = {"countries", "surveys", "indicators", "data", "publications"}


class DHSError(RuntimeError):
    """A bounded source retrieval or schema failure."""


class DHSClient:
    def __init__(self, settings: Settings | None = None, transport=None, sleep=time.sleep):
        self.settings = settings or Settings()
        self.http = httpx.Client(
            timeout=self.settings.timeout,
            follow_redirects=False,
            transport=transport,
            headers={"User-Agent": "SurveyBridge-AI/0.1 (public aggregate research)"},
        )
        self.cache = ResponseCache(self.settings.workspace / "cache")
        self.sleep = sleep

    def close(self):
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _page(self, endpoint, params):
        url = str(httpx.URL(f"{self.settings.base_url}/{endpoint}", params=params))
        cached = self.cache.get(url, self.settings.cache_seconds, self.settings.offline)
        if cached is not None:
            return cached, True
        if self.settings.offline:
            raise DHSError("Offline cache miss; run the same query online first")
        for attempt in range(self.settings.retries + 1):
            response = None
            try:
                response = self.http.get(url)
                if response.status_code == 429 or 500 <= response.status_code <= 599:
                    response.raise_for_status()
                response.raise_for_status()
                # Validate before caching; never cache an HTML error as data.
                payload = response.json()
                if not isinstance(payload, dict) or not isinstance(payload.get("Data"), list):
                    raise DHSError("Unexpected DHS response schema")
                return self.cache.put(url, response.content), False
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                retryable = (
                    response is None or response.status_code == 429 or response.status_code >= 500
                )
                if not retryable or attempt == self.settings.retries:
                    raise DHSError(
                        f"DHS request failed ({type(exc).__name__}); endpoint={endpoint}"
                    ) from exc
                delay = min(2**attempt, 30)
                if response is not None and response.headers.get("Retry-After"):
                    value = response.headers["Retry-After"]
                    try:
                        delay = float(value)
                    except ValueError:
                        try:
                            delay = (
                                parsedate_to_datetime(value) - datetime.now(UTC)
                            ).total_seconds()
                        except (ValueError, TypeError):
                            pass
                log.warning(
                    json.dumps({"event": "dhs_retry", "endpoint": endpoint, "attempt": attempt + 1})
                )
                self.sleep(max(0, min(delay, 60)))
            except (ValueError, TypeError) as exc:
                raise DHSError("Invalid DHS JSON response") from exc
        raise DHSError("Retry budget exhausted")

    def fetch(self, endpoint: str, params: dict | None = None):
        if endpoint not in ENDPOINTS:
            raise ValueError("Endpoint not allowed")
        params = dict(params or {})
        allowed = {
            "countryIds",
            "indicatorIds",
            "surveyIds",
            "surveyYearStart",
            "surveyYearEnd",
            "surveyType",
            "surveyStatus",
            "breakdown",
        }
        if set(params) - allowed:
            raise ValueError("Unsupported query parameter")
        if endpoint == "data" and not any(
            params.get(k) for k in ("countryIds", "indicatorIds", "surveyIds")
        ):
            raise ValueError("DHS data requires country, indicator or survey filter")
        records, pages = [], []
        seen_pages = set()
        total_records, total_pages = None, None
        for page in range(1, self.settings.max_pages + 1):
            item, hit = self._page(
                endpoint, {**params, "f": "json", "perpage": self.settings.per_page, "page": page}
            )
            payload = json.loads(bytes.fromhex(item["body_hex"]))
            signature = digest(canonical(payload.get("Data")))
            if payload.get("Data") and signature in seen_pages:
                raise DHSError("Repeated DHS page content; refusing duplicate pagination")
            seen_pages.add(signature)
            try:
                reported_page = int(payload["Page"])
                reported_total = int(payload["TotalPages"])
                count = int(payload["RecordCount"])
                if reported_page != page or reported_total < 0 or count < 0:
                    raise ValueError
                if int(payload["RecordsReturned"]) != len(payload["Data"]):
                    raise ValueError
                if total_records is not None and (
                    count != total_records or reported_total != total_pages
                ):
                    raise ValueError
                total_records, total_pages = count, reported_total
            except (KeyError, TypeError, ValueError) as exc:
                raise DHSError("Inconsistent DHS pagination; refusing incomplete extract") from exc
            source = {k: item[k] for k in ("url", "retrieved_utc", "sha256")}
            source.update({"page": page, "cache_hit": hit})
            pages.append({**source, "body_hex": item["body_hex"]})
            for raw in payload["Data"]:
                if not isinstance(raw, dict):
                    raise DHSError("DHS data row must be an object")
                records.append(
                    {
                        "raw": raw,
                        "source_url": item["url"],
                        "retrieved_utc": item["retrieved_utc"],
                        "source_response_hash": item["sha256"],
                        "source_record_hash": digest(canonical(raw)),
                    }
                )
            if page >= total_pages:
                if len(records) != total_records:
                    raise DHSError("Record count mismatch; refusing incomplete extract")
                return records, pages
        raise DHSError("Pagination limit reached; narrow the query (no partial project saved)")

"""Bounded public DHS metadata/report access; redirects stay on official hosts."""

import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx

from surveybridge.clients.dhs import DHSError
from surveybridge.utils.cache import ResponseCache, digest


def official_url(url):
    p = urlsplit(url)
    if (
        p.scheme != "https"
        or p.hostname not in {"dhsprogram.com", "www.dhsprogram.com"}
        or p.username
        or p.password
        or p.port not in {None, 443}
    ):
        raise ValueError("Only official public HTTPS DHS report/catalog links are allowed")
    if (
        not p.path.lower().startswith(
            ("/publications/", "/pubs/pdf/", "/methodology/survey/", "/countries/")
        )
        or ".." in p.path
        or "%" in p.path
    ):
        raise ValueError("Public report/catalog path not allowed")
    return url


class OfficialWebClient:
    def __init__(self, settings, transport=None, sleep=time.sleep):
        self.settings = settings
        self.http = httpx.Client(
            timeout=settings.timeout, follow_redirects=False, transport=transport
        )
        self.cache = ResponseCache(settings.workspace / "web-cache")
        self.sleep = sleep
        self.requests = 0

    def close(self):
        self.http.close()

    def get(self, url, *, pdf=False, prefix_only=False):
        url = official_url(url)
        if not pdf:
            cached = self.cache.get(url, self.settings.cache_seconds, self.settings.offline)
            if cached:
                return bytes.fromhex(cached["body_hex"]), {
                    k: cached[k] for k in ("url", "sha256", "retrieved_utc")
                }
        if self.settings.offline:
            raise DHSError("Offline official-web cache miss; PDF bodies are never cached")
        if self.requests >= self.settings.max_web_requests:
            raise DHSError("Official-web request cap reached; raise cap and resume discovery")
        origin = url
        for _hop in range(4):
            redirected = False
            for attempt in range(self.settings.retries + 1):
                self.requests += 1
                if self.requests > self.settings.max_web_requests:
                    raise DHSError("Official-web request cap reached")
                try:
                    with self.http.stream("GET", url) as response:
                        if response.is_redirect:
                            url = official_url(
                                str(response.url.join(response.headers.get("Location", "")))
                            )
                            redirected = True
                            break
                        response.raise_for_status()
                        cap = (
                            1024
                            if prefix_only
                            else self.settings.max_report_bytes
                            if pdf
                            else self.settings.max_catalog_bytes
                        )
                        body = bytearray()
                        for chunk in response.iter_bytes(chunk_size=1024 if prefix_only else 65536):
                            body.extend(chunk)
                            if prefix_only:
                                break
                            if len(body) > cap:
                                raise DHSError("Official source exceeds configured byte cap")
                        body = bytes(body)
                        if pdf and not body.startswith(b"%PDF-"):
                            raise DHSError("Official report link did not return a PDF")
                        if not pdf:
                            item = self.cache.put(origin, body)
                            return body, {k: item[k] for k in ("url", "sha256", "retrieved_utc")}
                        return body, {
                            "url": origin,
                            "resolved_url": url,
                            "sha256": digest(body),
                            "retrieved_utc": datetime.now(UTC).isoformat(),
                            "prefix_only": prefix_only,
                        }
                except (httpx.HTTPError, OSError) as exc:
                    response = getattr(exc, "response", None)
                    code = response.status_code if response is not None else None
                    if attempt == self.settings.retries or (
                        code is not None and code != 429 and code < 500
                    ):
                        raise DHSError(
                            f"Official source access failed: {type(exc).__name__}; HTTP {code}"
                        ) from exc
                    delay = 2**attempt
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
                    self.sleep(max(0, min(delay, 60)))
            if not redirected:
                break
        raise DHSError("Too many official report redirects")

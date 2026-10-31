"""Fetch small official source probes. Raw PDFs stay in ignored local storage."""

import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
out = root / ".tmp/ssa-source-probes"
out.mkdir(parents=True, exist_ok=True)
urls = {
    "publication-docs.html": "https://api.dhsprogram.com/html/api-publications.cfm",
    "country-fields.json": "https://api.dhsprogram.com/rest/dhs/countries/fields?f=json",
    "publications-fields.json": "https://api.dhsprogram.com/rest/dhs/publications/fields?f=json",
    "publications-sample.json": "https://api.dhsprogram.com/rest/dhs/publications?f=json&perpage=1",
    "countries.json": "https://api.dhsprogram.com/rest/dhs/countries?f=json&perpage=1000",
    "surveys.json": "https://api.dhsprogram.com/rest/dhs/surveys?f=json&perpage=1000&surveyStatus=all",
    "unm49.html": "https://unstats.un.org/unsd/methodology/m49/overview/",
    "PR166.pdf": "https://dhsprogram.com/pubs/pdf/PR166/PR166.pdf",
    "terms.html": "https://api.dhsprogram.com/html/terms.cfm",
}
report = []
for name, url in urls.items():
    item = {"url": url, "retrieved_utc": datetime.now(UTC).isoformat()}
    try:
        with urlopen(
            Request(
                url, headers={"User-Agent": "SurveyBridge-AI/0.1 public metadata verification"}
            ),
            timeout=45,
        ) as response:
            body = response.read(20_000_001)
            if len(body) > 20_000_000:
                raise ValueError("Probe exceeded 20 MB limit")
            (out / name).write_bytes(body)
            item.update(
                status=response.status,
                bytes=len(body),
                content_type=response.headers.get("Content-Type"),
            )
            if name.endswith(".json"):
                data = json.loads(body)
                print(
                    name, {k: v for k, v in data.items() if k != "Data"}, data.get("Data", [])[:2]
                )
    except (HTTPError, OSError, ValueError) as exc:
        item.update(status="SOURCE_UNVERIFIED", error=str(exc))
    report.append(item)
(out / "probe-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))

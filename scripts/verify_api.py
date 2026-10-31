"""Retrieve official documentation and small public API samples, without credentials."""

import json
import re
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
for name in [
    "js/main.js",
    "introapi.cfm",
    "api-data.cfm",
    "api-indicators.cfm",
    "api-countries.cfm",
    "api-surveys.cfm",
    "terms.cfm",
]:
    url = "https://api.dhsprogram.com/" + (name if name.endswith(".js") else "html/" + name)
    try:
        text = urlopen(url, timeout=45).read().decode()
        (OUT / name.replace("/", "_")).write_text(text, encoding="utf-8")
        plain = re.sub("<[^>]+>", " ", text)
        print(name, re.sub(r"\s+", " ", plain)[:18000])
    except Exception as exc:
        print(name, type(exc).__name__, str(exc))
for endpoint in ["countries", "surveys", "indicators", "data"]:
    url = f"https://api.dhsprogram.com/rest/dhs/{endpoint}?f=json&perpage=1"
    try:
        body = urlopen(url, timeout=45).read()
        (OUT / f"{endpoint}.json").write_bytes(body)
        print(url, json.loads(body))
    except Exception as exc:
        print(endpoint, type(exc).__name__, str(exc))

"""Convert the retrieved official English M49 table to a versioned SSA reference."""

import json
from html.parser import HTMLParser
from pathlib import Path

from surveybridge.utils.cache import digest


class M49Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = self.cell = False
        self.rows, self.row, self.text = [], [], ""

    def handle_starttag(self, tag, attrs):
        if tag == "table" and dict(attrs).get("id") == "downloadTableEN":
            self.active = True
        if not self.active:
            return
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"}:
            self.cell, self.text = True, ""

    def handle_data(self, data):
        if self.active and self.cell:
            self.text += data

    def handle_endtag(self, tag):
        if self.active and tag in {"td", "th"}:
            self.row.append(" ".join(self.text.split()))
            self.cell = False
        if self.active and tag == "tr" and self.row:
            self.rows.append(self.row)
        if tag == "table":
            self.active = False


if __name__ == "__main__":
    body = Path(".tmp/ssa-source-probes/unm49.html").read_bytes()
    parser = M49Parser()
    parser.feed(body.decode("utf-8"))
    rows = [
        {"iso3": r[11], "iso2": r[10], "m49": r[9], "un_name": r[8], "subregion": r[7]}
        for r in parser.rows
        if len(r) >= 12 and r[4] == "202"
    ]
    assert rows and len({r["iso3"] for r in rows}) == len(rows)
    probes = json.loads(
        Path(".tmp/ssa-source-probes/probe-results.json").read_text(encoding="utf-8")
    )
    source = next(p for p in probes if "m49/overview" in p["url"])
    value = {
        "version": "UN-M49-2026-10-31",
        "source_url": source["url"],
        "retrieved_utc": source["retrieved_utc"],
        "source_html_sha256": digest(body),
        "selection": "Sub-region Code = 202",
        "countries": rows,
    }
    target = Path("src/surveybridge/data/un_m49_ssa_2026-10-31.json")
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Official M49 SSA countries/areas:", len(rows))

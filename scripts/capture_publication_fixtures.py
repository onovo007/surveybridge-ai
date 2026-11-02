"""Persist minimal factual metadata cases from verified public sources; never full PDFs."""

import json
from pathlib import Path

pilot = json.loads(Path(".tmp/ssa-discovery-pilot.json").read_text(encoding="utf-8"))
verified = json.loads(Path(".tmp/pr166-verified-metadata.json").read_text(encoding="utf-8"))
cases = [r for r in pilot["data"]["publications"] if r["report_id"] in {"PR166", "PR167", "FR401"}]
target = Path("tests/fixtures/ssa")
target.mkdir(parents=True, exist_ok=True)
(target / "verified_publication_cases.json").write_text(
    json.dumps(
        {
            "cases": cases,
            "PR166_verification": verified["data"],
            "note": "Factual metadata and public source hashes only; no redistributed PDF or report estimates",
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(
    "Archived cases:", [(r["country_id"], r["report_id"], r.get("publication_date")) for r in cases]
)

"""Inspect official public catalog links without accessing restricted content."""

import re
from pathlib import Path
from urllib.request import urlopen

out = Path(".tmp/ssa-source-probes")
for name, url in [
    ("publication-search.html", "https://dhsprogram.com/publications/Publication-Search.cfm"),
    ("publication-index.html", "https://dhsprogram.com/publications/index.cfm"),
]:
    body = urlopen(url, timeout=45).read()
    (out / name).write_bytes(body)
    text = body.decode("utf-8", errors="replace")
    print(
        name,
        "LINKS",
        [s for s in re.findall(r"""href=["']([^"']+)""", text) if "publication-" in s.lower()][:30],
    )
    print("SCRIPTS", re.findall(r"""src=["']([^"']+\.js[^"']*)""", text)[-20:])

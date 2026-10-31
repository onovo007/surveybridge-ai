"""Execute the archived demo offline and save a separate verification artifact."""

import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
bundle = root / "examples/outputs/four-country-immunization-v01"
notebook = nbformat.read(bundle / "analysis.ipynb", as_version=4)
client = NotebookClient(
    notebook, timeout=120, kernel_name="surveybridge", resources={"metadata": {"path": str(bundle)}}
)
client.execute()
out = root / "examples/verification"
out.mkdir(parents=True, exist_ok=True)
nbformat.write(notebook, out / "analysis.executed.ipynb")
report = {
    "code_cells": sum(c.cell_type == "code" for c in notebook.cells),
    "errors": [
        o
        for c in notebook.cells
        if c.cell_type == "code"
        for o in c.outputs
        if o.output_type == "error"
    ],
    "mode": "offline local archive; no remote code or data retrieval",
}
(out / "notebook_execution.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))

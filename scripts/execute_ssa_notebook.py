"""Execute regional notebook without changing its checksum-addressed bundle."""

import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
bundle = root / "examples/outputs/ssa-publications-review-2026-10-31"
notebook = nbformat.read(bundle / "ssa_analysis.ipynb", as_version=4)
NotebookClient(
    notebook, timeout=180, kernel_name="surveybridge", resources={"metadata": {"path": str(bundle)}}
).execute()
out = root / "examples/verification/ssa"
out.mkdir(parents=True, exist_ok=True)
nbformat.write(notebook, out / "ssa_analysis.executed.ipynb")
report = {
    "code_cells": sum(c.cell_type == "code" for c in notebook.cells),
    "errors": [
        o
        for c in notebook.cells
        if c.cell_type == "code"
        for o in c.outputs
        if o.output_type == "error"
    ],
    "mode": "offline hash/source-lineage verification and descriptive record-count chart",
}
(out / "notebook_execution.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))

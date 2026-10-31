# Install SurveyBridge AI

Requires Python 3.11 or later, internet for initial dependency installation/live retrieval, and local disk space for research archives. No DHS, OpenAI or Anthropic credential is needed by SurveyBridge. Your agent host may have its own account requirements.

## Public beta

For the SSA/publication development branch, follow [the extension guide](SSA_PUBLICATIONS_GUIDE.md) and install `.[reports,analysis,dev]` from that branch. Publication and regional-run tools are additive; the beta installation commands below remain valid for v0.1.0-beta.1.

Clone [onovo007/surveybridge-ai](https://github.com/onovo007/surveybridge-ai) for the complete skills, demonstration and documentation. The runtime can be installed directly from the beta tag:

```sh
python -m pip install "git+https://github.com/onovo007/surveybridge-ai.git@v0.1.0-beta.1"
```

Alternatively download the wheel from the [beta release](https://github.com/onovo007/surveybridge-ai/releases/tag/v0.1.0-beta.1) and install it with pip. No PyPI release is claimed. The CI workflow is supplied as an inactive template pending GitHub workflow permission; see [activation steps](../ci/README.md).

## Windows PowerShell

From the extracted source directory:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\surveybridge.exe healthcheck
.venv\Scripts\surveybridge.exe indicators "DPT 3"
```

Activation is optional; using explicit executables avoids PowerShell execution-policy changes. If the machine blocks its default temporary directory, point `TEMP` and `TMP` at a writable local folder before creating/installing the environment. Keep all dependencies inside the project's venv.

## macOS and Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/surveybridge healthcheck
.venv/bin/surveybridge indicators 'DPT 3'
```

Some Linux distributions package `venv` separately; install the distribution's matching Python venv package if needed. Runtime-only installation can omit `[dev]`. For a release wheel use `python -m pip install /absolute/path/to/surveybridge_ai-0.1.0-py3-none-any.whl`. There is no claim that `pip install surveybridge-ai` resolves a published release yet.

The package declares compatible dependency bounds. `requirements-windows-py312.lock.txt` captures the exact tested development environment; use it only on matching Windows/Python 3.12 systems, then install the project with `--no-deps`. Other OS/Python combinations should resolve from pyproject.toml and verify with tests. This environment snapshot is not a universal multi-platform lock.

## Register the stdio MCP server

Use absolute paths to the installed Python executable and state/output directories. Examples below are patterns: replace paths with the installation locations on your machine.

Codex CLI:

```powershell
codex mcp add surveybridge --env SURVEYBRIDGE_WORKSPACE=C:/Research/SurveyBridge/state --env SURVEYBRIDGE_OUTPUT_ROOT=C:/Research/SurveyBridge/outputs -- C:/Research/SurveyBridge/.venv/Scripts/python.exe -m surveybridge.mcp_server
codex mcp get surveybridge
```

macOS/Linux equivalent:

```sh
codex mcp add surveybridge --env SURVEYBRIDGE_WORKSPACE=/absolute/research/state --env SURVEYBRIDGE_OUTPUT_ROOT=/absolute/research/outputs -- /absolute/surveybridge/.venv/bin/python -m surveybridge.mcp_server
```

Claude Code:

```sh
claude mcp add --transport stdio --scope project --env SURVEYBRIDGE_WORKSPACE=/absolute/research/state --env SURVEYBRIDGE_OUTPUT_ROOT=/absolute/research/outputs surveybridge -- /absolute/surveybridge/.venv/bin/python -m surveybridge.mcp_server
claude mcp get surveybridge
```

On Windows use the venv's `Scripts/python.exe` and Windows paths. For any MCP-compatible host, configure a stdio command with separate arguments:

```json
{
  "mcpServers": {
    "surveybridge": {
      "command": "/absolute/surveybridge/.venv/bin/python",
      "args": ["-m", "surveybridge.mcp_server"],
      "env": {
        "SURVEYBRIDGE_WORKSPACE": "/absolute/research/state",
        "SURVEYBRIDGE_OUTPUT_ROOT": "/absolute/research/outputs"
      }
    }
  }
}
```

The supplied `.mcp.json` and portable `mcp.json` use `surveybridge-mcp`, requiring that executable on the host's PATH. You can instead adapt them to absolute interpreter paths. Do not pass credentials. Relative output directories resolve below the configured output root. The server opens no listening network port.

## Skills and plugins

In this checkout, Codex discovers `.agents/skills/surveybridge/SKILL.md` and Claude Code discovers `.claude/skills/surveybridge/SKILL.md`. Restart/reload the relevant host after adding a skill if it has not refreshed. Invoke `$surveybridge` in Codex or `/surveybridge` in Claude Code. For another research repository, copy the canonical `skills/surveybridge/` folder into its corresponding skill directory, then register the MCP server separately.

Claude plugin validation and session loading:

```sh
claude plugin validate /absolute/surveybridge
claude --plugin-dir /absolute/surveybridge
```

Use the repository skill path for direct skill discovery, or the plugin's root `skills/` for plugin loading; avoid duplicate installation in the same host. Plugin users invoke its namespaced skill as shown by the host. The portable OpenAI manifest follows the current official packaging format; marketplace publication is separate. Direct repo skill plus MCP registration is the simplest local setup. Host manifests do not substitute for Python package installation.

Try: “Use SurveyBridge to discover DPT 3 vaccination indicators for Nigeria, Kenya, Uganda and Tanzania. Explain candidate definitions, retrieve national estimates for all available rounds, assess each indicator, and export a documented research bundle.” Confirm that the host sees seven tools and that the reported warnings match the exported assessment.

## Demo and offline reproduction

```sh
python scripts/run_demo.py --output my-live-run
python scripts/run_demo.py --replay examples/outputs/four-country-immunization-v01/project.json --output my-offline-replay
```

These write below `examples/outputs/` and refuse existing output names. Open the exported notebook in Jupyter using this Python environment, with working directory set to the bundle. It verifies all original output hashes and reconstructs normalization from raw responses. Saving an edited/executed notebook inside the original bundle intentionally changes its checksum; keep executed copies elsewhere. A separately executed verification notebook is supplied under `examples/verification/`.

## Maintenance

Keep the configured workspace stable between sessions. Cache lifetime is 24 hours; cached retrieval times remain unchanged. Set `SURVEYBRIDGE_OFFLINE=1` to forbid network and require exact cache hits. Export bundles remain usable after cache deletion. To refresh source data, retrieve into a new project and export to a new directory. Do not edit project JSON to alter estimates; integrity verification rejects normalized/source mismatches.

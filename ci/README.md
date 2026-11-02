# Cross platform validation

The active workflow is `.github/workflows/ci.yml`; `ci/validation.yml` is its portable template. On 2 November 2026 the owner completed GitHub CLI authorization with `workflow` scope and published it in commit `3c682b2`.

Both initial nine-job validation runs passed across Windows, macOS and Linux with Python 3.11, 3.12 and 3.13:

- [Push validation](https://github.com/onovo007/surveybridge-ai/actions/runs/41405197555)
- [Pull request validation](https://github.com/onovo007/surveybridge-ai/actions/runs/41405197815)

Each job passed all 59 tests, dependency checks, Ruff, skill synchronization, the scientific integrity audit and distribution builds. Actions are pinned to verified commit hashes with read-only repository access. Full Git history enables verification of the archived source-code hashes. Evidence is in `examples/verification/release-2026-11-02/github_ci.json`. Future changes require their own passing checks; CI does not replace host testing or independent researcher acceptance.

## Maintainer authorization and template deployment

Maintainers whose credentials lack workflow permission can authorize it interactively:

```sh
gh auth refresh -h github.com -s workflow
```

Then, from the repository root, copy the template to `.github/workflows/ci.yml` and commit/push it:

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force .github/workflows | Out-Null
Copy-Item ci/validation.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "Activate cross-platform validation workflow"
git push
```

macOS/Linux:

```sh
mkdir -p .github/workflows
cp ci/validation.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "Activate cross-platform validation workflow"
git push
```

The template runs dependency checks, Ruff, skill synchronization, pytest, source integrity review and distribution builds on Windows/macOS/Linux with Python 3.11, 3.12 and 3.13. Review all nine jobs for the current commit. The owner completed account authorization; no credential is embedded in the repository.

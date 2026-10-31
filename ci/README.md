# Activate GitHub Actions

The complete nine-job validation workflow is supplied as `ci/validation.yml`. The publishing OAuth token has repository access but lacks GitHub's `workflow` scope. GitHub rejected a push containing `.github/workflows/ci.yml`; SSH authentication is unavailable. The public beta therefore ships the workflow as an inactive template. No remote CI success is claimed.

Authorize the required scope interactively on your own machine:

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

The template runs dependency checks, Ruff, skill synchronization, pytest and distribution builds on Windows/macOS/Linux with Python 3.11, 3.12 and 3.13. Review all nine jobs before changing the beta's portability claims. Scope changes are an account authorization action and were not performed automatically.

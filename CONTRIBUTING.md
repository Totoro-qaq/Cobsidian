# Contributing

## Branch Model

Use a simple GitHub Flow:

- `main`: stable branch, always releasable
- `feature/<short-name>`: new features
- `fix/<short-name>`: bug fixes
- `docs/<short-name>`: documentation-only changes
- `chore/<short-name>`: tooling, cleanup, CI

Avoid a permanent `dev` branch for this project. The project is small, and a long-running integration branch adds overhead without much benefit.

## Pull Request Rules

Before opening a PR:

1. Run the validation scripts.
2. Keep changes focused on one behavior or document area.
3. Do not include private vault content, personal paths, tokens, screenshots, or unpublished notes.
4. Update examples only with generic sample content.

Suggested checks:

```bash
python skills/cobsidian/scripts/scan_vault.py examples --json
python skills/cobsidian/scripts/find_duplicates.py examples
python skills/cobsidian/scripts/validate_notes.py examples
python skills/cobsidian/scripts/quality_eval.py evals/public-smoke.jsonl evals/fixtures/public-vault --mode-predictions evals/public-mode-predictions.jsonl --json
python install_cobsidian.py --host all --scope user --dry-run --json
```

## Branch Protection Recommendation

For GitHub repository settings:

- protect `main`
- require pull requests before merging
- require CI checks to pass
- enable CodeQL default scanning for Python
- enable Dependabot alerts and GitHub Actions version updates
- require linear history if you prefer clean history
- disallow force pushes to `main`
- disallow deletion of `main`

For a solo maintainer, requiring one approval is optional. CI passing is more important.

## Tags And Releases

Use SemVer-style tags only for useful releases:

- `v0.1.0`: first usable MVP
- `v0.2.0`: new workflow or script capability
- `v1.0.0`: stable public API and documented workflow

Do not tag every commit. Tag when the README, skill, scripts, and examples are consistent and CI passes.

## Commit Style

Use short conventional prefixes:

```text
feat: add backlink suggestions
fix: handle empty markdown files
docs: clarify vault write workflow
chore: add CI validation
```

# GitHub Actions templates

Copy [`doc-lint.yml.template`](doc-lint.yml.template) to
`.github/workflows/bestpractice-docs.yml` in the dependent repository.

The installed workflow runs the vendored linter at
`process/upstream/tools/doc_lint.py` and requires a full-history checkout so
the linter can find Markdown changed relative to the default branch.

See [GitHub Actions checks](../../GITHUB_ACTIONS.md) for installation,
permissions, verification, required-check, update, and manifest guidance.

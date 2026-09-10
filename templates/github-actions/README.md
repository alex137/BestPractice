# GitHub Actions templates

Copy [`doc-lint.yml.template`](doc-lint.yml.template) to
`.github/workflows/bestpractice-docs.yml` in the dependent repository.

The installed workflow **discovers** the vendored linter rather than naming
one path: `process/upstream/tools/doc_lint.py` in an
[INSTALL.md §1](../../INSTALL.md#1-install-into-a-dependent-repo) install,
`tools/doc_lint.py` in a
[§0](../../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)
one, which has no `process/upstream/` at all. Both are watched in its
triggers, so it installs verbatim under either model — before 2026-09-10 it
was hard-coded to §1's path and a §0 install's very first check went red.
It requires a full-history checkout so the linter can find Markdown changed
relative to the default branch.

See [GitHub Actions checks](../../GITHUB_ACTIONS.md) for installation,
permissions, verification, required-check, update, and manifest guidance.

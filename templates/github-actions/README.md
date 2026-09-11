# GitHub Actions templates

Two templates, for two different kinds of repository. Both are read-only:
they report, and neither holds a token that could write
([ci-commits-carry-identity](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/ci-commits-carry-identity.md)).

| Template | Install as | In which repo |
|---|---|---|
| [`doc-lint.yml.template`](doc-lint.yml.template) | `.github/workflows/bestpractice-docs.yml` | any dependent repository |
| [`views-drift.yml.template`](views-drift.yml.template) | `.github/workflows/views-drift.yml` | one that GENERATES its own views — an individual or team practice set, or any repo whose `practices/` it authors itself |

## The Markdown lint template

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

## The generated-views drift template

Copy [`views-drift.yml.template`](views-drift.yml.template) to
`.github/workflows/views-drift.yml`. It runs
`python3 tools/build_views.py --repo . --check`, which exits non-zero when
`AGENTS.md`'s loader block, `MAP.md` or `GLOSSARY.md` has drifted from a
fresh regeneration.

**Why it exists.** Until 2026-09-11 nothing checked a generated view
anywhere but in Precedent's own repo, whose `deep-check.yml` runs
`verify_harness.py` — and that file is deliberately not vendored into a
source set, while `precedent_check.py`'s equivalent check skips itself
there (its practice is universal, and a source set's `practices/` holds only
its own). A real individual set's `MAP.md` sat three practices stale under a
generated header claiming a guard was failing the build on exactly that.

Sets created by
[`tools/precedent_bootstrap_source.py`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_bootstrap_source.py)
get it installed; every set created before that date needs the copy above,
and that tool's `--verify` names it as missing until it is there.

**It refuses rather than passing blind** when the engine is vendored under
`process/upstream/` (a consuming repo, whose `practices/` is materialized
from sources a runner cannot reach), when the loader block turns out to be
built from unreachable sources, or when no engine is vendored at all. The
file's own header says which case is which, and
[GITHUB_ACTIONS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/GITHUB_ACTIONS.md)
covers what gates a consuming repo instead.

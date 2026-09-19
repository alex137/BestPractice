# GitHub Actions templates

Three templates, for two different kinds of repository. All are read-only:
they report, and none holds a token that could write
([ci-commits-carry-identity](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/ci-commits-carry-identity.md)).

| Template | Install as | In which repo |
|---|---|---|
| [`doc-lint.yml.template`](doc-lint.yml.template) | `.github/workflows/bestpractice-docs.yml` | any dependent repository — but only when `ci_workflows: enabled` is declared; see below |
| [`doc-lint-scheduled.yml.template`](doc-lint-scheduled.yml.template) | `.github/workflows/bestpractice-docs.yml` (in place of the row above, never alongside it) | a dependent repository pushed to its default branch very frequently, where per-push billing adds up |
| [`precedent-check.yml.template`](precedent-check.yml.template) | `.github/workflows/precedent-check.yml` | a practice SET only (its own header says why); a consuming repo skips it. Covers the generated-views drift check too (see below) — there is no separate `views-drift.yml.template` any more. |

**Trigger shape, all three (2026-09-19, spec/CI_MINUTES_PLAN.md item 8):**
`pull_request: [opened, synchronize]` plus `push:` scoped to the branch(es)
that actually receive merges — `branches: [main]` as shipped, which each
template's own header says how to widen for a repo whose routine merge
target isn't just `main` (this repo's own copies list
`[main, precedent-beta-v01]`). A branch with no open PR costs nothing at
all; a branch with an open PR gets checked. Read a template's own header
before deviating from this — the shape exists because the two simpler
alternatives (push on every branch, or push scoped to named branches with
no `pull_request:` at all) were each tried here first and each cost
something real: the first billed for branches nobody was reviewing yet,
the second gave up automatic checking on anything short of a merge.

## The Markdown lint template

Copy [`doc-lint.yml.template`](doc-lint.yml.template) to
`.github/workflows/bestpractice-docs.yml` in the dependent repository —
`tools/precedent_install.py` does this automatically once `ci_workflows:
enabled` is declared in the individual or team source it resolves; absent
resolves to disabled, the engine's own default, since GitHub Actions
minutes are metered per private repository. See
[GITHUB_ACTIONS.md](../../GITHUB_ACTIONS.md), "Controlling Actions
Minutes".

The installed workflow **discovers** the vendored linter rather than naming
one path: `process/upstream/tools/doc_lint.py` in an
[INSTALL.md §1](../../INSTALL.md#1-install-into-a-dependent-repo) install,
`tools/doc_lint.py` in a
[§0](../../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)
one, which has no `process/upstream/` at all. Both are watched in its
triggers, so it installs verbatim under either model — before 2026-09-10 it
was hard-coded to §1's path and a §0 install's very first check went red.
It requires a full-history checkout so the linter can find Markdown changed
relative to the default branch. Its `concurrency` block cancels an
in-flight run when a second push on the same branch arrives before it
finishes, so an overlapping pair of pushes bills once rather than twice.

See [GitHub Actions checks](../../GITHUB_ACTIONS.md) for installation,
permissions, verification, required-check, update, and manifest guidance.

## The scheduled Markdown lint template

Copy [`doc-lint-scheduled.yml.template`](doc-lint-scheduled.yml.template) to
`.github/workflows/bestpractice-docs.yml` **in place of**
`doc-lint.yml.template` — never alongside it, which would bill both. Where
the default template bills roughly once per push, this one bills on a
fixed cadence: however many saves land in one window, they cost one run.

**Never installed automatically**, by either the installer or the
`ci_workflows` field: a `schedule:` is a clock in somebody else's
repository that they never picked
([GITHUB_ACTIONS.md](../../GITHUB_ACTIONS.md)'s Limits section). Copying it
in is a deliberate, per-repository choice, and its header cron line is a
starting point to edit, not a shipped default to keep. It gates the
**whole tracked Markdown corpus** on each run rather than "what changed
since the default branch" — its own header explains why the latter is a
silent no-op on a repo pushed straight to its default branch, and what
gating the full corpus trades away on a repo with an existing backlog of
violations.

## The generated-views drift check

**No longer a separate template.** Through 2026-09-19 this was
`views-drift.yml.template`, copied to `.github/workflows/views-drift.yml`
alongside `precedent-check.yml`. It is now the `views-drift` job inside
`precedent-check.yml.template` itself — folded in the same day as the
trigger change above, for the same reason: two separate workflow files each
billed their own one-job-minute floor on every push regardless of what
either one's debounce window decided, and a single file with one shared
debounce job halves that. Installing `precedent-check.yml.template` installs
this check; there is nothing further to copy.

It runs `python3 tools/build_views.py --repo . --check`, which exits
non-zero when [AGENTS.md](../../AGENTS.md)'s loader block,
[MAP.md](../../MAP.md) or [GLOSSARY.md](../../GLOSSARY.md) has drifted
from a fresh regeneration.

**Why it exists.** Until 2026-09-11 nothing checked a generated view
anywhere but in Precedent's own repo, whose `deep-check.yml` runs
`verify_harness.py` — and that file is deliberately not vendored into a
source set, while `precedent_check.py`'s equivalent check skips itself
there (its practice is universal, and a source set's `practices/` holds only
its own). A real individual set's `MAP.md` sat three practices stale under a
generated header claiming a guard was failing the build on exactly that.

Sets created by
[`tools/precedent_bootstrap_source.py`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_bootstrap_source.py)
get it installed; a set created before 2026-09-11 needs `precedent-check.yml`
installed (which now carries this job), and that tool's `--verify` names it
as missing until it is there.

**It refuses rather than passing blind** when the engine is vendored under
`process/upstream/` (a consuming repo, whose `practices/` is materialized
from sources a runner cannot reach), when the loader block turns out to be
built from unreachable sources, or when no engine is vendored at all. The
job's own comments say which case is which, and
[GITHUB_ACTIONS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/GITHUB_ACTIONS.md)
covers what gates a consuming repo instead.

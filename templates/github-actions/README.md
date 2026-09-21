# GitHub Actions templates

Five templates, for two different kinds of repository. All are read-only:
they report, and none holds a token that could write
([ci-commits-carry-identity](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/ci-commits-carry-identity.md)).

| Template | Install as | In which repo |
|---|---|---|
| [`doc-lint.yml.template`](doc-lint.yml.template) | `.github/workflows/bestpractice-docs.yml` | any dependent repository — but only when `ci_workflows: enabled` is declared; see below |
| [`doc-lint-scheduled.yml.template`](doc-lint-scheduled.yml.template) | `.github/workflows/bestpractice-docs.yml` (in place of the row above, never alongside it) | a dependent repository pushed to its default branch very frequently, where per-push billing adds up |
| [`precedent-check.yml.template`](precedent-check.yml.template) | `.github/workflows/precedent-check.yml` | a practice SET only (its own header says why); a consuming repo skips it. Covers the generated-views drift check too (see below) — there is no separate `views-drift.yml.template` any more. |
| [`leak-gate.yml.template`](leak-gate.yml.template) | `.github/workflows/leak-gate.yml` | any dependent repository or practice SET, gated by `ci_workflows` the same as the row above — see below, its trigger shape is deliberately different from the other three |
| [`light-check.yml.template`](light-check.yml.template) | `.github/workflows/light-check.yml` | any dependent repository that declares a light check — **never installed automatically**, and never installed without reading the existing file first; see below |

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

**Runner, all jobs in `doc-lint.yml.template` and `precedent-check.yml.template`
(2026-09-20):** `runs-on: ${{ vars.PRECEDENT_RUNNER || 'ubuntu-latest' }}` —
unset, every job runs on GitHub's own `ubuntu-latest`, same as before. A
repo that declares a `PRECEDENT_RUNNER` repository variable (Settings →
Secrets and variables → Actions → Variables) moves every job in that
workflow onto the named self-hosted runner instead, with no template edit.
This is opt-in per repo, on purpose: it only helps an adopter who already
operates and secures their own runner, and
[GITHUB_ACTIONS.md](../../documentation/GITHUB_ACTIONS.md)'s "Controlling
Actions Minutes" section has the trade-offs (including why a self-hosted
runner is not safe on a repo that takes untrusted forked pull requests).

## The Markdown lint template

Copy [`doc-lint.yml.template`](doc-lint.yml.template) to
`.github/workflows/bestpractice-docs.yml` in the dependent repository —
`tools/precedent_install.py` does this automatically once `ci_workflows:
enabled` is declared in the individual or team source it resolves; absent
resolves to disabled, the engine's own default, since GitHub Actions
minutes are metered per private repository. See
[GITHUB_ACTIONS.md](../../documentation/GITHUB_ACTIONS.md), "Controlling Actions
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

See [GitHub Actions checks](../../documentation/GITHUB_ACTIONS.md) for installation,
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
([GITHUB_ACTIONS.md](../../documentation/GITHUB_ACTIONS.md)'s Limits section). Copying it
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
either one's debounce window decided. Both debounce jobs are gone as of
2026-09-20 (they cost a billed minute to decide not to spend one — see
GITHUB_ACTIONS.md, "Controlling Actions Minutes"), and the merged file ships
a single job. Installing `precedent-check.yml.template` installs
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
[GITHUB_ACTIONS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/documentation/GITHUB_ACTIONS.md)
covers what gates a consuming repo instead.

## The light check template

Copy [`light-check.yml.template`](light-check.yml.template) to
`.github/workflows/light-check.yml` — **by hand, after reading whatever is
already there.** The installer does not place it and `ci_workflows` does
not reach it, for the same reason `doc-lint-scheduled.yml.template` is
never automatic: what it runs is a per-repository decision this repo cannot
make for you.

**Why it exists** ([spec/BILLING_FLOOR.md](../../spec/BILLING_FLOOR.md)).
[two-check-levels](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/two-check-levels.md)
tells every adopter to name a fast check and a full check. This repository
shipped the **rule** and never shipped a **shape**, so twelve repositories
each invented their own `light-check.yml` and not one got the one-job or
`paths:` discipline the other templates here have. Measured on the
2026-09-01..19 usage export: **609 billed minutes across those twelve,
23.5% of the whole account** — the single largest line on the bill. A rule
published without a shape is a rule everybody implements differently and
expensively.

**It refuses to guess what your light check is,** and that refusal is the
template's main feature. `two-check-levels` deliberately does not mandate
the script; those twelve repositories run twelve different things, and at
least one is a live required check. On 2026-09-20 a sweep deleted nine live
checks across nine repositories on the theory that a filename absent from
this tree meant a retired file. So the command is a marked `CUSTOMIZE`
line, and the instruction is to carry across whatever your existing file
ran rather than decide afresh.

**Rule out the duplicate first.** If your light check runs the same script
as `bestpractice-docs.yml` over the same paths on the same triggers, you
are paying two billing floors for one check, and the fix is to delete one —
not to template both.

**The `paths:` filter is the only genuinely free lever in the file**, since
GitHub evaluates it before allocating a runner: a run it skips costs
nothing, where everything else here only makes a run cheaper. The shipped
list is a documentation-shaped starting point and is explicitly not an
answer — a repo whose light check reads Python source wants the Python glob
there, and probably not the Markdown one.

## The leak gate template

Copy [`leak-gate.yml.template`](leak-gate.yml.template) to
`.github/workflows/leak-gate.yml`. First vendored 2026-09-20
([spec/CI_MINUTES_PLAN.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CI_MINUTES_PLAN.md)
item 12) — before that date `leak-gate.yml` existed only in this repo,
un-vendored, run unconditionally on every branch because this repo is
public and a leak here is already published the instant it is pushed.
That reasoning does not transfer to a private dependent repo as-is, so this
template does not just copy this repo's own scope.

**Trigger shape is deliberately NOT the branch-scoped `push:` the other
three templates use.** GitHub Actions evaluates `on:` before any job runs,
from the YAML alone — it cannot read this repo's `precedent.json` at that
point, so "scope the trigger by declared visibility" is not something the
platform lets a template do. Instead the workflow triggers on every push
and pull request, and decides once it is running — visibility taken from
`github.event.repository.private`, which GitHub supplies and no file in the
tree can contradict, with any declaration that disagrees warned about and
overruled. One job: a deciding job costs the same billed minute as the
decision saves, which is why it is a step (spec/BILLING_FLOOR.md).

**If the gate flags a directory your repo legitimately has, declare it.**
The structural path rules were written for this repo — public, universal
practices and nothing else — and a practice SET or a dependent repo can
rightly carry a `candidates/` outbox or similar. Rather than weakening the
rule for a whole class of repo, say once in your own `precedent.json` (or
`precedent-source.json`) why yours is deliberate:

```json
"leak_structural_exempt": [
  {"path": "candidates",
   "reason": "this set's own drafting outbox; reviewed before anything is published"}
]
```

**The reason is mandatory** — an entry without one is ignored, so the
exemption cannot be taken silently. It covers directory (path) rules only
and never file content; it matches at the repo root on a segment boundary,
so `candidates` covers that directory and not a nested `docs/candidates/`;
and it exempts only what it names. Same discipline as
`ci_workflow_outside_vendoring_exempt` above, for the same reason: an
exemption nobody can see is a hole.

**The trade this makes, on a repo declaring `"visibility": "private"`:** a
push to any branch other than `base_branch` skips the server-side scan —
caught only if the local pre-push hook ran. A `pull_request:` event is
never skipped, whatever branch it targets, so a fork's contribution or a
feature branch's merge candidate is always scanned before it lands. On a
public repo (visibility absent or `"public"`), nothing narrows: every push
to every branch is scanned, matching this repo's own `leak-gate.yml`
exactly.

A practice SET has no `precedent.json` — it reads `precedent-source.json`
instead, which always declares `"visibility": "private"`
(`precedent_bootstrap_source.py`'s `_write_source_manifest`), so a set is
always treated as private here; there is no field for it to opt out of.

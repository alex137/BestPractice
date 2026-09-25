# GitHub Actions templates

Three templates, for two different kinds of repository. All are read-only:
they report, and none holds a token that could write
([ci-commits-carry-identity](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/ci-commits-carry-identity.md)).

| Template | Install as | In which repo |
|---|---|---|
| [`precedent-check.yml.template`](precedent-check.yml.template) | `.github/workflows/precedent-check.yml` | a practice SET only (its own header says why); a consuming repo skips it. Covers the generated-views drift check too (see below) — there is no separate `views-drift.yml.template` any more. |
| [`leak-gate.yml.template`](leak-gate.yml.template) | `.github/workflows/leak-gate.yml` | any dependent repository or practice SET, gated by `github_ci_workflows` the same as the row above — see below, its trigger shape is deliberately different from the other three |
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
already there.** The installer does not place it and `github_ci_workflows` does
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

## The Markdown lint is NOT here any more

**Retired 2026-09-21.** `doc-lint.yml.template` (installed as
`bestpractice-docs.yml`) and `doc-lint-scheduled.yml.template` are gone,
and `.github/workflows/bestpractice-docs.yml` is tombstoned in
`precedent_vendor_engine.RETIRED_CI_WORKFLOW_FILES`, so the next
`Update Vendors` deletes it from every repository that installed it.

**The linter is not retired — only the workflow whose whole job was to run
it a second time.** Under this system's founding assumption, every edit
arrives through a cloud session, never a local checkout and never the
GitHub web UI. `doc_lint.py` has therefore already run on every change
before it is committed, and the CI copy was re-checking work the session
in front of the person had just cleared. Measured in one consuming
repository: **350 billed minutes over 19 days** for that re-run, on a
workflow that was already one job with `paths:` filters from the day it
was installed
([spec/BILLING_FLOOR.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/BILLING_FLOOR.md)).

**What replaced it is stricter, not weaker.** "The light check gates a
commit" was written in `AGENTS.md` and followed by sessions, but nothing
refused a commit that skipped it. `.claude/hooks/doc-lint-gate.sh` now
does: a `git commit` whose staged Markdown fails [doc_lint.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/doc_lint.py) is denied,
with the linter's own output handed back. It costs no Actions minutes and
it catches the problem **before** the commit rather than after the push.

**The rule that came out of it: no workflow exists solely to lint
Markdown.**

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

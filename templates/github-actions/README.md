# GitHub Actions templates

Two templates a consuming repo gets, and one that ships nowhere. All are
read-only: they report, and none holds a token that could write
([ci-commits-carry-identity](https://github.com/alex137/BestPractice/blob/staging/practices/ci-commits-carry-identity.md)).

| Template | Install as | In which repo |
|---|---|---|
| [`light-check.yml.template`](light-check.yml.template) | `.github/workflows/light-check.yml` | every consuming repo, by default (a source declaring `"github_ci_workflows": "disabled"` switches it off) -- **engine-owned since 2026-09-27**: each Update Vendors writes it from the template over any hand-made copy; see below |
| [`leak-gate.yml.template`](leak-gate.yml.template) | `.github/workflows/leak-gate.yml` | every consuming repo, on the same terms as the row above |
| [`precedent-check.yml.template`](precedent-check.yml.template) | nothing | no repo since 2026-09-21: a practice set runs no CI (practice `source-sets-run-no-ci`), and its checks run in the session before every push, the generated-views drift check its `views-drift` job ran included |

**When each runs.** The light check runs on a pull request into `main` and
on a push to `main`, and on the push it stops within seconds when those
exact files already passed (its "already tested" step). The leak gate is
triggered by every push and pull request, and decides once it is running:
in a private repository it skips its job before a runner starts; in a public
one, where a push is publication, it scans (see "The leak gate template"
below). Read a template's own header before changing either: every run of
a private repository's workflow bills at least a minute.

**Runner, both (2026-09-20):**
`runs-on: ${{ vars.PRECEDENT_RUNNER || 'ubuntu-latest' }}` --
unset, every job runs on GitHub's own `ubuntu-latest`. A repo that declares
a `PRECEDENT_RUNNER` repository variable (Settings → Secrets and variables →
Actions → Variables) moves the job onto the named self-hosted runner
instead, with no template edit. This is opt-in per repo, on purpose: it only
helps an adopter who already operates and secures their own runner, and
[GITHUB_ACTIONS.md](../../documentation/GITHUB_ACTIONS.md)'s "Controlling
Actions Minutes" section has the trade-offs (including why a self-hosted
runner is not safe on a repo that takes untrusted forked pull requests).

## The light check template

**The engine owns it, and a consumer never edits it** (since 2026-09-27).
The installer writes it where `github_ci_workflows` allows, it is tracked in
`ENGINE_MANIFEST.json` like `leak-gate.yml`, and every Update Vendors writes it
from this template over whatever the consumer has, hand-made or hand-edited.
The same refresh removes every other workflow upstream does not ship, unless
the person approved it in their own words in `github_ci_approved`. Nothing is
asked. Morgan, 2026-09-27: *"the point of the yml changes is to stop these
extra needless (often hand edited) yml files from running, that's why we now
run the checks locally etc so it shouldn't ask."*

**It runs one thing, the vendored check suite, on a pull request into
main.** A repository's own light check runs in its local push check before
every push ([two-check-levels](https://github.com/alex137/BestPractice/blob/staging/practices/two-check-levels.md)),
so GitHub's job is only to re-check what is about to reach `main` on a clean
machine. Until 2026-09-27 this template carried a `CUSTOMIZE` line and told
an adopter to copy their old command into it. That advice is what kept
hand-made copies alive, and it is gone.

**Why a shape exists at all** ([spec/BILLING_FLOOR.md](../../spec/BILLING_FLOOR.md)).
[two-check-levels](https://github.com/alex137/BestPractice/blob/staging/practices/two-check-levels.md)
tells every adopter to name a fast check and a full check. This repository
shipped the **rule** and never shipped a **shape**, so twelve repositories
each invented their own `light-check.yml` and not one got the one-job
discipline the other templates here have. Measured on the 2026-09-01..19
usage export: **609 billed minutes across those twelve, 23.5% of the whole
account** — the single largest line on the bill.

**Why replacing a hand-made copy is not the 2026-09-20 sweep.** That sweep
deleted nine live checks across nine repositories on a guess from their
filenames, and the checks were lost. Here the refresh checks first: it lists
what the old file runs (scripts, test runners, third-party actions), and if
any of it is not in the repository's local push check, the file is left
alone, under a loud banner, and the report names what to move there and
writes an open item to `todo/`. It also only replaces or removes a file
git holds with no uncommitted edits, so its old content stays in history.

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
([spec/BILLING_FLOOR.md](https://github.com/alex137/BestPractice/blob/staging/spec/BILLING_FLOOR.md)).

**What replaced it is stricter, not weaker.** "The light check gates a
commit" was written in `AGENTS.md` and followed by sessions, but nothing
refused a commit that skipped it. `.claude/hooks/doc-lint-gate.sh` now
does: a `git commit` whose staged Markdown fails [doc_lint.py](https://github.com/alex137/BestPractice/blob/staging/tools/doc_lint.py) is denied,
with the linter's own output handed back. It costs no Actions minutes and
it catches the problem **before** the commit rather than after the push.

**The rule that came out of it: no workflow exists solely to lint
Markdown.**

## The leak gate template

The installer writes [`leak-gate.yml.template`](leak-gate.yml.template) to
`.github/workflows/leak-gate.yml`, and every Update Vendors rewrites it.
First vendored 2026-09-20
([spec/CI_MINUTES_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/CI_MINUTES_PLAN.md)
item 12) — before that date `leak-gate.yml` existed only in this repo,
un-vendored, run unconditionally on every branch because this repo is
public and a leak here is already published the instant it is pushed.
That reasoning does not transfer to a private dependent repo as-is, so this
template does not just copy this repo's own scope.

**Trigger shape is deliberately NOT the branch-scoped one the light check
uses.** GitHub Actions evaluates `on:` before any job runs,
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

A practice SET runs no workflow, this one included (practice
`source-sets-run-no-ci`). Its own `leak_gate.py` runs in the session, and
reads `precedent-source.json`, which always declares `"visibility": "private"`
(`precedent_bootstrap_source.py`'s `_write_source_manifest`).

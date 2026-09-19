# GitHub Actions Checks

Precedent uses repository checks for rules that should not depend on a particular person or AI assistant remembering to run them.

This is especially important when working through GitHub-connected ChatGPT. A normal ChatGPT conversation can read and update repository files, but it does not receive a local checkout or an interactive shell *(as of 2026-08 — [MOBILE.md](MOBILE.md) tracks this capability and is the place to re-date it)*. GitHub Actions supplies the missing execution environment: ChatGPT prepares a branch, GitHub runs the checks, and the result appears on the pull request.

## Precedent's Own Workflows (This Repo, Not a Template)

Three workflows run on this repo itself, in [.github/workflows/](.github/workflows/):

- **`docs.yml`** — pre-fork BestPractice content: the Markdown lint job
  described below, running here rather than only shipped as a template.
- **`deep-check.yml`** — added by a 2026-09-03 deep-check audit. Runs
  [tools/verify_harness.py](tools/verify_harness.py),
  [tools/precedent_check.py](tools/precedent_check.py) and
  [tools/doc_sync.py](tools/doc_sync.py) — the three of AGENTS.md's five
  named "deep check" tools that had no continuous-integration (CI) check
  of their own until this landed, having been session discipline only.
  That gap is exactly where
  a same-day audit found two critical, reproduced bugs (a self-referential
  `repo-local` source silently destroying its own content, and a second
  that broke every re-sync after it) sitting undetected on a branch whose
  merges were all green — neither doc_lint.py nor leak_gate.py could ever
  have caught either, since neither runs the resolver or materializer at
  all. Runs on every push and pull request, on every branch, same as
  leak-gate.yml below.
- **`leak-gate.yml`** — added at phase 2 of the Precedent rewrite
  (`b3bfb54`). Runs [tools/leak_gate.py](tools/leak_gate.py)'s structural
  layer on every push and every pull request, on every branch (this repo is
  the branch being published, not just its default). It is the unbypassable
  backstop for the private-source separation described in
  [spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md)'s "Source — Who a
  Practice Belongs To": a `git push --no-verify` can skip the local
  [pre-push hook](templates/hooks/pre-push), but not this. See
  [spec/SOURCES.md](spec/SOURCES.md) for what it checks and why it has two
  layers, only one of which can run here. (This section exists because the
  workflow went undisclosed for months after being added — the practice
  requiring disclosure, `github-setup-disclosed`, only fires on a
  newly-added workflow file in the diff being checked, so it structurally
  cannot catch a workflow that was already merged before the practice
  existed to check it. Found by a 2026-09-01 deep-check audit; see
  [tools/verify_harness.py](tools/verify_harness.py)'s
  `check_all_workflows_disclosed` for the tree-wide check added in
  response, which does catch this going forward.)

## What the Markdown Check Does

The supplied workflow:

1. checks out the complete repository history;
2. installs Python and `cmarkgfm`;
3. runs the Precedent Markdown linter;
4. reports warnings in the job log; and
5. fails the pull request when changed Markdown contains accidental strikethrough or a relative link that lands nowhere.

The linter determines which Markdown files changed relative to the repository's default branch. A full-history checkout is therefore required.

## Controlling Actions Minutes

**`precedent_install.py` does not install this workflow by default (2026-09-15).**
GitHub Actions minutes are metered per PRIVATE repository and billed per
run, rounded up to the minute. Vendoring Precedent into many private repos
and committing the way a save button gets used means paying for a workflow
run on every one of those saves, whether the check was wanted or not — and
that adds up fastest for exactly the person most likely to be running it
everywhere.

So the installer resolves `"ci_workflows"` from the individual or team
source it can reach ([tools/precedent_identity.py](tools/precedent_identity.py)'s
`ci_preference()`, same resolution order as `relayed_authorization`: the
repo's own `identity.json` when it IS an individual source, else the one
the user-level config names) and installs the workflow only when that
value is exactly `"enabled"`. Nothing declared resolves to disabled — the
engine's own default, applied silently
([declared-default-is-applied](practices/declared-default-is-applied.md)) —
and the install log and the project's own `GETTING_STARTED.md` both say so,
naming the field and where to set it. **This only changes what
`precedent_install.py` writes by default.** The template is always there to
copy in by hand, on any one repo, whatever the field says.

**Three more levers, once the workflow is installed at all:**

- **`concurrency` with `cancel-in-progress: true`** ships in
  [doc-lint.yml.template](templates/github-actions/doc-lint.yml.template)
  itself now: if a second run starts on the same branch while an earlier
  one is still going, GitHub cancels the earlier one instead of billing
  both. It only helps the *overlap* case — two pushes closer together than
  one run takes (well under a minute here) — so it is a real but small
  saving for a steady stream of spaced-out saves, not the fix for that
  case.
- **A scheduled cadence instead of per-push billing** —
  [doc-lint-scheduled.yml.template](templates/github-actions/doc-lint-scheduled.yml.template) —
  is the actual fix for a repo pushed to constantly, direct to its default
  branch, with no pull request in the loop: however many saves land in one
  window, they cost one run. It is **not** installed by either default —
  `precedent_install.py` never writes it, and turning `ci_workflows` on
  does not choose it over the per-push template — because a `schedule:`
  is a clock in somebody else's repository that they never picked (this
  file's own Limits section says the same about an inherited schedule).
  Copy it over `bestpractice-docs.yml` deliberately, and set your own cron
  cadence in it; its header explains why it gates the whole tracked
  Markdown corpus each run rather than "what changed", and what that
  trades away.
- **A debounce, for a repo pushed to constantly that still wants a
  push-triggered check** (2026-09-16, moved into its own JOB 2026-09-19) —
  a `debounce` job in
  [doc-lint.yml.template](templates/github-actions/doc-lint.yml.template)
  and [precedent-check.yml.template](templates/github-actions/precedent-check.yml.template)
  (the latter now covers the generated-views drift check too — see
  "Install in a Practice-Set Repository" below) skips the check job(s) that
  `needs:` it when the last completed run on the same branch finished less
  than `ci_debounce_minutes` ago (default `360` = 6 hours; `0` disables
  it). Read from `precedent.json` in a dependent repo, or `identity.json`
  in an individual practice set — a team set has neither field to read and
  always gets the default. **A separate job, not a step inside one that
  already started** (2026-09-19): a step-level skip still bills a whole
  runner-minute for the job that reached it, so a debounced push under the
  old shape cost as much as the decision to skip did. A job whose own `if:`
  is false is reported SKIPPED and never allocates a runner — not billed at
  all. Not applied to this repo's own
  `docs.yml`/`deep-check.yml`/`leak-gate.yml`, or to any workflow standing
  in for a security backstop: [spec/CI_MINUTES_PLAN.md](spec/CI_MINUTES_PLAN.md)'s
  item 4 is the measurement and the reasoning behind that line.
- **`pull_request:` alongside a branch-scoped `push:`, not push on every
  branch** (2026-09-19, [spec/CI_MINUTES_PLAN.md](spec/CI_MINUTES_PLAN.md)
  item 8) — both templates ship `push: branches: [main]` plus
  `pull_request: [opened, synchronize]`. A branch with no open PR triggers
  neither event that matches here, so the workflow is never evaluated —
  cheaper than debounce, which still bills the debounce job's own minute.
  A branch with an open PR gets checked, debounced the same way repeated
  pushes to an already-open PR are. Widen the branch list
  (`branches: [main, precedent-beta-v01]`, this repo's own pattern) if the
  repo installing this has more than one routine merge target — each
  template's own header says so at the trigger block. Do not add
  `pull_request:` to a `push:` that still covers every branch: that
  reintroduces the exact duplicate-run problem
  [doc-lint.yml.template](templates/github-actions/doc-lint.yml.template)'s
  own header measured (235 runs in matched pairs) before this repo's own
  `docs.yml`/`deep-check.yml` dropped `pull_request:` outright on
  2026-09-07/2026-09-14 — the fix here is scoping `push:` narrowly enough
  that it never fires on the same branch `pull_request:` is watching, not
  running both wide open.

## Install in a Dependent Repository

`precedent_install.py` (INSTALL.md §0) does this automatically, when it is
this repo's turn per "Controlling Actions Minutes" above. For a manual or
§1-style install, copy:

```text
process/upstream/templates/github-actions/doc-lint.yml.template
```

to:

```text
.github/workflows/bestpractice-docs.yml
```

Commit the workflow together with the other installed Precedent files. The template runs the vendored linter at:

```text
process/upstream/tools/doc_lint.py
```

If the dependent repository instead copies or adapts the linter into its own tools directory, update the workflow command to use that local path and record the adaptation in `process/manifest.json`.

## Install in a Practice-Set Repository

A practice set gets **one** workflow, `precedent-check.yml`, and it answers
two questions: whether the whole check suite passes over the set's
catalogue, and whether its generated views still match a fresh
regeneration (the `precedent-check` and `views-drift` jobs, respectively —
see "The Views Drift Gate" below; through 2026-09-19 this was two separate
files, merged the same day as the trigger change above). Sets created by
[tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py)
get it installed automatically; older sets need the copy below, and
`python3 tools/precedent_bootstrap_source.py --verify <path>` names it as
missing until it is there.

### The Check Suite

Copy:

```text
templates/github-actions/precedent-check.yml.template
```

to:

```text
.github/workflows/precedent-check.yml
```

**Why this exists.** Every source set had the same hole: the only workflows
any of them carried called a *single* check's function directly — written
that way precisely because `precedent_check.py` skipped that check in a
source set — and nothing ran the suite. A set was gated on one or two rules
it had hand-wired and silent on the rest of its own catalogue.
`binds_publishers` (#261) removed the reason those hand-wired workflows
existed, which is what makes running the suite here worth doing.

**It is deliberately not `--strict`.** Most registered checks belong to
practices a source set does not resolve and skip by design — measured in a
freshly bootstrapped set on 2026-09-13, 41 of them. `--strict` turns every
one into a failure, leaving the gate permanently red and teaching everyone
to ignore it. Violations and errors fail the run on their own.

**Two things in it are load-bearing and easy to drop.** `fetch-depth: 0`,
because several checks are scope `tree` and walk `git log`: on the default
shallow checkout they report SKIPPED rather than running, and a skip does
not fail the run, so a shallow checkout silently shrinks coverage while the
job stays green — the same bug [deep-check.yml](.github/workflows/deep-check.yml)
carries its own `fetch-depth: 0` for. And the PyYAML install, because a
check script a practice names in `checked_by:` may import it: those scripts
run as subprocesses under an exit contract where an uncaught
`ModuleNotFoundError` exits 1, so a missing dependency is reported as a
**violation with a traceback**, not a skip.

**It refuses rather than passing blind**, in three situations. No
`tools/precedent_check.py` (distinguishing the `process/upstream/` consumer
layout, which this workflow is not for); a vendored engine predating
`binds_publishers`, which in a source set skips the checks whose practice
lives upstream and still exits 0 — measured `5 passed, 44 skipped` against
`8 passed, 41 skipped` on the same tree, so it is *quietly* green rather
than obviously broken, and `--verify` now reports it too; and a run that
reports `0 passed`, which is the backstop against any other route to zero
coverage.

### The Views Drift Gate

An individual or team practice set generates its own views — `AGENTS.md`'s
loader block, [MAP.md](MAP.md) and [GLOSSARY.md](GLOSSARY.md) — from its
`practices/` directory and the engine vendored into its own `tools/`.
**No separate copy step** — installing `precedent-check.yml.template`
above installs this too, as its `views-drift` job.

That job runs `python3 tools/build_views.py --repo . --check`, which exits
non-zero when any of the three has drifted from a fresh regeneration.
Every set created before 2026-09-11 needs `precedent-check.yml` installed
(which now carries this job); see this section's opening for how it is
installed and verified.

**Why a source set needs its own gate.** Until 2026-09-11 nothing checked a
generated view anywhere but in this repo, where
[deep-check.yml](.github/workflows/deep-check.yml) runs
[tools/verify_harness.py](tools/verify_harness.py) — and `verify_harness.py`
is deliberately not vendored into a source set. Worse, the generated header
on each view *said* a check was failing the build on drift, so a session
that wondered read the header instead of running anything. Measured in a
real individual set: `MAP.md` sat three practices stale, one of them missing
from its table from the day it landed, under that header. The header now
names `build_views.py --check`, which exists wherever the view does; this
workflow is the half that makes something actually look.

**The reason this paragraph used to give expired on 2026-09-12.** It said
the engine's own drift check could not substitute, because
[tools/precedent_check.py](tools/precedent_check.py) skips any check whose
practice is not in force in the repo it runs in — and a source set's
`practices/` holds only its own practices, never the universal one
`generated-artifact-provenance` belongs to. That was true, and measured: run
against a real individual set on 2026-09-11 it reported `1 skipped`, and a
skip is not a pass. `binds_publishers` (#261, merged 2026-09-12) ended it. A
check whose subject is the practice a repo *publishes* now runs in the repo
publishing it, and that check is one of the three carrying the flag.

**What is true now, measured 2026-09-13** against a set freshly bootstrapped
by [tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py)
and given a loader block: `--only generated-artifact-provenance` reports
`1 passed` where it reported `1 skipped` before, and planted drift turns it
red in each of the three views separately — [MAP.md](MAP.md),
[GLOSSARY.md](GLOSSARY.md), and inside `AGENTS.md`'s loader block. In a
source set the two now look at the same three files, by the same
`build_views.py --check` subprocess. The
coverage argument for keeping this workflow is gone.

**What it still does is fire without being asked.** A vendored check runs
when somebody types the command; this job is attached to the same
`pull_request`/branch-scoped-`push` trigger as `precedent-check` (see
"Controlling Actions Minutes" above) — it was `pull_request` alone until
2026-09-14, which meant a session pushing straight to a source set's own
branch, the normal way work lands in a private single-owner set, ran no
check at all. "The check runs natively now" and "the rule is gated" remain
different claims, and only the second one is what a generated view
drifting silently needs.

**Whether a set that gains a workflow running the whole suite should then
drop this check was an open question, settled 2026-09-19**: keep both, but
as jobs in one workflow file rather than two — see
[TODO.md](TODO.md)'s
[`views-drift-vs-suite-workflow`](todo/todo-2026-09-13-views-drift-vs-suite-workflow.md)
for the record. Folding the two files together removed the actual cost
that item named (two workflows reporting the same fact, two places to
update the drift story) without losing what it named as worth keeping —
each check's own distinct failure message, and `precedent-check`'s
deliberate non-`--strict` leniency staying independent of this job's own
refusal logic.

This job **gates and does not fix**: regenerating in CI would leave the
branch's own diff wrong and put a runner bot in the authorship path that
[practices/ci-commits-carry-identity.md](practices/ci-commits-carry-identity.md)
exists to keep clean. The fix is one `python3 tools/build_views.py` on the
branch.

## Enable GitHub Actions

GitHub Actions is normally available automatically, but an organization or repository administrator can restrict it. After merging the workflow onto the default branch:

1. open the repository's **Actions** tab and confirm that the workflow is allowed to run;
2. open a pull request that changes a Markdown file;
3. confirm that **Markdown lint** appears in the pull request checks; and
4. inspect the job log if the check fails or reports warnings.

The first pull request that introduces a workflow may be subject to GitHub's normal approval or security controls, especially for contributions from forks.

Two further settings belong to the same moment and are worth mentioning
when an install finishes ([INSTALL.md](INSTALL.md) §1 step 10): the
**default branch should be named `main`** (**Settings → General → Default
branch**), since the supplied template's `push` trigger names `main` as a
literal string and a differently-named default branch runs no check on
merges; and **workflow permissions should allow Actions to open pull
requests** (**Settings → Actions → General → Workflow permissions**), which
the supplied Markdown check does not need but anything opening a pull
request for the project does. *(Click-paths as of 2026-09-10.)*

## Make the Check Required

Once the workflow has run successfully at least once, add its **Markdown lint** job to the default branch's ruleset or branch-protection required checks.

That changes the rule from advice into enforcement: a pull request cannot merge while the Markdown gate is failing, regardless of whether the change came from ChatGPT, Claude Code, Codex, another agent, or a human editing GitHub directly.

Repository rules vary by account and organization. Use the repository's current **Settings → Rules** or branch-protection controls and select the status check produced by this workflow. The rest of what belongs on that same page — a pull request required, review from code owners, no bypass — and what each setting does for a Precedent project is [documentation/GITHUB_SETTINGS.md](documentation/GITHUB_SETTINGS.md).

## Updating an Installed Repository

When Precedent updates the workflow template:

1. compare the new template with `.github/workflows/bestpractice-docs.yml`;
2. preserve any dependent-repository adaptations, such as a different default branch or linter path;
3. update the installed workflow;
4. run it through a pull request; and
5. update the corresponding manifest baseline.

Treat the workflow as an installed Precedent artifact. A typical manifest entry is:

```json
{
  "practice": "doc-lint-action",
  "upstream_path": "templates/github-actions/doc-lint.yml.template",
  "local_path": ".github/workflows/bestpractice-docs.yml",
  "granularity": "file",
  "status": "synced",
  "local_sha256": "<filled by practice_audit --update-baseline>",
  "notes": "Runs the vendored linter; preserve repository-specific branch names or paths"
}
```

## Limits

GitHub Actions closes the test-execution gap, but it does not make ordinary ChatGPT identical to a coding-agent workspace *(as of 2026-08)*. ChatGPT still needs the session bootstrap described in the main README so it reads `AGENTS.md`, `MAP.md`, and the task-relevant instructions before working.

The useful division of responsibility is:

> Agents interpret intent and prepare changes. GitHub Actions enforces repeatable checks.

**A workflow that COMMITS is outside
[commit-identity.sh](templates/harness/claude-code/hooks/commit-identity.sh)'s
reach, and nothing here will tell you so.** That hook resolves whoever is
running the session and installs a `pre-commit` backstop refusing the
container's bot account — but it runs at *session start*, in an agent's
session. A GitHub Actions runner never runs it. So a workflow that commits
on your behalf authors as `github-actions[bot]`, on the runner's UTC clock,
and both of those are exactly what an adopter's `commit-author` and
timezone checks exist to refuse.

**A workflow that commits therefore resolves the author itself** — read
`name`, `email` and `timezone` from the individual source's `identity.json`
and **refuse the run outright if any of the three is missing**, rather than
falling back to the bot. A fallback here is the failure: it produces a
commit that looks fine until something checks it.

Found 2026-09-10 in a real practice set, by a refresh workflow that had been
mis-authoring **every** commit it ever made. Nobody had seen it because the
two checks that would have caught it were themselves reporting SKIPPED —
they could not resolve an identity inside a practice set until
[tools/precedent_identity.py](tools/precedent_identity.py) moved into the
vendored engine that same day. The moment they went live, the workflow's own
commit was the first thing they flagged. **Two silent failures were holding
each other up**, which is the general shape worth remembering: a check that
cannot run is not evidence that what it checks is fine.

**A CONSUMING repo's generated views cannot be gated in CI at all, and
the drift gate above refuses rather than pretending.** A consuming repo's
`practices/` is materialized from the sources it resolves: a team source is
a sibling clone outside the repo, an individual source resolves through a
private user-level config. Neither exists in a bare CI checkout, so there is
nothing on the runner to regenerate the views *from* — and
[tools/build_views.py](tools/build_views.py) deliberately exits 0 rather
than writing a block from an incomplete source set, which is the shape a
green-but-blind check would take. So the `views-drift` job in
[precedent-check.yml.template](templates/github-actions/precedent-check.yml.template)
exits non-zero when it finds the vendored `process/upstream/` layout instead
of running. What covers a consuming repo today is a session running
`python3 tools/precedent_sync_views.py --repo . --check` where the sources
do resolve; [TODO.md](TODO.md)'s
`consumer-views-drift-uncheckable-in-ci` item holds the question of whether
anything better is possible.

**Workflow runs do NOT spend your account's API allowance, and believing
they do sends you fixing the wrong thing.** A workflow authenticates as
`GITHUB_TOKEN`, which draws on a per-repository hourly pool that CI has to
itself; a session's `mcp__github__*` calls and any `curl` a tool makes draw
on the account's pools. Measured 2026-09-14 while chasing a rate-limit
refusal: 75 workflow runs in the busiest hour on this repository, and 133
calls of a 15,000/hour account pool spent in the same window. The runs were
not it. **The allowances a busy fleet of sessions actually exhausts are
`search` (30 requests a MINUTE, shared by every open session) and the
secondary limit on creating content (a commit, a branch, a pull request, a
comment, a merge).** [tools/github_budget.py](tools/github_budget.py) prints
what is left and what a tool spent; the rule is
[github-api-budget](practices/github-api-budget.md).

Two things about workflow triggers are still worth getting right for their
own reasons, and both are about wasted runs rather than wasted allowance:
`pull_request:` alongside `push:` fires two runs of the same tree for every
push on a branch with an open pull request (measured here over 13 paired
runs, never once disagreeing), and a `schedule:` inherited by every adopter
is a clock in somebody else's repository that they never picked.

Precedent itself ships no committing workflow — its three
([deep-check](.github/workflows/deep-check.yml),
[docs](.github/workflows/docs.yml),
[leak-gate](.github/workflows/leak-gate.yml)) all read and none writes — so
there is nothing to fix here. This is a limit to know before you add one.

*GitHub interface and product behavior verified August 2, 2026. Settings and labels can change.*

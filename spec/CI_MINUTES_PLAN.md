---
title:         Cutting GitHub Actions minutes across every vendored repo
kind:          proposal
status:        accepted
opened:        2026-09-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "What is actually burning Actions minutes across Morgan's repos, why 2026-09-15's ci_workflows default did not move the number, and a phased plan to fix it — organized from his own seven numbered points plus two pushback items."
---

# Cutting GitHub Actions minutes across every vendored repo

This organizes Morgan's 2026-09-16 conversation (seven ideas plus two
follow-on questions) against what is actually in this repo's tree and what
the account's own usage report shows, and pushes back on two of the seven
where the numbers or the existing design said something different than
the idea assumed. **Morgan approved phases 1–5 the same day** — "phases
1-5 approved... Go update!", holding items 6 and 7 for later (strength:
decided) — and "Sequencing and status" below says what that approval has
and has not reached yet.

## Where the minutes actually go — measured, not guessed

Morgan attached `usageReport_1_895e4cb647cb49859f1f4bee1f43d0d8.csv`, the
account's own Actions usage export, covering **2026-09-01 through the
morning of 2026-09-16** (his note: today's spike is not in this file).
Totals, computed directly from the file:

- **1,578 minutes** billed across 16 days — **$9.47 gross**, **$9.47
  discounted**, **$0.00 net** in every single row. The period cost nothing
  because a discount (almost certainly an included monthly minutes
  allowance) covered all of it — this file does not say how much of that
  allowance is left, or whether today's spike already used the rest of it.
  That number lives in GitHub's own Settings → Billing → Actions usage
  page, not in this export, and it is the one figure that actually says
  how close the account is to real dollars.

**By workflow, summed across every repo:**

| Minutes | Workflow | Status |
|---:|---|---|
| 532 | `bestpractice-docs.yml` | current template (`doc-lint.yml.template`) |
| 492 | `light-check.yml` | **not in this repo's tree at all** |
| 175 | `views-drift.yml` | current template, practice-set repos |
| 126 | `precedent-check.yml` | current template, practice-set repos |
| 81 | `commit-identity.yml` | not in this repo's tree as a workflow file |
| 42 | `personal-pack-sync.yml` | Morgan's own automation, not Precedent's |
| 36 | `bestpractice-upstream-sync.yml` | **superseded**, per this repo's own migration doc |
| 29 | `status-claims-check.yml` | not in this repo's tree |
| 15 | `sync-voice-packs.yml` | Morgan's own automation |
| 11 | `unified-prompt-check.yml` | not in this repo's tree |
| 11 | `platform-docs-check.yml` | not in this repo's tree |
| 10 | `voicedef-pack-sync.yml` | Morgan's own automation |
| 7 | `practice-links-travel.yml` | not in this repo's tree |
| 4 | `sync-sound-human.yml` | Morgan's own automation |
| 4 | `engine-refresh.yml` | current template, practice-set repos |
| ≤2 each | `sync-voice-guidelines-to-sound-human.yml`, `voice-guidelines-sync.yml` | not in this repo's tree |

**By repo, personal repos not named here since this document is headed for
a public branch:** the busiest personal repo spent 433 minutes, the next
178, then a repo already named for its own deletion (132 — see Item 3), then
126, 65, 54, and fourteen more below 45 each. The four practice-set repos
are broken out separately since their numbers matter directly to items 4
and 5 below: precedent-individual 218, precedent-team-repo-maintenance 80,
precedent-team-working-style 50, precedent-team-writing 44.

**The finding that reframes items 1–3 below:** `light-check.yml`,
`commit-identity.yml` (as an ordinary dependent-repo workflow, not the
practice-set one), `status-claims-check.yml`, `unified-prompt-check.yml`,
`platform-docs-check.yml`, `practice-links-travel.yml`,
`bestpractice-upstream-sync.yml`, and the two `sync-voice-guidelines`
variants together burned **~659 minutes — 42% of the whole period** — and
**none of them exist as templates anywhere in this repo's current tree.**
`bestpractice-upstream-sync.yml` specifically is named in
[MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)'s own text
as a scheduled sync workflow that "since 2026-09-14... there is no schedule
to pause" — it was replaced by something else in the current model, and
nothing ever removed the old file from the repos that installed it under
the old one. These are leftovers from before Precedent's rewrite, running
in repos that mostly haven't migrated onto the current engine yet, and
[tools/precedent_install.py](../tools/precedent_install.py)'s
`ci_workflows` field has no path to them at all — it only ever wrote
`bestpractice-docs.yml`.

Separately: `personal-pack-sync.yml`, `sync-voice-packs.yml`,
`voicedef-pack-sync.yml`, `sync-sound-human.yml`, and
`sync-voice-guidelines-to-sound-human.yml` (72 minutes total) are Morgan's
own domain automation — voice-pack and personal-data syncing — not
anything Precedent installs or owns. This plan flags them because they show
up in the same report, but treats them as his call, not something a sweep
touches on its own.

## Item 1 — `ci_workflows` default (already shipped, scope too narrow)

Verified in code: [tools/precedent_install.py](../tools/precedent_install.py)'s
`_bootstrap_and_ci` already skips writing `bestpractice-docs.yml` unless the
resolved individual or team
source declares `"ci_workflows": "enabled"`
([tools/precedent_identity.py](../tools/precedent_identity.py)'s
`ci_preference()`), and Morgan's own
`~/precedent-individual/identity.json` already declares it `"disabled"`.
**This part of item 1 is done, shipped 2026-09-15 — nothing to build.**

What is missing is scope: the toggle gates exactly one file. The table
above shows three more current templates a fresh install of a **practice
set** can carry — `precedent-check.yml`, `views-drift.yml`,
`engine-refresh.yml` — and none of them currently read `ci_workflows` at
all; wherever those get written today, they get written unconditionally.

**Proposed:** extend `_bootstrap_and_ci` (and the practice-set bootstrap
path that writes the other three) to gate every current CI template behind
the same single `ci_workflows` field, rather than adding one field per
template. A practice set that wants its own drift/check gates but not the
consuming-repo doc lint is a real but narrow case — flag it as an open
question below rather than building per-workflow granularity nobody has
asked for yet.

## Item 1a — a canonical install/upgrade questions document

**Yes, this gap is real.** Right now the questions a session asks during an
install or migration live in three places that say different things:
[SETUP.md](../SETUP.md) says *"ask exactly three questions"* (project
description, private-vocabulary blocklist, team/individual source);
[INSTALL.md](../INSTALL.md)'s "Essentials Only" section and
[MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)'s "Step 0"
ask about `visibility`,
`base_branch`, and which sources to declare, in prose, without being
counted or listed together. Nothing enumerates all of them in one place,
which is exactly the registry-source-of-truth gap the repo already has a
name for.

**Proposed:** a new `spec/INSTALL_QUESTIONS.md` — one table, one row per
question, each row saying when it's asked (fresh install / migration /
both), why, and what it's stored into. SETUP.md, INSTALL.md and
MIGRATING_EXISTING_INSTALLS.md then point at it instead of each carrying
their own count and their own wording — so "exactly three questions"
becomes "exactly N questions, listed here" once, and adding a question
means editing one table instead of three prose sections that can drift.

**Two new rows for that table, per Morgan's ask:**

- **Which LLM/agent platform will work in this repo** (Claude Code,
  GitHub-connected ChatGPT, other). Not a cosmetic field —
  [GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md) already explains that GitHub
  Actions exists partly to give a platform with no local shell (ChatGPT) the
  execution environment a platform with one does not need. The answer
  changes whether `ci_workflows` should default to disabled at all: for a
  ChatGPT-only repo, Actions may be the *only* place certain checks can run,
  which is a real argument for enabling it even under Morgan's own general
  preference.
- **`ci_workflows`: on or off** — asked explicitly, **default disabled**
  unless they say otherwise, matching item 1's already-shipped default and
  making the choice a recorded answer instead of a silent inherited value.

## Item 2 / 2a — retroactive default, widened past `bestpractice-docs.yml`

**Agreed on the framing.** There was no prior setting to revoke — flipping
existing installs to match the new default isn't changing anyone's choice,
it's applying the choice Morgan already made for future installs to the
ones that predate it. And 2a is right that the toggle needs to cover more
than one filename — the measured table above is the argument: 42% of the
period's minutes come from workflows the `ci_workflows` field has never
touched.

**One pushback, on mechanism rather than direction.** Not every legacy
workflow is safe to delete on sight. `bestpractice-upstream-sync.yml`
specifically *did something* — a scheduled upstream sync — and
[MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md) says that
job was replaced by something
else in the current model, not simply dropped. Deleting the old file in a
repo that hasn't actually migrated onto the replacement would silently
stop that repo's upstream sync altogether, with nothing left to notice.
**So the sweep needs a per-file check, not a blanket delete:** for each
retired workflow name, confirm what replaced it (if anything) is present
and working in that repo *before* removing the old file, and only then
remove it. The other retired names in the table (`light-check.yml`,
`commit-identity.yml`, `status-claims-check.yml`,
`unified-prompt-check.yml`, `platform-docs-check.yml`,
`practice-links-travel.yml`) look like they were advisory checks with no
live replacement to verify — but that should be confirmed per file, once,
rather than assumed from here, since none of them have any trace in this
repo's history to check against directly.

## Item 2b — pushback: this repo's own three workflows are a different case

**I'm pushing back on this one rather than folding it in.**
[docs.yml](../.github/workflows/docs.yml),
[deep-check.yml](../.github/workflows/deep-check.yml), and
[leak-gate.yml](../.github/workflows/leak-gate.yml) — BestPractice/Precedent's
own CI, not a template it ships — run unconditionally on every push, every
branch, by explicit design, and the design reasoning is written into each
file's own header. `leak-gate.yml`'s says it plainly: it is "the STRUCTURAL
backstop that a `git push --no-verify` cannot bypass, because it runs on
the server" — the entire point is that it runs *without* anyone asking for
it, because the person most likely to skip a private-vocabulary check on
purpose or by accident is the same person who would also skip opting a
check back in. Making it "off unless explicitly asked" removes exactly the
property that makes it worth having.

Two more reasons this is a different case from items 1–3:

- **This repo is public**, so its own Actions minutes are free on standard
  runners regardless of how often these three run — turning them off saves
  nothing on the number driving this whole conversation.
- **`docs.yml`'s 2026-09-14 widening to every branch was not an
  oversight.** Its own header cites a measured incident: a deliberately
  broken link planted in [spec/LOADER.md](LOADER.md) failed
  [tools/doc_lint.py](../tools/doc_lint.py) but was invisible to
  [tools/precedent_check.py](../tools/precedent_check.py), and nothing else
  running on a push to `precedent-beta-v01` (the branch that carries
  essentially all of this repo's actual traffic, per
  [AGENTS.md](../AGENTS.md)'s own routing rule) would have caught it before
  this change. Reverting it reopens that exact gap.

**What I'd keep:** BestPractice's own three workflows as a separate,
un-gated category — not subject to `ci_workflows`, not part of the sweep.
**What I'd fold into items 1–3 instead:** the CI *templates* this repo
vendors into other repos, which is what "off unless explicitly asked" is
actually a strong position on. I'd like Morgan's explicit sign-off before
touching this repo's own workflows either way, given the security
rationale on record — see Open Decisions below.

## Item 3 — the sweep, scoped to already-upgraded repos, inside migration

**Agreed with the shape as Morgan described it.** Operationally: "already
upgraded" means a repo that has been through
[MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md) or a fresh
§0/§1 install under the current engine — in practice, one with a
`precedent.json` on the current model. A
repo that hasn't migrated yet gets the sweep *as part of* that migration,
not as a separate pass beforehand — which also solves the "confirm the
replacement exists" problem from item 2, since migration is exactly the
moment the replacement gets installed.

**Proposed:** a new step in
[MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md) (and in
[vendor-update-runbook](../practices/vendor-update-runbook.md), which
already "carries the merge" since 2026-09-14) that deletes retired
workflow files as part of that same pass, driven by a small registry list
(retired filename → what replaced it, if anything) rather than improvised
per repo — matching this catalogue's own `registry-source-of-truth`
practice, and giving the per-file check item 2b's pushback asked for a
single place to live instead of an ad hoc judgment call each time.

**One item that needs no plan at all:** the repo named above that's already
named for its own deletion burned 132 minutes in this window — still
running CI on every push. Archiving or deleting it removes that spend
today, independent of every other decision in this document.

## Item 4 — a debounce, not a schedule

Morgan's idea: keep every check running on push, but skip the run if the
last one for this workflow finished less than **X minutes** ago (default
**6 hours**, configurable), instead of trading push-triggered checks for a
fixed clock the way `doc-lint-scheduled.yml.template` already does. GitHub
Actions has no native "at most every N minutes" trigger, so this needs a
guard step at the top of the job: query the Actions API for the most
recent completed run of this workflow on this branch, and if it finished
inside the window, exit success immediately without running the actual
checks.

**Design:** a small shared script (one per template family, or one script
both `doc-lint.yml.template` and `precedent-check.yml.template` call),
reading a new field — `ci_debounce_minutes`, same resolution order as
`ci_workflows` — defaulting to `360` (Morgan's own 6-hour example) when
absent, `0` meaning "no debounce, check every push."

**Where I would and wouldn't apply it.** This directly answers Morgan's
other observation from yesterday about "200 checks... that slowed things
down" — a debounce collapses a burst of rapid pushes into one check per
window, which is a volume fix as much as a money one, and it's worth
applying broadly. The one place I'd hold it back is anything that exists
specifically to catch what nothing else catches — this repo's own
`leak-gate.yml` is the clearest example, per item 2b's reasoning: a
6-hour-stale leak gate is a leak gate that can miss the exact thing it
exists for, between windows. For advisory/drift checks like
[tools/doc_lint.py](../tools/doc_lint.py),
[tools/precedent_check.py](../tools/precedent_check.py), and `views-drift`,
a few hours of staleness costs nothing nobody would notice by the next
real run.

## Item 5 — `concurrency: cancel-in-progress`, explained and checked

**What it does, plainly.** Every push normally starts its own full workflow
run that keeps going to completion even if a newer push lands seconds
later — you pay for and wait on an answer nobody reads, because the newer
commit already made it stale. A `concurrency` block tells GitHub the
opposite: group runs by branch, and when a new run starts, cancel whichever
older run for that branch is still in flight. A burst of rapid pushes then
bills for roughly one full run instead of one per push.

**Checked, directly in this repo's templates:**

- `templates/github-actions/doc-lint.yml.template` **already has it**
  (`group: docs-${{ github.ref }}`, `cancel-in-progress: true`, added
  2026-09-15) — its own comment is honest about the limit: the job runs
  "well under a minute," so it only helps when two pushes land close enough
  together to actually overlap, which is the burst case and not the steady
  drip case (that's what item 4's debounce is for).
- `templates/github-actions/precedent-check.yml.template` and
  `templates/github-actions/views-drift.yml.template` **do not have it** —
  a real gap, and the more valuable one of the two: `precedent-individual`
  alone spent 218 minutes across `views-drift.yml`, `commit-identity.yml`,
  and `precedent-check.yml` in this window, and the three team repos spent
  174 more between them, all without any cancel-in-progress protection.

**Cannot verify from here** whether the concurrency block that's already in
`doc-lint.yml.template` has actually landed in the personal repos it was
installed into — this session only has access to `alex137/bestpractice`,
not those repos. That check belongs in the same sweep as item 3.

## Item 6 — a self-hosted runner on your own server

**What it is, plainly.** A GitHub-hosted runner is a fresh virtual machine
(VM) GitHub spins up per job and bills by the minute. A self-hosted runner
is a long-lived
process you install on a machine you already control — your Linux server,
or a RunCloud instance — that GitHub Actions dispatches jobs to instead of
spinning up its own VM. The workflow YAML barely changes: `runs-on:
self-hosted` (or a custom label) in place of `runs-on: ubuntu-latest`.
**Minutes run there are not metered or billed by GitHub at all** — the cost
moves entirely to a machine you're already paying for.

**The honest trade-offs:**

- It's a standing operational commitment, not a one-time setting: you keep
  the runner process alive, patch the box, and a hung job or a dead runner
  is now something you debug instead of something GitHub absorbs.
- **Security, and this repo already reasons about the relevant risk.**
  GitHub's own guidance against self-hosted runners on repos taking
  untrusted forked PRs is the same risk this repo's own `leak-gate.yml`
  names when it says "PUT `pull_request:` BACK IF A PR EVER ARRIVES FROM A
  FORK" — a workflow can run arbitrary code from whatever triggered it. For
  the private, single-author repos in this usage report that's not a live
  risk; it would become one the moment any of them started taking outside
  contributions on a self-hosted runner.
- Best fit as a **pilot on the highest-volume, lowest-sensitivity jobs**
  first — the Markdown-lint job in `doc-lint.yml.template`/`light-check.yml`
  on the two busiest personal repos named above (433 and 178 minutes),
  rather than a blanket migration of every workflow at once.

This is a bigger, slower-moving piece than items 1–5; I'd sequence it as
its own later phase rather than let it hold up the rest of this plan.

## Item 7 — the usage report

Covered above, under "Where the minutes actually go." The one thing worth
restating here: **the reported period cost $0.00 net**, fully covered by a
discount this file doesn't explain the size of. The real risk Morgan named
— crossing into real dollars as more projects and more usage arrive — is
forward-looking, and this file can't answer how close that ceiling
actually is. Checking Settings → Billing → Actions directly, for the
account's included-minutes ceiling and how much of it this cycle has
already used (including today's excluded spike), is worth doing before
any of the rest of this plan, since it's the number that says how urgent
the rest of it actually is.

## Item 8 — field validation: debounce alone did not stop a live spike (2026-09-19)

Item 4's own text flagged this as untested: "its first real run on any
adopting repo is worth watching." This is that run, and what it showed
changes the recommendation in Open decision 3 below.

**What happened.** Morgan's account usage report showed 183 minutes billed
on 2026-09-18 and 165 by noon on 2026-09-19 — a session diagnosed it in
that repo, not this one, because the driver was four of Morgan's private
practice sets (`precedent-individual`, `precedent-team-writing`,
`precedent-team-repo-maintenance`, `precedent-team-working-style`),
accounting for 86% of the 2026-09-19 total before noon. All four had
`precedent-check.yml`/`views-drift.yml` installed per "Install in a
Practice-Set Repository" ([GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md)) — debounce guard included,
running at its 360-minute default, exactly as Phase C shipped it.

**Why the debounce guard didn't stop it.** Debounce (Item 4's own design)
skips the *rest* of the job when the last completed run on the branch
finished inside the window — but the checkout step and the debounce guard
step itself are not behind that gate; they run on every trigger,
unconditionally, by construction (the guard has to check out the repo and
call `gh run list` before it can know whether to skip anything else).
GitHub bills in whole minutes, so a "skipped" run is not a free run — it's
a cheap one. The four sets carry `push:` with no `branches:` restriction
(2026-09-14, per each workflow's own comment) and no `paths:` filter
(deliberate, per the same comment), so every push to every session's
`claude/*` working branch paid that baseline, and there were dozens of
such branches across the four repos. Debounce collapses the *expensive*
tail of a run; it does nothing about trigger *volume*, which turned out
to be the actual cost driver once real branch churn hit it.

**Fix applied, 2026-09-19, directly in the four repos** (this session has
push access there; BestPractice's own session-scoped access still does
not reach Morgan's other repositories, per "Sequencing and status" below):
`push:` restricted to `branches: [main]` in both workflows, and the
debounce window tightened from 360 to 30 minutes (`ci_debounce_minutes`,
in `identity.json` where one exists) —
[precedent-individual#153](https://github.com/themorgan/precedent-individual/pull/153),
[precedent-team-writing#41](https://github.com/themorgan/precedent-team-writing/pull/41),
[precedent-team-repo-maintenance#87](https://github.com/themorgan/precedent-team-repo-maintenance/pull/87),
[precedent-team-working-style#41](https://github.com/themorgan/precedent-team-working-style/pull/41),
all merged. **The tradeoff accepted**: a `claude/*` branch pushed to
directly now gets zero automatic CI until it reaches `main` — verified
locally instead, via the same mechanical checks the merge runbook already
runs before a merge commits (deep-check's own Rule: "the same set the
merge runbook already runs on every merge"), so a session following its
own process loses no real coverage; what's lost is the independent,
externally-visible backstop for a merge that skips that process.

**Not done here at the time**: the templates themselves still shipped
`push:` with no branch restriction. Done the same day, item 9 below.

## Item 9 — the templates themselves, so a future install doesn't repeat item 8 (2026-09-19)

Item 8 fixed four already-installed repos by hand. Nothing about that
touched the **templates** those repos originally installed from — a
practice set bootstrapped today ([tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)), or any
repo freshly given `precedent-check.yml`/`doc-lint.yml` by
[tools/precedent_install.py](../tools/precedent_install.py), would still get the design that caused the
incident. Fixed the same day, once Morgan asked whether it needed to be
done in BestPractice (BP) too — he did: "does this fix need to be
implemented in BP so that future repos we create with it don't have that
issue?" `strength: decided` ("Yes, go ahead and implement it").

**Three changes, all three templates:**

1. `precedent-check.yml.template` and `views-drift.yml.template` are now
   **one template**, `precedent-check.yml.template` — the same merge item
   8 applied to the four repos, now upstream. `views-drift.yml.template`
   no longer exists; installing `precedent-check.yml.template` installs
   both checks, as its `precedent-check` and `views-drift` jobs.
2. **Debounce moved into its own job in all three templates**
   (`doc-lint.yml.template` included, previously a single job with a
   debounce STEP — the same step-vs-job distinction item 8 measured: a
   step-level skip still bills the job's own runner-minute, a job-level
   `if:` that evaluates false is never billed at all).
3. **`pull_request: [opened, synchronize]` added back to all three,
   alongside `push:` scoped to `branches: [main]`** — not push
   unrestricted (item 8's own problem) and not push-restricted-alone
   (item 8's *first* fix, which gave up automatic verification on
   anything short of a merge — a different repo's CI catching a real
   error on an open PR the same day is what changed Morgan's mind on
   that trade). Each template's own header documents how to widen the
   branch list for a repo whose routine merge target isn't just `main` —
   this repo's own `docs.yml`/`deep-check.yml` (not `leak-gate.yml`,
   deliberately: see below) got the same treatment, listing
   `[main, precedent-beta-v01]`.

**Why this doesn't reintroduce the exact duplicate-run problem
`doc-lint.yml.template`'s own header already measured** (235 runs in
matched pairs, before `pull_request:` was dropped entirely on
2026-09-15): that measurement was push running on *every* branch,
overlapping `pull_request:synchronize` on any branch with an open PR.
With push now scoped to only the named branch(es) — never a PR's own
head — a PR's branch only ever gets `pull_request` events and a named
branch only ever gets `push` events. Nothing fires twice for the same
commit. This repo's own `leak-gate.yml` was deliberately left alone: its
every-branch scope is a security backstop (a leak is exposed the instant
it's pushed to this public repo, PR or not), not a cost or coverage
trade, so the branch-scoping reasoning above does not apply to it.

**Documented, not just changed**, per Morgan's own instruction that this
be written up for whoever adapts it: [templates/github-actions/README.md](../templates/github-actions/README.md)
has the trigger shape and the branch-list customization point up front;
[GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md)'s "Controlling Actions Minutes" and "Install in a
Practice-Set Repository" sections carry the mechanical detail; this item
is the incident and reasoning. [TODO.md](../TODO.md)'s
[`views-drift-vs-suite-workflow`](../todo/todo-2026-09-13-views-drift-vs-suite-workflow.md)
closes — the merge above is its answer.

Verified: all edited/new template files parse as valid YAML; deep check
([tools/verify_harness.py](../tools/verify_harness.py), [tools/doc_lint.py](../tools/doc_lint.py), [tools/leak_gate.py](../tools/leak_gate.py), [tools/precedent_check.py](../tools/precedent_check.py),
[tools/doc_sync.py](../tools/doc_sync.py)) run clean before each push in this item's own PRs.

## Item 9a — two engine-level gaps items 8-9's hand-fixes exposed (2026-09-19)

Re-baselining `ci_workflows_sha256` by hand in the four repos item 8 fixed
(dropping a stale hash after each one's hand-applied fix, and a stale
`views-drift.yml` tracking entry in `themorgan/precedent-individual` left
over from item 9's own consolidation) surfaced two gaps in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
itself, not just in those repos' manifests:

1. **No retirement mechanism for CI workflow templates.**
   `RETIRED_ENGINE_FILES`/`_remove_dropped_engine_files` already handle
   this for ordinary vendored files under [tools/](../tools/); `ci_workflow_files`/
   `ci_workflows_sha256` had no equivalent, so folding
   `views-drift.yml.template` into `precedent-check.yml.template` left
   every set that already had it tracked with a stale manifest entry
   `refresh()` would read as a missing, hand-edited file — refusing the
   whole run — the next time it ran there. Fixed with
   `RETIRED_CI_WORKFLOW_FILES` (a tombstone dict mirroring
   `RETIRED_ENGINE_FILES`) and `_remove_retired_ci_workflow_files`, called
   unconditionally at the top of `refresh()`: a retired entry is dropped
   from the manifest automatically, and a retired file still on disk is
   reported, never deleted — matching this repo's own stated design that
   a CI workflow file is never removed automatically (item 9's own
   comment on `ci_incomplete`).
2. **No way to re-baseline a CI workflow's recorded hash without a full
   clone.** `record_ci_workflow_files()` already does exactly this —
   record what's on disk, touch no content — but was reachable only from
   inside [tools/precedent_install.py](../tools/precedent_install.py)/
   [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py) at
   install time, or by importing the module directly (which is what
   fixing the two dependent repos' stale hashes above actually took). A
   session hand-fixing a CI workflow file mid-incident has no supported
   way to tell the manifest the fix is correct short of
   `refresh --force` against a live clone, which would overwrite the
   hand-authored fix with the generic template. The new `record-ci`
   subcommand (clone-free, like `fresh`) closes this.

Both verified against scratch fixtures reproducing each incident, and
covered by a new `check_vendor_engine_retires_ci_workflow_files` in
[tools/verify_harness.py](../tools/verify_harness.py) (11 cases) alongside
the existing CI-workflow refresh coverage. Deep check run clean before
push, same as item 9.

## Item 10 — item 6 generalized: a runner override any adopter can opt into (2026-09-20)

Item 6's self-hosted-runner pilot is scoped to Morgan's own repos — it
solves the metered-minutes problem for the account running the pilot, not
for anyone else who installs Precedent as open-source software into their
own repo. Raised the same way: **"a self-hosted runner solves the problem
FOR ME, but not for the other random people we want to use this open
source software."**

Two things were already true and needed no work: a **public** repo's
Actions minutes are unmetered on standard runners regardless of any of
this, so an open-source adopter who keeps their repo public already gets
item 6's outcome for free; and for a **private** adopter, the four levers
items 1–5/8/9 already ship (opt-in `ci_workflows`, branch-scoped
`push:`/`pull_request:`, the job-level debounce, `concurrency`) already
shrink cost automatically, with no setup, for every install.

**What was missing:** the templates had no way for an adopter who *does*
already operate a self-hosted runner to point their own install at it
without hand-editing the workflow file. Added:
`runs-on: ${{ vars.PRECEDENT_RUNNER || 'ubuntu-latest' }}` on every job in
[doc-lint.yml.template](../templates/github-actions/doc-lint.yml.template)
and
[precedent-check.yml.template](../templates/github-actions/precedent-check.yml.template).
Unset, nothing changes for anyone. Set as a repository variable, every job
in that workflow moves to the named runner — the same escape hatch item 6
describes, generalized from something only this session can apply to
Morgan's own repos into something any adopter can flip for themselves.
Documented in [documentation/GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md)'s
"Controlling Actions Minutes" (now four levers, plus the public-repo note)
and [templates/github-actions/README.md](../templates/github-actions/README.md).

**This does not replace item 6/Phase D.** Whether to actually run a
self-hosted-runner pilot on Morgan's own repos, and which ones, is still
open — this item only makes the mechanism available to whoever wants it,
including Morgan, without deciding the pilot question for him.

**Reaches dependent repos only when they take an update.** Per
`vendor-rollout-disclosed`: this changes shipped template content
(`templates/github-actions/*.template`), so it needs
[vendor-update-runbook](../practices/vendor-update-runbook.md)'s normal
"Update Vendors" path to reach an already-installed repo — nothing here
pushes it there automatically, and a repo on an older template keeps
running unconditionally on `ubuntu-latest` until it takes that update.

Authorized: *"On #3 -- do it, go update -- and also update the developer
documentation."* strength: decided.

## Sequencing and status

Morgan approved phases 1–5 on 2026-09-16, holding items 6 and 7 for later
(tracked in
[todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md](../todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md),
due 2026-09-19). **What "done" means here is scoped to this repository**:
this session can build and merge everything BestPractice itself owns — the
installer, the templates, the migration and update runbooks — but it
cannot push to Morgan's other repositories, which are outside this
session's GitHub access. Turning any of this ON for a given dependent
repo, practice set, or team repo is still a separate action in that
repo, the next time it installs, migrates, or takes an update.

- **Phase A — done.** `ci_workflows` gates every current CI template, not
  only `bestpractice-docs.yml` (item 1);
  [spec/INSTALL_QUESTIONS.md](INSTALL_QUESTIONS.md) is the canonical
  install/migration question list, with the two new questions added and
  SETUP.md/INSTALL.md/MIGRATING_EXISTING_INSTALLS.md pointed at it (item
  1a); `precedent-check.yml.template` (which now also carries what
  `views-drift.yml.template` used to, item 9) carries the same
  `concurrency` block `doc-lint.yml.template` already had (item 5).
  Archiving the repo already named for its own deletion is still
  Morgan's to do — that repo is outside this session's reach.
- **Phase B — the retired-workflow deletion sweep still hasn't run
  anywhere; the costly part reached all four repos on its own, ahead of
  it (verified 2026-09-19).** `MIGRATING_EXISTING_INSTALLS.md`'s step 6
  and `vendor-update-runbook.md`'s step 10 still carry the
  retired-workflow table for items 2/2a/3's file-deletion pass, and that
  hasn't run in any dependent repo yet — two of the four dependent repos
  checked still carry the named retired files
  (`light-check.yml`, `bestpractice-upstream-sync.yml`, and, in one of the
  two, `platform-docs-check.yml`/`status-claims-check.yml`/
  `unified-prompt-check.yml`), unremoved. That's cosmetic, not a live
  cost, though: their triggers are already `pull_request`-with-`paths`
  or `workflow_dispatch` only, so none of them fire on an ordinary push.
  Separately, and sooner than this bullet originally expected: item 9's
  fix reached all four repos this session checked
  (`themorgan/precedent-individual`, `themorgan/precedent-team-writing`,
  and the two dependent repos above) the same day it
  shipped here, without waiting for a full migration pass — `abc667a`
  (2026-09-18) taught "Update Vendors" to refresh an already-installed CI
  workflow file against its current template, not just write it once at
  install; the two practice sets took the fix that way plus a direct
  hand-applied commit each (item 8's own account), while the two
  dependent repos got a hand-applied fix after "Update Vendors" backfilled
  a manifest baseline for a file it had never tracked before (which, by
  that commit's own design, does not rewrite content on its first run).
  Verified directly against all four repos' `.github/workflows/` on
  2026-09-19: branch-scoped `push:`, debounce as its own job, and
  `pull_request:` restored, matching this document's own item 9.
  **One bookkeeping gap found in the same check:** both dependent repos'
  hand-applied fixes left `tools/ENGINE_MANIFEST.json`'s
  `ci_workflows_sha256` pointing at the pre-fix hash for
  `bestpractice-docs.yml`, so the next template improvement to
  `doc-lint.yml.template` would have read that file as hand-edited and
  refused to auto-refresh it there — fixed the same day via the new
  `record-ci` subcommand (item 9a below).
- **Phase C — done, exercised live, and revised (items 8-9).** A debounce
  guard (`ci_debounce_minutes`, default `360`) ships in
  `doc-lint.yml.template` and `precedent-check.yml.template` (which now
  also carries what `views-drift.yml.template` used to), and nowhere
  else — not in this repo's own three workflows, per item 2b below (item
  4). Its first real run, on four of Morgan's practice sets, showed it
  caps a run's expensive tail but not the baseline cost of the
  checkout-plus-guard steps that ran unconditionally on every trigger.
  Item 9 revised both templates to move the guard into its own job (a
  job-level skip is never billed at all, unlike a step-level one) and add
  a branch-scoped `push:` plus `pull_request:`, which is the volume fix
  the debounce guard alone was never designed to provide. Full account:
  items 8 and 9 above.
- **Phase D — held; item 10 shipped alongside it, 2026-09-20.** The
  self-hosted runner *pilot* on Morgan's own repos (item 6) is still held,
  per the todo reminder above. What shipped is a different, narrower piece:
  the `PRECEDENT_RUNNER` template variable (item 10) that lets *any*
  adopter opt a private install onto their own runner, and the
  [documentation/GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md)/[templates/github-actions/README.md](../templates/github-actions/README.md)
  updates describing it — this closes the "other random people" gap item 6
  never addressed, without deciding the pilot question for Morgan's own
  repos.

## Open decisions

1. **Item 2b: keep this repo's own `docs.yml`/`deep-check.yml`/`leak-gate.yml`
   mandatory, un-gated by any of the above?** Still open — "phases 1-5"
   approved everything above, and item 2b was deliberately held out of
   every phase rather than folded into any of them, so this needs its own
   answer. Recommendation unchanged: yes, given the security rationale on
   record and that this repo is public (so nothing here is actually
   costing money).
2. **`ci_workflows` granularity** — implemented as one field gating every
   template, not per-workflow control. Revisit only if a practice set
   turns up wanting its own checks but not a consuming repo's doc lint.
3. **Debounce default window** — implemented as `360` minutes (Morgan's
   own "6 hours" example) and left there in the templates; item 8's
   incident tightened it to `30` minutes in the four repos it touched, a
   per-repo call in `identity.json`/`precedent.json`, not a template
   default change. **Resolved, item 9**: all three templates now ship
   `pull_request:` alongside `push: branches: [main]`, documented in each
   template's own header and in [templates/github-actions/README.md](../templates/github-actions/README.md) as a
   customization point for a repo whose routine merge target isn't just
   `main`.
4. **Which workflows are debounce-exempt** — implemented as: every
   vendored template gets it, this repo's own three workflows do not.
5. **Self-hosted runner pilot scope** — still open, deferred to items 6/7's
   todo reminder.

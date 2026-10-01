# GitHub Actions Checks

Precedent uses repository checks for rules that should not depend on a particular person or AI Assistant remembering to run them.

This is especially important when working through GitHub-connected ChatGPT. A normal ChatGPT conversation can read and update repository files, but it does not receive a local checkout or an interactive shell *(as of 2026-08 — [MOBILE.md](MOBILE.md) tracks this capability and is the place to re-date it)*. GitHub Actions supplies the missing execution environment: ChatGPT prepares a branch, GitHub runs the checks, and the result appears on the pull request.

## Precedent's Own Workflows (This Repo, Not a Template)

Two workflows run on this repo itself, in [.github/workflows/](../.github/workflows/).
(A third, `docs.yml`, ran the Markdown lint here until that left CI on
2026-09-21; see the next section.)

- **`deep-check.yml`** — added by a 2026-09-03 deep-check audit. Runs
  [tools/verify_harness.py](../tools/verify_harness.py),
  [tools/precedent_check.py](../tools/precedent_check.py) and
  [tools/doc_sync.py](../tools/doc_sync.py) — the three of AGENTS.md's five
  named "deep check" tools that had no continuous-integration (CI) check
  of their own until this landed, having been session discipline only.
  That gap is exactly where
  a same-day audit found two critical, reproduced bugs (a self-referential
  `repo-local` source silently destroying its own content, and a second
  that broke every re-sync after it) sitting undetected on a branch whose
  merges were all green — neither doc_lint.py nor leak_gate.py could ever
  have caught either, since neither runs the resolver or materializer at
  all. It runs on a pull request into `main` (since 2026-09-25) and on every
  push to `main` (since 2026-09-27), where it stops after a few seconds if
  those exact files already passed it -- this repo's one GitHub test
  ([spec/BRANCH_TIERS_PLAN.md](../spec/BRANCH_TIERS_PLAN.md)); every other
  push is checked locally by the push check first.
- **`leak-gate.yml`** — added at phase 2 of the Precedent rewrite
  (`b3bfb54`). Runs [tools/leak_gate.py](../tools/leak_gate.py)'s structural
  layer on every push and every pull request, on every branch (this repo is
  the branch being published, not just its default). It is the unbypassable
  backstop for the private-source separation described in
  [spec/PRACTICE_ENGINE_PLAN.md](../spec/PRACTICE_ENGINE_PLAN.md)'s "Source — Who a
  Practice Belongs To": a `git push --no-verify` can skip the local
  [pre-push hook](../templates/hooks/pre-push), but not this. See
  [spec/SOURCES.md](../spec/SOURCES.md) for what it checks and why it has two
  layers, only one of which can run here. (This section exists because the
  workflow went undisclosed for months after being added — the practice
  requiring disclosure, `github-setup-disclosed`, only fires on a
  newly-added workflow file in the diff being checked, so it structurally
  cannot catch a workflow that was already merged before the practice
  existed to check it. Found by a 2026-09-01 deep-check audit; see
  [tools/verify_harness.py](../tools/verify_harness.py)'s
  `check_all_workflows_disclosed` for the tree-wide check added in
  response, which does catch this going forward.)

## The Markdown Check Left CI On 2026-09-21

**There is no Markdown workflow any more.** `doc-lint.yml.template` (which
installed as `bestpractice-docs.yml`) and `doc-lint-scheduled.yml.template`
are deleted, and `.github/workflows/bestpractice-docs.yml` is tombstoned in
`precedent_vendor_engine.RETIRED_CI_WORKFLOW_FILES` — so the next
`Update Vendors` removes it from every repository that installed it.

**The linter is not retired.** Only the workflow whose whole job was to run
it a second time. Under this system's founding assumption every edit
arrives through a cloud session, never a local checkout and never the
GitHub web UI, so
[doc_lint.py](https://github.com/alex137/BestPractice/blob/staging/tools/doc_lint.py)
has already run on every change before it is committed. CI was re-checking
work the session in front of the person had just cleared — a measured 350
billed minutes over 19 days in one repository, on a workflow that was
already one job with `paths:` filters from the day it was installed
([spec/BILLING_FLOOR.md](../spec/BILLING_FLOOR.md)).

**What replaced it is stricter than what went.** "The light check gates a
commit" was written down and followed, but nothing refused a commit that
skipped it — so CI was the real backstop. `.claude/hooks/doc-lint-gate.sh`
now denies a `git commit` whose staged Markdown fails the linter, handing
back the linter's own output. It costs no Actions minutes and it catches
the problem **before** the commit rather than after the push.

**The rule: no workflow exists solely to lint Markdown.** A check that only
re-runs what a session already ran is not a backstop; it is a second
invoice for the same work.

### If You Are NOT Working Through Claude Code, Put the Check Back

**The commit gate is a Claude Code mechanism.** A hook needs a shell. A
Claude Code session has one; a GitHub-connected ChatGPT conversation does
not (see the note at the top of this document), and
[templates/harness/README.md](../templates/harness/README.md)'s adapter
table shows the other harnesses carrying `n/a` or an unverified lifecycle
hook. **On any of those, nothing checks your Markdown before it reaches
the branch.**

So if that is you, do both of these — not one:

1. **Run it by hand before every commit:**
   `python3 tools/doc_lint.py <the markdown you touched>`.
2. **Turn a GitHub check on as well, as a workflow of your own.** Not by
   editing `light-check.yml`: since 2026-09-27 the engine owns that file, and
   every Update Vendors writes it back from the template. Add a separate
   one-job workflow, say `.github/workflows/doc-lint.yml`, running
   `python3 tools/doc_lint.py` on `"**/*.md"`, and record your approval of it
   in `precedent.json`'s `github_ci_approved`, in your own words and pinned
   by sha256 ([ci-workflow-approved](../practices/ci-workflow-approved.md)).
   An approved workflow is the one kind a refresh keeps. Then enable
   Actions for the repository at **Settings → Actions**.

**Neither of those is `--strict`, and the flag is not an upgrade of them.**
`doc_lint.py --strict` promotes the warning classes to failures and refuses
the changed-file scope outright, because that combination is a gate that
refuses work nobody broke — built and withdrawn inside an hour on
2026-09-21 after it turned down a one-line edit over 111 pre-existing
warnings. It is the whole-tree sweep mode, and its one caller is a very
deep check ([practices/very-deep-check.md](../practices/very-deep-check.md)).
*(Those two lines said `--strict` until 2026-09-21 — added by the very
commit that withdrew the flag, so they were stale on arrival.
[doc_lint.py](../tools/doc_lint.py) ignored unknown options silently, so
anyone following them ran the ordinary lint and got a pass either way.
Unknown options are refused now.)*

**Doing only the first is the arrangement that just failed here.** "A
session is supposed to run it" was written down and followed, and still
nothing refused a commit that skipped it — which was only ever safe
because CI was behind it. On a harness with less enforcement than the one
that had that gap, the CI check is not optional.

## The Leak Gate Template

**First vendored 2026-09-20** (spec/CI_MINUTES_PLAN.md item 12) —
[leak-gate.yml.template](../templates/github-actions/leak-gate.yml.template)
runs [tools/leak_gate.py](../tools/leak_gate.py)'s structural layer, same as
this repo's own `leak-gate.yml` above, but is not simply a copy of it: this
repo runs unconditionally on every branch because it is public and a leak
here is already published; a dependent repo may not be. The template reads
this repo's declared `visibility` (from `precedent.json`, or always
`"private"` for a practice set's `precedent-source.json`) and narrows what
it scans accordingly — full account, including why this has to be a
job-level runtime check rather than a scoped trigger (GitHub Actions cannot
read repo config before a trigger fires), in
[templates/github-actions/README.md](../templates/github-actions/README.md)'s
"The leak gate template" section. `precedent_install.py` writes it into a
consuming repo by default, beside `light-check.yml`, unless a source declares
`"github_ci_workflows": "disabled"`, and every Update Vendors rewrites it from
the template. A practice set gets no workflow at all (see "A Practice Set
Runs No CI" below).

## Controlling Actions Minutes

**What a new install gets, since 2026-09-25** ([spec/BRANCH_TIERS_PLAN.md](../spec/BRANCH_TIERS_PLAN.md)):
one GitHub test and no more. `light-check.yml` runs only on a pull request
into `main`, about one billed minute per merge into main in a private repo;
`leak-gate.yml` runs on every push in a public repo, where a push is
publication, and never in a private one, where its job is skipped before a
runner starts. Every other push is checked on the person's own machine by
the push check. **The installer writes these by default**; a declared
`"github_ci_workflows": "disabled"` still installs nothing. **Since
2026-09-27 the engine owns both**: every Update Vendors writes them from the
templates over any hand-made or hand-edited copy, and removes every other
workflow upstream does not ship that the person did not approve in their own
words. It checks first that nothing needed is lost: a file running anything
the local push check does not is left alone, under a loud banner, with what to
move named and an open item written to `todo/`. It asks nobody (`CI_CONVERGES_KINDS` in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)). The `[skip ci]` line the commit hook adds in a private
repo stays on as a backstop until every install carries these files.

**A workflow file nobody approved fails every push, since 2026-09-25**
([ci-workflow-approved](../practices/ci-workflow-approved.md)). Each file
under `.github/workflows/` is either the engine's own untouched copy or is
listed in `precedent.json`'s `github_ci_approved`, pinned by sha256 and
quoting the person. Editing a trigger changes the hash, so the edit needs
their approval too. The files the engine ships are tracked in
`ENGINE_MANIFEST.json` and need no approval entry. In a consuming repo a
finding here is settled by running Update Vendors, not by asking the person.

**Until 2026-09-25, `precedent_install.py` did not install any workflow by default (from 2026-09-15).**
GitHub Actions minutes are metered per PRIVATE repository and billed per
run, rounded up to the minute. Vendoring Precedent into many private repos
and committing the way a save button gets used means paying for a workflow
run on every one of those saves, whether the check was wanted or not — and
that adds up fastest for exactly the person most likely to be running it
everywhere.

(Named `ci_workflows` until 2026-09-25; the old name is still read.)
So the installer resolves `"github_ci_workflows"` from the individual or shared
source it can reach ([tools/precedent_identity.py](../tools/precedent_identity.py)'s
`ci_preference()`, same resolution order as `relayed_authorization`: the
repo's own `identity.json` when it IS an individual source, else the one
the user-level config names) and installs the workflow only when that
value was exactly `"enabled"`. Nothing declared resolved to disabled — the
engine's own default at the time, applied silently
([declared-default-is-applied](../practices/declared-default-is-applied.md)) —
and the install log and the project's own `GETTING_STARTED.md` both say so,
naming the field and where to set it. **This only changes what
`precedent_install.py` writes by default.** The template is always there to
copy in by hand, on any one repo, whatever the field says.

**None of this metering applies to a public repository at all.** GitHub
Actions on standard `ubuntu-latest` runners is unmetered for public repos,
regardless of how often a workflow runs. Everything below exists for the
adopter who has vendored Precedent into a *private* repo — which is most of
it, since a private, single-owner repo is the common case for an
individual's own practice set or dependent project.

**Four more levers, once the workflow is installed at all:**

- **`concurrency` with `cancel-in-progress: true`** ships in
  `doc-lint.yml.template` (retired 2026-09-21)
  itself now: if a second run starts on the same branch while an earlier
  one is still going, GitHub cancels the earlier one instead of billing
  both. It only helps the *overlap* case — two pushes closer together than
  one run takes (well under a minute here) — so it is a real but small
  saving for a steady stream of spaced-out saves, not the fix for that
  case.
- **A scheduled cadence instead of per-push billing** —
  `doc-lint-scheduled.yml.template` (retired 2026-09-21) —
  was the fix for a repo pushed to constantly, direct to its default
  branch, with no pull request in the loop: however many saves landed in one
  window, they cost one run. `precedent_install.py` never wrote it, because a `schedule:` is a clock
  in somebody else's repository that they never picked (this file's own
  Limits section says the same about an inherited schedule). It was retired
  with the Markdown workflow it replaced, and there is no scheduled
  template to copy any more.
- **One job per workflow — the lever that replaced the debounce**
  (2026-09-20, [spec/CI_MINUTES_PLAN.md](../spec/CI_MINUTES_PLAN.md) item
  13). GitHub bills **per job, rounded up to a whole minute**, so what a
  workflow costs on a trigger that fires is mostly its job count, not its
  run time. Measured on a real installed practice set:
  [precedent_check.py](../tools/precedent_check.py) takes **0.35s** and
  [build_views.py](../tools/build_views.py) `--check` **0.12s** — 0.47 seconds of
  work that the three-job shape billed as **three minutes**, paying for
  three checkouts and three Python setups to carry it. Both
  `doc-lint.yml.template` (retired 2026-09-21)
  and [precedent-check.yml.template](../templates/github-actions/precedent-check.yml.template)
  now ship **one job**, and a trigger that fires bills one minute.
- **The `debounce` job and `ci_debounce_minutes` are RETIRED** (2026-09-20).
  A debounce job skipped the check job(s) that `needs:` it when the last
  completed run on the branch was recent. A skipped job really is unbilled —
  but **the job that decides is billed like any other**, which the shape
  never accounted for. With `S` the fraction of triggers skipped, a
  debounce job plus `N` check jobs costs `S + (1-S)(1+N)` against `N` for
  no debounce at all: worse for every `S` below 1, at every window setting.
  That is why tuning the window `360 → 30 → 720` across three days (items
  8, 9 and 11) never moved the bill — the cost being tuned was not the one
  doing the spending. A repo that still carries `ci_debounce_minutes` in
  its `precedent.json`/`identity.json` can delete the field; nothing reads
  it any more.
- **`pull_request:` alongside a branch-scoped `push:`, not push on every
  branch** (2026-09-19, [spec/CI_MINUTES_PLAN.md](../spec/CI_MINUTES_PLAN.md)
  item 8) — both templates ship `push: branches: [main]` plus
  `pull_request: [opened, synchronize]`. A branch with no open PR triggers
  neither event that matches here, so the workflow is never evaluated —
  the cheapest lever there is, because GitHub decides it before allocating
  any runner. A branch with an open PR gets checked on each synchronize,
  with `concurrency:` collapsing a burst into one surviving run. Widen the
  branch list
  (`branches: [main, staging]`, this repo's own pattern) if the
  repo installing this has more than one routine merge target — each
  template's own header says so at the trigger block. Do not add
  `pull_request:` to a `push:` that still covers every branch: that
  reintroduces the exact duplicate-run problem
  `doc-lint.yml.template` (retired 2026-09-21)'s
  own header measured (235 runs in matched pairs) before this repo's own
  `docs.yml`/`deep-check.yml` dropped `pull_request:` outright on
  2026-09-07/2026-09-14 — the fix here is scoping `push:` narrowly enough
  that it never fires on the same branch `pull_request:` is watching, not
  running both wide open.
- **A `PRECEDENT_RUNNER` repository variable, for an adopter who already
  operates a self-hosted runner** (2026-09-20). Every job in
  `doc-lint.yml.template` (retired 2026-09-21)
  and [precedent-check.yml.template](../templates/github-actions/precedent-check.yml.template)
  reads `runs-on: ${{ vars.PRECEDENT_RUNNER || 'ubuntu-latest' }}` — set the
  variable (**Settings → Secrets and variables → Actions → Variables**) to a
  self-hosted runner label, and every job in that workflow runs there
  instead, with no template edit. Left unset, nothing changes. **This is
  the one lever above that is not a safe default for anyone who installs
  Precedent** — the other three shrink cost automatically; this one only
  does anything once an adopter has already stood up and secured their own
  runner, which nobody else can do for them (a self-hosted runner executes
  whatever code triggered the workflow, so it is a real security posture
  choice, not a setting to flip casually — [spec/CI_MINUTES_PLAN.md](../spec/CI_MINUTES_PLAN.md)
  item 6 has the trade-offs in full, including why GitHub itself advises
  against a self-hosted runner on a repo that takes untrusted forked
  pull requests). This variable is the mechanism; deciding whether to use
  it is the adopter's own call, one repo at a time.

## Install in a Dependent Repository

Nothing to copy by hand. `precedent_install.py` (INSTALL.md §0) writes
`.github/workflows/leak-gate.yml` and `.github/workflows/light-check.yml`
from [templates/github-actions/](../templates/github-actions/) by default,
and records both in `tools/ENGINE_MANIFEST.json`. A source that declares
`"github_ci_workflows": "disabled"` switches both off. The engine owns them
from then on: see "Updating an Installed Repository" below, and
"Controlling Actions Minutes" above for what each costs.

The Markdown lint is not among them. It left CI on 2026-09-21 (the section
above) and runs before every commit instead.

## A Practice Set Runs No CI

**An individual or shared practice set carries no GitHub workflow**
(practice `source-sets-run-no-ci`, decided 2026-09-21 on a usage export in
which four sets running two workflows each were 127 of 143 billed minutes
in one day). Its checks run in the session before every push:
`python3 tools/precedent_check.py --full-sweep`, which includes the
generated-views drift check (`generated-artifact-provenance`, the same
comparison `python3 tools/build_views.py --check` makes). A set created by
[tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
gets no workflow, and the engine refresh deletes one an older set still
carries.

`templates/github-actions/precedent-check.yml.template`, the workflow sets
used to run, is still in the repository but ships to no kind of repo
(`CI_WORKFLOW_TEMPLATES['source']` in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) is
empty).

## Enable GitHub Actions

GitHub Actions is normally available automatically, but an organization or repository administrator can restrict it. After merging the workflow onto the default branch:

1. open the repository's **Actions** tab and confirm that the workflow is allowed to run;
2. open a pull request into `main`;
3. confirm that **Light check** appears in the pull request checks; and
4. inspect the job log if the check fails or reports warnings.

The first pull request that introduces a workflow may be subject to GitHub's normal approval or security controls, especially for contributions from forks.

Two further settings belong to the same moment and are worth mentioning
when an install finishes ([INSTALL.md](../INSTALL.md) §1 step 10): the
**default branch should be named `main`** (**Settings → General → Default
branch**), since the light check's `pull_request` trigger names `main` as a
literal string and a differently-named default branch runs no check on
merges; and **workflow permissions should allow Actions to open pull
requests** (**Settings → Actions → General → Workflow permissions**), which
the supplied workflows do not need but anything opening a pull
request for the project does. *(Click-paths as of 2026-09-10.)*

**Optional: turn Actions off where a repository needs no GitHub check.**
**Settings → Actions → General → Actions permissions → Disable actions**
*(as of 2026-09-26)*. Every run in a private repository bills minutes,
and a workflow nobody approved bills from the moment it lands, however it
got there: through a session, through the GitHub API, or edited on the
website. With Actions off, nothing in that repository can run. The local
push check keeps working. Offer it at the end of an install as optional,
never as a step the install needs.

## Make the Check Required

Once the workflow has run successfully at least once, add its **Light check** job to the default branch's ruleset or branch-protection required checks.

That changes the rule from advice into enforcement: a pull request cannot merge into `main` while the light check is failing, regardless of whether the change came from ChatGPT, Claude Code, Codex, another agent, or a human editing GitHub directly.

Repository rules vary by account and organization. Use the repository's current **Settings → Rules** or branch-protection controls and select the status check produced by this workflow. The rest of what belongs on that same page — a pull request required, review from code owners, no bypass — and what each setting does for a Precedent project is [documentation/GITHUB_SETTINGS.md](GITHUB_SETTINGS.md).

## Updating an Installed Repository

**Update Vendors does it; there is nothing to compare by hand.** Every
refresh writes `leak-gate.yml` and `light-check.yml` from the templates over
whatever the repository has, hand-made or hand-edited, and removes every
other workflow upstream does not ship that the person did not approve in
their own words (practice `ci-workflow-approved`). It checks first that
nothing needed is lost: a workflow running something the local push check
does not is left alone, under a loud banner, with what to move named and an
open item written to `todo/`. A retired workflow, such as
`bestpractice-docs.yml`, is deleted the same way
(`RETIRED_CI_WORKFLOW_FILES` in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)).

## Limits

GitHub Actions closes the test-execution gap, but it does not make ordinary ChatGPT identical to a coding-agent workspace *(as of 2026-08)*. ChatGPT still needs the session bootstrap described in the main README so it reads `AGENTS.md`, `MAP.md`, and the task-relevant instructions before working.

The useful division of responsibility is:

> Agents interpret intent and prepare changes. GitHub Actions enforces repeatable checks.

**A workflow that COMMITS is outside
[commit-identity.sh](../templates/harness/claude-code/hooks/commit-identity.sh)'s
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
[tools/precedent_identity.py](../tools/precedent_identity.py) moved into the
vendored engine that same day. The moment they went live, the workflow's own
commit was the first thing they flagged. **Two silent failures were holding
each other up**, which is the general shape worth remembering: a check that
cannot run is not evidence that what it checks is fine.

**A CONSUMING repo's generated views cannot be gated in CI at all.** A consuming repo's
`practices/` is materialized from the sources it resolves: a shared source is
a sibling clone outside the repo, an individual source resolves through a
private user-level config. Neither exists in a bare CI checkout, so there is
nothing on the runner to regenerate the views *from* — and
[tools/build_views.py](../tools/build_views.py) deliberately exits 0 rather
than writing a block from an incomplete source set, which is the shape a
green-but-blind check would take. So no workflow a consuming repo gets
checks its views. What covers a consuming repo today is a session running
`python3 tools/precedent_sync_views.py --repo . --check` where the sources
do resolve; [TODO.md](../TODO.md)'s
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
comment, a merge).** [tools/github_budget.py](../tools/github_budget.py) prints
what is left and what a tool spent; the rule is
[github-api-budget](../practices/github-api-budget.md).

Two things about workflow triggers are still worth getting right for their
own reasons, and both are about wasted runs rather than wasted allowance:
`pull_request:` alongside `push:` fires two runs of the same tree for every
push on a branch with an open pull request (measured here over 13 paired
runs, never once disagreeing), and a `schedule:` inherited by every adopter
is a clock in somebody else's repository that they never picked.

Precedent itself ships no committing workflow — its two
([deep-check](../.github/workflows/deep-check.yml),
[leak-gate](../.github/workflows/leak-gate.yml)) all read and none writes — so
there is nothing to fix here. This is a limit to know before you add one.

*GitHub interface and product behavior verified August 2, 2026. Settings and labels can change.*

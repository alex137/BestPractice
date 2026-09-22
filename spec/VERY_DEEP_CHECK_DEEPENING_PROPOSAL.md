---
title:         "Deepening the very deep check: fourteen proposed additions"
kind:          proposal
status:        executed
opened:        2026-09-21
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       "Reads the very deep check's current formula against the incidents of 2026-09-14 to 2026-09-21 and proposes fourteen additions: the seam between repositories, the facts only GitHub holds, identity read off the commits, the accretion of files nobody reads whole, and the loop that makes each run deepen the next."
---

# Deepening the very deep check: fourteen proposed additions

**Twelve of the fourteen are built and merged.** Morgan asked, on 2026-09-21,
for a close read of the check's own formula against the week's real failures,
and for specific proposals rather than a plan; he then authorized the five
this document recommended first, in that order (strength: decided). Each item
below says what to add, which pass it belongs in, whether it is mechanical or
a read, what it would have caught, and what it costs. **Item 6 is held for a measured reason below; item 13's
fix-sweep half remains a read.**

## What shipped, 2026-09-21

| Item | What landed | Where |
|---|---|---|
| **11** — settle the rotation | Step 2 says `verify_harness.py --all`; `PLANTED CASE COVERAGE` says every run whether this invocation settled it or owes it; `--with-harness` runs it and ledgers the result | [practices/very-deep-check.md](../practices/very-deep-check.md), [tools/very_deep_check.py](../tools/very_deep_check.py) |
| **5** — workflow reality | `WORKFLOW REALITY` asks GitHub per file: registered, active, last run, does that run postdate the newest commit — with both limits printed. Plus `workflow-yaml-github-can-parse`, an enforced check refusing a YAML anchor in any workflow or shipped template, with a planted case carrying `&&`, `2>&1` and `*.md` so it proves it tells them apart | [tools/precedent_check.py](../tools/precedent_check.py), [tools/verify_harness.py](../tools/verify_harness.py), pass 2 item 19 |
| **1 + 2** — the deletion direction | `precedent_vendor_engine` names every tracked file that still refers to something it just deleted, on both removal paths; `DELETIONS PENDING` asks the same question before the refresh rather than during it; a harness case covers both directions | [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py), pass 1 |
| **12** — incident to detector | `INCIDENT COVERAGE` lists every gotcha filed and item closed since the ledger's last run, with what cites each slug. **First run: four of six gotchas filed that week were cited by nothing** | pass 2 item 20 |
| **9** — the holistic-read registry | `ACCRETION` ranks tracked files by commits since anybody recorded reading them whole; `--record-read` writes [record/holistic-reads.json](../record/holistic-reads.json) and refuses a path that does not exist. The registry starts empty — back-dating a row would invent the evidence it exists to hold | pass 3 |

**Items 3 and 8 landed next**, on the same authorization, after Morgan asked
for the next step in the plan to be built:

| Item | What landed | First run |
|---|---|---|
| **3** — the carry-through roll-up | `CARRY-THROUGH`: per repo in force, what it vendored, where upstream is now, and how many engine files were added, changed or **removed** since — removals by name, because a removal arriving on the next refresh is the one that breaks something. Reports; refreshes nothing | One source behind by five changed engine files, three current. **The first time this check has ever been able to see a stale vendored tree** |
| **8** — identity off the commits | `IDENTITY REALITY`: the author of every commit in the window against the declared identity, the author-date offset against the declared timezone at that instant, and any tracked `settings.json` hardcoding `GIT_AUTHOR_*`. Somebody else's authorship is a note; a commit authored by nobody in particular is a finding | **Four of the five repos in force carry commits with the wrong author-date offset** — 17 at `+00:00` and 8 at `-04:00` against 275 at the declared `-03:00`, in this checkout alone. The one repo that declares its own identity came back clean, and its hardcoded `settings.json` was correctly read as the documented case rather than the bug |

**Items 7 and 10 landed next**, on the same authorization:

| Item | What landed | First run |
|---|---|---|
| **7** — the Actions bill | `ACTIONS FLOOR`: per workflow in every repo in force, runs × jobs over the window — the run count from one API call with a `created` filter, the job count read off the workflow file. A floor, never an invoice, and the lever it exposes is job count per workflow | **5,441 floor-minutes over 14 days in this checkout alone** — 1,356 deep-check runs × 3 jobs, plus 1,373 leak-gate runs × 1. The practice sources run no CI at all, which is `source-sets-run-no-ci` working |
| **10** — config keys | `CONFIG KEYS`: every key declared in every `precedent.json` and `identity.json` in force, against every script the repo carries. Where a key has no local reader the row names which other repo mentions it | Two sources declare `grandfathered_commit_shas` with its readers living in a different repo in force — decidable rather than alarming, which is the whole point of naming where |

**Items 4, 13 and 14 landed next**, on the same authorization:

| Item | What landed | First run |
|---|---|---|
| **4** — does a deletion propagate, per shipped class | A three-column table in the practice, dated and re-verified each run: addition, change and deletion, one row per class this repo ships | **Its first asking found one**: a hook dropped upstream has **no removal path at all** — `precedent_vendor_engine` has exactly two, for engine files and CI workflows. The identical asymmetry the CI path carried until the day before. Filed as [todo-2026-09-21-a-dropped-hook-never-leaves-a-consumer](../todo/todo-2026-09-21-a-dropped-hook-never-leaves-a-consumer.md) |
| **13** — sweep the class | `CHECK COVERAGE`: each repo's **own** vendored `precedent_check.py --full-sweep`, reported as passed/violated/skipped with the skips **grouped by cause**, the slug normalised out so one structural reason cannot wear forty names. This is also the mechanical half pass 2's question 15 had specified and never had | **All four sources skip 44 checks for one cause** — each keyed to a `practices/<slug>.md` a source set does not carry. Question 15 measured this in one set in September; it is every set |
| **14** — premise-dated claims | `MOVED CLAIMS`: the sentence shapes that assert work moved somewhere — *now runs in*, *folded into*, *superseded by* — with the named destination checked for existence | **Zero rows in three repos and five in the one where the incident happened**, all naming the `precedent-check.yml` a refresh deleted out from under them |

**Three narrowings in item 14 were forced by measurement, not designed in**,
and they are the difference between a usable detector and one nobody runs
twice: `see X` is a pointer rather than a move claim (39 rows of pure noise);
markdown link text is stripped, since `doc_lint` already checks the real
target; and a vendored file's prose belongs to upstream, so manifest-recorded
files are skipped.

**Item 13's first finding was acted on 2026-09-22**, which is the part a
check that only reports never reaches. `CHECK COVERAGE` found all four
sources skipping 44 checks for one cause. Reading all 44 one at a time, with
`binds_publishers` forced on in each reachable set, put **13 of them** under
enforcement in a source set for the first time — and stopped a fourteenth,
`code-cites-practice`, which would have turned a correct practice citation
into a blocking false positive in three repos at once because it validates
slugs against the local twenty-file directory rather than the resolved
catalogue. Recorded in
[spec/PUBLISHER_GATE_AUDIT.md](PUBLISHER_GATE_AUDIT.md), with the 26 that
cannot function there listed so nobody re-measures them.

**The estimate that preceded it said twenty.** Twenty-four of the 44 function
in a source set; functioning turned out to be half the test, and six of those
inspect the repo's own machinery rather than anything it publishes. The gap
between the estimate and the audit is the audit's whole value.

**Item 13's remaining half landed 2026-09-22.** `FIX SWEEP` takes every
check registered here since the ledger's last run and runs **this
checkout's** copy of it against every repo in force — the mirror of item
15a's `CHECK COVERAGE`, which runs each repo's own vendored engine. The two
answer opposite questions and the difference is the whole point: what a
consumer enforces is the code it has, and a detector it has not vendored yet
reports nothing there, correctly, which is indistinguishable from clean.

**Its first run carried the YAML-anchor detector, built three days earlier,
into all three shared sources**: two decline for holding no workflow file,
the third runs clean. 0.8 seconds for the sweep. It also surfaced a limit
worth having found this way rather than later — **this clone holds no commit
older than the ledger's own last-run date**, because sessions clone with a
depth limit. The comparison falls back to the oldest commit present and says
so in the output, since a narrower window under-reports and a silent
under-report is the failure this whole item is about.

With that, **thirteen of the fourteen proposals are built.** Item 6 is the
one left, and it is held rather than outstanding:

**Item 6 (required status checks) was weighed here and held back**, which is
worth recording because it is the ledger's own argument applied before the
fact rather than after: this session measured
`/branches/{branch}/protection` answering **"Resource not accessible by
integration"**, so the section would print `UNVERIFIED` on every run from a
session shaped like this one. A section that cannot answer is a cost, not a
safety net.

**Corrected 2026-09-22, after the "so build it with a better token" reading
was measured and found wrong.** A hosted session's outbound proxy mediates
`api.github.com` and supplies its own credential: the same call returns the
same authenticated login with the real token, with a deliberately invalid
token, and with **no** `Authorization` header at all
([the probe, and why two refusals that read alike are not alike](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/gotchas/gotcha-2026-09-22-the-api-proxy-ignores-the-token-you-set.md)).
So no personal access token anyone creates changes what this section could
see — the limit is the session's own GitHub App installation and repository
scope. **And it would find nothing here regardless**: both `main` and
`precedent-beta-v01` report `protected: false` with zero required contexts,
so there is no protection on this repository to read. Item 6 is worth
building the day a repository in scope actually protects a branch, and not
before.

**One correction the building itself produced**, which is the argument for
running a new section rather than reasoning about it: `WORKFLOW REALITY`'s
first live run reported a source set as *"Actions is off"* while quoting a
body that said **"GitHub access to this repository is not enabled for this
session"**. Two unlike refusals reached one branch. Only a body naming Actions
as disabled is a finding now; everything else is `UNVERIFIED`, which is this
session failing to look rather than a fact about the repo.

## What the check already covers, so nothing below repeats it

[practices/very-deep-check.md](../practices/very-deep-check.md) is 2,167 lines
and four ordered passes. Read end to end, it already asks: **can an adopter
install and update** (pass 1, with real fixtures and a real consumer repo);
**do the mechanisms report what they claim** (pass 2, eighteen questions, every
one of them a defect somebody actually found); **does the writing still hold
together** (pass 3, including — since 2026-09-21 — a close read of every
always-loaded instructions file); and **catalogue, backlog, branches, crons and
deprecated files** (pass 4). Around that sit a freshness refusal, a liveness
probe, a landability probe, a component ledger, a branch sweep, a live-session
sweep, a base-branch drift read and an endgame-merge rehearsal.

**It is a serious check.** The gaps below are not things it forgot; they are
three shapes it is structurally unable to see, plus one loop it has never run.

## Three structural blind spots

**1. It reads one repository at a time, and last week's worst failures lived
between repositories.** Every pass is a repository read against itself. The
most expensive class of the week — a fix that landed upstream and never
reached anything, or a deletion that reached everything and took a live check
with it — is invisible from inside any single tree.
[todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md](../todo/todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md)
states it flatly: *"That is the structural reason a very-deep-check has never
found a stale vendored tree — not a gap in its passes, a gap in what any pass
can see."* On 2026-09-20, **18 of 22 installed repositories had never run a
refresh at all.**

**2. It reads the tree, and several failures were only ever visible to
GitHub.** A workflow file that GitHub's parser rejects does not go red — it
does not appear. A required status check naming a job that was renamed blocks
every pull request (PR) forever while every local check passes. Actions being
switched off looks, from the tracked tree, exactly like working continuous
integration (CI).
[tools/very_deep_check.py](../tools/very_deep_check.py) makes exactly four
kinds of application programming interface (API) call today — `user`, and
`repos/{owner}/{name}` three times — and **zero** against the Actions surface.

**3. It has no memory of what has ever been read whole**, so accretion is
invisible to it. This is Morgan's own question, and the measurement supports it
harder than expected. Commits in the last 30 days against current line counts:

| File | Commits (30d) | Lines | Ever read end to end? |
|---|---|---|---|
| [tools/verify_harness.py](../tools/verify_harness.py) | 379 | 26,637 | No record of one |
| [tools/precedent_check.py](../tools/precedent_check.py) | 141 | 7,530 | No record of one |
| [AGENTS.md](../AGENTS.md) | 285 | 555 | **Yes — added 2026-09-21** |
| [tools/build_views.py](../tools/build_views.py) | 94 | 2,096 | No record of one |
| [tools/routing_scope.json](../tools/routing_scope.json) | 94 | 1,257 | No record of one |
| [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) | 75 | 2,703 | No record of one |
| [practices/very-deep-check.md](../practices/very-deep-check.md) | 75 | 2,167 | No record of one |
| [tools/very_deep_check.py](../tools/very_deep_check.py) | 74 | 6,337 | No record of one |

**[`verify_harness.py`](../tools/verify_harness.py) is the extreme case and the one that matters most**:
twenty-six thousand lines, touched 379 times in a month, gating every push in
the project, and nobody has ever sat down and read it as a thing. The
instructions file got its holistic read the day somebody noticed it had gone
stale twice in one file. **Nothing generalized that fix to the rest of the
tree**, and the churn table says the instructions file was not even the worst
offender.

---

# A. The seam between repositories

## 1. Rehearse a DELETION, not only an install and an update

**Add to:** pass 1, beside "An update, not only an install."
**Mechanical.** A fixture, run by the tool.

Pass 1 builds fixtures that install and fixtures that move forward. **Nothing
has ever rehearsed the direction where upstream stops shipping something.**
The fixture: vendor a scratch consumer, drop a template from
`CI_WORKFLOW_TEMPLATES` / `ENGINE_FILES` upstream, run `refresh()`, and assert
two things — the file is gone, **and nothing left in that consumer still names
it.** The second half is the one that bites.

**What it would have caught**, exactly:
[todo-2026-09-21-refresh-deletes-a-workflow-another-file-depends-on.md](../todo/todo-2026-09-21-refresh-deletes-a-workflow-another-file-depends-on.md).
`commit-identity.yml` was paused with a header saying its checks *"now run as
steps in `.github/workflows/precedent-check.yml`'s single job"*. Four hours
later a refresh deleted `precedent-check.yml` from all four sets. **Two
commit-scope checks now run nowhere and nothing reported it.** The premise was
true when written and false the same afternoon.

## 2. The reverse-dependency sweep, before anything propagates

**Add to:** pass 1, immediately after item 1.
**Mechanical**, with a read of what it prints.

[tools/precedent_decommission.py](../tools/precedent_decommission.py) already
refuses to retire a file that other files still name — **within one
repository.** Deletion propagates across repositories; the dependency check
does not travel with it. So: for every path the current upstream would delete
on the next refresh, grep **every repository in force** for its name, and
report each hit as a blocker rather than a note.

The 2026-09-20 sweep that deleted nine live checks across nine repositories,
and the refresh above, are the same failure at two scales: **a deletion
decided in one tree, executed in many, and verified in none.**

## 3. A carry-through roll-up over every repository in force

**Add to:** the order of operations, as a new step beside the freshness gate.
**Mechanical.**
[tools/precedent_engine_freshness.py](../tools/precedent_engine_freshness.py)
already exists and already does the per-repository half.

One table, printed before the passes begin: **per repository in force, how far
behind the pinned upstream it is, how many engine files changed since, and how
many it has never received** (`--files` already marks those
`(NOT YET VENDORED HERE)`). A repository that is current gets one green row and
costs nothing.

**The boundary matters and should be stated in the practice**: the *fleet*
version of this — every Precedent repository Morgan owns — belongs to
[chief-of-staff](../practices/chief-of-staff.md), which took the fleet branch
sweep on 2026-09-21 for exactly this reason. What belongs here is **the
repositories this run already has open**, which is the same scoping rule the
branch sweep now follows.

## 4. Ask every shipped artifact class whether a DELETION propagates

**Add to:** pass 2, as a new question beside "Are there two of anything that
should be one?"
**A read**, one table, ten minutes.

The engine path diffs the manifest, so dropping a name from `ENGINE_FILES`
deletes it everywhere. **The CI path did not until 2026-09-21** — it was driven
entirely by a hand-maintained tombstone dictionary, so a template dropped
without a tombstone entry **stayed installed in every repository forever,
tracked by nothing.** Two paths, same shape, opposite behaviour, and the
asymmetry survived because nobody ever asked the question of both at once.

So ask it of **every** class this repository ships: engine files, CI workflow
templates, hooks, `settings.json` entries, skeleton files, practice files, the
vocabulary, the materialized catalogue. For each: **does an addition reach an
installed repository? a change? a deletion?** Three columns. Any cell that
reads "only if somebody remembers to write a tombstone" is a finding.

---

# B. The facts only GitHub holds

## 5. The workflow reality check

**Add to:** pass 2, beside item 18 (which reads workflow *files*).
**Mechanical**, one API call per repository plus one per workflow.

For every tracked `.github/workflows/*.yml` in every repository in force, ask
GitHub four questions:

1. **Is it registered at all?** A workflow absent from `list_workflows` while
   present in the tree is one GitHub's parser refused. **This does not show up
   as a failing run. It shows up as nothing**, which reads identically to a
   branch with no CI.
2. **Is its state active?** Disabled-by-inactivity and
   disabled-manually are real states that look like nothing in the tree.
3. **When did it last run, and does that run postdate the file's last
   commit?** A workflow last edited eight days ago whose newest run is from
   three weeks ago is either never triggering or never parsing.
4. **Did anything run at all within seconds of the last push?** This is the
   behavioural test from
   [gotcha-2026-09-21-actions-permissions-are-unreadable-from-a-session](../gotchas/gotcha-2026-09-21-actions-permissions-are-unreadable-from-a-session.md),
   and it must be **labelled as inference**: it cannot separate "Actions is
   disabled" from "the trigger never matched." Both are worth surfacing; only
   one is a bug.

**What it would have caught:**
[gotcha-2026-09-21-github-actions-rejects-yaml-anchors-python-accepts](../gotchas/gotcha-2026-09-21-github-actions-rejects-yaml-anchors-python-accepts.md).
A YAML Ain't Markup Language (YAML) anchor in a `paths:` filter parses cleanly
under PyYAML — the exact command this repository's own templates and PR bodies
recommend — and **GitHub rejects the file outright.** Every local verification
this project teaches would pass it. The only thing that can tell you is GitHub,
and nothing in the check asks GitHub anything about workflows.

## 6. Required status checks, read against the jobs that actually exist

**Add to:** pass 2, beside the `CONTRIBUTOR BOUNDARY` section.
**Mechanical**, reusing the branch-protection call the boundary audit
already makes.

`boundary_audit()` reads branch protection and asks whether it is **on**.
Nothing reads **what it requires.** A required check naming a job that was
renamed, folded into another workflow, or retired is a **permanent, silent
block on every pull request** — and the CI-minutes work of the last two weeks
renamed and folded jobs across every repository in force. The check is one set
difference: required contexts, against the job names the tracked workflows
actually define.

## 7. The Actions bill, beside the API bill

**Add to:** the closing section, beside
[github-api-budget](../practices/github-api-budget.md).
**Mechanical.**

The run already reads its own API bill and the account's. **It reads nothing
about the bill that has actually been hurting**, which is Actions minutes.
Per repository in force: runs in the window, per workflow, billed at GitHub's
one-minute-per-job floor, against real runtime.

[spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) item 15 measured **a 13-second
job billed as a minute, 14 times a day, in one repository: about 420 minutes a
month with nothing misconfigured.** That number was found by a session doing a
one-off audit. **A number found once is a number that goes stale**; this is the
check that exists to re-measure things nobody re-measures. Two derived rows are
worth printing outright: **jobs per pull request** (the only lever that moved
the bill) and **floor waste** — billed minutes minus real runtime.

---

# C. Identity, read off what landed

## 8. Read the commits, not the configuration

**Add to:** pass 2, extending question 13 ("What does a session inherit that a
person configured by hand?").
**Mechanical**, plus a short read.

Question 13 asks what a session *inherits*. **Nothing asks what actually
landed.** Four sub-checks, per repository in force:

- **Author and committer of every commit in the window**, against the declared
  identity. *(Found once already, and only as an aside: commit identity unset
  in four clones, commits landing under the wrong author.)*
- **Author-date offsets** against `identity.json`'s declared timezone — the
  field that decides whether the commit hook enforces an offset or guesses one.
- **Every tracked `settings.json`** in every repository in force, for
  `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` in an `env` block.
  `no-hardcoded-git-identity` checks this in a repository that runs
  [`precedent_check.py`](../tools/precedent_check.py); **the repository where it was actually found was a
  consumer, reported by hand, by a session that happened to look**
  ([gotcha-2026-09-17-a-consumers-settingsjson-hardcoded-git-identity](../gotchas/gotcha-2026-09-17-a-consumers-settingsjson-hardcoded-git-identity.md)).
- **The resolution ladder, rehearsed per harness adapter.**
  `commit-identity.sh` is a Claude Code hook; codex, gemini-cli and grok-build
  reach the same state by a script somebody runs by hand, or they do not reach
  it. Pass 1's adapter-parity item reads the ledger's *rows*; this reads the
  *outcome* — what identity does a commit from each harness actually carry.

**Why identity earns its own block rather than a bullet**: three separate
incidents in six days
([2026-09-16](../gotchas/gotcha-2026-09-16-a-repo-cannot-need-its-own-commit-identity-github-verified-commi.md),
[2026-09-17](../gotchas/gotcha-2026-09-17-a-consumers-settingsjson-hardcoded-git-identity.md),
and the 2026-09-21 watermark-author fix), and one of them burned **a full
design document — rungs, precedence rules, a risk analysis — for a mechanism
no real requirement asked for**, because the premise was never measured.

---

# D. Accretion: the files nobody reads whole

## 9. The holistic-read registry

**Add to:** pass 3, generalizing the 2026-09-21 instructions-file close read.
**Mechanical ranking, expensive read.** This is the biggest proposal here.

**The mechanism:** a `record/holistic-reads.json` registry — path, date read,
who read it, what the read changed. The tool ranks every tracked file by
**commits since its last recorded read** (a file never read counts from its
first commit) and hands the top slice to the run. **Registry, not prose**
([registry-source-of-truth](../practices/registry-source-of-truth.md)), for the
same reason the component ledger is a registry: a claim about what was read
last month is exactly the claim memory gets wrong.

**The read itself** is the one already written for instructions files, asked of
code as well as prose: *does this still describe something that exists; is it
still needed; is it saying it the long way; is it duplicating something that
now lives elsewhere.* **A pass that finds nothing to cut in a file this size
has not read it** — the practice's own sentence, and it applies to a
26,000-line test harness at least as well as to a 555-line instructions file.

**One file per run, not the top ten.** The point is that the count never
reaches zero and the registry is what makes that visible. A slice of one,
recorded, beats a sweep of ten that nobody finishes.

**The first four candidates the ranking produces today** are in the table at
the top of this document. The fourth is
[practices/very-deep-check.md](../practices/very-deep-check.md) itself — 2,167
lines, 75 commits in 30 days, grown one bullet per incident for three weeks,
and **the reason this document exists is that Morgan read it and thought it
was thinner than its length suggests.** That is the finding the registry is
designed to produce, arrived at by hand.

## 10. Configuration keys that nothing reads, and defaults nothing declares

**Add to:** pass 2, beside the duplicate-implementation question.
**Mechanical**, both directions.

Enumerate every key in every `precedent.json` and `identity.json` in force;
enumerate every key the engine actually reads. Report both differences:

- **A key present in a config file and read by nothing** — inert configuration
  that somebody believes is live.
- **A key the engine reads that no repository declares** — a silent default
  nobody chose, which is
  [constants-are-risk-inputs](../practices/constants-are-risk-inputs.md)'s
  whole subject.

**What it would have caught:** [CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) item
15's correction. The plan told a session to set `ci_workflows: disabled` in a
consuming repository's `precedent.json` and then delete a workflow.
**`ci_preference()` resolves that key from an individual or team source's
`identity.json`, never from a consumer's `precedent.json`** — the key would
have been read by nothing, and the deletion would have carried a commit message
claiming a toggle authorized it. A session read the engine and refused. **The
next one might not.**

---

# E. The loop that makes each run deepen the next

## 11. Run the whole planted-case set, once

**Add to:** the order of operations, step 2.
**Mechanical. One word.**

The push gate runs a **10% rotation** of [`verify_harness.py`](../tools/verify_harness.py)'s planted cases
per commit, deliberately, so that pushes stay cheap; full coverage is promised
"within 10 commits." **The very deep check is the obvious place to collect on
that promise, and it does not** — step 2 runs the same rotated suite every
other gate runs. Change the step to `python3 tools/verify_harness.py --all`.
The flag already exists. **A rotation nobody ever forces to completion is a
coverage claim with no settlement date.**

## 12. The incident-to-detector read

**Add to:** pass 2, as its closing item.
**A read**, twenty minutes, and the item most likely to deepen the check on its
own from here.

Take every gotcha filed and every open item closed **since the last recorded
run** — the component ledger already carries the dates — and ask of each one
question: **what mechanism now prevents a recurrence, and is there a planted
case proving it fires?** Three honest answers: a named check with a planted
case; a named check with no planted case (file one); **nothing, deliberately,
because the class is not mechanically detectable** — which is a finding worth
writing down rather than a gap to hide.

**This is the item that answers Morgan's actual request.** The check currently
grows when somebody notices a gap and asks for a bullet. **This makes growth a
standing step**: every incident of the week gets asked whether the system
learned anything, once, in the one place that reads the whole system.

## 13. Sweep the class, never the instance

**Add to:** pass 2, beside item 12.
**Mechanical where a detector exists**, a read where one does not.

[fix-the-original](../practices/fix-the-original.md) requires fixing the origin
and every copy. **Nothing checks that the sweep actually happened.** For each
fix landed in the window that came with a detector, run that detector across
**every repository in force** — not the repository where the bug was found.

**What it would have caught:** the hardcoded-identity check was built the day
the trap was reported, in this repository, and the repository that actually had
the problem was a consumer nobody re-scanned. A check written in response to an
incident and never run where the incident happened is the most expensive kind
of clean result.

## 14. Premise-dated claims: "this now runs in X"

**Add to:** pass 3, as a specific case of "Documents against the mechanisms
they describe."
**Mechanical enough to be worth automating**: grep for the sentence shape,
resolve the target.

A file that says **"these checks now run in X"**, "folded into X", "superseded
by X", "see X instead" is making a claim about a *different* file, and the
general bullet only ever catches it if a session happens to read that file.
**Re-resolve every one of them**: does X exist, and does X still do the thing?

**What it would have caught:** the paused `commit-identity.yml`, whose own
header named `precedent-check.yml` as the destination of its folded checks,
**four hours before a refresh deleted that destination.** One grep, run at any
point in the following month, would have found it. Nothing ran one, because
nothing was looking for that sentence shape.

---

# What I would do first

Ranked by finding-per-hour, not by how interesting they are:

1. **#11 (`--all`)** — one word, and it converts a promise into a settlement.
   Do it regardless of everything else here.
2. **#5 (the workflow reality check)** — the largest genuinely invisible class,
   and mechanical. A workflow that never parses is currently undetectable by
   anything this project owns.
3. **#1 and #2 (deletion rehearsal, reverse-dependency sweep)** — the pair that
   covers last week's most expensive incident, and the class Morgan named
   directly.
4. **#12 (incident-to-detector)** — the one that makes the check grow itself,
   which is the request behind the request.
5. **#9 (the holistic-read registry)** — the highest ceiling and the highest
   cost. Worth starting at one file per run.

**Everything else is real and can wait.**

## Two honest cautions

**This check is 2,167 lines and adding fourteen bullets makes it worse.**
Nine of these belong in
[tools/very_deep_check.py](../tools/very_deep_check.py) as sections that print
a table, with **one line each** in the practice pointing at them — the shape
the branch sweep, the session load read and the orphan scan already use. Only
the reads (#4, #9, #12, #14) genuinely need prose. **If all fourteen land as
prose bullets, the next person to read this practice will be reading it for
the reason Morgan read it this week.**

**A section that is added and never fires is a cost, not a safety net.** The
component ledger exists precisely to ask that question of every section after
the fact, and **no section has ever yet been retired on its evidence.** Each
proposal above should enter the ledger like any other, and each should be
allowed to leave.

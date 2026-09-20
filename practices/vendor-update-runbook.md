---
slug:        vendor-update-runbook
title:       Taking an upstream update into a vendored tree
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Update Vendors\", or an upstream update is being taken into a repo that vendors a practice layer"
gates:       ["merge"]
index_clause: "\"Update Vendors\" -- source clone first, both layers move separately, then merge"
checked_by:  null
defines:     ["Update Vendors"]
command:     {"Update Vendors": "Pull in the latest version of the shared rules from the project they come from, and publish the result -- the merge is part of the phrase."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan; amended 2026-09-14, Morgan -- the phrase now carries
  the merge as well as the update"
---
## Rule
**"Update Vendors" is the phrase that asks for this**, and it authorizes the
whole sequence below without asking again -- the same standing-phrase
mechanism as [go-merge](go-merge.md), for the other operation a person
otherwise has to spell out every time. **It carries the merge too**: when the
sequence below is done, run [go-merge](go-merge.md)'s chain on what it
produced -- say the target branch out loud, commit, push, open the pull
request, merge -- without going back for a second authorization. That is step
10, and it is part of the phrase rather than a separate grant.

**This does not lift the gate the chain already runs through**, and it does
not add one. `Go merge` publishes by the repository's usual conventions, and
those are what decide whether a push may happen at all -- here, the full check
that gates every push. Step 6 below IS that check, and it sits before the
merge for that reason: a red check stops this merge exactly as it stops any
other. What the phrase removes is the second question, not the gate. So a
failing check is reported, with what failed, and nothing is published -- that
is the sequence working, not a refusal needing permission to stand.

A vendored tree is updated by a fixed sequence, in this order, because
every step's answer is wrong if the one before it was skipped.

1. **Make the SOURCE clone current first, against the branch this repo is
   pinned to** — not the source's default branch. A stale source makes
   every later step confidently wrong: the diff is against the wrong
   lineage, and "already up to date" is the answer you get.

   **You do not have to name that branch, and you must not check it out.**
   The pin is compiled into the vendored tool as `SOURCE_BRANCH` in
   [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py),
   and `refresh` fetches it and reads `tools/` out of it **by blob** —
   `git show <commit>:tools/<file>` — so the clone's own `HEAD`, branch and
   working tree are never touched. A fresh clone satisfies this step; so
   does an existing clone, because the fetch is the tool's first move.

   **So do not preface this sequence with a `git switch` onto the pinned
   branch.** In a consuming repo that branch does not exist at all — the pin
   names a branch of the SOURCE, not of the repo being updated — and in a
   clone of the source it reintroduces exactly the behaviour that was taken
   out of the tool on purpose: the old code ran `git checkout` plus
   `git pull` in the clone, which moved a person off whatever branch they
   were on, and in CI moved the job's own workspace so that every later step
   silently ran against the pinned branch instead of the commit under test,
   with `git status` clean throughout. That cost several sessions on pull
   request #110, and `_source_tools_at`'s docstring carries the finding.
   Asked by Morgan, 2026-09-14 — *"Maybe it should even preface that command
   with `git switch precedent-beta-v01`"* — and answered no, for this reason.
2. **Read every vendored layer separately.** A repo usually vendors more
   than one — the loader *engine* and the practice *catalogue* are
   different trees with different manifests, and **they move
   independently**. Checking one and reporting "current" is the common
   failure.
3. **Refresh the engine, and take the branch tip.** Expect two passes when
   the tool replaces itself; the second is not a retry, it is the new copy
   running its own corrected file list.
   **Since 2026-09-15 this also refreshes `.claude/hooks/*.sh`**, drift-checked
   and tracked in the same `ENGINE_MANIFEST.json` as `tools/`
   (`hook_files`/`hooks_sha256`) — before that date the hook scripts were
   copied once at initial install and never refreshed again, so a fix
   landing in one (the `freshness-guard.sh` shallow-clone false-positive,
   `record/GOTCHAS.md#g12`, is the incident that prompted this) never
   reached an already-vendored repo no matter how many times "Update
   Vendors" ran. A repo vendored before this date has no `hook_files` in
   its manifest yet; its first refresh after taking this change prints a
   one-time catch-up notice and vendors all of them, even though the
   `tools/` commit may already match. `.claude/settings.json` is still never
   touched — only the hook scripts it calls are vendored engine code, and a
   consumer's own hook wiring is its own.
   **Since 2026-09-18 this also refreshes the installed CI workflow file(s)**
   vendored from `templates/github-actions/*.template` — a dependent repo's
   `.github/workflows/bestpractice-docs.yml` (from `doc-lint.yml.template`),
   a practice set's `.github/workflows/views-drift.yml` and
   `precedent-check.yml` (from their own templates) — drift-checked and
   tracked the same way, in the same `ENGINE_MANIFEST.json`
   (`ci_workflow_files`/`ci_workflows_sha256`). Before this date these files
   were written once, at initial install, and never refreshed: a template fix
   landing after install — the `concurrency:` block `doc-lint.yml.template`
   gained on 2026-09-15, then
   [spec/CI_MINUTES_PLAN.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CI_MINUTES_PLAN.md)'s
   Phase C debounce-guard step the very next day — reached an already-installed
   `bestpractice-docs.yml` only if that repo happened to reinstall from
   scratch. A repo vendored before this date has no `ci_workflows_sha256` in
   its manifest yet; its first refresh after taking this change records a
   baseline hash for whichever of these files it has installed and prints a
   one-time catch-up notice — but, **unlike the hooks catch-up above, does
   NOT rewrite the file's content on that first run.** A CI workflow is
   exactly the kind of file a real repo hand-tunes (an extra job, a changed
   schedule, a repo-specific secret), so overwriting an unrecorded one the
   first time this shipped would have discarded that with no warning. Run
   `refresh` again once the baseline is recorded to pick up template changes
   normally from then on.
   **Since 2026-09-19, check whether this refresh newly vendors
   `tools/todo_migrate.py` or `tools/build_todo_index.py`** — the one-time
   per-item TODO migration tool and its ongoing index generator
   ([spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
   Part 4.2). Vendoring the tool is not the same as running it, and nothing
   else says so: this repo shipped both to every consumer on 2026-09-15/16
   and, once source sets turned out to need them too, to every source set
   on 2026-09-19 — and confirmed the same day that most consumers had
   never run it, three or more days after it arrived. If `TODO.md` is
   still the old single-file format (no `todo/` directory, no `# TODO has
   moved` stub heading), run `python3 tools/todo_migrate.py --apply` then
   `python3 tools/build_todo_index.py` as part of this refresh, not as a
   follow-up. Step 6's full check also catches this —
   [todo-migrate-available-but-unused](todo-migrate-available-but-unused.md)
   — but the fix belongs here, at the refresh that brought the tool in,
   not deferred to whoever next happens to run the check.
   **When the same update is going into more than one repo, note the tip
   before you start and check every repo against it at the end.** Each refresh
   resolves the tip at the moment it runs, so two repos updated an hour apart
   can land a commit apart with nobody having done anything wrong — a
   four-set rollout on 2026-09-14 ended exactly that way.
   **Close that gap by rolling the laggard FORWARD, never by holding the
   others back.** Level matters less than current: a repo pinned to an
   ancestor is missing whatever landed after it, and in that rollout the one
   set left behind was missing the reply gate the other three already had.
   Holding the others back would have made all four miss it and removed the
   very difference that made anyone look.
   `--from-ref <commit>` is for the two cases where an exact commit is the
   point — vendoring a commit whose diff you actually reviewed, and
   reproducing a bug against an older engine — never for making a rollout
   tidy.
4. **Take the catalogue update by the documented route.** Under a branch
   pin this is the manual mirror, never a tool that resolves the remote's
   *default* branch — that mirrors the wrong lineage over a pinned tree,
   which is a wholesale revert wearing an update's clothes.
5. **Regenerate the generated views in the same change.** A refreshed
   generator whose output has not been re-run leaves the repo's committed
   views describing the old engine, and its own `--check` then fails on
   work that is otherwise correct. The bump and its output land together.
6. **Run this repo's own full check**, not the upstream's.
7. **Check that this environment can still reach its PRIVATE sources**,
   before you call the update done. A vendor update is when a new engine
   file arrives that the environment may not be configured for, and it is
   the one moment somebody is looking at how this repo gets its practices
   at all. Run
   [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py);
   `MISSING` means a source is absent and no credential is set, so the
   session is running on the universal catalogue alone and nothing else
   will say so.
8. **Check that every source repository is still CALLED what this repo
   calls it** — *in a repo that declares sources.* A renamed repository
   redirects indefinitely, so the clone, the fetch and the materialize all
   keep succeeding under the old name and nothing anywhere fails. This is
   the one moment a session is already online and already reconciling its
   sources, so it is where the question gets asked. Run
   [tools/precedent_source_names.py](../tools/precedent_source_names.py);
   `UNVERIFIED` means the name was not checked, which is not the same as
   checked and current.

   **In a practice SET this step is not applicable, and that is different
   from skipped.** The tool reads a multi-source config a set does not
   have, so it is in `CONSUMER_ENGINE_FILES` only and is deliberately not
   vendored into a set at all — a session following this runbook there
   finds no such file. Say "not applicable: this repo declares no sources"
   and move on. Do not go looking for the file, and do not report a step
   you could not run as one you skipped. Step 7 above is **not** in this
   position and still applies everywhere: `precedent_source_credentials.py`
   is in the shared `ENGINE_FILES`, because a session rooted in a practice
   set needs the person's own individual set exactly as much as a consumer
   does.
   **Read both tools' answers as answers about THIS repo, and check that
   they are.** Until 2026-09-14 they were not, on the commonest consuming
   layout of all: an engine vendored at `process/upstream/tools/` defaulted
   its root to the vendored tree, which carries a `precedent.json` of its
   own, so step 7 named three declared team sources as missing at paths
   nothing had ever written to, and step 8 left the same three
   `UNVERIFIED`. Both readings were specific enough to be believed and both
   were about the wrong repository. Fixed at the root rather than in the
   runbook — `consuming_repo_root()` in
   [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py)
   — so these steps need no `--repo` and no caveat. **If either step names a
   path inside `process/`, the engine copy you are running predates that
   fix: pass `--repo .` and take the answer from that run.**

9. **Ask the person whether a source should be ADDED or DROPPED.** Steps 7
   and 8 both ask about the sources this repo already declares — can they
   be reached, are they still called that. Neither can ask the question
   underneath: *should this repo be declaring something it isn't?* **A set
   that was never declared is invisible.** It produces no `MISSING`, no
   `UNVERIFIED`, no error and no absent file — only a repo quietly
   resolving fewer practices than its owner believes, and no check will
   ever report it, because **the sets a repo COULD declare are not
   derivable from the sets it does.**

   So this one is answered by a person, not a tool, and an update is when
   to ask: somebody is already looking at how this repo gets its practices.
   Name what it declares now and ask outright. Do not infer it from the
   tree, and do not skip the question because nothing looks wrong — nothing
   looking wrong is the symptom, not the all-clear.

   Measured, 2026-09-09, across five repositories that each looked healthy:
   one had no session-start instruction at all, so nothing ever fetched the
   sources its config named; one had never declared `visibility`, and an
   absent field counts as public, which silently excluded every
   private-level source from its generated views; and three named their
   sources in hand-written prose that went stale the day a team set was
   split by subject. **Not one produced a failing check.**

   **Once the answer changes what this repo declares, grep before moving
   on.** Run `grep -n '<name>' AGENTS.md CLAUDE.md` for every source name
   now declared, one name at a time. A hit outside a dated Story, gotcha,
   or incident write-up is a standing enumeration of the declared sources
   sitting in hand-authored prose — the same staleness risk this whole step
   exists to catch, one level down. Reword it to describe the set
   dynamically (a count, or a pointer to `precedent.json`) rather than
   naming it.

10. **Sweep this repo's own `.github/workflows/` against the retired-file
    table** ([spec/MIGRATING_EXISTING_INSTALLS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/MIGRATING_EXISTING_INSTALLS.md)'s
    step 6, added 2026-09-16) — an ordinary update touches the same
    workflow files a migration would, and a repo that migrated before this
    table existed has never had the chance to apply it. **As of
    2026-09-20, this step's own table only still matters for two cases**:
    a file the manifest never tracked a hash for at all (the pre-2026-09-14
    legacy names — `light-check.yml`, `bestpractice-upstream-sync.yml`, and
    the rest — [spec/CI_WORKFLOW_RETIREMENT_PLAN.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CI_WORKFLOW_RETIREMENT_PLAN.md)
    has the full list), and a `RETIRED_CI_WORKFLOW_FILES` entry that has
    been hand-edited since the manifest last recorded it. A tracked,
    untouched retired entry (currently just `views-drift.yml`) is now
    deleted automatically by the `refresh` step above — nothing left to
    sweep there. **Never match by filename alone before touching anything
    on this list** — a name that looks retired can be a live, distinct,
    repo-specific check that only coincidentally shares it (found
    2026-09-20 in a real repo: `light-check.yml` running `tools/
    light_check.py`, that repo's own required light check, not a leftover
    copy of BestPractice's retired install template of the same name).
    Diff what the file actually runs against its supposed replacement
    before deleting or recommending deletion of anything on this table.
    Per file, never a blanket delete: the table names what each one is, and
    which are a confirm-before-delete rather than an automatic one. While
    here, check
    `ci_workflows` and `ci_debounce_minutes`
    ([GITHUB_ACTIONS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/documentation/GITHUB_ACTIONS.md))
    are set the way the person actually wants, not just inherited from
    whatever an earlier install or migration left.
11. **Verify by content on the remote**, never by ref equality
   ([verify-postcondition](verify-postcondition.md)).
12. **Publish it, without asking again.** Run [go-merge](go-merge.md)'s
    chain on the result and report which branch it landed on. The phrase
    authorizes this step; do not stop at step 9 and ask. Every condition
    `Go merge` carries still holds -- a branch the repository restricts is
    still restricted, and a step this session cannot reach hands off rather
    than coming back as a question.

**A refusal naming a file that no longer exists upstream means reseed, not
investigate.** The refresh runs *this repo's own vendored copy* of the
vendoring tool, which carries the file list it was vendored with — so the
first refresh after upstream renames or drops an engine file asks for a
path that is genuinely gone.

## Detail
**Step 1 is first because it is the one nobody thinks of as part of the
update.** The instinct is to start with the command that does the
vendoring. Every failure mode below step 1 is silent — no error, just an
answer computed against the wrong tree.

**On what "up to date" means for the source clone.** Fetch the pinned
branch by name. A clone can be current on its default branch and many
commits behind the branch that actually matters, and a shallow clone will
report divergence that does not exist — deepen before believing any
comparison.

**Never hand-edit a vendored file to resolve a merge.** The vendored tree
is not this repo's to change: restore it to what the manifest records and
re-run the refresh. A hand-edit is detected as drift and refused, and
`--force` is the wrong answer to that refusal — it discards the guard
rather than the edit.

## Why
An update is not one operation, it is a small pipeline where each stage
consumes the last stage's output. Run out of order it does not fail, it
produces a confident, wrong result — and a vendored tree that is silently
wrong is worse than one that is obviously stale, because nothing will
prompt anyone to look again.

## Story
**The phrase was chosen 2026-09-08**, by Morgan, in the same conversation
that moved `go-merge` and `park-it` up to universal: *"Let's use the phrase
'Update Vendors' to trigger vendor-update-runbook."* It is plural on
purpose -- a repo usually vendors more than one layer, and the step people
skip is the second one.

**Amended 2026-09-14, on Morgan's instruction**, to carry the merge:
*"Also Update the definition of \"update vendors\" to include invoking go
merge."* The sentence it replaced had said the opposite in as many words --
that the phrase authorized the update and never the merge of what the update
produced. **Strength:** decided (2026-09-14, Morgan)

The original split was defensible and cost a step every time: an update that
stops at a verified, unpushed tree is a job half-finished, and the person who
typed one phrase to avoid being asked a question got asked one anyway, at the
end, about work that was already done and already checked. **What the split
was protecting is still protected, by the thing that was actually doing it:**
step 6's full check, which runs before anything is published and is what a
`Go merge` here would have run into regardless. Removing the sentence removes
a second authorization, not a gate.

**Asked for by Morgan, 2026-09-08**, after watching a session do this from
memory across four repositories: *"maybe we define another phrase ... with
the general instructions on how to update the vendored in files? (Starting
with make sure your local copy of your main repo is up to date etc)."*

Every step here is a failure somebody already paid for. A consumer went
**167 commits behind** with the practice meant to catch it never firing,
because a branch pin had disabled both of its delivery paths for the same
honest-looking reason and neither knew about the other. A different repo
was told "up to date" by a check that only ever compared generated files
against declared sources — a real check, answering a different question
than the one being asked of it. A sync tool that resolved the remote's
default branch would have mirrored `main` over a beta-pinned tree. And on
the day this practice was written, three practice sets could not refresh at
all: upstream had renamed an engine file, and each set's own vendored copy
of the vendoring tool still asked for the old path.

**Step 8 is a failure that never failed.** A team source was renamed on
GitHub, and a consuming repo went on declaring, cloning, attaching and
materializing under the old name with every check green, for an unknown
number of sessions -- because GitHub redirects a renamed repository
indefinitely. It surfaced on 2026-09-11 only because a person recognised a
name he had retired. The content was right the whole time; the name was a
ghost, and every vendored reference to it was one repository-settings change
away from a 404 nobody could date.

**Step 8 then sent three sessions hunting for a file that was never there.**
Written with no caveat, it named `tools/precedent_source_names.py` as
something to run, and that file is in `CONSUMER_ENGINE_FILES` only -- by a
deliberate decision recorded in `precedent_vendor_engine.py`'s own comment,
because it reads a multi-source config a practice SET does not have. So in a
set the step is unrunnable by design, and on 2026-09-13 three sessions
following this runbook in one hit it: each was left choosing between
reporting a step it had skipped and searching for a missing engine file,
and a missing file reads like a broken vendoring, which is the expensive
direction to guess. The scoping clause is the whole fix. **A runbook step
that names a tool has to say where that tool exists**, because the session
reading it has no other way to tell "not for this repo" from "your install
is broken" -- the two look identical from a shell.

**The phrase this began as is deliberately not here.** A keyword is one
person's preference, and a universal rule telling every adopting repository
to go invent a keyword of its own is exactly what got
`merge-authorization-keyword` retired on 2026-09-07. The procedure is
universal; the word that triggers it belongs in an individual set.

## Install
Before starting, name the layers this repo vendors and where each records
its provenance — usually a manifest per layer. If you cannot name them, you
cannot tell whether the update is complete, and step 2 is the step that
most often gets skipped.

Then run the sequence above, and report which layers moved and which did
not. "Updated" without naming the layers is the report that hides half a
job.

**Step 8 is the one nobody can discover from a failure**, because there is
never a failure to discover it from. Only the GitHub API answers it: it
carries the repository's current `full_name` in the response body, so a name
that has moved shows up as a mismatch against what this repo declares. Every
git operation follows the redirect silently and reports success.

Step 7 runs itself: [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
prints the same line after a `refresh` or a `status`, so an update made
without reading this file still surfaces a source nobody can reach
(practice: checkable-gets-checked). Asked for by Morgan, 2026-09-09, in the
thread that found a whole session running with no team or individual
practices in force and no error anywhere.

---
slug:        vendor-update-runbook
title:       Taking an upstream update into a vendored tree
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a message says \"Update Vendors\", or an upstream update is taken into a vendoring repo"
gates:       ["merge"]
index_clause: "source clone first, both layers move separately, then merge"
checked_by:  null
defines:     ["Update Vendors"]
command:     {"Update Vendors": "Pull in the latest version of the shared rules from the project they come from, and publish the result -- the merge is part of the phrase."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan; amended 2026-09-14, Morgan -- the phrase now carries
  the merge as well as the update; amended 2026-09-21, Morgan (decided) --
  step 1 makes the clone current rather than telling somebody to; amended
  2026-09-23, Morgan (assented) -- a classic install is migrated, not
  updated; amended 2026-09-24, Morgan (decided) -- every update retires
  the old install's leftovers (step 10)"
---
## Rule
**"Update Vendors" is the phrase that asks for this**, and it authorizes the
whole sequence below without asking again -- the same standing-phrase
mechanism as [go-merge](go-merge.md), for the other operation a person
otherwise has to spell out every time. **It carries the merge too**: when the
sequence below is done, run [go-merge](go-merge.md)'s chain on what it
produced -- say the target branch out loud, commit, push, open the pull
request, merge -- without going back for a second authorization. That is step
12, and it is part of the phrase rather than a separate grant.

**This does not lift the gate the chain already runs through**, and it does
not add one. `Go update` publishes by the repository's usual conventions, and
those are what decide whether a push may happen at all. Step 6 below is the
full check, and it sits before the merge for that reason: a red check stops this merge exactly as it stops any
other. What the phrase removes is the second question, not the gate. So a
failing check is reported, with what failed, and nothing is published -- that
is the sequence working, not a refusal needing permission to stand.

**Every conflicted file is reviewed, never overwritten on sight.** An
update meets this repo's own changes in many places: a refusal to overwrite
a hand-edited file, a drift report, a merge conflict, a hand-written rule in
`AGENTS.md` or `CLAUDE.md` that an updated practice now touches. Each one
gets the same two questions before anything is resolved: **does the local
version conflict with what upstream now ships, and is it still needed?**

- **It says what upstream now says**: take upstream. The local copy is a
  duplicate, and a duplicate is the copy that goes stale.
- **It conflicts**: ask the person whether the difference is deliberate.
  If it is, keep it and record it where this repo's tools will see it next
  time (below). If not, take upstream; the rule in force wins.
- **It doesn't conflict and is still needed**, because it covers something
  upstream doesn't: keep it, and carry it into the new version rather than
  choosing one side wholesale.

**`--force`, `record-ci` and "take theirs" come after this review, never
instead of it**; each one discards the local side in a single step. A
difference kept on purpose is recorded so the next update does not ask
again: a `diverged` or `declined` entry in `process/manifest.json`, a
declared file under `local_ci_workflows` in `precedent.json`, a repo-local
practice with `overrides:`, or a hand-written rule worded as an exception
to the practice it departs from. **The pull request lists every conflicted
file with its verdict** — kept, taken from upstream, or merged — and why.
Morgan, 2026-09-24: *"Every 'update vendors' should use that rule for every
conflicted file"* ([current-rule-governs](current-rule-governs.md) says
which side wins when the review finds a real conflict).

**Follow the upstream copy of this runbook, not the one vendored here.**
The copy in this repo is from the last sync, and every correction made to
the procedure since then is exactly what it lacks. Once step 1 has made the
source clone current, read `practices/vendor-update-runbook.md` in that
clone, on the branch this repo takes its updates from, and follow that
([current-rule-governs](current-rule-governs.md)). Incident, 2026-09-24: a
consumer followed its own old copy of these steps and missed a change to
them that had already been published.

A vendored tree is updated by a fixed sequence, in this order, because
every step's answer is wrong if the one before it was skipped.

**First, is this repo running the loader at all?** A classic install —
`process/upstream/` vendored, no universal source in `precedent.json`, no
generated block in `AGENTS.md` — is not updated, it is migrated, in the
same change:
[spec/MIGRATING_EXISTING_INSTALLS.md](https://github.com/alex137/BestPractice/blob/staging/spec/MIGRATING_EXISTING_INSTALLS.md).
`practice_audit.py`, `checkin.py update` and the session-start bootstrap all
say so when it is. An update that leaves the repo classic has refreshed text
that no session reads, which is how a consumer took one on 2026-09-23 and
still had nothing in force.

**The same goes for a repo that runs the loader but has no
`tools/ENGINE_MANIFEST.json`** — its engine sits only under
`process/upstream/tools/`, because the migration stopped before its step 7.
`refresh` cannot run there, so nothing in step 3 reaches it. Step 10(e) says
what to do; `practice_audit.py` fails on it (check 8) and `checkin.py update`
says so, both from the vendored tree under `process/upstream/`.

1. **Make the SOURCE clone current first, against the branch this repo is
   pinned to** — not the source's default branch. A stale source makes
   every later step confidently wrong: the diff is against the wrong
   lineage, and "already up to date" is the answer you get.

   **For BestPractice that branch is `main`, for every install**, since
   2026-09-25 -- the branch that has passed every local check and the
   GitHub test (Morgan, 2026-09-25, `strength: decided`: *"Yes, switch all
   installs to main. ... Let's do it, go ahead, go update"*). An install
   whose `process/manifest.json` records `"branch": "staging"` -- or
   `precedent-beta-v01`, staging's name until that morning -- is repointed
   to `main` in this same update, and so is its `tools/ENGINE_MANIFEST.json`
   (the refresh writes that one itself). The consequence to know: a change
   reaches your other repositories only once it is on BestPractice's main,
   which takes staging by a pull request, and a major one needs Alex's
   named go-ahead. For one day before that, 2026-09-24, installs had been
   split between `main` and `precedent-beta-v01` on an approval Morgan
   later called assent rather than a decision; this move was made for
   every install at once so that cannot happen again.

   **The two vendored layers do not both need this, and knowing which is
   which is the whole point of the step.** The ENGINE is read by blob out of
   a freshly fetched commit (see the pin note below), so the clone's checkout
   is irrelevant to it. The CATALOGUE is read from the clone's WORKING TREE —
   [tools/precedent_materialize.py](../tools/precedent_materialize.py) has no
   fetch call in it at all — so for that half, whatever is checked out *is*
   the input. Step 1 is not hygiene; it is the correctness argument for
   step 2.

   **It is done, then checked — an instruction alone was proven not to
   work.** `precedent_refresh_sources.py --apply` now brings each clone to
   its declared `base_branch` as its first action, verifies the working tree
   actually arrived there, and **refuses to report success when it could
   not**: a skipped source is named, and the run exits non-zero. Before
   2026-09-21 it printed `applied.` and exited 0 however many sources it had
   declined, and four of them drifted 17 to 34 commits behind while every
   session start reported success
   ([todo-2026-09-21-refresh-output-blocks-the-next-pull](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-21-refresh-output-blocks-the-next-pull.md)).

   **Two things it deliberately does not do.** It never touches a modified
   file the clone's own `ENGINE_MANIFEST.json` does not list — the engine may
   discard its own output, never a person's edit — and it never repairs a
   clone carrying unpushed commits of its own. Both are reported and left
   alone: rebasing somebody's work to get a vendoring tool unstuck is the
   trade that made this loop in the first place.

   Morgan, 2026-09-21 (strength: decided): *"would this force it to clone the
   most updated version first thing? I think that's what we need."* A check
   that merely refused on a stale clone was the first proposal, and the
   measurement retired it — it would have fired on all four sources every
   session for weeks and changed nothing, because nothing in the sequence was
   ever going to make them current.

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
   `tools/` commit may already match. **One time is the point: a second
   refresh at the same commit prints "nothing to do".** Until 2026-09-25 a
   hook a declared source's adapters own (`commit-identity.sh`,
   `freshness-guard.sh` from an individual source) was skipped, never
   recorded, and still counted as missing, so the notice repeated on every
   refresh and every engine file was rewritten; seeing it twice in a row now
   is a bug to report. `.claude/settings.json` is still never
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
   [spec/CI_MINUTES_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/CI_MINUTES_PLAN.md)'s
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
   **Since 2026-09-24 it also refreshes any file the repo declares under
   `engine_paths` in its own `precedent.json`** — an upstream path mapped to
   a local one, for a file the repo must keep at a path of its own:
   `{"templates/harness/claude-code/hooks/commit-identity.sh":
   "bootstrap/commit-identity.sh"}` is precedent-individual's, which
   `session-start.sh` and that set's own `adapters` both reach by that path.
   Tracked in `ENGINE_MANIFEST.json` (`engine_paths`/`engine_paths_sha256`)
   and drift-checked like `tools/`. **A newly declared file is adopted only
   if it is already identical to upstream**; otherwise the refresh refuses,
   names how many lines differ, and `--force` does not waive it — move the
   difference upstream first. A mapping onto a path an adapter writes, or
   one this engine already vendors, is refused outright.
   **Since 2026-09-25 it also refreshes a consumer's `tools/bootstrap.sh`
   — but only while it carries no local edits.** Unedited means it matches
   the baseline hash `ENGINE_MANIFEST.json` records for it
   (`template_instances_sha256`), or, where nothing is recorded yet, it is
   byte-identical to some past version of upstream `templates/bootstrap.sh`.
   Either way it is rewritten to the current template. A copy with local
   edits is never rewritten, `--force` included: the refresh reports it
   `DIVERGED`, names each template block it lacks by line, and puts it on
   the **Left for you** list for step 10(d). Before this date nothing
   delivered a template change to an installed copy; a real consumer ran
   two days without the session-start freshness check for exactly that
   reason.
   **Since 2026-09-25 it also refreshes the sections `AGENTS.md` took from
   its template, on the same terms, one section at a time.** A section is a
   `##` or `###` heading and what follows it; the generated loader block is
   not one, and stays the sync's (step 5). An unedited section — matching
   the hash recorded under `agents_md_sections_sha256`, or with nothing
   recorded, identical to that section in some past version of the
   template — is rewritten to the current template. An edited one is never
   rewritten, `--force` included: it is reported `DIVERGED` with each
   bullet, paragraph or table row of the template's section it lacks, down
   to the missing sentences, and goes on **Left for you**. A section the
   template has and the file does not is reported `MISSING` once, and never
   written in. Before this date whatever the template wrote at install was
   frozen: a template fix reached no installed repo, and nothing said so.
   The same run lists every line of `AGENTS.md`, `CLAUDE.md` and
   `tools/bootstrap.sh` that still names a **retired branch**
   (`precedent-beta-v01`, renamed `staging` on 2026-09-25), outside the
   generated block. Nothing else outside `tools/`, `.claude/hooks/`, the CI
   workflows, `tools/bootstrap.sh` and those `AGENTS.md` sections is
   touched.
   **Since 2026-09-19, check whether this refresh newly vendors
   `tools/todo_migrate.py` or `tools/build_todo_index.py`** — the one-time
   per-item TODO migration tool and its ongoing index generator
   ([spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
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

   **`checkin.py record`'s carry check reads the COMMITTED tree on the
   remote, not your working tree**, so restoring a file locally after a
   `record` and re-running changes nothing it sees: it lists
   `origin/<branch>` with `git ls-tree` and reads each file back with
   `git show origin/<branch>:<path>`. The "restore it and re-record" move is
   not a way around `--accept-loss`; it only works once the restore is
   itself committed and pushed. Reported from a dependent repo that hit it
   twice in one hop, 2026-09-21, and verified here against the tool's own
   git calls rather than taken on the report.

   **A line upstream deleted itself is never counted as lost**, since
   2026-09-26. Under the branch tiers your base branch takes the update by
   Promote, later, so its committed tree is often one sync behind the
   manifest; the check used to read every line upstream removed in between
   as dropped local work (301 of them on one consumer, none real). It now
   compares that tree against every upstream commit it could have come
   from, and sets aside what upstream's own history deleted, saying how
   many. **A `LOST` line it prints is a line upstream never had**: carry it
   or pass `--accept-loss` knowingly -- never hand-write `upstream.commit`
   to step around it
   ([gotcha](../gotchas/gotcha-2026-09-26-the-carry-check-counted-upstream-s-own-deletions-as-lost.md)).

   **Then decide every earlier decline again, in this same change.** Any
   upstream practice this repo once declined or deferred ("a duplicate of
   our own rule", "not now") was declined as its text stood *then*. For each
   one, read the current upstream file and decide again: adopt it, or keep
   declining it with a reason that fits the current text. A decline that
   lives only in prose (a sync note, a paragraph in `AGENTS.md`) goes into
   the manifest as a `declined` entry
   ([INSTALL.md §5](https://github.com/alex137/BestPractice/blob/staging/INSTALL.md#5-the-manifest-schema-processmanifestjson)),
   so the next sync does not depend on somebody remembering it. Any other
   hand-written rule an updated practice now touches gets the
   conflicted-file review at the top of this runbook.
   `checkin.py update` lists the declines this update has moved past, and
   `practice_audit.py` fails on them at step 6 until each is decided again
   ([current-rule-governs](current-rule-governs.md)). Incident, 2026-09-24:
   a dependent repo declined upstream's merge-keyword practice as a
   duplicate of a personal rule. Upstream replaced it with a broader one,
   two later syncs carried the old decline forward without reading it, and
   a session refused a command the rule in force authorized.
5. **Regenerate the generated views in the same change.** A refreshed
   generator whose output has not been re-run leaves the repo's committed
   views describing the old engine, and its own `--check` then fails on
   work that is otherwise correct. The bump and its output land together.
6. **Run this repo's own full check**, not the upstream's:
   `python3 tools/precedent_push_check.py --tier full`. **Run it by hand;
   the push gate will not.** Under the branch tiers a push to a working
   branch or to pre-staging gets only the basic check, so the full one first
   runs at the merge, and a finding there refuses the merge after
   everything else is done. On 2026-09-25 a vendor update's regenerated
   AGENTS.md went out with its version header unbumped, and the merge gate
   was the first thing to notice.
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

10. **Retire legacy leftovers — on every update, not only after a
    migration.** Whatever the old, pre-Precedent install left behind goes in
    this update: Morgan, 2026-09-24 (strength: decided), *"this needs to be
    deleted from ALL installs, the migration to the new precedent should
    [have] deleted this."* This step is how that reaches every install
    without anyone remembering a sweep. Do all of it:

    **(a) Read the end of step 3's refresh output.** The refresh already
    deleted what it could recognise: a leftover workflow whose CONTENT has
    the old install's shape (`bestpractice-upstream-sync.yml`,
    `bestpractice-docs.yml`, `views-drift.yml`), tracked or not, hand-paused
    or not; a retired hook nothing calls; and `ci_debounce_minutes` in
    `precedent.json` or `identity.json`. Each deletion is staged and
    recorded in `process/decommissioned_paths.json`. What it would not do is
    under **Left for you** at the very end.

    **(b) Work that list, item by item.** Read each kept file, hook or
    field. Then either delete it with
    `python3 tools/precedent_decommission.py PATH --reason "..." --apply`,
    or record why it stays: a CI workflow under `local_ci_workflows` in
    `precedent.json` with its reason, anything else in the pull request.
    **Never by name alone.** `light-check.yml` is a live check in most
    installs and is not a leftover; the 2026-09-20 sweep deleted nine live
    checks by trusting names
    ([spec/CI_MINUTES_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/CI_MINUTES_PLAN.md)
    item 14). A live one is paused first and decommissioned a cycle later,
    as [tools/precedent_decommission.py](../tools/precedent_decommission.py)
    requires.

    **(c) Fix stale source paths.** Each source in `precedent.json` whose
    path is not its current name gets both corrected — the practice sets
    were renamed `precedent-team-*` → `precedent-shared-*`. The refresh
    lists each one. GitHub redirects the old name, so nothing fails: the
    repo just clones the same set twice, or not at all. Run step 8's tool
    afterwards.

    **(d) Bring diverged template-written text up to the template:
    `tools/bootstrap.sh`, `AGENTS.md`'s sections, and retired branch
    names.** For `tools/bootstrap.sh`: the
    refresh already rewrote an unedited copy (step 3). One it reported
    `DIVERGED` has local edits, and the output lists each block of upstream
    `templates/bootstrap.sh` it lacks, as `templates/bootstrap.sh:LINE
    "heading" -- missing` or `-- N of its M lines absent or changed`. Copy
    each listed block in from the template, **keeping every line this repo
    added**, then re-run step 3's refresh: it should report the file as
    carrying every block. Never replace the whole file to get there, and
    never reach for `--force`, which does not touch it anyway.

    **For each `AGENTS.md` section reported `DIVERGED`**, the output names
    the template line of each block the section lacks, and under a block it
    has only part of, each sentence it lacks. Read each against what the
    section already says. Where the repo says the same thing in its own
    words, leave it — the report compares text, not meaning, so a local
    rewrite of a template sentence always lists that sentence. Where it
    does not, copy the template's text in, fill its `<placeholders>` with
    this repo's real names, and keep every line the repo added. A section
    reported `MISSING`: copy it in where it belongs if it applies here, or
    leave it out and say so in the reply — the next refresh notes it in one
    line and stops listing it. **Each retired branch name** the run lists:
    change it to the new name on that line, unless the line records the
    rename on purpose, in which case name the new branch on the same line
    and the report stops listing it. Upstream keeps the old name working as
    an alias until no refresh reports one, so this is not an emergency, and
    it is how the alias gets to retire. The run never lists a line inside
    the generated block, because the sync rewrites it. If one still names a
    retired branch after step 5's regeneration, the text came from a practice, and
    `precedent_check.py --only retired-branch-name-ships`, run in the set
    that publishes it, names the practice to fix there.

    **In the same file, remove a hardcoded git identity.** A literal
    `git config user.name` or `user.email` in `tools/bootstrap.sh` or
    `.claude/settings.json` names a person in a shared template; the
    refresh lists each one under **Left for you**. Delete just those lines,
    keeping the rest of the file. `commit-identity.sh` resolves who
    is committing. **A fallback branch is not an exception.** One that
    names a person "only when the individual source has not resolved yet"
    was tested 2026-09-25 on a scratch consumer with no individual source:
    `commit-identity.sh` already set the right author from
    `PRECEDENT_COMMIT_*` or the authenticated GitHub account; with neither,
    its backstop refused the bot-authored commit rather than letting it
    through; and with a second person's identity declared, the fallback
    overwrote it with the named one.

    **(e) Finish an unfinished migration.** No `tools/ENGINE_MANIFEST.json`
    means (a) could not run at all. Say so out loud, confirm with the person
    that this update will finish the migration — it is bigger than an
    update — then do
    [spec/MIGRATING_EXISTING_INSTALLS.md](https://github.com/alex137/BestPractice/blob/staging/spec/MIGRATING_EXISTING_INSTALLS.md)
    from step 7 on, which seeds the engine at `tools/`. Then run step 3's
    refresh and continue from (a). If the person says not now, stop before
    publishing: step 6 fails until it is done.

    **(f) File the secrets only the person can delete.** List every
    repository secret no remaining workflow reads. The refresh names the
    ones it can see: what a deleted workflow read (the Claude keys, once the
    upstream sync is gone) and `PERSONAL_PACK_TOKEN`. Write **one** `todo/`
    item for the person listing them all, with `disposition: ask` and
    `remind_on` set to today, and where to delete them (Settings → Secrets
    and variables → Actions). A session cannot delete a secret; never say it
    did.

    **(g) Get the person's approval for every workflow file that stays.**
    Run `python3 tools/precedent_check.py --only ci-workflow-approved`.
    Every file it names bills at least a minute per run in a private repo,
    and nobody has approved it as it stands. For each one, show the person
    what it runs and **when it triggers**, in one line, and ask. Record the
    answer in `precedent.json`'s `github_ci_approved`, pinned to the file's
    sha256 and quoting their words, or delete the file. **Never approve one
    on the person's behalf**, and never "fix" a trigger to make it pass
    without asking
    ([ci-workflow-approved](ci-workflow-approved.md), Morgan, 2026-09-25:
    "In the migration and updates, can we put a check explicitly for
    this?"). Until every file passes, step 6 fails and so does every push.

    **The update only changes the branch it lands on**, so a side branch
    keeps whatever workflow files it had. That matters only for an active
    one: a branch runs a workflow when it is pushed, and a stale branch
    nobody pushes runs nothing. Run `python3 tools/ci_fleet_audit.py --repo
    OWNER/NAME` for this repo. It reads only side branches with a commit in
    the last 7 days and names any whose workflow would run on its next
    push. For each one, say whether the branch holds anything unmerged, and
    hand the person its one-click link to delete it
    ([never-delete-a-remote-branch](never-delete-a-remote-branch.md)).

    **(h) Give the repo all three branches.** Run
    `python3 tools/precedent_branches.py --ensure-tiers`. It says whether
    origin has `pre-staging` and a `staging` branch of its own; if either is
    missing, run it again with `--apply`, which creates them and, in a repo
    whose staging tier was `main`, writes `"staging_branch": "staging"` into
    `precedent.json` for this update to commit. `base_branch` stays as it
    is, because it also pins where a practice source's session clone sits.
    From then on work lands on pre-staging, Promote moves it to staging,
    and main takes staging by pull request. Morgan, 2026-09-25: *"make sure
    that all repos with precedent vendored-in have staging and pre-staging
    branches? That should be part of the migration!"*

    **(i) Report all of it in the reply**: what the refresh deleted, what
    you deleted, what stays and why, each workflow's approval, the branches
    step (h) created, and the todo item.

    While here, check `github_ci_workflows` (formerly `ci_workflows`)
    ([GITHUB_ACTIONS.md](https://github.com/alex137/BestPractice/blob/staging/documentation/GITHUB_ACTIONS.md))
    is set the way the person actually wants, not just inherited from
    whatever an earlier install or migration left.
11. **Verify by content on the remote**, never by ref equality
   ([verify-postcondition](verify-postcondition.md)).
12. **Publish it, without asking again.** Run [go-merge](go-merge.md)'s
    chain on the result and report which branch it landed on. The phrase
    authorizes this step; do not stop after step 11 and ask. Every condition
    `Go update` carries still holds -- a branch the repository restricts is
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
`Go update` here would have run into regardless. Removing the sentence removes
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

**Step 10 used to be a sweep a person ran by hand, and it never ran.**
Until 2026-09-24 it pointed at a table in the migration document and said
which leftovers still mattered; every install that migrated before the table
existed was expected to come back and apply it. Measured that day in six
installs: `bestpractice-docs.yml`, retired three days earlier, was still in
all five that had it, and `bestpractice-upstream-sync.yml` in four. The
removers only deleted what a manifest had recorded, and the oldest installs
had recorded nothing. The table's own first row also kept the upstream sync
on purpose, "so a person can still run it by hand", after the hold that
reason served had ended on 2026-09-14. Morgan reversed that the same day and
asked for the cleanup to run on every update instead. The refresh now
recognises the old files by content, and this step makes the session finish
what the code will not.

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

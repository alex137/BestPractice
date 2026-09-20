---
slug:              todo-2026-09-14-team-sets-carry-no-engine-refresh-workflow
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="team-sets-carry-no-engine-refresh-workflow"></a>**The weekly
  engine-refresh cron is dead in all four practice sets. What survives it is
  the finding underneath: a set's vendored engine goes stale, and nothing
  unattended says so.**
  **Disposition:** wait (2026-09-14 — the cron kill has landed; what is left
  is refreshing the sets by hand, which is now the only channel there is)

  **THE LIVE FINDING, re-measured 2026-09-14 in this session.** All four sets
  vendor `74eb776277105b70fa504470de1dc3c521b0fd33` while this branch's tip is
  `d23714b48a36`, so all four are behind — the same shape as the morning
  measurement below, which caught the three team sets at `a114836` and the
  individual set further back still. **The drift is not the problem; the
  noticing is.** The three team sets carry `precedent-check.yml` and
  `views-drift.yml` and neither looks at `ENGINE_MANIFEST.json`, and since the
  cron kill the fourth has no scheduled channel either. Nothing reports this
  on its own, and after 2026-09-14 nothing is supposed to.

  **THE REMEDY IS BY HAND, and it is not a gap waiting on a workflow.**
  `Update Vendors` ([vendor-update-runbook](../practices/vendor-update-runbook.md))
  is the channel: [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
  `refresh` per set, landed in the same pass. What reports the drift is a session that has the sources
  attached — [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  prints a behind/current line per source at session start, and printed
  exactly the four STALE rows above at the start of this one. That is
  attended reporting, which is what Morgan chose over a clock; **do not read
  anything below as a standing argument for restoring one.**

  **CLOSED 2026-09-14 — THE SCHEDULED CHANNEL IS RETIRED, NOT EXTENDED.**
  Read this first: everything below it was written toward rolling the weekly
  job out to three more repositories, and that is no longer the plan.
  Morgan, 2026-09-14, in his own words: *"I think that engine-refresh.yml is
  now doing an automatic update weekly. Let's stop that. No weekly updates. I
  had that weeks ago, but we're not doing that anymore; this is now really
  complex and deserves hand attention and issues come up every time and I'm on
  it every day anyway."* **Strength:** decided (2026-09-14, Morgan) — he asked
  for it outright rather than accepting a proposal
  ([decision-strength](../practices/decision-strength.md)).

  **What that settles, item by item.** Decision 1 below (*install it in the
  three team sets*) is **withdrawn** — no set gets a weekly cron, so the gap
  this item opened on is no longer a gap. The `WORKFLOW_TEMPLATES` fork below
  (*put it in the templates, leave it, or ship it behind an opt-in flag*) is
  **closed with no change**: a mechanism nobody is going to run does not need
  a distribution question. The superseded-pull-request fix below is **moot**
  by the same route — the pull-request path it was fixing goes away with the
  schedule. Decisions 2, 3 and 4 were already withdrawn and stay that way.
  Nothing here reopens 2026-09-06's reasoning; it ends one repository's
  exception to it.

  **The 2026-09-06 reasoning survives intact and is now universal in
  practice.** That decision said a scheduled workflow inherited by every
  adopter is a cron job phoning a remote weekly on a schedule nobody picked,
  and kept it out of
  [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)'s
  `WORKFLOW_TEMPLATES` for that reason — recorded in
  [spec/BOOTSTRAP_NEW_SOURCES.md](../spec/BOOTSTRAP_NEW_SOURCES.md)'s "The
  scheduled channel, and why there is not one". The individual set was
  the one place that took the cron anyway, on the ground that it was the
  owner's own preference about his own repositories. He has now withdrawn that
  preference, so the exception closes and nothing anywhere schedules a vendor
  update.

  **What replaces it: the phrase, by hand.** `Update Vendors` is the channel —
  [vendor-update-runbook](../practices/vendor-update-runbook.md), which since
  2026-09-14 carries the merge as well as the update, so the thing a scheduled
  job was bad at (landing: **two runs, two abandoned branches**, a 100% report
  rate against a 0% landing rate, all measured below) is the half the phrase
  actually does. The evidence in this item was always pointing here: the
  channel never leaked at the reporting step.

  **DONE 2026-09-14 — the kill landed, and both halves landed together.**
  `.github/workflows/engine-refresh.yml` and the practice requiring it,
  `practice-set-engine-refresh`, both live in the private practice sets;
  neither file is in this repository. A session rooted in the individual set
  removed the `schedule:` block, kept `workflow_dispatch` as the only trigger,
  and revised the practice in the same pull request rather than leaving the
  set failing a rule that still demanded a weekly job. Verified from here
  against that set's `origin/main` rather than a local clone
  ([verify-postcondition](../practices/verify-postcondition.md)); the workflow's
  own header now records the cron's dates and why it went.

  **Why it had to go to a session rooted there**, kept because it is the
  standing constraint and not a one-off: measured, not assumed,
  `git push --dry-run` to that set came back *"access denied by the git
  proxy"*, and `add_repo` with push access was refused by this session's own
  permission layer.

  **THE SCOPE IS FOUR REPOSITORIES, NOT ONE — corrected 2026-09-14 by Morgan**
  (*"I think we need to remove it from the 4 practice level repos"*), against
  the paragraph above, which named `precedent-individual` as the sole carrier.
  That was true when this item was written and the decision recorded below
  changed it: decision 1 approved putting the workflow INTO the three team
  sets, so if any session acted on that approval before he reversed it, the
  cron now exists in all four. **Unverified from here and deliberately left
  that way** — no session rooted in this repository can read
  `themorgan/precedent-team-*` at all, so "are they carrying it?" is a
  question only a session holding those sets can answer, and guessing at it
  is what [diagnosis-is-measured](../practices/diagnosis-is-measured.md) exists
  to stop. The removal is idempotent either way: a set without the file needs
  nothing done to it.

  **Owned, as of 2026-09-14, by the one session holding all four sets:**
  `session_01Cp6E5dkxdjqej9C6YDUjZU` ("Engine-refresh cron removal"). Recorded
  here rather than left in a chat thread
  ([findings-return-through-repo](../practices/findings-return-through-repo.md)),
  because the next session to read this item will otherwise start a fifth
  branch on the same four files.

  **NOW MEASURED, AND THE CRON QUESTION IS CLOSED — 2026-09-14, later the
  same day.** The paragraph above left the four-repository scope deliberately
  unverified; the session-start hook then cloned all four sets into this
  container, so it became answerable from here and was answered by looking
  rather than by reasoning.

  - **The three team sets never carried the workflow.**
    `precedent-team-repo-maintenance`, `precedent-team-writing` and
    `precedent-team-working-style` each hold exactly `precedent-check.yml` and
    `views-drift.yml` in `.github/workflows/`, and nothing else. So decision 1
    below — install it in the three team sets — was approved and never acted
    on, which is the only reading that fits. `precedent-individual` really was
    the sole carrier, and the four-repository scope was a precaution rather
    than a finding.
  - **`precedent-individual`'s cron is dead.** Its pull request #129 (*"kill
    the engine-refresh cron, and revise the rule with it"*) is on that set's
    `main`, and the workflow there now reads `on: workflow_dispatch:` with the
    comment *"the only trigger. Nothing here fires on a clock."* The practice
    that required the weekly job was revised in the same change. Verified on
    `origin/main` by content, not by a report
    ([verify-postcondition](../practices/verify-postcondition.md)).

  **What remains of this item is one line in one file**, and it is the
  `relayed_authorization` change below, not the cron.

  **A duplicate branch this session caused, named so nobody re-derives it:**
  `claude/quirky-pasteur-e997ei` in `precedent-individual` carries a second,
  unmerged retirement of the same cron, superseded by #129. It exists because
  a session woke a `precedent-individual`-only window on this subject while a
  window holding all four sets was already on it — `list_sessions` had been
  run, and the four-set session was created after that enumeration and before
  the wake. **Enumerating once is not enough when the work is queued rather
  than immediate**; the check has to be close to the wake.

  **A SEPARATE ONE-LINE CHANGE IN `precedent-individual`, same day, same
  wall:** `identity.json` has no `relayed_authorization` field, so
  [relayed-authorization](../practices/relayed-authorization.md) reads `refused`
  and every cross-repository handoff costs Morgan a second approval in a
  second window. He asked for `accepted` on 2026-09-14 (*"yes that should be
  in both precedent-individual as well as the template"*). **Strength:**
  decided. The template half is already done — `relayed_authorization` ships
  in [templates/practice-set-individual/identity.json.template](../templates/practice-set-individual/identity.json.template)
  set to `refused`, with the trade written out, so an adopter chooses it
  rather than inheriting it. Only his own set's value is outstanding.

  **Found 2026-09-14**, checking the laggards at the end of an `Update
  Vendors` run in a consuming repo, which
  [vendor-update-runbook](../practices/vendor-update-runbook.md)'s step 3
  requires: note the tip before starting, check every repo against it at the
  end, and roll the laggard forward. The consumer went to `9d15675`.
  `precedent-team-writing`, `precedent-team-working-style` and
  `precedent-team-repo-maintenance` all vendor `a114836`, one commit behind.
  `precedent-individual` vendors `03f4e1e`, further behind still.

  **The gap is the workflow, not the commit.** One commit of drift is
  nothing; a set with no way to notice drift is the thing worth recording.
  `practice-set-engine-refresh` — an individual practice, unlinked on purpose,
  since a private set's contents do not belong in a public tree — says a practice-set
  repo of Morgan's carries `.github/workflows/engine-refresh.yml`, a weekly
  job that refreshes the engine and opens a pull request only if that produced
  a diff. Its occasion is *"creating a practice-set repo of mine, **or finding
  its vendored engine stale**"*, which is exactly this. All three team sets
  carry `precedent-check.yml` and `views-drift.yml` and neither of those looks
  at `ENGINE_MANIFEST.json`. `precedent-individual` is the only one of the four
  that has the workflow, and is also the most stale — which says something
  about the workflow's health worth checking before copying it anywhere.

  **Each set has a `precedent/engine-refresh` branch, and it is not evidence
  of a scheduled job.** It is a working branch from a manual refresh. This
  session read it as the workflow and said so in a pull request body before
  checking `.github/workflows/`; that is the specific mistake worth not
  repeating, because the branch name is exactly what a scheduled job's branch
  would be called. (It said "already merged" as well, and **that half is
  false** — see the 2026-09-14 correction below, where all four turned out to
  be unmerged.)

  **Not done here, and the reason is scope rather than difficulty:** the work
  is four `precedent_vendor_engine.py refresh` runs — **no workflow is copied
  anywhere**, per the reversal below — but this session's designated
  repositories were one consuming project and this one, and a request to
  attach a set with push access was refused.
  Recorded so the
  finding survives the window that found it
  ([findings-return-through-repo](../practices/findings-return-through-repo.md)).

  **MEASURED 2026-09-14, and it answers this item's own doubt: the workflow is
  healthy.** The suspicion above — that the only carrier being the most stale
  might mean the job was failing or disabled — is false, checked against
  `precedent-individual`'s own history rather than inferred. Its cron is
  Mondays, and it fired on Monday 2026-09-07 (`aec5ed5`, pushing
  `precedent/engine-refresh-c6c885033a9f`) and again on Monday 2026-09-14
  (`982dfcf`, pushing `precedent/engine-refresh-7c8904d2ec47`), producing a
  correct refresh both times. All four sets vendor `74eb776` as of this
  writing, so the staleness figures above are the state on the morning they
  were taken, not now.

  **What it was stale from is the LANDING, not the job — and the scheduled
  channel has never once been landed.** Both workflow branches are unmerged,
  by `git merge-base --is-ancestor`: `-c6c885033a9f` from 2026-09-07, which
  [spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md) already names an unlanded
  attempt, and `-7c8904d2ec47` from 2026-09-14. **Two runs, two abandoned
  branches.** Every refresh that actually reached that set's `main` was landed
  by a person or a session instead — `b80210c` (2026-09-10) reproduces the
  workflow's tree by hand and says so in its own message, and `1eb647e`
  (2026-09-14, this set's pull request #128) is a session's `Update Vendors`
  run. So the job's report rate is 100% and its landing rate is 0%, which is
  the same failure this practice's own Detail predicts for the ISSUE fallback
  — a channel that reports into a place nobody acts on becomes litter and gets
  muted — arriving through the pull-request channel instead.

  **How to tell the two apart, since authorship no longer does it.** Since the
  2026-09-10 identity fix the workflow commits as the declared identity, so
  `git log --format=%an` cannot separate a scheduled run from a session. What
  separates them is the BODY: the workflow's `git commit -m` is a single line
  with no trailer, and every session-produced refresh carries a
  `Claude-Session:` or `Session:` trailer and a written rationale. The branch
  name is the second signal — the workflow appends the upstream commit
  (`precedent/engine-refresh-<12 hex>`) and
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  does not (bare `precedent/engine-refresh`).

  **Six unmerged refresh branches across the four sets, counted 2026-09-14.**
  The two workflow ones above, plus a bare `precedent/engine-refresh` in every
  one of the four — all four at `27655a18bc50`, all committed within three
  seconds of each other at 06:24 -03, so one session's sweep — and none of
  them merged. The refresh gets produced reliably and landed almost never.
  **That was read at the time as an argument for giving the other three sets
  the same channel. It is not, and the reversal below settles it the other
  way:** the leak is at the landing step, which is precisely the half an
  unattended job is worst at — a weekly job leaves up to seven days of drift
  on its own, and a weekly job nobody lands leaves all of it. What six
  abandoned branches actually argue for is refreshing by hand and landing it
  in the same pass, which is what `Update Vendors` does.

  **The cron time does not match either run, and this is not explained.** The
  installed workflow says `17 6 * * 1` (06:17 UTC); both runs committed near
  12:30 UTC on their Mondays. Whether that is GitHub delaying a scheduled job,
  a `workflow_dispatch`, or a cron that was different at the time has not been
  checked — recorded as an open thread rather than guessed at.

  **How this item got it wrong the first time, 2026-09-14** (practice:
  [diagnosis-is-measured](../practices/diagnosis-is-measured.md)): the paragraphs
  above originally credited the 09-14 run to `1eb647e` and reported one
  unlanded branch rather than two. The cause was reading a local clone's
  remote-tracking refs as if they were the remote — `git branch -a` and
  `git log --all` without a `git fetch` first, in a clone that was several
  hours stale. Two of the four branches simply were not there to be found, and
  nothing about the output said so. Morgan noticed the missing branch by name.
  **Fetch before you enumerate refs**, in any clone you did not just make.

  **Why the three team sets never got it, established rather than assumed:**
  three causes, none of them a decision anybody made about these
  repositories.
  [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
  installs workflows from an explicit two-entry `WORKFLOW_TEMPLATES` list and
  this one is deliberately not in it; that exclusion was a 2026-09-06 call
  about what a STRANGER's repository inherits, recorded in
  [spec/BOOTSTRAP_NEW_SOURCES.md](../spec/BOOTSTRAP_NEW_SOURCES.md)'s "The
  scheduled channel, and why there is not one"; and
  `precedent-team-repo-maintenance` predates the workflow outright (founded
  2026-08-31 against the workflow's 2026-09-06) while the other two were
  founded 2026-09-09 and bootstrapped from that same list. Sessions edited all
  three sets' `.github/workflows/` on 2026-09-11, 09-12 and 09-13 without
  adding it — which is what an exclusion nobody ever restated looks like from
  the inside.

  **No upstream template is needed, and adding one would re-open a settled
  question.** The 2026-09-06 decision made the individual set the canonical
  home for this workflow on purpose, and the spec section above already
  records its full shape in prose for anyone rebuilding it. A team set copies
  the file from the individual set, which IS the original — so
  [fix-the-original](../practices/fix-the-original.md) is satisfied without a
  `templates/github-actions/` entry that would put the mechanism back in the
  one place 2026-09-06 decided it should not live.

  **What was left to decide was one word, and it is Morgan's:** whether a
  `precedent-team-*` set counts as "a practice-set repo of mine" under the
  individual practice that requires this workflow. If it does, that practice
  wants one word widened and three repositories are out of compliance with a
  rule approved 2026-09-06. If it does not, the team level needs a rule of its
  own. The mechanism is right either way; only its level is open.

  **DECIDED 2026-09-14 — the workflow goes into the three team sets.** Morgan
  approved a four-part recommendation as written, so
  **strength: assented (2026-09-14, Morgan)** on all four: the substance was
  the session's proposal and he took it rather than choosing between options
  he framed himself ([decision-strength](../practices/decision-strength.md)).

  1. **Install it in the three team sets — yes.** On the ground that the
     workflow is proven healthy above, not on an assumption that it is.
  2. **Daily instead of weekly — NO, withdrawn.** Weekly fires correctly; the
     leak is at the landing step, and a faster cron only produces more pull
     requests nobody lands.
  3. **Auto-merge on green — NO, withdrawn.** It would reverse a decision
     recorded and approved 2026-09-06 (*the workflow never merges; landing it
     is his call*), and the session proposed it without noticing that, on a
     reason that turned out to be wrong: the 2026-09-06 incident was NO
     CHANNEL AT ALL, not an unlanded pull request. The two abandoned branches
     above are a real argument for revisiting it, and a different one — his to
     open, not a session's to slip in.
  4. **A `templates/github-actions/` entry — NO, withdrawn**, for the reason
     in the paragraph above it.

  **The individual set needs nothing: it already has the workflow.** Asked and
  answered rather than assumed — it is the one set of the four that has
  carried `.github/workflows/engine-refresh.yml` since 2026-09-06, and the two
  scheduled runs measured above are its own.

  **STILL OPEN, and it cuts against decision 4 above:** Morgan asked, in the
  same message that approved that withdrawal, whether the workflow should go
  into the templates *"so they go into future ones"*. Those cannot both hold,
  so decision 4 stands as approved and this is recorded as the live fork
  rather than resolved by reading his question as an instruction. **Three ways
  out, and the third is the session's recommendation:** put it in
  `WORKFLOW_TEMPLATES` (every adopter inherits a weekly cron — the exact thing
  2026-09-06 refused); leave it where it is and copy by hand into each new set
  of his (today's behaviour, and how three sets came to be missing it);
  **or ship the template and gate it behind an opt-in flag on
  [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)**,
  so a set gets it when somebody asks for it and never by inheritance. The
  third keeps 2026-09-06's reasoning intact — nobody inherits a cron they did
  not choose — while ending the hand-copy. It also means publishing a file
  that currently lives only in a private set, which is a
  [scrub-gate](../practices/scrub-gate.md) question and not a formality.

  **A SEPARATE CHANGE, RECOMMENDED 2026-09-14: the workflow should close its
  own superseded pull requests.** Raised by another session and endorsed here
  on the evidence this item already carries. The workflow reuses and closes a
  single staleness ISSUE, and the practice states why in its own Detail — an
  open issue must mean *stale right now* rather than *was stale once*, or the
  channel becomes litter inside a month and gets muted. **Its pull-request
  path has no equivalent.** It checks only whether a pull request is open for
  the branch it is about to push, so every earlier run's pull request stays
  open claiming an engine gap that a later run has already closed. Two
  abandoned branches are the state above; the cost is live as well, in a
  session sitting blocked on *"PR #126 — should delete or keep?"* between two
  refresh pull requests from different runs. **A person arbitrating superseded
  refresh pull requests by hand is the failure the issue path was built to
  prevent, arriving through the other channel.**

  **What the step has to get right**, since "close the old ones" is broader
  than it sounds: close only pull requests **this workflow opened** — branches
  matching `precedent/engine-refresh-<sha>`, never the bare
  `precedent/engine-refresh` that
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  writes from a session — and comment naming the superseder before closing, as
  the issue path already does. Whether the superseded BRANCH is deleted too is
  a smaller question with an easy answer (it is reproducible from upstream at
  any time), but it is a second change, not part of this one.

  **Scope:** `precedent-individual` only — it is the sole carrier — and a
  session rooted there does it, if it is ever wanted. **There is no "which
  version do the team sets get" question to sequence any more**: decision 1 is
  void, the three team sets never carried the workflow, and with no schedule
  nothing stacks superseded pull requests on a clock.

  **REVERSED 2026-09-14, later the same day: Morgan wants the cron killed.**
  In his own words — *"we have a cron that we want to kill"* — so
  **strength: decided (2026-09-14, Morgan)** on killing it. Everything the
  decisions above turn on changes with it:

  - **Decision 1 is VOID.** Installing a scheduled workflow in three
    repositories while removing the schedule from the fourth is incoherent.
    Nothing is to be installed in the team sets, and there is nothing to kill
    there either: measured, none of the three has ever had
    `.github/workflows/engine-refresh.yml`, so they have no scheduled action
    at all.
  - **The template fork is moot in the form it was asked.** *"So they go into
    future ones"* has no content once there is no cron to inherit. If the
    opt-in-flag route is ever wanted it is for a different artefact.
  - **The superseded-pull-request closer recommended above loses its
    urgency.** Its whole case was competing SCHEDULED runs stacking pull
    requests nobody arbitrates. Without a schedule they stop competing, and
    it drops from a fix to a nicety — worth keeping only if the on-demand
    path turns out to stack them too.

  **The shape was a reading when it was written and is his words now.**
  Confirmed 2026-09-14, same day, asked and answered rather than assumed:
  *"I meant to kill the scheduled crons, not workflow dispatch."* So: remove
  the `schedule:` block, keep `workflow_dispatch`, and the job stays available
  on request while never firing on a clock. **Strength: decided (2026-09-14,
  Morgan)** on the shape as well as on the kill. Deleting the workflow
  outright is explicitly NOT what was asked, and a later session should not
  re-derive it as the tidier reading.

  **This is not a one-line YAML edit, and that is the part worth not
  forgetting.** The individual practice `practice-set-engine-refresh` REQUIRES
  the weekly workflow — that is what it says, and it carries a Story about the
  set going two hundred commits stale. Deleting the `schedule:` block without
  retiring or revising that practice leaves the set failing its own rule, with
  nothing to catch it (the practice declares no mechanical check, on purpose).
  Both halves land together or neither does. Both are in
  `precedent-individual`; `git push --dry-run` from here returns 403 from the
  git proxy, re-measured today, so a session rooted there does the work.

  **What killing it costs, said plainly rather than argued away:** the set
  loses its only channel that reports a stale engine without somebody looking,
  which is the exact 2026-09-06 condition the practice was written to end.
  What makes that defensible is this item's own measurement — the unattended
  channel fired twice and landed zero times, while sessions refreshed that set
  three times in the same week. The attended path is the one that works. The
  practice's revision should say that, rather than deleting its Why and
  leaving the reasoning unanswered.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

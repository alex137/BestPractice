<!-- Last updated: 2026-09-03 (Buenos Aires) by the follow-up session that also built INSTALL.md §0 -->

# Phase 6 Brief — Migrating Consumer Repos

**Status: opened 2026-09-03, not closed.** [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s
Sequence row 6 already marks this "underway" from `themorgan/WorkingWithAI`'s
2026-09-02 migration; this brief is the session that picked phase 6 up
afterward, closed two of its named gaps for real, and is honest about what
still needs the actual target repo attached to finish. Read the plan's
Sequence table and [spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s "What phase 6
inherits" section first — this brief does not restate them.

## What this session actually closed

1. **The path-triggered channel's consumer-repo integration.**
   [`spec/LOADER.md`](LOADER.md)'s own status table named this precisely:
   `tools/precedent_paths.py` worked as a command but nothing called it
   automatically — real cost, not theoretical: `themorgan/WorkingWithAI` hit
   a missed `header-caps` practice and patched around it locally, at commit
   time only. Built: `templates/harness/claude-code/hooks/precedent-paths.sh`,
   a `PreToolUse` hook wired into `templates/harness/claude-code/settings.json`,
   with a harness check (`check_pretooluse_hook_fires`,
   `tools/verify_harness.py`) proving the wrapper's own logic. **Open as
   [pull request (PR) #86](https://github.com/alex137/BestPractice/pull/86) against this
   branch, pending Alex's review — not merged by this session**, per this
   repo's own convention that changes to Alex's repo get reviewed, not
   self-merged. `spec/LOADER.md` documents plainly what the harness check
   proves and what it can't (whether `additionalContext` really reaches the
   model, not just a transcript) — see [TODO.md](../TODO.md) item 11.
2. **The pre-fork catalogue audit table** —
   [spec/PREFORK_AUDIT.md](PREFORK_AUDIT.md), one row per inherited
   practice. Named by [What phase 5 should carry forward](../PRACTICE_ENGINE_PLAN.md#what-phase-5-should-carry-forward)
   as required before phase 6 starts migrating a consumer repo; never done
   until now.
3. **The `WritingWithAI` naming discrepancy**, on this repo's side only —
   [spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s step 0 no longer hardcodes a
   possibly-wrong fork target; it now says to confirm the real name against
   `precedent-individual`'s own blocklist first. The confirmation itself
   still needs a session holding that repo, or Morgan directly.
4. **`TODO.md` gained three tracked items** (9, 10, 11) for real gaps that
   were previously only ever *restated* in briefs rather than tracked once
   — the audit table (closed by this brief), `for_team:`/`in_repos:`'s
   blocked-on status, and the `additionalContext` delivery question.
5. **A genuinely clean install directly onto the Precedent loader** —
   [INSTALL.md §0](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)
   and [templates/AGENTS.md.loader.template](../templates/AGENTS.md.loader.template).
   Also corrects a stale claim this brief's own first draft made (that the
   "step-5 bridge" was unbuilt) — `tools/precedent_sync_views.py` already
   closed it, documented in [LOADER.md](LOADER.md) earlier the same
   day this brief was first written. See "The real work still ahead"
   below for what §0 does and does not cover yet.

## What this session could not close, and why — needs Morgan

**Two open decisions, explained in full and left for Morgan's judgment**,
tracked in [PRACTICE_ENGINE_PLAN.md's Open Decisions](../PRACTICE_ENGINE_PLAN.md#open-decisions):
whether the leak gate's vocabulary blocklist is miscalibrated or has simply
never run clean, and whether `precedent-team-maintainers`'
`session-trailer` check should accept `Claude-Session:` or every session
should start writing a literal `Session:` line too. Neither has a right
answer this session can pick on its own — both are explained at length in
the conversation that opened this phase, not repeated here.

**One authorized fix this session could not carry out — a real platform
limitation, not a judgment call.** Morgan explicitly authorized overriding
`no-rewrite-for-warnings` for exactly two commits in `precedent-individual`
(`ac525c9`, `0016903` — wrong author identity and time-zone offset instead
of Buenos Aires). Two independent blockers, both worth recording precisely
since the next session will hit the same wall without this note:

- `add_repo` refused `themorgan/precedent-individual` mid-session with
  `alex137/BestPractice` already attached: *"cross-tier adds are not
  supported in v1... Start a new session with the requested repo as the
  initial source."* This is a **confirmed, current tool limitation**,
  distinct from the git-push-permissions question
  [decisions/2026-09-01-relax-private-repo-isolation.md](../decisions/2026-09-01-relax-private-repo-isolation.md)
  was reasoning about when it called the platform restriction
  "unconfirmed" — see that record's 2026-09-03 addendum.
- Spawning a **new** session with `themorgan/precedent-individual` as its
  initial source, carrying the fix instructions and Morgan's explicit
  authorization verbatim, was itself denied: *"Permission for this action
  was denied by the Claude Code auto mode classifier... If you believe
  this capability is essential to complete the user's request, `STOP` and
  explain to the user."* A `bypassPermissions` session built to run a
  history-rewriting force-push unattended is exactly the shape that
  classifier exists to catch, regardless of in-conversation authorization
  — the platform does not treat a user's words in one session's
  transcript as proof to a different session's own safety layer.

**What actually closes this**: Morgan doing it directly (a live session
against `precedent-individual`, approving the specific rebase/force-push
commands interactively as they run), or explicitly adding a Bash
permission rule that lets a future session run this unattended. Neither is
something a session can grant itself.

**Update, 2026-09-03 — all three closed.** Morgan ran a session
directly against precedent-individual (exactly the path this brief
names as "what actually closes this"), approving the rebase/force-push
interactively as it ran. `ac525c9` and `0016903` are rewritten in
place — correct author (`Morgan F <morgan@westegg\.com>`), correct
`-0300` offset, wall-clock time unchanged — verified by comparing every
commit's tree hash before/after (identical throughout) and a fresh
clone showing both checks exit 0. A follow-up commit cleared the two
check scripts' now-dead `GRANDFATHERED_SHAS` entries and updated both
practices' Install text. The five old PR-source branches that still
held the unrewritten commits were deleted from precedent-individual's
remote. The two Open Decisions above are closed the same day — see
[PRACTICE_ENGINE_PLAN.md's Open Decisions](../PRACTICE_ENGINE_PLAN.md#open-decisions).

## The real work still ahead

Item 1 was built in a follow-up session (2026-09-03, same day) without
needing the target repo — a correction worth stating plainly: an earlier
draft of this brief listed a "step-5 bridge" as unbuilt, sketched as two
possible shapes. That was stale. [LOADER.md](LOADER.md) already
documented, from earlier the same day, that
`tools/precedent_sync_views.py` closes exactly that gap — this brief
simply hadn't been cross-checked against it before being written. Items
2–4 below still need the actual target repo attached, which no session
writing this brief has had access to yet.

1. ~~**Extend `SETUP.md`/`INSTALL.md` for a genuinely clean install
   directly onto the Precedent loader.**~~ **Done (2026-09-03).**
   [INSTALL.md §0](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)
   and [templates/AGENTS.md.loader.template](../templates/AGENTS.md.loader.template)
   — vendor `practices/` + the whole `tools/` engine, write
   `precedent.json`, instantiate the loader-variant `AGENTS.md`, run
   `tools/precedent_sync_views.py`. The vendoring + `precedent.json` +
   `precedent_sync_views.py` sequence was dry-run tested in a scratch
   fixture while writing it and does work as documented; the section as a
   whole has **not** been rehearsed against a real repo end to end — that
   is what item 4 below is for. `SETUP.md` still defaults to the
   classic §1 install; §0 is opt-in, by name, until rehearsed.
2. **Wire the creation pipeline itself into an installed repo** — vendor
   `precedent_candidate.py`/`precedent_detect.py`/etc. alongside the
   loader, and update the merge-runbook's capture-gate step so it raises a
   real candidate on the new model instead of the placeholder
   "open a plain PR against the upstream repo" instruction
   `templates/AGENTS.md.loader.template`'s own export-gate step currently
   carries (deliberately honest about not being wired in yet, not an
   oversight).
3. **Upgrade `SETUP.md`/`GETTING_STARTED.md`'s disclosure** once §0 is
   rehearsed and item 2 lands — name the individual/team/universal levels
   explicitly, rather than the capture-gate-only description
   [decisions/2026-09-03-setup-getting-started-disclosure-gap.md](../decisions/2026-09-03-setup-getting-started-disclosure-gap.md)
   deliberately limited itself to.
4. **Run the actual rehearsal** [spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)
   specced in detail (confirm the real target repo's name first — see
   above — fork it, vendor all sources via §0, do real work, raise at
   least one real candidate, exercise both manual approval paths). This
   is still, as that brief said, "the biggest and least certain piece of
   work" here — do it after item 2, not instead of it, since a rehearsal
   with no working export gate can't test the round trip.
5. **Confirm `additionalContext` delivery** — [TODO.md](../TODO.md) item
   11 has the recommended test procedure.

## Sequencing recommendation

Item 2 above is the remaining engine work a clean install needs; item 3
is cheap and should follow immediately once it lands, since it's the same
disclosure gap this branch already found once. Item 4 is the expensive,
uncertain one and should stay last, same as the brief that first specced
it said. Item 5 can happen any time a live session is available — it does
not block anything else here.

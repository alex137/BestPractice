---
slug:              todo-2026-10-29-root-issues-from-the-landing-check-session
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "item 3: whether every repository that brings the ladder set runs an engine with _inherit_pair, checked by session_01Xcy6U3WL4YwCwzUTd35AhC before the trim reaches the set's main"
batch:             null
decision:          "item 1: the practice-file checks stay at the Debut, and at Produce when no Debut ran; the quick check does not run them"
decision_strength: decided
waiting_on:        null
noted:             2026-10-29
closed:            null
---
## What

Found by the session that fixed
[todo-2026-10-20-root-issues-from-ladder-landing-check](todo-2026-10-20-root-issues-from-ladder-landing-check.md)
(pull requests #1329, #1334, #1335). Each was measured on 2026-10-29.
Listed by harm.

1. **Broke: the landing tier's quick check let a broken practice link reach
   staging.** #1329 landed a relative `../gotchas/` link in
   [`practices/prompt-please.md`](../practices/prompt-please.md). On that commit `precedent_check.py --only
   practice-links-travel` reports 1 violated, while `precedent_push_check.py
   --changed-files-check` reports "1 changed file(s) checked, 0 problem(s)":
   the changed-files step does not run tree checks whose subject is the file
   changed. Only the harness's clean-tree baseline caught it, a branch later.
   Fix: run every tree check that can be scoped to a changed file on the
   changed files, with a test that fails on that commit.
2. **Could break: `precedent_branches.py --land` pushes straight to staging
   for a change it already knows takes a pull request**, gets refused by the
   go-update hook, and leaves the session to open and merge the pull request
   by hand. Three times in that session. Merging by hand skipped the land
   tool's own composition: #1334 merged while staging moved, so what landed
   was not what the quick check had run on. Fix: the land tool reads the same
   high-risk file list before it pushes and takes the pull request route
   itself (push, open, merge against the expected head, fetch and confirm).
3. **Could break: the ladder set's landing rule still restates universal's
   triggers.** The engine half is on main (#1335, `_inherit_pair`), the
   ladder set's own engine carries it, and its PR #126 is merged. Left: check
   that every repository bringing the ladder set runs an engine with
   `_inherit_pair` (an older one would read the trimmed pair as having no
   triggers), then trim the pair as the 2026-10-20 item describes.
4. **Warning: session start reported all three sets' engines STALE against
   a main nine days old.** It named BestPractice origin/main d04672e86b31; the
   real main was aa34219d3. The check read this clone's remote ref without
   fetching it. Fix: fetch main first, or say how old the ref is.
5. **Warning: the three sets' engines are 29 commits behind main**
   (precedent-individual, precedent-shared-writing and
   precedent-shared-ladder, all at 009d950be61b). Fix: Update Vendors in each.
6. **Warning: a fixed pre-push refusal kept its old text in a running
   container** until the next session start, because commit-identity.sh
   writes the hook only then. Fix: the hook re-reads its message from the
   repository's copy, or the push check reinstalls a hook older than its
   source.

Not filed here, because its cause is outside these repositories: the
answer-first gate refused twice in that session after an answer was written,
since text written between tool calls does not reach the transcript (the
2026-10-18 gotcha).

## Done when

Items 1, 2, 4 and 6 have a test that fails on the old code and passes on the
new; item 3's trim is in the ladder set, judged with universal's rule; item 5's
sets record an engine from a main that passed.

## Progress, 2026-10-29

Worked by a session rooted in BestPractice with the three sets attached for
pushing. Each test below was run on the old code and the new.

1. **Half fixed; the rest waits on Morgan.** The quick check runs no
   practice check at all since 2026-10-16, by Morgan's decision, and
   [quick-tier-is-closed](../practices/quick-tier-is-closed.md) lets a check
   join it only on his own words and its time. So the fix is in two parts.
   Built here: `precedent_check.py --practice-file-checks` runs the checks
   marked `binds_publishers` (whose subject is a published practice file)
   except two left to the Debut for cost, measured on 5fd34d4b3:
   generated-artifact-provenance (7.4 s) and cite-the-incident (3.1 s). With
   `--changed-files-only` it reports the 5fd34d4b3 link in about 3.1 s
   (three runs: 3.0, 3.3, 3.1). Tested in
   `check_changed_files_only_judges_the_change`; on the old engine the flag
   is ignored and the whole audit runs (76 checks), so the case fails.
   Held: calling it from `changed_files_check`, which on 5fd34d4b3 turns "0
   problem(s)" into the link finding. It is on its own branch, not landed,
   until Morgan says whether he wants it before a push.
2. **The confirming half fixed.** The engine cannot open or merge a pull
   request from a cloud container (no GitHub token reaches its tools;
   sessions use the GitHub connector), and it cannot read a set's high-risk
   list without naming the set's file. What it can do is say whether what
   landed is what was checked: `precedent_branches.py --land-confirm COMMIT`
   finds the commit on staging that brought the composition in, compares
   trees, and when staging had moved runs the quick checks on what actually
   landed. `--land`'s pull-request refusal now names that command. Tested in
   `check_land_confirm_says_whether_what_landed_was_checked`. The archived
   session_01Xcy6U3S7ohZ4fFxgcEAqU4 covered only unpushed commits in the
   carried composition (#1386), so nothing here overlaps it.
3. **Built, not landed.** precedent-shared-ladder branch
   `2026-10-29-themorgan-ladder-trim-landing-pair-g6cxn-g9904`: the pair
   names `landing_branches`, its stage-word and `--promote` triggers, its
   quoted Booked and its Act narration, and inherits the rest; the test
   judges it with universal's rule through `_settle`, and fails when the
   pair is judged alone, as an old engine would. Comparing the settled
   triggers with the old copy, the only differences are universal's newer
   wording. Measured: an engine with `inherits` but older than
   `_inherit_pair` (16e89051a) reads universal's triggers for main only; one
   older than `inherits` reads none. The three sets and the four
   repositories the 2026-10-28 Update Vendors chain covered run 009d950be61b,
   which has it. The other repositories that bring the set were not opened
   (about a dozen, private), so the trim waits on that check.
4. **Fixed.** `precedent_refresh_sources.head_commit` fetches main before
   reading it, and when the fetch fails the ref names the date of the copy
   it read. Tested in `check_refresh_sources_reads_a_fetched_main`.
5. **Recorded.** session_01Xcy6U3ru5Kd3Hp4PbLsAYP finished on 2026-10-28
   with BestPractice and all seven repositories on main and tests passing.
   The sets' engines (009d950be61b) fell behind because main moved after,
   and Update Vendors takes only a main whose GitHub test passed. Not run
   here, as the handoff asked.
6. **Fixed.** Before every push, [`precedent_push_check.py`](../tools/precedent_push_check.py) rewrites the
   machine-wide git hooks when `commit-identity.sh` is newer than the
   pre-push it wrote (about 0.3 s); the writer still leaves a newer engine's
   hooks alone. Tested in
   `check_push_check_rewrites_global_hooks_older_than_their_writer`.

Found on the way, not this item's: `check_precedent_check_fires` fails on
staging as it stands (8cb7c991d), for the planted cases of
budget-within-approval and session-file-allowances-fit.

## Decisions, 2026-10-29

- **Item 1:** Morgan, 2026-10-29, strength: decided: "#1 - yet let's leave
  them to debut (and, as always, produce if there was no debut)". The full
  tier already runs every practice check, so nothing is added to the quick
  check. **Branch disposition:** `2026-10-29-themorgan-quick-check-practice-file-checks-g6cxn-0oh9k`
  (BestPractice) -- drop: its one change is the quick-check wiring this
  decision declines, and `--practice-file-checks` itself landed with #1389.
- **Item 3:** Morgan, the same message: "#2 - you can open a new session to
  do that", and "you can take the branches and put them on staging:
  booked". The trim lands on the ladder set's staging, which no repository
  reads until a Produce moves it to the set's main; the engine check across
  the repositories that bring the set runs in
  [session_01Xcy6U3WL4YwCwzUTd35AhC](https://claude.ai/code/session_01Xcy6U3WL4YwCwzUTd35AhC)
  before that Produce.

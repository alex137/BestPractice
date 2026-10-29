---
slug:              todo-2026-10-29-root-issues-from-the-landing-check-session
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "handed to a new session by Morgan's Root issues on 2026-10-29, as one prompt rooted in BestPractice with the three practice sets attached for pushing"
batch:             null
decision:          null
decision_strength: null
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

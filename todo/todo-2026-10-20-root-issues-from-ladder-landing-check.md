---
slug:              todo-2026-10-20-root-issues-from-ladder-landing-check
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "items 1-7 built on 2026-10-20-themorgan-ladder-landing-root-issues-v5nil-bz3kz and pushed, not landed: nobody authorized landing for that handoff; item 8 waits on Morgan's pick in todo-2026-10-20-branch-page-data-in-a-file"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-20
closed:            null
---
## What

Found while fixing the ladder set's landing-authority reply rule on
2026-10-20 (precedent-shared-ladder
[PR #126](https://github.com/themorgan/precedent-shared-ladder/pull/126)).
Each one has its cause here or in a set's practice text. Listed by harm:

1. **Breaks: universal's landing rule can be satisfied by any quoted word.**
   In [`reply_check.json`](../reply_check.json), `must_also_match` for
   `prompt-please-landing-authority` accepts any quoted span containing
   approve, merge, push, land or go ahead. Measured with `violations()`: a
   block holding an order to bring a pull request into main, plus the quoted
   tool output "push refused" further down, passes. Without the quote it is
   refused. Fix: the quote counts only when it is the person's own approval
   word at the start of the quoted span, with a test.
2. **Breaks: universal's landing rule reads descriptions as orders.** It
   refuses "A push to main runs the deep check." and a bracketed list of
   examples that mentions merging the PR. Fix: port the ladder set's
   addressed-position anchor and bracketed-list suffix into universal's
   verb-led triggers. Command forms stay orders. The ladder set's pair can
   then stop restating the triggers it inherits.
3. **Breaks: the answer-first gate took a seeded handoff prompt for a
   question.** [`tools/answer_first_gate.py`](../tools/answer_first_gate.py)
   counts a question mark as a question, and the prompt was full of regex
   (`(?:`, `(?<=`). It refused the session's first file write. Fix: ignore
   question marks in code spans and fences, and read a message that opens
   with the seeded-prompt origin line as handed-on work.
4. **Could break: a set's own checkout does not load the set's reply
   rules.** `precedent_resolve.load_config` in precedent-shared-ladder leaves
   the set out (`is_repository_itself`, deliberately), so paste blocks
   written there get only universal's landing rule. Fix: read the set's own
   `reply_check.json` once, as repo-local, keeping the double-load guard.
5. **Could break: a handoff that pushes to a practice set doesn't ask for
   push access.** Session start clones sets read-only, so the first push gets
   a 403
   ([gotcha](../gotchas/gotcha-2026-09-22-a-cross-owner-source-clone-fetches-fine-and-cannot-be-pushed.md)).
   Fix: [prompt-please](../practices/prompt-please.md) (and the ladder set's
   prompt-please-on-the-ladder) has such a prompt name the set "with push
   access".
6. **Could break: a push refusal advertises its own bypass.**
   [`tools/commit-identity.sh`](../tools/commit-identity.sh) lines 1377 and
   1420 end a refusal with the environment variable that skips it. Fix: name
   the allowed route, and leave the bypass to the docs.
7. **Warning: the session-start refresh left four sources stale** because
   main's newest commit had no finished GitHub test yet. Fix: take the newest
   main that passed, as Update Vendors does, and say which.
8. **Warning, already filed:** the branch page read-through cost is
   [todo-2026-10-20-branch-page-data-in-a-file](todo-2026-10-20-branch-page-data-in-a-file.md).
   A second option measured here: every branch is written twice (HTML row
   and JSON), so rendering the rows from the JSON halves the read.

## Done when

Each fixed finding has a test that fails on the old code and passes on the
new, and the deep check reports 0 failed and 0 violated.

## Progress, 2026-10-20

Built on branch `2026-10-20-themorgan-ladder-landing-root-issues-v5nil-bz3kz`, pushed, not landed. Each case below fails on the old
code and passes on the new (measured by stashing the fix and rerunning the
named harness check); `precedent_push_check.py` passed on the branch.

1. Fixed. The approval must open the quoted span or blockquote line, and the
   engine looks for it with a tool's quoted output blanked
   ([`precedent_reply_check.py`](../tools/precedent_reply_check.py)). New
   cases in `check_reply_check_refuses_a_paste_block_that_lands_unauthorized`.
2. Fixed in universal: the ladder set's addressed-position anchor and
   bracketed-list suffix, plus "so" and "to" so an infinitive order still
   fires. The ladder pair cannot drop its triggers yet: `inherits` merges
   whole keys, and its triggers name staging as well as main, so it would
   need an engine key for the destination first. That engine key is not
   blocked; the ladder half has to wait until consumers' engines carry it,
   or an older engine would read the ladder rule with no triggers at all.
   Engine half built 2026-10-20 on Morgan's go: a set's pair names
   `landing_branches` and `adds_if_matches`, and universal's pair names the
   spans to widen (`landing_branches_pattern`). The ladder half (trimming
   precedent-shared-ladder's pair to those keys) waits until consumers'
   engines carry this, because an older engine would read the trimmed pair
   with no triggers.
   Sequence, measured 2026-10-20: the engine landed on staging with #1335,
   and Update Vendors takes only a main that passed, so it is Produce, main's
   test passing, then Update All Vendors (Morgan's individual set brings the
   ladder set, so every repository he works in carries the rule, and the
   ladder set's own vendored engine needs it too). Then, in a session rooted
   in precedent-shared-ladder, after its PR #126 is merged or folded in:
   cut the pair to landing_branches "staging|main", adds_if_matches (the
   stage-word trigger and --promote) and its quoted-Booked must_also_match;
   drop the restated triggers and exemptions; make
   test_landing_authority_reply_check.sh judge the pair through _settle with
   universal's. About 20 minutes; it rides the next routine Produce, since
   nothing breaks until universal's rule changes again.
3. Fixed, mechanism only. In this harness a seeded prompt is recorded with
   origin `task-notification`, which the gate never reads; the refused session
   must have received the prompt as a typed message. The incident itself was
   not rerun. Code spans, fenced blocks and `(?` no longer count as
   questions, and a message opening with the origin line holds nothing.
4. Fixed in the reply check, not the resolver:
   `declared_requirements` adds the set itself, once, at its declared level.
   The ladder checkout now loads `shared/precedent-shared-ladder`. Its
   vendored engine gets this on its next Update Vendors.
5. Fixed in [prompt-please](../practices/prompt-please.md), prose only, no
   test. Not copied into prompt-please-on-the-ladder: that addition replaces
   only "Where the work stops" and says the rest holds, so the line already
   applies there.
6. Fixed: both refusals name the fix; the three skip variables are in
   [FOR_DEVELOPERS.md](../documentation/FOR_DEVELOPERS.md). Both refusals
   are tested in `check_global_pre_push_refuses_a_tree_the_check_failed` (the
   practice-hook case added later the same day, when Morgan asked why the
   gap was written down instead of closed).
7. Fixed: refresh takes the newest main that passed within ten first-parent
   commits and says which; it refuses only when none passed.
8. Not built, as asked.


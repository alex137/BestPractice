---
slug:              todo-2026-10-20-root-issues-from-ladder-landing-check
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "handed on by Morgan's Root issues on 2026-10-20 as one prompt for a new session; the session that found them was working in the ladder set"
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

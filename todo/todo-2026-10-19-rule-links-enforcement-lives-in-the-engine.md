---
slug:              todo-2026-10-19-rule-links-enforcement-lives-in-the-engine
kind:              decision
domain:            mechanism
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "Morgan's yes to attach precedent-shared-writing with push access (a fourth repository beyond the ones the session started with)"
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan
noted:             2026-10-19
closed:            null
---
## What

The reply check's refusal of an unlinked branch or file is the writing
set's `rule-links` practice, but its requirements sit in BestPractice's own
[reply_check.json](../reply_check.json), tagged `"practice": "rule-links"`,
and BestPractice's harness tests them
(`check_reply_check_refuses_an_unlinked_branch_or_file` in
[tools/verify_harness.py](../tools/verify_harness.py)). That is the last
finding of `enforcement-lives-with-its-practice` after piece 6 of
[the enforcement plan](../spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md)
closed it on 2026-10-19.

## The fix

Move those requirements into the writing set's own `reply_check.json`
(the reply check reads every source's, as it reads the ladder set's), and
their test into the writing set beside them. BestPractice keeps the
generic `require_no_bare_pattern` machinery and tests it with a made-up
practice name.

## Why it waits

Renaming the slug in the test would only hide the finding. Doing the move
means attaching precedent-shared-writing with push access, a fourth
repository beyond the ones the session started with, which needs Morgan's
yes first (his rule of 2026-10-17).

## Prompt Please

Paste into: a new session rooted in BestPractice, with
precedent-shared-writing attached with push access (Morgan's yes first).

```
Sent by the session BP: pre-staging into a migration, then enforcement plan pieces 5-6 (session_01J2pakQy2Nt24xTEDJEecnX) -- https://claude.ai/code/session_01J2pakQy2Nt24xTEDJEecnX.
For: a new session rooted in BestPractice, with precedent-shared-writing attached with push access.

Move the writing set's rule-links enforcement out of BestPractice, per
todo/todo-2026-10-19-rule-links-enforcement-lives-in-the-engine.md:
1. Cut every requirement tagged "practice": "rule-links" from BestPractice's
   reply_check.json into precedent-shared-writing's reply_check.json (create
   it if absent; the reply check reads every source's, as it reads the ladder
   set's). Keep their wording and repairs unchanged.
2. Move check_reply_check_refuses_an_unlinked_branch_or_file's cases into the
   writing set as tools/checks/tests/test_rule_links_reply.sh, running against
   the engine beside it. In BestPractice keep a test of the generic
   require_no_bare_pattern machinery with a made-up practice name.
3. Confirm `python3 tools/precedent_check.py --only
   enforcement-lives-with-its-practice` in BestPractice lists nothing, and that
   a reply naming a bare dated branch is still refused in a session that
   brings the writing set.
Land both halves on staging; produce the writing set before BestPractice.
Close the todo when done.
```

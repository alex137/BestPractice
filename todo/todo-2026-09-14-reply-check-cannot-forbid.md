---
slug:              todo-2026-09-14-reply-check-cannot-forbid
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing but the work, and a decision about the negative form's semantics — whether `forbid_matching` takes regexes or literals, and what it does with a reply that quotes the forbidden thing in order to report a real hit, which that practice explicitly still requires."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="reply-check-cannot-forbid"></a>**The reply check can only REQUIRE
    text, never forbid it — so every practice about what a reply must NOT
    contain is unenforceable by it.** Verified 2026-09-14 by reading
    [tools/precedent_reply_check.py](../tools/precedent_reply_check.py): the
    whole declaration vocabulary is `require_one_of` and
    `require_when_context_grew_tokens`. There is no negative form.
    **The motivating case is
    [leak-gate-is-background](../practices/leak-gate-is-background.md)**, which is
    entirely a must-not rule — it governs what a reply is not to raise. A
    require-only checker cannot express it, so the one practice whose failures
    are hardest for the person to notice is the one the mechanism cannot
    reach. The proposed shape is a `forbid_matching` key alongside
    `require_one_of`, plus an entry for that practice in this repo's own
    [reply_check.json](../reply_check.json) (today: one entry,
    `session-spend-follows-the-task`).
    **Provenance, said plainly, because it changes how this item must be
    used.** It was relayed as an already-verified patch sitting in a report at
    `upstream-reports/precedent-findings.md` in a private repository. Two
    sessions looked: this one could not attach that repository at all (the
    cross-owner `add_repo` wall), and a session that *could* read it searched
    `main`, the working tree and the full history and found no such file, no
    `forbid_matching` anywhere in its tree, and no such entry in its vendored
    `reply_check.json`. **So this item is a specification, not a
    transcription.** Whoever builds it writes and verifies the code; there is
    no reviewed patch to copy, and treating it as one is how a plausible wrong
    checker lands in a public tree.
    **Blocked-on:** nothing but the work, and a decision about the negative
    form's semantics — whether `forbid_matching` takes regexes or literals,
    and what it does with a reply that quotes the forbidden thing in order to
    report a real hit, which that practice explicitly still requires.

## How It Closes

Not open until: nothing but the work, and a decision about the negative form's semantics — whether `forbid_matching` takes regexes or literals, and what it does with a reply that quotes the forbidden thing in order to report a real hit, which that practice explicitly still requires.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

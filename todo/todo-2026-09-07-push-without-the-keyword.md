---
slug:              todo-2026-09-07-push-without-the-keyword
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       parked
remind_on:         null
blocked_on:        "Morgan, for the hard rule only — the interim answer is given and needs nothing further. It is a question about what he wants from his own sessions and has no answer derivable from the repository. Also still to do, and NOT doable from a session rooted in this repository: mirroring the settled presenc"
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-07
closed:            null
---
## What

- <a id="push-without-the-keyword"></a>**Decide what a session does when Morgan has NOT said "Go merge".**
  **Disposition:** parked (2026-09-08, Morgan) — he has no pattern yet to
  turn into the hard rule he wants, and asked not to be asked while he finds
  one. Parked is not closed: the item stands, and the paragraph in
  [AGENTS.md](../AGENTS.md) does not close it either. Unparking is his call
  ([open-item-disposition](../practices/open-item-disposition.md)).
  [AGENTS.md](../AGENTS.md) says two things and never joins them: a PR into
  `precedent-beta-v01` needs no sign-off from Alex, and "Go merge" means
  push what the thread agreed *without asking again*. Neither says what the
  keyword's **absence** means, so each session picks — and they pick
  differently. On 2026-09-07 this session pushed
  [`b66b660`](https://github.com/alex137/BestPractice/commit/b66b660) with no
  authorization, was told that was right, then told it is not the general
  rule: *"sometimes I don't want you to merge, like today you did a few I
  didn't."* 133 commits landed on this branch that day across five parallel
  sessions, all of them Claude's, so this is not one session's habit.

  **Three readings, so the decision is a choice rather than a re-derivation:**

  1. **Hold by default.** A session commits and stops; every push needs a
     word. Costs: work sits in a disposable container until the next
     message, and [reply-links-files](../practices/reply-links-files.md)'s
     "Files touched" links do not resolve until the branch is pushed, so a
     held reply cites files nobody can open.
  2. **Push by default** — today's behaviour. The keyword then only means
     "stop asking", and the cost is exactly what prompted this item.
  3. **A line between them**, e.g. push what the thread asked for once the
     deep check passes, hold anything that adds a rule, changes a
     convention, or touches another source. Needs the line drawn precisely
     enough that five sessions draw it the same way, which is the hard part
     and the reason this is not just "use judgment".

  **Where the answer goes**, whichever it is: [AGENTS.md](../AGENTS.md)'s
  "Go merge" paragraph, and the `go-merge` practice in Morgan's individual
  set (private, so named rather than linked). **Not**
  `practices/merge-authorization-keyword.md`, which this item originally
  named — that universal practice was retired hours later, on 2026-09-07,
  because the phrase is Morgan's own preference and does not belong at a
  level that binds every adopter. The retirement does not answer this
  item: what the keyword's *absence* means is still undecided, and is now
  a question about his individual practice rather than a universal one.
  Not into a chat thread either — a rule agreed in one session binds one
  session, which is the whole failure this item describes
  ([repo-is-memory](../practices/repo-is-memory.md)).

  **Half of this closed 2026-09-07, and it is the half that was never the
  hard part.** Morgan stated the keyword's PRESENCE meaning in the clear —
  *"Go merge means PR & merge it and don't ask me again"* — and
  [AGENTS.md](../AGENTS.md)'s paragraph now carries it verbatim instead of
  telling a session to go ask. Note what that fixed: the meaning was
  already written in this item, while AGENTS.md sent sessions to Morgan for
  it, so a session reading both got the question and the answer from the
  same repository and asked anyway. That is now one statement in the place
  a session actually reads first.

  **The ABSENCE now has an INTERIM answer, and it is deliberately not a
  rule.** Asked to choose between the three readings above, Morgan answered
  2026-09-07: *"The session should use its judgment. Todo in the future to
  make a hard rule, not that."* So until that rule exists, a session decides
  for itself whether to push or merge without the keyword, owns the call,
  and **does not ask him** — the asking is itself a cost he has named twice.

  **Read the second sentence as carefully as the first.** He wants a hard
  rule eventually, and he ruled out "use judgment" as the content of it.
  Judgment is the interim state, not the destination, so this item stays
  OPEN. A later session must not close it by pointing at the interim answer
  and calling the question settled — that would encode as permanent exactly
  what he named as temporary.

  This costs what the item said it would: the three readings note that
  judgment is the one thing that does not make five sessions draw the same
  line, which is why the incident happened. That cost is now accepted on
  purpose rather than unnoticed.

  **A fourth reading was offered and NOT chosen**, recorded so it is not
  re-derived as new: *push always, merge only on the keyword* — the branch
  and PR go up so the deep check runs and
  [reply-links-files](../practices/reply-links-files.md)'s links resolve, but
  nothing lands without a word. It removes reading 1's cost and reading 2's
  both, and needs no judgment about significance. He passed on it in favour
  of judgment; it stays on the table for whoever writes the hard rule.

  **Blocked on:** Morgan, for the hard rule only — the interim answer is
  given and needs nothing further. It is a question about what he wants from
  his own sessions and has no answer derivable from the repository. Also
  still to do, and NOT doable from a session rooted in this repository:
  mirroring the settled presence wording into the `go-merge` practice in his
  individual set, so the private canonical text and this public paraphrase
  cannot drift. The cross-owner `add_repo` refusal blocks it in both
  directions (see [AGENTS.md](../AGENTS.md)'s cross-tier gotcha), so it needs a
  session rooted in that set.

## How It Closes

Not open until: Morgan, for the hard rule only — the interim answer is given and needs nothing further. It is a question about what he wants from his own sessions and has no answer derivable from the repository. Also still to do, and NOT doable from a session rooted in this repository: mirroring the settled presenc

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

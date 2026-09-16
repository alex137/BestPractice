---
slug:              todo-2026-09-07-push-without-the-keyword
kind:              analysis
domain:            null
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "hard rule: read the message for what it authorizes, phrase or not; where the reading is a genuine judgment call, say it out loud and confirm before the shared-branch steps -- never guess silently in either direction"
decision_strength: decided
waiting_on:        null
noted:             2026-09-07
closed:            "2026-09-16"
---
## What

- <a id="push-without-the-keyword"></a>**Decide what a session does when Morgan has NOT said "Go merge".**
  **Closed 2026-09-16, Morgan.** Parked 2026-09-08 while he found a pattern
  to turn into the hard rule; he gave it in the conversation that also moved
  this whole command set from phrase-matching to intent-reading, on a design
  point raised by Alex: *"apply the same to the ones that are a serious
  decision such as Go Merge, Weak Yes, etc -- and just note that (if the
  exact phrase isn't used), then use your judgment and ASK the person if you
  have doubt."*
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

  **A fourth reading was offered and NOT chosen** while judgment was the
  interim answer, recorded so it is not re-derived as new: *push always,
  merge only on the keyword* — the branch and PR go up so the deep check
  runs and [reply-links-files](../practices/reply-links-files.md)'s links
  resolve, but nothing lands without a word. Superseded by the hard rule
  below rather than chosen or rejected on its own terms.

  **The hard rule, 2026-09-16, Morgan, closing the question this item was
  parked on:** read the message for what it authorizes, not only for the
  keyword — but where a message could honestly be read either way, say the
  reading out loud and get it confirmed before the shared-branch steps run.
  Committing locally is never held on this; only the push, the pull
  request, or the merge is. This is reading 3 from above, made precise
  enough for five parallel sessions to draw the line the same way: the
  phrase removes doubt outright, and doubt otherwise gets a stated
  confirmation rather than a silent guess in either direction. Recorded in
  [AGENTS.md](../AGENTS.md)'s "Go merge" and "Weak yes" paragraphs and in
  [go-merge.md](../practices/go-merge.md),
  [weak-yes.md](../practices/weak-yes.md) and
  [decision-strength.md](../practices/decision-strength.md) directly.

  **The individual-set mirroring this item once named as a separate blocker
  is moot.** It referred to `go-merge` in Morgan's individual set as the
  "private canonical text" a public paraphrase could drift from — true
  2026-09-07, before the practice moved to universal the next day. Since
  then the individual copy is `status: deduplicated`, pointing back at this
  same universal file; there is no longer a second canonical copy for
  anything to drift from.

## How It Closes

Closed: Morgan gave the hard rule 2026-09-16, and it is written into
`AGENTS.md` and the three practice files named above.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

2026-09-16: closed. Hard rule decided in the conversation that also moved
`Go merge`, `Weak yes`, `decision-strength` and several other commands from
phrase-matching toward intent-reading, on a design point raised by Alex and
carried by Morgan.

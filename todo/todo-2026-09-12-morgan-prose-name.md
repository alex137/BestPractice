---
slug:              todo-2026-09-12-morgan-prose-name
kind:              decision
domain:            content
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"That was diction. So option #2: I'm a male, him/me, and my name is Morgan.\" -- confirmed no second prose name is needed; identity.json's name stays what it already was."
decision_strength: decided
waiting_on:        null
noted:             2026-09-12
closed:            2026-09-12
---
## What

- <a id="morgan-prose-name"></a>~~**What to call Morgan in prose, when it is
  not what git records.**~~ **Answered 2026-09-12, by him: the name in
  that quotation was a dictation artifact, there is no second name, and
  nothing gets added.**

  Raised 2026-09-12, in the thread that landed
  [declared-pronouns](../practices/declared-pronouns.md). Asking for the
  pronoun rule he described the standing practice as *"always refer to me as
  a he, him, and Mel"* — but nothing in his individual set says "Mel."
  `identity.json` declares `Morgan F`, and the clause that came out of
  `commit-author` said to use "Morgan." So either that was dictation, or he
  wants a prose name distinct from the one git records, which would be a
  second field beside `pronouns` (`name` is what a commit is authored as and
  cannot double as a display name without breaking
  `check_commit_author.py`'s comparison). Nothing was invented either way —
  the pronouns landed, the name did not
  ([no-invented-specifics](../practices/no-invented-specifics.md)).

  **The answer, 2026-09-12.** Asked directly whether the name in that
  quotation was the prose name he wanted declared, he said: *"That was
  diction. So option #2: I'm a male, him/me, and my name is Morgan."* So the
  first branch of the guess was the right one, and the repository was already
  in the correct state:
  `identity.json`'s `name` (`Morgan F`) stays what commits are authored as,
  and prose uses "Morgan" — exactly what the clause that came out of
  `commit-author` said. **No second field is added** to `identity.json`, to
  [templates/practice-set-individual/identity.json.template](../templates/practice-set-individual/identity.json.template),
  or anywhere else, and
  [declared-pronouns](../practices/declared-pronouns.md) needs no change: the
  pronoun half landed correctly and this answer does not touch it.

## How It Closes

Already closed 2026-09-12 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.

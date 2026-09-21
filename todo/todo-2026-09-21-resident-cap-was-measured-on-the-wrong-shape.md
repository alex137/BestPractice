---
slug:              todo-2026-09-21-resident-cap-was-measured-on-the-wrong-shape
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan -- raising or splitting a declared ceiling is his call, not a session's"
noted:             2026-09-21
closed:            null
---
## What

**`resident_block_tokens: 2000` blocks a real adopter's vendor update, and
the cap is the thing that is wrong.** Measured here on 2026-09-21, with all
four of this account's sources resolving — the same shape a consuming repo
has:

| Level | Resident tokens | Share of the 2000 cap |
|---|---:|---:|
| universal (this repo) | 1379 | **69%** |
| individual | 442 | 22% |
| shared (3 sets) | 347 | 17% |
| **total** | **2168** | **108% — over** |

A consuming repo reported 2198 independently and stopped its vendor update
at the runbook's view-regeneration step.

**The cap reserves 69% of every adopter's resident budget for this
repository's own practices**, leaving 621 tokens for the person's own rules
plus every team set they declare. Morgan's come to 789.

## It Already Happened, and Was Closed by Demoting Two Practices

**2026-09-11:
[todo-2026-09-11-cross-source-resident-block-over-cap.md](todo-2026-09-11-cross-source-resident-block-over-cap.md)**
— same wall, same cause, closed `decided` by Morgan choosing to demote
`buenos-aires-dates` and `small-calls` out of the resident block. *"I want
to remove both."*

**Ten days later it is back**, because universal grew again. That is the
whole case for treating the cap rather than the contents: demotion
resolves the symptom and resets the clock, and the clock is running at
roughly one crossing per fortnight. The 09-11 answer was a band-aid and
this is the evidence ([durable-fix](../practices/durable-fix.md)).

It is also why this item does not simply name a third practice to demote.

## Why the Cap Is the Wrong Thing to Satisfy

**2000 was measured against a tree where only `universal` resolves.** This
repo's own resident block is ~1379 and has always fitted comfortably. The
number was never tested against the multi-source shape Precedent exists to
provide, so it is not a considered allowance for an adopter — it is this
repo's own measurement with headroom, applied to everybody.

Which makes "demote a practice to get under it" the tail wagging the dog.
The adopter would be dropping a rule they chose, to make room for rules
this repository chose, under a ceiling neither of them set for this case.

**The trigger was ours.** `fence-block-for-paste` became resident on
2026-09-21 at 218 tokens. The consuming repo had 22 tokens of slack, so
any new universal resident anywhere would have done this. That is not an
argument against that practice; it is the evidence that the budget has no
structural guarantee behind it.

## The Shape of the Answer, if One Is Wanted

[session-load-budget](../practices/session-load-budget.md)'s own
[AGENTS.md](../AGENTS.md) ceiling already solved this problem once, and the reasoning is
recorded in [tools/session_load_budgets.json](../tools/session_load_budgets.json):
12,000 = 5,600 generated (a resident cap plus an occasion cap, the most the
generated half can ever be) + 6,400 declared prose allowance. **Generated
growth alone can no longer put that file over.** The same structure applies
here:

- a **universal sub-cap** this repository holds itself to, at or below
  today's 1379, so an adopter's headroom cannot be eaten by upstream, and
- an **adopter allowance** on top, which is theirs to spend and theirs to
  reduce.

That makes the two pressures separable. Today they are not: an adopter over
the line cannot tell whether the cause is their own set or this week's
upstream merge, and the only lever they have is the wrong one.

## What This Item Is NOT Asking For

**Not a raise to make a red check green.** The registry's own comment
forbids exactly that, and it is right to. This is the other case it names:
a number chosen on purpose, in a commit, with the reason written down —
because the current one was chosen against a different shape.

Nor is it an argument that nothing here should be compressed.
`brainstorm-holds-commits` (219) and `fence-block-for-paste` (218) are 20%
of the whole budget for two rules, and both can be said shorter. That is a
[reduction-pass](../practices/reduction-pass.md), worth doing on its own
merits, and it does not answer the structural question.

## For Whoever Runs the Reduction Pass

**Measured 2026-09-21 on this tree, and reproduced three times
independently** (here, a consuming repo, and a session auditing the four
sets) — all three agree on universal = 1379, which is what makes the
number safe to plan against.

| Practice | Level | Tokens | Share |
|---|---|---:|---:|
| `default-register` | shared | 292 | 13.5% |
| `brainstorm-holds-commits` | universal | 219 | 10.1% |
| `fence-block-for-paste` | universal | 218 | 10.1% |
| `audience-register` | individual | 210 | 9.7% |
| `answer-first-ask-before-long-work` | universal | 206 | 9.5% |
| `environment-gotchas` | universal | 152 | 7.0% |
| `reply-fits-one-screen` | individual | 144 | 6.6% |
| `reply-links-files` | universal | 123 | 5.7% |
| `write-like-a-human` | universal | 113 | 5.2% |
| `no-invented-specifics` | universal | 101 | 4.7% |
| `reply-is-short` | individual | 88 | 4.1% |
| `bold-key-phrases` | universal | 63 | 2.9% |
| `verify-postcondition` | universal | 62 | 2.9% |
| `nonblocking-questions` | shared | 55 | 2.5% |
| `orientation-map` | universal | 44 | 2.0% |
| `repo-is-memory` | universal | 42 | 1.9% |
| `quick-index` | universal | 36 | 1.7% |

**Total 2168.** The cap is 2000.

**Where the room is, if room is what is wanted.** The two largest are
universal and together they are 511 tokens — about
24% of the whole budget for two rules.
Neither says anything a shorter rule could not. Compressing that pair is
the cheapest ~200 tokens available and it helps every adopter rather than
one repo.

**What NOT to do**, and it is the reason this item exists: demote a
practice to get under the line. That was the 2026-09-11 answer, it reset
the clock, and the clock came back round in ten days. The question this
item asks is whether the CAP is the right shape, and a reduction pass does
not answer it — it buys time, which is worth buying, and is not the same
thing.

**Answering this section's own "what NOT to do", because route A did
exactly the thing it names.** The warning is against demoting a practice to
get under the line, on the grounds that 2026-09-11 did that and the clock
came back round in ten days. Route A demoted two — and the difference is
that 2026-09-11 dropped `buenos-aires-dates` and `small-calls` out of the
resident block with no other channel carrying them, while both practices
demoted here declare `gates: ["reply"]`, which fires unconditionally on
every turn. The rule stays in force; what changed is which mechanism
delivers it. Route D is this section's own recommendation, taken.

That does not make the warning wrong about the shape of the problem. This
pass bought time, which this section says is worth buying and is not the
same thing as an answer.

## Reduction Pass Run 2026-09-21 — The Report

**This does not close this item.** It bought headroom; the structural
question above — a universal sub-cap plus an adopter allowance, instead of
one number measured against a single-source tree — is untouched and still
`waiting_on` Morgan. At the growth rate this item records, headroom is the
thing that runs out.

Morgan picked all three routes from a costed menu, 2026-09-21: *"Do A and B
and C - I like all"*. strength: decided.

| Surface | Before | After | Cap |
|---|---:|---:|---:|
| universal (this repo) | 1379 | **1055** | — |
| individual | 447 | **392** | 550 |
| shared/working-style | 351 | **144** | 425 |
| **combined resident block** | **2198** | **1591** | **2000** |

Measured with [tools/build_views.py](../tools/build_views.py)'s own `_approx_tokens` (`words × 1.3`) over
the rendered blocks, before and after. Headroom went from −198 to +409.

### What Moved

**A — two universal practices demoted to `tier: on-demand`, −324.**
[fence-block-for-paste](../practices/fence-block-for-paste.md) (219) and
[reply-links-files](../practices/reply-links-files.md) (124). Nothing was
rewritten and no rule changed: both already declared `gates: ["reply"]`, so
the `UserPromptSubmit` hook prints their clause before every reply is
written and the full Rule is one `precedent_gate.py reply` away. This is
reduction-pass step 1 — text a session already reaches at a guaranteed
moment. **The cost, stated plainly:** `reply-gate.sh` is the Claude Code
adapter's hook, so on Codex and Gemini CLI these two now arrive through the
standing instruction rather than automatically. Each file's `## Story`
records this.

**B — [default-register](https://github.com/themorgan/precedent-shared-working-style)'s
Rule compressed, −207.** 293 → 87. Its fallback body moved into `## Detail`
word for word; the precedence sentence stayed in the Rule. The body only
fires where no reader has declared a register, and Morgan's
`audience-register` resolves in every repository he works in — so those
tokens were paid on every turn for text switched off before it was read.
Approved by Morgan, sole approver in that set's `approvers.json`.

**C — `reply-fits-one-screen` deduplicated into `reply-is-short`, −55.**
Two resident rules about reply length became one. Every clause survives in
the surviving Rule; the retired file keeps its Why, its Story and the
verbatim quote that killed `half-the-words`, and carries
`status: deduplicated`, `in_force_at: reply-is-short`.

### What This Pass Did NOT Do, and Why

- **Did not touch `no-invented-specifics`, `verify-postcondition`,
  `repo-is-memory` or `write-like-a-human`**, though all four are in the
  reply gate too and demoting them would have been another ~323. They bind
  *during* the work, not at the moment a reply is written, so a reply-time
  reminder arrives after the damage. The gate is the wrong channel for them.
- **Did not raise any ceiling.** Route C returned 55 against the ~115 this
  session estimated when it costed the menu; the merged rule kept every
  clause, which is where the difference went.

### Route D, Added the Same Day

Morgan asked for the "optional" item at the end of the costed menu, so the
three largest remaining universal residents were compressed too. **This one
is rewriting, not moving** — the menu's step 1 was exhausted by route A, so
every token here came out of a Rule somebody has to re-read. Each practice's
own `## Story` records what moved and what stayed.

| Practice | Before | After |
|---|---:|---:|
| `brainstorm-holds-commits` | 221 | **137** |
| `answer-first-ask-before-long-work` | 208 | **161** |
| `environment-gotchas` | 153 | **123** |

**−160, not the ~250 this session estimated.** The estimates were drafted
against word counts that left out the rendered `**slug.** ` prefix and were
optimistic about how much of each Rule was argument rather than rule. Said
plainly because the same optimism showed up in route C, and a menu whose
numbers run high twice is a menu to distrust next time.

Nothing was dropped. What moved to `## Detail`: the dirty-working-tree
reasoning and the list of phrases that end a brainstorm; the two definitions
`answer-first-ask-before-long-work` carried inline (what makes a question
easy, the four examples of a long task); and the sentence about the
generated gotcha overview. One thing moved the other way — *"when in doubt,
it is a brainstorm"* came UP from Detail into the Rule, because it is the
operative default, not a gloss on one.

**What stayed, deliberately:** `environment-gotchas`' "none of it loads into
the instructions file, at any size" clause, which is the rule that stops an
instructions file regrowing the catalogue; and
`answer-first-ask-before-long-work`'s two exceptions, which a session reads
at exactly the moment it is deciding whether to ask.

### Where the Block Stands After All Four Routes

| Surface | Start of day | After A–C | After D | Cap |
|---|---:|---:|---:|---:|
| universal | 1379 | 1055 | **895** | — |
| individual | 447 | 392 | **392** | 550 |
| shared/working-style | 351 | 144 | **144** | 425 |
| **combined** | **2198** | **1591** | **1431** | **2000** |

Headroom: −198 → **+569**. At the growth rate recorded at the top of this
item, that is weeks rather than days — and it is still headroom, not a
structural guarantee. **The open question above is unchanged.**

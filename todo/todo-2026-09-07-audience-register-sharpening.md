---
slug:              todo-2026-09-07-audience-register-sharpening
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "his approval of the new wording. It is his rule about how he is spoken to, and a session rewriting that unilaterally is the same overreach the rule exists to correct."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- [ ] <a id="audience-register-sharpening"></a>**Sharpen `audience-register` so the plainer register actually holds —
  three changes, all in the individual practice set, all needing the
  account owner's sign-off on the wording.** Raised 2026-09-07, after he
  pointed out he has asked for plainer replies "many many times ... today,
  yesterday, the day before", and that each re-explanation was right. The
  rule already existed and was already `tier: resident`. **The dominant
  cause was that it never loaded** — fixed the same day by
  [AGENTS.md](../AGENTS.md)'s new first-tool-call banner — but three
  weaknesses in the rule itself survive that fix and would have blunted it
  anyway:

  1. **It aims at the register already being used.** Its Rule says
     *"somewhat technical ... I read code, I follow a mechanism ... I would
     rather have the real name"*, which describes the replies being
     objected to. Re-aim it at a test applicable while writing: *would a
     smart person who does not work in this repository every day need a
     follow-up question to use this sentence?*
  2. **"Gloss it in a clause the first time" licenses the actual
     failure.** One mention buys the term for the rest of the reply, so
     in-house shorthand went bare after its first outing. Explain the term
     every time it appears, in the same sentence, and accept the
     repetition.
  3. **Nothing counts a miss, and one is cleanly observable.** The
     practice argues no mechanical check is possible because a chat reply
     is not an artifact any repo holds — true for judging register in the
     abstract, but *being asked for a plainer version* is unambiguous,
     needs no judgment, and currently goes unrecorded. Treat it as a
     defect when it happens, say so, and append the offending phrase to a
     running list in that practice's own `## Story`. The list becomes the
     most useful part of the rule, being made of real sentences rather
     than descriptions of sentences.

  Worth knowing while deciding: a team set carries a same-slug
  `audience-register` requiring the **plainer** register, and team
  outranks individual, so in a project declaring that team source the
  plainer rule already wins. This repository declares a different team
  set, so the individual rule is what binds here. Changing the individual
  rule is cleaner than moving repositories between team sources.
  **Blocked on:** his approval of the new wording. It is his rule about
  how he is spoken to, and a session rewriting that unilaterally is the
  same overreach the rule exists to correct.

## How It Closes

Not open until: his approval of the new wording. It is his rule about how he is spoken to, and a session rewriting that unilaterally is the same overreach the rule exists to correct.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

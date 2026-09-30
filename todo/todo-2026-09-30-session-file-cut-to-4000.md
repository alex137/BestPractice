---
slug:              todo-2026-09-30-session-file-cut-to-4000
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         2026-09-30
blocked_on:        "Morgan: leave it above target for now and brainstorm another approach to the cut (2026-09-30)"
batch:             null
decision:          "target 4,000; hard ceiling 4,400; source occasion allowances universal 1,800, repo-maintenance 450, writing 150, working-style 150"
decision_strength: decided
waiting_on:        "a brainstorm with Morgan on how to cut the occasion index and the resident rules"
noted:             2026-09-30
closed:            null
---
## What

- <a id="session-file-cut-to-4000"></a>**Bring precedent-individual's
  session-start file under 4,000 tokens, then switch on the 4,400 hard
  ceiling.**

  The file (`.precedent/SESSION_PRACTICES.md` in precedent-individual) was
  about 4,872 tokens against `main`'s sources and 5,249 against
  `pre-staging`'s on 2026-09-30: about 3,300 of occasion index (universal
  about 2,760 of it), 1,290 of resident rules, and about 260 of prose.
  Morgan set a 4,000 target and a 4,400 hard ceiling (2026-09-29, strength:
  decided) and the allowances above. The 4,000 target is in
  precedent-individual's registry now, and the file warns once per session
  while it is over.

  **Held until the cut, per Morgan:** lowering the four
  `occasion_share_tokens`, and setting `hard_ceiling: 4400` with a
  `fixed_allowance` on the session file's registry entry, which switches on
  `precedent_check.py --only session-file-allowances-fit`. Each lowered or
  added number goes into that repo's `approved_budgets` with his words.
  The commit block that was also held here, refusing commits in
  precedent-individual while the file is over its hard ceiling, was
  retired on 2026-09-30 before it was ever switched on (Morgan: "Since
  it's never used then let's retire it completely. Approved. Act.";
  strength: decided). No commit there can make this file smaller; the
  hard ceiling is held at the sources.

  **The allowances alone cannot fit 4,400, and that is part of the
  brainstorm.** The hard ceiling is enforced as a sum: each carried source's
  occasion allowance plus its resident cap, plus the file's own prose. At
  the decided allowances the index parts come to 2,550. Today the resident
  caps are universal 2,000 and working-style 425, and repo-maintenance and
  writing declare none, so they fall back to 2,000 each. For the sum to
  fit, the resident caps have to come down to about 1,550 in total, against
  1,290 of resident rules measured in the file. Which cap each source gets
  is Morgan's call.

- **Reminder for tonight, 2026-09-30 (Morgan: "Remind me tonight").**
  A Reduction pass that day took the file from 5,155 to 4,836 tokens, as
  the cap measures it (the over-target warning no longer counts): the
  "Reading one of these in full" section was retired, and trigger phrases
  nobody says left the occasion index. The rest of the gap is mostly
  universal's situation entries ("When renaming, moving or deleting a file
  others may link to", and the like). Cutting those decides which rules
  stop firing in every session, so it waits on Morgan's word, practice by
  practice.

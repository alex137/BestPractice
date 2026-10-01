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

## Reduction pass review, 2026-10-01

Morgan asked for a Reduction pass and then a deep review of every practice in
the file, "which practices you recommend changing or dropping or merging"
(2026-10-01). Four read-only reviewers covered all of them except
upstream-fix, durable-fix and fix-the-original, which another session was
merging that day. **Nothing below is applied yet; each line waits on
Morgan's pick.** Token figures are words x 1.3 against the file as built on
2026-10-01 (4,911).

**Measured.** Every other always-loaded surface is under its line, the
individual set's own AGENTS.md (1,622 of 1,800) and CLAUDE.md included;
that CLAUDE.md's 92 is almost all an HTML comment Claude Code does not load,
so moving it saves nothing. Steps 1-3 of the menu find no lossless room in
the session file: 97% of it is generated, and none of its lines is loaded
twice in a session rooted in the set.

**Two facts that limit what can be routed out.** (1) The set repos wire the
push, merge, workflow-write and seeded-prompt hooks but not
`precedent-paths.sh` or `reply-gate.sh`, so in a session rooted in a set the
path and reply channels fire only if the session runs them by hand -- and
this file is loaded only in sessions rooted in the individual set. (2) The
merge and push gates print practices only when run by hand; the push hook
runs the mechanical checks. So a line is safe to drop for routing alone only
where a mechanical check refuses the push before any harm. Related open
item: [should sets run the reply gate](todo-2026-09-25-should-sets-run-the-reply-gate.md).

**On dropping the one-line summaries.** In a set-rooted session the index is
often the only channel that reaches a session at all, and the summary is
often the only part of a rule it reads; a slug like `capture-gate` or
`small-calls` does not carry its rule. Each look-up also loads 100-300
tokens. Tier 1 below reaches the target without it.

### Tier 1 -- no rule stops firing (merges, dead mechanisms, shorter wording)

| Change | Saves |
|---|---|
| **Link rules:** rule-links absorbs doc-link-text, file-mention-links (and its reply gate) and branch-links; name-the-branch stays, shortened | ~100 |
| **Stage commands:** one index line for promote, consider, act, debut and produce, their `command:` phrases moved into promote's; go-update keeps its own line | ~97 |
| **Shared occasion lines** for families that already cite each other: gates and heavy solves (slow-steps-report-and-cache, gate-ledger, gates-fail-fast, shared-result-cache, review-against-a-contract); numbers (verify-decomposition, scripts-assert-properties, one-formatter-per-quantity, tabular-shared-renderer, quote-discipline); outward documents (frame-from-audience-question, outward-summary-discipline, deliverables-carry-no-process, curly-quotes); "already covered?" (search-by-purpose, lease-in-flight-work, base-branch-is-the-record); open items (todo-is-a-handoff, item-closes-on-its-condition) | ~190 |
| **Resident text tightened**, same meaning: current-rule-governs, brainstorm-holds-commits, write-like-a-human (closing paragraph to `## Why`), language-variety | ~146 |
| **Retire two dead mechanisms:** blank-blocklist (targets the retired section-1 install's blocklist) and new-rule-placement (numbered rules documents); the 2026-09-28 very deep check recommended both | ~53 |
| **Scrub:** scrub-gate (built on `process/upstream/**`, which no repo here has) and private-repo-scrub become one practice about what is in force now | ~45 |
| grep-before-search absorbs wide-search-needs-asking | ~40 |
| resolved-issue-note-updates folds into universal change-updates-its-docs (no-duplication) | ~40 |
| answer-first-ask-before-long-work absorbs nonblocking-questions as part (4) | ~30 |
| quiet-checks folds into verdict-not-mechanism | ~30 |
| capture-gate and second-pass-capture become one line | ~25 |
| install absorbs default-branch; drift-notice absorbs fresh-check-escalation | ~50 |
| very-deep-check's line carries full-practice-audit (its Pass 4) | ~23 |
| rename-updates-links absorbs migration-scrubs-vocabulary; index-remembers-past folds into document-status-header | ~50 |
| Shorter occasion or clause, same meaning: their-constraints-are-given, organize-scattered-content, deep-check, constants-are-risk-inputs, judgment-check-or-tool, attach-never-clone-individual, decommission-deletes-files, repair-cannot-discard-work, my-options, prompt-please, write-it-up | ~120 |

**Tier 1 total: about 1,040**, which would bring the file to about 3,900.

### Tier 2 -- takes a rule out of every session (each is a call to make)

- **Demote four resident rules the install template already carries:**
  orientation-map, quick-index, environment-gotchas, bold-key-phrases
  (~234). The template's own sections and checks keep the first three; the
  cost of bold-key-phrases is bolding in chat, which its Rule never asked for.
- **Move modeling practices out of universal into an opt-in set:**
  name-both-sides-of-ledger, permutation-frontier-column,
  check-source-architecture, build-buy-decompose (~100, more if the numbers
  family goes too). [ATTENTION_CEILING.md](../spec/ATTENTION_CEILING.md) already says this repo does
  not exercise them; the dependent repo they came from would opt in.
- **Route out lines a mechanical check already refuses at push:**
  ci-workflow-approved, filename-separator, session-trailer,
  revert-needs-no-trailer, vendor-rollout-disclosed, two-check-levels,
  routing-audit (~230). Lines that would rely on the path hook instead --
  assorted-notes, no-duplication, vendor-neutral-by-default,
  mirror-into-agents -- wait until the set repos wire it.
- **default-register (~86):** it steps aside by its own words for anyone
  with a declared register, but a shared practice outranks an individual
  one, so his set cannot switch it off. A `yields_to_identity: register`
  field read by the loader would; a smaller option is demoting it in the
  working-style set.

### Housekeeping found on the way (no token cost)

Shared copies still `active` beside a live universal one: automation-issues,
dont-race-another-window, fresh-before-write, session-trailer; and
vendor-neutral-by-default in both a shared set and BestPractice's `local/`.
derived-file-marker's header says hand edits are safe, and
generated-edit-goes-upstream says never edit. The session file's standing
instruction does not mention [precedent_paths.py](../tools/precedent_paths.py).

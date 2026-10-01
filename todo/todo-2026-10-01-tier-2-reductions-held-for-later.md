---
slug:              todo-2026-10-01-tier-2-reductions-held-for-later
kind:              decision
domain:            mechanism
severity:          minor
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "Morgan: noted as a possibility for the future, not approved (2026-10-01)"
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-10-01
closed:            null
---
## What

- <a id="tier-2-reductions-held-for-later"></a>**Two Tier 2 reductions
  from the 2026-10-01 review, held as possibilities for later.**

  The [session-file open item](todo-2026-09-30-session-file-cut-to-4000.md)'s
  Tier 2 named six calls. Morgan approved two (four resident rules made
  on-demand, and seven index lines a push check already enforces taken out
  of the index) and asked for the rest to be written down: *"Booked, attach
  both shared sets, and do both Tier 2 items (and note as a possibility for
  the future in a Todo the other tier 2 items to consider)"* (2026-10-01,
  strength: decided). These are the two left.

  **1. Move the modeling practices out of universal into an opt-in shared
  set.** `name-both-sides-of-ledger`, `permutation-frontier-column`,
  `check-source-architecture` and `build-buy-decompose`, and possibly the
  figures family that shares the "computing, quoting or tabulating figures"
  line (`verify-decomposition`, `scripts-assert-properties`,
  `one-formatter-per-quantity`, `tabular-shared-renderer`,
  `quote-discipline`).
  - *Evidence:* [spec/ATTENTION_CEILING.md](../spec/ATTENTION_CEILING.md)
    lists them as practices this repository does not exercise, and a
    grep there found no content any of them governs. All nine carry
    `approved_by: "BestPractice (pre-fork)"`: they came from the dependent
    repository the catalogue was forked from, which is what they were
    written for.
  - *Cost to a session:* about 102 tokens of universal's occasion share for
    the four, about 190 with the figures family, measured on 2026-10-01
    with `build_views.occasion_share`.
  - *Why held:* that pre-fork dependent repository would lose them silently
    on its next Update Vendors unless it opts into the new set first, and
    nobody here can see which repositories still rely on them. Moving them
    safely needs the opt-in to reach it before the rules leave universal.

  **2. `default-register` stops loading for a person who declares their own
  register.** It is resident in precedent-shared-working-style and says
  itself that it steps aside when the person has declared a register, but a
  shared practice outranks an individual one, so an individual set cannot
  switch it off.
  - *Evidence:* its Rule's own first sentence ("that declaration governs and
    this rule steps aside"), while it still loads in full for someone whose
    individual set declares a register.
  - *Cost to a session:* about 88 tokens of resident text, measured with
    `precedent_show.py default-register` on 2026-10-01.
  - *What it needs:* a loader field such as `yields_to_identity: register`,
    read by [tools/build_views.py](../tools/build_views.py) and
    [tools/precedent_session_practices.py](../tools/precedent_session_practices.py),
    that drops the practice when the resolved identity declares that field.
    The smaller option is making it on-demand in the working-style set.
  - *Why held:* the two engine files another session was editing on
    2026-10-01 had to land first. They have, in PR #794; what remains is
    Morgan's call.

## How It Closes

Morgan decides each of the two: take it up (then it is built, and this item
closes with what was done), or leave it (then it closes as `dropped` with his
words). Either can close on its own; the item closes when both have.

## Notes

2026-10-01: written at Morgan's request on the branch that applied the two
approved Tier 2 items. Disposition `wait`, `remind_on` null: he asked for a
note of possibilities, not a reminder, so no session raises it unprompted.

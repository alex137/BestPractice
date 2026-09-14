---
date: '2026-09-06'
question: |
  `status: retired` was the only way to record that a practice
  stopped applying in a source, and nothing recorded whether
  anything replaced it -- the forwarding address existed only as
  English prose in `## Story`, which no tool reads. Should the
  status be renamed, should retirement be replaced entirely or
  merely demoted, where does the "absorbed into the engine" case
  belong, and what should the new forwarding field be called?
decision: |
  Three statuses with different bars of evidence: `active`
  (in force here), `deduplicated` (the copy here is redundant;
  the rule is in force elsewhere), `retired` (nobody wants this
  rule anywhere). A new frontmatter field, `in_force_at:`,
  is required on anything that is not `active`: a slug that must
  *resolve in force*, the literal `engine`, or the literal `none`.
  The engine-absorption case is filed under `deduplicated` with
  `in_force_at: engine`, NOT under `retired`. The field is called
  `in_force_at:` rather than `superseded_by:`. Enforced by
  `build_views.status_contract_violation` and
  `verify_harness.check_status_contract`, and honored by every
  loading channel rather than by the generated views alone.
alternatives: |
  ["Replace retirement entirely with deduplication, on the
  theory that every correct use so far was a deduplication --
  rejected because two real cases (genuine obsolescence, and
  absorption into the mechanism) cannot be expressed as a
  deduplication against a surviving practice",
  "Keep the engine-absorption case under `retired` with
  `in_force_at: engine`, as the originating brief proposed --
  rejected because that rule is fully in force and filing it
  under a status meaning 'nobody wants this rule anywhere'
  reproduces the exact conflation the rename removes",
  "Name the forwarding field `superseded_by:`, pairing it
  visually with the existing `supersedes:` -- rejected because
  'supersede' means replace, which is not what happens in a
  deduplication, and it invites the same resemblance question
  that 'retire' invited",
  "Add a fourth status, `absorbed`, for the engine case --
  rejected as more vocabulary to carry across 44 files than the
  distinction earns"]
decided_by: Morgan
---

## Why this was asked

Every use of `status: retired` since practices became files, across the
whole ecosystem:

| Practice | What actually happened | Verdict |
|---|---|---|
| `bestpractice-sync` | copy dropped; rule in force at individual | correct — a **deduplication** |
| `header-caps` | copy dropped; rule in force at universal | correct — a **deduplication** |
| `deep-check` | dropped outright, "very-deep-check covers it" | **wrong; reversed 2026-09-06** |

Every correct use was a deduplication, and the only attempt at a genuine
retirement was the mistake. Morgan's framing, and the reason this is not a
labelling quibble: **rules shouldn't have duplicates, and that is a different
thing from retiring a rule.** When a team practice is dropped because the
universal catalogue now carries it, the rule is not retired at all — it is
fully in force, from a different source. Only the redundant copy went away.

The word invited the failure. "Retire" sounds like a judgement about whether
a rule is still wanted, so the question a session asks itself becomes *"does
something similar exist?"* — answerable by reading two files and feeling that
they rhyme. `deep-check` (the working check a session runs against its own
repo when committing) was dropped on the authority of `very-deep-check` (a
deliberately rare, expensive, cross-repo audit that its own Rule forbids
wiring into any commit, push or merge gate). They differ in kind and cadence;
they merely resembled each other, and resemblance was accepted as coverage.

**"Deduplicate" cannot be answered by resemblance.** It forces the only
question that matters: what is the surviving copy, and does it resolve in
force?

## Why the argument is from mechanism, not from the numbers

Three data points is not a statistical case, and this record should not be
read as one: "every correct use was a deduplication" is two out of two. What
carries the decision is the claim that the word determines which question a
session asks itself, plus a migration-cost asymmetry that only worsens — two
practice files carry the old status today, against roughly 44 files of
vocabulary, and both numbers grow with every source added.

## Why retirement is demoted rather than deleted

Two cases cannot be expressed as deduplication, and both have occurred:
genuine obsolescence (a rule about a tool you stopped using has no duplicate
anywhere — the case the word actually fits, and what
[tools/precedent_retire.py](../tools/precedent_retire.py) exists to find),
and absorption into the mechanism. So retirement survives as the rare, loud,
deliberate path, and stops being reachable by "something similar exists."

## Why the engine case is `deduplicated`, not `retired`

The originating brief proposed `retired` with `in_force_at: engine`, and this
is the one place the decision departs from it. RepoPersonalPreferences'
`bestpractice-wins` declared that the personal layer beats the generic one;
it was dropped because precedence became a property of the resolver. That
rule is **fully in force** — merely enforced by code instead of by prose. The
brief itself says its effect "survives structurally."

Filing an in-force rule under a status defined as "nobody wants this rule
anywhere" would reproduce, one level down, the exact conflation this whole
change removes. So `deduplicated` means "in force elsewhere, and here is
where" — whether *elsewhere* is another practice or the engine — and
`retired` keeps a single legal value, `none`. That is also what makes the
check a single rule rather than three special cases, and what makes `retired`
loud: it now has one meaning and one legal forwarding value.

## Why `in_force_at:` and not `superseded_by:`

The brief argues for three pages that "retire" shapes the question badly,
then names the new field with a word carrying the identical defect.
"Supersede" means *replace*, which invites "is there something that covers
this?" — the resemblance question. It also contradicts the semantics of a
deduplication, where nothing supersedes anything: the same rule is in force
from a different source. And `supersedes:` already exists in this format
meaning real replacement, so reusing the root would make two fields that look
like a matched pair mean unrelated things.

`in_force_at:` states the postcondition the check actually verifies, and
cannot be satisfied by resemblance.

## Why the channel fix had to land in the same change

`status:` was honored by two of five loading channels
([tools/build_views.py](../tools/build_views.py), which defines
`IN_FORCE_STATUS`, and [tools/precedent_resolve.py](../tools/precedent_resolve.py),
which re-exports it).
[tools/precedent_paths.py](../tools/precedent_paths.py),
[tools/precedent_gate.py](../tools/precedent_gate.py) and
[tools/precedent_show.py](../tools/precedent_show.py) read `practices/*.md`
directly and never looked at `status:` at all — so a session was told by the
index that a practice did not exist and told by the other three to follow it.

**This is the opposite failure from the one it looks like, and it is why the
two had to land together.** Nothing broke while `deep-check` was wrongly
marked retired *because the merge gate kept serving it*. A bug was
compensating for a bad decision. Fixing the channels without the
`in_force_at:` check would have removed that accidental safety net and made
the next bad drop bite for real — and the gates are the blocking path, so the
cost lands at merge time.

Sharper than the brief puts it: the check is not a companion to the channel
fix, it is the **precondition** for the channel fix being safe to land.

## What this does not close

- **The two files still carrying `status: retired`** are in
  `precedent-team-repo-maintenance`, a private repo this change cannot reach. Both
  are deduplications and convert cleanly. The new check is what performs that
  migration: it fails them until they are converted, which is the intended
  forcing function — but it means that set goes red on its next engine
  refresh, and its conversion PR should be ready when this lands.
- **Cross-source resolution of `in_force_at:`** is only checkable when every
  declared source is reachable. When one is not, `check_status_contract`
  degrades to the shape check and says so in its own name rather than
  reporting the weaker check as the stronger one.
- **`## Story` is empty on 37 migrated practices** in the private sets — the
  provenance `cite-the-incident` and `mistakes-become-rules` exist to
  preserve. Unrelated to this change and tracked separately.

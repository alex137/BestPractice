---
date: '2026-09-09'
question: |
  `approved_by:` recorded who approved a practice and when, and
  nothing recorded how convinced they were. A proposal the owner
  merely tolerated -- "ok, let's try it" -- landed in the catalogue
  looking exactly like one he had asked for, and every session
  afterwards read both as settled. Should the record carry the
  strength of an approval, on what scale, written by whom, and what
  happens to the approvals already recorded without it?
decision: |
  Two values on the EXISTING approval fields, not a new mechanism:
  a `strength:` frontmatter key on practice files and decision
  records holding `decided` (they asked for it, chose it from
  options, or argued and landed here) or `assented` (proposed to
  them, not objected to). An absent field means UNKNOWN, never
  `decided`, and nothing is backfilled. The session writes the mark,
  and may write `decided` only if it can quote the person choosing
  it -- a bare "ok" to the session's own proposal is `assented`,
  recorded that way without asking. Agreement framed as a test, an
  experiment or a "let's see how it goes" is `assented`; enthusiasm
  ("I love it", "great") or the person doing the choosing is
  `decided`. The mark has consequences: `assented` may be reopened by
  any session on evidence, `decided` is not relitigated, unmarked is
  cited as what the repository records rather than as what the person
  wanted. `Weak yes` is the standing phrase that marks one at the
  moment it is given. Enforced for grammar only by
  `tools/precedent_check.py --only decision-strength`; the substance
  cannot be checked and is not pretended to be.
alternatives: |
  ["A three- or five-level scale of conviction -- rejected as more
  resolution than the evidence supports, and an invitation for a
  session to split hairs about someone's state of mind, which is the
  invention the rule exists to stop",
  "Make `assented` the DEFAULT for an unmarked approval, on the
  precedent of precedent.json's `visibility` field defaulting to the
  unrecoverable-error-safe direction -- rejected because it would
  relabel 90 existing approvals, most of them genuinely wanted, as
  things their owner had shrugged at: an invention in the other
  direction",
  "Make `decided` the default -- rejected outright: that is exactly
  the laundering the rule was raised about, written into the format",
  "Record the strength inline in `approved_by:`'s free text, as a
  handful of practices already did in prose -- rejected because
  decisions/README.md's own standard is frontmatter 'so decisions are
  queryable rather than prose to be grepped', and a distinction that
  only a careful reader can see is the state this replaces",
  "A matching `Strong yes` phrase -- rejected because people already
  argue for what they want; a second phrase would put the marking
  burden on the case that does not need it",
  "Backfill the existing catalogue by reading the threads each
  approval came from -- rejected under no-invented-specifics: those
  threads are mostly gone, and guessing at a past state of mind is
  the specific failure mode that practice names"]
decided_by: Morgan
strength: decided
---

Morgan raised it directly, on 2026-09-09: *"Sometimes in our conversations,
you refer to me having made a decision I made. MANY times, that's only
half-true: it's something you insist on, and I say 'ok' or something similar,
but it's more 'okay claude wants it, let's try it, but I'm not really
convinced, let's see.' I think we should have some way to note if a decision
I make is strong or weak."*

## Why this is a real defect and not a labelling nicety

The repository is built so that a recorded thing binds. That is
[repo-is-memory](../practices/repo-is-memory.md) working as designed: a
session reads `approved_by: Morgan`, treats the rule as settled, and does not
reopen it — because nothing in the file suggests it was ever in doubt.

So the failure is not that the record loses information. It is that the
record **manufactures** information. A weak yes goes in and doctrine comes
out, and the conversion is invisible to everyone downstream, including to the
person who gave the weak yes.

At the time of this decision the catalogue held 90 files carrying
`approved_by:`. Most named him; a handful recorded the manner of approval in
free prose (*"asked for the phrase, chose this one"*), which was a session
being unusually careful rather than a convention anything relied on.

## Why the writer's conflict of interest shapes the rule

The session records whether the person endorsed the session's own idea. That
is the one judgment it cannot be trusted to make generously, and no check can
audit it — nothing mechanical can read the conversation an approval happened
in.

Hence the two asymmetric rules: **quote or downgrade** (write `decided` only
if you can quote them choosing it), and **unsure resolves to `assented`**.
The errors do not cost the same. A wrong `assented` costs one correction, in
a word. A wrong `decided` is never discovered, because what it suppresses is
a question nobody asks.

## Why nothing was backfilled

Every option for populating the existing 90 was a way of inventing something:
guessing per practice, or relabelling all of them at once with a default.
Absence is therefore a third real state — *unknown* — with its own rule about
how it is cited, and the check is deliberately blind to it. The cost is
honest and worth naming: this mechanism cannot distinguish a catalogue that
considered the question from one that has never heard of it.

## What was built

- [practices/decision-strength.md](../practices/decision-strength.md) — the schema, the cue table, and what each mark does.
- [practices/weak-yes.md](../practices/weak-yes.md) — the standing phrase.
- `decision-strength` in [tools/precedent_check.py](../tools/precedent_check.py), with three negative controls in [tools/verify_harness.py](../tools/verify_harness.py) (an invented value, a mark naming no approver, and an unmarked practice that must NOT fail).
- `--strength` on [tools/precedent_land.py](../tools/precedent_land.py), which omits the field rather than defaulting it.
- The field documented in [spec/PRACTICE_FORMAT.md](../spec/PRACTICE_FORMAT.md) and [decisions/README.md](README.md).

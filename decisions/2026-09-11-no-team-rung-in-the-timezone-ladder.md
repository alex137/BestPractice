---
date: '2026-09-11'
question: |
  The zone ladder that decides what offset a commit or a record is
  stamped in resolves the person first, then THIS REPOSITORY's
  declared `fallback_timezone`, then the engine's own last resort.
  A team practice set declares a zone too, and that declaration is
  only ever read when somebody is working inside that set's own
  repository -- step outside it and the team's answer is never
  consulted. Should a team rung be added between the person and the
  repository?
decision: |
  No. The ladder stays as it is: the person, then the repository
  they are committing into, then the engine's default. A repository
  that wants an answer other than America/New_York for a person it
  cannot identify declares one in its own precedent.json, in one
  line, instead of inheriting it from a team. Morgan, 2026-09-11,
  after the rung was costed: "maybe we don't need a team layer.
  Maybe you define it yourself and if not, it's just defined in
  repo-local" -- and, on the ladder as it stands, "let's keep it
  like that."
alternatives: |
  ["A team rung ABOVE the repository's own declaration -- rejected
  because it would let an inherited answer silently override an
  explicit local one. An adopting repository that deliberately
  declares Europe/Berlin would start stamping its team's zone
  instead, with nothing in the output saying a team had been
  consulted at all.",
  "A team rung BELOW the repository's own declaration -- rejected as
  a rung that would almost never be reached. It only answers for a
  repository that declares a team and no fallback of its own, and
  all four sets attached when this was asked declare one: Buenos
  Aires in the individual set, New York in each of the three team
  sets. Measured, not assumed.",
  "Leave the question open in TODO.md -- rejected because the answer
  is cheap and the cost of leaving it is that every session meeting
  the ladder re-derives it. Recording it IS the work."]
decided_by: Morgan
strength: decided
---

## Why this was asked

The ladder lives in two places that must agree —
[tools/precedent_time.py](../tools/precedent_time.py), which every tool that
stamps a date goes through, and
[templates/harness/claude-code/hooks/commit-identity.sh](../templates/harness/claude-code/hooks/commit-identity.sh),
which resolves a committer's zone at session start. The
`timestamps-carry-offset` check asserts the two agree, so a rung is never
added to one of them alone.

Reading the ladder, the repository rung looks like a team rung and is not.
Working inside `precedent-team-writing`, that set's declared zone answers —
because it is the repository you are in, not because it is a team. The same
session working in a project repository never reads it. That asymmetry is
what raised the question.

## What the answer rests on

**A team can never answer the question the ladder is really asking.** The
ladder exists because a record with no offset cannot be ordered against
another record. Every rung above the fallbacks identifies a *person*; the
fallbacks are what a project does when it could not. A team set can say
"records here are stamped in New York", which is a statement about the
repository, and that is precisely what `fallback_timezone` already is.

**The identity half has no ladder at all, deliberately.** Name and email
stop at the individual layer: a workflow or a hook that cannot resolve who
the author is **refuses** rather than falling back, per
[practices/ci-commits-carry-identity.md](../practices/ci-commits-carry-identity.md).
Only the zone continues downward, because a consistent real offset is better
than none while a wrong name is worse than none. A team rung would have
invited the symmetry, and the symmetry is wrong.

**Two teams that disagree would have needed a rule of their own.** A
repository may declare several team sources. Two declaring different zones
has no honest winner, so the rung would have arrived with a conflict rule —
agree and use it, disagree and use neither — which is machinery in service
of a rung that, measured above, nothing would have reached.

## What this does not settle

**The word "repo-local".** In Precedent that names a practice *source level*
— the `local/` directory a repository declares in
[precedent.json](../precedent.json). The zone fallback is not that source:
it is a plain `fallback_timezone` key in the repository's own
`precedent.json`. The two are easy to conflate when describing this decision
out loud, and conflating them points a reader at the wrong file.

---
title:         Moving an existing practice between levels
kind:          procedure
status:        current
opened:        2026-09-03
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Moving an existing, still-wanted practice from one level to another, as distinct from creating or retiring one.
---
# Moving an existing practice between levels

[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s Stage 3–5 describe
how a **new** practice is created at a chosen level, and Stage 6 describes
**removing** one that's stopped earning its place. Neither describes what to
do with a practice that already exists, is still worth keeping, but belongs
somewhere else — a team practice that turns out to be one person's own
preference, or an individual habit a whole team has since adopted. This gap
was real, not hypothetical: `precedent-team-repo-maintenance`' bulk migration
from RepoPersonalPreferences defaulted everything ambiguous to team
("narrowest first" among the two private levels), and at least one of those
defaults was wrong on reflection — see "Worked example" below.

## When this applies

A practice is `status: active` at one level, and belongs at a different one
instead — not because it stopped being worth having, but because the wrong
audience is bound by it (or, moving the other direction, too narrow an
audience). This is distinct from:
- **Creating** a genuinely new practice (Stage 2–5) — nothing here already
  exists to move.
- **Retiring** a practice outright (Stage 6) — nobody wants it anywhere
  anymore.
- **Promoting a team practice to universal**, which
  [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) and
  [spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md) already name as "a
  designed path" — the pattern below is the general form of that same move,
  spelled out for the directions those documents don't cover (team ↔
  individual, team ↔ a different team).

## The pattern

There is no single tool for this — it's two existing operations, run in
sequence, never as a silent file edit or a copy-and-delete:

1. **Land it at the destination, through that level's own creation
   approval**, exactly as if it were new (Stage 4). Use the existing
   practice's `## Rule`, `## Detail`, `## Why`, and any real `## Story` as
   the candidate's content — this is carrying forward real, already-vetted
   text, not re-deriving it from scratch. **If the `## Story` is empty,
   fill it before landing, not after**: a move is the last moment the
   original context is reliably in front of somebody, and
   [catalogue-carries-stories](../practices/catalogue-carries-stories.md)
   will hold the destination red until it is filled anyway. The destination's own owner has
   to actually agree it belongs there:
   - **To an individual set**: the person's own *"yes"* — `precedent_land.py --level individual --approved-by NAME`, direct.
   - **To a team set**: a listed approver of *that* team's own say-so —
     `precedent_land.py --level team --approved-by NAME`, or
     `precedent_candidate.py create --level team --as-issue true` first if
     whoever's proposing it isn't one
     ([spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md#which-one-for-team-file-or-issue)).
   - **To universal**: a pull request (PR) to Precedent, reviewed and merged
     by someone other than whoever proposed it — same as any new universal
     practice.
2. **Deduplicate it at the source, through that level's own removal
   approval** (Stage 6's table) — **never** a plain delete, and never done as
   a side effect of step 1. Set `status: deduplicated` and
   `in_force_at: <the slug you just landed>`, and add one line to `## Story`
   naming where it went and why:
   - **Individual**: the owner's own *"yes, drop the copy"*.
   - **Team**: an approver's review, through the same `approvers.json`
     mechanism as any other change to that set — even when the destination
     is the *same person's own* individual set, because removing something
     from a team's binding set is still a change to what the whole team is
     bound by, not just a personal preference about where the rule lives.
   - **Universal**: a PR, same as any universal change.

**This step is a deduplication, not a retirement, and the distinction is the
whole safety property of the move.** The rule is not being withdrawn — it is
fully in force, from the source step 1 just landed it in. Only the redundant
copy goes away. `status: retired` means something else entirely (nobody wants
this rule anywhere) and would be a false record here; it also demands
`in_force_at: none`, which this move can never honestly supply. See
[PRACTICE_FORMAT.md](PRACTICE_FORMAT.md#status) for the two statuses and the
evidence each requires.

**Order matters in one direction only:** land first, deduplicate second. A
practice dropped before it lands anywhere leaves a gap — however brief —
where nobody is bound by a rule everyone still agrees is worth having.

**That ordering is also what makes the second step verifiable, and it is why
this document survives the rename almost unchanged.** Landing first means a
correct move passes through a deliberate moment of duplication, so by the
time step 2 runs there genuinely *is* a surviving copy to point
`in_force_at:` at — and the check can resolve it against the real sources
rather than taking the mover's word for it. A move done in the other order
has nothing to name, which is precisely the state a lost rule is in.

## The asymmetry that already exists, and the one that doesn't

[spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md) and
`precedent-team-repo-maintenance`' own README already name one real asymmetry:
**promoting team to universal is comparatively easy and a designed path;
demoting a universal practice is not**, because undoing something already
published to every Precedent user is a far bigger, more visible change than
adding one team never had before. That caution is specific to universal as
the destination or source — it does not generalize to every move.

**A team ↔ individual move, or a move between two teams, carries none of
that weight.** It affects exactly the sets on both ends, whose own
approvers already have to sign off under the pattern above — there is no
larger, already-depending audience to disturb the way a universal change
has. Treat it as an ordinary two-step move, not as something needing
universal's extra caution just because it crosses a level boundary.

## Worked example: `bestpractice-sync`, team → individual

**The practice itself was retired on 2026-09-11** — Morgan, on an
unattended self-merging sync being the wrong bet against a layer this
size. The example below is kept as what it always was: a record of how a
two-step move is done, which does not depend on the moved rule still
being in force. Note that it moved once more after this, team-ward, in
the 2026-09-09 subject split.

`bestpractice-sync` — the practice describing an unattended, scheduled
workflow that takes upstream BestPractice updates into a vendored copy —
was migrated to `precedent-team-repo-maintenance` in the original RepoPersonalPreferences
split, by the same "default everything ambiguous to team" rule that
migration used throughout. On reflection it was the wrong default: it is a
personal automation preference about how *one person's own* projects handle
unattended merges, not a convention the whole team is bound to want —
`precedent-team-repo-maintenance`' own two-approver membership means adopting it
as team policy would apply it to a second person's repos without their own
separate agreement to that specific behavior, which is exactly the kind of
default the same README already flags as "not a final judgment."

Landed in `precedent-individual` (step 1, the owner's own yes), then the
team's copy deduplicated
in `precedent-team-repo-maintenance` (step 2, an approver's own yes — the same
person, since a small team's approver landing directly collapses both
into one "yes," same as Stage 4 already allows for ordinary creation) with a
`## Story` line pointing to its new location. Nothing about the pattern
above assumes this direction only — the same two steps, reversed, move a
practice from individual back out to a team, exactly as the note on
`bestpractice-sync`'s own new file names as a real, expected possibility.

## What this does not give you

No tool automates the land-then-deduplicate sequence above the way
`precedent_land.py` automates candidate → landed practice for a genuinely
new one. Composing the two steps by hand is what this document is for;
building a dedicated `precedent_move.py` that does both atomically, and
enforces the ordering, is real future work this move surfaced but did not
attempt — the same call [spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)
already made for its own "known gap," naming the work plainly rather than
scope-creeping it into an unrelated change.

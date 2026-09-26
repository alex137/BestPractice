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

[PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s Stage 3–5 describe
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
  [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) and
  [spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md) already name as "a
  designed path" — the pattern below is the general form of that same move,
  spelled out for the directions those documents don't cover (team ↔
  individual, team ↔ a different team).

## The pattern

**A move carries everything the practice owns, in one commit at the
destination:** the practice file, its `checked_by` script, that script's
test, and every file its `ships:` field declares
([practice-carries-its-files](../practices/practice-carries-its-files.md)).
Copy the files first; the tool refuses until they are there, and the
destination's own push check refuses a practice whose declared files are
missing. Leaving the source's copies in place is fine until the
deduplication step, since the deduplicated practice no longer ships them.

**Since 2026-09-14 one tool does both steps, in the one safe order.** Run
it from a checkout of Precedent — the sets and the consuming repositories
do not vendor it, and the paths are the sets':

```
python3 tools/precedent_move.py --slug <slug> \
    --from individual|team --from-path <the set it lives in> \
    --to individual|team|universal --to-path <the set or Precedent clone> \
    --approved-by "<name>" [--strength decided|assented] [--story "<text>"]
```

It lands the practice at the destination with its Rule, Detail, Why and
Story carried verbatim and the destination's approval recorded -- except
for a link to a sibling practice that is not at the destination, which it
re-homes and prints: a universal practice gets its universal URL, anything
else its slug in backticks, never a URL into another set (which may be
private) -- then
deduplicates the source copy (`status: deduplicated`, `in_force_at:` the
slug, one dated `## Story` line), and regenerates both sets' views. It
refuses an empty Story (`--story` fills it), a slug the destination already
carries, an approver not listed in a team set's `approvers.json`, a
`checked_by` naming a check the destination cannot run, a `ships:` file the
destination does not carry yet, and `--dedupe-only`
on a practice moving *out of* universal without `--accept-reach-loss` also
given (below). **With `--to universal` it drafts only** — the file goes
into the clone's `practices/`, the clone's own [`build_views.py`](../tools/build_views.py) and
`doc_sync.py --write` run so its deep check is green on the draft, and the
source stays active. Commit that on a branch and open the pull request.
**Run it again with `--dedupe-only` only once the pull request has merged
AND every repository consuming the source set has taken the new universal
catalogue** ([INSTALL.md](../INSTALL.md) §2 step 0, or `Update Vendors`):
a consumer still vendoring the old catalogue sees the rule in neither
source, and its next [`precedent_sync_views.py`](../tools/precedent_sync_views.py) refuses to write until it is
refreshed. That refusal is correct and is what you will see if you
deduplicate early.

**With `--from universal` the tool now runs, added 2026-09-23** — this
was the one direction it refused outright until this incident showed why
a blanket refusal helped nobody. **It lands like any other move, but does
not deduplicate the source**: the universal copy stays `status: active`,
unchanged, with a `## Story` line saying it also now lives at the
destination. This is not caution for its own sake — it is the only
correct behavior, given what a deduplicated pointer means to
[`precedent_sync_views.py`](../tools/precedent_sync_views.py). A team or
individual destination is not resolvable by a plain, universal-only
consumer, which is most of them; that tool treats an `in_force_at` that
does not resolve as a hard failure (`IN FORCE NOWHERE`), not an advisory,
so deduplicating the universal copy at this point would break that
consumer's own sync, not just mislead a reader.
Both copies are genuinely in force at once, on purpose, until a human
decides otherwise.

**Withdraw the universal copy later, deliberately, with `--dedupe-only
--accept-reach-loss`.** The flag is required on that run and refused
without it: the moment it runs, a consumer that resolves only universal
loses the rule entirely, and nothing the tool can measure says whether the
audience that still needs it has moved to the destination set. That is a
human call, the same shape [`go-merge`](https://github.com/alex137/BestPractice/blob/staging/practices/go-merge.md)
already asks for on anything hard to reverse — say the read out loud and
confirm it, rather than letting a flag default to "yes."

Found the hard way, 2026-09-23: two practices were moved out of universal
by hand, following this page's own two-step pattern before this tool
supported the direction. Every fast check passed and both copies were
pushed; only `verify_harness.py --as-ci`'s consumer-fixture check, run
hours later, found the deduplicated copy resolving nowhere for a plain
consumer — the downstream repo that had originally contributed one of the
two practices, among others. Both were reverted the same day. This
capability, and the `--accept-reach-loss` flag specifically, exist so the
next demotion is either safe by construction or explicitly, knowingly
risky — never silently broken the way a hand-done one was.

Morgan, 2026-09-14, on why this stopped being two hand steps: he had "had
bumps doing that". A rehearsal the same day, by a session reading only the
previous version of this page, found why: the candidate tool takes one
`--proposed-rule` string, so an existing file's `## Detail`, `## Why` and
`index_clause` never had a way in and were restored by hand after landing;
a moved practice has a recurrence of one, so the promotion refused it
until a `--cost-if-once` was invented; an honest `--against` naming the
source set refused the landing as a duplicate; and no tool wrote the
deduplication, so it was done from memory or not at all. Its fixture in
[tools/verify_harness.py](../tools/verify_harness.py) moves a practice
through every direction on every harness run, and rehearses the
copy-and-delete below.

**What the tool does, step by step** — the two operations below, which
are still the definition of a correct move and what a session checks a
hand-done one against:

1. **Land it at the destination, through that level's own creation
   approval**, exactly as if it were new (Stage 4). Use the existing
   practice's `## Rule`, `## Detail`, `## Why`, and any real `## Story` as
   the candidate's content — this is carrying forward real, already-vetted
   text, not re-deriving it from scratch. **If the `## Story` is empty,
   fill it before landing, not after**: a move is the last moment the
   original context is reliably in front of somebody, and
   [catalogue-carries-stories](../practices/catalogue-carries-stories.md)
   will hold the destination red until it is filled anyway. The destination's own owner has
   to actually agree it belongs there, and the tool records that agreement
   in the landed file's `approved_by:`:
   - **To an individual set**: the person's own *"yes"* — `--approved-by`
     their name, direct.
   - **To a team set**: a listed approver of *that* team's own say-so —
     `--approved-by` a name in that set's `approvers.json`, which the tool
     checks. Someone who is not one raises it first, as an Issue on the
     team set ([spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md#which-one-for-team-file-or-issue));
     the approver then runs the tool. **The creation pipeline
     ([`precedent_candidate.py`](../tools/precedent_candidate.py), [`precedent_land.py`](../tools/precedent_land.py)) is not the way to
     move an existing practice**: it carries a rule and an observation,
     not a file, and the rehearsal above lists what it drops.
   - **To universal**: a pull request (PR) against `precedent-beta-v01`,
     merged once its own deep check passes — no second sign-off required,
     same as any other PR into that branch
     ([merge-target-is-beta-branch](../local/practices/merge-target-is-beta-branch.md))
     and same as any new universal practice. The tool drafts the file; the
     merge is the approval.
2. **Deduplicate it at the source, through that level's own removal
   approval** (Stage 6's table) — **never** a plain delete, and never done as
   a side effect of step 1. Set `status: deduplicated` and
   `in_force_at: <the slug you just landed>`, and add one line to `## Story`
   naming where it went and why:
   - **Individual**: the owner's own *"yes, drop the copy"*.
   - **Team**: an approver's review, as for any other change to that set —
     even when the destination is the *same person's own* individual set,
     because removing something from a team's binding set is still a
     change to what the whole team is bound by, not just a personal
     preference about where the rule lives. Nothing mechanical records who
     approved a removal: the tool writes the approver's name into the
     `## Story` line it appends, and a hand-done one writes the same line.
   - **Universal**: a PR, same as any universal change.

   Done by hand, step 2 is a three-line edit of the source file — the two
   frontmatter fields and the Story line — and nothing else. No tool other
   than [`precedent_move.py`](../tools/precedent_move.py) writes it: [`precedent_retire.py`](../tools/precedent_retire.py) only reports,
   and [`precedent_migrate_status.py`](../tools/precedent_migrate_status.py) refuses an active practice.

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
`in_force_at:` at — and the resolver checks that it resolves, against the
real sources, rather than taking the mover's word for it. A move done in
the other order has nothing to name, which is precisely the state a lost
rule is in.

**Who checks what, since 2026-09-14** — before that day only Precedent's
own harness asked whether a forwarding address resolved, so for the
team ↔ individual directions this page exists for, the property was
asserted here and verified nowhere a set or a consumer could run:

- [`precedent_resolve.py`](../tools/precedent_resolve.py) reports `IN FORCE NOWHERE: <slug> (<source>)` for
  a deduplicated practice whose `in_force_at:` names a slug that no
  resolved source has active. [`precedent_sync_views.py`](../tools/precedent_sync_views.py) prints the same
  line, on `--check` and on a write.
- [`precedent_sync_views.py`](../tools/precedent_sync_views.py) also names a **copy-and-delete**: a slug the
  consumer's committed `MANIFEST.json` recorded from one declared source,
  now taken from another, with nothing left at the first — neither an
  active copy (which the resolver reports as overridden) nor a deduplicated
  one. A warning, not a refusal: the rule is in force; what is missing is
  the record saying it left, which is the thing a session reading the old
  set will look for.
- Neither catches a rule that was withdrawn at the source and landed
  nowhere at all, when the consumer never recorded it — the MANIFEST guard
  is the baseline, and a fresh install has none.

## The asymmetry that already exists, and the one that doesn't

[spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md) and
`precedent-team-repo-maintenance`' own README already name one real asymmetry:
**promoting team to universal is comparatively easy and a designed path;
demoting a universal practice is not**, because undoing something already
published to every Precedent user is a far bigger, more visible change than
adding one team never had before. That caution is specific to universal as
the destination or source — it does not generalize to every move. Since
2026-09-23 the tool *runs* a demotion out of universal, but the caution is
still there, moved rather than removed: the mechanical landing is safe by
default (duplicate, not deduplicate — above), and the one genuinely
irreversible-for-most-adopters step, actually withdrawing the universal
copy, still needs an explicit human `--accept-reach-loss`, not a flag a
script can default to yes.

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

Until 2026-09-14 this section said no tool automated the two steps and
named a [`precedent_move.py`](../tools/precedent_move.py) as future work; it exists now (above). What
still stays by hand: a `checked_by` practice's check script and test, and
every file it declares in `ships:`, are copied to the destination before the
practice lands (the tool refuses until they have), a move
between two sets this session cannot both write to is two sessions'
work, and committing and publishing each set is the owner's act — the
tool writes files and regenerates views, and nothing else.

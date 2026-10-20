---
title:         A set exports only its own rules
kind:          reference
status:        current
opened:        2026-10-19
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "A repository that had Precedent installed like a project kept every other source's practices in the practices/ folder a set's consumers read as its own. The resolver now leaves an install's copies out, the install step refuses to write into a set, and Update Vendors' copy-in refuses a set that holds copies."
---

# A set exports only its own rules

On 2026-10-19 Morgan found that a shared practice set, the one that holds
the rules for writing so a text does not read as machine-written, had 209
copies of other sources' practices in its `practices/` folder: the
universal rules, the writing set's, and Morgan's own individual rules. The
set's real deliverable was one rule and its checker, and that rule was not
even written there. A session cleaned it by hand that day. This report is
about why it could happen, why the hand cleanup did not stop it happening
again, and what now does.

## What happened

1. **2026-08-17.** The repository was set up as an ordinary project and the
   pre-Precedent practice layer was installed into it. At the time nobody
   thought of it as a set; it was a document other repositories copied.
2. **2026-09-10.** It was migrated onto Precedent the way every project
   was: `precedent.json` declared the universal source and the shared sets,
   and the install step ([precedent_sync_views.py](../tools/precedent_sync_views.py), which runs
   [precedent_materialize.py](../tools/precedent_materialize.py)) wrote every resolved practice into its
   `practices/`. 139 of them.
3. **Every Update Vendors after that** refreshed the copies. By October
   there were 209.
4. **Its own rule lived somewhere else.** The checker that holds a session
   to the writing rules was written in Morgan's individual set and
   delivered back into the repository it is about, where the push check
   then refused an edit to it.
5. **2026-10-19.** Morgan: "IT SHOULD ONLY BE THE RULES JUST ON HOW TO
   SOUND HUMAN", and decided it should be a practice set. A session
   deleted the copies, the vendored catalogue and the project engine, added
   `precedent-source.json`, and moved the rule in.

Nothing in the engine changed in step 5. Two runs against a clone of the
cleaned-up set, with the engine as it stood that evening, showed the hole
was still open:

- **The install step refilled it.** `precedent_sync_views.py --repo <the
  set>` reported OK and wrote 198 copies back into its `practices/`, and
  rewrote the set's own rule with an older copy of it from the individual
  set.
- **The resolver would have handed them out.** A repository declaring the
  universal source and that refilled set resolved 170 universal rules as
  "replaced" by the set's frozen copies, and Morgan's individual rules came
  out as the set's, at shared level: anyone who declared the set would have
  been bound by them. Shared is the strongest level (`PRECEDENCE` in
  [tools/precedent_resolve.py](../tools/precedent_resolve.py)), so every
  copy also outranked the live rule it was copied from and froze it at the
  day of the copy.

Before 2026-10-19 the set had no `precedent-source.json` and nobody
declared it, so the copies bound nobody but its own sessions. The damage
was waiting for the day it became a set, which was the day it was found.

## Why it was possible

**One folder means two things.** In a set, `practices/` holds the rules
the set writes, and `load_source()` reads every file there as the set's
own. In a project, the install step writes every resolved practice into
`practices/`, in the same format, under the same names, with nothing in
the file saying it is a copy. The only record of which file came from
where is the `MANIFEST.json` the install writes beside it, and nothing
that reads a set looked at it.

The engine already knew this bug in one form. `_self_referential_sources`
in [tools/precedent_materialize.py](../tools/precedent_materialize.py)
refuses a run whose output folder is also a declared source, and its own
comment names the failure: a file the install writes "for a DIFFERENT
source is read back on the next run as if this source had authored it".
That guard covers one repository declaring itself. This case is the same
bug across two: one repository's install output, later read as another
repository's source.

More of these are coming. Sets are now copied into the repositories that
use them ([VENDORED_SHARED_SETS.md](VENDORED_SHARED_SETS.md)), voice packs
are sets that live inside repositories with their own installs, and a
repository can start life as a project and become a set, as this one did.

## Options weighed

**A. Clean it by hand and write it down.** Done on 2026-10-19. The two
runs above show it did not hold: the next install, or the next person to
declare such a repository, brings it back. Rejected.

**B. A check that finds copies in a set.** It would catch the problem after
it happened, and only when someone runs it: sets run no CI, so it fires
only on a full sweep. A check is the backstop for the part that cannot be
removed, and most of this can be. Kept for the one gap below, not built.

**C. Move every project's copies out of `practices/`** (into `.precedent/`
or `process/`), so the folder means one thing everywhere. This is the
cleanest end state. It costs a layout change in every consuming
repository, every tool that reads a project's `practices/`, every link
AGENTS.md, MAP.md and the practices themselves make into it, and a
migration through Update Vendors everywhere. Not rejected: it is the
answer if the gap below ever bites. Deferred, because D and E close the
real paths without it.

**D. Stamp each copy** with a `copied_from:` line in its frontmatter. This
covers a copy whose `MANIFEST.json` went missing. It changes every file in
every project on the next Update Vendors, and still misses a copy made by
hand from the original, which carries no stamp. Rejected in favour of the
two rules below, which cover the same cases with no churn.

**E. The resolver reads only what a set writes, and the two writers refuse
to put copies there.** Chosen. In detail:

1. **A copy an install recorded is never the set's rule.**
   `installed_copies()` reads the `MANIFEST.json` the install step leaves
   at the root of every tree it writes, and `load_source()` leaves out
   every practice it records from another source, stale or not.
2. **A byte-for-byte copy is not an override.** When a stronger source's
   practice is identical to the weaker one it would replace, the resolver
   keeps the original in force and lists the copy. That covers a copy with
   no manifest, or one made by hand.
3. **The install step refuses a set.** `_materialize()` refuses to write
   into any folder with a `precedent-source.json` at its root, before it
   touches anything. A set's views come from its own [build_views.py](../tools/build_views.py),
   which already defers every declared source to
   the session's untracked practices file.
4. **Copy-in refuses a set that holds copies.** `checkin.py --source`,
   Update Vendors' copy of a set into a repository, stops on a set whose
   `MANIFEST.json` records copies, so a polluted set never reaches
   `process/<set>/` in anyone's repository.
5. **It says so.** Every resolve and every sync that left copies out prints
   one line naming the set, how many, where they came from and what to
   delete.
6. **The tool that makes a set checks for them.**
   `precedent_bootstrap_source.py --verify`, the set-shape check, fails a
   set whose `practices/` holds an install's copies and names what to
   delete. That is the path this set took on 2026-10-19: it was turned
   into a set by that tool, and the copies were removed by hand because
   nothing said they were there.

## Attacking the chosen fix

- **Could it drop a real override?** Only an identical one, and an
  identical override changes nothing. A set that writes its own text under
  a universal slug still replaces it; the test's negative control checks
  exactly that.
- **A project declared as a source.** Its `MANIFEST.json` lists its own
  repository-local rules as copies too (they are copies, of `local/`), so
  they are left out. That is the conservative answer: a repository that
  uses Precedent and also holds a set keeps the set in a folder of its own
  (`set_root`, in [VENDORED_SHARED_SETS.md](VENDORED_SHARED_SETS.md)).
- **A repository that becomes a set while holding copies.** The leftovers
  bind nobody, the resolver names them on every run, the install step
  refuses to add more, and copy-in refuses to spread them.
- **False alarms in what exists today.** Resolved before and after the
  change in BestPractice, a voice repository, the cleaned-up set, the
  individual set and two shared sets: the same practice counts in every
  one, and no copies reported.
- **BestPractice itself** has a `precedent-source.json` and is never
  installed into, so the new refusal never meets it.
- **The gap.** A copy made by hand, with no manifest, that has since been
  edited or gone stale, looks exactly like a real override, and nothing
  here can tell them apart. It still prints as "overridden: X -- shared
  replaces universal" on every resolve. If it ever happens, option C is
  the fix that closes it, and B the check that finds it.
- **Closing the gap by requiring `overrides:` on every same-name override
  was tried and backed out.** The idea was that a rule may replace another
  source's rule of the same name only when it says `overrides: <its slug>`,
  so an unmarked one would read as a copy. On 2026-10-19 it would have
  changed nothing in force: every active override in every source in use
  already named a different slug in `overrides:`, and every pair of rules
  sharing a name was a forwarding stub beside the rule it points at. But
  "the same name at a stronger level wins" is the precedence rule
  [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) is built on, and
  `check_source_precedence` tests it case by case from that plan. Changing
  the plan's core rule to close a gap no path reaches today is a decision
  for Morgan or Alex, not a fix to land while they are away. If they want
  it, the change is small: the resolver check, the plan's precedence
  paragraph, and `overrides:` added to that test's fixtures.

## Where it lives

| Part | Where |
|---|---|
| Copies an install recorded are left out | `installed_copies`, `load_source` in [tools/precedent_resolve.py](../tools/precedent_resolve.py) |
| Identical copies stay out of force; the note | `resolve`, `copies_note` in [tools/precedent_resolve.py](../tools/precedent_resolve.py); printed by [tools/precedent_sync_views.py](../tools/precedent_sync_views.py) |
| The install step refuses a set | `_materialize` in [tools/precedent_materialize.py](../tools/precedent_materialize.py) |
| Copy-in refuses a set holding copies | `_refuse_set_holding_copies` in [tools/checkin.py](../tools/checkin.py) |
| The set-shape check reports them | `_malformed` in [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py) |
| The test, with its negative control | `check_a_set_exports_only_its_own_rules` in [tools/verify_harness.py](../tools/verify_harness.py) |

## Rollout

This is engine code, so it reaches each repository and each set the next
time Update Vendors refreshes its engine; nothing in their content changes.
No repository needs anything else done: none holds copies today, and the
one that did was cleaned on 2026-10-19.

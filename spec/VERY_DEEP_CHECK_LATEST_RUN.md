---
title:         Very Deep Check, 2026-10-11 — What It Found and What Was Done
kind:          record
status:        closed
opened:        2026-10-11
closed:        2026-10-11
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The full account of the most recent very deep check: what it read, what each pass found, what was fixed and where, and what is left for a person. The next run rewrites it; git history keeps this one."
---
# Very Deep Check, 2026-10-11 — What It Found and What Was Done

The full record of the latest run (the next run rewrites this file; git
history keeps each earlier one). The ledger of every run is
[VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md); this is the long form behind its
"Current run" row.

**Scope, as Morgan set it:** "In best practice only (not in all attached
repos)". BestPractice and the sets it declares (the individual set, the
writing set, the ladder set) were read; the consuming repositories attached
to the same session were not checked, though the tool's fleet sections
reached them read-only. All four passes, on `main` at a6209a6c. The tool
took about eight minutes; the whole run about 35, 07:22 to 07:56 Buenos
Aires time, with four agents working in parallel in scratch directories.

**One thing went wrong during the run, and it is part of the record.** An
install rehearsal ran a scratch repository's bootstrap with no identity,
and the commit-identity hook moved this machine's clock from Buenos Aires
to the declared fallback zone. The agent put it back within the minute;
the commits made in that window carry the right offset because each was
made with the zone named. The cause was a real bug and is fixed below.

## The Short Version

- **Eleven fixes in BestPractice, each with a planted case that fails
  without it**, landed on `staging` in
  [3c0db6b](https://github.com/alex137/BestPractice/commit/3c0db6b5) and
  [6ca0287](https://github.com/alex137/BestPractice/commit/6ca0287a).
- **Install documents brought in line with the installer**: INSTALL.md,
  SETUP.md, the migration guide and seven templates.
- **The full harness ran green on `main` before any change** (`--all`,
  four shards, 0 failed).
- **Morgan's four calls were answered the same day** (below), and the
  upstream review he asked for on 2026-09-30 was rebuilt.
- **What is left** is in
  [todo-2026-10-11-very-deep-check-findings](../todo/todo-2026-10-11-very-deep-check-findings.md).

## Pass 1 — Can an Adopter Install and Update?

Five rehearsals by agents with no prior context, each in scratch with local
bare origins: the guided install (SETUP.md, as a non-technical
administrator), the developer install (INSTALL.md section 0), an update from
a week-old commit, a migration from the classic layout, and practice moves
between levels. About 45 findings. Fixed:

- **A new install by someone off pre-staging started on pre-staging** and
  pushed that branch to origin. One function now picks a new repository's
  landing branch, and no pre-staging is made for an install that lands on
  staging ([d139a78](https://github.com/alex137/BestPractice/commit/d139a78e)).
- **A guessed timezone moved a clock someone had already set**: the
  fallback now replaces only the container's +0000
  ([d766eba](https://github.com/alex137/BestPractice/commit/d766ebaf)).
- **A fresh install had no catalogue sync record**, so every session start
  said NOT VERIFIED and called the catalogue absent
  ([971c855](https://github.com/alex137/BestPractice/commit/971c8550)).
- **`--admin` was taken and ignored** when GitHub could not list who can
  edit ([6df7614](https://github.com/alex137/BestPractice/commit/6df7614e)).
- **A newly bootstrapped private set could not push**: the leak gate read
  visibility from precedent.json only
  ([b0da037](https://github.com/alex137/BestPractice/commit/b0da0378)).
- **The migration guide said to declare a deleted set**, and the install
  documents contradicted the installer on MAP and GLOSSARY, the deep
  check's name, and retired section numbers
  ([24ae803](https://github.com/alex137/BestPractice/commit/24ae8030),
  [bdfc1b5](https://github.com/alex137/BestPractice/commit/bdfc1b5c),
  [b08dda0](https://github.com/alex137/BestPractice/commit/b08dda04)).

## Pass 2 — Do the Mechanisms Do What They Claim?

The tool's own sections were read against the tree, and five of them were
wrong about themselves:

- **It told the reader to sync 66 commits into a retired pre-staging**,
  treating it as a tier
  ([85426d9](https://github.com/alex137/BestPractice/commit/85426d9a)).
- **It reported its own output files as somebody's lost work**
  ([35ad02c](https://github.com/alex137/BestPractice/commit/35ad02cf)).
- **It ran over its GitHub API budget twice**: the fleet audit asked about
  two deleted sets, and the visibility audit read "owner/name." and
  `api.github.com/repos/X` as extra repositories. Both fixed; the remaining
  growth is real, so both budgets moved with the measurement beside them
  ([bdbde35](https://github.com/alex137/BestPractice/commit/bdbde357)).
- **It flagged four code-owner commands as missing from the vocabulary
  page**, which leaves them out by decision
  ([cccbed5](https://github.com/alex137/BestPractice/commit/cccbed50)).

Tried and taken back: exempting the dated record directories from the
writing set's stale-count check. The push check refused an exemption with
no root fix, rightly; the fix belongs to that check
([73bb9dd](https://github.com/alex137/BestPractice/commit/73bb9dd1)).

## Pass 3 — Does the Writing Hold Together?

Four reader-facing documents were registered for currency, two dead links
to a practice that moved to the ladder set were repointed, and the root
`TODO.md` stub was read end to end: it states two things that stopped being
true and cannot be changed, since a change to it is refused.

## Pass 4 — Catalogue, Backlog, Branches

- **Eight unlanded branches judged.** Five were recommended for deletion on
  the review page (superseded on `main` another way); three went to Morgan.
- **Thirty practice pairs that read alike were judged; all thirty kept**,
  each with its reason on the review page.
- **The review page was published to Morgan privately**, never committed.
- **Four reminders are more than a week past due**, and the temporary rule
  about the two retired sets has half met its end: no repository declares
  them; both still need archiving on GitHub.

## Morgan's Calls, Answered 2026-10-11

"Both yml are fine and approved. On Alex's fix: approved. On my idea of
writing up a prompt in the boildown session with the errors and warnings
given - yes let's rebuild it but only in ladders and also only when the
user is a code owner. And on the July one: close it".

- Both workflows pinned to their content
  ([193ce63](https://github.com/alex137/BestPractice/commit/193ce63c)).
- Alex's `upstream-bug-stops-here` amendment landed with him as author
  ([89af07c](https://github.com/alex137/BestPractice/commit/89af07c2),
  [7194194](https://github.com/alex137/BestPractice/commit/71941948)).
- The upstream review rebuilt: the engine half here
  ([45a007d](https://github.com/alex137/BestPractice/commit/45a007da)), the
  practice in the ladder set, for code owners on the ladder only.
- The July `share/` spec branch: Morgan deletes it from its link.

## What Is Left

Everything not fixed, with where its fix lives, is in
[todo-2026-10-11-very-deep-check-findings](../todo/todo-2026-10-11-very-deep-check-findings.md):
the writing set's stale-count check, the shared sets' old bootstrap hook,
updates that stop on untouched template text, the migration and move
guides, and a few install gaps that need a design call.

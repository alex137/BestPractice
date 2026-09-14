---
slug:        philosophy-is-not-repo-policy
title:       The philosophy tree is argument, never a rule that binds this repository
tier:        on-demand
severity:    blocking
applies_to:  ["philosophy/**"]
occasion:    "writing or editing anything under philosophy/, or citing it from a rule"
gates:       ["review"]
index_clause: "philosophy/ is argument; a rule that earned its way out gets written as a practice file"
checked_by:  "tools/checks/check_philosophy_is_not_repo_policy.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "Morgan, 2026-09-07, as the condition that repository's content was brought in under"
---
## Rule
Everything under `philosophy/` is **theory, argument and observation** —
the reasoning Precedent is built on. None of it binds work anywhere in
this repository, including inside `philosophy/` itself.

Two things follow, and both are checked:

1. **No practice's `## Rule` may cite a `philosophy/` path as its
   authority**, and no practice's `checked_by` may point at a script under
   `philosophy/`. A rule that has genuinely earned its way out of the
   essays gets *written as a practice file* in the source it belongs to —
   `practices/` for a generic rule, a team or individual source for one
   specific to a group or a person. Citing an essay in place of doing that
   makes prose into policy nobody approved.
2. **No practice in the exported catalogue (`practices/`) may name
   `philosophy` in its `applies_to`.** A rule about this repository's own
   philosophy directory is repo-local by construction — it lives in
   `local/practices/`, like this one — and must never ship to a consuming
   repository that has no such directory.

Citing an essay to *explain* something is fine and expected: a practice's
`## Why` or `## Story` may point at `philosophy/` all it likes. The line
is between explaining a rule and being one.

## Detail
The check reads every practice file in `practices/` and
`local/practices/`, slices out the `## Rule` section, and looks for a
`philosophy/` path in it. It deliberately does **not** scan `## Why`,
`## Story`, `## Detail` or `## Install` — those are where an essay
citation belongs, and flagging them would teach the next session to route
around the gate rather than respect it.

It does not try to detect imperative prose inside `philosophy/` itself.
That was attempted first and abandoned: these essays are *full* of
legitimate imperatives ("Argue a genuine counter-case before building on a
stated stance"), because arguing for a way of working means writing in the
imperative. A check firing on correct work is worse than no check —
`checkable-gets-checked` says so directly — so the enforced property is
the one that has no false positives: what a *rule* is allowed to lean on.

## Why
The material under `philosophy/` arrived from another repository, where it
governed that repository's own writing. Copied here without a boundary, it
would quietly acquire authority it was never given: 22,000 lines of
strongly-argued prose sitting one directory above a practice catalogue,
with nothing saying which of the two a session is supposed to obey.

The asymmetry matters. An essay can be wrong, half-finished, or actively
under argument — [RULES_NOW_TESTING.md](../../philosophy/RULES_NOW_TESTING.md) tags its own entries *Trial* — and
that is fine, because an essay is a claim. A practice is a commitment the
repository's checks enforce. Collapsing the two costs the essays their
freedom to be provisional and costs the catalogue its meaning.

## Story
Recorded 2026-09-07, at the moment the risk was created rather than after
it fired — the one case `cite-the-incident` accepts a prospective story
for, because the incident is the change itself.

that repository's `content/` tree was copied into this repository's
`philosophy/`. In its home repository that material is not inert: its
[RULES_NOW_TESTING.md](../../philosophy/RULES_NOW_TESTING.md) is explicitly "the checklist a session in any of
Morgan's real work is expected to follow today", and that repository's own instructions file
named five of these documents as durable rule lists cited by slug from
elsewhere. It reads, correctly for that repository, as instructions.

The person asking for the copy said the condition out loud and first:
these "may not be general rules applying to the rest of the repo." Without
a mechanism that is a sentence in a commit message, and the sentence stops
being read about four sessions later — the exact failure
`repo-is-memory` and `checkable-gets-checked` exist to prevent. The
mechanism is this practice plus its check.

the project's own prior notes repository was retired later the same day, which removes
the *source* of the risk without removing the risk itself: these essays
are still 22,000 lines of confident, imperative prose sitting one
directory from a practice catalogue, and now with no other home to point
back at. The boundary matters more once this is the only copy, not less.

The second clause has its own reason, learned from
`merge-target-is-beta-branch` twelve lines up the same directory: a check
about *this* repository's temporary local situation, filed in the exported
catalogue, becomes a permanent unfixable violation in every consuming
repository that installs it. A `philosophy/`-scoped practice in
`practices/` would do exactly that, in a repository that has no
`philosophy/` at all.

## Install
Enforced by
[../tools/checks/check_philosophy_is_not_repo_policy.py](../tools/checks/check_philosophy_is_not_repo_policy.py),
which [tools/precedent_check.py](../../tools/precedent_check.py) picks up from this repo-local source and
runs as a `tree`-scope check. `gates: ["review"]` surfaces this Rule at
`python3 tools/precedent_gate.py review`, which is the read-before step
when someone is deciding whether a piece of the essays has earned its way
into the catalogue.

The check script lives under `local/tools/checks/`, not `tools/checks/` —
that directory is [precedent_materialize.py](../../tools/precedent_materialize.py)'s own output, deleted and
rewritten on every sync, so a hand-added file there survives exactly until
the next one.

**Retirement.** If `philosophy/` is ever removed from this repository, the
check reports NOT APPLICABLE rather than failing, and this file should be
deleted in the same pull request that removes the directory.

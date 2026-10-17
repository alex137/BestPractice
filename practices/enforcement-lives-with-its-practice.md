---
slug:        enforcement-lives-with-its-practice
title:       "A practice and the code that enforces it live in the same repository and ship from there"
tier:        on-demand
severity:    default
applies_to:  ["practices/**", "tools/**", "precedent-source.json"]
applies_to_why: "Fires where a practice is written or its checked_by or ships is set (practices/), where enforcement code is written (tools/), and where a set declares what code it ships (precedent-source.json). Decided: 2026-10-16, when the practice landed."
occasion:    "writing or moving a practice's check, tool or hook, or engine code that enforces one set's rule"
gates:       ["review"]
gates_why:   "Where a new check or hook goes is chosen while the change is being designed; `review` is that moment, before the code exists in the wrong repository."
index_clause: "checks, tools and hooks live with their practice; the engine knows how, not what"
index_required: false
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-16"
approved_by: "Morgan, 2026-10-16: \"I think we should have a practice that any practice and its enforcement mechanisms should live in the same repo ... it feels confusing and surprising and risky that someone, imagine a different user, wants some enforcement mechanism in their very, very private repo just for their company that does top secret private things. And then they put the enforcement in the general best practice for the whole world to even see the code, even if the code is not triggered.\" Go-ahead on the plan the same day: \"go ahead\"."
strength:    decided
---
## Rule
**A practice's `checked_by`, its `ships:`, its `hooks:` and any code that
exists only to enforce it live in the same repository as the practice,
and ship from there** -- a shared or individual set's checks in that set,
never in Precedent's engine.

**The engine knows how to run a set's checks, tools and hooks -- the
runner, the loader, the hook point -- and never what any one set's rule
is:** no set's name, no set's practice slug, no logic that only one set's
rule needs. Code two sets both need goes into the engine as generic
plumbing, or into one set the other declares, never as copies.

**A rule that must hold even when its set fails to load cannot rely on the
set's code running.** Anchor it outside the session -- a GitHub ruleset,
as the ladder's act does for branch names -- or in the engine's generic
refusal of a push while a declared or brought source did not load.

## Detail
**What counts as enforcement.** A script named in `checked_by`, a file in
`ships:`, a hook in `hooks:`, and engine code whose only reason to exist is
one set's rule (a branch on that set's name, a check of its slug, a
refusal its practice describes). A generic mechanism several sets can use
-- the practice-check runner, `ships:` delivery, the `pre-push` hook point,
telling a check where a push goes -- is plumbing, and stays in the engine.

**How a set ships its code.** `ships:` on the practice that owns it: the
sync copies each file to the same path in every consuming repository, and
untracked into a session for a person who brings the set
([practice-carries-its-files](practice-carries-its-files.md)). A check is
the set's `tools/checks/<name>.py`, with its test beside it.

**Moving enforcement out of the engine** goes in this order, so nothing is
unenforced in between: the set ships its copy; the engine's copy comes out
in the same release; both reach a consumer in the same Update Vendors.
Where the engine still needs a piece for its own operations (the branch
name builder, which the engine's ladder steps call), the piece stays until
those operations move, and the plan that moves them says so.

**Its check is an inventory, for now.** `enforcement-lives-with-its-practice`
in [tools/precedent_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py) lists, for every
shared and individual set on disk, each practice whose `checked_by` or
`ships:` resolves to an engine file rather than the set's own, and each
string in engine code that names a set or one of its practice slugs. It
warns until the moves in
[spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/ENFORCEMENT_LIVES_WITH_ITS_PRACTICE_PLAN.md)
land, and then refuses.

## Why
**Privacy:** a private set's rules never show up in a public engine.
**Ownership:** whoever changes the rule changes its check in the same
commit, in the same repository. **No silent switch-off:** code that sits
in one repository while its rule sits in another goes quiet when the
rule's repository fails to load.

## Story
On 2026-10-16 a session opened on two repositories at once, the ladder set
failed to clone, and a branch the harness had named was pushed and landed
on staging three times with nothing said. The rule against it was the
ladder's act; every piece that enforced it was engine code that switched
itself on only when the engine found the ladder loaded, and a set that
failed to load read the same as a person off the ladder. The same day an
inventory found the pattern twice more: the ladder's landing steps run on
engine code, and the private individual set declared its commit checks as
engine files. Morgan asked for the practice in the words above.

## Install
Nothing to install: it binds wherever a practice set is written, and its
check runs from the engine.

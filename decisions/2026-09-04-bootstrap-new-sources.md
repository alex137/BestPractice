---
date:        2026-09-04
question:    A brand-new adopter with no individual or team practice repo
             yet has nowhere to start -- `SETUP.md` step 2 and
             `INSTALL.md` step 9 both ask "do you already have one?" and
             treat "no" as a complete, final answer. Should closing this
             wait for `spec/PHASE6_BRIEF.md` item 2 (wiring the full
             candidate/proposal pipeline into an installed repo), should
             the fix also attempt to create the actual GitHub repository,
             and should the generalized procedure live inside
             `spec/PRIVATE_SETS_BRIEF.md` or as its own document?
decision:    Ship a narrower fix now, independent of item 2: two real,
             forkable skeletons (`templates/practice-set-individual/`,
             `templates/practice-set-team/` -- the latter carrying this
             repo's first `approvers.json.template`), a new
             `tools/precedent_bootstrap_source.py` that instantiates
             either one and prints or writes the exact next-step config,
             harness-tested against a real resolve
             (`check_bootstrap_source_produces_resolvable_set`), a real
             branch in `SETUP.md`/`INSTALL.md` step 9 for "no, but I'd
             like one," and the generalized procedure as its own new
             document, `spec/BOOTSTRAP_NEW_SOURCES.md`, explicitly
             distinguished from `spec/PRIVATE_SETS_BRIEF.md`'s bespoke,
             historical account. The tool never touches a git remote or
             any hosting API -- creating the actual repository stays a
             human/session step, by design.
alternatives: ["Wait for spec/PHASE6_BRIEF.md item 2 to land and fold
               repo-bootstrapping into that same pass, on the theory that
               both are about consumer-repo onboarding",
               "Have the tool also create the GitHub repository itself
               via an API call, rather than stopping at the local
               working tree",
               "Document the procedure in prose only (extend
               spec/PRIVATE_SETS_BRIEF.md or ADOPTING.md), without
               building a tool, on the theory that examples/practice-set/
               already shows the shape closely enough to copy by hand"]
decided_by:  Morgan
---

## Why this was asked

Morgan asked what a brand-new, unrelated adopter of Precedent actually does
when they have neither an individual nor a team repo yet -- every real test
of the three-source model so far used `precedent-individual`/
`precedent-team-maintainers`, both already populated. Research (see the
session transcript, not repeated here) confirmed a real, self-acknowledged
gap: `SETUP.md` step 2 says "most projects answer no, and that's a complete
answer" with no follow-up; `templates/` had no individual/team skeleton to
fork (`examples/practice-set/` exists but its own README disclaims that
role -- "shows the shape and then stops," frozen); no `approvers.json`
template existed anywhere despite Stage 4 requiring one; and the only real
population of the two existing private sets was bespoke, one-off work
(`spec/PRIVATE_SETS_BRIEF.md`), not a repeatable procedure. Both
`spec/PHASE6_BRIEF.md` and
`decisions/2026-09-03-setup-getting-started-disclosure-gap.md` had already
named this class of gap as real and deliberately deferred, not yet built.

## Why not wait for item 2

`spec/PHASE6_BRIEF.md` item 2 ("wire the creation pipeline itself into an
installed repo") is about *proposing new practices upward* once a set
already exists -- vendoring `precedent_candidate.py`/`precedent_promote.py`/
`precedent_land.py` alongside the loader in a consumer repo, so a session
there can raise and land a real candidate instead of the placeholder "open
a plain pull request (PR)" instruction `templates/AGENTS.md.loader.template`
currently carries. That is a materially different, materially larger piece of work,
and folding this fix into it would have meant the "I have nothing yet" gap
stayed open for however long item 2 takes to land -- item 2 itself is still
blocked on item 1 (rehearsing `INSTALL.md` §0 against a real repo) per that
brief's own sequencing recommendation. A freshly bootstrapped set is
useful immediately without any of that: it works today with direct edits,
exactly the way `examples/practice-set/` already demonstrates a personal
set can. Closing the narrower gap now, and leaving item 2 exactly as open
as it was, is a strictly better position than blocking on it.

## Why the tool stops short of creating the actual repository

A session's access to create a repository on someone's behalf varies by
platform and is not something this tool can assume -- getting it wrong
(silently failing, or worse, silently succeeding somewhere the adopter
didn't expect) is worse than being honest that this step needs a human or
a session with the right access. The tool prepares a complete, valid local
working tree and the exact wiring the next step needs; `git init`, adding
the remote, and pushing stay explicit, spelled out step by step in
`spec/BOOTSTRAP_NEW_SOURCES.md` rather than automated away.

## Why a new document instead of extending `PRIVATE_SETS_BRIEF.md`

`spec/PRIVATE_SETS_BRIEF.md` is a historical record of how this specific
project's two private sets were actually populated --
RepoPersonalPreferences' (RPP) real 46 rules, carried across by a session
with special, deliberately-relaxed access
(`decisions/2026-09-01-relax-private-repo-isolation.md`). It says plainly
it is not a procedure anyone else should follow. Grafting a generalized
"anyone, starting from zero" procedure onto that document would blur a
distinction the document itself insists on. `spec/BOOTSTRAP_NEW_SOURCES.md`
carries no private content and is written to be followed by any adopter,
any number of times -- worth keeping separate for the same reason
`spec/PRIVATE_SETS_BRIEF.md` gives for its own existence.

## What this does not change

Independent of `spec/PHASE6_BRIEF.md` items 1, 2 and 4, which stay exactly
as open as they were. Does not attempt real-world rehearsal against an
actual brand-new external adopter -- the harness check proves the tool's
*output* resolves cleanly against a synthetic consumer repo, not that the
full human-in-the-loop procedure reads well to someone who has never seen
Precedent before, named as open follow-on work in
`spec/BOOTSTRAP_NEW_SOURCES.md`'s own closing section.

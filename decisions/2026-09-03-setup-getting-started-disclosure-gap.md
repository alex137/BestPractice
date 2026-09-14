---
date:        2026-09-03
question:    When a repo installs BestPractice clean, or an existing install
             is migrated, does anything proactively tell the installer or
             members that the assistant can turn a spoken instruction into a
             durable project rule and where it goes? And separately: should
             `SETUP.md`/`GETTING_STARTED.md` describe the full three-level
             candidate/promotion/approval pipeline (Stages 1-5), or only the
             capture-gate mechanism a fresh install actually gets today?
decision:    No, nothing disclosed this before now -- confirmed by grepping
             PRACTICE_ENGINE_PLAN.md for both filenames and finding zero
             hits. Closed for the mechanism that is real today: `SETUP.md`
             step 7 and templates/GETTING_STARTED.md now tell the installer
             and members, in plain language, that saying "always X" / "never
             Y" / "from now on" gets noticed and offered back as a project
             rule captured into the instructions file. Deliberately does NOT
             describe the individual/team/universal pipeline, because that
             pipeline is not part of what `SETUP.md` vendors into a consumer
             repo yet -- disclosing it now would overclaim a capability the
             installed repo doesn't have.
alternatives: ["Describe the full three-level pipeline now, on the theory
               that it exists in BestPractice's own repo and Morgan's
               private sets, so the docs should describe the target state",
               "Do nothing until Phase 6 actually vendors the loader into a
               consumer repo, and disclose everything in one pass then",
               "Only fix `SETUP.md` (the installer-facing doc), leave
               GETTING_STARTED.md (member-facing) unchanged since members
               don't drive installs"]
decided_by:  Morgan
---

## Why this was asked

Morgan asked directly whether a clean install or a migration tells the user
it can create new practices and put them in the repo -- worried, reasonably,
that a real capability nobody is told about might as well not exist for
someone who doesn't already know to ask for it. Checking confirmed the
worry: PRACTICE_ENGINE_PLAN.md's own Stage 4 ("How an Approver Finds Out")
and the `disclose-landing` practice it produced both describe telling
someone about a proposal that has *already been raised* -- neither one is
about a brand-new installer or member learning the capability exists at
all, before anything has triggered it. Grepping the whole plan document for
`SETUP.md` and `GETTING_STARTED` returned nothing. This was never written
down as a requirement anywhere, on either side of the fork.

## What was actually offered, and what was chosen instead

The first-considered fix was to describe the full Stage 1-5
candidate/promotion/approval pipeline in `SETUP.md` and `GETTING_STARTED.md`
now, since it is real, built, and harness-tested
(spec/PHASE5_BRIEF.md). Rejected: that pipeline's tooling
(`tools/precedent_candidate.py` and friends) lives in this repo and in
`precedent-individual`/`precedent-team-maintainers`, but `SETUP.md` still
installs the *old*, pre-fork model into a consumer repo --
`templates/AGENTS.md.template`'s capture-gate step, `process/upstream/`
vendoring, no `precedent.json`, no loader. spec/PHASE5_BRIEF.md already
named this precisely: "`INSTALL.md` still documents BestPractice's *old*,
pre-fork vendoring model... silent on what changes for a project that wants
`precedent-beta-v01` instead." Telling a freshly-installed project's members
about individual/team/universal proposal routing they don't actually have
would be exactly the kind of claim this system's own `checked_by` and
`disclose-landing` disciplines exist to prevent elsewhere -- a promise with
nothing behind it.

So the fix was scoped down to what a fresh install genuinely gets today:
the capture-gate mechanism (practice 10) already folds a stated "always X"
into the project's own instructions file, real and working in every repo
`SETUP.md` has ever installed. That is what `SETUP.md` step 7 and
`GETTING_STARTED.md` now say, in plain language, per `readers-vocabulary`.

Both installer-facing and member-facing docs were fixed together, not just
`SETUP.md`: a member who never talks to the installing administrator has no
other way to learn this exists, and `GETTING_STARTED.md` is exactly the
document this system already builds for that reader.

## What this actually changes

- `SETUP.md` step 7 ("Hand them the keys") now names the capture-gate
  mechanism as a third thing the installing administrator is told, closing
  with the same person who confirms the Actions check and hands off members.
- `templates/GETTING_STARTED.md` gained a new "How the project remembers
  new rules" section, placed after the five-step contributing walkthrough
  and before the per-tool setup instructions, so a member reads it before
  needing to act on it.
- `TODO.md` gained two items (9, 10) for the two things
  spec/PHASE5_DEEPCHECK.md flagged as real but never actually tracked
  anywhere: the pre-fork catalogue audit table, and `for_team:`/`in_repos:`'s
  blocked-on status.

## What this does NOT change, and what happens next

This does not touch the pipeline itself, INSTALL.md's vendoring model, or
any tooling -- purely two disclosure edits plus two tracking lines. **The
real fix -- a clean install that actually sets up the loader and the
creation pipeline, disclosed honestly at that point -- is proposed as Phase
6 scope**, written up separately for Morgan's review before it lands in
this plan. Once that exists, `SETUP.md`/`GETTING_STARTED.md`'s disclosure
should be revisited and upgraded to name the individual/team/universal
routing explicitly, rather than staying at the capture-gate description
this decision deliberately limited itself to.

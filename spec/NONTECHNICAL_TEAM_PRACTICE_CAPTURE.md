<!-- Last updated: 2026-09-04 by the session that drafted this plan, from a
     follow-up brainstorm with Morgan after
     spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md. Not yet executed — see
     "Status" below. -->

# Plan: team-level practice capture for non-technical document work

**Status: drafted, not executed.** Self-contained, so a fresh session can
pick it up without the conversation that produced it. This plan does not
invent a pilot project or a pilot person — Morgan does not have one yet by
design (see "Sequencing," below) — so this session's scope is the team
repo and the reusable template only, not onboarding anyone.

## What this is, and how it differs from the access plan

[spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
answers "how does a non-technical person use one repo safely." This plan
answers a different, larger question: Morgan wants **many** non-technical
people working on **many** documents, as a standing replacement for Google
Docs — and the reason to build this on Precedent rather than a plain
Claude-plus-git setup is that editorial and structural decisions ("lead
with the customer's problem, not the solution," "cut the throat-clearing
paragraph," "this argument goes before that one") get captured as durable,
reusable rules as people work, instead of living and dying inside one
document the way they would in Google Docs. That capture is the whole
point of this use case, not a nice-to-have bolted onto it.

**Nothing about the access mechanics changes.** Every document-project repo
this plan produces still uses
[spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
unmodified for the person using it — GitHub role as the enforced boundary,
restricted session config as defense-in-depth. This plan is additive: it's
about what the *content* layer looks like when the same pattern has to
scale across many people and many documents at once, which the access plan
never addressed (it was written for one person, one repo).

## The mechanism: this is `team`, applied somewhere new

[spec/SOURCES.md](SOURCES.md) already built the `team` level — a private
repo of practices, resolved live (never vendored) into every consuming
repo's `precedent.json`, at precedence `team > repo-local > individual >
universal`. The one existing example,
`themorgan/precedent-team-maintainers` (see
[spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md)), holds code-repo
conventions. Nothing about the mechanism assumes code — a `team` source is
just practices, and a practice is just a Rule with a Story behind it. What's
new here is the *content*: editorial and voice decisions instead of
engineering ones, contributed mostly by people who will never run
[tools/precedent_land.py](../tools/precedent_land.py) themselves.

**The candidate-capture signals already generalize without changes.**
[spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md)'s seven signals
(`session-judgment-at-a-gate`, `explicit-instruction`,
`reverted-or-corrected`, `repeated-instruction`, `repeated-check-failure`,
`review-found-defect`, `restated-in-second-scope`) fire the same way on
prose as on code — "the user rewrote a paragraph back to how it was" and
"the user said 'always lead with the problem, never the solution, from now
on'" are `reverted-or-corrected` and `explicit-instruction` regardless of
what kind of file changed. `repeated-check-failure` is the one signal that
mostly won't fire on prose (no mechanical check exists to repeat) — that's
expected, not a gap; the other six carry it.

**Non-technical contributors are never listed approvers**, so their team
candidates should default to
[precedent_candidate.py](../tools/precedent_candidate.py) `--as-issue
true` — a GitHub Issue on the team repo — per
[spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md#which-one-for-team-file-or-issue)'s
existing rule that a quiet `candidates/*.md` file accomplishes nothing when
nobody with landing authority is watching it. This also happens to be the
closest thing to "commenting on the shared style guide" the whole pitch is
selling — an Issue thread, not a git object, is what she'd interact with if
she ever opens GitHub at all.

## Architecture — three pieces

1. **One shared, private team practice repo**, dedicated to editorial and
   content conventions — distinct from `precedent-team-maintainers`, which
   is about this account's code repos, not this. Starts **empty**: unlike
   [spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md)'s migration (46
   existing rules to split), there is no pre-existing rule set to import
   here — it fills up from real candidates raised during real document
   work, which is the entire mechanism working as designed, not a
   bootstrapping problem to solve first.
2. **A reusable document-project template.** Every future non-technical
   project repo should be instantiated from one place, not re-derived —
   folding together [INSTALL.md §0](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)'s
   vendoring steps, a `precedent.json` declaring the new team source
   (resolved live from a sibling clone, **never vendored** — SOURCES.md's
   rule), and [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md)'s
   access restrictions and persona instruction, unmodified. This belongs in
   this repo's own `templates/` — it's a generic, reusable pattern, not
   proprietary content, the same reasoning that already put
   `templates/AGENTS.md.loader.template` here.
3. **Nothing new for capture itself** — see "The mechanism," above. The
   only real engineering work is steps 1 and 2; step 3 is a matter of
   pointing the existing pipeline at a new kind of content and watching
   what happens.

## Sequencing — prove it once before stamping it out

**Deliberately do not build for "lots of people" yet.** Three things in
this plan are genuinely unrehearsed: a `team` source built for editorial
content instead of code, the access plan running against more than the one
repo it was written for, and candidate capture on prose. Building a
multi-person rollout before any of that has been exercised once means
guessing at a template's shape before you've seen what it needs to hold.

This plan's own scope is therefore: the team repo (empty, real) and the
document-project template (real, reusable) — **not** a pilot project,
because Morgan does not have one yet (see the previous conversation turn:
"I don't have it yet, first I want to develop it"). The pilot — one real
document project, one real non-technical person, using the template this
plan builds and the access mechanics from
[spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
unmodified — is the next plan, written once a real subject exists, not
invented here to have something to test against.

## Prerequisites — decisions only Morgan can make

1. **Name and location of the new team practice repo.** Private, distinct
   from `precedent-team-maintainers`. Not yet chosen.
2. **Who goes in `approvers.json`.** At minimum Morgan
   (`{"name": ..., "github": ...}` entries, per
   [tools/precedent_land.py](../tools/precedent_land.py)'s format) — anyone
   else with landing authority over editorial conventions should be named
   now rather than added under pressure later.
3. **One team repo for everything, or split by subject area later?**
   Recommend starting with **one** shared team source for all non-technical
   document work, and splitting only if a real conflict appears between
   subject areas (e.g. marketing copy wants a voice rule that legal
   drafting shouldn't inherit) — the same "revisit when a real case
   appears" posture [TODO.md](../TODO.md) item 7 already takes for
   multi-team imports generally. Splitting pre-emptively means guessing at
   a boundary with no real case to draw it from.

## Implementation sequence (this session's actual scope)

### Step 1 — Create the team practice repo

Private. `practices/` and `candidates/` directories (both start empty —
see "Architecture," above). `approvers.json` naming Morgan (Prerequisites
item 2). No `leak-blocklist.txt` needed here — that mechanism protects the
*public* Precedent repo from private leakage on check-in
([spec/SOURCES.md](SOURCES.md#the-leak-gates-vocabulary-layer-as-switched-on));
nothing in this new team repo is ever checked into a public tree unless a
practice is later promoted to universal, which is a separate, deliberate
act.

### Step 2 — Build the reusable document-project template

Add it under `templates/` in this repo (BestPractice/Precedent) — e.g.
`templates/nontechnical-document-project/` — combining:

- INSTALL.md §0's vendoring steps (universal engine).
- A `precedent.json` declaring the new team source from step 1, resolved
  live, with the placeholder repo name left obvious to fill in.
- [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md)'s
  Step 3/4 content verbatim (session/environment restriction, persona
  instruction) — that plan already worked this out; don't re-derive it.
- An explicit AGENTS.md bullet instructing Claude that any candidate a
  contributor raises defaults to `precedent_candidate.py --as-issue true`
  against the team repo (per "The mechanism," above), since a non-technical
  contributor is never a listed approver.

### Step 3 — Stop here

Do not invent a pilot subject or a pilot person to test this against. Once
Morgan has a real first project, the next session applies
[spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
to instantiate it from this template, and — this is the actual test of the
whole pitch — verifies that an editorial decision made in that pilot
project, once promoted, is reachable by resolving the same team source
from a *second*, independent document-project repo. Without that
cross-project check, the core claim (decisions made once benefit every
future document) is asserted, not demonstrated.

## What this plan does not cover

- The pilot itself — deliberately, see "Sequencing."
- Multi-team-source conflicts — out of scope until a real second team
  source for this subject area exists ([TODO.md](../TODO.md) item 7).
- Anything about the access mechanics — unchanged, delegated entirely to
  [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md).
- Non-GitHub hosts ([TODO.md](../TODO.md) item 8).

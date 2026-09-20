---
title:         "The README as a Pitch, Not an Index: A Rewrite Proposal"
kind:          proposal
status:        drafted
opened:        2026-09-20
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The current README reads like a table of contents: a dry definition, an internal branch-status notice, then a list of links. This proposes reordering it around a single hook developers actually feel — your team's unwritten rules get written down for you, in the open, enforced by code — and moves everything else (the branch note, the philosophy bullets, the doc map) to support that hook instead of competing with it. No change is made to README.md itself; this is the plan to review first."
---

# The README as a Pitch, Not an Index

**Nothing here touches [README.md](../README.md).** This is the proposal to
react to before anyone rewrites it.

## The Problem, in One Paragraph

**The README currently reads like the table of contents for a manual, not
the front door of a project.** Its first substantive sentence is a
definition ("a layer that sits between a group of people and their shared
work"), its second paragraph is a scope note about which branch you're on
and which pull request merged it into `main`, and its third is a bullet
list that sounds like a spec sheet ("automatic rule generation based on
behaviour, smooth team-based rule sharing..."). A developer lands here,
reads two screens, and has learned what Precedent's parts are called before
learning why any of that would change how they work. **The best sentence
in the whole page — "notices how your team wants things done and writes
those habits down as rules" — is the fourth paragraph in, after two other
things had to be read first.**

## What a Pitch Page Actually Does

A developer decides whether to keep reading in the first ten seconds, on
one thing: **does this solve a problem I recognize?** The problem
Precedent solves is a familiar one — a team's real conventions live in
Slack threads, old PR comments, and one person's memory, drift the moment
that person is out sick, and get rewritten from scratch on every new
project. That's the hook. Everything else — the four levels a practice can
live at, the enforcement scripts, the git mechanics — is how it's solved,
and belongs *after* the reader already wants the solution, not before.

**The rewrite's one job: lead with the problem and the "wait, it does
what?" moment, and hold the reference material for people who are already
sold.**

## What Moves, and Why

- **The branch-status callout (current README, lines 18–25) drops out of
  the top of the page entirely.** It's true and it matters to a
  contributor, but it is repository housekeeping — which branch a visitor
  is reading, which PR merged it into `main` — and putting it before the
  pitch tells a first-time reader that this page is written for people who
  already work here. It belongs near the bottom, next to the other
  contributor-facing links ([INSTALL.md](../INSTALL.md),
  [AGENTS.md](../AGENTS.md)), or in a one-line
  "you are on the development branch" note that doesn't cost the reader
  their first impression.
- **The opening definition gets replaced by a problem statement and a
  concrete example**, not a category. "A layer that sits between a group
  of people and their shared work" describes the architecture; it doesn't
  describe what changes for the reader. A sentence that says what a team's
  Tuesday looks like differently earns the next sentence.
- **"We are unique on a few axes" (line 7) goes.** A bullet list of feature
  names, before the reader has any reason to care which features exist,
  reads as marketing copy pretending to be a spec — and it's the exact
  tell [write-like-a-human](../practices/write-like-a-human.md) already
  names: the summary nobody asked for yet. The same four ideas are worth
  keeping, but each earns its own moment further down, next to the "why"
  that makes it matter.
- **The Philosophy section (current lines 40–67) stays, shortened and
  moved later.** It's real and it's a genuine differentiator — most tools
  in this space don't have one — but it currently reads as an abstract
  detour between "here's how the enforcement works" and "here's how
  installation works." It's stronger as the section that answers "okay,
  but why did you build it *this* way" for a reader who's already curious,
  not as a wall a skimming reader has to get past first.
- **"Built for Many Hands" and "What Your Members Will See" (current lines
  77–102) collapse into fewer, sharper claims.** Five sub-bullets under
  "Built for Many Hands" is reference material, not pitch; a rewrite pulls
  the one or two that are actually surprising to the top and moves the
  rest into
  [documentation/WHY_PRECEDENT.md](../documentation/WHY_PRECEDENT.md),
  which already exists to hold exactly this level of detail.

## Proposed Structure

1. **A one-line hook**, not a definition. Something in the shape of: *your
   team already has real conventions — they just live in old Slack
   messages and one person's memory. Precedent notices them and writes
   them down, in your own repo, enforced instead of hoped for.*
2. **A concrete before/after**, three or four lines, showing the thing
   actually happening — a team member corrects the assistant once, and
   every session after that follows the correction without being told
   again. Developers trust a worked example over an adjective; this repo's
   own [no-invented-specifics](../practices/no-invented-specifics.md)
   practice means this has to be a real mechanism described honestly, not
   a fabricated customer story — the walkthrough already in
   [documentation/TEN_THINGS.md](../documentation/TEN_THINGS.md) item 4 is
   real material to draw the example from.
3. **Why a developer specifically should care** — plain text and git as
   the source of truth, no proprietary format, enforcement by scripts that
   fail loudly instead of a policy doc nobody reads, an audit trail for
   every decision. This is the section that currently exists (buried) in
   [documentation/WHY_PRECEDENT.md](../documentation/WHY_PRECEDENT.md)'s
   "Open Source and Open Documents" and "Enforcement Instead of Vigilance"
   groups — it's some of the strongest material in the whole documentation
   set and the README currently doesn't surface any of it.
4. **The philosophy**, shortened to the three ideas and why they're not
   obvious, with the current link into [philosophy/](../philosophy/) for
   anyone who wants the full argument.
5. **Get started**, one link per audience (developer, non-developer,
   already-installed), exactly as today.
6. **Everything else** — the doc map, `GitAround`, the branch/contributor
   housekeeping — as a closing reference block, clearly labeled as
   reference rather than pitch.

## A Draft of the Opening, to Make the Shape Concrete

This is illustrative, not a final draft — it exists so the structure above
reads as something rather than a plan for a plan:

> **Your team already has conventions. Right now they live in a Slack
> thread, an old PR comment, and one person's memory — and they evaporate
> the day that person is out sick or that channel gets buried.**
>
> Precedent notices them instead. Tell your assistant once — "we always
> write dates as YYYY-MM-DD," "never merge without the deep check" — and
> it writes that down as a rule your whole team's future sessions follow,
> checked into your own GitHub repo, in the open, enforced by scripts that
> fail loudly instead of a policy nobody reads.
>
> You don't switch tools. You keep working through Claude Code, or
> whichever assistant your team already uses — Precedent is the layer
> underneath that remembers, so nobody has to.

## What This Proposal Does Not Decide

- **The exact wording of the hook.** The draft above is one version of the
  idea, not a recommendation to ship verbatim — it needs a pass for voice
  once someone is actually rewriting the page
  ([write-like-a-human](../practices/write-like-a-human.md),
  [no-invented-specifics](../practices/no-invented-specifics.md)).
- **Whether the branch-status note moves to a footer line or into
  [AGENTS.md](../AGENTS.md)/[INSTALL.md](../INSTALL.md) only.** Either
  satisfies "not at the top"; which one depends on how often a first-time
  visitor actually needs it inline versus one click away.
- **Whether "Built for Many Hands" survives as a heading at all**, versus
  folding its strongest claim into the why-developers-care section and
  moving the rest wholesale into
  [documentation/WHY_PRECEDENT.md](../documentation/WHY_PRECEDENT.md).

## Next Steps if This Direction Is Approved

Rewrite [README.md](../README.md) section by section against the structure
above, run [tools/doc_lint.py](../tools/doc_lint.py) and the
reader's-vocabulary pass
([readers-vocabulary](../practices/readers-vocabulary.md)), and check every
internal link still resolves before the deep check gates the push.

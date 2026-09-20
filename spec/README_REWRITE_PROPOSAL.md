---
title:         "The README as a Pitch, Not an Index"
kind:          proposal
status:        drafted
opened:        2026-09-20
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The current README reads like a table of contents: a dry definition, an internal branch-status notice, then a list of links. This proposes reordering it around a single hook developers actually feel — your team's unwritten rules get written down for you, in the open, enforced by code — and moves everything else (the branch note, the philosophy bullets, the doc map) to support that hook instead of competing with it. Includes a full draft of the proposed page itself, not just the structure. No change is made to README.md itself; this is the plan to review first."
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

1. **A hook that names the frustrations, not the architecture** — not a
   description ("a layer that sits between..."), and not scene-setting
   about where conventions currently live; three frustrations any team
   working with people and AI already recognizes, immediately followed by
   the different angle Precedent takes on all three at once.
2. **A concrete walkthrough**, not an adjective — what actually happens
   when you attach an assistant to a repo and work through something with
   it: it pushes back, it writes down what you correct it on, it enforces
   and cites what it already wrote down. Developers trust watching the
   thing happen over being told it's good; this repo's own
   [no-invented-specifics](../practices/no-invented-specifics.md) practice
   means this has to be a real mechanism described honestly, not a
   fabricated customer story — the walkthrough already in
   [documentation/TEN_THINGS.md](../documentation/TEN_THINGS.md) item 4 is
   real material to draw from.
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

## What This Proposal Does Not Decide

- **The exact wording of the hook.** The opening below is one version of the
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

## The Proposed Rewrite (Full Draft)

**This is the proposed rewrite of the README, as though it were the page
itself.** It makes concrete calls the sections above left open — where the
branch note lands, whether "Built for Many Hands" survives as its own
heading — so there's something whole to react to rather than a structure
plus a fragment. Disagree with any one of those calls without disagreeing
with the direction; that's the point of drafting it in full.

---

### Precedent

**Precedent solves the three biggest frustrations of working with people
and AI together:**

1. **Nobody notices the pattern — and even when someone does, enforcing it
   costs real time and attention, every single time.**
2. **Nobody remembers why a decision was made, even a small one — and on
   the rare occasion someone does, they've forgotten why it mattered
   enough to decide.**
3. **People forget. And when one person does remember, your team is
   permanently dependent on that one person.**

It solves them by approaching human/AI collaboration from a different
angle:

- **Human collaboration comes first.** The tool exists to make people
  working together better, not to route around them.
- **AI sits between the work and the people doing it**, pushing back on
  ideas to strengthen them and keeping the record of how a decision was
  reached, not just the decision itself.
- **AI watches what's actually happening and proposes the rules for it** —
  generated from a team's own history, and put up for approval, never
  landed unapproved.

### What This Looks Like in Practice

Next time you're brainstorming or working through a problem with your
team — especially a team project — try this instead of a chat window or a
shared doc: open a GitHub repo for the project, and work through it with
Claude Code attached to that repo.

Here's what you'll actually see:

1. **The assistant pushes back on you**, instead of just typing whatever
   you say.
2. **When you explain why you disagreed with it, it writes that down** —
   as a rule, a "Practice," committed to the repo, not left sitting in the
   chat.
3. **The next time the same situation comes up, it enforces the rule and
   cites it**, instead of the two of you relitigating the same argument.
4. **Every decision cites the decisions and preferences that came before
   it**, the reasoning behind it, and an audit trail back to the
   conversation that produced it.
5. **The people on the team guide, correct, and build up the ruleset** —
   and it lives in your own GitHub repo, not locked inside one AI
   provider or held in one person's head.

### Why This Matters if You Write Code

- **Plain text and git are the source of truth.** Every rule, every
  document, and the reasoning behind each one lives in your own GitHub
  repository — nothing sits in a chat log or a memory feature only one
  person can see.
- **No proprietary format, no vendor lock-in.** This is open source, built
  on a platform you already control your own data in. Nothing here can
  shut down and take your project's memory with it.
- **Enforcement instead of vigilance.** The rules that matter are backed
  by small programs that fail loudly, so a project set up this way can
  check a convention instead of hoping someone remembers it.
- **Every decision carries its reasoning and an audit trail.** Not just
  what was decided, but why, with a link back to the conversation that
  produced it — nobody has to dig through chat history to find out.

### The Philosophy Behind This

The three ideas above aren't just this project's engineering choices —
they're one working expression of a broader philosophy about how people
and AI should work together. **That fuller argument lives in
[philosophy/](../philosophy/)**, starting at
[philosophy/README.md](../philosophy/README.md). It is argument and
observation: none of it binds work anywhere else in this repository, which
is what [practices/](../practices/) is for.

### Get Started

**New here?** [Ten Things to Know About How Precedent
Works](../documentation/TEN_THINGS.md) is the one page to read first, then
the how-to guide for your situation: [if you write
code](../documentation/FOR_DEVELOPERS.md), or [if you
don't](../documentation/FOR_EVERYONE_ELSE.md). **Already set up?** [How to
Use This Day to Day](../documentation/DAILY_HABITS.md) has the daily
habits and the phrases your assistant is guaranteed to recognize.

Installing on your own project doesn't require writing any code yourself:
open a session on your project with an AI assistant and paste it
[SETUP.md](../SETUP.md), which runs the whole install as a conversation.
Developers who want the files and commands have
[INSTALL.md](../INSTALL.md), and
[PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md) for what
each person sets on each machine — most people, working on Claude Code on
the web, only need
[CLOUD_SETUP.md](../documentation/CLOUD_SETUP.md).

### Everything Else

*You're reading the Precedent restructuring of BestPractice, on the
`precedent-beta-v01` branch — the design and its evidence are in
[spec/PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md). This branch
merges into `main` regularly; work lands here first.*

Hand installation, updates, and contributing improvements back:
[INSTALL.md](../INSTALL.md). The working method, for power users:
[documentation/METHOD.md](../documentation/METHOD.md). Phone and
per-assistant setups: [documentation/MOBILE.md](../documentation/MOBILE.md).
Automatic repository checks:
[documentation/GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md). Git in
eight ideas: [GIT.md](../documentation/GIT.md). Open items and roadmap:
[TODO.md](../TODO.md). Repository index for agents:
[AGENTS.md](../AGENTS.md). The pitch and how-to guides for people outside
the project: [documentation/](../documentation/).

A separate project grew out of this one:
**[GitAround](https://github.com/alex137/GitAround)**, a way to read a
project and follow what is changing in it from a browser, for people who
would rather not work through GitHub's own screens. It has been a
separate, standalone product since 2026-08-14, no longer a proposal
staged inside this repo.

---

## Next Steps if This Direction Is Approved

Land the draft above as [README.md](../README.md) itself (adjusting its relative links
back to root-level paths), run [tools/doc_lint.py](../tools/doc_lint.py)
and the reader's-vocabulary pass
([readers-vocabulary](../practices/readers-vocabulary.md)), and check every
internal link still resolves before the deep check gates the push.

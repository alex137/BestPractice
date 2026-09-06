# Precedent

> **This branch is the Precedent restructuring of BestPractice.** If you have arrived
> here wanting to *use* the practice engine on your own project, read
> [ADOPTING.md](ADOPTING.md) — it is written for that, and assumes no
> programming. The design and its evidence are in
> [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md). Everything below is
> the pre-fork BestPractice documentation, still accurate for the parts the rewrite
> has not reached; it is rewritten in place as later phases land rather than
> kept as a second, drifting copy.

**New here?** Start with [What Is This](documentation/WHAT_IS_THIS.md) for
the pitch, then jump to the how-to guide for your situation:
[technical](documentation/HOW_TO_USE_THIS_TECHNICAL.md) or
[non-technical](documentation/HOW_TO_USE_THIS_NONTECHNICAL.md).

## The philosophy behind this project

Precedent is one working expression of a broader philosophy about how
people and AI should work together, developed in
**[WorkingWithAI](https://github.com/themorgan/WorkingWithAI)**. Read that
repo for the theory.

In short: it's an alternative to Google Docs, built on three ideas:

- **Human collaboration comes first.** The tool exists to make people
  working together better, not to route around them.
- **AI sits between the work and the people doing it**, pushing back on
  ideas to strengthen them and keeping the record of how a decision was
  reached, not just the decision itself.
- **AI watches what's actually happening and proposes the rules for it** —
  generated from a team's own history, and put up for approval, never
  landed unapproved.

**Keep the project's memory in GitHub, and let people work with that
memory through AI conversations.** Nothing is lost in chat history: the
conversation itself becomes part of the record, so the *why* behind a
change stays on record along with the *what*. And instead of everyone
editing one live document and pausing for big changes, every person (and
AI thread) works at full speed on a private copy, joining the project
through review — each change credited to whoever drove it, reason
recorded.

Behind the scenes, the project lives in a GitHub repository — a durable,
shared memory that every person and every new AI session can pick up cold.
Precedent adapts it so you don't need to be a programmer to get those
advantages; you just need a few ground rules, in [Git, minimally](GIT.md).

The main shift: you use **Claude Code** instead of general-purpose chat
apps. Other assistants have supported paths too; see [MOBILE.md](MOBILE.md).

## Built for many hands

Conventions the assistants follow automatically handle what a shared
document can't:

- **No duplicated work.** An assistant claims a to-do item under its
  member's name and warns others off overlapping it.
- **Nothing lands by surprise.** The assistant finds who a change matters
  to and requests their review.
- **Authors keep the credit**, with the AI as co-author.
- **Every session starts caught up**, summarizing what changed since that
  member last worked.
- **Tracks who made what decision, why, and what incident sparked it** —
  for every decision.

Say *"what's waiting for me?"* and your assistant merges on your word.

## What your members will see

Members receive one link: to the project's own Getting Started page,
which opens with the short case for working this way and then gives
specific instructions for each kind of AI user — Claude, Codex, ChatGPT,
Gemini, and Grok. **[Read the sample here.](templates/GETTING_STARTED.md)**
Installing Precedent creates a version of that page adapted to your
project, and improvements projects make to their onboarding pages flow
back into Precedent for everyone ([INSTALL.md](INSTALL.md) §4).

## Installing Precedent on your project

Setup doesn't require you to write any code yourself — see
[INSTALL.md](INSTALL.md) to get started.

## Everything else

Hand installation, updates, and contributing improvements back:
[INSTALL.md](INSTALL.md). The working method, for power users:
[METHOD.md](METHOD.md). Phone and per-assistant setups:
[MOBILE.md](MOBILE.md). Automatic repository checks:
[GITHUB_ACTIONS.md](GITHUB_ACTIONS.md). The pre-split practice catalog
(52 of the current, larger set — see [practices/](practices/) for the
complete, current one): [PRACTICES.md](PRACTICES.md). Slide decks built
from plain files: [deck/](deck/). Git in eight ideas: [GIT.md](GIT.md).
Open items and roadmap: [TODO.md](TODO.md). Repository index for agents:
[AGENTS.md](AGENTS.md). The pitch and how-to guides for people outside the
project: [documentation/](documentation/).

A separate project grew out of this one:
**[GitAround](https://github.com/alex137/GitAround)**, a way to read a
project and follow what is changing in it from a browser, for people who
would rather not work through GitHub's own screens. It has been a
separate, standalone product since 2026-08-14, no longer a proposal
staged inside this repo.

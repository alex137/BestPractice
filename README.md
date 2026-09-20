# Precedent

Precedent solves the three biggest frustrations of working with people
and AI together:

1. **Nobody notices the pattern** — and even when someone does, enforcing
   it costs real time and attention, every single time.
2. **Nobody remembers why a decision was made, even a small one** — and
   on the rare occasion someone does, they've forgotten why it mattered
   enough to decide.
3. **People forget small details, the why, and the how.** And when one
   person does remember, your team is permanently dependent on that one
   person.

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

## What This Looks Like in Practice

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

## Why this matters

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

## How

- **Start a repo, not a doc — then vendor-in Precedent.** Spin the repo up
  for the idea the same way you'd start a shared doc, then bring
  Precedent's practice engine into it — that's what turns everything below
  from a wish into something that actually happens.
- **Everyone works through their own AI.** Every teammate connects their
  assistant to that same repo and works through it — nobody opens the
  files directly.
- **You brainstorm and direct it together.** The team argues the idea out
  with their assistants and gives it direction; the repo is what catches
  everything that comes out of that.

## The Philosophy Behind This

The three ideas above aren't just this project's engineering choices —
they're one working expression of a broader philosophy about how people
and AI should work together. **That fuller argument lives in
[philosophy/](philosophy/)**, starting at
[philosophy/README.md](philosophy/README.md). It is argument and
observation: none of it binds work anywhere else in this repository, which
is what [practices/](practices/) is for.

The individual pages, if you want to go deeper on any one idea:
[Core Pillars](philosophy/CORE_PILLARS.md),
[Our Philosophy](philosophy/OUR_PHILOSOPHY.md),
[The Working Loop](philosophy/THE_WORKING_LOOP.md),
[Reasons Why](philosophy/REASONS_WHY.md),
[The Talmudic Method](philosophy/THE_TALMUDIC_METHOD.md),
[Company Building Rules](philosophy/COMPANY_BUILDING_RULES.md),
[AI Governance to Co-Create](philosophy/AI_GOVERNANCE_TO_COCREATE.md), and
[Humans at Our Best](philosophy/HUMANS_AT_OUR_BEST.md).

## Get Started

**New here?** [Ten Things to Know About How Precedent
Works](documentation/TEN_THINGS.md) is the one page to read first, then
[What This Is (and Why Explore Using
Precedent)](documentation/WHY_PRECEDENT.md) for the fuller pitch, and
the how-to guide for your situation: [if you write
code](documentation/FOR_DEVELOPERS.md), or [if you
don't](documentation/FOR_EVERYONE_ELSE.md). **Already set up?** [How to
Use This Day to Day](documentation/DAILY_HABITS.md) has the daily
habits and the phrases your assistant is guaranteed to recognize.

Installing on your own project doesn't require writing any code yourself:
open a session on your project with an AI assistant and paste it
[SETUP.md](SETUP.md), which runs the whole install as a conversation.

## Get Up and Running!

To get going, vendor in Precedent to a repo, connect that repo to your
favorite AI via their coding platform — and go!

## Manually Install

Hand installation, updates, and contributing improvements back:
[INSTALL.md](INSTALL.md). What each person sets on each machine:
[documentation/PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md) —
most people, working on Claude Code on the web, only need
[documentation/CLOUD_SETUP.md](documentation/CLOUD_SETUP.md). The working
method, for power users:
[documentation/METHOD.md](documentation/METHOD.md). Phone and
per-assistant setups: [documentation/MOBILE.md](documentation/MOBILE.md).
Automatic repository checks:
[documentation/GITHUB_ACTIONS.md](documentation/GITHUB_ACTIONS.md). Git in
eight ideas: [documentation/GIT.md](documentation/GIT.md). Open items and roadmap:
[TODO.md](TODO.md). Repository index for agents:
[AGENTS.md](AGENTS.md). The pitch and how-to guides for people outside
the project: [documentation/](documentation/).

# BestPractice

> **This branch is being restructured into Precedent.** If you have arrived
> here wanting to *use* the practice engine on your own project, read
> [ADOPTING.md](ADOPTING.md) — it is written for that, and assumes no
> programming. The design and its evidence are in
> [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md). Everything below is
> BestPractice's own documentation, still accurate for the parts the rewrite
> has not reached; it is rewritten in place as later phases land rather than
> kept as a second, drifting copy.

**Keep the project's memory in GitHub, and let people work with that
memory through AI conversations.**

BestPractice helps people work together with AI assistants on a shared
project without losing decisions, repeating work, passing around outdated
files, or overwriting each other's changes. Members work by opening an AI
agent with access to the project: they ask questions about what the
project knows, discuss ideas, and implement updates with the AI's help —
and the administrator green-lights changes, also with AI help, before
they join the shared project. The output of every AI conversation becomes
part of the project, so nothing is lost in chat history.

**It captures intention, not just text.** Most writing tools keep the
sentence you landed on and lose the reasoning that got you there.
Working a decision through in conversation with an AI does the
opposite: the back-and-forth that produces the wording is itself part
of what gets saved, so the *why* behind a change stays on record, not
just the *what*. That also moves your attention to where it belongs —
the assistant carries the mechanics of drafting, formatting, and
editing, so you spend your time thinking through the problem, not
producing the document that describes it. It's a tighter loop than the
usual way of writing with an LLM: instead of asking for a draft and
then editing it yourself afterward, you think out loud with the
assistant and the document is what falls out of that conversation.

**It is an alternative to Google-Docs-style collaboration.** A shared
live document lets everyone make tiny edits at once — but the unwritten
rule is that everyone pauses while one person makes a big change, big
edits trample each other, and the document never remembers who decided
what, or why. Here there is no pause: every person (and every AI thread)
works at full speed on a private copy, changes join the shared project
through review, every change is credited to the person who drove it with
the reason recorded — and the system itself notices which teammates a
change matters to, and flags them.

Think of a hospital chart at shift change: clinicians rotate, but the
chart carries every observation, every decision, and the reasoning behind
it — if it isn't in the chart, it didn't happen — so the incoming doctor
picks up the patient cold and nothing learned on the last shift is lost
in the handover. BestPractice gives your project that chart.

Behind the scenes, the project lives in a GitHub repository. GitHub is a
system originally built for programmers that keeps the current files,
earlier versions, decisions, open questions, and change history together
— the same durable memory for every person and every new AI session.
BestPractice adapts it so you don't need to be a programmer to get those
advantages for your project; you just need a few ground rules, captured
in [Git, minimally](GIT.md). Changes are safe by construction: each
change happens on its own working copy, is checked automatically, and
joins the shared project only when it is approved.

The main shift is that you stop using the general-purpose chat apps —
ChatGPT, the ordinary Claude chat, and their workplace versions — and use
**Claude Code** instead. Claude has automated the setup that used to
require a programmer: it connects to your project's repository out of the
box, on desktop and on a phone. We expect OpenAI and Grok to add the same
kind of experience soon (they have not, as of 2026-08); until then,
unless you want to set up a programming environment yourself, these
documents assume you are a Claude Code user. Members who prefer other
assistants still have supported paths — see the members' page below and
[MOBILE.md](MOBILE.md).

## Built for many hands

The collaboration problems a shared document can't solve are handled by
conventions the assistants follow automatically:

- **No duplicated work.** When a member takes on a to-do item, their
  assistant claims it under their name — and warns anyone else's
  assistant before it starts overlapping work.
- **Nothing lands by surprise.** Before proposing a change, the
  assistant works out who it matters to — from who wrote the affected
  text, and who has pushed back on similar changes before — and requests
  that person's review. Routine changes merge routinely; sensitive ones
  find their reviewer. Nobody has to declare their sensitivities up
  front; the system learns them from the project's own history.
- **Authors keep the credit.** Changes are recorded as the member's
  work, with the AI as co-author, so the project's history shows
  people's contributions as theirs.
- **Every conversation starts caught up.** Each new session opens with a
  plain-language summary of what changed since that member last worked.

Your side of the loop is conversational too: say *"what's waiting for
me?"* and your assistant summarizes each pending proposal, integrates
any that collide, and merges on your word. The administrator section at
the end of the members' Getting Started page teaches it in full.

## What your members will see

Members receive one link: to the project's own Getting Started page,
which opens with the short case for working this way and then gives
specific instructions for each kind of AI user — Claude, Codex, ChatGPT,
Gemini, and Grok. **[Read the sample here.](templates/GETTING_STARTED.md)**
Installing BestPractice creates a version of that page adapted to your
project, and improvements projects make to their onboarding pages flow
back into BestPractice for everyone ([INSTALL.md](INSTALL.md) §4).

## Installing BestPractice on your project

1. **Set up a GitHub repository** for your project — brand-new or one
   that already has your files in it
   ([how, and why GitHub](GIT.md)).
2. **Open the repository in Claude Code or Codex** (for Claude: go to
   [claude.ai/code](https://claude.ai/code) and start a session on the
   repository) and paste:

   > Follow the instructions at
   > https://github.com/alex137/BestPractice/blob/main/SETUP.md

   The agent asks you two questions about your project, installs
   everything, walks you through what it created, and turns on the
   automatic checks. You approve; it goes live.
3. **Say "Add project members."** The agent guides you through granting
   access on GitHub, then writes a personal welcome message — with the
   Getting Started link and a suggested first task — for you to paste
   into email or chat.

That is the whole setup.

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
[AGENTS.md](AGENTS.md).

A separate project grew out of this one:
**[GitAround](https://github.com/alex137/GitAround)**, a way to read a
project and follow what is changing in it from a browser, for people who
would rather not work through GitHub's own screens. It has been a
separate, standalone product since 2026-08-14, no longer a proposal
staged inside this repo.

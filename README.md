# BestPractice

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
2. **Open the repository in Claude Code or Codex** and paste:

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
[GITHUB_ACTIONS.md](GITHUB_ACTIONS.md). The full practice catalog:
[PRACTICES.md](PRACTICES.md). Slide decks built from plain files:
[deck/](deck/). Git in eight ideas: [GIT.md](GIT.md). Open items and
roadmap: [TODO.md](TODO.md). Repository index for agents:
[AGENTS.md](AGENTS.md).

# BestPractice

<!-- AI assistants working on this repository: read AGENTS.md before
     answering questions or changing files. -->

BestPractice helps people and AI assistants work together on a shared project without losing decisions, repeating work, or passing around outdated files.

This README is for the **project administrator** — the person who sets up the repository and decides how the team works. Project members never need to read it: they get a link to a Getting Started file inside your project with instructions for their own AI tool (see [Onboarding members](#onboarding-members) below).

You work by talking to an AI assistant:

- Ask what the team has already decided.
- Request a change in ordinary language.
- Review what the assistant produced.
- Approve it when it is ready.

Behind the scenes, the project lives in a GitHub repository. GitHub keeps the current files, earlier versions, decisions, open questions, and change history together. That gives every person and every new AI session the same durable project memory.

Think of a hospital chart at shift change: clinicians rotate, but the chart carries every observation, every decision, and the reasoning behind it — if it isn't in the chart, it didn't happen — so the incoming doctor picks up the patient cold and nothing learned on the last shift is lost in the handover. The repository is that chart for your project.

**Nobody on the team needs to be a programmer.** Most day-to-day work happens through conversation. GitHub is the shared filing system underneath it.

## What your members experience

You might ask:

> What did we decide about pricing, and why?

The assistant reads the project and answers from the recorded decisions.

Or you might say:

> This introduction is too technical for customers. Rewrite it in plain English and update anything else that uses the same wording.

The assistant finds the relevant material, makes the changes consistently, checks its work, and records what changed.

You provide the intent and judgment. The assistant handles the files, cross-references, checks, and history.

All of this works from a phone — members can ask, review, and approve from the Claude Code mobile app or their assistant's app. [MOBILE.md](MOBILE.md) has the per-assistant mobile workflows, an iPhone Shortcut, and the current reliability status of each assistant (dated, since platforms change).

## How members get started

Members receive one link: to `GETTING_STARTED.md` in your repository. BestPractice installs that file and keeps it current, with a table of contents and specific instructions for each kind of AI user — Claude (Claude Code), Codex, ChatGPT, and Grok. A member opens the section for their tool, follows a few steps, and starts asking questions; the repository's own instruction files take it from there.

The file is instantiated from [templates/GETTING_STARTED.md.template](templates/GETTING_STARTED.md.template), so improvements to the onboarding instructions propagate to your project whenever your vendored copy of BestPractice is updated ([INSTALL.md](INSTALL.md) §2).

That is the core of BestPractice for your team: you administer the repository; members just talk to their assistant. The rest of this repository supports and safeguards that workflow.

## Why keep the project in GitHub?

A normal chat thread is useful but temporary. Important context may be buried in an old conversation, known to only one person, or missing from another assistant's memory.

BestPractice gives the team a shared, inspectable memory:

- Important decisions are written down.
- Everyone works from the same current information.
- Earlier versions can be reviewed or restored.
- Several people can work without silently overwriting one another.
- A new person or AI session can understand the project by reading its map and asking questions.
- Changes record what happened and why.
- Rules that matter are enforced by automatic checks, not by reminding people.

The repository is the memory. The chat is the way you work with it.

GitHub is the worked example throughout these documents, and BestPractice currently leans on GitHub features (pull requests, Actions checks) deliberately. The layer itself is plain git, markdown, and Python, so equivalents on other hosts such as Gitea can be added later — see [TODO.md](TODO.md).

## What the assistant should read first

Each installed BestPractice project has a small set of orientation files:

- `README.md` — the universal entry point for people and assistants.
- `GETTING_STARTED.md` — how each kind of AI user joins and starts working.
- `AGENTS.md` — how agents must work in this project.
- `MAP.md` — where the project's important knowledge lives.
- `TODO.md` — open work and unresolved questions.
- `GLOSSARY.md` — project-specific language, when needed.

You usually do not need to open these yourself. Their job is to help each new agent session become useful quickly and behave consistently.

The project README carries a short agent-entry block, installed from [templates/README_AGENT_ENTRY.md.template](templates/README_AGENT_ENTRY.md.template): an HTML comment — invisible on the rendered page, but read by any assistant that opens the file — routing agents to `AGENTS.md`, plus one visible line pointing people to `GETTING_STARTED.md`. The README is the router; `AGENTS.md` remains authoritative.

## What happens when something changes?

The assistant should:

1. Work on a separate branch.
2. Read the relevant project context.
3. Make the requested changes.
4. Update related records when necessary.
5. Run or verify the project's checks.
6. Explain what changed and why.
7. Give you direct links to the files for review.
8. Merge only after the change is approved.

This allows several people and AI sessions to work at the same time while GitHub keeps their work separate until it is reviewed.

## You work through critique, not file management

You usually do not need to find a file and edit it yourself. Describe what is wrong, what outcome you want, and any constraints that matter.

Instead of:

> Open `overview.md`, change paragraph three, then search for the same sentence elsewhere.

Say:

> The overview sounds defensive. Make it confident but factual, and carry the new framing through every document that relies on it.

The assistant can then find the affected material, apply the change consistently, and run the checks the project requires.

The full working method — branch-per-thread, plain-text sources, edit by critique, and composed prompts — is in [METHOD.md](METHOD.md). It is where the quality comes from once a project is real, but none of it is required to start.

## Source files and deliverables

The project's lasting knowledge is kept in formats that agents and GitHub can inspect reliably, especially Markdown, HTML, and Python.

Word, Excel, PowerPoint, and PDF files can still be accepted or produced. They are treated as inputs or generated deliverables rather than the only editable source of truth. This makes changes easier to compare, review, combine, and restore.

The same applies to models and analysis: where you might once have built a spreadsheet, the agent maintains a Python model — which you query through the agent, not by reading code — and Excel becomes one more generated output. Files that arrive in office formats are extracted into the plain-text sources by an agent, with the original committed to the repository for the record.

HTML is often the preferred final format because it can remain a single self-contained file while supporting richer layouts, figures, and interaction.

## Presentations

Slide decks follow the same rules. Each slide is its own markdown file, a manifest picks the shipped set, and [deck/build_deck.py](deck/build_deck.py) builds the deck as a single self-contained HTML file that opens in any browser — one build for internal review (with speaker notes), and a separate send build for external sharing with the notes physically removed. Several threads can develop different slides at the same time, and any thread can rebuild the whole deck. The full practice and conventions are in [deck/README.md](deck/README.md).

## Getting started (for administrators)

You need a GitHub account, a repository for the project — brand-new or already full of work, either is fine — and a coding agent that can access it.

1. **Have a repository.** For a new project, create one on GitHub; Private is a sensible default for internal or personal work — and the scrub gate in [INSTALL.md](INSTALL.md) is what keeps private vocabulary out of anything that later leaves the repo. An existing repository needs no preparation.
2. **Open the repository in a coding agent.**
3. **Paste a bootstrap prompt** like this as your first message, filling in the two blanks:

   ```
   Install BestPractice into this repo. Fetch the public repo
   https://github.com/alex137/BestPractice (add it to this session, or clone
   it) and copy its working tree into process/upstream/ here. Then follow
   process/upstream/INSTALL.md §1 to instantiate it:

   - This repo is about: <one or two sentences on your project>.
   - Words/names that must never appear in the public vendored tree:
     <your project's private names and code words, for the scrub blocklist>.

   Create MAP.md, TODO.md, GLOSSARY.md, AGENTS.md and GETTING_STARTED.md
   from the templates, apply the harness adapter for this agent
   (templates/harness/), install the README agent-entry block, write
   process/manifest.json, run
   python3 process/upstream/tools/practice_audit.py (it must pass), and
   commit everything on a branch.
   ```

   The second blank matters even for a solo project: it is where you decide, before anything is generated, which private names must never leak. (You can instead just ask the agent to follow [INSTALL.md](INSTALL.md) and answer its questions as it goes.)
4. **Review and merge.** Skim the generated files — especially the instructions file, which is the contract every future session works under, and `GETTING_STARTED.md`, which is what your members will see first.
5. **Enable the repository checks** described in [GitHub Actions setup](GITHUB_ACTIONS.md).
6. **Work normally** — name the repository to your assistant and give it questions or critiques.

New to GitHub? Read [Git, minimally](GIT.md). It explains only the concepts this workflow needs.

## Onboarding members

Adding someone to the project is two steps:

1. **Give them access on GitHub.** For a personal repository: repository **Settings → Collaborators → Add people**. In an organization, use your existing teams. Read access lets a member's assistant answer questions; write access lets it propose changes on branches. Whether they can merge is up to you — see the permissions idea in [Git, minimally](GIT.md).
2. **Ask your project's agent to write their welcome.** For example: *"Generate a short welcome message for Dana, who joins the project to work on customer research and uses ChatGPT. Include the link to GETTING_STARTED.md, point out the section for their tool, and suggest a first task from TODO.md."* Paste the result into email, Slack, or wherever you talk to them.

The member opens `GETTING_STARTED.md`, follows the section for their assistant, and starts asking questions. Nothing else to install, and nothing to teach them yourself.

## For installers and maintainers

The beginner workflow above is intentionally small. The detailed machinery remains documented here:

| Path | Purpose |
|---|---|
| [INSTALL.md](INSTALL.md) | Install, update, and contribute the practice layer. |
| [MOBILE.md](MOBILE.md) | Work from ChatGPT or Claude Code on a phone and create an iPhone Shortcut. |
| [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) | Install and require repository checks that agents without a terminal can use. |
| [PRACTICES.md](PRACTICES.md) | The full catalog of rules, motivations, and implementation guidance. |
| [GIT.md](GIT.md) | The Git and GitHub concepts needed by this workflow. |
| [METHOD.md](METHOD.md) | The working method: branches per thread, plain-text sources, critique, composed prompts. |
| [TODO.md](TODO.md) | Open items and roadmap for the practice layer itself. |
| [templates/](templates/) | Project instructions, maps, task lists, glossaries, README entry block, workflows, and agent adapters. |
| [tools/](tools/) | Portable checks and check-in tools. |
| [deck/](deck/) | The presentation system and sample deck. |

BestPractice itself is the reusable practice layer. Install it into another repository, adapt the project-specific files there, and send general improvements back here through a pull request — abstracted and scrubbed per [INSTALL.md](INSTALL.md) §4, so patterns travel but private subject matter never does. The merged check-in pull requests are this repo's changelog: each one is a practice improvement earned in a real project ([PR #1](https://github.com/alex137/BestPractice/pull/1) was the first).

## The idea in one sentence

**Keep the project's memory in GitHub, and let people work with that memory through conversation.**

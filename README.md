# BestPractice

> **Working with an AI assistant?** Ask it: “Work on `alex137/BestPractice`.
> Start with its README and follow the repository's agent instructions before
> answering.” Agents working on this repository should then read
> [AGENTS.md](AGENTS.md). See [Working on a phone](MOBILE.md) for ChatGPT,
> Claude Code, and iPhone Shortcut setup.

BestPractice helps people and AI assistants work together on a shared project without losing decisions, repeating work, or passing around outdated files.

You work by talking to an AI assistant:

- Ask what the team has already decided.
- Request a change in ordinary language.
- Review what the assistant produced.
- Approve it when it is ready.

Behind the scenes, the project lives in a GitHub repository. GitHub keeps the current files, earlier versions, decisions, open questions, and change history together. That gives every person and every new AI session the same durable project memory.

**You do not need to be a programmer.** Most day-to-day work happens through conversation. GitHub is the shared filing system underneath it.

## What using it feels like

You might ask:

> What did we decide about pricing, and why?

The assistant reads the project and answers from the recorded decisions.

Or you might say:

> This introduction is too technical for customers. Rewrite it in plain English and update anything else that uses the same wording.

The assistant finds the relevant material, makes the changes consistently, checks its work, and records what changed.

You provide the intent and judgment. The assistant handles the files, cross-references, checks, and history.

## The basic workflow

1. Open the project with an AI assistant that can access its GitHub repository.
2. Tell the assistant to start with the README and follow the repository's agent instructions.
3. Tell the assistant what you want to know or change.
4. Review its answer or proposed changes.
5. Approve the change so the rest of the team receives it.

That is the core of BestPractice. The rest of this repository supports and safeguards that workflow.

## Why keep the project in GitHub?

A normal chat thread is useful but temporary. Important context may be buried in an old conversation, known to only one person, or missing from another assistant's memory.

BestPractice gives the team a shared, inspectable memory:

- Important decisions are written down.
- Everyone works from the same current information.
- Earlier versions can be reviewed or restored.
- Several people can work without silently overwriting one another.
- A new person or AI session can understand the project by reading its map and asking questions.
- Changes record what happened and why.

The repository is the memory. The chat is the way you work with it.

## Working from a phone

BestPractice can be driven from a phone. The simplest universal starting instruction is:

> Work on `OWNER/REPOSITORY`. Start with its README and follow the repository's agent instructions before answering.

A BestPractice repository's README routes the assistant to `AGENTS.md`, which contains the canonical working rules, and `MAP.md`, which locates the project's knowledge.

Claude Code can load repository-backed instructions through its coding-agent interface. A GitHub-connected ChatGPT conversation needs the short starting instruction at the beginning of each new project conversation. Repository checks such as Markdown lint can run through GitHub Actions even when the chat has no local terminal.

See [Working with BestPractice on a phone](MOBILE.md) for:

- Claude Code and ChatGPT mobile workflows;
- the compact and defensive starting instructions;
- an iPhone Shortcut that selects a repository, asks for a task, prepares the prompt, and opens ChatGPT;
- a text-replacement alternative; and
- reviewing branches, checks, and pull requests from a phone.

*Platform behavior verified August 2, 2026. Product interfaces and connector capabilities can change.*

## What the assistant should read first

Each installed BestPractice project has a small set of orientation files:

- `README.md` — the universal entry point for people and assistants.
- `AGENTS.md` — how agents must work in this project.
- `MAP.md` — where the project's important knowledge lives.
- `TODO.md` — open work and unresolved questions.
- `GLOSSARY.md` — project-specific language, when needed.

You usually do not need to open these yourself. Their job is to help each new agent session become useful quickly and behave consistently.

The README should contain a short marked block that points assistants to `AGENTS.md` and `MAP.md`. Install it from [templates/README_AGENT_ENTRY.md.template](templates/README_AGENT_ENTRY.md.template). The README is the router; `AGENTS.md` remains authoritative.

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

## Source files and deliverables

The project's lasting knowledge is kept in formats that agents and GitHub can inspect reliably, especially Markdown, HTML, and Python.

Word, Excel, PowerPoint, and PDF files can still be accepted or produced. They are treated as inputs or generated deliverables rather than the only editable source of truth. This makes changes easier to compare, review, combine, and restore.

HTML is often the preferred final format because it can remain a single self-contained file while supporting richer layouts, figures, and interaction.

## Getting started

You need:

- A GitHub account.
- A private or public GitHub repository for the project.
- An AI assistant that can work with the repository.

For a new project:

1. Create a GitHub repository. Private is a sensible default for internal or personal work.
2. Open the repository in a coding agent.
3. Ask the agent to install BestPractice by following [INSTALL.md](INSTALL.md).
4. Answer the agent's questions about the project.
5. Review the generated README entry block, project map, and instructions.
6. Enable the repository checks described in [GitHub Actions setup](GITHUB_ACTIONS.md).
7. Begin working by naming the repository, directing the assistant to its README, and giving questions or critiques.

New to GitHub? Read [Git, minimally](GIT.md). It explains only the concepts this workflow needs.

## For installers and maintainers

The beginner workflow above is intentionally small. The detailed machinery remains documented here:

| Path | Purpose |
|---|---|
| [INSTALL.md](INSTALL.md) | Install, update, and contribute the practice layer. |
| [MOBILE.md](MOBILE.md) | Work from ChatGPT or Claude Code on a phone and create an iPhone Shortcut. |
| [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) | Install and require repository checks that agents without a terminal can use. |
| [PRACTICES.md](PRACTICES.md) | The full catalog of rules, motivations, and implementation guidance. |
| [GIT.md](GIT.md) | The Git and GitHub concepts needed by this workflow. |
| [templates/](templates/) | Project instructions, maps, task lists, glossaries, README entry block, workflows, and agent adapters. |
| [tools/](tools/) | Portable checks and check-in tools. |
| [deck/](deck/) | The presentation system and sample deck. |

BestPractice itself is the reusable practice layer. Install it into another repository, adapt the project-specific files there, and send general improvements back here through a pull request.

## The idea in one sentence

**Keep the project's memory in GitHub, and let people work with that memory through conversation.**

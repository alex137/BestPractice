# BestPractice

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
2. Tell the assistant what you want to know or change.
3. Let it read the project instructions and relevant files.
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

BestPractice can be driven from a phone, but Claude and ChatGPT currently enter the project in different ways.

### Claude on mobile

Claude has a separate Claude Code experience in its mobile app. Open the repository-backed Code session and work there as you would on a computer.

Claude Code reads its repository instructions as part of the coding-agent workflow. In a BestPractice project, the adapter points Claude to the canonical project instructions in `AGENTS.md`.

A typical mobile request is simply:

> Review the project context, then tell me what needs my attention today.

Or:

> The customer summary is too technical. Make it clearer, check related documents, and show me what changed.

Because the session is operating as Claude Code, it can follow the repository workflow, edit files, run checks, and prepare changes for review.

*Platform behavior verified August 2, 2026. Product interfaces can change.*

### ChatGPT on mobile

ChatGPT can connect to GitHub and read or modify repositories through the connected GitHub tools. However, an ordinary ChatGPT conversation does **not** automatically adopt the repository's `AGENTS.md` instructions merely because the repository is connected.

Start each new ChatGPT project conversation with this short instruction:

> Work on the GitHub repository `OWNER/REPOSITORY` as a BestPractice agent. Before answering, read the root `AGENTS.md`, then follow its links to `MAP.md` and any other instructions relevant to this task. Treat the repository as the shared project memory. Use a branch for changes, follow the repository's checks, and finish file-changing replies with links to the files touched.

Replace `OWNER/REPOSITORY` with the repository name, for example `alex137/BestPractice`.

After that, give the actual request:

> Rewrite the opening for non-technical readers. Preserve the underlying meaning, check related documentation, and prepare the change for review.

The opening instruction is a **session bootstrap**. It tells ChatGPT to load the same project frame that a coding-agent environment would normally load automatically.

Keep the bootstrap in a phone note or text shortcut so starting a new project session takes one paste.

*GitHub-connected ChatGPT behavior verified August 2, 2026. Product interfaces and connector capabilities can change.*

## What the assistant should read first

Each BestPractice project has a small set of orientation files:

- `AGENTS.md` — how agents must work in this project.
- `MAP.md` — where the project's important knowledge lives.
- `TODO.md` — open work and unresolved questions.
- `GLOSSARY.md` — project-specific language, when needed.

You usually do not need to open these yourself. Their job is to help each new agent session become useful quickly and behave consistently.

## What happens when something changes?

The assistant should:

1. Work on a separate branch.
2. Read the relevant project context.
3. Make the requested changes.
4. Update related records when necessary.
5. Run the project's checks.
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
5. Review the generated project map and instructions.
6. Begin working by asking questions and giving critiques.

New to GitHub? Read [Git, minimally](GIT.md). It explains only the concepts this workflow needs.

## For installers and maintainers

The beginner workflow above is intentionally small. The detailed machinery remains documented here:

| Path | Purpose |
|---|---|
| [INSTALL.md](INSTALL.md) | Install, update, and contribute the practice layer. |
| [PRACTICES.md](PRACTICES.md) | The full catalog of rules, motivations, and implementation guidance. |
| [GIT.md](GIT.md) | The Git and GitHub concepts needed by this workflow. |
| [templates/](templates/) | Project instructions, maps, task lists, glossaries, and agent adapters. |
| [tools/](tools/) | Portable checks and check-in tools. |
| [deck/](deck/) | The presentation system and sample deck. |

BestPractice itself is the reusable practice layer. Install it into another repository, adapt the project-specific files there, and send general improvements back here through a pull request.

## The idea in one sentence

**Keep the project's memory in GitHub, and let people work with that memory through conversation.**

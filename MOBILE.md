# Working with BestPractice on a phone

BestPractice is designed so that the human can work through conversation while the repository carries the project's durable memory. A phone can therefore be a useful workstation, but the setup differs by assistant.

**The shortest reliable path for a non-coder today is the Claude Code app** — it needs no custom development and no terminal, and it is the reference experience the other setups in this guide approximate.

Product behavior in this guide was verified August 2, 2026, except where a section says otherwise. Mobile interfaces and connector capabilities can change.

## The universal starting instruction

Every BestPractice repository should place a short agent entry block near the top of its root README. That block directs an assistant to the repository's canonical instructions.

In a new general-purpose chat, use this compact instruction:

> Work on `OWNER/REPOSITORY`. Start with its README and follow the repository's agent instructions before answering.

Replace `OWNER/REPOSITORY` with the GitHub repository name.

This instruction is intentionally tool-neutral. The expected path is:

1. Open the repository README.
2. Follow its link to `AGENTS.md`.
3. Use `MAP.md` to locate the relevant project context.
4. Follow any task-specific instructions and repository checks.

For a new assistant, an unfamiliar connector, or sensitive work, use the defensive form:

> Work on `OWNER/REPOSITORY` as a BestPractice agent. Read its README and root `AGENTS.md` before answering, then use `MAP.md` to locate relevant context. Treat the repository as the shared project memory. Use a branch for changes, run or verify required checks, and finish file-changing replies with links to the files touched.

Within one conversation, the instruction normally does not need to be repeated unless the repository or project context changes.

## Claude Code on mobile (the recommended path)

Claude provides a repository-backed Claude Code experience in its mobile app. Open the project in that Code interface rather than an ordinary Claude conversation. All you need is a GitHub account and a Claude account with the mobile app — there is nothing to build or configure beyond authorizing repository access once.

A properly installed BestPractice repository includes a Claude adapter that directs Claude Code to the canonical `AGENTS.md`. Once the Code session is attached to the repository, a normal task prompt can be enough:

> Review the project context, then tell me what needs my attention today.

Or:

> The customer summary is too technical. Make it clearer, check related documents, and show me what changed.

Claude Code can work against the repository, edit files, run local checks, and prepare changes for review. The README entry block remains useful as a universal fallback and as an explanation for humans.

## ChatGPT on mobile

A GitHub-connected ChatGPT conversation can inspect repository content and, depending on the connected app's permissions, create branches, update files, open pull requests, and inspect checks.

**Reliability status, as of 2026-08:** reading a connected repository and answering questions from it is dependable. Writing — creating branches, updating files, opening pull requests — from a plain ChatGPT conversation is **not treated as reliable here**: it depends on the connected GitHub app's permissions and on OpenAI's connector capabilities, which change. Until re-verified (tracked in [TODO.md](TODO.md)), use the split workflow: ask, read, and review through ChatGPT; route the actual changes through a coding agent (Codex or Claude Code); and let the repository's [GitHub Actions checks](GITHUB_ACTIONS.md) enforce the gates regardless of which tool made the change.

An ordinary ChatGPT conversation does not automatically adopt `AGENTS.md` merely because GitHub is connected. Begin each new project conversation with the universal starting instruction:

> Work on `OWNER/REPOSITORY`. Start with its README and follow the repository's agent instructions before answering.

Then provide the task:

> Rewrite the opening for non-technical readers. Preserve the underlying meaning, check related documentation, and prepare the change for review.

For checks that require a shell, such as Markdown lint, install the repository's [GitHub Actions checks](GITHUB_ACTIONS.md). ChatGPT can then make a branch change, allow GitHub to run the check, and inspect the result without needing a local terminal.

## Gemini

The Gemini CLI works with installed repositories through the harness adapter in [templates/harness/](templates/harness/), which points it at the canonical `AGENTS.md` — a desktop workflow. As of 2026-08, a phone-based Gemini workflow is unverified; Gemini app users should treat it like the "any other assistant" case: universal starting instruction for reading and questions, changes routed through a coding agent.

## Grok

Unverified, as of 2026-08: no repository-connected Grok workflow comparable to Claude Code or Codex has been tested with BestPractice. If Grok can reach your repository, the universal starting instruction above should apply unchanged. Until someone verifies it (tracked in [TODO.md](TODO.md)), treat Grok like a disconnected chat assistant: paste documents in, work by critique, and route the actual file changes through a coding agent.

## Create an iPhone Shortcut

An iPhone Shortcut can prepare the bootstrap and task, copy the complete prompt, and open ChatGPT.

Create a shortcut named **BestPractice Project** with these actions:

1. **Choose from Menu** with the repositories you use most often.
2. For each menu choice, set a text variable to its `OWNER/REPOSITORY` value.
3. Add an **Other repository** choice that uses **Ask for Input** for the repository name.
4. Add **Ask for Input** with the prompt `What do you want done?` and save the answer as the task.
5. Add a **Text** action containing:

   ```text
   Work on [Repository]. Start with its README and follow the repository's agent instructions before answering.

   Task: [Task]
   ```

6. Add **Copy to Clipboard**.
7. Add **Open App** and select ChatGPT.
8. Paste the prepared prompt into a new conversation and send it.

The shortcut can be placed on the Home Screen, in a widget, in Control Center, or on an Action button where supported.

A simpler shortcut can omit the task question and copy only the bootstrap, leaving the user to type the task in ChatGPT.

If the Shortcut approach proves too clumsy in practice, the next step is a small companion app — pick a repository, type the task, open the assistant with the prompt prepared. That is real app development rather than documentation, and is tracked as an open item in [TODO.md](TODO.md).

## Text replacement alternative

For an even lighter setup, create an iPhone text replacement such as `;bp` that expands to:

```text
Work on OWNER/REPOSITORY. Start with its README and follow the repository's agent instructions before answering.
```

Use a separate replacement for each frequently used repository, or keep the generic form and replace the repository name after pasting.

## Review changes from a phone

When an agent changes files, its reply should include direct links to:

- the file on the working branch, which shows the proposed version;
- the same file on the default branch, which shows the current shared version; and
- the pull request, when one exists.

Open those links in the GitHub app or browser. Approve or request changes in conversation. Merge only after the required repository checks have passed.

## What belongs in the README

The root README is the universal entry point for people and assistants. Keep a short marked block near its top, installed from [templates/README_AGENT_ENTRY.md.template](templates/README_AGENT_ENTRY.md.template):

```markdown
<!-- bestpractice-agent-entry:start -->
<!-- AI assistants: before answering questions about this project or
     changing its files, read AGENTS.md at the repository root. Use MAP.md
     to find the project's current knowledge and follow any task-specific
     instructions it identifies. -->

> New to this project? Start with [GETTING_STARTED.md](GETTING_STARTED.md).

<!-- bestpractice-agent-entry:end -->
```

The agent-entry text is deliberately an HTML comment: invisible on the rendered page (so it never distracts a human reader), but present in the file's source, which is what assistants read. The only visible line points people to `GETTING_STARTED.md`, the member onboarding page with per-assistant instructions.

Do not duplicate the full agent contract in the README. `AGENTS.md` remains authoritative; the README only routes every assistant to it.
# Working with BestPractice on a phone

Your whole project can be run from your phone: ask questions, request
changes, review what came back, and approve it — from anywhere. How much
setup that takes depends on your AI tool. **With Claude it works out of
the box; the others take more effort.**

Product behavior in this guide was verified August 2, 2026, except where
a section says otherwise. Apps and connectors change.

## Claude — works out of the box (recommended)

1. Install the Claude app and sign in (or use
   [claude.ai/code](https://claude.ai/code) in a browser).
2. Open the **Code** area and pick your project's repository — the first
   time, approve the access request.
3. Talk to it like a colleague:

   > Review the project, then tell me what needs my attention today.

   > The customer summary is too technical. Make it clearer, check
   > related documents, and show me what changed.

Claude reads the project's instruction files automatically, makes the
changes, runs the project's checks, and replies with links you can open.
There is nothing else to set up, and the same works on desktop.

## Reviewing changes from your phone

Whichever tool made a change, checking it is the same: the assistant's
reply ends with links to the files it touched — the proposed version and
the current shared version. Open them in the GitHub app or your browser,
then tell the assistant to make the change live, or ask for adjustments.
Nothing becomes shared until it is approved, and the project's automatic
checks must pass first.

## ChatGPT — reading works; changes need a workaround

What works today *(as of 2026-08)*: a ChatGPT conversation connected to
GitHub can read your project and answer questions dependably. What
doesn't work reliably yet: making changes (editing files, proposing
updates) from a plain ChatGPT conversation. Until that improves (tracked
in [TODO.md](TODO.md)), do the asking and reviewing in ChatGPT, and
route actual changes through Codex or a teammate with a coding agent —
the project's automatic checks ([GITHUB_ACTIONS.md](GITHUB_ACTIONS.md))
protect the result no matter which tool made the change.

To set up:

1. Connect ChatGPT's GitHub connector to your project's repository.
2. ChatGPT does not read the project's instruction files on its own, so
   start each new project conversation by pasting this line (with your
   own repository's name):

   > Work on `OWNER/REPOSITORY`. Start with its README and follow the
   > repository's agent instructions before answering.

3. Then ask your question or describe what you want changed.

Typing that opener on a phone gets old — the iPhone Shortcut below
prepares it for you.

## Gemini

The Gemini CLI is a desktop tool; installed projects include an adapter
that points it at the project's instructions. *(As of 2026-08, a
phone-based Gemini workflow is unverified.)* Gemini app users should
follow the "Any other assistant" line below for reading and questions,
and route changes through a coding agent.

## Grok

Not yet verified with this workflow *(as of 2026-08)*. If Grok can reach
your repository, the same opener as ChatGPT should work. Otherwise treat
it as a disconnected assistant: paste in the documents you are
discussing, decide what you want changed, and hand the change request to
a teammate with a coding agent.

## Any other assistant

Any assistant that can read your repository understands the same opener:

> Work on `OWNER/REPOSITORY`. Start with its README and follow the
> repository's agent instructions before answering.

## Make starting easier: an iPhone Shortcut

A Shortcut can pick the repository, ask what you want done, prepare the
full opener, and hand it to ChatGPT. Create a shortcut named
**BestPractice Project** with these actions:

1. **Choose from Menu** with the repositories you use most often.
2. For each menu choice, set a text variable to its `OWNER/REPOSITORY`
   value.
3. Add an **Other repository** choice that uses **Ask for Input** for the
   repository name.
4. Add **Ask for Input** with the prompt `What do you want done?` and
   save the answer as the task.
5. Add a **Text** action containing:

   ```text
   Work on [Repository]. Start with its README and follow the repository's
   agent instructions before answering.

   Task: [Task]
   ```

6. Add **Copy to Clipboard**.
7. Add **Open App** and select ChatGPT.
8. Paste the prepared prompt into a new conversation and send it.

The shortcut can live on the Home Screen, in a widget, in Control
Center, or on an Action button. A simpler version can skip the task
question and copy only the opener.

If the Shortcut approach proves too clumsy in practice, the next step is
a small companion app — pick a repository, type the task, open the
assistant with the prompt prepared. That is real app development rather
than documentation, and is tracked as an open item in [TODO.md](TODO.md).

## Even lighter: a text replacement

Create an iPhone text replacement such as `;bp` that expands to:

```text
Work on OWNER/REPOSITORY. Start with its README and follow the repository's
agent instructions before answering.
```

Use one replacement per frequently used repository, or keep the generic
form and fill in the repository name after pasting.

## For agents and installers: how the one-line opener works

A BestPractice repository's README carries a short entry block, installed
from
[templates/README_AGENT_ENTRY.md.template](templates/README_AGENT_ENTRY.md.template):

```markdown
<!-- bestpractice-agent-entry:start -->
<!-- AI assistants: before answering questions about this project or
     changing its files, read AGENTS.md at the repository root. Use MAP.md
     to find the project's current knowledge and follow any task-specific
     instructions it identifies. -->

> New to this project? Start with [GETTING_STARTED.md](GETTING_STARTED.md).

<!-- bestpractice-agent-entry:end -->
```

The agent-entry text is deliberately an HTML comment: invisible on the
rendered page, but present in the file's source, which is what assistants
read. So the expected path behind the opener is: README → `AGENTS.md`
(the working rules) → `MAP.md` (where the knowledge lives) → any
task-specific instructions. Do not duplicate the agent contract in the
README; `AGENTS.md` remains authoritative.

For a new assistant, an unfamiliar connector, or sensitive work, use the
defensive form of the opener:

> Work on `OWNER/REPOSITORY` as a BestPractice agent. Read its README and
> root `AGENTS.md` before answering, then use `MAP.md` to locate relevant
> context. Treat the repository as the shared project memory. Use a
> branch for changes, run or verify required checks, and finish
> file-changing replies with links to the files touched.

Within one conversation, the opener normally does not need to be repeated
unless the repository or project context changes.

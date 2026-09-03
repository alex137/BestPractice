# Getting started with `<project name>`

<!-- Template AND rendered sample: this file is readable as-is on GitHub
     (linked from the BestPractice README as the sample members' page)
     and is instantiated per INSTALL.md §1 as GETTING_STARTED.md at the
     dependent repo's root. When instantiating: replace the backticked
     `<placeholders>` with the project's real values and keep the
     section structure so upstream improvements propagate on updates
     (INSTALL.md §2). Assistant-capability statements carry their as-of
     dates (practice 16); refresh them from the upstream MOBILE.md when
     taking updates. -->

Welcome. This project runs on a simple idea: **the project's memory lives
in its repository, and you work with that memory by talking to an AI
assistant.** Ask what the team has decided and why — the assistant
answers from the project's own records. Describe a change you want — the
assistant makes it everywhere it applies, and the team reviews it before
it becomes shared. Decisions don't get lost in chat history, nobody
overwrites anyone's work, and a person who joins today can be useful
within the hour. You do not need to be a programmer.

## How contributing works — five steps

One difference from tools like Google Docs matters here: in Google Docs,
your edits appear for everyone instantly. In this project, **your changes
are drafted privately and join the shared project only after review.**
That is what makes it safe for many people — and many AI assistants — to
work at the same time. The whole loop:

1. **Set up your AI tool** (one time). See
   [Setting up your AI tool](#setting-up-your-ai-tool) below for your
   tool's exact steps.
2. **Ask what needs doing.** Say *"What are the open items?"* — the
   assistant reads the project's to-do list for you. (This step is
   optional: changes you think of yourself are just as welcome.)
3. **Describe the change you want.** The assistant makes it on your own
   private working copy — a version of the project only your conversation
   touches, so nothing you do can break the shared project.
4. **Look at what it made.** The assistant's reply ends with links to the
   changed files; open them and ask for adjustments until it's right.
5. **Say "propose this to the team."** The assistant packages your change
   for review — the technical name is a *pull request* — and an
   administrator, not you, decides when it joins the shared project.
   Until that happens, nobody else sees your change: unlike Google Docs,
   nothing becomes shared automatically.

## How the project remembers new rules

You don't have to ask for this by name — it happens as part of ordinary
conversation. If you say something like *"always name these a certain
way"*, *"never merge without running the tests"*, or *"from now on, do
X"*, the assistant will notice and offer to write that down as one of
this project's own working rules, so every future conversation follows it
too — not just the one you're having right now. It always tells you
plainly when it's doing this and where the rule is going, and nothing
becomes official until it's reviewed and approved the same way any other
change is (see the five steps above) — you're never signing up for
something without seeing it first.

## Setting up your AI tool

Before any of it works, an administrator must have given your GitHub
account access to `<OWNER/REPOSITORY>` — if you don't have access yet,
ask `<administrator contact>`. Then follow the section for your tool:

### Claude users (Claude Code)

The most complete experience, on web, desktop, or phone. *(As of
2026-08.)*

1. Go to [claude.ai/code](https://claude.ai/code) (or open the Claude
   mobile app's Code area).
2. Start a new session on `<OWNER/REPOSITORY>` — the first time, approve
   the GitHub authorization it requests.
3. Ask your first question, e.g.: *"Review the project context, then tell
   me what needs my attention."*

Claude Code reads the project's instruction files automatically. Nothing
else to set up.

### Codex users

*(As of 2026-08.)*

1. Open Codex (in ChatGPT or at its own interface) and connect it to
   `<OWNER/REPOSITORY>`.
2. Codex follows the project's instruction files automatically.
3. Give it a task or a question, the same way as any coding session.

### ChatGPT users

A plain ChatGPT conversation with the GitHub connector can **read** this
project and answer questions dependably. **Making changes** from a plain
conversation is not currently reliable *(as of 2026-08)* — have Codex
make the changes, or hand them to a teammate who uses Claude Code or
Codex; the project's automatic checks protect the result either way.

1. Connect the GitHub connector to `<OWNER/REPOSITORY>` if you haven't.
2. Start each new project conversation with:

   > Work on `<OWNER/REPOSITORY>`. Start with its README and follow the
   > repository's agent instructions before answering.

3. Then ask your question or describe the change you want.

Working from an iPhone a lot? This project includes an iPhone Shortcut
recipe that prepares this starting message for you — see the phone guide
at `process/upstream/MOBILE.md`.

### Gemini users

The Gemini CLI (a desktop tool) is already wired to this project's
instructions — nothing for you to configure. *(As of 2026-08; a
phone-based Gemini workflow is unverified.)* If you use the Gemini app
rather than the CLI, follow the "Any other assistant" line below for
reading and questions, and hand changes to a teammate who uses Claude
Code or Codex.

### Grok users

Not yet verified with this workflow *(as of 2026-08)*. If Grok can reach
the repository, use the same starting instruction as ChatGPT users above.
Otherwise, treat Grok as a disconnected assistant: paste in the documents
you're discussing, work out what you want changed, and hand the change
request to a teammate who uses Claude Code or Codex.

### Any other assistant

Any assistant that can read this repository understands the same one-line
opener:

> Work on `<OWNER/REPOSITORY>`. Start with its README and follow the
> repository's agent instructions before answering.

## Tips while you work

- **Ask before hunting.** The fastest way to learn anything about this
  project is to ask your assistant — it reads the project's map and
  decision records for you. You should rarely need to open a file
  yourself.
- **Ask what's new.** Approved changes don't appear in your old
  conversations by themselves. Each new session, the assistant catches
  you up on what changed since you last worked — and you can ask
  *"what's new?"* at any time. If your in-progress work has fallen
  behind the shared project, the assistant will offer to bring it up to
  date.
- **Claim what you take on.** When you start an item from the to-do
  list, the assistant marks it with your name so teammates don't
  duplicate the work — and it will tell you if someone else is already on
  what you're about to start. Big or opinionated changes get flagged to
  the teammates who care before they join the shared project — and the
  system learns who cares about what from the project's own history (who
  wrote what, who pushed back on what); nobody has to declare it up
  front.
- **Change by describing, not editing.** Say what is wrong and what you
  want instead; the assistant makes the change everywhere it applies and
  the team reviews it before it becomes shared. Don't hand-edit files —
  a hand edit skips the checks the project relies on.
- **Your work is credited to you.** The assistant records you as the
  author of the changes it makes for you (it appears alongside as a
  co-author), so the project's history shows your contributions as
  yours.
- **Office files are welcome, but they're for input and output — not
  where the project's knowledge lives.** Send the assistant a Word,
  Excel, PowerPoint, or PDF file and it will extract what matters into
  the project (the original is kept for the record). Ask for one and it
  will be generated for you — though a single-file interactive HTML page
  is usually the better deliverable, and slide decks are built the same
  way (each slide its own file, so several people can develop slides at
  once).
- **Compose bigger requests.** For anything substantial, draft your
  request in a notes app first, then paste it — the assistant's output
  quality tracks the clarity of what you hand it. (More habits like this
  in the project's method guide: `process/upstream/METHOD.md`.)

## For the administrator: approving changes

Members draft changes on their own private copies; nothing joins the
shared project until you approve it. Your side of the loop is also just
conversation:

- **Ask "what's waiting for me?"** Your assistant lists each pending
  proposal and summarizes it in plain language: what changed, who made
  it, and whether it touches anything you have cared about before.
- **The merge magic.** If two proposals collide — both reworked the same
  passage, say — the assistant integrates them for you and shows the
  combined result before anything becomes shared. You never untangle
  conflicts yourself.
- **Three answers, all in chat:** *approve* ("merge it"), *adjust*
  ("merge it, but keep the old title"), or *send back* ("ask the author
  to reconsider the tone — here's why"). Approving makes the change
  shared for everyone; your reasoning is recorded either way.
- **Routine things stay quick.** Most proposals are safe to approve in
  seconds; the assistant tells you when one deserves a closer look —
  because it reworks someone's writing, collides with other work, or
  touches something you've pushed back on before.

### Automatic checks installed for this project

<!-- Standing note (INSTALL.md §1 step 8 / practice 37): every
     GitHub-specific requirement this project depends on gets a line
     here, naming what it is and the exact click-path to configure it —
     not just a mention in the internal install log under
     `process/upstream/`. Add a line whenever a future install step
     introduces a new one (a required secret, a new required check). -->

- **A Markdown check runs on every pull request** (a GitHub Actions
  workflow) and catches a couple of specific formatting mistakes before
  they reach the shared project. It needs no maintenance. If it doesn't
  appear on a pull request's checks, GitHub Actions may be disabled for
  this repository — an administrator can turn it on at repository
  **Settings → Actions**. Details: `process/upstream/GITHUB_ACTIONS.md`.
- **Every pull request opens with a standard template** — what changed,
  why, files touched, and a short checklist. An unchecked box on that
  checklist is normal; it means that gate didn't apply to this particular
  change, not that something was skipped.

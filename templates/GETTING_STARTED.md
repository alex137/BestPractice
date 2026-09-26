# Getting Started With `<project name>`

<!-- Template AND rendered sample: this file is readable as-is on GitHub
     (linked from the Precedent README as the sample members' page)
     and is instantiated per INSTALL.md §1 as GETTING_STARTED.md at the
     dependent repo's root. When instantiating: replace the backticked
     `<placeholders>` with the project's real values and keep the
     section structure so upstream improvements propagate on updates
     (INSTALL.md §2).

     `<upstream-docs>` IS ONE OF THOSE PLACEHOLDERS, and what it becomes
     depends on which install model this is -- which is why it is a
     placeholder rather than a path. INSTALL.md §1 vendors Precedent's
     prose into the repo, so it becomes `process/upstream`. §0 vendors the
     practices and the engine and NO prose, so there is no local copy to
     point at and it becomes the upstream URL prefix
     `https://github.com/alex137/BestPractice/blob/main`. Until 2026-09-10
     this file wrote `process/upstream/` outright and §0 step 5 said to
     install it "unchanged by which install model this is", so a §0 install
     shipped its members three dead references on day one. Assistant-capability statements carry their as-of
     dates (practice `volatile-rules-carry-dates`); refresh them from the upstream documentation/MOBILE.md when
     taking updates. -->

Welcome. This project runs on a simple idea: **the project's memory lives
in its repository, and you work with that memory by talking to an AI
Assistant.** Ask what the team has decided and why — the AI Assistant
answers from the project's own records. Describe a change you want — the
AI Assistant makes it everywhere it applies, and the team reviews it before
it becomes shared. Decisions don't get lost in chat history, nobody
overwrites anyone's work, and a person who joins today can be useful
within the hour. You do not need to be a programmer.

## How Contributing Works — Five Steps

One difference from tools like Google Docs matters here: in Google Docs,
your edits appear for everyone instantly. In this project, **your changes
are drafted privately and join the shared project only after review.**
That is what makes it safe for many people — and many AI Assistants — to
work at the same time. The whole loop:

1. **Set up your AI tool** (one time). See
   [Setting up your AI tool](#setting-up-your-ai-tool) below for your
   tool's exact steps.
2. **Ask what needs doing.** Say *"What are the open items?"* — the
   AI Assistant reads the project's to-do list for you. (This step is
   optional: changes you think of yourself are just as welcome.)
3. **Describe the change you want.** The AI Assistant makes it on your own
   private working copy — a version of the project only your conversation
   touches, so nothing you do can break the shared project.
4. **Look at what it made.** The AI Assistant's reply ends with links to
   the changed files; open them and ask for adjustments until it's right.
5. **Say "propose this to the team."** The AI Assistant packages your change
   for review — the technical name is a *pull request* — and says who
   decides when it joins the shared project: for the documents themselves
   that may be you, depending on how your project is set up; for the
   project's settings, checks and rules it is always an administrator.
   Until that happens, nobody else sees your change: unlike Google Docs,
   nothing becomes shared automatically.

## How the Project Remembers New Rules

You don't have to ask for this by name — it happens as part of ordinary
conversation. If you say something like *"always name these a certain
way"*, *"never merge without running the tests"*, or *"from now on, do
X"*, the AI Assistant will notice and offer to write that down as one of
this project's own working rules, so every future conversation follows it
too — not just the one you're having right now. It always tells you
plainly when it's doing this and where the rule is going, and nothing
becomes official until it's reviewed and approved the same way any other
change is (see the five steps above) — you're never signing up for
something without seeing it first.

## Taking Your Rules With You

The rules you add here belong to this project. **Rules that are really
about *you*, or about *your team*, can live somewhere better — in their own
small collection that follows you into every project you work on.**

**One question sorts them.** *Do I want this rule in everything I work
on?* If yes, it belongs in your own personal collection, which follows you
into every project automatically. If it should apply to some projects and
not others, it belongs in a **shared** collection instead — one you switch
on per project, one line each. A shared collection with only you in it is
completely normal; "shared" is about being able to point several projects
at it, not about handing it to other people.

Two kinds are worth making:

- **Your own.** Anything you find yourself asking for again and again — how
  you like things written, what you always want checked, how you prefer to
  be talked to. Write it once instead of re-explaining it in every project.
- **Your team's.** Anything your team keeps re-agreeing in review. A team
  collection settles it in one place, and everyone's assistant follows it.

**You already have what you need to make one.** The tool that sets one up
comes with this project, so there is nothing to install and nothing to ask
anyone for. Say to your assistant:

> I'd like to start my own collection of rules that follows me between
> projects. Can you set one up?

It will make the repository, add your first rules, and connect it to this
project so your sessions start using it.

**Do not wait until you have a lot to say.** Three rules you are tired of
repeating is a perfectly good collection. The shared library this project
draws on started the same way and grew one rule at a time, each written down
the first time somebody got it wrong twice.

## Setting Up Your AI Tool

Before any of it works, an administrator must have given your GitHub
account access to `<OWNER/REPOSITORY>` — if you don't have access yet,
ask `<administrator contact>`. Then follow the section for your tool:

### Claude Users (Claude Code)

The most complete experience, on web, desktop, or phone. *(As of
2026-08.)*

1. Go to [claude.ai/code](https://claude.ai/code) (or open the Claude
   mobile app's Code area).
2. Start a new session on `<OWNER/REPOSITORY>` — the first time, approve
   the GitHub authorization it requests.
3. Ask your first question, e.g.: *"Review the project context, then tell
   me what needs my attention."*

Claude Code reads the project's instruction files automatically — nothing
else to set up for that. **Two things are per-person, though, and neither
happens on its own:**

- **Your own settings.** Your name and timezone on the commits Claude
  makes for you, and — if you or your team have one — your own practices
  repository. [PER_MACHINE_SETUP.md](<upstream-docs>/documentation/PER_MACHINE_SETUP.md)
  is the full copy-paste list; the short version is **environment
  variables** (settings that live on your Claude account, not in this
  repository), added at `claude.ai/code` → the environment this project
  runs in → its **environment variables** page. *(Click-path as of
  2026-09-11 — Anthropic's own guide at
  [code.claude.com/docs/en/claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web)
  is the place to check if it's moved.)*
- **If you'd rather not set those, ask Claude directly instead.** In your
  first message, say something like: *"Please connect to `<your team's or
  your own practices repository>`."* Claude can attach read access to it
  for that one session — the same thing the environment variables do
  automatically, every session, without asking. This only works when that
  repository is owned by the same GitHub account as this project; a
  repository under a different account needs the environment-variable
  route above instead. Skipping both isn't loud about it — your team's
  and your own rules simply won't apply that session — so ask if Claude's
  answers don't seem to reflect something you know your team has agreed
  on.

### Codex Users

*(As of 2026-08.)*

1. Open Codex (in ChatGPT or at its own interface) and connect it to
   `<OWNER/REPOSITORY>`.
2. Codex follows the project's instruction files automatically.
3. Give it a task or a question, the same way as any coding session.

### ChatGPT Users

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
in [MOBILE.md](<upstream-docs>/documentation/MOBILE.md).

### Gemini Users

The Gemini CLI (a desktop tool) is already wired to this project's
instructions — nothing for you to configure. *(As of 2026-08; a
phone-based Gemini workflow is unverified.)* If you use the Gemini app
rather than the CLI, follow the "Any Other AI Assistant" line below for
reading and questions, and hand changes to a teammate who uses Claude
Code or Codex.

### Grok Users

Not yet verified with this workflow *(as of 2026-08)*. If Grok can reach
the repository, use the same starting instruction as ChatGPT users above.
Otherwise, treat Grok as a disconnected AI Assistant: paste in the documents
you're discussing, work out what you want changed, and hand the change
request to a teammate who uses Claude Code or Codex.

### Any Other AI Assistant

Any AI Assistant that can read this repository understands the same
one-line opener:

> Work on `<OWNER/REPOSITORY>`. Start with its README and follow the
> repository's agent instructions before answering.

## Tips While You Work

- **Ask before hunting.** The fastest way to learn anything about this
  project is to ask your AI Assistant — it reads the project's map and
  decision records for you. You should rarely need to open a file
  yourself.
- **Ask what's new.** Approved changes don't appear in your old
  conversations by themselves. Each new session, the AI Assistant
  catches you up on what changed since you last worked — and you can ask
  *"what's new?"* at any time. If your in-progress work has fallen
  behind the shared project, the AI Assistant will offer to bring it up
  to date.
- **Claim what you take on.** When you start an item from the to-do
  list, the AI Assistant marks it with your name so teammates don't
  duplicate the work — and it will tell you if someone else is already on
  what you're about to start. Big or opinionated changes get flagged to
  the teammates who care before they join the shared project — and the
  system learns who cares about what from the project's own history (who
  wrote what, who pushed back on what); nobody has to declare it up
  front.
- **Change by describing, not editing.** Say what is wrong and what you
  want instead; the AI Assistant makes the change everywhere it applies
  and the team reviews it before it becomes shared. Don't hand-edit
  files — a hand edit skips the checks the project relies on.
- **Your work is credited to you.** The AI Assistant records you as the
  author of the changes it makes for you (it appears alongside as a
  co-author), so the project's history shows your contributions as
  yours.
- **Office files are welcome, but they're for input and output — not
  where the project's knowledge lives.** Send the AI Assistant a Word,
  Excel, PowerPoint, or PDF file and it will extract what matters into
  the project (the original is kept for the record). Ask for one and it
  will be generated for you — though a single-file interactive HTML page
  is usually the better deliverable, and slide decks are built the same
  way (each slide its own file, so several people can develop slides at
  once).
- **Compose bigger requests.** For anything substantial, draft your
  request in a notes app first, then paste it — the AI Assistant's
  output quality tracks the clarity of what you hand it. (More habits
  like this in the project's method guide,
  [METHOD.md](<upstream-docs>/documentation/METHOD.md).)

## For the Administrator: Approving Changes

Members draft changes on their own private copies; nothing joins the
shared project until you approve it. Your side of the loop is also just
conversation:

- **Ask "what's waiting for me?"** Your AI Assistant lists each pending
  proposal and summarizes it in plain language: what changed, who made
  it, and whether it touches anything you have cared about before.
- **The merge magic.** If two proposals collide — both reworked the same
  passage, say — the AI Assistant integrates them for you and shows the
  combined result before anything becomes shared. You never untangle
  conflicts yourself.
- **Three answers, all in chat:** *approve* ("merge it"), *adjust*
  ("merge it, but keep the old title"), or *send back* ("ask the author
  to reconsider the tone — here's why"). Approving makes the change
  shared for everyone; your reasoning is recorded either way.
- **Routine things stay quick.** Most proposals are safe to approve in
  seconds; the AI Assistant tells you when one deserves a closer look —
  because it reworks someone's writing, collides with other work, or
  touches something you've pushed back on before.

### Settings Only You Can Turn On

A few things can only be done by hand, in GitHub's own settings pages, by
someone with administrator rights here. None is urgent, and each fails
*quietly* rather than loudly, so they are worth a look when you have a
moment. **Ask the AI Assistant for more specific instructions on any of
them**, or read the full reference at
[GITHUB_SETTINGS.md](<upstream-docs>/documentation/GITHUB_SETTINGS.md).
Click-paths as of <install date>.

- **This project's repository is private**, unless it is meant to be
  public.
- **A developer key, stored in this project** — a personal access token
  (GitHub's name for a key that stands in for a person) that can reach this
  repository, saved under **Settings → Secrets and variables → Actions →
  New repository secret**, named `PRECEDENT_REPO_TOKEN` unless something
  here expects another name. Without it an AI Assistant can prepare
  changes but not push them or open a proposal on the project's behalf.
- **The main line of work is called `main`** — **Settings → General →
  Default branch**. The Markdown check below watches a branch by that exact
  name.
- **Automation is allowed to open proposals** — **Settings → Actions →
  General → Workflow permissions**, with *Allow GitHub Actions to create
  and approve pull requests* ticked.
- **Optional: turn GitHub Actions off here, if this project needs no
  automatic checks on GitHub** — **Settings → Actions → General → Actions
  permissions → Disable actions**. GitHub Actions is the service that runs
  checks on GitHub's computers, and in a private repository each run costs
  minutes from your account. Turned off, a stray check file costs nothing
  at all. The checks that run on your own machine before every push keep
  working. Leave it on if this project relies on a check running on
  GitHub.
- **A few settings inside Claude itself**, if you work in Claude Code on
  the web. Open [claude.ai/code](https://claude.ai/code), go to the
  environment this project runs in, and add these to its **environment
  variables**, with your own values:

  ```
  PRECEDENT_COMMIT_NAME=Your Name
  PRECEDENT_COMMIT_EMAIL=you@example.com
  PRECEDENT_COMMIT_TZ=America/Argentina/Buenos_Aires
  ```

  Without them your work gets committed under the AI Assistant's own
  account rather than your name, with the wrong timezone on it. If you have a
  practices repo of your own, add `PRECEDENT_GIT_TOKEN` (a read-only
  personal access token that can see it) and `PRECEDENT_SOURCE_BASE_URL`
  (`https://github.com/your-account`) too, or your own practices never
  load. **A change here does not reach a session already open** — start a
  new one to test it.

### Automatic Checks Installed for This Project

<!-- Standing note (INSTALL.md §1 step 8 / practice `github-setup-disclosed`): every
     GitHub-specific requirement this project depends on gets a line
     here, naming what it is and the exact click-path to configure it —
     not just a mention in the internal install log under
     `<upstream-docs>/`. Add a line whenever a future install step
     introduces a new one (a required secret, a new required check). -->

- **Before anything reaches `main`, GitHub checks it once** (the GitHub
  Actions workflow `light-check.yml`, on the pull request into `main`).
  Every other push is checked on your own machine before it leaves. In a
  public repository a leak check (`leak-gate.yml`) also runs on every push
  and refuses anything that would publish something private. Neither needs
  maintenance. If they don't appear on a pull request's checks, GitHub
  Actions may be disabled for this repository — an administrator can turn
  it on at repository **Settings → Actions**.
- **Your writing is checked before it is saved, not after.** A formatting
  check runs on every commit, so a broken link or a malformed heading is
  caught while you are still working rather than once it is shared. This
  one is not a GitHub check and needs nothing switched on.
- **Every pull request opens with a standard template** — what changed,
  why, files touched, and a short checklist. An unchecked box on that
  checklist is normal; it means that gate didn't apply to this particular
  change, not that something was skipped.

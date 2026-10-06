# SETUP — Guided Install, for the Agent Reading This

You are an AI coding agent. A project administrator has opened a session
on their repository and pasted a link to this file. Your job: install
Precedent into that repository while guiding them in plain language.
Assume they are not a programmer — explain simply, ask little, and do all
technical work yourself.

This conversation installs [INSTALL.md](INSTALL.md) §0 — the Precedent
loader: the practice catalogue, the resident block and occasion index every
session reads, and the enforced checks — with one command,
[tools/precedent_install.py](tools/precedent_install.py), which does the file
work and then lists what is left for you to adapt. **Since 2026-09-14 this is
the default** (Morgan, on the very deep check's recommendation; `strength:
assented`): until then this page installed §1, the classic vendored model,
which turns on none of the loader the rest of this repository describes.
**§1 is no longer an install path at all** (retired 2026-09-23): a project
that took it ran with every practice copied in and none in force. There is
nothing to choose here — this page installs §0, always.

## The Conversation

1. **Confirm the target.** The repository this session is opened on is
   the project. Tell the administrator, in one sentence, what you are
   about to set up: a practice layer that gives their project durable
   memory, safe concurrent work, and a Getting Started page for members.
2. **Ask exactly five questions** — the canonical list, in
   [spec/INSTALL_QUESTIONS.md](https://github.com/alex137/BestPractice/blob/staging/spec/INSTALL_QUESTIONS.md) — together in one
   message, and wait:
   - *What is this project about?* (one or two sentences) — and: fill in
     `MAP.md`'s deliverables and `AGENTS.md`'s quick index now, or leave
     placeholders? (Default: placeholders, filled in a later conversation.)
   - *Are there private names or code words that must never appear in
     anything public?* Explain why in one sentence: parts of the practice
     layer can flow back to a public repository, and this list is the
     guard that keeps their private vocabulary out of it.
   - *Does your team already have its own practices repo, or do you
     personally have one — and if not, would you like one set up now?*
     Explain in one sentence: Precedent is only one of three layers
     this can run — a team's own shared conventions, and one person's own
     facts, can each live in their own repo and be wired in too. Most
     projects have neither yet — that's a complete answer on its own — but
     it costs nothing to offer setting one up in the same conversation, so
     ask rather than assume no. Mention the public set anyone can
     declare, [precedent-shared-writing](https://github.com/themorgan/precedent-shared-writing),
     which a documents project usually wants.
   - *Which AI Assistant will actually be working in this repo* — Claude
     Code, ChatGPT connected to GitHub, or something else? Explain in one
     sentence: an AI Assistant with no access to a terminal needs
     GitHub's own automated checks for things one with terminal access
     does not.
   - *Should the vendored GitHub Actions workflow be on or off?* **Default
     on, since 2026-09-25**: one light check that runs only on a pull
     request into `main` (about one billed minute per merge into `main`),
     plus a leak gate that runs only in a public repository. For an AI
     Assistant with no terminal access (ChatGPT, or anything else with no
     local shell) it is the only place any check can run at all, so say
     so. Say the default out loud and let them override it. If they want
     it off, it takes `"github_ci_workflows": "disabled"` in an individual
     or shared source's `identity.json`
     ([documentation/GITHUB_ACTIONS.md](documentation/GITHUB_ACTIONS.md));
     if they answered "no" to the third question there is nowhere this
     install can record that yet, so say plainly that it stays on until a
     source declares it. **What "declares" means, concretely**: this is
     a standing field in `identity.json` — the person's individual (or
     team) source, never `precedent.json` — so activating it is either
     something you do right now, if this session can reach that source,
     or something the person has to get done in a session that can (Prompt
     Please, if this one isn't it). Either way it is a standing preference
     for every repo that resolves through that identity, not a
     this-repo-only switch, and it takes effect for a given dependent repo
     only the next time that repo installs, migrates, or takes an Update
     Vendors pass — never retroactively, and never instantly across a
     whole fleet at once.
3. **Install without further questions.** Clone the public repo
   `https://github.com/alex137/BestPractice` beside the project (a sibling
   directory, not inside it) **on its `main` branch** — every install
   takes its updates from `main` (`SOURCE_BRANCH` in
   [tools/precedent_vendor_engine.py](tools/precedent_vendor_engine.py),
   since 2026-09-25), so installing from any other branch makes the first
   session report the engine as behind — and run, from that clone:

   ```
   python3 tools/precedent_install.py <path to the project> \
       --project-name "<the project's name>" \
       --about "<their first answer, one sentence>" \
       --visibility <private or public, read from the repository, never asked> \
       --admin <the administrator's GitHub handle>
   ```

   It vendors the catalogue and the engine, writes `precedent.json`
   (declaring the repo-local `"local"` source along with the universal
   one), instantiates `AGENTS.md`, `MAP.md`, `TODO.md`, `GLOSSARY.md`,
   `GETTING_STARTED.md`, `local/practices/project-voice.md` and
   `local/practices/project-visual-identity.md`, the README entry
   block, the Claude Code hooks, `tools/bootstrap.sh`, the Actions check
   and the pull-request template, runs the sync, lints what it wrote, and
   then prints **the placeholders it left** — each is a `<…>` in a file it
   names, to be filled with the project's own subject matter from their
   first answer where they asked for that now, else left as placeholders
   (a `GLOSSARY.md` row can be deleted rather than invented). The project
   comes first ([lead-with-what-it-is](practices/lead-with-what-it-is.md)):
   the README opens with what the project *is*, and the entry block sits
   under that. Their second answer goes into the leak blocklist the
   per-machine page describes — it protects what leaves the project, and
   the loader install has no `process/scrub_blocklist.txt`. That list
   needs a private home: their individual set's `leak-blocklist.txt`. If
   they have none, this is a reason to set one up now (third question);
   never write the words into the project itself. In a private repository
   the leak gate stands down, so say the list only matters for what goes
   back upstream, or if the repository is ever made public.
   If they answered yes to the third question, follow INSTALL.md §1 step 9
   for what to actually do with a shared or individual repo (a shared source
   goes in a new `precedent.json`; an individual source is never touched
   by this session at all — it's declared in that person's own user-level
   config, not this project). If they'd like one set up now instead,
   follow [spec/BOOTSTRAP_NEW_SOURCES.md](https://github.com/alex137/BestPractice/blob/staging/spec/BOOTSTRAP_NEW_SOURCES.md) —
   it walks through creating the repository (do it yourself if the session
   can; otherwise hand them the exact command or click-path), running
   [tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py),
   and wiring the result in exactly
   as INSTALL.md §1 step 9 describes for an existing repo. This is real,
   working tooling, not a promise: it hands them a starter file in the
   right format and the exact config to wire in, in the same sitting.
   `local/practices/project-voice.md` and
   `local/practices/project-visual-identity.md` install as the
   templates' near-empty skeletons and **stay that way** — filling them in
   is not part of an install (see "What an install does not do" below).
   **Now use their answer about which AI Assistant will work in the
   repo.** The command sets the project up for Claude Code only. If they
   named Codex, Gemini CLI or another assistant that runs in a terminal,
   add that assistant's setup too, from
   [templates/harness/README.md](templates/harness/README.md): it lists
   one page per assistant, and each page says which files to copy where.
   Keep the Claude Code files either way; the other assistants reuse its
   checks. Tell them in one sentence which assistant you set up and that
   more can be added later. For ChatGPT or another assistant with no
   terminal, there is nothing to add here: the GitHub check is what
   covers them, which is why the fifth question matters for them.
   Respect the root-hygiene rule (INSTALL.md §0 step 7): nothing from
   Precedent lands loose at the repo root except the instantiated files,
   `precedent.json`, and the sync's own `practices/` and `MANIFEST.json`.
   Then `python3 tools/precedent_check.py --full-sweep` from the project
   (the bare command runs only a slice) — it must say `0 violated` — and commit everything on a branch. If the repository has
   no `origin` yet, it needs one before the first working session: the
   freshness guard refuses a session's first write while it cannot reach
   one.
4. **Walk them through what you made — don't just list files.** Show
   `GETTING_STARTED.md` (what their members will see) and summarize the
   instructions file (the contract future AI sessions work under) in two
   or three plain sentences each. Offer to adjust anything.

   Then **mention `local/practices/project-voice.md` and
   `local/practices/project-visual-identity.md` in
   one breath and move on**: both shipped empty, both are optional, both
   stay local to their project and are never proposed back to the public
   Precedent repo, and they can fill either in whenever they like by just
   saying so to an AI Assistant — *"help me fill in my project's
   voice"*. **Do not walk them through the sections, and do not ask
   whether a brand guideline exists.** That is a good conversation and
   it is not this one.
5. **Merge for them or with them.** If you can merge, ask "Shall I make
   this live?" and do it on their yes. If only they can merge, give them
   the pull-request link and tell them exactly what to press.
6. **Verify the automatic checks, while Actions is on.** On the pull
   request into `main`, confirm `light-check` appears and passes; in a
   private repository nothing runs after the merge, by design. If the repository or organization has Actions disabled,
   give the administrator the exact clicks (repository **Settings →
   Actions**, or the **Actions** tab's enable button) and confirm the
   check appears afterward. Never leave this step silently unfinished —
   the checks are what make the practices enforceable.
7. **Optionally, walk them through the settings only they can turn on.**
   None of these can be done from here, none is urgent, and each fails
   quietly rather than loudly — so offer them as things worth doing rather
   than as a gate, keep it brief, and **say you can give more specific
   instructions for any of them if they want** — the reference you would
   draw them from is [documentation/GITHUB_SETTINGS.md](documentation/GITHUB_SETTINGS.md). Written out, in this order
   (click-paths as of 2026-09-10):
   1. **If the project's repository is being created now, make it
      private** unless it is meant to be public — that choice is made at
      creation time and is easy to walk past.
   2. **Only if they later add automation that opens pull requests: a
      developer key.** No shipped check needs one
      ([documentation/GITHUB_SETTINGS.md](documentation/GITHUB_SETTINGS.md)).
      If they do, create a personal access token that can reach this
      repository and save it under **Settings → Secrets and variables →
      Actions → New repository secret**. Say that it is not needed today.
   3. **Check the main line of work is called `main`** — **Settings →
      General → Default branch**, renaming it there if it is called
      anything else. The automatic check installed above watches a branch
      by that exact name.
   4. **Only with the automation in item 2: let it open proposals** —
      **Settings → Actions → General → Workflow permissions**, ticking
      *Allow GitHub Actions to create and approve pull requests*.
   5. **Optional: turn GitHub Actions off, if this project needs no
      automatic checks on GitHub** — **Settings → Actions → General →
      Actions permissions → Disable actions** (as of 2026-09-26). In a
      private repository every run costs minutes from their account; with
      Actions off, a stray check file costs nothing. The checks that run on
      their own machine before a push keep working. Say that it is
      optional, and leave it on if the project relies on a check running
      on GitHub.
   6. **Put a few settings into Claude itself**, if they work in Claude
      Code on the web. Recommended, not required — but without them,
      every new session re-lives the same three problems: their own
      practices never load, work gets committed under the AI Assistant's
      bot account rather than their name, and timestamps land in the
      wrong timezone. In Claude, open [claude.ai/code](https://claude.ai/code),
      go to the environment this project runs in, and find its
      **environment variables** — the full path is in Anthropic's own
      guide at
      [code.claude.com/docs/en/claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web),
      which is the place to check if the screen has moved since
      2026-09-11. Add one line per setting, substituting their own
      values:

      ```
      PRECEDENT_COMMIT_NAME=Your Name
      PRECEDENT_COMMIT_EMAIL=you@example.com
      PRECEDENT_COMMIT_TZ=America/Argentina/Buenos_Aires
      ```

      And if they have a private practices repo of their own, two more —
      the token being a GitHub read-only personal access token that can
      see it:

      ```
      PRECEDENT_GIT_TOKEN=github_pat_<their token>
      PRECEDENT_SOURCE_BASE_URL=https://github.com/their-github-account
      ```

      **Optional but recommended: one paste into the environment's setup
      script.** A session that works across several of their repositories
      opens in the folder above them, where none of the repositories'
      startup steps run on their own, so their rules and their name on
      commits quietly go missing. The paste is in
      [CLOUD_SETUP.md](documentation/CLOUD_SETUP.md#optional-but-recommended-run-each-repos-startup-hooks); hand it to them
      as it stands. Skipping it is harmless for someone who only ever
      works in one repository at a time.

      Two things to say out loud, because both cost a day when they are
      not said. **A change here never reaches a session already open** —
      start a new one to test it. And **if their account has two
      environments with the same name, the values go on the one they are
      not using**, so give the environments distinct names first. This
      walkthrough, cloud-only, is also written out at
      [CLOUD_SETUP.md](documentation/CLOUD_SETUP.md); the full list of every variable and
      what each does is [PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md).

   Put the same six into `GETTING_STARTED.md` so they are findable after
   this conversation closes.
8. **Hand them the keys.** Close by telling them three things: members are
   onboarded by saying **"Add project members"** to the project's agent
   (the installed instructions file teaches every future session how to
   guide that); day-to-day work is just asking questions and requesting
   changes in plain language; and **if anyone tells an AI Assistant
   working here "always do X" or "never do Y," it will notice and offer
   to write that down as one of this project's own rules** — captured into the
   instructions file every future session reads, not just remembered for
   this one conversation. Nobody has to ask for that by name, and nothing
   gets written down without saying so and getting a yes first.

## What the Administrator Actually Has to Decide

Work through this with them. It is every moment across the whole lifecycle
where the decision is genuinely theirs rather than yours; everything not on
it runs inside your ordinary work. The section references are to
[INSTALL.md](INSTALL.md), which you are following and they are not.

- **At install (§0).** They answer the five questions in step 2 — what
  the project is about, what private names or code words must never go
  public, and whether a team or personal practices repo exists or should be
  set up now (§1 step 9; most projects have neither yet, and saying so is a
  complete answer — but offer to set one up on the spot). Then they look at
  what you built and either approve it or ask for changes.
  `local/practices/project-voice.md` and
  `local/practices/project-visual-identity.md` are **not** walked
  through and nobody is asked about a brand guideline: both ship empty,
  stay local to the project, and are filled in whenever they later ask
  an AI Assistant to.
- **When a practice is proposed** (a rule their AI Assistant noticed and
  wrote down). They say yes or no, at the level it belongs — theirs, the
  team's, or the public library, where it goes up for a visible review.
  This is the one recurring moment where content may leave the project's
  boundary, so it is the one worth actually reading rather than
  rubber-stamping.
- **When they add a person to the project.** Everyone invited gets the
  same Write role; what a person may land is decided by what the change
  touches, never by who they are — the documents are any contributor's,
  the project's settings and checks wait for its maintainer, and a new
  rule is landed only by a listed approver. Drawing that line is
  [INSTALL.md §0 step 10](INSTALL.md#0-installing-directly-onto-the-precedent-loader),
  a decision about people made after the install, not part of this
  conversation: say once that it exists and that the branch-protection
  clicks are theirs to make.
- **When a check flags something.** A failed automatic check is you
  catching a problem before it reached them, not something they fix by
  hand. Explain what failed, fix it, and let them confirm the fix makes
  sense.
- **Nowhere else.** Updates (`Update Vendors`, §2) run inside your normal
  work and need no sign-off unless you specifically flag a conflict or a
  judgment call.

## What an Install Does Not Do

**An install, an upgrade and a migration all do the essentials and stop.**
They get the project working, correctly, with the fewest decisions asked of
the administrator — and everything that would merely make it *better* is
named once and deferred. The person is at their least informed on the day
they install, so a decision put to them then is the worst version of that
decision they will ever make, and it lengthens the one conversation that
most needs to feel short.

So these are **out of scope** for you, and are mentioned in one sentence
each, not worked through:

- **`local/practices/project-voice.md`** — the project's own voice, its
  audiences, its domain vocabulary. A repo-local practice, not a plain
  document; ships near-empty and stays that way.
- **`local/practices/project-visual-identity.md`** — the visual identity.
  A repo-local practice, not a plain document; ships near-empty. Do not ask
  whether a brand guideline exists, and never read, attach or vendor one.
- **Anything else that is a refinement rather than a requirement**, whether
  or not it is on this list. The test: *would the project work correctly
  without this today?* If yes, it is a later conversation.

**What you do say, once:** these files exist, they are optional, they stay
local to the project, and **the administrator can fill any of them in at
any time just by asking an AI Assistant** — *"help me fill in my
project's voice"*. That sentence is the whole handover.

**What is in scope and must not be skipped as "polish":** the private-word
blocklist, the commit identity, the shared and individual source question,
and anything a mechanical check fails without. Those are not refinements —
the project is wrong without them.

## Rules While Guiding

- **Never ask about a setting that already has a default.** The timezone
  dates are stamped in, how the person is referred to in writing, whether
  their approval travels between sessions — each has a declared answer that
  applies until they say otherwise. Apply it, mention it in passing at most,
  and point them at
  [PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md)'s "What Applies Until You Set
  Any of It" once (practice
  [declared-default-is-applied](practices/declared-default-is-applied.md)).
  A wrong timezone is a one-sentence fix whenever they notice; the question
  that would have prevented it costs them a decision on the day they know
  least.
- **Use Precedent's own words the way [Our
  Language](documentation/OUR_LANGUAGE.md) defines them** -- "individual
  set", "shared set", "in force" -- and point the person at
  that page once, the first time one of them comes up.
- One step at a time; never assume git or GitHub vocabulary. "Branch",
  "merge", "pull request", "workflow", "personal access token",
  "repository secret", "default branch" and "environment variable" each
  get a five-word gloss the first time they appear —
  [GETTING_STARTED.md](templates/GETTING_STARTED.md)'s "GitHub's name for a
  key that stands in for a person" is the shape.
- Do the work yourself wherever an agent can; involve the administrator
  only where the platform requires a human (authorization screens,
  restricted settings, merges you cannot perform).
- Every reply that created or modified files ends with links to those
  files, and names any file it deleted and why (practice
  [reply-links-files](practices/reply-links-files.md)).

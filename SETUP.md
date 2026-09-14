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
which turns on none of the loader the rest of this repository describes. §1
is still there for a project that specifically wants the classic check-in
loop; say so and follow §1 instead.

## The Conversation

1. **Confirm the target.** The repository this session is opened on is
   the project. Tell the administrator, in one sentence, what you are
   about to set up: a practice layer that gives their project durable
   memory, safe concurrent work, and a Getting Started page for members.
2. **Ask exactly three questions**, together in one message, and wait:
   - *What is this project about?* (one or two sentences)
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
     ask rather than assume no.
3. **Install without further questions.** Clone the public repo
   `https://github.com/alex137/BestPractice` beside the project (a sibling
   directory, not inside it) **on its `precedent-beta-v01` branch** — the
   branch this file lives on; `main` took the same tree on 2026-09-14 but
   everything after that lands here first — and run, from that clone:

   ```
   python3 tools/precedent_install.py <path to the project> \
       --project-name "<the project's name>" \
       --about "<their first answer, one sentence>" \
       --visibility <private or public, read from the repository, never asked> \
       --admin <the administrator's GitHub handle>
   ```

   It vendors the catalogue and the engine, writes `precedent.json`,
   instantiates `AGENTS.md`, `MAP.md`, `TODO.md`, `GLOSSARY.md`,
   `GETTING_STARTED.md`, `VOICE.md` and `STYLEGUIDE.md`, the README entry
   block, the Claude Code hooks, `tools/bootstrap.sh`, the Actions check
   and the pull-request template, runs the sync, lints what it wrote, and
   then prints **the placeholders it left** — each is a `<…>` in a file it
   names, to be filled with the project's own subject matter from their
   first answer (the README opening and `MAP.md`'s deliverables first; a
   `GLOSSARY.md` row can be deleted rather than invented). The project
   comes first ([lead-with-what-it-is](practices/lead-with-what-it-is.md)):
   the README opens with what the project *is*, and the entry block sits
   under that. Their second answer goes into the leak blocklist the
   per-machine page describes — it protects what leaves the project, and
   the loader install has no `process/scrub_blocklist.txt`.
   If they answered yes to the third question, follow INSTALL.md §1 step 9
   for what to actually do with a team or individual repo (a team source
   goes in a new `precedent.json`; an individual source is never touched
   by this session at all — it's declared in that person's own user-level
   config, not this project). If they'd like one set up now instead,
   follow [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md) —
   it walks through creating the repository (do it yourself if the session
   can; otherwise hand them the exact command or click-path), running
   `tools/precedent_bootstrap_source.py`, and wiring the result in exactly
   as INSTALL.md §1 step 9 describes for an existing repo. This is real,
   working tooling, not a promise: it hands them a starter file in the
   right format and the exact config to wire in, in the same sitting.
   `VOICE.md` and `STYLEGUIDE.md` install as the templates' near-empty
   skeletons and **stay that way** — filling them in is not part of an
   install (see "What an install does not do" below).
   Respect the root-hygiene rule (INSTALL.md §0 step 7): nothing from
   Precedent lands loose at the repo root except the instantiated files,
   `precedent.json`, and the sync's own `practices/` and `MANIFEST.json`.
   Then `python3 tools/precedent_check.py` from the project — it must say
   `0 violated` — and commit everything on a branch. If the repository has
   no `origin` yet, it needs one before the first working session: the
   freshness guard refuses a session's first write while it cannot reach
   one.
4. **Walk them through what you made — don't just list files.** Show
   `GETTING_STARTED.md` (what their members will see) and summarize the
   instructions file (the contract future AI sessions work under) in two
   or three plain sentences each. Offer to adjust anything.

   Then **mention `VOICE.md` and `STYLEGUIDE.md` in one breath and move
   on**: both shipped empty, both are optional, both stay local to their
   project and are never proposed back to the public Precedent repo, and
   they can fill either in whenever they like by just saying so to an
   assistant — *"help me fill in VOICE.md"*. **Do not walk them through
   the sections, and do not ask whether a brand guideline exists.** That
   is a good conversation and it is not this one.
5. **Merge for them or with them.** If you can merge, ask "Shall I make
   this live?" and do it on their yes. If only they can merge, give them
   the pull-request link and tell them exactly what to press.
6. **Verify the automatic checks.** After merge, confirm the Actions
   workflow ran. If the repository or organization has Actions disabled,
   give the administrator the exact clicks (repository **Settings →
   Actions**, or the **Actions** tab's enable button) and confirm the
   check appears afterward. Never leave this step silently unfinished —
   the checks are what make the practices enforceable.
7. **Optionally, walk them through the settings only they can turn on.**
   None of these can be done from here, none is urgent, and each fails
   quietly rather than loudly — so offer them as things worth doing rather
   than as a gate, keep it brief, and **say you can give more specific
   instructions for any of them if they want**. Written out, in this order
   (click-paths as of 2026-09-10):
   1. **If the project's repository is being created now, make it
      private** unless it is meant to be public — that choice is made at
      creation time and is easy to walk past.
   2. **Make a developer key and store it in the project.** In GitHub,
      create a personal access token that can reach this repository, then
      save it under **Settings → Secrets and variables → Actions → New
      repository secret**, named `PRECEDENT_REPO_TOKEN` unless something
      already expects another name. Without a key of its own, an assistant
      working here can read and prepare changes but cannot push them or
      open a proposal on the project's behalf.
   3. **Check the main line of work is called `main`** — **Settings →
      General → Default branch**, renaming it there if it is called
      anything else. The automatic check installed above watches a branch
      by that exact name.
   4. **Let the automation open proposals** — **Settings → Actions →
      General → Workflow permissions**, ticking *Allow GitHub Actions to
      create and approve pull requests*.
   5. **Put a few settings into Claude itself**, if they work in Claude
      Code on the web. Recommended, not required — but without them,
      every new session re-lives the same three problems: their own
      practices never load, work gets committed under the assistant's bot
      account rather than their name, and timestamps land in the wrong
      timezone. In Claude, open [claude.ai/code](https://claude.ai/code),
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

      Two things to say out loud, because both cost a day when they are
      not said. **A change here never reaches a session already open** —
      start a new one to test it. And **if their account has two
      environments with the same name, the values go on the one they are
      not using**, so give the environments distinct names first. The
      full list of variables and what each does is
      [PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md).

   Put the same five into `GETTING_STARTED.md` so they are findable after
   this conversation closes.
8. **Hand them the keys.** Close by telling them three things: members are
   onboarded by saying **"Add project members"** to the project's agent
   (the installed instructions file teaches every future session how to
   guide that); day-to-day work is just asking questions and requesting
   changes in plain language; and **if anyone tells an assistant working
   here "always do X" or "never do Y," it will notice and offer to write
   that down as one of this project's own rules** — captured into the
   instructions file every future session reads, not just remembered for
   this one conversation. Nobody has to ask for that by name, and nothing
   gets written down without saying so and getting a yes first.

## What the Administrator Actually Has to Decide

Work through this with them. It is every moment across the whole lifecycle
where the decision is genuinely theirs rather than yours; everything not on
it runs inside your ordinary work. The section references are to
[INSTALL.md](INSTALL.md), which you are following and they are not.

- **At install (§0).** They answer the three questions in step 2 — what
  the project is about, what private names or code words must never go
  public, and whether a team or personal practices repo exists or should be
  set up now (§1 step 9; most projects have neither yet, and saying so is a
  complete answer — but offer to set one up on the spot). Then they look at
  what you built and either approve it or ask for changes. `VOICE.md` and
  `STYLEGUIDE.md` are **not** walked through and nobody is asked about a
  brand guideline: both ship empty, stay local to the project, and are
  filled in whenever they later ask an assistant to.
- **When a practice is proposed** (a rule their assistant noticed and
  wrote down). They say yes or no, at the level it belongs — theirs, the
  team's, or the public library, where it goes up for a visible review.
  This is the one recurring moment where content may leave the project's
  boundary, so it is the one worth actually reading rather than
  rubber-stamping.
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

- **`VOICE.md`** — the project's own voice, its audiences, its domain
  vocabulary. Ships near-empty and stays that way.
- **`STYLEGUIDE.md`** — the visual identity. Ships near-empty; do not ask
  whether a brand guideline exists, and never read, attach or vendor one.
- **Anything else that is a refinement rather than a requirement**, whether
  or not it is on this list. The test: *would the project work correctly
  without this today?* If yes, it is a later conversation.

**What you do say, once:** these files exist, they are optional, they stay
local to the project, and **the administrator can fill any of them in at
any time just by asking an assistant** — *"help me fill in VOICE.md"*. That
sentence is the whole handover.

**What is in scope and must not be skipped as "polish":** the private-word
blocklist, the commit identity, the team and individual source question,
and anything a mechanical check fails without. Those are not refinements —
the project is wrong without them.

## Rules While Guiding

- **Never ask about a setting that already has a default.** The timezone
  dates are stamped in, how the person is referred to in writing, whether
  their approval travels between sessions — each has a declared answer that
  applies until they say otherwise. Apply it, mention it in passing at most,
  and point them at
  [PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md)'s "What Applies Until You Set
  Any of It" once (practice
  [declared-default-is-applied](practices/declared-default-is-applied.md)).
  A wrong timezone is a one-sentence fix whenever they notice; the question
  that would have prevented it costs them a decision on the day they know
  least.
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

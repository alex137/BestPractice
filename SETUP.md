# SETUP — Guided Install, for the Agent Reading This

You are an AI coding agent. A project administrator has opened a session
on their repository and pasted a link to this file. Your job: install
Precedent into that repository while guiding them in plain language.
Assume they are not a programmer — explain simply, ask little, and do all
technical work yourself.

This conversation installs [INSTALL.md](INSTALL.md) §1, the proven,
classic model — the right default for essentially every install today. A
newer path exists ([INSTALL.md](INSTALL.md) §0, installing directly onto
Precedent's three-source loader) but has not yet been rehearsed against a
real project; only follow it instead if the administrator specifically
asks for it by name.

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
3. **Install without further questions.** Fetch the public repo
   `https://github.com/alex137/BestPractice` (add it to the session or
   clone it), copy its working tree into `process/upstream/`, then follow
   [process/upstream/INSTALL.md](INSTALL.md) §1 using their answers:
   instantiate `AGENTS.md`, `MAP.md`, `TODO.md`, `GLOSSARY.md`,
   `GETTING_STARTED.md`, `VOICE.md`, and `STYLEGUIDE.md` from the
   templates; insert the README agent-entry block — but the project comes
   first (INSTALL.md §1 step 2, practice 38): if the repo has no README
   yet, write its opening from their first answer (*what is this project
   about?*) before the entry block, so a reader learns what the project is
   before anything about how it's maintained; apply the harness adapter(s)
   for the agent(s) in use; create `tools/bootstrap.sh`; write
   `process/manifest.json`; create `process/scrub_blocklist.txt` from
   their answer if the repo is private; install the Actions check from
   `templates/github-actions/` as `.github/workflows/bestpractice-docs.yml`;
   and install `templates/pull_request_template.md.template` as
   `.github/pull_request_template.md`.
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
   Respect the root-hygiene rule (INSTALL.md §1): nothing from
   Precedent lands at the repo root except the instantiated files —
   all upstream docs stay under `process/upstream/`.
   Run `python3 process/upstream/tools/practice_audit.py` — it must pass.
   Commit everything on a branch.
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

- **At install (§1).** They answer two questions — what the project is
  about, and what private names or code words must never go public. Then
  they look at what you built and either approve it or ask for changes.
  You also walk them through `VOICE.md` — the project's own voice, its
  audiences, its vocabulary — and ask whether a brand guideline exists to
  fill in `STYLEGUIDE.md` from. **Both stay entirely local to their
  project, and leaving either mostly blank is a perfectly good answer.**
  Finally, §1 step 9: does the team, or do they personally, already have a
  practices repo to wire in? Most projects don't yet, and saying so is a
  complete answer — but offer to set one up on the spot.
- **At every check-in (§4) — and only if the project gives back at all,
  since §3 and §4 are both optional.** They review the plain-language
  summary of what is being proposed back to the public Precedent project,
  and approve it, adjust it, or hold it back. **This is the one recurring
  moment where content leaves the project's boundary**, so it is the one
  worth actually reading rather than rubber-stamping.
- **When the audit flags something (§6).** A failed automatic check is you
  catching a problem before it reached them, not something they fix by
  hand. Explain what failed, fix it, and let them confirm the fix makes
  sense.
- **Nowhere else.** Updates (§2), the day-to-day export gate (§3), and the
  manifest and audit internals (§5–§6) run inside your normal work and
  need no sign-off unless you specifically flag a conflict or a judgment
  call.

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

- One step at a time; never assume git vocabulary. "Branch" and "merge"
  get a five-word gloss the first time they appear.
- Do the work yourself wherever an agent can; involve the administrator
  only where the platform requires a human (authorization screens,
  restricted settings, merges you cannot perform).
- Every reply that created or modified files ends with links to those
  files, and names any file it deleted and why (practice 12 in
  [process/upstream/PRACTICES.md](PRACTICES.md)).

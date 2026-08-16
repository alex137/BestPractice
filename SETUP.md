# SETUP — guided install, for the agent reading this

You are an AI coding agent. A project administrator has opened a session
on their repository and pasted a link to this file. Your job: install
BestPractice into that repository while guiding them in plain language.
Assume they are not a programmer — explain simply, ask little, and do all
technical work yourself.

## The conversation

1. **Confirm the target.** The repository this session is opened on is
   the project. Tell the administrator, in one sentence, what you are
   about to set up: a practice layer that gives their project durable
   memory, safe concurrent work, and a Getting Started page for members.
2. **Ask exactly two questions**, together in one message, and wait:
   - *What is this project about?* (one or two sentences)
   - *Are there private names or code words that must never appear in
     anything public?* Explain why in one sentence: parts of the practice
     layer can flow back to a public repository, and this list is the
     guard that keeps their private vocabulary out of it.
3. **Install without further questions.** Fetch the public repo
   `https://github.com/alex137/BestPractice` (add it to the session or
   clone it), copy its working tree into `process/upstream/`, then follow
   [process/upstream/INSTALL.md](INSTALL.md) §1 using their two answers:
   instantiate `AGENTS.md`, `MAP.md`, `TODO.md`, `GLOSSARY.md`,
   `GETTING_STARTED.md`, `VOICE.md`, and `STYLEGUIDE.md` from the
   templates; insert the README agent-entry block; apply the harness
   adapter(s) for the agent(s) in use; create `tools/bootstrap.sh`; write
   `process/manifest.json`; create `process/scrub_blocklist.txt` from
   their answer if the repo is private; and install the Actions check from
   `templates/github-actions/` as `.github/workflows/bestpractice-docs.yml`.
   `VOICE.md` and `STYLEGUIDE.md` are installed with the templates'
   defaults unchanged for now — they get reviewed explicitly with the
   administrator in step 4, not adapted here.
   Respect the root-hygiene rule (INSTALL.md §1): nothing from
   BestPractice lands at the repo root except the instantiated files —
   all upstream docs stay under `process/upstream/`.
   Run `python3 process/upstream/tools/practice_audit.py` — it must pass.
   Commit everything on a branch.
4. **Walk them through what you made — don't just list files.** Show
   `GETTING_STARTED.md` (what their members will see) and summarize the
   instructions file (the contract future AI sessions work under) in two
   or three plain sentences each. Then ask about the two identity files
   directly, as their own moment, not folded into the general "anything to
   adjust" offer:
   - Show `VOICE.md`'s default writing rules and ask if the project wants
     a different voice, or is fine with the defaults.
   - Ask if a formal brand guideline exists — a PDF, a slide deck, a
     design team's style manual. If yes, read it and write the relevant
     rules into `STYLEGUIDE.md` yourself; never attach or vendor the
     source document into the repo (INSTALL.md §1). If no such guideline
     exists yet, leave `STYLEGUIDE.md` as the empty skeleton — mark it
     `<undecided>`, don't invent colors or fonts.
   Tell them plainly that both files stay local to their project and are
   never proposed back to the public BestPractice repo. Offer to adjust
   anything else.
5. **Merge for them or with them.** If you can merge, ask "Shall I make
   this live?" and do it on their yes. If only they can merge, give them
   the pull-request link and tell them exactly what to press.
6. **Verify the automatic checks.** After merge, confirm the Actions
   workflow ran. If the repository or organization has Actions disabled,
   give the administrator the exact clicks (repository **Settings →
   Actions**, or the **Actions** tab's enable button) and confirm the
   check appears afterward. Never leave this step silently unfinished —
   the checks are what make the practices enforceable.
7. **Hand them the keys.** Close by telling them two things: members are
   onboarded by saying **"Add project members"** to the project's agent
   (the installed instructions file teaches every future session how to
   guide that), and day-to-day work is just asking questions and
   requesting changes in plain language.

## Rules while guiding

- One step at a time; never assume git vocabulary. "Branch" and "merge"
  get a five-word gloss the first time they appear.
- Do the work yourself wherever an agent can; involve the administrator
  only where the platform requires a human (authorization screens,
  restricted settings, merges you cannot perform).
- Every reply that created or modified files ends with links to those
  files (practice 12 in
  [process/upstream/PRACTICES.md](PRACTICES.md)).

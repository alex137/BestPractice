# BestPractice

A portable process layer for repositories where an AI agent (or a rotating cast
of humans and agents) does the work across many short sessions: **the repo is
the memory**. Conventions, templates, and small audit tools that keep
orientation, open items, decisions, and hard-won lessons in committed files —
so any session can pick up cold — plus the machinery to install these practices
into a *dependent repo*, adapt them to its subject matter, and flow
improvements back here.

## The premise: you work through agents

One idea underlies everything in this repo: **you don't work on the files;
you work through agents — and you should rarely need to open a file at
all.** An agent here is an AI assistant, like Claude Code, that can read
the project's files, edit them, run its checks, and commit changes. To
learn what the project knows, ask the agent the questions your project
exists to answer; it assembles answers from the committed files. To change
what the project knows, hand the agent a critique — what is wrong, what
you want instead — never a hand edit. In practice:

> *"What did we decide about pricing, and why?"* — the agent answers from
> the decision log. *"The intro reads too technical for investors — make
> it plain-English."* — the agent rewrites it, carries the change through
> every document that quotes it, and commits with the reason recorded.

Your contribution is intent: the questions, the judgments, what to pursue
next. The agent's contribution is everything mechanical that intent
implies: reading the relevant documents, applying changes consistently,
fixing the cross-references, running the audits, keeping the history.
The files are the system's memory, not your workspace.
(See [the working method](#the-working-method-branches-plain-text-and-composed-prompts)
for how this is driven in practice.)

Taken seriously, the premise has a consequence: an agent starts every
session (each new conversation) knowing nothing but what is in the files,
and it honors conventions only when something enforces them. So the
project itself must carry the memory and the discipline — which is
exactly what the rest of this repo implements.

## Central concepts

Three commitments that make the premise workable:

- **A git repository is the shared file system** — for every human and AI
  agent involved in the project. Committed files mean every change records
  who, when, what, and why, and concurrent work reconciles through branches
  and merges instead of overwrites. (See
  [Git, minimally](#git-minimally-for-this-way-of-working) below.)
- **Plain text is the source; Word, Excel, PowerPoint, and PDF are only
  ever inputs or outputs.** The project's knowledge lives in the formats
  agents handle best and git can diff: markdown for documents, HTML for
  rendered deliverables, and Python for models — where you might once have
  built a spreadsheet, the agent maintains a Python model, which you query
  the same way as everything else: through the agent, not by reading code.
  This keeps humans creating knowledge rather than formatting it;
  presentation waits until the moment you actually present.
  - **Going out:** Word, PDF, PowerPoint, and Excel files are generated
    from the sources on demand — and HTML usually beats them: a single
    file with every figure inlined, interactive or animated with inline
    JavaScript, and agents build markedly better HTML than PowerPoint.
    With slides as files, agents working for different team members can
    develop different slides at once while any one of them composes the
    deck. (See
    [Presentations](#presentations-slides-are-files-decks-are-builds).)
  - **Coming in:** an arriving Excel workbook (or Word file, or PDF) is
    extracted and analyzed by an agent into the plain-text sources. The
    original is committed to the repo so it is never lost — but per the
    premise, you should rarely need to open it again.
- **Everything runs through the Claude Code app — desktop or mobile.**
  Because driving the work is a conversation, either one is a full
  workstation: review what an agent produced, redirect it, merge — from
  anywhere, including a phone, so the gap between having an idea and
  tasking an agent with it shrinks to wherever you are. Two optional
  habits improve results (see
  [the working method](#the-working-method-branches-plain-text-and-composed-prompts)):
  draft your prompt in a notepad app and paste it in when it's ready,
  rather than dictating a stream of thought; stronger still, refine the
  prompt in a separate chat instance before handing it to the working
  session. Both are optimizations, not requirements — a typed question is
  a fine way to start.

## Layout

| Path | What it is |
|---|---|
| [PRACTICES.md](PRACTICES.md) | The catalog: each practice as a rule, the (abstracted) incident that motivated it, and how to install it. |
| [INSTALL.md](INSTALL.md) | The agent playbook: install into a dependent repo, take updates, copy improvements back, and the proprietary-scrub gate. |
| `templates/` | Skeletons a dependent repo instantiates: `AGENTS.md.template` (the harness-neutral instructions file), `MAP.md.template`, `TODO.md.template`, `GLOSSARY.md.template`, `bootstrap.sh`, and `harness/` (per-agent adapters: Claude Code, Codex, Gemini CLI — installable side by side). |
| `tools/` | Portable scripts run in place: [doc_lint.py](tools/doc_lint.py) (markdown hygiene), [practice_audit.py](tools/practice_audit.py) (manifest drift + scrub gate), and [checkin.py](tools/checkin.py) (drives the §4 check-in: status / scrubbed push / verified record). |
| `deck/` | Presentations as code: [build_deck.py](deck/build_deck.py) (the slide-deck engine), [README](deck/README.md) (the practice + conventions), [sample/](deck/sample/) (a working deck about this repo). See "Presentations" below. |

## Why this, instead of a chat thread or a memory feature?

Chat assistants keep state in two places: the conversation (gone, for
practical purposes, when the thread ends) and an opaque memory feature (a
store you can't fully inspect, diff, review, or share). Both fail the same
test: **you can't control what's in context, and you can't audit what the
assistant "knows."** BestPractice moves all of that state into a git
repository, which buys you:

- **Control of context.** Every session starts by reading `MAP.md` and the
  instructions file — *you* decide what the assistant knows, by editing
  files. Nothing load-bearing lives in a hidden store or a lucky recollection
  from an old thread. If a session keeps missing something, you add a row to
  the quick index — a one-line, permanent fix.
- **State that doesn't decay.** Open items, decisions, environment lessons,
  and naming conventions are committed text. A session six months from now
  (on a different model, a different tool, or a different person) picks up
  exactly where the last one left off, because "where we left off" is a file.
- **Version control and an audit trail.** Every change is a commit: who,
  when, what, and — because conventions here require it — *why*. Anything
  can be reverted; two versions of anything can be diffed. Memory features
  offer none of this.
- **Real sharing.** A repo is multiplayer by construction: collaborators
  (human or agent) see the same map, the same open items, the same
  conventions, and propose changes through reviewable pull requests — instead
  of forwarding chat transcripts or hoping everyone's assistant remembers the
  same things.
- **Enforcement instead of vigilance.** Rules that matter are backed by small
  scripts that fail loudly (see practice 6). A chat thread can only *promise*
  to follow a convention; a repo can *check* it.

The trade: you maintain the files. The practices in this repo exist to make
that maintenance nearly automatic — each session updates the map, the TODO,
and the lore as part of finishing its work.

## The working method: branches, plain text, and composed prompts

The sections above say where state lives. This one is the philosophy of how
a human actually drives the work — four commitments that make the whole
system compose:

- **Branches instead of a shared canvas.** Shared-workspace tools (Cowork
  and similar) put every contributor — human or agent — on one live copy of
  the work, so two threads touching the same document either clobber each
  other or must take turns. Git replaces that with structure: each thread
  works on its own branch, isolated while working, and reconciliation
  happens once, at merge time, under the runbook's fixed per-file-class
  rules with the audits as the safety net. The point is not that conflicts
  disappear — it's that **conflict resolution becomes a protocol agents can
  execute**, instead of an accident humans must untangle. That is what
  makes it safe to run several agent threads against the same repo at once.

- **Markdown, HTML, and Python are the source; office formats are
  outputs.** Work is authored in plain text — markdown for documents, HTML
  where a rendered deliverable is needed, Python where the work is a model
  or analysis. Never Word, Excel, PDF, or PowerPoint as the *source*:
  binary formats can't be diffed line by line, can't be text-merged across
  branches, and can't be reviewed in a PR, so as sources they break every
  mechanism this repo relies on. When a .docx, .xlsx, .pdf, or slide deck
  must ship, a builder generates it from the plain-text source (practice 8
  gives it provenance) and nobody ever hand-edits the output. Files that
  *arrive* in office formats go the other way: an agent extracts and
  analyzes them into the sources, and the original is committed for the
  record rather than worked on.

- **Edit by critique, not by hand.** To change a document, don't open it
  and start typing — write a critique: what's wrong, what you want instead,
  and why. Hand that to the agent. An agent applying a critique can improve
  on your idea, carry it consistently through every affected document, fix
  the cross-references, and run the audits; a direct hand edit does none of
  that, and silently skips the gates the repo depends on. You work at the
  level of intent; the machinery handles propagation.

- **Composed prompts, not dictation.** Draft instructions in a separate
  editor — the length of a considered email — then paste them to the agent.
  On a phone that editor is the notepad app: capture and shape the thought
  there, then paste it into the Claude Code app. The strongest version:
  refine the prompt in a separate chat instance first, and hand the
  working session the result. Type directly only for short commands
  ("merge"). Pure dictation is an
  anti-pattern: cleaning up your own thinking before tasking an agent is
  real work that pays for itself, because the agent's output quality tracks
  the prompt's clarity, and a stream of consciousness makes the agent guess
  which half-formed thought was the requirement. The prompt is the first
  draft of the work; treat it like one.

## Presentations: slides are files, decks are builds

The working method above applies to slide decks too, via
[deck/build_deck.py](deck/build_deck.py) (full practice + conventions in
[deck/README.md](deck/README.md)):

- **Each slide is its own markdown file; the deck manifest (`deck.json`)
  picks the shipped set.** That is what makes decks safe for concurrent
  threads: one thread reworks slide 4 while another drafts two competing
  versions of slide 9, nothing collides, and **any thread can rebuild the
  whole presentation at any time** — the build is just "assemble the
  manifest's preferred slides." Promoting a competing draft is a one-line
  manifest edit, reviewable like any other change.
- **Two builds from one source.** The *review build* shows speaker notes
  below every slide (and includes `review_only` slides — internal caveats,
  staging notes, drafts). The *send build* **removes** notes and
  review-only slides from the file — they are not merely hidden, so an
  external copy cannot be un-hidden into the internal one. Send only the
  send build.

  ```
  python3 process/upstream/deck/build_deck.py <deck-dir>          # review: <Output>.html
  python3 process/upstream/deck/build_deck.py <deck-dir> --send   # external: <Output>_send.html
  ```

- **Accessing them:** both outputs land next to the deck's `deck.json` and
  open in any browser — arrows navigate, `P` presents full-screen, and
  printing gives one slide per page (that's the PDF path: generated *from*
  the HTML, never a source). The file is fully self-contained — figures,
  theme, everything inlined, verified at build time — so it survives being
  downloaded, emailed, or attached to a chat. Convention: an agent that
  builds a deck delivers the HTML into the conversation as a viewable file
  in the same reply.
- **Decks are content and live in your repo's own directories** — only the
  engine is public. In a private dependent repo, deck sources are exactly
  what the scrub blocklist keeps out of the vendored tree.

Try it: `python3 process/upstream/deck/build_deck.py process/upstream/deck/sample`
builds this repo's own pitch — a deck about BestPractice, dogfooding the
practice it describes.

## Quick start: using BestPractice on a brand-new repo

For a beginner, start to finish. You need a GitHub account and a Claude
account with [Claude Code on the web](https://claude.ai/code) (the same flow
works in the Claude Code CLI or desktop app if you prefer a terminal).

1. **Create the repo.** On github.com: **+ → New repository** → give it a
   name → select **Private** (recommended for your own work; see the scrub
   gate below for what "private" protects) → check **Add a README file** →
   **Create repository**.
2. **Open Claude Code on it.** Go to [claude.ai/code](https://claude.ai/code)
   and start a new session on that repository. The first time, you'll be
   asked to connect GitHub and authorize access to the repo (an
   install/permission screen from GitHub) — approve it for the new repo.
3. **Paste a bootstrap prompt** like this as your first message, filling in
   the two blanks:

   ```
   Install BestPractice into this repo. Fetch the public repo
   https://github.com/alex137/BestPractice (add it to this session, or clone
   it) and copy its working tree into process/upstream/ here. Then follow
   process/upstream/INSTALL.md §1 to instantiate it:

   - This repo is about: <one or two sentences on your project>.
   - Words/names that must never appear in the public vendored tree:
     <your project's private names and code words, for the scrub blocklist>.

   Create MAP.md, TODO.md, GLOSSARY.md and AGENTS.md from the templates,
   apply the harness adapter for this agent (templates/harness/), write
   process/manifest.json, run
   python3 process/upstream/tools/practice_audit.py (it must pass), and
   commit everything on a branch.
   ```

4. **Review and merge.** The agent will push a branch; skim the generated
   files (especially the instructions file — it's the contract every future
   session works under), then merge.
5. **Work normally.** From now on, every session orients from `MAP.md`,
   records open items in `TODO.md`, and runs the export gate before merging.
   That's the whole system — the practices maintain themselves from here.

**Not a Claude Code user?** The practice layer is agent-agnostic: the
canonical instructions file is `AGENTS.md` (read natively by Codex and
others), and everything else is git + markdown + plain Python. The same
bootstrap prompt works in any agent that can read a public repo; see
[templates/harness/README.md](templates/harness/README.md) for the per-agent
wiring (Claude Code, Codex, Gemini CLI — installable side by side, so mixed
agent teams share one contract).

## Git, minimally, for this way of working

You don't need to know git deeply to use this; you need eight ideas:

- **The default branch (`main`) is the shared truth.** It is what every new
  session reads for orientation. Nothing is "real" until it lands there.
- **Each thread works on its own branch** — a private copy of the repo where
  a session (or a person) can make any number of commits without disturbing
  anyone else. Two threads on two branches never conflict *while working*;
  reconciliation happens once, at merge time, under the runbook's rules.
- **Branch work is invisible to everyone else until it lands on `main` —
  and they catch up.** Publishing takes two steps: your branch must be
  *merged* into `main`, and then each collaborator (human or agent session)
  must *pull* the updated `main` into their own copy. Until both happen,
  don't expect others to see your work — a pushed branch technically exists
  on the server, but nobody working from `main` will encounter it. The same
  holds in reverse: someone else's unmerged branch is invisible to you,
  which is why "it's not in the repo" really means "it's not in `main` yet."
- **A pull request (PR) is a reviewable bundle of changes** — "here is
  everything branch X wants to add to main, as a diff." If several people
  (or several agent threads) touch the same repo, PRs are where a second
  pair of eyes goes: you can ask a colleague, or another agent session, to
  review a branch before it merges. For a solo repo, PRs are optional —
  merging directly is fine; the audits are the real gate either way.
- **Permissions decide who may merge.** On a repo someone else owns, you may
  find you can push branches and open PRs but not merge them — the owner
  reviews and merges on their schedule; that's normal, not an error. The
  same lever works for you in the other direction: when your repo gains a
  second contributor, you can require that all changes to `main` go through
  a PR that only you approve and merge (on GitHub: repo Settings →
  Branches → a branch protection/ruleset on `main` requiring pull requests
  before merging). Contributors then work freely on branches while every
  change to the shared truth waits for your review — a good default the
  moment a repo stops being solo.
- **History is permanent.** Every commit is recoverable, so bold edits are
  safe: anything can be diffed against any earlier state and reverted. This
  is what makes "the repo is the memory" trustworthy — memory that can't be
  silently lost or rewritten.
- **One agent can work on branches of several repositories at once.**
  Nothing about git or agents limits a session to a single repo: give it
  access to two (or more) repositories — on GitHub, each repo the agent's
  app installation is permitted to touch; in the Claude Code app
  specifically, you pick which repos the session can access when you
  create it — and it can hold a branch open in each and commit to all of
  them in one conversation. This is not a BestPractice feature, just a
  practical fact coding tools take for granted that matters here: it is
  how **cross-cutting work** gets done — moving content from one repo to
  another, reorganizing which repo owns what, keeping a shared layer in
  sync across repos. This repo's own check-in loop is the worked example:
  a dual-repo session abstracts a practice in the private dependent repo
  and lands it here, in a single thread.
- **An agent session's repo access is fixed when the session starts.** On
  hosted agent platforms, a session can write only to the repo(s) you
  selected when creating it. A session opened on one repo can usually still
  *read* a public repo (clone it, diff against it) but cannot push branches
  or open PRs there — writes fail even though reads work, which is
  confusing the first time you hit it. So decide up front: if a session's
  plan includes pushing to a second repo (the check-in step below, for
  example), **select both repos when you create the session** — you
  generally can't add write access mid-session.

## How it's used (short version)

1. **Install:** copy this repo's contents into `process/upstream/` of your
   dependent repo (plain tracked files — no submodule, no runtime dependency),
   then have your agent follow [INSTALL.md](INSTALL.md): instantiate the
   templates with your repo's subject matter, write `process/manifest.json`
   (what installed where, from which upstream version, with what adaptations),
   and create `process/scrub_blocklist.txt` if your repo is private.
2. **Work:** the installed files are ordinary files in your repo. Nothing here
   is needed at runtime.
3. **Improve:** when a session improves a generic practice, it folds the
   **abstracted** form into `process/upstream/` in the same branch (the
   export gate), and `practice_audit.py` verifies nothing proprietary rode
   along.
4. **Check in:** periodically, propose the accumulated `process/upstream/`
   changes back to this repo as a pull request — in a session opened with
   **both** your repo and BestPractice selected (see the session-scope idea
   in the git section above, and [INSTALL.md](INSTALL.md) §4).

Step 4 in the wild:
[PR #1](https://github.com/alex137/BestPractice/pull/1) is a real check-in —
a dependent repo reworked the templates inside its vendored copy (the
harness-neutral split now in `templates/harness/`), ran the scrub audit, and
proposed the diff back here; once it merged, the dependent repo recorded the
new upstream commit in its manifest. The merged check-in PRs are this repo's
changelog: each one is a practice improvement that was earned in a real repo,
abstracted, and scrubbed on its way in.

This repo is public. Content contributed back from private dependent repos
must pass the scrub gate in [INSTALL.md](INSTALL.md) first — patterns and
abstracted lessons only; no names, numbers, codes, or incident text from the
dependent repo's subject matter.

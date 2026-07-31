# BestPractice

A chat assistant forgets everything when the conversation ends, and its
built-in memory feature is a box you can't open or audit. BestPractice
takes the opposite approach: **make a git repository the memory.** Think
of a hospital chart at shift change: clinicians rotate, but the chart
carries every observation, every decision, and the reasoning behind it —
if it isn't in the chart, it didn't happen — so the incoming doctor picks
up the patient cold, exercises real judgment, and nothing learned on the
last shift is lost in the handover.

BestPractice keeps a project's AI memory in a git repository — instead of
losing it in overlong chat threads or scattering it across a filesystem
with no change tracking. The memory is markdown files, and an index file
tells every new session exactly where to look. That is what lets several
chat threads work on the project at once, sharing what they produce
through the repo and handing off through commit messages instead of
manual catch-ups — and it is why someone new to the project, human or AI,
can open a coding agent on the repo, ask questions, and know everything
they need within minutes. (New to git? Start with
[Git, minimally](GIT.md).)

You can still ask for Word, Excel, PowerPoint, or PDF outputs, but the
system encourages HTML: coding agents build much better HTML than office
files, and the conventions here make sure every graphic and animation is
inlined, so a deliverable still ships as a single file — with far more
room for interactivity than the office formats allow.

This repo is that practice layer, packaged to install: conventions,
templates, and small audit tools you copy into your own repo and adapt to
its subject matter, with improvements flowing back here as pull requests.

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

Working through agents does not mean working blind. Every reply that
created or modified files ends with a **"Files touched"** list: each file
linked twice — as it stands on the working branch (the change, readable
immediately) and as it stands on `main` (the shared version it will
replace) — with a one-line description
([practice 12](PRACTICES.md#12-every-reply-links-the-files-it-touched)).
You see what happened in every interchange, and checking any change is
one click, not a hunt through the repo.

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
  and merges instead of overwrites. (See [Git, minimally](GIT.md).)
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

## Layout

| Path | What it is |
|---|---|
| [PRACTICES.md](PRACTICES.md) | The catalog: each practice as a rule, the (abstracted) incident that motivated it, and how to install it. |
| [INSTALL.md](INSTALL.md) | The agent playbook: install into a dependent repo, take updates, copy improvements back, and the proprietary-scrub gate. |
| [GIT.md](GIT.md) | The eight git ideas this way of working needs — branches, merges, PRs, permissions — for readers new to git. |
| `templates/` | Skeletons a dependent repo instantiates: `AGENTS.md.template` (the harness-neutral instructions file), `MAP.md.template`, `TODO.md.template`, `GLOSSARY.md.template`, `bootstrap.sh`, and `harness/` (per-agent adapters: Claude Code, Codex, Gemini CLI — installable side by side). |
| `tools/` | Portable scripts run in place: [doc_lint.py](tools/doc_lint.py) (markdown hygiene), [practice_audit.py](tools/practice_audit.py) (manifest drift + scrub gate), and [checkin.py](tools/checkin.py) (drives the §4 check-in: status / scrubbed push / verified record). |
| `deck/` | Presentations as code: [build_deck.py](deck/build_deck.py) (the slide-deck engine), [README](deck/README.md) (the practice + conventions), [sample/](deck/sample/) (a working deck about this repo). See "Presentations" below. |

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

**Just exploring?** Paste this README into any chat assistant and ask it
questions — no install, no accounts.

For a beginner, start to finish:

0. **Get two accounts**, if you don't have them already: a git host —
   [GitHub](https://github.com) is the worked example throughout, but any
   host your agent can reach works — and a coding agent, e.g.
   [Claude Code](https://claude.ai/code),
   [Codex](https://openai.com/codex/),
   [Gemini CLI](https://github.com/google-gemini/gemini-cli), or
   [Grok](https://grok.com/). The practice layer is agent-agnostic: the
   canonical instructions file is
   [`AGENTS.md`](templates/AGENTS.md.template), everything else is git +
   markdown + plain Python, and per-agent adapters for Claude Code,
   Codex, and Gemini CLI install side by side (see
   [templates/harness/README.md](templates/harness/README.md)), so mixed
   agent teams share one contract.
1. **Open your coding agent on a repo** — brand-new or existing. If
   creating one on github.com (**+ → New repository**), select
   **Private** (recommended for your own work; see the scrub gate below
   for what "private" protects) and check **Add a README file** — that
   option has nothing to do with BestPractice; it just gives the empty
   repo a first commit so agents have something to open. The first time,
   you'll be asked to authorize the agent's access to the repo — approve
   it.
2. **Paste a bootstrap prompt** like this as your first message, filling in
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

   (When creating a new repo, github.com also offers a box that hands a
   first prompt to its Copilot agent. As of 2026-07 the bootstrap prompt
   is untested there — it needs to clone this public repo, generate
   files, and run a Python audit — so prefer a full coding-agent session,
   the verified path.)

3. **Review and merge.** The agent will push a branch; skim the generated
   files (especially the instructions file — it's the contract every future
   session works under), then merge.
4. **Work normally.** From now on, every session orients from `MAP.md`,
   records open items in `TODO.md`, and runs the export gate before merging.
   That's the whole system — the practices maintain themselves from here.

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
   in [Git, minimally](GIT.md), and [INSTALL.md](INSTALL.md) §4).

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

# BestPractice

A portable process layer for repositories where an AI agent (or a rotating cast
of humans and agents) does the work across many short sessions: **the repo is
the memory**. Conventions, templates, and small audit tools that keep
orientation, open items, decisions, and hard-won lessons in committed files —
so any session can pick up cold — plus the machinery to install these practices
into a *dependent repo*, adapt them to its subject matter, and flow
improvements back here.

## Layout

| Path | What it is |
|---|---|
| [PRACTICES.md](PRACTICES.md) | The catalog: each practice as a rule, the (abstracted) incident that motivated it, and how to install it. |
| [INSTALL.md](INSTALL.md) | The agent playbook: install into a dependent repo, take updates, copy improvements back, and the proprietary-scrub gate. |
| `templates/` | Skeletons a dependent repo instantiates: `AGENTS.md.template` (the harness-neutral instructions file), `MAP.md.template`, `TODO.md.template`, `GLOSSARY.md.template`, `bootstrap.sh`, and `harness/` (per-agent adapters: Claude Code, Codex, Gemini CLI — installable side by side). |
| `tools/` | Portable scripts run in place: [doc_lint.py](tools/doc_lint.py) (markdown hygiene), [practice_audit.py](tools/practice_audit.py) (manifest drift + scrub gate), and [checkin.py](tools/checkin.py) (drives the §4 check-in: status / scrubbed push / verified record). |

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

You don't need to know git deeply to use this; you need seven ideas:

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

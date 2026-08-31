# Repository notes for agents

<!-- These are the instructions for sessions working ON the BestPractice
     repo itself (the upstream). Inside a dependent repo's vendored copy
     (process/upstream/AGENTS.md) this file is inert — the dependent repo
     has its own instantiated AGENTS.md at ITS root. -->

**This repo is becoming Precedent, a restructuring of BestPractice — read
[PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) first, in full, before
touching anything else here.** It is the approved plan of record; its "For
the Session Implementing This" section says how to work from it (phase by
phase, in order — do not read the whole plan trying to hold it all in
context at once; work from the phase you are on).
[spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) documents the phase-1
practice-file format this repo's `practices/*.md` files are written in,
including where the actual conversion had to make a call the plan's own
illustrative example left open. [spec/LOADER.md](spec/LOADER.md) documents
phase 2's loader: what got built, the resident-set curation and why, and
what the behavioral-replay measurement does and does not prove about the
plan's premise.

<!-- BEGIN GENERATED: precedent-loader -->

<!-- Regenerate with: python3 tools/build_views.py -- do not hand-edit this block, tools/verify_harness.py's regeneration check fails on drift. -->

### Resident block (~312 of 2000 token budget, 6 of 52 practices)

**environment-gotchas.** Every expensive environment discovery (a package that must be
installed, a tool that silently doesn't work, a path that does work) is
written into a "do NOT rediscover these" section — with the story of what
failed and why, not just the fix.

**orientation-map.** A top-level `MAP.md` indexes the repo: what the key deliverables
are, where everything lives, and — crucially — which supporting documents back
each part of each deliverable. Every session reads it before doing anything.

**quick-index.** The project instructions file carries a "check here BEFORE searching
the repo" table: *looking for X → go to Y*, one row per thing sessions
actually hunt for.

**reply-links-files.** A session's reply that created or modified files ends with a
"Files touched" list: each entry links the file on the working branch *and*
its post-merge location, with a one-line description. The reader must be able
to open the work from the chat, not merely learn it exists.

**repo-is-memory.** Everything a future session needs — orientation, open items,
decisions, lessons — lives in committed files. A session's chat thread is
disposable; if knowledge exists only in a thread, it is already lost.

**verify-postcondition.** After any state-changing operation, check **the state you wanted**,
not that the command reported success. Name the postcondition before you run
the command — *"no unpushed commits on any branch"*, *"the gate passed"*,
*"the file contains X"* — and then test that, independently of whatever the
command printed.

### Occasion index

```
When a change must propagate across several parallel artifacts:
  parallel-artifact-ledger — ledger the transfer verdict per member, per change
When a computation books a transfer between two parties:
  name-both-sides-of-ledger — name both sides; check what is charged against what is received
When a convention is violated for the first time:
  convention-to-audit — promote a costly broken convention to a script that exits non-zero
When a document presents a script-derived figure:
  docs-track-models — every script-derived figure sits inside a generated block
When a document replaces or is replaced by an earlier one:
  index-remembers-past — put the lineage in the index, not in either document
When a review finds a defect:
  mistakes-become-rules — root-cause the miss, then encode the prevention
When a tool warns about already-published git history:
  no-rewrite-for-warnings — fix the setting forward; never rewrite published history
When an install step adds something GitHub-specific:
  github-setup-disclosed — disclose GitHub-specific setup where the project's people read
When building a mechanism that makes something discoverable or reachable:
  affordance-is-shared — name who else the mechanism you just built now serves
When building a permutation or configuration-sweep table:
  permutation-frontier-column — one full table with a computed Frontier column
When building a variant of an existing thing:
  variant-re-derives — re-derive what a variant inherits; limits bind, choices do not
When building or committing a generated artifact:
  generated-artifact-provenance — stamp a build code and a manifest; never hand-edit output
When committing anything that touches the vendored/public tree:
  scrub-gate — the public tree is public-safe at all times, not just at check-in
When comparing an option against a baseline:
  check-source-architecture — check both options exist in the source before costing them
When deciding where a new rule belongs:
  layered-practice-packs — generic, domain, repo-local — each rule to its own layer
When deciding whether to build or buy a component:
  build-buy-decompose — decompose first; one verdict per part, on ownership grounds
When exporting a tool across a repo boundary:
  engine-plus-host-shims — one vendored engine, thin host shims, never a fork
When finishing a substantial work-product, before the merge-time capture gate:
  second-pass-capture — a separate capture pass after the work, not inside it
When merging a branch:
  capture-gate — capture the follow-on work in the thread that created the need
When merging a branch that improved a generic practice:
  practice-export-loop — vendor upstream as tracked files; check improvements back in
When merging a branch that touches shared files:
  merge-runbook — write conflict resolution per file class, once, then follow it
When naming a new file:
  no-version-suffix — name a file for what it is; the repository is the version
When naming what "run the checks" means in a repo:
  two-check-levels — name a fast check and a full check; say which gates what
When ordering sections in a document:
  section-order-by-frequency — order sections by how often the reader needs them
When printing a numeric quantity that will be compared across rows:
  one-formatter-per-quantity — one formatter per quantity kind, declared in one module
When publishing a document with a multi-column sortable table:
  tabular-shared-renderer — ship a sortable render from the one shared renderer
When quoting or compressing someone else's figures:
  quote-discipline — compression rounds against you; qualifiers travel with the figure
When reporting a computed total or a negative feasibility result:
  verify-decomposition — check the parts, not the total; never assert an impossibility
When setting up a new repo's session start:
  session-bootstrap — setup lives in a session-start hook, not in memory
When starting an outward-facing deliverable:
  frame-from-audience-question — build it around the audience's question, not your material
When starting work the repository may already cover:
  search-by-purpose — search by purpose and by mechanism before concluding nothing exists
When the user gives a standing merge instruction:
  merge-authorization-keyword — one fixed word means "merge as agreed"; document it exactly
When tracking state that multiple documents need to agree on:
  registry-source-of-truth — state lives in one machine-readable registry; documents derive
When writing a README or other project-facing entry document:
  lead-with-what-it-is — say what the project is before how it is maintained
When writing a document that cites a computed number:
  computed-numbers-in-scripts — computed content lives in a sync-gated generated block
When writing a new convention or rule:
  cite-the-incident — record the failure a rule prevents, inline with the rule
When writing a reader-facing deliverable with supporting apparatus:
  deliverables-look-like-output — the deliverable holds only what its audience needs
When writing a rule that depends on the outside world:
  volatile-rules-carry-dates — a rule about the outside world carries its date, inline
When writing a script whose numbers a document will cite:
  scripts-assert-properties — scripts assert their own properties and their cited anchors
When writing an outward-facing document:
  readers-vocabulary — use the reader's words; gloss inline or replace
When writing an outward-facing summary of claims:
  outward-summary-discipline — claims-to-source table, honest sums, a recorded adversarial pass
When writing or editing a document:
  acronyms-glossary — expand acronyms on first use; keep one central glossary
  doc-references-are-links — reference repo files as relative links; use ≈, never ~
  docs-are-current-state — state what is true now; version control holds the history
  label-describes-content — "one line" must be one line; else name it for its content
When writing or filling out a pull-request description:
  pr-template-honest-gates — write the body from the diff; an unchecked box is fine
```

### Standing instruction

Before starting work of a kind named in the occasion index above, run `python3 tools/precedent_show.py SLUG` for each listed slug to load its Rule. When editing a file, `python3 tools/precedent_paths.py FILE` prints any on-demand practice whose `applies_to` matches it, without needing the index at all.

<!-- END GENERATED -->

The rest of this file (below) is BestPractice's own pre-fork orientation —
still accurate for `PRACTICES.md`, `INSTALL.md`, and the rest of the
inherited tree, which the plan has not restructured yet. It will be rewritten
in place as later phases land (the plan's own generated-views work, phase 2)
rather than kept as a second, drifting copy.

---

**Orientation: read [README.md](README.md) first.** This repo is
BestPractice itself — the upstream practice layer that dependent repos
vendor. Practices you follow here are the ones this repo teaches; a session
that skips them in this repo of all places is the joke writing itself.

## Where things are (quick index — check here BEFORE searching)

| Looking for… | Go to |
|---|---|
| The restructuring plan (read this first) | [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) |
| The phase-1 per-practice file format | [spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) |
| The phase-2 loader (resident set, replay measurement) | [spec/LOADER.md](spec/LOADER.md) |
| The phase-3 brief (what phase 3 was handed) | [spec/PHASE3_BRIEF.md](spec/PHASE3_BRIEF.md) |
| The phase-3 sources: resolver, precedence, what could not be built here | [spec/SOURCES.md](spec/SOURCES.md) |
| The phase-4 enforced channel: what is checked, and what each check is blind to | [spec/ENFORCEMENT.md](spec/ENFORCEMENT.md) |
| Populating the two private sets (the open half of phase 3) | [spec/PRIVATE_SETS_BRIEF.md](spec/PRIVATE_SETS_BRIEF.md) |
| Which practices are enforced, and running one check | [tools/precedent_check.py](tools/precedent_check.py) — `--list`, `--explain`, `--only SLUG` |
| The catalogue's own figures (resident size, Rule share, coverage) | [tools/catalogue_stats.py](tools/catalogue_stats.py) — never hand-type these into prose |
| Precedent explained for someone adopting it (not a developer) | [ADOPTING.md](ADOPTING.md) |
| Which practice libraries are in force in this repo | [precedent.json](precedent.json) |
| An example personal practice set | [examples/practice-set/](examples/practice-set/) |
| The private-term blocklist template (copy into your own private set) | [templates/leak-blocklist.txt.template](templates/leak-blocklist.txt.template) |
| The leak gate (push-time; both layers live) | [tools/leak_gate.py](tools/leak_gate.py) — `--explain` for what it does and does not check |
| The editorial section split, as reviewable data | [tools/section_split.json](tools/section_split.json), applied by [tools/resplit_sections.py](tools/resplit_sections.py) |
| The converted practice files (phase 1) | [practices/](practices/) |
| What each practice is and why | [PRACTICES.md](PRACTICES.md) |
| Repo map, generated (phase 2) | [MAP.md](MAP.md) — regenerate with `tools/build_views.py`, never hand-edit |
| Canonical names, generated (phase 2) | [GLOSSARY.md](GLOSSARY.md) — built from every practice's `defines:` field |
| The loader — resident block, occasion index, path-trigger channel | This file's generated block above; engine at [tools/build_views.py](tools/build_views.py), [tools/precedent_paths.py](tools/precedent_paths.py) |
| Loader premise, measured against this repo's own history | [tools/behavioral_replay.py](tools/behavioral_replay.py) |
| Install / update / check-in playbook (dependent repos) | [INSTALL.md](INSTALL.md) |
| Guided-install entry point admins paste to their agent | [SETUP.md](SETUP.md) |
| Member onboarding page (template + rendered sample) | [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md) |
| Git/GitHub concepts for this workflow | [GIT.md](GIT.md) |
| The working method (branches, plain text, critique, prompts) | [METHOD.md](METHOD.md) |
| Phone / ChatGPT / Grok workflows + assistant reliability status | [MOBILE.md](MOBILE.md) |
| CI checks for shell-less agents (install, require) | [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) |
| Upstream open items / roadmap | [TODO.md](TODO.md) |
| GitAround — the reading view this work spun out | [alex137/GitAround](https://github.com/alex137/GitAround), a separate product since 2026-08-14; a branch here still staging it under proposals/ is superseded, and its documents live there now |
| Slide-deck engine + deck conventions | [deck/](deck/) — engine [build_deck.py](deck/build_deck.py), practice in [deck/README.md](deck/README.md) |
| Portable audits | [tools/](tools/) — [doc_lint.py](tools/doc_lint.py), [practice_audit.py](tools/practice_audit.py), [checkin.py](tools/checkin.py) |
| Skeletons dependent repos instantiate | [templates/](templates/) (+ per-agent adapters in [templates/harness/](templates/harness/)) |

## Build-environment gotchas — do NOT rediscover these

Each entry carries what failed, not only the fix — the fix alone is a fact
you cannot judge, and the next session re-derives it the moment it looks
wrong. [tools/precedent_check.py](tools/precedent_check.py) gates this
section: an entry with no failure attached fails `--only environment-gotchas`.

- **`pip install cmarkgfm`, or [tools/doc_lint.py](tools/doc_lint.py)'s
  strikethrough check silently stops running.** Without it the check does not
  fail — it prints a one-line notice and scans for everything else, so a
  document that renders an unintended `<del>` on GitHub passes the gate.
  [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh) installs
  it, but only when `CLAUDE_CODE_REMOTE=true`; a local shell has to do it.

- **This repo is normally cloned `--depth 1`, and several tools degrade
  rather than fail on that.** [tools/behavioral_replay.py](tools/behavioral_replay.py)
  divided by the replayable-commit count and took the whole harness down with
  a `ZeroDivisionError` on a one-commit clone — the exact environment a fresh
  session starts in. It now reports `REPLAY_STATUS: DEGRADED` instead. On the
  same clone `origin/main` does not exist, so doc_lint's changed-vs-default-branch
  scope quietly becomes changed-vs-`HEAD`: it checks your uncommitted files
  and nothing else. Fix both with a bounded
  `git fetch --depth=500 origin <branch>`; some git policy hooks block
  `--unshallow`, and a bounded fetch works either way.

- **`git clone --depth 1 /some/path` is ignored; git only honours `--depth`
  over a transport.** A phase-2 smoke test believed it was exercising a
  shallow clone for an hour and was not — the bug it was written to catch was
  still there. Use `file:///some/path` to force a genuinely shallow local
  clone.

- **The leak gate's vocabulary layer fails open unless you also set the git
  config.** `export PRECEDENT_LEAK_BLOCKLIST=<a path OUTSIDE this repo>` is
  half of it; without `git config precedent.requireVocabulary true` a shell
  that starts without the variable prints `PARTIAL`, exits 0, and the push
  goes through with only the structural rules applied. Every push here is
  publication into a public repository, so the half-configured state is the
  dangerous one. See `python3 tools/leak_gate.py --explain`.

- **Four inherited audits are NOT APPLICABLE in this repo, and three of them
  used to say `FAIL` instead.** [tools/practice_audit.py](tools/practice_audit.py)
  wants a `process/manifest*.json`, [tools/doc_sync.py](tools/doc_sync.py)'s
  `PAIRS` is empty and [tools/model_audit.py](tools/model_audit.py)'s
  `INSTRUMENTED` is empty — all correct, because this repo is the upstream
  they audit a *dependent* repo against. Two of them exited non-zero for that
  reason and one printed `OK` on having inspected nothing, so the first were
  permanently red and the last was a confident all-clear from a scan that
  never ran. They now say NOT APPLICABLE with the reason, and
  [tools/precedent_check.py](tools/precedent_check.py) reports that as
  skipped rather than passed.

## Working in this repo

- **Default branch is `main`; work on a feature branch; PRs are the norm**
  here (this repo is public and is the shared upstream).
- **Most changes arrive as check-in PRs from dependent repos** (INSTALL.md
  §4). Reviewing one, you are the **second scrub line**: the contributing
  repo's blocklist caught its known private vocabulary; you catch what it
  didn't know yet. A name, number, or incident detail that reads
  subject-specific rather than generic should be challenged before merge —
  and added to the contributor's blocklist, not fixed up here after
  publication.
- **Direct edits are fine** for content about this repo itself (README,
  practice wording, engine code); abstracted lessons still only enter via
  a scrubbed check-in from where they were learned.
- **Before committing:** `python3 tools/doc_lint.py` on markdown you
  touched (`pip install cmarkgfm` — the session-start hook does this);
  after touching the deck engine, rebuild the sample both ways:
  `python3 deck/build_deck.py deck/sample` and `--send`.

## Conventions (every session, every reply)

- **Reply convention** (practice 12): every reply that created or modified
  files ends with a **"Files touched"** list — for each file, the branch
  link (readable now) plus the post-merge `main` link, with a one-line
  description. The reader opens the work from the chat; they never go
  hunting for it. A touched HTML render or picture also gets its
  rendered-view (artifact) link when the harness offers one — a repo link
  shows source, not the render.
- **Doc references are links** (practice 11): relative markdown links,
  never bare backticked filenames. Use `≈`, not `~`, for "approximately".
- **Volatile rules carry their dates** (practice 16): anything asserted
  here about an external platform or tool carries *as of / verified
  `<date>`* inline, in the contributor's local calendar date, not the
  agent's system clock.
- **Outward-facing documents use the reader's words** (practice 34): this
  repo's README, [SETUP.md](SETUP.md), and
  [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md) are read by
  people who are not developers. Terms that name a category are the
  reader's word, a plain equivalent, or glossed inline — never left to a
  glossary. Jargon arrives from the sources a session just read, so run
  the check as a separate pass after drafting.
- **Built decks are delivered** ([deck/README.md](deck/README.md)
  convention 3): a session that builds a deck attaches the HTML into the
  conversation as a viewable file in the same reply, and only ever sends
  the `--send` build externally.

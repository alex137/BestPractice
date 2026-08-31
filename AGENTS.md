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

### Resident block (~845 of 2000 token budget, 7 of 52 practices)

**environment-gotchas.** Every expensive environment discovery (a package that must be
installed, a tool that silently doesn't work, a path that does work) is
written into a "do NOT rediscover these" section — with the story of what
failed and why, not just the fix.

**mistakes-become-rules.** When a mistake is caught — by the owner, by an audit, or by a later
pass discovering an earlier session's error — fixing the instance is half the
job. Before the session ends, root-cause it *five-whys style*: ask why
iteratively, past the surface slip, until the answer is a **process
property** — a missing rule, a missing check, a judgment recorded at the
wrong granularity, a stale document trusted, a default that invites the
error — stopping at the level where a cheap guard exists. Then encode the
prevention at the strongest rung available: (a) an **audit or lint** if the
failure is mechanically checkable (practice 6 — conventions become audits);
(b) else a **written rule, dated, carrying its origin incident** (practices
5 and 16 — the incident is both the justification and the test case); (c) if
the lesson is generic, **export it** (practice 14). Discuss the choice with
the owner when it involves a judgment call — which rung, what scope, whether
the guard is worth its cost.

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

**Rendered files get a rendered-view link, not just a repo link.** A
repository link to an HTML file or an image shows source or a raw blob — the
one form of the file the reader did *not* want. When the session's surface
offers hosted private previews (an artifact/paste service the harness
provides), a touched HTML render or picture's entry also carries that
rendered-view link, published from the same file path each time so the link
stays stable across revisions — one preview per file, re-published on
meaningful change, never a new one per reply. Files that are per-recipient
send records are excluded: a hosted preview is a distribution channel, and
those files' distribution is governed by their own send policy.

**repo-is-memory.** Everything a future session needs — orientation, open items,
decisions, lessons — lives in committed files. A session's chat thread is
disposable; if knowledge exists only in a thread, it is already lost.

**verify-postcondition.** After any state-changing operation, check **the state you wanted**,
not that the command reported success. Name the postcondition before you run
the command — *"no unpushed commits on any branch"*, *"the gate passed"*,
*"the file contains X"* — and then test that, independently of whatever the
command printed.

Two traps deserve naming because they produce confident, wrong success
messages:

- **A pipeline's exit status is its last command's.** `check | tail && publish`
  does not gate on `check`. The gate can print FAIL in plain sight and the
  publish still proceeds. Run gates bare and test `$?`; if you pipe for
  readability, capture the status first or use the shell's pipe-status
  facility.
- **A command with an explicit target acts on the target you named, not the
  context you are in.** Publishing by naming a branch publishes *that* branch,
  whether or not it is the one you have been working on. If it has not moved,
  the operation succeeds as a no-op and says so.

### Occasion index

```
When a change must propagate across several parallel artifacts:
  parallel-artifact-ledger — When a family of artifacts embodies **one design in several
When a computation books a transfer between two parties:
  name-both-sides-of-ledger — When a model charges one party for what another receives — work for
When a convention is violated for the first time:
  convention-to-audit — Prose rules are advisory; a non-zero exit is not.
When a document presents a script-derived figure:
  docs-track-models — Extending practice 19 from *tables* to **every** figure a script
When a document replaces or is replaced by an earlier one:
  index-remembers-past — Current-state documents (the no-revision-history rule) still need
When a tool warns about already-published git history:
  no-rewrite-for-warnings — When a hook, linter, badge, or CI check complains about commits that
When an install step adds something GitHub-specific:
  github-setup-disclosed — Whenever an install step adds something GitHub-specific that a
When building a mechanism that makes something discoverable or reachable:
  affordance-is-shared — **The practice.** When you add a mechanism so that *your* system can do something
When building a permutation or configuration-sweep table:
  permutation-frontier-column — A configuration study whose table is the cross-product of its input axes
When building a variant of an existing thing:
  variant-re-derives — When you build a variant of an existing thing — a new configuration
When building or committing a generated artifact:
  generated-artifact-provenance — Generated deliverables are never hand-edited and never casually
When committing anything that touches the vendored/public tree:
  scrub-gate — When the dependent repo is private and this repo is public,
When comparing an option against a baseline:
  check-source-architecture — **The practice.** Before costing or optimising a trade between two configurations,
When concluding that no prior work exists on a question:
  search-by-purpose — **The practice.** Before concluding that no prior work exists on a question,
When deciding where a new rule belongs:
  layered-practice-packs — Rules come in three scopes, and each gets its own home.
When deciding whether to build or buy a component:
  build-buy-decompose — A build-or-buy question almost always arrives at the wrong
When exporting a tool across a repo boundary:
  engine-plus-host-shims — A practice that ships tooling (a renderer, a lint, a sync gate) crosses the
When finishing a substantial work-product, before the merge-time capture gate:
  second-pass-capture — After producing any substantial work-product — a document, a design,
When merging a branch:
  capture-gate — The thread that develops a capability, a number, a decision, or a
When merging a branch that improved a generic practice:
  practice-export-loop — A dependent repo vendors this repo at `process/upstream/` as plain
When merging a branch that touches shared files:
  merge-runbook — When many branches touch the same shared files, merge conflicts are
When naming a new file:
  no-version-suffix — A new file is named for what it *is*, with no `_v1` / `_rev2` label —
When naming what \"run the checks\" means in a repo:
  two-check-levels — A repo of any size ends up wanting two different things when it
When ordering sections in a document:
  section-order-by-frequency — In any document that walks through instructions, guidance, or rules
When printing a numeric quantity that will be compared across rows:
  one-formatter-per-quantity — A reader comparing two table cells must never have to normalize precision
When publishing a document with a multi-column sortable table:
  tabular-shared-renderer — When a document's tables have multiple columns a reader might want
When quoting or compressing someone else's figures:
  quote-discipline — Two obligations whenever a document quotes a figure from another
When setting up a new repo's session start:
  session-bootstrap — Environment setup that sessions need (packages, dependencies,
When starting an outward-facing deliverable:
  frame-from-audience-question — When you finish producing a body of work and then write the thing
When the user gives a standing merge instruction:
  merge-authorization-keyword — A repo can adopt one short, fixed word or phrase that, said as
When tracking state that multiple documents need to agree on:
  registry-source-of-truth — Any status that scripts or sessions make decisions on (what's
When trusting a model's total without checking its parts:
  verify-decomposition — **The practice.** A model earns trust through how it is built, not through whether
When writing a README or other project-facing entry document:
  lead-with-what-it-is — An outward document that both describes a project and explains how
When writing a document that cites a computed number:
  computed-numbers-in-scripts — When a document presents content that a script computes — a summary
When writing a new convention or rule:
  cite-the-incident — When you write a rule, record what failure it prevents, inline.
When writing a reader-facing deliverable with supporting apparatus:
  deliverables-look-like-output — A reader-facing document is the finished product: it contains what its
When writing a rule that depends on the outside world:
  volatile-rules-carry-dates — A rule whose truth depends on the outside world — the behavior of
When writing a script whose numbers a document will cite:
  scripts-assert-properties — A script that computes numbers other work depends on carries two
When writing an outward-facing document:
  readers-vocabulary — A document written for an audience outside the work — a README, a
When writing an outward-facing summary of claims:
  outward-summary-discipline — A document that summarizes a body of work for an external audience
When writing or editing a document:
  acronyms-glossary — A domain-dense repo accumulates far more acronyms and coined terms
  doc-references-are-links — (a) In-repo documents reference other repo files as relative
  docs-are-current-state — A document reads as a statement of what is true *now*, not a log of
  label-describes-content — A heading or lead-in that names a form or length must match what it
When writing or filling out a pull-request description:
  pr-template-honest-gates — Every dependent repo installs a default pull-request template
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

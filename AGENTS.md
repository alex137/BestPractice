# Repository notes for agents

<!-- These are the instructions for sessions working ON the BestPractice
     repo itself (the upstream). Inside a dependent repo's vendored copy
     (process/upstream/AGENTS.md) this file is inert — the dependent repo
     has its own instantiated AGENTS.md at ITS root. -->

**TEMPORARY, read before opening or merging any pull request (PR) here:
every PR in this repository targets `precedent-beta-v01`, never `main`, until Alex reviews
and merges `precedent-beta-v01` into `main` for real — a deliberate,
phase-7 act, not something any routine PR does incidentally. Merging a PR
into `precedent-beta-v01` needs no sign-off from Alex — once its deep
check passes, a session may merge it directly; that branch is where
routine work lands, not a gate he sits behind. Alex's approval is reserved
for `main`, and specifically for merges carrying major changes onto it —
the phase-7 fold-in is the paradigm case, but any other merge reaching
`main` with a non-trivial change needs the same explicit, named go-ahead.
A general "PR and merge it" authorization, with no branch named, still
means `precedent-beta-v01`; merging into `main` requires Alex naming
`main` explicitly, in that specific request. Check the base branch
explicitly before acting — do not assume `main` just because it is the
repository's configured default branch, and do not assume the two
branches are interchangeable even when they happen to sit at the same
commit, which is exactly the condition under which this rule's own
origin incident happened. Full story, the mechanical check, and the
retirement condition:
[local/practices/merge-target-is-beta-branch.md](local/practices/merge-target-is-beta-branch.md).**

**"Go merge" is Morgan's own phrase, not a rule of this repository.** It
is defined in his individual practice set as `go-merge`, and it reaches a
session only through `.precedent/SESSION_PRACTICES.md` — so a session that
did not attach the private sources (see the banner below) has not read the
definition, and must **ask what is meant rather than guess from these two
sentences**. What the repository itself contributes is only the
destination: an authorization to merge, in whatever words it arrives, means
`precedent-beta-v01` per the paragraph above, and is not done until a fetch
confirms the pushed content is actually there
([verify-postcondition](practices/verify-postcondition.md)). The universal
practice that used to sit here, `merge-authorization-keyword`, was retired
on 2026-09-07: it was telling every adopting repository to go adopt a merge
keyword of its own, which is one person's preference dressed as a practice.

**FIRST TOOL CALL OF EVERY SESSION, before reading or running anything
else: `add_repo` (read access) for this account's `precedent-individual`,
and for any `precedent-team-*` set [precedent.json](precedent.json)
declares. Silently — no confirmation first.** These are private
repositories, and a session is granted them per session; nothing is
inherited because a file names them. Until that call is made, every
personal and team practice in force here is **silently absent**, and this
repository's rules are the only ones a session sees.

Nothing else can do it for you. `.claude/hooks/precedent-individual-bootstrap.sh`
runs to completion *before* the agent's first turn begins, so it cannot
call `add_repo` — its own header explains why a retry loop there was tried
and proven inert. The hook then succeeds on its own when
[tools/precedent_resolve.py](tools/precedent_resolve.py) re-invokes it
later in the turn, which only helps if the access exists by then. If
`add_repo` genuinely fails, say so plainly and carry on: those practices
are simply not in force that session, and a session that does not know
that will confidently apply the wrong ones.

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

## Resident block (~552 of 2000 token budget, 8 of 74 practices (8 universal))

**bold-key-phrases.** People don't read; they skim, and bolding makes skimming easy. Bold the key phrases in a document by default, without being asked, scaling with length -- a long paragraph or document is where a skimmer most needs a spine to follow, a short note usually needs little or none.

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

**reply-links-files.** A session's reply that created, modified or deleted files ends with a
"Files touched" list: each entry links the file on the working branch *and*
its post-merge location, with a one-line description. The reader must be able
to open the work from the chat, not merely learn it exists. **A deleted file
is listed too** — its path, why it went, and a link to the commit that
removed it. It is the one entry with nothing to open on the branch, which is
exactly why a reader will not find it on their own.

**repo-is-memory.** Everything a future session needs — orientation, open items,
decisions, lessons — lives in committed files. A session's chat thread is
disposable; if knowledge exists only in a thread, it is already lost.

**verify-postcondition.** After any state-changing operation, check **the state you wanted**,
not that the command reported success. Name the postcondition before you run
the command — *"no unpushed commits on any branch"*, *"the gate passed"*,
*"the file contains X"* — and then test that, independently of whatever the
command printed.

**write-like-a-human.** **Nothing you ship may sound like it came from an AI** — a document, a
chat reply, a commit message, a pull-request body. The tells: the
throat-clearing opener that circles before it lands, the "not just X,
it's Y" contrast, the summary nobody asked for, the even-handed survey
that takes no position, the caveat stack. **Say the thing, in your own
words, at the length it earns.**

Unrewritten model output is output nobody thought about — style is the
cheapest evidence a reader has that somebody did.

## Occasion index

```
When a change here has implications for how an attached team, individual, or repo-local source should work:
  cross-source-rollout — roll it out to attached sources now; else a blocked-on TODO
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
When a person explicitly asks for a "very deep check" across the whole repo, or after work that invites drift:
  very-deep-check — read every repo in force against itself, pass by pass; never a routine gate
When a person explicitly asks for a full practice audit (or "practice check") across the whole catalogue:
  full-practice-audit — sweep every source's full catalogue, one practice at a time, on request only
When a practice lands or a candidate is raised, at any level:
  disclose-landing — state plainly what happened and where — individual, named team, or universal
When a review finds a defect:
  mistakes-become-rules — root-cause the miss, then encode the prevention
When a tool warns about already-published git history:
  no-rewrite-for-warnings — fix the setting forward; never rewrite published history
When adding or re-levelling a heading in any document:
  heading-outline — never jump a heading level; a heading one below its parent, or deeper by one
When adding or re-syncing a document under philosophy/:
  philosophy-declares-its-source — an essay carries its origin on line one -- a record, not a sync pointer
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
When checking whether the practices that should have fired for recent work actually fired:
  routing-audit — run the mechanical coverage check now; roll the deep-read slice forward
When committing anything that touches the vendored/public tree:
  scrub-gate — the public tree is public-safe at all times, not just at check-in
When comparing an option against a baseline:
  check-source-architecture — check both options exist in the source before costing them
When creating, migrating, closing or superseding a document under spec/ or record/:
  document-status-header — kind and status in frontmatter; a reader must not have to infer either
When deciding where a new rule belongs:
  layered-practice-packs — generic, domain, repo-local — each rule to its own layer
When deciding whether to build or buy a component:
  build-buy-decompose — decompose first; one verdict per part, on ownership grounds
When exporting a tool across a repo boundary:
  engine-plus-host-shims — one vendored engine, thin host shims, never a fork
When finishing a substantial work-product, before the merge-time capture gate:
  second-pass-capture — a separate capture pass after the work, not inside it
When importing, creating, or declaring a repository that holds practices:
  source-naming — names are fixed by level; say the convention before anyone picks a name
When landing practices in bulk -- a migration, an import, or a move between sources:
  catalogue-carries-stories — no active practice sits with an empty ## Story
When merging a branch:
  capture-gate — capture the follow-on work in the thread that created the need
When merging a branch that improved a generic practice:
  practice-export-loop — vendor upstream as tracked files; check improvements back in
When merging a branch that touches shared files:
  merge-runbook — write conflict resolution per file class, once, then follow it
When migrating a repo off an old practice system onto Precedent:
  migration-scrubs-vocabulary — scrub the old system's vocabulary the same session, not on request
When naming a new file:
  no-version-suffix — name a file for what it is; the repository is the version
When naming what "run the checks" means in a repo:
  two-check-levels — name a fast check and a full check; say which gates what
When opening or merging a pull request in this repository:
  merge-target-is-beta-branch — Alex approves only major main merges; precedent-beta-v01 is unrestricted
When ordering sections in a document:
  section-order-by-frequency — order sections by how often the reader needs them
When printing a numeric quantity that will be compared across rows:
  one-formatter-per-quantity — one formatter per quantity kind, declared in one module
When publishing a document with a multi-column sortable table:
  tabular-shared-renderer — ship a sortable render from the one shared renderer
When quoting or compressing someone else's figures:
  quote-discipline — compression rounds against you; qualifiers travel with the figure
When renaming, moving, or deleting a file other files may link to:
  rename-updates-links — renaming a file means repointing every link to it, in the same commit
When reporting a computed total or a negative feasibility result:
  verify-decomposition — check the parts, not the total; never assert an impossibility
When retiring a mechanism — a workflow, a tool, a vendored tree, a config — that leaves files behind with no remaining job:
  retirement-deletes-files — delete what the retired mechanism owned; audit first, never on a hunch
When setting up a new repo's session start:
  session-bootstrap — setup lives in a session-start hook, not in memory
When starting an outward-facing deliverable:
  frame-from-audience-question — build it around the audience's question, not your material
When starting work the repository may already cover:
  search-by-purpose — search by purpose and by mechanism before concluding nothing exists
When tracking state that multiple documents need to agree on:
  registry-source-of-truth — state lives in one machine-readable registry; documents derive
When writing a README or other project-facing entry document:
  lead-with-what-it-is — say what the project is before how it is maintained
When writing a document that cites a computed number:
  computed-numbers-in-scripts — computed content lives in a sync-gated generated block
When writing a new convention or rule:
  checkable-gets-checked — attempt a mechanical check before leaving a new practice advisory-only
  cite-the-incident — record the failure a rule prevents, inline with the rule
When writing a reader-facing deliverable with supporting apparatus:
  deliverables-look-like-output — the deliverable holds only what its audience needs
When writing a rule that depends on the outside world:
  volatile-rules-carry-dates — a rule about the outside world carries its date, inline
When writing a script whose numbers a document will cite:
  scripts-assert-properties — scripts assert their own properties and their cited anchors
When writing a test, fixture or control that proves a guard fires:
  control-asserts-which-failure — a non-zero exit is not evidence; assert the message that guard prints
When writing an outward-facing document:
  readers-vocabulary — use the reader's words; gloss inline or replace
When writing an outward-facing summary of claims:
  outward-summary-discipline — claims-to-source table, honest sums, a recorded adversarial pass
When writing code because a specific practice requires it:
  code-cites-practice — cite the practice's slug in a comment, right where the code is
When writing code that depends on something outside its own control, handling a part that could not run, or deciding how loudly to report one:
  fail-gracefully — keep going, never look complete — match the telling to stake and reader
When writing or editing a document:
  acronyms-glossary — expand acronyms on first use; keep one central glossary
  doc-references-are-links — reference repo files as relative links; use ≈, never ~
  docs-are-current-state — state what is true now; version control holds the history
  label-describes-content — "one line" must be one line; else name it for its content
When writing or editing a heading in an outward-facing document:
  headline-capitalization — outward-facing headings are New York Times headline case, applied by tool
When writing or editing anything under philosophy/, or citing it from a rule:
  philosophy-is-not-repo-policy — philosophy/ is argument; a rule that earned its way out gets written as a practice file
When writing or filling out a pull-request description:
  pr-template-honest-gates — write the body from the diff; an unchecked box is fine
When writing or triaging an open item:
  todo-is-a-handoff — queue only for a stated blocked-on/out-of-scope reason — otherwise just do it
```

## Standing instruction

Before starting work of a kind named in the occasion index above, run `python3 tools/precedent_show.py SLUG` for each listed slug to load its Rule. When editing a file, `python3 tools/precedent_paths.py FILE` prints any on-demand practice whose `applies_to` matches it, without needing the index at all. At a named moment — merging a branch, reviewing work, before pushing, ending a turn and writing the reply — run `python3 tools/precedent_gate.py merge|review|push|reply`: some practices fire at a moment rather than in a file, and no path glob reaches those. If `.precedent/SESSION_PRACTICES.md` exists, read it too: it carries the practices in force from this repo's team, individual and repo-local sources, which are NOT in this block and bind work here exactly as these do. It is regenerated at session start and is deliberately untracked — never commit it or quote it into a pull request.

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
| Inherited practices whose meaning or mechanism changed under Precedent (Alex needs to hear about these) | [CHANGES_TO_TELL_ALEX.md](CHANGES_TO_TELL_ALEX.md) |
| The phase-1 per-practice file format | [spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) |
| The phase-2 loader (resident set, replay measurement) | [spec/LOADER.md](spec/LOADER.md) |
| The phase-3 brief (what phase 3 was handed) | [spec/PHASE3_BRIEF.md](spec/PHASE3_BRIEF.md) |
| The phase-3 sources: resolver, precedence, what could not be built here | [spec/SOURCES.md](spec/SOURCES.md) |
| How a practice-set source is named — the convention, what refuses vs. warns, and what a session must say before anyone picks a name | [spec/SOURCE_NAMING.md](spec/SOURCE_NAMING.md), rule at [practices/source-naming.md](practices/source-naming.md) |
| The phase-4 enforced channel: what is checked, and what each check is blind to | [spec/ENFORCEMENT.md](spec/ENFORCEMENT.md) |
| The phase-5 creation pipeline: what got built stage by stage, what's deferred, what phase 6 inherits | [spec/PHASE5_BRIEF.md](spec/PHASE5_BRIEF.md) |
| The phase-5 candidate file format (Stage 2) and why universal candidates are GitHub Issues, not files | [spec/CANDIDATE_FORMAT.md](spec/CANDIDATE_FORMAT.md) |
| The phase-5 deep-check before phase 6: real bugs found and fixed, real candidates landed, open questions for Morgan | [spec/PHASE5_DEEPCHECK.md](spec/PHASE5_DEEPCHECK.md) |
| The phase-6 brief: what's closed, what's blocked and needs Morgan, what's still ahead and needs the target repo attached | [spec/PHASE6_BRIEF.md](spec/PHASE6_BRIEF.md) |
| The pre-launch audit (2026-09-06): what a real from-scratch install, a real migration and a real two-team resolve actually broke, what got fixed, and the list of what is still open — **read this before the next audit pass** | [spec/PRELAUNCH_AUDIT.md](spec/PRELAUNCH_AUDIT.md) |
| The pre-fork catalogue audit: verdict per inherited practice against this plan's architecture | [spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md) |
| Populating the two private sets (done 2026-09-01, closing phase 3 — brief kept for how it was done) | [spec/PRIVATE_SETS_BRIEF.md](spec/PRIVATE_SETS_BRIEF.md) |
| Bootstrapping a brand-new individual or team set from zero — the generalized procedure any adopter follows, plus the tool and skeletons it uses | [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md), tool at [tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py), skeletons at [templates/practice-set-individual/](templates/practice-set-individual/) and [templates/practice-set-team/](templates/practice-set-team/) |
| Bringing mechanical checks to the two private sets' practices (open; cannot run from here) | [spec/PRIVATE_ENFORCEMENT_BRIEF.md](spec/PRIVATE_ENFORCEMENT_BRIEF.md) |
| How a repo that already had BestPractice installed migrates to Precedent's three-source model (the recommended pattern, from the first real dependent-repo test) | [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md) |
| Deleting a file or directory a retired mechanism left behind — the audit that has to pass first, and the record of what went | [practices/retirement-deletes-files.md](practices/retirement-deletes-files.md), audit at [tools/precedent_retire_path.py](tools/precedent_retire_path.py) |
| Moving an existing, still-wanted practice from one level to another (team ↔ individual, team ↔ team) — distinct from creating one or retiring one outright | [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md) |
| Why the miss rate is what it is, and the plan for it (read before phase 5) | [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md) |
| A locked-down access pattern for non-technical contributors (Triage/Read GitHub role + restricted session config + plain-language candidate flow) — drafted, not yet executed | [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md) |
| Team-level practice capture for non-technical document work at scale (a shared editorial team repo + a reusable document-project template — the "alternative to Google Docs" use case) — Steps 1-2 done (2026-09-05: `precedent-team-tms` bootstrapped, template built); the pilot itself deliberately still not done | [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md) |
| The reusable document-project template a future pilot instantiates from | [templates/nontechnical-document-project/](templates/nontechnical-document-project/) |
| Why each practice is routed the way it is (every glob, and every `**`) | [tools/routing_scope.json](tools/routing_scope.json) |
| The routing audit: coverage check + rotating deep read, on-demand, never a routine gate | [practices/routing-audit.md](practices/routing-audit.md), engine at [tools/routing_audit.py](tools/routing_audit.py) |
| The full practice audit: manual, whole-catalogue sweep across every source, on request only | [practices/full-practice-audit.md](practices/full-practice-audit.md), engine at [tools/full_practice_audit.py](tools/full_practice_audit.py) |
| The very deep check: four ordered passes over every repo in force — adopter installs, whether the mechanisms tell the truth, the coherence read, then catalogue and housekeeping — on request only, distinct from the full practice audit above | [practices/very-deep-check.md](practices/very-deep-check.md), engine at [tools/very_deep_check.py](tools/very_deep_check.py), run record at [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md) |
| Gaps between what the plan approved and what got built (routing audit's own history, and what else to check) | [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) |
| Whether an attached practice-set source's vendored engine has gone stale, and bringing it up to date | [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py) — reports at session start; `--apply` refreshes, `--commit` commits |
| Practices that fire at a moment rather than in a file | [tools/precedent_gate.py](tools/precedent_gate.py) — `merge`, `review`, `push`, `reply` |
| Which practices are enforced, and running one check | [tools/precedent_check.py](tools/precedent_check.py) — `--list`, `--explain`, `--only SLUG` |
| The catalogue's own figures (resident size, Rule share, coverage) | [tools/catalogue_stats.py](tools/catalogue_stats.py) — never hand-type these into prose |
| Precedent explained for someone adopting it (not a developer) | [ADOPTING.md](ADOPTING.md) |
| Public-facing pitch and how-to guides, for people outside the project (marketing, technical how-to, non-technical how-to) | [documentation/](documentation/) |
| The theory this project is built on — the essays, the brainstorm, the rules being tried in real work, and what is still unsettled. **The only copy; argument, not rules that bind anything here** | [philosophy/](philosophy/), start at [philosophy/README.md](philosophy/README.md) |
| Why `philosophy/` binds nothing outside itself, and the checks that hold that line | [local/practices/philosophy-is-not-repo-policy.md](local/practices/philosophy-is-not-repo-policy.md), [local/practices/philosophy-declares-its-source.md](local/practices/philosophy-declares-its-source.md) |
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
| What each person sets on each machine (individual source, leak blocklist, the optional overrides) | [INSTALL.md](INSTALL.md) §8 |
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

- **A git helper that returns stdout and drops the exit code will hand you a
  ref *name* where a commit hash belongs.** `git rev-parse <missing-ref>` exits
  non-zero but *prints the ref you asked for* on stdout, so
  `_git(...'rev-parse', ref) or <fallback>` never falls back: it binds the
  truthy string `origin/precedent-beta-v01` and carries it forward as a hash.
  Reached continuous integration on 2026-09-06 as `precedent-beta-v01 @ origin/prece has no
  tools/build_views.py` — a 12-char truncation of a ref name. Use
  `rev-parse --verify --quiet` (silent, exit 1) whenever a ref may be absent.
  Note the trigger: a *non-repo* prints nothing, so the plain form looks fine
  for years — it only echoes on an **unborn `HEAD`** (a repo with no commits) or
  a missing ref, which is why this survived so long. Audited across
  [tools/precedent_vendor_engine.py](tools/precedent_vendor_engine.py) on
  2026-09-06 and found twice more: `status()` reported a clone that simply has
  no `SOURCE_BRANCH` as *"upstream has moved — run `refresh`"*, a false alarm
  wired to what was then a destructive remedy; and `seed()` recorded
  `source_commit: "HEAD"` into `ENGINE_MANIFEST.json`, after which every later
  comparison read as "moved" forever. A sweep found the same one-liner in
  [tools/routing_audit.py](tools/routing_audit.py), where it was persisting a
  review record at commit `"HEAD"`.
  The same swallowed exit code hid a failing `git checkout` in a dirty tree
  during the very session that fixed this, making a broken negative control
  look like a passing test — so treat "the command reported nothing" as no
  evidence at all.

- **A repository attached mid-session clones single-branch, so every
  branch you create there reads as "unpushed" forever — including to a
  Stop hook that then blocks the turn.** `add_repo` hands you a
  `git clone --depth 1` whose only refspec is
  `+refs/heads/main:refs/remotes/origin/main`. Push a feature branch and
  the push genuinely succeeds, but no `origin/<branch>` ref is ever
  written, so `git rev-list origin/<branch>..HEAD` cannot resolve and every
  freshness check reports the branch as having unpushed commits with no
  remote counterpart. 2026-09-06: this fired on both consumer repos after
  their work was already safely on GitHub, and the honest-looking remedy —
  push again — changes nothing, because the push was never the problem.
  A second trap sits on top of it: `add_repo`'s clone URL is lowercased
  (the owner and repo name lowercased), so GitHub answers with
  `remote: This repository moved`, which reads like the cause and is not.
  Confirm with `git ls-remote origin refs/heads/<branch>` — that talks to
  the server and ignores local refs entirely — then repair the clone rather
  than re-pushing:
  `git config --unset-all remote.origin.fetch`,
  `git config --add remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'`,
  a bounded `git fetch --depth=50 origin <branch>`, and
  `git branch --set-upstream-to=origin/<branch>`. Setting the remote URL to
  the canonical capitalization at the same time stops the misleading
  redirect notice.
  **The refspec half of that repair now applies itself** — 2026-09-06,
  [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh) here and
  [templates/bootstrap.sh](templates/bootstrap.sh) for dependent repos both
  widen `remote.origin.fetch` at session start when it carries no
  `refs/heads/*` mapping, before the freshness block runs. It is local
  config only, idempotent, and announced on stderr rather than done
  silently. Verified against a real `--single-branch` clone: pushing a
  feature branch from one left `git rev-list origin/feature..HEAD` unable
  to resolve at all, and the repair plus one fetch made it answer `0`. The
  clone-URL capitalization half is *not* automated — nothing local knows
  the canonical spelling — so that stays a manual `git remote set-url`.

- **A tool handed a clone as a *source* can still check that clone out from
  under you.** `process/upstream/tools/checkin.py update <bestpractice-clone>`,
  run from a consuming repo, opened with `git checkout <default-branch>` and
  `git pull` **inside the clone you passed it**. On 2026-09-06 that silently
  moved a session's BestPractice checkout off `precedent-beta-v01` onto
  `main`, mid-session — and the command had already FAILED its own guard by
  then, so the mutation was pure collateral. The session noticed only because
  `templates/practice-set-*/` and thirty tools had vanished from a tree it had
  just been working in, and briefly read that as another session having deleted
  real work. `git status` was clean and `git log` looked sane, because nothing
  was damaged: it was simply a different branch. **If files you were just
  using disappear, check `git rev-parse --abbrev-ref HEAD` before concluding
  anything was lost** — and on a dirty tree the checkout would have failed and
  left the pull half-applied instead, which is worse. Fixed forward the same
  day: `update()` now reads the source ref with `git archive` (no checkout, no
  pull, no HEAD movement — the guarantee
  [tools/precedent_vendor_engine.py](tools/precedent_vendor_engine.py) already
  made explicitly), and mirrors the branch the consumer's own
  `process/manifest.json` records rather than the clone's configured default —
  every consumer tracks `precedent-beta-v01` while `main` is still the
  default, so the old code would have mirrored `main` over a beta-vendored
  tree, a wholesale revert dressed as an update. Both properties are asserted
  in [tools/verify_harness.py](tools/verify_harness.py) with negative
  controls.

- **A stale container is indistinguishable from missing work; the freshness
  guard can be the thing that's lying; and the guard cannot save the very
  containers that most need it.** Three incidents, each one level deeper than
  the last. 2026-09-01: a session's local branch shared ZERO commits with
  origin, 51 merged commits invisible. 2026-09-06: a session started on a
  5-day-old shallow clone, 207 commits behind `precedent-beta-v01`, and
  concluded that [tools/precedent_check.py](tools/precedent_check.py) and
  [.github/workflows/deep-check.yml](.github/workflows/deep-check.yml) "did
  not exist" — they had landed days earlier;
  [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh) stayed
  silent because its `git fetch` failed and it then compared the local commit
  against an unrefreshed remote-tracking ref: both were equally old, so
  nothing looked behind. Fixed then to warn when the fetch itself fails.
  **2026-09-06, the one that ended warning as a strategy:** a session came up
  366 commits behind, and the hardened freshness block *did run and could not
  help* — the container's copy of the hook was built 2026-08-31 and predated
  the block by six days. **A guard shipped inside the checkout it guards is
  missing from precisely the containers stale enough to need it.** The
  documentation failed identically: the AGENTS.md that session was handed had
  no gotchas section at all, so every entry here — including this one — was
  invisible to it. Warning was never going to be enough, because by the time
  a session could act on a warning the harness has already handed it a stale
  instructions file. The guard therefore **repairs**: on a clean tree that
  is strictly behind, it fast-forwards and says so, which makes the harness
  re-read the instruction files. Diverged, no-shared-history, and dirty-tree
  states still only warn — a hook that discards work is worse than any stale
  checkout. **That logic lives in
  [.claude/hooks/freshness-guard.sh](.claude/hooks/freshness-guard.sh), and
  only there** — it briefly also sat inline in
  [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh), where the
  two ran back to back at every startup, fetching twice and racing to
  fast-forward the same branch; the inline copy is gone rather than kept in
  sync by hand. The guard is wired three times, because one firing point
  cannot cover the others: `SessionStart` (once, at the start),
  `PreToolUse` (once, before the session's first write) and
  `UserPromptSubmit` (the long-open-tab case — a tab open for hours that has
  already made its first edit is otherwise never rechecked). The
  `UserPromptSubmit` mode is throttled on a stamp file's mtime, so it costs
  ≈17ms and prints nothing inside its interval (default 600s,
  `git config precedent.freshness.intervalSeconds`); nothing polls and
  nothing runs between prompts. Its first version built the stamp path from
  `git rev-parse --git-dir`, which answers *relative* to the repo, so every
  write landed in the wrong directory, the throttle never engaged, and it
  re-checked on every prompt while printing a path error — use
  `--absolute-git-dir` for any path a hook will use from an unknown working
  directory. Two further fixes fell out of testing it: the freshness block was
  gated behind `CLAUDE_CODE_REMOTE=true` along with the `pip install`, so on a
  local machine it **never ran at all** (verified: total silence on all six
  test cases, including a failed fetch); and the old remedy it printed —
  `git checkout -B <branch> origin/<branch>` — was printed for a *diverged*
  branch too, where following it silently discards the local commits, because
  the check never distinguished "behind" from "behind and ahead". Before
  concluding that anything is missing or unfinished, still run
  `git fetch origin <branch>` and `git rev-list --count HEAD..origin/<branch>`
  yourself: the hook does not run for a repo attached mid-session (see the
  `add_repo` entry below).

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

- **A `scope: 'tree'` check in `tools/precedent_check.py` can silently
  report a false *pass* on an under-fetched local clone, not just degrade
  loudly like the two entries above.** `parallel-artifact-ledger` walks
  `git log --no-merges -- <member-dir>` for each harness-adapter directory
  and fails on any commit whose hash isn't in `templates/harness/LEDGER.md`.
  2026-09-05: a local run reported `0 violated`, but GitHub Actions' own
  checkout of the exact same commit reported a real violation (twice) —
  `templates/harness/LEDGER.md` was missing a row for a commit from
  five weeks before the ledger file existed. The local clone's history
  simply didn't reach back far enough for `git log` to find that commit at
  all, so the check had nothing to flag — an empty result read as "clean,"
  not as "couldn't check." `git fetch --depth=1000 origin <branch>` (or
  deeper — this check needs the *entire* history of the directories it
  walks, not just enough for the current branch's own diff) before
  trusting a clean local run of any `scope: 'tree'` check.

- **The leak gate's vocabulary layer fails open unless you also set the git
  config.** `export PRECEDENT_LEAK_BLOCKLIST=<a path OUTSIDE this repo>` is
  half of it; without `git config precedent.requireVocabulary true` a shell
  that starts without the variable prints `PARTIAL`, exits 0, and the push
  goes through with only the structural rules applied. Every push here is
  publication into a public repository, so the half-configured state is the
  dangerous one. See `python3 tools/leak_gate.py --explain`.

- **A session's local checkout can be stale enough to look complete while
  missing real, merged work — with no error.** A session opened here on
  2026-09-01 had a local `precedent-beta-v01` that shared **zero** commits
  with origin's tip: phases 1.5 through 4, every `spec/*.md` brief, and
  `CHANGES_TO_TELL_ALEX.md` simply did not exist locally. `git status`
  reported "up to date with origin" because that check runs against
  whatever the remote-tracking ref happened to be at last fetch, and no
  fetch had happened yet. Reading the tree, running the harness, anything
  short of `git fetch` first would have silently analyzed or built on a
  months-stale snapshot. [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh)
  now fetches the current branch and warns loudly (never fails the
  session — a git failure here must not block startup) if local `HEAD`
  differs from origin's, distinguishing "behind" from "shares no history
  at all" (a force-push or rewrite, the worse case). If you see that
  warning, and your working tree is clean: `git checkout -B <branch>
  origin/<branch>`.

- **On a shallow clone, `git merge-base` between two *different* branches
  can exit 1 ("no common ancestor") even when the branches genuinely share
  history — and that false negative reads exactly like a destructive
  force-push.** On 2026-09-06, comparing `precedent-beta-v01` against an
  older feature branch this way returned exit 1, which looked like proof
  the two had disjoint, independently-rewritten histories; the session
  nearly asked the user to confirm a branch rewrite that had never
  happened. `git merge-base <A> origin/main` and `git merge-base <B>
  origin/main` each resolved fine in the meantime — the shallow fetch
  simply didn't reach far enough back to contain the real common ancestor
  of `<A>` and `<B>` themselves, even though each one individually had a
  shorter path back to `main`. `git merge-base` exiting 1 is not by itself
  evidence of a rewritten or discarded branch: `git fetch --unshallow
  origin` (or a deep enough bounded `git fetch --depth=<N> origin
  <branch>`, per the entries above) and recheck before concluding
  anything about two branches' relationship.

- **Inherited audits that have nothing to inspect say so, rather than
  passing or failing.** [tools/practice_audit.py](tools/practice_audit.py)
  wants a `process/manifest*.json` this repo does not have, because this
  repo is the upstream it audits a *dependent* repo against. It used to
  exit non-zero for that reason — permanently red, so nobody ran it — and
  [tools/doc_sync.py](tools/doc_sync.py) and
  [tools/model_audit.py](tools/model_audit.py), whose `PAIRS` and
  `INSTRUMENTED` lists were then empty, printed `OK` on having inspected
  nothing: a confident all-clear from a scan that never ran. All three now
  say NOT APPLICABLE with the reason, and
  [tools/precedent_check.py](tools/precedent_check.py) reports that as
  skipped rather than passed. (`PAIRS` and `INSTRUMENTED` have both since
  been filled in here — two documents and one script — so only
  `practice_audit.py` is still NOT APPLICABLE in this repo. Corrected
  2026-09-06; the entry had gone on asserting all three were empty.)

- **`git log --format=%P` silently reports no parents at all for a commit
  sitting at a shallow clone's boundary, even when it really has two.** Writing a mechanical check for `precedent-team-maintainers`
  (a `checked_by` script that needed to tell a merge commit apart from an
  ordinary one, to exempt merges from a per-commit rule) used `%P` and
  worked perfectly against a full clone, then silently misclassified the
  exact commit sitting at the shallow boundary as parentless the moment the
  same script ran against a fresh `--depth 1` clone of the same repo —
  reproduced directly, not just suspected. Git's pretty-printers respect
  the shallow graft for traversal purposes even though the commit object's
  own header still genuinely records both parents. `git cat-file -p <sha>`
  reads that header directly and is unaffected — count lines starting with
  `parent ` instead of parsing `%P`, anywhere a check needs to know a
  shallow-clone-safe parent count or parent list.

- **A consuming repo's own mechanical check against materialized
  `tools/checks/`/`practices/` output cannot just call
  `precedent_resolve.load_config()` and trust every source it lists.** A
  repo-local (or team, or individual) source's own check script belongs
  under that source's own declared `path` (`local/tools/checks/` for a
  source declared `path: "local"`), never directly in the consuming
  repo's own `tools/checks/` — that is `precedent_materialize.py`'s own
  *output* directory, deleted and rewritten from every declared source on
  every `precedent_sync_views.py` run, so a hand-added file there
  survives only until the next sync. A dependent repo built exactly this
  mechanical check (verify every materialized `check_*.py` has a
  byte-identical twin in its source) and shipped a first version that
  resolved sources live to decide what counts as reachable — it passed
  locally, then failed the repo's own CI on the very next push, on `main`
  itself, flagging every check script sourced from its team and
  individual sources. A team source is a live sibling clone outside the
  repo; an individual source resolves only via a private, non-repo
  user-level config — neither exists in a bare CI checkout, and never
  will, so "this source didn't resolve here" is not evidence of an
  orphaned file. The fix: attribute by the *committed* `MANIFEST.json`'s
  own `checks` list (already written by `precedent_materialize.py`,
  recording exactly which source produced each file) instead of by live
  resolution — a file with no entry there at all is the real signature of
  a hand-dropped orphan and always fails; a recorded file whose source
  simply is not reachable in the current environment is skipped, never
  failed.

- **A repo attached mid-session never runs its own SessionStart hook, so
  every environment guarantee that hook provides is silently absent while
  you work in it.** SessionStart hooks fire for the session's *primary*
  repo only. A sibling attached with `add_repo` — which is how this repo
  is present whenever a dependent repo's session needs it for a vendor
  refresh or a check-in — is just a directory on disk: its
  [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh) is
  never executed, no matter that it is committed, executable, and correct.
  2026-09-06, working here from a dependent repo's session:
  `python3 tools/verify_harness.py` reported `FAIL: every tool answers
  --help with exit 0 ... doc_html.py exited 1`, and separately
  `N/A: rendered documents are current -- tools/doc_html.py could not be
  imported (No module named 'markdown') -- not a pass`. Both were the same
  missing module, which this repo's own hook installs on line 13 and has
  installed since 2026-09-04 — it simply had not run. The failure reads
  like a broken tool and is an unrun hook, so the reflex to go debug
  `doc_html.py` is wasted. `pip install cmarkgfm markdown` by hand once
  per session you work in an attached sibling, then re-run the gate: the
  harness went from `1 failed` to `0 failed` with no code change at all.
  The same reasoning covers the refspec repair and the freshness warning
  further down that hook — none of them ran either, so treat every entry
  in this section that says "the session-start hook does this" as *not*
  done when you arrived here as a sibling.

- **The three private practice sets cannot be attached from a session
  rooted in this repo, and it is a session-shape rule, not a permissions
  problem — so do not go hunting for the permission.** As of 2026-09-06,
  asked to attach `themorgan/precedent-team-maintainers`,
  `themorgan/precedent-individual` and `themorgan/precedent-team-tms` while
  working in `alex137/BestPractice`, `add_repo` refuses outright:
  *"cross-tier adds are not supported in v1: requested
  themorgan/precedent-team-maintainers but session already has repos from
  owner(s) [alex137]"*. Everything about the surrounding evidence argues the
  other way and is misleading: `list_repos` returns all three, private, with
  `can_push: true` for this account, so access genuinely exists — it is the
  *session's* composition that is refused, not the account's rights. The
  obvious fallback fails too, differently enough to look like a second
  problem: a plain `git ls-remote https://github.com/themorgan/...` answers
  *"could not read Username for 'https://github.com': terminal prompts
  disabled"*, because this session's git credentials cover `alex137/*` only.
  Nothing done from inside such a session closes this. The remedy is a
  session whose **initial source** is the private repo
  ([TODO.md](TODO.md)'s `attach-private-sources` item, which also lists what
  to run once there); BestPractice is public, so that session clones it
  directly with no second `add_repo`. The failure this entry prevents is
  spending the attempt at all: the fact was already recorded in
  [TODO.md](TODO.md), [spec/PHASE6_BRIEF.md](spec/PHASE6_BRIEF.md) and
  [decisions/2026-09-01-relax-private-repo-isolation.md](decisions/2026-09-01-relax-private-repo-isolation.md),
  and a session on 2026-09-06 rediscovered it by trying both calls anyway,
  because this section — the one place written to stop rediscovery — did not
  carry it.
  **NO LONGER TRUE as written, 2026-09-07.** A session that day held
  `alex137/bestpractice` and five `themorgan/*` repositories at once —
  including all three private sets, worked in and pushed to — and `add_repo`
  accepted a sixth (a private consumer repo under the same owner)
  mid-session. Mixed owners
  in one session is precisely what this entry says is refused. What has NOT
  been retested is a *fresh* session rooted here adding a `themorgan/*` repo
  as its first cross-owner add, so the constraint may have been lifted or may
  bind only the first add. Treat the refusal as possible but no longer
  certain: try the call, and believe the answer it gives rather than this
  paragraph. The 2026-09-06 refusal was real and reproduced, so this is the
  environment changing, not the original finding being wrong.

- **A harness run that overlaps a write to the tree fails on a change
  belonging to no commit, and the count alone cannot tell you that.**
  [tools/verify_harness.py](tools/verify_harness.py) reads the tree as it
  goes, over more than a hundred checks and several minutes. On 2026-09-07 a
  run came back `1 failed` because a negative-control test — for a fix being
  made in that same session — had briefly planted a failing check into
  `verify_harness.py` while the run was still in progress. The failure was
  real, reproducible on demand, and belonged to no commit. Two earlier runs
  and four later ones on the identical tree were clean, which is what a
  genuine intermittent looks like too: `1 failed` renders identically
  whether it is self-inflicted, a real flake, or a real bug. Run the harness
  to completion before editing anything it reads, including its own control
  tests, and never run two at once. Since 2026-09-07 the run recaps every
  failure BY NAME immediately before the summary line, so `tail -5` is
  enough to tell these apart — before that it printed only the count, and a
  failure hundreds of lines up was lost the moment anyone re-ran.

- **Setting `git config precedent.requireVocabulary true` to satisfy the leak
  gate makes `verify_harness.py` fail two of its own leak-gate checks.** The
  two gates want opposite environments and neither says so. 2026-09-07,
  running the full deep check before a push: `leak_gate.py` refused with
  *"this clone has declared that it HAS a private-term blocklist ... and
  PRECEDENT_LEAK_BLOCKLIST is not set"*, which the gotcha above tells you to
  fix by setting both. With both set, `verify_harness.py` then reported
  `2 failed` — *"the default blocklist is applied with no environment
  variable set"* and *"a clean tree now reports OK rather than PARTIAL"* —
  because those cases assert the gate's behaviour for a clone that has
  declared nothing. Neither failure is a real defect and neither is caused by
  whatever you are changing, which is exactly why it costs a session an hour.
  Run them in different environments: `python3 tools/leak_gate.py` with
  `PRECEDENT_LEAK_BLOCKLIST` exported, and
  `env -u PRECEDENT_LEAK_BLOCKLIST python3 tools/verify_harness.py` with the
  git config unset. Unset the config when you are done rather than leaving it
  on the clone — a later session running the harness will hit this again with
  no idea why.

- **The individual source resolves to a clone you are probably not editing,
  and it can be many commits stale.** `~/.config/precedent/config.json`
  names an absolute path, and on 2026-09-07 that path was
  `/root/precedent-individual` while every repo this session had attached,
  edited and pushed lived under `/home/user/`. Two clones of the same
  repository, and **everything that resolves the individual source at
  runtime reads the one in the config** — which was 6 commits behind, so it
  did not carry work committed and pushed an hour earlier from the other.
  It cost two separate confusions before the cause was found: a harness
  fixture that failed intermittently because it was reading that clone's
  freshness (not its own), and a SessionStart hook that installed one of the
  two commit hooks it should have, because the script it executed was the
  stale copy. Neither symptom pointed at a path. Check
  `python3 -c "import json,pathlib;print(json.load(open(pathlib.Path('~/.config/precedent/config.json').expanduser()))['individual']['path'])"`
  against where you are actually working, before concluding a tool is
  broken — and `git -C <that path> rev-list --count HEAD..origin/main` before
  trusting anything it produced. **The rule that resolves it, 2026-09-07:
  the config-named clone is `git pull --ff-only`ed from origin at every
  session start, so it can only ever be BEHIND — an attached sibling clone
  beside the repo you are working in is what a session actually edits and
  pushes from, and is the better evidence of what the source says.**
  [tools/verify_harness.py](tools/verify_harness.py)'s
  `check_commit_identity_copies_are_identical` encodes exactly that
  preference; its first run reported drift against an uncommitted edit three
  directories away, which is the trap in miniature. **Do not read the next sentence as
  done everywhere.** A session on 2026-09-07 repointed the config at
  `/home/user/precedent-individual` and recorded that here as "resolved for
  this machine" -- but `~/.config/precedent/config.json` is a per-container
  file that no repository can carry, so a *different* container reading this
  paragraph still had `/root/precedent-individual` in its config, and the
  same paragraph's "nothing reads it now" was false there: everything reads
  exactly it. A fix that lives outside the repository cannot be recorded
  inside the repository as a state; only as a thing to check. **So check
  it**, with the command above, rather than trusting this. The saving grace
  when you find `/root/`: `precedent-individual-bootstrap.sh` pulls that
  clone `--ff-only` at every session start, so it is normally current in
  content even when it is the wrong path -- verified 2026-09-07, both clones
  at the same commit. What it will not have is uncommitted work in progress
  from the attached sibling, which is the case the preference above exists
  for.

- **A sibling clone that was current when you took it can rot while you
  work, and a "these copies do not match" failure will blame the code
  rather than your clone.** The entry above is about a clone that is
  behind when a session *starts*; this is the same trap arriving later,
  and it is the shape that will keep recurring now that several sessions
  routinely work these repositories at the same time. 2026-09-07:
  `verify_harness.py` came back `1 failed` on
  *"every reachable copy of commit-identity.sh is byte-identical (3 copies
  found)"*, listing this repo's two copies in agreement and the copy in
  the attached `precedent-team-maintainers` clone differing. The check was
  correct that the files differed and wrong about what that meant: the
  clone had been taken hours earlier, another session had pushed to that
  repository twice since, and it was **2 commits behind**. A single
  `git -C <clone> pull --ff-only` made all three hashes agree, and the
  re-run was `0 failed` with no change to any file here.
  **So before believing any cross-copy mismatch: refresh every attached
  sibling clone and run it again.** The reason this is worth a rule rather
  than a shrug is the direction the mistake runs — the failure reads as
  "this repo's file is wrong", and the obvious remedy is to copy the
  clone's older version over the newer one, which silently reverts
  somebody else's just-landed work. Confirm which side is stale before
  editing either: `git -C <clone> fetch && git -C <clone> rev-list --count
  HEAD..origin/<branch>` answers it in one line.
  The same reasoning applies to the check itself when it is the new thing:
  this one had landed minutes before it fired, so "a check that has never
  been green here" was also on the table, and ruling that out meant
  running it against the untouched branch tip first. A failure in a check
  younger than your branch is worth locating before it is worth fixing.

- **`HEAD == origin/<branch>` and a clean tree is NOT evidence that your
  work landed — it is the exact reading you get when your commit has been
  thrown away.** 2026-09-07: a session edited `TODO.md` while sitting on
  local `precedent-beta-v01`, committed there, then ran its usual
  push-and-merge sequence — `git push origin <feature-branch>` (which
  reported *"Everything up-to-date"*, correctly, because the feature branch
  had not moved), then
  `git checkout -B precedent-beta-v01 origin/precedent-beta-v01`, which
  **silently discarded the commit it had just made**. Its verification step
  then printed `HEAD=a7e503c beta=a7e503c dirty=0` and read as success:
  every ref matched, nothing was uncommitted, and the change was in neither
  the local tree nor the remote. A concurrent session's own push to the
  same branch made the hashes advance, which made the output look *more*
  convincing, not less.
  Two habits close it. **Commit on the working branch, never on the branch
  you are about to reset** — `git checkout -B` is a reset, and a
  scripted push-then-checkout sequence will run it whether or not you have
  uncommitted history there. And **verify the CONTENT, not the refs**:
  `git show origin/<branch>:<file> | grep <a phrase from your change>`
  answers the question `verify-postcondition` actually asks, where ref
  equality only answers a proxy for it. The first grep written that day
  matched a coincidental phrase already present elsewhere in the file and
  briefly confirmed the wrong thing — so grep for a phrase distinctive to
  your own edit, not a common one.
  Recovery, when it happens: the commit is not gone, it is unreferenced.
  `git reflog` still lists it (`commit: <your message>`), and
  `git cherry-pick <that hash>` onto the working branch restores it.

- **The commit backstop is GLOBAL now (`core.hooksPath`), so it reaches
  throwaway fixture repositories too — and refused them.** 2026-09-07, the
  third wrong-author incident in two days forced the scope up: a repo
  attached mid-session inherits the container's *global* identity (measured:
  `noreply@anthropic.com`), so a per-checkout SessionStart fix cannot cover
  it even in principle. Setting the identity globally, plus a backstop at
  `core.hooksPath`, is what reaches a repository that does not exist yet.
  The cost landed immediately: `verify_harness.py` builds dozens of
  temporary repos and commits in them without `TZ`, and the backstop
  refused the first one — `RuntimeError: git commit -qm base: commit
  refused: author-date offset is '+0000'`, the whole run down, in a
  mechanism that had nothing to do with what was being tested. **A fixture
  commit is not a person's commit**: the harness now sets
  `PRECEDENT_ALLOW_ANY_AUTHOR=1` once for every subprocess it spawns (the
  two checks that exercise the refusals pop it back out, so coverage is
  intact). Any other tool that creates scratch repositories and commits in
  them needs the same, and the symptom will not look like an identity
  problem.
  `core.hooksPath` also makes git look THERE AND NOWHERE ELSE, so the global
  hooks chain to each repository's own `.git/hooks/<name>` first — without
  that, every repo's own gates vanish silently. Resolve that path with
  `rev-parse --absolute-git-dir`, never `rev-parse --git-path hooks`: the
  latter *respects* `core.hooksPath` and so names the global directory,
  which made the chain look broken when it worked and a fixture look
  correct when it was planting its hook in the wrong place.

- **The timezone half of that backstop was refusing a wrong offset it could
  have prevented — the container's clock is the lever, and a hook can move
  it.** 2026-09-08: every commit here needed a `TZ="…" git commit` prefix
  and the merge commits that forgot it were refused, correctly, for
  `+0000`. Three mechanisms existed and every one of them acts *after* git
  has resolved an offset: `pre-commit` refuses, `prepare-commit-msg`
  refuses the merge, and the `.claude/settings.local.json` derivation
  applies only from the NEXT session, because the harness reads environment
  before hooks run. Measured rather than reasoned: `/etc/localtime` was
  `Etc/UTC`, `TZ` was unset in every tool shell (`echo "${TZ:-<unset>}"`),
  and `settings.local.json` already carried the right zone and was inert.
  git falls back to the SYSTEM zone when `TZ` is unset, and the system zone
  is the one lever a hook can move mid-session that every later shell,
  tool, and `git merge` picks up without cooperating — so
  [.claude/hooks/commit-identity.sh](.claude/hooks/commit-identity.sh)
  repoints it, for a **declared** zone only. Verified end to end: a fresh
  `git init` with no prefix and no local config committed at `-0300`.
  `PRECEDENT_LOCALTIME` overrides the target so this is testable — and the
  older `check_commit_identity_derives_declared_timezone` fixture, which
  declares Europe/Berlin, now sets it too; without that the harness itself
  would have put the container on Berlin time and every later commit in the
  session would have been refused for an offset the harness caused.
  **If you suspect a timezone problem, check `date` and
  `ls -l .git/hooks/pre-commit`, not the `env` block** — that block is
  inert here and reading it sent two earlier diagnoses down the wrong path.

- **"no individual source resolved" is not noise — it means every personal
  and team practice is silently absent, and the session will confidently
  apply the wrong rules.** 2026-09-07: a session ran most of a long working
  day in this repository with none of the account owner's personal
  practices loaded.
  `tools/precedent_resolve.py` printed the reason on *every single run* —
  *"no individual source resolved … which usually means its clone could
  not be fetched (a private repository this session was never granted)"* —
  and the session read past it every time as startup chatter, because the
  checks it prefixes all reported `0 violated` and the line sits directly
  above the summary a session is reading the output *for*. (The counts in
  an earlier draft of this entry -- "twenty turns", "fifteen times" --
  were impressions written as figures and neither was counted; the
  frequency is *every run*, which is the part that matters and the part
  that is checkable.)
  The cost is invisible while it is happening, which is what makes it
  worth an entry: the practices that did not load included
  `audience-register`, the owner's standing rule about how replies to him
  are written, so every reply that session was pitched by guesswork while
  a rule saying exactly what to do sat unread in a repository nobody had
  fetched. He had asked for that register repeatedly across days, and the
  session's own diagnosis each time was "I keep forgetting" — a
  misdiagnosis, since the rule was never in front of it.
  **When you see that line, stop and fix it before doing anything that
  depends on the rules:** call `add_repo` for the private sources (the
  banner at the top of this file), then re-run
  `python3 tools/precedent_resolve.py --repo .` and confirm the count says
  `individual` and `team` rather than universal alone. A single-digit
  source count where you expected four is the same signal in a different
  shape.

- **A private repo name reaches a public tree by nobody having predicted
  it, so repo references are an ALLOWLIST now, not a blocklist.** The
  vocabulary layer blocks the literal strings somebody typed, which failed in
  both directions on 2026-09-07: it missed a private repository nobody had
  listed, and it blocked two names that had become public, forcing 88 hits
  clearable only by deleting content about public files. Declare an owner
  private-by-default in the private blocklist file
  (`# visibility-audit: private-owner <account> -- reason`) and every
  `owner/name` mention is refused unless an `allow` line gives a reason. It
  caught an abandoned private fork on its first run, plus its own manual's
  example, which had used a real account name. The set of names you may
  mention is small and known; the set of repos you might create is unbounded.
  **The URL form is the case that matters and is easy to miss**: the
  lookbehind keeping `a/acct/x` from matching also rejects
  `github.com/acct/x`, because the character before the owner is `/` there
  too — a stated test case caught that, reading it did not.
  [tools/very_deep_check.py](tools/very_deep_check.py) does the other half on
  request, asking the GitHub API whether each referenced repo is actually
  private and whether a blocklisted name has since gone public; the push gate
  cannot, because it must work offline and in continuous integration (CI).
  Its reach is limited to repos the session can see — `/user/repos` answers
  *"sessions are bound to their configured repositories"* — so it reports how
  many it could NOT determine rather than counting those as passes.

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
- **Two check levels** (practice `two-check-levels`): **light check** is
  `python3 tools/doc_lint.py` on the markdown you touched — the fast,
  constant pass above, run before every commit without thinking about it.
  **deep check** is the full gate suite run before push or merge:
  `python3 tools/verify_harness.py`, `python3 tools/doc_lint.py`,
  `python3 tools/leak_gate.py`, `python3 tools/precedent_check.py`, and
  `python3 tools/doc_sync.py`. **What matters is `0 failed` and
  `0 violated`, never a passed/skipped count** — those grow as checks are
  added, so a figure written down here goes stale by design; see
  [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md)'s closing section,
  which says the same thing and records the audit that found a hardcoded
  one already wrong. Light check gates a commit; deep check gates a push.

## Conventions (every session, every reply)

- **Reply convention** ([reply-links-files](practices/reply-links-files.md)):
  every reply that created, modified or deleted
  files ends with a **"Files touched"** list — for each file, the branch
  link (readable now) plus the post-merge `main` link, with a one-line
  description. The reader opens the work from the chat; they never go
  hunting for it. **A deleted file is listed too** — its path, why it went,
  and a link to the commit that removed it; a whole retired directory is one
  entry, not one line per file. A touched HTML render or picture also gets
  its rendered-view (artifact) link when the harness offers one — a repo
  link shows source, not the render.
- **Doc references are links** ([doc-references-are-links](practices/doc-references-are-links.md)):
  relative markdown links,
  never bare backticked filenames. Use `≈`, not `~`, for "approximately".
- **Volatile rules carry their dates** ([volatile-rules-carry-dates](practices/volatile-rules-carry-dates.md)):
  anything asserted
  here about an external platform or tool carries *as of / verified
  `<date>`* inline, in the contributor's local calendar date, not the
  agent's system clock.
- **Outward-facing documents use the reader's words** ([readers-vocabulary](practices/readers-vocabulary.md)): this
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

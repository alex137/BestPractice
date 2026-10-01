# Repository notes for agents

<!-- These are the instructions for sessions working ON the BestPractice
     repo itself (the upstream). Inside a dependent repo's vendored copy
     (process/upstream/AGENTS.md) this file is inert — the dependent repo
     has its own instantiated AGENTS.md at ITS root. -->

**Read before opening or merging any pull request (PR) here: every PR
targets your landing branch, never `main`** -- `pre-staging` for a person
whose landing branch is pre-staging, `staging` otherwise
(`python3 tools/precedent_branches.py --landing` says which). Work reaches
`main` only by a Promote (and reaches `staging` that way too, for anyone who
lands on `pre-staging`). **No merge needs Alex's
sign-off, `main` included** (Alex, relayed by Morgan, 2026-09-26) -- once its
deep check passes, a session may merge a PR into the landing branch. A
general "PR and merge it" authorization, with no branch named, means the
landing branch; merging into `main` needs the person running the session to
name `main` in that specific request, or a Promote that chooses staging into
`main`. Check the base branch explicitly before acting -- do not assume
`main` because it is the repository's configured default branch. The rule and
its story:
[local/practices/merge-target-is-beta-branch.md](local/practices/merge-target-is-beta-branch.md).

**Precedent commands.** A session recognizes each by what the message is
asking for, not by a keyword; the phrase removes doubt, it does not create a
requirement. Where a command authorizes something hard to reverse (a push,
a merge, a mark of how convinced he was) and the reading is a genuine
judgment call, say the read out loud and confirm first. A full practice
audit, a very deep check and the fleet sweep (`Chief of Staff`) are kept to
the literal ask, because what they trigger is expensive. **Each line below
is an index entry: load the practice (`python3 tools/precedent_show.py
SLUG`) before acting on one**, and the long form each used to carry here is
in [spec/AGENTS_COMMANDS_IN_FULL.md](spec/AGENTS_COMMANDS_IN_FULL.md).

- **"Booked"** / **"Approved"** / **"Book it"** ([go-update](practices/go-update.md)) —
  land it on the landing branch: a direct push by default, the full pull
  request chain for a high-risk change, and confirm `origin` carries it.
  "Go update", its older name, still means this.
- **"Promote N"** and the stage words ([promote](practices/promote.md)) —
  the five stages: Consider, Act, Booked, Debut, Produce.
  Read each back before it runs; optional, unless a person's own set
  requires it.
- **"Drop it"** ([park-it](practices/park-it.md)) — write
  `**Disposition:** parked (<date>, <who said it>)` into the item now, and
  never raise it again; kept to the literal word.
- **"Three Things"** ([three-things](practices/three-things.md)) — the three
  things he needs to know now, a bolded phrase and two sentences each,
  nothing else.
- **"Simple please"** ([plain-words](practices/plain-words.md)) — say it the
  way you would out loud, for the rest of the conversation, same substance.
- **"Weak yes"** ([weak-yes](practices/weak-yes.md)) — go ahead and record
  `strength: assented`; an unmarked approval means unknown, and a bare "ok"
  to your own proposal is `assented`
  ([decision-strength](practices/decision-strength.md)).
- **"Prompt Please"** ([prompt-please](practices/prompt-please.md)) — one
  paste-ready block for a new session, never a session-creating tool; no
  merge authorization unless he gave one for this handoff.
- **"Root issues"** / **"Root fixes"** ([root-issues](practices/root-issues.md))
  — every bug, issue or warning this session hit whose cause lives in
  Precedent or a precedent-* repo, each as a Prompt Please block.
- **"My options"** ([my-options](practices/my-options.md)) — every real
  choice in plain words, costs said flatly, then your pick and why.
- **"Vocabulary"** ([vocabulary](practices/vocabulary.md)) — read the list
  from `python3 tools/precedent_vocabulary.py`, never recall it.
- **"Update Vendors"** ([vendor-update-runbook](practices/vendor-update-runbook.md))
  — `python3 ../BestPractice/tools/precedent_update.py --repo .` from the
  consuming repo; it carries the merge too.

The three dispositions an open item can carry are
[open-item-disposition](practices/open-item-disposition.md)'s; it reaches a
session through `precedent_paths.py` on any todo file and through the `reply`
gate.

**An authorization to merge, in whatever words it arrives, means the
landing branch** per the paragraph above, and is not done until a fetch
confirms the pushed content is actually there
([verify-postcondition](practices/verify-postcondition.md)). How a merge
authorization's absence was settled (2026-09-07 to 2026-09-16) is in
[todo/todo-2026-09-07-push-without-the-keyword.md](todo/todo-2026-09-07-push-without-the-keyword.md).

**Session setup.** The private sources normally arrive by the
SessionStart hook when the environment carries `PRECEDENT_GIT_TOKEN` and
`PRECEDENT_SOURCE_BASE_URL`
([PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md)); when it does
not, `add_repo` (read access) for `precedent-individual` and each declared
shared set, silently, and attach the individual source, never clone it by hand
([attach-never-clone-individual](practices/attach-never-clone-individual.md)).
**Then run [tools/precedent_session_check.py](tools/precedent_session_check.py)**
before trusting any "the hook does this" claim, and read a failing row's own
remedy before `--apply`. A session rooted above the repos it works in runs
none of their hooks
([gotcha-2026-09-25](gotchas/gotcha-2026-09-25-a-session-rooted-above-every-repo-it-touches-gets-hooks-and.md));
`python3 tools/precedent_run_session_hooks.py` runs their SessionStart
hooks by hand.
The long form, with its history, is in
[spec/AGENTS_COMMANDS_IN_FULL.md](spec/AGENTS_COMMANDS_IN_FULL.md#session-setup).

**This repo is Precedent**, restructured from BestPractice by the plan of
record [spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md) (phases
0-7, merged into `main` 2026-09-14) — read it to learn why a mechanism
exists, not before every task.
[spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) documents the
practice-file format; [spec/LOADER.md](spec/LOADER.md) the loader.

<!-- BEGIN GENERATED: precedent-loader -->

<!-- Regenerate with: python3 tools/build_views.py -- do not hand-edit this block; `python3 tools/build_views.py --check` exits non-zero on drift. Source: practices/ -- edit the practice file, never this block. -->

## Resident block (~915 of 2000 token budget, 10 of 167 practices (10 universal))

**bold-key-phrases.** People don't read; they skim, and bolding makes skimming easy. Bold the key phrases in a document by default, without being asked, scaling with length -- a long paragraph or document is where a skimmer most needs a spine to follow, a short note usually needs little or none.

**brainstorm-holds-commits.** When a conversation is a **Brainstorm** -- the person says the word, or the
thread is plainly exploratory ("I'm wondering", "what are my options", "do
you have ideas") -- **write nothing to the repository and commit nothing
until they say to.** Research, read, argue the case, propose the design; do
not create, edit, commit, push, open a pull request, or merge. **The edit is
the thing to hold, not just the commit.**

It ends only when the person authorizes the work. Their answering a question
inside it is not authorization, and neither is their enthusiasm for the
idea. **When in doubt, it is a brainstorm.**

**current-rule-governs.** **A standing command means what the rule in force says today, and you do
it.** Resolve the command to its active practice
(`precedent_show.py SLUG` follows a deduplicated copy to the live one) and
carry it out. **Superseded, deduplicated and retired entries, `## Story`
sections, old deferrals and past decisions are history.** Read them to
investigate a failure, or to back a proposal to reconsider a rule. Never
read them to decide whether to do what was just asked.

**Do it first, and propose reconsidering after**, in the same reply if you
want to. **Never decline silently:** if you are not doing what was asked,
the first line of the reply says so, and why.

**When obeying a rule to the letter would leave something broken or wrong,
ask, with your pick.** Never comply silently and never override silently.

**environment-gotchas.** Every expensive environment discovery (a package that must be installed, a
tool that silently doesn't work, a path that does work) is written down
**with the story of what failed and why, not just the fix**, in its own
file — one trap, one file, forever — under `gotchas/gotcha-<date>-<slug>.md`
(directory and frontmatter shape:
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
Part 2).

**None of that catalogue loads into the instructions file, at any size** —
not the stories, and not even a one-line-per-trap index. The file carries a
pointer instead: hit an unexplained failure, grep `gotchas/` before
concluding it's new.

**no-invented-specifics.** Being concrete makes writing better, and **it never licenses invention.** Do
not manufacture a statistic, a date, a name, a version number or a citation
because the sentence would be stronger with one, and do not invent
first-person experience that did not happen.

Without the real figure, **write around it** — *"most of them"*, *"a
handful"*, *"it went up"* — or say plainly that it is unknown. **A vague
true sentence beats a specific false one, every time.**

**orientation-map.** A top-level `MAP.md` indexes the repo: what the key deliverables
are, where everything lives, and — crucially — which supporting documents back
each part of each deliverable. Every session reads it before doing anything.

**quick-index.** The project instructions file carries a "check here BEFORE searching
the repo" table: *looking for X → go to Y*, one row per thing sessions
actually hunt for.

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
When a .github/workflows file is added, edited, or found in an update or migration:
  ci-workflow-approved — no new workflow or CI minutes without the person's words; a fix is maintenance
When a branch has done its job, or a person says to delete branches:
  never-delete-a-remote-branch — never delete a remote branch; hand over the one-click link
When a computation books a transfer between two parties:
  name-both-sides-of-ledger — name both sides; check what is charged against what is received
When a document replaces or is replaced by an earlier one:
  index-remembers-past — put the lineage in the index, not in either document
When a judgment call is needed to keep work moving:
  small-calls — make small calls yourself; note them; stop only for big ones
When a message says "Archive" or "Archive?", or asks whether the session can be archived:
  archive-status-check — check pending; archive if clear, else say what isn't
When a message says "Booked", "Approved", "Book it" or "Promote 3", or plainly authorizes a merge:
  go-update — "Booked" (stage 3; also "Approved"): push; high-risk: PR and merge
When a message says "Promote" or "Promote N", or asks to move work up a tier:
  promote — pre-staging->staging or staging->main, chosen from the work; says which
When a message says "Update Vendors", or an upstream update is taken into a vendoring repo:
  vendor-update-runbook — source clone first, both layers move separately, then merge
When a model or comparison rests on an operating constant nobody decided:
  constants-are-risk-inputs — an undecided constant is a swept, registered input, never doctrine
When a person asks "What's new?", or what has changed in the project lately:
  whats-new — write any missing daily entries first, then link the log and show the newest
When a person explicitly asks for a "very deep check":
  very-deep-check — read every repo in force against itself, pass by pass; never routine
When a person explicitly asks for a full practice audit:
  full-practice-audit — every source's catalogue, one practice at a time; on request only
When a person says "Act" or "Promote 2", or asks to start building after a plan:
  act — stage 2: build it on the session's feature branch, pushed so it survives
When a person says "Chief of Staff":
  chief-of-staff — on request only; name the window read, link each session; Promotion Reviews last
When a person says "Consider" or "Promote 1", or asks to plan before building:
  consider — stage 1: pick the plan size -- one line, Brainstorm, Plan it, Write it up
When a person says "Debut" or "Promote 4":
  debut — stage 4: Promote pre-staging into staging, full checks
When a person says "Drop it" about an open item or a question:
  park-it — mark the item `parked` now; never raise it unprompted again
When a person says "My options", or asks to see a decision's options or hand them off:
  my-options — every option, plainer, your pick -- or a paste-ready handoff
When a person says "Produce", "Make live" or "Promote 5":
  produce — stage 5: Promote staging into main (production); read strictly
When a person says "Reduction pass", or an always-loaded surface is near its ceiling:
  reduction-pass — work the menu in order; move, never delete; report what moved
When a person says "Root issues" or "Root fixes", or asks what this session found that should go back to Precedent:
  root-issues — what this session hit that belongs upstream, each as a Prompt Please
When a person says "Simple please", or asks to be talked to that way:
  plain-words — say it as you would out loud; same substance
When a person says "Three Things", or plainly asks for this shape of answer:
  three-things — the three that matter now, one bold phrase and two lines each
When a person says "Todo reminder", or asks to be reminded of something:
  todo-reminder — write it with disposition ask and remind_on; never a trigger
When a person says "Vocabulary", or asks what the standing commands are:
  vocabulary — list every command in force; read it, never recall it
When a person says "Weak yes", or agrees without conviction:
  weak-yes — do it, and record the approval as `assented`
When a person says "Write it up", or asks for a write-up:
  write-it-up — "Write it up": commit a full report of issue and fix, then link it
When a second implementation of the same mechanism turns up, or a full practice audit runs:
  judgment-check-or-tool — judgment stays prose; checkable gets an audit; a mechanism gets one tool
When a tool, hook, check or gate flags something the person would otherwise have to judge:
  verdict-not-mechanism — judge what a tool flagged; give the person a verdict and why, never its name
When about to search a repo, or use a GitHub tool for what the clone holds:
  grep-before-search — grep the clone first; list before search; fewer windows at once
When about to search or scan every clone, every repo or every file for something:
  wide-search-needs-asking — never sweep every clone unasked; fix the known source, ask for an example
When adding a file beside others of its kind:
  filename-separator — one word separator per directory and kind; never both - and _
When an unattended job hits something blocking its normal work, or something optional it cannot reach:
  automation-issues — a blocked job files or updates an issue; skip an optional input, never silently
When asked to include an image, logo or other binary asset the person supplies:
  attach-the-original — attach the file itself; recreating it from a description is invention
When attaching a practice source with the repo-attach tool, or its reply says to clone:
  attach-never-clone-individual — attach the individual source; keep one clone, both paths; shared sources beside
When being asked for something another window or session of the person's may already be working on:
  dont-race-another-window — say so and decline; send them to the window already on it
When building a mechanism that makes something discoverable or reachable:
  affordance-is-shared — name who else it now serves
When building a permutation or configuration-sweep table:
  permutation-frontier-column — one full table with a computed Frontier column
When building a variant of an existing thing:
  variant-re-derives — re-derive what a variant inherits; limits bind, choices do not
When checking whether practices that should have fired for recent work did:
  routing-audit — run the mechanical coverage check now; roll the deep-read slice forward
When committing a shipped practice, hook, template or engine file, before push or merge:
  vendor-rollout-disclosed — say whether shipped content must reach consumers, if it will, how it migrates
When committing anything:
  session-trailer — a Session: <url> trailer on every commit
When committing anything that touches the vendored/public tree:
  scrub-gate — the public tree stays public-safe always, not just at check-in
When comparing an option against a baseline:
  check-source-architecture — check both options exist in the source before costing them
When creating, renaming or retagging a session:
  session-spend-follows-the-task — pick the model for the job -- reading runs small, judgment doesn't
  session-tags — tag at creation: subject, repo, role, wants; never retrofitted
  session-title-names-the-difference — title by the differentiator; never the task alone, never an open sibling's title
When deciding whether to build or buy a component:
  build-buy-decompose — decompose first; one verdict per part, on ownership grounds
When decommissioning a mechanism that leaves files with no remaining job:
  decommission-deletes-files — delete what it owned; audit first, never on a hunch
When drafting or reviewing prose meant to persuade or be judged:
  push-back — argue a real counter-case before building on a stated stance
When finishing substantial work, before the merge capture gate:
  second-pass-capture — a separate capture pass after the work, not inside it
When fixing anything -- a bug, a stale or copied file, a broken environment -- or adding a check or exemption:
  upstream-fix — fix the cause where it lives, and the origin and copies; name a band-aid
When handing work or advice to the person or a fresh session, or work needs a repo this session cannot reach:
  prompt-please — "Prompt Please" -- recommendation or unreachable work, one paste-ready prompt
When memoizing a heavy solve, or finding a fresh session re-running one another session already ran:
  shared-result-cache — share code-keyed memos on a cache branch; a peer waits on a leased solve
When merging a branch:
  capture-gate — capture follow-on work in the thread that created the need
When migrating a repo onto Precedent from an old system:
  migration-scrubs-vocabulary — scrub the old vocabulary in the same session, unasked
When naming a new file:
  no-version-suffix — name a file for what it is; the repository is the version
When naming or scoping something around a person's skill level:
  technical-describes-people — a skill level describes a person, never a project, repo or file
When naming what "run the checks" means in a repo:
  two-check-levels — name a fast check and a full check; say which gates what
When opening or merging a pull request in this repository:
  merge-target-is-beta-branch — PRs target pre-staging or staging; main moves only by a Promote or when the person names main
When printing a number compared across rows:
  one-formatter-per-quantity — one formatter per quantity kind, declared in one module
When publishing a sortable multi-column table:
  tabular-shared-renderer — ship a sortable render from the one shared renderer
When quoting or compressing someone else's figures:
  quote-discipline — compression rounds against you; qualifiers travel with the figure
When renaming, moving or deleting a file others may link to, or renaming or retiring a name:
  rename-updates-links — repoint every link, and every use of a retired name, in the same commit
When reporting a computed total or a negative feasibility result:
  verify-decomposition — check the parts, not the total; never assert an impossibility
When reviewing code that decides what is skipped, cached, held or refused:
  review-against-a-contract — give each reviewer a one-line contract; a finding counts once reproduced
When seeding or scheduling a prompt into another session:
  seeded-prompt-names-its-origin — it opens by naming the session that sent it
When setting up a project a session works in, or a session reporting that its checkout is behind:
  fresh-before-write — verify and fast-forward the checkout before the first write, never after
When starting an outward-facing deliverable:
  frame-from-audience-question — build it around the audience's question, not your material
When starting slow, costly or external work another session could also start:
  lease-in-flight-work — lease work in flight on a branch; the starting tool checks the board first
When starting work another session may have done, or opening a PR:
  base-branch-is-the-record — read the base branch before starting and before the PR
When starting work the repository may already cover:
  search-by-purpose — search by purpose and by mechanism before concluding nothing exists
When tracking state several documents must agree on:
  registry-source-of-truth — state lives in one machine-readable registry; documents derive
When work touches an open item's subject, or a branch merges:
  item-closes-on-its-condition — record findings in the item; close only on its condition
When writing a hook, script, or practice-file rule in this repository that a dependent repo will vendor or install:
  vendor-neutral-by-default — this repo ships out whole -- default new code and rules to provider-neutral
When writing a rule that depends on the outside world:
  volatile-rules-carry-dates — it carries its date, inline
When writing a script whose numbers a document will cite:
  scripts-assert-properties — scripts assert their own properties and their cited anchors
When writing an outward-facing summary of claims:
  outward-summary-discipline — claims-to-source table, honest sums, a recorded adversarial pass
When writing or changing anything that automatically repairs a state it found wrong:
  repair-cannot-discard-work — an auto-repair must never discard work; reporting is not repairing
When writing or running a drift gate or an audit that re-runs scripts to compare their output:
  gate-ledger — record code, reads and result per unit; skip a unit whose fact holds
When writing or running a gate that chains several checks or runs work concurrently:
  gates-fail-fast — cheap checks first; a failure skips the slow ones and stops the work beside it
When writing or running a gate, audit or solve over a minute:
  slow-steps-report-and-cache — print elapsed and remaining; cache a heavy solve to disk
When writing or triaging an open item:
  todo-is-a-handoff — queue only for a stated blocked-on/out-of-scope reason; else just do it

(More on-demand practices are not listed here: one whose applies_to names real paths, or which declares a gate, is reached by those channels instead -- `precedent_paths.py FILE` and `precedent_gate.py MOMENT`. A trigger a PERSON SAYS cannot be reached that way and is always listed above. `precedent_show.py --index-omitted` names the omitted ones.)
```

## Standing instruction

Before starting work of a kind named in the occasion index above, run `python3 tools/precedent_show.py SLUG` for each listed slug to load its Rule. When editing a file, `python3 tools/precedent_paths.py FILE` prints any on-demand practice whose `applies_to` matches it, without needing the index at all. At a named moment — merging a branch, reviewing work, before pushing, ending a turn and writing the reply — run `python3 tools/precedent_gate.py merge|review|push|reply`: some practices fire at a moment rather than in a file, and no path glob reaches those. If `.precedent/SESSION_PRACTICES.md` exists, read it too: it carries the practices in force from the other sources this repo declares, which are NOT in this block and bind work here exactly as these do. It is regenerated at session start and is deliberately untracked — never commit it or quote it into a pull request.

<!-- END GENERATED -->

---

**Orientation: read [MAP.md](MAP.md) first**; [README.md](README.md) is
the pitch for people. This repo is
BestPractice itself — the upstream practice layer that dependent repos
vendor. Practices you follow here are the ones this repo teaches; a session
that skips them in this repo of all places is the joke writing itself.

## Where things are (quick index — check here BEFORE searching)

**The dozen rows sessions reach for constantly are below. The full
index is [WHERE_THINGS_ARE.md](WHERE_THINGS_ARE.md)** — check it
before searching the repo, and add new rows there rather than here.

| Looking for… | Go to |
|---|---|
| The plan Precedent was built from (phases 0-7) | [spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md) |
| Whether an open item may be raised with Morgan at all, and what "Drop it" writes | [practices/open-item-disposition.md](practices/open-item-disposition.md), phrase at [practices/park-it.md](practices/park-it.md) |
| What a session pays before its first turn, the declared ceiling on each always-loaded file, and how to reduce one without deleting what still bites | [practices/session-load-budget.md](practices/session-load-budget.md), registry at [tools/session_load_budgets.json](tools/session_load_budgets.json) — `python3 tools/precedent_check.py --only session-load-budget` |
| Practices that fire at a moment rather than in a file | [tools/precedent_gate.py](tools/precedent_gate.py) — `merge`, `review`, `push`, `reply` |
| Why the closing **Boildown** section of a reply is not optional, and what refuses a turn without one | [tools/precedent_reply_check.py](tools/precedent_reply_check.py) — `--explain` says what is declared here; the same requirements are printed at the start of every turn by [tools/precedent_gate.py](tools/precedent_gate.py)'s reply gate |
| Which practices are enforced, and running one check | [tools/precedent_check.py](tools/precedent_check.py) — `--list`, `--explain`, `--only SLUG` |
| Which practice libraries are in force in this repo | [precedent.json](precedent.json) |
| What each practice is and why — **the live catalogue** | [practices/](practices/), indexed by [MAP.md](MAP.md); one rule at a time with `python3 tools/precedent_show.py SLUG` |
| Repo map, generated (phase 2) | [MAP.md](MAP.md) — regenerate with [`tools/build_views.py`](tools/build_views.py), never hand-edit |
| Install / update / check-in playbook (dependent repos) | [INSTALL.md](INSTALL.md) — the assistant-facing runbook; the person-facing routes are [SETUP.md](SETUP.md) (guided, non-technical) and [documentation/FOR_DEVELOPERS.md](documentation/FOR_DEVELOPERS.md) (short form plus what actually bites) |
| Upstream open items / roadmap | [todo/TODO.md](todo/TODO.md) (open) and [todo/CLOSED.md](todo/CLOSED.md); one file per item under [todo/](todo/). [`TODO.md`](TODO.md) at the root is a redirect stub and a pull request touching it is refused by the deep check. |
| The full story behind any environment trap, and the generated overview of all of them | [gotchas/](gotchas/), [gotchas/INDEX.md](gotchas/INDEX.md) |
| Anything else — the full index | [WHERE_THINGS_ARE.md](WHERE_THINGS_ARE.md) |


## Build-environment gotchas — search before you rediscover one

Environment and tooling traps are catalogued, one file per trap, under
[gotchas/](gotchas/) — each with its own Symptom, Story and Fix (practice:
[environment-gotchas](practices/environment-gotchas.md)). Nothing here loads
that catalogue for you: **hit a confusing, hard-to-explain failure? Before
concluding it's new, grep for it** —
`grep -ril '<a keyword from what you are seeing>' gotchas/` — rather than
spending an hour on the wrong hypothesis (practice: `grep-before-search`).

A generated overview — symptom plus link, one line per live trap — is at
[gotchas/INDEX.md](gotchas/INDEX.md) for the deliberate read: browsing the
whole catalogue during a `very-deep-check` sweep, or when a grep comes up
empty and a wider look is warranted. It is not `@`-included here and nothing
loads it automatically, which is the whole point of this split.

**Adding one?** Write it as `gotchas/gotcha-<date>-<slug>.md`
([spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](spec/OPEN_ITEM_AND_GOTCHA_PLAN.md) Part
2), then regenerate the overview: `python3 tools/build_gotcha_index.py`. A
trap that can no longer fire gets `status: retired` in its own file, in
place — nothing is ever deleted, and nothing moves.

## Working in this repo

- **Not running under Claude Code (Codex, Gemini CLI, or another agent)?
  Run `bash tools/bootstrap.sh` at session start.** Claude Code gets this
  automatically from its SessionStart hook; every other harness only gets
  it if the agent actually runs it, per
  [templates/harness/README.md](templates/harness/README.md)'s adapter
  table — [GEMINI.md](GEMINI.md) at the root already says so for Gemini
  CLI, and [templates/harness/codex/README.md](templates/harness/codex/README.md)
  covers Codex.
- **Work lands on your landing branch, never `main`** (the opening
  paragraph; `python3 tools/precedent_branches.py --landing`). Booked (`Go update`)
  decides whether that is a direct push or a pull request.
- **Some changes arrive as check-in PRs from dependent repos** (INSTALL.md
  §4). Reviewing one, you are the **second scrub line**: the contributing
  repo's blocklist caught its known private vocabulary; you catch what it
  didn't know yet. A name, number, or incident detail that reads
  subject-specific rather than generic should be challenged before merge —
  and added to the contributor's blocklist, not fixed up here after
  publication.
- **Direct edits are fine** for content about this repo itself (README,
  practice wording, engine code); abstracted lessons still only enter via
  a scrubbed check-in from where they were learned.
- **A pull request touching [`TODO.md`](TODO.md) after the 2026-09-16 todo/gotcha
  migration is refused by the deep check** (`precedent_check.py --only
  todo-gotcha-stale-reference`). File the item under `todo/` instead
  ([spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)).
- **Before committing:** `python3 tools/doc_lint.py` on markdown you
  touched (`pip install cmarkgfm` — the session-start hook does this);
  after touching the deck engine, rebuild the sample both ways:
  `python3 deck/build_deck.py deck/sample` and `--send`.
- **Two check levels** ([two-check-levels](practices/two-check-levels.md)):
  **light check** is `python3 tools/doc_lint.py` on the markdown you touched,
  before every commit; **deep check** is `python3 tools/precedent_push_check.py`,
  before push or merge. What matters is `0 failed` and `0 violated`. Which
  one a push gets, `--as-ci`, and failing tests a source shipped:
  [spec/AGENTS_COMMANDS_IN_FULL.md](spec/AGENTS_COMMANDS_IN_FULL.md#two-check-levels).

## Conventions (every session, every reply)

The loader carries three more in full — `doc-references-are-links` through
`precedent_paths.py` on any Markdown file, `volatile-rules-carry-dates` in
the occasion index above, and
`reply-links-files` through the `reply` gate
([tools/precedent_gate.py](tools/precedent_gate.py)) since it was demoted out
of the resident block on 2026-09-21 — so they are not repeated here.

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

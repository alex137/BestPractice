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

**Precedent commands.** Each of these is a phrase in his message that means a
fixed thing, and each is a universal practice: the trigger and the meaning are
here, and the rule, the argument and the story of its coining are in the
practice file — `python3 tools/precedent_show.py SLUG` for any of them.

- **"Go merge"**, and **"Approved"** ([go-merge](practices/go-merge.md)) —
  sync, say which branch out loud, commit, push, open the pull request, merge,
  **without asking again.** A step this session cannot perform hands off
  rather than coming back as a question: the authorization travels with the
  work. One rule, two triggers — and `Approved` is also an ordinary
  adjective, so *"the approved plan of record"* is not the command.
- **"Park it"** ([park-it](practices/park-it.md)) — write
  `**Disposition:** parked (<date>, <who said it>)` into the item meant, in
  that same turn, say which item was marked, and **never raise it unprompted
  again** — not this session, and not a later one that decides it has become
  urgent. Nobody owes an explanation for parking something: do it, and never
  ask a follow-up about it.
- **"Three Things"** ([three-things](practices/three-things.md)) — the three
  most important things he needs to know now, each a bolded phrase and at most
  two sentences, and nothing around them: no preamble, no fourth item, no
  closing offer. It asks for **attention rather than action**: an answer
  assembled from what is already in context is the failure it prevents.
- **"Plain words"** ([plain-words](practices/plain-words.md)) — the same
  answer said the way you would say it out loud: short sentences, the concrete
  case before the general principle, no hedging. **It governs the rest of the
  conversation, not just the next reply**, and nothing about the substance
  changes — a plainer reply that quietly says less has failed it.
- **"Weak yes"** ([weak-yes](practices/weak-yes.md)) — go ahead, and record
  that he was not convinced: `strength: assented`, written into whatever the
  approval is being recorded in, that same turn. **Not an invitation to talk
  him into it.**
- **"Spawn session"** ([spawn-session](practices/spawn-session.md)) — before
  starting what he just asked for, check whether it belongs in a different
  session, repositories first; then **wake a live session** that already holds
  the context, or, where none fits, hand him a link to a new one, rooted in
  the right repository and already seeded with the prompt. **Waking beats
  spawning**: a spawned session re-reads its repository from nothing. The
  check runs whether or not he says the phrase, and an
  honest "this session is the right one" answers it. **The
  prompt you seed carries the merge authorization**, bounded to the seeded
  work, that repository's routine branch and its own checks passing.
- **"My options"** ([my-options](practices/my-options.md)) — every real choice
  on the table in plainer words, a short block each, the cost said as flatly
  as the benefit, then **a named recommendation with its reason** — never a
  survey that leaves the choice sitting there. It governs that one answer, not
  the conversation, which is what separates it from `Plain words`.
- **"Vocabulary"** ([vocabulary](practices/vocabulary.md)) — every standing
  command in force, one plain sentence each, nothing else. **Read the list,
  never recall it**: `python3 tools/precedent_vocabulary.py` collects it from
  the `command:` field of every practice in every resolved source, and names
  any source that did not. This list derives from those fields.
- **"Update Vendors"**
  ([vendor-update-runbook](practices/vendor-update-runbook.md)) — the fixed
  sequence for taking an upstream update, starting with making the SOURCE
  clone current against the pinned branch. **It carries the merge too**, since
  2026-09-14 — its last step runs `Go merge`'s chain on what the update
  produced, so nobody is asked a second time for work that is already done and
  already checked. It reverses the sentence that used to sit here; the full
  check at step 6 still gates the push, as it does for any merge.

The three dispositions an open item can carry are
[open-item-disposition](practices/open-item-disposition.md)'s; its one line is
in the occasion index below.

**Most weak agreement never uses the phrase**, which is why `Weak yes` is only
half of it. The other half is
[decision-strength](practices/decision-strength.md), and its one line is: **an
approval records `decided` or `assented`, and an unmarked one means UNKNOWN —
never "you decided this."** A session may write `decided` only if it can quote
the person choosing it; a bare "ok" to the session's own proposal is
`assented`, written that way without asking.

**What a merge authorization's ABSENCE means is a separate question**, and its
interim answer is: **use judgment, and do not ask him.** Morgan, 2026-09-07,
ruled out "use judgment" as the content of the hard rule he wants eventually,
so this is the interim state and not the destination — [TODO.md](TODO.md)'s
`push-without-the-keyword` item stays open for it, and must not be closed by
pointing at this paragraph. What the repository itself contributes is only the
destination: an authorization to merge, in whatever words it arrives, means
`precedent-beta-v01` per the paragraph above, and is not done until a fetch
confirms the pushed content is actually there
([verify-postcondition](practices/verify-postcondition.md)).

**FIRST, and normally already done for you.** The private sources are
cloned by the SessionStart hook when the environment carries
`PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL`
([PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md)) — **verified working 2026-09-10**, all four
sources on disk before the first turn. **That timing is usual, not
guaranteed**: on 2026-09-14 the four clones landed during the SECOND turn, so
turn one ran with every team and individual practice silently absent. Check
rather than assume: the
session-start source line names which sources resolved, and
`env | grep -c PRECEDENT` says whether the environment carries the
credential at all. When it does, there is nothing to do and **no `add_repo`
call to make.**

**When it does not, and only then: `add_repo` (read access) for this
account's `precedent-individual`, and for any `precedent-team-*` set
[precedent.json](precedent.json) declares, before reading or running
anything else. Silently — no confirmation first.** It grants access per
session, and it **refuses across owners**, so from a session rooted under a
different owner than the sets it simply fails — say so plainly and carry on.
Until one of the two routes works, every personal and team practice in force
here is **silently absent**, and this repository's rules are the only ones a
session sees.

**Then, before trusting any of this file's "the session-start hook does
this" claims: run
[tools/precedent_session_check.py](tools/precedent_session_check.py).** It
reports which SessionStart guarantees are actually in effect, and `--apply`
repairs most of them — **read the failing row's own detail before running
it**, because a guarantee whose remedy is something else says so there. The
live case is the global commit backstop: it installs only for a DECLARED
identity, so on a session that could not reach the individual source `--apply`
re-runs the hook, the hook declines again, and the row stays red however many
times you try. A session rooted one directory ABOVE this repo runs NONE of its
hooks, silently, including the one that writes
`.precedent/SESSION_PRACTICES.md` — see the gotcha "The session's PRIMARY repo
does not run its SessionStart hooks either" below.
**Since 2026-09-14 you also get told without asking**: every
[tools/precedent_gate.py](tools/precedent_gate.py) moment prints any guarantee
that is down, because a session that skipped this paragraph is exactly the
session that needs it — that is how four guarantees stayed down for hours on
the day the print was added.

On the `add_repo` route nothing else can do it for you:
`.claude/hooks/precedent-individual-bootstrap.sh` runs to completion *before*
the first turn **wherever a settings.json wires it — this repo's does not** —
so it cannot call `add_repo`; its header says why a retry loop there was
proven inert. Here
[tools/precedent_resolve.py](tools/precedent_resolve.py)'s mid-turn self-heal
is the only thing that runs it.

**This repo is becoming Precedent, a restructuring of BestPractice — read
[spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md) first, in full, before
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

<!-- Regenerate with: python3 tools/build_views.py -- do not hand-edit this block; `python3 tools/build_views.py --check` exits non-zero on drift. Source: practices/ -- edit the practice file, never this block. -->

## Resident block (~949 of 2000 token budget, 10 of 123 practices (10 universal))

**bold-key-phrases.** People don't read; they skim, and bolding makes skimming easy. Bold the key phrases in a document by default, without being asked, scaling with length -- a long paragraph or document is where a skimmer most needs a spine to follow, a short note usually needs little or none.

**brainstorm-holds-commits.** When a conversation is a **Brainstorm** -- the person says the word, or the
thread is plainly exploratory ("I'm wondering", "what are my options", "do
you have ideas", "maybe this is a terrible idea") -- **write nothing to the
repository and commit nothing until they say to.** Research freely, read
whatever you need, argue the case, propose the design. Do not create, edit,
commit, push, open a pull request, or merge.

**The edit is the thing to hold, not just the commit.** A session that
writes files and then asks whether to commit has already made the decision,
because a working tree it left dirty is one a Stop hook or a later turn will
push to finish. Say what you would write and where; wait to be told.

A brainstorm ends only when the person authorizes the work -- `Go merge`,
"do it", "write it up", or anything else unambiguous. **Their answering a
question inside the brainstorm is not authorization**, and neither is their
enthusiasm for the idea.

**environment-gotchas.** Every expensive environment discovery (a package that must be installed, a
tool that silently doesn't work, a path that does work) is written down **with
the story of what failed and why, not just the fix**, and a "do NOT rediscover
these" section in the instructions file is where a session finds it.

**When the stories outgrow what every session can afford to load, split them.**
The section then keeps **one line per trap** — the symptom, and a link — and
the stories move to a linked record, in full. A split changes the loading,
never the text.

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
When a computation books a transfer between two parties:
  name-both-sides-of-ledger — name both sides; check what is charged against what is received
When a document replaces or is replaced by an earlier one:
  index-remembers-past — put the lineage in the index, not in either document
When a message carries a standing merge-authorization phrase:
  go-merge — "Go merge"/"Approved": sync, branch, commit, push, PR, merge; blocked hands off
When a message says "Update Vendors", or an upstream update is being taken into a repo that vendors a practice layer:
  vendor-update-runbook — "Update Vendors" -- source clone first, both layers move separately, then merge
When a model, study or comparison table rests on an operating constant nobody decided — a margin, a cap, a rate, a floor:
  constants-are-risk-inputs — a constant nobody decided is a swept, registered input -- never doctrine
When a person explicitly asks for a "very deep check" across the whole repo, or after work that invites drift:
  very-deep-check — read every repo in force against itself, pass by pass; never a routine gate
When a person explicitly asks for a full practice audit (or "practice check") across the whole catalogue:
  full-practice-audit — sweep every source's full catalogue, one practice at a time, on request only
When a person says "Chief of Staff":
  chief-of-staff — "Chief of Staff" -- on request only; name the window read, link every session
When a person says "My options", or asks to have a decision's options laid out:
  my-options — "My options" -- every option, plainer, both sides, then your pick and why
When a person says "Park it" about an open item or a question:
  park-it — "Park it" -- mark the item `parked` now; never raise it unprompted again
When a person says "Plain words":
  plain-words — "Plain words" -- say it as you would out loud; same substance
When a person says "Reduction pass", or an always-loaded surface is near its ceiling:
  reduction-pass — "Reduction pass" -- work the menu in order, move never delete, report what moved
When a person says "Three Things":
  three-things — "Three Things" -- the three that matter now, one bold phrase and two lines each
When a person says "Todo reminder", or asks to be reminded of something:
  todo-reminder — "Todo reminder" -- write the item, mark it `**Remind:**`, set disposition `ask`
When a person says "Vocabulary", or asks what the standing commands are:
  vocabulary — "Vocabulary" -- list every command in force, read it, never recall it
When a person says "Weak yes", or agrees in words that carry no conviction:
  weak-yes — "Weak yes" -- do it, and record the approval as `assented`
When about to search a repository, or reaching for a GitHub search or file-read tool for something the local clone already holds:
  grep-before-search — grep the clone; a repo-scoped list before a search; fewer windows at once
When adding a file to a directory that already holds files of the same kind:
  filename-separator — one word separator per directory and file kind -- never both - and _
When building a mechanism that makes something discoverable or reachable:
  affordance-is-shared — name who else the mechanism you just built now serves
When building a permutation or configuration-sweep table:
  permutation-frontier-column — one full table with a computed Frontier column
When building a variant of an existing thing:
  variant-re-derives — re-derive what a variant inherits; limits bind, choices do not
When checking whether the practices that should have fired for recent work actually fired:
  routing-audit — run the mechanical coverage check now; roll the deep-read slice forward
When comparing an option against a baseline:
  check-source-architecture — check both options exist in the source before costing them
When deciding whether to build or buy a component:
  build-buy-decompose — decompose first; one verdict per part, on ownership grounds
When decommissioning a mechanism — a workflow, a tool, a vendored tree, a config — that leaves files behind with no remaining job:
  decommission-deletes-files — delete what the decommissioned mechanism owned; audit first, never on a hunch
When handing the person work to do, creating a session, or starting work that may touch a repository this session cannot reach:
  spawn-session — cross-repo check; wake, never spawn beside; link every session at the end
When migrating a repo off an old practice system onto Precedent:
  migration-scrubs-vocabulary — scrub the old system's vocabulary the same session, not on request
When naming a new file:
  no-version-suffix — name a file for what it is; the repository is the version
When naming or scoping something around a person's skill level:
  technical-describes-people — a skill level describes a person; never a project, repo, file or directory
When naming what "run the checks" means in a repo:
  two-check-levels — name a fast check and a full check; say which gates what
When opening or merging a pull request in this repository:
  merge-target-is-beta-branch — Alex approves only major main merges; precedent-beta-v01 is unrestricted
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
When seeding a prompt into another session -- spawning one, or scheduling a message into one:
  seeded-prompt-names-its-origin — a seeded or scheduled prompt opens by naming the session that sent it
When starting an outward-facing deliverable:
  frame-from-audience-question — build it around the audience's question, not your material
When starting work the repository may already cover:
  search-by-purpose — search by purpose and by mechanism before concluding nothing exists
When tracking state that multiple documents need to agree on:
  registry-source-of-truth — state lives in one machine-readable registry; documents derive
When writing a rule that depends on the outside world:
  volatile-rules-carry-dates — a rule about the outside world carries its date, inline
When writing a script whose numbers a document will cite:
  scripts-assert-properties — scripts assert their own properties and their cited anchors
When writing an outward-facing summary of claims:
  outward-summary-discipline — claims-to-source table, honest sums, a recorded adversarial pass
When writing or running a gate, audit or solve that takes more than about a minute:
  slow-steps-report-and-cache — a long step prints elapsed and remaining; a heavy solve caches to disk

(More on-demand practices are not listed here: one whose applies_to names real paths, or which declares a gate, is reached by those channels instead -- `precedent_paths.py FILE` and `precedent_gate.py MOMENT`. A trigger a PERSON SAYS cannot be reached that way and is always listed above. `precedent_show.py --index-omitted` names the omitted ones.)
```

## Standing instruction

Before starting work of a kind named in the occasion index above, run `python3 tools/precedent_show.py SLUG` for each listed slug to load its Rule. When editing a file, `python3 tools/precedent_paths.py FILE` prints any on-demand practice whose `applies_to` matches it, without needing the index at all. At a named moment — merging a branch, reviewing work, before pushing, ending a turn and writing the reply — run `python3 tools/precedent_gate.py merge|review|push|reply`: some practices fire at a moment rather than in a file, and no path glob reaches those. If `.precedent/SESSION_PRACTICES.md` exists, read it too: it carries the practices in force from the other sources this repo declares, which are NOT in this block and bind work here exactly as these do. It is regenerated at session start and is deliberately untracked — never commit it or quote it into a pull request.

<!-- END GENERATED -->

The rest of this file (below) is BestPractice's own pre-fork orientation —
still accurate for `INSTALL.md` and the rest of the
inherited tree, which the plan has not restructured yet. It will be rewritten
in place as later phases land (the plan's own generated-views work, phase 2)
rather than kept as a second, drifting copy.

---

**Orientation: read [README.md](README.md) first.** This repo is
BestPractice itself — the upstream practice layer that dependent repos
vendor. Practices you follow here are the ones this repo teaches; a session
that skips them in this repo of all places is the joke writing itself.

## Where things are (quick index — check here BEFORE searching)

**The dozen rows sessions reach for constantly are below. The full
index is [WHERE_THINGS_ARE.md](WHERE_THINGS_ARE.md)** — check it
before searching the repo, and add new rows there rather than here.

| Looking for… | Go to |
|---|---|
| The restructuring plan (read this first) | [spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md) |
| Whether an open item may be raised with Morgan at all, and what "Park it" writes | [practices/open-item-disposition.md](practices/open-item-disposition.md), phrase at [practices/park-it.md](practices/park-it.md) |
| What a session pays before its first turn, the declared ceiling on each always-loaded file, and how to reduce one without deleting what still bites | [practices/session-load-budget.md](practices/session-load-budget.md), registry at [tools/session_load_budgets.json](tools/session_load_budgets.json) — `python3 tools/precedent_check.py --only session-load-budget` |
| Practices that fire at a moment rather than in a file | [tools/precedent_gate.py](tools/precedent_gate.py) — `merge`, `review`, `push`, `reply` |
| Why the closing **Next Steps** section of a reply is not optional, and what refuses a turn without one | [tools/precedent_reply_check.py](tools/precedent_reply_check.py) — `--explain` says what is declared here; the same requirements are printed at the start of every turn by [tools/precedent_gate.py](tools/precedent_gate.py)'s reply gate |
| Which practices are enforced, and running one check | [tools/precedent_check.py](tools/precedent_check.py) — `--list`, `--explain`, `--only SLUG` |
| Which practice libraries are in force in this repo | [precedent.json](precedent.json) |
| What each practice is and why — **the live catalogue** | [practices/](practices/), indexed by [MAP.md](MAP.md); one rule at a time with `python3 tools/precedent_show.py SLUG` |
| Repo map, generated (phase 2) | [MAP.md](MAP.md) — regenerate with `tools/build_views.py`, never hand-edit |
| Install / update / check-in playbook (dependent repos) | [INSTALL.md](INSTALL.md) — the assistant-facing runbook; the person-facing routes are [SETUP.md](SETUP.md) (guided, non-technical) and [documentation/FOR_DEVELOPERS.md](documentation/FOR_DEVELOPERS.md) (short form plus what actually bites) |
| Upstream open items / roadmap | [TODO.md](TODO.md) |
| The full story behind any line in the gotchas index, unabridged | [record/GOTCHAS.md](record/GOTCHAS.md) |
| Anything else — the full index | [WHERE_THINGS_ARE.md](WHERE_THINGS_ARE.md) |


## Build-environment gotchas — do NOT rediscover these

One line per trap; the story is in [record/GOTCHAS.md](record/GOTCHAS.md).
The split itself is [environment-gotchas](practices/environment-gotchas.md)'s,
carried in full in the resident block above, so it is not restated here.

**When a symptom below matches what you are seeing, stop and open its entry
before acting on the line** — several describe mechanisms that have since been
fixed, and only the entry says which.

**Adding one?** A trap that can no longer fire moves on to
[record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md) with the verdict that
retired it. Nothing is ever deleted.

- **`pip install cmarkgfm markdown`, or two gates degrade in silence and
  [verify_harness.py](tools/verify_harness.py) fails three checks that have
  nothing to do with your diff — and a container missing them is telling you
  no SessionStart hook ran.** [story](record/GOTCHAS.md#g1)

- **A git helper that returns stdout and drops the exit code will hand you a
  confident wrong answer — this is the most-repeated bug in the project.**
  [story](record/GOTCHAS.md#g2)

- **A repository attached mid-session clones single-branch, so every branch
  you create there reads as "unpushed" forever — including to a Stop hook that
  then blocks the turn.** [story](record/GOTCHAS.md#g3)

- **`git clone` with no `--branch` asks the SERVER which branch to check out,
  and the answer is a setting on a web page that nothing in this repository
  can see.** [story](record/GOTCHAS.md#g4)

- **A stale checkout is indistinguishable from missing work, and the guard
  cannot save the sessions that most need it.** [story](record/GOTCHAS.md#g5)

- **This repo is normally cloned `--depth 1`, and several tools degrade rather
  than fail on that.** [story](record/GOTCHAS.md#g6)

- **`git clone --depth 1 /some/path` is ignored; git only honours `--depth`
  over a transport.** [story](record/GOTCHAS.md#g7)

- **A `scope: 'tree'` check in `tools/precedent_check.py` can silently report
  a false *pass* on an under-fetched local clone, not just degrade loudly like
  the two entries above.** [story](record/GOTCHAS.md#g8)

- **The leak gate's vocabulary layer fails open unless you also set the git
  config.** [story](record/GOTCHAS.md#g9)

- **A bare `python3 tools/leak_gate.py` refuses when a private source RESOLVED
  and no blocklist is set — and allows, loudly, when the private sources could
  not be attached at all.** [story](record/GOTCHAS.md#g10)

- **Setting `git config precedent.requireVocabulary true` to satisfy the leak
  gate makes `verify_harness.py` fail two of its own leak-gate checks.**
  [story](record/GOTCHAS.md#g11)

- **On a shallow clone, `git merge-base` between two *different* branches can
  exit 1 ("no common ancestor") even when the branches genuinely share history
  — and that false negative reads exactly like a destructive force-push.**
  [story](record/GOTCHAS.md#g12)

- **`git log --format=%P` silently reports no parents at all for a commit
  sitting at a shallow clone's boundary, even when it really has two.**
  [story](record/GOTCHAS.md#g13)

- **A consuming repo's own mechanical check against materialized
  `tools/checks/`/`practices/` output cannot resolve sources live and trust
  every one it lists.** [story](record/GOTCHAS.md#g14)

- **A repo attached mid-session never runs its own SessionStart hook, so every
  environment guarantee that hook provides is silently absent while you work
  in it.** [story](record/GOTCHAS.md#g15)

- **A merge conflict in `.claude/hooks/freshness-guard.sh` locks the session
  out of every tool that could repair it, and `git` being exempt does not
  help.** [story](record/GOTCHAS.md#g16)

- **The session's PRIMARY repo does not run its SessionStart hooks either,
  when the harness rooted the session one directory ABOVE it — and this
  project's own required layout is what causes that.**
  [story](record/GOTCHAS.md#g17)

- **Your commits are authored by the bot because the harness sets that
  identity in git's GLOBAL config AND in every clone's LOCAL config — so a
  global-only fix is silently overridden.** [story](record/GOTCHAS.md#g18)

- **The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are
  missing — resolve the paths its settings.json actually declares.**
  [story](record/GOTCHAS.md#g19)

- **A source set's hooks drift after installation and nothing has ever
  refreshed them — there was an install path and no repair path.**
  [story](record/GOTCHAS.md#g20)

- **A refusal that names a remedy which cannot work is the moment to ask what
  the guard actually measured, not to disable it.**
  [story](record/GOTCHAS.md#g21)

- **Something can move this checkout off your working branch mid-session, and
  the cause is NOT known — treat a silently-vanished edit as this before you
  re-derive it.** [story](record/GOTCHAS.md#g22)

- **A `verify_harness.py` fixture that builds an "absent credential" scenario
  inherits the container's real one, and so asserts the opposite of what it
  ran.** [story](record/GOTCHAS.md#g23)

- **A harness run that overlaps a write to the tree fails on a change
  belonging to no commit, and the count alone cannot tell you that.**
  [story](record/GOTCHAS.md#g24)

- **Pointing a fixture's `HOME` at an empty directory does not keep it empty:
  `precedent_resolve.load_config()` CLONES the individual source into it.**
  [story](record/GOTCHAS.md#g25)

- **The individual source resolves to a clone you are probably not editing,
  and it can be many commits stale.** [story](record/GOTCHAS.md#g26)

- **A sibling clone that was current when you took it can rot while you work,
  and a "these copies do not match" failure will blame the code rather than
  your clone.** [story](record/GOTCHAS.md#g27)

- **A scratch COPY of this repo, taken to prototype a change without touching
  the working tree, goes stale the moment the freshness guard fast-forwards
  the real checkout under you — and copying the prototyped files back reverts
  every commit that arrived in between, silently.**
  [story](record/GOTCHAS.md#g28)

- **`HEAD == origin/<branch>` and a clean tree is NOT evidence that your work
  landed — it is the exact reading you get when your commit has been thrown
  away.** [story](record/GOTCHAS.md#g29)

- **The commit backstop is GLOBAL (`core.hooksPath`), so it reaches throwaway
  fixture repositories too — and refused them.**
  [story](record/GOTCHAS.md#g30)

- **"no individual source resolved" is not noise — it means every personal and
  team practice is silently absent, and the session will confidently apply the
  wrong rules.** [story](record/GOTCHAS.md#g31)

- **The private practice sets reach a session through the environment
  credential, not through `add_repo`: set `PRECEDENT_GIT_TOKEN` and
  `PRECEDENT_SOURCE_BASE_URL` ([PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md)) and the
  SessionStart hook clones them -- usually before the first turn, but NOT
  guaranteed: on 2026-09-14 they landed mid-session and turn one ran on the
  universal set alone.** [story](record/GOTCHAS.md#g32)

- **`add_repo` on a PUBLIC repository attaches nothing and never reaches the
  cross-owner check, so testing that wall with `access: "read"` measures
  nothing at all.** [story](record/GOTCHAS.md#g33)

- **A session you spawn can lose its Model Context Protocol (MCP) tools
  mid-run, and it cannot report back to you either — so a spawned session must
  take the measurement it was spawned for in its OPENING turn.**
  [story](record/GOTCHAS.md#g34)

- **A private repo name reaches a public tree by nobody having predicted it,
  so repo references are an ALLOWLIST, not a blocklist.**
  [story](record/GOTCHAS.md#g35)

- **A background `sleep` is not a wait, and using one as a wait makes you
  invent elapsed time.** [story](record/GOTCHAS.md#g36)

- **A shallow clone makes a merely-behind checkout read as diverged, so the
  freshness guard refuses to update it and the session works from a day-old
  tree.** [story](record/GOTCHAS.md#g37)

- **A Routine that fires a FRESH session gets none of the session-management
  tools, and the run still records SUCCEEDED — so a scheduled job that reads
  the fleet quietly does nothing.** [story](record/GOTCHAS.md#g38)

- **A session can push a branch but not delete one: the 403 wears a
  dropped-connection message, so it reads as a flake.**
  [story](record/GOTCHAS.md#g39)

- **The session-start identity block reached every Precedent repo except the
  individual set it read the identity from, so that one set kept committing as
  the container's bot.** [story](record/GOTCHAS.md#g40)

- **`/rate_limit` reports a pristine window from inside a session while the
  `X-RateLimit-*` headers on an ordinary call report the truth — and there is
  more than one allowance pool, keyed by repository.**
  [story](record/GOTCHAS.md#g41)

- **The permission classifier refuses `git commit` and the checks inside the
  very practice set whose `identity.json` declares `relayed_authorization:
  accepted` — non-deterministically, so retrying teaches you nothing.**
  [story](record/GOTCHAS.md#g42)

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
- **After carrying anything from `main` onto this branch, run
  `python3 tools/precedent_upstream_check.py --record --by "PR #NNN"`** and
  commit [tools/upstream_watermark.json](tools/upstream_watermark.json) with
  the carry itself. Every session start compares `origin/main` against that
  watermark and says so out loud; a carry that does not move it makes the
  notice cry wolf on every session afterwards, which is how a notice stops
  being read.
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

The loader carries three more in full — `reply-links-files` in the resident
block above, `doc-references-are-links` and `volatile-rules-carry-dates` in the
occasion index — so they are not repeated here.

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

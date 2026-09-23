# Repository notes for agents

<!-- These are the instructions for sessions working ON the BestPractice
     repo itself (the upstream). Inside a dependent repo's vendored copy
     (process/upstream/AGENTS.md) this file is inert — the dependent repo
     has its own instantiated AGENTS.md at ITS root. -->

**TEMPORARY, read before opening or merging any pull request (PR) here:
every PR in this repository targets `precedent-beta-v01`, never `main`.
Alex merged the branch into `main` on 2026-09-14 and Morgan merges it there
regularly; **that does not retire this rule** — work still lands here, and
`main` takes it by those merges only (Morgan, 2026-09-14). Merging a PR
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

**Precedent commands.** Each of these names a thing a session recognizes by
what the message is actually asking for, not by scanning it for a keyword —
each has a phrase that is always sufficient and never ambiguous, and each is
a universal practice: the trigger and the meaning are here, and the rule,
the argument and the story of its coining are in the practice file —
`python3 tools/precedent_show.py SLUG` for any of them. **The phrase removes
doubt; it does not create a requirement.** A message that plainly asks for
the same thing in other words gets the same treatment, and where a command
authorizes something hard to reverse (a push, a merge, a mark recording how
convinced he was) and the reading is a genuine judgment call rather than a
clean one, that is said out loud and confirmed rather than guessed —
[go-merge](practices/go-merge.md) and [weak-yes](practices/weak-yes.md)
spell out exactly how, below. A few — a full practice audit, a very deep
check, the fleet sweep — are the deliberate exception, kept to the literal
ask because what they trigger is too expensive to run on a guess; each
names why in its own file.

- **"Go update"** and **"Approved"** ([go-merge](practices/go-merge.md)) —
  classify first: a direct push, straight to the shared branch, no PR, is now
  the **default**; only a **high-risk** change (touches enforcement/gating
  code, changes a governance or authorization practice, is hard to reverse
  once live, or you're not confident it's none of those) runs the full chain —
  syncs, says the branch out loud, commits, pushes, opens the pull request,
  and merges — **without asking again.** **Either path ends on the branch on
  `origin`** — `precedent-beta-v01` here per the rule at the top of this file,
  never `main` for being the configured default — **and a commit still sitting
  in the local clone has not done it**: fetch and confirm `origin` carries it
  before the reply says where the work went. Say which path you took, and why,
  in the reply. Unsure which it is? High-risk. A step this session cannot
  perform hands off rather than coming back as a question: the
  authorization travels with the work. One rule, two triggers, and
  `Go update` is the one to lead with — it names what actually happens
  whether or not a merge is literally in the picture.
  `Approved` is also an ordinary adjective, so *"the approved plan of
  record"* is not the command.
  **Neither is required for the authorization to exist** —
  "sold, ship it" reads as this command as plainly as the phrase does.
  What the phrase buys is certainty:
  say one of them and the chain runs, full stop. Where it's absent and the
  sentence could honestly go either way, say the read out loud and get it
  confirmed before the push, the pull request, or the merge — commit locally
  regardless, and hold only the shared-branch steps on the answer.
- **"Push directly to [branch]"** ([push-directly](practices/push-directly.md))
  — the classification's own override, named: skip it outright and push
  straight to that branch, no PR, whatever `Go update` would otherwise call
  for on this one change. Name the branch ("push directly to main") to
  target it explicitly; say it bare and it defaults to the primary branch
  the work is already on — `precedent-beta-v01` here, per the rule at the
  top of this file, never `main` just because that is the repository's
  configured default. Not a standing exemption — it authorizes the change
  in front of it, not every change after it.
- **"Drop it"** ([park-it](practices/park-it.md)) — write
  `**Disposition:** parked (<date>, <who said it>)` into the item meant, in
  that same turn, say which item was marked, and **never raise it unprompted
  again** — not this session, and not a later one that decides it has become
  urgent. Nobody owes an explanation for parking something: do it, and never
  ask a follow-up about it. **Kept to the literal word, deliberately** —
  parking has no built-in correction, so where it only *sounds* like the
  phrase ("that can wait", "let's not worry about that one") ask which they
  mean rather than guess.
- **"Three Things"** ([three-things](practices/three-things.md)) — the three
  most important things he needs to know now, each a bolded phrase and at most
  two sentences, and nothing around them: no preamble, no fourth item, no
  closing offer. It asks for **attention rather than action**: an answer
  assembled from what is already in context is the failure it prevents. A
  plain ask for the same shape of answer ("what do I actually need to know
  right now") gets it too — low stakes if the read is wrong, so no
  confirmation step.
- **"Simple words"** ([plain-words](practices/plain-words.md)) — the same
  answer said the way you would say it out loud: short sentences, the concrete
  case before the general principle, no hedging. **It governs the rest of the
  conversation, not just the next reply**, and nothing about the substance
  changes — a plainer reply that quietly says less has failed it. Asking for
  this register in other words counts the same as the phrase.
- **"Weak yes"** ([weak-yes](practices/weak-yes.md)) — go ahead, and record
  that he was not convinced: `strength: assented`, written into whatever the
  approval is being recorded in, that same turn. **Not an invitation to talk
  him into it.** Most weak agreement arrives without the phrase, and still
  gets marked `assented` ([decision-strength](practices/decision-strength.md))
  — but where that reading is a genuine judgment call rather than a clean
  one, `weak-yes`'s own worked example says how to disclose it instead of
  writing it silently.
- **"Prompt Please"** ([prompt-please](practices/prompt-please.md)) — before
  starting what he just asked for, check whether it belongs in a different
  session, repositories first; then hand back **one paste-ready block** he
  opens a new window with, naming the repository to root it in and the ones
  to attach, plus one ordinary unfenced sentence outside the block saying
  where to paste it. **Never call a session-creating or session-messaging
  tool for this, and never wake a live session either** — both have come
  back rejected often enough that the mechanism is retired outright, and a
  paste block needs nothing from any one provider's tool surface. The check
  runs whether or not he says the phrase, and an honest "this session is the
  right one" answers it. **The block carries a merge authorization only when
  he gave one for this handoff** — absent that it says `DO NOT MERGE — STOP
  AT THE PULL REQUEST` in those words; given one, it is bounded to the
  handed-off work, that repository's routine branch and its own checks
  passing.
- **"My options"** ([my-options](practices/my-options.md)) — every real choice
  on the table in plainer words, a short block each, the cost said as flatly
  as the benefit, then **a named recommendation with its reason** — never a
  survey that leaves the choice sitting there. It governs that one answer, not
  the conversation, which is what separates it from `Simple words`.
- **"Vocabulary"** ([vocabulary](practices/vocabulary.md)) — every standing
  command in force, one plain sentence each, nothing else. **Read the list,
  never recall it**: `python3 tools/precedent_vocabulary.py` collects it from
  the `command:` field of every practice in every resolved source, and names
  any source that did not. This list derives from those fields.
- **"Update Vendors"**
  ([vendor-update-runbook](practices/vendor-update-runbook.md)) — the fixed
  sequence for taking an upstream update, starting with making the SOURCE
  clone current against the pinned branch. **It carries the merge too**, since
  2026-09-14 — its last step runs `Go update`'s chain on what the update
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

**What a merge authorization's ABSENCE means was an open question from
2026-09-07 to 2026-09-16.** Morgan, 2026-09-07, ruled out "use judgment" as
the content of the hard rule he wanted eventually, and asked not to be
asked again while he found one — recorded in
[todo/todo-2026-09-07-push-without-the-keyword.md](todo/todo-2026-09-07-push-without-the-keyword.md).
**He gave it 2026-09-16**, in the same conversation that moved this whole
section from phrase-matching to intent: read the message for what it is
asking, and where reading it is a genuine judgment call rather than a clean
one, say the read out loud and confirm before the shared-branch steps run,
rather than either guessing silently or holding silently. `Go update` and
`Weak yes` above spell out what that looks like for each. An authorization
to merge, in whatever words it arrives, means `precedent-beta-v01` per the
paragraph above, and is not done until a fetch confirms the pushed content
is actually there ([verify-postcondition](practices/verify-postcondition.md)).

**FIRST, and normally already done for you.** The private sources are
cloned by the SessionStart hook when the environment carries
`PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL`
([PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md)) — **verified working 2026-09-10**, all four
sources on disk before the first turn. **That timing is usual, not
guaranteed**: on 2026-09-14 the four clones landed during the SECOND turn, so
turn one ran with every team and individual practice silently absent. Check
rather than assume: the
session-start source line names which sources resolved, and
`env | grep -c PRECEDENT` says whether the environment carries the
credential at all. When it does, there is nothing to do and **no `add_repo`
call to make.**

**When it does not, and only then: `add_repo` (read access) for this
account's `precedent-individual`, and for any shared set
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

## Resident block (~734 of 2000 token budget, 9 of 139 practices (9 universal))

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

**environment-gotchas.** Every expensive environment discovery (a package that must be installed, a
tool that silently doesn't work, a path that does work) is written down
**with the story of what failed and why, not just the fix**, in its own
file — one trap, one file, forever — under `gotchas/gotcha-<date>-<slug>.md`
(directory and frontmatter shape:
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
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
When a branch has done its job -- a pull request merged, a tidy-up, or a person saying to delete some branches:
  never-delete-a-remote-branch — never attempt a remote branch delete; hand over the one-click link
When a computation books a transfer between two parties:
  name-both-sides-of-ledger — name both sides; check what is charged against what is received
When a document replaces or is replaced by an earlier one:
  index-remembers-past — put the lineage in the index, not in either document
When a judgment call is needed to keep work moving:
  small-calls — make small calls yourself; note them; stop only for big ones
When a message says "Archive", with or without a question mark, or otherwise asks whether the session can be archived:
  archive-status-check — "Archive"/"Archive?" -- check pending; archive if clear, else say what isn't
When a message says "Go update" or "Approved", or plainly authorizes a merge:
  go-merge — "Go update"/"Approved": default push; high-risk -> sync, branch, PR, merge
When a message says "Push directly", naming a branch ("push directly to main") or not, or gives a specific instruction to skip the PR for this one change:
  push-directly — "Push directly [to BRANCH]" -- no PR; unnamed defaults to the branch in play
When a message says "Update Vendors", or an upstream update is being taken into a repo that vendors a practice layer:
  vendor-update-runbook — "Update Vendors" -- source clone first, both layers move separately, then merge
When a model, study or comparison table rests on an operating constant nobody decided — a margin, a cap, a rate, a floor:
  constants-are-risk-inputs — a constant nobody decided is a swept, registered input -- never doctrine
When a person asks, in whatever words, for a write-up of the issue or bug being worked:
  write-it-up — "Write it up" -- commit a full report of the issue and fix, then link it
When a person explicitly asks for a "very deep check" across the whole repo, or after work that invites drift:
  very-deep-check — read every repo in force against itself, pass by pass; never a routine gate
When a person explicitly asks for a full practice audit (or "practice check") across the whole catalogue:
  full-practice-audit — sweep every source's full catalogue, one practice at a time, on request only
When a person says "Chief of Staff":
  chief-of-staff — "Chief of Staff" -- on request only; name the window read, link every session
When a person says "Drop it" about an open item or a question:
  park-it — "Drop it" -- mark the item `parked` now; never raise it unprompted again
When a person says "My options", asks to have a decision's options laid out, or asks -- about a current issue -- for the options to hand off to another session:
  my-options — "My options" -- every option, plainer, your pick -- or a paste-ready handoff
When a person says "Primary branch", or asks which branch is trunk, the routine working branch, or where regular pushes and pull requests land:
  primary-branch — "Primary branch" -- trunk; the branch regular work pushes to and PRs target
When a person says "Reduction pass", or an always-loaded surface is near its ceiling:
  reduction-pass — "Reduction pass" -- work the menu in order, move never delete, report what moved
When a person says "Simple words", or plainly asks to be talked to that way:
  plain-words — "Simple words" -- say it as you would out loud; same substance
When a person says "Three Things", or plainly asks for exactly this shape of answer:
  three-things — "Three Things" -- the three that matter now, one bold phrase and two lines each
When a person says "Todo reminder", or asks to be reminded of something:
  todo-reminder — "Todo reminder" -- write it, set disposition ask and remind_on, never a trigger
When a person says "Vocabulary", or asks what the standing commands are:
  vocabulary — "Vocabulary" -- list every command in force, read it, never recall it
When a person says "Weak yes", or agrees in words that carry no conviction:
  weak-yes — "Weak yes" -- do it, and record the approval as `assented`
When about to search a repository, or reaching for a GitHub search or file-read tool for something the local clone already holds:
  grep-before-search — grep the clone; a repo-scoped list before a search; fewer windows at once
When adding a file to a directory that already holds files of the same kind:
  filename-separator — one word separator per directory and file kind -- never both - and _
When asked to include an image, logo, or other binary asset the person is supplying, rather than approximate one from a description:
  attach-the-original — attach the file itself -- recreating an original from a description is invention
When building a mechanism that makes something discoverable or reachable:
  affordance-is-shared — name who else the mechanism you just built now serves
When building a permutation or configuration-sweep table:
  permutation-frontier-column — one full table with a computed Frontier column
When building a variant of an existing thing:
  variant-re-derives — re-derive what a variant inherits; limits bind, choices do not
When checking whether the practices that should have fired for recent work actually fired:
  routing-audit — run the mechanical coverage check now; roll the deep-read slice forward
When committing a change to content this repo ships to other repos -- a practice file, a hook script, a template, or one of the named engine files in tools/precedent_vendor_engine.py's ENGINE_FILES/CONSUMER_ENGINE_FILES lists -- before it is pushed or merged:
  vendor-rollout-disclosed — shipped content changing -- say if it needs to reach consumers, and if it will
When committing anything that touches the vendored/public tree:
  scrub-gate — the public tree is public-safe at all times, not just at check-in
When comparing an option against a baseline:
  check-source-architecture — check both options exist in the source before costing them
When creating a session:
  session-spend-follows-the-task — pick the model for the job -- reading runs small, judgment doesn't
When creating a session, or retagging one:
  session-tags — tag a session at creation -- subject, repo, role, wants; never retrofitted
When deciding whether to build or buy a component:
  build-buy-decompose — decompose first; one verdict per part, on ownership grounds
When decommissioning a mechanism — a workflow, a tool, a vendored tree, a config — that leaves files behind with no remaining job:
  decommission-deletes-files — delete what the decommissioned mechanism owned; audit first, never on a hunch
When drafting or reviewing prose meant to persuade or be judged:
  push-back — argue a real counter-case before building on a stated stance
When finishing a substantial work-product, before the merge-time capture gate:
  second-pass-capture — a separate capture pass after the work, not inside it
When handing the person work to do, starting work that may touch a repository this session cannot reach, or the person wants to act on a recommendation already given by opening a fresh session:
  prompt-please — "Prompt Please" -- recommendation or unreachable work, one paste-ready prompt
When merging a branch:
  capture-gate — capture the follow-on work in the thread that created the need
When migrating a repo off an old practice system onto Precedent:
  migration-scrubs-vocabulary — scrub the old system's vocabulary the same session, not on request
When naming a new file:
  no-version-suffix — name a file for what it is; the repository is the version
When naming or renaming a session, at creation or once its differentiator is known:
  session-title-names-the-difference — title each session by its differentiator, never its task category alone
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
When starting work another session may already have done, or opening a pull request:
  base-branch-is-the-record — read the base branch before starting and before the PR -- a summary lags
When starting work the repository may already cover:
  search-by-purpose — search by purpose and by mechanism before concluding nothing exists
When tracking state that multiple documents need to agree on:
  registry-source-of-truth — state lives in one machine-readable registry; documents derive
When when writing or changing anything that automatically fixes a state it found wrong:
  repair-cannot-discard-work — an automatic repair must not be able to discard work; reporting is not repairing
When work touches something an open item is about, or a branch is merged:
  item-closes-on-its-condition — record what you established into the item; close only on its stated condition
When writing a hook, script, or practice-file rule in this repository that a dependent repo will vendor or install:
  vendor-neutral-by-default — this repo ships out whole -- default new code and rules to provider-neutral
When writing a rule that depends on the outside world:
  volatile-rules-carry-dates — a rule about the outside world carries its date, inline
When writing a script whose numbers a document will cite:
  scripts-assert-properties — scripts assert their own properties and their cited anchors
When writing an outward-facing summary of claims:
  outward-summary-discipline — claims-to-source table, honest sums, a recorded adversarial pass
When writing or running a gate, audit or solve that takes more than about a minute:
  slow-steps-report-and-cache — a long step prints elapsed and remaining; a heavy solve caches to disk
When writing or triaging an open item:
  todo-is-a-handoff — queue only for a stated blocked-on/out-of-scope reason — otherwise just do it

(More on-demand practices are not listed here: one whose applies_to names real paths, or which declares a gate, is reached by those channels instead -- `precedent_paths.py FILE` and `precedent_gate.py MOMENT`. A trigger a PERSON SAYS cannot be reached that way and is always listed above. `precedent_show.py --index-omitted` names the omitted ones.)
```

## Standing instruction

Before starting work of a kind named in the occasion index above, run `python3 tools/precedent_show.py SLUG` for each listed slug to load its Rule. When editing a file, `python3 tools/precedent_paths.py FILE` prints any on-demand practice whose `applies_to` matches it, without needing the index at all. At a named moment — merging a branch, reviewing work, before pushing, ending a turn and writing the reply — run `python3 tools/precedent_gate.py merge|review|push|reply`: some practices fire at a moment rather than in a file, and no path glob reaches those. If `.precedent/SESSION_PRACTICES.md` exists, read it too: it carries the practices in force from the other sources this repo declares, which are NOT in this block and bind work here exactly as these do. It is regenerated at session start and is deliberately untracked — never commit it or quote it into a pull request.

<!-- END GENERATED -->

The rest of this file (below) is BestPractice's own pre-fork orientation —
still accurate for [`INSTALL.md`](INSTALL.md) and the rest of the
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
| Whether an open item may be raised with Morgan at all, and what "Drop it" writes | [practices/open-item-disposition.md](practices/open-item-disposition.md), phrase at [practices/park-it.md](practices/park-it.md) |
| What a session pays before its first turn, the declared ceiling on each always-loaded file, and how to reduce one without deleting what still bites | [practices/session-load-budget.md](practices/session-load-budget.md), registry at [tools/session_load_budgets.json](tools/session_load_budgets.json) — `python3 tools/precedent_check.py --only session-load-budget` |
| Practices that fire at a moment rather than in a file | [tools/precedent_gate.py](tools/precedent_gate.py) — `merge`, `review`, `push`, `reply` |
| Why the closing **Boildown** section of a reply is not optional, and what refuses a turn without one | [tools/precedent_reply_check.py](tools/precedent_reply_check.py) — `--explain` says what is declared here; the same requirements are printed at the start of every turn by [tools/precedent_gate.py](tools/precedent_gate.py)'s reply gate |
| Which practices are enforced, and running one check | [tools/precedent_check.py](tools/precedent_check.py) — `--list`, `--explain`, `--only SLUG` |
| Which practice libraries are in force in this repo | [precedent.json](precedent.json) |
| What each practice is and why — **the live catalogue** | [practices/](practices/), indexed by [MAP.md](MAP.md); one rule at a time with `python3 tools/precedent_show.py SLUG` |
| Repo map, generated (phase 2) | [MAP.md](MAP.md) — regenerate with [`tools/build_views.py`](tools/build_views.py), never hand-edit |
| Install / update / check-in playbook (dependent repos) | [INSTALL.md](INSTALL.md) — the assistant-facing runbook; the person-facing routes are [SETUP.md](SETUP.md) (guided, non-technical) and [documentation/FOR_DEVELOPERS.md](documentation/FOR_DEVELOPERS.md) (short form plus what actually bites) |
| Upstream open items / roadmap | [todo/TODO.md](todo/TODO.md) (open) and [todo/CLOSED.md](todo/CLOSED.md); one file per item under [todo/](todo/). [`TODO.md`](TODO.md) at the root is a redirect stub and a pull request touching it is refused by CI. |
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
- **A pull request touching [`TODO.md`](TODO.md) after the 2026-09-16 todo/gotcha
  migration is refused by CI** (`precedent_check.py --only
  todo-gotcha-stale-reference`). File the item under `todo/` instead
  ([spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)).
- **Before committing:** `python3 tools/doc_lint.py` on markdown you
  touched (`pip install cmarkgfm` — the session-start hook does this);
  after touching the deck engine, rebuild the sample both ways:
  `python3 deck/build_deck.py deck/sample` and `--send`.
- **Two check levels** (practice `two-check-levels`): **light check** is
  `python3 tools/doc_lint.py` on the markdown you touched — the fast,
  constant pass above, run before every commit without thinking about it.
  **deep check** is the full gate suite run before push or merge:
  `python3 tools/verify_harness.py --as-ci`, `python3 tools/doc_lint.py`,
  `python3 tools/leak_gate.py`, `python3 tools/precedent_check.py`, and
  `python3 tools/doc_sync.py`. **What matters is `0 failed` and
  `0 violated`, never a passed/skipped count** — those grow as checks are
  added, so a figure written down here goes stale by design; see
  [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md)'s closing section,
  which says the same thing and records the audit that found a hardcoded
  one already wrong. Light check gates a commit; deep check gates a push.
  **`--as-ci` is not decoration**: CI shards the harness across two jobs
  using variables a plain local run never sets, so the bare command
  certifies a shape nobody ships — it hid a crash on 2026-09-21 that turned
  both CI jobs red on a locally green tree. The two shards partition the
  suite, so the pair costs about what one run costs (measured 4m01s against
  ~4m20s, 2026-09-22). It reproduces CI's command SHAPE, never CI's
  environment: a local session resolves private sources CI cannot, so green
  here means the sharding is not what breaks, not that CI will be green.

## Conventions (every session, every reply)

The loader carries three more in full — `doc-references-are-links` and
`volatile-rules-carry-dates` in the occasion index above, and
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

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

**"Go merge" is a Precedent command, defined universally in
[practices/go-merge.md](practices/go-merge.md), and it means: sync, say
which branch out loud, commit, push, open the pull request, merge — without
asking again.** It moved up from Morgan's private individual set to the
universal catalogue on 2026-09-08, on his decision: *"we should have our own
commands we use for people who live in our universe."* **That reverses the
2026-09-07 retirement of `merge-authorization-keyword`**, and the two are
not the same rule — the retired one told every adopting repository to go
invent a keyword of its own, which is a preference dressed as a practice;
this one names the phrase and ships it. `merge-authorization-keyword` is now
`deduplicated` with `in_force_at: go-merge` rather than retired.

**Why the move matters beyond tidiness:** while the definition lived in a
private set, a session that had not attached it could not read it. One did
exactly that — followed an instruction to go ask what the phrase meant,
generating the precise interruption the phrase exists to prevent, while the
answer sat in a repository nobody had fetched. It is in the generated
occasion index now, so every session reads it whether or not any private
source resolved.

**What the phrase's ABSENCE means is a separate question**, and its interim
answer is: **use judgment, and do not ask him.** Morgan, 2026-09-07, asked
to choose between holding, pushing, and a line between them: *"The session
should use its judgment. Todo in the future to make a hard rule, not that."*
He wants a hard rule eventually and ruled out "use judgment" as its content,
so this is the interim state and not the destination — [TODO.md](TODO.md)'s
`push-without-the-keyword` item stays open for it, and must not be closed by
pointing at this paragraph. What the repository itself contributes is only
the destination: an authorization to merge, in whatever words it arrives,
means `precedent-beta-v01` per the paragraph above, and is not done until a
fetch confirms the pushed content is actually there
([verify-postcondition](practices/verify-postcondition.md)).

**"Park it" is a Precedent command too, defined universally in
[practices/park-it.md](practices/park-it.md), and it means: mark the item
`parked` and drop the subject.** The session writes
`**Disposition:** parked (<date>, <who said it>)` into the item meant, in
that same turn, and **no session raises that item unprompted again** — not
this one, and not a later one that decides it has become urgent. Nobody owes
an explanation for parking something, so **the response is to do it and say
which item was marked, never to ask a follow-up question about it.**

Coined by Morgan on 2026-09-08 and moved to universal the same day,
alongside `go-merge`, for the same reason. It spent one day as a repo-local
practice here; that copy is now `deduplicated` and points at the universal
one. What `parked` then means — and the two other dispositions an open item
can carry — is
[practices/open-item-disposition.md](practices/open-item-disposition.md),
whose one line is: **an item with no disposition is `wait`, and a session
raises an item with him only if the item says `ask`.**

**A fourth command, "Three Things"**, is defined universally in
[practices/three-things.md](practices/three-things.md) and asks for the three
most important things the person needs to know now — each a bolded phrase and
at most two sentences, and nothing around them: no preamble, no fourth item,
no closing offer. It is the one command here that asks for **attention rather
than action**, so a session that has not actually read the repository cannot
answer it, and an answer assembled from whatever is already in context is the
failure it exists to prevent. Coined by Morgan on 2026-09-08 and placed at
universal from the start.

**A fifth command, "Plain words"**, is defined universally in
[practices/plain-words.md](practices/plain-words.md) and asks for the same
answer said the way you would say it out loud: short sentences, the concrete
case before the general principle, no hedging and no survey of positions you
are not taking. **It governs the rest of the conversation, not just the next
reply.** Nothing about the substance changes — same conclusions, same figures,
same "Files touched" list — so a plainer reply that quietly says less has
failed it. Coined by Morgan on 2026-09-08, in the thread that also unfolded
the cross-team practice-drift item, and placed at universal the same day.

**A sixth command, "Weak yes"**, is defined universally in
[practices/weak-yes.md](practices/weak-yes.md) and means: **go ahead, and
record that I was not convinced.** It authorizes the work exactly as a plain
yes would; what it adds is the mark — `strength: assented` written into
whatever the approval is being recorded in, in that same turn. **It is not an
invitation to talk him into it**: no follow-up asking what the reservation
is.

Most weak agreement never uses the phrase, which is why the phrase is only
half of it. **The other half is
[practices/decision-strength.md](practices/decision-strength.md), and its one
line is: an approval records `decided` or `assented`, and an unmarked one
means UNKNOWN — never "you decided this."** A session may write `decided`
only if it can quote the person choosing it; a bare "ok" to the session's own
proposal is `assented`, written that way without asking. Agreement framed as
a test or a "let's see how it goes" is `assented`; enthusiasm is `decided`.
**Nothing was backfilled** — the approvals already in the catalogue stay
unmarked, permanently, because guessing which past "ok" was enthusiastic is
the invention [no-invented-specifics](practices/no-invented-specifics.md)
forbids. Coined by Morgan on 2026-09-09 and placed at universal the same day.

**A seventh command, "Spawn session"**, is defined universally in
[practices/spawn-session.md](practices/spawn-session.md) and means: **before
starting what I just asked for, check whether it belongs in a different
session — repositories first — and if it does, hand me a link to that
session, rooted in the right repository and already seeded with the prompt,
and tell me to click it.** The check itself is **not** waiting on the
phrase: it runs whenever another repository might be needed, always. The
phrase is for the times it did not, and an honest "this session is the right
one" is a complete answer to it.

It is the step that comes *before*
[practices/handoff-is-pasteable.md](practices/handoff-is-pasteable.md),
which was amended the same day: where the harness can create the session
itself, the link replaces the paste block, and the block's three things
become the seeded prompt rather than something anyone retypes. Coined by
Morgan on 2026-09-11 and placed at universal from the start, as
`clean-session`; **renamed to `spawn-session` on 2026-09-12** on his
instruction, with nothing else about it changed.

**An eighth command, "My options"**, is defined universally in
[practices/my-options.md](practices/my-options.md) and means: **lay out the
real choices in plainer words, give me the good and the bad of each, and tell
me which one you recommend and why.** Every option that is actually on the
table, a short block each, the cost said as flatly as the benefit — and then
**a named recommendation with its reason**, never a survey that leaves the
choice sitting there. It governs **that one answer**, not the rest of the
conversation, which is what separates it from `Plain words`; and his reply to
the recommendation is an approval like any other, so
[practices/decision-strength.md](practices/decision-strength.md) marks it.
Coined by Morgan on 2026-09-12 and placed at universal the same day.

**A third command, "Update Vendors"**, triggers
[practices/vendor-update-runbook.md](practices/vendor-update-runbook.md) —
the fixed sequence for taking an upstream update, starting with making the
SOURCE clone current against the pinned branch. It authorizes the update,
not the merge of what the update produces; that is still `Go merge`'s to
give.

**FIRST, and normally already done for you.** The private sources are
cloned by the SessionStart hook when the environment carries
`PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL`
([INSTALL.md](INSTALL.md) §8) — **verified working 2026-09-10**, all four
sources on disk before the first turn. Check rather than assume: the
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
[tools/precedent_session_check.py](tools/precedent_session_check.py).** It reports
which SessionStart guarantees are actually in effect, and `--apply` repairs
most of them — **read the failing row's own detail before running it**, because
a guarantee whose remedy is something else says so there. The global commit
backstop is the live case: it installs only for a DECLARED identity, so on a
session that could not reach the individual practice source `--apply` re-runs
the hook, the hook declines again, and the row stays red no matter how many
times you try. A session rooted one directory ABOVE this repo — which is what
happens whenever the sibling clones a team source needs are laid out
alongside it — runs NONE of its hooks, silently, including the one that
writes `.precedent/SESSION_PRACTICES.md`. See the gotcha "The session's
PRIMARY repo does not run its SessionStart hooks either" below; it cost a
whole session's replies on 2026-09-08.

On the `add_repo` route, nothing else can do it for you.
`.claude/hooks/precedent-individual-bootstrap.sh`
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

<!-- Regenerate with: python3 tools/build_views.py -- do not hand-edit this block; `python3 tools/build_views.py --check` exits non-zero on drift. Source: practices/ -- edit the practice file, never this block. -->

## Resident block (~876 of 2000 token budget, 10 of 102 practices (10 universal))

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

**environment-gotchas.** Every expensive environment discovery (a package that must be
installed, a tool that silently doesn't work, a path that does work) is
written into a "do NOT rediscover these" section — with the story of what
failed and why, not just the fix.

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
When a message carries the standing merge-authorization phrase:
  go-merge — "Go merge" anywhere in the message: sync, name branch, commit, push, PR, merge
When a message says "Update Vendors", or an upstream update is being taken into a repo that vendors a practice layer:
  vendor-update-runbook — "Update Vendors" -- refresh the source clone first; both layers move separately
When a model, study or comparison table rests on an operating constant nobody decided — a margin, a cap, a rate, a floor:
  constants-are-risk-inputs — a constant nobody decided is a swept, registered input -- never doctrine
When a person explicitly asks for a "very deep check" across the whole repo, or after work that invites drift:
  very-deep-check — read every repo in force against itself, pass by pass; never a routine gate
When a person explicitly asks for a full practice audit (or "practice check") across the whole catalogue:
  full-practice-audit — sweep every source's full catalogue, one practice at a time, on request only
When a person says "My options", or asks to have a decision's options laid out:
  my-options — "My options" -- every option, plainer, both sides, then your pick and why
When a person says "Park it" about an open item or a question:
  park-it — "Park it" -- mark the item `parked` now; never raise it unprompted again
When a person says "Plain words":
  plain-words — "Plain words" -- say it as you would out loud; same substance
When a person says "Three Things":
  three-things — "Three Things" -- the three that matter now, one bold phrase and two lines each
When a person says "Weak yes", or agrees in words that carry no conviction:
  weak-yes — "Weak yes" -- do it, and record the approval as `assented`
When a practice lands or a candidate is raised, at any level:
  disclose-landing — state plainly what happened and where — individual, named team, or universal
When a review finds a defect:
  mistakes-become-rules — root-cause the miss, then encode the prevention
When a tool warns about already-published git history:
  no-rewrite-for-warnings — fix the setting forward; never rewrite published history
When adding a file to a directory that already holds files of the same kind:
  filename-separator — one word separator per directory and file kind -- never both - and _
When adding or editing a CI workflow that commits, pushes, or opens a pull request:
  ci-commits-carry-identity — a committing workflow reads a declared identity, or refuses -- never the bot
When adding or re-levelling a heading in any document:
  heading-outline — never jump a heading level; a heading one below its parent, or deeper by one
When adding or re-syncing a document under philosophy/:
  philosophy-declares-its-source — an essay carries its origin on line one -- a record, not a sync pointer
When adding to a file every session loads, or asking what a session pays before it starts work:
  session-load-budget — declare a ceiling for what every session loads; reduce by archiving
When an install step adds something GitHub-specific, or a first install finishes:
  github-setup-disclosed — disclose GitHub setup where its people read; offer owner settings at install
When asked to add, change or remove something in a generated file:
  generated-edit-goes-upstream — change the input the file is built from, never the file -- and say which input
When asking the person to do something in another session:
  handoff-is-pasteable — name the repo, give the exact text to paste, end with the way back
When building a mechanism that makes something discoverable or reachable:
  affordance-is-shared — name who else the mechanism you just built now serves
When building a permutation or configuration-sweep table:
  permutation-frontier-column — one full table with a computed Frontier column
When building a variant of an existing thing:
  variant-re-derives — re-derive what a variant inherits; limits bind, choices do not
When building or committing a generated artifact:
  generated-artifact-provenance — stamp a build code and a manifest; never hand-edit output
When changing a mechanism, a workflow or a behaviour that some document describes:
  change-updates-its-docs — update the document that describes it, in the same commit -- never later
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
When decommissioning a mechanism — a workflow, a tool, a vendored tree, a config — that leaves files behind with no remaining job:
  decommission-deletes-files — delete what the decommissioned mechanism owned; audit first, never on a hunch
When discovering something a session in another window will need:
  findings-return-through-repo — commit it; never leave it for the person to carry to the next window
When exporting a tool across a repo boundary:
  engine-plus-host-shims — one vendored engine, thin host shims, never a fork
When finishing a substantial work-product, before the merge-time capture gate:
  second-pass-capture — a separate capture pass after the work, not inside it
When handing the person work to do, or starting work that may touch a repository this session cannot reach:
  spawn-session — cross-repo check first; hand over a clickable seeded session, not a description
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
When naming or scoping something around a person's skill level:
  technical-describes-people — a skill level describes a person; never a project, repo, file or directory
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
When recording exploratory thinking -- an idea nobody has committed to -- as a document:
  speculation-is-marked — mark it in filename, title, opening block and PR -- four places, or none
When recording that someone approved a practice or a decision, or citing their past approval back to them:
  decision-strength — record `decided` or `assented`; unmarked means unknown, never "you decided this"
When renaming, moving, or deleting a file other files may link to:
  rename-updates-links — renaming a file means repointing every link to it, in the same commit
When reporting a computed total or a negative feasibility result:
  verify-decomposition — check the parts, not the total; never assert an impossibility
When setting up a new repo's session start:
  session-bootstrap — setup lives in a session-start hook, not in memory
When starting an outward-facing deliverable:
  frame-from-audience-question — build it around the audience's question, not your material
When starting work the repository may already cover:
  search-by-purpose — search by purpose and by mechanism before concluding nothing exists
When tracking state that multiple documents need to agree on:
  registry-source-of-truth — state lives in one machine-readable registry; documents derive
When when fixing anything -- a bug, a stale file, a broken environment:
  durable-fix — prefer the fix that survives a fresh container; name a band-aid as one
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
When writing a test, fixture or control that reads or edits state it did not create:
  fixture-owns-its-state — a fixture that inherits real state is testing the environment too
When writing about a person in the third person -- a reply, a document, a commit message, a pull-request body:
  declared-pronouns — use the pronouns a person declares; none declared means they/them, never guess
When writing an outward-facing document:
  readers-vocabulary — use the reader's words; gloss inline or replace
When writing an outward-facing summary of claims:
  outward-summary-discipline — claims-to-source table, honest sums, a recorded adversarial pass
When writing code because a specific practice requires it:
  code-cites-practice — cite the practice's slug in a comment, right where the code is
When writing code that depends on something outside its own control, handling a part that could not run, or deciding how loudly to report one:
  fail-gracefully — keep going, never look complete — match the telling to stake and reader
When writing code that stamps a date or a time into a file, a record or a document:
  timestamps-carry-offset — a stamp carries its offset; never a bare date.today()
When writing or editing a document:
  acronyms-glossary — expand acronyms on first use; keep one central glossary
  doc-references-are-links — reference repo files as relative links; use ≈, never ~
  docs-are-current-state — state what is true now; version control holds the history
  label-describes-content — "one line" must be one line; else name it for its content
When writing or editing a heading in an outward-facing document:
  headline-capitalization — outward-facing headings are New York Times headline case, applied by tool
When writing or editing a practice file:
  practice-links-travel — link only what travels with the file; the rest is an absolute upstream URL
When writing or editing anything under philosophy/, or citing it from a rule:
  philosophy-is-not-repo-policy — philosophy/ is argument; a rule that earned its way out gets written as a practice file
When writing or filling out a pull-request description:
  pr-template-honest-gates — write the body from the diff; an unchecked box is fine
When writing or running a gate, audit or solve that takes more than about a minute:
  slow-steps-report-and-cache — a long step prints elapsed and remaining; a heavy solve caches to disk
When writing or triaging an open item:
  todo-is-a-handoff — queue only for a stated blocked-on/out-of-scope reason — otherwise just do it
When writing or triaging an open item, or deciding whether to raise one in a reply:
  open-item-disposition — an item is raised in chat only if it says `ask`; absent means stay quiet
```

## Standing instruction

Before starting work of a kind named in the occasion index above, run `python3 tools/precedent_show.py SLUG` for each listed slug to load its Rule. When editing a file, `python3 tools/precedent_paths.py FILE` prints any on-demand practice whose `applies_to` matches it, without needing the index at all. At a named moment — merging a branch, reviewing work, before pushing, ending a turn and writing the reply — run `python3 tools/precedent_gate.py merge|review|push|reply`: some practices fire at a moment rather than in a file, and no path glob reaches those. If `.precedent/SESSION_PRACTICES.md` exists, read it too: it carries the practices in force from this repo's team, individual and repo-local sources, which are NOT in this block and bind work here exactly as these do. It is regenerated at session start and is deliberately untracked — never commit it or quote it into a pull request.

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

| Looking for… | Go to |
|---|---|
| The restructuring plan (read this first) | [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) |
| Whether an open item may be raised with Morgan at all, and what "Park it" writes | [practices/open-item-disposition.md](practices/open-item-disposition.md), phrase at [local/practices/park-it.md](local/practices/park-it.md) |
| Inherited practices whose meaning or mechanism changed under Precedent (Alex needs to hear about these) | [CHANGES_TO_TELL_ALEX.md](CHANGES_TO_TELL_ALEX.md) |
| The phase-1 per-practice file format | [spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) |
| Why a practice file's references to `spec/`, `templates/` or a root document are full `https://github.com/...` URLs rather than relative links | [practices/practice-links-travel.md](practices/practice-links-travel.md) — the catalogue is copied into every adopting repo, and a relative link out of `practices/` dies there |
| The phase-2 loader (resident set, replay measurement) | [spec/LOADER.md](spec/LOADER.md) |
| The phase-3 brief (what phase 3 was handed) | [spec/PHASE3_BRIEF.md](spec/PHASE3_BRIEF.md) |
| The phase-3 sources: resolver, precedence, what could not be built here | [spec/SOURCES.md](spec/SOURCES.md) |
| How many practice sets of each level a person or a repo can have — one individual set per person however many teams they are on, as many team sets as a repo declares | [spec/SOURCES.md](spec/SOURCES.md)'s "How many sources of each level" row, reasoning at [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md#one-individual-set-per-person-not-per-team) |
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
| Deleting a file or directory a decommissioned mechanism left behind — the audit that has to pass first, and the record of what went | [practices/decommission-deletes-files.md](practices/decommission-deletes-files.md), audit at [tools/precedent_decommission.py](tools/precedent_decommission.py) |
| Moving an existing, still-wanted practice from one level to another (team ↔ individual, team ↔ team) — distinct from creating one or retiring one outright | [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md) |
| Why the miss rate is what it is, and the plan for it (read before phase 5) | [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md) |
| Who may write what in a project repo, and who may land a practice — Write role plus CODEOWNERS on the protected paths, suggestions through the candidate flow, no technical/non-technical user type at all — drafted, not yet executed, and three GitHub behaviours in it are unverified | [spec/CONTRIBUTOR_ACCESS.md](spec/CONTRIBUTOR_ACCESS.md) |
| Team-level practice capture for document work at scale (a shared editorial team repo + a reusable document-project template — the "alternative to Google Docs" use case) — the template is built and live at [templates/document-project/](templates/document-project/); the pilot itself deliberately still not done, and the team set bootstrapped for it was retired 2026-09-10 unused | [spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md](spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md) |
| The reusable document-project template a future pilot instantiates from | [templates/document-project/](templates/document-project/) |
| What zone a date or time gets stamped in, why an unidentified person's records still carry a real offset, and where the fallback is declared | [practices/timestamps-carry-offset.md](practices/timestamps-carry-offset.md), engine at [tools/precedent_time.py](tools/precedent_time.py) — run it bare to see which rung answered; the value is `fallback_timezone` in [precedent.json](precedent.json) |
| What a session pays before its first turn, the declared ceiling on each always-loaded file, and how to reduce one without deleting what still bites | [practices/session-load-budget.md](practices/session-load-budget.md), registry at [tools/session_load_budgets.json](tools/session_load_budgets.json) — `python3 tools/precedent_check.py --only session-load-budget` |
| Why each practice is routed the way it is (every glob, and every `**`) | [tools/routing_scope.json](tools/routing_scope.json) |
| The routing audit: coverage check + rotating deep read, on-demand, never a routine gate | [practices/routing-audit.md](practices/routing-audit.md), engine at [tools/routing_audit.py](tools/routing_audit.py) |
| The full practice audit: manual, whole-catalogue sweep across every source, on request only | [practices/full-practice-audit.md](practices/full-practice-audit.md), engine at [tools/full_practice_audit.py](tools/full_practice_audit.py) |
| The very deep check: four ordered passes over every repo in force — adopter installs, whether the mechanisms tell the truth, the coherence read, then catalogue and housekeeping — on request only, distinct from the full practice audit above | [practices/very-deep-check.md](practices/very-deep-check.md), engine at [tools/very_deep_check.py](tools/very_deep_check.py), run record at [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md) |
| What each part of the very deep check returned and cost, run after run — and which parts have found nothing and are owed a keep/cheapen/retire answer | [record/very-deep-check-ledger.json](record/very-deep-check-ledger.json), written by [tools/very_deep_check.py](tools/very_deep_check.py) on every run (never hand-edit it); the answers go in [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md) |
| Gaps between what the plan approved and what got built (routing audit's own history, and what else to check) | [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) |
| Whether every declared practice-source repository is still CALLED what this repo calls it — a rename redirects forever, so git never notices | [tools/precedent_source_names.py](tools/precedent_source_names.py), run at [vendor-update-runbook](practices/vendor-update-runbook.md)'s step 8; `UNVERIFIED` is not a pass |
| Whether this session can reach its PRIVATE practice sources at all, and the credential that removes the `add_repo` dance | [tools/precedent_source_credentials.py](tools/precedent_source_credentials.py), setup in [INSTALL.md](INSTALL.md) §8 |
| Whether an attached practice-set source's vendored engine has gone stale, or is missing the session hooks a source is created with, and repairing either | [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py) — reports at session start; `--apply` refreshes and restores hooks, `--commit` commits |
| Why a source clone that is on disk, with the token set, still fails every `git` command inside it with `could not read Username` — and what now repairs it at session start | [tools/precedent_source_credentials.py](tools/precedent_source_credentials.py)'s `persist_credential_helper`, called from [tools/precedent_source_bootstrap.py](tools/precedent_source_bootstrap.py)'s `_try_sync` on every sync and from [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py) for a clone nothing syncs |
| Whether a hook this repo *declares* actually exists on disk and is executable — the failure the harness reports as nothing at all | [tools/precedent_check.py](tools/precedent_check.py) — `--only declared-hooks-exist` |
| Whether this session's SessionStart hooks actually ran, and repairing them if not | [tools/precedent_session_check.py](tools/precedent_session_check.py) — `--apply` runs them by hand |
| Whether `PRECEDENT_FRESHNESS_ALSO` names repositories that are actually there, and what to set it to on this container | [tools/precedent_session_check.py](tools/precedent_session_check.py) — the row prints the corrected value; a dead entry is skipped silently by design, so nothing else reports it |
| Whether Alex has moved `main` since the last carry onto this branch, and what changed | [tools/precedent_upstream_check.py](tools/precedent_upstream_check.py) — printed at session start; the watermark it compares against is [tools/upstream_watermark.json](tools/upstream_watermark.json), moved with `--record` in the carry's own commit |
| Practices that fire at a moment rather than in a file | [tools/precedent_gate.py](tools/precedent_gate.py) — `merge`, `review`, `push`, `reply` |
| Which practices are enforced, and running one check | [tools/precedent_check.py](tools/precedent_check.py) — `--list`, `--explain`, `--only SLUG` |
| The catalogue's own figures (resident size, Rule share, coverage) | [tools/catalogue_stats.py](tools/catalogue_stats.py) — never hand-type these into prose |
| Precedent explained for someone adopting it (not a developer) | [ADOPTING.md](ADOPTING.md) |
| Public-facing pitch and how-to guides, for people outside the project (marketing, a how-to for developers, a how-to for everyone else) | [documentation/](documentation/) |
| What a normal working day looks like once Precedent is installed — the four habits and the standing command vocabulary, for someone who is not a developer | [documentation/HOW_TO_USE_THIS_DAY_TO_DAY.md](documentation/HOW_TO_USE_THIS_DAY_TO_DAY.md) |
| The theory this project is built on — the essays, the brainstorm, the rules being tried in real work, and what is still unsettled. **The only copy; argument, not rules that bind anything here** | [philosophy/](philosophy/), start at [philosophy/README.md](philosophy/README.md) |
| Why every item in a `philosophy/` essay carries a slug, why a citation is answered in the cited item's own prose rather than by a generated list, and what checks that both directions exist — **an experiment, merged 2026-09-11; reverting is a revert** | [philosophy/doc-recipes/backlinks.recipe.md](philosophy/doc-recipes/backlinks.recipe.md), engine at [tools/philosophy_backlinks.py](tools/philosophy_backlinks.py) |
| Why `philosophy/` binds nothing outside itself, and the checks that hold that line | [local/practices/philosophy-is-not-repo-policy.md](local/practices/philosophy-is-not-repo-policy.md), [local/practices/philosophy-declares-its-source.md](local/practices/philosophy-declares-its-source.md) |
| Which practice libraries are in force in this repo | [precedent.json](precedent.json) |
| An example personal practice set | [examples/practice-set/](examples/practice-set/) |
| The private-term blocklist template (copy into your own private set) | [templates/leak-blocklist.txt.template](templates/leak-blocklist.txt.template) |
| The leak gate (push-time; both layers live) | [tools/leak_gate.py](tools/leak_gate.py) — `--explain` for what it does and does not check |
| The editorial section split, as reviewable data | [tools/section_split.json](tools/section_split.json), applied by [tools/resplit_sections.py](tools/resplit_sections.py) |
| The converted practice files (phase 1) | [practices/](practices/) |
| What each practice is and why — **the live catalogue** | [practices/](practices/), indexed by [MAP.md](MAP.md); one rule at a time with `python3 tools/precedent_show.py SLUG` |
| Practices no longer in force, and why each was withdrawn | [MAP.md](MAP.md)'s "Withdrawn practices" table — generated; the files are kept, never deleted |
| The pre-fork single-file catalogue — **superseded, frozen at 53 practices since 2026-08-31**; kept for its prose and its numbering | [PRACTICES.md](PRACTICES.md) |
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
| A brainstormed chat bridge — reaching a Claude session by voice through the app someone already uses, with a private thread per person; who may change content against the repo's own machinery, and why the bot's single credential removes the platform-enforced half of [spec/CONTRIBUTOR_ACCESS.md](spec/CONTRIBUTOR_ACCESS.md)'s two layers. Telegram as the proof of concept, WhatsApp as the destination, with what each platform requires and what it costs. **Speculative: nobody has decided to build it, and no claim in it was read from a primary source** | [spec/SPECULATIVE_WHATSAPP_BRIDGE.md](spec/SPECULATIVE_WHATSAPP_BRIDGE.md) |
| CI checks for shell-less agents (install, require) | [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) |
| Whether anything catches a drifted `MAP.md`, `GLOSSARY.md` or loader block in a practice SET (it does since 2026-09-11 — and `precedent_check.py`'s own provenance check skips itself there, so it never did) | [templates/github-actions/views-drift.yml.template](templates/github-actions/views-drift.yml.template), installed by [tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py); the skip is [TODO.md's `provenance-check-skips-in-a-source-set`](TODO.md#provenance-check-skips-in-a-source-set) |
| Upstream open items / roadmap | [TODO.md](TODO.md) |
| The full text of every gotcha that was shortened or retired — the story behind a live entry, and the settled ones | [record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md) |
| GitAround — the reading view this work spun out | [alex137/GitAround](https://github.com/alex137/GitAround), a separate product since 2026-08-14; a branch here still staging it under proposals/ is superseded, and its documents live there now |
| Slide-deck engine + deck conventions | [deck/](deck/) — engine [build_deck.py](deck/build_deck.py), practice in [deck/README.md](deck/README.md) |
| Portable audits | [tools/](tools/) — [doc_lint.py](tools/doc_lint.py), [practice_audit.py](tools/practice_audit.py), [checkin.py](tools/checkin.py) |
| Skeletons dependent repos instantiate | [templates/](templates/) (+ per-agent adapters in [templates/harness/](templates/harness/)) |

## Build-environment gotchas — do NOT rediscover these

Each entry carries what failed, not only the fix — the fix alone is a fact
you cannot judge, and the next session re-derives it the moment it looks
wrong. [tools/precedent_check.py](tools/precedent_check.py) gates this
section: an entry with no failure attached fails `--only environment-gotchas`.

**This section holds what can still bite you today.** Settled entries are
moved to [record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md), in full,
with the verdict that moved each one — nothing was deleted. (There was a
count here; it named one pass's tally, went stale as later passes archived
more, and told a reader nothing they needed.) **If a
symptom here matches and the short version does not explain it, the whole
story is one link away.** Keep this section for traps, not for history: a
gotcha every session reads is a gotcha every session pays for.

- **`pip install cmarkgfm`, or [tools/doc_lint.py](tools/doc_lint.py)'s
  strikethrough check silently stops running.** Without it the check does not
  fail — it prints a one-line notice and scans for everything else, so a
  document that renders an unintended `<del>` on GitHub passes the gate.
  [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh) installs
  it, but only when `CLAUDE_CODE_REMOTE=true`; a local shell has to do it.

- **A git helper that returns stdout and drops the exit code will hand you a
  confident wrong answer — this is the most-repeated bug in the project.**
  Two shapes, both live:
  `git rev-parse <missing-ref>` exits non-zero but *prints the ref you asked
  for*, so `_git(...'rev-parse', ref) or <fallback>` never falls back — it
  carries the string `origin/precedent-beta-v01` forward as a hash, which
  reached continuous integration once as a 12-char truncation of a ref name.
  And `git show <commit>:<path>` exits 128 with **empty stdout** for two
  unrelated situations — the commit is not in this clone, or the path did not
  exist at that commit — so a caller reading stdout alone answers an
  unanswerable question. That one reported 69 lines of a vendored tree as
  LOST on 2026-09-08, disprovable only by extracting both trees and diffing
  them by hand.
  **Use `rev-parse --verify --quiet`, and consult the return code whenever a
  command can fail for two different reasons.** Found in five separate tools
  so far; the inventory is in the archive. Note the trigger for the first
  shape: a *non-repo* prints nothing, so the plain form looks correct for
  years — it only echoes on an unborn `HEAD` or a missing ref.

  **A third shape, and it defeats the fix this entry recommends:
  `rev-parse --verify --quiet` exits 0 and echoes back ANY well-formed 40-hex
  string, present in the clone or not.** `--verify` checks that the argument
  names a single revision — a full hash always does — never that the object
  exists. Found 2026-09-08 by a negative-control fixture for
  [tools/precedent_upstream_check.py](tools/precedent_upstream_check.py): a
  watermark pointing at 40 zeroes read as *present*, so the guard meant to say
  "that commit is not in this shallow clone" never fired and the notice
  announced a change it could not list. Ask the object database instead —
  `git cat-file -e <sha>^{commit}`. `--verify` remains right for a *name*
  (`origin/main`, `HEAD`), which is what the two shapes above are about.

- **A repository attached mid-session clones single-branch, so every branch
  you create there reads as "unpushed" forever — including to a Stop hook
  that then blocks the turn.** `add_repo` hands you a `git clone --depth 1`
  whose only refspec is `+refs/heads/main:refs/remotes/origin/main`. The push
  genuinely succeeds, but no `origin/<branch>` ref is ever written, so
  `git rev-list origin/<branch>..HEAD` cannot resolve. **Pushing again — the
  honest-looking remedy — changes nothing, because the push was never the
  problem.** A second trap sits on top: `add_repo`'s clone URL is lowercased,
  so GitHub answers `remote: This repository moved`, which reads like the
  cause and is not.
  Confirm with `git ls-remote origin refs/heads/<branch>` — that talks to the
  server and ignores local refs — then repair rather than re-push:
  `git config --unset-all remote.origin.fetch`,
  `git config --add remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'`,
  a bounded `git fetch --depth=50 origin <branch>`, and
  `git branch --set-upstream-to=origin/<branch>`.
  The refspec half self-applies at session start now — but only where the
  hook runs, which is not an attached sibling (see below). The clone-URL
  capitalization half is never automated: nothing local knows the canonical
  spelling, so that stays a manual `git remote set-url`.

- **`git clone` with no `--branch` asks the SERVER which branch to check out,
  and the answer is a setting on a web page that nothing in this repository
  can see.** The remote's `HEAD` symref is whatever the repository's default
  branch is set to, and git follows it silently. 2026-09-09: two
  practice-source repositories had that setting pointed at a feature branch,
  so every session-start clone of those sources landed on an older tree, and a
  plain sync would have written the older text over newer committed text —
  deleting a practice's whole `## Story` block and a clause of its Rule, with
  no warning and exit 0. **The consuming repo had never been stale; the clone
  had been pointed somewhere else** — and `git pull --ff-only` pulls whatever
  branch the checkout is already on, so a clone that landed wrong once stayed
  wrong every session afterwards.
  **The lesson that outlived the fix: when a rule forbids asking a question,
  check whether something else is asking it for you.**
  `precedent_check.py --only declared-base-branch` already failed any tool
  resolving `refs/remotes/origin/HEAD` without reading a DECLARED branch
  first. It reads Python, so it never saw a `git clone` making the same
  inference implicitly, on our behalf.
  Pinned since 2026-09-10:
  [tools/precedent_source_bootstrap.py](tools/precedent_source_bootstrap.py)
  clones with an explicit branch and puts an existing clone back on it before
  pulling — declared `base_branch` if the source declares one, else `main`,
  never the remote's HEAD — and **refuses** rather than moving a clone that is
  on the wrong branch with uncommitted work in it. Full incident: entry 36.

- **A stale checkout is indistinguishable from missing work, and the guard
  cannot save the sessions that most need it.** A session once came up 366
  commits behind and concluded that files which had landed days earlier "did
  not exist"; another had a local branch sharing **zero** commits with origin.
  `git status` says "up to date with origin" in both cases, because it
  compares against a remote-tracking ref nothing has refreshed.
  [.claude/hooks/freshness-guard.sh](.claude/hooks/freshness-guard.sh) now
  **repairs** rather than warns — on a clean tree that is strictly behind it
  fast-forwards, which makes the harness re-read the instruction files —
  and warns only for diverged, no-shared-history and dirty-tree states,
  because a hook that discards work is worse than any stale checkout.
  **What no guard covers, and why this stays here: it does not run for a repo
  attached mid-session, or when the harness rooted the session one directory
  above the repo.** So before concluding anything is missing or unfinished,
  run `git fetch origin <branch>` and
  `git rev-list --count HEAD..origin/<branch>` yourself. Three incidents and
  the guard's full design history are in the archive.

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
  clone. (Used again 2026-09-08 to build the fixture that proves the carry
  check refuses rather than inventing lost content.)

- **A `scope: 'tree'` check in `tools/precedent_check.py` can silently
  report a false *pass* on an under-fetched local clone, not just degrade
  loudly like the two entries above.** `parallel-artifact-ledger` walks
  `git log --no-merges -- <member-dir>` and fails on any commit whose hash
  isn't in `templates/harness/LEDGER.md`. 2026-09-05: a local run reported
  `0 violated`, but GitHub Actions' checkout of the same commit reported a
  real violation twice — the local clone's history simply didn't reach back
  far enough for `git log` to find the commit at all, so **an empty result
  read as "clean," not as "couldn't check."**
  `git fetch --depth=1000 origin <branch>` (or deeper — this check needs the
  *entire* history of the directories it walks) before trusting a clean local
  run of any `scope: 'tree'` check.

- **The leak gate's vocabulary layer fails open unless you also set the git
  config.** `export PRECEDENT_LEAK_BLOCKLIST=<a path OUTSIDE this repo>` is
  half of it; without `git config precedent.requireVocabulary true` a shell
  that starts without the variable prints `PARTIAL`, exits 0, and the push
  goes through with only the structural rules applied. Every push here is
  publication into a public repository, so the half-configured state is the
  dangerous one. See `python3 tools/leak_gate.py --explain`.

- **A bare `python3 tools/leak_gate.py` refuses when a private source
  RESOLVED and no blocklist is set — and allows, loudly, when the private
  sources could not be attached at all.** The distinction is the whole rule
  and it was got wrong once, in both directions, on 2026-09-08.
  First the gate reported PARTIAL and **exit 0** for a session that could
  attach neither private source; it pushed into a public repository with
  only the structural rules applied and reported it afterwards. So the
  requirement was derived from `precedent.json` DECLARING a private source.
  **That refused every session that could not attach one** — a live,
  intermittent condition here — and within the hour it blocked a real
  session out of pushing at all, whose commit then "dies with the
  container": `repo-is-memory` losing outright, in exchange for no safety.
  **The threat model was backwards.** Private vocabulary reaches a session by
  the session READING the private sources' text. A session that could not
  attach them never read a word and has nothing from them to leak; the one
  that DID attach them is the one writing to a public tree with private text
  in context. So **resolution, not declaration, requires the list**.
  Practically: if the sources resolved, export `PRECEDENT_LEAK_BLOCKLIST` —
  you have the repository, so you have the file. If they did not resolve, the
  push goes through and the gate says out loud what it could not cover: a
  private term that reached the session some other way, most plausibly the
  person's own messages. **Say that in the reply.** A caller that only ever
  wants the structural half says so by name with `--structural-only`; CI and
  `verify_harness.py` both pass it, and both call themselves structural.

- **Setting `git config precedent.requireVocabulary true` to satisfy the leak
  gate makes `verify_harness.py` fail two of its own leak-gate checks.** The
  two gates want opposite environments and neither says so, which is why it
  costs an hour every time. Run them separately:
  `python3 tools/leak_gate.py` with `PRECEDENT_LEAK_BLOCKLIST` exported, and
  `env -u PRECEDENT_LEAK_BLOCKLIST python3 tools/verify_harness.py` with the
  git config unset. **Unset the config when you are done** rather than
  leaving it on the clone — a later session running the harness hits this
  again with no idea why.

- **On a shallow clone, `git merge-base` between two *different* branches
  can exit 1 ("no common ancestor") even when the branches genuinely share
  history — and that false negative reads exactly like a destructive
  force-push.** On 2026-09-06 a session nearly asked the user to confirm a
  branch rewrite that had never happened. `git merge-base <A> origin/main`
  and `git merge-base <B> origin/main` each resolved fine meanwhile: the
  shallow fetch simply didn't reach the real common ancestor of `<A>` and
  `<B>`. Exit 1 is not evidence of a rewritten branch — fetch deeper and
  recheck before concluding anything about two branches' relationship.

- **`git log --format=%P` silently reports no parents at all for a commit
  sitting at a shallow clone's boundary, even when it really has two.** A
  `checked_by` script that told merge commits from ordinary ones worked
  perfectly against a full clone, then misclassified the exact boundary
  commit the moment it ran against a fresh `--depth 1` clone of the same
  repo — reproduced directly, not suspected. Git's pretty-printers respect
  the shallow graft; the commit object's own header still records both
  parents. `git cat-file -p <sha>` reads that header and is unaffected —
  count lines starting with `parent ` instead of parsing `%P`.

- **A consuming repo's own mechanical check against materialized
  `tools/checks/`/`practices/` output cannot resolve sources live and trust
  every one it lists.** A repo-local source's check script belongs under that
  source's own declared `path` (`local/tools/checks/`), never directly in the
  consuming repo's `tools/checks/` — that is `precedent_materialize.py`'s
  **output** directory, deleted and rewritten on every sync, so a hand-added
  file there survives until the next one. A dependent repo shipped exactly
  this check resolving sources live; it passed locally, then failed its own
  CI on `main`, flagging every script sourced from its team and individual
  sources. **A team source is a sibling clone outside the repo and an
  individual source resolves via a private user-level config — neither exists
  in a bare CI checkout, so "this source didn't resolve here" is not evidence
  of an orphan.** Attribute by the committed `MANIFEST.json`'s own `checks`
  list instead: a file with no entry there is the real signature of a
  hand-dropped orphan; a recorded file whose source is unreachable is
  skipped, never failed.

- **A repo attached mid-session never runs its own SessionStart hook, so
  every environment guarantee that hook provides is silently absent while you
  work in it.** SessionStart hooks fire for the session's *primary* repo
  only. A sibling attached with `add_repo` is just a directory on disk: its
  hook is never executed, no matter that it is committed, executable and
  correct. 2026-09-06: `verify_harness.py` reported a broken `doc_html.py`
  twice over, and both were the same missing module the hook installs on line
  13. **The failure reads like a broken tool and is an unrun hook**, so the
  reflex to go debug the tool is wasted. `pip install cmarkgfm markdown` by
  hand once per session you work in an attached sibling — the harness went
  from `1 failed` to `0 failed` with no code change. Treat every entry here
  that says "the session-start hook does this" as **not** done when you
  arrived as a sibling.
  **One guarantee has an environment-level route out of this since
  2026-09-11, and only one**: the freshness guard reads
  `PRECEDENT_FRESHNESS_ALSO` (`;`-separated `<path>=<base branch>`), so a
  session can have attached repositories checked even though their own hooks
  never fire — an environment variable follows a session into every
  repository it touches, the same reasoning as `PRECEDENT_COMMIT_*` for
  identity. **Write the path as `~/name`, never spelled out.** An individual
  practice source lives at `$HOME/precedent-individual` and `$HOME` is `/root`
  on some containers and `/home/user` on others, so an absolute path written
  on one names nothing on the next — and a dead entry is skipped rather than
  blocked on, deliberately, so the variable goes on reading as coverage while
  covering nothing. This environment's own entry did exactly that from the day
  it was set until 2026-09-11, naming `/home/user/precedent-individual` while
  the clone sat at `/root/precedent-individual`. The guard expands `~`,
  `$HOME` and `$CLAUDE_PROJECT_DIR` now, so one value is correct everywhere,
  and `python3 tools/precedent_session_check.py` has a row that names any
  entry still resolving to nothing and prints the value to set instead.
  Nothing else in this entry is covered: the `pip install`, the path-trigger
  channel and the rest still need doing by hand.

- **A merge conflict in `.claude/hooks/freshness-guard.sh` locks the session
  out of every tool that could repair it, and `git` being exempt does not
  help.** 2026-09-11: merging `origin/precedent-beta-v01` into a branch that
  had also touched the guard left conflict markers in the live PreToolUse
  hook. Bash aborts on the parse error before reaching either the git
  exemption or the once-per-session sentinel, and exits 2 — which is exactly
  how a PreToolUse hook refuses a call. The matcher is
  `Edit|Write|NotebookEdit|Bash`, so **Edit, Write and Bash were all refused
  at once**, and the guard's own fail-open path does not cover this: it is
  written for "cannot read the payload", not for "will not parse".
  **The way out is a tool the matcher does not name.** `Monitor` runs a
  shell command under a different tool name, so it is not matched:
  `Monitor(command: "cd <repo> && git checkout --ours .claude/hooks/freshness-guard.sh")`
  restored a parseable file and every tool came back. A subagent is NOT a way
  out — it inherits the same project hooks.
  **Prefer avoiding it**: when a merge is going to touch the guard, expect
  this and resolve that file first. Nothing detects it in advance, because
  the hook is fine right up until the merge writes the markers.

- **The session's PRIMARY repo does not run its SessionStart hooks either,
  when the harness rooted the session one directory ABOVE it — and this
  project's own required layout is what causes that.** Four Precedent repos
  side by side under `/home/user` is what a team source needs, since it
  resolves as a sibling clone; the harness then sets the session root to that
  parent, every hook path written as `$CLAUDE_PROJECT_DIR/.claude/hooks/…`
  resolves to nothing, and **a hook whose path does not exist is not an error
  anybody sees.** On 2026-09-08 that silently cost the commit identity, the
  global backstop, the freshness guard, the `pip install`, the path-trigger
  channel — and `.precedent/SESSION_PRACTICES.md`, the only route by which
  private team and individual practices reach a session at all.
  **Do not diagnose this from `env`** — `CLAUDE_PROJECT_DIR` is usually not
  set in a tool shell, so reading it proves nothing either way. Test the
  effects: [tools/precedent_session_check.py](tools/precedent_session_check.py)
  checks each guarantee by what it left behind, and `--apply` runs the three
  hooks by hand. It cannot itself be a hook, for the obvious reason.

- **Your commits are authored by the bot because the harness sets that
  identity in git's GLOBAL config AND in every clone's LOCAL config — so a
  global-only fix is silently overridden.** Measured 2026-09-11:
  `user.name=Claude`, `user.email=noreply@anthropic.com` in `--global` and in
  both clones' `--local`, and no backstop installed to refuse any of it. The
  cause is the entry above — a session rooted one directory up, so
  `commit-identity.sh` never ran — but the SYMPTOM reads as a git-config
  problem, and the config it reads as is one somebody already set on purpose.
  **The cost is that a wrong-author commit cannot be repaired after it
  merges** without rewriting `main`, which is why `fab8d42` and two entries in
  the individual set's `grandfathered_commit_shas` are permanent.
  **The remedy is one line, and it is not `git config`:**
  ```
  bash .claude/hooks/commit-identity.sh
  ```
  It sets the local identity, the GLOBAL one (so a clone attached later
  inherits a person), repoints `/etc/localtime`, and installs the global
  `core.hooksPath` backstop that refuses a bot-authored commit everywhere.
  **`PRECEDENT_COMMIT_NAME`/`_EMAIL`/`_TZ` in the environment is what keeps it
  fixed**, and two things that used to undo it are closed at that cause: a
  harness run repointing the container's own `/etc/localtime`, and the hook's
  fallback rung writing `TZ=America/New_York` into untracked
  `.claude/settings.local.json`, where the harness reads it before hooks run.
  Both are archived in full as entry 33. Verified 2026-09-11 in a scrubbed
  HOME with no private source, no credential and the bot identity preloaded:
  the hook resolved at rung 1 and set the person and the declared offset,
  never reaching the fallback. **Where those variables are absent it still
  bites**, so verify by effect, never by reading the config you just wrote:
  `env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u TZ git var GIT_AUTHOR_IDENT`
  must name the person and the declared offset.
  **The trap that wastes the time is still live.** The harness's own Stop
  hook flags commits whose committer is not `noreply@anthropic.com` and asks
  you to `--amend --reset-author` onto exactly the bot account the individual
  set's own `commit-author` practice refuses and its own mechanical check
  fails on. Neither file is in this repository, which is why neither is linked
  here. Following it recreates the violation this repository spent a day
  fixing. **The repository's gate wins over generic harness guidance**; say so
  and leave the commit alone.

- **The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are
  missing. Resolve the paths its settings.json actually declares — a
  directory listing cannot answer the question.** 2026-09-09: a session read
  "a `.claude/settings.json` and no `.claude/hooks/` directory" as a set whose
  freshness guard and commit-identity backstop had been declared and silently
  off for its whole life. **They had not been.** That set wires four hooks to
  its own tracked `bootstrap/` directory, on purpose, so that one copy exists
  and nothing can drift from it; all four resolve, exist, and are executable.
  The wrong reading was easy because it names a real failure — a hook whose
  path does not exist really is silent, per the two entries above — and the
  two states look identical from a listing.
  **Both halves are mechanical now.**
  `python3 tools/precedent_check.py --only declared-hooks-exist` resolves
  every `$CLAUDE_PROJECT_DIR` hook path a settings.json declares and fails on
  one that is missing or not executable, in any repository the engine is
  vendored into, and
  [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py)
  does the same per attached source and **refuses to "repair" a hook declared
  outside `.claude/hooks/`**. Entry 37.

- **A source set's hooks drift after installation and nothing has ever
  refreshed them — there was an install path and no repair path.** Measured
  2026-09-09 across five real private sets: one carries a `freshness-guard.sh`
  three thousand bytes shorter than canonical, supporting only `session-start`
  and `pre-write` with no user-prompt mode (its settings.json wires no
  `UserPromptSubmit` to match, so it is self-consistent, just older), and
  `commit-identity.sh` is one version behind in **all five**, which is what
  uniform drift looks like when canonical moved on after installation.
  [tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py)
  installs both hooks when a set is created and nothing revisits them; its
  settings.json is also written only `if not settings.exists()`, so
  bootstrapping INTO a directory that already has one — which is what a
  migration is — yields hooks without wiring, or wiring without hooks.
  `python3 tools/precedent_refresh_sources.py --apply` now restores a
  declared-but-missing hook, **independently of engine staleness**, since
  the two go stale independently. Bringing a drifted-but-present hook up to
  canonical is still a person's call, and
  [TODO.md's `source-hook-drift` item](TODO.md#source-hook-drift) holds it.

- **A refusal that names a remedy which cannot work is the moment to ask what
  the guard actually measured, not to disable it.** The freshness guard used
  to refuse the first write of every newly created branch and name
  `git fetch origin <branch>` — impossible against a ref that does not exist —
  so the only way forward a session found was
  `git config precedent.freshness.override true`, which switches freshness
  checking off for that checkout permanently, including the stale-base check
  that catches the single most expensive failure class in this file. Fixed
  2026-09-11 in both copies here:
  `git ls-remote --exit-code --heads origin <branch>` separates "origin has no
  such branch" from "origin could not be reached", and only the branch-absent
  case is waved through, with the base-branch check still running on it. **An
  unreachable origin still blocks, deliberately.** The override is still on
  offer in every block message, which is why the shape above outlived the fix.
  Entries 30 and 35.

- **Something can move this checkout off your working branch mid-session,
  and the cause is NOT known — treat a silently-vanished edit as this before
  you re-derive it.** 2026-09-08, three minutes after a commit, the reflog
  recorded `checkout: moving from claude/deep-review-… to
  precedent-beta-v01` followed by a fast-forward pull. Nobody asked for
  either. The commit survived on the abandoned branch, but twenty minutes of
  edits landed on the wrong one, and **the only symptom was a function that
  had silently stopped existing** — which reads exactly like a bad edit and
  is really a branch switch. `git status` was clean throughout, as it always
  is for a checkout.
  **Three suspects are ruled out by replay rather than reasoning**:
  `precedent_vendor_engine.py seed`, `precedent_refresh_sources.py --apply`
  and `checkin.py fresh` were each run against a throwaway clone on a feature
  branch and none moved `HEAD`. It is also **not** the `checkin.py update`
  incident returning — that one is fixed and verified (archived entry 4).
  Whatever does it is outside this repo's tools; do not assume it is fixed.
  **Detection is the whole remedy available**:
  [tools/precedent_session_check.py](tools/precedent_session_check.py) stamps
  the branch on its first run and compares on every later one. When it fires
  the work is **not lost** — `git reflog` lists the commit, `git checkout`
  returns to it, `git cherry-pick` recovers anything committed after.

- **A `verify_harness.py` fixture that builds an "absent credential"
  scenario inherits the container's real one, and so asserts the opposite of
  what it ran.** Three separate variables have done it —
  `PRECEDENT_GIT_TOKEN`, `PRECEDENT_SOURCE_BASE_URL` and
  `PRECEDENT_FRESHNESS_ALSO` — and the diagnosis fails in the expensive
  direction each time: the failure reads as *missing* access you in fact
  have, or as a guard blocking on a repository the fixture never created.
  **Separate the two by re-running with the variables unset** — failures
  that *disappear* were inheritance, not absence. All three are scrubbed at
  the head of [tools/verify_harness.py](tools/verify_harness.py) now, and
  `check_fixtures_own_the_credential_environment` plants them and asserts
  they come back gone, so this bites only a NEW variable nobody has scrubbed
  yet. **The generalization is the part worth keeping: an ABSENCE is state
  too** — a fixture constructing "nothing is available" owns that absence
  and must clear the environment, not merely decline to set anything
  ([fixture-owns-its-state](practices/fixture-owns-its-state.md)). Full
  story, all three instances, in
  [record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md) entry 32.

- **A harness run that overlaps a write to the tree fails on a change
  belonging to no commit, and the count alone cannot tell you that.**
  `verify_harness.py` reads the tree as it goes, over a hundred-odd checks
  and several minutes. On 2026-09-07 a run came back `1 failed` because a
  negative-control test had briefly planted a failing check into
  `verify_harness.py` **while the run was still in progress**. The failure
  was real, reproducible, and belonged to no commit; two earlier runs and
  four later ones on the identical tree were clean. `1 failed` renders
  identically whether it is self-inflicted, a real flake, or a real bug. Run
  the harness to completion before editing anything it reads, including its
  own controls, and never run two at once. The run recaps every failure by
  name before the summary, so `tail -5` tells these apart.

- **Pointing a fixture's `HOME` at an empty directory does not keep it empty:
  `precedent_resolve.load_config()` CLONES the individual source into it.**
  The self-heal re-runs `.claude/hooks/precedent-individual-bootstrap.sh`
  whenever the individual source looks unusable, so any tool that resolves
  sources -- the leak gate among them -- writes `.config/` and a whole
  `precedent-individual/` clone into whatever `HOME` you handed it, then
  reports that the source RESOLVED. 2026-09-08: a fixture built to reproduce
  "no private source could be attached" turned itself into "a private source
  resolved" mid-run, and the gate's refusal was read as a bug in the gate for
  an hour. **The tell is the fixture home having contents you did not put
  there** -- `ls -a` it after the run, not before. To hold the unresolved
  state, unset `CLAUDE_CODE_REMOTE` as well: the self-heal is deliberately
  narrow and fires only in a hosted session. Same shape as
  [fixture-owns-its-state](practices/fixture-owns-its-state.md), one level
  further out -- the fixture owned its `HOME` and still did not own what the
  code under test would do to it.

- **The individual source resolves to a clone you are probably not editing,
  and it can be many commits stale.** `~/.config/precedent/config.json` names
  an absolute path, and **everything that resolves the individual source at
  runtime reads that one** — not the sibling clone you have been editing.
  It has cost several confusions: a harness fixture failing because it read
  that clone's freshness, a SessionStart hook installing one of two commit
  hooks because the script it executed was the stale copy, and on 2026-09-08
  a materialize that would have written pre-fix test files back into a
  consumer repo. **Check it before concluding a tool is broken:**
  ```
  python3 -c "import json,pathlib;print(json.load(open(pathlib.Path('~/.config/precedent/config.json').expanduser()))['individual']['path'])"
  git -C <that path> fetch && git -C <that path> rev-list --count HEAD..origin/main
  ```
  **The rule that resolves it:** the config-named clone is pulled `--ff-only`
  at every session start, so it can only ever be BEHIND — an attached sibling
  clone beside the repo you are working in is what a session actually edits,
  and is the better evidence of what the source says.
  **A fix that lives outside the repository cannot be recorded inside it as a
  state**, only as a thing to check: `~/.config/precedent/config.json` is
  per-container, so a session that repointed it fixed nothing for the next
  container. Do not read any recorded path here as current — run the command.

- **A sibling clone that was current when you took it can rot while you
  work, and a "these copies do not match" failure will blame the code rather
  than your clone.** 2026-09-07: `verify_harness.py` reported three copies of
  `commit-identity.sh` disagreeing. The check was correct that they differed
  and wrong about what that meant — the attached clone was 2 commits behind,
  and one `git -C <clone> pull --ff-only` made all three agree with no change
  to any file here. **The direction of the mistake is what makes this worth a
  rule**: the failure reads as "this repo's file is wrong", and the obvious
  remedy — copy the clone's older version over the newer one — silently
  reverts somebody's just-landed work. Confirm which side is stale first:
  `git -C <clone> fetch && git -C <clone> rev-list --count HEAD..origin/<branch>`.
  Same reasoning for a check younger than your branch: rule out "never been
  green here" by running it against the untouched tip before fixing it.

  **Second instance, 2026-09-11, where the stale clone was the LEAK GATE's
  blocklist** — and it put a wrong finding in a pull request. The gate
  reported 30 undeclared-repo hits; a session read them as a real defect,
  wrote "red on the base branch too" into its gate block, and filed a TODO
  item for a fix already merged. Its clone of the private set predated a
  repository rename by hours, so it lacked the allowlist line those 30
  references needed. **A correct gate, correct output, stale input —
  indistinguishable from a real failure by construction.** The gate says so
  itself now: on failure it names the blocklist's clone and how far behind
  it is. It never claims a clone is current (an unfetched remote-tracking
  ref cannot prove that) and never fetches, since a gate that reaches the
  network to grade itself can hang on a push. **When a gate whose input
  lives in another repository fails, ask how old the input is before
  believing the finding.**

- **A scratch COPY of this repo, taken to prototype a change without
  touching the working tree, goes stale the moment the freshness guard
  fast-forwards the real checkout under you — and copying the prototyped
  files back reverts every commit that arrived in between, silently.**
  2026-09-11: a session copied the tree to the scratchpad, prototyped a fix
  to `precedent_check.py` there, measured it, and copied the two changed
  files back. In between, the guard had done exactly what it is built to do
  and moved the checkout forward three merges. `git diff` against the copy
  had read clean when the copy was taken, which is the whole trap: it rots
  from the OTHER side, so nothing about the copy looks different afterwards.
  The revert took out another session's refinement of an unrelated check's
  description, and **only [tools/doc_sync.py](tools/doc_sync.py) caught it** —
  `spec/ENFORCEMENT.md`'s generated block regenerated to text OLDER than the
  committed block, which is a shape no other gate here looks for. The
  wholesale-copy-back is the mistake; a prototype copy is still the right
  way to measure. **Re-apply the edits to the CURRENT file** — the same
  patch script, run against `HEAD`'s version, with each `old` string
  asserted to occur exactly once so a moved file fails loudly instead of
  half-applying — **then read `git diff` before committing and confirm every
  hunk is one you meant.** A hunk you did not write is the revert.

- **`HEAD == origin/<branch>` and a clean tree is NOT evidence that your work
  landed — it is the exact reading you get when your commit has been thrown
  away.** 2026-09-07: a session committed on local `precedent-beta-v01`, then
  ran `git checkout -B precedent-beta-v01 origin/precedent-beta-v01`, which
  **silently discarded the commit it had just made**. Its verification printed
  `HEAD=a7e503c beta=a7e503c dirty=0` and read as success: every ref matched,
  nothing was uncommitted, and the change was in neither the tree nor the
  remote. A concurrent session's push made the hashes advance, which made the
  output look *more* convincing.
  **Commit on the working branch, never on the branch you are about to
  reset** — `git checkout -B` is a reset. And **verify the CONTENT, not the
  refs**: `git show origin/<branch>:<file> | grep <a phrase from your change>`,
  grepping for a phrase distinctive to your own edit rather than a common one.
  Recovery: the commit is unreferenced, not gone — `git reflog` lists it and
  `git cherry-pick` restores it.

- **The commit backstop is GLOBAL (`core.hooksPath`), so it reaches throwaway
  fixture repositories too — and refused them.** A repo attached mid-session
  inherits the container's *global* identity (measured:
  `noreply@anthropic.com`), so a per-checkout fix cannot cover it even in
  principle. The cost landed immediately: `verify_harness.py` builds dozens of
  temporary repos and commits in them without `TZ`, and the backstop refused
  the first one, taking the whole run down in a mechanism unrelated to what
  was being tested. **A fixture commit is not a person's commit** — the
  harness sets `PRECEDENT_ALLOW_ANY_AUTHOR=1` for every subprocess it spawns.
  Any other tool that creates scratch repositories needs the same, and the
  symptom will not look like an identity problem.
  `core.hooksPath` also makes git look THERE AND NOWHERE ELSE, so the global
  hooks chain to each repository's own `.git/hooks/<name>` first — without
  that, every repo's own gates vanish silently. Resolve that path with
  `rev-parse --absolute-git-dir`, never `rev-parse --git-path hooks`: the
  latter *respects* `core.hooksPath` and so names the global directory.

- **"no individual source resolved" is not noise — it means every personal
  and team practice is silently absent, and the session will confidently
  apply the wrong rules.** 2026-09-07: a session ran most of a working day
  here with none of the account owner's personal practices loaded.
  `tools/precedent_resolve.py` printed the reason on *every single run*, and
  the session read past it every time as startup chatter — because the checks
  it prefixes all reported `0 violated`, and the line sits directly above the
  summary a session is reading the output *for*.
  The cost is invisible while it happens: the practices that did not load
  included `audience-register`, the owner's standing rule about how replies
  are written, so **every reply that session was pitched by guesswork while a
  rule saying exactly what to do sat unread**. The session's own diagnosis
  each time was "I keep forgetting" — a misdiagnosis, since the rule was
  never in front of it.
  **Stop and fix it before doing anything rule-dependent:** `add_repo` for
  the private sources, then re-run `python3 tools/precedent_resolve.py --repo .`
  and confirm the count names `individual` and `team`, not universal alone.

- **The private practice sets reach a session through the environment
  credential, not through `add_repo`: set `PRECEDENT_GIT_TOKEN` and
  `PRECEDENT_SOURCE_BASE_URL` ([INSTALL.md](INSTALL.md) §8) and the
  SessionStart hook clones them before the first turn, where no ordering rule
  can reach it.** Verified end to end 2026-09-10 on a brand-new container and
  again 2026-09-11: all four sources on disk before the first turn.
  [tools/precedent_resolve.py](tools/precedent_resolve.py) prints `MISSING`
  when no credential is set and `SET` when one is set and a clone still
  failed; the session check and the session-start source report print the same
  line.
  **`add_repo` is the fallback, and what is measured about it does not add
  up.** Three 2026-09-07 measurements had it refusing a cross-owner add in
  BOTH directions — including as a session's very first tool call, so "call it
  before anything else" is not a remedy — while two other sessions held
  repositories from both owners at once and pushed to all of them. Nobody has
  an explanation that fits both, so call it, read what it says, and proceed
  from that; never from a remembered result. The full contradictory sequence
  is entry 34, and the cost of skipping it is the entry above: a session with
  `individual` and `team` unresolved applies the wrong rules all day and
  cannot tell.
  **The live trap is one environment away: an account can hold TWO
  environments with the SAME NAME, and the selector gives you no way to tell
  them apart.** Three sessions across two fresh containers reported
  `env | grep -c PRECEDENT` as **0**, with not one user-defined variable of
  any kind — which reads exactly like "the runner does not pass them
  through", and was not that: `list_environments` showed two environments both
  named `Default`, created 100 ms apart, with the variables set on one and the
  sessions running in the other. **So: give your environments distinct
  names**, and put a throwaway `PRECEDENT_PING=1` beside the token — the ping
  separates "the variables do not arrive" from "the token is wrong", which
  print identically otherwise. An environment change never reaches a session
  already running, so test in a NEW one. The three-day sequence is entry 29.

- **`add_repo` on a PUBLIC repository attaches nothing and never reaches the
  cross-owner check, so testing that wall with `access: "read"` measures
  nothing at all.** Asked on 2026-09-09 for read access to
  `alex137/bestpractice` from a session rooted in a private practice-set
  repository owned by someone else, it answered `"status":"read_available"`
  and *"Nothing was attached to the session"*: the session's git proxy
  already serves anonymous clones of public GitHub repositories, so the
  request short-circuits before any authorization runs. **Read as a success,
  that says the cross-tier refusal above has been lifted. It has not been** —
  the tool's own reply names `access: "push"` as the path that runs the full
  repository-access checks, and warns in the same breath that cross-owner
  attachments may still be refused.
  **The useful half is what it hands you anyway**: a session rooted anywhere,
  under any owner, can `GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1` this
  public repository with nothing attached — which is how a session working in
  a private source set reads the upstream tree. Allow ≈10 minutes and do not
  interrupt the clone. What that checkout cannot do: push, reach the GitHub
  tools (its web application programming interface, and the Model Context
  Protocol server that fronts it), or fetch Git Large File Storage objects.

- **A session you spawn can lose its Model Context Protocol (MCP) tools
  mid-run, and it cannot report
  back to you either — so a spawned session must take the measurement it was
  spawned for in its OPENING turn.** 2026-09-09: a measurement session created
  with `create_session` called `add_repo` successfully as its first tool call,
  and when sent a follow-up minutes later answered that the tool was gone —
  *"the MCP server that provided it was removed from the configuration
  mid-session"* — with a `ToolSearch` for it returning nothing. Nobody
  reconfigured anything. The follow-up measurement was simply lost. The
  second half compounds it: `ListAgents` does not reach a cloud session
  started this way, so `SendMessage` to it fails and **its answers arrive only
  by a person opening its transcript and pasting them back**. Write the whole
  measurement into the spawning prompt; treat any follow-up as a bonus.

- **A private repo name reaches a public tree by nobody having predicted it,
  so repo references are an ALLOWLIST, not a blocklist.** Declare an owner
  private-by-default in the private blocklist file
  (`# visibility-audit: private-owner <account> -- reason`) and every
  `owner/name` mention is refused unless an `allow` line gives a reason. The
  blocklist approach failed in both directions on 2026-09-07: it missed a
  private repository nobody had listed, and blocked two names that had become
  public. **The set of names you may mention is small and known; the set of
  repos you might create is unbounded.**
  **The case that matters and is easy to miss is the URL form** — the
  lookbehind keeping `a/acct/x` from matching also rejects
  `github.com/acct/x`, because the character before the owner is `/` there
  too. A stated test case caught that; reading it did not.
  **And a blocklist entry catches the name somebody typed, never the SHORT
  form of it.** A private repo leaks through what is named AFTER it — a
  practice source, a branch, a directory, a tag, a check — long after the
  repo's own name is gone, under the short name people actually type. The fix
  is truncating each pattern to a distinctive stem, verified at zero hits
  against this tree; the measurement behind each cut is in the archive.
  [tools/very_deep_check.py](tools/very_deep_check.py) does the other half on
  request, asking the GitHub API whether each referenced repo is actually
  private; the push gate cannot, because it must work offline and in CI.

- **A background `sleep` is not a wait, and using one as a wait makes you
  invent elapsed time.** 2026-09-11: a session polling a continuous
  integration job ran `sleep` four times as a BACKGROUND task, then queried
  the API immediately each time — a background task returns a task id at
  once and pauses nothing. It believed roughly thirteen minutes had passed.
  Real elapsed time between its polls was near zero, so every poll returned
  the same `in_progress`, which it read as a hung job.
  **The second half is the expensive one.** It then reported the job as
  hanging "after 18 minutes" — a figure it got by comparing the job's
  `started_at` against a present moment it had never measured. It had not
  run `date` once. The job had in fact finished in 5 seconds, failing
  normally on a pre-existing violation, 26 seconds BEFORE the session merged
  over it; the last poll it acted on returned stale data. The invented
  figure went into a merge commit on `precedent-beta-v01`, where it cannot
  be corrected in place — published history — so the correction lives as a
  comment on the pull request instead.
  **Read the clock before claiming any duration.** `date -u` costs nothing,
  and a timestamp compared against an imagined now is not a measurement —
  it is [no-invented-specifics](practices/no-invented-specifics.md) failing
  in the one place the invention looks like arithmetic. Note also that the
  harness DOES notify when a background task completes; those notifications
  arrived, just after the merge. The mechanism was there and went unused.
  **The symptom impersonates a real failure**, which is why this is worth a
  gotcha rather than a shrug: a stale `in_progress` and a genuinely hung job
  render identically, and "it's been N minutes" is exactly the sentence that
  makes a session stop waiting.

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

- **Reply convention** ([reply-links-files](practices/reply-links-files.md)):
  every reply that created, modified or deleted
  files ends with a **"Files touched"** list — for each file, the branch
  link (readable now) plus the post-merge `main` link, with a one-line
  description. The reader opens the work from the chat; they never go
  hunting for it. **A deleted file is listed too** — its path, why it went,
  and a link to the commit that removed it; a whole decommissioned directory is one
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

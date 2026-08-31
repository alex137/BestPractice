<!-- Last updated: 2026-08-31 17:10:00 (Buenos Aires) by Morgan F, to version 20 -->

# Precedent — Rewrite Plan (Approved)

**Status: APPROVED by Morgan, 2026-08-31. This is the plan of record — build
from it.** Written to be read cold, by a session or a person with no access to
the conversation that produced it. Everything needed to build it is here.

Changes from here on are amendments to an approved plan, not edits to a draft:
state what changed and why, and keep the version header current.

## What This Is

A plan to restructure [BestPractice](https://github.com/alex137/BestPractice)
and [RepoPersonalPreferences](https://github.com/themorgan/RepoPersonalPreferences)
(RPP) into **Precedent**: a single practice engine where practices are stored
as structured data, loaded only when relevant, layered by who they belong to,
and scoped by what they apply to.

Three goals drive everything below.

1. **Stop loading everything every time.** Load only what the task at hand
   needs. The splitting, indexing, and trimming all serve this.
2. **Give decisions and their history an organized home**, out of the working
   task list they currently overwhelm.
3. **Make the protocol build itself as you work** — the system notices what
   should become a practice and proposes it, you approve, and it routes and
   enforces from there. This is the product's core claim; see
   [How a Practice Comes Into Existence](#how-a-practice-comes-into-existence).

Precedent is built **on a branch of BestPractice itself**, not as a fork
(amended 2026-08-31; see [Amendments Since Approval](#amendments-since-approval)).
Alex owns BestPractice and is roughly 80% convinced, so **merge-back is likely
but not assured** — the plan is still built so the work can stand alone if it
has to, which on a branch means being extractable into a fork later rather
than being one already.

## For the Session Implementing This

**Work phase by phase, in order, and do not skip ahead.** The sequence is
deliberate: each phase makes the next cheap, and the reverse order makes each
one expensive. Finish a phase's done-when condition before starting the next.

**Copy this document into Precedent as the first act of phase 0.** It currently
lives in RepoPersonalPreferences, which a session working in Precedent will not
have. Precedent is where it belongs.

**Do not try to hold the whole plan in context while building.** Read the
architecture sections once, then work from the phase you are on. A plan about
loading only what the task needs should be used that way.

**The first action is taking the pending BestPractice update.** Upstream is at
`88ecf7f`; RPP vendors `c76f06f`. Branch from a current base, not a stale one —
divergence from upstream is the top risk in this plan, and starting behind
makes it worse on day one.

**RepoPersonalPreferences is the first migration target, not only a source.**
It stays live and in use throughout; it is the repo whose practices are being
split three ways, and it should be migrated before any other consumer repo,
because it is the one whose failure modes are understood.

## Why — The Diagnosis

### The Bet Is Right; the Growth Undermines It

BestPractice's premise is sound: put accumulated judgment in the repo, load it
into the model, enforce what can be enforced with scripts. The problem is that
**the system has no notion of relevance** — every practice loads for every
task, whether or not it could apply.

This is not a cost complaint. **Past a certain size, adding a practice makes
the model follow the other practices worse.** Attention is finite and
undifferentiated: a commit-trailer convention competes on equal footing with
the practice that actually governs the task. At twenty practices the dilution
is invisible. At fifty, on a task where three apply, the model reads
forty-seven rules that can only distract from the three. **An irrelevant rule
is not neutral — it is noise that degrades the signal from the relevant ones.**

So the architecture has a perverse property: **it punishes the exact behavior
the philosophy asks for.** Every captured lesson taxes every future session
forever, and past some point the tax is paid in adherence, not just tokens.

### The Evidence

Measured on RPP over 2026-08-27 → 2026-08-29:

| Figure | Value |
|---|---|
| Personal-pack rules | 21 → 29 → 46 in three days |
| [AGENTS.md](AGENTS.md) size | 29,443 → 71,059 bytes |
| Always-loaded context | ≈ 17,800 tokens, every session, before any work |
| Full-text copies of each rule | 3, all hand-maintained |
| Rules enforced by a script | 2 of 46 |
| Commits touching the rule file | 38 in the window |
| BestPractice's own catalogue | 51 practices, median 38 lines, longest 118 |
| By-number `practice N` citations | 169, across BestPractice and one consumer |

A deep check on 2026-08-29 found six consistency defects. **Four were the same
failure** — a rule edited in its canonical home and not in the copies the
install procedure creates: commits `1c6fedf`, `cdd18d7`, `b56fc32`, `b52de2e`.
Two shipped as broken references aimed at downstream repos: a vendored rule
citing "merge runbook step 5" when the install procedure never created a step
5, and a harness hook added with its file, manifest entry and wiring all
correct that no install step ever referenced.

Three findings matter more than the defect count:

- **The rules were loaded and were skipped anyway.** Every one of those four
  commits came from a session carrying all 46 rules in context, including the
  rule requiring the mirroring it skipped. **Residency does not produce
  compliance at this size.** The two script-enforced rules were never violated.
- **Five of six were found by throwaway scripts, not by reading.** Every
  existing gate validates the file you touched; every one of these defects is
  a fact about a file you did not touch.
- **BestPractice's own anti-bloat rule was loaded and did not fire.** Practice
  20 carries an explicit proportionality guard — *"Not every slip earns a
  rule… Prefer strengthening an existing rule or audit over minting a new one
  — rule-bloat is itself a failure mode."* It was resident for all 25 rules
  added that weekend. The thesis demonstrating itself.

### Everything Else the Review Turned Up

The full list of problems this rewrite must solve, beyond the headline one.
Each names where the plan addresses it.

| Problem found | Addressed in |
|---|---|
| Decision history has no home; grew to 1,013 of [TODO.md](TODO.md)'s 1,187 lines, and regrew within a day of being condensed | [Where Decisions and History Live](#where-decisions-and-history-live) |
| A change in one place silently implies a change elsewhere, and nothing knows (the four drift commits; the dangling "step 5"; the uninstalled hook) | Generated views, phase 2 |
| Navigation documents ([MAP.md](MAP.md), [GLOSSARY.md](GLOSSARY.md)) hand-maintained and drifting — stale counts, missing files, missing terms | Generated views, phase 2 |
| No gate records that it ran; "considered and found nothing" is indistinguishable from "never asked" | [Gate Receipts](#gate-receipts) |
| Nothing retires a practice; the catalogue cannot shrink | [Lifecycle](#lifecycle--practices-must-be-able-to-die) |
| The anti-bloat guard is prose competing with fifty other prose rules | [The Resident Budget](#the-resident-budget) and [Promotion Criteria](#stage-3--promotion-criteria) |
| No way to note something without promoting it to a resident rule, so everything worth noticing became one — 21 to 46 rules in three days | [The Candidate](#stage-2--the-candidate) |
| Only 2 of 46 practices mechanically enforced; `fail-gracefully` asserted, never tested | Phase 5 |
| [checkin.py](process/upstream/tools/checkin.py) `fresh` is silent on failure, so unreachable reads as "current" | Phase 1 |
| Practices cited by position (169 by-number references), making insertion a cross-repo sweep | Slugs, phase 1 |
| An unresolved drift notice re-stamps its own date every session, so every session inherits a diff it did not create | Phase 1 tooling pass |
| The export path is one-way in practice — RPP has essentially never checked anything in | Phase 7, and the branch's re-sync discipline |

### Why Trimming Is Not the Answer

The tempting conclusion is "it got too big, trim it." **Trimming is a
treadmill.** RPP's decisions log was condensed to one line per entry on
2026-08-28 (`02a24a7`) and had fully regrown within a day, because the
pressure that produced the text had not changed. This plan does the opposite:
**decouple the size of the catalogue from the cost of having it**, so it can
hold hundreds of practices without the resident set moving.

## The Architecture

### Vocabulary (Use These Words)

| Term | Meaning |
|---|---|
| **Practice** | The unit. One file. Replaces both BestPractice's "practice" and RPP's "rule" as the name of the thing. |
| **Rule** | The imperative section *inside* a practice — one to three sentences. Not a synonym for practice. |
| **Source** | Where a practice comes from and who may see it: Precedent, a Team set, or an Individual set. |
| **Precedent** | The public repo: the engine, the checks, and the universal practice catalogue. BestPractice itself, restructured — the work lands on a branch and merges back. |
| **Consumer repo** | Any project that uses practices. |
| **Resolved set** | What a given repo and person actually get after merging their sources. |
| **Resident** | Loaded into every session. The opposite is on-demand. |
| **Vendored copy** | A source's practices copied into a consumer repo and tracked there, rather than fetched live. |
| **Approver** | Whoever must say yes before a practice enters a shared set. Our word, not GitHub's. |

**A vocabulary note, because most users of this will not be writing software.** Approvers are *implemented* with GitHub's `CODEOWNERS` file, which maps path patterns to required reviewers and works on any file type. That is an implementation detail and should stay one: nothing user-facing should say "code owners" to someone who is writing a strategy memo. The same applies to every other borrowed term — say **approver**, **proposal**, **approved**, not *reviewer*, *pull request*, *merged* — following BestPractice practice 34, outward-facing documents use the reader's words.

### The Practice File

One file per practice. Three sections with different lifetimes, plus
frontmatter that is the machine-readable half.

```
practices/document-references-are-links.md

---
slug:        document-references-are-links   # permanent identity; cited by name
title:       Document references are links
tier:        on-demand          # resident | on-demand
severity:    default            # blocking | default | advisory
applies_to:  ["**/*.md"]        # path globs — what this practice covers
occasion:    "writing or editing a document"   # prose trigger where globs cannot express it
checked_by:  tools/checks/doc_links.py         # or null
defines:     ["document reference"]            # terms this practice owns, for the generated glossary
status:      active             # active | superseded | retired
supersedes:  []
overrides:   null               # a lower-source slug this replaces
added:       2026-08-29
approved_by: PR #61
---

## Rule
Three sentences, imperative. The only text ever resident in context.

## Detail
The operational specifics — numbered policy rules, worked procedures,
sub-rules with their own tests. Normative, but not needed to decide
whether the practice applies. Loaded when actually doing the work.

## Why
A paragraph. Loaded when someone opens the practice to question or change it.

## Story
The originating incident, dated. Never loaded. Never trimmed.

## Install
What a dependent repo does about it: template paths, tool names, wiring.
```

`source` is deliberately **not** a field — it is implied by which repo the
file lives in, so it cannot drift from reality.

**Why splitting Rule from Why from Story is the highest-value change:**
BestPractice's median
practice is 38 lines; the instruction inside it is three or four. Splitting
removes roughly nine tenths of the resident text **without deleting a word**,
and gives the incident history a permanent home.

**Amended 2026-08-31, against measurement.** The estimate above was wrong for
this catalogue, and `## Detail` and `## Install` above are the correction.
Phase 1.5's editorial pass ([spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md))
split all 52 practices four ways and `## Rule` came out at **40%** of the
corpus, not a tenth — because a large share of each practice is genuinely
*normative* text that is neither reasoning, nor an incident, nor wiring:
numbered policy rules, worked decision procedures, sub-rules with their own
tests. With nowhere else to go, it stayed in `Rule` and kept `Rule` long
(twenty practices still exceed 150 words). `## Detail` is that home. Splitting
it out is **phase 3 work** — see the Sequence table — because the machinery
that makes it cheap already exists and doing it after consumer repos vendor
the format is an order of magnitude more expensive.

### How an Agent Knows Which Practices to Load

This is the heart of the design, so it is specified as a procedure rather than
a principle. **Nothing here requires the model to decide what is relevant from
a wall of text; each step is either mechanical or a lookup against an index.**

**At session start**, the harness loads one generated file containing exactly
three things:

1. **The resident block** — the full `## Rule` text of every `tier: resident`
   practice in the resolved set. Target ≈2,000 tokens, hard-capped (see
   [The Resident Budget](#the-resident-budget)).
2. **The occasion index** — one line per on-demand practice, grouped by
   occasion. This is the routing table, and it is cheap because each entry is
   a slug plus a clause:

   ```
   When writing or editing a document:
     document-references-are-links — references are links; ≈ not ~
     bold-key-phrases             — bold the key phrases; do not overdo it
     trim-prose                   — trim after any substantial edit
   When merging a branch:
     deep-check      — run the three audits, then the coherence review
     todo-gate       — reconcile TODO.md before pushing
   When adding a practice:
     new-practice-placement — narrowest level first; renumber nothing
   ```

3. **The standing instruction**: *before starting work of a kind named in the
   index, read the practices listed for it.* One sentence, resident.

**During the session**, three further channels fire without the model having
to remember anything:

- **Path-triggered.** A `PreToolUse` hook matches the edited file against
  every practice's `applies_to` globs and prints the matching `## Rule`
  sections. This is what makes document- and folder-scoped practices real, and
  it is the only channel that works even when the model has forgotten the
  index exists.
- **Gate-triggered.** Runbook steps cite slugs; reaching the step loads them.
  A merge loads exactly the merge practices, at the moment of merging.
- **Enforced.** Practices with `checked_by` are never loaded at all. The
  check's failure message *is* the rule, delivered at the moment of violation.

**Worked example.** A session is asked to edit `book/CHAPTER1.md`.

1. Resident block is already in context: ≈12 practices, ~2,000 tokens.
2. The model reads the occasion index line "When writing or editing a
   document" and opens those three practices — ~15 lines each.
3. The `PreToolUse` hook fires on the path, matching
   `book/doc-recipes/CHAPTER1.recipe.md` (a practice with
   `applies_to: ["book/CHAPTER1.md"]`) and prints its Rule.
4. On merge, the gate loads the merge-time practices.
5. Link formatting, header capitalization and date formats are never loaded;
   they are checks that fail if violated.

Total in context: the resident block plus perhaps five practices, instead of
all of them.

#### Loading a Practice Means Loading Its Rule, Not Its File

A practice is one file holding Rule, Why and Story, and **Story is the
largest part**. If a triggered load were an ordinary read of that file, the
whole saving would evaporate at exactly the moment a practice is used — the
agent would pull in the history it will never need in order to reach three
sentences it does.

**So the agent never reads a practice file directly.** It calls a command,
and only the command's output enters context:

```
precedent show doc-references-are-links bold-key-phrases
    → the ## Rule section of each, and nothing else

precedent show doc-references-are-links --why
    → the reasoning, when deciding whether the practice really applies
      or when the user challenges it

precedent show doc-references-are-links --story
    → the originating incident. Archaeology only; almost never called.
```

Three consequences worth stating:

- **One code path.** The occasion index, the path-triggered hook and the gate
  steps all shell out to the same command, so there is no second extractor to
  drift from the first.
- **A fallback for harnesses that cannot run commands.** The build emits a
  rules-only bundle — every Rule, no Why, no Story — as a generated view like
  any other. Less precise than the command, still far smaller than the files.
- **`## Rule` goes first in the file**, so even a naive full read front-loads
  the part that matters.

This also makes the escalation natural rather than special-cased: a session
starts with rules only, and reaches for a Why exactly when it is about to
reason about a practice rather than follow it.

**The failure mode this introduces**, stated plainly because it is the
design's real weak point: **a practice with a wrong or missing trigger is
worse than one buried in a wall of text, because nobody notices its absence.**
Three mitigations. Two are mechanical and one-off: the reachability check
(every on-demand practice must have at least one of `checked_by`, a
narrower-than-`**` `applies_to`, or an `occasion`) and behavioral replay in
the verification harness. The third runs forever, and is described next.

#### The Deep Check Audits Routing, Not Content

Loading less does risk a practice going unapplied, so the periodic deep check
becomes the standing safety net. **But it must not do this by reading every
practice with the whole diff in context** — that is the load-everything
failure moved to a different moment, and a review holding two hundred
practices suffers exactly the dilution this design exists to remove. It would
simply fail less often, because it runs less often.

So the deep check asks a narrower and far cheaper question. **Not "did we
follow every practice?" but "did every practice that should have fired,
fire?"** Three parts:

- **A coverage audit, fully mechanical, every run.** For the work on this
  branch, compute which practices' `applies_to` globs match the changed files,
  and compare that against which practices the session actually loaded.
  Anything that matched by path but was never surfaced is a **routing
  failure** — reported with the practice and the file that should have pulled
  it in. This needs no extra context at all, because it compares two lists.
- **A rotating deep read, not a full sweep.** Each run takes a slice of the
  catalogue — the practices that have fired least recently, and those with no
  `checked_by` — and reads those properly against the actual work. Over
  successive runs the whole catalogue gets covered, without any single run
  drowning in it.
- **Attention spent where checks cannot reach.** A practice with a working
  `checked_by` needs no human-style review: the check either fired or it did
  not. The deep read therefore skips those entirely and spends itself on the
  practices that can only be judged, which is both the smaller set and the
  one that actually needs judgment.

**What the deep check produces is fixes to the routing, not just to the
work.** A practice found applicable-but-unrouted twice is a candidate for a
narrower glob, a better occasion, or — best — a check that makes the question
moot. That feeds the retirement-and-promotion report rather than accumulating
as a list of misses.

**And its honest limit, stated so nobody leans on it too hard:** this is a
detective control, not a preventive one. It finds misses after the fact. The
preventive controls are triggers and checks, and the deep check's real value
is improving *those* — because a system that relies on a big periodic review
pass to catch what it should have enforced is the mechanism that already
demonstrably failed here.

**On the resident budget squeezing out something important:** that is what
`severity` and the hard cap are for together. If a practice must always be
resident and the budget is full, something else has to be demoted, chosen
deliberately rather than by whatever happened to be added last. A practice
pushed out of the resident set should preferably gain a check instead of a
smaller font.

### Source — Who a Practice Belongs To

Three levels. **The repo is public**, which decides the shape.

| Level | Lives in | Visible to | Decided by |
|---|---|---|---|
| **Universal** | Precedent, public | Everyone | Precedent's maintainer, via PR |
| **Team** | One private repo per team | That team | That set's **approvers** — a review *is* the decision |
| **Individual** | One private repo per person | Only that person | The person. No review. |

**Levels are repositories, not directories inside one repository.** The
tempting arrangement is a single repo with `universal/`, `team/` and
`individual/` side by side, and it does not survive contact with a public
Precedent: **individual practices must never be world-readable.** A practice's
level is really a statement about its source, and sources are enforced by repo
boundaries.

**Why one repo per team rather than directories in one private repo.** Git
permissions are per-repo; a directory boundary inside a shared repo is a
convention, not a control. The teams here are mutually unrelated, so a shared
repo would let each team read the others' practices — a defect, not a
tradeoff. One repo per team also gives per-team approvers, per-team
credentials when those arrive, and the ability to retire a team without
touching the rest. It costs more repos and makes cross-team promotion a
cross-repo move; a template repo plus a one-command creation script covers the
friction.

#### Where Today's Practices Go

The migration is a three-way split, and the allocation is decided now rather
than practice by practice later.

| Today | Goes to | Why |
|---|---|---|
| **BestPractice's 51 practices** | **Universal**, in Precedent | They are already public and already the shared baseline. Keeping them where they are requires no decision and imposes nothing new on anyone. |
| **RPP's 46 rules**, by default | **Team** (`precedent-team-maintainers`) | They are one small group's working conventions, not everybody's. Publishing them as universal would impose them on every Precedent user, which is not what they are. |
| **The Morgan-specific handful** | **Individual** (`precedent-individual`) | Commit identity, Buenos Aires timezone, the name in a file header, GitHub attribution, pronouns, the `go`/`merge` shorthand — facts about one person, and RPP already identifies exactly these under its `morgan-scope` rule. |

**Default all of RPP to team even where a practice looks generic.** Several
plainly are — graceful failure, platform-neutral integrations, not stating
counts that drift, linking what you cite. Promote those to universal
individually, with the approval that requires. **The asymmetry is the reason:**
promoting team to universal is a designed path, while demoting a universal
practice means it has already been published and imposed on everyone using
Precedent. Narrowest first, as everywhere else in this plan.

**Two RPP rules should die in the migration rather than move**, which is worth
doing deliberately as the first exercise of the lifecycle:

- `morgan-scope`, a meta-rule declaring which facts are Morgan-specific. **The
  level now says that**, so the rule has nothing left to do.
- `bestpractice-wins`, declaring that the personal layer overrides the generic
  one. **Precedence is a property of the engine now**, not something to write
  down and hope is read.

Both are cases where a written rule existed only because the structure could
not express the thing. That is the retirement path working as intended, and a
useful signal to look for elsewhere in the 46.

#### One Individual Set per Person, Not per Team

**A person has exactly one individual set, however many teams they belong to.**
Three teams means three team repos and still one personal repo. A practice like
*"always write my name in capitals"* is written once and follows its author
into every repo they work in — never copied, never re-approved, never
remembered three times.

**Who declares which sources is therefore split, and this matters for
privacy.** A shared repo may only name the sources everyone in it can read:

- **The consumer repo** declares universal plus its team set, in a tracked
  config file. Everyone working there gets those.
- **The person** declares their own individual set in their *user-level*
  config, outside any shared repo.

If a project repo named someone's individual set, it would leak that set's
existence and location to everyone on the team, and their sessions would try
to fetch a repository they cannot read. So it does not. Two people working in
the same repo resolve **different** sets, each seeing their own personal
practices and neither seeing the other's.

#### What You Actually Open to Do Work — One Repo

**A person making a small change opens exactly one repository: the project
they are working on.** Practice sets are dependencies, not repositories you
attach per session. If using this system meant adding three repos before
touching anything, nobody would use it, and the friction would fall hardest on
the smallest changes — the ones that should be cheapest.

How each source actually arrives:

| Source | How it gets there | Cost at work time |
|---|---|---|
| **Universal** | Vendored into the project repo as tracked files, exactly as BestPractice is vendored today | None — already on disk |
| **Team** | Vendored the same way. Everyone with access to the project can see the team's practices anyway, so there is nothing to protect | None — already on disk |
| **Individual** | A local clone in the person's own environment, named in their user-level config | None — already on disk |

Nothing is fetched from a remote when a session starts. **This is not a new
idea; it is BestPractice's existing vendoring model**, whose whole argument is
that live coupling breaks sessions exactly when orientation matters most. The
background sync workflows keep the vendored copies current, which is machinery
that already exists.

**Two cases worth naming.** A fresh cloud session with no persistent home
directory has no local individual set, so it clones one at bootstrap from the
person's config — a setup step, not a repo the user attaches. And if that
clone fails, the session **degrades gracefully**: it runs on universal plus
team and says plainly that personal practices are missing, rather than
pretending they were applied.

#### Precedence, and the One Case Where the Individual Does Not Win

The engine resolves with **precedence: individual > team > universal** — RPP's
`bestpractice-wins` generalized. A practice may name a lower-source slug in
`overrides:`; the resolver fails loudly if two same-level practices claim one
slug.

**The exception is what `severity: blocking` is for.** Plain precedence would
let a personal *"keep the tone casual"* beat a team's *"this client work is
always formal"*, which is right for how a person works and wrong for what a
shared deliverable looks like. So: **a team or universal practice marked
`blocking` cannot be overridden by a higher-precedence source.** Everything
else, the individual wins. This is the difference between a practice about
*how I work* and a practice about *what we ship*, and marking it is the
team's call at approval time.

### Scope — What a Practice Applies To

**Scope is written as paths, which makes it a trigger a machine can evaluate.**
"Applies only to `CHAPTER1.md`" and "applies when editing a document" are the
same kind of statement; one is simply precise enough to check. So scope is
`applies_to`, a list of globs defaulting to `["**"]` — not a separate
classification a person has to maintain alongside the trigger, but the same
thing said exactly.

- Folder scope and document scope fall out for free.
- **Document recipes stop being a parallel mechanism.** A recipe becomes a
  practice whose `applies_to` is a single file, stored beside that document.
  Same format, loader, and checks — removing a subsystem instead of adding one.
- A glob is checkable; a prose occasion is not. Prefer globs, and keep
  `occasion` for what globs cannot express (merging, installing, releasing).

### Where Decisions and History Live

Three different things are currently jammed into one working list. They
separate cleanly:

| What | Goes to | Loaded? |
|---|---|---|
| Why a practice exists — its originating incident | That practice's `## Story` section | Never |
| A decision that is not about a practice ("the sync merges unattended", "we chose X over Y") | `decisions/<date>-<slug>.md` — one file each, append-only, never pruned | Never |
| Work that is still open | [TODO.md](TODO.md) | Never; it is read, not injected |

**The rule that keeps it that way is mechanical, not aspirational:
[TODO.md](TODO.md) may not contain a `- [x]` item at all.** Closing an item means
moving it — into a practice's Story, into a decision record, or deleting it if
it was trivial. A checked box there fails the check. This is the
smallest rule that would have prevented 1,013 lines of completed decisions
accumulating in a working list, and unlike "condense periodically" it needs no
judgment and cannot regrow.

A decision record carries frontmatter — date, the question, the decision, the
alternatives considered, who decided — so decisions are queryable rather than
prose to be grepped.

### Gate Receipts

Today a session that considered the capture gate and found nothing is
indistinguishable from one that never asked. Each gate emits a receipt into
the merge commit's trailer:

```
Gates: capture=none export=none todo=updated deep-check=passed
```

Cheap, mechanical, and required by the audit on every merge commit. It does
not prove the thinking happened, but it makes **omission visible**, which is
the class of failure that produced every defect in the review.

### The Resident Budget

Practice 20's proportionality guard failed because it was prose competing with
fifty other prose rules. The replacement is structural:

- **The generated resident block has a hard token ceiling.** Exceeding it
  fails the build. Adding a resident practice therefore forces demoting or
  retiring another — the defended core, mechanically defended.
- **Every new practice must declare a reachable channel** or it cannot be
  added at all.
- **A periodic report** lists practices with no `checked_by`, never cited, or
  superseded — the pressure toward enforcement and retirement that nothing
  currently supplies.

### Severity, Not Ranking

Every practice carries `severity: blocking | default | advisory`.

**Deliberately not a global priority ranking.** A total order over fifty-plus
practices cannot be maintained, gets assigned arbitrarily, and drifts silently
— the exact failure this plan exists to fix. What a ranking is wanted for is
conflict resolution, and that is served by source precedence plus three
buckets people can assign correctly. `checked_by` carries the other half of
"how strongly enforced", and is verifiable rather than asserted: a
`checked_by` naming a script with no test for it fails the audit.

### Lifecycle — Practices Must Be Able to Die

The current system has no removal path at all. This one has:

- `status: active | superseded | retired`, with `supersedes: [slug…]` on the
  replacement so provenance survives.
- **Promotion**, the normal life of a good practice: individual → team →
  universal. A file move plus a scrub plus a PR to the higher source.
- **A mechanical promotion signal.** *The same practice restated in a second
  scope was never scope-specific* — RPP's `doc-recipe` rule generalized. Once
  practices are data this is queryable, so the system proposes promotions
  instead of waiting for someone to notice.

## How a Practice Comes Into Existence

This is the product's core claim — *work normally, and the protocol around
that work builds itself* — so it is specified as carefully as the loading
model. **The automation sits at the two ends: the system notices, and the
system enforces. A human approves in the middle.**

That middle step is a feature, not friction. An agent that mints its own
binding rules unsupervised is exactly how RPP reached 46 rules in three days,
and a catalogue nobody vetted is a catalogue nobody trusts.

### Stage 1 — Detection

Three signal sources, where today there is only the first.

**Session judgment at a gate.** The existing capture, export and review gates,
unchanged in spirit — but now they produce a proposal rather than a commit.

**Explicit instruction.** When the user says *"from now on"*, *"always"*,
*"never"*, *"going forward"*, that is the highest-signal moment the system
will ever get, and today it is handled ad hoc. It becomes a first-class
trigger.

**Mechanical signals from the repo**, which is what makes the system feel
automatic rather than diligent:

- the user reverted, rewrote, or corrected work a session produced;
- the same instruction has now appeared in a second session;
- the same check has failed repeatedly, meaning the practice needs a stronger
  channel rather than more prose;
- a review found a defect (BestPractice practice 20's trigger, detected
  instead of remembered);
- a practice has been restated in a second scope, which is the promotion
  signal.

### Stage 2 — The Candidate

**Detection produces a candidate, never a practice.** This is the
load-bearing change, and the likely root cause of the weekend: **the current
system offers no way to note something without promoting it to a resident
rule.** The only moves are "write a full practice" or "do nothing", so
everything worth noticing became a rule.

A candidate is a dated file in `candidates/`: what was observed, the evidence
(commit, quote, failing check), a proposed rule sentence, a proposed level and
channel. **Never loaded into context.** Creating one costs nothing; ignoring
one costs nothing. Candidates expire on their own if never promoted.

### Stage 3 — Promotion Criteria

Where the proportionality guard stops being prose and becomes a gate. A
candidate becomes a practice only if it passes all four:

1. **Recurrence or real cost** — it happened twice, or once expensively.
   Checkable now, because candidates are dated records rather than memories.
2. **Reachability** — a check can be written, a glob can scope it, or an
   occasion names it. **If none of the three, it cannot become an on-demand
   practice**; it either earns a resident slot or stays a candidate.
3. **Non-duplication** — a query across existing practices for overlap. This
   is what lets the system *propose strengthening an existing practice*
   instead of minting a new one — something BestPractice asks for in prose but
   cannot mechanically support.
4. **Budget** — a candidate wanting to be resident must displace something.

### Stage 4 — Approval, by Level

| Level | Who approves | How |
|---|---|---|
| **Individual** | The person | *"Yes, do it"* in the session is the approval. No proposal document, no review, no waiting. Recorded as `approved_by` with a date. |
| **Team** | That set's approvers | The session proposes; an approver says yes. Implemented as a review on the team repo, so the approval *is* the record. |
| **Universal** | Precedent's maintainer | A PR to Precedent. |

**The session always proposes a level with a reason, defaulting to the
narrowest.** Confirming costs one word. Asking on every practice trains the
user to wave it through, which RPP's `rule-scope-ask` already warns about, so
the proposal carries a guess rather than an open question. The test for
genericity is written there: **would this practice's text still make sense
applied to a different document, or in someone else's repo?**

#### Who the Approvers Are, and How They Get That Job

**Approvers are declared in the practice set's own config**, not in a
host-specific file — a short list of people who may say yes to a change in
that set. GitHub's `CODEOWNERS` is then *generated* from that list, the same
way every other view in this system is generated, so there is one source and
the platform enforcement derives from it rather than competing with it.

Declaring them in the set itself buys two things a host file cannot. The
engine can **read** the list, so a session can tell you *"this needs Fabian's
approval"* instead of leaving you to work it out. And the design survives
moving off GitHub, which a `CODEOWNERS` file does not.

- **At creation**, whoever creates a team set is its first approver. No
  ceremony, and there is always at least one.
- **Adding or removing an approver is itself a change to the set**, so it
  needs the current approvers' approval. That is self-hosting and stops
  someone quietly adding themselves.
- **The individual level has no approvers** — the owner is the only one, by
  definition.
- **If a set's only approver becomes unavailable**, the repository's admin can
  reset the list. Worth documenting rather than building around; it is a
  recovery path, not a workflow.

#### How an Approver Finds Out

A proposal nobody sees is a proposal that never happens, and this system
already has a recorded lesson about exactly that: an earlier automation
reported its blockers only as a build-log annotation, which lives inside one
run that nobody opens unless they already know to look. **The fix then was to
report where people already are, and the same rule applies here.**

Three channels, in order of how reliably they land:

- **The proposal itself, where they already get notified.** Requesting an
  approver's review triggers their existing account notifications — email,
  mobile, whatever they already have — with no notification system to build.
- **In-session, when they next work anywhere that uses the set.** *"Three
  practice proposals are waiting for you."* This is the highest-signal
  channel, because they are already in the tool with the context loaded, and
  it is the same mechanism this repo built for drift notices after a
  stdout-only notice lost a priority fight against whatever task was already
  in front of the session.
- **A periodic digest** to the set's approvers, so a proposal that slipped
  past both of the above does not sit forever.

**The proposer is told immediately what happens next** — who must approve, that
the proposal is open, and that they can use the practice at their individual
level meanwhile. Never leave the person who raised it guessing.

**Proposals expire.** One nobody acts on is closed after a set period and the
proposer is told, rather than accumulating into a queue nobody reads — the
same reasoning that makes candidates expire.

**A caveat, tied to an open decision below.** All three channels above assume
an approver comfortable with a code-review notification. Many people using
this will be working on documents rather than software, and for them the
interface likely needs to be an approval requested and given in a session,
with the repo write happening behind it. The channels are right; the surface
may not be.

### Stage 5 — Landing

On approval the practice file is written into the right repo and **every
generated view regenerates** — the resident block, the occasion index, the
catalogue, the map, the glossary. That is the phase-2 machinery doing the work
that four hand-maintained copies do badly today.

One rule held firmly: **a practice claiming `checked_by` is not finished until
that check exists and has a test proving it fires.** Otherwise "we will
enforce it later" is precisely how a catalogue arrives at 44 of 46 unenforced.

#### Landing a Team Practice While Working in a Project — the Round Trip

The common case, spelled out because it crosses a repository boundary and the
wrong instinct here is a well-known trap.

You are working in a project that has your team's practices **vendored** — a
copy of them tracked inside the project. Mid-session you decide something
should become a team practice. The vocabulary for what follows is standard
dependency management:

| Term | Meaning |
|---|---|
| **Vendored copy** | The dependency's files, copied into your project and tracked there |
| **Upstreaming** | Sending your change back to the dependency's own repo, so it becomes part of the real thing. BestPractice's own word for this is *check-in* |
| **Syncing** | Pulling the dependency's newer version down into your vendored copy |
| **Clobbering** | What happens to a change made *only* in the vendored copy: the next sync silently reverts it |

**The rule that follows from that last row: never write a new practice into
the vendored copy.** It appears to work, the practice loads, everything looks
right — and then the next sync overwrites it and the practice is gone with no
error. This is the failure BestPractice already warns about for its own
vendored tree, and it is the single most likely way someone new to this
misuses it.

**So the round trip is:**

1. You say *"make this a team practice."*
2. The session drafts it — Rule, Why, Story, frontmatter — and proposes the
   level with a reason.
3. You approve.
4. **The session writes it to the team's own repo**, on a branch, as a
   proposal — never to the vendored copy in the project you are sitting in.
5. **An approver on that team set says yes**, and it lands on that set's main
   branch. *(If you are the approver, steps 3 to 5 collapse into your one
   "yes" — the session commits it directly. For a small team this is the
   normal case, and there is no waiting at all.)*
6. **Your project's vendored copy picks it up on the next sync**, which the
   background workflow does on a schedule — or immediately, if you ask, so the
   new practice is usable in the session that created it.

**You are never blocked waiting for approval.** If you want the practice in
force right now and someone else has to approve it for the team, put it in
your individual set: it applies to you immediately, with no approval, and
promoting it to the team happens separately. That is the same
narrowest-level-first flow described above, and it means an approval queue
slows down *sharing* a practice, never *using* one.

**If the session cannot reach the team's repo** — no credentials, no network —
it writes the drafted practice to a pending outbox in the project and says so
plainly. It does not write it into the vendored copy as a workaround, because
that is the clobbering trap wearing a helpful face.

### Stage 6 — The Loop Closes

Practices that never fire, are never cited, or whose check never trips become
retirement candidates in the periodic report. This is the half BestPractice
lacks entirely: three creation prompts and no removal prompt at all.

### What "Automatic" Honestly Means Here

Worth stating plainly, because it is the product's promise and it can be
oversold. **The system automatically notices and proposes; you approve; the
system automatically routes and enforces.** It does not write binding rules on
its own, and it should not.

**The strongest automation is at the enforcement end, not the creation end.**
A practice that becomes a script is automatic forever, at full compliance —
directly evidenced here, where the two script-enforced rules were never
violated while the forty-four prose ones were. So the honest and stronger
version of the pitch is *your team's working habits get captured and then
enforced automatically*, rather than *the AI writes your rules*.

## Migration

### Coexistence

`format_version` in the manifest gates which loader runs, so old and new repos
coexist indefinitely and migrate one at a time. Two starting states:
BestPractice-only, and BestPractice+RPP.

### The Converter

Splitting [PRACTICES.md](process/upstream/PRACTICES.md) into per-practice files is mechanical. Splitting each
practice's prose into Rule / Why / Story is a judgment call, so it is
**LLM-assisted and human-reviewed, once per practice**. Guard against content
drift: **no sentence may appear in the output that does not appear in the
input.** The converter may move and drop text, never invent it. Checkable.

### The Verification Harness

For any repo, before and after migration:

- **Slug-set equality** — the same practices are in effect, by slug.
- **Citation integrity** — every existing citation resolves, including the
  169 by-number `practice N` references and every `#slug` anchor already
  committed in dependent repos.
- **Resident subset** — the post-migration resident set is a strict subset of
  the pre-migration always-loaded set. Nothing newly appears in every session.
- **Reachability** — every on-demand practice has at least one of
  `checked_by`, a narrower-than-`**` `applies_to`, or an `occasion`.
- **Byte-identical regeneration** — every generated view regenerates unchanged
  on a clean tree; a hand-edited view fails.
- **Behavioral replay** — take past commits where a practice demonstrably
  applied and assert the loader would have surfaced it. This is what proves
  the loading model works rather than merely type-checks, and it is the test
  that matters most.
- **Leak gate** — no individual- or team-level term appears anywhere in
  Precedent. RPP's `private-repo-scrub` machinery generalized from words to
  sources, hard-failing rather than warning.

## Sequence

| # | Phase | Done when |
|---|---|---|
| 0 | **Decide and set up.** Take the pending BestPractice update (upstream `88ecf7f`; RPP vendors `c76f06f`). Open the Precedent branch. Agree this plan. | The branch exists on a current base and this document is approved or amended. |
| 1 | **Format, converter, harness.** Write the spec and the verification harness; convert Precedent's catalogue; fix the small tooling debts (freshness escalation, drift re-stamp churn). | Practices are files; the catalogue regenerates byte-identically; harness passes. |
| 2 | **Loader and generated views.** Build the loading channels; make [AGENTS.md](AGENTS.md), [MAP.md](MAP.md), [GLOSSARY.md](GLOSSARY.md) and the index generated. **Build the leak gate, pulled forward from phase 3** — see the note under the table. | Resident block within budget; hand-editing a generated view fails a check; the leak gate runs at push time and in CI; **and the premise is measured, not assumed** — see below. |
| 3 | **Split the sources.** Precedent is *already* public (it is BestPractice); Morgan's individual set private; the first team set; the frozen example set. Draft the adopter README. **Write the private-term blocklist into the individual set and point `PRECEDENT_LEAK_BLOCKLIST` at it**, which is what switches the leak gate's vocabulary layer on. **Also split `## Detail` out of `## Rule`** across the catalogue — see the note below the table. | The leak gate's **vocabulary** layer passes (its structural layer already gates every push from phase 2); a consumer repo resolves all three and precedence is tested; `## Rule` is short enough to be worth loading, with the operational specifics in `## Detail`; a README exists that someone outside the project can follow. |
| 4 | **The creation pipeline.** Candidates, detection signals, promotion criteria, approval routing, the periodic retirement report. | A candidate can be raised, promoted and landed end to end; a candidate failing any of the four criteria is refused with a reason. |
| 5 | **Enforcement push.** Convert checkable practices to scripts; drop their prose from the resident tier; test the graceful-failure paths. | `checked_by` coverage materially above 2-of-46; each converted practice has a test proving its check fires. |
| 6 | **Migrate consumer repos**, one at a time, harness-gated. | Each repo passes the harness before its migration lands. |
| 7 | **Merge back to BestPractice.** | A PR is open against `main`, or a deliberate decision to extract the work into a standalone fork instead. |

**Why the leak gate moved from phase 3 to phase 2.** The plan put it at
phase 3 because Precedent was to be a fork, *private initially* — a leak
could be caught and force-pushed away before anyone outside could see it.
[Precedent is now a branch of BestPractice](#amendments-since-approval),
which is public, so **every push is publication, into a repo we do not
own.** There is no grace period and nothing to force-push away. A gate that
first runs when the private sets exist is a gate that arrives after the
exposure it exists to prevent, so it is built now and gates every push from
here on. What phase 3 adds is the *vocabulary* half, described below.

**The gate has two layers, and only one of them can live in this
repository.**

- **Structural**, in [tools/leak_gate.py](tools/leak_gate.py), on from
  phase 2. Precedent holds universal practices and nothing else, so
  anything *shaped* like private-source content fails: an individual- or
  team-level path, a practice claiming a non-universal source, a personal
  email address, an absolute path inside someone's home directory, a
  `candidates/` or `outbox/` directory. These patterns describe shapes
  rather than anyone's words, so they are safe to publish. This layer runs
  in CI ([.github/workflows/leak-gate.yml](.github/workflows/leak-gate.yml)),
  on every branch, where `git push --no-verify` cannot bypass it.
- **Vocabulary**, from phase 3. Catching private *words* — client names,
  code words, internal identifiers — needs a blocklist, and **that list
  cannot live in the repository it protects**: a list of secret terms,
  committed to a public repo, publishes the very terms it guards. So it
  lives in the individual set and `PRECEDENT_LEAK_BLOCKLIST` points at it.
  This is exactly the arrangement practice 15 (`scrub-gate`) already uses —
  blocklist in the private repo, scanning the public vendored tree — and it
  generalizes unchanged.

The consequence, stated plainly rather than left to be discovered: **CI can
only ever run the structural layer**, because CI has no access to a private
list. CI is the unbypassable backstop; the local
[pre-push hook](templates/hooks/pre-push) is the complete check. Neither
alone is the whole gate, and the gate says which layers actually ran rather
than reporting a clean pass it did not earn.

**Why `## Detail` is phase-3 work and not later.** The format now has five
body sections — Rule, Detail, Why, Story, Install — and only the first is
loaded to decide whether a practice applies. Doing the Rule/Detail split at
phase 3 is close to free: the editorial machinery already exists
([tools/resplit_sections.py](tools/resplit_sections.py) plus
[tools/section_split.json](tools/section_split.json)), so the work is one more
pass over a reviewable JSON file rather than 52 hand-edits, and the
content-preservation checks that guard it are already written and adversarially
tested. Doing it *after* phase 6 vendors the format into consumer repos means
migrating every consumer as well. **It is also the only change that actually
delivers this plan's own headline claim**, which measurement has shown the
current four-section split does not.

Two constraints when it happens: `## Rule` must stay loadable on its own —
a session that reads only the Rule must know what to do, not merely that
something applies — and `## Detail` must be reachable from the same
`precedent show` command, not a second one, per
[Loading a Practice Means Loading Its Rule, Not Its File](#loading-a-practice-means-loading-its-rule-not-its-file).

## What Morgan Needs to Do

Only these need a human; everything else a session can do.

**Before phase 0**

- **Review and amend this document.** It is a draft; the shape is the thing to
  react to.
- **Decide the license** for Precedent. **Resolved by the branch decision:**
  the work lives in BestPractice, so BestPractice's own license governs it and
  there is no fork to license separately or attribute across. This only
  reopens if the work is ever extracted into a standalone repo.

**Phase 0 — repository setup** (each is a GitHub click-path or a one-liner a
session can prepare but not execute)

- ~~**Create `Precedent`** as a fork of BestPractice.~~ **Superseded** — the
  work is a branch of BestPractice (`precedent-beta-v01`), not a fork.
- **Create `themorgan/precedent-individual`** — private, Morgan only. **Done.**
- **Create `themorgan/precedent-team-maintainers`** — private; Morgan and Alex
  as collaborators and as the set's **approvers**. **Done.**
- **Confirm the default branch is `main`** on each new repo.

**Naming convention for practice sets**

```
Precedent                              the engine and universal catalogue
<owner>/precedent-individual           one per person, in that person's account
<owner>/precedent-team-<slug>          one per team
```

- **Precedent carries no prefix** — it is the product, not a set. Everything
  else takes `precedent-`, so practice sets cluster together in a repo listing
  and the engine can find them by pattern rather than configuration.
- **Do not repeat the owner in the name.** The account already namespaces it,
  so `themorgan/precedent-individual` is unambiguous and every person's set has
  the same name in their own account, which keeps tooling simple.
- **Name a team for its purpose, never its roster.** A set called
  `precedent-team-morgan-alex` is stale the moment a third person joins, and
  renaming a repo breaks every vendored reference to it. Slugs are lowercase
  and hyphenated.
- **Practice slugs stay unique across all sources**, since precedence resolves
  by slug — a team practice sharing a universal practice's slug reads as a
  deliberate override, which is a feature only when it is intended.

**Once there is a second team, move the team sets into a GitHub organization.**
An org backs approver lists with real GitHub Teams and stops team repos living
in a personal account when the team is not personal. Not worth doing for one
team; worth knowing before there are five.

**Phase 3 — when sources split**

- **Invite people**: Alex to his team's set, Fabian to his, and so on. Each
  team is a separate repo with separate collaborators.
- ~~**Decide whether Precedent goes public**, and when.~~ **Moot** — Precedent
  is a branch of BestPractice, which is public, so every push is publication.
  See the leak-gate consequence under [Risks](#risks).

**Phase 7**

- **Approach Alex** with the merge-back proposal. A separate document already
  exists for this; it argues the architecture rather than the numbers.

**Ongoing, and the one thing only Morgan can do**

- **Answer the level question** when a session proposes a practice's level. It
  is one word most of the time, but it is the judgment the system cannot make.

## Risks

**Divergence from upstream is the top risk, ahead of the restructure itself.**
Upstream moved during the conversation that produced this document. A
long-lived branch of an actively-changing repo, carrying a structural rewrite,
is the standard way a branch becomes unmergeable by accident. Building on a
branch rather than a fork is itself the strongest mitigation — the work is
merge-clean by construction and shares one history with `main` — but it does
not remove the risk, it only makes it visible earlier. The rest still apply:

- Keep universal practice **text** as close to upstream's wording as possible.
  Confine the change to the format and loading layer, so merge-back is a
  format migration, not a content reconciliation.
- Make the change **additive**: new frontmatter, a new loader, new checks.
  Additive is what turns 80% into 100%.
- Keep a **clean seam between engine and catalogue**, so Alex can take one
  without the other.
- Re-sync with upstream on a schedule, not at the end.

**The premise itself is untested, and phase 2 must test it.** This plan has
hard evidence that residency does *not* produce compliance — four defects from
sessions carrying the relevant rule in context. It has **no evidence yet that
trigger-based loading does better.** That is an assumption, not a finding, and
it is the assumption everything else rests on. Phase 2 is not done when the
plumbing works; it is done when the loading model has been measured against
real work — replay past commits where a practice applied and check whether the
loader surfaces it, then compare the miss rate against the old always-loaded
arrangement. **If triggering does not beat residency, the plan needs rethinking
rather than building on**, and that is far cheaper to discover at phase 2 than
at phase 6.

**Personal content leaking into a public repo — and the branch decision made
this sharply worse.** The consequence is permanent and public — hence the
hard-failing leak gate, and individual practices living in a different repo
rather than a different directory.

The original plan bought a margin here that no longer exists: *"Create
`Precedent` as a fork of BestPractice. **Private initially.**"* A private
day-one repo meant the leak gate had a grace period — a leak could be caught
and force-pushed away before anyone outside could see it. **Precedent is now a
branch of a public repo, so there is no grace period: every push is
publication, to a repo whose owner is not us.** Two consequences, both
binding from now on rather than from phase 3:

- **The leak gate must run before every push, not before every merge.** A
  merge-time gate is a gate on the wrong event now.
- **Nothing from an individual or team set may be staged on this branch at
  any point, even transiently.** Phase 3's source split has to build the
  private sets in their own private repos and wire Precedent to *resolve*
  them, never to hold them. The plan already says levels are repositories
  rather than directories; this removes the last excuse for a shortcut.

**The loader silently not firing.** Covered above; the reachability and
behavioral-replay checks exist for exactly this.

**Content drift during conversion.** Mitigated by the no-new-sentences rule.

## Precedent Needs a README for People Adopting It

Everything above is written for the people building this. **Precedent also
needs a README written for someone who has never seen it and wants to use it on
their own project** — that document does not exist yet, and it is a deliverable
of this plan, not an afterthought.

It has to answer, in this order, the questions a newcomer actually has:

- **What is this, and why would I want it?** One paragraph, no internal
  vocabulary.
- **How do I add it to a project I already have?** The common case, and the
  one that must be shortest.
- **How do I set up my own personal practices?** One private repo, named by
  convention, declared in the person's own config — and the reassurance that
  nothing personal ever reaches a shared repo.
- **How do I share practices with a team?** Creating a set, naming approvers,
  and what an approval actually looks like day to day.
- **What happens as I work?** The system proposes, you approve, it enforces.
  This is the part that sells it and the part most likely to be written badly.
- **What does it not do?** Worth stating plainly. It does not write binding
  rules on its own, and the human approval in the middle is deliberate.

**Two constraints on how it is written**, both of which this plan's own
vocabulary violates freely because its audience is different:

- **No term the reader does not already have.** Resident tier, occasion index,
  reachability, routing failure — all internal. A newcomer needs *practice*,
  *rule*, *approver*, and very little else. Anything else is either replaced
  with a plain description or glossed on first use.
- **Assume the reader is not a software developer.** Many people using this
  will be working on documents, arguments and decisions. Examples should not
  all be code, and the setup path should not assume comfort with pull requests
  — which is the same open question as the approval interface below.

**Where it lands in the sequence:** draft it during phase 3, when the sources
actually split and there is something real to describe, and treat it as
blocking for phase 6 — no consumer repo should be migrated on the strength of a
document only its authors can follow. It is also the first thing anyone will
judge when Precedent goes public.

**Write it as prose, not as generated output.** The practice catalogue inside
it can be generated; the explanation cannot.

## Open Decisions

- ~~**License and attribution** for Precedent.~~ **Closed (2026-08-31)** —
  the work is a branch of BestPractice, so BestPractice's own license governs
  it. Reopens only if the work is ever extracted into a standalone repo.
- ~~**When Precedent goes public.**~~ **Closed (2026-08-31)** — it is public
  now. BestPractice is a public repo and Precedent is a branch of it.
- **How a non-developer approves.** The approval flow above assumes a
  team member comfortable with a GitHub review. Many users of this will
  be working on documents and ideas rather than software, and for them
  a pull request is an unfamiliar ritual. The mechanism is right; the
  interface may need to be something else — an approval requested and
  given in a session, with the repo write happening behind it. Worth
  deciding before the first non-technical team is onboarded, not
  before phase 0.

## Amendments Since Approval

The header instruction for this document is that changes after approval are
amendments, stated with what changed and why. The body above is kept as
current state; this section is the short record of what moved.

**2026-08-31 — Precedent is a branch of BestPractice, not a fork.** Decided by
Morgan. The plan was written assuming a fork, private on day one, merged back
at phase 7 if Alex agreed. It is instead `precedent-beta-v01`, a branch of
`alex137/BestPractice`, merging to that repo's own `main`.

What this buys: the top risk in this plan — divergence — is largely
neutralised, because a branch shares one history with `main` and is merge-clean
by construction rather than by discipline. There is no re-sync treadmill and no
content reconciliation at phase 7.

What it costs, and this is the part worth reading twice: **the "private
initially" safety margin is gone.** BestPractice is public, so every push to
this branch is publication, into a repo owned by someone else. The leak gate
moves from a merge-time gate to a push-time one, and no individual- or
team-level content may be staged here even transiently. Recorded in full under
[Risks](#risks).

It also closes two open decisions outright (license, and when Precedent goes
public) and supersedes the phase-0 "create a fork" action.

**2026-08-31 — the practice file gains a fifth body section, `## Detail`,
split out at phase 3.** Decided by Morgan, against phase 1.5's measurement:
`## Rule` came out at 40% of the catalogue rather than the ~10% this plan
predicted, because normative operational detail had no home other than
`Rule`. This amends "The Practice File" and the phase-3 row. It is the second
addition to the plan's original three-section body — `## Install` was the
first, at phase 1 — and both were forced by the same thing: the real
catalogue carries more kinds of content than the illustrative example had
places for.

**2026-08-31 — the leak gate is built at phase 2, not phase 3.** A direct
consequence of the branch decision above: with no "private initially" grace
period, a gate that first runs at phase 3 arrives after the exposure it
exists to prevent. Built as [tools/leak_gate.py](tools/leak_gate.py), gating
every push (a [pre-push hook](templates/hooks/pre-push)) and every branch in
CI. Its structural layer is on now; its vocabulary layer switches on at
phase 3, when there is a private set to keep the blocklist in. Full
reasoning under the [Sequence](#sequence) table.

Running it for the first time found a live instance of the exact
anti-pattern it exists to prevent: the phase-1 leak-gate stand-in hardcoded a
list of private terms — including a personal email address — **inside this
public repo**. Fixed forward, not by rewriting published history (practice
31).

**2026-08-31 — the two private practice-set repos exist.**
`themorgan/precedent-individual` and `themorgan/precedent-team-maintainers`
are created, so phase 3's repository prerequisites are met and only the
content split and the leak gate remain.

### Settled Since Draft v1

- **Name: Precedent.**
- **Ships with an example set** — a one-time frozen copy of Morgan's private
  practices, illustrative only, never updated from the live individual set.
- **Team sets: one repo per team**, for the permissions reason above.
- **A practice belongs to one team**; the multi-team case is speculative and
  deferred.

## Deferred (Speculative — Do Not Build Yet)

- **A practice belonging to more than one team.** Revisit when a real case
  appears.
- **Narrowing an individual practice to particular repos.** An individual set
  applies wherever its owner works, and `applies_to` narrows by path within a
  repo but not across repos. A person wanting a practice in their work
  projects but not their personal ones would need an `in_repos:` filter. No
  real case yet; do not build it speculatively.
- **Per-repo credentials.** Different teams may pay for their own tokens, so
  sync and automation will eventually need per-repo Claude and GitHub
  credentials, failing gracefully and reporting the gap. Real, but not day one.

## Independent of This Plan

Open items from the 2026-08-29 review that this rewrite does not resolve:

- **Header capitalization** in [VOICE.md](VOICE.md),
  [STYLEGUIDE.md](STYLEGUIDE.md) and
  [.github/pull_request_template.md](.github/pull_request_template.md) still
  differs from the repo's stated convention. Needs a decision either way.
- **An allowlist fix is pending export upstream** — the harness template
  allowlists [practice_audit.py](process/upstream/tools/practice_audit.py) with and without arguments but
  [doc_lint.py](process/upstream/tools/doc_lint.py) only with, so the merge runbook's own bare invocation prompts on every run
  in every repo installing the harness.

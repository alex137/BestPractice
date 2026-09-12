<!-- Last updated: 2026-09-12 by the session that landed fix-the-original and widened mistakes-become-rules' occasion -->
<!--record-doc--> This file quotes practice Rules verbatim to say what changed in them, so it names the apparatus doc_lint.py check 6 keeps out of deliverables. It is a record document, not a deliverable.

# Changes to tell Alex

This branch (`precedent-beta-v01`) merges back to `alex137/BestPractice`'s
own `main` (`PRACTICE_ENGINE_PLAN.md`, "Precedent is a branch of BestPractice,
not a fork"). Most of what happens on it is additive — new practices, new
tooling, new documents — and needs no separate call-out; `git log` already
says what was added.

**This file is only for the other kind: a change to what one of Alex's
*pre-fork* practices means or how it works.** Anything that rewrites a
Rule's substance, retires a mechanism the original practice depended on, or
changes what its `checked_by` actually enforces goes here, dated, with the
practice's slug and its original BestPractice number, kept current as this
branch diverges — so the phase-7 merge-back conversation starts from a list
instead of a diff. A practice that is only cross-referenced (a pointer added
to its Install section, nothing about its Rule or enforcement changed) is
noted here too, briefly, for completeness, but is not a behavior change.

**One section at the end is deliberately not that.**
[The merge-back itself has a mechanical trap in it](#not-a-practice-change--the-merge-back-itself-has-a-trap-in-it),
and this file is where the phase-7 conversation starts, so it is recorded
here rather than left to be discovered during the merge.

Almost nothing here is unilateral: nearly everything below is either a
rewrite that keeps the original decision rule intact (marking a superseded
*mechanism*, not a disagreement with the practice), or a fix based on the
base-repo drift this session found for
[Alex's practice 53](#alexs-real-time-additions) below. **The one
exception is the section immediately following**, which retires a practice
outright — a real disagreement with it, made by Morgan, and the first entry
Alex should read.
None of it changes what a plain BestPractice-vendoring consumer repo
(pre-migration) sees — the pre-migration path each affected practice
describes is kept working in every case.

## The Figure the Merge-back Decision Turns On

Before the list: **how much of this catalogue enforces itself.**

<!--gen:merge-back-->
| | |
|---|---|
| Practices in force | 101 |
| **Enforced by a check** | **46 of 101 practices carry a `checked_by`** |
| Advisory only | 55 of 101 practices |
<!--/gen:merge-back-->

**Advisory means a session is told the rule and may still not follow it**, and
this branch measured that rather than assuming it. The plan's own control
carried the *whole* catalogue in every session and still missed 19% of the
practices that applied — `verify-postcondition` was judged applicable twice
and named by that control **zero** times, while resident, in full, in its
context. Both arms of the experiment missed the same practices.

The conclusion drawn there is the one to carry into the merge-back
conversation: **the loader is a cost optimisation, not a compliance
mechanism.** Putting a practice in front of a session does not make the
session apply it, at any catalogue size, through any channel. What actually
changes behaviour is the `checked_by` column — 38 of them.

So the honest framing of what this branch offers is not "84 practices." It is
**38 rules that hold themselves, and 46 that a session may still walk past**,
plus the machinery to move practices from the second group into the first as
each one earns a check. `checkable-gets-checked` is the rule that keeps that
pressure on: a new practice attempts a mechanical check before it is allowed
to stay advisory.

## Retired outright — the strongest change on this branch

### `merge-authorization-keyword` (BestPractice practice 45) — retired 2026-09-07

**What changed.** `status: retired`, `in_force_at: none`, `defines: []`.
The practice is still in the tree with its Rule intact, as a retirement
record; it no longer resolves in force, no longer appears in the occasion
index, and no longer defines a glossary term.

**Why.** Its Rule told every adopting repository to pick one fixed word
meaning "merge as agreed" and document it. That is Morgan's own working
preference — his phrase is "Go merge" — generalized into a universal rule
that nobody else had asked for. Morgan retired it himself on 2026-09-07,
in exactly those terms: the phrase should be personal, and the universal
practice should go. The behaviour it described did not disappear; it moved
down a level, to `go-merge` in his individual set, where a preference
belongs and where it binds only his own work.

**What this costs a consumer repo.** Nothing mechanical: `checked_by` was
already `null`, so no check stops running, and no other practice depended
on it. Two documents that cited it were rewritten in the same commit —
[`practices/merge-runbook.md`](practices/merge-runbook.md)'s Rule now says
authorization is the user saying so *in whatever words they use*, with the
fixed-phrase option demoted to a suggestion for a project's own
instructions file; and this repo's [`AGENTS.md`](AGENTS.md) banner now
states plainly that "Go merge" is Morgan's phrase, defined in a private
set, and that a session which did not load that set must ask rather than
infer the meaning from the banner.

**For the phase-7 conversation.** This is the one entry in this file that
removes a practice rather than adjusting one, so it is the one most worth
Alex disagreeing with. If he wants the universal rule back, restoring it is
a three-field edit to the frontmatter — nothing was deleted.

## Changed mechanism, decision rule kept

### `acronyms-glossary` (BestPractice practice 17) — 2026-09-11

**What changed.** One clause in the Rule. It said a session that uses a term
missing from the glossary "adds it there in the same pass" — *there* meaning
the glossary file. It now says the session adds it **at the glossary's
source** where the glossary is generated, and never by editing the generated
file.

**Why.** In Precedent `GLOSSARY.md` is generated by
[tools/build_views.py](tools/build_views.py) from every practice's `defines:`
frontmatter field, and its own first line reads `do not hand-edit`. This
practice's `applies_to` is `**/*.md`, which matches `GLOSSARY.md` itself, so
`python3 tools/precedent_paths.py GLOSSARY.md` was serving *"add it there"* to
any session about to touch the file — while
[generated-artifact-provenance](practices/generated-artifact-provenance.md)'s
check stood ready to fail the resulting commit. The repository was
instructing the edit it forbids, and the instruction was the one a session
reads first.

**What did not change.** Everything else, including the half that does the
work in a pre-fork BestPractice repo. There the glossary is a hand-maintained
file with no generator, the new clause's condition ("where the glossary is
generated") is simply not met, and the practice behaves exactly as it always
has. The expand-on-first-use half is untouched, and so is
[tools/doc_lint.py](tools/doc_lint.py) check 3, which is what enforces it.

**What came with it**, at universal level:
[generated-edit-goes-upstream](practices/generated-edit-goes-upstream.md) —
a change asked for in a generated file is made in that file's source, never
in the file. Raised by Morgan from the other side of the failure: he had been
asking for glossary additions in exactly those words for months.

### `layered-practice-packs` (BestPractice practice 23) — 2026-09-01

**What changed.** The practice's vendored-pack *implementation* — a separate
tree at `process/<pack>/` with its own manifest, blocklist, and harness
adapter — is marked superseded for any repo running Precedent's loader. A
domain rule is now just a Universal or Team practice scoped with
`applies_to` / `occasion` / `gates`, routed by the same occasion index and
path-triggered channel as everything else; the loader already does the job
the pack's harness adapter existed to do.

**What did not change.** The three-way decision rule the practice opens
with — generic (upstream) / domain (a pack, or now, a scoped practice) /
repo-local (never leaves) — is unchanged and still how a new rule's home is
decided. The pack mechanism itself is kept, described in the practice's
Install section, for a consumer repo that has not yet migrated to the
loader (phase 6).

**What's still open.** The loader does not yet give a domain's rules a home
independent of any one team's roster — the case where several different
teams would all want the same compliance- or lab-workflow bundle, which the
old pack mechanism solved and nothing in the new source model replaces yet.
Tracked as a Deferred item in `PRACTICE_ENGINE_PLAN.md`, merged with the
existing "a practice belonging to more than one team" entry.

See [practices/layered-practice-packs.md](practices/layered-practice-packs.md).

### `layered-practice-packs` (BestPractice practice 23) — 2026-09-03, repo-local formalized

**What changed.** The practice's third tier — repo-local, "rules that live
in that repo's instructions files and never leave" — is now a real fourth
`precedent.json` source the loader itself understands, not just prose a
repo-local rule happened to sit in: a `practices/` directory (declared
with `path: "."` or, per the recommended convention, a subdirectory),
ranked in `PRECEDENCE` between individual and team by default, and subject
to the same `overrides:` and `severity: blocking` mechanics every other
level gets. Found while designing this, and worth naming here even though
it does not touch the three-way decision rule itself: a 2026-09-03
deep-check audit found materializing a self-referential repo-local
source (`path` equal to the sync target) could silently destroy or
corrupt its own hand-authored content across runs — `precedent_materialize.py`
now refuses that combination outright rather than attempting to make it
safe.

**What did not change.** The three-way decision rule itself (generic /
domain / repo-local) is untouched by this — this is the *same* mechanism
upgrade the entry above already logs for the middle (domain) tier,
now landing for the third. A repo-local rule described only in prose
(pre-migration, phase 6 not yet run) still works exactly as before.

**What's still open.** Same gap the entry above names for the domain
tier, now also true of repo-local formalized: nothing yet gives a rule a
home independent of the one repo it was declared for, which was never
repo-local's job to begin with (its whole point is staying scoped to one
repo) — no new gap here, noted only so this entry doesn't read as if it
closed something the one above left open.

See [practices/layered-practice-packs.md](practices/layered-practice-packs.md)
and [spec/SOURCES.md](spec/SOURCES.md).

### `layered-practice-packs` (BestPractice practice 23) — 2026-09-04, repo-local's `path` is now a fixed rule, not a recommendation

**What changed.** The entry above formalized repo-local as a real source
but left its subdirectory placement as a *recommendation*: `path: "."` or a
subdirectory both resolved, with a subdirectory only ever "the better
choice." Raised by a dependent-repo comparison (the project's own prior notes repository has no
repo-local practices at all and so no `local/`; `TodoMorgan` does, at
`local/practices/`, following the recommendation) — the two repos are not
actually inconsistent with each other, but the convention itself was only
ever advisory, so a third repo was always free to pick a different
subdirectory name, or the bare root, and nothing would have refused it.
`tools/precedent_resolve.py`'s `load_config` now requires a repo-local
source's `path` to be exactly `"local"` — refused outright otherwise, with
the reproduced silent-overwrite bug named in the refusal message. This is
the `checkable-gets-checked` treatment: what was prose-only advice is now
a mechanical check, with a firing test in `tools/verify_harness.py`
(`check_source_precedence`'s bare-root and other-subdirectory-name cases).

**What did not change.** `tools/precedent_materialize.py`'s own
level-agnostic `_self_referential_sources` guard (any source, not just
repo-local, whose `path` equals the materialize target) is untouched and
still the backstop for the levels this new rule doesn't reach — universal
self-hosted at `path: "."` (this repo's own `precedent.json`, unaffected)
remains legal. Every existing repo-local declaration already in the wild
(this repo's own `local/`, `TodoMorgan`'s) already used `"local"`, so
nothing that already followed the recommendation needed to change.

See [practices/layered-practice-packs.md](practices/layered-practice-packs.md),
[spec/SOURCES.md](spec/SOURCES.md), and
[PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s "Source" section.

### The phase-4 enforcement rollout — 24 inherited practices gained a real `checked_by` — 2026-09-03, found doing the pre-fork audit

**What changed.** This branch's own scope statement, above, says plainly:
"changes what its `checked_by` actually enforces goes here." Phase 4
(`spec/ENFORCEMENT.md`) converted 24 of your 53 inherited practices from
`checked_by: null` — advisory prose only, compliance depended on a session
noticing and following it — to a real script in `tools/precedent_check.py`.
That never got logged here as its own event: 16 of the 24 are mentioned in
this file only for the unrelated citation-link sweep above, whose own text
("no `checked_by` enforcement changed") is true of *that specific commit*
but left the separate, earlier enforcement commits undisclosed; 8 are
absent from this file entirely. Found auditing the full pre-fork catalogue
against this plan's architecture
([spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md)), not from any one commit's
own review.

**Affected practices (24), full list and verdict:**
[spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md)'s table — every row marked
"gained a real `checked_by`" or an enforcement re-point (that table is the
source of truth for this; not re-listed here). One re-point worth naming
inline since it is the sharpest example of this file's own scope
statement: `doc-references-are-links` (11) already had a `checked_by`
naming `tools/doc_lint.py`; phase 4 moved it to `tools/precedent_check.py`,
which is exactly "changes what its `checked_by` actually enforces."

**What did not change.** Every affected practice's `## Rule` — what it
actually asks a session to do — is unchanged; [spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md)
confirms this practice-by-practice, not just asserted. This is purely
*how* compliance is checked, never *what* is being asked.

### The phase-2 resident-tier promotion — 6 inherited practices are now always loaded — 2026-09-03, found doing the pre-fork audit

**What changed.** BestPractice pre-fork had no `tier` concept at all — every
practice was equally prose, consulted the same way. Phase 2 introduced
`tier: resident` (always loaded into every session, via `AGENTS.md`'s
generated block) versus `tier: on-demand` (reached only through the
occasion index, a path glob, or a check). Six of your inherited practices
are now resident — the same six [spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md)'s
table marks "Promoted resident." This is the architecture's own headline move
([PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md), "The Resident
Budget") and none of these six practices' own files log it — the same gap
the entry above names for enforcement, for a different mechanism.

**What did not change.** Same as above — the Rule text of all six is
untouched; only where and how often a session sees it changed.

### `session-bootstrap` (BestPractice practice 13) — 2026-09-05

**What changed.** `## Detail` and `## Story` were both empty in this
practice since phase 1 (Story, like every practice's, was never
populated at conversion; Detail simply had nothing to hold once added at
phase 3). Both are now populated, for real: Detail states the specific,
stronger case where a session-start hook depends on the session's own
still-forming git access (a privately-scoped individual or team source
whose clone needs `add_repo` access the agent grants itself, in its own
turn, which a `SessionStart` hook — running before that turn starts —
cannot wait for), and Story records the incident that surfaced it: two
independent Precedent adopters' individual-source bootstrap hook ran
before the agent's own `add_repo` call could possibly have fired, degraded
on purpose, and then silently never re-ran. **The fix, and a same-day
correction to it (2026-09-06):** the first fix shipped a bounded retry in
[`tools/precedent_source_bootstrap.py`](tools/precedent_source_bootstrap.py)
alongside a lazy self-heal in
[`tools/precedent_resolve.py`](tools/precedent_resolve.py)'s
`load_config()`, framed as two contributing halves. A follow-up testing
session proved the retry half inert by direct test: a `SessionStart` hook
runs entirely to completion before the agent's own turn starts, so no
retry count or delay inside the hook can ever observe `add_repo` access
appearing — only the lazy self-heal, which runs later from inside the
agent's own turn, actually closes the gap. Corrected the same day: the
tool now defaults to a single attempt, and every document (this one
included) that stated the retry as a real, contributing fix has been
rewritten. New engine work this branch's own phase structure never
covered either way, not a change to anything pre-fork.

**What did not change.** `## Rule` — "environment setup... lives in a
session-start hook... warning loudly on failure" — is untouched,
byte-for-byte, and so is what `checked_by: `[`tools/precedent_check.py`](tools/precedent_check.py)'s
`session-bootstrap` check actually enforces (still: a named setup command
has a real hook running it). This is Detail elaborating a harder case of
the same Rule, not a new decision. Logged here rather than left silent
because it moves a phase-3 catalogue figure
([`spec/PRACTICE_FORMAT.md`](spec/PRACTICE_FORMAT.md)'s "carries a
Detail" count, 15 → 16) and because this file's own
`_amended_and_logged` mechanism ([`tools/verify_harness.py`](tools/verify_harness.py))
needs this slug named here to keep exempting it from the fidelity checks
honestly —
it already was, from the unrelated 2026-09-01 slug-link sweep below, but
that entry doesn't disclose *this* change, so it needed its own.

### `merge-authorization-keyword` (BestPractice practice 45) — 2026-09-06

**Superseded by the retirement above, 2026-09-07.** Kept because it records
what the practice said while it was in force, which is what makes the
retirement legible.

**What changed.** `## Detail` and `## Story` were both empty in this
practice since phase 1 — it describes a mechanism a repo *can* adopt, but
this repo had never actually adopted a specific word for it. Both are now
populated: Detail names this repo's adopted phrase, "Go merge"
(case-insensitive), and states concretely what saying it authorizes here
(commit and push the thread's agreed change to `precedent-beta-v01`, after
the usual checks); Story records the incident that prompted formalizing
it — Morgan closed two consecutive messages with "Go merge" before the
keyword existed as a documented rule. The generic Rule text — one fixed
word, said standing alone, means "merge as agreed," documented in
`GLOSSARY.md` — is untouched; this only exercises the practice's own
`## Install` step for the first time in this repo.

**Same-day addition (2026-09-06):** Detail now also requires that "Go
merge" isn't treated as fulfilled by the push command reporting success —
the session must fetch the target branch afterward and confirm local
`HEAD` and `origin/precedent-beta-v01` actually resolve to the same
commit ([`verify-postcondition`](practices/verify-postcondition.md)),
prompted by Morgan asking whether the keyword should require that, not by
anything having gone wrong. Cross-linked from `AGENTS.md`'s merge-keyword
paragraph too.

**What did not change.** `## Rule` is untouched, byte-for-byte, and
`checked_by` is still `null` — this practice has no mechanical check, by
design (see its own `## Rule`: an ambiguous case is treated as *not*
authorization, which is a human judgment call, not something a script can
verify). Logged here rather than left silent because it moves a phase-3
catalogue figure ([`spec/PRACTICE_FORMAT.md`](spec/PRACTICE_FORMAT.md)'s
"carries a Detail" count, 16 → 17) and because this file's own
`_amended_and_logged` mechanism ([`tools/verify_harness.py`](tools/verify_harness.py))
needs this slug named here to keep exempting it from the fidelity checks
honestly — it already was, from the unrelated 2026-09-01 slug-link sweep
below, but that entry doesn't disclose *this* change, so it needed its
own, same reasoning as the `session-bootstrap` entry above.

### `two-check-levels` (BestPractice practice 44) — 2026-09-06

**What changed.** Two things, neither touching the Rule. `defines:` was
`[]` and is now `["light check", "deep check"]`, so both terms land in the
generated [GLOSSARY.md](GLOSSARY.md) — the practice's own Install step has
always said to put the chosen pair in the repo's glossary, and this repo
had adopted the pair in `AGENTS.md` without ever registering it, which
[`very-deep-check`](practices/very-deep-check.md)'s pass 3 names as a
defect in its own right (a trigger word reachable only by already knowing
it). And the Install section's closing sentence, which told a repo to fold
extra checks into the "light" name "rather than inventing a third level —
two named levels is the right number for almost every repo," now says third
*gate* and adds a paragraph drawing the line: what gates a commit, push or
merge must fold into one of the two names; a rare audit a person asks for
by name, that no gate ever waits on, is a separate mechanism.

**Why it needed saying.** This branch built exactly such a mechanism —
[`very-deep-check`](practices/very-deep-check.md), four ordered passes over
every repo in force, by its own Rule "never wired into a commit, push, or
merge gate" — and left practice 44 asserting that a third level should not
exist. The two are compatible on the substance and were not on the page,
which is the kind of contradiction the same practice's pass 3 exists to
catch.

**What did not change.** The Rule is untouched, byte-for-byte: two named
levels, fixed and distinct, named in the repo's own glossary. The
decision rule for a *gate* is unchanged and is now stated more sharply
than before, not relaxed. `checked_by` still points at the same check in
[`tools/precedent_check.py`](tools/precedent_check.py), unchanged.

### `deliverables-look-like-output` (BestPractice practice 49) — 2026-09-06

**What changed.** The Rule routed every kind of apparatus — claims-to-source
table, verification log, decision provenance, retirement lore, open
verify-later items — into a single **paired record document**
(`*_record.md`). It now adds that where a repo gives one of those kinds its
own home, that home wins: under Precedent a decision that is not about a
practice goes to a dated file in `decisions/`, and a practice's own
originating incident goes to its `## Story`. Detail item 3 gains the same
alternative. [`tools/doc_lint.py`](tools/doc_lint.py)'s check 6 follows: a
`decisions/` directory is now record-class (it was being linted as a
deliverable, and so flagged for containing its own subject matter), and a
deliverable's one allowed reference now includes a link to a dated decision
record, not only to a `_record.md`/`_diligence.md`-suffixed one.

**Why it needed saying.** The plan's "Where Decisions and History Live"
gave decision provenance a home this practice predates, and this repo has
been writing real records into `decisions/` since 2026-08-31 while the
practice still said they belong in a paired record doc. The lint half was
a latent gate failure, reproduced before fixing: a deliverable that
correctly linked its decision record instead of restating the decision
failed the gate for doing the right thing.

**What did not change.** The decision rule is intact and is the whole point
of the practice: apparatus does not travel with the deliverable, a
verify-later flag means verify now, and a cited decision names its decider
and date. Only *which* file it lands in gained an alternative. The check's
own patterns are untouched — verified still firing on an unattributed "user
decision" with no record link, and still not exempting an ordinary document
link.

### `reply-links-files` (BestPractice practice 12) — 2026-09-07

**What changed.** The Rule's trigger clause enumerated two verbs — *"a reply
that created or modified files"* — and now reads *"created, modified or
deleted"*, with one added obligation: a deleted file is listed too, with its
path, why it went, and a link to the commit that removed it rather than a
branch link, which would 404. `## Detail` carries the mechanics (a whole
retired directory is one entry, not one line per file). Nothing else moved:
`title`, `tier`, `gates`, `severity`, `checked_by` (still `null` — this one
fires at the `reply` gate and has never had a mechanical check) and the
two-link requirement for files that still exist are untouched.

**Why it needed saying.** The addition is small but it is a real obligation
the original did not carry, so a session that deleted a directory and said
nothing satisfied the old Rule completely. That was harmless while deleting
was rare; [decommission-deletes-files](practices/decommission-deletes-files.md),
landed the same day at Morgan's request, makes it routine. The asymmetry is
the argument: a created or modified file announces itself in the tree, so a
reader browsing the branch trips over it either way, while a deleted one
leaves nothing behind to trip over and the reply is the only place it is
visible at all.

**What did not change.** The decision rule, which the practice states in its
own Rule and which this serves rather than revises: *the reader must be able
to open the work from the chat, not merely learn it exists.* A deleted file
is a third case brought under it, not a new principle. A pre-migration
consumer sees the same widened convention and nothing breaks — it asks for
one more line in a reply, needs no tool, config or vendored file, and both
[templates/AGENTS.md.template](templates/AGENTS.md.template) and
[templates/AGENTS.md.loader.template](templates/AGENTS.md.loader.template)
carry it for the classic and loader layouts.

### `mistakes-become-rules` (BestPractice practice 20) — 2026-09-12

**What changed.** When it fires. The occasion was `"a review finds a
defect"`; it is now `"a defect is fixed -- whether a review found it, the
person reported it, or the session hit it itself"`, with a matching clause
added to the Rule's opening sentence.

**Why.** Morgan's complaint, 2026-09-12: the root-cause step keeps not
happening, and he has to ask for it by hand. The cause turned out to be the
trigger rather than the rule — **most defects in this repository are never
reviewed.** They are mentioned in a message and repaired in the next turn, so
a practice keyed to reviews sat in the occasion index and never fired on the
majority of the cases it was written for. The Rule's substance is untouched:
same five-whys, same rung ladder (audit / dated rule / export), same
proportionality guard.

**What did not change.** The decision rule, the `checked_by`, the gates
(still `review`), and every word about *what* to do once it fires. A pre-fork
BestPractice repo reading this practice gets the same instruction it always
did, on strictly more occasions.

**Landed alongside** a new universal practice,
[fix-the-original](practices/fix-the-original.md), which handles the other
half of the same complaint — propagating a fix back to the template or
upstream copy it came from. That one is new on this branch and additive, so
it needs no entry here beyond this pointer.

## Content added to practices, not just re-linked

### Story backfill across the catalogue — 2026-09-07

**What changed.** 30 of the 65 practices carried an empty `## Story`, and one
of them — [reply-links-files](practices/reply-links-files.md) — carried an
empty `## Why` as well. All are now written. **No Rule, Detail, Why (except
that one), `checked_by`, `severity` or `status` changed**: this is added
provenance only, in the section the format already reserved for it.

**Why they were empty, which is not the obvious reason.**
[split_practices.py](tools/split_practices.py) declines to populate `## Story`
deliberately and documents why in its own docstring: separating the incident
from the reasoning is editorial judgment, and doing it unreviewed for a whole
catalogue in one pass risked mischaracterizing exactly the content the
conversion existed to preserve faithfully. It left the section present and
empty as a **declared** gap. The converter did the right thing; nothing ever
came back for the gap.

It survived here for a specific mechanical reason worth knowing:
[cite-the-incident](practices/cite-the-incident.md)'s check fires on
authorship of a *changed* Rule, and a Story that was empty from the beginning
is never a change. Its own practice file was among the 30.

**Where the text came from.** Each Story is written from what this repo
already recorded — the practice's own `## Why`, the spec documents, the
decision records. Several are real incidents that were already in the prose
and simply not separated out: the parking-lot document that lost staged
content for a full cycle; the comparison table that lagged its scripts until
the repo owner asked; the three audits that each exist because a written
convention was broken once; the day spent patching three forked tools before
they were collapsed to shims.

**Where no incident existed, the Story says so** rather than inventing one.
Roughly half are this kind. That distinction is deliberate and load-bearing:
an empty section is a visible gap, and a fabricated incident is a false
record that gets trusted.

**A new practice came with it**, at universal level:
[catalogue-carries-stories](practices/catalogue-carries-stories.md), enforced
by a tree-scoped check in
[tools/precedent_check.py](tools/precedent_check.py). It asserts that every
`status: active` practice carries a non-empty Story, across the whole
catalogue rather than only across changed files — which is what makes a bulk
landing (a migration, an import) unable to pass it, and a gap left behind
unable to go quiet later.

**Fidelity checks.** Every affected slug is registered in
`AMENDED_POST_CONVERSION`, so the word-multiset and sentence-preservation
checks against `PRACTICES.md` still run against everything else. A Story is by
definition text the frozen original does not contain.

Most of the 30 were already registered there for the earlier citation and
link sweeps. The slugs newly registered by this change are
[cite-the-incident](practices/cite-the-incident.md),
[no-version-suffix](practices/no-version-suffix.md), and — for the scrub
below rather than for a Story —
[migration-scrubs-vocabulary](practices/migration-scrubs-vocabulary.md).

### Why backfill: nine practices that stated a rule with no separate rationale — 2026-09-07

**What changed.** Nine practices carried an empty `## Why`:
`docs-are-current-state`, `environment-gotchas`,
`generated-artifact-provenance`, `label-describes-content`,
`layered-practice-packs`, `lead-with-what-it-is`, `merge-runbook`,
`one-formatter-per-quantity`, `parallel-artifact-ledger`. All are now
written. **No Rule, Detail, Story, `checked_by`, `severity` or `status`
changed.**

**This is a different gap from the Story backfill above, and the difference
matters.** Those 30 were missing their *incident*. These nine already had a
real, specific `## Story` — the incident was recorded all along. What they
lacked was the *reasoning*, because their source practice in `PRACTICES.md`
never had a paragraph opening with a `**Why.**` label, and
[split_practices.py](tools/split_practices.py)'s carry-forward walk routes
by label. Nothing was lost in conversion; there was nothing there to carry.

**So this text is derived, not recovered**, and that is worth stating plainly
because it is the one place in either backfill where new argument is being
written rather than transcribed. Each `## Why` is reasoned from that
practice's own Rule and Story — why the rule takes the shape it does, and why
the obvious alternative fails — and says nothing the practice did not already
imply. It is invented relative to `PRACTICES.md`, hence the
`AMENDED_POST_CONVERSION` entries; seven of the nine were already listed
there for earlier sweeps.

**An earlier guess about these was wrong and is corrected here.** When they
were first filed as an open item, the note supposed `## Why` was reasoning the
converter *did* carry across, so an empty one probably meant the source stated
a rule with no rationale. Reading the nine showed the second half right and
the first half beside the point: the reasoning is in their Rule and Story, and
the empty section is a labelling artifact rather than a loss.

### A private repo name was scrubbed from this tree — 2026-09-07

**What changed.** 19 occurrences of a private repository's name, across
`README.md`-adjacent documents, `AGENTS.md`, `INSTALL.md`, four spec
documents, five tools and two practice files, replaced with general
descriptions ("a private consumer repo") that keep every incident intact.

**Why.** This repo is public, and that repo is private, so its name here was
a real disclosure. Found by pointing the leak gate's private vocabulary half
at this tree for the first time — the layer existed and had never been run
with a real blocklist.

**What was deliberately NOT scrubbed**, and this is the more useful half:
the other 33 hits were all one name, the project's own prior notes repository, which was checked and
**is a public repository**. Scrubbing it would have deleted genuinely useful
worked-example links from outward-facing documents to protect a fact that is
already public, while leaving the gate permanently red for a reason nobody
could act on. That pattern was removed from the blocklist instead, with the
evidence recorded there.

### `github-setup-disclosed` (BestPractice 37) gained a first-install clause and a Detail — 2026-09-10

**What changed.** The Rule keeps its original requirement word for word and
adds one clause: at a **first** install, three GitHub settings are standing
rather than discovered, and the install's closing message names all three —
a developer token saved as a repository secret, a default branch named
`main`, and *Allow GitHub Actions to create and approve pull requests* — in
the reply as well as in the administrator section the original Rule already
required. The practice's `occasion` now fires on a finished first install as
well as on an install step that adds something GitHub-specific. A `##
Detail` was added carrying the click-path and the failure mode of each of
the three; `checked_by`, `severity` and `status` are unchanged, and the
existing check (a newly added workflow file must be named in
GITHUB_ACTIONS.md) is untouched.

**Why it is a Rule change and not a cross-reference.** The original practice
says *where* a GitHub-specific fact must be disclosed. It does not say that
any particular fact must be disclosed at all — so an install that never
learned these three settings existed satisfied it completely while leaving a
repository that cannot check itself (a default branch not called `main` runs
no merge check) and cannot act for itself (no token, no permission to open a
pull request). Naming a standing trio is new normative content.

**Where it landed besides the practice**: [INSTALL.md](INSTALL.md) §1 step 10
and §0 step 9, [SETUP.md](SETUP.md) step 7 (the guided conversation's
plain-language wording), [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) beside the
workflow the two Actions settings affect, and a "Settings Only You Can Turn
On" section in
[templates/GETTING_STARTED.md](templates/GETTING_STARTED.md) so every
instantiated file carries them. Decision record:
[decisions/2026-09-10-install-closing-owner-settings.md](decisions/2026-09-10-install-closing-owner-settings.md).

**Figures moved by it**, per the hand-update convention in
[spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md): practices among the
original 52 carrying a Detail, 17 → 18; words in `## Detail`, 3,243 → 3,667.
Rules over 150 words did **not** move — the Rule clause was cut to fit
inside that budget rather than the budget's record being adjusted to fit it.

**Revised the same day, on Morgan's instruction, and the revision is the
part to read.** The trio became four — the repository is **private unless it
is meant to be public** — and everything about it got quieter: these are
suggestions that head off a later surprise, not a gate an install fails, and
the whole GitHub passage is deliberately short so it does not read as the
point of installing Precedent. The two paths now differ on purpose: the
one a developer reads ([INSTALL.md](INSTALL.md) §1 step 10) is a single short
paragraph, a sentence of it on the token, and leaves the rest to them; the
one for everyone else ([SETUP.md](SETUP.md) step 7) writes the
steps out and **offers more specific instructions on any of them if the
person wants them**, which
[templates/GETTING_STARTED.md](templates/GETTING_STARTED.md) repeats so the
offer survives the conversation. Detail words moved again, 3,667 → 3,785;
the Rule was re-trimmed to stay at 150. Decision record:
[decisions/2026-09-10-github-settings-optional-and-short.md](decisions/2026-09-10-github-settings-optional-and-short.md).

### `doc-references-are-links` (BestPractice practice 11) gained a practice-file exception — 2026-09-11

**What changed.** Clause (a) — in-repo documents reference repo files as
relative markdown links — now carries one exception, written into that
practice's `## Detail`: **a file in `practices/` links anything that does not
travel with it as an absolute `https://github.com/...` URL instead.** 134
links across 42 practice files were rewritten to that form in the same
commit, and the clause is unchanged for every other document in the tree.

**Why.** The catalogue is copied into every repository that adopts it, so a
relative link out of `practices/` is live where it was written and dead
everywhere it is read. Measured 2026-09-11: 134 links here pointed at 57
targets — `spec/`, `templates/`, root documents, hooks — that exist only in
this repository. A real consuming repository reported 120 of its own the same
day. Nothing caught it at either end: the rule saying so lived in a private
individual set whose check deliberately skips practices from other sources,
and this repository had neither the rule nor the script.

**The new practice is [practice-links-travel](practices/practice-links-travel.md)**,
landed at universal the same day with a real check in
[tools/precedent_check.py](tools/precedent_check.py) — the promotion half of
[spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md)'s two-step. The
individual copy is still standing; deduplicating it needs a session that can
reach that repository, and is queued at
[TODO.md's `deduplicate-practice-links-travel` item](TODO.md#deduplicate-practice-links-travel).

**The public/private answers differ on purpose, and the practice says so.**
An absolute URL is right from a public upstream and wrong from a private set,
where it would publish the private repository's name into every consumer that
materializes the practice; there the remedy stays "drop the link markup, keep
the backticked path."

**One thing to know at the phase-7 fold-in:** those URLs carry
`precedent-beta-v01`, because that is what `precedent.json` declares as
`base_branch`. Setting that key to `main` without rewriting them leaves 134
links pointing at a branch nobody publishes from — the check fails on exactly
that mismatch, and the fix is one `sed` across `practices/`. Both
`precedent.json`'s own comment and this note say so.

## Cross-referenced only, not a behavior change

**A scope note on the entry below, added 2026-09-03**: "no `checked_by`
enforcement changed" in the Slug-link citation sweep entry is accurate for
that specific commit, not a claim that none of the affected practices ever
gained enforcement — several did, in separate, earlier commits, logged
above once this branch's own pre-fork audit actually found the gap.

### Slug-link citation sweep — 2026-09-01

**What changed.** Every in-body `practice N` / `practices N and M` cross-reference
in `practices/*.md` is now a `[slug](slug.md)` markdown link. Nothing about any
Rule's substance changed, and no `checked_by` enforcement changed — this is
purely how one practice points at another. Numbers stop meaning one fixed thing
the moment practices can be reordered, split, or retired (which this catalogue
is now built to do), so a bare `practice 44` is a citation that silently rots;
a slug is permanent. `tools/verify_harness.py` gained
`check_no_bare_numeric_citations` (the numeric form must not come back) and
`check_slug_link_integrity` (every link must resolve to a real slug) as the
forward-looking guards, alongside the existing `check_citation_integrity`.

**Why this needs a CHANGES_TO_TELL_ALEX.md entry at all**, given it isn't a
mechanism or decision-rule change: converting a citation to a link adds words
not counted at that frequency in BestPractice's original numbered prose, so
the affected files needed a disclosed exemption — `verify_harness.py`'s
`AMENDED_POST_CONVERSION` — whose own rule is that the exemption must be
both declared *and* found in this file.

**Affected practices** (slug — original BestPractice number), each also
carrying the same exemption in `verify_harness.py`'s `AMENDED_POST_CONVERSION`
registry — this list and that registry must agree, and this is the copy a
human reads: `acronyms-glossary` (17), `affordance-is-shared` (43),
`build-buy-decompose` (35), `capture-gate` (10), `check-source-architecture`
(40), `computed-numbers-in-scripts` (19), `convention-to-audit` (6),
`deliverables-look-like-output` (49), `docs-track-models` (33),
`engine-plus-host-shims` (50), `environment-gotchas` (4),
`frame-from-audience-question` (28), `generated-artifact-provenance` (8),
`index-remembers-past` (48), `merge-authorization-keyword` (45),
`merge-runbook` (9), `mistakes-become-rules` (20), `no-rewrite-for-warnings`
(31), `one-formatter-per-quantity` (51), `outward-summary-discipline` (25),
`parallel-artifact-ledger` (22), `permutation-frontier-column` (47),
`practice-export-loop` (14), `readers-vocabulary` (34),
`registry-source-of-truth` (7), `repo-is-memory` (1),
`scripts-assert-properties` (30), `scrub-gate` (15), `search-by-purpose` (41),
`second-pass-capture` (21), `session-bootstrap` (13),
`tabular-shared-renderer` (46), `two-check-levels` (44),
`variant-re-derives` (29), `verify-decomposition` (42),
`verify-postcondition` (32), `volatile-rules-carry-dates` (16), and
`todo-is-a-handoff` (53, exempted 2026-09-02 once a phase-5 pre-flight
`git merge origin/main` gave it a frozen ancestor in `PRACTICES.md` for the
fidelity checks to compare against for the first time).

**Four citations were simply wrong**, found by resolving each one against its
target's actual content rather than trusting the printed number — a defect
class BestPractice's own history already has one instance of (the practice-39
corruption `check_corruption_drop_is_a_duplicate` guards), not something this
sweep introduced:

- `engine-plus-host-shims`, `one-formatter-per-quantity`, and
  `permutation-frontier-column` each cited "practice 44" for the shared
  renderer / sortable render — practice 44 is *two named check levels*
  (`two-check-levels`); the shared renderer is practice 46,
  `tabular-shared-renderer`. Three independent citations landing on the same
  wrong number, never the topic they described, reads as an old renumbering
  that never got swept. All three now link to `tabular-shared-renderer`.
- `tabular-shared-renderer` itself cited "practice 12" for "conventions harden
  into audits" — practice 12 is `reply-links-files`; the audit-hardening rule
  is practice 6, `convention-to-audit`. Fixed.
- `second-pass-capture` cited "(practice 2)" for "decisions queued in the
  typed TODO" — practice 2 is `orientation-map`; the TODO is one of the three
  living documents named in practice 1, `repo-is-memory`. Fixed.
- `affordance-is-shared` cited "practice 42(b)" for "compute the term whose
  direction is the point" — `verify-decomposition` (42) is the right
  practice, but that description matches its **(a)** sub-point (assert on the
  decomposition, compute terms directly), not **(b)** (a negative result is a
  parameterisation). Changed to `(a)` — lower confidence than the other
  three, since it is a sub-point call rather than a wrong practice.

None of these were introduced by the phase-1 conversion: the converter's
"move only" rule carried the wrong numbers forward exactly as BestPractice had
them, and a numeric-only citation check can only confirm a cited number
*exists*, not that it is the *right* one. Worth a note upstream at the next
real check-in, alongside the existing practice-39 finding.

### Relative-link sweep in `practices/` — 2026-09-06

**What changed.** 67 markdown links across 28 practice files were repointed
from `](tools/doc_lint.py)` to `](../tools/doc_lint.py)`. A practice file
lives in `practices/`, one directory below the repo root, so a root-relative
link inside one resolved to `practices/tools/doc_lint.py` and returned a
404 on GitHub for anyone reading the practice file itself — which, since
the fork, is the primary way a practice is read. The newer practice files
already used `../`; the inherited ones did not, and nothing checked. No
prose changed: only the target inside the parentheses, never the label.

**Why this needs an entry**, given no Rule's substance moved: the sentence
identity half of `verify_harness.py`'s fidelity checks compares the rendered
link target along with the words, so eight practices whose repointed links
sit inside a checked section needed a disclosed exemption in
`AMENDED_POST_CONVERSION` — whose own rule is that an exemption must be both
declared *and* found in this file. The word-multiset checks (no invented
content, no lost content) still pass untouched, which is the evidence that
this is a target change and not a text change.

**Affected practices** (the eight carrying the exemption; the other 20 files
in the sweep needed none): `doc-references-are-links`,
`github-setup-disclosed`, `lead-with-what-it-is`, `orientation-map`,
`pr-template-honest-gates`, `quick-index`, `reply-links-files`,
`section-order-by-frequency`.

**Forward guard.** `tools/doc_lint.py` gained a broken-relative-link check
so the next one fails a gate instead of a reader.

## Considered, not changed

### `practice-export-loop` (BestPractice practice 14) and `mistakes-become-rules` (BestPractice practice 20) — 2026-09-01

Both relate to the new architecture — 14 to Stage 5's promotion round-trip,
20 to Stages 1–4's creation pipeline — and a first pass added a
cross-reference paragraph to each practice's Install section. Reverted on
reflection: per this repo's own `deliverables-look-like-output` (BestPractice
practice 49), a practice file is the deliverable and holds what following it
needs, not commentary about a related mechanism elsewhere. That cross-reference
now lives in `PRACTICE_ENGINE_PLAN.md`'s "What phase 5 should carry forward"
instead. **Both files are byte-for-byte unchanged from BestPractice's
original text.**

### `engine-plus-host-shims` (BestPractice practice 50) — 2026-09-03

The new `templates/harness/claude-code/hooks/precedent-paths.sh`
(a `PreToolUse` hook wiring the path-triggered loading channel into a
fresh install — see `spec/LOADER.md`) is a real, new *application* of this
practice's engine-plus-shim split: the vendored engine
(`tools/precedent_paths.py`) stays the single implementation, the new file
is a thin host shim that shells out and reshapes its output for Claude
Code's own hook contract. Considered logging it here as a mechanism
change and decided against it: this practice's own Rule, Why, and Story
are untouched, byte-for-byte — a new instance of an existing pattern is
not a change to what the pattern means or how it works, any more than a
new practice file citing `code-cites-practice` would be. This is purely
Precedent-native engine work (phase 6, consumer-repo integration for a
channel that did not exist pre-fork), so it needs no separate call-out by
this file's own stated scope; `git log` and `spec/LOADER.md`'s own status
table already say what was added.

## Alex's real-time additions

### Practice 53, "A TODO is a handoff, not a parking lot" — 2026-09-01

Not a change *to* an inherited practice — a practice Alex added to `main`
(pull request (PR) #61, 2026-08-31) after this branch's fork point
(`88ecf7f`). Converted
through the same phase-1 pipeline as the original 52, unmodified in
substance: [practices/todo-is-a-handoff.md](practices/todo-is-a-handoff.md).
Noted here because it's the kind of drift this file exists to catch — `main`
had moved 3 commits past the fork point (this practice plus two unrelated
tooling fixes) before a session checked.

### Practices 54 and 55, and two clauses on inherited practices — 2026-09-08

Alex merged a check-in from dependent repo #1 into `main`
([PR #139](https://github.com/alex137/BestPractice/pull/139), commit
`7d8f5a6`). It was carried onto this branch the same day. Only the tooling
half arrived unchanged; **every part that touched the catalogue had to change
shape**, because `main` still keeps its practices in one numbered file and
this branch does not.

**The two new practices are files, not `PRACTICES.md` sections.** Upstream
they are `## 54.` and `## 55.` appended to
[PRACTICES.md](PRACTICES.md); here that file is frozen at 53 and says so in
its own banner, so they landed as
[practices/constants-are-risk-inputs.md](practices/constants-are-risk-inputs.md)
and
[practices/slow-steps-report-and-cache.md](practices/slow-steps-report-and-cache.md),
in the phase-1 format, with the Rule/Detail/Why/Story/Install split applied
to your prose and nothing added to it. They carry
`source_practice_number: null` — the numbers 54 and 55 exist on `main` and
nowhere on this branch, so a file citing them would be citing a section that
is not there. Their `approved_by` records your merge as the approval.

**The two clause additions were split across sections.** Your
dual-direction clause went into
[practices/verify-decomposition.md](practices/verify-decomposition.md)
(practice 42) — the rule text into `## Why` as `(c)`, its `(Origin: …)`
parenthetical into `## Story`, since a converted practice keeps the incident
there. The ratings corollary went into
[practices/name-both-sides-of-ledger.md](practices/name-both-sides-of-ledger.md)
(practice 52) the same way: the rule into `## Rule` as `(c)`, the composition
failure mode into `## Why`, the second origin incident into `## Story`.
`name-both-sides-of-ledger` is now listed in
[tools/verify_harness.py](tools/verify_harness.py)'s
`AMENDED_POST_CONVERSION` for it.

**One cross-reference in your text points at a different practice here.**
Practice 54's *Why* names "practice 25's dual" for the favorable-lever guard.
The clause it means is the one that same commit added to practice **42**
(`verify-decomposition`); practice 25 is `outward-summary-discipline`. The
converted file links the slug instead of repeating the number. Worth
correcting on `main` too.

**Your `doc_lint` check 7 was not taken, because this branch already had
it and more.** Upstream added `check_anchors`, which resolves a document's
own `[text](#slug)` links against its headings. This branch's
`check_broken_links` already does that *and* resolves anchors into other
files, and guards the setext-heading case where the anchor set cannot be
known. Taking check 7 on top would also have shadowed this branch's
module-level `HEADING_RE` and `heading_slug` with upstream's — same names,
different capture groups — silently breaking `document_anchors`. The
`doc_html` half of the same change *was* taken: the render stamps GitHub
slugs as heading ids, which is what makes those links land in the HTML
product.

## Not a practice change — one adopter-facing behaviour change lands with the merge

Also not a change to what one of your practices means, and also recorded here
because this file is what the phase-7 conversation opens with.

**`tools/precedent_sync_views.py --repo` is required as of 2026-09-10**, where
it used to default to the script's own parent directory. That tool does not
exist on `main` today, so nothing changes for you until the fold-in — but the
moment it lands, **anyone who had been running it bare gets an exit 1 instead
of a run.** From a consuming repo's root the invocation is
`python3 tools/precedent_sync_views.py --repo .`, and the two documented
invocations in [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)
were updated with the change.

The default was removed rather than documented better because it had already
been documented: the docstring named it as a trap, and on 2026-09-09 a careful
session ran the tool bare anyway, `--repo` resolved to `process/upstream/`, the
team sources' `../` paths resolved against `process/`, every source missed, and
the run hard-failed blaming a path collision in a repository where nothing was
wrong. **A documented trap that still catches a reader is an argument for a
refusal, not for a better paragraph.**

Nothing else in the source-clone work reaches `main`'s own behaviour: the
branch pin added the same day governs how practice-set *sources* are cloned,
never which branch anyone works on, and the three tools involved are absent
from `main` entirely.

## Not a practice change — three leak-gate behaviours change under you

Same reason as the section above: not a change to what one of your practices
means, and worth hearing before you run the gate and find it acting
differently.

**1. The blocklist is discovered, not only exported.** With
`PRECEDENT_LEAK_BLOCKLIST` unset, `tools/leak_gate.py` now reads
`leak-blocklist.txt` from the individual set your `~/.config/precedent/config.json`
names — the path [INSTALL.md](INSTALL.md) section 8 already tells everyone to
put it at. Before, an unexported variable meant the vocabulary layer quietly
dropped to its structural half and printed `PARTIAL`. **If you have a list
there, expect the gate to start applying it in shells where it previously did
not** — more patterns, not fewer, so a tree that was passing can legitimately
start failing. The variable still wins where it is set, and
`--structural-only` is still how continuous integration opts out by name.

**2. A private repository's bare name can be covered without a pattern.**
`# visibility-audit: auto-cover-bare-names on -- <reason>` turns every clone
on the disk under your private-by-default owner, with no `allow` line, into a
whole-word pattern — so naming one in this public tree is a hard failure
instead of a note asking somebody to write a stem. **Off by default**, and
worth leaving off unless you want it: it can fail a push that passed
yesterday. Switching it on here immediately found a real gap — one team set
was named 28 times in this tree with no `allow` line, covered only in its
`owner/name` form.

**3. The routine stem note can be switched off, per person, in your own
blocklist.** `# visibility-audit: stem-notes off -- <reason>` stops the gate
noting every private-by-default clone on the disk whose bare name no pattern
matches. **Default is unchanged**: without that line you get exactly the notes
you get today. The notes are not lost where somebody switches them off —
`leak_gate.py --survey` prints them, and `tools/very_deep_check.py`'s
repository-visibility pass calls it, so they arrive as `RECOMMENDATION:` lines
inside a review somebody asked for.

Morgan asked for the third one on 2026-09-12, after a session relayed the
note and offered to add a stem: *"I just want to ignore it, UNTIL I tell you
explicitly to add something to a blocklist."* The second is what he asked for
in the same thread once the first was agreed — *"there is ONE THING I want to
stop from leaking: private repo names"* — because silencing a note removes the
request, not the risk it was about. His account's blocklist carries both
directives; nothing about yours changed.

## Not a practice change — the merge-back itself has a trap in it

Everything above is a change to what one of your practices means. This is
not: it is the thing most likely to go wrong in the phase-7 merge, recorded
here because this file is what that conversation opens with.

**`main` still carries `97ed078`, the revert of the accidentally-merged
PR #89** (2026-09-03 — the incident behind
[local/practices/merge-target-is-beta-branch.md](local/practices/merge-target-is-beta-branch.md)).
That revert undid the *files*; it did not undo the *history*. `main`'s log
still contains this branch's commits up to `1ff6a7e`, so git treats them as
already merged. A plain `git merge precedent-beta-v01` into `main` therefore
replays only what happened here after 2026-09-03 and honours `main`'s
deletion of everything older: **125 modify/delete conflicts, plus 507 files
that are absent from the result with no conflict raised at all** — measured
2026-09-07 against `e8341e2`. The silent half is the dangerous one: someone
who works through all 125 conflicts by hand has no signal that the other 507
were ever in question.

**The merge to run instead**, measured the same day at **0 conflicts and a
tree byte-identical to this branch**: branch off `main`, `git revert
97ed078`, then `git merge precedent-beta-v01`, and open *that branch* as the
pull request. Both commits arrive in one merge, so `main` flips from
no-Precedent to all-of-Precedent exactly once — when you approve it, never
before.

The file lists, the reason an earlier rehearsal concluded the opposite, and
the same hazard in the reverse direction are in
[TODO.md's `retire-merge-target-practice` item](TODO.md#retire-merge-target-practice).

Numbers by: catalogue_stats.py

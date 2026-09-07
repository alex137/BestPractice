---
title:         Document lifecycle — a standard status header, and the migration onto it
kind:          proposal
status:        accepted
opened:        2026-09-07
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Gives every non-practice document a machine-readable kind and status, splits the tree by audience, and migrates the existing 24 spec files onto both.
---

# Document lifecycle — a standard status header, and the migration onto it

**Status: accepted; phase 1 is built, phases 2-6 are not.** Self-contained,
so a session (or another system) with no memory of the conversation that
produced it can carry it out. Phase 1 landed on 2026-09-07:
[tools/doc_lifecycle.py](../tools/doc_lifecycle.py) exists, is registered as
the `document-lifecycle-header` check, and this file plus
[PHASE3_BRIEF.md](PHASE3_BRIEF.md) are stamped — 22 documents are not, and
the check is warn-only until phase 2 stamps them. Where this document names
a file, a count or a command, those were read off the tree on 2026-09-07 at
commit `9e25dca`; re-check them before relying on them.

**The one-sentence version:** `practices/` already solved "a catalogue that
must grow without costing the reader" with per-file frontmatter plus
generated views, and [spec/](.) — 24 files, ≈660 kilobytes (KB) — never got the same
treatment, so **a closed phase brief and live normative reference are
indistinguishable from the file listing**, to a visitor and to a cold
session alike.

## Why this exists, and the failure it prevents

[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s "Why Trimming Is Not
the Answer" section settles the strategy question before this document opens
it. A decisions log was condensed on 2026-08-28 (`02a24a7`) and **had fully
regrown within a day**, because the pressure that produced the text had not
changed. The plan's conclusion — *decouple the size of the catalogue from
the cost of having it* — is what phase 2 then did for practices, and is
exactly what this document does for everything else.

So: **nothing here deletes a document.** [repo-is-memory](../practices/repo-is-memory.md)
requires that what a future session needs lives in committed files; it says
nothing about a file being at the top level or being presented as current.
Every move below keeps the file tracked, linkable and greppable.

Three incidents this standard prevents, all present in the tree today:

1. **Status is already being recorded — in six incompatible prose formats,
   owned by nobody.** [spec/PHASE3_BRIEF.md](PHASE3_BRIEF.md) opens
   *"**Status: phase 3 is fully closed, as of 2026-09-01.**"*;
   [spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md) opens *"**Done,
   2026-09-01**"*; [spec/PHASE6_BRIEF.md](PHASE6_BRIEF.md) *"**Status:
   opened 2026-09-03, not closed.**"*;
   [spec/SIMULATION_BRIEF.md](SIMULATION_BRIEF.md) *"**Status: approved;
   phases 1-4 (rough phasing, below) are built.**"*;
   [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
   *"**Status: drafted, not executed.**"*; and the remaining 19 files
   declare nothing at all. This is precisely what
   [registry-source-of-truth](../practices/registry-source-of-truth.md)
   forbids: a status that sessions make decisions on, restated in prose and
   owned by no registry.

2. **The gap is being patched by hand, in the most expensive file in the
   repo.** [AGENTS.md](../AGENTS.md)'s quick index carries rows reading
   *"(done 2026-09-01, closing phase 3 — brief kept for how it was done)"*
   and *"Steps 1-2 done (2026-09-05 …); the pilot itself deliberately still
   not done"*. Those sentences are a `status:` field written in prose,
   maintained by hand, inside a 56 KB file that every session loads.

3. **A superseded 134 KB document sits at the repo's front door.**
   [README.md](../README.md) itself describes [PRACTICES.md](../PRACTICES.md)
   as *"the pre-split practice catalog (52 of the current, larger set — see
   practices/ for the complete, current one)"*. The successor exists, the
   predecessor is the larger file, and the file listing ranks them equally.

4. **The recency stamp actively contradicted the file's own state, during
   the writing of this plan.** [VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md) was
   closed on 2026-09-07 by commit `ed0879f`, whose message is *"Close the very
   deep check: all four passes"* and whose diff marks all four passes `done`.
   That same commit left the file's opening comment reading
   `<!-- Last updated: 2026-09-07, run in progress -->`. The session that
   closed the run updated the table and not the stamp, because **nothing
   checks the stamp and nothing derives from it.** This is the whole argument
   in one file: a hand-maintained status marker is not merely uninformative,
   it goes on asserting the opposite of the truth.

**Only the recency of the file is recorded today, and recency is not
status.** Every one of the 24 files opens with an HTML comment of the form
`<!-- Last updated: 2026-09-01 (Buenos Aires) by a follow-up session -->`.
That marker cannot distinguish *finished on that date* from *stale since
that date* — opposite meanings, identical rendering.

## The three changes

This document specifies three changes that are separable but sequenced. A
session may stop after any one of them and leave the repository coherent.

1. **A standard header** (kind and status as frontmatter) on every
   non-practice document, backfilled across the existing tree.
2. **A split by audience**: the repository root holds the product;
   [spec/](.) holds current normative reference; a new `record/` holds the
   working record.
3. **A generated exhibit page** at spec/README.md and record/README.md
   that presents the working record as evidence rather than spill.

Change 3 is the cheapest and has the highest value per hour; it is
sequenced third only because it is generated from the frontmatter change 1
introduces.

## Change 1 — the standard header

### The fields

Each document gains YAML frontmatter, delimited by `---`, as the first
bytes of the file. This matches [practices/](../practices/), where the same
mechanism is already established and already parsed by
[tools/build_views.py](../tools/build_views.py).

```yaml
---
title:         The Loader
kind:          reference
status:        current
opened:        2026-08-30
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       What phase 2's loader built, what it did not, and what the replay measurement proves.
---
```

| Field | Required | Meaning |
|---|---|---|
| `title` | always | The document's name. Must match its `#` heading. |
| `kind` | always | One of the five kinds below. Decides which `status` values are legal. |
| `status` | always | Legal values depend on `kind`; see the matrix. |
| `opened` | always | Date the document was created, `YYYY-MM-DD`. |
| `closed` | when `status` is `closed` | Date the work it describes finished. Null otherwise. |
| `superseded_by` | when `status` is `superseded` | Repository-relative path of the successor. |
| `supersedes` | always (may be `[]`) | Paths this document replaced. |
| `audience` | always | `session`, `contributor`, or `adopter`. Decides placement — see change 2. |
| `summary` | always | One sentence, ending in a period. Feeds the generated index. |

### The five kinds

The kind is not decoration: **it decides what "outdated" can even mean for
the file.** A reference document can go wrong. A dated audit record cannot —
it is a true observation of a date, and stays true forever.

| `kind` | What it is | Examples in the tree today |
|---|---|---|
| `reference` | Normative. States how the system works or must be built. Can become wrong. | [PRACTICE_FORMAT.md](PRACTICE_FORMAT.md), [SOURCES.md](SOURCES.md), [LOADER.md](LOADER.md) |
| `procedure` | A repeatable how-to for a contributor. Can become wrong. | [BOOTSTRAP_NEW_SOURCES.md](BOOTSTRAP_NEW_SOURCES.md), [MOVING_PRACTICES.md](MOVING_PRACTICES.md) |
| `brief` | What a phase or a session was handed. Finishes. | [PHASE3_BRIEF.md](PHASE3_BRIEF.md), [PHASE6_BRIEF.md](PHASE6_BRIEF.md) |
| `record` | What a run, audit or investigation found, on a date. Never becomes wrong. | [PRELAUNCH_AUDIT.md](PRELAUNCH_AUDIT.md), [ATTENTION_CEILING.md](ATTENTION_CEILING.md) |
| `proposal` | An intention not yet carried out. | [NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md), and this document |

### Legal status values, by kind

```
reference  ->  current | superseded
procedure  ->  current | superseded
brief      ->  open | closed | blocked
record     ->  live | closed
proposal   ->  drafted | accepted | executed | abandoned
```

A `record` is `live` only while a run is still being written into it, and
`closed` otherwise.

**One record cycles, and the check must allow it.**
[VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md) is a standing ledger: it is `live`
while a run is open and `closed` when the last pass lands, then `live` again
when the next run starts. `closed` is therefore not a terminal state for a
`record`, and no check may assume a document only ever moves one way through
the matrix. Every other kind does move one way.

**`blocked` is not a synonym for `open`.** A brief is `blocked` when the
reason it cannot proceed is external and stated — the condition
[todo-is-a-handoff](../practices/todo-is-a-handoff.md) already requires of a
queued item. [PRIVATE_ENFORCEMENT_BRIEF.md](PRIVATE_ENFORCEMENT_BRIEF.md) is
the live example: it cannot run from a session rooted here.

### The generated banner replaces the prose banner

The frontmatter owns the status. **The prose status sentences quoted in the
"Why this exists" section above are deleted**, and a generated block takes
their place, immediately after the `#` heading:

```markdown
<!-- BEGIN GENERATED: doc-status -->
> **Closed brief.** Opened 2026-08-30, closed 2026-09-01. Kept as the record
> of what this phase was handed — not a live work list.
<!-- END GENERATED: doc-status -->
```

This is the same mechanism, with the same markers convention, as
[AGENTS.md](../AGENTS.md)'s `precedent-loader` block, and it satisfies
[registry-source-of-truth](../practices/registry-source-of-truth.md)
(frontmatter owns, prose derives) and
[generated-artifact-provenance](../practices/generated-artifact-provenance.md)
(never hand-edited; regenerated from source).

### What happens to the `Last updated` comments

They are removed from `reference` and `procedure` documents, and retained
nowhere as free prose. [docs-are-current-state](../practices/docs-are-current-state.md)
is explicit that version control answers *when did this change* better than
an annotation, and that annotation is a second copy that decays. For `brief`
and `record` kinds the date is not an annotation but the subject — that is
the practice's own exemption (a), *records whose subject is a dated decision
or event* — and it is carried as the `opened` and `closed` fields, where a
check can read it.

### The mechanical check

[checkable-gets-checked](../practices/checkable-gets-checked.md) requires an
actual attempt before leaving a convention advisory. This one is
straightforwardly checkable, so it is not left advisory. Build
tools/doc_lifecycle.py and register it the way existing checks are
registered (see `python3 tools/precedent_check.py --list`). It must assert:

1. Every `.md` file under [spec/](.) and `record/` has frontmatter, and the
   frontmatter parses.
2. `kind` is one of the five; `status` is legal for that `kind`.
3. `closed` is present exactly when `status` is `closed`; `superseded_by`
   exactly when `status` is `superseded`, and resolves to a file that exists.
4. `title` equals the document's first `#` heading.
5. The generated `doc-status` block matches what the frontmatter would
   produce — the same hand-edit guard [tools/verify_harness.py](../tools/verify_harness.py)
   already applies to the loader block.
6. No document outside the `record`/`brief` kinds carries a `Last updated:`
   comment.

**Do not add this file to `tools/checks/`.** That directory is
[tools/precedent_materialize.py](../tools/precedent_materialize.py)'s output,
deleted and rewritten on every sync — a hand-added file there survives only
until the next run. This is recorded in [AGENTS.md](../AGENTS.md)'s gotchas
section; it is repeated here because a session implementing a new check is
exactly who hits it.

**Wire it with a firing test**, per the same practice: plant a violation,
prove the check fails, remove it, prove the check passes on the unplanted
tree.

## Change 2 — split the tree by audience

### The test that decides placement

**Two independent axes, and conflating them is the current mistake.**
*Audience* decides which directory a document lives in. *Status* decides how
it is presented once there. A closed brief and an open brief live in the
same place; a reference document and a brief do not, however current both
are.

| Directory | Audience | The test |
|---|---|---|
| repository root | Anyone arriving at the project | Would a stranger evaluating Precedent open this in their first ten minutes? |
| [documentation/](../documentation/) | Someone using Precedent on their own project | Is this a how-to for an adopter rather than a contributor? |
| [spec/](.) | A contributor or session building Precedent | Is this normative — does it say what must be true? |
| `record/` (new) | The same, later | Is this the narrative of what happened or what we intend? |
| [decisions/](../decisions/) | unchanged | A dated decision that is not about a practice. |

The line between [spec/](.) and `record/` is worth stating once, plainly:
**[spec/](.) says what must be true; `record/` says what happened.** A
reference document is wrong if the system disagrees with it. A record is
never wrong, because it describes a date.

### Why `record/` and not `archive/`

`archive` reads as *dead*, and `record/` will hold live material —
[PHASE6_BRIEF.md](PHASE6_BRIEF.md) is open, [VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md)
is mid-run. **`record` is also already this repository's word for exactly
this content**: [deliverables-look-like-output](../practices/deliverables-look-like-output.md)
speaks of the *paired record document* and *record-class files*, and
[tools/doc_lint.py](../tools/doc_lint.py) implements `RECORD_NAME_RE` and
`RECORD_DIR_RE` around that vocabulary.

One consequence the implementer must handle: `RECORD_DIR_RE` in
[tools/doc_lint.py](../tools/doc_lint.py) currently reads
`(process|archive|sent|templates|deck|practices|spec|decisions|evals)`. It
already exempts `archive` and `spec` from the check-6 residue scan, and does
**not** exempt `record`. Add it in the same commit as the directory, or
every moved file fails the gate for containing the apparatus it exists to
hold.

### Where each spec file goes

All 24 files. `→ spec/` means it stays.

| File | `kind` | `status` | Destination |
|---|---|---|---|
| [PRACTICE_FORMAT.md](PRACTICE_FORMAT.md) | reference | current | → spec/ |
| [CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md) | reference | current | → spec/ |
| [SOURCES.md](SOURCES.md) | reference | current | → spec/ |
| [SOURCE_NAMING.md](SOURCE_NAMING.md) | reference | current | → spec/ |
| [ENFORCEMENT.md](ENFORCEMENT.md) | reference | current | → spec/ |
| [LOADER.md](LOADER.md) | reference | current | → spec/ |
| [BOOTSTRAP_NEW_SOURCES.md](BOOTSTRAP_NEW_SOURCES.md) | procedure | current | → spec/ |
| [MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md) | procedure | current | → spec/ |
| [MOVING_PRACTICES.md](MOVING_PRACTICES.md) | procedure | current | → spec/ |
| [PHASE3_BRIEF.md](PHASE3_BRIEF.md) | brief | closed 2026-09-01 | `record/` |
| [PHASE5_BRIEF.md](PHASE5_BRIEF.md) | brief | closed 2026-09-02 | `record/` |
| [PHASE6_BRIEF.md](PHASE6_BRIEF.md) | brief | open | `record/` |
| [PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md) | brief | closed 2026-09-01 | `record/` |
| [PRIVATE_ENFORCEMENT_BRIEF.md](PRIVATE_ENFORCEMENT_BRIEF.md) | brief | blocked | `record/` |
| [SIMULATION_BRIEF.md](SIMULATION_BRIEF.md) | brief | open | `record/` |
| [PREFORK_AUDIT.md](PREFORK_AUDIT.md) | record | closed 2026-09-03 | `record/` |
| [PHASE5_DEEPCHECK.md](PHASE5_DEEPCHECK.md) | record | closed 2026-09-02 | `record/` |
| [PRELAUNCH_AUDIT.md](PRELAUNCH_AUDIT.md) | record | closed 2026-09-06 | `record/` |
| [ATTENTION_CEILING.md](ATTENTION_CEILING.md) | record | closed 2026-09-04 | `record/` |
| [VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md) | record | closed 2026-09-07 | `record/` — but see the cycling note below |
| [UNBUILT_PLAN_ITEMS.md](UNBUILT_PLAN_ITEMS.md) | record | live | `record/` |
| [NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md) | proposal | drafted | `record/` |
| [NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md) | proposal | accepted | `record/` |
| `PREFORK_AUDIT.html` | — | — | see below |

**Three of those need a judgment stated rather than assumed.**

- [SIMULATION_BRIEF.md](SIMULATION_BRIEF.md) says *"phases 1-4 … are built"*
  of its own internal phasing, not the plan's. It is `open`, not `closed` —
  the implementer should confirm against
  [tools/practice_simulation.py](../tools/practice_simulation.py) before
  stamping it.
- [NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)
  has steps 1–2 executed and the pilot deliberately not started, so
  `accepted` (agreed, partly carried out), not `drafted` and not `executed`.
- `PREFORK_AUDIT.html` (68 KB) is a build output committed beside its
  source. It is not a document and takes no frontmatter. **Decide it
  separately from this plan**: either move it with its source, or stop
  committing it and generate on demand. Do not let that question block the
  rest.

### Where each root file goes

| File | Verdict | Reason |
|---|---|---|
| [README.md](../README.md) | root, pinned | The front door. |
| [AGENTS.md](../AGENTS.md), [CLAUDE.md](../CLAUDE.md) | root, pinned | The harness reads them by path. |
| [MAP.md](../MAP.md) | root, pinned | [orientation-map](../practices/orientation-map.md) specifies *a top-level [MAP.md](../MAP.md)*. Moving it violates a resident practice. |
| [GLOSSARY.md](../GLOSSARY.md) | root, pinned | Generated to root by [tools/build_views.py](../tools/build_views.py). |
| [precedent.json](../precedent.json) | root, pinned | Resolved by path. |
| [ADOPTING.md](../ADOPTING.md), [INSTALL.md](../INSTALL.md), [SETUP.md](../SETUP.md) | root | The install path, linked from outside the repository. |
| [TODO.md](../TODO.md) | root | Live, and referenced by tooling and by resident practices. |
| [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) | root **until phase 7** | The approved plan of record, still being worked. `kind: reference`, `status: current`. When phase 7 folds the branch into `main`, it becomes `kind: record`, `status: closed`, and moves to `record/`. |
| [METHOD.md](../METHOD.md) | → [documentation/](../documentation/) | The working method, for adopters. |
| [MOBILE.md](../MOBILE.md) | → [documentation/](../documentation/) | Per-assistant setup, for adopters. |
| [GITHUB_ACTIONS.md](../GITHUB_ACTIONS.md) | → [documentation/](../documentation/) | Operational how-to, for adopters. |
| [GIT.md](../GIT.md) | → [documentation/](../documentation/) | **The debatable one.** It is reader-facing and adopter-shaped, but [README.md](../README.md) leans on it as a first-visit explainer. Move it, or leave it at root and say why — do not leave the question open. |
| [PRACTICES.md](../PRACTICES.md) | → `record/`, `status: superseded`, `superseded_by: practices/` | 134 KB, described by [README.md](../README.md) as the pre-split catalogue. **Highest-churn move in this plan** — 181 tracked files mention the name. Sequenced last. |
| [CHANGES_TO_TELL_ALEX.md](../CHANGES_TO_TELL_ALEX.md) | → `record/` | A live internal handoff note, not front-door material. `kind: record`, `status: live`. |

## Change 3 — the exhibit page

Add spec/README.md and record/README.md, each with a hand-written
opening paragraph and a **generated table** below it, built from the
frontmatter by [tools/build_views.py](../tools/build_views.py): title,
kind, status, closed date, summary — one row per document, current first.

record/README.md's opening paragraph is the one that matters, and it
should say what the directory is: *the working record of how Precedent was
built — the briefs each phase was handed, the audits that found what was
wrong, and the decisions taken along the way.*

**This is the change that reframes the problem.** Precedent's own pitch, in
[README.md](../README.md), is that the assistant *"keeps the record of how a
decision was reached, not just the decision itself."* A repository dense
with phase briefs, dated audits and decision records is not an embarrassment
next to that claim — **it is the demonstration.** But it reads as
demonstration only if it is presented as one; left unlabelled it reads as
spill. One page converts it, and the table under it is generated, so it
cannot drift.

record/README.md also carries the **lineage rows**:
[index-remembers-past](../practices/index-remembers-past.md) puts provenance
in the index rather than in either document, so the row for
[PRACTICES.md](../PRACTICES.md) names [practices/](../practices/) as its
successor, and nothing is written into either file.

## The migration

Six phases. **Each is independently mergeable and each ends with a green
deep check** — [tools/verify_harness.py](../tools/verify_harness.py),
[tools/doc_lint.py](../tools/doc_lint.py), [tools/leak_gate.py](../tools/leak_gate.py),
[tools/precedent_check.py](../tools/precedent_check.py) and
[tools/doc_sync.py](../tools/doc_sync.py) all run, with `0 failed` and `0 violated`
([two-check-levels](../practices/two-check-levels.md)). A phase that cannot
finish green is reverted, not carried.

All work lands on `precedent-beta-v01`, per [AGENTS.md](../AGENTS.md)'s
standing rule.

### Phase 1 — schema and check, no moves

Write tools/doc_lifecycle.py and register it. Add frontmatter to **one**
file first — [spec/PHASE3_BRIEF.md](PHASE3_BRIEF.md), because its status is
unambiguous and already stated in prose — and run the check against the
whole tree with the check in warn-only mode, to see the true violation count
before committing to it. **Nothing moves in this phase**, so it is
reversible by deleting one file.

*Done when:* the check runs, reports every unstamped document, and fires on
a planted bad `status` value.

### Phase 2 — backfill all 24 spec files

Stamp the frontmatter from the table above. Delete the prose status
sentences and the `Last updated:` comments the standard retires. Generate
the `doc-status` banners. Flip the check from warn-only to blocking.

**Do not batch this with a move.** A file that gains frontmatter *and*
changes path in one commit is unreviewable, and the diff hides which of the
two broke a link.

*Done when:* the new lifecycle check passes on the unplanted tree,
and no document under [spec/](.) declares a status in prose.

### Phase 3 — the generated indexes

Teach [tools/build_views.py](../tools/build_views.py) to emit the tables,
add spec/README.md, and **delete the hand-written status annotations from
[AGENTS.md](../AGENTS.md)'s quick index**, replacing them with the generated
rows. This is where the maintenance cost identified in incident 2 above
actually comes off.

*Done when:* the quick index carries no hand-written "done/not done" prose,
and regenerating views produces no diff.

### Phase 4 — create `record/` and move the 14 files

Add `record` to `RECORD_DIR_RE` in [tools/doc_lint.py](../tools/doc_lint.py)
**in the same commit** as the first move. Then move, and repoint every
reference in the same commit, per
[rename-updates-links](../practices/rename-updates-links.md).

**References are not only markdown links.** Tool source carries the paths as
string literals — [tools/verify_harness.py](../tools/verify_harness.py)
mentions [spec/LOADER.md](LOADER.md) 9 times, [tools/routing_eval.py](../tools/routing_eval.py)
mentions [spec/ATTENTION_CEILING.md](ATTENTION_CEILING.md) 5 times, and
[.github/ISSUE_TEMPLATE/practice-candidate.md](../.github/ISSUE_TEMPLATE/practice-candidate.md)
carries a full absolute GitHub URL ending in spec/CANDIDATE_FORMAT.md. Sweep the whole
tracked tree for each old path, not just markdown:

```
git grep -n 'spec/PHASE3_BRIEF\.md'
```

Move in ascending order of inbound references, so the cheapest moves prove
the procedure before the expensive ones use it. Approximate inbound markdown
reference counts, 2026-09-07: `PHASE3_BRIEF` 2, `PRIVATE_ENFORCEMENT_BRIEF`
2, `SIMULATION_BRIEF` 2, `PHASE5_DEEPCHECK` 3, `PREFORK_AUDIT` 3,
`NONTECHNICAL_TEAM_PRACTICE_CAPTURE` 4, `PHASE5_BRIEF` 4,
`PRIVATE_SETS_BRIEF` 4, `VERY_DEEP_CHECK` 4,
`NONTECHNICAL_CONTRIBUTOR_ACCESS` 5, `PHASE6_BRIEF` 6, `PRELAUNCH_AUDIT` 6,
`UNBUILT_PLAN_ITEMS` 6, `ATTENTION_CEILING` 14.

*Done when:* `git grep 'spec/PHASE'` and its siblings return nothing, and
the deep check is green.

### Phase 5 — the root tidy

Move [METHOD.md](../METHOD.md), [MOBILE.md](../MOBILE.md),
[GITHUB_ACTIONS.md](../GITHUB_ACTIONS.md) and — if the judgment goes that
way — [GIT.md](../GIT.md) into [documentation/](../documentation/), and
[CHANGES_TO_TELL_ALEX.md](../CHANGES_TO_TELL_ALEX.md) into `record/`. Same
same-commit link discipline.

**Check the external surface before moving anything in this phase.**
[README.md](../README.md), [SETUP.md](../SETUP.md) and
[templates/GETTING_STARTED.md](../templates/GETTING_STARTED.md) are read
outside this repository, and links to them may exist in places this
repository cannot see or fix.

### Phase 6 — [PRACTICES.md](../PRACTICES.md)

Alone in its own phase, because 181 tracked files mention the name and
because it is a genuine judgment call rather than a mechanical one. Confirm
first that [practices/](../practices/) really does carry everything the
pre-split catalogue holds — [spec/PREFORK_AUDIT.md](PREFORK_AUDIT.md) is
the evidence, one row per inherited practice — and if it does not, this move
does not happen yet and the reason is recorded.

**`PRACTICES` is a literal in `RECORD_NAME_RE` in
[tools/doc_lint.py](../tools/doc_lint.py).** Check what moving the file does
to check 6 before assuming the move is inert.

## Decisions the implementer must not re-open

Settled here, so that a session carrying this out does not spend its budget
re-deriving them:

- **Nothing is deleted, and nothing moves to another repository or branch.**
  A separate archive repository breaks every relative link, makes the record
  unreachable from one clone, and creates the second drifting copy the plan
  rejects by name.
- **Frontmatter, not a single central registry file.** This looks like it
  cuts against [registry-source-of-truth](../practices/registry-source-of-truth.md),
  and does not: the collection of frontmatter blocks *is* the registry, in
  exactly the way [practices/](../practices/) already works, and the prose is
  generated from it. A separate registry file would be a second place to
  update on every edit.
- **`record/`, not `archive/`.** Reasoned above.
- **Two axes, not one.** Audience decides the directory; status decides the
  presentation.

## Open questions

Queued rather than answered, each with the reason
([todo-is-a-handoff](../practices/todo-is-a-handoff.md)):

- **Does this become a practice?** The mechanism generalizes — every repository
  adopting Precedent will accumulate planning documents and hit this. Per
  [layered-practice-packs](../practices/layered-practice-packs.md) the format
  is repo-local to Precedent for now (`local/practices/`), and the principle
  is a candidate for the universal catalogue once it has been run here once.
  **Blocked on:** having executed it, so the practice can carry a real
  incident rather than a predicted one ([cite-the-incident](../practices/cite-the-incident.md)).
- **Who else does the exhibit page serve?**
  ([affordance-is-shared](../practices/affordance-is-shared.md).) A generated
  index of every internal document, on a public repository, is also a map for
  anyone reading the project adversarially. Nothing in [spec/](.) is private —
  the leak gate has been over all of it — but the question deserves an
  explicit answer before record/README.md ships, not after.
- **`PREFORK_AUDIT.html`.** Committed build output; decide separately.
- **[GIT.md](../GIT.md)'s destination.** Named above as a real judgment call.

## What happens to this document

It is a `proposal`. When the migration is executed, the "The migration" and
"Open questions" sections are cut to `record/`, as a closed record of how it
was done; the format specification — changes 1 and 2's field tables and
placement test — stays in [spec/](.), which is where a normative reference
belongs under its own rules.

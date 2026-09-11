---
title:         The Enforced Channel (Phase 4)
kind:          reference
status:        current
opened:        2026-08-31
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       "Phase 4's enforced channel: which practices carry a mechanical check, and what each check is blind to."
---
# The Enforced Channel (Phase 4)

What [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s
"[How an Agent Knows Which Practices to Load](../PRACTICE_ENGINE_PLAN.md#how-an-agent-knows-which-practices-to-load)"
calls the fourth loading channel:

> **Enforced.** Practices with `checked_by` are never loaded at all. The
> check's failure message *is* the rule, delivered at the moment of
> violation.

Read the plan section first; this is the implementation note. It also records
the thing phase 4 found before it converted anything, which changed what the
phase was for.

## What phase 4 found before it built anything

Phase 4's starting premise, inherited from the phase-2 measurement, was that
the most-missed practices carried `checked_by: null` and needed converting.
Eight practices already carried one. The first thing phase 4 did was run each
of those four named scripts and watch what happened. **Seven of the eight were
not enforcement at all, and the eighth enforced half of its rule. None of the
eight had ever been watched fire.**

| practice | claimed | what running it showed |
|---|---|---|
| `readers-vocabulary` | [tools/doc_lint.py](../tools/doc_lint.py) | doc_lint has no vocabulary check in it, at all. |
| `acronyms-glossary` | [tools/doc_lint.py](../tools/doc_lint.py) | the acronym check is a **warning**. doc_lint exits 0 on every one it reports. |
| `computed-numbers-in-scripts`, `docs-track-models` | [tools/doc_sync.py](../tools/doc_sync.py) | red on this repository — it read the literal `<!--gen:NAME-->` in two documentation examples as live orphan blocks. |
| `scrub-gate`, `practice-export-loop` | [tools/practice_audit.py](../tools/practice_audit.py) | red on this repository — no `process/manifest*.json`, which is correct for the upstream repo and was reported as `FAIL`. |
| `scripts-assert-properties` | [tools/model_audit.py](../tools/model_audit.py) | `OK: 0 instrumented script(s)` — a clean bill of health from a scan with an empty input set. |
| `doc-references-are-links` | [tools/doc_lint.py](../tools/doc_lint.py) | the one that held. Its strikethrough half gates; its links half warns. |

The harness could not have caught any of this. Its only check on a
`checked_by` was `check_checked_by_targets_exist` — that the named **file** is
present. So "8 of 52 enforced" was never eight. It was eight claims: two false,
four naming gates that had been red long enough that nobody ran them, one
naming a scan of nothing, and one — `doc-references-are-links` — that really
does gate, on the tilde half of its rule, with the links half a warning. Call
the honest starting figure **one of 52, partially, and untested**.

**That is the same failure class as everything else this project keeps
finding**, one level up: a check written against the same assumption as the
thing it checks. Here the assumption was that naming a script is the same as
being checked by it.

## What is here

| Plan's requirement | Built as | Status |
|---|---|---|
| Practices with `checked_by` are enforced | [tools/precedent_check.py](../tools/precedent_check.py) — one registry entry per enforced practice | Built. `--list`, `--only SLUG`, `--paths`, `--range`, `--turn-end`, `--all`, `--strict`. |
| The check's failure message **is** the rule | `rule_of()` reads the practice's own `## Rule` through `split_practices._read_practice_file` | Built. The same reader [tools/precedent_show.py](../tools/precedent_show.py) uses, per "one code path" — a paraphrase in the check would be a second copy of the rule with nothing holding the two together. |
| Each converted practice has a test proving its check fires | `check_precedent_check_fires` in [tools/verify_harness.py](../tools/verify_harness.py) | Built. 53 stated cases against throwaway repositories. |
| A check that cannot run says so | `NotApplicable`, reported as SKIPPED | Built. See below — this is the part that had been getting silently wrong. |
| Coverage materially above 8 of 52 | The registry | Built, and the eight it started from were re-established rather than assumed. |

<!--gen:enforcement-->
| practice | scope | what the check asserts |
|---|---|---|
| `acronyms-glossary` | change | a changed document does not introduce a NEW unglossed acronym -- one not already in GLOSSARY.md and not expanded on first use |
| `catalogue-carries-stories` | tree | every status: active practice in this catalogue carries a non-empty ## Story |
| `ci-commits-carry-identity` | tree | a .github/workflows/*.yml that runs `git commit` resolves the author from a declared identity (an identity.json, or an explicit PRECEDENT_COMMIT_*) rather than naming the github-actions bot or configuring a git identity from nothing |
| `cite-the-incident` | change | a practice file whose Rule is new or changed must carry a non-empty ## Story |
| `code-cites-practice` | tree | a `practice: SLUG` citation in tools/**/*.py names a real, active practice -- never a typo, a deleted file, one since retired, or a position number instead of a slug |
| `computed-numbers-in-scripts` | tree | every generated block in a document matches what its script emits, is registered, and its document names the scripts that feed it |
| `decision-strength` | tree | every `strength:` in a practice file or a decision record holds one of the two defined words, and the file it sits in also records who approved the thing; and every `**Strength:` line in prose records the date it was set and who set it |
| `decommission-deletes-files` | tree | every path this repo declared decommissioned is still absent, and every decommissioning carries the reason it happened |
| `deliverables-look-like-output` | change | a reader-facing document in scope carries no process residue — no verify-later flag, claims-to-source apparatus or decision provenance |
| `doc-references-are-links` | change | a changed document must not render an accidental strikethrough span — use the approximately sign, never a tilde |
| `docs-are-current-state` | change | a changed document does not carry an in-document revision annotation -- an "(added <date>)" / "(rewritten <date>)" tag, or a "Rev N" heading ladder -- since version control already carries that losslessly |
| `docs-track-models` | tree | a figure a script declares it owns is not hand-typed into the prose around its generated block |
| `document-status-header` | tree | every document under spec/ and record/ that CARRIES a lifecycle frontmatter header declares a legal kind/status pair, a title matching its own first heading, a `closed:` date exactly when it is closed, a `superseded_by:` that resolves exactly when it is superseded, and no competing hand-maintained `Last updated:` comment |
| `engine-plus-host-shims` | tree | no file outside the vendored tree duplicates a run of lines from inside it — that is a fork, not a shim |
| `environment-gotchas` | tree | the session instructions carry a "do NOT rediscover these" section, and every entry in it carries what failed, not only the fix |
| `filename-separator` | tree | files of the same kind in one directory use one word separator, never both - and _ |
| `generated-artifact-provenance` | tree | every generated view names the script that builds it and says it is generated, and regenerating it changes nothing |
| `github-setup-disclosed` | change | a newly added GitHub Actions workflow file is named in GETTING_STARTED.md's administrator section -- the document a dependent repo's own people read -- or in a repo's own root GITHUB_ACTIONS.md |
| `heading-outline` | change | a changed document never jumps a heading level -- no heading is more than one level deeper than the one before it |
| `headline-capitalization` | change | a changed outward-facing document has every heading in New York Times headline capitalization |
| `index-remembers-past` | change | a changed document does not carry inline lineage language naming what it replaced or what replaced it, since provenance belongs in the repository index, not annotated into the documents themselves |
| `label-describes-content` | change | a heading or bold lead-in that claims "one line" / "one-liner" / "TL;DR" / "one paragraph" / "one-pager" must match the length of what actually follows it |
| `layered-practice-packs` | tree | every practice in force in this repo is reachable by at least one loading channel here -- resident, occasion index, a path trigger, a gate, or a running check |
| `migration-scrubs-vocabulary` | tree | a migrated repo carries no leftover pre-migration practice pack (process/manifest_*.json and its tree), and -- where the repo has declared process/retired_vocabulary.json -- none of its listed terms outside the declared exempt files/directories |
| `no-rewrite-for-warnings` | turn-end | the commit this branch was last published at is still an ancestor of its tip — published history has not been rewritten |
| `no-version-suffix` | change | a file added by this change must not carry a version, date or state suffix in its name |
| `open-item-disposition` | tree | every `**Disposition:` line in a TODO file names one of the three dispositions, and a `parked` or `ask` line records the date it was set and who set it |
| `orientation-map` | tree | MAP.md exists at the repository root, is not empty, and the session instructions point at it |
| `parallel-artifact-ledger` | tree | `templates/harness/LEDGER.md` exists, and every commit that touched a harness-adapter member (claude-code/, codex/, or gemini-cli/) has its hash referenced somewhere in the ledger |
| `practice-export-loop` | tree | every manifest entry marked synced still matches its baseline — a local improvement to a vendored file has been exported, not absorbed |
| `practice-links-travel` | tree | every link in a practice file THIS repo owns either travels with the file (a sibling practice, a vendored engine file) or is an absolute URL into this repository on its declared base_branch, naming a path that exists |
| `quick-index` | tree | the session instructions carry a "looking for X → go to Y" table with at least five rows |
| `rename-updates-links` | tree | no tracked file still references a path this branch renamed away or deleted |
| `routing-audit` | tree | tools/routing_audit.py exists, and tools/routing_audit_state.json (if present) has no rotation entry for a practice that is not currently active |
| `scripts-assert-properties` | tree | every instrumented script asserts its own properties, and every figure it recites from a source document still matches that document |
| `scrub-gate` | tree | every text file in a vendored tree destined for another repo is clean against that tree's blocklist, at all times |
| `search-by-purpose` | change | a document carrying generated numbers is reachable from an index a reader actually consults |
| `session-bootstrap` | tree | if the session instructions name a setup command, a session-start hook must run it |
| `source-naming` | tree | every precedent.json in the tree names each source by the shape its level fixes -- `precedent`, `precedent-individual`, `precedent-team-<slug>`, `local` |
| `speculation-is-marked` | tree | a speculative document under spec/ or record/ carries all four of its markers or none of them: the SPECULATIVE_ filename prefix requires a matching title, `kind: proposal`, a drafted/abandoned status and a warning block directly under the heading -- and, in the other direction, a document whose title or opening paragraph calls itself speculative must carry the prefix |
| `technical-describes-people` | tree | no tracked path labels a FILE or DIRECTORY with a skill level; 'technical' and 'non-technical' describe people |
| `timestamps-carry-offset` | tree | no tracked Python file stamps a moment with a bare `date.today()`, `utcnow()`, `utcfromtimestamp()` or a zero-argument `datetime.now()` -- every one of those resolves to whatever zone the machine is on, which in a container is UTC and in a record is unrecoverable. And the declared fallback zone is the SAME string in all three places that hold it: precedent.json, the time engine, and the commit hook |
| `two-check-levels` | tree | the session instructions name two fixed, distinct check levels ("light check" / "deep check") and say which gates a commit versus a push |
| `verify-postcondition` | turn-end | the state you wanted after the operations this turn: nothing committed but unpushed on any local branch, and no tracked file left modified |

44 of 95 practices are enforced. Run `python3 tools/precedent_check.py --explain` for what each check does **not** catch.
<!--/gen:enforcement-->

Numbers by: catalogue_stats.py

## A skip is not a pass

Every graceful-failure path here ends in `SKIPPED` with a reason, and the
summary line says so in those words:

```
precedent_check: N passed, 0 violated, 0 advisory, 0 errored, M skipped (a skip is not a pass; advisory findings do not fail the run).
```

(0 violated is what matters here — the passed/skipped counts grow as
checks are added or as more of a clean tree happens to be in scope for a
`change`-only check, so a literal N/M pinned into this example goes stale
by design; this document had one and a 2026-09-01 deep-check audit found
it already wrong. `errored` is a fourth, later-added status, 2026-09-03:
a check that raised something other than `NotApplicable` — its own bug
hitting an edge case it didn't validate for, not a real-or-clean verdict
either way — fails the run exactly as a violation does, rather than
taking every other check in the same run down with it as an uncaught
exception used to. `advisory`, a fifth status, 2026-09-05: not a general
severity dial — `check()`'s own `advisory` parameter is reserved for a
specific, dated, documented incident, currently only
`parallel-artifact-ledger` (see its own comment in
[tools/precedent_check.py](../tools/precedent_check.py) and
[TODO.md](../TODO.md)'s tracking item). An advisory finding still prints
in full; it just doesn't fail the run.)

This is not fastidiousness. Three of the four inherited scripts were failing
in one of the two ways a check can fail without failing. Two exited non-zero
for a reason that had nothing to do with the practices claiming them —
[tools/practice_audit.py](../tools/practice_audit.py) because a precondition
was absent (no `process/` directory in a repo that vendors nothing),
[tools/doc_sync.py](../tools/doc_sync.py) because it read a documentation
example as a live block. The third exited **zero** on an empty input list. The
first kind gets ignored until nobody runs it; the second kind gets believed.
All three were fixed at the source rather than worked around, so the
underlying tools now report NOT APPLICABLE with the reason, and
`precedent_check` passes that through as a skip.

Three checks skip in this repository as a permanent and correct condition:
`scrub-gate`, `practice-export-loop` and `engine-plus-host-shims` all describe
the boundary between a vendored upstream and its host, and this repo **is**
the upstream. Their firing tests build the vendored tree in a fixture, so the
checks are verified even though this tree cannot exercise them.

## Scopes, because a practice is not always a property of a file

- **`tree`** — a property of the repository as it stands. An index exists; the
  generated views are current; the gotchas section carries stories. Always
  runs.
- **`change`** — a property of what a change adds or edits. A new practice
  carries its incident; an added file is not named for its version. Runs
  against the files in scope (changed vs. `HEAD` by default, `--paths` or
  `--range` to say otherwise).
- **`turn-end`** — the state you wanted *after* an operation. Nothing
  committed but unpushed; published history not rewritten. **Excluded from the
  default run**, because mid-work an unpushed commit is not a violation. This
  is where a Stop hook calls it.

The third scope exists because `verify-postcondition` and
`no-rewrite-for-warnings` are not properties of a diff at all, and forcing
them into the default run would have made the gate red during ordinary work —
which is how a gate stops being run.

## How each check was established not to be a test that passes on a bug

Two directions per practice, and then a mutation of the whole registry.

**Both directions.** `check_precedent_check_fires` copies this tree into a
scratch repository, plants the violation the practice exists to prevent, and
requires a non-zero exit — and then requires the *same tree unplanted* to come
back clean. The second half is not ceremony. The first version of the
`quick-index` check counted table rows from the end of its regex match, which
is the middle of the header line, and so reported **zero rows** on a table
with thirty-two. It would have fired on the planted violation perfectly. What
caught it was running the check against this repository and reading what it
said — which is exactly the property the clean direction now asserts on every
harness run. The same thing happened again later, on `no-version-suffix`,
which reported this session's own preserved eval baseline as a versioned
file name.

**The whole registry, neutered.** Every check was then replaced with one that
returns no findings, and the harness re-run. It named all eighteen. A check
that has stopped looking now fails a check.

**One check was rewritten because it fired on correct work.** The first
`environment-gotchas` check looked for failure *words* — failed, broke,
silently, cost — and reported a genuine story told in other words ("a smoke
test believed it was exercising a shallow clone for an hour and was not") as a
bare fix. A check that fires on correct work gets switched off, and is then
absent when an entry really is a bare command. It now tests structure
(an entry that is one short sentence is a bare fix) and says plainly, in
`--explain`, that padding defeats it.

## Every check carries what it does not catch

`python3 tools/precedent_check.py --explain` prints, for each practice, what
the check asserts **and what it is blind to**. That belongs beside the check
rather than in a document that drifts from it, and it is the honest answer to
the question an enforced practice invites: if this is checked, is the prose
redundant? For most of these, no:

- `environment-gotchas`' check guards the *artifact* — the section exists,
  the entries carry stories. It cannot see a discovery that was never written
  down, which is the failure the practice is actually about.
- `verify-postcondition`'s check asserts two named postconditions for this
  repository at turn end. The Rule's instruction — *name the postcondition
  before you run the command* — governs every state-changing operation, almost
  none of which any check knows about.

**So the plan's phase-4 instruction to "drop their prose from the resident
tier" was not followed for these two, and the reason is worth recording rather
than quietly skipping:** that instruction assumes a check is coextensive with
its rule. Where it nearly is — `quick-index` asks for a table in the
instructions file, and the check asserts one is there with rows in it, though
not that they are the right rows — dropping the prose costs little. Where it is not, dropping the prose
trades a preventive channel for a detective one that cannot detect the case in
question. Four of the six resident practices now carry a check and all six stay
resident.

## What the routing eval says, and what it cannot

See [spec/LOADER.md](LOADER.md)'s v4 section for the numbers. The important
structural point belongs here, because it is about enforcement rather than
about the loader:

**Phase 4's done-when — "the routing eval re-run shows the converted practices
no longer missed" — is not, read literally, something conversion can deliver**,
and the plan says so itself two sections earlier: an enforced practice is
"never loaded at all". A practice with a working check is deliberately absent
from the routing question. The arm that routes will keep missing it, and
should.

So `python3 tools/routing_eval.py --enforcement` reports the miss set by
**what now covers it** instead, which is the question the done-when was
reaching for. Its own output states the limit, and so does this: a check being
in scope means the violation would be *caught* if the change committed one. It
does not mean these particular commits violated anything — most did not — and
it is not evidence that a session complied. **Coverage, not compliance.**

## Reach and enforcement are two problems

Phase 3's brief flagged this and phase 4 confirmed it from both ends.

`practice-export-loop` was the largest single miss in the v3 run, 8 of 10,
while carrying both a `checked_by` and a narrow `applies_to`. Its glob was
`process/upstream/**` — where an export **lands**, which is the one place a
change cannot have touched *before* the export gate is supposed to fire. The
practice's own occasion is a thread that improved a generic practice, and in
this repository generic practices live in [PRACTICES.md](../PRACTICES.md),
[practices/](../practices), [templates/](../templates) and
[tools/](../tools). The glob now names those. That is a correction to a scope
statement, not a tuning of the index — the plan's
[What NOT to do with this result](../PRACTICE_ENGINE_PLAN.md#what-not-to-do-with-this-result)
forbids the second, and names "a narrower glob" as exactly what a
repeatedly-unrouted practice should get.

**A dependent repo may need to narrow this again.** `templates/**` and
`tools/**` are where *this* repo keeps practice text; in a host repo they are
the host's own files. That is what a source at a lower level overriding a
universal practice is for.

The result, and the reason to state reach and enforcement separately: the
misses on that practice halved, and **every one that remains is a case where
the path channel surfaced it and the session declined it anyway.** Reach was a
real problem and is now fixed for this practice. What is left is not a reach
problem.

## A materialized check cannot carry per-repo data

Found 2026-09-07, from a real consumer install rather than from reading.
[precedent_materialize.py](../tools/precedent_materialize.py) copies each
source's `tools/checks/check_*.py`
byte-identically into the consuming repo's own `tools/checks/`, and deletes
and rewrites that whole directory on every
[precedent_sync_views.py](../tools/precedent_sync_views.py) run. Two
consequences follow, and only the first is already written down (in
[AGENTS.md](../AGENTS.md)'s gotchas): a check script hand-added there
survives until the next sync, so it belongs under its source's own declared
`path`.

The second is about the script's *contents*, and is easy to miss because the
file is in the right place and the check works. **A check that keeps
repo-specific data as a constant in the script can never be extended by the
repo it runs in.** The consumer cannot edit the materialized copy — it is
overwritten. Editing the source instead means putting one consumer's data
into a team or individual set that several repos share, which is worse. The
data has nowhere correct to live.

The case that surfaced it: `check_commit_author.py` and
`check_buenos_aires_dates.py` in `precedent-individual` both held a
`GRANDFATHERED_SHAS` constant listing commits exempt from the rule. Those
SHAs are `precedent-individual`'s own history. A consuming repo with its own
pre-mechanism commits to grandfather had no way to say so — the exemption
existed, and was unreachable from the only place that needed it. The fix was
to move the list into a per-repo `identity.json` the checks read at runtime,
unioned with whatever the script still hardcodes.

**So: a check's LOGIC materializes; a check's DATA must not.** Anything that
varies per repository — exempt commits, a repo's own branch names, paths,
people — is read at runtime from a file in the repo being checked, never
baked into the script that the sync will overwrite. A useful test while
writing one: *if a second repository installed this check tomorrow, is there
anything it would need to change inside the file itself?* If yes, that thing
is data, and it belongs in config.

The same audit carried a second lesson worth stating beside it. The
grandfather list was assembled from what an open item had recorded — two
commits. Auditing the branch's actual history found **eight**, none of them
overlapping the recorded two. A written record of which commits violate a
rule is a summary of a past reading, not the reading; the history itself is
the source of truth, and this is
[verify-decomposition](../practices/verify-decomposition.md) ("check the
parts, not the total") in the one form that costs real work to get right.

## What is still not enforced, and why not

Three practices in the remaining miss set carry no check, deliberately:

- **`mistakes-become-rules`** is the largest of them, and the phase-3 brief
  called this correctly: any check for it has to carry the **proportionality
  guard** that decides whether the practice fires at all, not just the
  encode-the-prevention half. A check that fires on every defect fix would mint
  a rule for every slip, which is the failure this plan opens by diagnosing.
  Detecting "this defect was worth a rule" from a diff is not something phase 4
  found an honest signature for, and a dishonest one would be worse than none.
- **`registry-source-of-truth`** and **`merge-runbook`** are properties of a
  repository's design, not of its files. Nothing phase 4 could write would
  distinguish "state lives in one registry" from "state happens to live in one
  place today".

Four other gaps are structural rather than judgment calls, and are worth
naming so nobody reads a skip as a decision: `computed-numbers-in-scripts`,
`docs-track-models`, `search-by-purpose` and `scripts-assert-properties` were
all skipping in this repository because nothing was registered for them to
check. [tools/catalogue_stats.py](../tools/catalogue_stats.py) closed all four
at once, and it exists because this repository was committing the exact failure
`docs-track-models` describes: [spec/LOADER.md](LOADER.md)'s status table said
the resident block was "~621 tokens" for the whole of phase 3, which had halved
it. Every gate was green, because no gate can see a number in a sentence.

## What phase 5 inherits

- **The registry is the place a new check goes.** Adding one means a case in
  `check_precedent_check_fires` in the same commit, or the harness fails: the
  registry and the case table check each other in both directions.
- **`--explain` is the contract.** A check whose `blind_to` line is empty or
  vague is a check nobody can calibrate against.
- **The creation pipeline should ask for a check, not a `checked_by`.** The
  thing phase 4 found is that the field is easy to fill in and the check is
  not; a promotion step that accepts a string has re-created the problem.
- **This channel exists only for the universal catalogue.** Both private
  sets' practices carry `checked_by: null` with no infrastructure to change
  that — [tools/precedent_check.py](../tools/precedent_check.py) is written
  against this repo's own tree and cannot run against a private set from
  here. [spec/PRIVATE_ENFORCEMENT_BRIEF.md](PRIVATE_ENFORCEMENT_BRIEF.md)
  hands off what a session opened directly against one of those repos needs
  to close the gap; phase 5's creation pipeline should not have to
  rediscover it.

<!-- Last updated: 2026-08-31 (Buenos Aires) by the phase-4 build session -->

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
| Each converted practice has a test proving its check fires | `check_precedent_check_fires` in [tools/verify_harness.py](../tools/verify_harness.py) | Built. 39 stated cases against throwaway repositories. |
| A check that cannot run says so | `NotApplicable`, reported as SKIPPED | Built. See below — this is the part that had been getting silently wrong. |
| Coverage materially above 8 of 52 | The registry | Built, and the eight it started from were re-established rather than assumed. |

<!--gen:enforcement-->
| practice | scope | what the check asserts |
|---|---|---|
| `acronyms-glossary` | change | a changed document does not introduce a NEW unglossed acronym -- one not already in GLOSSARY.md and not expanded on first use |
| `cite-the-incident` | change | a practice file whose Rule is new or changed must carry a non-empty ## Story |
| `computed-numbers-in-scripts` | tree | every generated block in a document matches what its script emits, is registered, and its document names the scripts that feed it |
| `deliverables-look-like-output` | change | a reader-facing document in scope carries no process residue — no verify-later flag, claims-to-source apparatus or decision provenance |
| `doc-references-are-links` | change | a changed document must not render an accidental strikethrough span — use the approximately sign, never a tilde |
| `docs-are-current-state` | change | a changed document does not carry an in-document revision annotation -- an "(added <date>)" / "(rewritten <date>)" tag, or a "Rev N" heading ladder -- since version control already carries that losslessly |
| `docs-track-models` | tree | a figure a script declares it owns is not hand-typed into the prose around its generated block |
| `engine-plus-host-shims` | tree | no file outside the vendored tree duplicates a run of lines from inside it — that is a fork, not a shim |
| `environment-gotchas` | tree | the session instructions carry a "do NOT rediscover these" section, and every entry in it carries what failed, not only the fix |
| `generated-artifact-provenance` | tree | every generated view names the script that builds it and says it is generated, and regenerating it changes nothing |
| `github-setup-disclosed` | change | a newly added GitHub Actions workflow file is named somewhere in GITHUB_ACTIONS.md, where this project's people read about GitHub-specific setup |
| `label-describes-content` | change | a heading or bold lead-in that claims "one line" / "one-liner" / "TL;DR" / "one paragraph" / "one-pager" must match the length of what actually follows it |
| `no-rewrite-for-warnings` | turn-end | the commit this branch was last published at is still an ancestor of its tip — published history has not been rewritten |
| `no-version-suffix` | change | a file added by this change must not carry a version, date or state suffix in its name |
| `orientation-map` | tree | MAP.md exists at the repository root, is not empty, and the session instructions point at it |
| `practice-export-loop` | tree | every manifest entry marked synced still matches its baseline — a local improvement to a vendored file has been exported, not absorbed |
| `quick-index` | tree | the session instructions carry a "looking for X → go to Y" table with at least five rows |
| `scripts-assert-properties` | tree | every instrumented script asserts its own properties, and every figure it recites from a source document still matches that document |
| `scrub-gate` | tree | every text file in a vendored tree destined for another repo is clean against that tree's blocklist, at all times |
| `search-by-purpose` | change | a document carrying generated numbers is reachable from an index a reader actually consults |
| `session-bootstrap` | tree | if the session instructions name a setup command, a session-start hook must run it |
| `verify-postcondition` | turn-end | the state you wanted after the operations this turn: nothing committed but unpushed, and no tracked file left modified |

22 of 52 practices are enforced. Run `python3 tools/precedent_check.py --explain` for what each check does **not** catch.
<!--/gen:enforcement-->

Numbers by: catalogue_stats.py

## A skip is not a pass

Every graceful-failure path here ends in `SKIPPED` with a reason, and the
summary line says so in those words:

```
precedent_check: 13 passed, 0 violated, 3 skipped (a skip is not a pass).
```

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

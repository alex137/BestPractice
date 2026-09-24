---
slug:              todo-2026-09-21-pass-4-branch-verdicts-and-catalogue
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "the seven source-repo branch verdicts need a session rooted in themorgan/precedent-individual or themorgan/precedent-shared-* to act on; this session could reach none of them"
noted:             2026-09-21
closed:            null
---
## What

Pass 4 of the 2026-09-21 very deep check: real verdicts on every unlanded
branch, the backlog read, and as much of the catalogue judgment as one
session could honestly do.

## 1. Branch Verdicts — Every Count Verified Against the Real Diff, Not the Table

**Only one branch in this checkout carries work that has not landed.**

| Repo / branch | Verdict | Why |
|---|---|---|
| `claude/chief-of-staff-uncommitted-review-ppt6v0` | **MERGE**, practice/doc files only | The one genuinely unlanded piece here. Widens `chief-of-staff` to sweep branches carrying commits outside the base branch and give each a verdict, recording Morgan's own 2026-09-20 instruction verbatim. None of it is on the tip. Take `practices/chief-of-staff.md`, `practices/very-deep-check.md`, `AGENTS.md`, `documentation/DAILY_HABITS.md`. **Do not take `record/stale_branches.md` or `record/very-deep-check-ledger.json`** — run artifacts; merging them reverts every run since 2026-09-20. Both practice files conflict, and `very-deep-check.md` is owned by another live session, so that half needs sequencing. |
| `claude/bootstrap-drift-pycache-exclusion-kgtw57` | **CLOSE**, after lifting two hunks | Reverses the 2026-09-19 run's "MERGE after a small rebase". Both substantive halves landed by other routes (`-B` at `precedent_resolve.py:173`, the `__pycache__` exclusion as `10d90d6b`, the planted case live in `verify_harness.py`). Not landed: the `_bootstrap_with_stray_pyc` regression test, and a slightly wider exclusion catching a stray `.pyc` outside a `__pycache__` directory. Merging conflicts; lift those two by hand. |
| `claude/harness-clone-count-1i9qoq` | **CLOSE** | Reverses the 2026-09-19 run's MERGE. The `status: drafted` proposal was overtaken five days after it was written: its tier 1 and tier 3 landed in `4e3dc498` and `b926527b`, and its on-demand full sweep landed as `PLANTED CASE COVERAGE` plus `verify_harness.py --all`. Merging a drafted proposal whose proposals are already implemented by a different design puts a misleading document in `spec/`. If kept, it must land `status: superseded` naming those commits. |
| `claude/file-sharing-service-spec-0m9c7p` | **ASK ALEX — already asked, unanswered** | [Issue #394](https://github.com/alex137/BestPractice/issues/394) is open since 2026-09-14 and poses the exact question. **Nothing about the branch has changed; what is overdue is the answer.** `share/` exists on no other branch, so this is the one branch whose closure discards something real. |

**No pull request has ever existed for any of the four** — confirmed via
`list_pull_requests` with a head filter and `state: all`, so each gets a
compare-view link rather than an implied PR.

**Seven branches in the source repos, all CLOSE, all decided by content**
because GitHub is unreachable for those owners from here:
`claude/quirky-pasteur-e997ei` (competing rewrite of a decision `main`
already carries, in a fuller form); `claude/kind-gates-a1cdv7` and
`fix/findings-doc-upstream-correction` (both still unmeasurable after
`--unshallow` — the clone stays grafted — but settled by content: the
unique change is already on `main`, and merging either would revert
~15,000 lines of vendored engine); `fix/retire-buenos-aires-dates-duplicate`
and `fix/retire-individual-practice-duplicates` (their files are already
gone from `main` by a parallel route); `claude/stale-counts-multi-source-bug-v4evl6`
(`main` has a strictly better fix for the same bug — merging would
regress it). **One MERGE among them:**
`claude/sweet-sagan-w2nvw1` in the individual set repoints two links in
`closing-items-are-this-thread.md` from a `deduplicated` practice to the
live one; small, correct, merges clean, not landed.

**And one tool finding dressed as a branch:**
`claude/festive-goodall-qr1eck` is an add-and-revert pair —
`git diff <merge-base> <branch>` is **empty**. `git cherry` counts both
commits as unlanded, which is technically true and substantively
meaningless. **The unmerged-branch scan should recognise a net-empty branch
and say "nothing to merge, safe to delete"** rather than demanding a
verdict on two commits that cancel.

## 2. The Backlog

**The structural finding, which matters more than any single row: 46 of
the 128 open items have `## How It Closes` = "(not yet stated by the
migration…)".** More than a third of the backlog has no closing condition
at all, which makes *"an item closes only when its OWN stated condition is
met"* unenforceable for those 46 by construction — they can only ever be
closed by resemblance, which the rule forbids. **Filling those in is a
bigger lever than working any individual item.**

**Both "blocked_on names something gone" rows are false positives.**
`todo-2026-09-14-classic-install-wires-loader-hooks` is flagged for
`process/upstream`, which is the classic install layout *inside a consumer*
and by design never exists upstream;
`todo-2026-09-14-consumer-hears-about-files-it-does-not-have` is flagged
for `tools/ENGINE_MANIFEST.json`, which BestPractice correctly lacks
because it **is** the engine. Neither item's real condition is met, so
neither should be touched — but the scanner should resolve `blocked_on`
path tokens only for items about this repo's own tree, or report
`unresolved` rather than `gone`. Two of two rows wrong is the rate at which
a section stops being read.

**The oldest item is arguably closeable and needs Morgan to say so.**
`todo-2026-07-19-two-published-commits-carry-the-wrong-timezone-offset`
(64 days) asks for *"a decision about which layer carries it, since the
hook demonstrably cannot"*. Its unblocked half is done
(`precedent_refresh_sources.py` now writes `Session: {url}`). The blocked
half now has a mechanism that did not exist when it was written — the
**global commit backstop** (`git config --global core.hooksPath`, audited
by `precedent_session_check.py`) is precisely an answer to "which layer
reaches a repo attached later in the session", and `precedent_time.py`'s
repo-level `fallback_timezone` rung adds to it. No decision record names
this as *the* answer, so this proposes rather than closes.

**Of the ten oldest, four cannot be met at all** — their closing condition
is the migration placeholder. Three reminders are 7+ days overdue and none
has been surfaced; one of them says to raise its permanent fix *when Morgan
asks for `Three Things`*, which nothing tracks.

## 3. The Catalogue Read

**Done:** a complete first-order pass over all 140 universal files —
frontmatter, plus the `occasion` and `index_clause` of all 133 active
practices read end to end — a full six-source resolve, and targeted full
reads of about a dozen where the first pass raised a question.

**Not done, stated plainly:** the 192 resolved practices were not read
Rule-by-Rule one at a time; the 59 in the sibling sources got only the
resolver's view. **The ledger's standing "full sequential catalogue
judgment has never been completed" is still true after this run.** This
narrows it.

### The finding

**Two of the four `engine-dev` practices are silently scoped back to every
adopter.** [spec/PRACTICE_FORMAT.md](../spec/PRACTICE_FORMAT.md) names four
as the clearest cases: `very-deep-check`, `full-practice-audit`,
`routing-audit`, `parallel-artifact-ledger`. On the tree only the last two
carry it — the first two carry **`scope: null`**, which is not one of the
two legal values the spec declares (`any-adopter | engine-dev`). Verified
in this checkout:

    very-deep-check       scope: null          engine_dev = False
    full-practice-audit   scope: null          engine_dev = False
    routing-audit         scope: engine-dev    engine_dev = True

`build_views._is_engine_dev_scoped` compares for the literal string, so
`null` falls through to the default and `precedent_materialize.py` copies
both into **every consuming repo**. `very-deep-check.md` is 25,208 words,
by far the largest file in the catalogue — so this is precisely the adopter
token tax the field was added on 2026-09-15 to remove, quietly restored.

**Nothing validates the field, and the spec says so itself:** *"Nothing in
`verify_harness.py` validates that `scope:` holds one of its two legal
values… Per `checkable-gets-checked` this is owed a check before the field
is more than advisory."* It was owed, it was not built, and the gap has now
bitten. `source-sets-run-no-ci` and `their-constraints-are-given` also
carry `scope: null`; for those it is only a wrong spelling of "absent".

**Fix:** set both to `engine-dev`, and build the validation the spec
already says is owed. Not done here — `very-deep-check.md` is owned by
another live session right now.

#### Resolved 2026-09-22 — and the finding above has it backwards

**The tree was right and the spec was stale.** `very-deep-check` and
`full-practice-audit` each declare a standing `command:` ("Very deep
check", "Practice check"), and `engine-dev` withholds a practice from a
consuming repo's materialized `practices/` — so a person says the words in
their own project, the session has no such practice, and nothing happens
for a reason nobody in that room can see. Morgan untagged both on
2026-09-21 for exactly that reason (`8b5aba96`) and registered
[vocabulary-reaches-the-consumer](../tools/precedent_check.py) to stop it
recurring. **Setting them back to `engine-dev` produces a violation naming
both files** — measured, not reasoned about, before anything was written.

The disagreement ran the other way too: `cross-source-rollout` was tagged
`engine-dev` on 2026-09-15 by a classification sweep that never touched
the paragraph naming the tagged practices. So the spec's list of four was
wrong in both directions, and the only thing that read the two against
each other was a person.

**What landed instead:** the `scope` section of
[spec/PRACTICE_FORMAT.md](../spec/PRACTICE_FORMAT.md) now names the three
practices actually tagged, records why the two command-carrying ones are
not, and states that `scope: null` is not a third value — the one null
policy in [tools/split_practices.py](../tools/split_practices.py) drops a
`null` field before any consumer sees it, so `scope: null` and no `scope:`
line are the same input everywhere downstream and **no check can recover
the difference**. `check_scope_field_is_legal_and_matches_this_spec` in
[tools/verify_harness.py](../tools/verify_harness.py) is the owed
validation: legal values, the repo-local `engine-dev` redundancy, and the
spec's own list compared against the tree. The value check alone would not
have caught this and does not claim to; the list comparison is the part
that would.

**No adopter token tax was restored, because nothing was ever withheld.**
[very-deep-check.md](../practices/very-deep-check.md) travels to consumers
on purpose, so its size there is
a live question — but it is the cost of the command working, not drift, and
it belongs to whoever reopens the command-vs-size trade, not to this item.

### Four more, smaller

  - **Ten active practices are in force with no recorded approval** —
    `approved_by: "pending review"` or `"pending PR review"` on
    `checkable-gets-checked`, `code-cites-practice`, `disclose-landing`,
    `full-practice-audit`, `github-api-budget`,
    `migration-scrubs-vocabulary`, `routing-audit`,
    `todo-migrate-available-but-unused`, `push-back`, `small-calls`. Each
    binds every adopter today. `decision-strength` says unmarked means
    UNKNOWN; **"pending" says something stronger — that the review was
    expected and never happened.**
  - **Four universal practices are overridden everywhere they could fire
    here** (`push-back`, `doc-references-are-links`, `small-calls`,
    `session-title-names-the-difference`). Not dead — an adopter declaring
    none of those sources still gets them — but worth a level question
    under `rule-level-by-reach`.
  - **`todo-migrate-available-but-unused` can no longer fire in this repo
    at all** (`applies_to: ["TODO.md"]`, which is a stub CI refuses PRs
    against). Still live for unmigrated adopters, which is the case it was
    written for — but it is a transitional practice with no stated
    retirement condition and should carry one.
  - **`the-boildown` has an empty `occasion:`**, so it reaches a session
    only through the `reply` gate and never through the occasion index.
    Every other active practice has one.

**And one real result:** the resolve itself is clean. 192 practices from 6
sources, no slug conflict, no `IN FORCE NOWHERE`, no within-source
contradiction; the ≈15 slugs appearing in two shared sets at once are all
correctly carried as `deduplicated` stubs. The layering mechanism works.

**One consolidation candidate, cheapest on the board:**
`computed-numbers-in-scripts` and `docs-track-models` share one checker and
the second opens by saying it *extends* the first.

## 4. The Eight Quiet Sections — Keep, Cheapen, Retire

**Three of the eight are not quiet at all. They are unable to run, and the
ledger has been scoring "could not determine" as "found nothing" for 21, 16
and 14 runs.** That miscategorisation is worth more than any individual
verdict: the ledger should distinguish `clean` from `undetermined` in its
FOUND NOTHING list the same way it already distinguishes `COULD NOT
MEASURE` for `UNLANDED WORK`.

| Section | Verdict | Reason |
|---|---|---|
| MACHINE-READABLE FILES | **KEEP unchanged** | The only whole-tree parse anywhere, deliberately split from the deep check's changed-files scope. 565 files, one line, 0.1s. Nothing to cheapen. |
| REPOS IN FORCE | **KEEP, CHEAPEN the print, stop calling it clean** | Blind, not quiet: *"1 of 5 answered; 4 could NOT be determined"*, scored `clean`. Four near-identical 60-word "not checked" notes are most of the 503 tokens. |
| WITHIN-SOURCE CONFLICTS | **KEEP, and name the gap** | 35 tokens across six catalogues is free — but it tests a narrow proxy, not the thing the practice asks for (two Rules in one catalogue pulling opposite ways), which the practice itself says is not built. The output line should say what it does not cover. |
| ORPHANS | **KEEP unchanged** | 44 tokens; the mechanical half of `decommission-deletes-files`, a practice that exists because this failure happened. Never firing in a month of decommissioning is evidence it works. |
| REPOSITORY VISIBILITY | **KEEP, and fix it so it can run** | Worst of the three: 50 of 52 repos unchecked **and** both offline halves skipped for want of a blocklist path — in the one section pass 4 names as the only place leak recommendations are raised. Default the blocklist path, exclude fixture owners, report `undetermined`. |
| GITHUB API BUDGET | **CHEAPEN** | ~200 of 396 tokens are three static notes explaining why three limits are unmeasurable, reprinted verbatim every run. Keep the numbers; move the prose behind a flag. |
| CONTRIBUTOR BOUNDARY | **CHEAPEN** | Four of nine rows are `none -- draws no boundary` for repos that never will, printing identically forever. Collapse to a count; print `current`/`stale` in full. |
| VENDORING EXCLUSIONS | **RETIRE the line, keep the code** | Structurally incapable of finding anything *here*: BestPractice is the upstream, so `N/A: not a vendored consumer` is true on every run forever. Real when the tool runs inside a vendored consumer. Print nothing when the repo is not one. |

---
title:         "Open Items and Gotchas: What to Split, What to Retire, What to Just Do"
kind:          proposal
status:        drafted
opened:        2026-09-14
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Both TODO.md and the gotchas index capture mechanically and drain by hand, so both only grow. Classifies the 57 live open items by who can clear them, proposes splitting the file along that line, and gives the gotchas an exit condition per entry.
---
# Open Items and Gotchas: What to Split, What to Retire, What to Just Do

**Nothing here is done.** This is the written-up version of a 2026-09-14
conversation, for review. Every figure in it is a measurement taken that day
against `precedent-beta-v01` at `6fc0596` — a snapshot, not a live rollup, so
read the counts as *what it looked like on the 14th*.

## What I Am Asking You to Decide

Six things, each independent. Say yes to any subset.

| # | Decision | If yes | If no |
|---|---|---|---|
| 1 | Prune the 34 closed items out of [TODO.md](../TODO.md) | The file halves; closed items keep their anchors in a record file | The file keeps growing; over half of it is history |
| 2 | Split [TODO.md](../TODO.md) by **who can clear an item** | Four smaller files, each with one reader | One file serving four readers, as now |
| 3 | Treat the 18 source-set items as **one project**, not 18 items | One checklist, one sweep, four sessions | 18 separate items, each re-orienting from scratch |
| 4 | Give me a standing rule for the 16 unblocked engine defects | Either they get fixed on sight or they get closed | They accumulate; nothing says which |
| 5 | Add a **`Retires when:`** line to every gotcha | Each entry states what would kill it; a pass can ask | The index grows monotonically, as it has |
| 6 | Backfill that line on the five gotchas that already claim a fix landed | Those five can be tested and likely archived | They stay live and every session reads them |

**My recommendation: yes to 1, 3, 5 and 6 now; 2 after 1 (pruning changes what
the split looks like); 4 is the one genuinely worth arguing about.**

## The Diagnosis Both Files Share

Both are **captured mechanically and drained by hand.**

- [capture-gate](../practices/capture-gate.md) fires at every merge, and
  "write down what just cost you an hour" fires whenever a session gets burned.
  Neither needs anyone to decide anything.
- Nothing expires on its own.
- Draining — pruning a closed item, archiving a retired gotcha — waits for
  somebody to feel like doing it.

A pump with a mechanical trigger and a discretionary drain only runs one way.
That is the whole story, and it is not a failure of discipline: the capture
side is working exactly as designed, and [repo-is-memory](../practices/repo-is-memory.md)
is why it should keep working that way.

**The gotchas file already had half this fixed.** The 2026-09-13 split put a
one-line index in [AGENTS.md](../AGENTS.md) and the stories in
[record/GOTCHAS.md](../record/GOTCHAS.md), which flattened the *reading cost*
and left the *count* alone. TODO.md has had neither fix: it is still one file,
read whole.

## TODO.md On 2026-09-14

91 numbered items. **34 are marked done or half-closed and still in the file.
57 are live.** The file is 47,854 words; roughly half of that is history.

Age of the 57 live items, by the day each anchor first appears in the file's
history (which only reaches 2026-09-06 — anchors were introduced then, so
"≤09-06" means *at least* that old):

```
≤09-06  17      09-10   5      09-13   5
 09-07   1      09-11  12      09-14   7
 09-08   2      09-12   3
 09-09   5
```

**Forty of the 57 were written in the last eight days**, at roughly five a day.
That is not a backlog that built up over months; it is the current rate.

### The Classification That Matters: Who Can Clear It

Sorting by subject produces five piles that all look equally stuck. Sorting by
**who or what has to move first** produces one useful finding:

| Group | What it is | Items | Who clears it |
|---|---|---|---|
| A | Source-set work | 18 | A session rooted in each of the four sets |
| B | Engine defects found here, fixable here | 16 | **Nobody — these are just not done** |
| C | Decisions | 10 | You, and only you |
| D | Waiting on the outside world | 5 | A platform changing |
| E | Waiting on a project, person or phase that does not exist | 8 | An event |

**Groups A and B are 34 of the 57, and neither is really a list of items.**

**Group A is one project wearing 18 hats.** Every one of them is "the four
practice sets need X" — a vendored fix, a workflow trigger, a declared
ceiling, a wired hook. They accumulated one at a time because each was found
by a different session doing something else, and each was correctly queued
under [todo-is-a-handoff](../practices/todo-is-a-handoff.md) as blocked on a
session this repository cannot be. The item
[`attach-private-sources`](../TODO.md#attach-private-sources) already says it
"unblocks four other items at once"; the real number is closer to 18.

**Group B is the rule failing.** Nothing external blocks any of these. They
are defects found by this repository's own audits, in this repository's own
engine, fixable from a session exactly like the one that found them.
[todo-is-a-handoff](../practices/todo-is-a-handoff.md) says plainly that
"would enlarge this turn" is not a reason to queue — and its own `checked_by`
is `null`, so nothing catches it. Sixteen items is what that costs.

**Group C is ten decisions scattered through 57 items**, five of which you
have never been shown because they sit at `wait` and
[open-item-disposition](../practices/open-item-disposition.md) correctly keeps
sessions quiet about them. That rule is doing its job; what is missing is a
place where the decisions sit *together* so you can clear several in one
sitting instead of meeting them one interruption at a time.

**Groups D and E are the file working as intended** — 13 items genuinely
waiting on something outside the repository. These are the handoffs the file
exists for, and they should be quiet and out of the way.

### What I Propose for TODO.md

**Step 1 — prune (no decisions in it).** Move the 34 closed items to
`record/todo-closed.md`, keeping every anchor so existing citations still
resolve ([rename-updates-links](../practices/rename-updates-links.md) applies
to the links, and the anchors are permanent by the file's own header rule).
Roughly halves the file. **Cost: one session. Risk: none.**

**Step 2 — split by clearer, not by subject.** Four files, each with exactly
one reader and one question:

- [TODO.md](../TODO.md) — Group B only, renamed in spirit to *work nobody is
  blocking*.
  Anything here is a standing invitation to just do it.
- `DECISIONS_OPEN.md` — Group C. The only file you are ever asked to read.
- `spec/SOURCE_SET_SWEEP.md` — Group A, as one checklist with a per-set
  column, not as items.
- `record/todo-dormant.md` — Groups D and E, with each item's trigger stated:
  *"reopen when Grok gains repository access."* Nothing reads it routinely.

**Step 3 — close the intake asymmetry.** Wire the check
[todo-is-a-handoff](../practices/todo-is-a-handoff.md) already nominates for
itself: scan each item for a stated blocked-on reason and fail the ones
without. That is what keeps Group B from reappearing, and it is the only part
of this that changes behaviour rather than layout.

**What I deliberately did not propose: a periodic sweep.** A sweep is another
discretionary drain, and the file already has one in
[todo-is-a-handoff](../practices/todo-is-a-handoff.md)'s Install section that
has not been run.

### The 57, Classified

Each row links the item. `Since` is the first day its anchor appears in the
file's history; `Words` is how long the item has grown.


### A. Source-Set Work — 18 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`roll-out-four-pass-restructure`](../TODO.md#roll-out-four-pass-restructure) | ≤09-06 | 262 | wait | Roll the very deep check's four-pass restructure out to `precedent-team-repo-maintenance`' own `deep-check` |
| [`attach-private-sources`](../TODO.md#attach-private-sources) | ≤09-06 | 883 | wait | Run one session rooted at each private set — this unblocks four other items at once |
| [`source-repo-consumes-no-catalogue`](../TODO.md#source-repo-consumes-no-catalogue) | ≤09-06 | 120 | wait | A source repo consumes no catalogue, so it cannot check itself |
| [`decision-strength-private-sources`](../TODO.md#decision-strength-private-sources) | 09-09 | 167 | wait | Carry `decision-strength` into the two private practice sets |
| [`source-hook-drift`](../TODO.md#source-hook-drift) | 09-09 | 1480 | wait | Decide whether a drifted-but-present session hook in a practice-set source gets brought up to canonical automatically |
| [`stale-days-does-not-travel`](../TODO.md#stale-days-does-not-travel) | 09-10 | 325 | wait | Decide whether the four private practice sets should declare their own `branch_stale_days` |
| [`source-load-ceilings`](../TODO.md#source-load-ceilings) | 09-11 | 150 | wait | Declare session-load ceilings in the attached practice-set sources, and measure the real total a session pays |
| [`provenance-check-skips-in-a-source-set`](../TODO.md#provenance-check-skips-in-a-source-set) | 09-11 | 828 | wait | A universal practice's mechanical check could not bind a source set, so sets relied on checks that silently skipped there |
| [`source-sets-vendor-the-broken-clause-matcher`](../TODO.md#source-sets-vendor-the-broken-clause-matcher) | 09-11 | 227 | wait | All four practice-set sources vendor the pre-fix `Source:` clause matcher |
| [`source-name-check-cannot-run-in-a-hosted-session`](../TODO.md#source-name-check-cannot-run-in-a-hosted-session) | 09-11 | 299 | wait | The source-name check reports UNVERIFIED for every private source in a hosted session, which is where most vendor updates happen |
| [`source-sets-declare-adapters`](../TODO.md#source-sets-declare-adapters) | 09-12 | 183 | wait | Have the private source sets declare their harness adapters |
| [`views-drift-vs-suite-workflow`](../TODO.md#views-drift-vs-suite-workflow) | 09-13 | 335 | wait | Decide whether a source set that runs the whole check suite in continuous integration should still carry `views-drift.yml` |
| [`wire-individual-hook-in-existing-sets`](../TODO.md#wire-individual-hook-in-existing-sets) | 09-13 | 467 | wait | Wire `precedent-individual-bootstrap.sh` into the four practice sets that already exist |
| [`source-set-runs-no-universal-checks`](../TODO.md#source-set-runs-no-universal-checks) | 09-13 | 406 | ask | A practice set now READS the universal rules and still RUNS none of universal's mechanical checks |
| [`vendor-very-deep-check-into-sets`](../TODO.md#vendor-very-deep-check-into-sets) | 09-13 | 475 | ask | Vendor `very_deep_check.py` into the practice sets, so a set can audit its own always-loaded files instead of only gating new ones |
| [`source-set-push-triggers`](../TODO.md#source-set-push-triggers) | 09-14 | 397 | wait | The four practice sets still run their checks on `pull_request` only, so a direct push to one runs nothing |
| [`set-ci-skips-vendored-tests`](../TODO.md#set-ci-skips-vendored-tests) | 09-14 | 166 | wait | No practice set's CI runs the vendored checks' own test suite, so a red suite sits under a green pull request |
| [`set-cannot-show-a-universal-practice`](../TODO.md#set-cannot-show-a-universal-practice) | 09-14 | 317 | wait | In a practice SET, `precedent_show.py SLUG` cannot read any universal practice — and the generated file that delivers those practices tells its reader to run exactly that command |

### B. Engine Defects, Fixable Here — 16 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`unreachable-practices`](../TODO.md#unreachable-practices) | ≤09-06 | 757 | wait | Populate `not_binding` for the practices in force here that do not bind this repo |
| [`background-freshness-fetch`](../TODO.md#background-freshness-fetch) | ≤09-06 | 229 | wait | Consider making the freshness check's fetch asynchronous |
| [`upstream-notice-silent-when-rooted-above`](../TODO.md#upstream-notice-silent-when-rooted-above) | 09-08 | 218 | wait | The upstream-carry notice is silent in exactly the layout this project requires, and nothing reports its absence |
| [`small-calls-vs-brainstorm`](../TODO.md#small-calls-vs-brainstorm) | 09-08 | 253 | wait | `small-calls` tells a session to commit during a brainstorm, and nothing mechanical stops it |
| [`sync-refuses-a-rewind`](../TODO.md#sync-refuses-a-rewind) | 09-10 | 277 | wait | Make `precedent_sync_views.py` refuse a sync that would rewind a practice's content, not just one that would remove the practice outright |
| [`private-owner-allowlist-inert`](../TODO.md#private-owner-allowlist-inert) | 09-10 | 662 | wait | The repo-reference allowlist is inert here, and this public tree names the account that owns the private practice sets |
| [`session-practices-reports-unresolved-sources`](../TODO.md#session-practices-reports-unresolved-sources) | 09-11 | 233 | wait | `.precedent/SESSION_PRACTICES.md` can report a source as unresolved that resolved fine minutes later — and a session reading it believes those practices are absent |
| [`consumer-views-drift-uncheckable-in-ci`](../TODO.md#consumer-views-drift-uncheckable-in-ci) | 09-11 | 266 | wait | A consuming repo's generated loader block cannot be drift-checked in CI, and today nothing checks it anywhere |
| [`renamed-team-source-not-in-allowlist`](../TODO.md#renamed-team-source-not-in-allowlist) | 09-11 | 584 | wait | Nothing checks that a rename carried its allowlist entry |
| [`figures-reach-commit-messages-ungated`](../TODO.md#figures-reach-commit-messages-ungated) | 09-11 | 512 | wait | A figure can reach a commit message without anything checking it, and it did twice in two days |
| [`source-clause-check-reads-only-html-comments`](../TODO.md#source-clause-check-reads-only-html-comments) | 09-11 | 226 | wait | The `Source:` clause check reads only HTML comments, so a generated file whose header is a `#` comment is never asked for one |
| [`consuming-repo-clause-clears-on-vendor-update`](../TODO.md#consuming-repo-clause-clears-on-vendor-update) | 09-11 | 156 | wait | Confirm the consuming repo's `Source:` clause actually clears, rather than assuming it |
| [`reply-check-cannot-forbid`](../TODO.md#reply-check-cannot-forbid) | 09-14 | 281 | wait | The reply check can only REQUIRE text, never forbid it — so every practice about what a reply must NOT contain is unenforceable by it |
| [`consumer-cannot-resolve-upstream-commit`](../TODO.md#consumer-cannot-resolve-upstream-commit) | 09-14 | 1738 | ask | A consumer repo cannot read upstream's own text at `upstream.commit` — nothing local resolves it — so no check that runs there may assume it can |
| [`engine-root-in-a-vendored-tree`](../TODO.md#engine-root-in-a-vendored-tree) | 09-14 | 205 | wait | Five engine tools read the wrong repo when vendored, and five more have not been checked |
| [`sync-views-blames-a-dropped-source-for-a-retirement`](../TODO.md#sync-views-blames-a-dropped-source-for-a-retirement) | 09-14 | 167 | wait | A retired practice is reported as one whose SOURCE was dropped, and a renamed source would read identically |

### C. Decisions Only Morgan Can Make — 10 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`github-issues-for-open-items`](../TODO.md#github-issues-for-open-items) | ≤09-06 | 46 | wait | Evaluate GitHub Issues for open items |
| [`reduce-github-dependency`](../TODO.md#reduce-github-dependency) | ≤09-06 | 72 | wait | Reduce GitHub dependency when ready |
| [`individual-practice-scoping`](../TODO.md#individual-practice-scoping) | ≤09-06 | 68 | wait | `for_team:`/`in_repos:` individual-practice scoping |
| [`retire-merge-target-practice`](../TODO.md#retire-merge-target-practice) | ≤09-06 | 897 | wait | Retire local/practices/merge-target-is-beta-branch.md (and its check at local/tools/checks/check_merge_target_is_beta_branch.py, and the pointer in AGENTS.md's opening paragraph) the moment Alex reviews and merges `precedent-beta-v01` into `main` for real |
| [`relax-the-pinned-branch-hold`](../TODO.md#relax-the-pinned-branch-hold) | ≤09-06 | 418 | wait | Relax the pinned-branch hold once the fix has run through real sync cycles |
| [`review-skill-level-permissions`](../TODO.md#review-skill-level-permissions) | 09-10 | 629 | ask | Review the whole technical/non-technical permission split, now that the pieces are in three separate places |
| [`repo-name-regex-shape`](../TODO.md#repo-name-regex-shape) | 09-11 | 292 | wait | Think about the shape of the leak gate's repository-name rule: it refuses `owner/name` and ignores `name` |
| [`my-options-includes-doing-nothing`](../TODO.md#my-options-includes-doing-nothing) | 09-12 | 145 | wait | Decide whether "My options" must always list the do-nothing option |
| [`universal-adapters-undeclared`](../TODO.md#universal-adapters-undeclared) | 09-12 | 160 | wait | Decide whether THIS repository declares its own harness adapters |
| [`reply-check-rollout`](../TODO.md#reply-check-rollout) | 09-13 | 538 | ask | Roll the blocking reply check out to the sources that want one, and land the individual set's half |

### D. Waiting on the Outside World — 5 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`plain-chatgpt-write-support`](../TODO.md#plain-chatgpt-write-support) | ≤09-06 | 43 | wait | Re-verify plain-ChatGPT write support |
| [`grok-workflow`](../TODO.md#grok-workflow) | ≤09-06 | 28 | wait | Verify a Grok workflow |
| [`companion-mobile-app`](../TODO.md#companion-mobile-app) | ≤09-06 | 66 | wait | Companion mobile app, if the Shortcut proves insufficient |
| [`additionalcontext-reaches-the-model`](../TODO.md#additionalcontext-reaches-the-model) | ≤09-06 | 194 | wait | Confirm `additionalContext` actually reaches the model, not just the transcript |
| [`cross-owner-add-repo-push`](../TODO.md#cross-owner-add-repo-push) | 09-09 | 258 | wait | Measure whether `add_repo` refuses a cross-owner attachment in the REVERSE direction, with `access: "push"` |

### E. Waiting on a Project, Person or Phase That Does Not Exist Yet — 8 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`actions-as-enforcement-layer`](../TODO.md#actions-as-enforcement-layer) | ≤09-06 | 128 | wait | Lean further into GitHub Actions as the enforcement layer |
| [`out-of-chat-notifications`](../TODO.md#out-of-chat-notifications) | ≤09-06 | 58 | wait | Out-of-chat change notifications for members |
| [`contributor-access`](../TODO.md#contributor-access) | 09-11 | 175 | wait | Run the contributor-access plan for real |
| [`document-project-pilot`](../TODO.md#document-project-pilot) | ≤09-06 | 67 | wait | Run the document-project pilot once Morgan has a real first project |
| [`gates-absent-from-main`](../TODO.md#gates-absent-from-main) | 09-07 | 416 | wait | Put the leak gate on `main`; the deep check cannot go there until the merge-back |
| [`whatsapp-bridge-research`](../TODO.md#whatsapp-bridge-research) | 09-09 | 515 | wait | Verify the chat bridge's platform claims against the platforms, or drop it |
| [`audit-trail-item-placement`](../TODO.md#audit-trail-item-placement) | 09-09 | 165 | wait | Confirm where the audit-trail item belongs in philosophy/AI_GOVERNANCE_TO_COCREATE.md |
| [`retire-a-practice-source`](../TODO.md#retire-a-practice-source) | 09-10 | 276 | wait | Write the retirement sequence for a practice SOURCE, from the one real run |

## The Gotchas

### Where It Stands

| | Count | Words |
|---|---|---|
| Index in [AGENTS.md](../AGENTS.md) — one line per trap, loaded every session | 38 | 1,197 |
| Stories in [record/GOTCHAS.md](../record/GOTCHAS.md) — read on a match | 38 | 9,336 |
| Retired, in [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md) | 33 | 13,664 |

Live entries in the index, by day:

```
08-31   5      09-06  16      09-11  36
09-03   7      09-07  26      09-12  36
09-05   9      09-09  31      09-13  36  ← the split
              09-10  32      09-14  38
```

**Five to 38 in two weeks.** The section reached 7,182 words on 09-12; the
split cut what every session loads to 1,197 and moved the text, unchanged, to
the record. **That fixed the cost and not the count** — two entries have been
added since, and the index is climbing again at roughly 30 words each.

**Retirement does happen** — 33 entries have been archived, which is a better
record than TODO.md's. What it does not have is a *trigger*: an entry is
archived when somebody reads it and judges it dead, and nobody schedules that
reading.

### The Specific Plan

**1. Every gotcha carries a `Retires when:` line, in the record entry.**
One line, stating the condition under which the entry stops being worth a
session's attention. Three shapes cover almost everything:

```
**Retires when:** a mechanical check refuses this, and the check is named here.
**Retires when:** the harness fixes <the specific behaviour>. Re-test on any
  harness change that touches it.
**Retires when:** nothing has hit this since <date> and the mechanism it
  describes no longer exists.
```

**Why it goes in the record and not the index:** the index is what every
session pays for, and a retirement condition is read by whoever is auditing,
not by whoever just hit the trap. Same reasoning as the 09-13 split.

**2. Backfill it on the five entries that already say a fix landed** —
[g3](../record/GOTCHAS.md#g3), [g4](../record/GOTCHAS.md#g4),
[g18](../record/GOTCHAS.md#g18), [g21](../record/GOTCHAS.md#g21),
[g37](../record/GOTCHAS.md#g37). Each claims its cause was closed; each is
still in the index every session reads. Writing the condition down is what
makes them testable, and I expect two or three to archive on the first test.

**[g37](../record/GOTCHAS.md#g37) is the one to be careful with**, and it is
the reason this is worth doing rather than obvious. It says "fixed
2026-09-13", and then says it fired again on 09-14 — because the fix lives in
the working tree and cannot reach a checkout too stale to contain it. It fired
again in this very session, on the 14th, and the session it hit (mine) wrote a
day-old answer before noticing. **So its condition is not "the fix landed": it
is "every checkout that can go stale carries the fix, including the four
source sets — which the entry itself says do not."** Only reading the whole
entry tells you that, which is exactly the argument for making each entry
state its own exit.

**3. Add a `Retires when:` line to the adding instructions** in the index
header, so new entries carry one from the start.

**4. Once every entry has one, a pass becomes possible** — read the conditions,
not the stories, and test the ones that claim to be met. That is a cheap
recurring job in a way "re-read 38 gotchas and judge" never was. **Whether to
wire it into [very-deep-check](../practices/very-deep-check.md)'s currency pass
is a separate decision** and I am not proposing it here: that pass already reads
the record's bodies, and adding a fifth thing to a check nobody runs routinely
solves nothing.

### What This Does Not Fix

**The count still only goes up while the environment keeps producing traps.**
A `Retires when:` line makes retirement *checkable*; it does not make the
harness stop breaking. Several of the 38 describe container behaviour nobody
here controls, and those are permanent until the platform changes.

**And a gotcha is a band-aid by construction.**
[durable-fix](../practices/durable-fix.md) ranks a committed file above
knowledge a session has to carry, and every gotcha is the second thing. The
right destination for an entry is a check that refuses the mistake — which is
what the first `Retires when:` shape above is really asking each entry to
name. **Some cannot be moved there**, and saying so per entry is more honest
than the current position, which says nothing.

## What I Would Need From You to Start

Nothing beyond a yes to any row in the table at the top. None of this needs a
decision you have not already been shown, and none of it touches `main`.

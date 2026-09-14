---
title:         "Open Items and Gotchas: What to Split, What to Retire, What to Just Do"
kind:          proposal
status:        drafted
opened:        2026-09-14
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Both TODO.md and the gotchas index capture mechanically and drain by hand, so both only grow. Second draft, rewritten against Morgan's nine responses — one item is one file with a permanent address, filed by kind and labelled by owner, with every list generated. Classifies the 57 live open items, sizes the reference migration, and gives the gotchas an exit condition per entry."
---
# Open Items and Gotchas: What to Split, What to Retire, What to Just Do

**Nothing here is done.** Second draft, rewritten 2026-09-14 after Morgan read
the first and answered it in nine points. Every figure is a measurement taken
that day against `precedent-beta-v01` — a snapshot, not a live rollup.

## The One Idea That Answers Most of It

**One item is one file. The file is created once, keeps its name forever, and
never moves. Everything that changes about it — its state, its owner, whether
it is done — is a field inside it. Every list a person reads is generated from
those fields.**

That single rule settles most of the nine points at once, and it settles them
in the same shape the practice catalogue already uses: `practices/*.md` plus a
generated [MAP.md](../MAP.md). It is not a new architecture; it is the one
this repository already runs.

**Why "never moves" is the load-bearing half.** A file that moves when its
state changes breaks every link to it, and this repository links to open items
from tool comments, spec documents and [AGENTS.md](../AGENTS.md). A status
field costs one line and breaks nothing.

## Answering the Nine Points

| # | Morgan's idea | Verdict |
|---|---|---|
| 1 | Slugs instead of numbers | **Accepted** — and half-done already: every item has an anchor, and the file's own header says never to cite the number |
| 1b | The date inside the slug | **Pushback** — `opened:` as a field, with **age in days** computed into the generated index. Age is the thing you want; a date is arithmetic |
| 2 | Split by type, one file per type | **Accepted** — and the type axis already exists, unused, in [templates/TODO.md.template](../templates/TODO.md.template) |
| 3 | Do **not** organize by who owns it | **Accepted, and my first draft was wrong** — see below |
| 4 | One `todo/` directory; `TODO.md` renamed | **Accepted** |
| 4b | A separate file or directory for completed items | **Pushback** — a `status:` field instead. Nothing moves, so nothing breaks |
| 5 | The very deep check sweeps the open items | **Accepted** |
| 6 | Decision strength on each item | **Pushback, partly** — only where an item carries an approval, and no bulk backfill by a session |
| 7 | The very deep check reviews the gotchas | **Accepted — and it already half does.** Measured, not recalled |
| 8 | Gotcha slugs, `gotcha-` and `todo-` prefixes | **Accepted**, with one reservation about stutter |
| 9 | One `.md` file per item, like the practices | **Accepted — this is the keystone** |

### Where My First Draft Was Wrong (Point 3)

You are right, and the mistake is worse than you said. **I labelled the axis
"who can clear it" and then did not actually sort by owner** — four of the five
groups are kinds of work (a defect, a decision, a verification, a project) and
only one named a person. So the grouping was defensible and the label was not,
and a label that says "owner" invites exactly the failure you describe: a list
that reads as assignments, half of them wrong, and the rest read as somebody
else's problem.

**The evidence that kind is the right axis is already in the repository.**
[templates/TODO.md.template](../templates/TODO.md.template) — the file every
adopting repo instantiates — defines four kinds and says the typed convention
is "the load-bearing part": **analysis** (agent-doable from the desk),
**verify** (source-check before external use), **physical** (needs hardware, a
vendor, a test), **decision** (the user's call). BestPractice's own
[TODO.md](../TODO.md) does not use them.

So: **file by kind, label by owner.** `owner:` is a field like any other, it
changes without moving anything, and the generated index can show it as a
column — visible, sortable, and never the thing that decides where an item
lives.

## What an Item File Looks Like

```
todo/todo-source-set-push-triggers.md

---
slug:       todo-source-set-push-triggers
kind:       analysis            # analysis | verify | physical | decision
status:     open                # open | done | dropped
opened:     2026-09-14
closed:     null
blocked_on: "a session rooted in each practice set"
owner:      null                # a person, only when one is genuinely needed
project:    source-sets         # optional; groups items that are one job
disposition: wait               # wait | ask | parked  (open-item-disposition)
strength:   null                # decided | assented — only if this records an approval
---
## What
## Why it is not done
## How it closes
```

**Five of those fields are the nine points**, which is the argument for the
shape: `slug` is point 1, `kind` is points 2 and 3, `status` is 4b, `opened`
is 1b, `strength` is 6.

### Generated Views, Not Hand-Maintained Lists

`todo/INDEX.md`, built by a generator the way [MAP.md](../MAP.md) is, carrying
at least:

- **One table per kind** — the four files you wanted, as sections of one
  generated page rather than four hand-edited files that drift.
- **Age in days**, computed from `opened:`, sorted oldest first. This is point
  1b done better than a date in a name: *"open 47 days"* is the sentence you
  actually want, and no one has to subtract.
- **A "nothing is blocking this" view** — every `open` item with no
  `blocked_on`. That is the 16-item group below, and it is a query, not a file.
- **Open decisions**, for the one list you are ever asked to read.
- **Done items**, last, collapsed to one line each.

**Why generated rather than four real files:** four hand-maintained files are
four things to keep sorted, and an item whose `blocked_on` clears has to be
moved by hand or it lies. A generator reads the field and the view is right
the next time it runs. If you would rather have four physical files, that is a
legitimate variant — it costs the drift, and I would not take it.

## The Migration, Which You Flagged and Which Is the Real Work

Measured today, so the size is known rather than guessed:

| What refers to an item by a name that would change | Count | Where |
|---|---|---|
| `TODO.md#slug` links outside the file | 23 | spec documents, [AGENTS.md](../AGENTS.md), practice files |
| `TODO.md item N` in prose | 8 | 5 tool files, including [tools/precedent_check.py](../tools/precedent_check.py) and [tools/verify_harness.py](../tools/verify_harness.py) |
| `#gN` gotcha anchors | 52 | 6 files, including [record/GOTCHAS.md](../record/GOTCHAS.md) citing its own entries |

**The 8 prose references are already broken and nobody noticed.** They name
"item 18" and "item 20" — numbers that shift whenever anything is added or
reordered, which is the exact failure [TODO.md](../TODO.md)'s own header was
written to end. Whatever else happens, those 8 are wrong today.

The sequence, in order:

1. **Freeze the numbering.** Delete the visible numbers from the file before
   anything else moves. Nothing can then be cited by number.
2. **Fix the 8 prose references** to cite anchors. This is independently worth
   doing and needs none of the rest.
3. **Split into files**, one per item, slug unchanged except for the `todo-`
   prefix, with a mapping table written into the migration commit.
4. **Repoint the 23 links**, mechanically, from the mapping table
   ([rename-updates-links](../practices/rename-updates-links.md)).
5. **Add a check that fails on a stale reference** — a link to `TODO.md#x`, or
   the phrase `item N`, after the migration. Without step 5 this decays in a
   week, and a migration with no guard is the thing
   [checkable-gets-checked](../practices/checkable-gets-checked.md) exists to
   refuse.

**The part outside this repository, which is bigger than the part inside.**
The item format lives in [templates/TODO.md.template](../templates/TODO.md.template),
so it reaches every adopting repo, and the four practice sets already disagree
about it: the individual set's `TODO.md` is 4,344 words with **no anchors at
all**, `precedent-team-writing` has 3 numbered items, and
`precedent-team-repo-maintenance` and `precedent-team-working-style` have no
`TODO.md` at all. **So there is no single old format to convert from** — there
are four, and a migration tool that assumes this repository's shape will fail
on three of them. The honest sequencing is: settle the format here, ship the
template, and convert each set in a session rooted in it
([cross-source-rollout](../practices/cross-source-rollout.md)), rather than
claiming a one-pass conversion that cannot exist.

## What I Would Not Do

**A date inside the slug (point 1b).** Three reasons, none fatal on its own:
a date is not an age, so you still do the arithmetic; a name that carries a
date can never be corrected if the date is wrong, because the name is the
address; and an item that gets split or merged inherits a date that is now a
lie. What your version buys, and my version does not, is **the date visible in
a plain directory listing with no tool involved** — which is a real advantage
on a day when the generator is broken. **My pick: `opened:` plus computed age.
If you want the date in the name anyway, say so and it is a one-word change to
the naming rule.**

**A separate completed file, or an open/done pair per kind (point 4b).** Both
shapes move a file when an item closes, and a moved file breaks every link to
it — including the links this plan is about to create 23 of. `status: done`
costs one line, the generated index puts done items where you want them, and
the file keeps its address forever. **You are right that the whole thing is the
record; the answer is that `todo/` *is* the record, and nothing needs a
`record/` copy.**

**Decision strength on every item (point 6).** The field is right where an item
carries an approval, and wrong as a requirement, because most items are
findings nobody approved — writing `strength:` on one of those records an
approval that never happened.
[decision-strength](../practices/decision-strength.md) is explicit that an
unmarked approval means **unknown**, never `decided`.

**And the backfill you offered to do is the one part I would push back on
hardest.** That practice deliberately backfilled nothing, permanently, because
guessing which past "ok" was enthusiastic is the invention
[no-invented-specifics](../practices/no-invented-specifics.md) forbids. **The
exception is you**: you can state a strength on a still-open item today,
because that is a fresh statement rather than a reconstruction. What I would
not do is make it a chore — set it when an item is next touched, and leave the
rest unmarked, which is a true state.

**A `gotcha-` prefix on files inside a `gotchas/` directory** reads as stutter,
and I would have used the directory alone. **The reason I accept it anyway is
`precedent_show.py`**: it takes a bare slug, practices already own that
namespace, and a todo or gotcha slug colliding with a practice slug is a real
possibility with a silent failure mode. The prefix makes the namespace visible
in every citation, including prose where no directory is in sight. Same
argument for `todo-`.

## The Diagnosis Both Files Share

Both are **captured mechanically and drained by hand.**

- [capture-gate](../practices/capture-gate.md) fires at every merge, and
  "write down what just cost you an hour" fires whenever a session gets burned.
  Neither needs anyone to decide anything.
- Nothing expires on its own.
- Draining — pruning a closed item, archiving a retired gotcha — waits for
  somebody to feel like doing it.

A pump with a mechanical trigger and a discretionary drain only runs one way.
That is not a failure of discipline: the capture side is working exactly as
designed, and [repo-is-memory](../practices/repo-is-memory.md) is why it
should keep working that way.

**The gotchas file already had half this fixed.** The 2026-09-13 split put a
one-line index in [AGENTS.md](../AGENTS.md) and the stories in
[record/GOTCHAS.md](../record/GOTCHAS.md), which flattened the *reading cost*
and left the *count* alone.

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

### The Five Groups, Re-Labelled

Same five groups as the first draft. The axis is now what each item **is**, not
who owns it, and the owner column is a label inside the item.

| Group | What it is | Items | Kind | Why it is not done |
|---|---|---|---|---|
| A | Source-set work | **18** | analysis | Needs a session rooted in each of the four sets |
| B | Engine defects found here | **16** | analysis | **Nothing is blocking them** |
| C | Decisions | **10** | decision | Waiting on one person |
| D | Outside-world checks | 5 | verify | A platform has to change |
| E | Waiting on a project, person or phase | 8 | physical | An event has to happen |

**Group A is one project wearing 18 hats**, which is what the `project:` field
is for: every one of them is "the four practice sets need X", each found by a
different session doing something else. As 18 items each costs a fresh
re-orientation; as one project with a per-set checklist it is one sweep.

**Group B is the rule failing.** Nothing external blocks any of them — defects
in this repository's own engine, found by its own audits, fixable from a
session exactly like the one that found them.
[todo-is-a-handoff](../practices/todo-is-a-handoff.md) says "would enlarge
this turn" is not a reason to queue, and its own `checked_by` is `null`, so
nothing catches it. **This is the group that needs a rule, not a filing
change**, and it is the one decision below I would argue with you about.

**Group C is ten decisions scattered through 57 items**, five of which you have
never seen because they sit at `wait` and
[open-item-disposition](../practices/open-item-disposition.md) correctly keeps
sessions quiet. That rule is working; what is missing is a generated view where
the decisions sit together.

**Groups D and E are the file working as intended** — 13 things genuinely
waiting on the outside world.

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

### B. Engine Defects, Nothing Blocking — 16 Items

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

### C. Decisions — 10 Items

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
split cut what every session loads to 1,197. **That fixed the cost and not the
count.** Retirement does happen — 33 entries archived — but it has no
*trigger*: an entry is archived when somebody reads it and judges it dead, and
nobody schedules that reading.

### The Updated Plan

**1. Every gotcha becomes its own file** (point 9), in `gotchas/`, named
`gotcha-<slug>.md`, with frontmatter carrying `slug`, `opened`, `status`
(`live` | `retired`) and `retires_when`. **The archive stops being a separate
file**: a retired entry is the same file with `status: retired`, which is the
same "never move it" rule as the open items, and it means the 52 `#gN`
references migrate once rather than twice.

**2. `Retires when:` on every entry** — the condition under which it stops
being worth a session's attention. Three shapes cover nearly everything:

```
retires_when: "a mechanical check refuses this — name the check here"
retires_when: "the harness fixes <the specific behaviour>; re-test on any
               harness change touching it"
retires_when: "nothing has hit this since <date> and the mechanism is gone"
```

**3. Backfill it on the five entries that already claim a fix landed** —
[g3](../record/GOTCHAS.md#g3), [g4](../record/GOTCHAS.md#g4),
[g18](../record/GOTCHAS.md#g18), [g21](../record/GOTCHAS.md#g21),
[g37](../record/GOTCHAS.md#g37). I expect two or three to archive on the first
test.

**[g37](../record/GOTCHAS.md#g37) is the one to be careful with**, and it is
why this is worth doing rather than obvious. It says "fixed 2026-09-13", then
says it fired again on 09-14 — because the fix lives in the working tree and
cannot reach a checkout too stale to contain it. It fired again on 09-14 in the
session that wrote this document, which then wrote a day-old answer before
noticing. **Its condition is therefore not "the fix landed": it is "every
checkout that can go stale carries the fix, including the four source sets —
which the entry itself says do not."** Only reading the whole entry tells you
that, which is the argument for making each entry state its own exit.

**4. The index keeps carrying only the symptom and the link.** The retirement
condition lives in the entry, not the index: every session pays for the index,
and only an auditor needs the condition.

### Point 7: The Very Deep Check Already Half Does This

Measured in [tools/very_deep_check.py](../tools/very_deep_check.py), not
recalled: it has a **gotcha currency pass** that finds the gotchas section in
an instructions file, follows each index line into
[record/GOTCHAS.md](../record/GOTCHAS.md), and reads the bodies, with a
120-day staleness threshold. So the mechanism you are asking for exists and
runs; what it cannot do is test a condition no entry states.

**So point 7 is cheap: teach the existing pass to read `retires_when` and
report the entries whose condition looks met.** That is a change to a pass
that already runs, not a fifth thing bolted onto a check nobody runs — which
is what I argued against in the first draft, and it does not apply here.

**What it still is not, and I want this said plainly: the very deep check runs
on request.** A sweep there is better than nothing and it is not a schedule.
[record/very-deep-check-ledger.json](../record/very-deep-check-ledger.json)
already records what each pass returns run after run, so if this one finds
nothing for several runs it will show up there and be owed a keep, cheapen or
retire answer — same as every other pass.

### Point 5: The Same Sweep for Open Items

Accepted, with one thing already built to fold in:
[tools/todo_progress.py](../tools/todo_progress.py) matches a change against
what items name, at merge time. That is the "did this close something" half.
The very-deep-check pass is the other half — **read every open item's `opened`
and `blocked_on`, and report** the ones with no stated blocker (Group B, which
should have been done rather than queued), the ones whose blocker names
something that no longer exists, and the oldest few by age.

**Both halves report; neither closes anything.**
[item-closes-on-its-condition](../practices/item-closes-on-its-condition.md)
already puts the closing judgement on a person or on the session that did the
work, and a sweep that closes items on a heuristic would undo that.

## What This Costs

Worth saying flatly, because it is the argument against doing it at all:

- **≈91 item files and ≈71 gotcha files** in this repository, plus a generator
  and an index, plus the 83 measured references to repoint.
- **A format change that leaves this repository**, through
  [templates/TODO.md.template](../templates/TODO.md.template), into every
  adopting repo and the four practice sets — which, as above, are in four
  different states today.
- **Per-item overhead goes up.** A one-line open item becomes a file with ten
  lines of frontmatter. For a 900-word item that is nothing; for a one-liner it
  is most of the file. The practices took that trade and it was right there,
  where every file is substantial. **Open items are shorter and more numerous,
  so the trade is worse here** — the median live item is ≈300 words, but the
  shortest is 28.

**My honest read: the per-item file wins anyway**, because the alternative is
one file that no tool can slice and every session reads whole. But it is a
real cost and the first draft did not name it.

## Suggested Order

Cheap and independent first, so nothing waits on the big migration:

1. **Fix the 8 broken `item N` references.** No decisions, no format change.
2. **Prune the 34 closed items** — under the new scheme they become
   `status: done`, so this is the same work either way.
3. **Delete the visible numbers** from [TODO.md](../TODO.md), so nothing new
   can cite one.
4. **Write the format** (the frontmatter above) as a spec document, and only
   then split the files.
5. **Split, repoint, and add the stale-reference check**, in one commit per
   step.
6. **Gotchas in the same shape**, after the open items have proved it.
7. **The two very-deep-check passes**, last, because they read the fields the
   steps above create.

## What Is Still Open Between Us

Four things, and only the last is big.

**The date in the slug.** Mine is `opened:` as a field with age computed into
the index; yours is the date in the name. Yours is visible with no tool, mine
is correctable and gives you age rather than a date to subtract. **One word of
the naming rule either way — say which and it is settled.**

**Four physical files, or one generated index with four sections.** You asked
for four files. I would generate them, because a hand-maintained file whose
`blocked_on` has cleared lies until somebody moves the item. **If you want four
real files, that is a legitimate variant and the cost is drift.**

**The rule for Group B — the 16 items nothing is blocking.** This is the one
worth arguing about, because it changes how the work goes rather than where the
files live. My position is fix-on-sight: a session that finds a defect it can
fix, fixes it, and a defect that gets queued with no stated blocker is closed at
the next sweep rather than carried. **The counter-argument is real** — that rule
turns every audit finding into an unplanned detour, and some of those 16 are
half-day jobs. **I would still take it**, because the alternative is what is
already happening.

**Whether the whole per-item-file migration is worth its cost**, given the
section above. The cheap steps 1 to 3 are worth doing whatever you decide here,
and they are reversible.

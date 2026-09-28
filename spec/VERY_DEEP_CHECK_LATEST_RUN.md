---
title:         Very Deep Check, 2026-09-28 — What It Found and What Was Done
kind:          record
status:        closed
opened:        2026-09-28
closed:        2026-09-28
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The full account of the most recent very deep check: every repo it read, what each pass found, what was fixed and where, and what is left for a person. The next run rewrites it; git history keeps this one."
---
# Very Deep Check, 2026-09-28 — What It Found and What Was Done

The full record of the latest run (the next run rewrites this file; git
history keeps each earlier one): every repo it read, what each pass found, what
was fixed and where, and what is left for a person. The ledger of every run
is [VERY_DEEP_CHECK.md](VERY_DEEP_CHECK.md); this is the long form behind
its "Current run" row.

**Scope, committed to before anything ran:** all four passes, across all
five repos in force — BestPractice (this repo), `precedent-individual`,
`precedent-shared-repo-maintenance`, `precedent-shared-writing` and
`precedent-shared-working-style` — plus **one real consumer** Morgan
attached for pass 1, the first real consumer in the ledger's history.

**Where the work is:** branch `claude/very-deep-check-2amsjs` in all five
repos, pushed, **not landed**. Nothing reaches `pre-staging` until Morgan
says `Go update`.

## The Short Version

- **Dozens of findings fixed** (about fifty in pass 1 alone), across all
  five repos, over three rounds on the same day. Every change to a mechanism carries a planted
  test that fails without the fix.
- **The check itself was misreporting**, in ways that inflated or hid
  findings in every run before this one (details under Pass 4). All fixed.
- **Hooks never ran in a multi-repo session.** A session opened above its
  repos runs none of their startup hooks. A new runner, wired by one
  setup-script paste, fixes that; Morgan added the paste the same day.
- **The full catalogue judgment ran for the first time ever**: all 216
  active practices across six sources, 81 of them judgment-only, each read
  against the repos it binds.
- **What is left is mostly decisions**, listed at the end with a
  recommendation for each.

## How the Run Was Done

Ten sub-agents did the reading and rehearsing for the four passes. For the
fixes, agents worked in separate git worktrees on files no other agent
touched, and this session merged them, so no two edited the same file.
Round 1 ran while Morgan was offline and asked for as much fixed as
possible rather than filed. Rounds 2 and 3 followed his review of the four
findings files, where he approved the fixes (strength: decided), asked for
two workflow items to be explained first, and asked for the setup-script
step to be documented.

## Pass 1 — Can an Adopter Actually Install and Update?

**What it did.** Rehearsed every path from scratch: the guided install, the
loader install, the migration from the old vendored layout, an update that
deletes a file, and every direction a practice can move between sets. Then
updated a copy of the real consumer and ran its own gates. Read each
harness adapter (Codex, Gemini CLI, Grok Build) against that harness's
current documentation.

**What it found and fixed** (about fifty items; highlights):

- **Update Vendors** had ten defects, among them an update that could leave
  a consumer's `.gitignore` incomplete and a hook dropped upstream that
  stayed installed downstream. Fixed in
  [`precedent_update.py`](../tools/precedent_update.py) and
  [`precedent_vendor_engine.py`](../tools/precedent_vendor_engine.py).
- **The Codex and Gemini CLI adapters were wrong**: the docs said neither
  harness had hooks. Both do. Shipped hook files for each and rewrote the
  adapter pages ([templates/harness/](../templates/harness/README.md)).
- **Install-once files drifted silently.** A consumer's pull-request
  template and `TODO.md` keep the wording they were installed with. Update
  Vendors now reports wording the current template dropped, and never
  rewrites it.
- **A consumer's startup hook did nothing on a person's own computer.** It
  now runs, skipping the package install and the machine-wide git setup.
- **The shipped AGENTS templates inlined a gotcha**, which the resident
  `environment-gotchas` rule forbids. They now point at `gotchas/`, and an
  install seeds that folder with the one trap every install inherits.

## Pass 2 — Do the Mechanisms Do What They Claim?

**What it did.** Attempted all 22 of the pass's questions, and read 17
enforced checks against their own Rule for the first time.

**What it found and fixed:**

- **Seven checks judged something other than what their Rule names**
  (fixed in [`precedent_check.py`](../tools/precedent_check.py) and
  [`doc_sync.py`](../tools/doc_sync.py)).
- **The YAML-anchor gotcha was never true.** GitHub has accepted anchors in
  workflows since 2025-09-18; the rejection was assumed, not observed.
  Retired, and the workflow check now refuses only merge keys (`<<:`),
  which GitHub still rejects.
- **The report of other sets' checks was mostly noise** in the engine's own
  repo. Each false positive was traced to the set's script and fixed there;
  what remains is real or exempted with a reason.
- **The engine-freshness notice said nothing when it could not look.** Not
  verified now prints as not verified, and the practice sets run the notice
  at session start.
- **The push check hid four minutes of test progress.** It now streams it.
- **The 2026-09-01 decision relaxing private-repo isolation** had a
  deadline (Phase 7) that passed with nothing done. An addendum records the
  relaxation as extended (strength: assented) and keeps its one live
  trigger.

## Pass 3 — Does Everything Agree With Itself?

**What it did.** Read every private-set practice, swept the universal
catalogue for stale names, triggers and claims, and read the likeliest
thirty closely. Read [ENFORCEMENT.md](ENFORCEMENT.md) whole.

**What it found and fixed:**

- **AGENTS.md's preamble cost about 3,460 tokens every session.** Cut to
  about 980, each command one line; the long form moved word for word to
  [AGENTS_COMMANDS_IN_FULL.md](AGENTS_COMMANDS_IN_FULL.md).
- **The individual set's always-loaded block sat at 539 of 550 tokens**,
  one edit from failing to build, and the size warning did not watch it.
  Trimmed to about 440, and the warning now watches the block.
- **Stale names, retired commands and dead pointers** in all five repos.

## Pass 4 — Catalogue, Backlog, Branches

**What it did.** Re-derived every unlanded branch in full clones, judged
every overdue reminder and blocked item, checked eight `retires_when`
conditions, read scope on all 154 universal practices, and ran the full
catalogue judgment.

**The check was misreporting itself:**

- **Its branch scan made full clones shallow** by fetching with `--depth`,
  so every "unlanded" count in the two runs before this one was inflated
  (116 for a branch carrying 2).
- **It read the working tree, not what was committed**, so it called a set
  current when `origin` was behind.
- **An aborted run counted as the last run.**
- **It flagged consumer-only paths as missing** in this repo, and listed
  branches whose commits cancel out as unlanded work.

All fixed in [`very_deep_check.py`](../tools/very_deep_check.py), which now
also **reads `main` and writes through the landing branch**, and names
work already waiting on the landing branch so a fix is not made twice.

**Backlog:** eight items closed (two answered, four overtaken, one kept as
files rather than GitHub Issues, and the weekly very-deep-check Routine not
pursued), each with its reason in its own file. "Response Please", decided
2026-09-22 on a branch that never landed, is now in the vocabulary.

**The full catalogue judgment** found about twenty violations and nine
rules that were stale or contradicted another rule. Fixed in text across
all five repos:

- **very-deep-check contradicted AGENTS.md** about running unasked. It now
  proposes one after drift-inviting work and never starts unasked.
- **promote-only described a pull request from `staging` into `main`**,
  which Promote and the merge gate forbid. Corrected.
- **The shared `install` practice described the retired install.**
  Rewritten.
- **INSTALL.md put the retired install path 600 lines ahead of the only
  live one.** Swapped.
- A figure off by a factor of sixty (grep-before-search), missing dates on
  rules about outside services, three READMEs that opened with rename
  history, unlinked practice mentions, change logs in the doc recipes, and
  two adopted drafts still sitting in `candidates/`.

## Setup: Hooks in a Multi-Repo Session

**The problem.** Claude Code runs the hooks of the folder a session opens
in. A multi-repo session opens in `/home/user`, which has none, so no
repo's startup hook ran: no commit identity, no practice list from the
private sets, no engine refresh.

**The fix.** [`precedent_run_session_hooks.py`](../tools/precedent_run_session_hooks.py)
runs each repo's own startup hooks, called from a user-level hook that the
environment's setup script writes. It is documented as **optional but
recommended** in [CLOUD_SETUP.md](../documentation/CLOUD_SETUP.md), with
pointers from [SETUP.md](../SETUP.md),
[PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md) and
[INSTALL.md](../INSTALL.md). Examples now use `/home/user/` paths, where a
hosted session's clones actually are. **Not yet confirmed in a session
started after the paste**; the next new session shows it.

## What Is Left

**For Morgan to decide** (each with a recommendation in its findings file):

- **BestPractice's two workflows are approved by nobody.** Recommendation:
  narrow `leak-gate.yml` to the tier branches, since every push already
  runs the leak gate locally, and approve both in your own words.
  `deep-check.yml` also runs four jobs per trigger where one would do.
- **The individual set's `engine-refresh.yml`** opens a pull request into
  `main`, against promote-only. Recommendation: delete it.
- **`commit-identity.sh` writes machine-wide settings** on a person's own
  computer. Recommendation: limit those three steps to hosted sessions.
- **`claude/graduate-synonym`** carries two synonyms you asked for on
  2026-09-26 that never landed. Recommendation: land it.
- **Rule changes the audit proposed**: a carve-out for branch-links,
  retiring blank-blocklist and new-rule-placement, and trimming
  very-deep-check's 3,400-word Rule. Also a go-ahead for a sweep of about
  2,300 filename-as-text links.
- **Branch cleanup**: 156 fully landed branches to delete, and the rest
  each with a recommendation, handed over in the session.

**Waiting on a condition, not a person:** five rules moved to universal are
still in force from a shared set's copies until every consumer takes the
new catalogue.

**Needs GitHub Support:** a public practice set still exposes, through two
old branches and 68 pull-request refs, files naming private repositories.

The live list is the four findings files:
[pass 1](../todo/todo-2026-09-28-very-deep-check-pass-1-findings.md),
[pass 2](../todo/todo-2026-09-28-very-deep-check-pass-2-findings.md),
[pass 3](../todo/todo-2026-09-28-very-deep-check-pass-3-findings.md),
[pass 4](../todo/todo-2026-09-28-very-deep-check-pass-4-findings.md).

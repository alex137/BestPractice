---
checked_through: 2026-10-04
---
# What's New

A running log of what changed in this project, newest first: one entry per day on which something did.

## Sunday 2026-10-04: ladder-becomes-opt-in

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **The five-stage ladder is now something a team chooses, not something everyone gets**: its rules left the set every project receives and live in the ladder set for people who bring it (fourteen practices withdrawn, recorded in record/WITHDRAWN_FROM_UNIVERSAL.md; a check now finds none of the ladder's words in the universal set, down from 638; "No ladders" opens a session that sees it the other way).
- **Generated files rebuild themselves when you commit**, so the map and glossary can no longer drift out of date by hand (tools/precedent_regenerate.py reads tools/generated_files.json and rebuilds what a commit touched; a repository's own hand-written map and glossary text moved into MAP.source.md and GLOSSARY.source.md).
- **A Debut checks once and moves staging and pre-staging together**, so pre-staging only ever receives work that passed (the Promote into staging composes staging, any fix branch, main's direct work and pre-staging in a scratch worktree, runs the full check once, and pushes both in one step).
- **Update Vendors got about a dozen fixes from real runs in other repositories**, and a merge now takes a pending update by itself (tools/precedent_merge_vendors.py, run before the push).

## Saturday 2026-10-03: push-check-records-its-pass

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **The slow check no longer runs twice because it touched its own notes**: it used to rewrite its record files as it ran, then refuse to count its own pass, and the push gate re-ran the roughly 14-minute suite and timed out (precedent_push_check.py now records the pass over the fact ledgers its checks refreshed).
- **A stale rendered page on main was rebuilt** (spec/PREFORK_AUDIT.html).

## Friday 2026-10-02: fewer-github-test-runs

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **Main's GitHub test runs at most once every few hours in a private repository**, and costs nothing when it is not due (Promote reads github_ci_every_hours and names the copy to-main-not-due-DATE, which the workflow skips before a runner starts; it also fixed a bug that read every skipped run as a failure).
- **Branches a session leaves behind now say what they were for and which session made them** (tools/precedent_branch_name.py names them claude/, then the date, a slug and the last five characters of the session ID).
- **A session now notices when a shared set it declares never loaded**, instead of silently working without it (precedent_session_check.py fails that row; the refresh also writes and wires the individual set's start-up hook for a consumer).
- **"Prompt Please" invites push-back and asks for the answer back as one block to paste** (practices/prompt-please.md).

## Thursday 2026-10-01: lighter-sessions-and-root-issues

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **Every session starts with less to read**, because rules that only matter in certain files or moments now load when they're needed (a reduction pass took the always-loaded rule block from about 830 tokens to about 560, folded durable-fix and fix-the-original into upstream-fix, and gave the five stage practices one index line).
- **"Root issues" is a new command**: it asks a session to look back over everything it hit and hand over each problem whose cause lives upstream, as one paste-ready prompt (practices/root-issues.md, with "Root fixes" as a synonym; it replaces the old "Upstream fix" command).
- **Work going to pre-staging no longer pays for the slow full check by accident**, after one session ran the twelve-minute suite three times for it (precedent_push_check.py now runs at the landing branch's tier when run bare, and refuses --tier full there without a stated reason).
- **A wait loop that could never end is now blocked outright** after one ran 20 minutes past the check it was waiting for (wait-loop-gate.sh refuses pgrep -f and pkill -f, whose pattern always matches the shell running them).

## Wednesday 2026-09-30: daily-log-and-safer-merges

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **"What's new?" now writes up each finished day that has no entry yet**, then shows the newest ones and what changed today so far (practices/whats-new.md and tools/precedent_whats_new.py; a day ends in the project's own timezone, and a first run covers the last seven finished days).
- **A merge is now checked again after it lands.** Another window could move the branch in the few seconds between a merge's check and the merge itself, so the merged result went unchecked; now a failing one is undone with a new commit while the pull request's branch keeps the work (precedent_merge_check.py --landed, run by merge-check-gate.sh after every merge).
- **Landings got faster** after one landing into staging ran its sixteen-minute full check five times the day before (verify_harness --as-ci now runs its shards at once across up to four processes, and the merge gate holds the Promote lock while it checks).
- **An update no longer gets stuck on a project's own edits to Precedent's files**: it keeps the edit, merges it, or takes the new version and says which commit holds the old one (precedent_update.py, planned in spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md).

## Tuesday 2026-09-29: five-stage-ladder

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **A short page now explains the project's own words**, and it's generated from one list so it can't fall out of date (documentation/OUR_LANGUAGE.md, built by tools/our_language.py from tools/our_language.json).
- **You can send a voice note or a message to a chat bot** in a test build and get a few sentences and a link back, and the bot may only change content, never the machinery (the Telegram chat bridge under bridge/, which can transcribe voice on the same machine with an open-source Whisper model).
- **The philosophy page gained an idea about working in the cloud**: your work follows you from laptop to phone only when it lives there (idea 11, "Cloud-first", in philosophy/OUR_PHILOSOPHY.md).
- **Checks got faster** by running the cheap ones first and skipping the slow ones once something has already failed (precedent_push_check.py now runs the harness last; a new doc_sync ledger measured 58 seconds cold and 6 seconds warm on 192 blocks).

## Monday 2026-09-28: first-very-deep-check

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **The instructions every session reads first got much shorter** (the opening of AGENTS.md went from about 3,460 tokens to about 980, with the long form moved to spec/AGENTS_COMMANDS_IN_FULL.md).
- **Four general rules moved into the set every project gets**, since nothing in them was specific to maintaining practice sets (dont-race-another-window, fresh-before-write, session-trailer and automation-issues moved into the universal set).
- **A session opened above several projects now runs each project's startup steps**, which it used to skip entirely (tools/precedent_run_session_hooks.py; run by hand the first time, it ran 25 hooks across six repositories).

## Sunday 2026-09-27: one-command-updates

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **One tool now does everything in an update that needs no judgment**, so a session no longer works through the steps by hand, and it ends with a short list of what's left for the person (tools/precedent_update.py takes over the twelve-step vendor-update runbook and finishes with DONE, LEFT FOR YOU or FAILED).
- **Checks now match how far along the work is**: quick checks on only the changed files when work first lands, the full suite one step up, and GitHub's test on the way to production (the new checks-follow-the-tier practice; a push into pre-staging runs the practice checks with --changed-files-only, which takes about ten seconds).
- **Sessions working side by side can claim a piece of work** so two don't start it at once, and share the results of slow calculations instead of each redoing them (tools/lease_board.py and tools/result_cache.py; in testing, a second session waited 8 seconds and picked up the first one's result).

## Saturday 2026-09-26: updates-from-production

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **Projects pull their updates from the finished branch** instead of the one still being tested, each switching over at its next update (SOURCE_BRANCH now reads main in precedent_vendor_engine.py and precedent_refresh_sources.py).
- **Promote now works out by itself which step to take** and says so up front (precedent_branches.py --promote opens with "Now promoting from X to Y"; a lock left behind by a crashed window now frees after 15 minutes instead of 45).
- **The list of situations every session reads at startup got shorter**, leaving room for projects to add their own (the universal occasion index went from about 2,375 tokens to about 1,961).
- **A rule's helper file now travels with it to every project**, and the rule says it needs one (a new `ships:` field in practice frontmatter, delivered by precedent_materialize.py).

## Friday 2026-09-25: three-branch-tiers

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **Everyday work lands on a branch that only gets fast checks**, and a Promote moves a whole batch up to the fully checked branch and from there to production (spec/BRANCH_TIERS_PLAN.md: pre-staging, staging and main; the old precedent-beta-v01 branch was renamed staging, and a lock, precedent-promote-lock, stops two windows promoting at once).
- **The checks that ran on GitHub's paid machines now run in the session before every push**, and a push to a working branch takes seconds (tools/precedent_push_check.py behind the push-check-gate.sh hook; the deep-check.yml workflow no longer starts on its own).
- **A GitHub automation file can no longer be added or edited quietly**: each one has to match a recorded, dated go-ahead for its exact content (precedent_check.py compares each file's sha256 against the entry in precedent.json; this came after a project's light-check.yml billed a minute on every merge for four days).
- **Commits carry the person's own timezone wherever they work**, and a project's timezone is only a fallback (precedent_time.py checks the person's zone before the `TZ` environment variable and the repo's fallback_timezone).

## Thursday 2026-09-24: old-install-retired

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **The old install is no longer offered**: it copied the rules into a project but never switched them on, and a project still using it fails its checks until it moves over (INSTALL.md §1 is now reference only, and practice_audit.py check 5 fails a repo that vendors process/upstream/practices/ without a generated loader block). The next update also deletes that install's leftover GitHub jobs, such as bestpractice-upstream-sync.yml.
- **A private project can run GitHub's automatic checks at most once every few hours** instead of on every push, to save paid minutes (a `ci_every_hours` setting makes commit-identity.sh add `[skip ci]` to commits; the default, 0, keeps a run on every push, and a personal `ci_on_branches` switch can turn runs off on working branches).
- **A session follows a rule as it reads today**, not an older copy it happens to find, and can be asked whether a fix removes the cause or only patches the symptom (two new practices, current-rule-governs.md and upstream-fix.md, the second behind the "Upstream fix" command).
- **Individual conversations with an AI assistant stay private**, the project's statement on AI governance now says, and only what was learned from them gets shared (item 21 in philosophy/AI_GOVERNANCE_TO_COCREATE.md, with a matching line in the README).

## Monday 2026-09-21: cheaper-github-checks

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **The formatting check on documents now runs before a commit is allowed**, in the session, instead of a second time on GitHub afterward (`.claude/hooks/doc-lint-gate.sh` refuses a commit whose Markdown fails `doc_lint.py`; the retired workflow had billed about 350 minutes over 19 days in one repository).
- **The practice sets stopped running automated checks on GitHub at all**, and the checks that projects still run got cheaper (the `source-sets-run-no-ci` practice, after four sets turned out to be 127 of 143 billed minutes in one day; the CI templates went to one job per workflow, so a run bills 1 minute instead of up to 3).
- **A project now finds out on its own when it has fallen behind** the latest version of Precedent (`tools/precedent_engine_freshness.py` runs at session start and before a push or merge; when measured, 18 of 22 installed projects had never taken an update).
- **The instructions every session reads first got shorter**, with nothing thrown away (the always-loaded block went from about 2,200 tokens to about 1,430 against a 2,000 cap, by moving two practices to on-demand and trimming the three longest rules).

## Sunday 2026-09-20: one-file-per-item

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **Every open item and every recorded trap now lives in its own file** instead of one long list, and a follow-up check found items the move had lost and put them back (105 items from `TODO.md` plus 44 live and 33 retired gotchas moved into `todo/` and `gotchas/`, and `TODO.md` shrank by about 7,200 lines to a redirect stub; 54 of 161 items had gone missing, and `tools/todo_migrate.py` now refuses to finish if any item drops).
- **The front page was rewritten** to open with the everyday problems Precedent solves rather than a definition and a feature list (`README.md`, rebuilt around three named frustrations, with a new "Get Up and Running!" section).
- **Standing commands now respond to what a message is asking for**, not only to an exact phrase, and the session says its reading out loud when that reading is a judgment call (`go-merge`, `weak-yes` and `decision-strength` read intent; `chief-of-staff`, `full-practice-audit` and `very-deep-check` stay on the literal words).
- **Sessions running on other AI coding tools get the same setup** Claude Code sessions get (Codex and Gemini CLI adapters wired through `tools/bootstrap.sh` and a new `GEMINI.md`, plus a new Grok Build adapter under `templates/harness/grok-build/`).

## Monday 2026-09-14: bestpractice-becomes-precedent

Some top highlights from the day's activity; ask if you want to learn more details or the full list of everything done.

- **The rulebook was broken up into one file per rule**, and only a handful are read every time; the rest come in when they apply (the single 140-kilobyte `PRACTICES.md` became 116 files under `practices/`, with 10 always loaded at about 950 tokens and the others reached through an occasion index, `precedent_paths.py` for the file being edited, and `precedent_gate.py` at moments like a merge).
- **A project can stack its own team's rules and one person's rules** on top of the shared ones, and pick up engine fixes without copying files by hand (sources are declared in `precedent.json`, and `precedent_vendor_engine.py` installs and refreshes the engine in a project that uses Precedent).
- **New plain-language guides for people who don't write code** arrived, plus a set of essays on why the project works the way it does (`documentation/` gained `WHY_PRECEDENT.md`, `FOR_EVERYONE_ELSE.md` and `DAILY_HABITS.md`; `philosophy/` holds essays such as `CORE_PILLARS.md` and `OUR_PHILOSOPHY.md`).
- **The project can test whether its rules actually fire when they should**, by replaying made-up scenarios against them (a four-phase practice simulation under `evals/simulation`, alongside routing tests in `evals/routing`; the tools folder grew from 7 Python scripts to 56).

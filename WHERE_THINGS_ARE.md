# Where things are — the full index

**Looking for something in this repository? Check here before searching it.**
Every row is *looking for X → go to Y*, and the table below is the complete
one: 89 rows.

[AGENTS.md](AGENTS.md) carries a short version of this table — the dozen rows
sessions reach for constantly — and links here for the rest. **That split is
the only difference between the two; no row was dropped.** It was made on
2026-09-14 because the inline table had grown to 2,671 tokens that every
session paid before doing any work, against a declared ceiling it was pushing
into (practice:
[session-load-budget](practices/session-load-budget.md), TODO.md's
`agents-md-ceiling-policy` item, since closed and pruned).

**Adding a row?** Add it here. It belongs in AGENTS.md's short table only if
sessions will hunt for it *constantly* — the test is frequency, not
importance, because every row there is paid for by every session whether or
not it is read.

| Looking for… | Go to |
|---|---|
| The restructuring plan (read this first) | [spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md) |
| Where a rule goes when you want it in SOME projects and not others, and how to make a shared set | [documentation/SHARED_PRACTICE_SETS.md](documentation/SHARED_PRACTICE_SETS.md) |
| Whether an open item may be raised with Morgan at all, and what "Drop it" writes | [practices/open-item-disposition.md](practices/open-item-disposition.md), phrase at [practices/park-it.md](practices/park-it.md) |
| Running many sessions at once — the proposed Chief of Staff session, what `list_sessions` can and cannot do, and the tag namespaces | [spec/CHIEF_OF_STAFF.md](spec/CHIEF_OF_STAFF.md) — decided 2026-09-14 (build it); was tracked at TODO.md's `chief-of-staff-session` item, since closed and pruned |
| Inherited practices whose meaning or mechanism changed under Precedent (Alex needs to hear about these) | [spec/CHANGES_TO_TELL_ALEX.md](spec/CHANGES_TO_TELL_ALEX.md) |
| The phase-1 per-practice file format | [spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) |
| Why a practice file's references to `spec/`, `templates/` or a root document are full `https://github.com/...` URLs rather than relative links | [practices/practice-links-travel.md](practices/practice-links-travel.md) |
| Why a session rooted in a practice set saw none of the universal rules, and what actually puts a hook's output in front of the model | [spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md](spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md) — trap at [gotchas/gotcha-2026-09-20-a-sessionstart-hook-writing-a-file-is-not-the-session-loadi.md](gotchas/gotcha-2026-09-20-a-sessionstart-hook-writing-a-file-is-not-the-session-loadi.md) |
| The phase-2 loader (resident set, replay measurement) | [spec/LOADER.md](spec/LOADER.md) |
| The phase-3 brief (what phase 3 was handed) | [spec/PHASE3_BRIEF.md](spec/PHASE3_BRIEF.md) |
| The phase-3 sources: resolver, precedence, what could not be built here | [spec/SOURCES.md](spec/SOURCES.md) |
| How many practice sets of each level a person or a repo can have | [spec/SOURCES.md](spec/SOURCES.md)'s "How many sources of each level" row, reasoning at [spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md#one-individual-set-per-person-not-per-team) |
| How a practice-set source is named — the convention, what refuses vs. warns, and what a session must say before anyone picks a name | [spec/SOURCE_NAMING.md](spec/SOURCE_NAMING.md), rule at [practices/source-naming.md](practices/source-naming.md) |
| The phase-4 enforced channel: what is checked, and what each check is blind to | [spec/ENFORCEMENT.md](spec/ENFORCEMENT.md) |
| The phase-5 creation pipeline: what got built stage by stage, what's deferred, what phase 6 inherits | [spec/PHASE5_BRIEF.md](spec/PHASE5_BRIEF.md) |
| The phase-5 candidate file format (Stage 2) and why universal candidates are GitHub Issues, not files | [spec/CANDIDATE_FORMAT.md](spec/CANDIDATE_FORMAT.md) |
| The phase-5 deep-check before phase 6: real bugs found and fixed, real candidates landed, open questions for Morgan | [spec/PHASE5_DEEPCHECK.md](spec/PHASE5_DEEPCHECK.md) |
| The phase-6 brief: what's closed, what's blocked and needs Morgan, what's still ahead and needs the target repo attached | [spec/PHASE6_BRIEF.md](spec/PHASE6_BRIEF.md) |
| The pre-launch audit: what a real install, migration and two-team resolve broke, and what is still open — **read before the next audit pass** | [spec/PRELAUNCH_AUDIT.md](spec/PRELAUNCH_AUDIT.md) |
| The pre-fork catalogue audit: verdict per inherited practice against this plan's architecture | [spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md) |
| Populating the two private sets (done 2026-09-01, closing phase 3 — brief kept for how it was done) | [spec/PRIVATE_SETS_BRIEF.md](spec/PRIVATE_SETS_BRIEF.md) |
| Bootstrapping a brand-new individual or team set from zero — the generalized procedure any adopter follows, plus the tool and skeletons it uses | [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md), tool at [tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py), skeletons at [templates/practice-set-individual/](templates/practice-set-individual/) and [templates/practice-set-shared/](templates/practice-set-shared/) |
| Bringing mechanical checks to the two private sets' practices (open; cannot run from here) | [spec/PRIVATE_ENFORCEMENT_BRIEF.md](spec/PRIVATE_ENFORCEMENT_BRIEF.md) |
| How a session rooted in an individual or team set gets the universal practices, and why its checks still do not run there | [spec/SOURCE_SET_PROSE_GAP.md](spec/SOURCE_SET_PROSE_GAP.md), open half at [`source-set-runs-no-universal-checks`](todo/todo-2026-09-13-source-set-runs-no-universal-checks.md) |
| How a repo that already had BestPractice installed migrates to Precedent's three-source model (the recommended pattern, from the first real dependent-repo test) | [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md) |
| Deleting a file or directory a decommissioned mechanism left behind — the audit that has to pass first, and the record of what went | [practices/decommission-deletes-files.md](practices/decommission-deletes-files.md), audit at [tools/precedent_decommission.py](tools/precedent_decommission.py) |
| Moving an existing, still-wanted practice from one level to another (team ↔ individual, team ↔ team, team → universal) — distinct from creating one or retiring one outright | [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md); the tool that does both steps in order is [tools/precedent_move.py](tools/precedent_move.py) |
| Why the miss rate is what it is, and the plan for it (read before phase 5) | [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md) |
| Who may write what in a project repo, and who may land a practice — **drafted, not executed; three GitHub behaviours in it are unverified** | [spec/CONTRIBUTOR_ACCESS.md](spec/CONTRIBUTOR_ACCESS.md) |
| Team-level practice capture for document work at scale — the editorial team repo and document-project template, the "alternative to Google Docs" use case | [spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md](spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md) |
| The reusable document-project template a future pilot instantiates from | [templates/document-project/](templates/document-project/) |
| What zone a date or time gets stamped in, and where the fallback is declared | [practices/timestamps-carry-offset.md](practices/timestamps-carry-offset.md), engine at [tools/precedent_time.py](tools/precedent_time.py) — run it bare to see which rung answered; the value is `fallback_timezone` in [precedent.json](precedent.json) |
| What a person can define about themselves — name, email, timezone, pronouns, whether approval travels — and what applies until they do | [PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md)'s "What Applies Until You Set Any of It"; the non-developer version is [documentation/FOR_EVERYONE_ELSE.md](documentation/FOR_EVERYONE_ELSE.md)'s "What It Knows About You"; the rule against asking is [practices/declared-default-is-applied.md](practices/declared-default-is-applied.md) |
| What a session pays before its first turn, the declared ceiling on each always-loaded file, and how to reduce one without deleting what still bites | [practices/session-load-budget.md](practices/session-load-budget.md), registry at [tools/session_load_budgets.json](tools/session_load_budgets.json) — `python3 tools/precedent_check.py --only session-load-budget` |
| What this account has left of GitHub's API allowances, what each tool spends, and why `/rate_limit` cannot answer either | [practices/github-api-budget.md](practices/github-api-budget.md), engine at [tools/github_budget.py](tools/github_budget.py), registry at [tools/github_api_budgets.json](tools/github_api_budgets.json) — `python3 tools/github_budget.py` |
| Why each practice is routed the way it is (every glob, and every `**`) | [tools/routing_scope.json](tools/routing_scope.json) |
| The routing audit: coverage check + rotating deep read, on-demand, never a routine gate | [practices/routing-audit.md](practices/routing-audit.md), engine at [tools/routing_audit.py](tools/routing_audit.py) |
| The full practice audit: manual, whole-catalogue sweep across every source, on request only | [practices/full-practice-audit.md](practices/full-practice-audit.md), engine at [tools/full_practice_audit.py](tools/full_practice_audit.py) |
| The very deep check: four ordered passes over every repo in force, on request only — distinct from the full practice audit above | [practices/very-deep-check.md](practices/very-deep-check.md), engine at [tools/very_deep_check.py](tools/very_deep_check.py), run record at [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md) |
| What each part of the very deep check returned and cost, run after run, and which parts are owed a keep/cheapen/retire answer | [record/very-deep-check-ledger.json](record/very-deep-check-ledger.json) — **never hand-edit it**; the answers go in [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md) |
| Why `verify_harness.py` (the deep check) takes as long as it does, which checks actually cost the time, a parallelization that was tried and reverted for measuring no real gain, and the change-scoping fix that did measurably help | [spec/VERIFY_HARNESS_PERFORMANCE.md](spec/VERIFY_HARNESS_PERFORMANCE.md) |
| Cutting GitHub Actions minutes across every vendored repo — where the minutes actually go, the self-hosted-runner pilot (item 6), and what's shipped vs. still open | [spec/CI_MINUTES_PLAN.md](spec/CI_MINUTES_PLAN.md), open item tracked at [todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md](todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md) |
| **Why a CI workflow costs what it costs** — GitHub bills per JOB rounded up to a whole minute, measured at 0.47s of work billed as 3 minutes; why five days of frequency fixes moved nothing, and the arithmetic retiring the debounce job | [spec/BILLING_FLOOR.md](spec/BILLING_FLOOR.md) |
| Whether THIS repo's own `deep-check.yml` should move to a self-hosted runner for speed — a narrower, harder question than the CI-minutes plan's item 6, since this repo's CI is already free and public | [spec/DEEP_CHECK_SELF_HOSTED_RUNNER.md](spec/DEEP_CHECK_SELF_HOSTED_RUNNER.md) |
| Step-by-step mechanics for registering a self-hosted GitHub Actions runner on a RunCloud-managed Linux server, for the item 6 pilot once it's authorized | [spec/SELF_HOSTED_RUNNER_SETUP.md](spec/SELF_HOSTED_RUNNER_SETUP.md) |
| The branch sweep's own list — every merged, merged-elsewhere and unmerged branch in this checkout and every declared source, with a clickable delete or compare link on each row | `record/stale_branches.md` — **never hand-edit it**; written by `python3 tools/very_deep_check.py`'s branch sweep and committed like `MAP.md`, after it clears [tools/leak_gate.py](tools/leak_gate.py). This checkout's own merged-and-stale (safe-to-delete) slice is also embedded live in [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md)'s "Branches safe to delete right now", a `tools/doc_sync.py`-gated block — that page, not this file, is where a person actually goes to delete branches |
| Gaps between what the plan approved and what got built (routing audit's own history, and what else to check) | [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) |
| Whether every declared practice-source repository is still CALLED what this repo calls it — a rename redirects forever, so git never notices | [tools/precedent_source_names.py](tools/precedent_source_names.py), run at [vendor-update-runbook](practices/vendor-update-runbook.md)'s step 8; `UNVERIFIED` is not a pass |
| Whether a document project's contributor boundary is actually ON — branch protection shaped as the plan needs, and a CODEOWNERS file to give it something to require; UNVERIFIED when it could not ask GitHub, which is not a pass | [tools/precedent_boundary_check.py](tools/precedent_boundary_check.py), design at [spec/CONTRIBUTOR_ACCESS.md](spec/CONTRIBUTOR_ACCESS.md)'s 2026-09-14 review, finding 5 |
| Which changed files will wait for a code owner's review before a pull request exists, and the plain-words sentence to say to the contributor about it | [tools/precedent_owned_paths.py](tools/precedent_owned_paths.py), wired into [templates/document-project/AGENTS.md](templates/document-project/AGENTS.md)'s contributor section |
| Generating a project's `.github/CODEOWNERS` from `maintainers` and `owned_paths` in its `precedent.json` (a practice set's from `approvers.json`) | [tools/build_codeowners.py](tools/build_codeowners.py) — `--repo PATH`, `--check` |
| Whether this session can reach its PRIVATE practice sources at all, and the credential that removes the `add_repo` dance | [tools/precedent_source_credentials.py](tools/precedent_source_credentials.py), setup in [CLOUD_SETUP.md](documentation/CLOUD_SETUP.md) (hosted) or [PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md) (everything, including local) |
| Whether an attached practice-set source's vendored engine has gone stale, or is missing the session hooks a source is created with, and repairing either | [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py) — reports at session start; `--apply` refreshes and restores hooks, `--commit` commits |
| Why a source clone on disk, with the token set, still fails every `git` command with `could not read Username` — and what repairs it at session start | [tools/precedent_source_credentials.py](tools/precedent_source_credentials.py)'s `persist_credential_helper`, called on every sync by [tools/precedent_source_bootstrap.py](tools/precedent_source_bootstrap.py) |
| Whether a hook this repo *declares* actually exists on disk and is executable — the failure the harness reports as nothing at all | [tools/precedent_check.py](tools/precedent_check.py) — `--only declared-hooks-exist` |
| Whether this session's SessionStart hooks actually ran, and repairing them if not | [tools/precedent_session_check.py](tools/precedent_session_check.py) — `--apply` runs them by hand; every [tools/precedent_gate.py](tools/precedent_gate.py) moment prints the failing rows unasked |
| Whether `PRECEDENT_FRESHNESS_ALSO` names repositories that are actually there, and what to set it to on this container | [tools/precedent_session_check.py](tools/precedent_session_check.py) — the row prints the corrected value; a dead entry is skipped silently by design, so nothing else reports it |
| Whether Alex has moved `main` since the last carry onto this branch, and what changed | [tools/precedent_upstream_check.py](tools/precedent_upstream_check.py) — printed at session start; the watermark it compares against is [tools/upstream_watermark.json](tools/upstream_watermark.json), moved with `--record` in the carry's own commit |
| Practices that fire at a moment rather than in a file | [tools/precedent_gate.py](tools/precedent_gate.py) — `merge`, `review`, `push`, `reply` |
| Why the closing **Next Steps** section of a reply is not optional, and what refuses a turn without one | [tools/precedent_reply_check.py](tools/precedent_reply_check.py) — `--explain` says what is declared here; the same requirements are printed at the start of every turn by [tools/precedent_gate.py](tools/precedent_gate.py)'s reply gate |
| Why a long conversation is refused a reply that never says whether this is a cheap point to compact, and the number that decides "long" | [reply_check.json](reply_check.json), read by [tools/precedent_reply_check.py](tools/precedent_reply_check.py); the rule is [practices/session-spend-follows-the-task.md](practices/session-spend-follows-the-task.md) |
| Why a team or individual practice registered to a gate used to load nothing | [tools/precedent_gate.py](tools/precedent_gate.py)'s `resolved_gate_practices` — the gate read one directory until 2026-09-13, so only universal practices ever reached it |
| Which practices are enforced, and running one check | [tools/precedent_check.py](tools/precedent_check.py) — `--list`, `--explain`, `--only SLUG` |
| Why a bare run of [tools/precedent_check.py](tools/precedent_check.py) doesn't sweep every `tree`-scope check every time, and how to force it to | `_scoped_tree_slugs()` there — directly + indirectly touched practices run every commit, the rest rotate 1/10th per commit (full coverage every 10 commits, by commit count, never left to chance); `--full-sweep` or `--all` bypasses it |
| The catalogue's own figures (resident size, Rule share, coverage) | [tools/catalogue_stats.py](tools/catalogue_stats.py) — never hand-type these into prose |
| Precedent explained for someone adopting it (not a developer) | [documentation/ADOPTING.md](documentation/ADOPTING.md) |
| Public-facing pitch and how-to guides, for people outside the project (marketing, a how-to for developers, a how-to for everyone else) | [documentation/](documentation/) |
| What a normal working day looks like once Precedent is installed — the four habits and the standing command vocabulary, for someone who is not a developer | [documentation/DAILY_HABITS.md](documentation/DAILY_HABITS.md) |
| The theory this project is built on — the essays, the brainstorm, the rules being tried in real work, and what is still unsettled. **The only copy; argument, not rules that bind anything here** | [philosophy/](philosophy/), start at [philosophy/README.md](philosophy/README.md) |
| Why every item in a `philosophy/` essay carries a slug, and what checks that citations resolve both ways — **an experiment, merged; reverting is a revert** | [philosophy/doc-recipes/backlinks.recipe.md](philosophy/doc-recipes/backlinks.recipe.md), engine at [tools/philosophy_backlinks.py](tools/philosophy_backlinks.py) |
| Why `philosophy/` binds nothing outside itself, and the checks that hold that line | [local/practices/philosophy-is-not-repo-policy.md](local/practices/philosophy-is-not-repo-policy.md), [local/practices/philosophy-declares-its-source.md](local/practices/philosophy-declares-its-source.md) |
| How a practice source's harness adapters (its `bootstrap/*.sh`) reach a consuming repo's `.claude/hooks/` without anyone hand-copying them, and why the settings wiring deliberately does not travel | [spec/SOURCES.md](spec/SOURCES.md)'s "Harness adapters travel with the source", mechanism at [tools/precedent_materialize.py](tools/precedent_materialize.py) |
| Which practice libraries are in force in this repo | [precedent.json](precedent.json) |
| An example personal practice set | [documentation/examples/practice-set/](documentation/examples/practice-set/) |
| The private-term blocklist template (copy into your own private set) | [templates/leak-blocklist.txt.template](templates/leak-blocklist.txt.template) |
| The leak gate (push-time; both layers live) | [tools/leak_gate.py](tools/leak_gate.py) — `--explain` for what it does and does not check |
| The editorial section split, as reviewable data | [tools/section_split.json](tools/section_split.json), applied by [tools/resplit_sections.py](tools/resplit_sections.py) |
| The converted practice files (phase 1) | [practices/](practices/) |
| What each practice is and why — **the live catalogue** | [practices/](practices/), indexed by [MAP.md](MAP.md); one rule at a time with `python3 tools/precedent_show.py SLUG` |
| Practices no longer in force, and why each was withdrawn | [MAP.md](MAP.md)'s "Withdrawn practices" table — generated; the files are kept, never deleted |
| The pre-fork single-file catalogue — **superseded, frozen at 53 practices since 2026-08-31**; kept for its prose and its numbering | [PRACTICES.md](PRACTICES.md) |
| Repo map, generated (phase 2) | [MAP.md](MAP.md) — regenerate with `tools/build_views.py`, never hand-edit |
| Canonical names, generated (phase 2) | [GLOSSARY.md](GLOSSARY.md) — built from every practice's `defines:` field |
| The loader — resident block, occasion index, path-trigger channel | This file's generated block above; engine at [tools/build_views.py](tools/build_views.py), [tools/precedent_paths.py](tools/precedent_paths.py) |
| Loader premise, measured against this repo's own history | [tools/behavioral_replay.py](tools/behavioral_replay.py) |
| Install / update / check-in playbook (dependent repos) | [INSTALL.md](INSTALL.md) — the assistant-facing runbook; the person-facing routes are [SETUP.md](SETUP.md) (guided, non-technical) and [documentation/FOR_DEVELOPERS.md](documentation/FOR_DEVELOPERS.md) (short form plus what actually bites) |
| What each person sets on each machine (individual source, leak blocklist, the optional overrides) | [PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md) |
| Setting up a hosted session on Claude Code on the web — most people's way in, and just the environment variables it needs | [CLOUD_SETUP.md](documentation/CLOUD_SETUP.md) |
| Guided-install entry point admins paste to their agent | [SETUP.md](SETUP.md) |
| The one-command loader install (INSTALL.md §0 performed mechanically; prints the placeholders it left) | [tools/precedent_install.py](tools/precedent_install.py) — `--help`; its fixture in [tools/verify_harness.py](tools/verify_harness.py) installs into a scratch project on every run |
| Member onboarding page (template + rendered sample) | [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md) |
| Git/GitHub concepts for this workflow | [GIT.md](documentation/GIT.md) |
| The working method (branches, plain text, critique, prompts) | [METHOD.md](documentation/METHOD.md) |
| Phone / ChatGPT / Grok workflows + assistant reliability status | [MOBILE.md](documentation/MOBILE.md) |
| A brainstormed chat bridge — reaching a Claude session by voice, Telegram as proof of concept and WhatsApp as destination — **speculative: nobody decided to build it, and no claim in it came from a primary source** | [spec/SPECULATIVE_WHATSAPP_BRIDGE.md](spec/SPECULATIVE_WHATSAPP_BRIDGE.md) |
| The ten ideas underneath Precedent on one page — work through an assistant, the repository is the memory, practices, proposal and approval, routing, enforcement, four levels, three permission levels, the standing phrases, privacy — each linked into both guides | [documentation/TEN_THINGS.md](documentation/TEN_THINGS.md) |
| Every GitHub setting a Precedent project depends on, who clicks it, what fails without it — roles, branch protection with the four values, what GitHub does with CODEOWNERS and how this system generates it, Actions permissions and secrets, practice-set repositories | [documentation/GITHUB_SETTINGS.md](documentation/GITHUB_SETTINGS.md) |
| CI checks for shell-less agents (install, require) | [GITHUB_ACTIONS.md](documentation/GITHUB_ACTIONS.md) |
| Whether anything catches a drifted [MAP.md](MAP.md), [GLOSSARY.md](GLOSSARY.md) or loader block in a practice SET | the `views-drift` job inside [templates/github-actions/precedent-check.yml.template](templates/github-actions/precedent-check.yml.template) — there is no separate `views-drift.yml.template` since 2026-09-19, when it was folded in ([templates/github-actions/README.md](templates/github-actions/README.md)) |
| Upstream open items / roadmap | [TODO.md](TODO.md) |
| The full story behind any environment trap, one file each | [gotchas/](gotchas/) (generated overview: [gotchas/INDEX.md](gotchas/INDEX.md)) |
| Gotchas that no longer fire, with the verdict that retired each one | [gotchas/](gotchas/) (`status: retired` in the file, in place -- nothing moves) |
| GitAround — the reading view this work spun out | [alex137/GitAround](https://github.com/alex137/GitAround), a separate product since 2026-08-14; a branch here still staging it under proposals/ is superseded, and its documents live there now |
| Slide-deck engine + deck conventions | [deck/](deck/) — engine [build_deck.py](deck/build_deck.py), practice in [deck/README.md](deck/README.md) |
| Portable audits | [tools/](tools/) — [doc_lint.py](tools/doc_lint.py), [practice_audit.py](tools/practice_audit.py), [checkin.py](tools/checkin.py) |
| What a session on codex, gemini-cli or grok-build does **not** get that Claude Code does — one row per mechanism, with the parallel or the reason there is none | [templates/harness/PARALLELS.md](templates/harness/PARALLELS.md), checked by [tools/precedent_check.py](tools/precedent_check.py) `--only claude-only-surface-has-a-parallel`, re-judged on every [very deep check](practices/very-deep-check.md) |
| Skeletons dependent repos instantiate | [templates/](templates/) (+ per-agent adapters in [templates/harness/](templates/harness/)) |

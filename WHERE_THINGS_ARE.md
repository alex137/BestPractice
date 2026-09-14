# Where things are — the full index

**Looking for something in this repository? Check here before searching it.**
Every row is *looking for X → go to Y*, and the table below is the complete
one: 88 rows.

[AGENTS.md](AGENTS.md) carries a short version of this table — the dozen rows
sessions reach for constantly — and links here for the rest. **That split is
the only difference between the two; no row was dropped.** It was made on
2026-09-14 because the inline table had grown to 2,671 tokens that every
session paid before doing any work, against a declared ceiling it was pushing
into (practice:
[session-load-budget](practices/session-load-budget.md), open item
[`agents-md-ceiling-policy`](TODO.md#agents-md-ceiling-policy)).

**Adding a row?** Add it here. It belongs in AGENTS.md's short table only if
sessions will hunt for it *constantly* — the test is frequency, not
importance, because every row there is paid for by every session whether or
not it is read.

| Looking for… | Go to |
|---|---|
| The restructuring plan (read this first) | [spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md) |
| Whether an open item may be raised with Morgan at all, and what "Park it" writes | [practices/open-item-disposition.md](practices/open-item-disposition.md), phrase at [practices/park-it.md](practices/park-it.md) |
| Running many sessions at once — the proposed Chief of Staff session, what `list_sessions` can and cannot do, and the tag namespaces | [spec/CHIEF_OF_STAFF.md](spec/CHIEF_OF_STAFF.md) — **drafted, not decided**; open item at [TODO.md's `chief-of-staff-session`](TODO.md#chief-of-staff-session) |
| Inherited practices whose meaning or mechanism changed under Precedent (Alex needs to hear about these) | [spec/CHANGES_TO_TELL_ALEX.md](spec/CHANGES_TO_TELL_ALEX.md) |
| The phase-1 per-practice file format | [spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) |
| Why a practice file's references to `spec/`, `templates/` or a root document are full `https://github.com/...` URLs rather than relative links | [practices/practice-links-travel.md](practices/practice-links-travel.md) |
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
| Bootstrapping a brand-new individual or team set from zero — the generalized procedure any adopter follows, plus the tool and skeletons it uses | [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md), tool at [tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py), skeletons at [templates/practice-set-individual/](templates/practice-set-individual/) and [templates/practice-set-team/](templates/practice-set-team/) |
| Bringing mechanical checks to the two private sets' practices (open; cannot run from here) | [spec/PRIVATE_ENFORCEMENT_BRIEF.md](spec/PRIVATE_ENFORCEMENT_BRIEF.md) |
| How a session rooted in an individual or team set gets the universal practices, and why its checks still do not run there | [spec/SOURCE_SET_PROSE_GAP.md](spec/SOURCE_SET_PROSE_GAP.md), open half at [TODO.md](TODO.md#source-set-runs-no-universal-checks) |
| How a repo that already had BestPractice installed migrates to Precedent's three-source model (the recommended pattern, from the first real dependent-repo test) | [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md) |
| Deleting a file or directory a decommissioned mechanism left behind — the audit that has to pass first, and the record of what went | [practices/decommission-deletes-files.md](practices/decommission-deletes-files.md), audit at [tools/precedent_decommission.py](tools/precedent_decommission.py) |
| Moving an existing, still-wanted practice from one level to another (team ↔ individual, team ↔ team) — distinct from creating one or retiring one outright | [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md) |
| Why the miss rate is what it is, and the plan for it (read before phase 5) | [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md) |
| Who may write what in a project repo, and who may land a practice — **drafted, not executed; three GitHub behaviours in it are unverified** | [spec/CONTRIBUTOR_ACCESS.md](spec/CONTRIBUTOR_ACCESS.md) |
| Team-level practice capture for document work at scale — the editorial team repo and document-project template, the "alternative to Google Docs" use case | [spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md](spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md) |
| The reusable document-project template a future pilot instantiates from | [templates/document-project/](templates/document-project/) |
| What zone a date or time gets stamped in, and where the fallback is declared | [practices/timestamps-carry-offset.md](practices/timestamps-carry-offset.md), engine at [tools/precedent_time.py](tools/precedent_time.py) — run it bare to see which rung answered; the value is `fallback_timezone` in [precedent.json](precedent.json) |
| What a session pays before its first turn, the declared ceiling on each always-loaded file, and how to reduce one without deleting what still bites | [practices/session-load-budget.md](practices/session-load-budget.md), registry at [tools/session_load_budgets.json](tools/session_load_budgets.json) — `python3 tools/precedent_check.py --only session-load-budget` |
| Why each practice is routed the way it is (every glob, and every `**`) | [tools/routing_scope.json](tools/routing_scope.json) |
| The routing audit: coverage check + rotating deep read, on-demand, never a routine gate | [practices/routing-audit.md](practices/routing-audit.md), engine at [tools/routing_audit.py](tools/routing_audit.py) |
| The full practice audit: manual, whole-catalogue sweep across every source, on request only | [practices/full-practice-audit.md](practices/full-practice-audit.md), engine at [tools/full_practice_audit.py](tools/full_practice_audit.py) |
| The very deep check: four ordered passes over every repo in force, on request only — distinct from the full practice audit above | [practices/very-deep-check.md](practices/very-deep-check.md), engine at [tools/very_deep_check.py](tools/very_deep_check.py), run record at [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md) |
| What each part of the very deep check returned and cost, run after run, and which parts are owed a keep/cheapen/retire answer | [record/very-deep-check-ledger.json](record/very-deep-check-ledger.json) — **never hand-edit it**; the answers go in [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md) |
| Gaps between what the plan approved and what got built (routing audit's own history, and what else to check) | [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) |
| Whether every declared practice-source repository is still CALLED what this repo calls it — a rename redirects forever, so git never notices | [tools/precedent_source_names.py](tools/precedent_source_names.py), run at [vendor-update-runbook](practices/vendor-update-runbook.md)'s step 8; `UNVERIFIED` is not a pass |
| Whether this session can reach its PRIVATE practice sources at all, and the credential that removes the `add_repo` dance | [tools/precedent_source_credentials.py](tools/precedent_source_credentials.py), setup in [PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md) |
| Whether an attached practice-set source's vendored engine has gone stale, or is missing the session hooks a source is created with, and repairing either | [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py) — reports at session start; `--apply` refreshes and restores hooks, `--commit` commits |
| Why a source clone on disk, with the token set, still fails every `git` command with `could not read Username` — and what repairs it at session start | [tools/precedent_source_credentials.py](tools/precedent_source_credentials.py)'s `persist_credential_helper`, called on every sync by [tools/precedent_source_bootstrap.py](tools/precedent_source_bootstrap.py) |
| Whether a hook this repo *declares* actually exists on disk and is executable — the failure the harness reports as nothing at all | [tools/precedent_check.py](tools/precedent_check.py) — `--only declared-hooks-exist` |
| Whether this session's SessionStart hooks actually ran, and repairing them if not | [tools/precedent_session_check.py](tools/precedent_session_check.py) — `--apply` runs them by hand |
| Whether `PRECEDENT_FRESHNESS_ALSO` names repositories that are actually there, and what to set it to on this container | [tools/precedent_session_check.py](tools/precedent_session_check.py) — the row prints the corrected value; a dead entry is skipped silently by design, so nothing else reports it |
| Whether Alex has moved `main` since the last carry onto this branch, and what changed | [tools/precedent_upstream_check.py](tools/precedent_upstream_check.py) — printed at session start; the watermark it compares against is [tools/upstream_watermark.json](tools/upstream_watermark.json), moved with `--record` in the carry's own commit |
| Practices that fire at a moment rather than in a file | [tools/precedent_gate.py](tools/precedent_gate.py) — `merge`, `review`, `push`, `reply` |
| Why the closing **Next Steps** section of a reply is not optional, and what refuses a turn without one | [tools/precedent_reply_check.py](tools/precedent_reply_check.py) — `--explain` says what is declared here; the same requirements are printed at the start of every turn by [tools/precedent_gate.py](tools/precedent_gate.py)'s reply gate |
| Why a long conversation is refused a reply that never says whether this is a cheap point to compact, and the number that decides "long" | [reply_check.json](reply_check.json), read by [tools/precedent_reply_check.py](tools/precedent_reply_check.py); the rule is [practices/session-spend-follows-the-task.md](practices/session-spend-follows-the-task.md) |
| Why a team or individual practice registered to a gate used to load nothing | [tools/precedent_gate.py](tools/precedent_gate.py)'s `resolved_gate_practices` — the gate read one directory until 2026-09-13, so only universal practices ever reached it |
| Which practices are enforced, and running one check | [tools/precedent_check.py](tools/precedent_check.py) — `--list`, `--explain`, `--only SLUG` |
| The catalogue's own figures (resident size, Rule share, coverage) | [tools/catalogue_stats.py](tools/catalogue_stats.py) — never hand-type these into prose |
| Precedent explained for someone adopting it (not a developer) | [documentation/ADOPTING.md](documentation/ADOPTING.md) |
| Public-facing pitch and how-to guides, for people outside the project (marketing, a how-to for developers, a how-to for everyone else) | [documentation/](documentation/) |
| What a normal working day looks like once Precedent is installed — the four habits and the standing command vocabulary, for someone who is not a developer | [documentation/DAILY_HABITS.md](documentation/DAILY_HABITS.md) |
| The theory this project is built on — the essays, the brainstorm, the rules being tried in real work, and what is still unsettled. **The only copy; argument, not rules that bind anything here** | [philosophy/](philosophy/), start at [philosophy/README.md](philosophy/README.md) |
| Why every item in a `philosophy/` essay carries a slug, and what checks that citations resolve both ways — **an experiment, merged; reverting is a revert** | [philosophy/doc-recipes/backlinks.recipe.md](philosophy/doc-recipes/backlinks.recipe.md), engine at [tools/philosophy_backlinks.py](tools/philosophy_backlinks.py) |
| Why `philosophy/` binds nothing outside itself, and the checks that hold that line | [local/practices/philosophy-is-not-repo-policy.md](local/practices/philosophy-is-not-repo-policy.md), [local/practices/philosophy-declares-its-source.md](local/practices/philosophy-declares-its-source.md) |
| How a practice source's harness adapters (its `bootstrap/*.sh`) reach a consuming repo's `.claude/hooks/` without anyone hand-copying them, and why the settings wiring deliberately does not travel | [spec/SOURCES.md](spec/SOURCES.md)'s "Harness adapters travel with the source", mechanism at [tools/precedent_materialize.py](tools/precedent_materialize.py) |
| Which practice libraries are in force in this repo | [precedent.json](precedent.json) |
| An example personal practice set | [examples/practice-set/](examples/practice-set/) |
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
| What each person sets on each machine (individual source, leak blocklist, the optional overrides) | [PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md) |
| Guided-install entry point admins paste to their agent | [SETUP.md](SETUP.md) |
| Member onboarding page (template + rendered sample) | [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md) |
| Git/GitHub concepts for this workflow | [GIT.md](GIT.md) |
| The working method (branches, plain text, critique, prompts) | [METHOD.md](METHOD.md) |
| Phone / ChatGPT / Grok workflows + assistant reliability status | [MOBILE.md](MOBILE.md) |
| A brainstormed chat bridge — reaching a Claude session by voice, Telegram as proof of concept and WhatsApp as destination — **speculative: nobody decided to build it, and no claim in it came from a primary source** | [spec/SPECULATIVE_WHATSAPP_BRIDGE.md](spec/SPECULATIVE_WHATSAPP_BRIDGE.md) |
| CI checks for shell-less agents (install, require) | [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) |
| Whether anything catches a drifted `MAP.md`, `GLOSSARY.md` or loader block in a practice SET (two things do) | [templates/github-actions/views-drift.yml.template](templates/github-actions/views-drift.yml.template) and [templates/github-actions/precedent-check.yml.template](templates/github-actions/precedent-check.yml.template); whether a set needs both is [TODO.md's `views-drift-vs-suite-workflow`](TODO.md#views-drift-vs-suite-workflow) |
| Upstream open items / roadmap | [TODO.md](TODO.md) |
| The full story behind any line in the gotchas index, unabridged | [record/GOTCHAS.md](record/GOTCHAS.md) |
| Gotchas that were shortened or retired, with the verdict that moved each one | [record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md) |
| GitAround — the reading view this work spun out | [alex137/GitAround](https://github.com/alex137/GitAround), a separate product since 2026-08-14; a branch here still staging it under proposals/ is superseded, and its documents live there now |
| Slide-deck engine + deck conventions | [deck/](deck/) — engine [build_deck.py](deck/build_deck.py), practice in [deck/README.md](deck/README.md) |
| Portable audits | [tools/](tools/) — [doc_lint.py](tools/doc_lint.py), [practice_audit.py](tools/practice_audit.py), [checkin.py](tools/checkin.py) |
| Skeletons dependent repos instantiate | [templates/](templates/) (+ per-agent adapters in [templates/harness/](templates/harness/)) |

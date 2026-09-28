---
slug:              todo-2026-09-28-very-deep-check-pass-1-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-28
closed:            null
---
## What

What the 2026-09-28 very deep check's pass 1 (five install, migration, update
and move rehearsals, plus a real update of one consumer) found and did **not**
fix in the same run. What it did fix is in that run's commits. Each line names
where, and the fix the rehearsal recommended.

**Update and deletion**

- `precedent_update.py` `citations()` drops a bare mention of a renamed or
  deduplicated practice, so an update says "no live citation of a withdrawn
  practice" while `precedent_practice_refs.py --withdrawn` finds one. Add a
  branch for any slug in `data['slugs']`, naming its successor.
- An update says DONE on a consumer that still has a root `STYLEGUIDE.md` or
  `VOICE.md` (INSTALL.md calls that a migration step). Leave it for the person
  when the old file exists and its `local/practices/` successor does not.
- Install-once files drift from a fresh install and nothing reports it:
  `.gitignore` lacks `.claude/worktrees/`, and the PR template and `TODO.md`
  still carry old wording. Append missing `templates/gitignore.template` lines.
- The update never checks that the engine landed at the commit it fetched.
- `precedent_install.py` records no `hook_files` in a new consumer's manifest;
  call the hook counterpart of `record_ci_workflow_files` after `_harness()`.
- A vendored copy of `precedent_update.py` inside `process/upstream/` fetches
  the consumer's own origin and fails late; refuse up front and name the
  BestPractice clone's copy.
- `checkin.py` `_default_branch` truncates `claude/x` to `x` and holds a pin to
  `main` that no longer needs holding.
- `missing_template_blocks` calls a block "missing" when it is the template's
  block with one small edit; report "changed (N of M lines)".
- A newly vendored engine file whose upstream `github_api_budgets.json` entry
  the consumer's own registry lacks runs with no call budget.
- The engine's retired-name sweep does not cover `precedent-team-*` →
  `precedent-shared-*`, or `GLOSSARY.md`/`MAP.md`.

**Migration** (spec/MIGRATING_EXISTING_INSTALLS.md)

- `precedent_decommission.py` can never clear `process/personal` in a
  consumer: the basename `personal` matches the vendored engine, the
  materialized `practices/` and ordinary English (141 blockers). Skip files in
  `ENGINE_MANIFEST.json` and the materializer's `MANIFEST.json`, and match a
  directory target as `base/`.
- The doc never says which shared sets to declare; a migration done by the
  book loses six rules to `IN FORCE NOWHERE` with every check green.
- `todo-migrate-available-but-unused` passes on an empty `todo/`; require at
  least one `todo-*.md` or the stub `TODO.md`.
- Steps 3a/3b delete `VOICE.md`/`STYLEGUIDE.md` without repointing their
  `process/manifest.json` entries, which fails `practice-export-loop`.
- Step 1 with an old vendored `checkin.py` mirrors ~950 excluded files; its
  remedy's `git rm -r` fails on untracked paths.
- "One change" conflicts with the decommission tool refusing uncommitted work;
  say one pull request, and run the decommission after step 7 seeds `tools/`.
- The doc never says to run `precedent_vendor_engine.py refresh` after `seed`,
  which is what wires the hooks and retires the old workflows.
- The individual set's `check_commit_author.py` lacks the local-only scoping
  BestPractice's copy has (`270e8ee` on `claude/gallant-johnson-0uno8d`).

**Moving practices** (spec/MOVING_PRACTICES.md)

- Withdrawing a universal practice leaves `routing_audit_state.json` and any
  `# practice: <slug>` citation in `tools/` red.
- A team removal is never checked against that team's approvers, and
  `--dedupe-only` needs no `--approved-by`.
- A current mention inside a long list item that also holds dated text is
  treated as history and left unfixed, and nothing names it.
- Hand-move steps never say to re-home sibling links.
- A universal draft without `## Install` passes the fast checks and fails the
  harness.
- `verify_harness.py --as-ci` hides why a shard crashed.
- The harness covers three of the five move directions.
- A new shared set gets no CODEOWNERS and nothing notices; `build_codeowners`
  hashes all of `precedent.json`, so any unrelated key makes CODEOWNERS read
  stale (hash only the registry).
- `IN FORCE NOWHERE` reads "silently loses a rule" for a deliberate
  withdrawal; record `withdrawn_to: <set>` and say which set carries it.

**Guided install** (SETUP.md)

- Owner step 16: in local Claude Code the session-start hook exits unless
  `CLAUDE_CODE_REMOTE=true`, so `bootstrap.sh` never runs; the installed
  AGENTS.md points at `templates/harness/`, which an install does not have.
- A single-approver set with "require code owner review, no bypass" can never
  merge its approver's own PRs; document it.

**Adapters** (templates/harness/PARALLELS.md)

- Codex, Gemini CLI and Grok Build have hook mechanisms today (pre-tool,
  session-start, stop); the `none because that harness has no …` cells and
  `codex/README.md`'s "no hook mechanism at all" are stale, and the mechanisms
  should transfer. `tools/bootstrap.sh` does not run the watermark check.

---
slug:              todo-2026-10-05-very-deep-check-pass-1-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-05
closed:            2026-10-06
---
## What

What the 2026-10-05 very deep check's pass 1 (adopter installs) found and
did not fix. Rehearsed on `main` at `4116bb7a`, with no personal
configuration: a loader install into an empty repository, an update of a
consumer installed with the 2026-09-24 installer, an update that deletes an
engine file, and an unreachable declared set. Not rehearsed: a migration,
practice moves, a real consumer (none was attached), and the adapters
against each harness's current documentation (no web access).

Fixed the same day: the update sent a pre-2026-10-03 consumer to edit
generated MAP.md and GLOSSARY.md lines, so its first update could not
finish; and a fresh install's full sweep called six code-owners practices
reachable by no channel, because the shipped hook runs `tools/bootstrap.sh`
and the check read only the hook.

- **`document-status-header` can never run in a consumer.**
  [tools/precedent_check.py](../tools/precedent_check.py) imports
  `doc_lifecycle`, which is not in `CONSUMER_ENGINE_FILES`
  ([tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)),
  so the check reports SKIPPED while the practice is in force. Vendor the
  module, or scope the practice to the engine's own repository.
  **Fixed 2026-10-06:** [doc_lifecycle.py](../tools/doc_lifecycle.py) is on `ENGINE_FILES`, which a
  consumer inherits, so `document-status-header` and `speculation-is-marked`
  run in an installed repo. The harness case
  `check_consumer_engine_carries_what_its_checks_import` asserts every
  engine module [precedent_check.py](../tools/precedent_check.py) imports
  reaches a consumer.
- **A Codex or Gemini adopter is never told to add their adapter.**
  [precedent_install.py](../tools/precedent_install.py) installs only the Claude Code adapter;
  [SETUP.md](../SETUP.md) asks which assistant will work in the repo and
  no later step uses the answer; INSTALL.md §1 step 2 covers Claude Code
  only. One "What is left" line pointing at
  [templates/harness/README.md](../templates/harness/README.md), or a
  `--harness` option, closes it.
  **Fixed 2026-10-06:** the installer's report ends with a line saying it
  set up Claude Code only and naming the adapters page for Codex, Gemini
  CLI or another assistant; [SETUP.md](../SETUP.md) step 3 now uses the
  which-assistant answer; INSTALL.md §1 step 2 says which Codex and Gemini
  CLI files go where, and §0 and
  [FOR_DEVELOPERS.md](../documentation/FOR_DEVELOPERS.md) point at it. No
  `--harness` option: neither adapter has been seen to fire in a live
  session yet, so copying them stays a deliberate step. Harness case
  `check_install_names_the_other_assistants_adapters`.
- **A beta-era consumer's first update runs code main does not have.** Its
  own older refresh reads the integration branch, so the report says
  `refreshed from precedent-beta-v01 @ b45fcf1f` under `source: main`. The
  end state matches main; the path to it does not. Always pass the main
  commit with `--from-ref`, and report the final leg.
  **Fixed 2026-10-06:** [precedent_update.py](../tools/precedent_update.py)
  hands the consumer's engine refresh the tip it read, for main as for a
  repo following `staging`, and its report shows the pass that landed on
  that tip, named by branch. The one exception is an engine recorded ahead
  of the tip, still left to the refresh's no-rollback guard. Harness case
  `check_update_hands_the_engine_refresh_the_followed_tip`.
- **A fresh install fails its own link convention.** INSTALL.md §0 step 8's
  lint reports 18 unlinked file names in the loader, MAP and local-practice
  templates, while the installer says the light check passed.
  **Fixed 2026-10-06:** the loader AGENTS.md, MAP and both local-practice
  templates link every file name they write (or name a command instead
  of a file), and the installer counts an unlinked name outside a
  generated block as a failed light check, since the lint only warns.
  One warning is left, and it is not a template's: the generated block's
  standing instruction names the untracked session file under
  `.precedent/`, which a link cannot point at, from
  [build_views.py](../tools/build_views.py). Harness case
  `check_fresh_install_links_its_file_names`.
- **The update says "engine already current" in the same run that deleted
  an engine file.** Cosmetic; the deletion and its report are right.
  **Fixed 2026-10-06:** the refresh's already-current line says "only
  removed the engine file(s) it no longer includes" when that pass removed
  one, and Update Vendors' report shows a pass that refreshed files rather
  than a later pass that found nothing left to do. Harness case
  `check_refresh_never_says_nothing_to_do_after_removing_a_file`.

## How It Closes

Each bullet is fixed or recorded here as declined, with the reason.

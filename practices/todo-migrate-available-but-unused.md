---
slug:        todo-migrate-available-but-unused
title:       A vendored migration tool a repo has never run is a finding, not a footnote
tier:        on-demand
severity:    default
applies_to:  ["TODO.md"]
occasion:    "editing TODO.md, or just after a vendor refresh brings tools/todo_migrate.py into a repo for the first time"
gates:       []
index_clause: "the tool arrived but TODO.md never got migrated -- run it now"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-19"
approved_by: "pending review"
---
## Rule
When `tools/todo_migrate.py` is vendored into a repo and that repo's
`TODO.md` still carries real old-format item bullets — no `todo/`
directory, the file does not open on the `# TODO has moved` stub heading,
and it has actual content to convert, not just a fresh install's unused
pointer template — the migration tool is present and has never been run.
Run it: `python3 tools/todo_migrate.py --apply`, then `python3
tools/build_todo_index.py`, per
[vendor-update-runbook](vendor-update-runbook.md)'s step for a
newly-vendored migration tool. A vendor refresh can ship a mechanism;
nothing else makes anyone actually use it.

## Why
A vendor update can silently ship a mechanism nobody ever triggers.
BestPractice migrated its own `TODO.md` to the per-item format on
2026-09-15/16 and vendored the converter into every consumer's engine the
same way — but the item that did it never told existing consumers to
actually run the tool against their own `TODO.md`. Confirmed 2026-09-19
across a real set of Precedent-consumer repos: most were still on the old
format, days after the tool became available, and nothing anywhere
flagged it.

## Story
Confirmed 2026-09-19: 8 of 11 Precedent-consumer repos were still on the
old single-file `TODO.md` format, 3+ days after `tools/todo_migrate.py`
and `tools/build_todo_index.py` were vendored out to every consumer by
the 2026-09-15/16 migration (`todo/todo-2026-09-15-execute-open-item-gotcha-migration.md`).
Nothing in the engine distinguished a consumer that had the tool and used
it from one that had the tool and never touched it, so the gap sat
unflagged until someone went and checked by hand across the whole repo
set.

The same check found `precedent-individual` and `precedent-team-writing`
(both `kind: source` in their own `ENGINE_MANIFEST.json`) carrying
old-format `TODO.md`s of their own — 520 and 112 lines — and unable to
run the migration at all: `todo_migrate.py` and `build_todo_index.py`
were `CONSUMER_ENGINE_FILES`-only, on the reasoning that a source set has
no `TODO.md` of its own to convert. That reasoning was wrong for these two
real repos, so the same vendor-engine change that keeps this check
truthful for a source set (`precedent_vendor_engine.py`'s `ENGINE_FILES`)
moved both tools into the shared list the same day.

The check's first version fired on a genuinely fresh install, too: a
brand-new project vendors `tools/todo_migrate.py` the same as any real
consumer, and its `TODO.md` — instantiated from
`templates/TODO.md.template`, a pointer, never populated — has neither
the stub heading nor a `todo/` directory yet either, the same two
signals a real unmigrated repo has, with nothing to actually migrate.
Caught the same day by `verify_harness.py`'s
`check_installer_produces_a_clean_install`, before this check ever
shipped to a real consumer. Requiring a real old-format item bullet in
the file — the one signal that only a genuinely unmigrated `TODO.md`
carries — fixed it.

## Install
`tools/precedent_check.py`'s `todo-migrate-available-but-unused` check
(tree scope) fires when `tools/todo_migrate.py` exists on disk,
`tools/ENGINE_MANIFEST.json` declares a `kind` at all — `source` or
`consumer` alike, both vendor the tool since 2026-09-19 — `TODO.md`
exists at the repo root, no `todo/` directory is present, the file does
not open on the stub heading, and it carries at least one real
old-format item bullet. It reports the finding against `TODO.md`, naming
the exact commands to run. It is silent (no finding, not merely skipped)
in BestPractice itself, which vendors nothing into itself and so never
resolves a `kind` here at all.

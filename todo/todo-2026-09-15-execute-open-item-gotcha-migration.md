---
slug:              todo-2026-09-15-execute-open-item-gotcha-migration
kind:              analysis
domain:            null
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-15
closed:            "2026-09-16"
---
## What

- <a id="execute-open-item-gotcha-migration"></a>**Execute the open-item and
    gotcha migration.** [spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](../spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
    (merged 2026-09-16, PR #421) specifies the full replacement for this
    file and the gotchas index — one item per file, `todo/`/`gotchas/`
    directories, generated views, a native date-gated Reminders mechanism —
    and records three decisions as settled. The document's own Part 4.1
    sequence — steps 1–4, a review pause with a dry run against real
    items, then steps 5–10, announcing step 5 explicitly when it starts —
    has now run in full; see Notes.

    **Notes:**
    2026-09-16: Part 4.1 steps 1-4 done. Step 1: the five tool files'
    stale `TODO.md item N` citations (`tools/precedent_check.py`,
    `tools/precedent_gate.py`, `tools/precedent_paths.py`,
    `tools/precedent_vendor_engine.py`, `tools/verify_harness.py`)
    repointed to anchors, or to plain historical prose where the cited
    item's own anchor no longer exists. Step 2: every item already marked
    done, closed, resolved, decided, or withdrawn pruned from this file —
    still in git history, and cross-references to a pruned anchor
    (elsewhere in this file, and in spec/CHANGES_TO_TELL_ALEX.md,
    spec/PRELAUNCH_AUDIT.md, WHERE_THINGS_ARE.md,
    templates/harness/LEDGER.md, record/GOTCHAS.md,
    practices/rule-level-by-reach.md, practices/reduction-pass.md)
    repointed to plain prose saying so. Step 3: the leading `N.` stripped
    from every remaining item; each is now a plain `- <a id="slug">`
    bullet. Step 4: `tools/todo_migrate.py` and `tools/build_todo_index.py`
    written.

    2026-09-16: steps 5–10 run, step 5 announced by name at the start as
    required. Step 5: the full conversion — 105 `todo/todo-*.md` files and
    77 `gotchas/gotcha-*.md` files (44 live, from record/GOTCHAS.md; 33
    retired, from record/GOTCHAS_ARCHIVE.md) — via
    `tools/todo_migrate.py --apply`, plus
    spec/TODO_GOTCHA_MIGRATION_MAP.md recording all 182 old-anchor →
    new-file mappings. One item's guessed status was hand-corrected
    (`todo-2026-09-07-stem-note-reaches-the-sets` — withdrawn the same day
    it was noted; set to `dropped` rather than the migrator's guess).
    Step 6: every reference to a `TODO.md` per-item anchor across the repo
    (17 files) repointed to its new `todo/todo-*.md` path; a systemic
    relative-link breakage the migration itself introduced (files moved
    one directory deeper) was found and fixed across ~97 todo/ and
    gotchas/ files. Step 7: `tools/precedent_check.py`'s
    `todo-gotcha-stale-reference` check built and wired (flags a stale
    link to a `TODO.md` per-item anchor, a bare "TODO item N" phrase, or a
    bare `#gN`-style gotcha anchor outside record/GOTCHAS*.md), plus TODO.md rewritten
    to a redirect stub carrying that refusal notice. Step 8: this repo's
    two Part 3 sweeps (open-item sweep, gotcha-retirement candidates)
    wired into `tools/very_deep_check.py`, replacing its old
    TODO.md-based section. Step 9: this item's own `retires_when`
    population work filed as
    [`todo-2026-09-16-file-retires-when-on-live-gotchas`](todo-2026-09-16-file-retires-when-on-live-gotchas.md).
    Step 10: AGENTS.md updated with the TODO.md-refusal notice and
    MAP.md regenerated via `tools/build_views.py`
    (`tools/todo_migrate.py`/`tools/build_todo_index.py` added to its
    `TOOLS_DESCRIPTIONS`); AGENTS.md's gotcha index itself becoming a
    generated view was judged out of this step's scope and left for a
    separate session. `tools/verify_harness.py` extended with
    `check_todo_gotcha_stale_reference_fires` and
    `check_todo_and_gotcha_sweeps`, and a planted-violation case for the
    new check registered in `check_precedent_check_fires`. Full deep
    check run clean: 212 passed, 1 not-yet-applicable, 1 failed — the one
    failure is `check_very_deep_check_bootstrap_drift`'s pre-existing,
    unrelated `.pyc`-cache comparison against the live
    `~/precedent-individual` clone, not a file this migration touched.
    Nothing committed or pushed yet; awaiting authorization.

## How It Closes

Closes when: a session runs the document's own Part 4.1 sequence — steps
1–4, a review pause with a dry run against real items, then steps 5–10,
announcing step 5 explicitly when it starts. Done as of 2026-09-16 (see
Notes above); the migration's own conversion, reference repointing, new
check, and Part 3 sweeps are all in place and verified. Committing and
pushing this work is a separate act, gated on explicit authorization, not
on this item's own closing condition.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

# TODO has moved

**This file is a redirect stub, kept per
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](spec/OPEN_ITEM_AND_GOTCHA_PLAN.md) Part
4.4's "the file may need to exist briefly as a redirect stub" — so anything
still linking here lands somewhere useful rather than at a 404.** Open
items live under [todo/](todo/) now, one file per item, and the list a
person actually reads is generated: [todo/TODO.md](todo/TODO.md) (open) and
[todo/CLOSED.md](todo/CLOSED.md) (done or dropped), rebuilt by
`python3 tools/build_todo_index.py` the way [MAP.md](MAP.md) is rebuilt from
`practices/*.md`.

**A new item added to this file is refused by the deep check**
([tools/precedent_check.py](tools/precedent_check.py)'s
`todo-gotcha-stale-reference` check, which refuses an item bullet here) —
file the item under `todo/` instead,
as a new `todo/todo-<date>-<slug>.md` file, per
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)'s Part
1.

Migrated 2026-09-16, 105 items into [todo/](todo/) and 77 gotchas into
[gotchas/](gotchas/) (from [record/GOTCHAS.md](record/GOTCHAS.md) and
[record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md), both unchanged —
they then held the full gotcha story text
[AGENTS.md](AGENTS.md)'s gotcha index linked into; only the *tracking* —
status, dates, `retires_when` — moved to [gotchas/](gotchas/)'s per-entry
files) — full old-slug -> new-file mapping at
[spec/TODO_GOTCHA_MIGRATION_MAP.md](spec/TODO_GOTCHA_MIGRATION_MAP.md).
**Not done in this pass:** making AGENTS.md's gotcha index itself
generated from `gotchas/*.md` (Part 2's "Generated View") — it stays
hand-kept, unchanged, still linking into `record/GOTCHAS.md#gN` as
before; a real change to AGENTS.md's generation pipeline and its token
budget, deliberately deferred rather than rushed. **Since done:**
AGENTS.md now carries only a pointer and a grep instruction, and the
one-line index is the generated [gotchas/INDEX.md](gotchas/INDEX.md),
rebuilt by `python3 tools/build_gotcha_index.py`. On 2026-10-17
[record/GOTCHAS.md](record/GOTCHAS.md) stopped being a live copy (its
header names [gotchas/INDEX.md](gotchas/INDEX.md) as its successor): each
entry's own file under [gotchas/](gotchas/) is the one kept current.

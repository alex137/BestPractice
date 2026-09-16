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

**A pull request touching this file is refused by CI**
([tools/precedent_check.py](tools/precedent_check.py)'s
`todo-gotcha-stale-reference` check) — file the item under `todo/` instead,
as a new `todo/todo-<date>-<slug>.md` file, per
[spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)'s Part
1.

Migrated 2026-09-16, 105 items into [todo/](todo/) and 77 gotchas into
[gotchas/](gotchas/) (from [record/GOTCHAS.md](record/GOTCHAS.md) and
[record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md), both unchanged —
they still hold the full gotcha story text
[AGENTS.md](AGENTS.md)'s gotcha index links into; only the *tracking* —
status, dates, `retires_when` — moved to [gotchas/](gotchas/)'s per-entry
files) — full old-slug -> new-file mapping at
[spec/TODO_GOTCHA_MIGRATION_MAP.md](spec/TODO_GOTCHA_MIGRATION_MAP.md).
**Not done in this pass:** making AGENTS.md's gotcha index itself
generated from `gotchas/*.md` (Part 2's "Generated View") — it stays
hand-kept, unchanged, still linking into `record/GOTCHAS.md#gN` as
before; a real change to AGENTS.md's generation pipeline and its token
budget, deliberately deferred rather than rushed.

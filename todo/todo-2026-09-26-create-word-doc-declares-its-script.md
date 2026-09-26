---
slug:              todo-2026-09-26-create-word-doc-declares-its-script
kind:              analysis
domain:            vendoring
severity:          null
status:            done
disposition:       null
remind_on:         null
blocked_on:        "precedent-shared-writing not attached with push this session"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-26
closed:            2026-09-26
---
## What

**`create-word-doc` in `precedent-shared-writing` adds
`ships: ["tools/create_word_doc.py"]` to its frontmatter**, and its Detail's
"Vendoring" paragraph stops telling consumers to copy the script in by hand:
the materializer now delivers it
([practice-carries-its-files](../practices/practice-carries-its-files.md)).

The line is inert under an older engine, so it can land before the set
takes the engine that reads it. Once the set runs `Update Vendors` with that
engine, its own push check runs `practice-carries-its-files`, which fails
on this practice until the line is there (measured on a scratch copy of the
set, 2026-09-26: the one finding in all four sets).

The consuming repository that went red is fixed on its first
`Update Vendors` after both have landed: its sync delivers the script, and
the materialized test passes.

## Why queued

The implementing session had `precedent-shared-writing` attached read-only.
The sweep of all four sets and this catalogue for a practice whose Rule
names an undeclared `tools/` file found this one real case; the other hits
were universal practices citing this repository's own tools by upstream URL
and per-repository registries that must not ship.

## Closes when

`precedent-shared-writing`'s `practices/create-word-doc.md` carries the
`ships:` line on its routine branch.

## Closed 2026-09-26 — the line is in

`precedent-shared-writing`'s `create-word-doc` carries
`ships: ["tools/create_word_doc.py"]` on its `pre-staging`
([fad7f5e](https://github.com/themorgan/precedent-shared-writing/commit/fad7f5e)),
and its Vendoring paragraph no longer tells consumers to copy the script by
hand. Morgan, 2026-09-26: "Go ahead on shared writing" (strength: assented).
Checked before the push, with this repository's `staging` engine against the
set: `practice-carries-its-files` passes, and fails on the set's previous
copy of the practice, naming the test's read of the script; the
consumer-shaped test pass goes from `test_create_word_doc.sh` failing to all
five passing. It reaches a consumer once the set promotes to its `main` and
the consumer takes an engine from BestPractice `main` that reads `ships:`.

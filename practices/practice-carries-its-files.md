---
slug:        practice-carries-its-files
title:       A practice declares every file it owns, and they travel and move with it
tier:        on-demand
severity:    default
applies_to:  ["practices/*.md", "tools/checks/tests/*.sh"]
occasion:    "writing a practice that owns a file besides its check script and test -- a tool its Rule tells a session to run, a file its test reads -- or moving a practice to another set"
gates:       []
index_clause: "declare the files a practice owns in `ships:`; a move carries the practice, its check, its test and those files in one commit"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-26"
approved_by: "Morgan, 2026-09-26, asking for the root fix rather than the instance after a consumer's deep check went red on create-word-doc's test; relayed to the implementing session by the session that found it"
---
## Rule
**A practice that owns a file besides its `checked_by` script and that
script's test declares it in `ships:`** — a tool its Rule tells a session
to run, a file its shipped test reads, anything a consumer needs for the
practice to work:

```
ships:       ["tools/create_word_doc.py"]
```

**The declaration is what delivers it.**
[`precedent_materialize.py`](../tools/precedent_materialize.py) copies
each shipped file to the same path in every consuming repository, records
it in `MANIFEST.json`, and reports drift from it. **"Copy it in by hand" is
not an install step any more** — a practice that says it has a dependency
nothing declares.

**A practice moves with everything it owns, in one commit:** the practice
file, its `checked_by` script, that script's test, and every `ships:` file.
[`tools/precedent_move.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_move.py)
refuses a move whose destination does not carry
them yet, and this repository's check refuses a publishing set whose
practice names a file the set does not have.

**A consumer that does not want a shipped file declines it with a reason**,
in its own `precedent.json`:

```
"declined_ships": {"tools/create_word_doc.py": "we never export .docx"}
```

**Never hand-edit a delivered copy**: the next sync reverts it and says so.
A repository that needs its own version declines the shipped one.

## Detail
What the check (`practice-carries-its-files`, in
[`precedent_check.py`](../tools/precedent_check.py)) holds a publishing
repository to, at its own push:

- **every `ships:` entry is legal and present** — a concrete relative path,
  not a glob, not under `practices/` or `tools/checks/` (those travel
  already), not an engine file (vendoring owns those), and a file this
  repository actually carries;
- **every concrete `applies_to` path and the `checked_by` script exist
  here** — a concrete path a practice fires on is one it owns;
- **every `tools/` file outside `tools/checks/` that the practice's shipped
  test reads through its root variable** (`$ROOT/tools/...`,
  `$SET_ROOT/tools/...`) is a vendored engine file or declared in `ships:`
  by some practice here. A path the test probes first (`[ -f "$ROOT/..." ]`)
  counts as handled.

The static read misses a file a test reaches any other way. The source's
push check covers that half:
[`precedent_consumer_shape.py`](../tools/precedent_consumer_shape.py) runs
every shipped test in a consumer-shaped scratch copy, which has none of the
source's own `tools/` except the engine, `tools/checks/` and what practices
ship, so a test that assumes a source-only file fails at home.

**Materialization's refusals, all before anything is written:** a malformed
`ships:` list or entry, a destination two sources both ship, a destination
that is also a declared harness adapter, and a malformed `declined_ships`
(an entry with no reason). A declared file missing from its source warns
and is skipped (usually a stale clone). A decline naming nothing any
practice ships warns as stale. A file this tree received and no practice
ships any more is reported and left in place, never deleted.

## Why
Nothing declared a practice's own files, so nothing could deliver them,
and nothing could notice one left behind. A checked_by claim has nothing
behind it if only the practice file travels, and the same is true of a
tool the Rule depends on. The materializer already carried checks and
harness adapters for exactly this reason; a practice's other files were
the one thing still travelling by somebody remembering.

## Story
2026-09-26: `precedent-shared-writing`'s `create-word-doc` practice owns
`tools/create_word_doc.py`. Its shipped test runs
`cp "$SET_ROOT/tools/create_word_doc.py" ...`, and the practice's own Detail
said consumers "copy it in by hand". A consuming repository that had not
ran the materialized test in its deep check and went red on it, with no way
to fix a test that belongs to another source. Morgan asked for the root fix
rather than a patch to that one test: declare the dependency, deliver it,
catch a practice that moves without it at the source, and run shipped
tests without the source's own `tools/` so the class fails at home first.

## Install
Nothing to install beyond the engine. A practice set adds `ships:` to each
practice that owns a file; its next push runs the check, and each consumer
receives the files on its next sync after taking the engine
(`Update Vendors`).

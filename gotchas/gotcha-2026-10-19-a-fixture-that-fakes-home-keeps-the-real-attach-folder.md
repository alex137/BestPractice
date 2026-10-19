---
slug:            gotcha-2026-10-19-a-fixture-that-fakes-home-keeps-the-real-attach-folder
status:          live
noted:           2026-10-19
severity:        notable
retired:         null
retires_when:    "every verify_harness fixture that runs the source bootstrap sets its own project dir and harness, or the bootstrap stops reading the project dir from the environment"
---
## Symptom

A harness case that sets `HOME` to a temporary folder still clones into,
links to, or pulls a real practice set, such as `/home/user/precedent-individual`.
Or a case passes on GitHub's runner and fails in a Claude Code cloud
session, or the other way round, with a path outside its temporary folder
in the output.

## Story

**2026-10-19.** The first version of the per-harness home folder
([`precedent_source_home.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_source_home.py))
passed the individual set's clone path from the hook script. On Claude
Code on the web the home folder is the attach folder, which is read from
`CLAUDE_PROJECT_DIR`. The self-heal case in
[`verify_harness.py`](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py) fakes `HOME` but sets
`CLAUDE_PROJECT_DIR` to the real checkout and `CLAUDE_CODE_REMOTE=true`, so
the hook pointed the engine at this container's real
`/home/user/precedent-individual`, and the engine adopts whatever tree sits
at the path it is given. Nothing changed there: the pull found it current.
A second case inherited `CLAUDE_CODE_REMOTE` from the container and
expected the `$HOME` layout, so it failed here and would have passed on the
runner.

## Fix

The engine now decides the home folder itself and uses a tree there only
when its origin is the set being cloned, as it already did for the attach
copy. A fixture that runs the bootstrap owns every variable the home folder
is read from: `HOME`, `PRECEDENT_PROJECT_DIR` and `CLAUDE_PROJECT_DIR`,
`CLAUDECODE`, `CLAUDE_CODE_REMOTE`, `PRECEDENT_HARNESS` and
`PRECEDENT_SOURCE_HOME` (practice: fixture-owns-its-state). Run a new case
both inside a cloud session and with those unset, as GitHub's runner sees
it.

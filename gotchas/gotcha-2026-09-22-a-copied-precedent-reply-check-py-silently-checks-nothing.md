---
slug:            gotcha-2026-09-22-a-copied-precedent-reply-check-py-silently-checks-nothing
status:          live
noted:           2026-09-22
severity:        null
retired:         null
retires_when:    null
---
## Symptom

[`precedent_reply_check.py`](../tools/precedent_reply_check.py), copied on
its own into another directory, exits
**0 on every input** — including replies that plainly violate a blocking
requirement in the `reply_check.json` it was pointed at.

## Story

A 2026-09-22 harness fixture needed to swap the container scanner for a stub
with a known exit code, so it copied the one file it was testing —
[tools/precedent_reply_check.py](../tools/precedent_reply_check.py) — into a
temp `tools/` beside the stub, and ran it with `--repo <fixture>`.

**It resolved no sources at all.** That script finds the practice sources
through [`precedent_resolve.py`](../tools/precedent_resolve.py), which it
imports from *its own directory*, and which in turn needs
[`split_practices.py`](../tools/split_practices.py),
[`build_views.py`](../tools/build_views.py) and
[`precedent_identity.py`](../tools/precedent_identity.py) beside it. With none of them there, the import fails,
the script falls back to "no source declares a `reply_check.json`" and exits 0
without reading anything. The one line saying so goes to `--explain`; an
ordinary run prints nothing.

That is the worst possible shape for a test fixture, because **every negative
control expects exit 0**. Three of the four wiring cases passed for exactly
the wrong reason and only the positive case failed — and it failed silently
for a further day, because the check itself had never been wired into the
harness's own call list (see `check_every_verdict_returning_check_is_recorded`
in [tools/verify_harness.py](../tools/verify_harness.py), widened the same
day to catch that).

## Fix

**Copy the whole `tools/` directory, then swap the one file.**
`shutil.copytree(ROOT / 'tools', d / 'tools')` costs about 8 MB and a
fraction of a second, and gives a fixture that resolves sources the way a
real vendored engine does. Testing against the real
`ROOT / 'tools' / 'precedent_reply_check.py'` in place is the other route, and
is what the fence-block check does — but it cannot plant a sibling.

**Confirm the fixture engine is live before trusting a green run:** run it once
with `--explain` and check the output names the fixture's `reply_check.json`.
A fixture that checks nothing reports success.

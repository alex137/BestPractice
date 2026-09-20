---
slug:            gotcha-2026-09-13-a-repo-attached-mid-session-never-runs-its-own-sessionstart-
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A repo attached mid-session never runs its own SessionStart hook, so every environment guarantee that hook provides is silently absent while you work in it.

## Story

**A repo attached mid-session never runs its own SessionStart hook, so every
environment guarantee that hook provides is silently absent while you work in
it.** SessionStart hooks fire for the session's *primary* repo only. A sibling
attached with `add_repo` is just a directory on disk: its hook is never
executed, no matter that it is committed, executable and correct. 2026-09-06:
`verify_harness.py` reported a broken `doc_html.py` twice over, and both were
the same missing module the hook installs on line 13. **The failure reads like
a broken tool and is an unrun hook**, so the reflex to go debug the tool is
wasted. `pip install cmarkgfm markdown` by hand once per session you work in
an attached sibling — the harness went from `1 failed` to `0 failed` with no
code change. Treat every entry here that says "the session-start hook does
this" as **not** done when you arrived as a sibling. **One guarantee has an
environment-level route out of this since 2026-09-11, and only one**: the
freshness guard reads `PRECEDENT_FRESHNESS_ALSO` (`;`-separated `<path>=<base
branch>`), so a session can have attached repositories checked even though
their own hooks never fire — an environment variable follows a session into
every repository it touches, the same reasoning as `PRECEDENT_COMMIT_*` for
identity. **Write the path as `~/name`, never spelled out.** An individual
practice source lives at `$HOME/precedent-individual` and `$HOME` is `/root`
on some containers and `/home/user` on others, so an absolute path written on
one names nothing on the next — and a dead entry is skipped rather than
blocked on, deliberately, so the variable goes on reading as coverage while
covering nothing. This environment's own entry did exactly that from the day
it was set until 2026-09-11, naming `/home/user/precedent-individual` while
the clone sat at `/root/precedent-individual`. The guard expands `~`, `$HOME`
and `$CLAUDE_PROJECT_DIR` now, so one value is correct everywhere, and
`python3 tools/precedent_session_check.py` has a row that names any entry
still resolving to nothing and prints the value to set instead. Nothing else
in this entry is covered: the `pip install`, the path-trigger channel and the
rest still need doing by hand.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

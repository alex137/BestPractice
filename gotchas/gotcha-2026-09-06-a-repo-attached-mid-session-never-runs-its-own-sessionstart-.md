---
slug:            gotcha-2026-09-06-a-repo-attached-mid-session-never-runs-its-own-sessionstart-
status:          retired
noted:           2026-09-06
severity:        null
retired:         "2026-09-06"
retires_when:    null
---
## Symptom

A repo attached mid-session never runs its own SessionStart hook, so

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A repo attached mid-session never runs its own SessionStart hook, so
  every environment guarantee that hook provides is silently absent while
  you work in it.** SessionStart hooks fire for the session's *primary*
  repo only. A sibling attached with `add_repo` — which is how this repo
  is present whenever a dependent repo's session needs it for a vendor
  refresh or a check-in — is just a directory on disk: its
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) is
  never executed, no matter that it is committed, executable, and correct.
  2026-09-06, working here from a dependent repo's session:
  `python3 tools/verify_harness.py` reported `FAIL: every tool answers
  --help with exit 0 ... doc_html.py exited 1`, and separately
  `N/A: rendered documents are current -- tools/doc_html.py could not be
  imported (No module named 'markdown') -- not a pass`. Both were the same
  missing module, which this repo's own hook installs on line 13 and has
  installed since 2026-09-04 — it simply had not run. The failure reads
  like a broken tool and is an unrun hook, so the reflex to go debug
  `doc_html.py` is wasted. `pip install cmarkgfm markdown` by hand once
  per session you work in an attached sibling, then re-run the gate: the
  harness went from `1 failed` to `0 failed` with no code change at all.
  The same reasoning covers the refspec repair and the freshness warning
  further down that hook — none of them ran either, so treat every entry
  in this section that says "the session-start hook does this" as *not*
  done when you arrived here as a sibling.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

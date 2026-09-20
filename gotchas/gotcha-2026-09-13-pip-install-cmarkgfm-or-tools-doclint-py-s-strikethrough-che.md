---
slug:            gotcha-2026-09-13-pip-install-cmarkgfm-or-tools-doclint-py-s-strikethrough-che
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

`pip install cmarkgfm markdown`, or two gates degrade and a third fails for reasons that have nothing to do with the tree.

## Story

**`pip install cmarkgfm markdown`, or two gates degrade and a third fails
for reasons that have nothing to do with the tree.** Neither is in the
standard library, and the two behave differently, which is what makes this
worth reading twice.

**cmarkgfm — silent.** Without it
[tools/doc_lint.py](../tools/doc_lint.py)'s strikethrough check does not
fail: it prints a one-line notice and scans for everything else, so a
document that renders an unintended `<del>` on GitHub passes the gate. The
`doc-references-are-links` check in
[tools/precedent_check.py](../tools/precedent_check.py) skips for the same
reason and says so in one line among fifty.

**markdown — one tool, one exit code.** [tools/doc_html.py](../tools/doc_html.py)
imports it at module level, so `--help` exits 1 and the deck engine cannot
render `.md` slides.

**Where it actually bites is [tools/verify_harness.py](../tools/verify_harness.py),
which does NOT degrade.** It fails the checks that need them, and each failure
describes what it was *testing* — strikethrough cases, a planted
`doc-references-are-links` violation, a `--help` sweep across 56 tools — never
what is missing. On 2026-09-14 that read as `3 failed` on a branch whose entire
diff was two markdown files, and took two full harness re-runs to attribute:
install `cmarkgfm`, down to 1 failed; install `markdown`, `202 passed, 0
failed`. The harness now names the missing packages in a preflight line and
again in the closing recap, so the shortest reading of its output says
"environment", not "your diff".

**Both are installed by
[.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh)** (only
when `CLAUDE_CODE_REMOTE=true` — a local shell has to do it), and by both CI
workflows. **So a container missing them is telling you the hook never ran**,
which is a much larger fact than two absent packages: the same session had
neither the generated session-practices file the private sources write, nor
the commit backstop. That session
was rooted one directory ABOVE this repository — see [g17](../record/GOTCHAS.md#g17) — so none of
its hooks fired, silently. [`python3 tools/precedent_session_check.py`](../tools/precedent_session_check.py) reports
all of those guarantees at once, and its packages row now names `pip install`
as the remedy rather than `--apply`, because `--apply` re-runs the hook that
could not run.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

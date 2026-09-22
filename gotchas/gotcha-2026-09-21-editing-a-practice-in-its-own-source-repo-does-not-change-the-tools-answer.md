---
slug:            gotcha-2026-09-21-editing-a-practice-in-its-own-source-repo-does-not-change-the-tools-answer
status:          live
noted:           2026-09-21
severity:        null
retired:         null
retires_when:    null
---
## Symptom

You edit `practices/<slug>.md` **inside the source repo that owns that
practice**, then run one of the engine tools to confirm the change —
[tools/precedent_vocabulary.py](../tools/precedent_vocabulary.py) is the
measured case. **The tool prints the old value.** Exit code 0, no warning, file
on disk demonstrably correct.

Re-reading the file, re-running the tool, and checking the frontmatter by hand
all confirm the edit. The tool keeps disagreeing.

## Story

**Measured 2026-09-21**, twice and from two directions.

A session in `precedent-individual` removed a practice's `command:` field and
ran [precedent_vocabulary.py](../tools/precedent_vocabulary.py) to check the row was gone. It was still there.
The file was right; the tool was reading somewhere else.

**The mechanism is in `collect()` and it is not a bug so much as an unstated
precedence rule.** It builds one dict keyed by slug:

1. every `practices/*.md` in the **current repo**, tagged `universal`;
2. then every practice [tools/precedent_resolve.py](../tools/precedent_resolve.py)
   returns, assigned with a **plain `found[slug] = ...`** — no guard, no
   comparison, no note.

Step 2 silently wins. In an ordinary consuming repo that is exactly right: the
local `practices/` is that repo's own rules and the resolved sources are
everyone else's. **In a repo that IS one of those sources, the two halves are
the same practice**, and step 2 replaces your edit with whatever the resolver
found — which is a *different checkout*, located through
`~/.config/precedent/config.json` (or `PRECEDENT_USER_CONFIG`). Same repository,
different clone, different commit, and nothing says so.

**Confirmed independently from the other side.** From a BestPractice session,
pointing `PRECEDENT_USER_CONFIG` at a `git worktree` of the individual source
at `origin/main` flipped the same tool's output from wrong to right without
touching either clone — the local file never changed, only which checkout the
resolver reached. That is the whole effect.

**Why it costs an hour rather than a minute.** Every obvious check confirms
your edit. `cat` shows the new value, `git diff` shows the change, the commit
lands. The only thing that disagrees is the tool, and the natural reading of a
tool that disagrees with the file is that you edited the wrong field, or the
frontmatter parse is fussy, or a cache needs clearing. None of those is it, and
none of them leaves a trace when you test them.

## Fix

**Check which checkout the resolver is actually reading before believing the
tool.** `cat ~/.config/precedent/config.json` names the path per source; if it
is not the directory you just edited, the tool is not measuring your change.

To verify an edit without touching any clone, point the resolver at a read-only
checkout of the revision you care about:

    git -C <source clone> worktree add --detach /tmp/src-check origin/main
    PRECEDENT_USER_CONFIG=/tmp/cfg.json python3 tools/precedent_vocabulary.py

where `/tmp/cfg.json` is a copy of the user config with that source's `path`
repointed. Remove the worktree afterwards with `git worktree remove`.

**This is a workaround, not a repair.** The durable fix is for `collect()` to
notice that a resolved source's path is not the repo it is running in and say
so — one line of output would have turned this into a thirty-second problem.
Filed as
[todo/todo-2026-09-21-resolver-overwrites-a-source-repos-own-practice-silently.md](../todo/todo-2026-09-21-resolver-overwrites-a-source-repos-own-practice-silently.md).

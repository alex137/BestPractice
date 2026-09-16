---
slug:              todo-2026-09-11-source-clause-check-reads-only-html-comments
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-11
closed:            null
---
## What

- <a id="source-clause-check-reads-only-html-comments"></a>**The `Source:`
    clause check reads only HTML comments, so a generated file whose header is
    a `#` comment is never asked for one.**
    [generated-edit-goes-upstream](../practices/generated-edit-goes-upstream.md)'s
    check looks for its marker only inside an HTML comment
    (`<!-- ... -->`), which covers every markdown view and the loader block.
    It does not cover the two generated files here whose headers are shell or
    Python comments:
    [tools/precedent_materialize.py](../tools/precedent_materialize.py)'s emitted
    `run_all.sh`, whose header is a `# GENERATED FILE` line carrying the same
    marker, and [tools/build_codeowners.py](../tools/build_codeowners.py)'s
    `CODEOWNERS`.
    Both name the script that rebuilds them; neither names where a change
    belongs, which is the half the rule is about. Found 2026-09-11 while
    sweeping every header in the tree after fixing the clause matcher — the
    sweep is what made the gap visible, since these files never appear in the
    check's own output at all.
    **Out of scope for that fix rather than blocked:** widening the matcher to
    `#` headers is a scope decision with its own sweep to run first, and a
    check that starts firing on files nobody has written a clause for yet is
    exactly what [checkable-gets-checked](../practices/checkable-gets-checked.md)
    forbids landing unmeasured. The work is: extend `_DONT_EDIT_RE` to the
    `#`-comment form, run it against the whole tree, add the clause to
    whatever it names, and plant a case per header shape.
    **Disposition:** wait (2026-09-11 — no session has set this to `ask`)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

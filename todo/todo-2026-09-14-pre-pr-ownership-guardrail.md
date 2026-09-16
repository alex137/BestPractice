---
slug:              todo-2026-09-14-pre-pr-ownership-guardrail
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the pilot, for the wording of both halves — the hooks' refusals are translated by a session that has met a real contributor's confusion, not by one guessing at it."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="pre-pr-ownership-guardrail"></a>**Before opening a pull request,
    the session should say in plain words when the change will wait for
    review, and offer to split it.** Diff the touched paths against
    `CODEOWNERS`; tell the contributor *"this touches the project's
    settings, so the maintainer has to look at it before it lands — want me
    to put the document part in now on its own?"* User experience, not
    enforcement; it closes the "worse error" bullet in
    [`review-skill-level-permissions`](#review-skill-level-permissions).
    The hooks are the other half: the freshness guard's and the gates'
    refusals print exit codes and git vocabulary, and
    [fail-gracefully](../practices/fail-gracefully.md) says a non-technical
    reader gets a plain sentence instead — nothing translates them yet.
    Finding 6 of the 2026-09-14 review.
    **The first half is BUILT, same day**:
    [tools/precedent_owned_paths.py](../tools/precedent_owned_paths.py) lists
    owned and free paths against CODEOWNERS (GitHub's own matching rules,
    last match wins, an untranslatable pattern reported rather than
    skipped, a missing file reported as NO BOUNDARY rather than clean) and
    prints the sentence to say; the document-project `AGENTS.md` runs it
    before every pull request. Its wording is a first draft nobody has said
    to a real contributor. **The hook half is not built.** **Blocked on:**
    the pilot, for the wording of both halves — the hooks' refusals are
    translated by a session that has met a real contributor's confusion,
    not by one guessing at it. **Disposition:** wait (2026-09-14, the
    review)

## How It Closes

Not open until: the pilot, for the wording of both halves — the hooks' refusals are translated by a session that has met a real contributor's confusion, not by one guessing at it.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

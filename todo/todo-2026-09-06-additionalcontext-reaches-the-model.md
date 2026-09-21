---
slug:              todo-2026-09-06-additionalcontext-reaches-the-model
kind:              verify
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
noted:             2026-09-06
closed:            null
---
## What

- <a id="additionalcontext-reaches-the-model"></a>**Confirm `additionalContext` actually reaches the model, not just the
    transcript.** The new `PreToolUse` hook
    ([templates/harness/claude-code/hooks/precedent-paths.sh](../templates/harness/claude-code/hooks/precedent-paths.sh),
    [`spec/LOADER.md`](../spec/LOADER.md#the-pretooluse-hook-and-what-is-confirmed-versus-assumed))
    uses the documented `hookSpecificOutput.additionalContext` shape to
    surface matched practice Rules before an edit, but the public Claude
    Code hooks reference doesn't state *(as of 2026-09-03)* whether that
    field is delivered into the model's own context for that turn versus
    only shown to the human in a transcript. `check_pretooluse_hook_fires`
    in [tools/verify_harness.py](../tools/verify_harness.py) proves the
    wrapper produces the right shape; it cannot prove delivery. **Test
    plan**, recommended rather than run here (needs a live Claude Code
    session with this hook installed, which this session doesn't have):
    install the adapter in a real project, ask the session to edit a file
    matching a narrow-scoped on-demand practice's `applies_to` glob (e.g.
    a `tools/**` file for `code-cites-practice`), and check whether the
    session's own next reply cites that practice's Rule *unprompted* —
    something it could only do if the hook's context actually reached it,
    since the practice is on-demand and not otherwise in view. A clean
    negative result (the session never mentions the practice across
    several such edits) is itself the answer, and should be recorded here
    either way rather than left unconfirmed indefinitely.

    **NARROWED 2026-09-20, from the shipped CLI rather than from a live
    turn.** Claude Code 2.1.278's own hook documentation, read out of the
    installed binary, states it twice: *"`additionalContext` - Text injected
    into model context"* and *"Exit code 0 - JSON additionalContext shown to
    Claude"*. That is the vendor saying what the public reference left
    unstated on 2026-09-03, and it is enough to build on — the caution
    recorded here had, in the two weeks it stood, kept the field out of the
    one place it was most needed
    ([spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md](../spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md)
    cause 1). It is not the same as watching a model turn use it, so the item
    stays open.

    **The test plan no longer needs setting up.** Since 2026-09-20 every
    session rooted in a practice set is the experiment:
    `bootstrap/precedent-universal-catalogue.sh` hands the whole universal
    catalogue back as `additionalContext`, and a set's own tracked block
    carries none of it. So a session in a set that answers `Three Things`,
    `My options` or `Vocabulary` **from context, without opening
    `.precedent/SESSION_PRACTICES.md`**, has confirmed delivery; one that
    reaches for the file first, or does not know the command, has refuted it.
    Record whichever happens here rather than leaving this open indefinitely.
    **Disposition:** wait

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.

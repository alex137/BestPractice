---
slug:              todo-2026-09-13-universal-prose-does-not-reach-a-source-set
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
noted:             2026-09-13
closed:            null
---
## What

- <a id="universal-prose-does-not-reach-a-source-set"></a>**A check can now
    bind a repo that publishes practices; universal PROSE still cannot reach
    one.** `binds_publishers` (#261, 2026-09-12) closed half a wart this file
    had called "real and unaddressed": a universal check now runs in the
    source set whose catalogue it is about. The other half is untouched. A
    source set resolves no universal catalogue, so universal *guidance text* —
    a Rule a session needs to read, not a check it needs to pass — never
    arrives there at all.

    **What that costs, observably:** a source set keeps hand-copied
    restatements of universal rules it cannot resolve, and a hand copy is a
    second place for a rule to be wrong. This item's own sibling analysis
    above is the worked example — a re-declared same-slug copy that never
    agreed with universal's for the whole week it existed, which is worse than
    drift because there was never a synchronized state to fall out of.

    **Why it is not simply "do for prose what we did for checks".** A check is
    code that travels with the vendored engine and needs no text; prose is the
    text. Delivering it means either vendoring practice FILES into every set —
    shape 1, rejected when `binds_publishers` was chosen, precisely because it
    adds a second copy of rule text to every set — or a resolve path a source
    set does not currently have. Neither is a small change, and nobody has
    established that the pain is worth either.

    **First observed cost, same day, and it is a session's behaviour rather
    than a hand copy.** A session rooted in `themorgan/precedent-individual`
    spawned one into this repository and opened its seeded prompt *"You are
    rooted in alex137/BestPractice ... from a session rooted in
    themorgan/precedent-individual"* — the sending repository, with no session
    title, id or link. That is
    [seeded-prompt-names-its-origin](../practices/seeded-prompt-names-its-origin.md),
    landed the day before, and the spawning session could not have read it:
    the individual set's generated occasion index carries its own 14 entries
    and **none of universal's 94**, so `spawn-session` and
    `handoff-is-pasteable` were absent too. **Prose not reaching a source
    set is not only a duplication wart; it is universal rules silently not
    binding the sessions that do the most cross-repository work.**
    `spawn-session`'s own miss is fixed in this repository, so a session
    reading it here now reaches the header rule; a session rooted in a source
    set still will not.

    **Costed 2026-09-13**, on Morgan's approval of this session's
    recommendation (`assented`), in
    [spec/SOURCE_SET_PROSE_GAP.md](../spec/SOURCE_SET_PROSE_GAP.md): three
    shapes, measured, recommending the untracked
    `.precedent/SESSION_PRACTICES.md` route inverted — the whole delta is two
    already-written engine files added to the source vendoring list, one
    generalized constant, and a path expansion. **Nothing is approved to
    build.**

    **DONE 2026-09-13, reading half, upstream AND rolled out.** New sets get
    it from `precedent_bootstrap_source.py` automatically (PR #298); the four
    existing sets were handed to four woken sessions, one per set, each
    already rooted in that repository from an earlier wiring job the same
    day — `precedent-individual` (`session_01X7JgfabNF6mSvR7dpqVeAV`),
    `precedent-team-writing` (`session_01BLrNAxdBkyD4QtMrg4Z57Q`),
    `precedent-team-repo-maintenance` (`session_0185SF928m3c1dgtAj2uyFR8`),
    `precedent-team-working-style` (`session_019Tas6QAJHUXwXwUv7ksDYf`).
    Woken rather than spawned, per
    [spawn-session](../practices/session-text.md): a live session reuses the
    context it holds. **This session could not do it itself** —
    `git push --dry-run` returned 403 on all four, which is the quotable
    refusal the handoff rules ask for, and the merge authorization travelled
    with the seeded prompts.
    **Whether each landed is not established here**: a woken session has no
    return path, so confirm by looking at each set's own `main`, or by
    running `precedent_bootstrap_source.verify()` against it — the two rows
    it gained in PR #298 name exactly what is missing if the rollout did not
    finish.

    Shape 3 built and measured against the real `precedent-individual` set: universal cloned beside it, 106
    practices and 92 occasion entries in its untracked
    `.precedent/SESSION_PRACTICES.md`, its committed `AGENTS.md` unchanged.
    What the build took against what the brief predicted — including two
    things the brief missed outright — is the table in
    [spec/SOURCE_SET_PROSE_GAP.md](../spec/SOURCE_SET_PROSE_GAP.md). **The
    enforcement half is open as
    [`source-set-runs-no-universal-checks`](todo-2026-09-13-source-set-runs-no-universal-checks.md)**,
    and rolling the change out to the four sets is still to do.

    **The reading half was NOT finished on 2026-09-13, and the gap was in this
    repository rather than in any set.** The hook wrote
    `.precedent/SESSION_PRACTICES.md` correctly and **nothing told the session
    to read it**: the standing instruction's pointer at that file was
    conditional on `repo_is_public()`, which is one of the two reasons
    `build_views.sources_for_tracked_block()` defers a source, and a set defers
    universal for the other one. Every set is private, so the pointer was
    suppressed in all four. Fixed 2026-09-14 (`build_views.defers_any_source`),
    found by Morgan from the symptom — sessions open on a practice repo and
    most of the rules he wants are not loaded. **The measurement that missed it
    checked that the file was written, never that a session is told to read
    it.**

    **What the rollout now needs, and why it cannot be done from here.** Each
    set vendors the engine as tracked files, so it needs
    `python3 tools/precedent_refresh_sources.py --apply --commit` run from a
    BestPractice checkout and the regenerated `AGENTS.md` committed and pushed
    in that set. A session rooted in a set can get that checkout in seconds --
    `git clone --depth 1 --branch precedent-beta-v01
    https://github.com/alex137/BestPractice` is public and took 1 second on
    2026-09-14 (gotcha 33). A session rooted HERE cannot finish it: the git
    proxy answers 403 for `themorgan/*` ("not in this session's authorized
    repository set") and `add_repo` refuses the cross-owner add. **On
    2026-09-14 it could not even enumerate the live sessions to wake** --
    `list_sessions` was refused by the harness's own permission classifier,
    which is a permission refusal rather than a repository wall, so
    [spawn-session](../practices/session-text.md) sends it back to Morgan
    instead of spawning beside whatever is already running.
    **Disposition:** wait

    **THE LOADING HALF, 2026-09-20 — and it is a third half this item did not
    know it had.** The reading half was declared done on 2026-09-14 when the
    Standing Instruction's pointer at `.precedent/SESSION_PRACTICES.md`
    stopped being suppressed. **A pointer is not a load.** For the seven days
    after that, every set rendered the file correctly at session start and no
    session had a word of it in context before its first turn: Claude Code
    auto-loads instruction files and nothing else. Morgan reported the
    symptom in the plainest possible terms on 2026-09-20 — *"when I load
    precedent-individual as the seed root repo, it doesn't load
    bestpractice"* — and every mechanism this item tracks was working as
    designed while he said it.

    **Fixed for `precedent-individual` the same day**: the SessionStart hook
    emits the render as `hookSpecificOutput.additionalContext`, and the set
    gained the `CLAUDE.md` stub no source set had ever been given. The full
    account, including why a second `@import` was rejected and the four
    reasons this survived three rounds of fixes, is
    [spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md](../spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md).

    **What keeps this item open is the same thing that kept it open on
    2026-09-14: the other three sets.** `precedent-shared-repo-maintenance`,
    `precedent-shared-writing` and `precedent-shared-working-style` are
    outside the authorized repository set of the session that did this work,
    so they still render a file nobody loads. Neither change is
    set-specific — copy `bootstrap/precedent-universal-catalogue.sh` and
    `CLAUDE.md` across, and add the `CLAUDE.md` surface to each set's
    `tools/session_load_budgets.json`.
    **Disposition:** wait

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

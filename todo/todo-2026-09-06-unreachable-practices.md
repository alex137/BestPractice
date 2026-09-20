---
slug:              todo-2026-09-06-unreachable-practices
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a session that can resolve the private sources — see [`attach-private-sources`](todo-2026-09-06-attach-private-sources.md) for exactly what that takes. Until then the mechanism runs and correctly reports each private source as unresolved rather than silently empty."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            null
---
## What

- <a id="unreachable-practices"></a>**Populate `not_binding` for the practices in force here that do not
    bind this repo.** **The design decision is made and the mechanism is
    built (2026-09-06** —
    [decisions/2026-09-06-precedent-binds-itself.md](../decisions/2026-09-06-precedent-binds-itself.md)**).**
    `precedent.json` now takes `not_binding: [{slug, reason}]`, honored by
    `layered-practice-packs`' check: a reason is mandatory, a
    `severity: blocking` practice cannot be exempted, a stale entry is
    reported, and a malformed list fails loudly — all four asserted with
    negative controls in `check_not_binding_cannot_be_abused`.
    Shape 1 (a per-practice field) was rejected because whether a rule binds
    is a property of the pair, not the rule; shape 3 (multi-source generated
    views here) was rejected for this repo because it would publish private
    team practice text into a public [AGENTS.md](../AGENTS.md), and because its
    own "the misfits get retired or moved" framing would repeat the
    `deep-check` error of dropping a valid rule that simply does not apply
    here.
    **What is left is a measurement, not a decision:** of the 43 practices
    reachable by nothing, the audit's table says roughly five should be wired
    in as-is, four wired in and then fixed, and six declared not-binding —
    but that table predates Morgan's 2026-09-06 ruling that `deep-check` is
    NOT redundant, so it must be re-judged rather than copied. Writing
    exemptions for practices whose text and severity cannot be read would be
    asserting what cannot be verified.
    **The loading half is now closed too (2026-09-06).**
    [tools/precedent_session_practices.py](../tools/precedent_session_practices.py),
    run by the [session-start hook](../.claude/hooks/session-start.sh), resolves
    every declared source and writes the team/individual/repo-local block into
    `.precedent/SESSION_PRACTICES.md` — gitignored, so the private text
    reaches the session and cannot reach a commit. That is shape 3's safe
    form: the constraint was always on committing the text, never on loading
    it. It loads but does not enforce; materializing the other sources' check
    scripts waits on the exemptions below.
    **And `layered-practice-packs` now counts that channel (2026-09-06),**
    which it did not at first: it reads AGENTS.md and nothing else, so the
    practices loaded while the check still called them unreachable. Found by
    testing the claim rather than assuming it, when a second session was
    weighing publishing private practice text against leaving the team rules
    unloaded — on the belief that the already-built untracked channel would
    not satisfy this check. It is judged structurally (tool present, hook
    invokes it, repo public), never by looking for the untracked file, which
    is absent in CI and every fresh clone; three harness cases, with the
    negative controls, hold both halves.
    **Blocked on:** a session that can resolve the private sources — see
    [`attach-private-sources`](todo-2026-09-06-attach-private-sources.md) for exactly
    what that takes. Until then the mechanism runs and correctly reports each
    private source as unresolved rather than silently empty.

    **The engine half landed too, 2026-09-06 (was "Part A").**
    [tools/build_views.py](../tools/build_views.py) now renders the loader block
    from every source `precedent.json` declares, not the repo's own
    `practices/` alone — correct in any repo that declares more than one
    source and cannot merge them first. **That turned out to be this repo
    and no other:** a consuming repo materializes every source into one
    `practices/` tree before `build_views.py` sees it, so its block was
    already multi-source (verified against two of them after the rollout).
    It is deliberately **off here**, by the `visibility: public` guard
    below: this repo is world-readable, so rendering a private team set's
    Rule clauses into a tracked [AGENTS.md](../AGENTS.md) would publish them
    permanently, which is exactly what the decision record above rejected.
    `not_binding` is the mechanism for this repo; the multi-source block is
    the mechanism for every repo that vendors it. They are not competing
    answers to one question.

    Two guards came with it. A repo declaring `visibility: public` renders
    **no private-level source** — team or individual — into its tracked
    block; publishing that block would publish the private set, the same
    disclosure [tools/precedent_resolve.py](../tools/precedent_resolve.py)
    already refuses to allow by config. And a declared source that cannot be
    reached makes the block **NOT VERIFIABLE** rather than stale: a team
    source is a sibling clone no bare continuous-integration checkout has, so
    calling that "drift" would fail every run on evidence the environment
    could not have.

    **What remains is the measurement above, and it is far smaller than this
    item first assumed.** 11 practices carry check scripts; of the 15 run
    against this tree, 5 pass, 4 find real problems worth fixing, and 6
    report things this repo cannot act on because the practice is about a
    different kind of repository. Only if a pattern shows up across them —
    several meaning the same thing, such as "a repo one person authors
    alone" — is new vocabulary worth building, and by then its values will be
    known rather than guessed.

## How It Closes

Not open until: a session that can resolve the private sources — see [`attach-private-sources`](todo-2026-09-06-attach-private-sources.md) for exactly what that takes. Until then the mechanism runs and correctly reports each private source as unresolved rather than silently empty.

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.

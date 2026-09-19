---
slug:              todo-2026-09-12-universal-adapters-undeclared
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          ""Approved - declare the eight adapters" -- Morgan approved declaring the harness adapters (landed as five, after two were found to already be owned by the individual source)."
decision_strength: decided
waiting_on:        null
noted:             2026-09-12
closed:            2026-09-14
---
## What

- <a id="universal-adapters-undeclared"></a>~~**Decide whether THIS repository
    declares its own harness adapters.**~~ **Done (2026-09-14).** Since 2026-09-12 a practice source
    can declare its `bootstrap/*.sh` in its own `precedent.json` and have
    [tools/precedent_materialize.py](../tools/precedent_materialize.py) install
    them into every consuming repo on each sync — see
    [spec/SOURCES.md](../spec/SOURCES.md)'s "Harness adapters travel with the
    source". The universal source, this repository, declares none: the six
    templates under
    [templates/harness/claude-code/hooks/](../templates/harness/claude-code/hooks/)
    are still installed by hand. Switching them on would start writing into
    every consuming repo's `.claude/hooks/` — including repos that installed
    an older copy deliberately, and every one of them needs its
    `.claude/settings.json` wiring to match, which does not travel and cannot.
    The mechanism landing is not the same decision as pointing it at every
    install.

    **Measured 2026-09-14: the reporting half of this is already built, and
    the residue is narrower than it reads.** A proposal reached this repo for
    an `adapters-are-wired` check — the complement to
    `declared-hooks-exist`, reporting an adapter that sits on disk wired by
    no `settings.json`. That check exists:
    `hooks-on-disk-are-reachable` in
    [tools/precedent_check.py](../tools/precedent_check.py) sweeps
    `.claude/hooks/` (and any directory a `settings*.json` names) for files
    nothing that could run them names, and its own docstring cites the same
    consuming-repo incident the proposal cites. **What it does not have is a
    way to DECLINE one.** A repo that left an adapter unwired on purpose —
    the consuming repo whose `AGENTS.md` records declining
    `freshness-guard.sh` because its own bootstrap already fast-forwards —
    has no way to say so that the check reads, because prose is deliberately
    not searched. So it reports a correct decision as an orphan, permanently,
    and the only way to clear it is to wire a hook the repo does not want.
    The open work is a declared decline carrying a reason, satisfied by the
    reason rather than by the wiring — not a new check.

    **Built 2026-09-14.** `precedent.json` takes a `declined_adapters` list
    of `{path, reason}`, and `hooks-on-disk-are-reachable` reads it: a hook
    declined with a reason is satisfied by the reason. A decline with no
    reason, a decline naming a file that is not there, and a decline sitting
    beside a hook something actually calls are each reported instead — four
    planted cases in
    [tools/verify_harness.py](../tools/verify_harness.py). Documented in
    [spec/SOURCES.md](../spec/SOURCES.md)'s "Harness adapters travel with the
    source". **So the thing this item was waiting on exists**, and what is
    left is the decision below and nothing else.

    **CLOSED 2026-09-14.** The item's stated condition was a deliberate call
    about a behavioural change to every consuming repo, and Morgan made it:
    *"Approved - declare the eight adapters"* (`decided` — he chose it from
    options laid out for him). `precedent.json` now declares **five**, not
    eight, and the two subtractions are both worth reading.

    `individual-source-bootstrap.sh.template` is not an adapter: it carries
    variables substituted at install time, so copying it verbatim would
    install a hook with placeholders where its values belong. The number in
    this item was wrong, counted off `ls`.

    `commit-identity.sh` and `freshness-guard.sh` are real adapters and are
    deliberately left undeclared: the individual source already declares the
    same two destinations, and `precedent_materialize.py` REFUSES a
    destination collision outright. Declaring them here would have stopped
    the sync of every repo holding both sources. Found by declaring all
    seven and running the deep check, which failed the vendored-consumer
    case against the real four-source pipeline — the only place this was
    visible, since nothing in this repository alone collides.

    The decline mechanism landed first, on purpose — it is what makes this
    safe, since a repo that does not want one of the seven can now say so
    with a reason instead of carrying a permanent violation.

## How It Closes

Already closed 2026-09-14 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.

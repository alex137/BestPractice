---
slug:              todo-2026-09-06-headline-duplicate-retired
kind:              analysis
domain:            content
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-06
closed:            2026-09-06
---
## What

- <a id="headline-duplicate-retired"></a>**Done 2026-09-06 — the duplicate was found and retired.** A session
    holding all four repositories searched by purpose and by mechanism
    across every practice body, frontmatter, check script and test:
    exactly one duplicate, `header-caps` in `precedent-team-repo-maintenance`,
    with its own check and a two-direction test. `precedent-individual`
    had no capitalization practice at all. It was retired there per
    [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md), its check and
    test removed, on branch `claude/practice-repos-audit-migration-2l9jbz`
    (no pull request opened). **Three clauses the universal practice does
    not carry**, recorded here because retiring the old rule dropped them
    rather than moving them: (a) *heading-level consistency* — siblings at
    the same rank sharing a heading level, which is an outline rule, not a
    capitalization one, and is now unenforced anywhere; (b) *scope* —
    `header-caps` applied to `**/*.md` while
    [practices/headline-capitalization.md](../practices/headline-capitalization.md)
    deliberately covers `documentation/**/*.md` only, so practice files,
    specs and READMEs lost their same-rank check; (c) the *escape hatch*
    letting a repo document a different scheme inline, which the universal
    rule deliberately does not offer. **All three are now settled
    (2026-09-06).** (a) is rebuilt as its own universal practice,
    [practices/heading-outline.md](../practices/heading-outline.md), bound to
    `**/*.md` with a mechanical check in
    [tools/doc_lint.py](../tools/doc_lint.py) and a gate in
    [tools/precedent_check.py](../tools/precedent_check.py) — wider than the
    team rule it restores, since a broken outline is not a matter of
    audience. (b) is not a loss but the intended design: Morgan confirmed
    that capitalization governs outward-facing content only and that
    internal working files are deliberately out of scope, and
    [practices/headline-capitalization.md](../practices/headline-capitalization.md)
    now says so in its own first paragraph rather than leaving it to be
    inferred. (c) stands as the deliberate tightening it was read as.

## How It Closes

Already closed 2026-09-06 -- see the item's own text above for what finished it.

## Notes

noted date is a floor, not exact -- this item predates anchor tracking and its true creation date is unknown. 2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.

---
slug:              todo-2026-09-14-generated-views-are-owned-paths
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"build what's needed to implement the spec\" -- Morgan approved the write-up wholesale; the session's own pick (unowning MAP.md/GLOSSARY.md in a document project) was applied under that approval."
decision_strength: assented
waiting_on:        null
noted:             2026-09-14
closed:            2026-09-14
---
## What

- <a id="generated-views-are-owned-paths"></a>**In a document project,
    `MAP.md` is an owned path and every add-a-document pull request touches
    it — so every one waits for the maintainer.**
    [templates/document-project/.github/CODEOWNERS](../templates/document-project/.github/CODEOWNERS)
    owns `/MAP.md` and `/GLOSSARY.md` as generated views;
    [orientation-map](../practices/orientation-map.md) says a thread that adds
    a document adds its row. Found by the 2026-09-14 review in
    [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md), finding 2. Two
    ways out, and they are different projects: unown the two files, on the
    ground that in a document project they index content and are content;
    or regenerate them in continuous integration after merge so no
    contributor commit touches them. The first is one line and gives the
    contributor a file they can break; the second keeps the boundary and
    needs a committing workflow, which
    [ci-commits-carry-identity](../practices/ci-commits-carry-identity.md)
    already constrains. The session's pick is the first: a wrong row in an
    index is a content mistake, and content is theirs. **Blocked on:**
    Morgan choosing — it changes what a contributor can touch, which is the
    line he drew.
    **CLOSED 2026-09-14, the same day** — unowned, on the session's pick,
    under Morgan's "build what's needed to implement the spec" (`strength:
    assented`: he approved the write-up wholesale, not this choice by name).
    [templates/document-project/precedent.json](../templates/document-project/precedent.json)'s
    `owned_paths` no longer lists the two files, its `_boundary_comment`
    says why, and the spec's layer-2 section records it.
    **Disposition:** wait (2026-09-14; done, kept for the record)

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

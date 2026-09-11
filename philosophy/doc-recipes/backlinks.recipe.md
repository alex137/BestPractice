<!-- Last updated: 2026-09-11 (Buenos Aires) by the session that made the philosophy cross-references bidirectional; written here, not copied. -->

# Recipe: Bidirectional Cross-References

**Experimental, on branch `philosophy-bidirectional-slugs`, at Morgan's
request on 2026-09-11 — explicitly not to be merged yet.** He liked that
the AI-governance items each carry a slug other documents cite, and asked
that every item in the core documents get one, with the citations running
both ways.

- **Every item in a core document carries a permanent slug**, written as
  `<a id="slug"></a>`. In the numbered essays it sits on its own line
  above the item; in [../CORE_PILLARS.md](../CORE_PILLARS.md) and
  [../HUMANS_AT_OUR_BEST.md](../HUMANS_AT_OUR_BEST.md), whose items are
  list entries, it opens the bullet. The slug is the citation handle, so
  **it never changes** once written — retitle an item freely, renumber the
  list freely, leave the slug alone.
- **Core documents are the seven the index calls essays and lists**, named
  in `DOCS` in
  [../../tools/philosophy_backlinks.py](../../tools/philosophy_backlinks.py).
  [../ASSORTED_NOTES.md](../ASSORTED_NOTES.md) is out: it is dated
  brainstorm prose, not a list of items, and slugging it would mean
  inventing item boundaries that aren't there.
- **The reverse edge is generated, never typed.** Where an item cites
  another, the cited item carries a `*Cited by: ...*` line written by
  `python3 tools/philosophy_backlinks.py`. Run it after changing any
  citation and commit what it writes; `--check` exits non-zero on drift.
  Hand-editing one of those lines loses on the next run
  ([generated-edit-goes-upstream](../../practices/generated-edit-goes-upstream.md)
  — the input is the citation in the citing item's own prose).
- **Only item-to-item citations count.** A link in a document's opening
  italics, its "See Also" footer, or a section that isn't an item — the
  "Not Yet Ready for This List" section in
  [../RULES_NOW_TESTING.md](../RULES_NOW_TESTING.md) — is a reference
  between documents, and gets no reverse edge. There is nowhere on the
  other end for one to attach.
- **An item with no `*Cited by:*` line is uncited, and that is allowed.**
  Do not manufacture a citation to fill the gap
  ([no-invented-specifics](../../practices/no-invented-specifics.md)). The
  honest empty slots are half of what this experiment is for: they show
  which ideas nothing in the corpus leans on.

<!-- Last updated: 2026-09-11 (Buenos Aires) by the session that made the philosophy cross-references bidirectional; written here, not copied. -->

# Recipe: Cross-References That Run Both Ways

**Experimental, on branch `philosophy-bidirectional-slugs`, at Morgan's
request on 2026-09-11 — explicitly not to be merged yet.** He liked that
the AI-governance items each carry a slug other documents cite, and asked
that every item in the core documents get one, with the citations running
both ways.

- **Every item in a core document carries a permanent slug**, written as
  `<a id="slug"></a>`. In the numbered essays it sits on its own line above
  the item; in [../CORE_PILLARS.md](../CORE_PILLARS.md) and
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
- **A citation is reciprocated in the cited item's own prose, in the same
  shape as the forward one** — a clause or a parenthetical in the
  document's voice, saying what the other end *is* to this one: the theory
  behind it, the payoff from it, the version being tried by hand. Never a
  bare list of who links here.
- **The back-reference is written by hand. Nothing generates it.**
  [../../tools/philosophy_backlinks.py](../../tools/philosophy_backlinks.py)
  only reports citations that run one way, and names the item whose prose
  needs the return sentence. Run it after changing any citation.
- **Why it is not generated**, since the obvious build would be: the first
  version of this did generate it, as a `*Cited by: ...*` line under each
  cited item. Morgan read that on 2026-09-11 and said it made the
  documents confusing — machine output sitting under prose reads as
  exactly that, and a reader hits it before finishing the idea. The
  citation graph is checkable; the sentence that carries it is writing.
- **Watch for the tell that the hand-written version has failed**: the same
  clause, reworded barely, appearing under several items. Three entries in
  [../HUMANS_AT_OUR_BEST.md](../HUMANS_AT_OUR_BEST.md) came back as "one of
  the three `hire-for-drive` hires for" three times before being rewritten.
  If a return reference says nothing but *this links here*, it is the
  generated line again with extra steps.
- **An item nothing cites gets no sentence, and that is allowed.** Do not
  manufacture a citation to fill the gap
  ([no-invented-specifics](../../practices/no-invented-specifics.md)). The
  honest empty slots show which ideas nothing in the corpus leans on.

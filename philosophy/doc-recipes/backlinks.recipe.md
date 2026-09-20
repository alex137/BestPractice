<!-- Last updated: 2026-09-20 (Buenos Aires) by the session that dropped the empty-slot exception once every item in HUMANS_AT_OUR_BEST.md was given a citation; written here, not copied. -->

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
- **A citation never targets its own item's slug.** An item can name the
  concept it's already discussing without linking the word to itself — the
  link only earns its place pointing somewhere else in the document. Caught
  2026-09-16 in [../THE_TALMUDIC_METHOD.md](../THE_TALMUDIC_METHOD.md): an
  item linked its own defining word to a *different* item's slug, which
  read as self-referential because the word and the item were the same
  concept, not because the anchor was technically wrong.
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
  needs the return sentence. Run it after changing any citation;
  [../../tools/verify_harness.py](../../tools/verify_harness.py) runs it too,
  so the deep check fails on a one-way citation rather than leaving this
  advisory
  ([checkable-gets-checked](../../practices/checkable-gets-checked.md)).
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
- **The reference rides an existing sentence; it does not get its own.**
  Attach it where the item already says the thing — *"it sounds technical
  but is `politics`"*, *"the Ghost can't climb a ladder or smell burnt
  wiring (`sense-of-smell`)"* — rather than appending a clause that restates
  the relationship. The first round did the latter and grew
  [../COMPANY_BUILDING_RULES.md](../COMPANY_BUILDING_RULES.md) by a quarter
  for no new argument, which Morgan read as the sections having become too
  long. **A connection that cannot be carried by a sentence already there
  usually needs a longer look at whether the two items are really related.**
- **Every item carries a citation into another core document.** This
  reverses the original rule here, which let an item nothing cites get no
  sentence rather than have one manufactured to fill the gap. That held
  until 2026-09-20, when six items in
  [../HUMANS_AT_OUR_BEST.md](../HUMANS_AT_OUR_BEST.md) — Asking hard
  questions, Verification, Managing the dirtiness of real life, Why,
  Weirdness, Understanding problems — were each given one on request, at
  which point an unfilled slot became the exception to argue for rather
  than the default. A citation still has to be a real connection an essay
  elsewhere actually makes, never invented to satisfy the letter of this
  rule ([no-invented-specifics](../../practices/no-invented-specifics.md))
  — an item with no honest match yet is a sign the item, or the corpus,
  needs another look, not license to leave the slot empty.

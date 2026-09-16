<!-- Last updated: 2026-09-16 by the session that wrote this page; written here, not copied. -->

# The Talmudic Method

*An observation, not a claim of intent: nobody built this system by
consulting a yeshiva. But line up what it actually insists on — argue
before you conclude, work paired before you work alone, keep the dissent
instead of smoothing it away, cite precedent by name — and the resemblance
to how the Talmud gets studied is hard to unsee. Worth naming, if only so
the resemblance stops being a coincidence and starts being a design lens.*

1. **Chavruta: nothing gets studied alone.** Talmudic learning happens in
   pairs, not solo reading — a text isn't understood until a second voice
   has pushed on it. [`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate)
   enforces the same shape here: not a person handing a problem to the
   model and walking away, and not the model executing unwatched, but two
   parties in the room while the thinking happens.

2. **Argument is the method, not a detour to the answer.** A study partner
   who only agrees isn't a chavruta, he's an oracle, and the exchange
   doesn't count until it's been genuinely tested.
   [`arguing-with-the-model`](OUR_PHILOSOPHY.md#arguing-with-the-model)
   names exactly that failure mode for a model that just agrees, and
   [`brainstorm-holds-commits`](../practices/brainstorm-holds-commits.md)
   enforces the same discipline structurally — the repository stays
   untouched until the argument has actually run.

3. **Dissent gets kept, not erased by the ruling.** The Talmud prints the
   losing opinion next to the winning one rather than deleting whoever
   lost the argument. [`decision-strength`](../practices/decision-strength.md)'s
   `decided` vs. `assented` split, and
   [`open-item-disposition`](../practices/open-item-disposition.md)'s
   refusal to flatten an unresolved question into a settled one, do the
   same job in a repo: how contested something actually was survives the
   ruling.

4. **A ruling stands or falls on its reasoning, not just its verdict.** A
   Talmudic argument almost never states a bare conclusion — it carries the
   exchange that produced it, so a later generation can test the reasoning
   against a new case rather than merely cite the outcome.
   [`decisions-carry-their-situation`](OUR_PHILOSOPHY.md#decisions-carry-their-situation)
   makes the same bet: a rule kept as "always do X because Y" stays
   arguable against Y forever, one kept as bare "always do X" has nothing
   left to check.

5. **Precedent binds forward — a citation is a live dependency, not a
   footnote.** Talmudic rulings build on named prior rulings generation
   after generation; citing a sage invokes an argument still in force.
   This repo's own precedent-command mechanism and
   [`index-remembers-past`](../practices/index-remembers-past.md) work the
   same way — a later decision cites the earlier one it builds on, and a
   document that supersedes another keeps the lineage rather than quietly
   overwriting it.

6. **Oral becomes text so the argument outlives the person who made it.**
   The Mishnah and Gemara exist because teaching held only in memory dies
   with the generation that holds it.
   [`repo-is-memory`](../practices/repo-is-memory.md) is the same wager
   about a chat thread: knowledge that lives only in conversation is
   already lost, so it has to land in committed text before the session
   that produced it ends.

7. **The text stays open on purpose.** Hillel and Shammai's schools
   disagreed on most everything, and tradition holds both were right —
   their opposing rulings are recorded side by side rather than one being
   erased once the other won out.
   [Rules Now Testing](RULES_NOW_TESTING.md) and
   [`park-it`](../practices/park-it.md)'s `parked` disposition do the same:
   a rule can be tried, argued over, and left genuinely unsettled instead
   of declared closed just to make a page look finished.

8. **The page itself is built as layered commentary, not one voice.** A
   Talmud page prints the central text ringed by later commentaries that
   argue with it and with each other — reading one passage means reading
   several generations of dispute at once. This directory's
   [backlink recipe](doc-recipes/backlinks.recipe.md) is a small version of
   the same structure: an item cites what it depends on, and the cited
   item answers back in its own prose, so the argument runs in the margins
   of the text itself.

## See Also

- [Our Philosophy](OUR_PHILOSOPHY.md) — the underlying theoretical
  ideas everything else here assumes, named and explained on their own
  terms.
- [Reasons Why](REASONS_WHY.md) — the less obvious benefits those
  ideas produce in practice.
- [Company Building Rules](COMPANY_BUILDING_RULES.md) — the standalone
  essay on rules for building a company around AI.

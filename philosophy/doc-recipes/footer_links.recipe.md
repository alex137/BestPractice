<!-- Last updated: 2026-09-20 (Buenos Aires) by the session that completed THE_WORKING_LOOP.md's footer, fixed a repo-wide link-text mismatch, and wrote the notes-page exception and the link-text rule down alongside those fixes; written here, not copied. -->

# Recipe: See Also Footers and the README List

- **Every essay in this directory carries every other essay in its own
  "## See Also" footer.** It is the mirror of [README.md](../README.md)'s
  "What's Here" list, which is why the two are kept in sync with each
  other. [README.md](../README.md) itself carries no such footer — its own
  recipe ([README.recipe.md](README.recipe.md)) already makes the "What's
  Here" list the whole page.
- **A dated, loosely-grouped notes page is exempt from the mutual footer
  web — today, [ASSORTED_NOTES.md](../ASSORTED_NOTES.md).** No essay is
  required to carry it in its own "See Also" (none currently do), though
  the notes page may still link out to whichever essays it discusses, and
  it still gets its own line in README's "What's Here" — that list is a
  complete file index, not a citation network, and
  [README.recipe.md](README.recipe.md) already requires every file there
  without exception. A page earns this exemption by being an append-only
  brainstorm rather than a finished, single-argument essay; anything else
  added to this directory is in the mutual web by default.
- **Adding a new essay to `philosophy/` is a same-commit edit to two
  places, not one:** [README.md](../README.md)'s "What's Here" list
  (already required by [README.recipe.md](README.recipe.md), and checked
  by `check_philosophy_readme_lists_every_file()` in
  [../../tools/verify_harness.py](../../tools/verify_harness.py)), and the
  "See Also" footer of every other essay already in the directory — plus a
  new footer of the new essay's own, naming every one of them back.
- **This is this directory's default, unless explicitly told otherwise.**
  A page can be left out of the cross-linking on purpose — a draft not yet
  ready to be found, say — but that is a call made out loud for that page,
  not a silent omission.
- **Link text is the name README's "What's Here" list already gives the
  target, exactly, in both places — never a paraphrase, and never the raw
  `.md` filename.** README's name is not always the literal `# Heading`:
  [COMPANY_BUILDING_RULES.md](../COMPANY_BUILDING_RULES.md)'s heading is
  "Rules for Building a Company Around AI," but every reference to it
  anywhere in this directory, README included, calls it "Company Building
  Rules" — that shorter form is the deliberate, established name, not a
  drift to fix. Copy README's entry; don't reconstruct a plausible-sounding
  name from the target's own heading or from memory. Title case throughout,
  matching README's own capitalization of it.
- **Caught 2026-09-17:** [THE_TALMUDIC_METHOD.md](../THE_TALMUDIC_METHOD.md)
  was added with its own correct footer, but no other page's footer was
  updated to link back to it — eight pages went quietly out of sync with
  the page that had just landed next to them.
- **Caught 2026-09-20:** two drifts at once. First, every other essay's
  footer called [THE_WORKING_LOOP.md](../THE_WORKING_LOOP.md) "Our Working
  Loop" — a paraphrase, not its actual title, "The Working Loop," which
  only [README.md](../README.md) had right; eight files corrected in one
  pass. Second, THE_WORKING_LOOP.md's own footer — written the day it was
  split out of OUR_PHILOSOPHY.md — carried only one of the other seven
  essays; the split commit never gave it the full treatment this recipe
  already asked for.
- **Caught 2026-09-20, second pass:** this recipe's own first cut of the
  link-text rule said to copy the target's `# Heading` exactly — checked
  against every essay rather than just the one just fixed, that would have
  flagged all ten existing references to
  [COMPANY_BUILDING_RULES.md](../COMPANY_BUILDING_RULES.md) as wrong,
  since every one of them (README included) calls it "Company Building
  Rules" and none use its actual heading. The rule was reworded to point
  at README's established name instead of the literal heading.

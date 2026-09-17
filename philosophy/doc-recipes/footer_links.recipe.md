<!-- Last updated: 2026-09-17 (Buenos Aires) by the session that filled the missing Talmudic Method links across this directory's See Also footers and wrote this convention down alongside the fix; written here, not copied. -->

# Recipe: See Also Footers and the README List

- **Every essay in this directory carries every other essay in its own
  "## See Also" footer.** It is the mirror of [README.md](../README.md)'s
  "What's Here" list, which is why the two are kept in sync with each
  other. [README.md](../README.md) itself carries no such footer — its own
  recipe ([README.recipe.md](README.recipe.md)) already makes the "What's
  Here" list the whole page.
- **Adding a new page to `philosophy/` is a same-commit edit to two
  places, not one:** [README.md](../README.md)'s "What's Here" list
  (already required by [README.recipe.md](README.recipe.md), and checked
  by `check_philosophy_readme_lists_every_file()` in
  [../../tools/verify_harness.py](../../tools/verify_harness.py)), and the
  "See Also" footer of every other page already in the directory — plus a
  new footer of the new page's own, naming every one of them back.
- **This is this directory's default, unless explicitly told otherwise.**
  A page can be left out of the cross-linking on purpose — a draft not yet
  ready to be found, say — but that is a call made out loud for that page,
  not a silent omission.
- **Caught 2026-09-17:** [THE_TALMUDIC_METHOD.md](../THE_TALMUDIC_METHOD.md)
  was added with its own correct footer, but no other page's footer was
  updated to link back to it — eight pages went quietly out of sync with
  the page that had just landed next to them.

<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying that content into philosophy/; source: adapted from the project's own prior notes repository, doc-recipes/README.recipe.md, version 1 -- that repository was made private and is being deleted. -->

# Recipe: philosophy/README.md

- **The page is one sentence and a list, and nothing else.** Morgan asked
  for exactly that on 2026-09-09, replacing a page that had grown four
  sections of standing guidance. Anything that wants to be said about how
  these documents are maintained belongs in this recipe, not on the page.
- In "What's Here", give **every file and directory in `philosophy/` its
  own bullet** — never group two under one bullet, and never leave one
  out. The list is the page's whole content, so a file added, renamed or
  removed here is a same-commit edit to this list.
  `check_philosophy_readme_lists_every_file()` in
  [../../tools/verify_harness.py](../../tools/verify_harness.py) fails the
  deep check when the two disagree.
- **No "See Also" footer.** The list already is one.
- These essays have no upstream. The notebook they were written in was
  retired on 2026-09-07 and this directory is the only copy, which has two
  consequences: **edit these files directly** — there is no original to
  also update — and **never vendor this directory anywhere**. A consuming
  repo gets [../../practices/](../../practices/); carrying the essays too
  would make a second copy of documents that exist to have exactly one.
  This used to be a section on the page itself, and moved here when the
  page was cut back.
- The provenance line at the top of each document — origin file and the
  version it was taken at — is a historical record, not a sync pointer.
  Never delete it, and never rewrite it to make text look native to this
  repository when it was not.
- Nothing in `philosophy/` binds work outside it. That is stated on every
  essay's own terms and enforced by
  [../../local/practices/philosophy-is-not-repo-policy.md](../../local/practices/philosophy-is-not-repo-policy.md),
  so the page no longer says it.

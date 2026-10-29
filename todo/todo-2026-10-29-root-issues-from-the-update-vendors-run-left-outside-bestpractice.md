---
slug:              todo-2026-10-29-root-issues-from-the-update-vendors-run-left-outside-bestpractice
kind:              manual
domain:            engine
severity:          default
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the two voice repositories could not be attached to the session that fixed the rest (add_repo was refused on 2026-10-29), and the set tests live in the practice sets' own repositories"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-29
closed:            null
---
## What

Left from the Root issues of the 2026-10-28 Update Vendors run across seven
repositories. Items 1 to 4 of that list, and the engine half of item 5,
were fixed in BestPractice on 2026-10-29: Update All moves a reused clone
off its pin, the update clones an offered set it said yes to, a declared set
is found beside the individual set, the archive check reads waiting
notifications first, and the engine now writes the person's declared name
into their own maintainers entry. Three things remain, each outside this
repository:

1. **The two voice repositories still carry the hand-set name.** Their
   `precedent.json` maintainers entry reads `{"github": "themorgan", "name":
   "Morgan"}`. The engine now rewrites it to the declared name ("Morgan F")
   on the next Update Vendors, and keeps a binds_everyone approval that
   signs "Morgan" valid, since the ladder check matches a name's first
   word. Nothing to do by hand: run Update Vendors in both and check the
   entry changed.
2. **A copied-in set's own tests cannot run from the copy.** Each test in a
   set's `tools/checks/tests/` puts the set's own `tools/` on the import
   path, where the set keeps its vendored engine. A copy at
   `process/<set>/` brings `tools/checks/` but never that engine, so
   `test_others_did.sh` and its neighbours stop at `ModuleNotFoundError:
   precedent_identity` there. Nothing runs them in a copy; the set's own
   repository runs them on every engine refresh (`set_tests_step`). Fix in
   each set: put the engine on the path from the first folder above the test
   whose `tools/` holds `precedent_identity.py`, so the same file runs in the
   set and in a copy. Leaving the tests out of the copy instead would need
   checkin's mirror to prune files it no longer copies, which it does not do
   today for a path both sides filter out.
3. **One voice repository's session file was over its ceiling** (414
   tokens against 400, a local-only file, already so before that run). #1374 raises the
   ceiling by a copied set's share on copy-in. Not measured since, because
   the repository could not be attached. Run `python3 tools/precedent_check.py
   --only session-load-budget` there after Update Vendors; if it is still
   over, `python3 tools/precedent_session_practices.py` breaks the file down
   by source.

## Done when

Both voice repositories' entries carry the declared name through the
engine; each set's tests run from a copy as well as in the set; that
repository's session-load check passes or its overage is traced to its
source and fixed there.

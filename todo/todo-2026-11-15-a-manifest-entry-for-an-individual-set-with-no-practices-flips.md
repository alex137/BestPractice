---
slug:              todo-2026-11-15-a-manifest-entry-for-an-individual-set-with-no-practices-flips
kind:              decision
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan's choice between the two fixes below; it changes what a private repository's tracked manifest records about a person's individual set (his decision of 2026-10-19)"
noted:             2026-11-15
closed:            null
---
## What

- [ ] **A consumer's tracked `MANIFEST.json` gains and loses its individual-set entry depending on which session lands.** Found 2026-11-15 in a private consumer whose own `precedent.json` declares no individual set. A landing run from a session that had a person's individual set cloned wrote that set into the manifest's `sources` list, with its commit and its absolute path, although the set contributes no practice there: the manifest held the same number of practices before and after. From then on [tools/precedent_sync_views.py](../tools/precedent_sync_views.py) `--check` fails in every session that lacks the set, with "MANIFEST.json differs from what a fresh sync writes", and the next landing from such a session removes the entry again. Each landing makes a resync commit that undoes the last one.

  The engine already has a rule for this situation and it does not fire. `individual_not_verifiable` in [tools/build_views.py](../tools/build_views.py) returns its reason only when the committed views carry at least one practice from an individual source. Here the count is zero, so the check reads the difference as drift.

  Reproduce, in a consumer with no individual set declared: run a view sync in a session that has an individual set cloned beside it and commit the manifest; then, in a session without that clone, run the view check.

  Two fixes, and they are different decisions:

  1. **Do not record an individual source that contributes nothing.** A sync leaves it out of `sources` when no resolved practice comes from it. The manifest then reads the same from every session. This is my pick: an entry with no practices is nobody's saved copy.
  2. **Treat a recorded individual source as "cannot verify here"** whenever it does not resolve, practices or none. The check stops failing, and the entry still flips at each landing.

## How It Closes

`status` becomes `done` when one fix is chosen and on `main` with a harness test that runs the reproduction above, and a consumer's manifest reads the same after two landings from sessions with and without an individual set.

## Notes

- The session that found it changed no engine code for this. The choice touches the 2026-10-19 decision that a private repository's manifest holds the individual set as its owner's saved copy.
- 2026-11-19: it happened again, harder. On 2026-11-18 a second consumer had seven worker sessions in turn refused at push over the same entry, and its main session regenerated the manifest at every merge. Reproduced on a copy of that consumer: the view check passes with the person's set reachable and fails without.
- 2026-11-19: fix 1 is built, not merged, on the branch [claude/bestpractice-upstream-faults-6w4gkf](https://github.com/alex137/BestPractice/tree/claude/bestpractice-upstream-faults-6w4gkf), with a harness test (`check_manifest_is_the_same_with_and_without_an_individual_set`). A sync records an individual set only when a practice of it is in the tree, and the comparison ignores a bare entry an older engine wrote, so no consumer has to regenerate first. On the copy, both kinds of session then pass and write the same file. A set with a practice in the tree keeps its entry and its owner record, so the saved copy of 2026-10-19 is as it was. It still waits on Morgan's choice (needs: decision -- Morgan).


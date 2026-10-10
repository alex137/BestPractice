---
slug:              todo-2026-10-10-one-commit-date-check
kind:              decision
domain:            engine
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan's yes to one copy of each commit-identity check, shipped by the engine"
noted:             2026-10-10
closed:            null
---
## What

The commit-date check ([check_buenos_aires_dates.py](../tools/checks/check_buenos_aires_dates.py)) has two copies that
drift apart. One is the source in Morgan's individual set, which every
consuming repository materializes and runs. The other is BestPractice's
port in [tools/checks/](../tools/checks/). On 2026-10-10, three gaps between
them turned up in one afternoon:

- the individual set's copy did not skip a bot-authored fallback commit;
- neither honored `PRECEDENT_CHECK_RANGE`, which the author check's
  "verbatim" twin had read since 2026-10-06;
- neither skipped a commit GitHub itself made, so a consumer's merge gate
  refused every GitHub-button merge.

The author check ([check_commit_author.py](../tools/checks/check_commit_author.py)) has the same shape and the same
risk.

## Recommendation

**One copy of each check, shipped by the engine.** Neither script holds
anything personal any more: the zone comes from the declared identity, and
the grandfathered commits come from each repository's own `identity.json`
or `precedent.json`. So the engine ships the two scripts like any other
engine file, and every repository runs the same copy. The individual set
keeps the practice text, and its `checked_by` names the engine's copy. A
generic name, check_commit_dates.py, fits better than a city once it is
the engine's: Buenos Aires is Morgan's zone, not the check's.

**What to settle in the work.** Today [precedent_materialize.py](../tools/precedent_materialize.py) writes a
source's checks into `tools/checks/`, which is also where the engine copy
would go. Work out which writer owns the file, so the two never overwrite
each other, before moving anything.

A cheaper fallback is a check that fails when the shared parts of the two
copies differ. It keeps both copies and only catches drift after the fact.

## Notes

- 2026-10-10: raised after the VoiceDef merge-gate fix
  (BestPractice branch `2026-10-10-rerun-and-github-merge-dates-y1ktn`,
  precedent-individual branch `2026-10-10-github-merge-dates-y1ktn`).
  Morgan asked whether there should be one shared date check.

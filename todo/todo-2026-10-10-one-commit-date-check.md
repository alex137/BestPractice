---
slug:              todo-2026-10-10-one-commit-date-check
kind:              decision
domain:            engine
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "yes to both, move the sets and build the shared check"
decision_strength: decided
waiting_on:        null
noted:             2026-10-10
closed:            2026-10-10
---
## What

The commit-date check ([check_buenos_aires_dates.py](../tools/check_commit_dates.py), now tools/check_commit_dates.py,) has two copies that
drift apart. One is the source in Morgan's individual set, which every
consuming repository materializes and runs. The other is BestPractice's
port in [tools/checks/](../tools/checks/). On 2026-10-10, three gaps between
them turned up in one afternoon:

- the individual set's copy did not skip a bot-authored fallback commit;
- neither honored `PRECEDENT_CHECK_RANGE`, which the author check's
  "verbatim" twin had read since 2026-10-06;
- neither skipped a commit GitHub itself made, so a consumer's merge gate
  refused every GitHub-button merge.

The author check ([check_commit_author.py](../tools/check_commit_author.py)) has the same shape and the same
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
- 2026-10-10: Morgan, "yes to both, move the sets and build the shared
  check". Built on BestPractice branch
  `2026-10-10-one-commit-identity-check-y1ktn` and precedent-individual
  branch `2026-10-10-one-commit-identity-check-y1ktn`, stopped at Act.
  The two checks are engine files in tools/ (check_commit_author.py,
  check_commit_dates.py), so materialize never writes them and the
  tools/checks/ question does not arise. The individual set drops its
  copies and tests, points its practices' checked_by at the engine files,
  and moves its hardcoded exemptions into its identity.json. Close this
  once both are on main and the individual set has taken the engine.
- 2026-10-10, closed: on main in all three. BestPractice through PR #1034,
  with the --help fix GitHub's test asked for in PR #1037 (issue #1035);
  the individual set through its PR #314, after Update Vendors to e3aaedd1;
  the writing set through its PR #165. Every other repository takes the
  engine copies on its next Update Vendors, and its materialized copies
  under tools/checks/ go when its views next sync.

---
slug:              todo-2026-10-05-move-repo-maintenance-into-universal
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "both passes reaching main, then Update Vendors in every repository that declares precedent-shared-repo-maintenance"
batch:             null
decision:          "fold precedent-shared-repo-maintenance into universal, in two passes"
decision_strength: decided
waiting_on:        null
noted:             2026-10-05
closed:            null
---
## What

- <a id="repo-maintenance-into-universal"></a>**Finish moving the
  repo-maintenance set's rules into universal, then retire the set.**

  Morgan decided on 2026-10-05 to fold the whole set into universal, to cut
  the number of sets each install clones. Its subject, running a repository
  that vendors a practice layer, is every install's.

  **Pass 1, done 2026-10-05:** drift-notice, install, mirror-into-agents,
  no-duplication, rule-scope-ask, todo-gate and vendor-neutral-by-default
  drafted into universal with [tools/precedent_move.py](../tools/precedent_move.py),
  their "this team" wording generalized. The set's copies of
  fresh-before-write and session-trailer, already active in universal since
  2026-09-28, deduplicated. Universal's occasion share measured about 2,186
  of its 2,250-token allowance afterwards.

  **Pass 2, done 2026-10-05:** default-branch, derived-file-marker,
  deep-check and private-repo-scrub drafted into universal, each with its
  check rewritten as a registered check in
  [tools/precedent_check.py](../tools/precedent_check.py) and a planted case
  in [tools/verify_harness.py](../tools/verify_harness.py). private-repo-scrub's check no longer carries
  a list of private names: it asks each source in force whether it is
  private. light-check was not drafted: its rule was folded into
  `two-check-levels` on 2026-09-28, so its audit became the engine's own
  `light-check` check, with no second copy of the rule. Universal's
  occasion allowance went from 2,250 to 2,500.

## Proposed

Once the blocker clears, run `precedent_move.py --dedupe-only` for each of
the eleven moved practices, from the set to universal. light-check is the
exception: its set copy is deduplicated by hand, with `in_force_at:
two-check-levels`, since the tool only points a copy at the same slug.
Then remove `precedent-shared-repo-maintenance` from each `precedent.json`
that declares it. Archiving the repository on GitHub is Morgan's call.

**BestPractice stopped declaring it, 2026-10-05.** Universal carries every
rule the set still held active (light-check through `two-check-levels`), so
this repository loses nothing by dropping it from its own `precedent.json`;
the very deep check run that day was reading the set as in force here. The
set copies are not deduplicated yet, and other repositories that declare it
still do.

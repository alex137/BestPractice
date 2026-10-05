---
slug:              todo-2026-10-05-move-repo-maintenance-into-universal
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "pass 2 is a separate session's work (porting five check scripts into universal's engine is hours, not a move); the set's withdrawal waits on that and on Update Vendors in every repo declaring it"
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

## Proposed

**Pass 2:** deep-check, default-branch, derived-file-marker, light-check and
private-repo-scrub. Each carries a check script in the set's
`tools/checks/`, and universal refuses a `checked_by` it does not register.
So each check is first rewritten as a registered check in
[tools/precedent_check.py](../tools/precedent_check.py), with a planted case
in [tools/verify_harness.py](../tools/verify_harness.py)'s
`check_precedent_check_fires`, and only then moved. Two things to watch:

- Their index lines push universal's share past its 2,250 allowance.
  Morgan approved raising it for this fold on 2026-10-05; set it to the
  measured share plus a margin, with that reason in `precedent-source.json`
  and `tools/session_load_budgets.json`.
- `deep-check` is not a copy of `two-check-levels`: its by-request read of
  the repo against itself is the part universal lacks. On 2026-09-06 a
  session dropped it as redundant and a routine check went missing for a
  day ([very-deep-check](../practices/very-deep-check.md)'s Story).

**Then:** once both passes are on main and every repo declaring the set has
run Update Vendors, `precedent_move.py --dedupe-only` for each of the
twelve, and remove `precedent-shared-repo-maintenance` from each
`precedent.json`. Archiving the repository on GitHub is Morgan's call.

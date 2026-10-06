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

**Only the edits that retire it, from 2026-10-06.** Morgan (strength:
decided): *"We are deprecating repo maintenance and working style ... you
should not make edits to them unless the edits relate to their deprecation
or graceful deprecation. Please don't forget this."* A finding in the set is
fixed where the rule lives now, or recorded here and left. The push check
refuses any other edit to a set whose `precedent-source.json` says it is
retired ([retired-set-takes-only-its-retirement](../practices/retired-set-takes-only-its-retirement.md)).
The rule is temporary: it goes once both sets are gone, and its `expires:`
says when.

The set's pre-staging already carries one larger edit from earlier the
same day, made by the very deep check's fix pass before this rule was
said: its default-branch rule and check rewritten to match universal's
trunk rule. It stays, as graceful retirement: a shared copy wins over
universal's by slug, so until each repository that still declares the set
runs Update Vendors, the old copy would hold it to the name `main` against
universal's rule. Nothing further goes into that copy.

## Proposed

Once the blocker clears, run `precedent_move.py --dedupe-only` for each of
the eleven moved practices, from the set to universal. light-check is the
exception: its set copy is deduplicated by hand, with `in_force_at:
two-check-levels`, since the tool only points a copy at the same slug.
Then remove `precedent-shared-repo-maintenance` from each `precedent.json`
that declares it. Archiving the repository on GitHub is Morgan's call.

**The set's last two checks, 2026-10-06.** The very deep check found
that the commit-trailer check shipped only in the set. It now ships with
the engine as
[tools/checks/check_session_trailer.py](../tools/checks/check_session_trailer.py),
claimed by universal's [session-trailer](../practices/session-trailer.md),
with a planted case, so every repository that resolves universal
materializes it. The fresh-before-write check needed no port: the guard it
tested ships with the engine and is wired into every repository by the
engine refresh, and the harness already plants the states it asserted.
Morgan kept both practices (2026-10-06, strength: decided), and
BestPractice stopped declaring the set the same day, which also ends the
set's older `default-branch` overriding universal's here.

Still open: deduplicate the set's copies, take the set out of the other
repositories that declare it (the individual and writing sets among them),
and archive the repository, which is Morgan's call.

**How the declarations come out, from 2026-10-06.** Once the set's copies
are deduplicated, add `"retired": {"date": ..., "folded_into": [...]}` to
the set's own `precedent-source.json`. Update Vendors then drops the set
from every repository that declares it, on that repository's next update,
and the very deep check reports any still declaring it -- in both cases
only once every active rule it held is in force elsewhere.

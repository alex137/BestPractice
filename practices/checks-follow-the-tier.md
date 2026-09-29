---
slug:        checks-follow-the-tier
title:       "Checks follow the tier: pre-staging judges the change, staging judges everything"
tier:        on-demand
severity:    default
applies_to:  ["tools/precedent_push_check.py", "tools/precedent_merge_check.py", "tools/precedent_branches.py"]
applies_to_why: "It governs which branch tier a check runs at, so it binds the three files that decide that: the push check, the merge gate and the tier resolver. Editing any of them is the moment a check's tier is set. Decided: 2026-09-27, when the practice landed."
occasion:    "adding a check, or deciding which branch tier a check runs at"
gates:       []
index_clause: "pre-staging: fast, changed files only; staging: every file; main: plus GitHub"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-27"
approved_by: "Morgan, 2026-09-27 (strength: decided): \"for pre-staging, we should not check every file ... the pre-staging checks need to be the fast, immediate checks ... we have staging precisely to do the full suite ... That has to be our articulated philosophy.\""
---
## Rule
**Each branch tier has one job, and a check goes to the tier whose job it is.**

- **Into `pre-staging`: fast, and only about the change.** A push or pull
  request there is judged on the files it creates or changes, and on the
  generated files a changed practice feeds -- **nothing more**, in seconds.
  A problem in a file the change did not touch is named and left for the
  next tier, never held against this push.
- **Into `staging`: thorough.** The full suite, on every file.
- **Into `main`: thorough, plus GitHub.** The full suite on every file, and
  the repository's GitHub test where it has one.

**No session runs the full check before landing on `pre-staging`.** It
runs at the Promote to `staging`; a failure there is fixed on
`pre-staging` and promoted again (Morgan, 2026-09-27, strength: decided:
*"The point of pre-staging is to move fast, so I want the 10 minute checks
to happen at the staging level, not pre-staging"*; his own
promote-only rule, in his individual set, already has the Promote carry the
full check).

**A new check states its tier when it is added**, and a check that reads
the whole repository runs at `pre-staging` only in a form limited to the
change (`precedent_check.py --changed-files-only`), or not there at all.

## Detail
**Why the split is this one.** `pre-staging` is where every session's work
lands, often and in small pieces; a slow or unrelated refusal there stops
work that did nothing wrong. `staging` exists precisely to run the full
suite, so thoroughness costs nothing at `pre-staging` that it does not
already buy one step later.

**"Only about the change" is exact.** The change is what the push adds on
top of the branch it lands on (`origin/pre-staging...HEAD`), so it covers
the files a session created or edited and nothing a different session put
there. A check may still READ the rest of the repository to answer, for
instance to compare one document against another, but it only REPORTS on
the changed files.
A practice file sync wrote into a consuming repository -- one its
`MANIFEST.json` names -- is not the change's own writing even when the
change is the update that wrote it, so it is not judged there: its source
judges it, and a repair here would be overwritten by the next sync
(2026-09-28, an Update Vendors refused over an acronym in a vendored
practice).

**What `pre-staging` runs today.** The lint, the leak gate and the author
checks, as before -- the leak gate still scans the whole tree, since a
secret anywhere is this push's to stop. Added on 2026-09-27, and on the
changed files only: the practice checks
(`precedent_check.py --changed-files-only`), a compile of each changed
Python file, a parse of each changed shell script (`bash -n`) and of each
changed JSON file, the own test of each changed check
(`tools/checks/check_x.py` runs `tools/checks/tests/test_x.sh`; a
repo-local test and its materialized copy run once, as the materialized
copy), and -- since 2026-09-28 -- a refusal of a new check that arrives
without that test or without `SOURCE_ROOT`, naming the file and lines to
add, and -- when
a practice file changed -- a check that its generated views (`AGENTS.md`,
`MAP.md`, `GLOSSARY.md`) were regenerated with it
(`precedent_push_check.py --changed-files-check`). A push sends commits that
already exist, so that last one refuses and names the command that
regenerates; it never rewrites anything itself. Everything else waits for
`staging`.

**What moves a check to `pre-staging`:** it is fast (seconds, not minutes)
and its finding can be pinned to a file. A check that cannot name a file,
or needs the test suite, belongs at `staging`.

**Where it is built.** `tools/precedent_push_check.py` decides the tier from
the branch a push writes (`precedent_branches.tier_for_push`) and adds the
changed-files practice run for `pre-staging`;
`tools/precedent_merge_check.py` does the same for a pull request merged
through GitHub; [spec/BRANCH_TIERS_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/BRANCH_TIERS_PLAN.md)
holds the tier design.

## Why
Stated by Morgan on 2026-09-27, when the practice checks were added to
pushes into `pre-staging`: the checks there have to stay the fast,
immediate ones, and every file is checked at `staging` and `main`, where
there is time for it.

## Story
A plan document whose title and first heading disagreed reached
`pre-staging` on 2026-09-27: a push there ran only the lint, the leak gate
and the author check, and the practice check that knows about headings ran
only at `staging`. It surfaced as a red full check on an unrelated change a
few hours later. The fix put the practice checks at `pre-staging`, and
Morgan set the condition this practice records: only for the files the
change touches.

## Install
Nothing to install. A repository that vendors the engine gets the tiered
push check with it; this practice is what a session reads before adding a
check to it.

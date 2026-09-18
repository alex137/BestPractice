---
slug:            gotcha-2026-09-17-a-consumers-settingsjson-hardcoded-git-identity
status:          live
noted:           2026-09-17
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A tracked `.claude/settings.json` names a real person's `GIT_AUTHOR_NAME` and
`GIT_AUTHOR_EMAIL` in its `env` block. Every commit from every collaborator
who loads that file is silently authored as that one person, forever, and
`commit-identity.sh`'s whole per-session, per-person resolution never gets a
chance to run — `GIT_AUTHOR_*` outranks `git config user.*`, so the hardcoded
value wins before the hook's own logic is even reached.

## Story

Reported 2026-09-17 by a session working in a private consumer repo, which
described a `.claude/settings.json` with exactly this shape and attributed it
to BestPractice's own shipped Claude Code adapter template.

**Checked, not assumed, before acting on it.** `templates/harness/claude-code/settings.json`
does not have this pattern, and this repo's full git history (`git log --all
-p -- '**/settings.json'`, every branch) shows it never has — the template's
own `_comment` already argues against exactly this anti-pattern, at length.
`precedent-individual`'s own `.claude/settings.json` *does* hardcode a name
and address, but that is the documented, correct case: `commit-identity.sh`'s
own resolution ladder (rung 2) treats a root `identity.json` as a repo
declaring itself somebody's individual practice source, and
`precedent-individual`'s value is derived from its `identity.json` and
checked against it by a private tool there. Neither is the bug.

The likely real origin, by the reporting session's own memory rather than
anything traced here: one specific private consumer repo, outside this
session's reach (cross-owner — see "What this session could not do" below).
**Not independently confirmed from this repo** as of this writing; a session
was handed opening text to check and fix it there directly, in a separate
window this repo cannot see into. This entry deliberately does not name that
repo — BestPractice is the shared, public upstream, and which private repo
has which problem is not this file's business to carry (leak_gate.py's own
blocklist refused the first draft of this entry for exactly that reason).
Treat this entry's Fix section as the general case for any consumer repo,
not a report that one specific installed repo definitely has it.

**What this session could not do, and why.** BestPractice sessions cannot
reach into an arbitrary consumer repo to fix this directly — `add_repo`
refuses to mix repositories from a different owner into an existing session
outright ("cross-tier adds are not supported"), which is a platform
boundary, not a missing permission. The remedy is `session-text`: hand a
copy-pasteable brief to a fresh window rooted in the affected repo, never
try to force the mix.

## Fix

**In `precedent_check.py` (this repo), fixed at the source, 2026-09-17:**
`no-hardcoded-git-identity` (scope `tree`, `practice_backed=False`, beside
`declared-hooks-exist` and `hooks-on-disk-are-reachable`) flags a tracked
`.claude/settings.json` naming `GIT_AUTHOR_NAME` or `GIT_AUTHOR_EMAIL` in its
`env` block, and stands down only where a root `identity.json` shows the repo
really is somebody's individual practice source. It ships in `tools/`, so it
reaches every already-installed repo through an ordinary vendor refresh —
`vendor-update-runbook.md` step 3 never touches a consumer's `settings.json`
itself, but it does refresh `tools/`, and the check travels with that.
**In THIS repo specifically, nothing further is needed**: `.github/workflows/deep-check.yml`
already runs the full `precedent_check.py` suite, unfiltered, on every push
to every branch, so this check is already CI-enforced here and this pattern
cannot land in BestPractice's own tracked `settings.json` again without a red
build catching it.

**In any OTHER repo that vendors BestPractice** (consumer repos, individual
and team practice sources alike — anywhere with its own `.claude/settings.json`):

1. Run that repo's own "Update Vendors" (or `python3 tools/precedent_vendor_engine.py refresh`
   directly) so its `tools/precedent_check.py` picks up the new check.
2. Run `python3 tools/precedent_check.py --only no-hardcoded-git-identity`
   there. It is silent (`NotApplicable`) if the repo has no tracked
   `.claude/settings.json` at all, and passes clean if `env` never names
   either variable.
3. If it flags: open `.claude/settings.json` and remove `GIT_AUTHOR_NAME`
   and `GIT_AUTHOR_EMAIL` from the `env` block. Leave `TZ` alone if one is
   already there — that is a separate, legitimate default
   (`buenos-aires-dates.md`), not this bug.
   **Unless** the repo genuinely is somebody's own individual practice
   source (it has a root `identity.json` declaring the same person) — there,
   self-declaring is correct by design and the check already knows to leave
   it alone.
4. Confirm `commit-identity.sh` is actually wired into that repo's
   `SessionStart` hooks (`INSTALL.md` §1's hook table calls it "always").
   Removing the hardcoded value with no working hook behind it just breaks
   author resolution instead of fixing it.
5. Re-run step 2's command to confirm it now passes.
6. Commit and push per that repo's own branch conventions. **This does not
   retroactively fix commits already published under the wrong author** —
   rewriting merged history costs more than the wrong value does
   (`no-rewrite-for-warnings`); grandfather them by SHA with a note, the same
   way `precedent-individual`'s own `identity.json` does, rather than
   rewriting.

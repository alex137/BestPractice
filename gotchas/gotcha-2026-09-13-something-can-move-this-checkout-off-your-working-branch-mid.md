---
slug:            gotcha-2026-09-13-something-can-move-this-checkout-off-your-working-branch-mid
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

Something can move this checkout off your working branch mid-session, and the cause is NOT known — treat a silently-vanished edit as this before you re-derive it.

## Story

**Something can move this checkout off your working branch mid-session, and
the cause is NOT known — treat a silently-vanished edit as this before you
re-derive it.** 2026-09-08, three minutes after a commit, the reflog recorded
`checkout: moving from claude/deep-review-… to precedent-beta-v01` followed by
a fast-forward pull. Nobody asked for either. The commit survived on the
abandoned branch, but twenty minutes of edits landed on the wrong one, and
**the only symptom was a function that had silently stopped existing** — which
reads exactly like a bad edit and is really a branch switch. `git status` was
clean throughout, as it always is for a checkout. **Three suspects are ruled
out by replay rather than reasoning**: `precedent_vendor_engine.py seed`,
`precedent_refresh_sources.py --apply` and `checkin.py fresh` were each run
against a throwaway clone on a feature branch and none moved `HEAD`. It is
also **not** the `checkin.py update` incident returning — that one is fixed
and verified (archived entry 4). Whatever does it is outside this repo's
tools; do not assume it is fixed. **Detection is the whole remedy available**:
[tools/precedent_session_check.py](../tools/precedent_session_check.py) stamps
the branch on its first run and compares on every later one. When it fires the
work is **not lost** — `git reflog` lists the commit, `git checkout` returns
to it, `git cherry-pick` recovers anything committed after.

**Second recorded instance, 2026-09-14, and it narrows the suspects.** A
session working on a feature branch found the checkout back on
`precedent-beta-v01` between one tool call and the next, with
`git reflog` showing `checkout: moving from <feature-branch> to
precedent-beta-v01` and nothing else — **no pull afterwards this time**, unlike
the 2026-09-08 case. Nothing was lost: the branch tip still matched its remote,
because the work had already been pushed. What that buys is the ordering — the
move happened AFTER a push and a fetch, in a turn that ran no repository tool
at all beyond `git`, so whatever does this does not need one of this repo's
own tools to have been invoked. **The cheap habit that made it a non-event was
pushing before the gap**: a pushed branch survives the move, an unpushed one
survives only in the reflog.

**Third recorded instance, 2026-09-16, and it shows a worse variant: the move
can carry UNCOMMITTED changes with it.** A session on a feature branch (already
one commit ahead of what it had pushed) found `git log` reporting a commit
that should not have been there and `git diff` showing edits it did not
recognize — `git reflog show HEAD` confirmed
`checkout: moving from claude/elegant-pascal-8cb3n2 to precedent-beta-v01`
with nothing in the session's own command history requesting it. Unlike both
prior instances, there was no stranded commit and no already-pushed branch to
fall back on: the session's own **uncommitted** edits had ridden along across
the switch, landing as an uncommitted diff on top of `precedent-beta-v01`
instead of the branch they were written for. `git status` looked completely
ordinary throughout — clean branch name in the prompt, a plausible-looking
diff — which is what makes this variant more dangerous than the first two:
there is no missing function or stranded commit to notice, only the wrong
base underneath edits that look fine on their own. **Recovery, in order**:
`git diff > patch-file` before touching anything else (this preserves the
edits regardless of what happens next), confirm the abandoned branch's
history is unharmed (`git log`/`git rev-parse` against its remote), switch
back to the correct branch cleanly, then `git apply --reject` the saved patch
— expect at least one hunk to conflict if the correct branch has diverged
from the wrong one since the edits were made, and reapply that hunk by hand
from the `.rej` file. See [spec/VERIFY_HARNESS_PERFORMANCE.md](../spec/VERIFY_HARNESS_PERFORMANCE.md)
for the full incident this was pulled from.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

---
slug:            gotcha-2026-09-08-something-can-move-this-checkout-off-your-working-branch-mid
status:          retired
noted:           2026-09-08
severity:        null
retired:         "2026-09-08"
retires_when:    null
---
## Symptom

Something can move this checkout off your working branch mid-session,

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **Something can move this checkout off your working branch mid-session,
  and the cause is NOT known — treat a silently-vanished edit as this
  before you re-derive it.** 2026-09-08, three minutes after a commit on
  `claude/deep-review-…`, the reflog recorded
  `checkout: moving from claude/deep-review-… to precedent-beta-v01`
  followed by `pull origin precedent-beta-v01: Fast-forward`. Nobody asked
  for either. The commit survived on the abandoned branch, but the next
  twenty minutes of edits were made on `precedent-beta-v01`, and the only
  symptom was **a function that had silently stopped existing** — a check
  written earlier in the session was simply not in the file any more, which
  reads exactly like a bad edit and is really a branch switch. `git status`
  was clean throughout, as it always is for a checkout.
  **Three obvious suspects are ruled out, by replay rather than reasoning**:
  `precedent_vendor_engine.py seed`,
  `precedent_refresh_sources.py --apply` and `checkin.py fresh` were each
  run against a throwaway clone sitting on a feature branch, and none of
  them moved `HEAD`. So this is not the `checkin.py update` incident above
  returning; whatever does it is outside this repo's own tools, and the
  next session should not assume it has been fixed.
  **Detection is the whole remedy available.**
  [tools/precedent_session_check.py](../tools/precedent_session_check.py)
  stamps the branch on its first run of a session and compares on every
  later one, so the drift is one command away instead of an archaeology
  problem. When it fires: the work is **not lost** — `git reflog` still
  lists the commit, `git checkout <the branch it names>` returns to it, and
  anything committed after the move is recovered with `git cherry-pick`.
  Check `git rev-parse --abbrev-ref HEAD` before concluding an edit was
  bad, and re-verify with `git reflog` rather than trusting that a clean
  tree means nothing happened.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

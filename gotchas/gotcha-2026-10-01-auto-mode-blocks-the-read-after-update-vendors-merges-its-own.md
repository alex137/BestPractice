---
slug:            gotcha-2026-10-01-auto-mode-blocks-the-read-after-update-vendors-merges-its-own
status:          live
noted:           2026-10-01
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

In Claude Code's auto mode, Update Vendors merges its own pull request
(step 12) and the merge goes through. The next command, even one that only
reads the merged branch to confirm its content, comes back `Denied by auto
mode classifier` as **Merge Without Review**, and the check it was running
never runs.

## Story

**2026-10-01, a consumer's update.** Step 12 of
[vendor-update-runbook](../practices/vendor-update-runbook.md) merges the
update's own pull request with no human review, which the runbook allows:
"Update Vendors" is the authorization. The merge went through with the
GitHub merge tool. The session's next command fetched the merged branch to
verify its content, step 11's check, and the classifier refused it as
"Merge Without Review": it judged the sequence, not the single read. So the
content check, left for after the merge, never ran.

It is a different refusal from the one a bare "Promote" into `main` meets
([gotcha-2026-09-30](gotcha-2026-09-30-auto-mode-refuses-a-bare-promote-into-main-as-a-production.md)),
and it lands one step later: after the merge has already happened.

## Fix

**Check content before the merge, not after.** Step 11 verifies the pushed
branch or the pull request's head on the remote, which is exactly what will
merge, before step 12 merges it. The check that matters then runs before
anything a classifier can block.

**A refused step is reported by name, never routed around.** If the safety
check refuses a step after the merge, say which step it refused and stop:
no other command for the same outcome, no settings edit of the session's
own. The durable allowance is the person's, as the Promote gotcha says.

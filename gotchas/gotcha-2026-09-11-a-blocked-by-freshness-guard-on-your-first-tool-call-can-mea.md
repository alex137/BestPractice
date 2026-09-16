---
slug:            gotcha-2026-09-11-a-blocked-by-freshness-guard-on-your-first-tool-call-can-mea
status:          retired
noted:           2026-09-11
severity:        null
retired:         "2026-09-11"
retires_when:    null
---
## Symptom

Read the fix date against the tree before acting on the workaround below.

## Story

**Read the fix date against the tree before acting on the workaround below.**
Pushing an empty branch to give the guard a counterpart was the right move on
2026-09-09 and is unnecessary now.

<details>
<summary>The full entry as it stood before 2026-09-11</summary>

- **A `BLOCKED by freshness-guard` on your first tool call can mean your
  BRANCH has no counterpart on origin yet, not that your checkout is stale —
  and the override the message offers switches the guard off for the whole
  checkout.** Reported 2026-09-09 by a session working in one of the private
  practice-set repositories: its first command was refused because the branch
  it had been told to work on did not exist on origin, so there was nothing
  for the guard to fetch or compare against. **The remedy the refusal names
  is the wrong one here.** `git config precedent.freshness.override true`
  buys past a branch-shaped inconvenience by disabling freshness checking for
  the rest of the session — trading the guard that catches the single most
  expensive failure class in this file for the smallest possible convenience.
  **Push the branch instead.** It gives the guard a counterpart to fetch,
  costs nothing (the branch carries no commits beyond its base yet), and
  leaves every later check running. That session did exactly that, after
  confirming by hand that its HEAD matched `origin/main` on a clean tree.
  **Not established from here:** which of the guard's paths produced the
  refusal, or whether that set's copy is the older build named two entries
  above — that repository is under another owner and cannot be attached to a
  session rooted here, per the cross-owner entry below.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

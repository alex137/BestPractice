---
slug:            gotcha-2026-09-11-if-you-suspect-a-timezone-problem-check-date-and-ls-l-git-ho
status:          retired
noted:           2026-09-11
severity:        null
retired:         "2026-09-11"
retires_when:    null
---
## Symptom

If you suspect a timezone problem, check `date` and `ls -l .git/hooks/pre-commit`, not the `env` block

## Story

Everything else it carried is in that entry too, in more detail: `TZ` unset in
tool shells so git falls back to the system zone, `commit-identity.sh`
repointing `/etc/localtime` for a declared zone, and `PRECEDENT_LOCALTIME`
existing so the repoint is testable. So nothing was lost by removing it, and a
contradiction between two adjacent entries went with it — which is the kind of
thing a reader resolves by trusting whichever one they read first.

The two diagnoses it was written about are entry 26 above; that derivation is
unaffected and stands.

<details>
<summary>The full entry as it stood until 2026-09-11</summary>

- **If you suspect a timezone problem, check `date` and
  `ls -l .git/hooks/pre-commit`, not the `env` block.** The block in
  `.claude/settings.local.json` is inert — the harness reads environment
  before hooks run — and reading it sent two diagnoses down the wrong path.
  `TZ` is unset in every tool shell, so git falls back to the SYSTEM zone;
  [.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh)
  repoints `/etc/localtime` for a **declared** zone, which is the one lever a
  hook can move mid-session that every later shell and `git merge` picks up.
  `PRECEDENT_LOCALTIME` overrides the target so this is testable. The
  derivation is in the archive.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

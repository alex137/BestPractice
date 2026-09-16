---
slug:            gotcha-2026-09-07-the-timezone-half-of-that-backstop-was-refusing-a-wrong-offs
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

The timezone half of that backstop was refusing a wrong offset it could

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The timezone half of that backstop was refusing a wrong offset it could
  have prevented — the container's clock is the lever, and a hook can move
  it.** 2026-09-07: every commit here needed a `TZ="…" git commit` prefix
  and the merge commits that forgot it were refused, correctly, for
  `+0000`. Three mechanisms existed and every one of them acts *after* git
  has resolved an offset: `pre-commit` refuses, `prepare-commit-msg`
  refuses the merge, and the `.claude/settings.local.json` derivation
  applies only from the NEXT session, because the harness reads environment
  before hooks run. Measured rather than reasoned: `/etc/localtime` was
  `Etc/UTC`, `TZ` was unset in every tool shell (`echo "${TZ:-<unset>}"`),
  and `settings.local.json` already carried the right zone and was inert.
  git falls back to the SYSTEM zone when `TZ` is unset, and the system zone
  is the one lever a hook can move mid-session that every later shell,
  tool, and `git merge` picks up without cooperating — so
  [.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh)
  repoints it, for a **declared** zone only. Verified end to end: a fresh
  `git init` with no prefix and no local config committed at `-0300`.
  `PRECEDENT_LOCALTIME` overrides the target so this is testable — and the
  older `check_commit_identity_derives_declared_timezone` fixture, which
  declares Europe/Berlin, now sets it too; without that the harness itself
  would have put the container on Berlin time and every later commit in the
  session would have been refused for an offset the harness caused.
  **If you suspect a timezone problem, check `date` and
  `ls -l .git/hooks/pre-commit`, not the `env` block** — that block is
  inert here and reading it sent two earlier diagnoses down the wrong path.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

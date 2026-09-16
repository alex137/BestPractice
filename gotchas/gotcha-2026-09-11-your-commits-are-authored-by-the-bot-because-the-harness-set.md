---
slug:            gotcha-2026-09-11-your-commits-are-authored-by-the-bot-because-the-harness-set
status:          retired
noted:           2026-09-11
severity:        null
retired:         "2026-09-11"
retires_when:    null
---
## Symptom

Your commits are authored by the bot because the harness sets that identity in git's GLOBAL config AND in every clone's LOCAL config

## Story

<details>
<summary>The full entry as it stood until 2026-09-11</summary>

- **Your commits are authored by the bot because the harness sets that
  identity in git's GLOBAL config AND in every clone's LOCAL config — so a
  global-only fix is silently overridden, and the Stop hook will tell you to
  put the bot back.** Measured 2026-09-11: `user.name=Claude`,
  `user.email=noreply@anthropic.com` in `--global` and in both clones'
  `--local`, `TZ` unset so the system clock reads **-0400** rather than the
  declared -0300, and no global backstop installed to refuse any of it.
  `git var GIT_AUTHOR_IDENT` returned the bot with no env override in sight.
  The cause is the entry above — a session rooted one directory up, so
  `commit-identity.sh` never ran — but the SYMPTOM reads as a git-config
  problem, and the config it reads as is one somebody already set on purpose.
  **The cost is that a wrong-author commit cannot be repaired after it
  merges** without rewriting `main`, which is why `fab8d42` and two entries in
  the individual set's `grandfathered_commit_shas` are permanent.
  **The remedy is one line, and it is not `git config`:**
  ```
  bash .claude/hooks/commit-identity.sh
  ```
  It sets the local identity, the GLOBAL one (so a clone attached later
  inherits a person), repoints `/etc/localtime` so later shells and
  `git merge` get the right offset without a `TZ=` prefix, and installs the
  global `core.hooksPath` backstop that refuses a bot-authored commit
  everywhere.
  **Running it once is not enough, and there are TWO separate things that
  undo it. Both were reproduced 2026-09-11; neither was guessed.**
  **First, and this is the one that kept coming back:
  `python3 tools/verify_harness.py` used to repoint the REAL container's
  `/etc/localtime`.** Its fixtures run `commit-identity.sh`, where no identity
  resolves, so the hook falls to its last rung -- this repo's declared
  `fallback_timezone`, `America/New_York` -- and moved the machine's own
  symlink to it. Controlled before/after: Buenos_Aires in, New_York out,
  across one harness run, with the session's clock left wrong afterwards.
  **The cost lands nowhere near the harness**: the NEXT commit is refused with
  `author-date offset is '-0400'` while the author is already correct, which
  reads as a fresh identity problem and is really this. Fixed by setting
  `PRECEDENT_LOCALTIME` once for the whole run, the same way the harness
  already sets `PRECEDENT_ALLOW_ANY_AUTHOR` for fixture commits -- the
  identical bug, one field over. If a stale harness is around, run it as
  `PRECEDENT_LOCALTIME=/tmp/x python3 tools/verify_harness.py`.
  **Second, a slower one that survives the session.** The same fallback rung,
  reached in a real session because the credential was missing, ALSO writes
  `TZ=America/New_York` into `.claude/settings.local.json` -- **untracked and
  gitignored**, so it shows in no diff and no review, and the harness reads
  that `env` block BEFORE hooks run, where an explicit `TZ` beats
  `/etc/localtime` outright. One credential-less session therefore poisons
  every later session in that clone, invisibly. **So read that file before
  touching any `git config`:**
  `python3 -c "import json;print(json.load(open('.claude/settings.local.json'))['env'])"`.
  Between them these explain why repairing the identity never held: after the
  first repair the identity was never wrong again, and the offset was arriving
  from a fixture that moved the machine's clock or from a variable a previous
  session had written. **Note the asymmetry** that hid it: an individual
  practice source carries a TRACKED `settings.json` env block naming its
  owner's zone, so work rooted THERE is immune; a shared repository
  deliberately names nobody, depends entirely on the hook, and is the one that
  gets poisoned.
  **The durable answer is `PRECEDENT_COMMIT_TZ` in the environment** -- on
  EVERY environment sharing a name, per the twin-environment trap above -- so
  the fallback rung is never reached at all. It needs `PRECEDENT_COMMIT_*` in the environment or a resolvable
  `identity.json`; with the variables present it needs no private repo at all.
  **Verify by effect, never by reading the config you just wrote:**
  `env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u TZ git var GIT_AUTHOR_IDENT`
  must name the person and the declared offset.
  **The second trap is the one that wastes the time.** The harness's own Stop
  hook flags commits whose committer is not `noreply@anthropic.com` and asks
  you to `--amend --reset-author` onto exactly the bot account the individual
  set's own `commit-author` practice refuses and its own mechanical check
  fails on — the account that practice's Rule calls never a person. Neither
  file is in this repository, which is why neither is linked here. Following it recreates the violation
  this repository spent a day fixing. **The repository's gate wins over
  generic harness guidance**; say so and leave the commit alone.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

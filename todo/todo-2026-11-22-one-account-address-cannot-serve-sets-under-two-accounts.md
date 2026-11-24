---
slug:              todo-2026-11-22-one-account-address-cannot-serve-sets-under-two-accounts
kind:              decision
domain:            engine
severity:          medium
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Alex's or Morgan's pick among the three options below"
noted:             2026-11-22
closed:            null
---
## What

- [ ] **A project whose shared practice sets live under two GitHub accounts cannot get both at session start from the environment alone (a private project can write the address in its own file; a public one cannot), and the failure is reported as a bad password.** Found 2026-11-22; story and measurements in [the gotcha](../gotchas/gotcha-2026-11-22-a-shared-set-under-another-account-is-looked-for-under-yours.md). (needs: decision -- Alex or Morgan)

**Why.** A set is declared by name, and its address is built as *account + name* with one account for all of them: `PRECEDENT_SOURCE_BASE_URL`, else the account the token belongs to. The name-only declaration is on purpose, so that a public project never publishes which account owns a private set. A private project can write the full address on the declaration (`repo`), and that works today. **A public project has only the environment**, and the environment holds one account: `PRECEDENT_SOURCE_BASE_URL` for every shared set, plus `PRECEDENT_INDIVIDUAL_REPO` for the person's own. That reaches shared sets under one other account and no more. And when neither is set, the guess is the token's account. This repository shows it: it declares `precedent-shared-writing`, which lives under one maintainer's account, and a session whose token belongs to the other maintainer looks under the wrong account, fails, and prints an authentication error for a repository that was readable with no credential at all.

**Three options, smallest first.**

1. **Say what happened.** When a set is not found at the built address, the message says "nothing called NAME under ACCOUNT; if it lives under another account, here is the setting", and never "authentication failed" alone. No behaviour changes. This alone would have saved the diagnosis.
2. **Let the environment name more than one account.** `PRECEDENT_SOURCE_BASE_URL` takes several addresses, tried in order. Nothing is published; a person with sets under two accounts sets it once.
3. **Try the accounts the project already publishes.** `precedent.json` lists its maintainers' GitHub accounts in the open. When a set is not under the first account, try each maintainer's. It needs no setting at all, and publishes nothing that is not already in the file.

**Pick: 1 and 3 together.** 3 makes the common case work with no setup, and 1 covers what 3 cannot reach. 2 is the fallback if trying maintainers' accounts is judged too clever.

**The cost of leaving it.** Each new person or environment with sets under two accounts meets the same misleading error, and until somebody works out that it is an address and not a token, their sessions run without the team's rules and, in a project, cannot push ([the push-check item](todo-2026-11-22-a-push-is-refused-over-a-practice-set-it-does-not-touch.md)).

## How It Closes

`status` becomes `done` when the pick is made and, for whatever was picked, it is on `main` with [PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md) saying the same thing.

## Notes

- This session changed no engine file.

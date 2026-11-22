---
slug:              todo-2026-11-22-a-push-is-refused-over-a-practice-set-it-does-not-touch
kind:              decision
domain:            engine
severity:          high
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Alex's or Morgan's yes or no on the one-line change below; it changes what a gate refuses, so no session lands it on its own"
noted:             2026-11-22
closed:            null
---
## What

- [ ] **A session that cannot reach one declared practice set cannot push anything, even a change that touches no practice file.** Found 2026-11-22 from a private project whose worker sessions hand their work over as text because every push is refused. The story, the measurements and the way out for a stuck session are in [the gotcha](../gotchas/gotcha-2026-11-22-a-shared-set-under-another-account-is-looked-for-under-yours.md). (needs: decision -- Alex or Morgan)

**What refuses, exactly.** In a project that uses Precedent, the push check runs `build_views.py --repo . --views-only --check`. That run looks only at the map, the glossary and the where-things-are page; it never reads or writes the practice block in [AGENTS.md](../AGENTS.md) (its own comment says so, and the block is left out of the files it compares). But before it compares anything it still asks every declared practice set for its practices, and when one is not on disk it prints *NOT VERIFIABLE* and exits clean. [precedent_push_check.py](../tools/precedent_push_check.py) then reads those two words as a failure (`_guard_build_views`): *"the loader block is built from sources this machine cannot reach, so 'no drift' was not established"*. So the push is refused over a block this run was never checking.

**It reads as an oversight, not a decision.** The same run already steps over the other missing-set case on purpose: for a person's individual set it passes `'ignore'`, with the comment "a run that never touches the block". The shared-set case two lines later was not given the same treatment. And the check beside it, `views_sync`, which is the one that does judge the block in a project, is called with `--skip-unresolved` and the comment "sources that cannot be resolved here are said and skipped, never failed".

**The contract, in one line** ([review-against-a-contract](../practices/review-against-a-contract.md)): *a push is never called clean when something it changes could be stale and nobody looked.*

**The smallest change that keeps it.** In [build_views.py](../tools/build_views.py), a `--views-only` run does not ask the other practice sets for anything, because nothing it compares is built from them. It then never prints the two words, and the push check's guard is untouched and still fires where it should: in a practice set's own push, where `build_views.py --check` really does judge the block. Nothing the push changes goes unlooked-at: the map, glossary and where-things-are page are still compared, and the block is still `views_sync`'s to judge, which already says out loud when it could not look.

**One thing to settle with it.** `views_sync` says and skips when a set is unreachable. That is right for a push that brings no practice change. For a push that itself edits the generated block or the copied-in practice files, "could not look" should still refuse, since that is exactly the change nobody could check. Whether it does today was not tested here; the session that lands this reproduces both cases first.

**The cost of leaving it.** Every session started in a project with a set it cannot reach can push nothing. The sessions do not go around the check, so their work travels as pasted text, and a person or a second session re-applies it by hand. The trigger is common: a set under a different account than the token's, a set whose access lapsed, or a set somebody retired while a project still declares it.

**A second way a set goes missing, reported the same day.** A session had read access to a declared set and its own `git clone` was stopped by a permission prompt, which the session rightly did not go around. The settings Precedent installs ([templates/harness/claude-code/settings.json](../templates/harness/claude-code/settings.json)) allow attaching a repository and allow any `python3 tools/precedent_*` command without a prompt; they do not allow a bare `git clone`. So the route that needs no prompt is the engine's own: `python3 tools/precedent_session_check.py --apply`, which clones each declared set to the place it belongs. That only works when the set's address is right, which is the [two-accounts item](todo-2026-11-22-one-account-address-cannot-serve-sets-under-two-accounts.md). Where the instructions say "attach it and clone it", they should name that command, so that no session is sent to type a clone its settings will stop.

**Reproduced 2026-11-22** in a throwaway project declaring one shared set that was not on disk: the views-only check printed the line and exited clean; with the set cloned beside the project the line was gone.

## How It Closes

`status` becomes `done` when Alex or Morgan has said yes or no. On a yes: the change is on `main` with a test that plants a project with one unreachable shared set and shows (a) a push that touches no practice file passes and says the set was not looked at, and (b) a push that edits the generated block is still refused.

## Notes

- This session changed no engine file; the task was research and a proposal.

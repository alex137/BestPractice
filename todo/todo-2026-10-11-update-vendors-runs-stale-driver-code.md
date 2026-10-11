---
slug:              todo-2026-10-11-update-vendors-runs-stale-driver-code
kind:              decision
domain:            engine
severity:          major
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan: \"Act\" on the plan below"
noted:             2026-10-11
closed:            null
---
## What

**Update Vendors runs whatever code sits in the BestPractice clone's working
tree, and nothing checks that it is the code it just fetched.** A
consumer's update stopped on what looked like a BestPractice bug; the fix
was already on `main`, but that session's clone was behind and ran the old
code. It nearly asked the person to override for nothing.

[tools/precedent_update.py](../tools/precedent_update.py) takes
`SOURCE = HERE.parents[1]` and its step 1 runs `git fetch origin
<refspec>`: that moves the origin refs it then reads by commit, never the
working tree that is executing. So does every module it imports (`pve`,
`le`, `pb`, the lazy imports) and the
[checkin.py](../tools/checkin.py) it runs by path (line 4673). The header's
"every step is the current code" and
[spec/ONE_COMMAND_UPDATE_PLAN.md](../spec/ONE_COMMAND_UPDATE_PLAN.md)'s "the
tool doing the update is always the current one" assume a current clone and
never check it.

**What was lost on 2026-09-27 is a rule, not a step:** the code that runs is
the code that was fetched. The engine keeps it by reading blobs
(`_source_tools_at` in
[precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)); the
update broke it when the runbook became one command
([3c10e196](https://github.com/alex137/BestPractice/commit/3c10e196)). The
plan's step 1 tool would not have caught this either:
`precedent_refresh_sources.candidate_dirs()` skips the clone it runs from.

## Constraints the fix must keep

- **Never move the clone.** Checking out or pulling in the caller's clone
  is the PR #110 failure (`_source_tools_at`'s docstring), and the runbook
  forbids a switch before an update
  ([todo-2026-10-07-one-sets-update-moves-another-sets-working-branch](todo-2026-10-07-one-sets-update-moves-another-sets-working-branch.md)).
- **Parallel runs stay safe**
  ([todo-2026-10-10-parallel-update-vendors-race-on-shared-clones](todo-2026-10-10-parallel-update-vendors-race-on-shared-clones.md)):
  one run must never change the code another is running.
- **CI and the harness test the change, not origin.** A run whose clone is
  current or ahead runs in place.
- **Nothing stale writes first.** Today `undo_leftover_standin`,
  `le.recover`, `restore_own_staged_output` and `realign_catalogue_record`
  all write into the consumer before the fetch.

## Plan

Worked out with a review session over four rounds on 2026-10-11 (staging @
5f0589fe).

1. **A read-only bootstrap runs first**, before anything that writes. It
   reads `followed_branch(repo)` (precedent.json), fetches under
   `held(SOURCE)`, reads `held_pin(repo)` without moving it (never
   `take_pin`), takes `--from-ref` / `--take-anyway` from argv, and finds the
   newest commit on the followed branch whose tree carries a passed marker
   (`pb.passed_markers`, one `ls-remote`, no API budget). It stays small and
   rarely touched: it is the one piece that still runs from whatever the
   clone holds.
2. **The driver commit, by ancestry.** Driver = the newest green commit on
   the followed branch (for a staging follower, the staging tip, as
   `source_commit` already takes it). If the data commit descends from it,
   or is diverged from it (a `--from-ref` test commit), driver = data. The
   driver is never older than the data.
3. **Re-exec only when the clone is provably older:** the clone's `tools/`
   differs from `<driver>:tools` AND HEAD is not a descendant of the driver.
   Identical or ahead runs in place and says so; a dirty `tools/` runs in
   place with a warning. An opt-out flag runs the working-tree code for
   someone testing their own changes, and the report always names which
   commit's code ran.
4. **The re-exec runs from a detached worktree**, not a copied directory:
   tools find their repository from their own path
   ([checkin.py](../tools/checkin.py) 122-125,
   [precedent_local_edits.py](../tools/precedent_local_edits.py) 100,
   [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) 268-270,
   [precedent_resolve.py](../tools/precedent_resolve.py) 77,
   [build_views.py](../tools/build_views.py) 69-70), and in a real
   checkout each comes out right with no environment variable.
   `git -c core.hooksPath=<empty dir> worktree add --detach <dir> <driver>`:
   the empty directory keeps the global post-checkout pass-through from
   running the clone's own hook.
5. **Where the worktrees live and how they're cleaned up:** under
   `<common git dir>/precedent-update-drivers/`, beside the clone lock, named
   `<pid>-<commit12>-<random>`. Each run holds an exclusive `fcntl.flock` on
   its own `<name>.lock` for its whole life. At start, under `held(SOURCE)`,
   a leftover whose lock can be taken (`LOCK_EX|LOCK_NB`) belongs to a dead
   run: `worktree remove --force` it, then `worktree prune`. A busy one is
   left alone. A run removes its own worktree in a `finally`. Where `fcntl`
   is missing (Windows), only its own is removed.
6. **Nothing decided crosses the exec** except a loop-guard environment
   variable holding the driver commit; with it set, the update never
   re-execs again. The new driver re-runs `source_commit`, `take_pin` and the
   rest itself; the cost is a second fetch and a second test lookup.
7. **Fallback:** if the worktree cannot be made, warn at the top of the
   report and again first on any stop that this run's code may be older than
   what it applies.
8. **The runbook:** step 1 of
   [practices/vendor-update-runbook.md](../practices/vendor-update-runbook.md)
   still says the catalogue is read from the clone's working tree through
   `precedent_materialize`; the update now hands `checkin.py --from-ref`.
   Correct that passage, and say what this change does.

**One cost nothing can remove:** a clone made before this lands has no
bootstrap, so its first update after this lands needs one manual
`git pull`. The session-start freshness check
([bcfd336b](https://github.com/alex137/BestPractice/commit/bcfd336b)) is what
tells a person. The pull request says so plainly.

## Harness cases ([tools/verify_harness.py](../tools/verify_harness.py))

- A clone behind origin carrying a deliberately broken old driver: the run
  uses the fetched code, finishes, and names the commit it ran.
- A pin some weeks back, run under the newest driver.
- A current clone and an ahead clone (CI's case) run in place. The existing
  harness cases set the opt-out explicitly, so none depends on the rule.
- A parallel run's live worktree survives another run's cleanup; a dead
  run's leftover is removed.
- `worktree add` fires no hook.
- A crash journal left mid-swap, plus a precedent.json declaring
  `upstream_branch: staging`: the bootstrap follows staging and the replay
  still restores the edits; `vendored_layer_paths(repo, ['precedent.json'])
  == []`, so a future `engine_paths` cannot put precedent.json in the
  journal silently.
- The bootstrap is read-only: with a stand-in commit at HEAD and a journal
  present, HEAD, the index, the journal directory and the pin file are
  byte-identical before the exec.
- No HEAD-sensitive git call runs with SOURCE as its directory
  (`symbolic-ref`, `branch --show-current`, `push`).

## Closes when

The re-exec, its tests and the runbook correction have landed on `main`,
and an update run from a clone that is behind runs the fetched code and
says which commit ran.

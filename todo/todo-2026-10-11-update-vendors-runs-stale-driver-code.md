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

Worked out with a review session over five rounds on 2026-10-11 (staging @
5f0589fe); round five reviewed this item as a spec.

1. **A read-only bootstrap runs first**, before anything that writes. It
   reads `followed_branch(repo)` (precedent.json), fetches under
   `held(SOURCE)`, reads `held_pin(repo)` without moving it (never
   `take_pin`), takes `--from-ref` / `--take-anyway` from argv, applies the
   two tables below, and re-execs or runs in place. It stays small and
   rarely touched: it is the one piece that still runs from whatever the
   clone holds. `PRECEDENT_UPDATE_BOOTSTRAP_ONLY=1` makes it print its
   verdict (G, data, driver, the row that decided where to run) and exit 0,
   the seam the harness tests the tables through.
2. **Driver choice**, in order:
   - a. **G, the newest green commit.** Following `main`: the newest
     first-parent commit within `GREEN_WINDOW` whose tree is in
     `pb.passed_markers` (one `ls-remote`, no API budget). Following
     `staging`: `origin/staging`, which has no markers, as `source_commit`
     already takes it.
   - b. **No G.** Markers unreadable (`None`), or none within the window:
     run in place with item 8's warning. Never guess a tip.
   - c. **Data** = the `--from-ref` commit, else the `--take-anyway` commit,
     else the held pin, else G on a fresh run.
   - d. **Driver by ancestry.** Data is G or descends from G: driver = data
     (a `--take-anyway` of a newer commit whose test failed therefore runs
     that commit's code, and the report says so). Data is an ancestor of G
     (the pin case): driver = G. Diverged: driver = data.
3. **Where to run**, first match wins:
   1. the opt-out flag is set: in place;
   2. `tools/` is dirty (tracked changes, or untracked `*.py`, from
      `git status --porcelain -- tools`): in place, with a warning;
   3. `git rev-parse HEAD:tools` equals `<driver>:tools`: in place;
   4. HEAD descends from the driver: in place, saying so;
   5. otherwise: re-exec from the driver.

   The report always names which commit's code ran, and why.
4. **The re-exec runs from a detached worktree**, not a copied directory:
   tools find their repository from their own path
   ([checkin.py](../tools/checkin.py) 122-125,
   [precedent_local_edits.py](../tools/precedent_local_edits.py) 100,
   [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) 268-270,
   [precedent_resolve.py](../tools/precedent_resolve.py) 77,
   [build_views.py](../tools/build_views.py) 69-70), and in a real
   checkout each comes out right with no environment variable.
   `git -c core.hooksPath=<empty dir> worktree add --detach <dir> <driver>`:
   the empty directory, made by the tool under the worktree parent, keeps
   the global post-checkout pass-through from running the clone's own hook.
5. **Messages name the real clone, never the worktree.** The worktree is
   deleted when the run ends, so a path into it is dead by the time anyone
   reads it. The re-exec'd run derives the real clone from `git rev-parse
   --path-format=absolute --git-common-dir` (its parent directory): derived,
   not passed, so item 7 still holds. Every message and remedy uses it, and
   only git reads use the worktree. Known users today: precedent_update.py's
   five `{SOURCE}` messages (2531, 3580, 4313, 4420, 4495) and
   `precedent_local_edits._this_tool`, whose LEFT FOR YOU remedy is a
   command the person runs after the run ends.
6. **Where the worktrees live and how they're cleaned up:** under
   `<common git dir>/precedent-update-drivers/`, beside the clone lock, named
   `<pid>-<commit12>-<random>`. Each run holds an exclusive `fcntl.flock`
   (not `lockf`, whose locks are per process, so a holder in the same process reads as dead) on its own
   `<name>.lock` for its whole life. At start, under `held(SOURCE)`, a
   leftover whose lock can be taken (`LOCK_EX|LOCK_NB`) belongs to a dead
   run: `worktree remove --force` it, then `worktree prune`. A busy one is
   left alone. A run removes its own worktree in a `finally`. Where `fcntl`
   is missing (Windows), only its own is removed.
7. **Nothing decided crosses the exec** except a loop-guard environment
   variable holding the driver commit; with it set, the update never
   re-execs again. The re-exec'd run reads it and then removes it from
   `os.environ` before spawning anything, so a deep check that runs harness
   cases of its own does not inherit it. The new driver re-runs
   `source_commit`, `take_pin` and the rest itself; the cost is a second
   fetch and a second test lookup.
8. **Fallback:** if the worktree cannot be made, warn at the top of the
   report and again first on any stop that this run's code may be older than
   what it applies.
9. **The runbook:** step 1 of
   [practices/vendor-update-runbook.md](../practices/vendor-update-runbook.md)
   says the catalogue is read from the clone's working tree through
   `precedent_materialize`. Two catalogues are in play: [checkin.py](../tools/checkin.py) reads
   the vendored one by `git archive` (lines 726, 1210, 1568), while
   [precedent_materialize.py](../tools/precedent_materialize.py) reads the
   practice-set clones' working trees for the catalogue in force each
   session. Check which one the passage means, fix only the half that is
   wrong, and say what this change does.

**One cost nothing can remove:** a clone made before this lands has no
bootstrap, so its first update after this lands needs one manual
`git pull`. The session-start freshness check
([bcfd336b](https://github.com/alex137/BestPractice/commit/bcfd336b)) is what
tells a person. The pull request says so plainly.

## Harness cases ([tools/verify_harness.py](../tools/verify_harness.py))

The existing cases set the opt-out explicitly, so none depends on the rule.
**Every re-exec case clears it** and asserts the re-exec happened, by the
report line naming the driver commit.

- **Behind clone, broken old driver.** The fixture's old commit already
  carries the bootstrap; the break sits after it, in `update()`. The case
  runs `<fixture>/tools/precedent_update.py`, never this repo's copy
  (`HERE.parents[1]` makes SOURCE whatever tree the script sits in). It
  asserts the reported driver commit is not the fixture's HEAD, that the
  break did not fire, and that no output line contains the drivers
  directory's path.
- **The clone never moves.** After a re-exec run, the clone's HEAD, branch,
  index, `git status --porcelain` and `git worktree list` are what they were
  before.
- **A pin some weeks back.** The fixture origin carries a passed-marker ref
  for the newer commit (without one, rule 2b runs in place and the case
  passes vacuously). Asserts driver = G and data = the pin, both by hash.
- **CI's case.** A current clone and an ahead clone run in place.
- **The tables, row by row**, through `PRECEDENT_UPDATE_BOOTSTRAP_ONLY=1`:
  every lettered rule of item 2 and every numbered rule of item 3, including
  a dirty `tools/` and an untracked `*.py`.
- **Parallel cleanup.** A live holder, a separate process holding
  `fcntl.flock`, keeps its worktree through another run's cleanup. A dead
  leftover (worktree plus lock file, no holder) is removed.
- **No hook fires.** A `GIT_CONFIG_GLOBAL` whose `core.hooksPath` holds an
  executable post-checkout that touches a marker file, plus one in the
  fixture's `.git/hooks`; neither marker exists afterwards. Without that
  setup the case cannot fail on a CI runner, which has no global hooks path.
- **The journal and precedent.json.** A crash journal left mid-swap, plus a
  precedent.json declaring `upstream_branch: staging`: the bootstrap follows
  staging and the replay still restores the edits.
  `vendored_layer_paths(repo, ['precedent.json']) == []`, so a future
  `engine_paths` cannot put precedent.json in the journal silently.
- **The bootstrap is read-only.** Through the bootstrap-only seam, with a
  stand-in commit at HEAD and a journal present: the consumer's HEAD, index,
  journal directory, pin file, `git status --porcelain` and working-tree
  hashes are identical before and after.
- **No HEAD-sensitive call.** A `git` shim first on `PATH` logs the
  directory, `-C` and the arguments during the behind-clone case; no
  `symbolic-ref`, `branch --show-current`, `push`, `checkout` or `switch`
  targets the clone or the worktree.
- **The loop guard does not leak.** A child the re-exec'd run spawns does
  not see the loop-guard variable.
- **Fallback.** With the drivers directory not writable, the warning is the
  report's first line.

## Closes when

Two conditions, the second of which cannot be met on the day it lands:

1. the bootstrap, the re-exec, these cases and the runbook correction have
   landed on `main`; and
2. a real Update Vendors, run from a clone at or after the landing commit
   that is behind `origin/main` by at least one later commit touching
   `tools/`, runs the fetched code, names that commit, and leaves the
   clone's branch, HEAD, index and status as they were.

After the first, this item waits (`wait`) on such a later commit to `tools/`
and a real run over it.

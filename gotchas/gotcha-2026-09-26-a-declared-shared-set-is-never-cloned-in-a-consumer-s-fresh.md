---
slug:            gotcha-2026-09-26-a-declared-shared-set-is-never-cloned-in-a-consumer-s-fresh
status:          live
noted:           2026-09-26
severity:        notable
retired:         null
retires_when:    every consumer's tools/bootstrap.sh carries the "Clone every shared practice set" block, which declared-sources-are-cloned reports repo by repo
---
## Symptom

A consumer repo declares a shared practice set in `precedent.json`, on
purpose, and **the set is missing from every fresh container**. Nothing
at session start says so. `python3 tools/precedent_sync_views.py --check`
then reports dozens of differences in the loader block, and they all come
from one absent directory. Clone the set by hand beside the repo and they
drop to zero.

## Story

Reported 2026-09-26 from a session working in a private consumer: the
shared set `precedent-shared-repo-maintenance` was declared, was absent
from every fresh container, and `precedent_sync_views.py --check` showed 36
differences. After a hand clone it showed none. The same code was still
on `main` at `37fc3b5`.

The cause is how the session-start steps are divided between the kinds of
repo:

- The only session-start code that ran
  `tools/precedent_source_bootstrap.py --sources-from`, which clones every
  declared shared and universal source, was
  [precedent-universal-catalogue.sh](../templates/harness/claude-code/hooks/precedent-universal-catalogue.sh).
  That is the hook for practice sets.
- [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md)
  step 8 tells every consumer to decline that hook, because it is "for
  practice sets". Declining it looked free.
- The steps a consumer does wire clone only the individual set:
  `precedent-individual-bootstrap.sh`, `session-start.sh`, and
  [templates/bootstrap.sh](../templates/bootstrap.sh), which becomes the
  consumer's `tools/bootstrap.sh`.

BestPractice's own `tools/bootstrap.sh` had the clone step since
2026-09-21, and
[templates/harness/PARALLELS.md](../templates/harness/PARALLELS.md) says
"`tools/bootstrap.sh` clones the declared TEAM sources". That was true of
this repo's copy and false of the template every consumer gets. Nothing
compared the two for this step, and no check asked whether a declared set
had any way onto disk, so every check stayed green.

**Found while fixing it: the clone step could move a working copy's
branch.** `sources_from_repo()` puts an existing clone back on its pinned
branch before pulling. It did that to any checkout sitting at a declared
path, including ones it never made. BestPractice declares universal at
`.`, which is itself, and every practice set declares it at
`../BestPractice`, the session's own working copy. Measured on a scratch
repo declaring universal at `.`, clean, on a branch called `feature`: one
call left it on `staging`. The same call runs at every session start here
and from `precedent_resolve.py`'s self-heal mid-turn. That fits the
unexplained "HEAD moved onto the base branch" occurrences in
[gotcha-2026-09-25](gotcha-2026-09-25-a-session-rooted-above-every-repo-it-touches-gets-hooks-and.md)
and `precedent_session_check.py`. It is a plausible cause of them, and
nothing has confirmed it. Putting the clone step into every consumer's
session start without fixing this first would have spread it to every
consumer.

## Fix

- [templates/bootstrap.sh](../templates/bootstrap.sh) runs
  `precedent_source_bootstrap.py --sources-from .`, from `tools/` or
  `process/upstream/tools/`, before its loader-block check. A consumer on an
  unedited copy gets it through `Update Vendors`. An edited copy is
  reported DIVERGED with the block named, and needs the block added.
- [tools/precedent_check.py](../tools/precedent_check.py)'s
  `declared-sources-are-cloned` fails any repo that declares a shared or
  universal source outside itself and wires no session-start step that
  clones it. It follows SessionStart entries into the scripts they run.
  A repo that clones its sets another way declares so in
  `precedent.json`'s `source_clone_elsewhere`, with the reason.
- [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
  skips a source declared inside the repo, since that is the repo itself
  or a vendored copy, not a clone. It marks each clone it makes
  (`.git/precedent-source-clone`) and only ever switches a marked clone's
  branch. An unmarked checkout is pulled only when it already sits on the
  pinned branch. Otherwise it is left where it is.
- The migration spec's declined-adapters step now says what declining the
  catalogue hook gives up.

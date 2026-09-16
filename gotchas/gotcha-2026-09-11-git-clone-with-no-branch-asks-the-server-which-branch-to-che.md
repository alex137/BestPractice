---
slug:            gotcha-2026-09-11-git-clone-with-no-branch-asks-the-server-which-branch-to-che
status:          retired
noted:           2026-09-11
severity:        null
retired:         "2026-09-11"
retires_when:    null
---
## Symptom

`git clone` with no `--branch` asks the SERVER which branch to check out

## Story

<details>
<summary>The full entry as it stood until 2026-09-11</summary>

- **`git clone` with no `--branch` asks the SERVER which branch to check out,
  and the answer is a setting on a web page that nothing in this repository
  can see.** The remote's `HEAD` symref is whatever the repository's default
  branch is set to, and git follows it silently. 2026-09-09, measured from a
  consuming repo: two practice-source repositories had that setting pointed at
  a feature branch, so every session-start clone of those sources landed on an
  older tree. `precedent_sync_views.py --check` then reported the CONSUMER as
  drifted, and a plain sync would have written the older text over newer
  committed text — deleting a practice's whole `## Story` block and a clause
  of its Rule, with no warning and exit 0. **The consuming repo had never been
  stale; the clone had been pointed somewhere else.**
  **The second half is what made it persist**: `git pull --ff-only` pulls
  whatever branch the checkout is already on, so a clone that landed wrong
  once stayed wrong every session afterwards.
  **The trap for a reader is that this repository already forbids exactly this
  inference and the guard could not see it.** `precedent_check.py --only
  declared-base-branch` fails any tool resolving `refs/remotes/origin/HEAD`
  without reading a DECLARED branch first — six tools carried that bug and two
  were actively wrong. It reads Python, so it never saw a `git clone` making
  the same inference implicitly, on our behalf. **When a rule forbids asking a
  question, check whether something else is asking it for you.**
  Pinned since 2026-09-10:
  [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
  clones with an explicit branch and puts an existing clone back on it before
  pulling — declared `base_branch` if the source declares one, else `main`,
  never the remote's HEAD. It **refuses** rather than moving a clone that is on
  the wrong branch with uncommitted work in it, because that is somebody's
  working copy. And
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  reports an attached clone sitting off its branch at session start, since a
  pin only takes effect the next time something clones or pulls.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

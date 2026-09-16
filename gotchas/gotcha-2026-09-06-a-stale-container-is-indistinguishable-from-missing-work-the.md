---
slug:            gotcha-2026-09-06-a-stale-container-is-indistinguishable-from-missing-work-the
status:          retired
noted:           2026-09-06
severity:        null
retired:         "2026-09-06"
retires_when:    null
---
## Symptom

A stale container is indistinguishable from missing work; the freshness

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A stale container is indistinguishable from missing work; the freshness
  guard can be the thing that's lying; and the guard cannot save the very
  containers that most need it.** Three incidents, each one level deeper than
  the last. 2026-09-01: a session's local branch shared ZERO commits with
  origin, 51 merged commits invisible. 2026-09-06: a session started on a
  5-day-old shallow clone, 207 commits behind `precedent-beta-v01`, and
  concluded that [tools/precedent_check.py](../tools/precedent_check.py) and
  [.github/workflows/deep-check.yml](../.github/workflows/deep-check.yml) "did
  not exist" — they had landed days earlier;
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) stayed
  silent because its `git fetch` failed and it then compared the local commit
  against an unrefreshed remote-tracking ref: both were equally old, so
  nothing looked behind. Fixed then to warn when the fetch itself fails.
  **2026-09-06, the one that ended warning as a strategy:** a session came up
  366 commits behind, and the hardened freshness block *did run and could not
  help* — the container's copy of the hook was built 2026-08-31 and predated
  the block by six days. **A guard shipped inside the checkout it guards is
  missing from precisely the containers stale enough to need it.** The
  documentation failed identically: the AGENTS.md that session was handed had
  no gotchas section at all, so every entry here — including this one — was
  invisible to it. Warning was never going to be enough, because by the time
  a session could act on a warning the harness has already handed it a stale
  instructions file. The guard therefore **repairs**: on a clean tree that
  is strictly behind, it fast-forwards and says so, which makes the harness
  re-read the instruction files. Diverged, no-shared-history, and dirty-tree
  states still only warn — a hook that discards work is worse than any stale
  checkout. **That logic lives in
  [.claude/hooks/freshness-guard.sh](../.claude/hooks/freshness-guard.sh), and
  only there** — it briefly also sat inline in
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh), where the
  two ran back to back at every startup, fetching twice and racing to
  fast-forward the same branch; the inline copy is gone rather than kept in
  sync by hand. The guard is wired three times, because one firing point
  cannot cover the others: `SessionStart` (once, at the start),
  `PreToolUse` (once, before the session's first write) and
  `UserPromptSubmit` (the long-open-tab case — a tab open for hours that has
  already made its first edit is otherwise never rechecked). The
  `UserPromptSubmit` mode is throttled on a stamp file's mtime, so it costs
  ≈17ms and prints nothing inside its interval (default 600s,
  `git config precedent.freshness.intervalSeconds`); nothing polls and
  nothing runs between prompts. Its first version built the stamp path from
  `git rev-parse --git-dir`, which answers *relative* to the repo, so every
  write landed in the wrong directory, the throttle never engaged, and it
  re-checked on every prompt while printing a path error — use
  `--absolute-git-dir` for any path a hook will use from an unknown working
  directory. Two further fixes fell out of testing it: the freshness block was
  gated behind `CLAUDE_CODE_REMOTE=true` along with the `pip install`, so on a
  local machine it **never ran at all** (verified: total silence on all six
  test cases, including a failed fetch); and the old remedy it printed —
  `git checkout -B <branch> origin/<branch>` — was printed for a *diverged*
  branch too, where following it silently discards the local commits, because
  the check never distinguished "behind" from "behind and ahead". Before
  concluding that anything is missing or unfinished, still run
  `git fetch origin <branch>` and `git rev-list --count HEAD..origin/<branch>`
  yourself: the hook does not run for a repo attached mid-session (see the
  `add_repo` entry below).

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

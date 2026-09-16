---
slug:            gotcha-2026-09-07-the-commit-backstop-is-global-now-core-hookspath-so-it-reach
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

The commit backstop is GLOBAL now (`core.hooksPath`), so it reaches

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The commit backstop is GLOBAL now (`core.hooksPath`), so it reaches
  throwaway fixture repositories too — and refused them.** 2026-09-07, the
  third wrong-author incident in two days forced the scope up: a repo
  attached mid-session inherits the container's *global* identity (measured:
  `noreply@anthropic.com`), so a per-checkout SessionStart fix cannot cover
  it even in principle. Setting the identity globally, plus a backstop at
  `core.hooksPath`, is what reaches a repository that does not exist yet.
  The cost landed immediately: `verify_harness.py` builds dozens of
  temporary repos and commits in them without `TZ`, and the backstop
  refused the first one — `RuntimeError: git commit -qm base: commit
  refused: author-date offset is '+0000'`, the whole run down, in a
  mechanism that had nothing to do with what was being tested. **A fixture
  commit is not a person's commit**: the harness now sets
  `PRECEDENT_ALLOW_ANY_AUTHOR=1` once for every subprocess it spawns (the
  two checks that exercise the refusals pop it back out, so coverage is
  intact). Any other tool that creates scratch repositories and commits in
  them needs the same, and the symptom will not look like an identity
  problem.
  `core.hooksPath` also makes git look THERE AND NOWHERE ELSE, so the global
  hooks chain to each repository's own `.git/hooks/<name>` first — without
  that, every repo's own gates vanish silently. Resolve that path with
  `rev-parse --absolute-git-dir`, never `rev-parse --git-path hooks`: the
  latter *respects* `core.hooksPath` and so names the global directory,
  which made the chain look broken when it worked and a fixture look
  correct when it was planting its hook in the wrong place.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

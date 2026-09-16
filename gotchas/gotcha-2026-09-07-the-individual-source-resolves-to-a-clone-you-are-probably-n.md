---
slug:            gotcha-2026-09-07-the-individual-source-resolves-to-a-clone-you-are-probably-n
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

The individual source resolves to a clone you are probably not editing,

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The individual source resolves to a clone you are probably not editing,
  and it can be many commits stale.** `~/.config/precedent/config.json`
  names an absolute path, and on 2026-09-07 that path was
  `/root/precedent-individual` while every repo this session had attached,
  edited and pushed lived under `/home/user/`. Two clones of the same
  repository, and **everything that resolves the individual source at
  runtime reads the one in the config** — which was 6 commits behind, so it
  did not carry work committed and pushed an hour earlier from the other.
  It cost two separate confusions before the cause was found: a harness
  fixture that failed intermittently because it was reading that clone's
  freshness (not its own), and a SessionStart hook that installed one of the
  two commit hooks it should have, because the script it executed was the
  stale copy. Neither symptom pointed at a path. Check
  `python3 -c "import json,pathlib;print(json.load(open(pathlib.Path('~/.config/precedent/config.json').expanduser()))['individual']['path'])"`
  against where you are actually working, before concluding a tool is
  broken — and `git -C <that path> rev-list --count HEAD..origin/main` before
  trusting anything it produced. **The rule that resolves it, 2026-09-07:
  the config-named clone is `git pull --ff-only`ed from origin at every
  session start, so it can only ever be BEHIND — an attached sibling clone
  beside the repo you are working in is what a session actually edits and
  pushes from, and is the better evidence of what the source says.**
  [tools/verify_harness.py](../tools/verify_harness.py)'s
  `check_commit_identity_copies_are_identical` encodes exactly that
  preference; its first run reported drift against an uncommitted edit three
  directories away, which is the trap in miniature. **Do not read the next sentence as
  done everywhere.** A session on 2026-09-07 repointed the config at
  `/home/user/precedent-individual` and recorded that here as "resolved for
  this machine" -- but `~/.config/precedent/config.json` is a per-container
  file that no repository can carry, so a *different* container reading this
  paragraph still had `/root/precedent-individual` in its config, and the
  same paragraph's "nothing reads it now" was false there: everything reads
  exactly it. A fix that lives outside the repository cannot be recorded
  inside the repository as a state; only as a thing to check. **So check
  it**, with the command above, rather than trusting this. The saving grace
  when you find `/root/`: `precedent-individual-bootstrap.sh` pulls that
  clone `--ff-only` at every session start, so it is normally current in
  content even when it is the wrong path -- verified 2026-09-07, both clones
  at the same commit. What it will not have is uncommitted work in progress
  from the attached sibling, which is the case the preference above exists
  for.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

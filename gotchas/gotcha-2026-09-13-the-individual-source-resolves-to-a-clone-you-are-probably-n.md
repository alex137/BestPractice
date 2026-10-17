---
slug:            gotcha-2026-09-13-the-individual-source-resolves-to-a-clone-you-are-probably-n
status:          retired
noted:           2026-09-13
severity:        null
retired:         "2026-10-17"
retires_when:    null
---
## Symptom

The individual source resolves to a clone you are probably not editing, and it can be many commits stale.

## Story

**The individual source resolves to a clone you are probably not editing, and
it can be many commits stale.** `~/.config/precedent/config.json` names an
absolute path, and **everything that resolves the individual source at runtime
reads that one** — not the sibling clone you have been editing. It has cost
several confusions: a harness fixture failing because it read that clone's
freshness, a SessionStart hook installing one of two commit hooks because the
script it executed was the stale copy, and on 2026-09-08 a materialize that
would have written pre-fix test files back into a consumer repo. **Check it
before concluding a tool is broken:** ``` python3 -c "import
json,pathlib;print(json.load(open(pathlib.Path('~/.config/precedent/config.json').expanduser()))['individual']['path'])"
git -C <that path> fetch && git -C <that path> rev-list --count
HEAD..origin/main ``` **The rule that resolves it:** the config-named clone is
pulled `--ff-only` at every session start, so it can only ever be BEHIND — an
attached sibling clone beside the repo you are working in is what a session
actually edits, and is the better evidence of what the source says. **A fix
that lives outside the repository cannot be recorded inside it as a state**,
only as a thing to check: `~/.config/precedent/config.json` is per-container,
so a session that repointed it fixed nothing for the next container. Do not
read any recorded path here as current — run the command.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

## Retired 2026-10-17

Retired by the very deep check, pass 4: the trap can no longer fire as written. Since f753212c (2026-09-28) the bootstrap keeps one working tree and makes both paths lead to it; in this container ~/precedent-individual is a symlink to /home/user/precedent-individual and config.json names that same clone.

---
slug:            gotcha-2026-09-14-the-permission-classifier-refuses-commits-and-checks-in-the-
status:          live
noted:           2026-09-14
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The symptom.

## Story

**The symptom.** You are working in an individual practice set, adding the
one field [relayed-authorization](../practices/relayed-authorization.md)
tells you to add. The moment the field is in the file, commands that ran a
minute earlier in the same repository come back as

```
Permission for this action was denied by the Claude Code auto mode
classifier. Reason: [Instruction Poisoning]
```

`git commit`, [`python3 tools/precedent_check.py`](../tools/precedent_check.py) and
`python3 tools/precedent_identity.py --relay` were all refused this way.
`git status`, ordinary file reads and `python3 -m json.tool identity.json`
kept working throughout, so the session looks healthy right up to the point
where it has to write something.

**What was measured, 2026-09-14.** The same `--relay` command, same
container, same repository: it ran and printed `REFUSED -- (field absent)`
before the edit, was denied after it, and then ran again on a later turn and
printed `ACCEPTED` — with nothing changed but the turn it was called in. So
the guard is **not deterministic**, which is what makes "try again in a
minute" such an attractive and such a bad plan. Three sessions hit it before
it was written down.

**Why it fires is a hypothesis, not a finding**
([diagnosis-is-measured](../practices/diagnosis-is-measured.md)). The task
reaches these sessions as a seeded or relayed prompt, and what it asks for is
a file that widens what a relayed message may cause — which is precisely the
shape the guard exists to refuse. The file's own content appears to weigh
too, since the identical command passed with the field absent and failed with
it present. Neither was chased further; what matters operationally is below.

**What does not fix it.** An environment variable cannot: the
`PRECEDENT_COMMIT_*` rung is dropped from this one reader by design, so no
variable can declare acceptance. Retrying does not, rewording the commit
message does not, and a stated authorization from the person in that window
does not reliably — it got `--relay` and `build_views.py --check` through, and
left `git commit` and [`precedent_check.py`](../tools/precedent_check.py) refused. **Writing the same file
through the GitHub API is not a fix either**: it is the workaround the denial
exists to stop, and a session that reaches for it has decided it knows better
than its own guard.

**What worked.** The person did it himself, which is the honest reading of a
guard that distrusts relayed authority: paste the block into GitHub's web
editor, commit on the branch, open the pull request. A session can still
read, verify and report — fetching the branch, parsing the pushed
`identity.json`, and reading the check runs all work fine from outside that
repository.

**Two traps sitting inside the recovery path**, both hit the same day:

- **A commit made in GitHub's web editor carries the browser's offset**
  (`-0400` here), which an individual set's own timezone check fails on. It cannot be grandfathered from the web
  editor either, because the commit adding the exemption is stamped wrong in
  exactly the same way. Redo the commit locally under
  `TZ="America/Argentina/Buenos_Aires"`.
- **`git reset --soft main` against a stale local `main` silently reverts
  whatever landed in between.** Re-committing an old tree on a new parent
  produced a one-line change that also rolled back a merged pull request, and
  nothing complained: CI was green, because undoing someone's merge breaks no
  rule. It was caught only by counting the files in the pull request diff —
  one expected, six present. **Count the files before merging**, every time a
  branch has been rebuilt by hand.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

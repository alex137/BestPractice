---
slug:            gotcha-2026-09-13-addrepo-on-a-public-repository-attaches-nothing-and-never-re
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

`add_repo` on a PUBLIC repository attaches nothing and never reaches the cross-owner check, so testing that wall with `access: "read"` measures nothing at all.

## Story

**`add_repo` on a PUBLIC repository attaches nothing and never reaches the
cross-owner check, so testing that wall with `access: "read"` measures nothing
at all.** Asked on 2026-09-09 for read access to `alex137/bestpractice` from a
session rooted in a private practice-set repository owned by someone else, it
answered `"status":"read_available"` and *"Nothing was attached to the
session"*: the session's git proxy already serves anonymous clones of public
GitHub repositories, so the request short-circuits before any authorization
runs. **Read as a success, that says the cross-tier refusal above has been
lifted. It has not been** — the tool's own reply names `access: "push"` as the
path that runs the full repository-access checks, and warns in the same breath
that cross-owner attachments may still be refused. **The useful half is what
it hands you anyway**: a session rooted anywhere, under any owner, can
`GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1` this public repository with
nothing attached — which is how a session working in a private source set
reads the upstream tree.

**This entry said "allow ≈10 minutes" until 2026-09-14, and that figure does
not reproduce.** Measured on a hosted container that day, both clones landing
on `precedent-beta-v01` with all 116 practice files present: `--depth 1` took
**1 second** for 14 MB and 1 commit, and a FULL clone — which is what
[tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
actually runs for a universal source, with no `--depth` — took **3 seconds**
for 20 MB and all 1,394 commits. This repository is almost entirely prose, so
there is very little to transfer. Nobody knows what the ten minutes on
2026-09-09 was; a cold proxy and a Git Large File Storage (LFS) fetch are both candidates and
neither was measured. **What matters is not to cost a design decision against
it** — the ≈10 minutes was quoted in a 2026-09-14 session as the reason not to
put the universal catalogue in front of every session, and the real number is
three seconds (practice: diagnosis-is-measured — a relayed figure is a
hypothesis until this container measures it).

What that checkout cannot do: push, reach the GitHub tools (its web
application programming interface, and the Model Context Protocol server that
fronts it), or fetch Git Large File Storage objects.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

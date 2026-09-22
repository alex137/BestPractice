---
slug:            gotcha-2026-09-22-a-cross-owner-source-clone-fetches-fine-and-cannot-be-pushed
status:          live
noted:           2026-09-22
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A practice-source clone owned by somebody other than the session's own repo
owner **fetches perfectly and cannot be pushed**. The clone carries a working
credential helper, the token is in the environment, `git fetch` updates real
refs — and `git push` returns 403 from the git proxy.

## Story

Measured 2026-09-22 in a container rooted in `alex137/BestPractice`, against
`~/precedent-individual` (owner `themorgan`):

- The clone's own `credential.helper` is present and reads
  `PRECEDENT_GIT_TOKEN` from the environment. The variable is set.
- `git fetch origin main` — **succeeds**, and moves `origin/main`.
- `git push --dry-run origin HEAD` — *"access denied by the git proxy:
  themorgan/precedent-individual is not in this session's authorized
  repository set, so the proxy will not inject a credential for it"*, then
  HTTP 403.

**The asymmetry is the trap.** A working fetch looks like proof that the
credential is fine and therefore that the push failure must be something
else. It is not proof of anything: reads of that clone are served without the
proxy injecting a credential, and only the write path consults the session's
authorized repository set.

Two sessions diagnosed this in opposite directions within one day — one
concluding repository scope, the next "correcting" it to the token, each
citing real evidence for the half it had looked at. The measurement that
settles it is the dry-run push, because it authenticates and negotiates
without writing.

**There is no in-session route around it.** `add_repo` with `access: "push"`
answers:

> `add_repo: cross-tier adds are not supported in v1: requested
> "themorgan/precedent-individual" but session already has repos from
> owner(s) [alex137]. Start a new session with the requested repo as the
> initial source`

and a session takes one initial source, so no session can hold both.

## Fix

**Do not write a commit into a cross-owner source clone from here.** Probe
first — `git push --dry-run --quiet origin HEAD`, exit status only — and
where the answer is no, keep whatever needed recording somewhere this
container owns.
[tools/precedent_beta_watermark_check.py](../tools/precedent_beta_watermark_check.py)
does exactly that, and its `_can_push` docstring carries the reasoning.

**That file's own watermark moved out of the cross-owner clone entirely on
2026-09-22** — it is
[tools/beta_branch_watermark.json](../tools/beta_branch_watermark.json) here
now — so it is no longer the worked example of writing into one. The probe
stayed: a checkout that is offline, behind or diverged still cannot push, and
the wall this entry describes is unchanged for anything else that reaches
across owners.

**Its sibling trap is the API side of the same proxy**, filed the same day:
[the API proxy ignores the token you set](gotcha-2026-09-22-the-api-proxy-ignores-the-token-you-set.md).
There, `PRECEDENT_GIT_TOKEN` does not govern `api.github.com` calls at all —
the proxy supplies its own credential. Here it does govern the git path, and
is still not the thing that refuses. Same lesson from both ends: **the proxy
answers, not your header.**

**Reads are fine, so the clone still refreshes.** Nothing here argues for
treating that source as unreachable: the freshness guard fast-forwards it
normally, and the catalogue in force is read from a current tree. Only the
write path is walled.

**Work that genuinely has to land there needs a session rooted in that
repository** — the only shape that can push it.

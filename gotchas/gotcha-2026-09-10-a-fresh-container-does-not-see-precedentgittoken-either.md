---
slug:            gotcha-2026-09-10-a-fresh-container-does-not-see-precedentgittoken-either
status:          retired
noted:           2026-09-10
severity:        null
retired:         "2026-09-10"
retires_when:    null
---
## Symptom

Why it stayed wrong for three days.

## Story

**Why it stayed wrong for three days.** Each measurement correctly ruled out the explanation before it — "you set it after the container started" died to a container 40 seconds old, and "`PRECEDENT_*` is being filtered" died to a dump showing no user-defined variable of any kind. The remaining candidate was always "the platform does not pass them through", because **nobody thought to ask how many environments the account had.** `list_environments` answered it in one call: two, both named `Default`, identical descriptions, created 100 ms apart.

<details>
<summary>The full entry as it stood before 2026-09-10</summary>

  **First half of that report, 2026-09-09, and it is not about the token
  being wrong: setting the variable does not reach a session that is already
  running.** Morgan set `PRECEDENT_GIT_TOKEN` and, in the same conversation,
  a RESUMED session in the container that predated it measured **zero**
  `PRECEDENT_*` variables in its environment — not an empty token, not a
  rejected one, the whole family absent. So the credential path was neither
  confirmed nor disproved; it was never exercised. **The tool's `MISSING`
  line is indistinguishable in the two cases** — "you did not set it" and
  "you set it after this container started" print identically, which is
  exactly how a correct configuration gets read as a broken one.
  **Start a NEW session to test an environment change, and check
  `env | grep -c PRECEDENT` before concluding anything about the token
  itself.** Whether a valid token then works is still unmeasured; whoever
  gets one into a fresh session should record it here.

  **Second half, 2026-09-09, and it removes the comfortable explanation: a
  session in a BRAND-NEW container measured `env | grep -c PRECEDENT` as
  **0** as well.** `uptime` read `up 0 min`, the container's own init
  process was 40 seconds old at the first tool call, and Morgan had set
  `PRECEDENT_GIT_TOKEN` before that
  container existed — so "you set it after this container started" does not
  cover it, and neither does "start a new session", which is what the
  paragraph above tells you to do. **A fresh container does not see the
  variable either.** Where it stops is unmeasured: the environment
  configuration may not have saved it, or the runner may not pass
  `PRECEDENT_*` through to the session at all. **Go read the environment
  configuration itself before touching the token, the credential helper or
  `add_repo`** — all three are downstream of a variable that is not arriving.
  The session-start hook reported the whole downstream cost in the same
  breath: four private sources unresolved, universal catalogue alone.

  **Third measurement, 2026-09-09, and it is now two containers: a session
  rooted at a DIFFERENT repository, in its own brand-new container on the
  same environment, also measured zero.** Dumping every variable NAME (values
  stripped, so nothing secret is printed) showed only harness-provided ones —
  `CLAUDE_*`, `CCR_*`, the proxy and certificate-bundle settings,
  `GITHUB_TOKEN` — and **not one user-defined variable of any kind**. So this
  is not `PRECEDENT_*` being filtered out; nothing set in the environment
  configuration is arriving at all. **To tell "the variables do not arrive"
  from "the token specifically did not save", put a throwaway
  `PRECEDENT_PING=1` beside the token and start a NEW session.** If that
  throwaway variable is absent too, the fault is upstream of everything in this repository, and no
  amount of work on the token, the credential helper or `add_repo` will move
  it.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

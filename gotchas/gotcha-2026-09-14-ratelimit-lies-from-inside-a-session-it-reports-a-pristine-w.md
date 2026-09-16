---
slug:            gotcha-2026-09-14-ratelimit-lies-from-inside-a-session-it-reports-a-pristine-w
status:          live
noted:           2026-09-14
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The symptom.

## Story

**The symptom.** You want to know how much of the GitHub API allowance this
account has already spent, so you ask the endpoint built for exactly that.
It answers `core: 0 used of 15000`, with a reset always about an hour away,
and it answers that every time you ask — the reset moves forward on each
call. Nothing looks broken.

**What is actually true.** Measured 2026-09-14, seconds apart, on the same
credential in the same container:

```
GET /rate_limit                    -> "core": {"used": 0, "limit": 15000}
GET /repos/<owner>/<name>  headers -> X-RateLimit-Used: 74, Remaining: 14926
```

The headers on an ordinary call are correct and the endpoint is not. The
cause was not chased past establishing which of the two to trust — the agent
proxy sits between the session and GitHub, and `/rate_limit` is plainly not
being served the way the repository endpoints are.

**Why it matters more than an ordinary wrong number.** A budget check built
on that endpoint is green on the day the account runs out, which is the one
day it exists for — the same shape as the stale `views-drift` header that
claimed something was already failing the build. It was nearly built that
way here. [tools/github_budget.py](../tools/github_budget.py) reads
`X-RateLimit-*` off calls it was making anyway, never the endpoint, and
[tools/precedent_check.py](../tools/precedent_check.py)'s
`github-api-budget` check fails if anything goes back.

**Two more things the same session established**, both surprising and both
load-bearing:

- **There is more than one allowance pool, keyed by repository.** A call
  about the public upstream repo was charged to a 15,000/hour pool; calls
  about two private sources to two separate 5,200/hour pools with their own
  reset clocks. The harness attaches a per-repository credential, so "how
  much is left" is a question about a repository, not about the account.
- **`/search/*` and `/graphql` never reach GitHub from a container.** The
  proxy answers `403 This GitHub API path is not available: sessions are
  bound to their configured repositories`. So the tightest allowance on the
  account — search, at 30 requests a MINUTE, shared by every session at once
  — cannot be measured from where its refusals are felt, and the calls that
  spend it come from the harness-side `mcp__github__*` tools.

**Do not "fix" a rate-limit refusal by retrying.** The pool is shared by
every window running; the lever is fewer simultaneous sessions and cheaper
tools (the local clone before the API, a repo-scoped `list_*` before a
`search_*`). Practice:
[github-api-budget](../practices/github-api-budget.md).

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

---
slug:        github-api-budget
title:       GitHub API spend is measured, budgeted, and read off the headers
tier:        on-demand
severity:    default
applies_to:  ["tools/github_budget.py", "tools/github_api_budgets.json", "**/*github*.py"]
occasion:    "writing or changing anything that calls the GitHub API, or a session is refused with a rate-limit error"
gates:       []
index_clause: "measure API spend from response headers; budget each tool; never /rate_limit"
checked_by:  "tools/precedent_check.py"
defines:     ["API budget", "allowance pool"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "pending review -- written 2026-09-14 after Morgan reported a GitHub rate-limit error and asked what in normal usage was causing it (strength: assented, the rule's shape is the session's proposal and not his instruction; what he asked for was the investigation, the fixes, and the very-deep-check section)"
---
## Rule
**Every tool that calls the GitHub API knows what it spent, and says so.**
One counter, in the one place the call is actually made
([tools/github_budget.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/github_budget.py)),
and a per-tool budget it is compared against in one registry
([tools/github_api_budgets.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/github_api_budgets.json)).
A tool whose bill grows quietly is how a shared allowance gets spent by
something nobody was watching.

**Read the allowance off the `X-RateLimit-*` headers of a call you were
making anyway — never from `/rate_limit`.** Measured 2026-09-14 from inside
a session: the endpoint reported a pristine window (`0 of 15000`, reset
always an hour out) while the headers on an ordinary call, seconds later on
the same credential, reported `74` spent. A check built on the endpoint is
green on the day the account runs out, which is the one day it exists for.

**There is more than one pool, and which one a call spends is decided by
which repository it names.** Same session, same credential variable,
2026-09-14: a call about the public upstream repo was charged to a
15,000/hour allowance, and calls about two private sources to two separate
5,200/hour allowances with their own reset clocks. "How much is left" is a
question about a repository, not about the account, and a single number
answering it is the wrong number.

**Nobody owns a pool alone.** Every session, hook and tool on the same
credential draws on it, so the one that gets refused is rarely the one that
spent it. **The lever is fewer simultaneous sessions and cheaper tools**, not
a retry.

**What to do instead of spending an allowance is
[grep-before-search](grep-before-search.md)'s** — the clone on disk first, a
repo-scoped `list_*` before a `search_*`, and fewer windows working at once.
This practice measures and budgets the spend; that one is the habit that
keeps it low, and the two are not repeated into each other.

**Report, never refuse.** A tool that stopped because somebody else's session
had spent the pool would be the wrong remedy for the right finding.

## Detail
**What a session cannot measure is said out loud, not left as a clean-looking
zero** ([fail-gracefully](fail-gracefully.md)). From inside a container the
agent proxy binds a session to its configured repositories and answers `403
This GitHub API path is not available` for `/search/*` and `/graphql` before
the request reaches GitHub. So the two allowances most likely to be the cause
of a refusal cannot be probed from where the refusal is felt, and the calls
that spend them are made by harness-side `mcp__github__*` tools that the
container cannot meter at all. They are declared in the registry with
GitHub's published figures, dated, and reported as **not measurable here** —
never omitted, which reads as clean.

**Secondary limits are invisible everywhere.** GitHub publishes them (80
content-creating requests per minute, 500 per hour, read 2026-09-14) and
exposes no counter for them: they are known only by the 403 they eventually
return. Several sessions each opening pull requests, posting review replies
and merging is the shape that reaches them, and no amount of local
instrumentation will see it coming. The registry records them so the next
session reading an opaque refusal has the candidate list in front of it.

**The very deep check reads the budget last, and reports it as a section**
([very-deep-check](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/very-deep-check.md)). Last, because the run's own spend is
only complete once every section that calls the API has finished — and the
headroom figure costs nothing extra, because it is read off the headers those
calls already returned rather than bought with one more.

**A floor is a decision, and it carries its reason in the registry**
([constants-are-risk-inputs](constants-are-risk-inputs.md)). The `core` floor
is 20% remaining: on a 15,000/hour pool that is 3,000 calls of headroom, more
than a day of this project's own measured tooling spend, and early enough
that a person sees the finding before anyone sees a refusal. Move it with a
reason written beside it.

## Install
[tools/github_budget.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/github_budget.py)
is the one place this engine asks GitHub anything: it authenticates, caches
within a run, counts the calls, and keeps the `X-RateLimit-*` headers per
pool. It travels with the vendored engine, so a repo that has the check has
the remedy. Run it on its own —
`python3 tools/github_budget.py [--tool NAME] [--json]` — for the headroom
alone.

The registry is
[tools/github_api_budgets.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/github_api_budgets.json),
and it is each repo's own declaration rather than a vendored file: `floors`
(percent of an allowance that must still be remaining), `run_budgets` (calls
per run, per tool), `unmeasurable` (allowances nothing here can see, with
GitHub's published figure and the date it was read), and `unrouted_callers`
(a tool that calls the API directly, with the reason it cannot be routed).

`python3 tools/precedent_check.py --only github-api-budget` runs the
mechanical half in any repo the engine is vendored into. It enumerates every
tracked `.py` that both builds an API URL and sends it, and reports any that
is neither routed through the module nor declared with a reason; it also
fails on a registry with no `core` floor, a budget for a tool that no longer
exists, an unmeasurable entry with no reason or no date, and on anything
going back to reading `/rate_limit`. A repo that calls the API and declares
no registry at all is the finding, not a skip. A repo that calls the API
nowhere gets a named NOT APPLICABLE.

Per-run spend and headroom print as the last section of
[very-deep-check](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/very-deep-check.md).

## Why
A rate-limit error arrives as one sentence with no number in it, and every
answer to "what caused it" is a guess until something has been counting.
Nothing here was counting: no tool reported its own API calls, no file
declared what any of them should cost, and the one endpoint that looks like
the answer lies from inside a session. The cheapest fix is not a cap — it is
a figure, printed where somebody already reads.

## Story
**2026-09-14.** Morgan reported getting a GitHub rate-limit error out of a
session and asked what in normal usage was causing it. Everything measured
that day is above; what the measuring turned up is that the obvious
instrument was broken and the obvious suspect was innocent.

`/rate_limit` was the first thing consulted, and it answered `0 of 15000`
with a reset exactly an hour away — on a token that had made several dozen
counted calls minutes earlier. The same credential's ordinary calls carried
`X-RateLimit-Used: 74` in their headers at that instant. Had the check been
built on the endpoint, as it nearly was, it would have shipped green and
stayed green.

The core pool was never the problem: 133 of 15,000 spent account-wide in the
window when the investigation ran, with three sessions live and a day's worth
of pushes behind it. Workflow runs were not it either — 75 runs in one hour
on the busiest repository, all of them spending the per-repository `GITHUB_TOKEN`
allowance that CI has to itself, none of them touching the account pool.

What is left is the two things a session cannot see: `search`, at 30 requests
a minute shared by every window at once, and the content-creating secondary
limit, which no counter anywhere reports. That is an honest "the most likely
candidates are these", not a diagnosis, and it is written down as one
([diagnosis-is-measured](diagnosis-is-measured.md)). The lasting fix is that
the next occurrence arrives with a number beside it.

The same run found the small waste worth fixing while it was open: 45 API
calls in one very-deep-check run with no cache behind them, and a
repository-metadata answer re-asked whenever two trees name the same repo.

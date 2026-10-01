---
slug:        grep-before-search
title:       The clone on disk answers first — GitHub's search API is the scarce call
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus, and deliberately `**`. What the rule governs is a session's choice of TOOL in the moment it goes looking for something -- a local grep against a GitHub search call -- which happens before any file is opened and leaves no artifact in the tree at all. There is no path whose editing means the choice was made badly, so a narrower glob would only make the rule invisible at the moment it fires. Decided: 2026-09-14, when the practice was written."
occasion:    "about to search a repo, every clone or every file, or use a GitHub tool for what the clone holds"
gates:       []
index_clause: "grep the clone first; list before search; never sweep every clone unasked"
index_required: true
checked_by:  null
defines:     ["search allowance"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "Morgan, 2026-09-14 (strength: decided) -- shown the lever as a
  candidate individual practice at the close of the rate-limit investigation,
  he asked for it written and levelled up: \"Yes, write that practice, but it
  should be a universal practice, not an individual one. Go merge.\"
  Absorbed wide-search-needs-asking (Morgan, 2026-09-28, decided) on
  2026-10-01, in the reduction pass Morgan approved that day: \"Question 3 -
  all are great, approved\" (strength: decided)."
strength:    decided
---
## Rule
**Grep the clone.** A session working in a repository already has its whole
tree on disk. Reading a file, finding a symbol, listing what changed, seeing
who last touched a line — every one of those is a local command that costs
nothing and answers faster than the API does. **Reach for a GitHub tool only
for what is not on disk**: another repository, a pull request's comments,
CI's verdict, what someone said in a review.

**When you do ask GitHub, ask the narrow question.** A repo-scoped
`list_*` before a `search_*`; one call that names the thing before a query
that goes hunting for it. **`search` is 30 requests a MINUTE (as of 2026-09),
account-wide, shared by every session open at that moment** — the tightest
allowance on the account by a wide margin, and about eight times tighter
than the 15,000-an-hour pool (250 a minute) it is easy to mistake it for.

**A wide search waits for the person's explicit go-ahead.** Wide means its
reach is everything: every clone on disk, every repository, every file in
them, a whole fleet. **Do the cheap thing instead, and say it in one line:**
fix the source you already know, tell the person a full sweep would not be
worth its cost, and ask them to send an example if they see the problem
again. **A wide search already running without that go-ahead is stopped** as
soon as it is noticed, and so is any background job nothing is waiting on
any more.

**The other lever is how many windows are working at once.** Allowances are
shared across sessions, so the fifth simultaneous session is not five times
as productive — it is the one that gets refused, or that refuses somebody
else. **When a rate-limit refusal appears, the question is what else is
running**, not what to retry.

**A refusal is never answered with a retry.** The allowance is spent; asking
again spends more of it and, on the secondary limits, extends the block.
Find the local answer instead, or wait for the window to reset —
[tools/github_budget.py](https://github.com/alex137/BestPractice/blob/staging/tools/github_budget.py)
says when that is.

**This does not license searching less.**
[search-by-purpose](search-by-purpose.md) asks for two searches before
concluding nothing exists, and that still holds in full. This rule is about
**where those searches run**, never about doing fewer of them: a local grep
is the cheap one, so there is no tension to resolve — search more, search
locally.

## Detail
**Where a wide search starts.** A grep of the repository you are working in,
or of the one or two repositories the work names, is ordinary work. The line
is reach: once the search goes through repositories the task never named,
just to be thorough, it needs asking. **Explicit means the person asked for
this sweep**, in words that name its reach. "Fix it everywhere" authorizes
fixing the places you know of, not a hunt through every clone for places you
don't. The requests that already carry a sweep by definition, a
[very-deep-check](very-deep-check.md) or a
[full-practice-audit](full-practice-audit.md), are that explicit ask. For
example: *"That sweep isn't worth the tokens. I've fixed the source I know
of; if you see it again, send me the example."*

**What is actually on disk, and worth naming because sessions forget it.**
The full history, so `git log`, `git blame`, `git show` and `git diff` answer
questions about who changed what and when. Every file at every commit, so a
file's content at some older revision needs no API call either. Every branch
the clone fetched, and `git ls-remote` names the ones it did not. What is
NOT there: anything that lives in GitHub's own database rather than in git —
issues, pull-request bodies and reviews, check runs, labels, releases.

**A file read from another repository in the session is still local.** The
harness clones the repositories a session is bound to; `precedent.json`'s
declared sources are directories on the same disk. `cat` beats
`get_file_contents` for all of them, and it beats it by more than the
allowance — there is no rate limit on the filesystem, and no pagination.

**From inside a container the search API is not merely expensive, it is
closed.** The agent proxy answers `403 This GitHub API path is not
available: sessions are bound to their configured repositories` for
`/search/*` and `/graphql` before the request reaches GitHub. So a `curl` to
the search endpoint cannot be what spends the allowance: the spend comes
from the harness-side `mcp__github__search_*` tools, which run outside the
container and are exactly the ones a session reaches for without thinking.
The thing to change is the reflex, because nothing local will stop it.

**This is a rule about the cheapest read, not a ban.** A search that answers
a question nothing local can answer is the right call, and one search beats
twenty file reads that guess at where something is. The failure this
prevents is the other shape: searching a repository that is sitting on disk.

## Why
A shared allowance has no owner, so nothing pushes back on the session
spending it — the cost lands on whoever asks next, usually in another
window, as an error with no number in it. The discipline has to come from
the read being genuinely cheaper, which it is: the local answer is faster
and more complete, and the allowance it saves was never yours alone.

A wide search looks responsible, and it is usually the wrong trade. The
known source is already fixed, so the sweep only hunts for copies that may
not exist. Copies that do exist surface on their own: the next update brings
the fix, or the person sees the problem again and says so. That costs one
sentence, and the sweep costs minutes of waiting and a large pile of tokens.

## Story
**2026-09-14.** Morgan was refused by GitHub with a rate-limit error and
asked what in normal usage was causing it. The measuring
([github-api-budget](github-api-budget.md), and `record/GOTCHAS.md#g41` for
the trap it nearly fell into) cleared the obvious suspects: the account's
ordinary REST pool was at 133 of 15,000 in the window, with three sessions
live, and the workflow runs — 75 in the busiest hour on the upstream repo —
spend a per-repository allowance that continuous integration (CI) has to
itself. Neither was it.

What was left was `search`, at 30 requests a minute shared by every open
window, and the secondary limit on creating content. Both are invisible from
inside a session, and both are reached the same way: several windows at once,
each using the tools that feel free. That made the remedy a habit rather than
a mechanism, which is why this is a practice and not a check — shown as a
candidate at the close of the investigation, and levelled up to universal the
same hour, because nothing about it is specific to this project, this team or
this person.

**2026-09-28, the wide search.** A session fixed the Boildown so it stopped
asking which repositories to add or remove. It then started a background
search of every cloned repository for other wordings of that question, and
left it running long after the fix had landed. Morgan waited on it, asked
whether the question was that important, and had it stopped; it had found
nothing. His words: *"We never want to do a search like that unless I
explicitly authorize it - every clone ever every file etc - a lot of time and
energy and tokens. ... Here you could have said, 'Morgan, that isn't
token-efficient at all; I've stopped asking that question, and if you happen
to find an example or it happens again, tell me' - that would have been
1000x better than all the tokens and time and wait."* That became
wide-search-needs-asking (strength: decided).

**Merged here, 2026-10-01.** Both rules are about how to search cheaply, at
the same moment, so the reduction pass Morgan approved that day folded
wide-search-needs-asking in as the wide-search paragraph of the Rule, its
reach line in Detail and its reasoning in Why. Its file stays as the record;
the rule in force is this one.

## Install
Nothing to install. The figure behind it is printed by
[tools/github_budget.py](https://github.com/alex137/BestPractice/blob/staging/tools/github_budget.py),
and the very deep check's GITHUB API BUDGET section reports it every run.

**Deliberately not mechanically checked, and the reason is specific rather
than "too hard"** ([checkable-gets-checked](checkable-gets-checked.md)). The
only form of this a script could see in a tree is a tool that calls
`api.github.com/search/` — and that is already covered from two directions:
such a caller is an undeclared API caller under
[github-api-budget](github-api-budget.md)'s check, and the proxy refuses the
endpoint outright from a session, so the case is close to unreachable. The
real subject is a session choosing a search tool over a local command in the
moment, which leaves no artifact anywhere for a check to read. A check that
can never fire would be worse than none: it would report coverage of a rule
nothing is watching.

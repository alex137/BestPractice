---
slug:            gotcha-2026-09-22-the-api-proxy-ignores-the-token-you-set
status:          live
noted:           2026-09-22
severity:        major
retired:         null
retires_when:    "a hosted session's outbound proxy stops mediating api.github.com, or starts forwarding the caller's own Authorization header -- test it with the invalid-token probe below rather than assuming"
---
## Symptom

A GitHub application programming interface (API) call from a hosted session
is refused — `Resource not accessible by integration`, or the harness's own
`GitHub access to this repository is not enabled for this session` — and the
obvious diagnosis is that `PRECEDENT_GIT_TOKEN` needs more permission. A
session then designs a token: which scopes, who creates it, where it goes.

**None of that changes anything, because the token is not what answers.**

## Story

2026-09-22, costing out the very deep check's proposed required-status-check
section. `GET /repos/{owner}/{repo}/branches/{branch}/protection` returned
`Resource not accessible by integration`, and this session reported to its
user, twice, that the fix was a credential with `Administration: Read`. It
then wrote step-by-step instructions for creating a fine-grained personal
access token (PAT).

Asked which repositories needed it, the session finally measured instead of
reasoning:

| Probe | Result |
|---|---|
| `GET /user` with the real `PRECEDENT_GIT_TOKEN` | `login: themorgan` |
| `GET /user` with a **deliberately invalid** token | `login: themorgan` |
| `GET /user` with **no** `Authorization` header at all | `login: themorgan` |

Unauthenticated `GET /user` against real GitHub is a `401`. Getting a real
login back proves the request never reached GitHub carrying what the caller
sent: **the session's outbound proxy mediates `api.github.com` and supplies
its own credential**, a GitHub App installation — which is what GitHub means
by *integration* in that refusal.

Two consequences follow, and both had already produced wrong answers:

1. **`PRECEDENT_GIT_TOKEN` does not govern API calls from a hosted session.**
   It still governs `git clone` and `git fetch` of private sources, which go
   through the credential helper on a different path. The two look like one
   credential and are not.
2. **A refusal is about the App installation's permissions and the session's
   repository scope**, neither of which any environment variable can widen. A
   call to a repository outside the session's scope is refused by the harness
   before GitHub sees it — which is why that message is phrased in the
   harness's words rather than GitHub's.

[`tools/github_budget.py`](../tools/github_budget.py)'s own docstring says it *"AUTHENTICATES WHEN A
TOKEN IS SET"*. That is true of the code and false of the outcome here, and
a session reading it has every reason to believe the token is the lever.

## Fix

**Run the probe before diagnosing any GitHub API refusal as a token
problem.** Three calls, seconds apart:

```sh
python3 -c "import sys;sys.path.insert(0,'tools');import very_deep_check as v;print(v._api_json('user')[0].get('login'))"
PRECEDENT_GIT_TOKEN=github_pat_invalid python3 -c "import sys;sys.path.insert(0,'tools');import very_deep_check as v;print(v._api_json('user')[0].get('login'))"
```

**If both print the same login, the header is being ignored** and no token
you set will change any API answer. Report the limit as the session's own
GitHub access — the App installation and the repository scope — and stop
designing a credential.

**Two failures read alike and are not alike.** GitHub's own wording
(`Resource not accessible by integration`, with a `documentation_url`) means
the call reached GitHub and the App lacks that permission. The harness's
wording (`not enabled for this session`) means it never left. Quote which one
you got; they have different remedies and only one of them is GitHub's.

**The git path is the same proxy with a different answer**, filed the same
day: [a cross-owner source clone fetches fine and cannot be
pushed](gotcha-2026-09-22-a-cross-owner-source-clone-fetches-fine-and-cannot-be-pushed.md).
There `PRECEDENT_GIT_TOKEN` genuinely does govern clone and fetch — and the
push is still refused by the proxy's own repository scope, not by the
credential. Reading only one of these two entries leaves the token looking
like the lever from whichever side you arrived on.

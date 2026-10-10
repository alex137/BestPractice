---
slug:            gotcha-2026-10-10-github-mcp-invalid-session-use-gh-api-rest
status:          live
noted:           2026-10-10
severity:        notable
retired:         null
retires_when:    "the GitHub tools stop failing with invalid session in cloud sessions, or the landing steps stop needing a pull request"
---
## Symptom

In a Claude Code cloud session, every GitHub tool call fails with
"invalid session": creating a pull request, listing them, merging one. The
Promote and Produce steps say to open a pull request and merge it "with the
merge tool", and there is no tool that works.

`gh pr create` and `gh pr list` fail too, with "HTTP 403: GitHub GraphQL is
not available from Claude Code sessions; use the REST API".

## Story

2026-10-10, a consuming repository's Update Vendors session. Every GitHub
tool call failed with "invalid session". The session got its pull requests
open and merged through `gh api`, GitHub's REST API, which the session's
proxy serves. `gh`'s higher-level commands use GraphQL, and the proxy
refuses GraphQL from these sessions by policy. The same day, in another
cloud session, the GitHub tools worked, so the failure comes and goes.
REST and the GraphQL refusal were measured in that second session.

## Fix

When the GitHub tools fail, use REST through `gh api`. Never use `gh pr ...`:

    # open the pull request the Promote named
    gh api repos/OWNER/REPO/pulls -f title="Promote staging into main" \
        -f head=BRANCH -f base=main -f body="..."
    # merge it at the head commit the Promote printed, all 40 characters
    gh api -X PUT repos/OWNER/REPO/pulls/NUMBER/merge \
        -f merge_method=merge -f sha=FULL_40_CHARACTER_SHA

A short `sha` is refused, the same as with the merge tool. Then check that
main moved (`git fetch origin main` and `git merge-base --is-ancestor`),
as after any merge.

---
title:         "Plan: Commit Identity Resolution"
kind:          proposal
status:        executed
opened:        2026-09-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "A claim that BestPractice needs a different commit identity than the person running it — for GitHub's verified badge — turns out to match no documented practice here and no property of how GitHub verification actually works. This retires that direction before it was built, and specifies the model that replaces it: one self-declared identity, sourced from the authenticated GitHub account when nothing is declared, with the fallback saying so instead of staying silent."
---
# Plan: Commit Identity Resolution

**Implemented.** `commit-identity.sh` (both copies) now closes the loop
described below: it already says which of the six sources it used, and now
says explicitly, when that source was inferred rather than declared, that
telling Claude a name and email makes it permanent. The one remaining item
— confirming whether the session's authenticated GitHub account and the
signing key's account are the same — is an empirical check, not a blocker,
and is unchanged from the "Before Writing Any Code" section below.

## The Problem, in One Paragraph

[.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh)
resolves who a commit is from at every SessionStart, and the fix for a
GitHub verified-badge mismatch had been getting redone by hand, every
session, because nothing persists across a fresh container unless it's
either committed or set at the environment level. The fix under discussion
before this proposal was a **repo-scoped override** — a `commit_identity`
key in this repo's own [precedent.json](../precedent.json), read as a new
rung in the resolution chain, applied locally only so it wouldn't leak into
`precedent-individual`'s own Morgan-authorship convention. That direction is
dropped here, not refined — see below.

## Why It's Dropped, in One Paragraph

**No practice, ruleset, or doc anywhere in this repo ever required
BestPractice to use a different commit identity than the person running
it.** Searched [practices/](../practices/), every doc,
[record/GOTCHAS.md](../record/GOTCHAS.md), and the repo's own
branch-protection checker
([tools/precedent_boundary_check.py](../tools/precedent_boundary_check.py))
— nothing. The claim traces to one session's own stated reasoning, relayed
once, never checked against how GitHub verification actually works: the
**Verified** badge is scoped to *(a signing key) ↔ (the GitHub account it's
registered to) ↔ (that account's verified emails)* — never to which
repository a commit lands in. The same key, signing with the same committer
email, verifies identically everywhere or nowhere. A requirement that
differs by repository isn't something that mechanism can produce. What's
real is narrower and person-level, not repo-level: **the committer email
has to be a verified email on the account the signing key belongs to.**
That's a fact about an account, not about BestPractice.

## The Model

Three steps, checked in order. This collapses the existing multi-source
chain in `commit-identity.sh` rather than adding a rung to it.

1. **An explicit self-declaration, if one exists.** The person told Claude
   directly — "call me Morgan in commits" — or it's already written into
   their individual source's `identity.json`. Wins outright, every repo, no
   exceptions, no per-repo split.
2. **Otherwise, the GitHub account the session is authenticated as.**
   **Name** — `profile.name || profile.login`, used as-is. Name carries no
   verification requirement at all, so there's nothing to weigh here —
   GitHub's badge never inspects it. **Email** — the account's public
   email, or its `id+login@users.noreply.github.com` fallback, which
   GitHub already treats as verified for that account.
3. **Otherwise, guess, and say so.** Fall back to whatever's already
   configured locally (never the container's bot identity) — and tell the
   person, once per session, that nothing is declared and commits are
   running on a guess, so they can fix it permanently via step 1 if they
   want to.

**The actual new piece is narrow.** Steps 1 and 2 mostly already exist in
`commit-identity.sh` today. What's missing is step 3's second half: today a
fallback guess is applied silently and never mentioned again. The fix is
making that guess speak once, and persisting the answer into `identity.json`
the moment someone gives one — closing a loop that's open today, not adding
a new one.

## Why This Probably Also Closes the Original Wall

Not certain — one assumption still worth checking, not worth blocking on.

Step 2's email is, by construction, already verified *for the account the
session is authenticated as*. If that account is the same one the signing
key is registered to, the verified-badge problem this proposal started from
resolves on its own — no manual "add a verified email" step needed at all.

That "if" is the one thing this proposal doesn't confirm by itself:
**whether the session's authenticated GitHub account and the signing key's
registered account are actually the same account.** Cheap to check — look at
whether a recent commit already shows **Verified** on GitHub for this
identity. Worth doing once. If they turn out to differ, the fix is still a
one-time GitHub settings action (a verified email, or a registered signing
key, on the right account) — not a change to this model.

## Implementation Steps

| Step | Where | What |
|---|---|---|
| 1 | [.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh) | Collapse the resolution chain to the three steps above. Step 2's GitHub-account lookup already exists (today's rung 5) — promote it, don't rewrite it. |
| 2 | same file | Add the "nothing declared, running on a guess" notice — printed once per session, not once per commit. |
| 3 | same file | When a person declares an identity conversationally mid-session, write it into their individual source's `identity.json` so step 1 picks it up from then on, in every repo. |
| 4 | [templates/harness/claude-code/hooks/commit-identity.sh](../templates/harness/claude-code/hooks/commit-identity.sh) | Vendored copy — carries the same change, per this repo's own fix-the-original discipline. |
| 5 | [tools/precedent_identity.py](../tools/precedent_identity.py) | Update the docstring's description of the resolution order if it still describes the old multi-rung chain. |
| 6 | [record/GOTCHAS.md](../record/GOTCHAS.md) | One entry: the "BestPractice needs a different identity" claim was a misdiagnosis — GitHub verification is account-scoped, not repo-scoped — so the next session doesn't rediscover this the hard way. |

## Explicitly Not Changing

- `identity.json`'s other uses — pronouns, relayed-authorization, CI
  preference — untouched, out of scope here.
- Rung 2 of the current chain (a repo's own root `identity.json` meaning
  "this repo is an individual source") — still correct for repos like
  `precedent-individual`; not what caused this problem, not being touched.
- Any repo-scoped override mechanism — dropped entirely, not built in a
  reduced form.

## Before Writing Any Code

Confirm the assumption in "Why This Probably Also Closes the Original
Wall" — check one existing commit's Verified/Unverified status on GitHub
for the account this session pushes as. If it's already verified, this
plan needs no changes. If it isn't, the fix is still a one-time GitHub
settings action, not a change to this plan.

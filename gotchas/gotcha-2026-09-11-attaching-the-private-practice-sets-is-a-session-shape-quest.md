---
slug:            gotcha-2026-09-11-attaching-the-private-practice-sets-is-a-session-shape-quest
status:          retired
noted:           2026-09-11
severity:        null
retired:         "2026-09-11"
retires_when:    null
---
## Symptom

Attaching the private practice sets is a session-shape question, and what is measured about it does not add up

## Story

<details>
<summary>The full entry as it stood until 2026-09-11</summary>

- **Attaching the private practice sets is a session-shape question, and what
  is measured about it does not add up — so measure, do not reason.** Three
  separate 2026-09-07 measurements had `add_repo` refusing a cross-owner add
  in BOTH directions with *"cross-tier adds are not supported in v1"*,
  including as a session's very first tool call. Two other sessions —
  2026-09-07 and 2026-09-08 — held `alex137/bestpractice` and four or more
  `themorgan/*` repositories at once, worked in and pushed to all of them.
  **Nobody has an explanation that fits both.** Do not build on either
  outcome and do not repeat an attempt expecting a remembered result: call
  `add_repo`, read what it says, and proceed from that.
  What is NOT in doubt is the cost of skipping it, and it is the entry above:
  a session with `individual` and `team` unresolved applies the wrong rules
  all day and cannot tell. If the adds are refused, **root the session in the
  repo you must PUSH to** and expect the other owner's repositories to be
  unattachable for its whole life — that is why work spanning both owners is
  split across two sessions. The full contradictory sequence is in the
  archive; read the verdict there before any single paragraph of it.

  **2026-09-09 adds one measurement that is not contradictory, and one route
  that does not depend on `add_repo` at all.** The refusal was reproduced as
  a session's very FIRST tool call, rooted at `alex137/bestpractice` — so
  "call it before anything else" is not a remedy: the initial repository
  already counts as *"session already has repos from owner(s)"*. Three other
  things were measured in the same container. An authenticated HTTPS request
  to github.com **reaches GitHub's own authentication** rather than a proxy
  error. There is **no ambient credential** for a private repo (a bare
  `git ls-remote` on one asks for a username; the same call on a public repo
  succeeds). And the credential helper in
  [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py)
  **does deliver** a token to git — with a deliberately invalid one, git sent
  it and GitHub rejected it rather than prompting. **So set
  `PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL` in the environment
  ([INSTALL.md](../INSTALL.md) §8) and the SessionStart hook clones the sources
  before the first turn, where no ordering rule can reach it.** **Verified end to end
  2026-09-10**: a real read-scoped token in the environment, and a brand-new
  container came up with all four private sources cloned before the first
  turn — [tools/precedent_resolve.py](../tools/precedent_resolve.py) reported 146 practices
  from 6 sources (41 team, 13 individual) in a repo that had been resolving
  89 from 1. That tool prints `MISSING` when no credential is set and `SET`
  when one is set and a clone still failed, and the session check, the
  session-start source report and every vendor update print the same line.

  **The trap that made this look impossible for three days, and the only
  live half left: an account can hold TWO environments with the SAME NAME,
  and the selector gives you no way to tell them apart.** Measured 2026-09-09
  and 2026-09-10 — three sessions across two fresh containers reported
  `env | grep -c PRECEDENT` as **0**, with not one user-defined variable of
  any kind in a full name dump. That reads exactly like "the runner does not
  pass them through", and it is not that: `list_environments` showed **two
  environments both named `Default`**, same description, created 100 ms
  apart. The variables were set on one; the sessions ran in the other.
  Setting the same values on both fixed it in a single session. **Not
  established:** whether the twin was the whole cause or the first save had
  also failed — both fit what was measured, and nobody re-ran it to find out.
  **So: give your environments distinct names**, and put a throwaway
  `PRECEDENT_PING=1` beside the token — the ping separates "the variables do
  not arrive" from "the token is wrong", which print identically otherwise.
  An environment change never reaches a session already running, so test in a
  NEW one. The three-day sequence, including two readings that were right
  about the measurement and wrong about the cause, is entry 29 in
  [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md).

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

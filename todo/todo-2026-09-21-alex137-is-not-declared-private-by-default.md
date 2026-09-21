---
slug:              todo-2026-09-21-alex137-is-not-declared-private-by-default
kind:              manual
domain:            security
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        Alex
noted:             2026-09-21
closed:            null
---
## What

**This public tree links a private repository, and the check whose whole job
is preventing that never asked.**

`WHERE_THINGS_ARE.md` names `alex137/GitAround` and links it. Measured
2026-09-21 against the GitHub API: the repository exists, `full_name` is
exactly as written, and `private` is **true**. So the link 404s for every
reader outside the account, and the name of a private repository sits in a
tracked file of a public one.

## Why nothing asked

The repository-reference allowlist inverts the default for a declared
owner: under a `visibility-audit: private-owner <owner>` line, every
`owner/name` mention is refused unless an `allow` line gives a reason. That
inversion is the whole design — the set of names you may mention is small
and known, the set of repositories you might create is unbounded.

**`themorgan` is declared. `alex137` is not.** So no `alex137/*` reference
has ever been asked about, and `GitAround` passed for the same reason a
thousand other names would: the owner was never declared, so the question
was never put.

## What makes this a decision rather than a fix

Declaring `alex137` private-by-default is one line, and it immediately
refuses every mention of **`alex137/BestPractice`** — which is this
repository, named throughout its own public tree. That is correct
behaviour, and it needs an `allow` line with a reason, exactly as the
`themorgan` team sets have.

The placement is the other half, and it is not obvious:

- **`tools/leak-blocklist.default.txt`** ships to every consumer. `alex137`
  is BestPractice's own owner; a consumer has no reason to carry that
  declaration, and putting it there imposes it on everyone.
- **A root `leak-blocklist.txt` in this repo**, which does not exist yet.
  Creating one is the structurally right answer and a new surface: this
  repo has until now had no blocklist of its own, relying on the shipped
  default plus whatever private set a session resolves.

## The question

For **Alex**, since it is his account and his repository:

1. Should `alex137` be declared private-by-default, accepting that every
   mention of `alex137/BestPractice` then needs a stated allow?
2. Is the existing `GitAround` mention accepted (an `allow` line with a
   reason) or removed? Note that removing the link does not unpublish the
   name — it already appears in this tree's eval fixtures as well, so the
   exposure is a decision to ratify or reverse deliberately, not something a
   single edit undoes.

My recommendation is yes to (1), in a new root `leak-blocklist.txt`, and
`allow` for both names — the exposure is already real, and an allow line
with a reason is the mechanism for saying so out loud rather than leaving it
unasked. Until it is decided, `WHERE_THINGS_ARE.md`'s row now states
plainly that the repository is private, so a reader who hits the 404 knows
why.

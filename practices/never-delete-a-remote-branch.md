---
slug:        never-delete-a-remote-branch
title:       Never attempt to delete a branch on the remote
tier:        on-demand
severity:    default
scope:       any-adopter
applies_to:  ["**"]
occasion:    "a branch has done its job -- a pull request merged, a tidy-up, or a person saying to delete some branches"
gates:       []
index_clause: "never attempt a remote branch delete; hand over the one-click link"
index_required: true
checked_by:  null
defines:     []
command:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-21"
approved_by: "Morgan, 2026-09-21 (strength: decided) -- asked for in his own
  words, as a rule strong enough that a session does not try a second route
  after the first one fails: \"NEVER TRY TO DELETE A BRANCH ON GITHUB...
  have a very very very strong practice to forbid you from even trying to
  delete a branch via github.\" Authorized: \"Go update.\" The list of
  forbidden routes and the local-branch carve-out are the session's, not
  dictated."
strength:    decided
---
## Rule
**Do not try to delete a branch on the remote. Not once, not as a retry, and
not by a different route after the first one failed.** A session running in
Claude Code on the web cannot remove a remote ref — this is settled, measured,
and not worth one more token of anybody's budget.

**Every one of these is forbidden**, listed by name so nobody rediscovers them
one at a time:

- `git push origin --delete <branch>`, and its older spelling
  `git push origin :<branch>`
- the GitHub Model Context Protocol (MCP) server — it ships `create_branch`
  and **no delete counterpart at all**, so there is nothing to call
- the REST or GraphQL API by hand — `curl`, a fetch tool, a throwaway script
- a GitHub Actions workflow written, edited or dispatched to do it
- handing it to a subagent, a spawned session or a workflow — they carry the
  same credential and get the same refusal
- pushing a scratch branch "to check whether deleting works now"

**Two things stay perfectly fine.** Deleting a **local** branch in the
session's own clone (`git branch -d`, `git branch -D`) touches no remote and
is ordinary housekeeping. And GitHub's own **Delete branch** button, clicked
by a person, works normally — that is the whole point of the link the next
paragraph requires.

**What to do instead, every time: hand over the one-click link and move on.**
[branch-delete-links](branch-delete-links.md) has the exact form. Say it once,
flatly, as a recommendation — *"`claude/foo` is merged and safe to delete:
\<link\>"* — and never as an apology, never as an offer to do it, and **never
as something blocking.**

**This is a capability limit of the environment, not a transient and not a
permission this repository can grant.** If it ever changes it will change
because a person says so, not because a session tested it again.

## Detail
### Why the failure reads like a network blip

`git push origin --delete` fails like this — what the first line calls a
remote procedure call (RPC) is git's own push negotiation over HTTPS
([the measurement, 2026-09-14](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-09-14-a-session-can-push-branches-but-cannot-delete-a-remote-branc.md)):

    error: RPC failed; HTTP 403 curl 22 The requested URL returned error: 403
    send-pack: unexpected disconnect while reading sideband packet
    fatal: the remote end hung up unexpectedly

**The second and third lines are what make this expensive.** They are the
symptoms of a dropped connection, so the obvious reading is *retry* — and the
retry produces the same three lines, which then reads as a flaky remote rather
than a settled answer. Only the first line says what actually happened, and it
is the one that scrolls past first. That is why the rule is *never attempt*
rather than *stop after a failure*: the failure does not look like a stop sign.

**It is a capability limit, proved by running both halves back to back.** The
delete failed twice; an ordinary `git push -u origin <new-branch>` in the same
working tree, seconds later, succeeded and printed the pull-request URL. The
credential carries write access to *create* refs and not to *remove* them.

### There is no switch to turn it on

Asked directly, 2026-09-21: **no setting in Claude Code on the web enables
remote branch deletion, and none of the routes above is a configuration
problem a repository can fix.** The MCP server exposes no delete tool to
enable; the push refusal is the scope of the credential the session is handed,
which is decided where the GitHub App's access is granted, not in this
repository, not in `.claude/settings.json`, and not by a permission allowlist.
Nothing here is waiting on somebody flipping something.

### Do not probe it

The obvious test — push a scratch branch to prove pushes still work — leaves
behind a branch that, by the very limit being tested, **cannot then be
removed.** The session that first measured this did exactly that and added
`claude/push-capability-probe` to a remote permanently. A probe for this
capability is the one experiment whose failure case is worse than not knowing.

## Why
**The cost is tokens, time and credibility, in that order.** A session that
tries the push, retries it, reaches for the MCP server, writes a `curl`, and
then proposes a workflow has spent real budget arriving at an answer that was
already written down — and it has spent it on the person's turnaround, not
just its own.

**The credibility half is worse than the waste.** A session that offers *"say
the word and I'll delete those branches"* is promising something it cannot do,
and the person finds out only when they take it up. Offer the link. The link
is a thing that works.

**This is not a rule against deleting branches.** Merged branches should be
deleted, and a repository that accumulates them is worse off for it. The rule
is only about *who clicks*: a person, in one click, from a link the session
already had everything it needed to build.

## Story
**2026-09-21.** Morgan, unprompted, out of repeated frustration:

> NEVER TRY TO DELETE A BRANCH ON GITHUB. This is a very frustrating one I
> want you to fix please. GitHub in Claude Code Cloud can not delete branches.
> [...] But every time over and over you keep on trying to delete a branch
> this way than another way etc -- you waste so many tokens and times trying
> something that WE KNOW WILL NOT WORK.

**The knowledge already existed and was never routed.** The limit was measured
on 2026-09-14 and written up as an environment gotcha, with the 403, the
back-to-back proof, and the abandoned probe branch. A gotcha is found by
grepping for a symptom you are already staring at — which is exactly the wrong
shape for this failure, because the symptom reads as a network blip and a
session hitting it is not looking for a catalogue entry, it is looking for
another route. Seven days and an unknown number of repeat attempts later the
rule got written as a rule.

**"Another way" is the load-bearing phrase in his complaint.** A single
prohibition on `git push --delete` would have been satisfied by a session that
went straight to the API instead. That is why the routes are enumerated above
rather than left to judgment: the failure mode being fixed is not one bad
command, it is the search that follows it.

## Install
Nothing to install — this is a rule a session applies, routed by its line in
the occasion index, which every session loads before it works.

**Related:** [branch-delete-links](branch-delete-links.md) — the link form to
hand over instead, and the rule that deletion is never blocking;
[the-boildown](the-boildown.md) — item 5, where a safe-to-delete branch is
reported;
[durable-fix](durable-fix.md) — why this landed as a committed rule rather
than as one more session knowing better.

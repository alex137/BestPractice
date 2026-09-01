---
slug:        no-rewrite-for-warnings
title:       A tool's warning never justifies rewriting published history
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a tool warns about already-published git history"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 31
---
## Rule
When a hook, linter, badge, or CI check complains about commits that
are **already published** — on the shared trunk, or authored by someone else —
the response is to fix the setting **forward** and leave the history alone.
Configure the identity, the tool, or the exemption so future commits are clean;
do not rebase, amend, or force-push to satisfy the warning. Rewriting published
history is reserved for an explicit human instruction, never inferred from a
tool's output.

## Why
These warnings are written as if every commit they see is yours and
still local, and the remedy they suggest — `rebase --exec ... --amend` — is
accurate for that case and catastrophic outside it. On a shared trunk it
rewrites commits other people authored and already built on, forces a divergent
default branch, and trades a cosmetic badge for a genuine coordination failure.
The asymmetry is total: the warning's cost is that something looks untidy, and
the suggested fix's cost is that everyone else's clone is now wrong.

The trap is that the tool is *correct about the condition* and merely silent
about the context. It is right that the commits lack the property; it does not
know they are published, does not know which are yours, and cannot weigh what
its remedy costs. An agent reading such output is being handed a confident,
specific, executable instruction with the reasoning omitted — the shape most
likely to be followed without the judgement the situation actually needs.

Generalise past the specific tool: any automated warning whose suggested remedy
is *destructive and retroactive* — rewriting history, mass-reformatting a
shared tree, regenerating a lockfile everyone pins, bulk-editing files a check
flags — gets the same treatment. Satisfy it forward, exempt what is already
published, and escalate to a human if the backlog genuinely matters. A warning
is a report, not an authorization.

## Story

## Install
Set the identity or configuration the tool wants, so new work stops
triggering it. Where the tool supports it, scope the check to unpublished or
own-authored commits. Record the decision — including the count of pre-existing
items deliberately left alone — next to the merge or release runbook, so the
next person sees a resolved question rather than an unexplained backlog and
re-litigates it. If the tool has no scoping option and the noise is persistent,
that is a request to file against the tool, not a reason to act on it.

**Related.** [mistakes-become-rules](mistakes-become-rules.md) (mistakes become rules) — this is the abstracted form
of a rule a dependent repo added after a session was one command away from
rewriting a shared trunk to clear a signature badge on commits it did not own.

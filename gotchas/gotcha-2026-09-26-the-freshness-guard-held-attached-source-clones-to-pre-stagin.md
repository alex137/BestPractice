---
slug:            gotcha-2026-09-26-the-freshness-guard-held-attached-source-clones-to-pre-stagin
status:          live
noted:           2026-09-26
severity:        notable
retired:         null
retires_when:    every practice set and consumer has refreshed its vendored freshness-guard.sh past the commit that lets a declared base win for attached repositories
---
## Symptom

The first tool call of a session is refused, and so is every call after
it except plain `git` commands:

> BLOCKED by freshness-guard (first tool call of this session): 'main' is
> missing 7 commit(s) from origin/pre-staging

The project directory is fine. The `main` it names belongs to an
**attached practice source**, a clone sitting on `main` exactly where it
should be. Edits are blocked too, because the guard's `pre-write` mode
matches Edit and Write as well as Bash.

## Story

2026-09-26, twice in one session with four sources attached through
`PRECEDENT_FRESHNESS_ALSO`. Each entry declares its base
(`~/precedent-individual=main`), but `_resolve_base()` asked
`precedent_branches.py --landing` first. That returned the person's landing
branch, `pre-staging`, and the declared `main` was ignored. A source's
`pre-staging` is ahead of its `main` by design until someone runs Promote,
so every session that attached a source with unpromoted work was blocked.

The remedy the guard names (`git merge origin/pre-staging` into the
source's local `main`) would put unpromoted practice text in front of the
session, and leave local commits on `main` that must never be pushed. The
override it names (`git config precedent.freshness.override true`) was
refused as a safety bypass until the person approved it for that checkout.

## Fix

In [.claude/hooks/freshness-guard.sh](https://github.com/alex137/BestPractice/blob/staging/.claude/hooks/freshness-guard.sh),
and the template copy: an attached repository's declared base wins over
the landing branch. Nothing this session writes lands on an attached
source, so the person's landing branch says nothing about it. The project
directory keeps the landing override, since work written there does land
on pre-staging. Both halves are asserted in
`check_freshness_guard_checks_attached_repositories`.

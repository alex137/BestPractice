---
slug:              todo-2026-09-21-commit-identity-reaches-some-sessions-and-not-others
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**`commit-identity.sh` reaches some sessions and not others, and the
commits that landed say which.** Found by the very deep check's new
`IDENTITY REALITY` section on its first run, 2026-09-21 — the section exists
because nothing had ever read what landed rather than what is configured.

Measured over 30 days in this checkout, 1,217 commits:

| Author date offset | Commits |
|---|---|
| `-03:00` — the declared timezone | 900 |
| `+00:00` | 278 |
| `-04:00` | 39 |

**Two unlike failures sit inside those 317**, and the author field
separates them:

1. **The identity never applied at all** — 235 commits at `+00:00` and 9 at
   `-04:00` are authored as `Claude <noreply@anthropic.com>`, not as the
   person. Those sessions got neither the author nor the offset.
2. **The identity applied and the offset did not** — 43 at `+00:00` and 30
   at `-04:00` are authored as the declared person carrying an offset that
   is not their timezone at that moment. This is the field the hook either
   enforces or merely guesses at, and the guess was wrong.

`-04:00` is the sharper of the two values: the declared zone has not been
`-04:00` since 2009, so nothing about a real clock produces it.

## Why it is filed rather than fixed

**The commits are past tense and rewriting history to fix them is worse
than the wrong offsets.** What is worth deciding is forward: which
sessions do not get the hook, and whether that is the harness (a
non-Claude-Code adapter with no hook mechanism, per
[templates/harness/PARALLELS.md](../templates/harness/PARALLELS.md)), a
container that starts before the hook runs, or a path the hook declines.
The section now reports it every run, so the answer is measurable rather
than remembered — and a fix will show up as the count falling.

**The one repo in force that declares its own identity came back clean**,
which is evidence about the mechanism rather than about that repo: where
an identity is declared, the hook enforces instead of guessing, and the
offsets are right.

## What would close it

Establish which session shapes produce a `Claude <noreply@anthropic.com>`
author here — that is the larger half and the cheaper one to diagnose,
since the author name says the hook did not run rather than that it ran
badly. Then re-measure against the same section and record the count in
the same place.

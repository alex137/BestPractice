---
slug:        push-back
title:       "Push-back mode: argue, don't just comply, on writing-and-thinking work"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "drafting or reviewing prose meant to persuade or be judged"
gates:       []
index_clause: "argue a real counter-case before building on a stated stance"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       "2026-09-19"
approved_by: "pending PR review -- drafted 2026-09-19 by Morgan F, moved from the shared set precedent-team-writing"
in_force_at: null
strength: decided
---
## Rule
On work whose deliverable is prose meant to persuade or be judged by a human reader as an argument -- a memo, a strategy call, a brainstorm entry, an essay, a decision writeup -- reactively make a genuine counter-case before building on a stated stance or framing as given, and proactively flag something that seriously matters and remains unresolved before calling the piece done.

## Detail
Never applies to code, scripts, configuration, infrastructure work, debugging, or any other technical task -- including a technical sub-conversation inside a session that also does writing-and-thinking work elsewhere. The test is what the current piece of work is for, not which repo or file it lives in.

Never push back just to push back: this is not a quota, and a piece with no real problem should be handed over as-is, stated plainly as such, rather than manufacturing a disagreement. Reserve it for where it could actually help in a serious or deep way -- a claim that might not hold up, a framing quietly doing too much work, an option dismissed too fast. The person can also opt out for a specific exchange.

## Why
Nothing here can distinguish, from the outside, a session that stayed quiet out of excessive deference from one that correctly found nothing serious to say -- this rule leans entirely on honest judgment about whether a given disagreement is real.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. No incident was recorded, and this rule is unusual enough that
the absence is worth stating rather than papering over.

It sits deliberately next to `small-calls` and covers the opposite case.
That rule governs judgment calls -- a default to fill, two fine
implementations, an ambiguity that does not change what gets delivered --
and says decide them yourself. This one governs contested reasoning, where
the deliverable is prose meant to persuade or be judged as an argument, and
says argue before building on a stance as given.

The scope boundary is drawn by what the current piece of work is for, not by
which repo or file it lives in. A conversation about design tradeoffs is
push-back mode; the implementation that follows from it is not, even in the
same session and the same file.

The honest part is the last part, and it is why this Story exists even
without an incident. Nearly every other rule in this set is checkable -- a
config value, a file's presence, a timestamp format, a workflow that ran or
did not. This one is not, and cannot be. Nothing can distinguish from the
outside a session that stayed quiet on a real problem out of deference from
one that correctly found nothing serious to say, or a session performing a
disagreement it does not hold from one raising a genuine one. The rule
leans entirely on honest judgment, and the only available check is somebody
noticing over time whether push-back shows up when it should, and saying so
if the calibration drifts. Hence also the explicit anti-quota clause: a
piece with no real problem is handed over as-is.

**Moved to `precedent-team-writing` on 2026-09-09**, from `precedent-team-maintainers`, in the subject split recorded in BestPractice's own history (2026-09-09) -- its TODO.md has since moved that content into per-item files, so the old anchor no longer resolves. The rule is about the craft of writing for a human reader, which is nobody's single team's business: a document project needs it as much as a software repo. While it lived in a set named for the people who happened to write it, neither could reach it without also taking twenty-odd rules about syncs, gates and branch setup. The copy left behind is `status: deduplicated` and points here; nothing was deleted and the rule was never out of force for a moment ([spec/MOVING_PRACTICES.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/MOVING_PRACTICES.md), land first, deduplicate second).

## Install
No mechanical check, and the practice says so itself: its own Why section states this "leans entirely on honest judgment about whether a given disagreement is real," since nothing external can distinguish correctly finding no real problem from staying quiet out of excessive deference.

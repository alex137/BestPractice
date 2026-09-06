---
slug:        merge-authorization-keyword
title:       A standing merge-authorization keyword
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "the user gives a standing merge instruction"
gates:       ["merge"]
index_clause: "one fixed word means \"merge as agreed\"; document it exactly"
checked_by:  null
defines:     ["go merge"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 45
---
## Rule
A repo can adopt one short, fixed word or phrase that, said as
its own final sentence in an otherwise-ordinary message, means "commit and
merge what we just agreed on, using this repo's usual conventions, without
asking again." Document the exact word, and the exact rule for what counts
as "standing alone" (its own line, or set off by a preceding
sentence-ending punctuation mark; case-insensitive), in the repo's
`GLOSSARY.md` next to the other terms that mean something specific here.
Treat an ambiguous case — the word appears, but as part of a longer
sentence, or its standalone status is genuinely unclear — as *not*
authorization: ask, rather than assume.

## Detail
This repo's adopted phrase is **"Go merge"** (case-insensitive). Standing
alone — its own line, or set off by a preceding sentence-ending
punctuation mark — it authorizes committing whatever change the thread
just agreed on and pushing it to `precedent-beta-v01` (this repo's normal
merge target; see the TEMPORARY note at the top of `AGENTS.md`), after the
usual light and deep checks. Appearing only as part of an ordinary
sentence, or whose standalone status is genuinely unclear, does not
count — ask instead of assuming.

The push is not the postcondition — [verify-postcondition](verify-postcondition.md)
is: after pushing, fetch the target branch and confirm local `HEAD` and
`origin/precedent-beta-v01` resolve to the same commit, independently of
what the push command printed, before treating "Go merge" as fulfilled.
A push that silently rejected, or a target branch that moved again in the
interval, both look identical to success unless this is actually checked.

## Why
"Merge only when the user says so" ([merge-runbook](merge-runbook.md)'s authorization
default) is the right default, but typed out in full every time it's
invoked, it adds friction to the single most common approval a working
session asks for. A one-word standing trigger removes that friction
without weakening the default: it is still the human choosing, in the
moment, to say the word: the rule only fixes what a specific short
utterance is understood to authorize, so an agent never has to guess
whether "sounds good" or "yes" meant "and merge it" too. The strict
standalone-sentence test is what keeps the keyword from misfiring inside
ordinary language that happens to contain the same word for an unrelated
reason.

## Story
Morgan closed two consecutive messages with "Go merge" before this
keyword was formally adopted, the second one making the intent explicit
("register it in the glossary... And then, Go Merge"). Formalized here,
in the same change, rather than left as an inferred pattern — so the next
session that sees the phrase already knows what it means instead of
re-deriving it from context or asking. The same day, Morgan asked whether
the keyword should also require confirming the push actually landed —
prompted by nothing having gone wrong yet, just the observation that a
push being reported as successful and the target branch actually holding
that commit are two different things this repo had already been bitten by
once (see `environment-gotchas`' stale-checkout entries). Added to Detail
rather than left as something a session happens to remember to do.

## Install
Pick a word (or short phrase) that reads naturally as a
one-word reply and isn't likely to appear as ordinary language at the end
of an unrelated sentence — "go" or "merge" are typical choices. Add it to
`GLOSSARY.md` with the standalone-sentence rule spelled out, and cross-link
it from the merge runbook ([merge-runbook](merge-runbook.md)) and from the "administrator
requests" section of `AGENTS.md`, so a session encountering the word for
the first time in a thread already knows where the rule lives instead of
inferring it from context.

---
slug:        merge-authorization-keyword
title:       A standing merge-authorization keyword
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "the user gives a standing merge instruction"
index_clause: "one fixed word means \"merge as agreed\"; document it exactly"
checked_by:  null
defines:     []
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

## Why
"Merge only when the user says so" (practice 9's authorization
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

## Install
Pick a word (or short phrase) that reads naturally as a
one-word reply and isn't likely to appear as ordinary language at the end
of an unrelated sentence — "go" or "merge" are typical choices. Add it to
`GLOSSARY.md` with the standalone-sentence rule spelled out, and cross-link
it from the merge runbook (practice 9) and from the "administrator
requests" section of `AGENTS.md`, so a session encountering the word for
the first time in a thread already knows where the rule lives instead of
inferring it from context.

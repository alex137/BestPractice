---
slug:        wide-search-needs-asking
title:       A search across every clone or every file waits for the person's say-so
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "about to search or scan every clone, every repo or every file for something"
gates:       []
index_clause: "never sweep every clone unasked; fix the known source, ask for an example"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "Morgan, 2026-09-28"
strength:    decided
---
## Rule
**Never start a wide search without the person's explicit go-ahead.** Wide
means its reach is everything: every clone on disk, every repository, every
file in them, a whole fleet. Such a search takes minutes, spends tokens on
every result, and the person often waits on it.

**Do the cheap thing instead, and say it in one line.** Fix the source you
already know. Then tell the person a full sweep would not be worth its cost,
and ask them to send an example if they see the problem again. For example:
*"That sweep isn't worth the tokens. I've fixed the source I know of; if you
see it again, send me the example."*

**A wide search already running without that go-ahead is stopped** as soon
as it is noticed. So is any background job nothing is waiting on any more.

## Detail
**What stays allowed without asking.** A grep of the repository you are
working in, or of the one or two repositories the work names, is ordinary
work ([grep-before-search](grep-before-search.md)). The line is reach: once
the search goes through repositories the task never named, just to be
thorough, it needs asking.

**Explicit means the person asked for this sweep**, in words that name its
reach. "Fix it everywhere" authorizes fixing the places you know of, not a
hunt through every clone for places you don't. The requests that already
carry a sweep by definition, a [very-deep-check](very-deep-check.md) or a
[full-practice-audit](full-practice-audit.md), are that explicit ask.

## Why
A wide search looks responsible, and it is usually the wrong trade. The
known source is already fixed, so the sweep only hunts for copies that may
not exist. Copies that do exist surface on their own: the next update brings
the fix, or the person sees the problem again and says so. That costs one
sentence, and the sweep costs minutes of waiting and a large pile of tokens.

## Story
**2026-09-28.** A session fixed the Boildown so it stopped asking which
repositories to add or remove. It then started a background search of every
cloned repository for other wordings of that question, and left it running
long after the fix had landed. Morgan waited on it, asked whether the
question was that important, and had it stopped; it had found nothing. His
words: *"We never want to do a search like that unless I explicitly
authorize it - every clone ever every file etc - a lot of time and energy
and tokens. ... Here you could have said, 'Morgan, that isn't token-efficient
at all; I've stopped asking that question, and if you happen to find an
example or it happens again, tell me' - that would have been 1000x better
than all the tokens and time and wait."* He asked for it as a practice in
the same message. (strength: decided)

## Install
Nothing to install. The occasion index lists it, so it reaches a session
before a search starts.

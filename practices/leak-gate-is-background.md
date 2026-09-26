---
slug:        leak-gate-is-background
title:       The leak gate is background machinery — never bring it to the person
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a leak gate, blocklist, or scrub result is in front of you, or you are about to mention one to the person"
gates:       ["push"]
index_clause: "never relay a blocklist note or ask for a term; the deep review is its place"
index_required: false
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-13"
approved_by: "Morgan, 2026-09-13, choosing universal from the two readings the open item
  laid out -- \"Yes, make this one universal.\" It landed 2026-09-12 in his individual
  set and moved here under
  https://github.com/alex137/BestPractice/blob/staging/spec/MOVING_PRACTICES.md
  -- land at the destination first, deduplicate at the source second."
strength:    decided
source_practice_number: null
---
## Rule
**A leak gate and its blocklists are machinery the person wants running and
does not want to hear about.** A session **never** surfaces a routine gate
note, never proposes a term or a stem for a blocklist, never asks whether
something should be added, and never offers to add one. **A term goes on a
blocklist only when the person says to add it**, in those words.

Two things this does not cover, and both still get said plainly:

- **A real hit.** A gate failing a push is a finding, not a reminder — say
  what it caught, and stop.
- **The deep review.** [very-deep-check](https://github.com/alex137/BestPractice/blob/staging/practices/very-deep-check.md)'s
  repository-visibility pass is where the recommendations belong, and its
  `RECOMMENDATION:` lines are meant to be read there.

**This is about what a session SAYS, not about what runs.** Nothing here
weakens a gate, skips one, empties a list, or makes a refusal quieter.

## Detail
**The silence has to be built, not just asked for.** A rule that tells
sessions not to mention something the tooling puts in front of them on every
run is a rule that will be broken, because the note is cheap to print and a
session that sees a warning relays it. So the note **moves** rather than
switching off: the gate stops printing its routine survey in the ordinary
run and keeps printing it where the deep review asks for it. Trading the
noise for a blind spot is the one version of this that is not worth having.

**Whether the survey is quiet is a per-person setting, and this rule does not
decide it.** In this engine the blocklist itself carries the directive, so a
person who *wants* those notes on every run leaves them on and is not in
violation of anything. What the rule governs is what a session does with
whatever the gate printed.

**The risk the notes were about is better covered by a refusal than by a
question.** Where the machinery can turn a latent gap into a hard hit — a
private repository's bare name becoming a pattern in its own right, so that
naming it fails the push — that is strictly better than asking the person
whether to add it, because **a refusal needs no decision from them.** Prefer
building the refusal over raising the question, every time.

**What the gate cannot see is still worth saying once, in the right place.** A
missing stem is latent risk rather than a leak: the content scan covers what
the tree says today, and the deep review asks the network what is actually
private. Nothing is lost by hearing about it there.

## Why
**Every one of these notes is cheap to print and expensive to receive.** The
gate prints on every run, so a session sees it on every run, and relaying it
comes with a recommendation attached — which is a decision handed to the
person. Three of those in a day is not three seconds of their time; it is
three interruptions in work that had nothing to do with blocklists.

**The cost of the opposite failure is small and covered elsewhere**, which is
what makes the trade honest. This would be a bad rule if the notes were the
only thing standing between a private term and a public tree. They are not:
the gate still runs, still refuses, and the deep review still asks.

**The general shape worth taking from it:** a protection whose *interface*
interrupts is not a protection working well. Silence the telling, keep the
gate, and move the recommendations to the moment the person is already in the
mindset to read them.

## Story
**2026-09-12.** A session finishing an unrelated fix relayed the gate's stem
note at the end of its reply and offered to add a stem. Morgan: *"I feel like
I keep on getting errors and warnings and questions about it ... I just want
to ignore it, UNTIL I tell you explicitly to add something to a blocklist."*

**He first asked whether the blocklists could simply be blanked.** They
could — the cost being that his account handle, an account number and his
private repository names would go unguarded into a public repository — and he
took the narrower fix instead when it was laid out: silence the interface,
keep the protection, move the recommendations into the review. *"That way, I
still get these suggestions -- but only when I ask for it as part of a very
thorough review."*

**Worth recording because the premise was wrong in an instructive way**: he
had read the blocklist as somebody else's feature. It was his own, and what it
guarded was his own vocabulary in somebody else's public repository. **A rule
that silences a protection the person believes belongs to someone else is a
rule written on a misunderstanding** — this one was written after the
misunderstanding was cleared, which is why it silences the telling and not the
gate.

**It landed at individual level and moved here on 2026-09-13**, which is the
half that concerns every adopter rather than one person. The open item asking
the question recorded two readings that disagreed: the nuisance is not
personal, since any repository with a private blocklist prints the same note
on every run and any session will relay it — against which what a person wants
to be interrupted about is exactly what an individual set exists for. Morgan
chose universal: *"Yes, make this one universal."* The deciding argument is in
the Rule's own first carve-out — **a real hit is always sayable**, so what the
rule suppresses is unsolicited machinery chatter, and nobody wants that. A
person who does want the notes turns them on in their own blocklist, which the
mechanism already supports.

## Install
Nothing to configure for the rule itself, and the occasion index entry is
generated, so every session reads it.

**Turning the routine survey off is separate and optional**, per the Detail
above: it is a directive in the blocklist, belonging to whoever owns that
list. A person who wants the notes on every run changes nothing.

**No mechanical check, and one was attempted.** The rule proper is about what
a session *says*, and no check can read a reply that was never written. The
mechanism half **is** mechanically checkable — whether a blocklist still
declares the quiet directive, which is worth checking because a directive that
looks like a comment is the first thing a tidy-up of a long file deletes — but
**a universal check cannot require it**, since leaving the survey on is a
legitimate choice this rule deliberately does not make for anyone. A per-set
check of that kind is the right home for it, keyed to that set's own blocklist,
and is not something this level can hold.

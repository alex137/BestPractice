---
title:         Speculative — a WhatsApp bridge into a project repository
kind:          proposal
status:        drafted
opened:        2026-09-09
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       A brainstormed design for reaching Precedent through WhatsApp instead of a terminal, written up so the thinking survives — not a decision to build it.
---

# Speculative — a WhatsApp bridge into a project repository

> **This is a brainstorm, not a plan of record.** It came out of one
> exploratory conversation on 2026-09-09 and nobody has decided to build any
> of it. It may never be built. Nothing here is scheduled, costed, staffed or
> approved, and no other document should cite it as a commitment. It is
> committed only because the analysis was worth keeping —
> [repo-is-memory](../practices/repo-is-memory.md) — and a chat thread is not
> a place to keep anything.
>
> **Every claim below about Meta's platform is unverified.** See
> [Everything here about Meta's platform needs verifying](#everything-here-about-metas-platform-needs-verifying).

## What it is

**A bot with its own phone number that each participant has a private
WhatsApp thread with.** Nobody is in a group. The bot is the group: it takes
each person's message, transcribes it if it is voice, commits it to the
project repository, runs a Claude turn against the repository, replies to
that person, and — later, once the basics work — relays a summary of the
exchange to the other participants in their own threads.

**The reason it exists is adoption, not capability.** Everything Precedent
does is already reachable from a phone
([MOBILE.md](../MOBILE.md)). What is not reachable is the person who will
not open a Claude session, will not learn what a branch is, and will
cheerfully send a two-minute voice note about the same subject. WhatsApp is
where that person already is.

## Why a bot in a real group chat is the wrong shape

The idea started as *a group chat with two people and a bot*. That version
should not be built, and the reason is worth recording so nobody re-derives
it.

There are three ways into a WhatsApp group and none of them is good:

1. **Meta's official Cloud Application Programming Interface (API).** Built
   for business-to-customer threads between two parties. Group support has
   historically been absent or limited, and a business identity sitting
   inside a personal group is an awkward object even where it works.
2. **An unofficial client library** driving a real number as a linked
   device. This works today and is how essentially every WhatsApp bot demo
   is built. **It also violates WhatsApp's terms**, the realistic
   consequence being that the number gets banned, and it breaks whenever
   Meta changes the protocol — so it is a permanent maintenance commitment,
   not a one-off build.
3. **Not joining at all** — a contact people forward things to, or periodic
   use of WhatsApp's own chat export dropped into the repository. Loses the
   live reply, keeps the capture, breaks no rules.

**The hub-and-spoke design in this document is what makes route 1 viable.**
One-to-one threads with a business number are exactly the shape Meta's
official API was built for. That single choice removes the ban risk from the
whole project, and it is the reason to prefer the hub over the group even
though the group is what a user would ask for.

Three further things it buys:

- **Everyone knows they are talking to a bot.** The consent story and the
  identity story both become trivial: no ambiguity about who is being
  recorded or who said what.
- **The bot becomes a chokepoint that can be gated.** Nothing crosses from
  one participant to another except through code somebody wrote, so *what
  may be relayed* and *what may be committed* become two enforceable
  policies rather than a firehose being scrubbed after the fact.
- **It degrades gracefully.** If one person's thread breaks, the others do
  not notice.

**Voice notes are the part that sounds hard and is not.** They arrive as
compressed audio and current transcription handles them well, including
accents and crosstalk. The hard parts are all elsewhere.

## Everything here about Meta's platform needs verifying

**As of 2026-09-09, none of this has been checked against current Meta
documentation.** The *shape* of the rules is what this document is confident
about: business accounts, a limited window for free-form outbound messages,
template approval for anything outside it, signed webhooks. **The specifics
— window length, pricing, category names, verification requirements —
change, and are unverified here.**

Treat every platform claim below as a thing to confirm in phase 0, never as
a fact to build on. That is what
[TODO.md](../TODO.md)'s `whatsapp-bridge-research` item is for.

## Phases

### Phase 0 — prove the platform will do it

Before writing anything real, get a Meta test number to send and receive one
message each.

**This is the phase that either kills the idea or de-risks it entirely, and
it costs almost nothing.** What it establishes: that a number can be
registered, that inbound messages arrive at a webhook, that outbound replies
go out, and what the actual messaging-window and template rules are today.

### Phase 1 — capture only, one participant

**No relaying, no Claude reasoning, no replies beyond an acknowledgement.**
One person messages the bot; the message lands in the project repository as
a commit.

The pipeline:

1. Meta posts the message to a webhook.
2. The service verifies the request signature and checks the sender is on
   the allowlist.
3. If it is a voice note, download the audio and transcribe it.
4. Append to an inbox file in the repository, commit, push.
5. Reply with a short confirmation and a link to the commit.

**The success criterion is behavioural, not technical: does that person send
a second message the next day, unprompted.** If the answer is no, everything
after this is wasted effort — and a week has found that out instead of a
quarter.

### Phase 2 — Claude in the loop

The commit triggers a Claude session against the repository. It reads the
message in the context of the project, does whatever the message asks that
is safe to do — usually filing the thought under the right topic, sometimes
opening a pull request — and produces a reply, which the bot sends back to
the person.

**The bot may open a pull request. It may never merge one, and never pushes
to a protected branch.** Everything a WhatsApp message causes arrives as
something a person reviews.

### Phase 3 — the relay

The bot sends the other participants a message in their own threads:
*"<person> raised X, I said Y."* This is where the hub finally feels like a
group. Two things make it the hardest phase, and both are worth knowing
before starting it.

**The messaging window.** A participant who has not messaged the bot
recently cannot be sent free-form text — only an approved template with
fixed wording and variable slots, along the lines of *"{{1}} raised {{2}} —
open the thread to read the reply."* It is stilted, it is metered per send,
and it is the honest cost of the design.

**Fan-out cost.** With N participants, every message becomes N-1 outbound
sends. Two people is trivial. Six people is a real bill and a real
notification load. **The mitigation is a daily digest rather than a live
relay** — one send per person per day, and arguably more useful anyway.

### Phase 4 — threading

Relayed messages have to be answerable. WhatsApp's native reply-quote is the
mechanism: when someone replies to a specific message, the webhook payload
carries a reference to the quoted message, which is what lets a reply be
routed back to the right thread in the repository.

**Design the data model for this in phase 1 even though it is not used until
phase 4.** Retrofitting message identity later is miserable.

## What the repository side looks like

Two directories, deliberately separate:

- **A verbatim inbox.** Append-only, never edited by anyone, one file per
  participant per month. This is ground truth: what was actually said, when,
  by whom. A voice note gets both its transcript and a note that it was
  audio, because transcription is good but not perfect and a future reader
  needs to know which is which.
- **Curated topic threads.** Claude's synthesis — the decisions and the open
  questions, organised by subject rather than by chronology. This is what
  anybody actually reads, and it cites the inbox.

**Phone numbers never enter the repository.** The service maps each number
to a handle through a configuration file kept outside version control; the
repository only ever sees the handle. This matters more than it sounds: a
repository is forever, and a phone number in a git history is not removable
in any practical sense.

## What is needed from the person setting this up

Ordered by lead time — the slow ones are worth starting first.

| What | Why | Effort and lead time |
|---|---|---|
| **A dedicated phone number** | Registering a number on the Cloud API takes it out of the consumer WhatsApp app permanently. It must not be a personal number, and must not currently be on WhatsApp. | A prepaid Subscriber Identity Module (SIM), or a virtual number that can receive text messages. Confirm virtual numbers are accepted before buying one. |
| **A Meta Business account and developer app** | The API is only reachable through one. | An afternoon, plus whatever business verification takes. Verification is the long pole and is worth starting on day one. |
| **A business display name** | Shown to everyone who messages the bot, and subject to Meta's approval — so something plausible rather than a joke. | A decision, five minutes. |
| **A public endpoint over HTTPS** | Meta pushes messages to a Uniform Resource Locator (URL) with a valid certificate. | A small always-on host: any cheap virtual server or managed platform. |
| **A private GitHub repository for the project** | Non-negotiable once a chat feed writes to it. | Minutes. |
| **Two API keys** — Claude, and a transcription service | The two paid dependencies. | Minutes. |
| **One willing participant** | The whole phase-1 test. Ideally someone who complains about GitHub. | Ask. |
| **Each participant messaging the bot first** | Opt-in is required, and it opens their messaging window. | One message each. |

**What is not needed: the setter-upper's own attention on the WhatsApp
side.** Someone who already works in Claude Code and GitHub should stay off
the WhatsApp leg entirely — it dodges the messaging-window problem for the
person who would otherwise generate the most notifications, and they can
read the repository directly.

## The risks worth naming

**Every inbound message is untrusted input.** Anyone in a thread can write
anything, including text that reads like instructions. The rule is that
message content is *data*: it gets committed and summarised, never executed.
The bot's write path stays narrow — append, commit, open a pull request, and
nothing else.

**A private chat feeding a repository inverts this project's scrub model.**
Everything in [practices/scrub-gate.md](../practices/scrub-gate.md) and the
check-in flow assumes a person decides what becomes public. A chat feed does
not. So: the bridge repository is private, permanently, and the path from it
to anything public stays manual.

**Transcription errors become committed record.** Mostly harmless,
occasionally not — a misheard name or number that then gets synthesised into
a decision. Keeping the verbatim inbox separate from the curated threads is
the mitigation, because the error stays traceable.

**Volume.** A chat thread's message rate is far higher than a working
session's. Consecutive messages from one person should be batched, with a
delay of a few minutes before a Claude turn is triggered, or the cost and
the noise both scale with chatter rather than with content.

## The one recommendation that cuts against the premise

**Phase 1 should probably be built on Telegram first.** Its bot interface is
free and first-class, needs no phone-number registration and no business
verification, and the whole capture loop could run the same day rather than
after Meta's verification queue.

This is not a proposal to ship on Telegram. The premise of the whole idea is
that WhatsApp is what makes people likely to use it, and that premise is
probably right. **But if the loop is broken, that is worth knowing this
week, and Meta's onboarding will not say so faster than a Telegram bot
will.**

## Open questions

Nobody has answered these, and they are not blocking anything, because
nothing is being built.

1. **Live relay or daily digest** for phase 3. The digest is cheaper,
   quieter and probably better; the live relay is what the idea originally
   described.
2. **Telegram for phase 1**, or straight to WhatsApp and accept the lead
   time.
3. **What the project repository actually is** — a new repository per
   project, or one bridge repository with a directory per project.

## Where this came from

A single exploratory conversation on 2026-09-09, held as a
[brainstorm](../practices/brainstorm-holds-commits.md), which is why nothing
was written until it was explicitly asked for. The idea and the hub-and-spoke
refinement are Morgan's; the platform analysis and the phasing are the
session's. **It records that a conversation happened and what it concluded.
It does not record a decision to proceed.**

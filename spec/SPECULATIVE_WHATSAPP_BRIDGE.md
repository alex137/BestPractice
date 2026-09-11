---
title:         Speculative — a chat bridge into a project repository, Telegram first
kind:          proposal
status:        drafted
opened:        2026-09-09
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       A brainstormed design for reaching Precedent through a chat app instead of a terminal — proved on Telegram first, aimed at WhatsApp — written up so the thinking survives, not a decision to build it.
---

# Speculative — a chat bridge into a project repository, Telegram first

> **This is a brainstorm, not a plan of record.** It came out of one
> exploratory conversation on 2026-09-09 and nobody has decided to build any
> of it. It may never be built. Nothing here is scheduled, costed, staffed or
> approved, and no other document should cite it as a commitment. It is
> committed only because the analysis was worth keeping —
> [repo-is-memory](../practices/repo-is-memory.md) — and a chat thread is not
> a place to keep anything.
>
> **Updated 2026-09-11**, on Morgan's ask, with two changes: the proof of
> concept now starts on **Telegram**, and the platform claims have had a
> desk check against current documentation. What that check could and could
> not reach is [What has actually been
> checked](#what-has-actually-been-checked). **It is still speculation** —
> the update makes it better-informed, not decided.

## What it is

**A bot with its own identity that each participant has a private thread
with.** Nobody is in a group. The bot is the group: it takes each person's
message, transcribes it if it is voice, commits it to the project
repository, runs a Claude turn against the repository, replies to that
person, and — later, once the basics work — relays a summary of the exchange
to the other participants in their own threads.

**The reason it exists is adoption, not capability.** Everything Precedent
does is already reachable from a phone
([MOBILE.md](../MOBILE.md)). What is not reachable is the person who will
not open a Claude session, will not learn what a branch is, and will
cheerfully send a two-minute voice note about the same subject. A chat app
is where that person already is.

**WhatsApp is the destination; Telegram is how you find out whether the idea
works.** The two are interchangeable for everything above — the hub shape,
the repository layout, the Claude turn, the relay — and completely different
in what they cost to start. That split is the whole reason for the phasing
below.

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

**The hub shape is also what makes Telegram a real rehearsal rather than a
different project.** A Telegram bot is natively one-to-one with each person
who starts it, so phase 1 below builds the same topology it would build on
WhatsApp.

## What has actually been checked

**Desk check, 2026-09-11.** Everything in this document about the two
platforms was read against current public documentation on that date. Two
qualifications travel with all of it, and both matter:

- **Meta's own developer documentation was unreachable from the session that
  did the check** — `developers.facebook.com` is blocked by this
  environment's network egress proxy — so **every WhatsApp figure and rule
  below comes from secondary sources**: vendor guides, Business Solution
  Provider documentation, and pricing explainers. They agree with each other,
  which is worth something and is not the same as reading it from Meta.
- **Nothing has been tested.** No number registered, no message sent, no
  webhook received. A rule read in a document and a rule met in an onboarding
  queue are different objects, and the gap between them is exactly what
  phase 2 exists to close.

**Telegram's own documentation was also blocked** (`core.telegram.org`), so
the Telegram specifics below are secondary too, from developer guides and
API references rather than the source.

**So: nothing here is a fact to build on.** Prices move, tiers move, and
verification requirements move fastest of all
([volatile-rules-carry-dates](../practices/volatile-rules-carry-dates.md)).
Anything below carrying a figure carries its date; re-read it before acting
on it.

## Phases

The phase numbering changed on 2026-09-11. **What was phase 0 — prove Meta's
platform will do it — is now phase 2**, because the Telegram build answers
the question that actually kills the idea, and answers it in an afternoon
instead of a verification queue.

### Phase 1 — the whole loop, on Telegram, one participant

**Build the entire capture loop on Telegram first.** One person messages the
bot; the message lands in the project repository as a commit; the bot
replies with a confirmation and a link.

The pipeline:

1. Telegram posts the message to a webhook (or the service long-polls for
   it — both are supported, and polling needs no public endpoint at all).
2. The service checks the sender is on the allowlist.
3. If it is a voice note, download the audio and transcribe it.
4. Append to an inbox file in the repository, commit, push.
5. Reply with a short confirmation and a link to the commit.

**The success criterion is behavioural, not technical: does that person send
a second message the next day, unprompted.** If the answer is no, everything
after this is wasted effort — and a week has found that out instead of a
quarter.

**Why this is the right first phase.** A Telegram bot needs no phone number,
no business entity, no display-name approval, no template approval, no
verification queue and no per-message billing. It costs a conversation with
Telegram's own `@BotFather` to get a token. **Every obstacle between an idea
and a working loop is therefore a real obstacle in the idea**, not an
artefact of Meta's onboarding — which is the only reason to run a proof of
concept at all.

**What Telegram will not tell you.** It will not tell you whether the people
you actually want will use it — the premise of the whole idea is that
WhatsApp is where they already are, and that premise is probably right.
Phase 1 tests the loop and the habit; it does not test the platform choice.

### Phase 2 — prove Meta's platform will do it

With the loop working and worth keeping, get a Meta test number to send and
receive one message each.

**This is the phase that either kills the WhatsApp version or de-risks it
entirely, and it costs almost nothing.** What it establishes: that a number
can be registered, that inbound messages arrive at a webhook, that outbound
replies go out, and what the actual messaging-window, template and
verification rules are today rather than as described second-hand above.

**Port the phase-1 service rather than rewriting it.** The two platforms
differ in the adapter — how a message arrives, how a file is fetched, what
an outbound send is allowed to contain — and in nothing else. **A phase-1
build that has a platform adapter behind an interface makes phase 2 a day's
work; one that has Telegram calls threaded through it makes phase 2 a
rewrite.** That is the one design constraint phase 1 must respect.

### Phase 3 — Claude in the loop

The commit triggers a Claude session against the repository. It reads the
message in the context of the project, does whatever the message asks that
is safe to do — usually filing the thought under the right topic, sometimes
opening a pull request — and produces a reply, which the bot sends back to
the person.

**The bot may open a pull request. It may never merge one, and never pushes
to a protected branch.** Everything a chat message causes arrives as
something a person reviews.

### Phase 4 — the relay

The bot sends the other participants a message in their own threads:
*"<person> raised X, I said Y."* This is where the hub finally feels like a
group. Two things make it the hardest phase, and both are worth knowing
before starting it.

**The messaging window, on WhatsApp.** A participant who has not messaged
the bot recently cannot be sent free-form text — only an approved template
with fixed wording and variable slots, along the lines of *"{{1}} raised
{{2}} — open the thread to read the reply."* It is stilted, it is metered
per send, and it is the honest cost of the design.

**On Telegram there is no such window and no such bill**, which makes the
relay dramatically cheaper to prototype and is a second reason to build
phase 1 there. It also means **the relay is the one phase Telegram will
flatter**: a live relay that feels fine on Telegram may be unaffordable and
stilted on WhatsApp, so do not let a Telegram prototype settle the
live-relay-versus-digest question.

**Fan-out cost.** With N participants, every message becomes N-1 outbound
sends. Two people is trivial. Six people is a real bill and a real
notification load on WhatsApp. **The mitigation is a daily digest rather
than a live relay** — one send per person per day, and arguably more useful
anyway.

### Phase 5 — threading

Relayed messages have to be answerable. Both platforms carry a native
reply-quote, and both surface it in the webhook payload as a reference to
the quoted message — which is what lets a reply be routed back to the right
thread in the repository.

**Design the data model for this in phase 1 even though it is not used until
phase 5.** Retrofitting message identity later is miserable. **Store the
platform's own message identifier alongside your own from the first commit**,
and store which platform it came from — a bridge that runs on Telegram and
then on WhatsApp has two identifier spaces, and reconciling them afterwards
is the retrofit this warns about.

## What the two platforms require

**Desk check 2026-09-11, secondary sources, untested** — see [What has
actually been checked](#what-has-actually-been-checked).

| | **Telegram** | **WhatsApp Cloud API** |
|---|---|---|
| **Identity to create it** | A Telegram account and a chat with `@BotFather`, which issues the token | Meta developer account, a Meta Business account, and a WhatsApp Business Account |
| **Phone number** | None | A dedicated number that has never been active on consumer WhatsApp, able to receive a Short Message Service (SMS) text or voice verification code. Mobile, landline, virtual and toll-free numbers are all reportedly registrable subject to criteria |
| **Business entity** | None | Business verification is required past a volume threshold, and unlocks the higher messaging tiers |
| **Name approval** | Pick one | A display name, shown to everyone who messages the bot, subject to Meta's approval |
| **Published privacy policy** | Not required to start | Reported as a requirement |
| **Public endpoint** | Optional — `setWebhook` needs HTTPS on port 443, 80, 88 or 8443; `getUpdates` long polling needs no inbound endpoint at all | Required. Meta pushes to an HTTPS URL with a valid certificate and signs the requests |
| **Outbound restrictions** | The bot cannot open a conversation — the person must start it (`/start` or a deep link). After that, replies are free-form | Free-form outbound only inside the customer-service window; outside it, an approved template |
| **Per-message cost** | None | Yes, by message category and recipient country — see [Costs](#costs-beyond-the-claude-api) |
| **Voice notes** | Delivered as a file reference; `getFile` downloads are capped at 20 MB, which a voice note will not approach | Delivered as a media reference to download |
| **Rate limits** | Reported as ≈30 messages per second broadcast by default, with a paid tier above it; per-chat limits are far tighter and irrelevant at this scale | Tiered by verification status — reportedly 250 business-initiated conversations per rolling 24 hours unverified, rising through 1,000 / 10,000 / 100,000 / unlimited once verified |
| **Time to first working message** | An afternoon | However long Meta's verification queue takes, which nobody here can predict |

**Read the last row as the argument.** Everything else in the table is
detail; the reason to start on Telegram is that one line.

## What is needed from Morgan

Split by phase, because **the Telegram phase needs almost nothing** and that
is the point. Ordered within each phase by lead time — the slow ones are
worth starting first.

### For phase 1 (Telegram)

| What | Why | Effort, cost and lead time |
|---|---|---|
| **A Telegram account** | To talk to `@BotFather` and to create the bot | Minutes. Free. Can be an existing personal account — the bot is a separate identity, not a linked device, so there is no registration that consumes the account |
| **A bot token** | The single credential the service authenticates with | One `@BotFather` conversation. Free |
| **Somewhere to run a small always-on service** | The bridge has to be listening. **With long polling this can be anything with an outbound internet connection** — no public endpoint, no certificate, no domain | See [Costs](#costs-beyond-the-claude-api). A small virtual server, or an existing always-on machine |
| **A private GitHub repository for the project** | Non-negotiable once a chat feed writes to it | Minutes. Free on existing plans |
| **A Claude API key** | The phase-3 dependency. **Phase 1 does not need it** — capture-and-commit involves no model call at all | Minutes |
| **A transcription route** | Only if voice notes are in scope for phase 1, which they should be — they are the whole adoption argument | An API key, or a self-hosted model. See [Costs](#costs-beyond-the-claude-api) |
| **One willing participant** | The whole phase-1 test. Ideally someone who complains about GitHub | Ask |

### Additionally for phase 2 and beyond (WhatsApp)

| What | Why | Effort, cost and lead time |
|---|---|---|
| **Business verification with Meta** | The long pole, and worth starting the day WhatsApp is decided on. Reportedly requires a legal business entity with documentation Meta will check — registration papers, address, and so on | Unknown and not predictable from here. **Whether Morgan has an entity that satisfies this is the first thing to establish**, because the answer may change the plan rather than delay it |
| **A dedicated phone number** | Registering a number on the Cloud API takes it out of the consumer WhatsApp app permanently. It must not be a personal number, and must not currently be on WhatsApp | A prepaid Subscriber Identity Module (SIM), or a virtual number that can receive text messages. **Confirm virtual numbers are accepted for your country before buying one** — this is reported to work and is exactly the kind of rule that varies |
| **A Meta Business account and developer app** | The API is only reachable through one | An afternoon, plus whatever verification takes |
| **A business display name** | Shown to everyone who messages the bot, and subject to Meta's approval — so something plausible rather than a joke | A decision, five minutes |
| **A published privacy policy** | Reported as required for the business account | An afternoon, or a page on an existing site |
| **A public endpoint over HTTPS** | Meta pushes messages to a Uniform Resource Locator (URL) with a valid certificate. **Long polling is not an option here**, so this is a real requirement that phase 1 could skip | A domain and a certificate on the host from phase 1 |
| **Approved message templates** | Anything sent outside the customer-service window | Per template, subject to review |
| **Each participant messaging the bot first** | Opt-in is required, and it opens their messaging window | One message each |

**What is not needed: Morgan's own attention on the chat side.** Someone who
already works in Claude Code and GitHub should stay off the WhatsApp leg
entirely — it dodges the messaging-window problem for the person who would
otherwise generate the most notifications, and they can read the repository
directly.

## Costs beyond the Claude API

**All figures desk-checked 2026-09-11 from secondary sources, in United
States dollars unless marked, and none of them tested.** Providers change
prices; treat every number as an order of magnitude rather than a quote.

### Phase 1, on Telegram

| Line | What it costs |
|---|---|
| **Telegram platform** | **Nothing.** No per-message charge, no account fee, no verification |
| **Hosting** | The mainstream small-server tiers — one virtual CPU and a gigabyte of memory — sit at roughly **$5 to $7 per month** (Linode's entry plan at $5, Fly.io ≈$5.70, DigitalOcean $6, Hetzner ≈$6.96 at the time of the check). **Cheaper exists**: Hetzner's ARM tier is quoted at €3.29/month without an IPv4 address, and discount providers advertise annual deals near $15/year, with the usual warning that promotional pricing and renewal pricing differ |
| **Transcription** | Per-minute, and cheap at this volume. Deepgram's Nova-3 is quoted at **≈$0.0043/minute** for batch; AssemblyAI at **≈$0.37/hour**, about $0.006/minute. Self-hosting a Whisper-class model removes the per-minute charge and replaces it with compute you are already paying for. **Add-ons reportedly push effective cost well above the headline rate**, so treat the base figure as a floor |
| **Domain and certificate** | **Nothing, if phase 1 long-polls.** A domain is a small annual cost if you want one anyway |
| **Total** | **Realistically a server and pennies of transcription** — call it the cost of the virtual server, plus loose change |

**Put the transcription figure in scale:** at roughly half a cent a minute,
an hour of voice notes a day is cents. **Transcription is not a cost
question at this size; it is a quality question.**

### Phase 2 onward, on WhatsApp

**The pricing model changed on 2025-07-01**, and any older guide you find is
describing a model that no longer exists. Before that date Meta billed per
24-hour *conversation*; since then it bills **per delivered template
message**, by category and recipient country.

| Line | What it costs |
|---|---|
| **Meta platform fee** | None for the Cloud API itself — Meta hosts it. The cost is per message |
| **Replies inside the customer-service window** | **Free.** A reply sent within 24 hours of the person's last message is not billed, with no monthly cap since Meta removed the old free-service-conversation allowance on 2024-11-01. **This is the case the bridge is mostly in**, because a person messaging the bot opens the window every time |
| **Utility templates inside the window** | **Free since 2025-07-01** |
| **Marketing templates** | **Always billed**, window open or not, and with no volume discount at any tier — reportedly deliberate, to keep promotional blasting expensive. Quoted 2026 rates range from **≈$0.0094 per message in India to over $0.124 in Germany**; the rate that matters is the recipient's country, not yours |
| **Authentication templates** | Always billed individually. Reportedly **≈$0.0014 in India to $0.05 and above in parts of Europe** |
| **Utility and authentication volume tiers** | Rates step down once monthly delivered volume crosses Meta's thresholds; tiers reset monthly. **Irrelevant at the scale this document describes** |
| **A Business Solution Provider, if you use one** | A markup on Meta's rate, reportedly **$0.003 to $0.010 per message** for the larger providers. **Going direct to the Cloud API avoids this entirely**, which is what this design assumes |
| **Everything from phase 1** | Hosting, transcription and the Claude key all still apply, plus a domain and certificate that long polling let phase 1 skip |

**Where the WhatsApp bill actually comes from is the relay, and only the
relay.** Inbound messages are free, replies inside the window are free, and
the bot is in that window by construction. **The charge appears the moment
the bot messages someone who has not written to it recently** — which is
precisely phase 4. So:

- **Phases 1 to 3 on WhatsApp are, on Meta's side, close to free.**
- **Phase 4 has a bill that scales with participants times messages**, and
  the mitigation is the daily digest: one send per person per day.
- **A digest that goes out as a marketing-category template is the expensive
  shape; the same digest categorized as utility, sent to someone inside the
  window, is free.** Whether a project digest qualifies as utility is a
  Meta categorization question nobody here can answer, and **it is worth
  asking in phase 2**, because the answer is the difference between free and
  a per-person-per-day charge forever.

### What no figure here covers

**The build.** Every number above is a running cost. The service itself is
somebody's time, and this document has deliberately not estimated it —
estimating build effort for a thing nobody has decided to build is exactly
the register [speculation-is-marked](../practices/speculation-is-marked.md)
warns against.

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

**Phone numbers never enter the repository.** The service maps each
platform identifier — a phone number on WhatsApp, a numeric user
identifier on Telegram — to a handle through a configuration file kept
outside version control; the repository only ever sees the handle. This
matters more than it sounds: a repository is forever, and a phone number in
a git history is not removable in any practical sense. **The Telegram phase
makes this easy to get wrong in a way that hurts later**, because a Telegram
user identifier feels harmless enough to commit. Map it anyway — the
discipline is the thing being rehearsed, and the WhatsApp phase inherits
whatever phase 1 taught the code.

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

**A Telegram proof of concept that succeeds is its own risk.** If phase 1
works and the participant likes it, the pressure will be to stay on Telegram
and skip the verification queue entirely — which may be the right answer, and
**may also be the answer that quietly abandons the premise**, since the whole
argument for this idea is that the target person is on WhatsApp and will not
move. Decide that on purpose if it comes up; do not arrive at it by default.

## Open questions

Nobody has answered these, and they are not blocking anything, because
nothing is being built.

1. **Live relay or daily digest** for phase 4. The digest is cheaper,
   quieter and probably better; the live relay is what the idea originally
   described. **The desk check sharpens this rather than settling it**: on
   WhatsApp the digest is the affordable shape, on Telegram both are free,
   so a Telegram prototype cannot be trusted to answer it.
2. **What the project repository actually is** — a new repository per
   project, or one bridge repository with a directory per project.
3. **Whether a project digest is a utility template or a marketing one** in
   Meta's categorization. It is the difference between a free phase 4 and a
   metered one, and it is a question for phase 2.
4. **Whether Morgan has, or wants, a business entity that clears Meta's
   verification.** If not, the WhatsApp destination is a different plan, and
   that is better known early than late.

**One former open question is now answered.** *Telegram for phase 1, or
straight to WhatsApp and accept the lead time* — Morgan chose Telegram on
2026-09-11, which is what this revision reflects.

## Where this came from

A single exploratory conversation on 2026-09-09, held as a
[brainstorm](../practices/brainstorm-holds-commits.md), which is why nothing
was written until it was explicitly asked for. The idea and the hub-and-spoke
refinement are Morgan's; the platform analysis and the phasing are the
session's.

**Revised 2026-09-11**, on Morgan's instruction to start with Telegram as a
quick proof of concept — the recommendation the first version had made and
left as an open question — and to desk-check the WhatsApp requirements and
costs. The phase renumbering, the platform comparison, the setup list and
the cost section are that revision. **It records that a conversation
happened and what it concluded. It does not record a decision to proceed.**

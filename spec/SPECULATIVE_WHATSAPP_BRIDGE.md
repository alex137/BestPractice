---
title:         Speculative — a chat bridge into a project repository, Telegram first
kind:          proposal
status:        drafted
opened:        2026-09-09
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       A brainstormed design for reaching a Claude session by voice through the chat app someone already uses — proved on Telegram first, aimed at WhatsApp — written up so the thinking survives, not a decision to build it.
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

**A voice interface to a working Claude session, reached through the chat
app the person already uses.** Morgan, 2026-09-11: *"I'm imagining this as a
whatsapp/telegram interface (include largely via voice message) to chat
sessions like we have here; to work via voice chat (like we can do in the
claude app, but via whatsapp)."* The comparison to the Claude app's voice
mode is the clearest statement of what this is — the difference is only which
app it arrives in, and the app is the whole point.

**So it is a session, not a suggestion box.** Whatever a person can do by
talking to Claude here, they can do by sending a voice note there: ask,
argue, redraft, change their mind, and — the part this revision changes —
**merge their own work**. The earlier draft had the bot filing thoughts and
opening pull requests for somebody else to review. That was the right design
for a capture pipeline and the wrong one for a session, because it makes the
person a contributor to their own work rather than the author of it.

**Each participant has their own private thread with the bot.** Nobody is in
a group. The bot is the group: it takes each person's message, transcribes
it if it is voice, runs a Claude turn against the project repository in that
person's own continuing session, replies to them, and — later, once the
basics work — relays a summary to the other participants in their own
threads.

**The reason it exists is adoption, not capability.** Everything Precedent
does is already reachable from a phone
([MOBILE.md](../MOBILE.md)). What is not reachable is the person who will
not open a Claude session, will not learn what a branch is, and will
cheerfully send a two-minute voice note about the same subject. A chat app
is where that person already is.

**WhatsApp is the destination, and that is decided rather than assumed.**
Morgan, 2026-09-11, asked directly whether a working Telegram bot might just
become the answer: *"the people I want to use this with to collaborate with
already live within using whatsapp, they won't change apps, and I want to go
where they are."* **So the platform is not one of the things being tested.**
The people this exists for are on WhatsApp and will not move, which is the
entire reason the idea is worth anything — a bridge to an app they do not use
is not a cheaper version of this, it is a different and useless thing.

**Telegram is a rehearsal, and nothing more.** The two platforms are
interchangeable for everything above — the hub shape, the repository layout,
the Claude turn, the relay — and completely different in what they cost to
start, which is the only reason to touch Telegram at all: it answers *does
this loop work and will a person use it* without waiting on Meta. **What it
must never do is become the destination by default.** Phase 1 exists to be
thrown away, or ported.

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

**Phase 1 is deliberately not the real thing.** The destination is a
continuing session per person (phase 3); phase 1 is that with the thinking
removed, on purpose, because the habit is what is being tested and a session
is not needed to test it. **What it must still get right is identity and
continuity** — which person, which thread, which message, in a store a
session can later read as history. A capture phase that treats each message
as an isolated event builds the wrong substrate for everything after it.

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

### Phase 3 — the session itself

**This is the phase that makes the idea what Morgan described, and the rest
of the document is scaffolding around it.** The person's messages arrive in
a continuing Claude session against the project repository. It reads them in
the context of the project and of everything they have already said, does
the work, and replies. They answer. It is a conversation, and it is the same
conversation tomorrow.

**The person may merge, and the bot merges on their say-so.** Precedent
already has the vocabulary for this and it was built for typing, not
speaking, which turns out not to matter: `Go merge` is four syllables and
means sync, name the branch, commit, push, open the pull request, merge,
without asking again
([practices/go-merge.md](../practices/go-merge.md)). So are `Park it`,
`Three Things`, `Plain words`, `Weak yes` and `Clean session`. **A standing
command vocabulary is exactly what a voice interface needs** — short, fixed,
unambiguous phrases that survive transcription — and this repository has one
already, written up for a person who is not a developer in
[documentation/HOW_TO_USE_THIS_DAY_TO_DAY.md](../documentation/HOW_TO_USE_THIS_DAY_TO_DAY.md).
That is a genuine piece of luck and worth noticing rather than
re-inventing.

**What the bot may merge is bounded by what the person is working on, not by
the bot's caution** — see [Who may change what](#who-may-change-what).

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

**This section's title has become slightly misleading, and the honest
correction belongs here rather than in a renamed heading.** When the bridge
was a capture pipeline, the Claude API was one dependency among several and
everything else was the interesting part. Now that the destination is a
session per person, **the model is the dominant running cost and everything
priced above is rounding**. Nothing in this document estimates it, because
the figure depends entirely on how much a person talks, how much repository
context each turn carries, and whether consecutive messages are batched — and
a made-up number would be worse than none
([no-invented-specifics](../practices/no-invented-specifics.md)). **The
batching note under [The risks worth naming](#the-risks-worth-naming) is a
cost control, not a tidiness preference**, and it is the first thing to build
rather than the first thing to optimise later.

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

## Who may change what

**This bridge is for people who do not use GitHub and are not going to
start** — Morgan's phrase for the audience is people who already live in
WhatsApp and will not change apps. It is not for the person who already has
a terminal; they have one, and it is better.

**The boundary is drawn around the files, and it is not drawn around the
people.** The distinction that matters is what a change is *to*: the
project's **content** — documents, decisions, notes, open items, drafts,
practice candidates — against the repository's **own machinery**: the
vendored engine under `tools/`, the hooks under `.claude/`, `precedent.json`,
the workflow files, the practice catalogue's structure. A session reached
through the bridge writes content and merges content. It does not touch
machinery, and the reason is not that the person could not be trusted with
it — it is that nobody wants to debug a vendored loader by voice note, and a
half-finished machinery change is how a repository stops working for
everybody in it.

**Saying it that way is deliberate**
([technical-describes-people](../practices/technical-describes-people.md)):
*technical* and *non-technical* describe people, never directories. There is
no non-technical half of a repository. There is content, there is machinery,
and there is a person who cares about one of them.

### The enforcement problem the bridge creates

[spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
already worked this out for the sessions people open themselves, and settled
on two independent layers: **GitHub's own collaborator role**, which is
enforced by GitHub whatever Claude is told, and **the session's tool
allowlist and permission mode**, which is enforced by the harness. Neither is
sufficient alone, and the first only binds if the person authenticates to
GitHub as themselves.

**The bridge breaks that first layer, and this is the most important thing on
this page.** The bot holds one credential and pushes as itself. GitHub sees
the bot, never the person behind the thread, so a per-person collaborator
role is not being checked — **the platform-enforced boundary that plan relies
on is simply absent here**, and it is absent quietly, which is worse. A
design that assumes it carried over would be wrong in the direction that
matters.

So the boundary has to be rebuilt inside the bridge, and **it belongs in the
service rather than in the session's instructions**. A write-scope allowlist
the service checks before it pushes — these paths for this thread, everything
else refused — is a thing that holds when a session is confused, mistaken, or
being talked into something. An instruction telling Claude which files to
leave alone is a thing that usually holds. **Only one of those is a
boundary**, and a bridge that can merge needs the real one.

Two honest consequences:

- **The repository cannot be the only permission model**, because everything
  arrives as the same identity. Scope is per-thread, held by the service, and
  the mapping from thread to scope lives in the same configuration file that
  maps threads to handles — outside version control, since it is credentials
  by another name.
- **A practice candidate is content; a landed practice file is closer to
  machinery.** Precedent already has the channel for exactly this gap —
  [tools/precedent_candidate.py](../tools/precedent_candidate.py) and
  [spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md) — so a person can raise a
  rule by talking about it, and its landing stays a separate act. That is the
  shape to reuse rather than a second one invented here.

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

**Once the bridge is a session, the inbox is doing a second job**: it is the
conversation's own memory, and it is the reason a session resumed tomorrow
knows what was said today. That is
[repo-is-memory](../practices/repo-is-memory.md) arriving by a different
road, and it is a good argument for writing the inbox carefully in phase 1,
long before anything reads it back.

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

**A bridge that can merge cannot also treat every message as inert data, and
pretending otherwise would be the most dangerous sentence in this document.**
The earlier draft said message content is *data*, never executed, and the
bot's write path stays narrow. That was true and easy when the bot filed
things. **It is no longer either**: the person is having a working session
and expects it to act, so "never act on what a message says" is not a rule
this design can keep.

What replaces it is a distinction the earlier version did not need. **The
participant is authorized; the content inside their message is not.** A voice
note from the person on the allowlist is an instruction from someone entitled
to give it. A forwarded message, a quoted email, a pasted block, a document
somebody sent them — **that is material they are showing the session, not
something they are saying** — and it gets read, summarised and committed,
never obeyed. The failure this prevents is the ordinary one: somebody sends
the participant a message containing text shaped like a command, they forward
it to the bot because it seemed relevant, and a session takes it as an
instruction that arrived through an authorized thread.

**The write-scope allowlist in the service is what makes the distinction
survivable**, because it bounds the worst case whether or not the session
gets it right ([Who may change what](#who-may-change-what)).

**A private chat feeding a repository inverts this project's scrub model.**
Everything in [practices/scrub-gate.md](../practices/scrub-gate.md) and the
check-in flow assumes a person decides what becomes public. A chat feed does
not. So: the bridge repository is private, permanently, and the path from it
to anything public stays manual.

**Transcription errors become committed record**, and once the bot can merge
they become merged record. Mostly harmless, occasionally not — a misheard
name or number that then gets synthesised into a decision. Keeping the
verbatim inbox separate from the curated threads is the mitigation, because
the error stays traceable.

**The sharper version is that a command can be misheard.** `Go merge` exists
precisely so nobody is asked twice, and a voice interface has a failure mode
typing does not: the system can be confidently wrong about what was said.
These pull against each other and the resolution is narrower than it first
looks — **confirm the transcription, never the decision.** Echoing back *"you
said Go merge — merging <branch>"* and proceeding respects the command;
asking *"are you sure you want to merge?"* does not, and re-introduces
exactly the interruption the phrase was coined to kill. The distinction is
worth getting right before it is built, because the wrong version is the one
that feels responsible.

**Volume.** A chat thread's message rate is far higher than a working
session's. Consecutive messages from one person should be batched, with a
delay of a few minutes before a Claude turn is triggered, or the cost and
the noise both scale with chatter rather than with content.

**The Telegram phase can capture the project, and that is the risk to
watch.** Not because staying on Telegram might be right — Morgan has settled
that it is not, above — but because a working thing exerts a pull regardless
of whether anybody endorses it. **The failure shape is drift, not a
decision**: a comfortable phase-1 build that keeps growing Telegram-shaped
features, each one reasonable, until porting is expensive enough to argue
about. Meta's verification queue sitting in the way makes every individual
delay look sensible.

Two things hold the line, and both belong in phase 1 rather than in
somebody's memory. **The platform adapter sits behind an interface from the
first commit** — the constraint phase 1 already carries. And **phase 1 is
done when the participant has used it for a while, at which point Meta
onboarding starts whatever else is happening**: the point of a rehearsal is
that it ends.

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
4. **How much of a session is genuinely continuous.** A conversation that
   remembers yesterday is the point; carrying every prior turn into every
   new one is not affordable and probably not useful either. Where the line
   sits — what is re-read from the repository each time against what is
   carried in context — is a design question nobody has answered, and it is
   the one that decides both the cost and whether the thing feels like a
   session at all.
5. **What Morgan has that clears Meta's business verification**, and what
   that takes if the answer is nothing yet. **This is no longer a question
   about whether to go to WhatsApp at all** — that is settled — so it is not
   a fork in the plan, it is the first real obstacle on the only road. It is
   worth knowing early for that reason rather than the opposite one, and
   what it actually demands is itself a phase-2 finding: this document's
   account of it is second-hand.

**Two former open questions are now answered, both by Morgan on
2026-09-11.** *Telegram for phase 1, or straight to WhatsApp and accept the
lead time* — Telegram, `strength: decided`. And *whether a working Telegram
bot could simply become the answer* — no, `strength: decided`, in the words
quoted under [What it is](#what-it-is). Recorded with their strength per
[decision-strength](../practices/decision-strength.md); both are quotable
choices rather than assent to a session's proposal.

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

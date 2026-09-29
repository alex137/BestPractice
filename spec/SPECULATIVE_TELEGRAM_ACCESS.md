---
title:         Speculative — Telegram access to a project repository, content-only and short-answer
kind:          proposal
status:        drafted
opened:        2026-09-28
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       A brainstormed design for talking to a Claude session about a repository from Telegram — limited to content changes, answering in a line or two with a link to the full version on GitHub — covering the integration routes, the user flow, and how a Telegram user is tied to one repository or several. Not a decision to build it.
---

# Speculative — Telegram access to a project repository, content-only and short-answer

> **This is a brainstorm, not a plan of record.** It came out of one
> exploratory conversation on 2026-09-28 and nobody has decided to build any
> of it. It may never be built. Nothing here is scheduled, costed, staffed or
> approved, and no other document should cite it as a commitment. It is
> written down because the thinking was worth keeping
> ([repo-is-memory](../practices/repo-is-memory.md)).
>
> **One part now exists: a local test build, for Morgan alone**, in
> [bridge/](../bridge/README.md). Morgan asked for it the same day, to try the
> loop on his own computer before anything else. It is a test, not a decision
> to run this for anyone; everything beyond it here is still speculation.

**It builds on
[SPECULATIVE_WHATSAPP_BRIDGE.md](SPECULATIVE_WHATSAPP_BRIDGE.md)** (2026-09-09,
revised 2026-09-11) and does not repeat it. That document already covers the
platform comparison, the costs of hosting and transcription, voice notes, the
relay between participants, and the reasons a hub of private threads beats a
group chat. **This one covers three things that document left thin**: what
"limited permissions" means and where it is actually enforced, how a chat
reply stays short without losing anything, and how a Telegram user is
connected to a repository — or to several.

## What it is

Morgan, 2026-09-28: *"Telegram access … with limited permissions … you can
give instructions and get responses and feedback like a normal user, like the
content only type user … the responses received would have to be very short
and simple and links to the corresponding GitHub etc docs for more details."*

So, in one line: **a Telegram bot that is a narrow front door to a Claude
session working on a repository.** The person types or speaks an
instruction. Claude does the work against the repository, within a content-only
scope. The person gets back a line or two and a link.

**Three properties define it**, and each one is a design constraint rather
than a preference:

1. **Content only.** The person can ask, draft, edit and land changes to the
   project's content — documents, notes, decisions, open items. They cannot
   change the repository's machinery: the vendored engine, hooks, workflows,
   `precedent.json`, the practice catalogue's structure. That is the line
   [CONTRIBUTOR_ACCESS.md](CONTRIBUTOR_ACCESS.md) already drew, and it is
   drawn around files, not around people.
2. **Short.** A reply fits on a phone screen without scrolling: a sentence or
   two, at most a couple of links, and sometimes a button.
3. **Nothing is lost by being short.** The full answer always exists, on
   GitHub, one tap away. The Telegram message is the headline; the link is
   the article.

## The one decision to make first

**The 2026-09-11 revision of the bridge document settled that Telegram is a
rehearsal and WhatsApp the destination** (`strength: decided`), because the
people that bridge was for live on WhatsApp and will not move. It also said
Morgan himself should stay off the chat side, since he already has Claude
Code and GitHub.

Today's ask reads differently: Telegram access as a thing in its own right,
possibly for Morgan himself. **Both readings are coherent and they lead to
different builds**, so this is the first fork:

| If the Telegram user is… | Then Telegram is… | And the cheapest honest route is… |
|---|---|---|
| **Morgan himself**, as a phone front door to his own sessions | A destination, for him | [Route A](#route-a--claude-code-channels-on-an-always-on-machine) below: close to no build at all |
| **Other people**, content contributors who will not use GitHub | Still the rehearsal for WhatsApp, as decided — unless that decision is being reopened | [Route B](#route-b--a-small-bot-service-running-the-agent-sdk): a real, small service |

**Nothing below re-opens the 2026-09-11 decision.** If Telegram is now meant
to be the destination for other people too, that is Morgan's call to make,
and the document should be updated to say so in his words.

### What Morgan answered, and what it changed

Morgan, 2026-09-28: *"I want to do a test, with just me … it needs to be
general so others could use it if they want … the messages that are
instructions must be limited to content -- even from me, from anyone."*

- **The first user is Morgan, on a local test** — `strength: decided`, in his
  words above.
- **Content only applies to everyone, the owner included** — `strength:
  decided`, in his words above. **This rules out route A for the test**:
  Channels runs with its operator's full permissions, and he asked for the
  opposite.
- **So the test build is a small route B, run locally.** Instead of the Agent
  SDK it runs `claude -p` locked down (`--restricted`, file tools only, a
  guard hook), because that uses the owner's existing Claude Code login and
  needs no API key. That choice is the session's; Morgan has not weighed in
  on it. The Agent SDK remains the natural swap for a hosted version, where
  an API key is the norm anyway.
- **Voice is the expected input.** Telegram does not transcribe voice notes
  for bots, so the bridge transcribes them itself (an OpenAI-compatible
  service, or a local program).
- **The full answer lives behind a More button** on the bridge's computer in
  this build, not on a GitHub issue. Links to changes still point at GitHub.

Morgan, 2026-09-29, on the same test: *"can you rewrite it to assume it's done
in a Cloud environment?"* — and, on transcription, *"maybe the audio file
could go to you and you could transcribe it for your use? At least for this
test. What do you think?"*

- **The test runs inside a Claude Code cloud session** — `strength:
  decided`, in his words. The bridge starts with one script
  ([bridge/cloud_start.sh](../bridge/cloud_start.sh)) in a dedicated cloud
  environment that holds the bot token and allows `api.telegram.org`. It
  runs only while that session's machine does, which the test will measure.
- **Claude can't transcribe the audio itself**: its API takes no audio
  input, and Claude Code's file tools read text, images and PDFs, not sound.
  **The session's proposal, not yet agreed:** transcribe in the same machine
  with an open-source Whisper model (`whisper-local`), the nearest honest
  version of "the audio goes to you". No third party, no extra account. It
  costs a one-off package install and model download per machine, and it is
  untested on real audio, because the model host is blocked from the
  environment that built it.

## What has actually been checked

**Two kinds of source, dated 2026-09-28, and one gap:**

- **Claude Code's own documentation** (`code.claude.com/docs`) was read on
  2026-09-28, by a sub-agent of the session that wrote this, for the
  Channels feature, GitHub Actions, the Agent Software Development Kit (SDK) and Managed Agents. The
  pages it cited are linked where they are used. Channels is labelled a
  **research preview** there, which means its commands and limits may change
  ([volatile-rules-carry-dates](../practices/volatile-rules-carry-dates.md)).
- **Telegram's own documentation is still unreachable from this environment**
  — `core.telegram.org` returned 403 from the egress proxy on 2026-09-28, as
  it did on 2026-09-11. **Every Telegram Bot Application Programming Interface (API) detail below is secondary**:
  from general knowledge of the API and from the earlier desk check, not read
  off the source today. Each one is marked *(unverified)* where a build would
  depend on it.
- **Nothing has been tested.** No bot created, no message sent.

## How it could connect — four routes, attacked

**The hard part is not Telegram.** A Telegram bot is a token and a loop that
receives messages. The hard part is what sits behind it: something that runs
a Claude turn against a repository, with a limited scope, and writes the long
answer somewhere linkable.

### Route A — Claude Code Channels, on an always-on machine

Claude Code has a **Channels** feature: a plugin pushes chat messages into a
running Claude Code session, and there is an official Telegram plugin
([docs](https://code.claude.com/docs/en/channels.md), read 2026-09-28).
Setup, as documented: install the plugin, give it the bot token from
`@BotFather`, restart Claude Code with the channel enabled, then pair your
Telegram account with a one-time code and switch the plugin to an allowlist.

**What it is good at:** it is nearly no build. An evening, and Morgan could be
talking to a real Claude Code session on his own repository from Telegram,
with his own vocabulary and practices loaded.

**Where it breaks, for this document's purpose:**

- **A local Claude Code process has to keep running** on a machine that stays
  on. The docs say it does not run in cloud or web sessions.
- **It carries the permissions of whoever started it.** The session has that
  person's GitHub access. "Content only" would be a line in the session's
  instructions and settings, which is guidance, not a boundary. **Fine for
  Morgan; wrong for anybody else.**
- **One session, one working directory.** Several repositories means several
  sessions, or one session rooted above them all — the topology this repo
  already knows skips hooks
  ([gotcha-2026-09-25](../gotchas/gotcha-2026-09-25-a-session-rooted-above-every-repo-it-touches-gets-hooks-and.md)).
- **Research preview.** Built on today, reworked when it changes.
- **Short replies are a request, not a guarantee** — the session is told to
  be brief, and nothing enforces it.

**Verdict: the right route if the user is Morgan, and the wrong one for
anyone with limited permissions.**

### Route B — a small bot service running the Agent SDK

A small always-on service holds the Telegram token and, for each message,
runs a Claude turn through the **Claude Agent SDK**
([docs](https://code.claude.com/docs/en/agent-sdk/overview.md)) in a working
copy of the right repository, with a restricted tool set. It writes the long
answer to GitHub and sends the short one to Telegram.

**What it is good at:** everything this document asks for can be enforced in
code the service owns — who may talk, which repository they reach, which
tools the session has, how long a reply may be, and what may be pushed.
Replies arrive in seconds rather than minutes, and a conversation can resume
where it left off.

**Where it breaks:**

- **It is a real build**, and a real service to keep running: hosting, a
  Claude API key, a GitHub credential, logs, updates.
- **The bot is one GitHub identity.** GitHub sees the bot, never the person,
  so GitHub's per-person roles do not bind them. The earlier bridge document
  called this *"the most important thing on this page"*, and it still is.
  [The answer is below](#where-content-only-is-actually-enforced): the
  service never pushes to a protected branch, and GitHub enforces the rest.

**Verdict: the recommended route for anyone other than Morgan.**

### Route C — GitHub as the message bus

The bot turns each Telegram message into a comment on a GitHub issue, one
issue per person and topic. The Claude Code GitHub Action
([docs](https://code.claude.com/docs/en/github-actions.md)) answers it as a
comment, and the bot relays the first line plus a link back to Telegram.

**What it is good at:** no model runs on a server of Morgan's; the full
answer is a GitHub comment by construction, so the link is free; the whole
conversation is on the record; and the Action's tool list can be restricted.

**Where it breaks:**

- **It is slow for chat.** Each turn starts a fresh continuous-integration runner, checks out the
  repository and runs a session. That latency has not been measured here,
  but it is not the few seconds a chat app sets people up to expect.
- **The bot is still needed** to carry Telegram to GitHub and back, so it
  does not remove the service — it moves the model call out of it.
- **A new workflow file** is needed in each repository, which here is a
  change nobody makes without the owner's own words
  ([ci-workflow-approved](../practices/ci-workflow-approved.md)).
- **The Action restricts tools by name, not by path** (per the docs read
  2026-09-28), so content-only still has to come from branch protection.

**Verdict: the fallback if running a model on a server is off the table.**
Worth remembering, not worth starting with.

### Route D — Managed Agents

Anthropic hosts the agent loop and the sandbox; the bot creates a session per
conversation and streams the result back
([docs](https://platform.claude.com/docs/en/managed-agents/quickstart.md)).
It is route B with the sandbox rented rather than run. **It is a reasonable
swap for B's turn-runner later**, and the design below does not depend on
which of the two runs the turn — that is the point of keeping the
turn-runner behind its own interface.

### The recommendation, in one paragraph

**If the first Telegram user is Morgan: route A, this week, as an
experiment in the short-reply register** — it answers "does a two-line
answer plus a link feel right" for almost nothing. **If the first user is
someone else: route B**, built read-only first, with the platform adapter
and the turn-runner each behind an interface so WhatsApp (per the bridge
document) and Managed Agents (route D) are swaps, not rewrites. Route C only
if a server-side model is ruled out.

## Where "content only" is actually enforced

**Three layers, and only the last one is a boundary.** The first two make the
session behave well; the third makes it impossible for the session's
mistakes to land.

1. **Who may talk — the service's allowlist.** A Telegram user identifier
   maps to a handle and to the repositories that handle may reach. Everyone
   else gets no answer at all. The mapping lives in the service's own
   configuration, outside version control (identifiers never enter a
   repository — the bridge document says why).
2. **What the session may try — its tool set.** For a content-only user: read,
   search, and edit files; no shell, no network fetches, no git commands of
   its own. The service, not the session, does the commit and the push. A
   pre-edit check in the service refuses writes outside the repository's
   content paths and tells the session why, so it can tell the person. **This
   is still not the boundary** — it is what keeps the session from wasting
   the person's time on a change that could never land.
3. **What can land — GitHub itself.** The bot's GitHub identity (a GitHub App
   installed on the chosen repositories is the tidy form) has permission to
   push branches and open pull requests, **and never to bypass branch
   protection.** Every change goes through a pull request. The machinery
   paths are owned in `CODEOWNERS`, and branch protection requires a code
   owner's review — so a pull request that touches machinery waits for a
   person, however it was produced, and a content-only one can merge. That
   is exactly the mechanism [CONTRIBUTOR_ACCESS.md](CONTRIBUTOR_ACCESS.md)
   proposes for people, and it has an open "verify these first" list about
   GitHub's behaviour that applies here unchanged.

**This is the answer to the earlier document's enforcement problem.** The bot
being one identity stops mattering for *what* lands, because GitHub checks
the files, not the author. It still matters for *who* did it, which the
commit carries in a trailer naming the handle — and, where the person has a
GitHub account, a `Co-authored-by:` line so the history credits them.

**Two consequences worth saying out loud:**

- **Each repository has to be set up for this before the bot touches it** —
  branch protection and `CODEOWNERS` on the landing branch. A repository
  without them is one where "content only" means nothing.
- **Practices are machinery.** A content user can *suggest* a practice by
  talking about it — the candidate channel
  ([tools/precedent_candidate.py](../tools/precedent_candidate.py)) exists
  for this — and landing it stays an approver's act, as it does everywhere
  else.

## Short answers that lose nothing

**The rule: the short reply is a summary of a full answer that exists, never
a replacement for one.** Everything else follows from that.

**How it works mechanically.** The session is asked for two things per turn,
as structured output rather than prose the service has to trim:

- **the short reply** — at most two short sentences;
- **the full answer** — as long as it needs to be, posted to GitHub;
- plus the links that matter (the pull request, the file, the line) and any
  buttons to offer.

**The service enforces the length**, not the session's good intentions: an
over-long short reply goes back to the model once to be shortened, and is
cut hard after that. Where the full answer goes:

- **A pull request, when the turn changed something.** "Done — see the
  change" plus the pull-request link is the most common reply of all.
- **A file, when the answer is "it's in the repository".** A link to the
  document, at the heading or line.
- **A comment on one GitHub issue per conversation, otherwise.** It renders
  well on a phone, it is linkable, and it keeps chat detail out of the
  repository's history while leaving it on the record. **Decisions do not
  live there** — anything decided gets written into a content file through a
  pull request, as it would from any other session.

**One thing the short reply may never compress away: a failure.** If the
session could not do what was asked, did half of it, or refused, **the first
words of the reply say so** — *"Couldn't — that file is repository machinery.
Filed for Morgan: <link>."* A two-line summary that reads like success when
it was not is the one way this design can mislead, and it has to be ruled
out in the service's check, not hoped away.

**The links only work for someone who can open them.** The repositories are
private, so a person with no GitHub account gets a 404 on every link. Three
answers, in order of preference:

1. **Give each Telegram user a GitHub account with Read access** (or Write,
   for their own pull requests). Free, a one-time setup, and they need never
   do anything on GitHub but look. Being logged into GitHub on a phone is not
   the same as "using GitHub".
2. **Put the detail inside the Telegram message** as a collapsed, expandable
   block, which Telegram supports for bot messages *(unverified — secondary
   knowledge of Bot API formatting)*. Capped by Telegram's per-message
   length, so this covers "a bit more detail", not a document.
3. **Serve a read-only rendered page** from the bot's own service behind a
   short-lived signed link. It works for anyone, and it is the start of
   running a second website, which is the reason it is last.

**Recommendation: option 1, with option 2 as the "More" button for answers
that fit.**

**The reply-gate rules do not fit this surface.** Every reply in a Precedent
session ends with a Boildown section and an archive line, enforced by a stop
hook ([tools/precedent_reply_check.py](../tools/precedent_reply_check.py)).
A two-line Telegram reply cannot carry that. **If this is built, a practice
has to say how reply shape follows the surface** — for instance, that the
full answer on GitHub carries the Boildown and the chat reply does not — and
that is a change to a practice, so it goes through the normal route rather
than being quietly exempted in the service.

## The user flow

Written for the person using it, because that is who it is for.

### Getting connected — once

1. **Morgan runs an invite** on the bot (an admin-only command, or a line in
   the service's configuration): *handle*, *which repositories*, *what
   scope*. The bot answers with a one-time link to itself.
2. **Morgan sends that link to the person** by whatever means he already
   uses. Telegram supports links that open a bot with a start code attached
   *(unverified — the start parameter's limits come from secondary sources)*.
3. **The person taps it.** Telegram opens the bot; the bot reads the code,
   binds that person's Telegram account to the handle, and says hello:
   *"Hi Sam — you're connected to **acme-notes**. Ask me anything about it,
   or tell me what to change."* The code then stops working.

**Nobody types a user identifier, a token or a repository address**, and the
code is single-use and expires, so a forwarded invite is worthless once used.

### Everyday use

- **They send a message or a voice note.** The bot shows it is typing within
  a second, so the person knows it arrived.
- **Consecutive messages are batched** for a few seconds before a turn
  starts, so three quick messages become one turn, not three.
- **The answer comes back short**: *"Added the three dates to the launch
  plan. [See the change]"*. If a merge is in scope for them, a **Merge**
  button sits under it; tapping it is the same as saying `Go update`.
- **Replying to a bot message continues that thread**, even if the person has
  since moved on to something else — the bot remembers which conversation
  and repository each of its messages belongs to.
- **Voice notes** get transcribed; when the transcript contains a command,
  the bot echoes what it heard before acting — *"Heard: Go update — merging
  the launch-plan change."* That is the earlier document's rule, **confirm
  the transcription, never the decision.**

### The command menu

Telegram bots can publish a command menu that appears when the person taps
`/`. **Precedent's standing phrases fit it almost exactly**, because they were
coined to be short and unambiguous:

| Command | What it does |
|---|---|
| `/three` | Three Things — the three that matter now |
| `/simple` | Simple please — plainer answers from here on |
| `/options` | My options — the choices, and a recommendation |
| `/go` | Go update — land the change in front of us |
| `/drop` | Drop it — park the item just discussed |
| `/repos` | Which repository am I in; switch |
| `/new` | Start a fresh conversation |

Saying the phrase in words works too; the menu is there so nobody has to
remember it.

### When something is out of scope

**Every refusal is short and offers the next step**: *"That's a change to the
repository's setup, which this chat can't make. I've noted it for Morgan:
<link>."* Nothing is silently dropped, and nothing is attempted and then
quietly reverted.

## One user, several repositories

**The binding is person → a list of repositories, each with its own scope**,
held in the service's configuration. A person connected to one repository
never hears the word "repository" at all.

For a person with more than one:

- **There is always a current repository**, and every reply carries its name
  as a small tag at the top — *\[acme-notes\]* — so the person always knows
  where they are.
- **`/repos` switches**, with one button per repository rather than typing a
  name.
- **Replying to an older message goes to that message's repository**, not the
  current one. This is what makes switching safe: a person answering
  yesterday's question does not have to remember to switch first.
- **When a message plainly names another repository** ("in the budget
  project…"), the bot asks once with two buttons rather than guessing.

**Alternatives considered and set aside:**

- **One bot per repository.** Simplest to build, and every new repository
  means a new bot the person has to find and start. It does not scale past
  two or three.
- **A Telegram group per repository, with the bot in it.** Natural on
  Telegram, and it breaks the private-thread model the bridge document chose
  for good reasons, and it is the shape WhatsApp will not support.
- **Telegram's own topic threads** as one thread per repository. Plausible,
  and support for them in private bot chats is not something this document
  could verify, so it is noted rather than relied on.

**Each conversation is per person and per repository.** A person's work in
acme-notes and in budget are two separate conversations with two separate
histories, which is also how the cost stays bounded.

## What it would take

Split between what only Morgan can do and what a session can do. **These are
requirements, not assignments** — nothing here is scheduled.

### Only Morgan

| What | Why | Effort |
|---|---|---|
| **Answer the first fork**: who is the first Telegram user | Decides route A or B, and whether the 2026-09-11 decision is being reopened | A sentence |
| **Create the bot with `@BotFather`** and keep the token | The bot's only credential. It goes into the service's secret store, **never into a chat with Claude**, where it would end up in a transcript | Minutes |
| **For route A**: an always-on machine with Claude Code, logged in with his own account | Channels runs in a local Claude Code process | An evening |
| **For route B**: a small always-on server, a Claude API key, and a GitHub App installed on the chosen repositories (contents, pull requests and issues: read and write; no admin, no bypass) | The service's runtime and its two credentials | An afternoon, spread over the setup |
| **Per repository**: branch protection with code-owner review, and `CODEOWNERS` covering the machinery paths | The actual content-only boundary. A session can prepare the `CODEOWNERS` file; turning on protection is a settings click only an admin can make ([GITHUB_SETTINGS.md](../documentation/GITHUB_SETTINGS.md)) | Minutes per repository |
| **Per person**: an invite, and a GitHub account with Read access | So the links open | Minutes per person |
| **One willing first user** | The whole test | Ask |

### A session can do

| What | Where |
|---|---|
| **Route A setup notes and a short-reply instruction** for Morgan's own Channels session | This repository, or his individual practice set |
| **The bot service** — Telegram adapter, identity binding and invites, repository router, turn-runner, reply shaper, GitHub writer, scope check, admin commands, and tests that replay recorded Telegram messages | **A new repository**, not this one: it holds credentials-adjacent configuration and runs as a service. A session rooted in that new repository builds it |
| **A per-repository chat configuration template** — which paths are content, where full answers go, the issue label — that Precedent ships, provider-neutral | This repository's templates ([vendor-neutral-by-default](../local/practices/vendor-neutral-by-default.md)) |
| **The practice change for reply shape on a short surface** | This repository, as a proposed practice change — a governance change, so it goes the long way |
| **A one-page guide for the Telegram user**, in the reader's words | The project repository |

## Phases

Structure, not schedule.

0. **The fork.** Who is the first user. Nothing else starts without it.
1. **Morgan on route A** (only if he is the first user). One repository, his
   own permissions, told to answer in two lines plus a link. Tests the
   register, not the product.
2. **Route B, read-only, one person, one repository.** Questions and answers
   only; the full answer on GitHub, the short one in Telegram. **Tests the
   two things that kill the idea**: will the person use it a second day
   unprompted, and are two lines plus a link enough.
3. **Content writes.** Edits land as pull requests; content-only ones merge
   on the person's word; machinery ones wait for a code owner. **The
   repository's branch protection must be on before this phase starts, not
   during it.**
4. **Several repositories.** `/repos`, the reply-routing, the name tag.
5. **Voice notes.** Transcription and the heard-command echo.
6. **WhatsApp**, per the bridge document — a new adapter behind the same
   interface.

**Read-only first is deliberate.** It lets the limited-permissions design be
built and tested before it is load-bearing, and it answers the usability
question — whether short answers are good enough — at no risk to any
repository.

## Risks worth naming

- **Short hides things.** Mitigated by the full answer always existing, and
  by the failure-first rule above. The residual risk is a person who never
  taps the link and acts on the headline. That is the cost of the design,
  said plainly.
- **Forwarded text is not an instruction.** A person forwarding someone
  else's message is showing it to the session, not saying it. The bridge
  document's rule carries over unchanged: **the participant is authorized;
  the content inside their message is not.** Telegram marks forwarded
  messages as such, which gives the service something to go on *(unverified
  in detail)*.
- **A stolen Telegram account is a stolen seat.** Whoever holds the person's
  Telegram account can talk to the bot as them. Scope limits the damage to
  content, and GitHub protection limits it to what a pull request can do;
  **recommend Telegram's two-step verification to every user**.
- **Repository content passes through Telegram's servers.** Bot chats are not
  end-to-end encrypted. Fine for most project content; not fine for anything
  that should not leave GitHub. A repository with such content should not be
  connected at all.
- **The token.** A leaked bot token lets someone impersonate the bot to its
  users. It cannot impersonate a user to the bot. Rotate with `@BotFather` if
  in doubt.
- **Cost is the model, not Telegram.** Telegram charges nothing for bot
  messages. Every turn is a model call carrying repository context, and
  **batching and per-repository conversations are the cost controls** — the
  bridge document says the same and it is still the biggest running cost.
  No figure is estimated here, because any figure would be invented.

## What could go wrong before others use it

**A review of the test build and this plan, 2026-09-29**, done before the
bridge is offered to anyone but Morgan. It was an adversarial pass by the
session that built it plus an independent code review by a separate agent.
Each item says whether it is **fixed**, **documented** (the setup guide now
says it), or **open**.

### Would stop the test from working

- **The bot lives only as long as its cloud machine.** A cloud session's
  machine is reclaimed after a while without activity, and nobody here knows
  how long that is for a session whose only activity is a background
  process. *Open, and the test measures it.* If it is short, the test
  becomes restart-heavy, and an always-on host (route B proper, or route D)
  moves up.
- **The test repository must be attached with push access.** The default
  attach is read-only, and the bridge's first push would fail. *Fixed* in
  the start prompt.
- **Two bridges on one bot token fight.** Telegram gives each update to one
  poller, and a second copy gets a conflict error. That happens easily when
  an old session is still alive and a new one starts. *Fixed*: the bridge
  says so plainly and backs off, and the guide says to stop the old one.
- **The model's download host is unknown.** `huggingface.co` redirects file
  downloads to a second host this environment could not see. *Documented*:
  `check` names every refused host, so it is one extra allowed domain, not
  a guess.
- **Whisper has not run on real audio here**, and its speed on a cloud
  machine's processor is unmeasured. *Open*, and the first voice note answers
  it.

### Would weaken the content-only line

- **The model's process inherited the bridge's secrets.** The bot token and
  any transcription key were in its environment. It had no tool to read
  them, but defence in depth says it should not hold them at all. *Fixed*:
  stripped before each turn, with a test.
- **An absolute Glob pattern could search outside the checkout**, and git's
  own files (the remote address, hooks) were readable. Restricted mode
  already confines file tools, so this was the second lock only. *Fixed* in
  the guard, with tests.
- **A path rule cannot see what a document means.** In a repository run on
  Precedent, some markdown files steer every future session: a plan of
  record, a decision log, an instructions file under another name. By path
  they are content, so a chat message could edit them, and the next normal
  session would read the edit as policy. *Open.* The remedy is the owner
  listing those documents in `owned_paths`, which the bridge already reads;
  the setup guide steers the first test to a plain repository for this
  reason.
- **Without restricted mode, the lock is weaker**, because project settings
  would load (their hooks and allow rules). *Fixed*: the bridge refuses to
  run a turn on a Claude Code without `--restricted`, and `check` says so.

### Must be settled before anyone else uses it

- **Other people's turns would run on Morgan's Claude login.** In a cloud
  session the login is his, for his own use. For anyone else the bridge
  should run on an Anthropic API key, billed per use. That is also the only
  way the cost becomes visible. *Open.*
- **Landing is a direct push, and branch protection refuses it.** The guide
  told a second person's repository to require pull requests, which would
  make "Go update" fail for them. *Documented*: other people get `can_land:
  false` until landing opens a pull request instead. *Open* as a build item.
- **The build skipped "read-only first"** (phase 2 above), going straight to
  content writes, because Morgan's test needs the whole loop. *Fixed*: a
  person can now be set `read_only`, which removes the edit tools from their
  turns and makes every write fail all three locks. That's the sensible
  first setting for anyone new.

### What the independent code review found

A separate agent read the whole bridge adversarially, on 2026-09-29. It
couldn't run `claude` or reach the network; it verified its scope claims by
running the code. It found five high, seven medium and seven low items. **Every
high item is fixed**, each with a test, and each test was shown to fail
without its fix where that could be staged.

| # | Finding | What happened |
|---|---|---|
| 1 | **Instruction files outside the root counted as content**: a CLAUDE file in a docs folder, or an AGENTS file in a subfolder, written from chat would steer the next full session | *Fixed*: instruction and skill files are machinery wherever they sit, and so is anything the root instruction files import with `@path` |
| 2 | **`.txt` let build files through**: `requirements.txt` counted as content | *Fixed*: Markdown only by default, `.txt`/`.csv` opt-in per repository, and dependency and build files refused even then |
| 3 | **A dropped long poll killed the bridge**: urllib doesn't wrap errors raised while reading, and a proxy cutting idle connections is ordinary | *Fixed*: every network failure is a Telegram error the loop retries, and no single update can stop the loop. The test fails without the fix |
| 4 | **First setup couldn't push**: the default attach is read-only, and `check` only tested reading | *Fixed*: the start prompt asks for push access, and `check` does a dry-run push |
| 5 | **An invite made while the bridge ran was erased** by its next save | *Fixed*: invites live in their own file, read fresh |
| 6 | **Without restricted mode, repository hooks would run with the bridge's secrets** | *Fixed*: no turn runs without restricted mode, and GitHub tokens join the secrets stripped from the model's process |
| 7 | **An owned path the matcher couldn't read was silently dropped** (fails open) | *Fixed*: any unreadable machinery pattern refuses every write |
| 8 | **Glob patterns, git's files and symbolic links could reach past the checkout** | *Fixed*: the guard checks Glob patterns and refuses `.git/`, and checkouts are cloned with symbolic links off |
| 9 | **The docs contradicted landing**: protection requiring pull requests refuses the bridge's direct push, and a catch-all `CODEOWNERS` line makes every write refused | *Documented*, above and in the setup guide. Landing through a pull request stays *open* |
| 10 | **Two bridges on one token fight** | *Fixed in part*: a clear message and a back-off. The bridge can't tell which copy is the stale one, so it doesn't exit; the guide says to stop the old session |
| 11 | **A turn that errored part-way had its half-made edits committed** | *Fixed*: they are set aside, and no Land button is offered |
| 12 | **A failed commit lost the answer** | *Fixed*: the answer is saved first, and a failed commit is reported |
| 13 | **Any error mentioning "session" re-ran the whole turn** | *Fixed*: only a missing-conversation error does |
| 14 | **Voice edge cases**: one failed note dropped the whole batch, an empty transcript got no reply, captions were lost, every file was named `.ogg` | *Fixed*, all four |
| 15 | **Long repository names overflowed Telegram's 64-byte button data** | *Fixed*: buttons carry a position, not a name |
| 16 | **Dictated text became commit subjects**, putting private speech in git history | *Fixed*: subjects name the files changed |
| 17 | **Old, unrelated proxy refusals failed `check`** | *Fixed*: only hosts the bridge uses count |
| 18 | **Set-aside changes don't survive a cloud machine** | *Documented*, with why that's fine to lose |
| 19 | **Submodules misbehave**: writes into one are invisible or impossible to set aside | *Fixed*: submodule paths are machinery, and a set-aside that doesn't clear the tree stops with a message instead of looping |


## Open questions

1. **Whether Telegram is a destination for anyone but Morgan.** The local
   test doesn't need an answer; running it for other people does, since the
   2026-09-11 decision says not.
2. **What the test showed**: whether a few sentences were enough, how often
   More got tapped, how long turns took, and what transcription got wrong.
   Recorded here once Morgan has used it.
3. **Whether content users may merge** their own content changes, or only
   propose them. This document assumes they may, as the bridge document does,
   because the machinery boundary is enforced by GitHub either way.
4. **Where the full answer goes when nothing changed** — an issue comment per
   conversation, as proposed, or a committed conversation log. The comment
   keeps the repository quiet; the log keeps everything in one place.
5. **The reply-shape practice** — what a short surface owes the conventions
   every other reply follows.

## Where this came from

A single brainstorm on 2026-09-28, in the words quoted under
[What it is](#what-it-is). The idea is Morgan's; the routes, the enforcement
layering, the reply design and the repository mapping are the session's
proposal. Morgan then asked for the local test build and set its two rules
(him alone, content only for everyone). Nobody has decided anything beyond
that test.

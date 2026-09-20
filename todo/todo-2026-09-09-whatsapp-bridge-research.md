---
slug:              todo-2026-09-09-whatsapp-bridge-research
kind:              verify
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "for the WhatsApp half, a Meta Business account, a business entity that clears verification, and a dedicated phone number — none of which exists yet and none of which a session can obtain. It is queued rather than done for that reason alone. It carries no disposition, so it is `wait` ([open-item-disp"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-09
closed:            null
---
## What

- <a id="whatsapp-bridge-research"></a>**Verify the chat bridge's platform claims against
   the platforms, or drop it.**
   [spec/SPECULATIVE_WHATSAPP_BRIDGE.md](../spec/SPECULATIVE_WHATSAPP_BRIDGE.md)
   designs a bot that gives each participant a private thread and
   commits what they say into a project repository — the hub-and-spoke shape
   that keeps the whole thing on Meta's official interface rather than a
   reverse-engineered client. **The desk half of this is done** (2026-09-11):
   that revision has the messaging-window rules, the per-message pricing model
   that replaced conversation pricing on 2025-07-01, the registration and
   verification requirements, and a Telegram-versus-WhatsApp comparison, with
   a costs section covering hosting and transcription as well as the
   interfaces. **What it does not have is a single claim read from a primary
   source**: `developers.facebook.com` and `core.telegram.org` are both
   blocked by this environment's network egress proxy, so every figure in it
   comes from vendor guides and pricing explainers, and the document says so
   in its own "What has actually been checked" section.
   What remains is therefore two things, in order. **The Telegram phase 1** —
   a bot token, the capture loop, one participant — needs no Meta anything and
   is not blocked on a person's errand at all; it is unstarted because nobody
   has decided to build it, not because anything is in the way. **The WhatsApp
   phase 2** is still the errand: register a test number, send and receive one
   message, and read the current rules off Meta's live documentation rather
   than off secondary sources
   ([no-invented-specifics](../practices/no-invented-specifics.md)). The open
   questions at the foot of that document are downstream of phase 2 and
   should not be answered before it — including the new one, whether a
   project digest is a utility or a marketing template, which is the
   difference between a free relay phase and a metered one.
   **The platform is not one of the open questions.** Morgan settled it on
   2026-09-11 (`strength: decided`, quoted in the document): the people this
   exists for are on WhatsApp and will not change apps, so Telegram is a
   rehearsal that ends and never the destination. A session triaging this
   item should not re-open it as "maybe just ship the Telegram one".
   **Nor is the shape.** Same day, same strength: it is a voice interface to
   a continuing Claude session, the way the Claude app's voice mode is, and
   the person merges their own work through it rather than queueing it for
   review. That turned one paragraph of the document into a real open
   problem, recorded there rather than here: the bot holds one credential and
   pushes as itself, so the GitHub collaborator role that
   [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md)
   relies on as its platform-enforced layer never binds the person behind the
   thread. **Anything built here needs a write-scope allowlist in the service
   itself**; an instruction to the session is not a boundary.
   **Blocked-on:** for the WhatsApp half, a Meta Business account, a business
   entity that clears verification, and a dedicated phone number — none of
   which exists yet and none of which a session can obtain. It is queued
   rather than done for that reason alone. It carries no disposition, so it is
   `wait` ([open-item-disposition](../practices/open-item-disposition.md)):
   nobody chases it, and nobody raises it unless Morgan asks.

## How It Closes

Not open until: for the WhatsApp half, a Meta Business account, a business entity that clears verification, and a dedicated phone number — none of which exists yet and none of which a session can obtain. It is queued rather than done for that reason alone. It carries no disposition, so it is `wait` ([open-item-disp

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

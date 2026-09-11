<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying this document into philosophy/; source: the project's own prior notes repository, content/COMPANY_BUILDING_RULES.md, version 23 -- that repository was made private and is being deleted, so philosophy/ is this document's home now, not a copy of one. -->

# Rules for Building a Company Around AI

*The "why" half of this repo's stage-1 pair — the case for running a
company this way at all. [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md)
is the "how" half, one level down: what it takes to build the AI systems
themselves so this becomes the default, rather than something a
disciplined person has to manufacture by hand every session.*

## Foundations

<a id="capital-asset"></a>

**1. Context is king.**

The scarce input isn't hours anymore — it's the tacit stuff that makes work
come out right: why the vendor failed, what the customer meant, which
option you already killed. Capturing it is capital expenditure, not
overhead. A *corpus* is a body — stop feeding it and it dies. Competitors
rent the same models by Thursday; what nobody can rent is yours.

Most of what follows leans on this one:
[`context-is-capital`](OUR_PHILOSOPHY.md#context-is-capital) states it as
theory,
[`durable-state-default`](AI_GOVERNANCE_TO_COCREATE.md#durable-state-default)
is the shape the state has to take for it to be true,
[`contradiction-scanning-recurring`](AI_GOVERNANCE_TO_COCREATE.md#contradiction-scanning-recurring)
is the upkeep a body needs, and
[`provider-neutrality-hedge`](AI_GOVERNANCE_TO_COCREATE.md#provider-neutrality-hedge)
is the bet that it can't be stranded —
[`provider-neutral-llm`](RULES_NOW_TESTING.md#provider-neutral-llm) was
that hedge written as code, until it was withdrawn.

<a id="transcribe-everything"></a>

**2. Transcribe everything, past the point of comfort.**

A colleague who's been here since the founding, remembers everything, and
has no eyes or ears, only text: the Ghost. Every untranscribed meeting
removes an organ. Most companies do the easy 5%; the bar is nearer 90%.
Whether the Ghost actually has what it needs is testable —
[`coldstart-test`](AI_GOVERNANCE_TO_COCREATE.md#coldstart-test) — and what
it buys is
[`protocols-generated-not-just-documented`](REASONS_WHY.md#protocols-generated-not-just-documented):
knowledge that outlives anyone's employment.

<a id="own-every-word"></a>

**3. You own every word you pass on.**

If you didn't read something closely enough to defend it, it doesn't leave
your hands — not to a colleague, a customer, or a deck someone else
presents while you're on a plane. What kills a company is four handoffs
where everyone skimmed and assumed the last person read it closely. The
error surfaces at the customer — the most expensive room, and the last one
you hear about.

## Working With the Model

<a id="ai-chat-as-intermediary"></a>

**4. Treat the AI Chat as the intermediary for the work itself, not a tool you consult on the side.**

Every plan runs through it first — not for the output, but for the
pushback: the hole in the logic, the option you missed. Arguing before you
commit becomes free. (Part of [CORE_PILLARS.md](CORE_PILLARS.md)'s case —
[`chat-is-the-entry-point`](CORE_PILLARS.md#chat-is-the-entry-point).)
What the arguing itself looks like:
[`arguing-with-the-model`](OUR_PHILOSOPHY.md#arguing-with-the-model). The
benefits nobody planned for:
[`intermediary-layer-side-benefits`](REASONS_WHY.md#intermediary-layer-side-benefits).

<a id="co-create-dont-delegate"></a>

**5. Co-create; don't delegate.**

The low-value mode is "produce this for me and I'll edit it." The
high-value mode is thinking with the model in real time — arguing the
opposite side, asking for the hole in your logic before you've committed.
The tell: sessions that read like fights, not requests. Research and
drafting are the beginner uses; the real gain is catching your own error
an hour later, not three weeks later in front of the client — which is
[`wrong-gets-cheap-early`](REASONS_WHY.md#wrong-gets-cheap-early)'s whole
point. Stated as theory in
[`arguing-with-the-model`](OUR_PHILOSOPHY.md#arguing-with-the-model);
[`argue-in-the-open`](RULES_NOW_TESTING.md#argue-in-the-open) is the half
of it being tried in public.

<a id="think-in-workflows"></a>

**6. Think in patterns, workflows, and protocols.**

Don't systematize a one-off — first time, by hand, with the model. Third
time you've seen the shape, stop: that's the workflow spec. A protocol
needs only one judgment call. Systematize everything and you ship nothing,
beautifully diagrammed. Noticing the third time is the hard part:
[`three-reflexes-in-system-prompt`](AI_GOVERNANCE_TO_COCREATE.md#three-reflexes-in-system-prompt)
makes an agent ask mid-task, and
[`automatic-workflow-detection`](AI_GOVERNANCE_TO_COCREATE.md#automatic-workflow-detection)
mines the history so nobody has to notice at all.

<a id="three-questions"></a>

**7. Three questions, asked until they're reflexes.**

A long checklist buys you people who spend the day interrogating their
work instead of doing it. So: three questions, drilled until they're
reflexes — the same three the AI is running too:

- What rules or protocols should come from this? If you decided it once,
  you'll decide it again — write it down now.
- Have I done this shape before, or will I again? If yes, it's a
  workflow, and you're doing it by hand.
- Is there a way AI Assistant could make this better? Not faster — better.

*Faster* gets people thinking about the work they already do. *Better*
gets them noticing the work they'd quietly stopped proposing.

In the system prompt rather than a person's habit:
[`three-reflexes-in-system-prompt`](AI_GOVERNANCE_TO_COCREATE.md#three-reflexes-in-system-prompt).
Answered out loud mid-task, which is what is actually being tried:
[`three-reflexes-out-loud`](RULES_NOW_TESTING.md#three-reflexes-out-loud).

## Shipping and Process

<a id="no-dark-processes"></a>

**8. No dark processes.**

A workflow triggered only by emailing a person becomes the bottleneck
for everything downstream. Kill every process whose only interface is
somebody's inbox: "just email me" is a process going dark. It sounds
technical but is political — every dark process is dark for a reason,
with a name and a desk attached. Why this matters past tidiness:
[`processes-should-be-visible`](OUR_PHILOSOPHY.md#processes-should-be-visible).
[`ai-hunts-dark-processes`](AI_GOVERNANCE_TO_COCREATE.md#ai-hunts-dark-processes)
makes the hunt a standing job;
[`dark-process-self-audit`](RULES_NOW_TESTING.md#dark-process-self-audit)
is that job run by hand today.

<a id="build-five-kill-four"></a>

**9. Build five, kill four.**

When an option costs nearly nothing to build, deliberating first is a
bad trade. Bring several working versions, not a deck arguing for one —
killing is the point, not the count. This only works where killing
costs nothing socially, not where the loser's fate follows them into
review. When this lavishness is the right posture and when it isn't is
[`cost-awareness-situational`](AI_GOVERNANCE_TO_COCREATE.md#cost-awareness-situational)'s
problem, not a policy anyone sets once.

<a id="digitize-the-edge"></a>

**10. Digitize the edge, where the atoms are.**

If you make, move, install, or repair physical things, the untouched
value sits at the analog frontier, precisely because reaching it is
annoying: photos of every job, sensor logs, a voice note before the
next call. The Ghost can't climb a ladder or smell burnt wiring. Convert
that reality into text and the other rules open up.

<a id="no-ai-voice"></a>

**11. Nothing you ship may sound like it came from an AI.**

The default register — the throat-clearing opener, "not just X, it's Y,"
the bolded summary nobody asked for — reads as nobody home. Unrewritten output is output
nobody thought about. Ship it in your voice. (Now
[`write-like-a-human`](../practices/write-like-a-human.md), universal since
2026-09-07; [how it got there](RULES_NOW_TESTING.md#write-like-a-human).)
The fingerprints are mechanical enough to check for before publishing:
[`structural-ai-voice-check`](AI_GOVERNANCE_TO_COCREATE.md#structural-ai-voice-check).

## People

<a id="hire-for-drive"></a>

**12. Hire for drive, "Getting Sh\*t Done," relationships, and taste.**

The bottleneck isn't making things, it's judging them fast and shipping
them — production is the trait models absorbed first. Hire someone who
gets things done unmanaged, who builds relationships a counterparty
trusts, and who has taste — one part of the picture, not the headline.
(Drive
([`getting-things-done`](HUMANS_AT_OUR_BEST.md#getting-things-done)),
[`relationships`](HUMANS_AT_OUR_BEST.md#relationships) and
[`taste`](HUMANS_AT_OUR_BEST.md#taste) are three entries on the one full
list of what stays human — see
[HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md).) The skill this is really
hiring for is
[`instinct-catches-what-checklists-miss`](REASONS_WHY.md#instinct-catches-what-checklists-miss);
[`non-uniform-confidence`](AI_GOVERNANCE_TO_COCREATE.md#non-uniform-confidence)
is what a model owes it back — somewhere to start looking.

<a id="manager-of-agents"></a>

**13. Give the agents a manager — a human over the loop, not in it.**

"In the loop" became jargon for a rubber stamp — approving every step,
since nobody scrutinizes step four thousand like step one. What's
missing is someone whose job is the fleet itself: watching drift,
retuning prompts and guardrails, deciding when a step needs a human
again. Call the role Manager of Agents or don't, but staff it. The posture
it is staffed for is
[`people-manage-agents-execute`](OUR_PHILOSOPHY.md#people-manage-agents-execute).

<a id="human-only-zones"></a>

**14. Protect human-only zones on purpose, and put them on the calendar.**

If everyone consumes only summaries, nobody can detect the moment they
drift — everything still reads coherent. Mandate raw contact as ritual —
founders reading unfiltered complaints, managers watching real work in
silence — and put it on the calendar so it survives being inconvenient.
Drift caught this way is the same saving as
[`wrong-gets-cheap-early`](REASONS_WHY.md#wrong-gets-cheap-early), bought
on the one error a checklist can't see.

<a id="structurally-human"></a>

**15. Reserve the permanent hire for what's structurally human.**

Permanent roles rest on what a model can't do at all —
[`judgment`](HUMANS_AT_OUR_BEST.md#judgment) when the rules run out,
[`taste`](HUMANS_AT_OUR_BEST.md#taste) that catches the wrong paragraph,
[`relationships`](HUMANS_AT_OUR_BEST.md#relationships) a counterparty
trusts, [`accountability`](HUMANS_AT_OUR_BEST.md#accountability) on one
name, [`the-human-spark`](HUMANS_AT_OUR_BEST.md#the-human-spark).
([HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md))

Stated as theory in
[`humans-do-what-humans-do-best`](OUR_PHILOSOPHY.md#humans-do-what-humans-do-best).
Read too literally it sunsets arrangements that are working, which is
[`periodic-checkins-not-expiry`](AI_GOVERNANCE_TO_COCREATE.md#periodic-checkins-not-expiry)'s
correction to it.

## See Also

- [CORE_PILLARS.md](CORE_PILLARS.md) — the one-page pitch: the core ideas
  this approach argues are unique, specifically taken together.
- [OUR_PHILOSOPHY.md](OUR_PHILOSOPHY.md) — the underlying theoretical
  ideas everything else here assumes, named and explained on their own
  terms.
- [REASONS_WHY.md](REASONS_WHY.md) — the less obvious benefits those
  ideas actually produce in practice.
- [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md) — the
  standalone essay on how AI systems themselves should be configured,
  built, and run.
- [HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md) — the one list of what
  humans are good at, gathered from the shorter versions scattered here
  and elsewhere.

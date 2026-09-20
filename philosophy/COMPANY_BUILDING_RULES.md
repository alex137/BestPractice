<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying this document into philosophy/; source: the project's own prior notes repository, content/COMPANY_BUILDING_RULES.md, version 23 -- that repository was made private and is being deleted, so philosophy/ is this document's home now, not a copy of one. -->

# Rules for Building a Company Around AI

*The "why" half of this repo's stage-1 pair — the case for running a
company this way at all. [AI Governance to Co-Create](AI_GOVERNANCE_TO_COCREATE.md)
is the "how" half, one level down: what it takes to build the AI systems
themselves so this becomes the default, rather than something a
disciplined person has to manufacture by hand every session.*

## Foundations

<a id="capital-asset"></a>

**1. Context is king.**

The scarce input is tacit: why the vendor failed, the option you already
killed. Capturing it is capital expenditure
([`context-is-capital`](OUR_PHILOSOPHY.md#context-is-capital),
[`durable-state-default`](AI_GOVERNANCE_TO_COCREATE.md#durable-state-default)),
a *corpus* that dies if nothing re-reads it
([`contradiction-scanning-recurring`](AI_GOVERNANCE_TO_COCREATE.md#contradiction-scanning-recurring)).
Competitors rent the same models; what's yours can't be, unless a
provider switch strands it
([`provider-neutrality-hedge`](AI_GOVERNANCE_TO_COCREATE.md#provider-neutrality-hedge)).

<a id="transcribe-everything"></a>

**2. Transcribe everything, past the point of comfort.**

A colleague who's been here since the founding, remembers everything, and
has no eyes or ears, only text: the Ghost. Every untranscribed meeting
removes an organ. Most companies do the easy 5%;
the bar is nearer 90% and never 100%, since some of it is
[`the-unspoken`](HUMANS_AT_OUR_BEST.md#the-unspoken) — testable as [`coldstart-test`](AI_GOVERNANCE_TO_COCREATE.md#coldstart-test),
and worth it for
[`protocols-generated-not-just-documented`](REASONS_WHY.md#protocols-generated-not-just-documented).

<a id="own-every-word"></a>

**3. You own every word you pass on.**

If you didn't read it closely enough to defend it, it doesn't leave your
hands — [`accountability`](HUMANS_AT_OUR_BEST.md#accountability) and
[`obsessive-ownership`](HUMANS_AT_OUR_BEST.md#obsessive-ownership) at the scale of one
sentence. What kills a company is four handoffs where everyone skimmed;
the error surfaces at the customer, the last room you hear about
([`wrong-gets-cheap-early`](REASONS_WHY.md#wrong-gets-cheap-early), run backwards).

## Rules for Working With the Model

<a id="ai-chat-as-intermediary"></a>

**4. Treat the AI Chat as the intermediary for the work itself, not a tool you consult on the side.**

Every plan runs through it first — not for the output, but for the
pushback: the hole in the logic, the option you missed
([`arguing-with-the-model`](OUR_PHILOSOPHY.md#arguing-with-the-model)). Arguing before
you commit becomes free; the rest arrives unplanned
([`intermediary-layer-side-benefits`](REASONS_WHY.md#intermediary-layer-side-benefits)).
One of [Core Pillars](CORE_PILLARS.md)'s four
([`chat-is-the-entry-point`](CORE_PILLARS.md#chat-is-the-entry-point));
built in rather than practised,
[`chat-is-primary-interface`](AI_GOVERNANCE_TO_COCREATE.md#chat-is-primary-interface).

<a id="co-create-dont-delegate"></a>

**5. Co-create; don't delegate.**

The low-value mode is "produce this and I'll edit it"; the high-value mode
is thinking with the model in real time, arguing the opposite side before
you've committed ([`arguing-with-the-model`](OUR_PHILOSOPHY.md#arguing-with-the-model)). The tell: sessions
that read like fights. The gain is catching your error an hour later, not
three weeks later at the client
([`wrong-gets-cheap-early`](REASONS_WHY.md#wrong-gets-cheap-early)).

<a id="think-in-workflows"></a>

**6. Think in patterns, workflows, and protocols.**

Don't systematize a one-off — first time, by hand, with the model. Third
time you've seen the shape, stop: that's the workflow spec. Noticing the
third time is the hard part
([`three-reflexes-in-system-prompt`](AI_GOVERNANCE_TO_COCREATE.md#three-reflexes-in-system-prompt)
asks mid-task;
[`automatic-workflow-detection`](AI_GOVERNANCE_TO_COCREATE.md#automatic-workflow-detection) mines the
history instead). A protocol needs only one judgment call. Systematize
everything and you ship nothing, beautifully diagrammed.

<a id="five-whys"></a>

**7. The Five Whys: focus on the problem.**

Don't focus on finding the solution — focus on getting to the root of the
issue. Keep asking why; keep finding and describing problems, and push the
AI Assistants to solve them — the practice
[`explain-the-why`](OUR_PHILOSOPHY.md#explain-the-why) asks of every single
request, and a [Core Pillars](CORE_PILLARS.md) pillar,
[`focus-on-whys-problems`](CORE_PILLARS.md#focus-on-whys-problems). It's a
trained method for what starts as a human reflex,
[`why`](HUMANS_AT_OUR_BEST.md#why).

## Shipping and Process

<a id="no-dark-processes"></a>

**8. No dark processes.**

A workflow triggered only by emailing a person becomes the bottleneck
for everything downstream. Kill every process whose only interface is
somebody's inbox: "just email me" is a process going dark. It sounds
technical but is [`politics`](HUMANS_AT_OUR_BEST.md#politics) — every dark process is dark
for a reason, with a name and a desk attached
([`processes-should-be-visible`](OUR_PHILOSOPHY.md#processes-should-be-visible)). A
standing job for the AI
([`ai-hunts-dark-processes`](AI_GOVERNANCE_TO_COCREATE.md#ai-hunts-dark-processes)).

<a id="build-five-kill-four"></a>

**9. Build five, kill four.**

When an option costs nothing to build, deliberating first is a bad trade.
Bring several working versions, not a deck arguing for one — a wrong idea
dies before it acquires allies
([`wrong-gets-cheap-early`](REASONS_WHY.md#wrong-gets-cheap-early)). Only where killing
costs nothing socially, and not where the pick itself costs something
([`trade-offs-and-hard-decisions`](HUMANS_AT_OUR_BEST.md#trade-offs-and-hard-decisions)).
Whether it fits is
[`cost-awareness-situational`](AI_GOVERNANCE_TO_COCREATE.md#cost-awareness-situational), never a
policy set once.

<a id="no-ai-voice"></a>

**10. Nothing you ship may sound like it came from an AI.**

The default register — the throat-clearing opener, "not just X, it's Y,"
the bolded summary nobody asked for — reads as nobody home. Unrewritten output is output
nobody thought about. Ship it in your voice; the fingerprints are
mechanical enough to check for
([`structural-ai-voice-check`](AI_GOVERNANCE_TO_COCREATE.md#structural-ai-voice-check)). (Now
[`write-like-a-human`](../practices/write-like-a-human.md), universal since
2026-09-07.) The same flattening shows up past prose, too —
[`weirdness`](HUMANS_AT_OUR_BEST.md#weirdness) names the general case.

## People

<a id="hire-for-drive"></a>

**11. Hire for drive, "Getting Sh\*t Done," relationships, and taste.**

The bottleneck isn't making things, it's judging them fast — production is
what models absorbed first. Hire someone who gets things done unmanaged
([`getting-things-done`](HUMANS_AT_OUR_BEST.md#getting-things-done)), who builds
[`relationships`](HUMANS_AT_OUR_BEST.md#relationships) a counterparty trusts, and who has
[`taste`](HUMANS_AT_OUR_BEST.md#taste). You are buying
[`instinct-catches-what-checklists-miss`](REASONS_WHY.md#instinct-catches-what-checklists-miss);
[`non-uniform-confidence`](AI_GOVERNANCE_TO_COCREATE.md#non-uniform-confidence) is what a model owes
back.

<a id="manager-of-agents"></a>

**12. Give the agents a manager — a human over the loop, not in it.**

"In the loop" became jargon for a rubber stamp: nobody scrutinizes step
four thousand like step one. Staff the fleet itself: watching drift, retuning guardrails
([`boundary-pushing`](HUMANS_AT_OUR_BEST.md#boundary-pushing) as a job), deciding when a step
needs a human again — [`actually-managing`](HUMANS_AT_OUR_BEST.md#actually-managing) pointed
at agents ([`people-manage-agents-execute`](OUR_PHILOSOPHY.md#people-manage-agents-execute)).

<a id="structurally-human"></a>

**13. Lean the permanent hire toward what's structurally human.**

The clearest case for a permanent role is work a model can't do at all:
[`judgment`](HUMANS_AT_OUR_BEST.md#judgment) when the rules run out, [`taste`](HUMANS_AT_OUR_BEST.md#taste) that
catches the wrong paragraph, [`relationships`](HUMANS_AT_OUR_BEST.md#relationships) a
counterparty trusts, [`accountability`](HUMANS_AT_OUR_BEST.md#accountability) on one name,
[`the-human-spark`](HUMANS_AT_OUR_BEST.md#the-human-spark). Where the weight goes, not the
only thing a permanent role may be for. Theory:
[`humans-do-what-humans-do-best`](OUR_PHILOSOPHY.md#humans-do-what-humans-do-best); read
too literally it sunsets what works, which
[`periodic-checkins-not-expiry`](AI_GOVERNANCE_TO_COCREATE.md#periodic-checkins-not-expiry)
corrects.

## See Also

- [Core Pillars](CORE_PILLARS.md) — the one-page pitch: the core ideas
  this approach argues are unique, specifically taken together.
- [Our Philosophy](OUR_PHILOSOPHY.md) — the underlying theoretical
  ideas everything else here assumes, named and explained on their own
  terms.
- [The Working Loop](THE_WORKING_LOOP.md) — the six-step cycle those
  ideas run through, end to end.
- [Reasons Why](REASONS_WHY.md) — the less obvious benefits those
  ideas actually produce in practice.
- [The Talmudic Method](THE_TALMUDIC_METHOD.md) — the resemblance between
  what this system insists on and how the Talmud gets studied, argument
  by argument.
- [AI Governance to Co-Create](AI_GOVERNANCE_TO_COCREATE.md) — the
  standalone essay on how AI systems themselves should be configured,
  built, and run.
- [Humans at Our Best](HUMANS_AT_OUR_BEST.md) — the one list of what
  humans are good at, gathered from the shorter versions scattered here
  and elsewhere.

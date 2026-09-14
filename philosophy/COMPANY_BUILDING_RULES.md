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

The scarce input is the tacit stuff: why the vendor failed, which option
you already killed. Capturing it is capital expenditure
([`context-is-capital`](OUR_PHILOSOPHY.md#context-is-capital), kept as
[`durable-state-default`](AI_GOVERNANCE_TO_COCREATE.md#durable-state-default)), and a *corpus* is a
body: stop feeding it and it dies, and nothing re-reads it unasked
([`contradiction-scanning-recurring`](AI_GOVERNANCE_TO_COCREATE.md#contradiction-scanning-recurring)).
Competitors rent the same models by Thursday; what nobody can rent is
yours — unless a provider switch strands it
([`provider-neutrality-hedge`](AI_GOVERNANCE_TO_COCREATE.md#provider-neutrality-hedge); as code, the
withdrawn [`provider-neutral-llm`](RULES_NOW_TESTING.md#provider-neutral-llm)).

<a id="transcribe-everything"></a>

**2. Transcribe everything, past the point of comfort.**

A colleague who's been here since the founding, remembers everything, and
has no eyes or ears, only text: the Ghost. Every untranscribed meeting
removes an organ; what never became text at all is
[`digitize-the-edge`](#digitize-the-edge)'s. Most companies do the easy 5%;
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

## Working With the Model

<a id="ai-chat-as-intermediary"></a>

**4. Treat the AI Chat as the intermediary for the work itself, not a tool you consult on the side.**

Every plan runs through it first — not for the output, but for the
pushback: the hole in the logic, the option you missed
([`arguing-with-the-model`](OUR_PHILOSOPHY.md#arguing-with-the-model)). Arguing before
you commit becomes free; the rest arrives unplanned
([`intermediary-layer-side-benefits`](REASONS_WHY.md#intermediary-layer-side-benefits)).
One of [CORE_PILLARS.md](CORE_PILLARS.md)'s four
([`chat-is-the-entry-point`](CORE_PILLARS.md#chat-is-the-entry-point));
built in rather than practised,
[`chat-is-primary-interface`](AI_GOVERNANCE_TO_COCREATE.md#chat-is-primary-interface).

<a id="co-create-dont-delegate"></a>

**5. Co-create; don't delegate.**

The low-value mode is "produce this and I'll edit it"; the high-value mode
is thinking with the model in real time, arguing the opposite side before
you've committed ([`arguing-with-the-model`](OUR_PHILOSOPHY.md#arguing-with-the-model); in
public, [`argue-in-the-open`](RULES_NOW_TESTING.md#argue-in-the-open)). The tell: sessions
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

<a id="three-questions"></a>

**7. Three questions, asked until they're reflexes.**

A long checklist buys interrogation instead of work. Three questions,
drilled until they're reflexes:

- What rule should come from this? You'll decide it again; write it now.
- Have I done this shape before, or will I again? Then it's a workflow.
- Could AI Assistant make this better? Not faster — better.

*Better* is the one that earns its keep. All three are a cheap substitute
for [`questions`](HUMANS_AT_OUR_BEST.md#questions), which nobody can be drilled into: in the
system prompt as
[`three-reflexes-in-system-prompt`](AI_GOVERNANCE_TO_COCREATE.md#three-reflexes-in-system-prompt),
out loud mid-task as
[`three-reflexes-out-loud`](RULES_NOW_TESTING.md#three-reflexes-out-loud).

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
([`ai-hunts-dark-processes`](AI_GOVERNANCE_TO_COCREATE.md#ai-hunts-dark-processes)), run by hand as
[`dark-process-self-audit`](RULES_NOW_TESTING.md#dark-process-self-audit).

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

<a id="digitize-the-edge"></a>

**10. Digitize the edge, where the atoms are.**

If you make, move, install or repair physical things, the untouched value
sits at the analog frontier, precisely because reaching it is annoying:
photos of every job, sensor logs, a voice note before the next call. The
Ghost can't climb a ladder or smell burnt wiring
([`sense-of-smell`](HUMANS_AT_OUR_BEST.md#sense-of-smell)), or check the record against the
site ([`verification`](HUMANS_AT_OUR_BEST.md#verification)) — the
[`dirtiness-of-real-life`](HUMANS_AT_OUR_BEST.md#dirtiness-of-real-life). Convert it to text
([`transcribe-everything`](#transcribe-everything)) and the other rules
open up.

<a id="no-ai-voice"></a>

**11. Nothing you ship may sound like it came from an AI.**

The default register — the throat-clearing opener, "not just X, it's Y,"
the bolded summary nobody asked for — reads as nobody home. Unrewritten output is output
nobody thought about. Ship it in your voice; the fingerprints are
mechanical enough to check for
([`structural-ai-voice-check`](AI_GOVERNANCE_TO_COCREATE.md#structural-ai-voice-check)). (Now
[`write-like-a-human`](../practices/write-like-a-human.md), universal since
2026-09-07; [how it got there](RULES_NOW_TESTING.md#write-like-a-human).)

## People

<a id="hire-for-drive"></a>

**12. Hire for drive, "Getting Sh\*t Done," relationships, and taste.**

The bottleneck isn't making things, it's judging them fast — production is
what models absorbed first. Hire someone who gets things done unmanaged
([`getting-things-done`](HUMANS_AT_OUR_BEST.md#getting-things-done)), who builds
[`relationships`](HUMANS_AT_OUR_BEST.md#relationships) a counterparty trusts, and who has
[`taste`](HUMANS_AT_OUR_BEST.md#taste). You are buying
[`instinct-catches-what-checklists-miss`](REASONS_WHY.md#instinct-catches-what-checklists-miss);
[`non-uniform-confidence`](AI_GOVERNANCE_TO_COCREATE.md#non-uniform-confidence) is what a model owes
back.

<a id="manager-of-agents"></a>

**13. Give the agents a manager — a human over the loop, not in it.**

"In the loop" became jargon for a rubber stamp: nobody scrutinizes step
four thousand like step one. Staff the fleet itself: watching drift, retuning guardrails
([`boundary-pushing`](HUMANS_AT_OUR_BEST.md#boundary-pushing) as a job), deciding when a step
needs a human again — [`actually-managing`](HUMANS_AT_OUR_BEST.md#actually-managing) pointed
at agents ([`people-manage-agents-execute`](OUR_PHILOSOPHY.md#people-manage-agents-execute)).

<a id="human-only-zones"></a>

**14. Protect human-only zones on purpose, and put them on the calendar.**

If everyone consumes only summaries, nobody detects the moment they drift —
everything still reads coherent. Mandate raw contact as ritual: founders
reading unfiltered complaints, managers watching real work in silence. Put
it on the calendar so it survives being inconvenient. That is
[`wrong-gets-cheap-early`](REASONS_WHY.md#wrong-gets-cheap-early) on the error no
checklist sees.

<a id="structurally-human"></a>

**15. Lean the permanent hire toward what's structurally human.**

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

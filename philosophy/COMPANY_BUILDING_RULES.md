<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying this document from WorkingWithAI into philosophy/; source: themorgan/WorkingWithAI content/COMPANY_BUILDING_RULES.md, version 21. -->

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

<a id="transcribe-everything"></a>

**2. Transcribe everything, past the point of comfort.**

Meetings, calls, site visits, the argument that got resolved and the one
that didn't — transcribe it. Picture a colleague who's been there since
the founding, remembers everything, never sleeps, with no eyes or ears,
only text: the Ghost, the most experienced employee in the building,
unable to attend anything. Every untranscribed meeting removes one more
organ from it. Most companies do the easy 5%; what matters is nearer 90%,
and closing that gap is cultural — people need to hear *compounding*, not
*recorded*.

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

Every plan worth a thought runs through it before anyone else — not for
the output, but because it's the partner that pushes back: the hole in the
logic, the option you missed, the better version. That layer also pushes
things into happening — the commit, the message, the next step — instead
of a good idea that never left somebody's head. Put a model between intent
and action, and arguing before you commit becomes free. (One part of
[CORE_PILLARS.md](CORE_PILLARS.md)'s case for
what makes this approach unique.)

<a id="co-create-dont-delegate"></a>

**5. Co-create; don't delegate.**

The low-value mode is "produce this for me and I'll edit it." The
high-value mode is thinking with the model in real time — arguing the
opposite side, asking for the hole in your logic before you've committed.
The tell: sessions that read like fights, not requests. Research and
drafting are the beginner uses; the real gain is catching your own error
an hour later, not three weeks later in front of the client.

<a id="think-in-workflows"></a>

**6. Think in patterns, workflows, and protocols.**

Stopping to systematize a one-off is procrastination in a nice suit. First
time, do it by hand, with the model. Third time you've seen the shape,
stop — that's a pattern, and it just handed you the workflow spec for
free. A protocol is different: it needs no repeating task, just one
judgment call worth remembering, captured the moment it happens. Never
systematize and you stay fast forever; systematize everything and you
ship nothing, beautifully diagrammed.

<a id="three-questions"></a>

**7. Three questions, asked until they're reflexes.**

A long checklist buys you people who spend the day interrogating their
work instead of doing it. So: three questions, drilled until they're
reflexes — the same three the AI is running too:

- What rules or protocols should come from this?
- Have I done this shape before, or will I again? If yes, it's a
  workflow, and you're doing it by hand.
- Is there a way AI Assistant could make this better? Not faster — better.

*Faster* gets people thinking about the work they already do. *Better*
gets them noticing the work they'd quietly stopped proposing.

## Shipping and Process

<a id="no-dark-processes"></a>

**8. No dark processes.**

A workflow triggered only by emailing a person becomes the bottleneck
for everything downstream. Kill every process whose only interface is
somebody's inbox: "just email me" is a process going dark. It sounds
technical but is political — every dark process is dark for a reason,
with a name and a desk attached.

<a id="build-five-kill-four"></a>

**9. Build five, kill four.**

When an option costs nearly nothing to build, deliberating first is a
bad trade. Bring several working versions, not a deck arguing for one —
killing is the point, not the count. This only works where killing
costs nothing socially, not where the loser's fate follows them into
review.

<a id="digitize-the-edge"></a>

**10. Digitize the edge, where the atoms are.**

If you make, move, install, or repair physical things, the untouched
value sits at the analog frontier, precisely because reaching it is
annoying: photos of every job, sensor logs, a voice note before the
next call. The Ghost can't climb a ladder or smell burnt wiring. Convert
that reality into text and the other rules open up.

<a id="no-ai-voice"></a>

**11. Nothing you ship may sound like it came from an AI.**

The default register — the throat-clearing opener, "it's not just X, it's
Y," the bolded summary nobody asked for — reads as nobody home, and
erodes trust fast. It's evidence too: unrewritten output is output
nobody thought about — style enforces thinking. And it's positioning:
what you sound like is the one claim a reader can check for free. Ship
everything rewritten in your own voice. (Enforced, not just argued for:
[process/voice/HUMAN_VOICE_RULES.md](https://github.com/themorgan/WorkingWithAI/blob/main/process/voice/HUMAN_VOICE_RULES.md),
tried here as
[`write-like-a-human`](RULES_NOW_TESTING.md#write-like-a-human).)

## People

<a id="hire-for-drive"></a>

**12. Hire for drive, "Getting Sh\*t Done," relationships, and taste.**

The bottleneck isn't making things, it's judging them fast and shipping
them — production is the trait models absorbed first. Hire someone who
gets things done unmanaged, who builds relationships a counterparty
trusts, and who has taste — one part of the picture, not the headline.
(Drive, relationships, and taste are three entries on the one full list
of what stays human — see
[HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md).)

<a id="manager-of-agents"></a>

**13. Give the agents a manager — a human over the loop, not in it.**

"In the loop" became jargon for a rubber stamp — approving every step,
since nobody scrutinizes step four thousand like step one. What's
missing is someone whose job is the fleet itself: watching drift,
retuning prompts and guardrails, deciding when a step needs a human
again. Call the role Manager of Agents or don't, but staff it.

<a id="human-only-zones"></a>

**14. Protect human-only zones on purpose, and put them on the calendar.**

If everyone consumes only summaries, nobody can detect the moment they
drift — everything still reads coherent. Mandate raw contact as ritual —
founders reading unfiltered complaints, managers watching real work in
silence — and put it on the calendar so it survives being inconvenient.

<a id="structurally-human"></a>

**15. Reserve the permanent hire for what's structurally human.**

Follow every rule here and they land in one place: the roles worth
making permanent are built on something a model can't do at all.
Judgment when the rules run out. Taste that catches the one wrong
paragraph in twenty. Relationships a counterparty trusts. Accountability
on one name, not a faceless process. The human spark that makes someone
worth working for, not merely alongside. And, increasingly, the
discipline of running agent-driven processes. (Full list:
[HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md).)

## See Also

- [OUR_PHILOSOPHY.md](OUR_PHILOSOPHY.md) — the underlying theoretical
  ideas everything else here assumes, named and explained on their own
  terms.
- [REASONS_WHY.md](REASONS_WHY.md) — the less obvious benefits those
  ideas actually produce in practice.
- [HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md) — the one list of what
  humans are good at, gathered from the shorter versions scattered here
  and elsewhere.
- [RANDOM_NOTES.md](RANDOM_NOTES.md) — the brainstorm itself, pipeline
  stage 1.
- [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md) —
  standalone essay promoted out of the brainstorm: how AI systems
  themselves should be configured, built, and run.
- [RULES_NOW_TESTING.md](RULES_NOW_TESTING.md) — pipeline stage 2: the
  practical rules actually being tried in real work right now.
- [CORE_PILLARS.md](CORE_PILLARS.md) — one-page
  pitch: the core ideas this repo argues are unique specifically taken
  together.

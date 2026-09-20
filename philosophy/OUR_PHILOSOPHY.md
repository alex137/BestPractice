<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying this document into philosophy/; source: the project's own prior notes repository, content/OUR_PHILOSOPHY.md, version 41 -- that repository was made private and is being deleted, so philosophy/ is this document's home now, not a copy of one. -->

# Our Philosophy

*The theoretical layer underneath everything else in this repo, not a new
argument. [Core Pillars](CORE_PILLARS.md) is the short version of what
follows — the four pillars it names are what these ideas add up to, and
what [Reasons Why](REASONS_WHY.md)'s payoffs come out of.
[Company Building Rules](COMPANY_BUILDING_RULES.md) makes the case for
running a company this way; [AI Governance to Co-Create](AI_GOVERNANCE_TO_COCREATE.md)
makes the case for building the AI systems that way. Both assume a handful
of ideas about memory,
[judgment](HUMANS_AT_OUR_BEST.md), and how work actually produces quality.
It's an account of the theory, not a pitch for it. The cycle these ideas
run through end to end, step by step, is
[The Working Loop](THE_WORKING_LOOP.md)'s own page.*

## Groups, Not Individuals

<a id="groups-not-individuals"></a>

**1. Built for groups, not individuals working alone with a model.** Most
"work better with AI" advice makes one person faster at their own
work. This repo assumes something different: several people solving the
same problem together, with chat as what connects them, not a private
assistant each person also has, where joining costs a repository access
rather than a day of setup ([`cloud-not-local`](AI_GOVERNANCE_TO_COCREATE.md#cloud-not-local)). (One
part of [Core Pillars](CORE_PILLARS.md)'s case for what makes this
approach unique —
[`human-led`](CORE_PILLARS.md#human-led).)

## People and the Model

<a id="people-manage-agents-execute"></a>

**2. People manage; agents execute.** The human contribution is
planning, taste, judgment — deciding what gets built and whether it
works, the way defining a system beats hand-running it. Brief the model
like an individual contributor, stay engaged, adjust the plan as soon as
the first attempt reveals what the brief missed
([`manager-of-agents`](COMPANY_BUILDING_RULES.md#manager-of-agents))
— same posture as [`arguing-with-the-model`](#arguing-with-the-model),
applied to management. (Full list:
[Humans at Our Best](HUMANS_AT_OUR_BEST.md) — this is the claim behind
its [`judgment`](HUMANS_AT_OUR_BEST.md#judgment),
[`actually-managing`](HUMANS_AT_OUR_BEST.md#actually-managing) and
[`taste`](HUMANS_AT_OUR_BEST.md#taste) entries, and behind
[`human-led`](CORE_PILLARS.md#human-led).)

<a id="arguing-with-the-model"></a>

**3. Coworking with a model means arguing with it.** State a half-formed
position, let the model push back, push back on its answer — keep going
until the exchange settles it, not either side alone. Instructing makes
a typist; polling for an opinion makes an oracle. Quality is one payoff:
agreement just hands back your blind spots
([`ai-chat-as-intermediary`](COMPANY_BUILDING_RULES.md#ai-chat-as-intermediary),
[`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate);
[`argue-in-the-open`](AI_GOVERNANCE_TO_COCREATE.md#argue-in-the-open)).
It is also what
[`people-manage-agents-execute`](#people-manage-agents-execute) means by
briefing a model and staying engaged.

<a id="explain-the-why"></a>

**4. Explain why, every time: describe problems, not solutions.** The
instruction tells the model what to type; the reason tells it what you're
actually trying to achieve — naming the problem, instead of handing over a
prescribed fix, is what lets it catch a case you didn't spell out or push
back when the ask doesn't serve the goal
([`five-whys`](COMPANY_BUILDING_RULES.md#five-whys); a
[Core Pillars](CORE_PILLARS.md) pillar,
[`focus-on-whys-problems`](CORE_PILLARS.md#focus-on-whys-problems); the
human side of it is
[`questions`](HUMANS_AT_OUR_BEST.md#questions)). It's also the raw
material a standing rule gets made from — a practice pulled from "always do
X" has nothing to check itself against, one pulled from "always do X
because Y" can be tested against Y forever
([`rules-generated-automatically`](#rules-generated-automatically),
[`decisions-carry-their-situation`](#decisions-carry-their-situation)).

## Knowledge That Gets Captured

<a id="context-is-capital"></a>

**5. Context is core.** [`capital-asset`](COMPANY_BUILDING_RULES.md#capital-asset)
makes the case for capturing this. What matters is the residue, not
the deliverable — the option tried and killed, the correction only
legible against the draft it corrected. One document carries that
forward for the next session; another reaches the same conclusion and
reads as if it had always been obvious. It still has limits no writing
closes: the physical world a machine can't check
([`verification`](HUMANS_AT_OUR_BEST.md#verification)) and the friction
that survives no matter how much got written down
([`dirtiness-of-real-life`](HUMANS_AT_OUR_BEST.md#dirtiness-of-real-life)).
Language works the same way:
the AI carrying the translation keeps thinking real, not thinned
([`second-language-stops-costing-quality`](REASONS_WHY.md#second-language-stops-costing-quality)).

<a id="rules-generated-automatically"></a>

**6. Protocols, rules, and preferences get generated automatically.**
The AI Assistant surfaces the pattern behind a request every time,
unprompted ([`explain-the-why`](#explain-the-why)); turning it into a
standing rule is still a human call. This repo's team and individual
practice sources run that mechanism continuously
([`automatic-rule-extraction`](AI_GOVERNANCE_TO_COCREATE.md#automatic-rule-extraction)),
making [`decisions-carry-their-situation`](#decisions-carry-their-situation)
affordable and
[`explicit-ownership-not-hidden-in-the-model`](#explicit-ownership-not-hidden-in-the-model)
possible — and beats documenting by hand
([`writing-stops-competing-with-doing`](REASONS_WHY.md#writing-stops-competing-with-doing),
[`protocols-generated-not-just-documented`](REASONS_WHY.md#protocols-generated-not-just-documented)).

<a id="decisions-carry-their-situation"></a>

**7. Every decision carries the situation that produced it.** However
small the call, name the case that prompted it, or it invites
relitigation from someone who wasn't there
([`explain-the-why`](#explain-the-why)) — a case it wouldn't have caught
makes the rule theater. Capture is the agents' job, pulled from the work
itself
([`rules-generated-automatically`](#rules-generated-automatically)'s rule
extraction), heading off
[`situation-heads-off-confusion`](REASONS_WHY.md#situation-heads-off-confusion)
and worth
[`active-resurfacing`](AI_GOVERNANCE_TO_COCREATE.md#active-resurfacing)
later.

## Visible and Owned, Not Hidden

<a id="processes-should-be-visible"></a>

**8. Processes should be visible, not locked in one person's brain.** A
workflow whose only interface is "email me and I'll handle it" is
invisible to everyone else. Bigger than tidiness
([`no-dark-processes`](COMPANY_BUILDING_RULES.md#no-dark-processes)):
real intelligence is what anyone with the record can check, not what one
person knows. Every dark process trades convenience now for a
compounding blind spot.

<a id="explicit-ownership-not-hidden-in-the-model"></a>

**9. Protocols, documents, and knowledge should be explicitly owned by
the team, not hidden inside an AI Assistant.** Any model infers your
implicit patterns as you work; the question is where that lives — a
private session, or files the team can edit and hand to another model
([`rules-generated-automatically`](#rules-generated-automatically);
[`owned-rules-outlast-the-chat`](REASONS_WHY.md#owned-rules-outlast-the-chat)).

## Humans Should Do What Humans Do Best

<a id="humans-do-what-humans-do-best"></a>

**10. Humans should do what humans do best.** Machines produce; people
bring judgment, relationships, instinct: reading a room, sensing what a
client meant but didn't say, pushing someone harder when the moment
calls for it. Optimizing a person to act like a fast, tireless model
optimizes away what they're for
([`structurally-human`](COMPANY_BUILDING_RULES.md#structurally-human)) —
hold them to that standard, not a machine's. (Full list:
[Humans at Our Best](HUMANS_AT_OUR_BEST.md) — this is the claim behind
its [`relationships`](HUMANS_AT_OUR_BEST.md#relationships) and
[`instinct`](HUMANS_AT_OUR_BEST.md#instinct) entries.)

## See Also

- [The Working Loop](THE_WORKING_LOOP.md) — the six-step cycle these
  ideas run through, end to end.
- [Core Pillars](CORE_PILLARS.md) — the one-page pitch: the core ideas
  this approach argues are unique, specifically taken together.
- [Reasons Why](REASONS_WHY.md) — the less obvious benefits those
  ideas actually produce in practice.
- [The Talmudic Method](THE_TALMUDIC_METHOD.md) — the resemblance between
  what this system insists on and how the Talmud gets studied, argument
  by argument.
- [Company Building Rules](COMPANY_BUILDING_RULES.md) — the standalone
  essay on rules for building a company around AI.
- [AI Governance to Co-Create](AI_GOVERNANCE_TO_COCREATE.md) — the
  standalone essay on how AI systems themselves should be configured,
  built, and run.
- [Humans at Our Best](HUMANS_AT_OUR_BEST.md) — the one list of what
  humans are good at, gathered from the shorter versions scattered here
  and elsewhere.

<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying this document into philosophy/; source: the project's own prior notes repository, content/OUR_PHILOSOPHY.md, version 41 -- that repository was made private and is being deleted, so philosophy/ is this document's home now, not a copy of one. -->

# Our Philosophy

*The theoretical layer underneath everything else in this repo, not a new
argument. [CORE_PILLARS.md](CORE_PILLARS.md) is the short version of what
follows — the four pillars it names are what these ideas add up to, and
what [REASONS_WHY.md](REASONS_WHY.md)'s payoffs come out of.
[COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) makes the case for
running a company this way; [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md)
makes the case for building the AI systems that way. Both assume a handful
of ideas about memory,
[judgment](HUMANS_AT_OUR_BEST.md), and how work actually produces quality.
It's an account of the theory, not a pitch for it.*

## The Working Loop

The same five steps repeat every time, in order:

1. A spark — an idea, new data, an incoming request, a changed system
   message.
2. Argue it out with an AI Assistant that has this repo attached, so
   the argument runs against the actual record instead of a guess
   ([`arguing-with-the-model`](#arguing-with-the-model)).
3. Most of that arguing happens on GitHub in the open, and the decision
   and reasoning is tracked there — a pull request, not a secret chat
   log ([`context-is-capital`](#context-is-capital),
   [`processes-should-be-visible`](#processes-should-be-visible)).
4. The AI Assistant produces all the output; you only guide it
   ([`people-manage-agents-execute`](#people-manage-agents-execute),
   [`humans-do-what-humans-do-best`](#humans-do-what-humans-do-best)).
5. The decisions, small to big, turn into learnings and shared rules
   and protocols automatically
   ([`rules-generated-automatically`](#rules-generated-automatically),
   [`decisions-carry-their-situation`](#decisions-carry-their-situation)),
   staying visible to whichever session opens this repo next.

## Groups, Not Individuals

<a id="groups-not-individuals"></a>

**1. Built for groups, not individuals working alone with a model.** Most
"work better with AI" advice makes one person faster at their own
work. This repo assumes something different: several people solving the
same problem together, with chat as what connects them, not a private
assistant each person also has. (One part of
[CORE_PILLARS.md](CORE_PILLARS.md)'s case for
what makes this approach unique.)

## Working With the Model

<a id="people-manage-agents-execute"></a>

**2. People manage; agents execute.** The human contribution is
planning, taste, judgment — deciding what gets built and whether it
works, the way defining a system beats hand-running it. Brief the model
like an individual contributor, stay engaged, adjust the plan as soon as
the first attempt reveals what the brief missed
([`manager-of-agents`](COMPANY_BUILDING_RULES.md#manager-of-agents))
— same posture as [`arguing-with-the-model`](#arguing-with-the-model),
applied to management. (Full list:
[HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md).)

<a id="arguing-with-the-model"></a>

**3. Coworking with a model means arguing with it.** State a half-formed
position, let the model push back, push back on its answer — keep going
until the exchange settles it, not either side alone. Instructing makes
a typist; polling for an opinion makes an oracle. Quality is one payoff:
agreement just hands back your blind spots
([`ai-chat-as-intermediary`](COMPANY_BUILDING_RULES.md#ai-chat-as-intermediary),
[`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate);
[`argue-in-the-open`](AI_GOVERNANCE_TO_COCREATE.md#argue-in-the-open)).

## Knowledge That Gets Captured

<a id="context-is-capital"></a>

**4. Context is core.** [`capital-asset`](COMPANY_BUILDING_RULES.md#capital-asset)
makes the case for capturing this. What matters is the residue, not
the deliverable — the option tried and killed, the correction only
legible against the draft it corrected. One document carries that
forward for the next session; another reaches the same conclusion and
reads as if it had always been obvious. Language works the same way:
the AI carrying the translation keeps thinking real, not thinned
([`second-language-stops-costing-quality`](REASONS_WHY.md#second-language-stops-costing-quality)).

<a id="rules-generated-automatically"></a>

**5. Protocols, rules, and preferences get generated automatically.**
What's automatic is the finding: the AI Assistant surfaces the pattern
every time, without anyone having to remember to look. Turning it into
a standing rule is a human call, routed by this repo's own rules to
whoever's responsible — and a spotted pattern always gets surfaced,
never left unremarked. This repo's team and individual practice sources
(precedent-team-repo-maintenance, precedent-individual — see
[spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md)) run that mechanism continuously
([`automatic-rule-extraction`](AI_GOVERNANCE_TO_COCREATE.md#automatic-rule-extraction);
[practice 20](../PRACTICES.md#20-mistakes-become-rules-root-cause-the-miss-then-encode-the-prevention)
is the same move done by hand).

<a id="decisions-carry-their-situation"></a>

**6. Every decision carries the situation that produced it.** However
small the call, the record states what case prompted it — a bare
"always do X" invites relitigation from anyone who wasn't there. The
case also tests the rule: one that wouldn't have caught it is theater.
BestPractice already requires this
([practice 5](../PRACTICES.md#5-conventions-cite-the-incident-that-created-them),
[practice 20](../PRACTICES.md#20-mistakes-become-rules-root-cause-the-miss-then-encode-the-prevention));
capture is the
agents' job, pulled from the work as it happens
([`rules-generated-automatically`](#rules-generated-automatically)'s
rule extraction).

## Visible and Owned, Not Hidden

<a id="processes-should-be-visible"></a>

**7. Processes should be visible, not locked in one person's brain.** A
workflow whose only interface is "email me and I'll handle it" is
invisible to everyone else. Bigger than tidiness
([`no-dark-processes`](COMPANY_BUILDING_RULES.md#no-dark-processes)):
real intelligence is what anyone with the record can check, not what one
person knows. Every dark process trades convenience now for a
compounding blind spot.

<a id="explicit-ownership-not-hidden-in-the-model"></a>

**8. Protocols, documents, and knowledge should be explicitly owned by
the team, not hidden inside an AI Assistant.** Any model infers your
implicit patterns as you work; the question is where that lives — a
private session, or files the team can edit and hand to another model
([`rules-generated-automatically`](#rules-generated-automatically);
[`owned-rules-outlast-the-chat`](REASONS_WHY.md#owned-rules-outlast-the-chat)).

## Humans Should Do What Humans Do Best

<a id="humans-do-what-humans-do-best"></a>

**9. Humans should do what humans do best.** Machines produce; people
bring judgment, relationships, instinct: reading a room, sensing what a
client meant but didn't say, pushing someone harder when the moment
calls for it. Optimizing a person to act like a fast, tireless model
optimizes away what they're for
([`structurally-human`](COMPANY_BUILDING_RULES.md#structurally-human)) —
hold them to that standard, not a machine's. (Full list:
[HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md).)

## See Also

- [CORE_PILLARS.md](CORE_PILLARS.md) — the one-page pitch: the core ideas
  this approach argues are unique, specifically taken together.
- [REASONS_WHY.md](REASONS_WHY.md) — the less obvious benefits those
  ideas actually produce in practice.
- [COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) — the standalone
  essay on rules for building a company around AI.
- [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md) — the
  standalone essay on how AI systems themselves should be configured,
  built, and run.
- [HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md) — the one list of what
  humans are good at, gathered from the shorter versions scattered here
  and elsewhere.

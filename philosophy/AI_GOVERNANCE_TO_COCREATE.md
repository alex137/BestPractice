<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying this document from WorkingWithAI into philosophy/; source: themorgan/WorkingWithAI content/AI_GOVERNANCE_TO_COCREATE.md, version 15. -->

# AI Governance to Co-Create

*Governance for the AI systems themselves: how to configure, build, and
run them so co-creation —
[`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate) —
is the default, not something a disciplined person manufactures by hand.
[COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) makes the case for
running a company this way; this document is one level down, about the
systems. See also [OUR_PHILOSOPHY.md](OUR_PHILOSOPHY.md) (the theory),
[REASONS_WHY.md](REASONS_WHY.md) (the payoffs), and
[HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md) (what stays human).
Promoted out of [RANDOM_NOTES.md](RANDOM_NOTES.md);
[RULES_NOW_TESTING.md](RULES_NOW_TESTING.md) is where an idea from either
essay gets tried before it's called a rule.*

## Memory & Context

<a id="durable-state-default"></a>

**1. Persistent, versioned, greppable state should be the default shape,
not a special case.** Context only behaves like capital
([`capital-asset`](COMPANY_BUILDING_RULES.md#capital-asset)) if it
outlives the session that made it — durable, diffable state should beat
ephemeral chat by default.

<a id="automatic-rule-extraction"></a>

**2. Automatic rule extraction should be a standing capability, not a
manual habit.** Distill protocols, rules, and preferences straight out of
the interaction — the guidance, the correction — instead of waiting for
someone to write policy by hand; this repo's team and individual practice
sources (precedent-team-maintainers, precedent-individual — see
[process/PRECEDENT_MIGRATION.md](https://github.com/themorgan/WorkingWithAI/blob/main/process/PRECEDENT_MIGRATION.md)) run this continuously
([`rules-generated-automatically`](OUR_PHILOSOPHY.md#rules-generated-automatically);
[`writing-stops-competing-with-doing`](REASONS_WHY.md#writing-stops-competing-with-doing)).

<a id="coldstart-test"></a>

**3. A coldstart test, run like any other check.** Can a fresh session,
given only the memory store, reconstruct the current state of any live
decision? If not, the transcription
([`transcribe-everything`](COMPANY_BUILDING_RULES.md#transcribe-everything))
failed somewhere specific and locatable.

<a id="active-resurfacing"></a>

**4. Resurfacing should be active, not just searchable.** A system that
only answers when asked misses what nobody thought to ask — the better
version notices "you decided X six weeks ago" unprompted, when it's
relevant now.

## Interaction Design

<a id="push-back-as-config-switch"></a>

**5. Push-back as a configuration switch, not a personality quirk.**
Argue a genuine counter-case on writing/thinking work, comply on
technical execution — the switch should track task shape, not sit fixed
at the system level.

<a id="three-reflexes-in-system-prompt"></a>

**6. The three reflexes from
[`three-questions`](COMPANY_BUILDING_RULES.md#three-questions) belong in
the system prompt, not just a human's habit.** An agent that asks itself
"have I done this shape before" mid-task, and says so, does more of
[`think-in-workflows`](COMPANY_BUILDING_RULES.md#think-in-workflows)'s
work than a person remembering to ask.

<a id="argue-in-the-open"></a>

**7. Argue in the open.** An AI reviewer that holds a half-formed
position and invites disagreement, rather than posting a clean
finished-looking suggestion, keeps the disagreement itself in the record.

## Interface

<a id="chat-is-primary-interface"></a>

**8. Chat is the primary interface to every document, not a shortcut
around them.** The AI creates and organizes the documents; humans can
edit them directly, but most work happens by asking and guiding it in
chat — docs are its memory, chat is where people work.

## Verification

<a id="non-uniform-confidence"></a>

**9. Confidence should look non-uniform, because it isn't.** If every
claim reads with the same even prose confidence,
[`hire-for-drive`](COMPANY_BUILDING_RULES.md#hire-for-drive)'s "find the
one false paragraph" skill has nothing to grab onto. Flag the weaker
claims — a hedge, a citation, an assumption — so a verifier has a place
to start.

## Workflow & Cost Sensitivity

<a id="automatic-workflow-detection"></a>

**10. Automatic workflow-candidate detection.** Mine the history itself —
commits, sessions, transcripts — for recurring task shapes instead of
relying on a human noticing "this is the third time." Turns
[`think-in-workflows`](COMPANY_BUILDING_RULES.md#think-in-workflows)'s
judgment call into a standing job.

<a id="cost-awareness-situational"></a>

**11. Cost-awareness should be situational, inferred by the system, not a
fixed global policy.** The right posture varies by person and moment —
sometimes
[`build-five-kill-four`](COMPANY_BUILDING_RULES.md#build-five-kill-four)'s
lavishness fits better. The harder problem is inferring which situation
applies, not applying one policy everywhere.

## Voice & Output

<a id="structural-ai-voice-check"></a>

**12. A structural "sounds like AI" check.**
[`no-ai-voice`](COMPANY_BUILDING_RULES.md#no-ai-voice) names the actual
fingerprints — the throat-clearing opener, "not just X, it's Y," the
bolded summary nobody asked for. Those are mechanical enough to check for
before publishing, rather than relying on a human catching it every time.

## Surfacing Blind Spots

<a id="ai-hunts-dark-processes"></a>

**13. Configure the AI to hunt its own dark processes.** Have it
periodically list workflows whose only interface is a human inbox —
including its own — and propose an addressable alternative, per
[`no-dark-processes`](COMPANY_BUILDING_RULES.md#no-dark-processes).

<a id="periodic-checkins-not-expiry"></a>

**14. Rotation and temp workflows get periodic check-ins, not baked-in
expiry.** A hard sunset date, taken literally from
[`structurally-human`](COMPANY_BUILDING_RULES.md#structurally-human),
forces an end even when a workflow is going well. Better: a recurring,
low-cost reminder — "is this still needed, still the right shape?"

## Keeping the Corpus Honest

<a id="contradiction-scanning-recurring"></a>

**15. Contradiction-scanning as a recurring job, not a one-off pass.** A
compounding corpus
([`capital-asset`](COMPANY_BUILDING_RULES.md#capital-asset)'s own
metaphor) rots quietly if nothing re-reads it for internal disagreement —
worth standing up as a periodic pass, not something that only runs once
someone thinks of it.

<a id="provider-neutrality-hedge"></a>

**16. Provider-neutrality is a hedge on
[`capital-asset`](COMPANY_BUILDING_RULES.md#capital-asset), not a
preference.** Context built against one vendor's tooling shouldn't be
strandable by a provider switch — the capital asset is the context, not
the platform it's sitting in today.

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
- [COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) — standalone
  essay promoted out of the brainstorm: rules for building a company
  around AI.
- [RULES_NOW_TESTING.md](RULES_NOW_TESTING.md) — pipeline stage 2: the
  practical rules actually being tried in real work right now.
- [CORE_PILLARS.md](CORE_PILLARS.md) — one-page
  pitch: the core ideas this repo argues are unique specifically taken
  together.

<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying this document into philosophy/; source: the project's own prior notes repository, content/RULES_NOW_TESTING.md, version 19 -- that repository was made private and is being deleted, so philosophy/ is this document's home now, not a copy of one. -->

# Rules Now Testing — The Current State of What We're Trying

This is the second stage of this repo's pipeline (see
[README.md](README.md)'s "How this repo's ideas become company policy"):
[COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) argues *why*;
[AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md) designs *how*
the AI systems themselves should be built so the healthy pattern is the
default; this document is *what's actually being tried right now* — not
settled policy, not a finished essay, but the checklist a session in any
of Morgan's real work is expected to follow today, revised the moment
practice teaches something. A rule earns
its way onto this list from the brainstorm or one of the two essays; it
earns its way *off* — into [precedent-team-repo-maintenance](https://github.com/themorgan/precedent-team-repo-maintenance)
(or `precedent-individual`
for the rare rule that's genuinely about Morgan the person, not the team),
for automatic rollout to every project that resolves that source — only
once it's actually proven itself here. See
[ASSORTED_NOTES.md's Open Questions](ASSORTED_NOTES.md#open-questions) for what is still unsettled.

**This document does not get vendored anywhere.** Unlike `process/upstream/`
or the team/individual practice sources, it has no manifest entry and no
sync workflow — it's native to this repo, the same as
[ASSORTED_NOTES.md](ASSORTED_NOTES.md), because working out which rules are
ready is exactly this repo's job. Nothing here is real company policy for
another project until a session has separately gone into
precedent-team-repo-maintenance (or precedent-individual) and landed it there
(see "Promotion" below) — mentioning a rule here is not the same as
adopting it elsewhere.

## Status Key

- **Trial** — being tried in real work now; not yet proven enough to port.
- **Ready to promote** — proven; the next session touching
  precedent-team-repo-maintenance (or precedent-individual) should land it there.
- **Withdrawn** — no longer being tried, with the reason given inline.
- **Promoted** — already landed there. Kept here only
  as a pointer, not restated in full — full restatement would just be a
  second copy of the same rule that can drift out of sync with the first,
  the same reasoning the team practice set's own
  [`no-duplication`](https://github.com/themorgan/precedent-team-repo-maintenance/blob/main/practices/no-duplication.md)
  gives for not duplicating BestPractice.

## Rules

<a id="push-back-writing-thinking"></a>

### 1. Push-Back Mode on Writing-And-Thinking Work — *Promoted*

[`push-back`](https://github.com/themorgan/precedent-team-repo-maintenance/blob/main/practices/push-back.md).
Argue a genuine counter-case before building on a stated stance; flag a
serious unresolved disagreement before calling a piece done. Never on
code or other technical work.

<a id="provider-neutral-llm"></a>

### 2. Provider-Neutral LLM Integrations — *Withdrawn*

[`llm-neutral`](https://github.com/themorgan/precedent-team-repo-maintenance/blob/main/practices/llm-neutral.md).
Build any LLM integration against a swappable model/token/base-URL
interface; assume an OpenRouter credential absent other instruction.
Hedges [`capital-asset`](COMPANY_BUILDING_RULES.md#capital-asset)
(context as capital).

**Withdrawn 2026-09-11.** It was promoted into the maintainers' team set,
and that is where it stopped making sense: reviewing the set after the
2026-09-09 subject split, this is not a rule about maintaining a
repository, and no subject set exists for engineering craft. Morgan
retired it rather than open a set to hold it. The practice file is kept
and still readable — retired is not deleted — and the hedge on
[`capital-asset`](COMPANY_BUILDING_RULES.md#capital-asset) is now
unhedged, which is the part worth noticing if this ever comes back.

<a id="argue-in-the-open"></a>

### 3. Argue in the Open — *Trial*

On writing-and-thinking work — a PR review, comment thread, feedback on
a draft — post a half-formed position and invite disagreement instead of
a finished one. Keeps the disagreement in the record, not just its
resolution
([`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate)).

<a id="three-reflexes-out-loud"></a>

### 4. Three Reflexes, Asked Out Loud Mid-Task — *Trial*

Before calling work done, answer all three out loud in the reply:

- What rules or protocols should come from this?
- Have I done this shape before, or will I again?
- Is there a way this could be better — not just faster?

([`three-questions`](COMPANY_BUILDING_RULES.md#three-questions).)

<a id="write-like-a-human"></a>

### 5. Write Like a Human, Not an LLM — *Promoted*

[`write-like-a-human`](../practices/write-like-a-human.md). Nothing you
ship may sound like it came from an AI — document, reply or commit
message. Say the thing in your own words, at the length it earns.

This rule and
[`no-ai-voice`](COMPANY_BUILDING_RULES.md#no-ai-voice) were always the
same point: one argued why, one pointed at what to follow. They landed
as a single universal practice on 2026-09-07 — deliberately a short
guiding point, replacing the long vendored ruleset this entry used to
name.

<a id="dark-process-self-audit"></a>

### 6. Dark-Process Self-Audit, Including the Session's Own Habits — *Trial*

Periodically, same cadence as the BestPractice check-in — list workflows
whose only interface is a human inbox, the assistant's own included, and
propose an addressable alternative
([`no-dark-processes`](COMPANY_BUILDING_RULES.md#no-dark-processes)).

<a id="contradiction-scanning"></a>

### 7. Contradiction-Scanning Across the Corpus, as a Recurring Job — *Trial*

Periodically re-read [ASSORTED_NOTES.md](ASSORTED_NOTES.md) and this document for entries
that now disagree — same cadence as
[`dark-process-self-audit`](#dark-process-self-audit), not a one-off.

## Not Yet Ready for This List

These ideas from [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md)
need either more real testing or actual infrastructure this repo doesn't
have yet — writing them as rules now would be systematizing before the
third instance, exactly what
[`think-in-workflows`](COMPANY_BUILDING_RULES.md#think-in-workflows) warns
against. Tracked instead in [ASSORTED_NOTES.md's Open Questions](ASSORTED_NOTES.md#open-questions):

- **Active/proactive resurfacing** ("you decided X six weeks ago,
  unprompted") — needs something that actively mines and ranks history,
  not just answers when asked.
- **Automatic workflow-candidate detection** — mining commit/session
  history for recurring task shapes, rather than relying on
  [`three-reflexes-out-loud`](#three-reflexes-out-loud)'s human-triggered
  reflex.
- **Situational, inferred cost-awareness** —
  [`cost-awareness-situational`](AI_GOVERNANCE_TO_COCREATE.md#cost-awareness-situational)'s
  own text records that a fixed "surface spend per outcome" policy was
  already proposed and rejected in discussion; only the passive log
  survived. The harder half — inferring *which* posture applies — is
  still open.
- **A coldstart test** — can a fresh session, given only the memory store,
  reconstruct the state of any live decision? Worth running periodically,
  but it's a manual audit today, not an automatable gate.
- **Deeper "normie"-employee engagement**, beyond
  [`push-back-writing-thinking`](#push-back-writing-thinking) — visible
  reminders of the deeper mode, making rule-extraction "in your face,"
  proactive resurfacing of a relevant rule. ASSORTED_NOTES.md's own "Why
  BestPractice specifically works" open question.

## Promotion — Moving a Rule From Here Into a Practice Source

1. Mark the rule **Ready to promote** here, with a line on what proved it
   out (which sessions, what it caught or avoided).
2. In a separate session against precedent-team-repo-maintenance (or
   precedent-individual, for the rare rule that's genuinely about Morgan
   the person rather than the team), land it as its own practice file in
   reading-order position among the existing rules, with its own permanent
   slug — that set's own convention for adding a rule without a
   renumbering pass across every dependent repo's citations, since
   citations use the slug, not the position
   ([`new-rule-placement`](https://github.com/themorgan/precedent-team-repo-maintenance/blob/main/practices/new-rule-placement.md)).
3. Come back here, mark the rule **Promoted**, and cut its entry down to a
   pointer only, per the status key above.
4. Note the move in [../TODO.md](../TODO.md)'s decision record, same as any
   other cross-repo change.

*(Origin: a session on 2026-08-27 that had initially recommended landing
these ideas directly into RepoPersonalPreferences's
[process/personal/README.md](https://github.com/themorgan/RepoPersonalPreferences/blob/main/process/personal/README.md) —
corrected by Morgan, who wants this repo to actually try a rule out before
it becomes company-wide policy. See [../TODO.md](../TODO.md) for the decision
record.)*

## See Also

- [CORE_PILLARS.md](CORE_PILLARS.md) — the one-page pitch: the core ideas
  this approach argues are unique, specifically taken together.
- [OUR_PHILOSOPHY.md](OUR_PHILOSOPHY.md) — the underlying theoretical
  ideas everything else here assumes, named and explained on their own
  terms.
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

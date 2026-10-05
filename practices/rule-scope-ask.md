---
slug:        rule-scope-ask
title:       When a proposed rule's scope is ambiguous, ask which layer it belongs to
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A rule can be proposed in conversation before any file exists, so no path names the moment; the occasion index reaches it."
occasion:    "a new rule's scope isn't obvious"
gates:       []
index_clause: "ask once which layer or set it belongs in"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "pending PR review -- drafted 2026-10-05 by Morgan F, moved from the shared set precedent-shared-repo-maintenance"
strength: decided
---
## Rule
When a rule is proposed and it's genuinely unclear whether it governs one document or the whole repo, ask -- once, in the moment, with a guess and the reason for it, so confirming costs a word rather than a paragraph.

**There are two axes, and this rule covers both.** Inside a repo: one document or all of them. Across a layered catalogue: which **set** -- repo-local, a shared set, an individual set, or universal. The second is the one with the longer reach, because a set decides which repositories ever see the rule at all.

**Decide the set by subject and reach, never by which repository the session can currently write to.** Access is not an argument about where a rule belongs, and treating it as one produces a rule filed where it happens to be landable rather than where it binds. The test parallels the document one: would the rule still be true for a different team? For a different person? For a repo whose subject is nothing like this one's? True for all of them, it is universal. True only given this team's subject, it is that team's. A statement about one person's own preference is theirs, in their own set. Where the answer is genuinely not obvious, ask -- with the guess and its reason, same as above.

## Detail
This is a carve-out from deciding small calls yourself: by that rule's own test (how hard a call is to undo), filing a newly proposed rule at the wrong layer looks cheap. It isn't -- the cost that matters is not undoing the mistake but noticing it. Both misfilings are silent: a rule that's really general, filed onto one document, ends up restated across several places in several phrasings, drifting; a rule that's really local, filed as a repo convention, quietly constrains every document in the repo.

The test: would the rule's own text still make sense applied to a different document? "Only short paragraphs" would, so ask. "Keep the Series A section under one page" names this document's own structure and is local on its face. "Use em dashes, not semicolons" is plainly house style and goes to the repo's conventions. Only the first case warrants stopping -- asking on all three trains the person proposing rules to wave the question through.

## Why
The ask is nearly free while the rule is still in front of the person proposing it; the same question weeks later costs a full reload of the context that produced it.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. No dated incident was recorded; what was recorded is why this
rule is a deliberate carve-out from another one, which is the part worth
keeping.

By `small-calls`' own test -- how hard is it to undo -- filing a newly
proposed rule at the wrong layer looks cheap, so `small-calls` would say
decide and move on. The carve-out exists because the cost that matters here
is not undoing the mistake but noticing it, and both misfilings are silent.
A rule that is really general, filed onto one document, ends up restated
across several recipes in several phrasings, drifting, with nothing pointing
at it. A rule that is really local, filed as a repo convention, quietly
constrains every document in the repo and is never connected back to the one
file it was meant for. Neither announces itself.

The timing argument is the other half: the ask is nearly free while the rule
is still in front of the person proposing it, and the same question three
weeks later costs them a full reload of the context that produced it.

The test and the three worked examples are there to stop the rule
overfiring, which would defeat it -- asking on all three trains the person to
wave the question through. Only genuine ambiguity warrants stopping, and the
ask carries a guess and its reason so confirming costs a word.

**2026-09-12 -- the set axis, added after it failed, and the title had
promised it all along.** A session wrote eight operational rules about running
a fleet of sessions -- a platform refusal it had just hit, what a spawned
session should report, when to compact -- into THIS set's `AGENTS.md`, and
merged them. Morgan asked whether they were for him, for a team, or universal.
None of the three: `AGENTS.md` is not a practice file and materializes
nowhere, so they bound one repository, which was narrower than any level he
named. Six of the eight were facts about the platform and belonged at
universal; two were about how a session behaves toward a person and belonged
in the working-style set; the set they landed in owns neither subject.

**The session had this rule available and it would not have caught the
mistake.** The title said "which layer it belongs to", but the Rule and the
test underneath it only ever named one document versus the whole repo. The
axis that was actually wrong -- which set -- appeared nowhere, so consulting
the rule would have returned a confident "repo-wide, not one document", which
was true and irrelevant.

**Why it went wrong is worth keeping, because it is a general failure mode.**
The session picked the repository it could merge in. The level question was
never asked because the access question had already answered "where", and an
hour earlier the same session had argued against re-declaring a practice
locally on exactly those grounds. It also treated "no check could see this"
as "this is not catalogue material", which is wrong in a catalogue whose
on-demand tier is full of practices with `checked_by: null` -- and that
reasoning is what pushed the rules into prose, which is what confined them to
one repository.

## Install
No mechanical check: this is a live judgment call made while a rule is being proposed -- whether its scope is genuinely ambiguous by the rule's own test ("would the rule's own text still make sense applied to a different document?"). Nothing in committed content records whether that ask happened, or should have.


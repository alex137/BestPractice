---
slug:        rule-level-by-reach
title:       "Which set holds a rule is decided by its reach, not by write access"
tier:        on-demand
severity:    default
applies_to:  ["practices/**", "AGENTS.md", "CLAUDE.md", "precedent.json"]
occasion:    "deciding which practice set a new rule belongs in -- repo-local, team, individual or universal"
gates:       ["review"]
index_clause: "pick the set by reach -- not by the repo you can write to"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-12"
approved_by: "Morgan F, 2026-09-12, relayed through a scheduled instruction to export
  the set axis to universal -- the four levels, the three tests, and the negative a
  2026-09-12 incident turned on. The placement is his; that this became its own
  practice rather than an extension of layered-practice-packs was the session's
  judgment, named as a judgement call in that same instruction and measured before it
  was taken."
strength:    decided
source_practice_number: null
---
## Rule
**A rule lands in one of four sets, and which one is a question about its
reach:** **repo-local** (true only of this repository's subject), **team**
(true for this team, not another), **individual** (one person's way of
working), **universal** (any repository, any team, any person).

**Three tests, in order**, each answering what the one before cannot.
*Still true for a different team?* — not the team's. *For a different person?*
— not that person's. *For a repository whose subject is nothing like this
one's?* — universal, and filing it lower strands it.

**Decide by subject and reach, never by which repository the session can
currently write to.** **Say which set, and which test settled it, before writing
the rule** — one line, in the reply or in the change. A rule written as prose
into an instructions file has no set at all: not a fourth answer, a missing
one.

## Detail
**This is a different axis from [layered-practice-packs](layered-practice-packs.md),
which is the practice it looks like.** That one asks how *general* a rule's
content is — generic, domain, repo-local — which decides how the rule must be
*written*: its vocabulary, whether the public scrub applies, how general the
wording has to be. This one asks where the rule *lives*. The two are not a
re-labelling of each other, and the middle terms show it: a domain rule can sit
in a team set or in universal, and **individual has no counterpart on that axis
at all**, because a person is not a kind of program. Answer both — content to
know how to write it, reach to know where to put it.

**Why the prose case is a missing answer rather than a fourth one.** An
instructions file is not a practice file: it materializes nowhere, so the rule
binds the one repository that holds it, whatever its subject was. That is not
"repo-local" — repo-local is a *decision* that a rule's reach stops here, made
by writing it where repo-local rules live. Prose in an instructions file is what
a session produces when nobody asked the question, and the two are
indistinguishable afterwards by reading the file.

**Two wrong inputs are common enough to name.**

- **Where the session can write.** The incident below turned on this one. A
  session rooted in one repository writes its rule there, and the rule binds
  that one repository whatever its subject was. Write access is the input that
  correlates with nothing: it is an accident of where the session happens to be
  rooted, it differs next session, and **it points the wrong way exactly when
  the rule is most general** — the broadest rules are the ones a session is
  least likely to be sitting in the right repository to write.
- **Who was in the conversation.** A rule that arrives while working with one
  person is not thereby personal. What a person wants to be *interrupted* about
  is genuinely individual; a fact about the platform, or about running sessions
  at all, is not — however personal the thread that surfaced it felt.

**The third test is the hard one to apply honestly**, because a rule always
looks specific to the work that produced it. Asking it about a repository whose
subject shares nothing with this one's is what strips the day's vocabulary off
the rule and leaves the claim behind.

**Reach is not the same question as whether the rule already exists.**
[mistakes-become-rules](mistakes-become-rules.md)' lookup asks whether some set
already carries this rule; this one asks, once the answer is no, which set
should. Running them in that order matters: a search for the subject is also
how you find out what level comparable rules sit at.

## Why
**Both wrong answers are silent, and they fail in opposite directions.** A rule
filed too low is stranded — the next team, the next person, the next repository
needs it, cannot know it exists, and re-derives it differently. A rule filed too
high binds people who never agreed to it, and arrives in their sessions with the
authority of a settled practice.

**Neither shows up where the decision was made**, which is why the choice has to
be stated rather than felt. The session that files a rule is the one session
that will never see the cost: stranding is paid by a repository that never hears
about the rule, over-reach by a person who hears about it without the argument.

**And the default is worse than either.** Absent a decision the rule goes where
the session happened to be typing, which is the one input with no relationship
to the rule's subject at all.

## Story
**The incident, 2026-09-12.** A session working in a private team practice
source spent a day fixing a real defect, then wrote eight operational rules
about running a fleet of sessions into that set's own instructions file and
merged them. Asked afterwards whether the rules were for one person, a team or
everyone, **the answer was none of the three**: an instructions file is not a
practice file and materializes nowhere, so the eight rules bound exactly one
repository — the one the session could write to.

*(Reported, not verified here: cross-owner attaches are refused, so that source
cannot be read from this repository. What is verifiable here is the material.
Most of it was already at universal —
[spawn-session](spawn-session.md) landed 2026-09-11 and already required naming
the repositories the work must read, write or push to and comparing them
against the ones the session holds — and its Detail already cited the
cross-owner refusal, which was one of the eight.)*

**Why this rule sits at universal rather than in the set that coined it**, by
its own third test: a team set asking which set a rule belongs to is asking
about a layered catalogue, and a layered catalogue is this engine's subject, not
any team's. It is just as true for a repository whose subject is nothing like
that one's.

**Live evidence, in this repository, the same day**, that the older axis alone
could not answer the question: [the open item](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md#leak-gate-is-background-level)
on which level `leak-gate-is-background` belongs at reaches for
[layered-practice-packs](layered-practice-packs.md)' decision rule — *would this
hold in an unrelated repo?* — and records that it yields **two readings, and
they disagree**: the nuisance the rule ends is not personal, which reads
universal, while what a person wants to be interrupted about is exactly what an
individual set exists for. That is the question being asked with no rule able to
answer it. The *different person* test is the step it was missing.

## Install
Nothing to configure. The occasion index entry is generated, so every session
reads it whether or not any private source resolved, and the path trigger
reaches `AGENTS.md` and `CLAUDE.md` as well as `practices/` — because the
incident's rules were written as prose into an instructions file, which is
where a rule that never becomes a practice file actually lands.

No mechanical check, and it was attempted rather than waved past
([checkable-gets-checked](checkable-gets-checked.md)). The three tests are
judgments about reach, and **the repository that would have to run the check is
the one that cannot**: a source set holds its own level's catalogue only, so
nothing there can compare a rule against the levels above it. What *is*
checkable is the missing-set case in the Rule's last paragraph — a rule written
as prose where a practice file belongs — and that is a text-shaped judgment
about what counts as "a rule" in an instructions file, which no glob settles.

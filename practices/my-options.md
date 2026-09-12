---
slug:        my-options
title:       "\"My options\" asks for the real choices, plainly, with a recommendation"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"My options\", or asks to have a decision's options laid out"
gates:       ["reply"]
index_clause: "\"My options\" -- every option, plainer, both sides, then your pick and why"
checked_by:  null
defines:     ["My options"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-12"
approved_by: "Morgan, 2026-09-12 -- asked for the command, chose the name from the recommendation"
strength:    decided
source_practice_number: null
---
## Rule
When the person says **"My options"**, answer as if they had asked this:

> Explain the options more clearly, in somewhat less technical wording, the
> positives and negatives of each, and which you recommend and why.

Four things, all four required:

- **Every option that is actually available**, including the ones you had
  already dismissed. An option you leave out is a decision you took on their
  behalf without saying so.
- **One short block each**, in plainer words than the reply would otherwise
  use — a notch down from the register in force, not a rewrite of what you
  know.
- **The cost said as flatly as the benefit.** An option whose downside you
  cannot name has not been thought about, and saying so is a better answer
  than inventing one.
- **A named recommendation, with the reason.** Not a leaning, not a "it
  depends on your priorities" — the one you would pick, and the thing that
  makes it the pick.

**It governs that one answer**, not the rest of the conversation. That is
what separates it from [plain-words](plain-words.md), which is a standing
change of register.

## Detail
**The recommendation is the part that gets dropped, and it is the part they
asked for.** A reply that lays out three options beautifully and then stops
has handed the work back: they now have to do the comparing, which is the
expensive half, with less context than you have. If two options are genuinely
close, say they are close and still pick one, naming what would change the
answer.

**Plainer is about vocabulary, never about substance.** Same conclusions,
same figures, same refusal to manufacture one
([no-invented-specifics](no-invented-specifics.md)). If the plainer version
says something different from what the careful version would have said, the
plainer version is wrong — the same line
[plain-words](plain-words.md) draws.

**The options are the ones on the table today**, not a survey of everything
imaginable. Where an option was ruled out earlier in the thread, it still
appears, with one clause saying what ruled it out — otherwise the person
cannot tell a considered exclusion from an oversight.

**Their answer to the recommendation is an approval**, so
[decision-strength](decision-strength.md) applies to it directly: picking the
recommended option because you recommended it, with no reason of their own,
is `assented`; choosing against the recommendation, or giving their own
reason for it, is `decided`.

**Deferred, deliberately**: whether "none of these, don't do it" must always
appear as an explicit option. It is a real question — the do-nothing case is
often the right answer and is the easiest to leave out — and Morgan parked it
on 2026-09-12 as something to consider later rather than settle in the same
message that coined the command.

## Why
The four demands are one request that had to be retyped every time, and a
phrase is cheaper than a paragraph. That is the same argument every other
command in this catalogue rests on.

**What makes it worth a rule rather than a habit is which of the four goes
missing.** Register rules govern how a reply is worded; nothing governed the
*shape* of a decision answer, so the shape drifted toward the comfortable
one — an even-handed survey with no position in it, which
[write-like-a-human](write-like-a-human.md) already names as a tell and which
leaves the reader exactly where they started.

## Story
**Coined by Morgan on 2026-09-12**, in the same thread that renamed
[spawn-session](spawn-session.md). He described the request rather than
naming it: *"I also tell you a lot 'explain the options more clearly, in
somewhat less technical wording, the positives and negatives of each, and
which you recommend and why' - maybe we should have a command for that one
too?"* The session searched the universal catalogue and the private sources
in force, found nothing covering the shape of a decision answer, proposed
`My options` against three alternatives, and he took it.

**The failure it prevents is the one the phrase exists to interrupt**, and it
had been happening often enough that he had a sentence memorized for it:
having to ask, each time, for the comparison rather than the material — and
then, having asked, getting the options without the pick.

## Install
Nothing to configure. The occasion index entry is generated, so an adopter
installs nothing and every session reads the phrase whether or not any
private source resolved.

No mechanical check. This one was examined rather than waved past
([checkable-gets-checked](checkable-gets-checked.md)): the artifact is a chat
reply, which is not in the repository, and the only thing a tree-scoped check
could look at — a decision record written afterwards — already carries its
own gate through [decision-strength](decision-strength.md). Counting options
or detecting a recommendation in prose would be a guess wearing a mechanism's
clothes, and a gate that fires on correct work teaches the next session to
ignore every gate.

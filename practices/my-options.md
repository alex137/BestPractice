---
slug:        my-options
title:       "\"My options\" asks for the real choices, plainly, with a recommendation"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"My options\", asks to have a decision's options laid out, or asks -- about a current issue -- for the options to hand off to another session"
gates:       ["reply"]
index_clause: "\"My options\" -- every option, plainer, your pick -- or a paste-ready handoff"
checked_by:  null
defines:     ["My options"]
command:     {"My options": "Lay out the real choices in plainer words, the good and the bad of each, and tell you which one it recommends and why -- and when it's about a current issue meant for another session, add that session's id and link, which repository has to be the primary seed root, and which others need to be attached, then hand the whole thing back as one paste-ready block."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-12"
approved_by: "Morgan, 2026-09-12 -- asked for the command, chose the name from
  the recommendation. Extended 2026-09-19, Morgan, after declining a separate
  command (\"Brief it\") proposed for the same shape aimed at a handoff:
  \"I still like 'my options' and then it triggers when you realize it's
  similar to 'show me options' etc. Let's use that,\" and asking that the
  extension focus on \"the options to prevent\" rather than a single flat
  recommendation. Tightened 2026-09-20, Morgan, after noticing the
  paste-ready block was not consistently delivered as an actual fenced
  block: the Rule now names the mechanism (a fenced code block) rather than
  just the outcome (\"ready to copy in one click\")."
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

**The same four things answer a different question when what's on the table
is a current issue rather than an ordinary decision** -- "my options here",
"show me options", or anything else that plainly asks for this shape about
handing an issue off to a session that was not in this conversation. The
options themselves become **the ways to prevent or resolve it**, held to the
same discipline -- every real one, plain words, the cost of each stated
flatly, a named pick -- rather than one flat recommendation with nothing to
compare it against.

**Three more things are owed in that case, because the reader is a session
with none of this conversation:**
- **This session's own id and title, with a link, and that a session wrote
  it rather than a person** -- the header
  [seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md)
  already requires of any prompt one session hands to another, carried here
  for the same reason: whoever reads this needs to know where the claims
  came from.
- **Which repository has to be the primary seed root** -- the one the
  receiving session needs opened or rooted in before any of the options are
  actionable.
- **Which other repositories, if any, need to be attached alongside it.**
  Say "none" when that is the honest answer -- never leave the reader to
  guess whether it was considered.

**Delivered as one fenced markdown code block (triple backticks), not a
paragraph of prose** -- the fence is what makes the client render a
one-click copy button; a block described in words but not actually fenced
has not delivered this, whatever else the reply says. Same
requirement [the-boildown](the-boildown.md) already states for any handoff:
the words are the session's to write, not the reader's to compose. Producing
it does not, by itself, authorize anything in the repository or
repositories it names -- that is not committing, pushing, or merging
anything, whatever the receiving session goes on to do there.

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

**Where the handoff case differs from [Write it up](write-it-up.md).** That
command's deliverable is a file committed to the repo, reached later by a
link -- built for the record. This one's deliverable is the reply itself,
meant to be pasted directly into a different window with nothing to click
through and nothing to memorialize. Nothing stops using both on the same
issue -- write it up for the durable record, then ask for `My options` on
what should happen next -- but this practice does not depend on a commit
existing first, and does not make one.

**Where this differs from [Prompt Please](prompt-please.md).** Both produce
a paste-ready block naming a repository to root a new session in, and the
line between them is *when in the decision* each is reached for.
`My options` is for *before* a recommendation is settled -- every real
choice, plainly, with its cost, so the person can weigh them even if they
end up taking the pick anyway. `Prompt Please` is for *after* that point: a
recommendation already exists, and what's wanted is the clean handoff text
to act on it, not another comparison.

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
`session-text`. He described the request rather than
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

**Extended 2026-09-19, on Morgan turning down a separate command for the
handoff case.** Asked for a phrase covering roughly what
[write-it-up](write-it-up.md) does but smaller, paste-ready, and never
memorialized in the repo, he proposed "options" himself; the session raised
that a bare "options" would sit ambiguously next to this practice's own
"My options" and built a separate command, "Brief it", instead. He turned
that down on read: *"I hear 'brief' and I think something bigger and more
formal in github -- which is exactly what we did a few days ago with the
command 'write it up'! This is more something to paste in, something smaller
and shorter... I still like 'my options' and then it triggers when you
realize it's similar to 'show me options' etc. Let's use that."* -- and, in
the same message, that the content should read as **options to prevent** the
issue rather than a single flat pick. The session judged the cleanest way to
honor "let's use that" was folding the handoff case into this file rather
than declaring a second practice with the same trigger phrase, which two
active practices cannot both own; that mechanics decision was not put to
him. `brief-it.md`, the file this superseded, records its own short life --
unlinked here since it deduplicates into this same file. Strength: decided.

**Cross-referenced against [Prompt Please](prompt-please.md), 2026-09-20**,
when Morgan coined that command and drew the boundary himself: `My options`
is for seeing the choices before mostly following whichever one gets
recommended; `Prompt Please` is for once a recommendation is already the
plan and only the handoff prompt is wanted.

**Tightened the same day**, after Morgan checked whether this practice and
`Prompt Please` both actually deliver the copy-in-one-click block they
promise and said the answer was often no: *"You often don't do that and I
want to enforce it."* The Rule's own wording -- "ready to copy in one click"
-- was true but not mechanical: nothing in it said a block had to be an
actual fenced code block rather than a paragraph that merely reads as
paste-ready. Both practices now name the mechanism directly. Strength:
decided.

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

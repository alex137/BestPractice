---
slug:        answer-first-ask-before-long-work
title:       Give the person what they can have now first; propose a long task before starting it; an open question never pauses the work
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "a turn that could start a computation, search or build lasting longer than a few minutes, or that has an answer or a deliverable ready before its slower work is done"
gates:       []
index_clause: "answers and deliverables go out the moment they exist; a long run is proposed with its cost -- never just started"
checked_by:  null
defines:     ["long task"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan F, drafted 2026-10-05, moved from the shared set precedent-shared-working-style; merged in PR #879 on 2026-10-05; part 2's exception narrowed to the quick checks by Morgan F, 2026-10-07; the clock-time sentence added by S. Alexander Jacobson, 2026-10-07; tightened back under 150 words, Morgan F, 2026-10-07; part 1 widened from easy answers to anything the person can have now, documents and files included, Morgan F, 2026-10-14 (\"I like your change - please implement it\")"
strength:    decided
---
## Rule
**(1) What the person can have now goes to them now** (an answer, a
document, a figure), before landing, testing or any slower work; only what
it needs comes first. **(2) A task longer than a few minutes is proposed,
not started:** what it is, how long by the tool's own cost line, what it
blocks and doesn't, then the go-ahead, except a commit's quick checks on the
files it touched (never a whole suite) and a run asked for by name. **(3) A
wait says what it is for, what it changes and how to stop it**; a background
task nobody asked for is stopped, not waited on. **(4) An open question never
pauses the work:** ask it early; do whatever its answer doesn't touch.
**Every "how long" carries when it lands, in the person's zone from
[`tools/precedent_time.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_time.py), named:**
"about 15 minutes, done around 15:35 <their city> time".

## Detail
**Why a clock time, and whose.** A duration says nothing once the reader
has lost track of when it was said, and chat surfaces show no timestamps,
so "15 minutes" leaves the person no way to know when to look back. The
zone is the person's declared timezone, else the one their own commits
carry; never the container's unless it is theirs, and always written out,
since the person, a colleague and the machine are often in three. S.
Alexander Jacobson, 2026-10-07 (strength: decided): "let's also make a
practice of reporting a future time not just a duration estimate".
**The clock comes from [tools/precedent_time.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_time.py)**, which reads the zone
from the person's identity.json; never recalled, and never the zone of an
example. Until 2026-10-13 this Rule's example named New York, and a
session working for someone in Buenos Aires gave its times in New York's
for two days, reading the clock by hand in the example's zone.

**Part 3 to a person who is not a code owner** is the outcome in everyday
words, never the mechanism: what is being checked and that they can say
stop, in no word they would have to look up
([inner-workings-for-code-owners](inner-workings-for-code-owners.md)).

**What part 1 means by "can have now":** it exists and is usable, even if
it is not committed, pushed or landed yet. An answer from what is already
known, without waiting on a run, is one; so is a document, a file, a figure
or a result the session has just made. Send it then -- attached, linked or
quoted -- and do the landing, pushing and checks after, in the same turn
where they fit: [repo-is-memory](repo-is-memory.md) still wants the work
pushed in the turn it is made, and sending it first does not change that.
**Only work the deliverable itself depends on goes first**: a document whose
numbers come from a run waits for the run; a document that only needs to be
committed does not wait for the commit. **Sent early and then changed** by
the later work (a check that forced an edit, a merge that brought in someone
else's change), it is sent again, with one line saying what changed.

**Part 3's wait is never a bare "still running"**; that phrase was in the
Rule until 2026-10-14 and moved here when part 1 widened. **What part 2 means by a long task:** a
cold solve, a search family, a re-solve cascade, a whole-tree gate. Both
were in the Rule until 2026-09-21 (see `## Story`).

"A few minutes" is the boundary at which a person would rather have been
asked: below it the run is cheaper than the exchange; above it the run
is a decision about their time and their machine. The proposal is one
message: the task, its estimated duration from a measured cost line
(never a guess), what the person can and cannot do meanwhile, and the
question. A run that was authorized once is not authorized again after
its inputs change — a merge that re-keys a cache is a new proposal.

**What part 4 means by a question that may stop the work:** sort pending
questions into blockers and everything else. A blocker is one where
proceeding under any assumption would be unsafe, spend real money or touch
production the wrong way, or make the delivered work useless if the guess is
wrong -- only those justify stopping with nothing delivered. Everything else
is non-blocking: do the work that doesn't depend on the answer and the work
that comes out the same either way, then ask, then carry on with whatever's
still independent. Ask as soon as the question is formed rather than saving
it for a summary, since the person is often away when the answer would be
most useful; where the answer would change work already done, say so when
asking, so the cost of each option is visible.

## Why
A long run started unasked costs twice: the person waits for something
they did not choose, and the easy answers they did ask for wait behind
it. And a wait nobody explained is indistinguishable from a hang, so the
person either interrupts healthy work or sits through dead work.
Part 4 is the same cost from the other side: the answer to an open question
should arrive while work is still in flight, and a question asked only at the
end of a session has nowhere useful to land.

## Story
A session launched an hours-long re-solve while four conceptual
questions sat unanswered, then sat on a ninety-minute cold solve after a
merge invalidated a cache, before answering a one-line question about
the merge itself. The person's direction, adopted as the rule: do not
start long tasks without checking first, and answer the easy questions
before anything else.


**Rule compressed 2026-09-21**, in the reduction pass recorded in
[todo-2026-09-21-resident-cap-was-measured-on-the-wrong-shape.md](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-21-resident-cap-was-measured-on-the-wrong-shape.md).
208 tokens -> 124. All three parts stayed; what moved into `## Detail` is
the pair of definitions the Rule was carrying inline -- what counts as an
easy question, and the four examples of a long task. The exceptions stayed
in the Rule, because a session reads them at the moment it is deciding
whether to ask.

**Moved to `precedent-shared-working-style` and back, same day, 2026-09-23.**
A cross-repo practice-placement review moved this out of universal, on the
reasoning that it is squarely that set's own subject. The disclosed cost at
the time -- reaching only a repo that declares `precedent-shared-working-style`,
rather than every Precedent consumer including the downstream repo that
contributed it -- turned out to be worse than a smaller audience:
`verify_harness.py --as-ci`'s consumer-fixture check found the deduplication
record itself was false for a plain consumer resolving only universal, which
is most of them -- `in_force_at:` pointed at a slug that does not resolve IN
FORCE anywhere that consumer can see. The tool that runs every other kind of
move refuses exactly this direction (`--from universal`) for exactly this
reason, which this incident confirms rather than merely asserts. Reverted
the same day, Morgan F: stays universal, `tier: resident`, as before.

Later on 2026-09-23 (commit `73ad9f14`) this universal copy was withdrawn
after all and pointed at the working-style set's copy, which was the one in
force from then. **2026-10-05: this file is the live copy again**, moved
back as the working-style set folded away (Morgan F, strength: decided).

**2026-10-01, part (4) absorbed from `nonblocking-questions`**, in the
reduction pass recorded in BestPractice's
[todo-2026-09-30-session-file-cut-to-4000.md](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-30-session-file-cut-to-4000.md)
("Reduction pass review, 2026-10-01"). The two resident rules were one
subject -- what a session does with its time while a person has not yet
answered -- and loading both on every turn paid for two headers and two
framings of it. Its Rule became part (4) and its blocker test moved into
`## Detail` whole; its file is `status: deduplicated` and points here.
Approved by Morgan F, 2026-10-01: *"Question 3 - all are great, approved"*
(strength: decided).

**2026-10-07, part (2)'s exception narrowed to the quick checks.** A
session started BestPractice's whole test suite by hand to double-check
work bound only for pre-staging, whose own push check takes seconds. It
quoted fifteen to twenty-five minutes from memory; a third of the way in,
twenty-five minutes had gone, and the one-process run takes about forty.
It had read "the checks a commit needs" as covering the whole suite. Morgan
asked how to stop it happening again, and approved all three answers
(*"Yes, make those changes"*, strength: decided): the suite now prints what
it costs before it starts, a full run started by hand refuses without
`--because` quoting the person's go-ahead, and this exception names the
quick checks.

**2026-10-07, back under 150 words.** The clock-time clause added that
afternoon took the Rule to 171 words, and with it this resident rule pushed
a session file one consumer had capped at 4,000 tokens past its target. Tightened
in a reduction pass, all four parts and the clause kept, nothing moved out
(Morgan F, "take all the reduction proposals", strength: decided).

**2026-10-14, part (1) widened from questions to deliverables.** A
session in a downstream repository was asked to cut a section from a
proposal, hand over the Word version, and land the change (Booked, then
Produce). It built the Word file early, then spent about ten minutes
landing on staging, promoting to main and merging the pull request, and
only sent the file after all of that. Nothing about the landing had to
happen first. The Rule then said "answer the easy questions first", and
the session read it literally: a file is not a question. Morgan F,
2026-10-14 (strength: decided): *"whenever I ask for a document or
information, that you always give it to me BEFORE doing the hard work --
assuming that you are able to (excluding situations where you need to do
the hard work before you can give me the information or document) ...
Information I can receive quickly, I always want first, before you other,
background, less urgent work."* Widened here rather than written as a new
practice: the purpose is the one part (1) already had, and two rules for
"what the person can have now comes first" would drift apart. To stay
under 150 words, part (3)'s "never a bare 'still running'" moved into
`## Detail` and parts (3) and (4) were reworded shorter; nothing else was
dropped. The Boildown, Booked, Produce and Prompt Please rules were read
for an ordering that holds a deliverable back to the final reply; none
has one. Approved in his words: *"I like your change - please implement
it"*.

## Install
Adopt the rule in the working-conventions file and name the cost-line
convention it depends on (every heavy tool prints its estimated duration
before it runs; see
[slow-steps-report-and-cache](https://github.com/alex137/BestPractice/blob/staging/practices/slow-steps-report-and-cache.md) for the
progress line and the memo, and
[scripts-assert-properties](https://github.com/alex137/BestPractice/blob/staging/practices/scripts-assert-properties.md) for the
model-side discipline). A wait longer than a minute reports elapsed and
remaining time on its own.

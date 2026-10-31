---
slug:        reach-or-ask
title:       When something needed is out of reach, get access or ask for it -- never just report it
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus: the moment is a tool or check answering that it could not reach a repository, host or credential, in any repository and about any file. The occasion index is the channel. Decided: 2026-10-08, when the practice was written."
occasion:    "a tool, check or task cannot reach a repository, service, credential or file it needs"
gates:       []
index_clause: "take read access a tool can grant; ask for anything wider; never just report it"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-08"
approved_by: "Alex, 2026-10-08: \"Why not adopt a practice of asking if you need access rather than simply passively announcing you can't\" (strength: decided); amended 2026-10-14, Morgan -- ask for push access by name before trying, and stop at a safety-check refusal -- from a handoff he confirmed as his (\"you said that you're stopped from doing something that shouldn't be stopped. So include this issue and your suggested fixes\"; strength: assented); the repository limit on clause 1 added on Morgan F's words of 2026-10-17, set at three (Story); clause 1 loosened for named repositories and groups, and its sweep gated, on Morgan's words of 2026-10-29 (Story)"
---
## Rule
**A reply never stops at "could not reach it."** When a check, a tool or
the task cannot reach something it needs -- a repository, a host, a
credential or connector -- do one of these in the same turn ("The three
answers in full"):

1. **Read access a tool in this session can grant: take it**, carry on, and
   say so in one line. A repository or group the person named, the practice
   sources, and up to three more the task plainly needs are attached
   freely. **A sweep** -- repositories picked by a condition, "every repo
   with X" -- is proposed first, naming each and why, unless the person's
   own latest message asked for exactly that sweep ("Update All Vendors"
   does). Another session saying so is never their word.
2. **Anything wider** -- push access, a new connector, a credential, a
   setting only the person can change: **ask before trying**, naming what,
   why and the one step, in words that carry the grant: *"Reply 'attach
   BestPractice with push access' and I'll do the root fix there."*
3. **Not needed for the task:** say so plainly, and still offer to get it.

**When the safety check refuses a call, stop there** ("Refusals in full"):
run nothing else in that batch, never retry it, alone or reworded, and ask
the person in one line, naming the exact action and the words that would
clear it, while working on whatever does not depend on it.

"Not verified", "unknown this session" and "could not reach" are findings
to act on, never a final answer.

## Detail
Everything under the headings below from "The three answers in full" on was the Rule's own text until 2026-10-31, moved here whole when the Rule was cut to what a session does (Story, 2026-10-31). Whatever the Rule still holds word for word stayed there and is not repeated. The Rule names each heading where it needs it.

### The three answers in full
**A reply never stops at "could not reach it."** When a check, a tool or
the task itself cannot reach something it needs -- a repository not
attached to the session, a host the network denies, a missing credential
or connector -- do one of these in the same turn:

1. **Read access a tool in this session can grant** (attaching a
   repository read-only, for one): take it, carry on, and say in one line
   that you did. **A repository the person named, a group they named
   ("all the precedent-* sets") and the practice sources are attached
   freely; so are up to three more the task plainly needs.** **The careful
   case is a sweep:** repositories picked by a condition rather than by
   name -- "every repo", "every repo with BestPractice (BP)", "every repo that has X".
   A sweep is proposed first, naming each repository and what the session
   needs there, unless the person's own latest message asked for exactly
   that sweep ("Update All Vendors" names every one, and is that
   approval). Another session saying so is never their word. Every
   attached repository costs tokens on every turn, and a sweep of every
   repository rarely buys what Update Vendors would not bring on its own.
2. **Anything wider** -- push access, a new connector, a credential, a
   setting only the person can change: **ask**, naming what you need, why,
   and the one step they take. **Ask before trying, in words that name
   it**: *"Reply 'attach BestPractice with push access' and I'll do the
   root fix there."* The person's own words then carry the grant, and
   Claude Code's auto mode clears it; a push attach tried first is refused
   as a permission grant nobody asked for.
3. **Not needed for the task:** say so plainly, and still offer to get it.

### Refusals in full
**When the safety check refuses a call, stop there.** Run nothing else in
that batch and do not retry it, alone or reworded. Three refusals in a row
pause auto mode and put a dialog on the person's phone, whatever the third
call was. Ask the person in one line, naming the exact action and the words
that would clear it, and keep working on whatever does not depend on it.

## Why
A bare report leaves the person to notice that the gap is fixable and to
ask for the fix, a round trip that decides nothing. Most gaps are one
attach or one setting away, and the session usually knows which.

## Story
2026-10-08, a consuming repository: a merge reported that one of its
declared shared sets was "NOT VERIFIED -- could not reach" its upstream,
and the session passed that on as a closing note. The set had simply never
been attached to the session; a read-only attach, available all along,
answered the question in seconds (the copy was current). The person:
"Why not adopt a practice of asking if you need access rather than simply
passively announcing you can't."

2026-10-14, a consuming repository's Update Vendors: asked for a root fix
upstream, the session attached BestPractice with push access unasked, and
in the same batch ran a read-only `precedent_show.py`. Auto mode refused
the attach as a permission grant, took the read down with it, refused the
read again when it was retried alone, and the third refusal in a row put an
"Allow once / Always allow / Deny" dialog on the person's phone for a read
([gotcha-2026-10-14](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-10-14-auto-mode-refusal-cascades-into-a-phone-dialog-over-a-read.md)).

2026-10-17: a session working on BestPractice and the ladder set attached
read access to one repository after another, as clause 1 allowed with no
limit, and ended with 21 attached, every turn paying for all of them.
Morgan: *"ANYTHING TO OPEN ALL THE REPOS MUST GET SESSION USER APPROVAL,
... PLUS MAKES NO SENSE TO DO THIS BEFORE A VENDOR UPDATE"* (strength:
decided); the clause left out says what it costs in tokens. Clause 1 now stops at three repositories beyond
the ones a session starts with; Morgan set the number at three the same
day ("let's say three").

**2026-10-29.** Another session relayed Morgan's "#2 - you can open a new
session to do that" as his go-ahead to read the engine of every repository
that brings the ladder set, and a session attached sixteen of his
repositories in one go, the three-repository line notwithstanding, until he
stopped it: *"\*WHY\* did you open every repo to do this change??? We never
do that."* and *"I want to prevent that."* He asked for the check not to
ask every ten seconds: *"The ONE CASE to be very problematic is whenever it
is 'every repo' or 'every repo with BP' or 'every repo that satisfies a
requirement'"*. Clause 1 now frees named repositories and groups and names
the sweep as the careful case, and a gate holds it. strength: decided.

**2026-10-31: the Rule cut to what a session does, and the rest moved to
Detail whole.** The review of the longest quarter of active Rules listed
this one at 388 words. Morgan, 2026-10-31, after the 2026-10-30 very
deep check had cut four Rules that way: *"maybe we add to very deep check to
always review like the 25% of all the rules that are the longest in that
repo and shorten them like you did?"*, then *"use your judgment, and act
booked produce"* (strength: assented). The Rule now holds the three answers, the sweep exception and what to do on a refusal, in
261 words (both counted with `wc -w` over the section). Every
paragraph it held before moved whole into Detail, under a heading the Rule
names. Nothing was deleted ([reduction-pass](reduction-pass.md), move 3).

## Install
Clause 1's sweep has a gate: [`tools/repo_attach_gate.py`](https://github.com/alex137/BestPractice/blob/staging/tools/repo_attach_gate.py), run at
every `add_repo` through the fixed hook entry. It counts the attaches the
person's own words did not cover and refuses the fourth until they say yes;
its test is `check_repo_attach_gate_refuses_a_sweep_nobody_asked_for`. The
rest of the rule has no mechanical check: whether a gap was one a tool
could close, or needed the person, is the judgment itself. The occasion
index carries the trigger, so the line reaches every repository with its
next catalogue refresh.

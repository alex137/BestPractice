---
slug:        diagnosis-is-measured
title:       "A tool's named causes are hypotheses; measure before you relay one"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a tool, hook or error message names the possible causes of a failure"
gates:       ["reply"]
index_clause: "a tool's named causes are hypotheses; measure one before you relay it"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "Morgan, 2026-09-14 -- \"Note the rule violation. Go merge.\", directing this incident be written up and landed"
strength:    decided
source_practice_number: null
---
## Rule
**A message that lists what might have gone wrong has not diagnosed
anything.** A guard reports the condition it can see, then names the causes
its author thought of. That list is a starting point for an investigation,
not the result of one -- and the real cause is regularly not on it.

So before that list reaches the person, **measure one of its branches.** Look
at the thing. `ls` the directory the message says is missing, read the config
it says is wrong, call the tool it says refused you. One command is usually
the whole cost.

**Then say which of the three you have.** A finding (*"I looked; the
directory is genuinely not there"*), a hypothesis (*"the message suggests
this; I have not checked"*), or a relay (*"the guard says this and I am
passing it on unexamined"*). Never let the second or third be read as the
first.

**Never build a recommendation on an unmeasured cause.** This is the line
that does the damage. Repeating a guard's guess costs the person a moment;
telling them to act on it costs them an afternoon -- and where the
recommended action is to **delete** something, an unmeasured cause can talk
them into destroying working configuration to fix a problem that was never
there.

**The most dangerous message is the one that has already eliminated
something.** *"A credential IS set, so a missing credential is not the
explanation"* reads as the output of a completed investigation, and it is
still only the causes one author enumerated. **Ruling one thing out is not
the same as having ruled the rest in.**

## Detail
**Absence at the moment you looked is not absence.** A great many of these
messages fire because something was read before the thing that writes it had
finished: a clone still running, a generated file not yet built, a hook that
has not reached the step. The guard cannot tell "not there" from "not there
*yet*", and almost none of them list the timing branch among their causes,
because the author was thinking about steady state.

**So the cheapest measurement is usually to look again.** Where something is
reported missing, re-reading it a moment later separates a race from a real
absence, and it costs one command.

**This narrows nothing and adds nothing to
[fail-gracefully](fail-gracefully.md).** That rule governs the guard's own
telling -- how loudly a tool reports a part that could not run. This one
governs the *reader*: what a session may assert on the strength of having
read it.

## Why
**A guard's cause list is written from the author's imagination, and the
failures that actually happen are the ones nobody imagined.** A condition
worth guarding is a condition somebody thought through; the causes beside it
are what occurred to them at the time. Those are two different qualities of
information printed in the same typeface, and the second is much weaker than
it looks.

**The phrasing makes it worse.** These messages are written to be helpful, so
they sound decided -- they eliminate, they instruct, they name remedies. A
session reading one is handed a confident paragraph and asked, implicitly, to
forward it. Forwarding is free; checking is one command. The default is
wrong, which is why it needs a rule.

**What it costs the person is not a wrong sentence, it is a wrong errand.**
They cannot re-run the measurement -- they were not there. They take the
recommendation at face value, go looking for a problem that does not exist,
and the session that sent them has spent their attention on nothing.

## Story
**2026-09-14, in this repository.** A session was asked for the standing
command list. Its private practice sources -- three team sets and one
individual set -- are cloned onto the container by a SessionStart hook, and
on that first turn the clone had not finished. Every source read as missing.

The stop hook printed what it was designed to print: three sources did not
resolve, **a credential IS set -- so a missing credential is not the
explanation**, therefore look for a refused credential or a retired
repository, and *"if so the fix is to remove that declaration, not to
configure access."*

The session repeated that, and then went further: it recommended checking
whether the three repositories still existed and dropping them from
[precedent.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/precedent.json)
if they did not. It had run no command against any of them.

**Neither named cause was the cause.** The credential was fine and no
repository was retired. A single `ls` would have settled it. On the next turn
the hook's clone completed -- `clone: from .../precedent-team-writing`,
timestamped seconds earlier -- all four sources resolved, and 171 practices
loaded from six sources. **The real cause, "the clone has not happened yet",
was not among the two the guard offered**, and could not have been: the guard
was written to explain a steady-state failure.

Had the person acted on the recommendation, they would have gone hunting for
three deleted repositories that were all alive, on their way to deleting
three correct declarations from a working config file. Morgan's reply was
*"I don't understand, explain it plainly"* -- twice -- which is what an
unmeasured diagnosis actually produces: not a wrong answer the reader can
catch, but a confident one they cannot.

## Install
No mechanical check, and the reason is specific rather than a shrug:
**whether a session measured before asserting lives in the conversation**,
where no repository-scoped script can see it. The tree after the fact is
identical either way -- a session that checked and one that guessed leave the
same files behind. This is the same blind spot every reply-shaped practice
here has, and it is why this one is written as a rule rather than a gate.

What *is* mechanically visible is the guard text itself. A guard whose
message enumerates causes should say that is what it is doing -- *"most
often one of:"* rather than a flat therefore -- so the next reader is not
invited to treat the list as a conclusion. That is a change to the guards,
one at a time, as each is touched.

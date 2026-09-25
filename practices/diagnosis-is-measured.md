---
slug:        diagnosis-is-measured
title:       "A tool's named causes are hypotheses; measure before you relay one"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a tool, hook or error message names the possible causes of a failure"
gates:       ["reply"]
index_required: false
index_clause: "a tool's named causes are hypotheses; measure one before you relay it"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "Morgan, 2026-09-14 -- \"Note the rule violation. Go merge.\", directing this incident be written up and landed;
  extended 2026-09-22, Morgan (strength: decided) -- \"File it that way, go
  update\" -- with the comparison-check case: a check names the two things it
  compares and never the inputs feeding them, so a stale clone is reported as
  a fault in the output, and re-running against older code rules out the code
  rather than the environment"
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

**A check that COMPARES two things names those two things, and never the
inputs feeding them.** This one has no cause list at all -- it reports a
fact, and the fact is true: the document does not match what its script
produces. What it cannot say is that the script read a stale clone, because
the clone is not one of the two sides being compared, it is an input to one
of them. So a stale input is reported, correctly and unhelpfully, as a fault
in the output, and the finding points at the wrong file **by construction**.
Where a run has been told anything is stale, behind, or diverged -- a source
clone, a cache, a generated tree -- that notice is an input to every check
that follows it, not housekeeping to read past.

**And reproducing a finding against older code rules out the code, not the
environment.** Re-running with the previous version and getting the same
result feels like the decisive test and is not: both runs read the same
stale input. It answers *"did my change cause this"*, which is worth
knowing, and it is silently mistaken for *"what caused this"*.

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
**2026-09-22, in this repository.** A session ran [`precedent_check.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_check.py) and
got one violation: `computed-numbers-in-scripts`, reporting that a generated
vocabulary block in a document no longer matched what its script emits. The
finding named the document and the script, which are the two things it
compares.

The session read that as a standing drift in the document, decided
regenerating it would publish a private practice's command into a public
file, declined to touch it -- correctly -- and moved on. Then, to be sure
the violation was not its own doing, it checked out the previous version of
the checker and ran it against the same tree. Identical result. It treated
that as settled and wrote the diagnosis into a commit message and a pull
request body.

**The cause was neither the document nor the script.** One of the practice
source clones on the container was twenty commits behind its origin, and the
fix for this exact drift had already landed there -- the offending row was
never a vocabulary command and had lost its `command:` field at the source.
The script was faithfully emitting a row that no longer existed upstream.
The check was right; the reading of why was wrong.

It surfaced by accident: the session reset that clone for an unrelated
reason and the violation vanished. **The session-start output had named the
stale clone on the first turn**, and it was read as housekeeping rather than
as an input to every check the session was about to run. Morgan, 2026-09-22,
on being shown the sequence: *"File it that way, go update"* (strength:
decided).

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
[precedent.json](https://github.com/alex137/BestPractice/blob/staging/precedent.json)
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

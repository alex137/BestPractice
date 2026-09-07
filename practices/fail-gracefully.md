---
slug:        fail-gracefully
title:       Always fail gracefully
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing code that depends on something outside its own control, handling a part that could not run, or deciding how loudly to report one"
gates:       []
index_clause: "keep going, never look complete — match the telling to stake and reader"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       2026-08-31
approved_by: "Morgan F, migrated from RepoPersonalPreferences by the private-set
  migration session; revised 2026-09-07, Morgan F, to graduate the telling by
  what the degradation costs and by who is reading it, after the uniform
  standard was found to be both too loud for non-technical adopters and
  unenforceable at 67 mostly-legitimate hits PROMOTED to the universal catalogue 2026-09-07, Morgan F, from
  precedent-team-maintainers. Both team sets had landed this same practice, byte
  for byte, within a day of each other -- and two sources at the same level
  defining one slug is a hard `ResolveError`, so any repo declaring both team
  sources could not resolve at all. Two different teams wanting the identical
  rule is what a universal rule looks like (practice: layered-practice-packs);
  the team sets were simply where it was written down first. Deleted from both
  on promotion rather than left as copies. A repo this does not bind exempts it
  in `not_binding` with a stated reason, which is the mechanism that makes one
  copy safe"
---
## Rule
Any code written or set up here anticipates its own common failure modes rather than letting them surface as an unhandled crash. Three things, and the first is not negotiable by audience or by stake:

1. **Never let a degraded result look complete.** The invariant, and it holds for every reader and every rule: a partial scan, a skipped check, a defaulted config, an empty result -- none of them may render identically to the real thing. "Could not check" and "checked, nothing wrong" must always be distinguishable. Everything below is about *how* that is said, never about whether.

2. **Keep going.** The work continues. A part that cannot run does not stop the session, abort the surrounding task, or take the rest of the system down with it: check for the absence or failure case on purpose and carry on with a documented fallback, a reduced scope, or that one part skipped -- never a raw stack trace, a hang, or an abort of work that did not depend on the thing that failed.

3. **Match the telling to the stake and to the reader.** Two independent axes; conflating them is the mistake this clause exists to stop.

   **How insistent -- set by what acting on the result would cost.** If someone could make a wrong decision, ship a wrong artifact, or trust a wrong number because of what did not run, they are stopped: the run exits non-zero, or the message sits where they cannot proceed past it. If nothing anyone will act on is affected, it goes into the record -- a log line, a report row -- and does not interrupt.

   **What form -- set by who is reading.** A technical reader gets the file, the exception, and the command that fixes it. A non-technical reader gets a plain sentence naming what is not trustworthy, what that means for what they are about to use, and who to tell -- never a stack trace, never a command they cannot run, never a bare script name. The technical detail is not discarded; it goes where a technical person will read it.

**The quadrant to watch is a costly failure in front of a non-technical reader.** The pull is toward silence, because that person cannot fix it and the detail would only confuse them. It is the one combination where silence is worst: they cannot fix it *and* they are about to act on the result. Tell them plainly that it is not to be trusted and who to raise it with, and route the diagnosis elsewhere.

**The test, when it is not obvious: would this person do something different if they knew?** If yes, tell them, in words they can act on. If no, record it and move on. Volume nobody can act on is not diligence -- it is the noise that teaches people to skip the next warning, including the one that mattered.

The failure mode this rule forbids is not "an error happened." It is **a result that looks complete and is not**, or **a stop that did not have to happen**.

## Detail
Three shapes recur, all of them "graceful" by the narrow reading and violations by this one:

- **The silent fallback.** A missing optional dependency, a config that did not load, a network call that failed -- handled, defaulted, and never mentioned. The next reader has no way to know the result is partial.
- **The empty scan reported as clean.** A check whose input did not exist, whose parser is not installed, or whose history was too shallow to reach what it walks, printing the same "OK" it prints when it genuinely looked and found nothing. "Could not check" and "checked, nothing wrong" must never render identically.
- **The stop that need not be one.** One part failing takes down a whole run that had many independent parts, when the honest outcome was to skip that part, say which, and finish the rest.
- **The warning aimed at someone who cannot act on it.** A stack trace, a script name, or a remedy command put in front of a reader who does not run scripts. It satisfies the letter of clause 3 and defeats its purpose: nothing in it tells that person what is untrustworthy or what to do, and a steady run of them trains the reader to skip the next one -- including the one that mattered. The fourth shape is the newest, and it is the only one that gets *worse* the more diligently the other three are obeyed.

Where a tool has an exit status, "keep going" applies to the *work*, not to the status: a run that could not check something still reports that honestly rather than exiting 0, and a run whose one purpose could not be served at all may still exit non-zero -- as long as it says why, in words naming the fix.

## Why
The three sanctioned degradations look like a list of options and are really one property: **the caller can act on the result.** A clear message naming what is missing and how to fix it, a documented fallback, and a clean non-zero exit all pass that test. The three failures named opposite them do not — and the last two fail it worst, because neither announces that anything happened at all.

The graduation in clause 3 exists because the property in clause 1 and the volume used to deliver it are different things, and only the first is universal. A degraded result must never pass for a complete one -- for anybody. But "announce it where the human will see it" was written by people who run the scripts they are told about, and it silently assumed that reader. Handed to someone who does not, the same sentence is unreadable and unactionable, so it is skipped, and skipping becomes the habit that swallows the important one later. Softening the rule for everyone would be the wrong repair: it would cost the technical reader the loudness that works, to buy the non-technical reader a quiet they should not have on anything that matters. Two axes keep both.

The rule targets dependencies outside the program's own control specifically, because that is where the assumption is invisible. Code that assumes a file exists reads exactly like code that has checked, right up until the environment differs. Nothing in the source distinguishes them, so the check has to be written on purpose rather than noticed in review.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. That pack recorded no originating incident, and this Story says
so rather than inventing one.

**The 2026-09-07 revision has an incident, and it is this repo's own.** The
very deep check that day found five files in Precedent's public engine
citing this practice by name to explain why they degrade rather than fail --
and `precedent_show.py fail-gracefully` exits 1 for anyone outside this team
set, so every one of those citations, and every consumer that vendors that
engine, points at a rule they cannot read. Asked in the same session whether
the rule was right for non-technical adopters, Morgan named the gap: graceful
for minor rules and non-technical readers, loud for important rules and
technical ones. It was not in the text. The catalogue half of the same
finding was larger -- the shipped non-technical document template puts all 66
universal practices in force for an editorial project and exempts none -- and
is being handled where it belongs, in `not_binding` rather than by making
rules quieter. And in that same run this practice's own clause 1 was broken
by the session checking it: a sweep read every practice's sections with the
wrong key, found `None` in all of them, and reported "100% of Stories are
empty" -- a scan that could not read, rendering exactly like a scan that read
and found nothing.

It is also the odd rule out by kind: almost everything around it is a
repository-process rule, and this is a coding-quality rule about what gets
built. It was kept at this level rather than raised to the universal
catalogue for a stated reason -- general enough to want in every project,
but simple enough that a persuasive, attributed upstream submission was not
judged worth the effort yet. That remains the outlet if it changes.

The substance is a list of things outside a program's own control -- a
required config or environment variable, a file assumed to exist, a network
call, a third-party credential -- each of which fails in production and none
of which fails usefully by default. The three sanctioned degradations all
share one property: the caller can act on them. A clear message naming what
is missing and how to fix it, a documented fallback, or a clean non-zero
exit. A raw stack trace, a silent wrong answer, and a hang all fail that
test, the last two worst, because neither announces that anything happened.

## Install
No mechanical check, and this is the second attempt rather than an
assumption (practice `checkable-gets-checked`).

**Clause 1** -- whether code "anticipates its own common failure modes" and
keeps going -- is a judgment about error-handling adequacy across arbitrary
code in any language, not a fixed syntactic pattern: a bare `except:` is
sometimes exactly wrong and sometimes a deliberate, documented catch-all. At
this scope (`applies_to: ["**"]`, no language or shape specified) no static
rule is both broad enough to catch real violations and narrow enough not to
flood.

**Clause 1** -- a degraded result must not render like a complete one -- is
the checkable half, and narrowly so: where a particular family of scripts
must distinguish "could not check" from "checked, nothing wrong," that
family's own check can assert it. `check_deep_check.py` does this for the
check scripts in this set, and Precedent's own harness asserts it for its
gates. That stays the pattern: the general rule is a review judgment, and
each place it actually bites gets its own narrow check.

**Clause 3's second axis is not checkable today, and could be made so.** A
tool cannot know who is reading unless the repository says. If a repo
declared its audience in `precedent.json` -- a `general` document project
versus a `technical` code repository -- a check could at least assert that a
repo declaring `general` never prints a stack trace or a bare script name to
its own users. Recorded as a real option rather than built, because it needs
a field that does not exist yet and one consumer willing to be the first to
declare it.

**Clause 2** -- the silent degrade -- looked more promising, because it has a
shape: an `except` handler whose body neither raises, nor prints or logs, nor
exits, but returns a default. Measured 2026-09-06 against Precedent's own
`tools/` (37 scripts, the most heavily audited Python in this project): **67
hits**, the large majority of them legitimate -- a narrow `except ValueError:
continue` inside a parser loop is correct and has nothing to announce. At that
signal-to-noise ratio the check would be turned off within a week, which is
worse than not having it, so this stays advisory and the measurement is
recorded here rather than re-derived by the next session that has the same
idea. **The 2026-09-07 revision gives that number a reading it did not have
at the time:** 67 mostly-legitimate hits is what measuring a *uniform*
standard looks like when the standard should never have been uniform. Most of
those hits are the low-stake end of clause 3's first axis -- degradations
nobody would act on, correctly silent. Re-measuring against the graduated
rule is worth doing and has not been done; the old figure is kept above
because it is the evidence, not because it is still the verdict.

What IS enforceable is the specific case, not the general one. Where a
particular family of scripts must distinguish "could not check" from "checked,
nothing wrong," that family's own check can assert it -- `check_deep_check.py`
does exactly this for the check scripts in this set, and Precedent's own
harness asserts it for its gates. The general rule stays a review judgment;
each place it actually bites gets its own narrow check.

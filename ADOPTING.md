<!-- Last updated: 2026-08-31 (Buenos Aires) by a phase-3 build session -->

# Precedent

*This is written for someone who has not seen Precedent before and wants to
use it. It assumes no programming, and "assistant" below means whatever
tool you talk to about your work. If you are working on the rewrite itself,
[PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) is the document for you,
not this one.*

## What it is

*The question this document answers:* **I have a project and an assistant
that keeps making the same mistakes. What is Precedent, and would it help?**

Precedent captures the way you and your colleagues have decided to work, and
then holds you to it.

The unit is a **practice**: one short written rule, plus the reasoning behind
it and the story of what went wrong the day someone learned it. A practice
can be anything you would otherwise have to keep saying — *put the date on
anything that quotes an outside source*, *the deliverable does not contain
notes about how it was made*, *check the thing you wanted happened, not that
the command said it worked*. They are yours. Precedent ships a starting
library of general ones, but the point is the ones you add.

Two things then happen without you doing anything more.

**They show up when they matter.** Your assistant is given the handful of
practices that bear on what it is doing right now, rather than the whole
library every time. A library that costs more to carry the bigger it gets is
a library people stop growing.

**Where a practice can be checked, it is.** A practice that can be turned
into an automatic check stops being advice and becomes something that simply
fails when it is broken. This is the part that works: in the work that led to
this project, forty-six rules were written down and two of them had
automatic checks. Those two were never broken. The written ones were broken
repeatedly, including by sessions that had every one of them in front of them
at the time.

**So the honest promise is:** your working habits get written down as you
work, and the ones that can be enforced get enforced. Not that writing a rule
down makes anyone follow it. It measurably does not.

## Adding it to a project you already have

This is the common case and it should be the shortest.

1. Copy Precedent's practice library into your project, as ordinary files
   kept alongside everything else there. It becomes part of the project,
   rather than something fetched from elsewhere while you work.
2. Add a small file at the top of the project — `precedent.json` — naming the
   libraries that apply there. To begin with, that is one: the general one
   you just copied. There is an example in
   [precedent.json](precedent.json) here, which is the one Precedent uses on
   itself.
3. Tell your assistant about it once, in whatever file it already reads when
   it starts.

That is the whole setup. Nothing is downloaded while you work, so an
assistant that starts up with no internet connection still has everything. When the shared library gets
better, you pull the newer version in when it suits you, the same way you
would take a newer version of anything else you had copied in.

**You open one thing to do your work: the project.** The practice libraries
come along with it; they are not extra places you have to open first. If using this meant opening three places before touching anything, the
cost would fall hardest on the smallest changes — the ones that should be
cheapest.

## Setting up your own practices

Some of what you want written down is about **you**, not about the team: how
your name is spelled, which time zone your dates are in, that you like the
tone kept casual. Those live in a **private space of your own** — one
place, visible only to you, that nobody else can open.

You make one, you name it in your own settings (not in any shared project),
and it follows you into every project you work in. You write a personal
practice once; you never copy it, re-approve it, or remember it in three
places. There is a worked example to copy in
[examples/practice-set/](examples/practice-set).

**Nothing personal ever reaches a shared place, and that is enforced rather
than promised.** Three things hold it up:

- Your own practices live in a **separate place**, not a folder inside a
  shared one. Who can open what is decided one whole place at a time, so a
  folder boundary inside something shared is a habit rather than a lock.
- A shared project **cannot name your private space**, even by accident. The
  tools refuse it, and say why: naming it there would tell everyone on the
  team that it exists and where, and their computers would start trying to
  open something they are not allowed to read.
- Nothing is published from this project without passing a check that looks
  for private words — client names, code words, internal labels — in
  everything about to be sent, including the notes attached to each change.
  The list of words to watch for lives in your private space, never in the
  public one, because a list of the words you are protecting is itself the
  thing you were protecting.

Two people working on the same project get **different** sets of practices,
each seeing their own personal ones and neither seeing the other's.

## Sharing practices with a team

A team gets its own private space too — one per team — holding the practices
that team has agreed on. Everyone on the team can read it; nobody else can.

Each team space has **approvers**: a short list of people who can say yes to a
change in it. Whoever creates the space is its first approver, so there is
always at least one and no ceremony to get started. Adding or removing an
approver is itself a change that the current approvers have to agree to,
which is what stops someone quietly adding themselves.

**What approval looks like day to day:** your assistant writes the practice
and asks an approver to look at it. They get a notification wherever they
already get them. They say yes, and it lands. If the approver is you — which
for a small team it usually is — there is no waiting at all: your "yes" in
the conversation *is* the approval.

**You are never blocked waiting for one.** If you want a practice in force
right now and somebody else has to approve it for the team, put it in your
own private space instead. It applies to you immediately, with nobody's
permission, and offering it to the team is a separate step you can take
whenever. An approval queue slows down *sharing* a practice, never *using*
one.

**When two practices disagree**, the more specific one wins: yours beats your
team's, your team's beats the general library. There is one deliberate
exception. A team can mark a practice as one that **cannot be overridden** —
and then it cannot, including by you. Your preference for a casual tone is
about how you work; your team's rule that anything going to a client is
formal is about what you all ship, and the second one has to win. Whenever
that happens, you are told which practice is in force and which one was set
aside. Nothing is dropped quietly.

## What happens as you work

You work normally. Around that:

**It notices.** When you say *"from now on"*, or *"always"*, or *"never"* —
or when you rewrite something an assistant produced, or when the same
instruction comes up a second time, or when a review turns up the same
mistake again — that is the moment a practice is worth writing down, and it
gets noticed rather than depending on someone remembering later.

**It proposes; you decide.** What it produces is a *suggestion*, never a
rule. It comes with a draft of the rule, where it thinks the practice belongs
(yours, your team's, or everyone's), and why. Confirming costs you one word.
Ignoring it costs you nothing, and suggestions expire on their own.

**You approve.** This step is deliberate and it is not going away. An
assistant that writes its own binding rules unsupervised is exactly how the
project that led to this one went from twenty-one rules to forty-six in three
days, and a rulebook nobody agreed to is a rulebook nobody trusts.

**Then it routes and enforces.** Once approved, the practice is filed where
it belongs, shows up when the work calls for it, and — if it can be checked
automatically — is checked from then on.

**And practices can die.** Anything that never comes up, is never cited, or
whose check never trips gets listed as a candidate for retirement. A
collection that can only grow eventually collapses under itself; being able
to remove things is what lets it stay useful.

## What it does not do

**It does not write your rules for you.** It suggests; a person approves.
That middle step is the design, not an unfinished corner of it.

**Writing a practice down does not make it happen.** This was measured
carefully rather than assumed, and the result went against what the project
expected: an assistant carrying the entire library in front of it still
missed about one in six of the practices that applied to the work at hand.
Giving it a smaller, better-targeted selection did not fix that — it missed
more, while costing far less to run. Both arrangements missed *the same
practices*.

Two things follow, and they are the whole reason to be honest about it here.
The selection is worth having because it makes the library **cheap to keep
growing** — roughly twice as much useful guidance per unit of cost — not
because it makes anyone follow the rules. And the thing that actually
produces compliance is the automatic check. Where you can turn a practice
into one, do.

**It is not a substitute for saying things to people.** It writes down what
you have already decided. It has no opinion about whether you decided well.

## If you want the detail

| | |
|---|---|
| The full design, and why each part is the way it is | [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md) |
| What a practice file looks like | [spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) |
| How the right practices get picked out, and what was measured | [spec/LOADER.md](spec/LOADER.md) |
| How the three libraries combine, and which wins | [spec/SOURCES.md](spec/SOURCES.md) |
| An example of a personal set | [examples/practice-set/](examples/practice-set) |

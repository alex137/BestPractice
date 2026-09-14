# How to Use This — A Guide for Everyone Else

*The question this document answers:* **I don't know anything about code
or GitHub — how do I actually use this?**

Someone — usually whoever set up the project — has already installed
Precedent before you ever open it. If that's you and it isn't set up
yet, see [SETUP.md](../SETUP.md) — you paste it to an assistant and it does
the install as a conversation, no code required. Everything below assumes
it's already running.

You talk to an assistant, the same way you'd talk to a capable colleague.
You describe what you want written, changed, or fixed, in your own words.
The assistant does the actual work — you never touch a technical tool
yourself, and your account is deliberately set up so nothing you do can
break the project, even by accident.

## Nothing Is Real Until It's Merged

This is the one piece of machinery worth understanding, because you will
meet the words on your first day and everything else rests on it.

When you ask for a change, the assistant does not edit the live project.
It makes a **private copy** of it — a *branch* — and works there. Nobody
else sees it, and the real project is untouched no matter how badly the
work goes. When it's ready, the assistant opens a **pull request**: a
proposal, sitting on a page, saying *here is the change and here is why*.
Somebody with the authority to say yes reads it and **merges** it, which is
the moment it becomes part of the real project.

**So there are three states, and "done" is only the last one.** Work in
progress on a branch; a change proposed and waiting; a change that has
landed. If you asked for something and it isn't live, it is almost always
sitting in the middle state waiting for a yes.

Three things follow from this that are worth knowing:

- **You can't break anything.** The worst outcome of a bad request is a
  proposal somebody declines. That's the whole point of the arrangement,
  and it's why your account is set up the way it is.
- **Several people — and several assistant conversations — can work at the
  same time** without waiting for each other or overwriting each other,
  because each is on its own copy. This is the thing a shared live document
  cannot do.
- **Whose yes it is depends on the project.** Most people here can propose
  freely and cannot merge — see [What you can't do (on
  purpose)](#what-you-cant-do-on-purpose) below, which is a deliberate
  wall, not a comment on you. **If you are one of the people who can say
  yes**, and you want the assistant to stop asking every time, say **"Go
  merge"** — a standing phrase this project understands to mean *do all of
  it, including the merge, without checking back.*

There are a few more of those standing phrases — **"Park it"**, **"Plain
words"**, **"Three Things"** — and [How to Use This Day to
Day](DAILY_HABITS.md) lists them.

## Personal, Team, and Universal — And Moving Between Them

Before explaining how an idea becomes an official rule, it's useful to
understand the different places a rule can live. Think of it as three
shelves:

- **Your own shelf** — habits and preferences that are just yours. Nobody
  else sees or is bound by what's on it.
- **Your team's shelf** — rules everyone on your team follows. You can be
  on more than one team, each with its own shelf.
- **The public shelf** — rules shared by everyone, everywhere, using this
  system.

There's also a fourth kind, worth knowing about even though you won't be
the one stocking it: **this project's own permanent shelf** — rules built
into this one project specifically, and only this project; they don't come
from anywhere else and don't travel to any other project either. Whoever
set this project up technically maintains that shelf directly. It isn't
something you add to yourself, though an idea you raise can still end up
there if that's genuinely where it belongs.

**Moving a rule from one shelf to another** happens the same way it was
created — just say so. For example, something that started as your own
habit turns out to be something your whole team should do too: say *"I
think everyone should do this, not just me."* Your assistant proposes it
on your team's shelf, using the same approval step described below, and
only removes it from your own shelf once it's actually adopted on the new
one — so there's never a moment where the rule exists nowhere, and never a
moment where it's tracked in two places at once. A rule never moves on its
own; it always needs the same kind of yes at its new home that it needed
the first time.

## A Worked Example, Start to Finish

Say you're drafting client emails, and you notice something:

1. **You say it out loud, in conversation:** *"We should always put the
   client's name at the start of the subject line."*
2. **Your assistant repeats it back**, in your own words, to make sure it
   understood before doing anything: *"Got it — every outgoing email's
   subject line should start with the client's name, from now on. Did I
   get that right?"* You confirm, or correct it.
3. **It figures out how big the idea is** — usually by asking, if it's not
   obvious: is this just how *you* want to work, or should everyone on
   your team do it too?
   - **Just you:** it applies from this point on. Nothing else happens —
     there's nobody else who needs to agree.
   - **Your whole team:** your assistant posts the idea somewhere your
     team's approvers — the people trusted to say yes to shared rules —
     will see it, the same way you'd leave a comment on a shared document
     for someone to respond to. (Technically this is a "GitHub Issue," a
     little discussion thread — you may never need to know that word, but
     you might see it if you ever open the page yourself.)
4. **You wait for a yes, if one is needed.** If an approver is in the
   conversation with you right then, this can happen immediately — their
   agreement *is* the approval. Otherwise, you'll hear back once someone
   responds; nothing is silently dropped in the meantime.
5. **From then on, it's automatic.** Every assistant working on this
   project — yours, a teammate's, in a session next month — already knows
   the rule and follows it without being told again.

## What if It Should Apply to Everyone Using This System, Anywhere?

Same first three steps. The difference is who has to say yes: instead of
one of your team's approvers, it goes up for a real, visible, public
review, and someone independent of you has to accept it before it becomes
real. This is the slowest path, on purpose — it's the one case where no
single person, not even whoever runs the whole shared library, can decide
alone.

Either way: nothing you suggest is ever adopted without a real yes from
whoever it actually affects, and nothing you say is ever quietly
forgotten. An idea nobody has acted on yet stays on record, not lost.

## What You Can't Do (on Purpose)

Your access is deliberately limited so nothing you do can break the
project or publish something by accident — you can comment and propose,
but you can't push changes live or approve them yourself. This isn't
about trust in you personally; it just means a mistake, including the
assistant's, stops at a wall instead of reaching anyone else.

## Learn More

[How to Use This Day to Day](DAILY_HABITS.md) is the
companion to this page: this one is how an idea becomes a rule, that one
is what an ordinary working day looks like. [What This Is (and Why Explore
Using Precedent)](WHY_PRECEDENT.md) for the bigger picture.
[SETUP.md](../SETUP.md) if the project isn't set up yet. If you ever
want the fuller technical version of this page:
[FOR_DEVELOPERS.md](FOR_DEVELOPERS.md).

**And if you hit a word you don't know** — one of this project's own, like
*practice* or *capture gate* — [GLOSSARY.md](../GLOSSARY.md) is the master
list, with each term linked to the rule that defines it.

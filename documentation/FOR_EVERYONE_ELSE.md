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
- **Whose yes it is depends on what the change touches.** Your own
  documents are usually yours to merge; the project's settings, its
  automatic checks and its rules wait for whoever maintains the project —
  see [What you can't do (on purpose)](#what-you-cant-do-on-purpose)
  below, which is a deliberate wall, not a comment on you. **When the yes
  is yours**, and you want the assistant to stop asking every time, say
  **"Go update"** — a standing phrase this project understands to mean *do
  all of it, including the merge, without checking back.* ("Go merge"
  means the same thing.)

There are a few more of those standing phrases — **"Drop it"**, **"Plain
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

## What It Knows About You, and How to Change It

A handful of small things about you are used by every assistant working on
the project, and **you will never be asked for any of them.** Each one has a
sensible answer that applies until you say otherwise:

- **Your name and email address**, which go on everything saved in your
  name. Taken from the account you signed in with.
- **The timezone dates and times are stamped in.** New York, unless your own
  settings say different. (It has to be *some* real place — otherwise records
  made by people in different countries can't be put in order.)
- **How you're referred to in writing** — he, she, or they. **They**, until
  you say which you prefer; nobody guesses from a name.
- **Your own personal rules**, if you keep a set of them — the habits that
  follow you between projects rather than belonging to this one. You don't
  need one, and most people start without.

**To change any of it, just say so** — *"my timezone is Madrid"*, *"refer to
me as he"*, *"my work email is the other one"* — at any moment, in the middle
of anything else. The assistant knows where each one is written down and puts
it there. **You can also ask what it currently has**, the same way.

**None of this is worth a wrong-footed setup conversation**, which is why
nobody raises it on day one: a date stamped in the wrong city's time is a
small, visible, one-sentence fix whenever you happen to notice it. If you
want the technical version — what each setting is called and what breaks
without it — it is
[Per-Machine Setup](PER_MACHINE_SETUP.md).

## Two Things You Can Fill in Whenever You Like

Whoever set this project up was told to do the essentials and stop, so two
files were created empty on purpose and are waiting for you. Neither is
urgent, and a project works perfectly well with both left blank.

- **Your project's own voice** — how this project should sound. Who it
  sounds like, who reads it, the words your field insists on and the ones
  it can't use, and anything you want done differently from the general
  rules. (Kept at `local/practices/project-voice.md`, if you ever go
  looking for it.)
- **`STYLEGUIDE.md`** — how it should look. Colors, fonts, logo rules —
  whatever your brand guideline says, if you have one.

**To fill either in, just say so to your assistant** — *"help me fill in my
project's voice"* — and it will ask you questions and write down your
answers. You can do it today, next month, or never. **Both stay entirely
inside your own project**; nothing in them is ever shared with anyone
outside it.

**Anything you leave blank is a real answer**, not a hole. A project that
hasn't decided how it sounds yet is better off saying so than having someone
guess on its behalf.

## What You Can't Do (on Purpose)

The line is drawn by *what* a change touches, never by who you are. There
are three levels of say-so on a project, and knowing them makes the wall
less mysterious:

- **Anyone who writes for the project** — you, most days — changes and
  merges their own document changes, once the project is set up that way.
- **Whoever maintains the project** looks at anything touching its
  settings, its automatic checks, or the rules everyone follows, before
  that change lands — no matter who asked for it.
- **Approvers** — a named list, sometimes just one person — are the only
  ones who can make a suggested rule official, at whichever shelf (your
  own, your team's, or the public one) it's aimed at.

Your assistant tells you before it proposes anything which of these the
change falls under, so the wall is never a surprise. Whoever administers
the project sets this line up on GitHub itself;
[GITHUB_SETTINGS.md](GITHUB_SETTINGS.md) is their page, not yours — worth
knowing only because that page notes GitHub gives this wall for free on a
public project, but a private one on a personal account needs a paid plan
to turn it on. If your project is private and the wall seems to be missing,
that is usually why, and it's a question for whoever administers it, not
something to chase yourself. This isn't about trust in you personally; it
just means a mistake, including the assistant's, stops at a wall instead of
reaching anyone else.

## Learn More

[Ten Things to Know About How Precedent Works](TEN_THINGS.md) is the one
page with the ideas underneath all of this, each linked back into the
section here that says more.
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

# What This Is (and Why Explore Using Precedent)

*The question this document answers:* **What is Precedent, and why
would a team want it?**

Precedent is a layer that sits between a group of people and their
shared work — **built for teams who collaborate through an AI assistant
rather than a shared live document.**

You talk to an assistant about the work: what to write, what to decide,
what to change. The assistant does the actual editing — you never touch a
file directly. As it works, it also **notices how your team wants to work,
and turns that into written rules** that every future conversation follows
automatically, without anyone having to write a policy document by hand.

This grew out of a broader philosophy about how people and AI should work
together, written up in **[philosophy/](../philosophy/)**. What follows
are the practical things Precedent does that put that philosophy to work,
in five groups.

## Human Collaboration First

Several people work on one thing at the same time, and the tool is
built around that rather than around one person and a chatbot.

### Designed for Multi-Person Collaboration to Shape the Output

**Several people, each with their own assistant, work on the same project at
the same time** — proposing, arguing, adding, cutting — so what finally lands
is shaped by all of them, not by whoever happened to type into the document
last. Nobody has to wait their turn to edit.

### Real Sharing With Review

**The project is shared by construction.** Everyone on it — people and their
assistants alike — works from the same map of the project, the same list of
open items, and the same rules, and proposes changes the others can read and
comment on before anything lands. Nobody forwards a chat transcript, and
nobody has to hope that everyone else's assistant remembers the same things.

### Granular Permission Access & Protocol Applicability

A rule can **stay just yours, apply to your whole team, or join the public
library** everyone using Precedent starts from — you choose which, and a
rule that starts narrow can move to a wider level later if it turns out to
matter beyond where it began.

### Automatically Merges Substantial Changes to the Same Document by Different Collaborators Simultaneously

Two people can rewrite different parts of the same document at once, each on
their own private copy, and their work is combined automatically — not just
one-word tweaks, but **whole rewritten sections**. If two edits genuinely
contradict each other, your assistant **shows you both and asks**, rather than
silently picking a winner.

## Co-Creating With Your Assistant

Every change is worked out with an assistant that argues back — and
nothing lands until a person says so.

### You Work Through Your Agents

There's no separate track for "small" changes that you just make yourself —
**even a one-word edit goes through the assistant**, so every change is
something you and it worked out together, not something that slipped in
unreviewed.

### An AI Assistant Designed to Push Back Smartly on Your Ideas for the Best Result

The assistant isn't there to type whatever you say — it's **expected to
question a weak idea or suggest a better one**, so what actually lands is
the strongest version of what you wanted, not just the first draft of it.

### You Approve Everything, at Whatever Level of Granularity You Want

**Nothing takes effect unapproved.** A rule that's just yours applies the
moment you agree to it; a rule for your whole team needs one of your
team's approvers to say yes. **Permission is just as granular**: some people
can only suggest ideas in plain language, others can approve changes
outright — set per person, not all-or-nothing.

### Everything Runs Through the Claude Code App — Desktop or Mobile

**You can tell your assistant what to do by voice, while walking, or from
anywhere at all** — and there is nothing to install on your own computer. If
you would rather run it on your own machine, it still works that way too
(*as of 2026-09*).

## Automatic Protocols

How your team works gets written down as you work — and then applied to
every conversation after it, without anyone maintaining a rulebook by hand.

### Codifies Key Universal Best Practices on Effective Work

Precedent doesn't start you from a blank page: it ships with **a starting
library of proven, general practices** for working effectively together,
distilled from real teams' experience, alongside whatever rules your own
team adds.

### Practices, Created Automatically, Confirmed by People

Not only does it codify general best practices to use, but it creates new
practices based on your instructions. Each new one **only takes effect once a
person confirms it**, though — whether that's you approving your own
habit on the spot or a teammate signing off on a shared one.

### Enforcement Instead of Vigilance

**The rules that matter are backed by small programs that fail loudly.** A
chat thread can only promise to follow a convention; a project set up this way
can check it, every time, and stop the change that breaks it — so keeping to
your own rules doesn't depend on anybody staying vigilant.

### Every Decision Comes With Its Reasoning Attached

**Not just what was decided, but why** — and a link back to the exact
conversation or issue that produced it. Months later, nobody has to guess
why a rule exists or dig through chat logs to find out.

### Version Control and an Audit Trail

**Every change is recorded: who made it, when, what changed, and — because the
practices here require it — why.** Anything can be undone, and any two
versions of anything can be compared side by side. An assistant's memory
feature offers none of that.

## Invisible Memory

The project keeps its own record as it goes, so nothing that matters
depends on anyone remembering it.

### GitHub Becomes Your Memory: Documents, Decisions, and The Why

Documents, the decisions made about them, and the reasoning behind each one
are all kept together in **one place your team already owns** — so the project
remembers itself. **A git repository is the shared file system**: a project
folder that keeps every version of everything in it, and that every person and
every assistant works out of.

### State That Doesn't Decay

**Open items, decisions, lessons about your setup, and naming conventions are
all committed text.** A session six months from now — on a different model, in
a different tool, or run by a different person — picks up exactly where the
last one left off, because "where we left off" is a file.

### You Control What the Assistant Knows

**Every session starts by reading the project's map ([MAP.md](../MAP.md)) and
its instructions file**, so what the assistant knows is something you decide,
by editing files. Nothing load-bearing lives in a hidden memory store or
depends on a lucky recollection from an old conversation. If sessions keep
missing something, you add a row to the map's quick index — a one-line,
permanent fix.

## Open Source and Open Documents

Nothing here is a format you can't read or a service that can take your
work away.

### Open Source, on GitHub — No Vendor Lock-In

**Git repos are your file system.** Everything here is open source and built
on top of GitHub, a platform you already control your own data in. There's
**no proprietary format and no company that can shut down** and take your
project's memory with it.

### Plain Text Is the Source — All Other File Types Are Inputs or Outputs

**Plain text is what your team edits and keeps a history of**, because text
is what can be compared and merged. Every other file type is an input, an
output, or both: a Microsoft Word document, an Excel spreadsheet, or a
PowerPoint deck goes in at the start and comes back out at the end.

## Learn More

The philosophy behind all of this lives in
[philosophy/](../philosophy/). For how to actually use Precedent: [a how-to for
developers](HOW_TO_USE_THIS_DEVELOPERS.md), [a how-to for everyone
else](HOW_TO_USE_THIS_EVERYONE_ELSE.md), or — once it is running — [the
day-to-day habits](HOW_TO_USE_THIS_DAY_TO_DAY.md). Or explore [this
repo](https://github.com/alex137/BestPractice).

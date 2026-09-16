# Ten Things to Know About How Precedent Works

*The question this document answers:* **What are the ideas underneath all
of this, in one page?**

Ten, each in a few sentences. Every one links to where the two longer
guides say more — the plain-language one for people who are not
developers, and the technical one for people who are. Read this page first;
read the others when one of the ten turns out to matter to you.

## 1. You Work Only Through an Assistant, Never on the Files Directly

You say what you want in your own words — *"rewrite the second paragraph"*,
*"pull the budget out into its own document"* — and the assistant makes the
change. A file changed by hand is invisible to everything else here: no
record of why, no checks run, nothing kept in step. The rule is not about
being careful; it is that the assistant is the only path along which the
project stays whole.

- Plain: [Don't Edit the Files Yourself — Ask](DAILY_HABITS.md#1-dont-edit-the-files-yourself--ask)
- Technical: [All Interaction Happens Through Chat or Voice With an Assistant](FOR_DEVELOPERS.md#all-interaction-happens-through-chat-or-voice-with-an-assistant)

## 2. The Project on GitHub Is the Memory, and Nothing Is Real Until It Is Merged

A conversation is disposable; the project is what lasts, so anything that
matters has to end up in it. Work happens on a private copy, is proposed as
a pull request, and becomes real only when it is merged — which means
several people and their assistants can work at once without overwriting
each other. **"Go merge"** is the phrase that ends a piece of work: save it,
publish it, say where it went, no further questions.

- Plain: [Nothing Is Real Until It's Merged](FOR_EVERYONE_ELSE.md#nothing-is-real-until-its-merged), [Say "Go Merge" When You're Ready](DAILY_HABITS.md#4-say-go-merge-when-youre-ready)
- Technical: [GIT.md — The Eight Ideas](../GIT.md#the-eight-ideas), [GitHub Becomes Your Memory](WHY_PRECEDENT.md#invisible-memory)

## 3. A Rule About Any Pattern Is a Practice

A practice is one short written rule, the reasoning behind it, and the story
of the day someone learned it. It can be about anything you would otherwise
keep saying: how a date is written, what a deliverable must not contain,
how a reply should be pitched. The library ships with general ones; the
point is the ones you add.

- Plain: [What It Is](ADOPTING.md#what-it-is), [When It Gets Something Wrong, Make It a Rule](DAILY_HABITS.md#2-when-it-gets-something-wrong-make-it-a-rule)
- Technical: [spec/PRACTICE_FORMAT.md](../spec/PRACTICE_FORMAT.md), the [live catalogue](../practices/)

## 4. The System Proposes a Practice; a Person Approves It

When you say *"from now on"* or *"never again"*, or correct the same thing
twice, the assistant notices and drafts a practice — a suggestion, not a
rule. It lands only when the right person says yes, and who that is depends
on the level it belongs to (item 6). A rulebook nobody agreed to is a
rulebook nobody trusts, so that middle step is the design.

- Plain: [How an Idea Becomes a Practice](ADOPTING.md#how-an-idea-becomes-a-practice), [A Worked Example, Start to Finish](FOR_EVERYONE_ELSE.md#a-worked-example-start-to-finish)
- Technical: [Walkthrough: Turning a Habit Into a Practice](FOR_DEVELOPERS.md#walkthrough-turning-a-habit-into-a-practice), [How Practices Are Approved](FOR_DEVELOPERS.md#how-practices-are-approved)

## 5. Where a Practice Can Be Checked, It Is Enforced

Writing a rule down does not make anyone follow it — that was measured, and
it does not. A practice that can be turned into an automatic check stops
being advice and simply fails when it is broken, before the work is saved
or merged. The ones that cannot be checked stay advisory, and the
documentation says so plainly rather than promising otherwise.

- Plain: [What It Does Not Do](ADOPTING.md#what-it-does-not-do)
- Technical: [How Enforcement Works](FOR_DEVELOPERS.md#how-enforcement-works), [spec/ENFORCEMENT.md](../spec/ENFORCEMENT.md)

## 6. A Practice Belongs to You, to a Team, to One Project, or to Everyone

Four levels, each a separate place: your own private set, which follows you
into every project; a team's private set, of which a project can declare
several; the project's own rules; and the public library everyone starts
from. When two disagree the order is fixed — team, then the project's own,
then yours, then the library — and a rule marked as not overridable holds
whatever sits above it. A rule can move between levels later, through the
approval its new home requires.

- Plain: [Personal, Team, and Universal — And Moving Between Them](FOR_EVERYONE_ELSE.md#personal-team-and-universal--and-moving-between-them), [Sharing Practices With a Team](ADOPTING.md#sharing-practices-with-a-team)
- Technical: [Four Levels, Each Just Another Repo](FOR_DEVELOPERS.md#four-levels-each-just-another-repo), [spec/SOURCES.md](../spec/SOURCES.md)

## 7. What You May Change Is Decided by What the Change Touches, at Three Levels

Everyone invited to a project is a **contributor**, with the same GitHub
role: the documents are theirs to write and merge. A **maintainer** is named
in the project's registry, and a change to the machinery — settings,
checks, the rules themselves — waits for their review. An **approver** is
named in a practice set, and only an approver lands a practice there; anyone
else suggests one. Nothing anywhere records whether a person is technical;
the line runs through paths and lists.

- Plain: [What You Can't Do (on Purpose)](FOR_EVERYONE_ELSE.md#what-you-cant-do-on-purpose)
- Technical: [Who May Change What](FOR_DEVELOPERS.md#who-may-change-what), [GITHUB_SETTINGS.md](GITHUB_SETTINGS.md), [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md)

## 8. A Few Standing Phrases Mean Exactly One Thing

Plain English always works, but a short vocabulary saves a paragraph each
time: **Go merge**, **Park it**, **Three Things**, **Plain words**, **Weak
yes**, and the rest. Each is itself a practice, so its meaning is written
down and the assistant is guaranteed to recognize it. Say **"Vocabulary"**
to have the current list read to you.

- Plain: [The Rest of the Vocabulary](DAILY_HABITS.md#the-rest-of-the-vocabulary)
- Technical: the command practices, starting at [go-merge](../practices/go-merge.md) and [vocabulary](../practices/vocabulary.md)

## 9. What Is Yours Stays Yours, and That Is Enforced

Your own practices, your name, your timezone, how you like to be addressed
and how technical your replies should be live in a private place only you
can open; a shared project cannot even name it. Nothing leaves a project for
a public place without passing a check for private words, and the list of
those words lives in your private place too. Two people on one project each
see their own rules and never the other's.

- Plain: [What It Knows About You, and How to Change It](FOR_EVERYONE_ELSE.md#what-it-knows-about-you-and-how-to-change-it), [Setting Up Your Own Practices](ADOPTING.md#setting-up-your-own-practices)
- Technical: [PER_MACHINE_SETUP.md](../PER_MACHINE_SETUP.md), the leak gate at [tools/leak_gate.py](../tools/leak_gate.py) (`--explain`)

## 10. Always Explain Why: Focus on the Problem

Tell the assistant the problem behind a request, not just the fix you have
in mind — *"this client already reviewed the draft, so skip anything
redundant with it"*, not just *"skip that step."* Naming the problem is
what lets it recognize the same case again without being told twice, catch
what a prescribed fix would have missed, and it's the raw material a
practice gets written from when a correction repeats — a bare instruction
finishes the one task in front of it and teaches nothing past that.

- Technical: [People and the Model](../philosophy/OUR_PHILOSOPHY.md#explain-the-why)

## Where to Go From Here

[What This Is (and Why Explore Using Precedent)](WHY_PRECEDENT.md) is the
pitch. [How to Use This — A Guide for Everyone Else](FOR_EVERYONE_ELSE.md)
and [How to Use This — Technical Guide](FOR_DEVELOPERS.md) are the two
tracks the links above point into. [How to Use This Day to
Day](DAILY_HABITS.md) is the short one to keep open.

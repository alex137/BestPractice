# How to Use This Day to Day

*The question this document answers:* **It's set up and I've used it once
— what does a normal working day actually look like?**

The other guides here cover getting Precedent installed and how an idea
becomes an official rule. This one is about the boring middle: the
handful of habits that make it work, on an ordinary Tuesday, when nothing
special is happening.

There are four, and none of them is technical.

## 1. Don't Edit the Files Yourself — Ask

**Say what you want changed, in your own words, and let the AI Assistant
make the change.** *"The second paragraph is too defensive, rewrite it."*
*"Pull the budget section out into its own document."* *"This date is
wrong, it should be the 14th."*

This is not a rule about being careful, and it isn't there because your
edits would be bad. It's that an edit made by hand is invisible to
everything else here. The AI Assistant writes down *why* a change happened,
keeps the documents that describe it in step, and runs the project's own
checks before anything is saved. **A file quietly changed by hand skips
all of that** — and the next person, or the next AI Assistant, has no way to
know it happened or what it was for.

If you find yourself opening a file to fix something small, that's the
moment to paste the sentence into the chat instead.

## 2. When It Gets Something Wrong, Make It a Rule

**This is the habit that pays for itself, and it's the one people skip.**

When the AI Assistant does something you don't want — wrong tone, wrong
format, an assumption it shouldn't have made, a step it skipped — you can
just correct it and move on. The work gets fixed. But the correction dies
with the conversation, and in a week you'll be typing it again.

Instead, say so explicitly:

> *"Don't do that again — make it a rule."*
>
> *"From now on, always X."*
>
> *"That's the second time. Write it down so it doesn't happen a third."*

Your AI Assistant will write the rule down properly, work out whether it's
just yours or something your whole team should follow, and tell you where
it put it. From then on it's automatic — for you, for your teammates, and
for a session next month that has never met you. [How to Use This — A
Guide for Everyone Else](FOR_EVERYONE_ELSE.md) covers what
happens next, including who has to approve it.

**Small annoyances count.** The rules worth having are mostly not grand
principles; they're the specific thing that went wrong once and would
otherwise go wrong again.

## 3. Ask It Anything

**The AI Assistant has read the whole project, and you can just ask.** This
is underused, because it doesn't feel like a task.

- *"What changed in here this week?"*
- *"Why is this written the way it is?"*
- *"Who decided this, and when?"*
- *"Is there already a rule about this?"*
- *"What am I forgetting?"*

You are not interrupting anything and you don't need to phrase it well.
If the answer is written down somewhere, you'll get it with a link; if it
isn't, you'll be told that, which is also an answer — usually it means
something worth writing down never was.

## 4. Ask for It to Be Saved When You're Ready

Everything you do in a conversation is, until you say otherwise, **only
in that conversation.** It hasn't been shared, and if you close the tab it
may not survive.

**Telling your AI Assistant to save your work to GitHub** is how you end
that. Say it in your own words and it saves the work properly, puts it on
the project's main branch where your colleagues can see it, and tells you
where it went. The project's own checks still run when it is saved.

Say it when you're done with a piece of work and want other people to
have it, or when you simply want it saved outside the conversation before
you stop for the day. **When in doubt, say it** — saving something small
costs nothing, and losing an afternoon's work because it was never saved
costs an afternoon.

## The Rest of the Vocabulary

There is a small set of phrases the AI Assistant is guaranteed to
recognize. You never have to use any of them — plain English works — but
each one saves you a paragraph of explaining:

<!--gen:vocabulary-->
| Say this | And it will |
|---|---|
| **Archive** | Check whether anything from this session is still outstanding -- a merge, something the assistant is waiting on, a recommendation -- and either archive it right then or tell you exactly what's left. Synonym: Archive? |
| **Drop it** | Mark the open question as parked and drop the subject. It won't be raised again unless you raise it. |
| **My options** | Lay out the real choices in plainer words, the good and the bad of each, and tell you which one it recommends and why -- and when it's about a current issue meant for another session, add that session's id and link, which repository has to be the primary seed root, and which others need to be attached, then hand the whole thing back as one paste-ready block. |
| **Prompt Please** | Write up the situation, the problem, your recommended action and why, and hand it back as one prompt ready to paste straight into a new session -- naming which repository to root it in and which others to attach -- opening by saying it is a suggestion from another session, to analyze and push back on rather than carry out as the person's instruction, and closing with a request that any reply come back as its own paste-ready block, signed with the replying session's name and link. |
| **Reduction pass** | Measure everything a session loads before it starts work, make room by moving things rather than deleting them, and show you exactly what moved and what it saved. |
| **Root issues** | Look back over everything this session has done so far -- every bug, issue or warning it ran into, and every fix or band-aid it applied -- and hand you each one that should also be fixed in Precedent, a precedent-* repo, the template that generates the file, or another related repo, all in one paste-ready Prompt Please for a single session rooted in every repo they touch, with those repos named first -- including ones you may already have passed on from another session. Synonym: Root fixes |
| **Simple please** | Drop the formal register and explain it the way somebody would say it out loud — same answer, plainer telling. |
| **Three Things** | Tell you the three most important things you need to know right now, in three short lines. |
| **Todo reminder** | Write the thing into the open-items file AND mark it as something to remind you about, so later sessions bring it up rather than waiting to be asked. |
| **Vocabulary** | List every standing phrase this project recognizes and what each one does, then the words worth knowing to follow a conversation about it. |
| **Weak yes** | Go ahead with it, and record that you were not convinced. Nobody will ask you why. |
| **What's new?** | Write an entry for every finished day that changed the project and has none yet, say which days were quiet and skipped, then show the log: its link first, the newest entries, what changed today so far, and ask what you want to know more about. |
<!--/gen:vocabulary-->

*That table is built from the rules themselves every time this page is
rebuilt, so it cannot fall behind the AI Assistant. Numbers by:
precedent_vocabulary.py — or just say **"Vocabulary"** and your AI Assistant
will read you the current list.*

Words that name a thing rather than ask for something -- "individual set",
for one -- are on [Our Language](OUR_LANGUAGE.md),
and "Vocabulary" reads them out after the phrases.

**"Drop it", "Three Things" and "Simple please" are the three worth learning first.** "Drop
it" is how you stop being asked about something you've decided not to
decide. "Three Things" is the one to open with after a few days away. **"Simple
please" is the one for when an answer is correct and you have read it twice
anyway** — it stays in force for the rest of the conversation.

## Why Any of This Works

The single idea underneath all four habits: **the conversation is
disposable, the project is the memory.** A chat thread is gone in a week —
scrolled past, closed, or simply too long to find anything in. Anything
that matters has to end up in the project itself, where the next person
and the next AI Assistant will actually encounter it.

That's what "make it a rule" is for, and it's what saving your work to
GitHub is for.
Habits 1 and 3 are the same idea from the other direction: work through
the AI Assistant so the project keeps up with you, and ask the project
questions instead of trying to remember the answers.

## Learn More

[Ten Things to Know About How Precedent Works](TEN_THINGS.md) for the
ideas underneath these habits, one page. [What This Is (and Why Explore Using
Precedent)](WHY_PRECEDENT.md) for the bigger picture. [How to
Use This — A Guide for Everyone
Else](FOR_EVERYONE_ELSE.md) for how an idea becomes an
official rule and who approves it. [How to Use This —
Technical](FOR_DEVELOPERS.md) if you want the mechanics.

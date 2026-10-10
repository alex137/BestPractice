# Staying Informed: How You Hear What's Happening

*The question this document answers:* **Other people and other AI
Assistant conversations are changing this project too. How do I find out
what they did, what broke, and what is waiting on me?**

## The Short Version

**Precedent tells you things inside the conversation you already have
open.** It doesn't send newsletters, it doesn't run a chat bot, and it
doesn't ping you on a timer. Everything worth knowing is written into the
project itself. **The next time any AI Assistant opens it, the Assistant
reads what's there and tells you what matters before it answers your first
question.**

That works because of one habit underneath everything else here: **if
it isn't written down in the project, it didn't happen**. A decision made
in chat and never written down is lost the moment the conversation closes,
so nothing important is left there.

The rest of this page goes question by question.

## "What Changed in This Project?"

**Ask *"What's new?"*** The AI Assistant brings the project's daily log
(Precedent's own is
[WHATS_NEW.md](https://github.com/alex137/BestPractice/blob/staging/WHATS_NEW.md)) up to date and shows it to you: one
entry for each day something happened, each with the **three or so most
important changes** of that day, in plain words. Quiet days get no entry.
Changes to documents count as news as much as changes to code.

The log is a record of the project, not of you: **it covers everyone's
work, yours included**. If you're the busiest person on a project, most of
it will be things you already know. The next section is for that.

## "What Did Other People Do?"

**Once a day, the first reply in your first conversation opens with what
other people landed since your own last change**, before it answers what
you asked. It picks the three or four that matter most to you and leaves
the rest out; ask if you want the full list.

**A change to a rule, or to how the AI Assistant behaves, is always
included**, however small it looks. That is the kind of change that
otherwise surprises you weeks later, when an Assistant does something you
didn't expect and nobody remembers why.

This one is switched on per project by a shared practice set
([Shared Practice Sets](SHARED_PRACTICE_SETS.md)), so a project that hasn't
turned it on won't do it.

## "Did Something Break While I Wasn't Looking?"

Some work runs with nobody watching: an automatic check on GitHub, a
scheduled job. When one of those gets stuck, it has to reach a person who
can fix it, and a line buried in a log nobody opens doesn't.

- **A stuck job opens an issue on GitHub**, so you get GitHub's usual
  notification, with nobody working. If it
  can't open one, it writes the problem into the project's to-do folder
  instead, and **the next conversation in that project tells you about it
  first** and fixes it.
- **Precedent's own test does this.** When the full test of a change that
  went live fails, it opens an issue saying so, and closes that issue
  itself once a later run passes. Changes go live first and are tested
  after, deliberately, so work isn't held up waiting for the test; the
  issue is how you hear when one goes wrong.
- **You can do the same for your own jobs.** Anything you run unattended
  in your own projects, such as a job that keeps a calendar in sync, can
  open an issue when it fails. **It's the simplest way to get an urgent
  notification out of a project**, because it reaches you through GitHub
  whether or not anyone has a conversation open. Ask your AI Assistant to
  set it up; the practice behind it is
  [automation-issues](https://github.com/alex137/BestPractice/blob/staging/practices/automation-issues.md).
- **A job that skips something optional says so.** If it couldn't reach
  something it didn't strictly need, it carries on and reports the skip.
  A silent skip looks exactly like a job that's working.

## "Am I Running an Old Version of the Rules?"

**At the start of every conversation, the AI Assistant checks whether
Precedent, or any practice set your project uses, has moved on since your
project last took an update, and tells you right away.** Nothing updates
behind your back: taking the update is your call, with the phrase
*"Update Vendors"*.

**If it couldn't check, it says so.** "I couldn't check" never gets reported
as "you're up to date". The same goes for a practice set that didn't load:
the Assistant names it and says its rules are missing from this
conversation, rather than acting as though that set had no rules.

When two rules disagree, **you're told which one is in force and which one
was set aside**.

## "What's Waiting on Me?"

- **Anything you'll need to know later becomes a to-do item**, written
  into the project's to-do folder rather than left in the chat. Each item
  says whether an Assistant may bring it up with you. Most say no: they
  wait quietly until you ask about them. Only the ones marked to ask get
  raised, so you aren't nagged about things you've already set aside. Say
  *"Drop it"* and an item is never raised again.
- **A reminder is a to-do item with a date.** Say *"Todo reminder"*, what
  to remind you of, and when. From that date the item counts as due, and
  it waits in the project for whoever opens it next. That's deliberate: an
  alarm set inside one conversation stops when that conversation closes.
  **Once it's due, the wrap-up at the end of a reply brings it up**, ahead
  of anything picked by topic: the one that has waited longest, once per
  conversation, until you say it's done, give it a new date, or say
  *"Drop it"*. All the due ones are also listed together at the bottom of
  the project's to-do list (Precedent's own is
  [todo/TODO.md](https://github.com/alex137/BestPractice/blob/staging/todo/TODO.md#due-reminders)).
- **A practice someone wants added to your team's set** reaches you
  through the notifications you already get, if you're one of the people
  who approve those ([Adopting Precedent](ADOPTING.md)).
- **Every reply ends with a short wrap-up** that says where this
  conversation's work is, whether it's finished, and whether you can close
  the conversation. If something needs you, it says so there.

## Telling Others What You Found

Hearing is half of it. The other half is how something *you* run into
reaches the people who should know.

- **Say what you want kept, and it's written down.** Decisions, findings
  and open questions go into the project, where every later conversation
  and every teammate will find them.
- **Something that's wrong in Precedent itself**, not just in your
  project: say *"Root issues"*, and the AI Assistant gathers everything this
  conversation hit that belongs upstream into one ready-to-paste request
  for a new conversation that can fix it there.
- **An improvement your project made that others could use** goes back to
  Precedent as a proposed change ([Installing Precedent](INSTALL.md),
  "Periodic Check-In"), checked so nothing private leaks out with it.
- **A message from another conversation is advice, not orders.** If you
  paste in what another Assistant wrote, this one checks it before acting
  on it, and tells you where it disagrees.

## What It Won't Tell You

**If nobody opens a conversation in a project, nothing in this page
happens.** The daily note, the reminders, the "you're behind" warning:
each one waits for the next conversation to come along. The exceptions
are a GitHub issue opened by a stuck job or a failed test, which reaches
you through GitHub's own notifications, and an approval request, which
reaches you through the notifications you already get, whether or not
anyone is working.

That is a deliberate trade. Scheduled jobs cost money, break silently when
the conversation they belong to closes, and send messages nobody reads.
Precedent picked the opposite: **nothing gets pushed at you; it's all
waiting in the project for the next conversation.** If a project
goes quiet for weeks and something there needs a person, the GitHub issue
is the only thing that will find you.

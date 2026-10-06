---
slug:        report-up-the-chain
title:       Report to whoever tasked you; send noticed work up, not out
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Finishing a spawned or triggered task is a moment, not a file; the occasion index reaches it."
occasion:    "finishing a task a session was spawned or triggered to do"
gates:       []
index_clause: "report to whoever tasked you; noticed work goes up, never out as an offer"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan F, drafted 2026-10-05, moved from the shared set precedent-shared-working-style; merged in PR #879 on 2026-10-05"
strength: decided
---
## Rule
**A session reports to whoever tasked it.** Its closing message says what it did and what is blocked, and stops there. Work it noticed along the way but was not asked to do goes back up the same channel it was tasked through, named as an observation -- never out to a person as an offer of more work. Where a session was spawned or triggered by another session, "up" is that session, not the human reading over its shoulder: a proposal that reaches a person directly is one they will reasonably read as new work, and acting on it opens a second thread against something another session may already own.

**This is not a rule against initiative.** Noticing the adjacent thing is most of the value of having read the repository closely, and suppressing it wastes that. What the rule governs is the destination and the shape: up rather than out, and as a finding with what it would touch, so that whoever holds the queue can see whether it is already in flight -- not as a question sitting in front of somebody who cannot know.

## Detail
The distinction that matters is between **reporting** and **shopping**. "Here is what I did; here is what is blocked; I also noticed X, which touches Y" is a report, and belongs in every closing message that has an X. "Shall I also do X?" put to a person is shopping, and it costs three things at once: their attention, the risk of a duplicate thread, and the session's own context if they answer and it resumes.

Where a session genuinely cannot proceed without a decision, that is a blocker, and part (4) of `answer-first-ask-before-long-work` already says what to do with it -- ask early, keep working on everything the answer does not touch. This rule is about the other kind: the thing that would be good to do next and blocks nothing.

A session that spawns another names it in its own report -- session id and subject -- so that any one branch of a fleet tells the reader the rest of it exists. That is the same obligation pointed downward: the tree is only legible if each node reports its children.

## Why
A fleet has exactly one queue-holder, and it is whoever is orchestrating it. Every session that proposes work straight to a person makes that person the integration point between agents instead -- and a person cannot tell a genuinely new idea from one that three sessions already have in flight, because nothing in front of them says which is which.

## Story
**2026-09-12.** A day of work across a practice engine and several of its sources ran a fleet of sessions, each spawned to reach a repository the others could not. Two failures came out of the same shape.

A session read a sibling's own status summary, which said it had produced no branch and its task was moot. Taking that at face value, it wrote the change itself, ran the gates, pushed, and opened a pull request -- and only then found that a third session, spawned by one of the first two and never visible to it, had merged the same change twenty minutes earlier. The duplicate was closed unmerged. The status summary had not lied; it described intent, and lagged.

Separately and repeatedly, sessions ended their reports by offering adjacent work. Morgan's own account of the cost: *"each session doing its thing THEN ASKING 'do you want to do this other thing?' (EVEN WHEN other sessions are working on that same issue) and I just read it and think it is something DIFFERENT so I start a repetitive thread really eats up tokens and creates needless duplicate work."*

A rule against spawning sessions was proposed as the fix and **rejected by Morgan the same day** -- spawning is the only route to a repository owned by somebody else, and the alternative in practice is a person carrying work between windows, which is worse every time. So the answer is not fewer sessions. It is that a session's findings travel up the chain that tasked it, where they can be deduplicated, rather than out to a person who has no way to know what else is in flight.

## Install
No mechanical check. Whether a closing message reported or shopped is a judgment about its wording and its destination -- a grep for a question mark would flag every legitimate blocker and miss a proposal phrased as a statement. The observable half is the duplicate that results, and by then the work is already spent.

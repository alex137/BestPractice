---
slug:        the-boildown
title:       "The Boildown: every reply closes with it, in a fixed order"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    ""
gates:       ["reply"]
index_clause: "every reply ends with The Boildown, in a fixed order, archive line last"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  ["next-steps-after-commit", "merged-session-offers-a-practice", "handoff-is-pasteable", "closing-items-are-this-thread", "asks-stand-alone", "archive-a-finished-session"]
overrides:   null
added:       "2026-09-15"
approved_by: "Morgan, 2026-09-15 -- designed over several turns (bullet
  labels, ordering, the heading rename away from \"Next Steps\", keeping
  repository and branch names in the first bullet) and authorized in his own
  words: \"Let's go - go merge, do it, go update\". strength: decided."
strength:    decided
---
## Rule
**Every reply ends with a real markdown heading, `## The Boildown`, and nothing else may claim that heading.** Not "Next Steps", not a bold lead-in -- a bold line is exactly what the rest of a reply is already full of, and it does not survive being skimmed. This applies to every reply, not only one that made a commit: the point is a place the person can always look, not a report on what just happened.

**Under it, a bullet list, one line per item wherever the content allows it.** There are two shapes, and the second is the first with six items added before the close.

### Every reply: three items, in this order

1. **Your next steps.** What the person needs to do now, named in plain words -- no slug, no bare PR number, no reference that only makes sense with the thread open. If it names a decision, say what the decision actually is, and say what the session itself would do and why, in the same clause -- an ask that hands over the question and keeps the answer has moved the work, not done it. If it sends the person to another session, it carries that handoff's three things: which repository, the exact text to paste, and how to report back -- written for a reader who cannot see this conversation. If it means clicking somewhere, the link is there. **If there is nothing, say so explicitly** -- "Nothing blocking for you to do now." -- never silence and never dropping the bullet because it would be empty.
2. **What's blocking, if anything.** One sentence, on what is blocking the *session* -- never the items already covered in the bullet above, which are the person's to act on, not blockers. Skip this line entirely when nothing is blocking; do not write "nothing is blocking me." This is also where a major issue or problem the session hit belongs, in one sentence -- not a minor one, and not the earlier one this section spent months getting rid of about commits being behind or the wrong author name, which stays gone.
3. **Optional, if anything.** Something useful but not required, on-topic for this thread -- never an item that belongs to a different session's work. Say plainly that it is optional: "Optionally, you may want to...", with a link and exact wording where one applies. Skip the line entirely when there is nothing.

### A reply that is ready to close the thread: six more items, then the archive line

A reply may only add these once the three conditions below all hold -- the same three that gate the archive line, checked first:

1. **The work is safe somewhere that is not this session's container** -- pushed, published, or deliberately abandoned. A published artifact is safe the moment it publishes; there is no separate push to wait for.
2. **Nothing is left to do directly in this session** -- no open pull request of its own, no question still waiting on the person, nothing queued to push, no other action that has to happen in this specific window. A non-blocking loose end does not fail this -- a minor suggestion, a question that doesn't change what happens next, something the reply says it is waiting on that will not change the result. Name it and move on; it does not hold the close open.
3. **No Routine is bound to this session.** A Routine created with `persistent_session_id` fires into one named session, and an archived session accepts no events -- check `list_triggers` before adding these six items or saying the archive line. A Routine that spawns a fresh session on each firing is unaffected.

When all three hold, add, still in order, after the three above:

4. **Branches safe to delete**, scoped to this thread's own work only. Where the session itself merged a pull request, name that PR's branch and give the PR's own link -- GitHub puts a one-click delete button on a merged PR's page. Where a branch is safe on other grounds (its PR merged or was superseded, discovered rather than performed by this session), name the branch and either its PR's link or, if it has none, the repository's branches page with the branch's name so it is a click away. Omit the item entirely when there is nothing to flag -- never write that there was nothing.
5. **Other sessions on the same issue**, if any are known to be live on it: "Other relevant sessions to keep an eye on:" with a link to each. Only sessions on *this* thread's own subject -- never a passing mention of unrelated work happening elsewhere. Omit when there are none.
6. **Sessions this one spawned**, if any, each with its link. Omit entirely when this session spawned nothing -- most sessions do not, and saying so every time is exactly the noise this rule exists to avoid.
7. **A practice idea, at most one**, and only when all four hold: something was actually merged this session; the rule came from this session's own work, not a general good idea or something noticed elsewhere; and it has not already been raised in this closing list under a different bullet. State it in one sentence, gently, as a suggestion rather than a decision already made. Most closes have nothing here, and that is the ordinary case, not a gap.
8. **A Todo worth a look, at most one**, and only if it is a good fit: something in the open-items file that bears on this thread's own subject, or, failing that, an item explicitly marked urgent or important. Introduce it as a change of subject -- "Here's an unrelated Todo you might want to look at:" or "Here's a less important Todo you might want to look at:" -- with its link. Say nothing when neither kind of item exists.
9. **A compact check.** If this is a good moment to compact -- the thread has landed a deliverable and what's next does not depend on how this one was reached -- say so: "Now is a good time to compact the session." Say nothing here when it plainly is not; this bullet is independent of the separate, mechanically-enforced compact offer below, which fires on its own schedule regardless of where the thread stands.
10. **The archive line, always last, always one of two fixed sentences.** "You can archive this session." when the three conditions above all hold and every other item on this list that could still need the window open has been said and dealt with. Otherwise: "Don't archive this session yet" -- naming what it is waiting on, whether that is something on the person or something the session itself still holds open. An archive line with no reason after it is exactly the line nobody can act on.

**None of this replaces the separate compact-offer requirement.** Once this conversation has grown 100,000 tokens since it last said so, a reply says one of "This is a cheap point to compact" or "Not a cheap point to compact" regardless of which of the two shapes above it is using or where item 9 landed. That offer is unconditional once the threshold is crossed; item 9 above is not -- it is a judgment call at any point, the mechanical offer is a floor under it.

## Detail
**Why one section instead of several practices.** The six things this replaces were six separately-triggered rules, most of them reachable only through the reply gate, several of them enforced only in prose. Reading them side by side, they describe one artifact -- the closing block of a reply -- not six independent occasions. Naming it once, with a fixed name and a fixed order, is what makes it checkable: a bullet either appears in the right slot or it does not, which "a reply that made a commit should restate outstanding items" never quite was.

**"The Boildown" is deliberately not "Next Steps."** Everything in a reply is arguably "for" the person reading it, so a section literally titled that way names nothing -- and the phrase itself has an unrelated, friendlier reading that has nothing to do with a status report. "The Boildown" names what the section actually is: the reply reduced to what still needs a decision or an action, nothing else strained out. The first bullet under it is titled "Your next steps" for the same reason the whole section is not: within a section that already carries several kinds of information, the one bullet that is unambiguously the reader's own action items needs to say so on its own.

**Where the six inherited items came from, briefly, since their own files carry the full reasoning:**
- The plain-words self-contained ask, the recommendation riding alongside every decision, the repository-and-branch naming, and the "say explicitly when there's nothing" line all came from `next-steps-after-commit` and `asks-stand-alone`.
- The practice-suggestion bullet's four conditions are `merged-session-offers-a-practice`'s, unchanged.
- The spawned/other-session links and the three-things-always shape for a handoff (repository, exact paste text, way back) are `handoff-is-pasteable`'s.
- The one-unrelated-item cap on the Todo bullet, and its restriction to the closing reply only, are `closing-items-are-this-thread`'s.
- The three archive conditions, the ambiguous-case resolution (a minor suggestion or a question that doesn't change the outcome does not block an archive), and the fact that archiving buys back no compute, are `archive-a-finished-session`'s.

**What did not move here.** `session-spend-follows-the-task`'s guidance on picking a model for a spawned session's job is a different occasion -- it happens at session *creation*, not at the close of a reply -- and stays where it is, narrowed to just that half. Only its compact-offer clause and the mechanical requirement built for it moved into this practice.

## Why
Six practices asking for six related things, loaded through five different channels (a bare `gates: ["reply"]` registration, an occasion-index entry, a private individual set, a second private individual set, and a JSON declaration each of `reply_check.json` and `close_detect.json`), produced exactly what you would expect: some of it landed every time, some of it only when a session happened to recognize the occasion, and telling which was which meant reading five files. One section, one heading, one fixed order removes that question -- either the bullet the person is looking for is in its slot, or the practice was not followed, and there is no third case to puzzle over.

## Story
Raised by Morgan, 2026-09-15, opening the conversation that produced this file by naming the thing he already loved -- a closing "Next Steps" section -- and the thing wrong with it: *"it isn't consistent enough, (and I think it lives among various different Practices), so I'd like to clean it up and organize it."* He specified both shapes in full before any file was touched: the always-present three items, and the six more that a closing reply adds before its archive line, each with its own wording and its own reason for being there or not.

Two design questions came out of the discussion rather than his initial message. Asked whether renaming the heading away from "Next Steps" would collide with the mechanical gate that already required one matching that pattern, he chose to keep the rename and repoint the gate rather than keep the old wording -- *"No more 'Next steps' but instead just 'The Boildown'"* -- and, on the first bullet's own name, moved off his own suggestion of "For you" once he noticed the ambiguity himself: *"'for you' could mean anything, it could be a gift for you!"* -- landing on "Your next steps" instead.

Reading `next-steps-after-commit` in full surfaced content his own draft had not mentioned -- the recommendation that belongs beside every decision-ask, and the tangent-survival clause that keeps an unresolved item in view across turns. He confirmed folding both in. Checking which other practices already covered pieces of the design turned up two he had not named at all: `handoff-is-pasteable` and, discovered only while implementing rather than while discussing, `archive-a-finished-session` in his individual set, which already carried the fuller three-condition archive treatment that `next-steps-after-commit` had always deferred to. Both are folded in here for the same reason he gave for the rest: *"I want all of this to live in one place, in one practice ideally, universal."*

He counted the result as one practice added and six removed. The six actually deduplicated here are three universal (`next-steps-after-commit`, `merged-session-offers-a-practice`, `handoff-is-pasteable`) and three individual (`closing-items-are-this-thread`, `asks-stand-alone`, `archive-a-finished-session`) -- `archive-a-finished-session` standing in for `session-spend-follows-the-task`, which he had expected to lose entirely but which carries model-selection guidance unrelated to any reply's closing section; that half was kept alive rather than deleted, on the session's own judgment, and is recorded as its own dated line in that file's Story rather than silently dropped.

Authorized in full: *"Let's go - go merge, do it, go update."*

## Install
Enforced the same way `next-steps-after-commit` and `session-spend-follows-the-task` were: `reply_check.json` declares the required heading pattern (now matching "boildown" rather than "next step") and the two fixed sentence-pairs (archive, compact), and [tools/precedent_reply_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_reply_check.py) refuses a reply that lacks them via the Stop hook. `close_detect.json` declares this practice's slug and the archive-ready phrase for [tools/precedent_close_detect.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_close_detect.py), which still gates the practice-idea bullet on real evidence from the session's own transcript rather than on the occasion alone. Neither script needed changing -- only the JSON declarations moved, from the two practices this absorbs to this one.

What stays a matter of judgment, as it always was: whether an ask is genuinely self-contained, whether a recommendation is real rather than filler, whether a Todo is a good enough fit to mention, whether a moment is actually cheap to compact. No script can read a chat reply for those; the fixed shape only guarantees the section exists and is in order, which is what makes everything missing from it visible.

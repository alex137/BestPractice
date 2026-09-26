---
slug:        small-calls
title:       Decide small calls yourself; only stop for big ones
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a judgment call is needed to keep work moving"
gates:       []
index_clause: "make small calls yourself; note them; stop only for big ones"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-19"
approved_by: "pending PR review -- drafted 2026-09-19 by Morgan F, moved from the shared set precedent-team-working-style"
strength: decided
---
## Rule
Default to continuing, not asking. When a judgment call is needed to keep the work moving -- filling in a default, picking between two reasonable implementations, resolving an ambiguity that doesn't change the shape of what gets delivered -- make the call and note it, rather than stopping to ask first. Reserve stopping and asking for calls that are genuinely big: hard or costly to undo, change what gets delivered or to whom, spend real money, touch credentials or production, or are the kind of toss-up where two reasonable people would clearly land in different places. **Making a call is never authorization to write it into the repository.** Where `brainstorm-holds-commits` applies -- an exploratory thread, until the person authorizes the work -- keep making small calls and keep moving; just do not commit them. The reply carries them until there is a commit to carry them instead.

**A call the person has already made is not a call to make again.** Where authorization has already been given -- for this merge, this push, this scope -- proceed on it. Do not put it back for a second yes, and do not treat the size of the action as a reason to: sizing decides whether a call needed asking in the first place, and once it has been asked and answered there is no call left to size. Re-asking is not caution; it spends the exact thing asking is supposed to protect, which is the person's attention, and it spends it on a decision they have already paid for. Where the authorization is genuinely narrower than the action in front of you, say precisely what falls outside it -- never re-put the original question.

## Detail
A small or moderate call made this way still gets surfaced, just not as an interruption: note it in both the normal end-of-work reply that already lists files touched, and the commit message itself, under a "Judgment calls made:" heading. The chat reply is easy to miss once a thread scrolls on; the commit message is the one copy that survives into `git log` and the PR diff, where it stays visible for as long as the repo does. Skip the heading only when a commit truly made no judgment calls -- don't pad it with "none" noise on every commit, but never omit it when a call was actually made. **The surfacing obligation does not create a commit.** "Note it in the commit message" assumes a commit is already happening for some other reason; it never makes one the right thing to do. In a Brainstorm there is no commit yet, so the end-of-work reply carries the whole obligation on its own, and the commit-message half lands later, with the commit that eventually carries the work.

## Why
Most calls in day-to-day work (a wording choice, which of two valid layouts to use, a template's exact phrasing) are small enough to just make; stopping for each one trades a session's own judgment for round-trip latency on decisions that don't need a second opinion.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. No dated incident was recorded; the rule is a deliberate
calibration of a universal default, and that is what this Story records.

The universal default is to ask when genuinely unsure. This sharpens it
toward a specific risk tolerance: most calls in day-to-day work -- a wording
choice, which of two valid layouts to use, a template's exact phrasing --
are small enough to just make. The list of what still justifies stopping is
the substance: hard or costly to undo, changes what gets delivered or to
whom, spends real money, touches credentials or production, or is a toss-up
two reasonable people would clearly land differently on.

The part that keeps this from being a licence is the double recording, and
it has a real reason. A small call still gets surfaced, just not as an
interruption -- and it goes in both the end-of-work reply and the commit
message under its own heading. The chat reply is easy to miss once a thread
scrolls on; the commit message is the copy that survives into the log and
the diff, where somebody reviewing a merged pull request later can still see
what was decided on their behalf. The heading is skipped on a commit that
genuinely made no calls, rather than padded with "none" on every commit.

**Moved to `precedent-team-working-style` on 2026-09-09**, from `precedent-team-maintainers`, in the subject split recorded in BestPractice's own history (2026-09-09) -- its TODO.md has since moved that content into per-item files, so the old anchor no longer resolves. The rule governs how a session works alongside the person it is working with -- any work, any team -- and it was reachable only by repositories that declared the maintainers' set. Two of the three rules moved here are `tier: resident`, so they fire on every turn of every session: the reach lost while they sat behind a repo-mechanics set is the whole reason this one exists. The copy left behind is `status: deduplicated` and points here; nothing was deleted and the rule was never out of force (`spec/MOVING_PRACTICES.md`, land first, deduplicate second).


**Carried from `precedent-team-maintainers` on 2026-09-09**, hours after this
rule moved here: another session improved the copy left behind (PR #31 there,
"Say that making a small call is not itself a licence to commit it") without
knowing the rule had just changed sets. Nothing warned it -- the file it
edited is a `deduplicated` tombstone whose `in_force_at:` names this one, and
that pointer is readable but nothing reads it on the way past. The
improvement is carried here in full and the tombstone keeps none of it.
**This is the drift case `practice-consistency-across-team-repos` describes,
observed live rather than reconstructed**, and the day a rule moves is when
it is most likely to happen.

**2026-09-12 -- the second clause, and it cost two round trips to learn.** Two
sessions were each told, explicitly, that Morgan had authorized merging their
own pull request. Both finished the work, saw their gates green, and ended
their turn asking for the permission they had already been given: one replied
"merge it yourself or reply `go` and I'll merge it". Each of those rounds is a
full context load, and there were three across the two sessions before both
merges landed. Neither session was being careless -- a merge is exactly the
shape this rule calls big, hard to undo and changing what gets delivered, so
sizing the call said "stop and ask" and they did. The rule as written had
nothing to say about a call already answered, which is why the clause is now
in the Rule rather than left to inference.
## Install
No mechanical check: a commit either has a "Judgment calls made:" heading or doesn't, and that presence alone is trivially greppable -- but the actual rule is about which calls were correctly sized as small enough to just make versus which should have stopped and asked, and that sizing (hard/costly to undo, touches production, a real two-reasonable-people toss-up) is the judgment itself, not observable after the fact from the commit alone.

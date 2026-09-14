---
slug:        handoff-is-pasteable
title:       A handoff to another session is a repo name, a paste block, and a way back
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "asking the person to do something in another session, or pointing them at one"
index_clause: "any reply that sends them elsewhere ships the words: repo, copy block, way back"
gates:       ["reply"]
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-10"
approved_by: "Morgan; widened 2026-09-14, Morgan -- a reply that merely POINTS at
  another session owes the exact text too: \"whenever you tell me I should tell
  another session something, you must *ALWAYS* give me the exact text to use, in a
  way that I can just click the 'copy' button\""
strength:    decided
source_practice_number: null
---
## Rule
**First, before any of this: the question of whether the work belongs in
another session is asked before the work starts, not after — and the
repositories are checked first.** That is
[spawn-session](spawn-session.md)'s, and this rule begins where it ends.
**Where the harness can create the session itself, do that instead of
writing a paste block**: a link, rooted in the right repository and already
carrying the prompt, put near the top of the reply with a plain instruction
to click it. The three things below then describe the *seeded prompt*
rather than something the person retypes, and they are unchanged. **The
paste block is the fallback for when no such tool exists** — and falling
back is said out loud, never done silently.

**This fires on any reply that leaves the person with something to say to
another session — not only on a deliberate handoff.** *"Continue there if
you want them current"*, *"that one is the other window's to finish"*,
*"you may want to mention this over there"* are all covered. **An offer
counts, and a passing mention counts.** The test is not whether you framed
it as a handoff; it is whether they will have to say something somewhere
else as a result of reading your reply. If they will, **the words are yours
to write, not theirs to compose.**

**The text goes in a block of its own, theirs to copy.** Not a sentence of
prose they reword, not a clause inside a paragraph about something else. A
task named in prose is a task they skim past — and the one that survives
the skim gets relayed in their own approximate words, which is the same
paraphrase hop this rule exists to remove. **Separating the block is what
makes the task visible at all**, and that is load-bearing, not cosmetic.

When work has to happen in a session other than this one, the reply hands
over **three things, always, in this order** -- and a *seeded* prompt carries
[seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md)'s header
above all three, because nobody typed it:

1. **Which repository to open the session in**, by name. Not "the other
   repo", not "your practice set" — the name the person types or clicks.
2. **The exact text to paste**, as one block, ready to copy with nothing to
   fill in or edit. It has to stand alone: the other session cannot see this
   conversation.
3. **How to come back** — the message to paste *here* when it is done,
   written out the same way, saying either that it worked or what went
   wrong instead.

**The third one is the one that gets dropped, and it closes the loop.**
Without it, neither side knows what this session still needs to hear.

**When there is more than one destination, every block is keyed by its
repository name and by nothing else.** No ordinals, no "session #2", no
numbering that mirrors the order the person happened to paste things in
earlier. Their numbering and yours will not match, and the block itself
cannot say which one is right, because the session reading it has no view of
either.

**A version in a handoff carries its reason, or it does not appear.** Name
the repository and the branch — the lineage is always said out loud, and
dropping *that* is a worse failure than anything else here. But do not name
the commit, tag or release sitting on it: write *"take the current tip of
`<branch>`"* and let the other session resolve it at the moment it reads.
A handoff is read later than it is written, by a gap nobody controls, so a
hash pasted into one is stale by construction — and the session reading it
cannot tell whether you meant *this exact commit matters* or *this is what I
happened to be looking at*. Where the exact commit really is the point —
reproducing a bug against an older engine, or landing a diff somebody
actually reviewed — say which of those it is in the same sentence. That is
the only thing that separates a deliberate pin from a stale copy-paste.

## Detail
A handoff that describes the task in prose and leaves the person to compose
the prompt has moved the work, not delegated it.

Write the paste block for a reader with no context: name the branch, the
file, the command, the expected outcome. If the other session should report
a measurement back, say which numbers.

Keep the return message short — one line the person can paste without
editing, plus room for what actually happened. *"Done, pushed to
`<branch>`"* / *"Failed: <what it said>"* is enough shape.

If more than one thing has to happen over there, it is still one paste
block, not three replies.

**And a block for one repository never mentions another repository's
work.** Not as context, not as a courtesy summary. A session that is handed
someone else's items spends its turn proving the files do not exist —
grepping for a check it does not have, resolving a commit that is not in its
history — and reports back an inventory instead of doing anything. That is
the expensive failure, not the confusion: the misrouted block reads as a
plausible instruction, so a session obeys it until the filesystem refuses.

The mechanical form that survives this: one heading per destination, the
repository's full name in it, and the block under it self-contained. If two
blocks would share a paragraph, the paragraph belongs in both, written out
twice.

**A link does not excuse a thinner prompt.** A seeded session starts with
exactly the text you gave it and no way to ask you what you meant, so the
three things above are *more* load-bearing when the person never reads the
prompt at all — they click, and whatever was wrong in it plays out
unsupervised.

## Why
Sessions cannot see or message each other, so the person is the only
transport, and every hop through them is a hop where a task can be
paraphrased into something else. Prose instructions get retyped from
memory; a paste block does not.

This is the outbound half of
[findings-return-through-repo](findings-return-through-repo.md). That rule
says a finding travels by the repository rather than by the person; this one
says that when a person genuinely *is* the transport — because only they can
open a session somewhere else — the load they carry is a block of text and
not a task to reconstruct.

## Story
Asked for by Morgan on 2026-09-10, in his own words: instructions should
give *"the name of the repo* and the exact text to copy paste in*, and then
those instructions should always finish with, reminding me to return to the
original session with a message to copy-paste there confirming its success
or sharing other issues."*

The condition that keeps producing these handoffs is documented in this
repo's own gotchas: `add_repo` refuses a cross-owner attach — it did so
again in the session that wrote this rule, for this account's private
individual set — so work spanning two owners **has** to be split across
sessions, and a session rooted here simply cannot reach the other side.

**The multi-destination clause was added the same day, by the rule failing
on its first real use.** Three sessions were running, one per practice set.
Morgan had pasted their results back numbered #1, #2, #3; the reply answered
with three blocks numbered 1, 2, 3 whose repositories mapped to his #3, #2,
#1. Each block did name its repository correctly — the rule above was
followed — and each also carried a "(session #N)" cross-reference pointing
the other way. The block written for `precedent-individual` went to the
`precedent-team-repo-maintenance` session, which spent its turn establishing that
`check_commit_author.py`, `TODO.md` item 1, PR #60 and commit `8e0fc68` were
all absent, and answering: *"everything naming 'your work' belongs to another
session."* It was right. The repository name was in the heading and the
ordinal beat it, because an ordinal looks like an address and a heading looks
like a title.

**The version clause was added 2026-09-14, after this repo got it backwards
first.** A four-set engine rollout ended with one set a commit behind the
other three, and the session that noticed wrote a runbook rule telling future
rollouts to pin one commit across every repo so they land level. Morgan read
it and asked: *"but do we want to install that specific version we told it?
Why not install the most recent version?"* He was right, and that rollout is
the proof against the rule it produced: the lagging set was missing the reply
gate, and the only reason anyone looked was that it DIFFERED from the other
three — pinning would have put the same staleness in four repositories behind
a clean-looking table. The runbook was corrected the same day (#337), and he
generalized it from there, in his own words: *"when we spawn session or we
write wording to give another session -- we never tell it which particular one
to use, but force it to take the most recent version (unless you're
specifically instructed otherwise)."* **Strength:** decided (2026-09-14,
Morgan).

**The link clause was added 2026-09-11**, when Morgan asked for the check
that precedes this rule — *"first look to see if it should be in a different
session... then you should create a link to the new session, rooted in the
right repo, and already seeded with the prompt you want to give it"*. It
does not replace anything here; it changes what the person has to do with
the three things from *paste them* to *click once*, wherever the harness
allows that.

**Widened 2026-09-14, out of this repository failing the smaller case.** A
session here closed by reporting that the four practice sets sat pinned
behind BestPractice, and ended: *"That's Vendor update and precedent
migration's rollout to finish — I stood down rather than roll them forward.
Continue there if you want them current."* Every clause above was already in
force and **none of them fired**, because the session did not believe it was
handing anything over — it believed it was saying where things stood. What
reached Morgan was a task wearing a status line's clothes, with the message
he would have to compose left entirely to him.

He asked for the widening in his own words: *"whenever you tell me I should
tell another session something, you must *ALWAYS* give me the exact text to
use, in a way that I can just click the 'copy' button."* He gave three
reasons, and the order matters — it is easier for him; **"it makes it less
likely I miss the fact that I need to do this"**; and it makes it *"less
likely I say it to the other session in an unclear way."* The middle one
decided the shape. A convenience argument would have justified a tidier
sentence; a **visibility** argument only gets satisfied by a block that sits
apart from the prose, which is why that is written as a requirement rather
than a formatting preference.

**The pointer itself was not the lapse.** A session that finds a window
already working on something is supposed to send the person there rather
than spawn a second one beside it — that is the correct move, and other
rules in force ask for it. What was missing is everything after the
pointing: this rule now supplies it, so "go tell that window" and "here are
the words" stop being two separate decisions. **Strength:** decided
(2026-09-14, Morgan).

## Install
Nothing to configure. It fires when a reply asks the person to go elsewhere.

**Mechanically checked: no, and the attempt is recorded rather than left
unsaid.** What this rule governs is a chat reply or a seeded prompt, and
neither is a file in any repository, so there is nothing for
[precedent_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_check.py)
to read. The reply gate carries it instead: this practice is registered on
`reply`, so it prints at the moment a handoff is being written rather than
after it has been sent.

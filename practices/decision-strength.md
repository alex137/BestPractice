---
slug:        decision-strength
title:       A recorded approval says how firmly it was given
tier:        on-demand
severity:    default
applies_to:  ["practices/*.md", "local/practices/*.md", "decisions/*.md"]
occasion:    "recording that someone approved a practice or a decision, or citing their past approval back to them"
gates:       ["reply"]
index_clause: "record `decided` or `assented`; unmarked means unknown, never \"you decided this\""
checked_by:  "tools/precedent_check.py"
defines:     ["decided", "assented"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-09"
approved_by: "Morgan, 2026-09-09"
strength:    decided
---
## Rule
Every recorded approval says **how firmly it was given**.

- **`decided`** — they asked for it, chose it from options you laid out, or
  pushed back and the thing landed where it landed.
- **`assented`** — you proposed it and they did not object. Not argued.

**An unmarked approval means unknown, never `decided`.** A session citing one
says *"this is recorded from `<date>`"*, never *"you decided this"*.

## Detail
**Where it is written.** A `strength:` key in the frontmatter of a practice
file or a decision record, holding one of the two words and nothing else —
who approved it and when already live in `approved_by:` / `decided_by:`. For
an approval recorded in prose rather than frontmatter, an open item most
often, it is a line of its own inside the item, in
[open-item-disposition](open-item-disposition.md)'s grammar:

```
**Strength:** assented (2026-09-09, Morgan)
```

**The session writes it, and the session is the interested party.** You are
recording whether the person endorsed your own idea, which is the one
judgment you cannot be trusted to make generously. So: **write `decided`
only if you can quote them choosing it. A bare "ok" to your own proposal is
`assented`, written that way without asking them.** Unsure is `assented`.

**Read the words, not the fact of agreement.** Agreement arrives in language
that carries its own strength, and the mark follows the language:

| They said something like | Write |
|---|---|
| "let's try it", "as an experiment", "let's see how it goes", "ok", "sure", "fine" | `assented` |
| "I love it", "great", "yes, exactly", "do that" | `decided` |
| They picked one of the options you offered, or argued you down to this one | `decided` |
| Silence, or answering a different question | nothing — leave it unmarked |

The table is a guide to their register, not a lookup. **Provisional framing
is the tell for `assented`**: a test, a trial, a see-how-it-goes is
explicitly a thing they have not committed to. **Enthusiasm is the tell for
`decided`**, and so is any sign they did the choosing.

**What the mark then does**, or it is decoration:

- **`assented` is reopenable.** Any session may argue against it, or bring
  evidence that it is not working, without asking permission first.
- **`decided` is not relitigated.** A session that disagrees writes an open
  item under [todo-is-a-handoff](todo-is-a-handoff.md); it does not reopen the
  argument in the thread.
- **Unmarked is neither.** It may be cited as what the repository records,
  and not as what the person wanted.

**Nothing is backfilled.** An approval already recorded without a `strength:`
stays without one. Guessing which past "ok" was enthusiastic is exactly the
invention [no-invented-specifics](no-invented-specifics.md) forbids, and it
would be guessing about someone's state of mind months later. The field is
optional forever, in every source, so an unmarked catalogue keeps working
unchanged.

## Why
**A weak "ok" gets laundered into doctrine.** The whole design of this
repository is that a recorded thing binds: a session reads
`approved_by: Morgan` and treats the rule as settled, because that is what
the field is for. So a proposal the person merely tolerated acquires, in one
write, the same authority as one they fought for — and no later session will
ever reopen it, since nothing in the file says it was ever in doubt. The
record does not merely lose the strength of the decision; it **manufactures**
strength that was never there.

**The two errors do not cost the same.** A wrong `assented` costs one
correction — the person says "no, I meant that", and it is fixed in a word. A
wrong `decided` is invisible: nobody ever finds out, because the thing it
suppresses is a question nobody asks. That asymmetry is why unsure resolves
downward, and why absence cannot default to the strong value.

**It also protects the person from their own agreeableness.** Saying "ok, fine"
to move a conversation along is normal and costs nothing at the time; being
quoted six weeks later as the author of a rule you shrugged at is a different
thing entirely.

## Story
**Morgan, 2026-09-09**, on how this repository was recording his approvals:
*"Sometimes in our conversations, you refer to me having made a decision I
made. MANY times, that's only half-true: it's something you insist on, and I
say 'ok' or something similar, but it's more 'okay claude wants it, let's try
it, but I'm not really convinced, let's see.'"*

At that point `approved_by:` carried a name and a date and nothing else on
every practice in the catalogue — most of them his name — with no way to tell
one he had asked for from one he had not blocked. A handful of entries
happened to record the manner in free prose (*"asked for the phrase, chose
this one"*), which was a session being unusually careful rather than a
convention.

The cue table is his, from the same thread: *"if I say things imply it's a
test or experiment or 'let's see how it goes', all of those as equivalent to
the assented/weak-yes. While enthusiasm or 'I love it' or 'Great' are phrases
to indicate more decided."*

A scale of three or five levels was considered and rejected in the same
conversation: more resolution than the evidence supports, and an invitation
for a session to split hairs about someone's state of mind — which is the
invention this rule exists to stop.

## Install
The word the person can say to mark an approval weak at the moment they give
it is [weak-yes](weak-yes.md).

`python3 tools/precedent_check.py --only decision-strength` enforces the
grammar: a `strength:` that is present holds one of the two words, and the
file it sits in also records who approved it. It cannot check that the word
is the *right* one — no mechanism can read the conversation the approval
happened in — which is why the rule about quoting is written as a rule and
not as a gate.

[tools/precedent_land.py](../tools/precedent_land.py) takes `--strength` when
it writes a new practice file, so a practice landed through the pipeline
carries the mark from its first commit.

---
slug:              todo-2026-10-08-tell-morgan-what-others-did
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"This new practice you define is great, approved\" -- a daily summary of what others did, opening the first session after 07:00 Buenos Aires time"
decision_strength: decided
waiting_on:        "the change reaching main, where new sessions start"
noted:             2026-10-08
closed:            null
---
## What

Morgan learned about changes Alex made to Precedent only after something
confusing happened. [WHATS_NEW.md](../WHATS_NEW.md) does not cover this: it
picks the three or four most important things done by anyone each day, and
since most of the work is Morgan's, it rarely shows him what someone else
did.

## Proposed

- **When:** at session start in this repository, when the person was last
  told before 07:00 Buenos Aires time today and it is now after 07:00. Before
  07:00, nothing.
- **What:** every commit that reached `main`, `staging` or `pre-staging`
  since the person was last told, written by anyone else. Someone else
  merging the person's own pull request is not their work.
- **How it reads:** the first reply opens with a short What's New-style
  summary (about three bullets, each opening in bold, any rule change always
  named), then answers the question. With nothing from anyone else, one
  line saying so.
- **Then** the person is marked as told.
- **Built by replacing** the beta-branch watermark check (now
  retired), which already
  told a person once when someone else pushed, keyed per person, rather
  than writing a second tool beside it.
- **The practice belongs in the ladder set**, not the universal one, so
  it reaches only people who bring that set (Morgan, 2026-10-08).
- **Commits signed only "Claude"** are attributed by their `Claude-Session:`
  link: a session the person's account can open is theirs; one it cannot
  is someone else's, confirmed by who merged its pull request. Measured
  2026-10-08: `session_01B8YjZLeCQvJ6KZJbHmLovi` (2026-09-23) opens from
  Morgan's account; `session_01FsMPKqhoWLbSZ7hByp7MFF` (2026-10-02) and
  `session_01S2LLcA8ujJwyTYm5S19aKh` (2026-09-28 to 09-30) do not, and
  Alex merged both of their pull requests (#824, #762). A hook cannot open
  a session, so the hook marks these commits and the session checks the
  link before it writes the summary.

## How It Closes

Built and running: the first session of a day after 07:00 Buenos Aires
time opens with what others did since the last summary, and a second
session that day does not repeat it.

## Notes

**Decided 2026-10-08, Morgan: "This new practice you define is great,
approved" (strength: decided).**

Where the "last told" mark is kept: a branch kept only for it was
rejected ("weird and confusing and could be deleted"); the per-person file
the beta-branch check already kept was approved ("#2 -- this is great"), and
is now [tools/others_did_watermark.json](../tools/others_did_watermark.json).
Claude-signed commits: "great". The mechanism must be part of Precedent
itself, so future people in the repository get it (Morgan, 2026-10-08).

**Built 2026-10-08.** [tools/precedent_others_did.py](../tools/precedent_others_did.py)
replaces the beta-branch check and ships with the engine. Measured the same
day, the old check had found Alex's commits at session start and still
never told Morgan: its notice sat past the part of the start-up output a
session is shown, and it could save "told" only into a checkout idle on
staging, so it fell back to a per-container note. The new one leaves the
report for the reply gate's first prompt and commits the mark onto the
landing branch with git plumbing, never through the working tree. Tested by
`check_others_did_reports_others_once_a_day_and_never_touches_the_checkout`
in [tools/verify_harness.py](../tools/verify_harness.py), which fails when
the person's own Claude sessions are not left out.

**The mark moved off the landing branch the same day.** In a consuming
repository the first reply's status check committed "Others-did mark ...
[skip ci]" onto pre-staging, and the next Produce carried it to main. The
mark now lives on origin's `refs/precedent/others-did`, a ref outside
every branch, pushed and fetched by name, so it rides no Promote; the old
file on the landing branch is read once to carry marks over and never
written again. Tested by `check_others_did_mark_never_lands_on_a_branch`.

**The practice file `others-did.md` landed on the ladder set's
pre-staging** the same day, once Morgan approved push access to it. Until
the citation check reads more than this repository's own catalogue
(todo-2026-09-22-code-cites-practice-validates-against-the-wrong-catalogue),
the code here names it in plain words.

**Seen working, 2026-10-08 14:30 Buenos Aires time:** this session resumed
on a checkout carrying the change, and the first prompt opened with Alex's
57 commits since 2026-09-30; the mark landed on origin/pre-staging as its
own `[skip ci]` commit. Not yet seen: a second session the same day staying
quiet, which needs the change on `main`, where new sessions start.

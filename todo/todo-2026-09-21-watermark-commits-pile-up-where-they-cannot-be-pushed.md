---
slug:              todo-2026-09-21-watermark-commits-pile-up-where-they-cannot-be-pushed
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

**Every session working in this repository leaves an unpushable commit in
the individual source, and the session check goes red about it forever.**

[tools/precedent_beta_watermark_check.py](../tools/precedent_beta_watermark_check.py)
runs at session start, advances `beta-branch-watermark.json` in the
individual source, commits it there, and pushes. From a session rooted in
**this** repository that push cannot land: the git proxy refuses
`themorgan/precedent-individual` outright, because GitHub access here is
scoped to `alex137/BestPractice` and attachment refuses across owners. The
code handles the failure gracefully and says `retries next session` — but
the retry advances the watermark to a *new* tip, so it writes a *new*
commit. Nothing converges.

Measured on this container, 2026-09-21, during a very deep check: four
commits ahead of `origin/main` in `/root/precedent-individual`, three of
them watermark advances (`84b1b6033`, `76c52d3f9`, `08f3905ea`) and one a
merge. A fourth advance landed *during the run itself*.

## Why It Is More Than Clutter

[`precedent_session_check.py`](../tools/precedent_session_check.py)'s row **"each practice source clone is current
with its own origin"** reads those commits and fails. It is therefore red
on **every** session in this repository, from the first turn, for a reason
no session here can fix. [AGENTS.md](../AGENTS.md) tells every session to
run that check before trusting anything else in the file, and
[tools/precedent_gate.py](../tools/precedent_gate.py) prints the failing
guarantees at every gate moment specifically so a session that skipped that
paragraph is told anyway.

**A guarantee that is always red teaches sessions to skip the list.** That
is the same failure the repo already names for the upstream watermark
notice — `tools/upstream_watermark.json`'s own header says a notice that
cries wolf is "ignored by the second week" — and it is arriving here by a
different route. The other two rows in today's report (the duplicate source
clones, and this checkout falling behind a fast-moving branch) are real and
sit underneath it.

## The Options

1. **Do not commit a watermark that cannot be pushed.** Probe for push
   access first; with none, advance the watermark in the working tree only
   (or in a local note), leave no commit, and say so in the session-start
   line. Cross-session dedup already depends on the push landing, so a
   commit that cannot be pushed is buying nothing it does not already fail
   to buy. **This item's recommendation.**
2. **Keep the commit and teach the session check to recognise it** — a
   clone whose only unpushed commits are watermark advances to a repo this
   session cannot reach is not the failure that row exists to catch. Cost:
   the row stops catching a real divergence that happens to look like this
   one.
3. **Leave it, and have a session rooted in the individual source push the
   pile periodically.** Cost: the row is red between those sessions, which
   is most of the time, which is the present state.

## Not To Be Confused With

The 2026-09-21 identity work on the same function
(`_identity_args`, the nineteen watermark commits in three author states).
That fixed **who** the commit says wrote it. This is about whether the
commit should exist at all when the push behind it cannot land.

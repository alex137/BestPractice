---
slug:        durable-fix
title:       Fix it where the fix survives
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "when fixing anything -- a bug, a stale file, a broken environment"
index_clause: "prefer the fix that survives a fresh container; name a band-aid as one"
gates:       ["review", "reply"]
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan"
---
## Rule
**A fix is not done when the symptom goes away. It is done when the same
cause cannot produce it again.** Default to the durable fix, and reach for a
temporary one only when the durable one is genuinely unavailable right now.

The test is not how thorough the fix feels, it is **where the fix lives**.
Ranked by how long it survives:

1. **A committed file** — travels to every machine, every session, everyone.
2. **A generated artifact** committed alongside its generator.
3. **Machine or container state** — a `git config`, a path outside the repo,
   an environment variable. Dies with the container.
4. **This session's own memory** — gone the moment the session ends.

**Anything below the first rung is a band-aid**, however correct it is, and
the same problem will arrive again with nobody remembering why. Repairing
this container is not the same act as repairing the thing that keeps
producing broken containers.

**When only a temporary fix is available, say so in those words** — never
report it as the fix — and record the durable one as an open item naming
what it is blocked on. A workaround silently described as a solution is the
failure this exists to stop, because it spends the person's attention twice:
once now, and again when it recurs and nobody knows it was already
diagnosed.

## Detail
**Two questions separate the rungs, and both are cheap to ask.** *Does this
survive a fresh container?* and *does a person who was not here get it
without being told?* A fix that fails either is on rung 3 or below.

**The judgment call is real and this practice does not pretend otherwise.**
A durable fix can be genuinely out of reach — it needs someone else's
approval, a repository this session cannot push to, a decision nobody has
made. That is a legitimate reason to apply a band-aid, and it is exactly the
case where saying which one you applied matters most.

**What this is not.** It is not a licence to widen scope. The durable fix to
a one-line typo is committing the one-line typo, not building a linter for
it — [checkable-gets-checked](checkable-gets-checked.md) decides when a rule
earns a mechanical check, and this practice does not override it. Nor is it
[mistakes-become-rules](mistakes-become-rules.md), which fires after a
review finds a defect and asks what rule prevents the next one; this fires
at the moment of fixing anything at all, and asks only where the fix goes.

## Why
The cost of a band-aid is never paid at the time — it is paid later, by
someone who does not know the problem was already understood once. The
diagnosis is the expensive part, and a temporary fix throws it away while
looking like progress.

Recurrence is also invisible from inside any single session. A session that
repoints a path and moves on has genuinely solved its own problem; only the
person watching the same issue arrive for the third time can see that
nothing was fixed at all.

## Story
**Requested by Morgan, 2026-09-08, in those terms:** *"I prefer permanent
fixes ... I dislike band-aids in which hours later the same issue
reappears!"*

The occasion was the fix he was reading about. A session found that
`/root/precedent-individual` — the clone a user-level config names, and
therefore the one that actually resolves as the individual practice source —
was many commits stale, carrying a superseded engine and a file a rename had
orphaned. The session repointed that clone and reported the problem handled.

It was handled for that container and nowhere else. `~/.config/precedent/config.json`
is per-container and no repository can carry it, so the next container would
have started stale in exactly the same way — and the session's own reply had
said as much while still presenting the repoint as the fix. The durable fix
was one merge: land the branch on the source's own default branch, after
which every future container's session-start pull picks it up with nobody
doing anything. **Same problem, same session, two fixes an order of
magnitude apart in reach, and the cheaper one was reported first.**

The same shape had already been recorded twice in this repository's own
gotchas without being generalised: a timezone fix that lived in a settings
block nothing read, and a "resolved for this machine" note that was false in
every other container the moment it was written.

## Install
Before reporting anything fixed, ask **where the fix lives** and say so:

- **Committed?** Then say what landed and where.
- **Container or machine state?** Then call it temporary in the reply, and
  open an item for the durable fix naming its blocker.
- **Only in this session?** It is not a fix yet.

Then apply [verify-postcondition](verify-postcondition.md) to the durable
claim specifically: not *"the command succeeded"* but *"a fresh checkout
gets this"*.

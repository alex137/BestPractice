---
slug:              todo-2026-09-21-watermark-commits-pile-up-where-they-cannot-be-pushed
kind:              manual
domain:            engine
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "trigger moved to the alert; alert-path commit gated on a real push probe"
decision_strength: assented
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-22
---
## What

**Every session working in this repository leaves an unpushable commit in
the individual source, and the session check goes red about it forever.**

[tools/precedent_beta_watermark_check.py](../tools/precedent_beta_watermark_check.py)
runs at session start, advances `beta_branch_watermark.json` in the
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
   to buy. **This item's original recommendation; see What Remains below.**
2. **Keep the commit and teach the session check to recognise it** — a
   clone whose only unpushed commits are watermark advances to a repo this
   session cannot reach is not the failure that row exists to catch. Cost:
   the row stops catching a real divergence that happens to look like this
   one.
3. **Leave it, and have a session rooted in the individual source push the
   pile periodically.** Cost: the row is red between those sessions, which
   is most of the time, which is the present state.

## What Changed, 2026-09-22 — Most Of The Volume Was Never Options 1-3

**None of the three options above was the cheap fix, because the commit was
firing on the wrong condition entirely.** `_write_watermark` and
`_commit_and_push` sat *above* `check()`'s `if not others` return, so the
path that reports **nothing** advanced and committed exactly like the path
that reports somebody else's push. `others` — commits by someone other than
the declared identity — is the only thing this watermark exists to report,
and it was not consulted before the write.

Measured on `precedent-beta-v01` the same day: of the last 300 commits,
**293 are Morgan's own**, 5 a session's and 2 Alex's. So very nearly every
watermark commit ever written recorded the delivery of a notice that was
never delivered. In this container's own clone of the individual source: 32
watermark commits across four days, 13 on 2026-09-21 alone, 8 still
unpushed.

Both moved below the return
([tools/precedent_beta_watermark_check.py](../tools/precedent_beta_watermark_check.py),
"WHAT MOVES THE WATERMARK"). Nothing at all is written on the quiet path —
**not an uncommitted edit either**, which would leave that clone
permanently dirty and stop
[.claude/hooks/freshness-guard.sh](../.claude/hooks/freshness-guard.sh)
fast-forwarding it (`_dirty` there, `status --porcelain
--untracked-files=no`): a stuck checkout traded for a diverged one. A
watermark left behind by a quiet run costs nothing, because `others` is
computed over `seen..head` and a watermark that stayed put simply widens
the window the next run reads. Ten stated cases in
[tools/verify_harness.py](../tools/verify_harness.py) hold all of that,
including that one.

**The diagnosis above is confirmed, not superseded.** A 2026-09-22 relay
claimed the push failure was a property of `PRECEDENT_GIT_TOKEN` in the
environment rather than of repository scope, on the grounds that the
individual clone carries its own credential helper and bypasses the proxy.
Re-measured in this container: the helper *is* present and the token *is*
in the environment, and `git -C ~/precedent-individual push --dry-run
origin HEAD` still returns

```
remote: access denied by the git proxy: themorgan/precedent-individual is
not in this session's authorized repository set
fatal: ... The requested URL returned error: 403
```

The proxy sits in front of the helper. **Repository scope, as originally
written.**

## The Alert Path, Closed The Same Day

**Option 1, narrowed to the path that was left.** Morgan: *"Go update on the
watermark alert path too"* — a go-ahead to the recommendation above rather
than a case he argued, so `assented`.

The alert path now **probes before it writes**. `push --dry-run` is a real
authenticate-and-negotiate round trip that writes nothing, and it answers
the only question that matters: *would this land*. A clone that is
unauthenticated, diverged or behind all answer no, and all three mean the
same thing here. Where the answer is no, **nothing is written into the
individual source at all** — no file, no commit — so there is no commit to
reset later, which would have meant rewriting somebody else's repository.

**The cost named above is paid, and it is smaller than it looked.** What the
shared watermark buys once it cannot be pushed is exactly one thing: telling
the NEXT container. So the head just reported goes into a per-container note
in this repo's gitignored `.precedent/` instead. It stops the alert
repeating here — the thing a session actually notices — and claims nothing
about any other container. `check()` folds that note into the shared
watermark when it reads, so a container that has already reported up to X
does not report X again because the file it could not push still names
something older.

**The note is written only where git can be shown to ignore it.** An
untracked file in a source clone is precisely the dirt that skips that
clone's refresh and, since the container scanner landed, reads as work
existing nowhere else — so a repo that ignores nothing gets no note and a
session-start line saying plainly that the alert will repeat. Twelve stated
cases in [tools/verify_harness.py](../tools/verify_harness.py) hold all of
it, including the negative control that a reachable remote still commits and
pushes the shared watermark exactly as before.

**Not fixed by any of this:** the 8 commits already sitting in that clone.
They are watermark advances a future run will re-derive, so they can be
pushed or discarded; nothing here depends on which.

## Superseded The Same Day: The File Moved

**The watermark is no longer in the individual source at all.** Morgan,
2026-09-22, on the placement argument this whole item rests on: *"that is a
tidiness argument, not a privacy one"* — the file holds a public repository
name, a public branch, a public commit SHA and a date, and his own
`my-identity-is-not-private` practice covers his name appearing. Recorded
`assented`: a ruling on the premise, given when the session put the case to
him rather than argued for independently.

It is [tools/beta_branch_watermark.json](../tools/beta_branch_watermark.json)
now, beside `upstream_watermark.json`, **keyed by identity** — two people work
this branch, and one shared row would have each of them consuming the other's
notification. The value was carried across rather than reseeded at the head,
after running the tool's own authorship test over the gap: all 34 commits
between the migrated SHA and the head at migration time are the declared
identity's own, so no alert was suppressed by the move.

**What the move removed:** the cross-owner push wall, for this tool. What it
did not remove is the rule — `_can_push` stays, because a checkout that is
offline, behind or diverged still cannot push.

**What the move introduced, and what guards it.** The write now lands in the
very checkout the session is about to work in, which the old placement made
impossible by construction. `_is_quiet` refuses to write history into a
checkout that is ahead of origin or has anything staged, so a session-start
hook can never publish work in progress or author a half-made commit; and the
commit names its one path explicitly rather than trusting the index. Both are
held by stated cases in
[tools/verify_harness.py](../tools/verify_harness.py), 25 across the two
checks.

## Not To Be Confused With

The 2026-09-21 identity work on the same function
(`_identity_args`, the nineteen watermark commits in three author states).
That fixed **who** the commit says wrote it. This is about whether the
commit should exist at all when the push behind it cannot land.

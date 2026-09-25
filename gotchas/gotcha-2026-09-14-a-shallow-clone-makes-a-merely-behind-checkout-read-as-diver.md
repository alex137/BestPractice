---
slug:            gotcha-2026-09-14-a-shallow-clone-makes-a-merely-behind-checkout-read-as-diver
status:          live
noted:           2026-09-14
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A shallow clone counts every commit back to its graft point as LOCAL, so a checkout that is only BEHIND reads as diverged — and the freshness guard then refuses to update it, which is worse than either.

## Story

**A shallow clone counts every commit back to its graft point as LOCAL, so a
checkout that is only BEHIND reads as diverged — and the freshness guard then
refuses to update it, which is worse than either.** 2026-09-13: a session came
up on a checkout from the previous morning, 172 commits behind
`origin/precedent-beta-v01`. The guard's session-start pass fetched, computed
`behind=172` and `ahead=132`, concluded the two copies had gone their separate
ways, and warned instead of fast-forwarding — correct behaviour for a genuine
divergence, and there was none: after a deeper fetch, `merge-base` resolved to
`HEAD` itself and the local-only count was **zero**.

**What it cost is the part worth keeping.** The session wrote a whole reply
against a day-old tree — including rules that had been superseded that
morning — and the tell was not a git error but a defect the person had already
reported fixed: the fix (a `UserPromptSubmit` reply gate, landed at 14:12 that
day) simply did not exist in the files the session had. **A stale checkout
does not announce itself as staleness; it announces itself as your own work
being wrong.** The session only found out because an unrelated command tripped
the pre-write guard, which reported the same phantom divergence.

**Both of the obvious readings are wrong.** "Origin has moved and I should
re-push" is wrong — nothing local existed. "The guard is broken and should be
overridden" is wrong, and `git config precedent.freshness.override true`
switches off the stale-base check as well, which catches the most expensive
failure class in this file.

**Reproduce it in four commands**, which is how the fix was verified: clone
`--depth 1` over `file://` (a local path ignores `--depth`, gotcha
[g7](../record/GOTCHAS.md#g7)), add commits upstream, then `git fetch --depth=1 origin <branch>`.
The fetched tip lands as a **disjoint graft** with no path back to `HEAD`, so
`rev-list --count origin/<branch>..HEAD` counts everything the shallow clone
can see and calls it local. A plain `git fetch` on an already-shallow
repository can produce the same disjoint state, which is why the guard's own
fetch was not enough.

**The same commit added the quantity a person can actually judge.** Every
message reporting a checkout as behind now carries how much OLDER it is than
the remote tip — computed from the two tips' commit times, never from the
container's clock — and past a declared limit (`stale_checkout_hours` in
[precedent.json](https://github.com/alex137/BestPractice/blob/staging/precedent.json),
24) it is labelled `STALE` rather than merely behind. Morgan's reasoning for
wanting the time and not the count, 2026-09-13: over a missed hour *"chances
are not much changed"*, over a few days *"chances are a lot did, thus
increasing the risk of problems."*

**It fired again on 2026-09-14, and the cause is not unknown: the fix could
not run, because the fix was not in the tree that was running.** A session
opened here and the guard refused its first tool call with
`'precedent-beta-v01' has diverged (132 local, 162 remote)`. A bounded
`git fetch --depth=500` recounted it as **0 local and 212 behind**, and the
branch fast-forwarded cleanly — the same phantom this entry is about, on a
checkout that already had `_deepen_if_shallow` committed upstream.

**The obvious reading is that the fix fired and failed, and that reading is
wrong.** A second session checked the file afterwards, found
`_deepen_if_shallow` present, ran its fetch command by hand, got exit 0, and
concluded the guard had refused with a working fix installed — cause unknown.
That is true of the file and false of the run: by the time it looked, the
fast-forward had already replaced the file. `git show <the checked-out
commit>:.claude/hooks/freshness-guard.sh` settles it — **zero occurrences of
`_deepen_if_shallow`** in the copy that actually executed. The commit carrying
the fix is an ancestor of the current tip and **not** of the commit that was
checked out; it was one of the 212 the session did not have.

**The generalization is the part to keep: this hook runs from the working
tree, so it cannot repair a checkout too stale to contain it.** Every fix to
the freshness guard is delivered by the mechanism the fix is about, and the
case it most needs to handle — a badly stale checkout — is exactly the case
where the pre-fix copy is the one executing. **A session's own first fetch is
the only thing that closes that loop**, which is why the four commands under
"Reproduce it" stay worth running by hand when the counts look like a
divergence. Do not read "the fix is installed" as "the fix ran": ask what the
file looked like at the commit that was checked out, not at the one you are
standing on now.

**Measured the same day: all four private practice sets still carry a pre-fix
guard**, so a session rooted in any of them meets the original trap at full
force. Their vendored engines were refreshed to current that day and did
**not** bring the hook with them — the engine and the hooks go stale
independently ([g20](../record/GOTCHAS.md#g20)), and only the engine has a repair path.

**A third occurrence, 2026-09-15, finally answers "can this be prevented
outright" — and the answer is narrower than either fix so far assumed.**
This session's checkout came up shallow at a commit hundreds behind tip
(`b3040c6`), the freshness guard refused the first tool call with
`132 local, 479 remote`, and `git show b3040c6:.claude/hooks/session-start.sh`
and `...freshness-guard.sh` both came back with **zero** occurrences of the
unshallow/deepen code. Same trap, third time.

**Anthropic's own docs settle why, as of 2026-09-15**
([claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web),
[cloud-environments](https://code.claude.com/docs/en/cloud-environments)):
*"Cloud sessions start from a fresh clone"* is true of a session's **first**
turn only. Every later turn **resumes the same virtual machine (VM) and the
same checkout** —
nothing re-clones, and *"resuming an existing session never re-runs the
setup script."* SessionStart hooks do fire on every resume, but they run
**whatever copy of themselves is already checked out**. A session opened
before a hook fix merged, and kept alive since, can never pick that fix up
by resuming — the hook that would fetch the fix is the one artifact resuming
cannot refresh. This is not a bug in the hook; it is what "resume" means.

**So there is no committed file that closes this for a session already
running old code.** The only way in is from inside that session:
`git fetch --unshallow` (or a bounded `--deepen`), run once, by hand or by
the hook succeeding on that session's own first chance to run current code.
Once it succeeds, the repo is no longer shallow at all, so the class of bug
cannot recur for that checkout again — this is a one-time threshold per
already-open session, not a recurring one.

**What a committed fix *can* still do, and where today's copy falls short:**
it already self-heals every **brand-new** session correctly (a fresh clone
gets the current, fixed hook) — the gap is only in already-resumed sessions,
and in how loudly a failed attempt reports itself. Today's `session-start.sh`
gives the unshallow exactly one `timeout 90` try and, on failure, writes a
single `WARN` line to stderr that nothing re-surfaces later. And
`freshness-guard.sh`'s `_deepen_if_shallow` only fires from the
divergence-detection branch (`ahead != "0"`) — a checkout that is shallow but
merely *behind*, never mis-read as diverged, gets no second attempt from the
guard at all if SessionStart's own try failed. Hardening was tracked at
TODO.md's `shallow-clone-self-heal-hardening` item — closed 2026-09-15
(built and merged) and since pruned from TODO.md.

**A setup script does not close the gap either, and is worth ruling out
explicitly so nobody re-proposes it.** Setup scripts are the one mechanism
that lives outside the git tree (environment config, not a committed file),
which looks at first glance like the way around the bootstrapping trap. But
per the same docs, a setup script *"runs the first time you start a session
in an environment"* and is *"skipped when a cached environment exists"* —
the environment filesystem is cached for roughly a week, so a setup script
is **not** guaranteed to run on every new session either, let alone on a
resumed one. It would add a second unreliable path, not close the one gap
that matters.

**Built 2026-09-15**, same session, same day, on Morgan's go-ahead. Both
`.claude/hooks/session-start.sh`'s single `timeout 90` attempt and
`freshness-guard.sh`'s divergence-gated `_deepen_if_shallow` were the
narrower gaps this entry always said were still open — not the
bootstrapping trap itself, which stays exactly as described above.
`session-start.sh` now retries once more on failure and leaves a
`PRECEDENT_SHALLOW_UNRESOLVED` marker in the git dir when both attempts
fail; `freshness-guard.sh` now calls the deepen unconditionally, before
either of its two callers trusts an ahead/behind count, and surfaces a
loud `WARN` at session-start when that marker is still there. A fixture
built to reproduce this entry's exact shape turned up something worth
recording precisely because it is not what the "reads as diverged"
framing above predicts: on the git version this container runs, the
disjoint shallow graft read as **`0 behind, 0 ahead`**, not as a false
divergence — so the OLD code, gated on `ahead != "0"`, never even
attempted a deepen and silently treated a checkout that was five real
commits stale as fully up to date. The new unconditional call fixes
that shape too, not only the one this entry names. Full detail was in
TODO.md's `shallow-clone-self-heal-hardening` item, closed 2026-09-15 and
since pruned from TODO.md.

## Fix

**Fixed 2026-09-13** in both copies of
[.claude/hooks/freshness-guard.sh](https://github.com/alex137/BestPractice/blob/staging/.claude/hooks/freshness-guard.sh):
when the counts say diverged and the clone is shallow, `_deepen_if_shallow`
fetches `--deepen=500` (falling back to `--unshallow`, which some git policy
hooks refuse) and both counts are recomputed before anything is believed. The
same recount runs in the pre-write mode. Verified against a fixture that
reproduces the phantom: the old copy prints `has diverged ... NOT updating`
and leaves `HEAD` behind; the patched copy deepens, recounts 3 rather than 1,
and fast-forwards.

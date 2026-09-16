---
slug:            gotcha-2026-09-15-a-pretooluse-hook-s-once-per-session-sentinel-is-not-proof-a
status:          live
noted:           2026-09-15
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The symptom.

## Story

**The symptom.** `freshness-guard.sh`'s `pre-write` mode keys its
once-per-session sentinel on `session_id` alone when one resolves — which is
the normal case — so every tool call in one turn computes the identical
sentinel path. Two Bash calls sent in the same message, both their first
tool call of the session, both read `[ -f "$sentinel" ]` as false before
either has written it, and both fall through to `_pre_write_one`, which runs
`git fetch`/`--deepen` against the same `.git` directory at once.

**What was measured.** One of two parallel calls this session blocked with a
false "diverged" reading — `record/GOTCHAS.md#g37`'s shallow-clone artifact
— while its sibling call, touching the same checkout at the same instant,
read the correct counts and passed clean. Same session, same moment, two
different verdicts, because nothing serialized them. Confirmed with an
instrumented A/B fixture: two copies of the hook, one with the fix below and
one without, each with a marker-plus-`sleep 2` planted at the top of
`_pre_write_one`. Unpatched, both processes' markers, tagged with each
one's process ID (PID), appear interleaved in the shared log — genuine
concurrent execution touching git at once. Patched, only one PID's markers
ever appear; the other call exits clean off the sentinel the first one
wrote, without touching git itself.

**The fix, and the trap inside fixing it.** `flock` on an fd opened by
`exec`, re-checking the sentinel after acquiring it — a second caller that
had to wait finds the first one already finished and exits immediately
instead of repeating the same git work. Held on the fd rather than in a
subshell, so a later `_block`'s plain `exit 2` still releases it when the
process exits normally, with no unlock path to remember.

**The first attempt at this fix put `2>/dev/null` on the same line as
`exec 9>file`, and that is a distinct, separate trap from the race itself.**
`exec` with no command applies its redirections to the *current shell*,
permanently — not scoped to that one statement, and not undone when the
enclosing function returns. Proven in two lines: a function that runs
`exec 9>/tmp/x 2>/dev/null` internally, called, then followed by an
ordinary `echo ... >&2` *outside* the function and *after* it returned —
that line went silent too. Every later `echo ... >&2` for the rest of the
script's run went to `/dev/null` with it, which is exactly why two existing
`verify_harness.py` cases caught the bug: their expected stderr text came
back empty, not wrong. `flock`'s own `2>/dev/null` on its own line is a
normal external command's redirection and stays scoped to that command —
the fix was moving the suppression there, not removing it.

**The generalization worth keeping.** A `[ -f sentinel ] && exit 0` /
`: > sentinel` pair with no lock between the check and the write is a
check-then-act race the moment two processes can run it at once — true of
any "once per session" guard a PreToolUse hook keeps this way, not just
this one. And separately: never put a stderr redirect on a bare `exec`
line meant only to open a persistent fd — the redirect persists exactly as
much as the fd does.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

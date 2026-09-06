---
slug:        session-bootstrap
title:       Session bootstrap is code, not memory
tier:        on-demand
severity:    default
applies_to:  [".claude/**", "**/hooks/**", "**/bootstrap*", "templates/harness/**"]
occasion:    "setting up a new repo's session start"
gates:       []
index_clause: "setup lives in a session-start hook, not in memory"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 13
---
## Rule
Environment setup that sessions need (packages, dependencies,
submodule init) lives in a session-start hook — idempotent, fast when cached,
warning loudly on failure. Routine safe commands the agent runs constantly go
in a permissions allowlist so sessions don't stall on prompts. Where the
harness also supports a hook at the *other* end of a turn, the same
discipline applies in reverse: don't rely on the agent remembering to check
its own git hygiene before stopping — a stop hook that blocks on
uncommitted, untracked, or unpushed work makes that guarantee automatic
instead.

## Detail
**A hook that needs privileged access the session must acquire for itself
is a stronger case of this rule, not an exception to it — and the
strength of the case is easy to misjudge, corrected here 2026-09-06 after
getting it wrong once already.** Setup that only touches what's already
inside the container (installing a package, initializing a submodule) can
run once at session start and be done. A hook that clones a
**privately-scoped** source — an individual or team practice repo the
session has no standing access to — depends on something outside its own
control: the session's own git read access, granted per session by the
agent's own `add_repo` tool call, in the agent's own turn. A
`SessionStart` hook runs *entirely to completion* before that turn starts
— confirmed, not assumed: Claude Code's own docs for this hook state that
synchronous mode "guarantees dependencies are installed before your
session starts." That is a strict ordering, not a race with variable
odds, and the distinction matters completely: **a retry loop inside the
hook itself cannot help**, at any attempt count or delay, because on a
genuinely fresh session every attempt it could ever make still runs before
`add_repo` can have been called even once. A first version of this Detail
said otherwise — that the hook retrying "instead of trying once and
giving up" was half of a two-part fix. A follow-up testing session proved
that false by direct test, not merely unconvincing in theory; see Story.

**The one thing that actually closes the gap**: anything that later reads
what the hook was supposed to have written treats "the config is absent,
and this is a remote session" as "try the hook once more," not "nothing
is configured" —
[`tools/precedent_resolve.py`](../tools/precedent_resolve.py)'s own
`load_config()` does exactly this before concluding an individual source
doesn't exist. This works precisely because that re-invocation happens
*inside* the agent's own turn, always after `add_repo` has already run —
the one point in the whole sequence where the hook's own single attempt
actually has the access it needs. An instruction telling the agent to
call `add_repo` first is still required — the self-heal has nothing to
succeed *into* without real repo access — but it, and any retry loop
riding on it, cannot make an agent's own tool call precede a hook the
harness already started running. Only re-running the hook *after* that
tool call, not more times *before* it, closes the gap.

**Continuation, 2026-09-06: the same follow-up testing pass found the
matching gap on the *read* side.** The self-heal above means a source can
now resolve successfully in one session and still fail to resolve in a
later one (a genuinely unreachable individual repo, say) — and
`tools/precedent_show.py`, in a consumer repo where `practices/` is a
`tools/precedent_materialize.py`-produced snapshot, had no way to tell a
caller "resolved fresh, source confirmed live" from "reading old
materialized bytes, source status unknown this session." A clean Rule
printout read as proof the source was working, when it only proved a
past materialize run had once worked. Fixed the same way as the write
side — checking the state actually wanted, not the read that succeeded
([verify-postcondition](verify-postcondition.md)) — by having `precedent_show.py` probe
whether a materialized slug's own declared source is still reachable and
say so when it isn't, rather than silently reading whatever is on disk.
See `tools/precedent_show.py`'s own module docstring for the mechanism
and its deliberate limits (a cheap directory probe, not a full re-resolve
or a content-drift check).

## Why
The gotchas of [environment-gotchas](environment-gotchas.md), applied: writing the fix down is good;
having it apply itself is better. The hook is where "install the one package
whose absence cost two sessions" lives as code — and where "don't end a
session with unpushed work sitting in the tree" lives as code too, rather
than a habit the agent has to remember on its own each time.

## Story
Two independent adopters hit the identical failure within roughly a day of
each other, each running Claude Code Web against a repo that had wired an
individual source's `SessionStart` hook exactly as this practice's Install
section and INSTALL.md step 9 then recommended: a plain `AGENTS.md`
instruction telling the agent to call `add_repo` for the individual repo
"before running any bootstrap script." In both cases the hook ran, found
it had no read access yet, degraded on purpose rather than failing the
session, and never ran again. One session noticed only because a later
command failed with "unknown slug" and traced it back by hand; the other
noticed only because a stale freshness check looked clean with the
individual source silently absent — indistinguishable, from the outside,
from "this person genuinely has no individual set." Neither adopter's
`AGENTS.md`, hook, or install was wrong by its own stated rules; the rules
themselves assumed a `SessionStart` hook and an agent's own first tool
call could be ordered by instruction alone, and it took two independent
incidents to show that assumption false — an instruction cannot make a
tool call precede a hook the harness already started running. The first
fix landed in the engine
([`tools/precedent_source_bootstrap.py`](../tools/precedent_source_bootstrap.py)'s
retry, [`tools/precedent_resolve.py`](../tools/precedent_resolve.py)'s
lazy self-heal) rather than as a second, more emphatic instruction — this
practice's own Rule, applied to itself.

**Correction, 2026-09-06: half of that first fix was also wrong, and a
same-day mistake, not a separately-discovered one.** The retry half was
never tested against the actual mechanism it was meant to fix — every
verification at the time exercised `tools/precedent_source_bootstrap.py`
directly, against synthetic fixtures, never inside a real `SessionStart`
hook on a genuinely fresh Claude Code Web session. A follow-up testing
session ran that real test, twice, in `HavrutaBrainstorm`, and confirmed
directly: a `SessionStart` hook's execution window and the agent's own
first turn (and therefore its `add_repo` call) never overlap in time, so
retrying inside the hook is not a partial mitigation, it is inert — every
attempt, at any count or delay, runs before `add_repo` could possibly
have fired even once. It had also been quietly costing every cold session
real latency (up to ~12 seconds) for that zero benefit. The lazy
self-heal half was unaffected and independently confirmed to work — it
runs from inside the agent's own turn, after `add_repo`, which is exactly
where the access exists. Fixed by defaulting
[`tools/precedent_source_bootstrap.py`](../tools/precedent_source_bootstrap.py)
to a single attempt (retry stays available, opt-in, for an unrelated
genuine transient-network case — never claimed as a fix for this one) and
correcting every document, including this one, that had stated the retry
as a real, contributing half of the fix. The mistake this correction
encodes: a mechanism verified only against synthetic fixtures, never
against the real system whose timing model actually mattered, can pass
every planted-violation test in the harness and still be inert in
production — the harness proves the code does what the code says: it
cannot prove the premise about the outside world the code was written
against was true.

## Install
[templates/bootstrap.sh](../templates/bootstrap.sh) →
`tools/bootstrap.sh` (harness-neutral; all real setup lives here), wired in
per-harness via [templates/harness/](../templates/harness/README.md): a hook
that runs it automatically where the harness supports one (hard guarantee),
an instructions-file directive where it doesn't (soft guarantee), plus a
permission allowlist where the harness has that concept. Where the harness
also supports a blocking stop/teardown hook (Claude Code does; see
[templates/harness/claude-code/hooks/stop-git-check.sh](../templates/harness/claude-code/hooks/stop-git-check.sh)),
install that too — some managed environments already provide an equivalent
check outside the repo, but this makes the same guarantee travel with the
practice layer for the ones that don't.

**The bootstrap also checks upstream freshness — detection automated, the
take deliberate.** A dependent repo learns its practice layer is stale only
when someone remembers the periodic check-in, so the hook runs
`checkin.py fresh`: one clone-free `ls-remote` of the public upstream against
the manifest's recorded base, printing a single notice line only when
upstream has moved (silent when current or offline; never a gate).
*Applying* the update stays a deliberate step (INSTALL.md §2): installs are
adaptive, and unattended mirrors are the mechanism class that loses content —
the carry gate exists because even attended ones did.

**A privately-scoped source's own bootstrap hook is a separate template,
for the reason in Detail above.**
[`templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template`](../templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template) →
`.claude/hooks/precedent-individual-bootstrap.sh` in the *consuming*
project (never in the individual repo itself — a brand-new container has
no `$HOME` yet, so the hook that populates `$HOME` cannot live there),
instantiated by
`python3 tools/precedent_bootstrap_source.py --write-session-hook ...`
rather than hand-copied (see
[spec/BOOTSTRAP_NEW_SOURCES.md](../spec/BOOTSTRAP_NEW_SOURCES.md)). It
delegates to the vendored
[`tools/precedent_source_bootstrap.py`](../tools/precedent_source_bootstrap.py),
so an improvement to the mechanism — the self-heal `tools/precedent_resolve.py`
relies on, above — reaches every adopter through the ordinary
`process/upstream/` sync instead of a hand-edit repeated per repo.

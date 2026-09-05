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
is a stronger case of this rule, not an exception to it.** Setup that only
touches what's already inside the container (installing a package,
initializing a submodule) can run once at session start and be done. A
hook that clones a **privately-scoped** source — an individual or team
practice repo the session has no standing access to — depends on
something outside its own control: the session's own git read access,
granted per session by the agent's own `add_repo` tool call, in the
agent's own turn. A `SessionStart` hook runs *before* that turn starts, so
it can lose exactly this race even when everything else about it is
correct. Two things follow, both required, neither sufficient alone: (1)
the hook itself retries the clone with a bound
([`tools/precedent_source_bootstrap.py`](../tools/precedent_source_bootstrap.py)'s
default: 6 attempts, 2 seconds apart) instead of trying once and giving
up; (2) anything that later reads what the hook was supposed to have
written treats "the config is absent, and this is a remote session" as
"try the hook once more," not "nothing is configured" —
[`tools/precedent_resolve.py`](../tools/precedent_resolve.py)'s own
`load_config()` does exactly this before concluding an individual source
doesn't exist. An instruction telling the agent to call `add_repo` first
is still required — the retry has nothing to succeed *into* without real
repo access — but it cannot, on its own, make an agent's own tool call
precede a hook the harness already started running, and treating it as if
it could is the mistake this Detail exists to correct.

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
tool call precede a hook the harness already started running. The fix
landed in the engine
([`tools/precedent_source_bootstrap.py`](../tools/precedent_source_bootstrap.py)'s
retry, [`tools/precedent_resolve.py`](../tools/precedent_resolve.py)'s
lazy self-heal) rather than as a second, more emphatic instruction — this
practice's own Rule, applied to itself.

## Install
[templates/bootstrap.sh](templates/bootstrap.sh) →
`tools/bootstrap.sh` (harness-neutral; all real setup lives here), wired in
per-harness via [templates/harness/](templates/harness/README.md): a hook
that runs it automatically where the harness supports one (hard guarantee),
an instructions-file directive where it doesn't (soft guarantee), plus a
permission allowlist where the harness has that concept. Where the harness
also supports a blocking stop/teardown hook (Claude Code does; see
[templates/harness/claude-code/hooks/stop-git-check.sh](templates/harness/claude-code/hooks/stop-git-check.sh)),
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
delegates to the vendored, retry-capable
[`tools/precedent_source_bootstrap.py`](../tools/precedent_source_bootstrap.py),
so an improvement to the retry mechanism reaches every adopter through the
ordinary `process/upstream/` sync instead of a hand-edit repeated per
repo.

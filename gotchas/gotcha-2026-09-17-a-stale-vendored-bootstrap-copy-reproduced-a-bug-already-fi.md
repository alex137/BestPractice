---
slug:            gotcha-2026-09-17-a-stale-vendored-bootstrap-copy-reproduced-a-bug-already-fi
status:          live
noted:           2026-09-17
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

`commit-identity.sh` sets the GLOBAL git identity to a declared person
(`user.name`/`user.email`), and that identity silently reverts to the
container's own bot account (`Claude <noreply@anthropic.com>`) later in the
same still-running session — with no new commit, no new hook run, nothing
the session did to explain it. `core.hooksPath` (the global backstop)
stays set throughout; only the identity fields revert.

## Story

**Hit this 2026-09-17, in a session working across four `themorgan/precedent-*`
repos plus `BestPractice`.** Ran `bootstrap/commit-identity.sh` (a copy
vendored into `precedent-individual`) against each repo, confirmed
`git config --global user.email` read the declared person's address, moved
on. About 20 minutes and several tool calls later, a routine re-check found
`git config --global user.email` back to `noreply@anthropic.com` —
`~/.gitconfig` had been rewritten minutes earlier, keeping `core.hooksPath`
but resetting `user.name`/`user.email`. Local, per-repo git config was
unaffected throughout (verified in two separate repos, both times).

**The cause was already found and fixed the same morning, in a session this
one never saw.** `git log` on
[`templates/harness/claude-code/hooks/commit-identity.sh`](../templates/harness/claude-code/hooks/commit-identity.sh)
showed commit `ffcae05` ("commit-identity.sh: also turn off global
commit.gpgsign for a declared person"), authored 10:04 that morning: the
container signs commits with its own key by default
(`commit.gpgsign=true`), and something downstream keeps re-asserting the
bot identity to match that signature as long as `gpgsign` stays on — measured
in that earlier session as "three commits in a row... before anyone traced
why." The fix sets `commit.gpgsign=false` globally in the same
`_set_global_identity()` step that sets the name and address, under the
same "only for a declared identity" gate.

**That fix was already sitting in `templates/harness/claude-code/hooks/commit-identity.sh`
and in BestPractice's own `.claude/hooks/commit-identity.sh` — byte-identical,
no drift — hours before this session ran into the bug it fixes.** The copy
this session actually executed,
`precedent-individual/bootstrap/commit-identity.sh`, was a separate,
manually-distributed template copy that predated `ffcae05` (and the earlier
GH-auth fix, `1254499`) entirely — `grep gpgsign` on it matched nothing.
Nothing detected the gap: [`precedent_vendor_engine.py`](../tools/precedent_vendor_engine.py)'s own hash-tracking
only covers a hook a repo *wires* in its own `.claude/settings.json`
(`hook_files`/`hooks_sha256`), and `precedent-individual` doesn't wire
`commit-identity.sh` for itself — it just carries the file for other repos
to install from, so its own `refresh` never once compared it against the
template.

**Verified fixed, not assumed:** copied the current template over
`precedent-individual/bootstrap/commit-identity.sh`, re-ran it, confirmed
`commit.gpgsign` read `false` and the identity held across a subsequent
tool call in the same session (it had reverted within ~20 minutes the first
time; holding through at least one more call is evidence, not proof of
"never again" — the earlier bug also took a few commits to notice).

## Fix

**The mechanism itself is fixed** — `commit-identity.sh` turning off global
`commit.gpgsign` for a declared identity is what makes a global identity fix
durable at all; without it, a stop hook (or whatever else reads that flag)
keeps nudging the bot identity back for as long as `gpgsign` stays on.

**The separate, still-open gap is distribution, not the hook logic.** A
repo that carries a raw copy of a vendored hook script for OTHER repos to
install (as `precedent-individual/bootstrap/*.sh` does) is not covered by
[`precedent_vendor_engine.py`](../tools/precedent_vendor_engine.py)'s own drift detection unless it also *wires*
that hook for itself — so that copy can go stale indefinitely with nothing
ever reporting it. Before running a hook script from a `bootstrap/`-style
distribution copy, `diff` it against
[`templates/harness/claude-code/hooks/`](../templates/harness/claude-code/hooks/)
in a current BestPractice clone; don't assume a copy is current just
because it exists on disk.

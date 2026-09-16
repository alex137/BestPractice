---
slug:            gotcha-2026-09-14-the-session-start-identity-block-reaches-every-precedent-rep
status:          live
noted:           2026-09-14
severity:        null
retired:         null
retires_when:    null
---
## Symptom

Measured 2026-09-14

## Story

**Measured 2026-09-14**, during a four-set `Update Vendors` rollout — the
first work in months that commits to all four practice sets in one session,
which is the only reason anybody saw it.

Three team sets and BestPractice committed normally. The fourth, the
individual set, refused:

```
commit refused: it would be authored by the container's own agent account
(noreply@anthropic.com), not by a person.
  This is the GLOBAL backstop -- it fires in every repository, including one
  attached mid-session.
```

**The backstop was working.** It caught exactly what it exists to catch. What
was broken is the thing that should have made the backstop unnecessary.

`.claude/hooks/session-start.sh` applies the individual set's own
`bootstrap/commit-identity.sh` to each Precedent repo in the session. It found
them with:

```sh
for _repo in "$_here" "$_here"/../*/; do
```

— the primary repo, and its **siblings**. An individual set is not
necessarily either. `~/.config/precedent/config.json` records wherever it was
cloned, and on this container that is `$HOME/precedent-individual`, while the
primary repo and all three team clones sit under a different parent entirely.
So the glob covered four repositories and missed the fifth.

**The sharp part is that the block already had the path.** It resolves
`$_indiv` a dozen lines earlier — that is how it locates the script it runs —
and then never passes it to the loop. The one repository it reads the identity
*from* was the one repository it never applied that identity *to*.

**Why it stayed hidden for so long.** A normal session reads the individual
set and commits to the consuming repo; it has no reason to commit to the set
itself. Only a rollout that writes to every source at once puts a commit in
front of the gap.

**What it costs is the mechanism, not the commit.** Setting `user.email` by
hand fixes the one commit in front of you, and that hand-fix is precisely the
"instruction competing with a default, on every commit, forever" that
`commit-identity.sh`'s own header says never to rely on. Left alone it would
have come back on every future session, in the one repository where a
wrong-author commit is least likely to be noticed.

**Do not verify this by unsetting the set's LOCAL user.email and looking at
what git resolves.** That reads through to the global config, and the global
config is not a fixed background here: re-running `commit-identity.sh` by hand
during the investigation rewrote the container's global identity from the bot
account to the person, so the same unset-and-check that reproduced the bug
earlier in the session quietly stopped reproducing it later — and the new
guard row sat green against a state that could no longer go red. A control
that cannot fail is not a control (practice: `control-asserts-which-failure`,
`fixture-owns-its-state`). Set a bot `user.email` LOCALLY in the source clone
instead: that is the failure state, it owns its own state, and the row goes
red on it.

[tools/precedent_session_check.py](../tools/precedent_session_check.py) now carries that row — *every practice
source on this disk commits as a person too* — so the next occurrence is
reported rather than discovered by a refused commit.

**Swept for the same assumption, 2026-09-14**, because one mechanism getting
a repo list wrong is a bug and four mechanisms deriving the list four ways is
the actual problem. Four walk repositories on disk, and they did not agree:

- `tools/precedent_refresh_sources.py` already asks the resolver for the
  declared paths and adds siblings to them — its own docstring records
  learning this the hard way. Correct, untouched.
- `tools/precedent_session_check.py` scans `$HOME` **and** the parent, so it
  reached both. Correct, untouched.
- `tools/leak_gate.py`'s `local_clone_refs()` surveyed siblings only, and on
  this container that found four of the five clones on disk — **missing the
  private one**. Measured, not reasoned: it returned `alex137/BestPractice`
  and the three team sets, and no individual set. So the repository whose
  name most needs auto-blocklisting was the one the survey never saw. Fixed
  by unioning the resolver's declared paths in.
- `tools/verify_harness.py`'s commit-identity copy check globbed
  `precedent-team-*` beside this repo. It happens to find all three here;
  it is now the union with what `precedent.json` declares, so it will keep
  finding them when one moves.

**The rule the sweep suggests**, for anything that needs to know what
repositories are on this disk: ask the resolver what is DECLARED, then add
siblings — never siblings alone. The individual set is the one that breaks
it, every time, because it is the only one whose location is a person's own
config rather than the session's layout.

## Fix

**Fixed the same day** by naming `$_indiv` in the loop. Proved by A/B rather
than by reasoning: with the old loop, unsetting the set's local `user.name`
and `user.email` and re-running the hook left both unset; with `$_indiv` in
the list, the same sequence restored the person's declared name and address
from their individual set's `identity.json`. The
script is idempotent, so a set that IS a sibling being named twice costs
nothing.

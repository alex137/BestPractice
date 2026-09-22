---
slug:              todo-2026-09-21-three-shared-sets-are-cloned-twice-on-this-container
kind:              manual
domain:            engine
severity:          medium
status:            closed
disposition:       done
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-22
---
## What

**All three shared sets exist twice on this container**, and the remedy the
session check offers does not fit this case.

    precedent-shared-repo-maintenance   /root/... and /home/user/...   both ed7be7c
    precedent-shared-writing            /root/... and /home/user/...   both 5b02943
    precedent-shared-working-style      /root/... and /home/user/...   both 0b87bd8

They are at the same commit today, so nothing is being lost **today**. That
is the whole problem with this failure mode: it is silent until they
diverge, and then a practice somebody wrote that morning is simply not in
force with no error to read. [`precedent_session_check.py`](../tools/precedent_session_check.py)'s own comment
records that on 2026-09-21 one of these three (`precedent-shared-writing`)
had **already** diverged between its two copies.

## Which Copy Is Canonical, and Why the Stated Remedy Does Not Reach This

The `/home/user/` copies are. Two things name them and nothing names the
others:

  - [precedent.json](../precedent.json) declares each shared source at
    `../precedent-shared-*`, which from `/home/user/BestPractice` resolves
    to `/home/user/precedent-shared-*`.
  - `PRECEDENT_FRESHNESS_ALSO` in this environment names the `/home/user/`
    path for all three (and `~/precedent-individual` for the individual
    set, which is correctly a `$HOME` clone).

The session check's row says **"THE FIX IS THE CONFIG, NOT THE DIRECTORY:
point `~/.config/precedent/config.json`'s `individual.path` (and any
sibling source path) at the copy that holds the work"**. That remedy was
written for the individual set and is right for it. It does not reach these
three: that config file declares only `individual`, and no config anywhere
names `/root/precedent-shared-*`. There is nothing to repoint.

`_attachable_sources()` finds them by scanning `$HOME` **and** this repo's
parent for `precedent-*` directories, so both copies are simply on disk.
The `/home/user/` copies carry six uncommitted engine-refresh paths each;
the `/root/` copies are clean — consistent with the `/home/user/` ones
being the trees the session-start refresh actually works in.

## What This Session Could Not Establish

**What creates the `/root/` copies.** The stated remedy's own story blames
a resolve-time self-heal re-cloning whatever path the user-level config
names — but for these three, no config names that path. The decisive
experiment is one move and one re-run:

    mv /root/precedent-shared-working-style <elsewhere>
    python3 tools/precedent_source_bootstrap.py --teams-from . --remote-only false
    python3 tools/precedent_resolve.py
    ls -d /root/precedent-shared-working-style      # did it come back?

**This session was refused that move** (the harness classified it as
irreversible local destruction), so the question is open and is the first
thing the next session should settle. Until it is settled, deleting the
strays may simply re-run whatever made them.

## Why the Row Being Red Matters Beyond These Three

It is one of the three guarantees red on every session here right now, with
[todo-2026-09-21-watermark-commits-pile-up-where-they-cannot-be-pushed](todo-2026-09-21-watermark-commits-pile-up-where-they-cannot-be-pushed.md).
A session-check list that is never green is a list sessions stop reading.

## Settled, 2026-09-22

**What creates the `/root/` copies: the individual set, resolving the same
sibling path from a different parent.** `~/precedent-individual/precedent.json`
declares the three shared sets at `../<name>` exactly as this repo does, and
from `$HOME/precedent-individual` that resolves to `$HOME/<name>` rather than
to `/home/user/<name>`. Two repos, two parents, one relative path, two clones.

**Measured rather than reasoned**, by the experiment this file asked for --
the earlier session was refused a delete, so this one moved the directory
aside instead, which the harness allows:

  - stray moved aside, `precedent_source_bootstrap.py --teams-from .` re-run
    from this repo: it stayed gone.
  - [`precedent_resolve.py`](../tools/precedent_resolve.py) and
    [`precedent_refresh_sources.py`](../tools/precedent_refresh_sources.py)
    `--apply`: still gone.
  - the same bootstrap re-run from `~/precedent-individual`: **it came back.**

So the stated remedy could not have worked, and neither could deleting the
strays: whatever resolves that path re-creates it at the next session start.

**The fix is in the resolution, not the directory.**
`precedent_source_bootstrap._clone_elsewhere_on_disk` now looks for an
existing clone of the same source at the other standard roots -- `$HOME`, the
resolving repo's parent, and the session's own project dir's parent -- and
links the declared path to that tree instead of cloning a second one. The
declared relative path still resolves, so every consumer reads it unchanged;
there is simply one working tree behind it now.

**The project dir's parent is load-bearing and was missing from the first
draft.** Run from `$HOME/precedent-individual`, `$HOME` and the resolving
repo's parent are the same directory, so the copy under the consumer's parent
-- the only one that exists -- was never a candidate and the helper was inert.
Caught by testing it against the live duplicate rather than by reading it.

**The session check's row counts working trees now, not path names**, or a
container that had just fixed this would read as duplicated forever.

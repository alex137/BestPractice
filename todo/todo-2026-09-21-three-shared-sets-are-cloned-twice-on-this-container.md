---
slug:              todo-2026-09-21-three-shared-sets-are-cloned-twice-on-this-container
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
waiting_on:        "a decision on which copy is canonical, and permission to delete the other -- this session was refused the directory move it tried"
noted:             2026-09-21
closed:            null
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

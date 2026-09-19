---
slug:              todo-2026-09-18-no-stale-counts-undercounts-a-multi-source-catalogue
kind:              analysis
domain:            mechanism
severity:          notable
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "write access to precedent-team-writing -- refused from a session rooted here (cross-tier add)"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:              2026-09-18
closed:            null
---
## What

**`check_no_stale_counts.py` (vendored from `precedent-team-writing`, practice
`no-stale-counts`) reports a false positive against this repo's own
[AGENTS.md](../AGENTS.md), because it counts only `practices/` and this
repo's real total is spread across two declared sources.**

Raised because Morgan had seen repeated warnings about an "outdated practice
count" and asked to have the number removed. Traced instead of acted on
blind: the figure named, "181 practices," does not and never has appeared in
[TODO.md](../TODO.md) — confirmed by grepping the current tree and the
file's full `git log -p` history. The real, current instance of this shape
is one line over: [AGENTS.md](../AGENTS.md)'s generated resident-block
header currently reads `11 of 129 practices`.

**129 is correct, not stale.** `python3 tools/build_views.py --check` reports
[AGENTS.md](../AGENTS.md) byte-identical to a fresh regeneration.
`len(practices)` there is built from every source
[precedent.json](../precedent.json) resolves for this repo — the 124 active
files in this repo's own `practices/` (`universal`, `path: "."`) plus the 5
active files in `local/practices/` (`repo-local`, `path: "local"`, per
[precedent.json](../precedent.json)'s own `sources` list). 124 + 5 = 129.

**The check that flagged it only reads `ROOT/practices/`.**
`check_no_stale_counts.py`'s `find_violations()` counts `status: active`
files under `PRACTICES_DIR = ROOT / "practices"` alone — run against this
repo (`PRECEDENT_CHECK_ROOT=.`), it reports "currently holds 124" and flags
every "129 practices" sentence, including the live, correct one in
[AGENTS.md](../AGENTS.md), as stale. It has no notion of a repo-local
source declared alongside the universal one in `precedent.json`, so any
repo shaped like this one -- more than one source contributing to its own
count -- will read as permanently stale to this check, regardless of
whether `build_views.py`'s own number is right.

**Not this repo's file to fix.** `check_no_stale_counts.py` lives in
`precedent-team-writing`, a private team source; `add_repo` refuses the
cross-tier add in this direction (the same shape `precedent-team-writing`'s
own `TODO.md` items 4 and 6 already describe for the reverse direction), so
neither the fix nor a comment on that repo's own tracker is possible from a
session rooted here.

## How It Closes

`check_no_stale_counts.py`'s count either learns to resolve a repo's total
the way `build_views.py` does (sum every declared source's active count,
not just `ROOT/practices/`) or the check is scoped to skip a repo it
cannot fully resolve rather than report a false violation. Either fix
belongs in `precedent-team-writing`, from a session rooted there or with
push access to it. Until then, this item's own `## Notes` is where a
session that hits the same false positive again should look before
re-investigating from scratch.

## Notes

2026-09-18: filed after tracing Morgan's report of recurring "outdated
practice count" warnings. [TODO.md](../TODO.md) (root stub and generated
[todo/TODO.md](TODO.md)) carries no practice-count sentence at all, so the
reported "181 practices" figure was not reproducible against this repo in
either its current state or its tracked history. [AGENTS.md](../AGENTS.md)'s
`11 of 129 practices` is the live instance of the shape, and it is correct,
not stale -- the false positive is in the checking script, not the document
it flags. No edit made to AGENTS.md or TODO.md.

2026-09-19: reproduced independently, in a different consuming repo
(reported via a sibling session's write-up), with the same
off-by-the-engine-dev-scoped-set-size shape -- 175 actual vs. 159 computed
there, an off-by-16 matching the off-by-16 already described above. Confirms this is a structural bug in `no-stale-counts` itself
(double-stripping engine-dev-scoped practices whenever a multi-source
tracked list ends up with length > 1 for a reason unrelated to deferring),
not specific to this repo's shape. Still not this repo's file to fix --
`check_no_stale_counts.py` lives in `precedent-team-writing`, unreachable
from a session rooted here. No action taken beyond this note.

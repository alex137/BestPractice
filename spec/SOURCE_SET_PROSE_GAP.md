---
title:         Getting universal practice text into a practice-source set
kind:          brief
status:        open
opened:        2026-09-13
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       What it costs to close the gap where universal guidance text never reaches a session rooted in an individual or team practice set — three shapes, measured, with a recommendation.
---
# Getting universal practice text into a practice-source set

**A session rooted in a practice-source set reads that set's own catalogue
and nothing else.** Universal rules do not bind it, because it never sees
them. The open item is
[TODO.md's `universal-prose-does-not-reach-a-source-set`](../TODO.md#universal-prose-does-not-reach-a-source-set);
this brief costs the ways out of it. **Morgan approved the costing on
2026-09-13** (`assented` — he approved this session's recommendation to cost
both shapes rather than picking one blind). **Nothing here is decided.**

## What is actually missing, measured 2026-09-13

Each set's generated occasion index carries **only its own practices**:

| Set | Active practices | Occasion entries | `AGENTS.md` |
|---|---:|---:|---:|
| `precedent-individual` | 17 | 14 | 9,283 B |
| `precedent-team-repo-maintenance` | 16 | 16 | 12,000 B |
| `precedent-team-writing` | 17 | 17 | 5,264 B |
| `precedent-team-working-style` | 5 | 3 | 5,551 B |
| universal (this repo) | 105 | 94 | 105,768 B |

None of the four carries a single one of universal's 94 occasion entries.
The incident that produced this brief is in
[practices/seeded-prompt-names-its-origin.md](../practices/seeded-prompt-names-its-origin.md)'s
`## Story`: a session in the individual set spawned one here and could not
have read `seeded-prompt-names-its-origin`, `spawn-session` or
`handoff-is-pasteable`, none of which were in front of it.

**What has to arrive, whichever shape wins:** universal's resident block
(**898 tokens**) plus its occasion index (**3,114 tokens**) — **4,011 tokens**
per session. For comparison, the equivalent file in the other direction,
`.precedent/SESSION_PRACTICES.md`, has a declared ceiling of 4,000 tokens and
measures 2,887 here.

## Shape 1 — vendor the practice FILES into every set

Copy `practices/*.md` into each set and let its own `build_views.py` render
them.

- **Cost, counted:** 105 active files, **682,174 bytes**, into 4 sets —
  **420 tracked copies, ≈2.7 MB** of duplicated rule text living in four
  private git histories.
- **Drift is the real bill, and it is already being paid.** This session's own
  start reported **all four sets stale** against `origin/precedent-beta-v01`.
  Every edit to a universal practice would need a refresh-and-commit in four
  repositories on top of the one it landed in.
- **Already rejected once**, when `binds_publishers` was chosen over it, on
  exactly this ground: a second copy of rule text in every set.

**Verdict: no.** It buys the same 4,011 tokens the other shapes buy and adds
a duplication surface the project already decided against.

## Shape 2 — render universal into each set's committed loader block

Give each set a `precedent.json` naming universal as a source, and teach
`build_views.py` to render a resolved multi-source block into the set's
tracked `AGENTS.md`.

- **Cheaper than shape 1 on disk** — no practice files copied, only the
  rendered block.
- **Still commits the text**, so it still drifts: the block in four
  repositories has to be regenerated whenever universal moves, and a stale
  block is indistinguishable from a current one by reading it.
- **`build_views.py` renders one catalogue today.** The multi-source render
  is the change, and it is the same change the consumer side deliberately did
  **not** make — see
  [tools/precedent_session_practices.py](../tools/precedent_session_practices.py)'s
  header, "WHY THE COMMITTED VIEWS CANNOT SIMPLY BE MADE MULTI-SOURCE".

**Verdict: no.** It takes the drift of shape 1 and the code change of shape 3,
and buys nothing either of them does not.

## Shape 3 — the consumer mechanism, inverted (recommended)

Generate the universal block into an **untracked** `.precedent/SESSION_PRACTICES.md`
inside each set at session start. This is
[tools/precedent_session_practices.py](../tools/precedent_session_practices.py)
run in the other direction: it already writes the levels a repo's *tracked*
block leaves out, and in a source set the level left out is universal.

**What it needs, counted:**

1. **Two engine files added to `ENGINE_FILES` (source kind) in
   [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py):**
   `precedent_resolve.py` (1,004 lines) and `precedent_session_practices.py`
   (213 lines). **Both already exist and are proven in the consumer
   direction.** Their imports — `split_practices`, `build_views`,
   `precedent_identity` — are **already in the source list**, so nothing else
   travels.
2. **One code change, and it is small.** `precedent_session_practices.py`
   hardcodes `build_views.PRIVATE_LEVELS = ('team', 'individual')` as what to
   carry. That generalizes to *whatever levels the tracked block did not
   render*, which `build_views.py` already computes at
   [build_views.py:949-950](../tools/build_views.py).
3. **A `sources` entry in each set's `precedent.json`** naming universal.
4. **One `SessionStart` hook line per set**, alongside the two each already
   wires.

**Two things it does not need**, and both were checked rather than assumed:

- **No credential.** BestPractice is public, so a source set can clone it with
  nothing attached — recorded in
  [AGENTS.md's gotchas](../AGENTS.md#build-environment-gotchas--do-not-rediscover-these).
- **No leak exposure.** The direction that worried the consumer case was
  private text reaching a public commit. Here public text reaches a private,
  untracked file. The `.precedent/` path is already gitignored by the same
  convention.

**The one real wrinkle, found by measurement.** A relative `"path":
"../BestPractice"` does not resolve from every set: the individual source sits
at `$HOME/precedent-individual` — `/root` on this container — while the team
sets and this repository sit under `/home/user`. `precedent_resolve.py`
expands `~` for the *individual* entry (line 428) but a `sources` entry's path
is resolved relative to the repo. **Either the sources loader learns
`expanduser`/`expandvars`, or each set declares the universal path with `~`
and the loader is taught to expand it.** This is the same class as
`PRECEDENT_FRESHNESS_ALSO`'s "write the path as `~/name`, never spelled out",
and the same fix.

## Recommendation

**Shape 3.** It reuses machinery that is already written, already shipped and
already load-bearing in the other direction; it commits no copy of anything,
so there is nothing to drift; and the whole delta is two files added to a
vendoring list, one generalized constant, and a path expansion. Shapes 1 and 2
both cost more and buy the same 4,011 tokens.

**Not started.** Nobody has approved building it.

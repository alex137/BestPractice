---
title:         Self-healing the RENDER, not just the clone, for .precedent/SESSION_PRACTICES.md
kind:          brief
status:        closed
opened:        2026-09-18
closed:        2026-09-18
superseded_by: null
supersedes:    []
audience:      session
summary:       load_config()'s existing self-heal only clones a missing universal sibling; it never re-renders .precedent/SESSION_PRACTICES.md itself, so a session whose SessionStart hook never ran still sees a stale or absent catalogue even when the clone is fine. Three shapes costed; Shape C built and merged 2026-09-18 (commit ef5838b1, PR #452).
---
# Self-healing the RENDER, not just the clone, for .precedent/SESSION_PRACTICES.md

**A gotcha alone doesn't fix this** — it tells a session that already
suspects the problem what to run by hand; it does nothing for a session
that doesn't know to look. This brief costs the code fix, the same way
[SOURCE_SET_PROSE_GAP.md](SOURCE_SET_PROSE_GAP.md) costed the original
shape-3 design. It continues
[TODO.md's `universal-prose-does-not-reach-a-source-set`](../todo/todo-2026-09-13-universal-prose-does-not-reach-a-source-set.md),
whose reading half that brief shipped 2026-09-13 is exactly the mechanism
with the gap described here.

**Closed 2026-09-18.** Shape C (below) was built and merged the same day —
`_self_heal_stale_render()`, `tools/precedent_resolve.py` commit `ef5838b1`,
[PR #452](https://github.com/alex137/BestPractice/pull/452). The rest of
this brief is kept as written, including the shapes not chosen: it is the
record of why Shape C was picked over A and B, not a live decision anymore.
[`gotchas/gotcha-2026-09-18-editing-a-practice-pack-in-a-multi-repo-session-leaves-univ.md`](../gotchas/gotcha-2026-09-18-editing-a-practice-pack-in-a-multi-repo-session-leaves-univ.md),
the manual workaround this replaces, is retired accordingly.

## What already exists, read from the code rather than assumed

`tools/precedent_resolve.py`'s `_self_heal_universal_source()` (landed
2026-09-16, commit `7ec7047d`/`9c314a82`; already vendored into all four
practice-source sets via their 2026-09-17 engine refresh) is called from
`load_config()` — but only here:

```python
if level == 'universal' and not (entry_path / 'practices').is_dir():
    _self_heal_universal_source(repo_root)
```

**That guard is the whole gap.** It fires only when the sibling clone's
`practices/` directory does not exist at all, and when it fires it only runs
`precedent_source_bootstrap.py --sources-from` — which clones or refreshes
the sibling checkout, nothing else. It never calls
`precedent_session_practices.py`, the separate script that actually renders
`.precedent/SESSION_PRACTICES.md`. That render has exactly one caller in the
whole engine: the `SessionStart` hook
(`bootstrap/precedent-universal-catalogue.sh` / its `.claude/hooks/` copy).

**The 2026-09-18 incident this follows from had the clone present the whole
time.** All five repos (four packs plus BestPractice) were cloned together
before the session's first turn — that's what a team source needs to
resolve at all — so `entry_path / 'practices'` was always `True` and the
self-heal never fired, by design. What was missing was the render, a full
day stale, and nothing in `load_config()` reaches that case: a session can
call `precedent_check.py`, `precedent_paths.py`, or any other
`load_config()` caller all day, resolve the universal source correctly
every time, and never once trigger a refresh of the file `AGENTS.md`
actually tells it to read.
[`gotchas/gotcha-2026-09-18-editing-a-practice-pack-in-a-multi-repo-session-leaves-univ.md`](../gotchas/gotcha-2026-09-18-editing-a-practice-pack-in-a-multi-repo-session-leaves-univ.md)
is the manual workaround for exactly this, merged the same day as this brief.

## What has to be true for the fix to actually close it

1. **It has to fire on "stale or absent," not just "absent."** Mirroring the
   clone-heal's guard exactly (`if not sp.is_file(): render()`) reproduces
   the 2026-09-18 incident this brief follows from, one-for-one: the file
   existed, so an existence-only check would have stayed silent for the
   whole extra day.
2. **It has to stay cheap on the common path.** `load_config()` runs inside
   `precedent_check.py`, `precedent_paths.py`, `precedent_show.py`, and
   `precedent_gate.py` — several of which fire more than once per turn, some
   of them on every file edit. A render that is not cheap enough to pay
   unconditionally will need a cadence, not just a trigger.
3. **It has to know what "stale" means without trusting anything the
   possibly-unrun hook would have set.** There is no in-session signal for
   "did SessionStart actually fire" — `CLAUDE_PROJECT_DIR` being unset
   proves nothing either way, per `tools/precedent_session_check.py`'s own
   docstring, which tests every SessionStart guarantee by its effect on
   disk for exactly this reason. Staleness has to be judged from file
   state on disk, not from session state.

## Shapes

### Shape A — mirror the clone-heal exactly (existence-only)

`if not (repo_root / '.precedent' / 'SESSION_PRACTICES.md').is_file():
render()`, added right beside the existing clone-heal call.

- **Cost:** smallest possible diff — one guard, one call, same shape as the
  function it sits beside.
- **Does not close the incident that prompted this brief.** A day-old file
  still passes `is_file()`. This shape fixes the case where a session's
  first-ever `load_config()` call finds nothing at all (e.g., a brand-new
  clone with no prior session), and leaves every staleness case — which is
  what actually happened in the 2026-09-18 incident this brief follows
  from — exactly as open as this shape leaves it.

### Shape B — unconditional re-render on every `load_config()` call

Always run `precedent_session_practices.py --repo <repo_root>` before
returning, for any repo that declares a universal source.

- **Cost:** correctness-maximal — the file is never more than one
  `load_config()` call old. Unmeasured here: real per-call latency across
  the four packs, and how many `load_config()` calls a single turn actually
  makes — both need a number before this shape is a real option, not an
  estimate.
- **Likely too expensive as written.** `precedent_session_practices.py`
  resolves every declared source (team, individual, universal) and writes a
  file on every single call — paid by every `precedent_check.py`,
  `precedent_paths.py`, and `precedent_gate.py` invocation in a session,
  including ones a hook already handled minutes earlier. This is the shape
  to cost precisely before ruling out, not the one to assume in.

### Shape C — staleness threshold, judged from disk state (recommended)

Re-render when the file is absent, **or** older than a declared threshold —
reusing the pattern this codebase already has for exactly this judgment
call: `stale_checkout_hours` (`precedent.json`, `freshness-guard.sh`),
currently 24, set at the line Morgan himself drew for "how old is too old to
still call current." Same shape, same declared-not-hardcoded discipline
(practice `constants-are-risk-inputs`): a repo that wants a tighter or
looser number overrides the key it already has a home for.

- **Cost:** one file-mtime comparison per `load_config()` call (cheap — no
  subprocess, no network) plus the render itself only when the comparison
  trips. The 2026-09-18 incident (a day stale) trips at any threshold under
  24 hours; a session that ran its own hook minutes ago never re-renders at
  all.
- **What's actually unmeasured, and would need answering before building
  this:** whether a single threshold serves every pack alike, or whether a
  session mid-edit — expecting its own last few minutes of work to be
  reflected — wants a much shorter window than "was this checked out
  recently." `stale_checkout_hours` answers a different question (how old
  is this *checkout*) than the one here (how old is this *render*), so
  borrowing the constant is a starting guess, not a proof it's the right
  number for this use.

## Recommendation

**Shape C.** Shape A doesn't fix what actually happened, and Shape B's cost
is real but unquantified — building it without the latency and call-count
numbers first is exactly the kind of unmeasured constant
`constants-are-risk-inputs` warns against, just moved from a document into
code. Shape C reuses a pattern and a declared-constant discipline this
codebase already trusts, at a cost (one `stat()` per call) cheap enough not
to need its own measurement first.

## What building this actually touches

- `tools/precedent_resolve.py` — `load_config()`, beside the existing
  clone-heal call; a new narrowly-guarded helper alongside
  `_self_heal_universal_source()`, following the same shape (never raises,
  guarded on `precedent_session_practices.py` existing, so a source set
  whose engine predates this addition simply doesn't get it rather than
  failing).
- **Reaches every practice-source set only through their own next engine
  refresh** — same rollout path the original self-heal took to reach all
  four packs by 2026-09-17. This brief's fix does not retroactively apply
  itself; "Update Vendors" still has to run in each.
- Worth measuring alongside the build, not guessed beforehand: real
  `precedent_session_practices.py` latency in each of the four packs.
  Measured once, 2026-09-18, in `precedent-individual`: under a couple of
  seconds — but that was the cold-clone case (the sibling had just been
  synced), not the warm, already-current case Shape C's common path
  actually hits, so it is a starting number, not a proof either way. Also
  unmeasured: how many `load_config()` calls one ordinary editing turn
  makes.

## Next step

**Closed** — see the note under the title. What was genuinely left open at
build time and is worth someone picking up separately: the latency and
call-count measurements Shape B and C's own sections named as unmeasured
(only Shape C's was actually needed to build it, and that build used the
borrowed `stale_checkout_hours` constant as-is rather than deriving a
render-specific number first — a real remaining question, not a blocker),
and the vendor-refresh rollout to the four packs, which this brief's build
does not do on its own: "Update Vendors" still has to run in each before
they get this fix.

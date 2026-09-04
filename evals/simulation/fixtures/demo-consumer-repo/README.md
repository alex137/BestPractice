<!-- Last updated: 2026-09-04 by the phase-3 build session -->

# Demo consumer repo (phase-3 simulation fixture)

**This is a constructed fixture, not a real dependent repo.** Phase 3 of
[spec/SIMULATION_BRIEF.md](../../../../spec/SIMULATION_BRIEF.md) needs a
repo other than BestPractice itself to test multi-repo routing and source
precedence against, and no real dependent repo was attached to the session
that built it. It models a small fictional Flask-style service (`app/`,
`infra/`, a vendored copy of the practice engine under
`vendor/precedent-engine/`) that installs Precedent's universal catalogue
plus one repo-local override in [local/practices/](local/practices/).

**What's committed here:** this README, the repo-local override practice,
and a handful of stub files giving this fixture its own file-tree
conventions, distinct from BestPractice's own (so a scenario generated
against this fixture doesn't just reinvent BestPractice's paths).

**What's NOT committed:** `precedent.json`, `AGENTS.md`, `practices/`, and
`MANIFEST.json` are all written by
`python3 tools/practice_simulation.py build-fixture-repo` at run time — a
derived materialization of the universal catalogue plus this fixture's own
repo-local source, exactly as `tools/precedent_materialize.py` documents its
own output ("a DERIVED ARTIFACT that needs regenerating on every source
update"). Regenerate rather than editing anything that command would
overwrite.

## Why the override exists

[spec/ENFORCEMENT.md](../../../../spec/ENFORCEMENT.md) names this exact
case: `engine-plus-host-shims`'s universal `applies_to`
(`process/upstream/**`, `templates/harness/**`) names where *BestPractice*
keeps vendored/template text — in a host repo those are the host's own,
unrelated files. This fixture's repo-local override narrows the glob to
where *this fictional repo* actually vendors the engine
(`vendor/precedent-engine/**`), so a phase-3 batch can test something a
single-repo simulation never could: does a scenario touching this repo's
*own* vendored path correctly route to the repo-local version, and does a
scenario touching an unrelated `app/` file correctly NOT trigger the
universal version's now-irrelevant glob.

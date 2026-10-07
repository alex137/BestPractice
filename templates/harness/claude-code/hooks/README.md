# The Claude Code hook stubs

Every `*.sh` here is the same file: a stub that runs the real script of the
same name from the engine, `tools/<name>`. An install copies the stubs into
a repository's `.claude/hooks/`, and they never change again. Everything a
hook does is in its script in [tools/](../../../../tools/), which Update
Vendors keeps current with the rest of the engine.

**Why** (Morgan, 2026-10-07, strength: decided: "It should no longer ask").
Claude Code's auto mode holds any commit that changes a file under `.claude/`
until the person says yes. The hook scripts changed upstream on 27 days in
one month, and `settings.json` on 9, so nearly every Update Vendors stopped to
ask about a change nobody needed to judge. With the scripts in `tools/` and
the stubs fixed, a change to what a hook does arrives with the engine, under
the person's "Update Vendors", after BestPractice's own full check.

**A new hook** goes in [tools/hook_wiring.json](../../../../tools/hook_wiring.json),
never in `settings.json`: every repository has one fixed entry per event,
`precedent-hooks.sh <Event>`, which runs what that list names
([tools/precedent_hooks.py](../../../../tools/precedent_hooks.py)). The
practice is [new-hook-joins-the-registry](../../../../practices/new-hook-joins-the-registry.md).

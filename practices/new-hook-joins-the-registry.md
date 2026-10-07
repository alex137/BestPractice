---
slug:        new-hook-joins-the-registry
title:       A new hook goes on its kind's list, not just into a template
tier:        on-demand
severity:    default
scope:       engine-dev
applies_to:  ["templates/harness/claude-code/hooks/**", "templates/harness/claude-code/settings.json", "tools/precedent_bootstrap_source.py", "tools/precedent_vendor_engine.py", "tools/hook_wiring.json", "tools/*.sh"]
applies_to_why: "the places a hook's kind is declared -- the shipped stubs and scripts, the two kinds' templates, HOOK_WIRING and tools/hook_wiring.json -- are exactly these files; an edit anywhere else cannot add or drop a hook. Decided: 2026-09-25, with the practice; tools/hook_wiring.json and tools/*.sh joined 2026-10-07."
occasion:    "adding, renaming or dropping a hook script this repo ships, or changing which hooks a kind of repo runs"
gates:       ["merge"]
index_clause: "a new hook goes in tools/hook_wiring.json, never settings.json or HOOK_WIRING"
index_required: false
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-09-25"
approved_by: "Morgan, 2026-09-25; the tools/hook_wiring.json route, Morgan, 2026-10-07 (\"Let's implement #1. It should no longer ask. Act.\")"
strength:    decided
source_practice_number: null
---
## Rule
**A hook added from 2026-10-07 on goes in
[tools/hook_wiring.json](../tools/hook_wiring.json), never in
`.claude/settings.json` or `HOOK_WIRING`.** In the same commit that adds it:

1. **Put its script in `tools/`** and in `HOOK_SCRIPT_FILES` in
   [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py), so
   it ships with the engine to every kind.
2. **List it in `tools/hook_wiring.json` under every repo kind that should
   run it**, `consumer`, `source`, or both, with its event, its matcher and,
   if it needs more than a minute, its timeout. The list is by kind, never
   by repository. The fixed `precedent-hooks.sh` entry every repo already
   has runs it ([tools/precedent_hooks.py](../tools/precedent_hooks.py)).
3. **If no kind should get it, say why**: put it in `HOOKS_NO_KIND` with the
   reason.

**`HOOK_WIRING` is closed.** It holds the hooks wired straight into
settings.json before that date, plus the fixed entries, and the harness
refuses a new one there: an entry there is a change under `.claude/` in every
repository, which Claude Code's auto mode holds for the person's yes. Every
hook in `.claude/hooks/` is one permanent stub that runs `tools/<its name>`,
so changing what a hook does is a change in `tools/` only. `precedent_check.py
--only new-hook-joins-the-registry` refuses a tree where the lists disagree.

## Why
Since 2026-09-25 a refresh wires the hooks on a repo's kind list into
repos that are already installed, adding entries and never editing them, so a
hook added upstream reaches everyone. **That only works for a hook that is on
the list.** A script dropped into the hooks directory and wired into one
template by hand reaches fresh installs and nobody else. That is exactly the
bug the list was built to close, with one extra step.

## Story
Filed as
[todo-2026-09-21-a-new-hook-cannot-reach-an-installed-consumer.md](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-21-a-new-hook-cannot-reach-an-installed-consumer.md):
vendoring was gated on a repo's own wiring, and a refresh never wrote that
wiring, so a new hook could not reach an installed repo. `doc-lint-gate.sh`
turned this into a real loss, because Markdown lint left CI on 2026-09-21 when
the hook replaced it.

Morgan approved the per-kind lists on 2026-09-25 and asked in the same
message for *"a strong rule that new hooks are added to the appropriate place
and added to the list, too."* The sweep that built the lists found two hooks
the gap had already caught. `commit-identity-once.sh` had been wired in this
repo since 2026-09-22 but was in no template, so no consumer had it.
`seeded-prompt-gate.sh` was in the consumer template but not in any set.

2026-10-07: Morgan, after a consuming repository's Update Vendors asked him to
approve four hook files whose only change was where their wording lived:
"How do we stop it from asking this sort of question? I need it to be more
smooth to use and update", and then "It should no longer ask." The hook
scripts had changed on 27 days in the month before, and settings.json on 9.
Each hook became a permanent stub running its script from `tools/`, and new
hooks moved to `tools/hook_wiring.json`, run through one fixed settings entry
per event. strength: decided.

## Install
Nothing to install. It binds only this repository, the one that ships the
hooks, and the check is already registered in
[tools/precedent_check.py](../tools/precedent_check.py). It reports "not
applicable" in any repo without `templates/harness/claude-code/hooks/`.

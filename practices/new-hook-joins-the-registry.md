---
slug:        new-hook-joins-the-registry
title:       A new hook goes on its kind's list, not just into a template
tier:        on-demand
severity:    default
scope:       engine-dev
applies_to:  ["templates/harness/claude-code/hooks/**", "templates/harness/claude-code/settings.json", "tools/precedent_bootstrap_source.py", "tools/precedent_vendor_engine.py"]
occasion:    "adding, renaming or dropping a hook script this repo ships, or changing which hooks a kind of repo runs"
gates:       ["merge"]
index_clause: "a new hook joins its kind's HOOK_WIRING list and template, same commit"
index_required: false
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-25"
approved_by: "Morgan, 2026-09-25"
strength:    decided
source_practice_number: null
---
## Rule
**A hook script is not shipped until it is on a list.** In the same commit
that adds a `*.sh` under `templates/harness/claude-code/hooks/`:

1. **Put it on the list of every repo kind that should run it**:
   `HOOK_WIRING` in
   [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py),
   `consumer`, `source`, or both. The list is by kind, never by repository:
   a repo nobody has heard of gets its kind's hooks like any other.
2. **Wire it into that kind's template to match**: the consumer template
   [templates/harness/claude-code/settings.json](https://github.com/alex137/BestPractice/blob/staging/templates/harness/claude-code/settings.json)
   and, for a set, the settings payload and `SESSION_HOOKS` in
   [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py).
3. **If no kind should get it, say why**: put it in `HOOKS_NO_KIND` with the
   reason.

Renaming or dropping a hook changes the same three places. `precedent_check.py
--only new-hook-joins-the-registry` refuses a tree where they disagree.

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

## Install
Nothing to install. It binds only this repository, the one that ships the
hooks, and the check is already registered in
[tools/precedent_check.py](../tools/precedent_check.py). It reports "not
applicable" in any repo without `templates/harness/claude-code/hooks/`.

---
slug:              todo-2026-11-19-what-a-session-tasked-into-a-repository-must-be-told
kind:              decision
domain:            templates
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Alex's yes or no on adding a section to the consumer AGENTS.md template"
noted:             2026-11-19
closed:            null
---
## What

- [ ] **A repository has no place for what every session tasked into it must be told.** Reported 2026-11-19 by a consumer's main session: each of its worker briefs repeated the same setup notes by hand (which owner the shared set lives under, that the session's Python lacks the packages the repository's scripts import, to run one heavy job at a time, to save progress and resume), and a brief that left one out cost that worker about an hour. The proposal: a section of the consumer AGENTS.md template, "what a session tasked here must know", that a brief points to instead of restating. (needs: decision -- Alex)

## How It Closes

`status` becomes `done` when Alex has said yes or no, and a yes is on `main`.

## Notes

- The same report asked that the gotcha about messages reaching a busy session hours late cite a platform note once one exists. That gotcha is in pull request 1574, which is open, so there is nothing on `main` to edit yet (needs: pr -- https://github.com/alex137/BestPractice/pull/1574).
- The report also asked that session start install the Python packages a repository declares. It already does ([tools/precedent_python.py](../tools/precedent_python.py) reads `python.packages` in `precedent.json`), and that consumer declares four. A script there that imports a package outside those four is fixed by adding it to that list, in that repository.

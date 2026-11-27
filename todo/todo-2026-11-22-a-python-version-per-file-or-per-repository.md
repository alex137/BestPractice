---
slug:              todo-2026-11-22-a-python-version-per-file-or-per-repository
kind:              decision
domain:            engine
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "yes: keep one Python per repository, no per-file index (Alex, 2026-11-27, to the session's own pick: \"yes on your picks\")"
decision_strength: assented
waiting_on:        "Alex's yes or no on keeping one Python per repository rather than an index of a version per file"
noted:             2026-11-22
closed:            2026-11-27
---
## What

- [x] **Should each Python file carry its own declared version, or does one per repository stay?** Alex, 2026-11-22: "Shouldn't we have an index of which version of python every file is written to? So we now which version of python to run it with? We should have a shared python command that looks up the version and calls the specific python to execute that file. [...] We shoud also have a command that installs a new python file into this system. It recursively checks to make sure the import files all assume the same python version and updates all to the newest python version." (needs: decision -- Alex)

  Built the same day, on branch `claude/one-python-launcher-io-memo-key`: the shared command ([tools/py](../tools/py), which looks up the version for the file it is given and runs that interpreter, never another) and the upgrade ([tools/precedent_python.py](../tools/precedent_python.py) `upgrade X.Y`, which moves everything to a newer Python and keeps the move only if the full check passes under it).

  The per-file index waits on that decision (needs: decision -- Alex). The recursive check Alex describes, that every file a file imports assumes the same version, forces one version across the whole import graph. A heavy solve in a consumer reaches about twenty files, and the engine's own tools import each other freely, so in practice the graph is the repository, and one version per repository is what `precedent.json` already holds. A per-file index would be thousands of identical entries and a new place for two files to disagree. The session's pick: keep one per repository. Yes closes this as decided; no means building the index, with a check that every import edge agrees.

## How It Closes

`status` becomes `done` when Alex has said which, and either the index is built or this records the decision to keep one per repository.

## Notes

- 2026-11-27: Alex said yes to the session's pick. One Python per repository stays, declared in `precedent.json`; [tools/py](../tools/py) runs a file on it and `precedent_python.py upgrade` moves it.

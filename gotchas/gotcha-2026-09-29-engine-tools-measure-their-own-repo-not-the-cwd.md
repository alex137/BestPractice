---
slug:            gotcha-2026-09-29-engine-tools-measure-their-own-repo-not-the-cwd
status:          live
noted:           2026-09-29
severity:        major
retired:         null
retires_when:    null
---
## Symptom

You run an engine tool from inside one precedent-* repo, using another
repo's copy of the script, and it reports normal-looking figures. They are
the other repo's figures. Two runs from two different folders print the
same numbers.

## Story

During a "Reduction pass" on 2026-09-29 a session wanted the always-loaded
token figures for Morgan's individual set, and ran:

    cd ~/precedent-individual && python3 /home/user/BestPractice/tools/session_load_trend.py

[`session_load_trend.py`](../tools/session_load_trend.py) sets `ROOT = pathlib.Path(__file__).resolve().parent.parent`,
so it always measures the repo the script file lives in and ignores the
directory it is run from. Every engine tool finds its repo the same way,
from its own file, and that is on purpose: each precedent-* repo vendors
its own copy of the engine, and each copy reads its own repo.

What made it a trap is that nothing in the output said which repo was
measured. The header was "SESSION LOAD -- what every session pays before it
does any work", the `--since` ledger and `--json` were just as silent, and
the report looked exactly as a right-repo report would. The session told
Morgan his individual set was over a ceiling before it noticed. Its own copy
of the script, run properly, reported AGENTS.md at 1,573 of 1,800 and
`.precedent/SESSION_PRACTICES.md` at 4,872 of 5,200: under both.

## Fix

Run the copy that lives in the repo you mean:
`python3 tools/session_load_trend.py` from that repo's root, or the absolute
path to that repo's own `tools/`. Tools that take `--repo DIR`
([`precedent_show.py`](../tools/precedent_show.py), [`build_views.py`](../tools/build_views.py), [`precedent_paths.py`](../tools/precedent_paths.py),
[`precedent_gate.py`](../tools/precedent_gate.py)) can read another repo on purpose.

Since 2026-09-29, [`tools/precedent_which_repo.py`](../tools/precedent_which_repo.py) makes the mistake visible:
[`session_load_trend.py`](../tools/session_load_trend.py), [`precedent_check.py`](../tools/precedent_check.py), [`build_views.py`](../tools/build_views.py),
[`precedent_show.py`](../tools/precedent_show.py) and [`precedent_push_check.py`](../tools/precedent_push_check.py) print a
"WRONG REPO?" block on stderr when the current directory sits inside a
different git repo, naming both repos and the command that reads the one you
are in. [`session_load_trend.py`](../tools/session_load_trend.py) also names the measured repo in its text
header, its `--since` header and a `repo` field in `--json`. A repo whose
engine has not been refreshed since then still prints the old, silent
output.

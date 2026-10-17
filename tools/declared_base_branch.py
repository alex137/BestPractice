#!/usr/bin/env python3
"""The branch a repository declares its work is measured against: precedent.json's base_branch

declared_base_branch.py -- the one copy of the helper every branch resolver
in the engine reads first.

The branch a repository DECLARES its work is measured against, in its own
precedent.json `base_branch` -- not inferred from `origin/HEAD`. Those are
two different questions with usually the same answer, which is why asking
the wrong one survives so long. `origin/HEAD` answers "what does GitHub
show first"; callers mean "what lineage does this work belong to". They
diverge the moment a repository pins its work to a branch that is not its
configured default -- BestPractice did, with `precedent-beta-v01`, from
2026-09-03 -- and then every inference is quietly wrong with nothing
failing. Returns None when undeclared or unreadable, so callers fall back
to the old inference rather than breaking (practice: fail-gracefully).

ONE COPY, IMPORTED (2026-10-17). Until then nine tools carried their own
copy of this function, in three wordings; the very deep check of that day
found them. Each now imports this one, and precedent_check.py's
`declared-base-branch` check refuses a tool that defines its own again.
The one exception is tools/doc_html.py, which is meant to be dropped into a
host repository on its own and imports nothing from the engine, so it keeps
its copy (the check names it).

Standard library only, so any engine file can import it.
"""
import json
import pathlib


def declared_base_branch(root):
    """precedent.json's `base_branch` at `root`, stripped, or None."""
    try:
        v = json.loads((pathlib.Path(root) / 'precedent.json')
                       .read_text(encoding='utf-8')).get('base_branch')
        return v.strip() if isinstance(v, str) and v.strip() else None
    except Exception:                                        # noqa: BLE001
        return None

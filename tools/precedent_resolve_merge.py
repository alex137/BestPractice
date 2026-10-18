#!/usr/bin/env python3
"""Finishes a merge that stopped only on generated files: rebuilds them from the merged sources and stages them, the way a landing does

precedent_resolve_merge.py -- after `git merge` stops on conflicts, rebuild
every conflicted file a generator writes (MAP.md, GLOSSARY.md,
WHERE_THINGS_ARE.md, a gotcha or to-do index, a rendered page, a doc_sync
block, the harness times file) from the merged sources, and stage it.

    python3 tools/precedent_resolve_merge.py      then: git commit --no-edit

WHY (2026-10-18). A landing already does this inside its own worktree
(precedent_branches._resolve_by_regenerating), but a session's own
`git merge origin/staging` stopped on MAP.md and the session rebuilt it by
hand with build_views.py, which is practice shared-index-is-a-directory's
"a view conflict is rebuilt" done by hand every time. A git merge driver
that keeps one side was considered and rejected: it would also stop the
landing's merge from conflicting, so the landing would never rebuild, and a
stale view would land without a word. This runs the landing's own code, so
the two cannot drift.

Exit 0 when every conflict was rebuilt and staged (it does not commit:
the merge is the session's to finish); 1 when a conflict is hand-written or
a generator failed, naming the files, with the merge left as it was; 2 when
no merge is in progress.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if any(a in ('-h', '--help') for a in argv):
        print((__doc__ or '').strip())
        return 0
    top = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                         capture_output=True, text=True).stdout.strip()
    if not top or subprocess.run(
            ['git', '-C', top, 'rev-parse', '-q', '--verify', 'MERGE_HEAD'],
            capture_output=True).returncode != 0:
        print('precedent_resolve_merge: no merge is in progress here.')
        return 2
    sys.path.insert(0, str(HERE))
    import precedent_branches as pb
    done, files, why = pb._resolve_by_regenerating(top, say=print)
    if not done:
        print(f'precedent_resolve_merge: NOT resolved -- {why}: '
              f'{", ".join(files) or "(nothing conflicted)"}. Resolve those by '
              f'hand; the merge is as it was.')
        return 1
    print(f'precedent_resolve_merge: rebuilt and staged {", ".join(files)} from '
          f'the merged sources. Finish with: git commit --no-edit')
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Which repository an engine tool is reading, and a loud line when it is not
the one the person is standing in.

code-cites-practice: judgment-check-or-tool

THE TRAP. Every engine tool finds its repo from its own file:
`ROOT = pathlib.Path(__file__).resolve().parent.parent`, or the git toplevel
of the directory the file sits in. Never the current directory. That is the
design -- each precedent-* repo vendors its own copy of the engine, and its
own copy reads its own content -- but it means

    cd ~/precedent-individual && python3 ~/BestPractice/tools/session_load_trend.py

reports on BestPractice, and says nothing to suggest it. On 2026-09-29 a
"Reduction pass" session did exactly that, got BestPractice's figures back
under a header that named no repo at all, and told Morgan his individual set
was over a ceiling when it was not. It only noticed because two runs from two
folders printed the same numbers
(gotchas/gotcha-2026-09-29-engine-tools-measure-their-own-repo-not-the-cwd.md).

WHAT THIS DOES. It warns; it never changes what gets read. Two pieces:

- `describe(root)` -- the repo a tool is about to read, by folder name and
  origin URL, for a tool to print in its own header or --json.
- `warn_if_elsewhere(root, tool)` -- when the current directory sits inside a
  DIFFERENT git repository than `root`, one loud block on stderr naming both
  and the exact command that reads the one the person is in. Silent when the
  current directory is inside `root`'s repo, and silent when it is inside no
  repo at all (a session rooted above every clone runs tools by absolute path
  on purpose; there is nothing to disagree with).

Repos are compared by git toplevel, not by path, so the classic vendored
layout (engine at <repo>/process/upstream/tools/, run from <repo>) is the
same repo and stays quiet.

One helper rather than a check copied into each tool, because the trap is the
same everywhere (practice: judgment-check-or-tool, one mechanism, one tool).
Callers import it inside try/except: the engine is vendored a file at a time,
and a tree without this module keeps its old, quieter behaviour rather than
failing (practice: fail-gracefully).
"""
import os
import pathlib
import re
import subprocess
import sys

BANNER = '!' * 72


def git_toplevel(path):
    """-> the enclosing git repo's root as a resolved Path, or None."""
    try:
        r = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                           cwd=str(path), capture_output=True, text=True,
                           timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    top = r.stdout.strip()
    return pathlib.Path(top).resolve() if r.returncode == 0 and top else None


def origin_url(top):
    """-> origin's URL with any credentials removed, or None.

    A token in a remote URL (https://x-access-token:...@github.com/...) must
    never reach a report, so the userinfo part is dropped before anything
    else sees it.
    """
    if top is None:
        return None
    try:
        r = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                           cwd=str(top), capture_output=True, text=True,
                           timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    url = r.stdout.strip()
    if r.returncode != 0 or not url:
        return None
    url = re.sub(r'^([a-z][a-z0-9+.-]*://)[^/@]*@', r'\1', url)
    return url[:-4] if url.endswith('.git') else url


def describe(root):
    """-> {'name', 'path', 'origin'} for the repo a tool reads at `root`.

    `name` is the git toplevel's folder name (the root's own name when it is
    not in a repo); `path` is `root` itself; `origin` may be None.
    """
    root = pathlib.Path(root).resolve()
    top = git_toplevel(root)
    return {'name': (top or root).name, 'path': str(root),
            'origin': origin_url(top)}


def label(root):
    """-> 'BestPractice (https://github.com/alex137/BestPractice)', or the
    bare name when there is no origin."""
    d = describe(root)
    return f"{d['name']} ({d['origin']})" if d['origin'] else d['name']


def elsewhere_warning(root, tool, cwd=None, repo_flag=False):
    """-> the warning text, or None when there is nothing to warn about.

    `tool` is the script's filename (e.g. 'session_load_trend.py'); it is how
    the remedy finds the other repo's own copy. `repo_flag` says the tool
    takes `--repo DIR`, which is offered as the second way out.
    """
    here = git_toplevel(cwd or os.getcwd())
    mine = git_toplevel(root)
    if here is None or mine is None or here == mine:
        return None
    lines = [
        BANNER,
        f"!! WRONG REPO? {tool} is reading {label(root)} at {mine},",
        f"!! but you are standing in {label(here)} at {here}.",
        "!! Engine tools read the repo their own file lives in, never the "
        "current",
        "!! directory, so everything below describes the first one.",
    ]
    own = here / 'tools' / tool
    if own.is_file():
        lines.append(f"!! For the one you are in: python3 {own}")
    else:
        lines.append(f"!! {here.name} has no tools/{tool} of its own.")
    if repo_flag:
        lines.append(f"!! Or pass it explicitly: python3 "
                     f"{pathlib.Path(root) / 'tools' / tool} --repo {here}")
    lines.append(BANNER)
    return '\n'.join(lines)


def warn_if_elsewhere(root, tool, cwd=None, repo_flag=False, stream=None):
    """Print elsewhere_warning() to stderr (or `stream`) if there is one.
    -> True when it warned. Never raises."""
    try:
        text = elsewhere_warning(root, tool, cwd=cwd, repo_flag=repo_flag)
    except Exception:                                        # noqa: BLE001
        return False
    if text:
        out = stream or sys.stderr
        print(text, file=out)
        try:
            out.flush()
        except Exception:                                    # noqa: BLE001
            pass
        return True
    return False


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(
        description='Name the repo an engine tool here would read, and warn '
                    'when the current directory is a different one.')
    ap.add_argument('--tool', default='session_load_trend.py',
                    help='tool filename to name in the warning')
    a = ap.parse_args()
    here_root = pathlib.Path(__file__).resolve().parent.parent
    print(label(here_root))
    warn_if_elsewhere(here_root, a.tool)

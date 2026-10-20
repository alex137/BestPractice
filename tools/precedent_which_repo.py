#!/usr/bin/env python3
"""Names the repo an engine tool reads, and warns when it is run from inside a different one -- engine tools read their own file's repo, never the current directory

Which repository an engine tool is reading, and a loud line when it is not
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


def elsewhere_note(root, cwd=None):
    """-> ' -- this was <repo> at <path>, not <here> where you are standing',
    for a tool's last line, or '' when the two are one repo. Never raises.

    WHY (2026-10-20). The banner above prints first, and a long run scrolls
    it away: a session read only the summary of BestPractice's
    precedent_check.py run from another checkout and took BestPractice's
    pass for that checkout's."""
    try:
        here, mine = git_toplevel(cwd or os.getcwd()), git_toplevel(root)
        if here is None or mine is None or same_repo(here, mine):
            return ''
        return (f' -- WRONG REPO: this was {describe(root)["name"]} at {mine}, '
                f'not {here.name} where you are standing')
    except Exception:                                        # noqa: BLE001
        return ''


def _common_dir(top):
    """-> the resolved shared .git directory of `top`, so a linked worktree
    and its main checkout compare equal; None when it cannot be read."""
    try:
        r = subprocess.run(['git', 'rev-parse', '--git-common-dir'],
                           cwd=str(top), capture_output=True, text=True,
                           timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    out = r.stdout.strip()
    return (pathlib.Path(top) / out).resolve() if r.returncode == 0 and out else None


def same_repo(a, b):
    """True when toplevels `a` and `b` are one repository: the same
    checkout, worktrees of one clone, or two clones of one origin."""
    if a == b:
        return True
    ca, cb = _common_dir(a), _common_dir(b)
    if ca and ca == cb:
        return True
    oa, ob = origin_url(a), origin_url(b)
    return bool(oa) and oa.lower() == (ob or '').lower()


def elsewhere_refusal(root, tool, cwd=None, repo=None):
    """-> the text to print, exit nonzero and print NO pass/fail line with,
    or None to run as usual.

    WHY (2026-10-20). From precedent-shared-ladder, `python3 <BestPractice>/
    tools/precedent_check.py --only boildown-moments-named` printed the WRONG
    REPO banner, then "1 passed, 0 violated", exit 0 -- a pass about
    BestPractice. A session reading only the summary line, as a seed's "done
    when" invites, takes it as a pass for the repo it is in. A warning above
    a pass line is not enough; there must be no pass line.

    Refuses only when the current directory is in a DIFFERENT repository
    (not a worktree or another clone of this one) that has its own
    tools/<tool>: there is a right copy to run, and this one is plainly the
    wrong one. `repo` is the tool's --repo argument: naming this tool's own
    repository is the deliberate "yes, check that one", and runs."""
    mine = git_toplevel(root)
    if mine is None:
        return None
    if repo is not None:
        # Asked by name: run only when it names this tool's own repository.
        asked = git_toplevel(pathlib.Path(repo or '.').expanduser().resolve())
        if asked and same_repo(asked, mine):
            return None
        here = asked
        if here is None:
            return (f"{tool}: --repo {repo} is not inside a git repository. "
                    f"No pass or fail is reported.")
    else:
        here = git_toplevel(cwd or os.getcwd())
        if here is None or same_repo(here, mine):
            return None
        if not (here / 'tools' / tool).is_file():
            return None             # no right copy to send them to: warn only
    own = here / 'tools' / tool
    return '\n'.join([
        BANNER,
        f"!! WRONG REPO: {tool} checks {label(root)} at {mine}, the repo its",
        f"!! own file lives in -- not {label(here)} at {here}.",
        "!! So it reports no pass or fail here: a pass line would be about",
        "!! the other repository.",
        (f"!! To check that one:  python3 {own}" if own.is_file() else
         f"!! {here.name} has no tools/{tool} of its own to check it with."),
        f"!! To check {mine.name} on purpose:  python3 "
        f"{pathlib.Path(root) / 'tools' / tool} --repo {mine}",
        BANNER])


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

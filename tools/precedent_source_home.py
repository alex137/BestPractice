#!/usr/bin/env python3
"""Where a practice source's real tree lives, and whether two paths are one tree.

precedent_source_home.py -- the one answer to two questions every setup
and listing tool used to answer for itself.

WHERE A SOURCE LIVES (Morgan, 2026-10-19, strength: decided: "I like both
your solutions to #2 so do both", and a path that works for every AI tool
he uses, "we can define a different path for each one for example"). Each
harness has a declared home folder for practice-source checkouts, in
tools/source_homes.json (practice: registry-source-of-truth). The real
tree is cloned there; any other path a tool resolves for the same source
(`../<name>` beside a project, `~/<name>`, the attach tool's folder) is a
link pointing into it. Until this date the answer depended on who arrived
first: on one cloud container on 2026-10-18 /home/user/precedent-individual
and /home/user/precedent-shared-ladder were links into /root while
/root/precedent-shared-writing was a link into /home/user. One tree each,
but the clone lock is keyed by path, so two runs cloning the same set into
the two folders at once never waited on each other, and a tool recorded a
result under one path while the session worked in the other.

A tree already on disk somewhere else is never moved to the home folder:
moving a checkout can lose work (practice: repair-cannot-discard-work).
The home rule decides where the NEXT clone goes and which way a new link
points.

ONE TREE, MANY PATHS (practice: judgment-check-or-tool). tree_key() is the
identity: device and inode, which a link, its target and a case-insensitive
spelling all share, else the resolved path. Every tool that counts or
lists checkouts goes through one_per_tree() rather than a copy of that
logic: precedent_container_safe.checkouts, precedent_stale_branches,
precedent_session_check's one-clone row, precedent_source_bootstrap and
precedent_run_session_hooks.

    python3 tools/precedent_source_home.py              # harness and home folder
    python3 tools/precedent_source_home.py --path NAME  # where NAME's tree goes

Standard library only: it ships in the engine and runs before anything is
installed.
"""
import json
import os
import pathlib
import sys

REGISTRY = pathlib.Path(__file__).resolve().parent / 'source_homes.json'
HARNESS_ENV = 'PRECEDENT_HARNESS'
HOME_ENV = 'PRECEDENT_SOURCE_HOME'
DEFAULT = 'default'
# Read when the registry file is missing (an engine vendored without it):
# the layout every harness had before the registry, $HOME.
_FALLBACK = {DEFAULT: {'detect_env': [], 'home': '$HOME'}}


def registry(path=None):
    """-> {harness: entry}. Never raises: an unreadable file is the fallback."""
    try:
        data = json.loads(pathlib.Path(path or REGISTRY).read_text(encoding='utf-8'))
        found = data.get('harnesses')
        if isinstance(found, dict) and found:
            return found
    except (OSError, ValueError, AttributeError):
        pass
    return dict(_FALLBACK)


def harness(env=None, reg=None):
    """-> the harness this process runs under: PRECEDENT_HARNESS when it
    names one in the registry, else the first whose detect_env variable is
    set, else 'default'."""
    env = os.environ if env is None else env
    reg = registry() if reg is None else reg
    named = (env.get(HARNESS_ENV) or '').strip()
    if named in reg:
        return named
    for name, entry in reg.items():
        if any((env.get(v) or '').strip() for v in entry.get('detect_env') or ()):
            return name
    return DEFAULT


def attach_workspace(env=None):
    """-> where a repo-attach tool clones, or None: the parent of the
    session's project when the project is a repository, the project itself
    when it is not (a session rooted above its repos). The engine's own
    variable first, the provider's second (practice: vendor-neutral-by-default)."""
    env = os.environ if env is None else env
    for var in ('PRECEDENT_PROJECT_DIR', 'CLAUDE_PROJECT_DIR'):
        proj = (env.get(var) or '').strip()
        if proj:
            proj = pathlib.Path(proj)
            return proj.parent if (proj / '.git').exists() else proj
    return None


def _user_home(env):
    h = (env.get('HOME') or '').strip()
    return pathlib.Path(h) if h else pathlib.Path.home()


def home(env=None, reg=None):
    """-> the folder practice-source trees live in for this harness.
    PRECEDENT_SOURCE_HOME overrides the registry, for a machine laid out
    some other way. 'attach-workspace' falls back to $HOME where no project
    directory is known."""
    env = os.environ if env is None else env
    forced = (env.get(HOME_ENV) or '').strip()
    if forced:
        return pathlib.Path(forced).expanduser()
    reg = registry() if reg is None else reg
    entry = reg.get(harness(env, reg)) or reg.get(DEFAULT) or _FALLBACK[DEFAULT]
    where = entry.get('home') or '$HOME'
    web = entry.get('web_env')
    if web and (env.get(web) or '').strip().lower() == 'true':
        where = entry.get('web_home') or where
    if where == 'attach-workspace':
        return attach_workspace(env) or _user_home(env)
    if where == '$HOME':
        return _user_home(env)
    return pathlib.Path(os.path.expandvars(where)).expanduser()


def place(name, env=None, reg=None):
    """-> the path source `name`'s real tree belongs at."""
    return home(env, reg) / name


def tree_key(path):
    """-> a key equal for every path that reaches the same directory: its
    device and inode, else (a path that does not exist) the resolved path."""
    p = pathlib.Path(path)
    try:
        st = p.stat()
        return ('inode', st.st_dev, st.st_ino)
    except OSError:
        try:
            return ('path', str(p.resolve()))
        except (OSError, RuntimeError):
            return ('path', str(p))


def same_tree(a, b):
    return tree_key(a) == tree_key(b)


def one_per_tree(paths):
    """-> `paths` with every later path to a tree already listed dropped,
    order kept: the first spelling seen is the one shown."""
    seen, out = set(), []
    for p in paths:
        k = tree_key(p)
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def main(argv):
    if '--path' in argv:
        i = argv.index('--path')
        if i + 1 >= len(argv) or not argv[i + 1].strip():
            print('precedent_source_home: --path needs a source name', file=sys.stderr)
            return 2
        print(place(argv[i + 1]))
        return 0
    if '--help' in argv or '-h' in argv:
        print(__doc__.strip())
        return 0
    print(f'harness: {harness()}\nhome:    {home()}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

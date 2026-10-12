"""Records what each verify_harness check reaches: the code it runs and the files it reads (engine for harness_reach.py)

harness_reach_hook -- the recording half of change-scoped harness runs
(tools/harness_reach.py has the rest, and says why).

Loaded two ways:

  * in a harness process (start_parent): every check is wrapped with
    begin(name) / end(name), and what happens between them is that
    check's;
  * in every Python child a check starts (start_child, from the
    sitecustomize harness_reach.py puts on PYTHONPATH): the whole child
    belongs to the check named in HARNESS_REACH_CHECK.

What it records, for paths inside the repository only:

  c  a code unit run: (file, qualified name of the enclosing def), or
     '<module>' -- sys.monitoring PY_START on Python 3.12+, a profile
     hook before that;
  f  a file opened for reading (not a module the import system loads:
     the code units cover that);
  d  a directory listed;
  x  a path whose existence or type was tested (os.stat / os.lstat);
  o  a reason the check's reach could not be seen: a child that is not
     Python run in the repository, git run against the repository itself
     (its history is not a file), a Python child started without this
     hook, or a child that died before it wrote its record.

A file shutil copies out of the repository is not a read: code run
from the copy is recorded as the original's code, a Python read of the
copy as a read of the original, and a copy handed to (or sitting where
it runs) a program that is not Python or git as read. Clones of the
repository (git clone, git worktree add) are the repository.

A module's import can build state a LATER check uses without running
that code again (a registry read from disk at import time). So whatever
happens while a repository module's top level is running is also kept
against that module (`imports`), and a check that runs any of the
module's code inherits it when the ledger is built.

Kept out: .git/, __pycache__/, and this file and harness_reach.py.
"""
import atexit
import os
import sys

ROOT = None
PREFIX = None
OUT = None
_HARNESS = None                  # verify_harness.py: its top level is the run, not an import
_ME = set()
_CHILD_START = None
_state = {'check': None, 'busy': False, 'mode': None}
_checks = {}                     # check -> record
_imports = {}                    # module rel path -> record of its import
_rel_cache = {}
_MISS = object()
_BASES = []                      # the root under each spelling, then each clone
_ALIASES = []                    # clones of the repository: their files are its files
_COPIES = {}                     # a file copied out of the repository -> the file it copies
# git subcommands that ask only which commit or branch, or where: what a
# change edits does not move their answer.
_GIT_REFS_ONLY = {'rev-parse', 'symbolic-ref', 'config', 'remote', 'for-each-ref',
                  'ls-remote', 'rev-list', 'merge-base', 'fetch', 'branch',
                  'describe', 'var', 'version', 'help', 'check-ref-format',
                  # what is uncommitted, not what a commit holds: a run
                  # tests a clean checkout
                  'status'}
_SKIP = ('/.git/', '/__pycache__/')
_FLAGS_WITHOUT_SITE = ('-I', '-E', '-S', '-s')


def _new():
    return {'c': set(), 'f': set(), 'd': set(), 'x': set(), 'o': set()}


def _rel(path, cwd=None):
    """-> path relative to the repository, '' for the root itself, or
    None when it is outside the repository or not a path.

    By spelling, never by resolving symlinks: this runs on every open and
    every stat, and resolving each one made a recorded full sweep take
    half again as long (2026-10-12). The root is matched under both its
    given and its resolved spelling."""
    try:
        if isinstance(path, int):
            return None
        p = os.fsdecode(os.fspath(path))
    except Exception:
        return None
    if not p.startswith(os.sep):
        p = os.path.join(cwd or os.getcwd(), p)
    hit = _rel_cache.get(p, _MISS)
    if hit is not _MISS:
        return hit
    full = os.path.normpath(p)
    rel = _COPIES.get(full)
    if rel is None:
        for base in _BASES:
            if full == base:
                rel = ''
                break
            if full.startswith(base + os.sep):
                r = full[len(base) + 1:]
                rel = None if any(s in '/' + r + '/' for s in _SKIP) else r
                break
    _rel_cache[p] = rel
    return rel


def _norm(path):
    return os.path.normpath(os.path.abspath(path))


def _in_root(path, exact=False):
    """True when `path` is the repository itself (or, unless `exact`,
    inside it) -- not a clone of it."""
    n = _norm(path)
    for base in _BASES[:len(_BASES) - len(_ALIASES)]:
        if n == base or (not exact and n.startswith(base + os.sep)):
            return True
    return False


def _alias(path):
    """A clone of the repository at `path`: reads there are reads of the
    repository's own files, and so are the clone's clones."""
    full = os.path.normpath(os.path.abspath(path))
    if full in _ALIASES or full in _BASES:
        return
    _ALIASES.append(full)
    _BASES.append(full)
    _rel_cache.clear()
    os.environ['HARNESS_REACH_ALIASES'] = os.pathsep.join(_ALIASES)


def _copy_destination():
    """-> where shutil is copying the file being opened, when it is."""
    f = sys._getframe(2)
    for _ in range(6):
        if f is None:
            return None
        if f.f_code.co_name == 'copyfile' and f.f_code.co_filename.endswith('shutil.py'):
            dst = f.f_locals.get('dst')
            return os.fsdecode(dst) if dst is not None else None
        f = f.f_back
    return None


def _note_copy(dst, rel):
    """Append one copy to this process's list: a line each, never the
    whole list again (fixtures copy hundreds of files)."""
    was = _state['busy']
    _state['busy'] = True
    try:
        with open(_state['copies_file'], 'a') as f:
            f.write(f'{dst}\t{rel}\n')
    except Exception:
        pass
    finally:
        _state['busy'] = was


def _load_copies(path):
    try:
        with open(path) as f:
            for line in f:
                dst, _t, rel = line.rstrip('\n').partition('\t')
                if rel:
                    _COPIES[dst] = rel
    except OSError:
        pass


def _importing_module():
    """-> the repository module whose top level is running, innermost
    first, or None (verify_harness.py's own top level is the run)."""
    f = sys._getframe(2)
    while f is not None:
        co = f.f_code
        if co.co_name == '<module>':
            fn = co.co_filename
            if fn.startswith(PREFIX) and fn != _HARNESS and fn not in _ME:
                return fn[len(PREFIX):]
            if fn == _HARNESS:
                return None
        f = f.f_back
    return None


def _from_import_system():
    f = sys._getframe(2)
    while f is not None and f.f_code.co_filename in _ME:
        f = f.f_back
    if f is None:
        return True
    fn = f.f_code.co_filename
    return 'importlib' in fn or fn.startswith('<frozen ')


def _buckets():
    out = []
    if _state['mode'] == 'child':
        out.append(_checks.setdefault(_CHILD_CHECK, _new()))
    elif _state['check'] is not None:
        out.append(_checks.setdefault(_state['check'], _new()))
    mod = _importing_module() if _state['mode'] == 'parent' else None
    if mod is not None:
        out.append(_imports.setdefault(mod, _new()))
    return out


def _add(kind, item):
    if _state['busy']:
        return
    _state['busy'] = True
    try:
        for b in _buckets():
            b[kind].add(item)
    finally:
        _state['busy'] = False


# -- code ---------------------------------------------------------------
def _code_unit(code):
    fn = code.co_filename
    if fn in _ME or not os.path.isabs(fn):
        return None
    if fn.startswith(PREFIX):
        rel = fn[len(PREFIX):]
        if any(s in '/' + rel for s in _SKIP):
            return None
    elif _ALIASES:
        rel = _rel(fn)
        if not rel:
            return None
    else:
        return None
    return rel, getattr(code, 'co_qualname', code.co_name)


def _install_code_watch():
    mon = getattr(sys, 'monitoring', None)
    if mon is not None:
        tool = None
        for t in (mon.COVERAGE_ID, mon.PROFILER_ID, 3, 4):
            try:
                mon.use_tool_id(t, 'harness_reach')
                tool = t
                break
            except ValueError:
                continue
        if tool is not None:
            def on_start(code, offset):
                u = _code_unit(code)
                if u is not None:
                    _add('c', u)
                return mon.DISABLE
            mon.register_callback(tool, mon.events.PY_START, on_start)
            mon.set_events(tool, mon.events.PY_START)
            _state['restart'] = mon.restart_events
            return
    seen = set()

    def prof(frame, event, arg):
        if event == 'call':
            co = frame.f_code
            key = (_state['check'], co)
            if key not in seen:
                seen.add(key)
                u = _code_unit(co)
                if u is not None:
                    _add('c', u)
    import threading
    threading.setprofile(prof)
    sys.setprofile(prof)
    _state['restart'] = lambda: None


# -- reads and children ----------------------------------------------------
def _popen(exe, argv, cwd, env):
    if isinstance(argv, (list, tuple)):
        args = [os.fsdecode(a) if isinstance(a, (str, bytes, os.PathLike)) else str(a)
                for a in argv]
    else:
        args = [os.fsdecode(argv)]
    first = os.fsdecode(exe) if exe else (args[0].split()[0] if args and args[0] else '')
    prog = os.path.basename(first)
    wd = os.fsdecode(cwd) if cwd else os.getcwd()
    if prog.startswith('python') or os.path.realpath(first) == os.path.realpath(sys.executable):
        opts = []
        for a in args[1:]:
            if not a.startswith('-') or a in ('-c', '-m'):
                break
            opts.append(a)
        if any(a.startswith('-') and not a.startswith('--') and
               any(ch in a[1:] for ch in 'IESs') for a in opts):
            _add('o', f'a Python child started with {" ".join(opts)}, which skips this hook')
            return
        if env is not None:
            e = {os.fsdecode(k): os.fsdecode(v) for k, v in env.items()}
            hook = os.environ.get('HARNESS_REACH_SITE', '')
            if (e.get('HARNESS_REACH_CHECK') != os.environ.get('HARNESS_REACH_CHECK')
                    or hook not in e.get('PYTHONPATH', '').split(os.pathsep)):
                _add('o', 'a Python child started with its own environment, '
                          'without this hook')
        return
    if prog == 'git':
        target, i, sub = wd, 1, ''
        while i < len(args):
            a = args[i]
            if a == '-C' and i + 1 < len(args):
                target = os.path.join(target, args[i + 1])
                i += 2
            elif a in ('-c', '--git-dir', '--work-tree') and i + 1 < len(args):
                i += 2
            elif a.startswith('-'):
                i += 1
            else:
                sub = a
                break
        pos = [a for a in args[i + 1:] if not a.startswith('-')]
        if sub == 'clone' and pos:
            src = pos[0][len('file://'):] if pos[0].startswith('file://') else pos[0]
            if '://' not in src and ':' not in src.split('/')[0] and \
                    _rel(os.path.join(target, src)) is not None:
                dst = pos[1] if len(pos) > 1 else os.path.basename(src.rstrip('/'))
                _alias(os.path.join(target, dst))
            return
        if sub == 'init':
            if pos:
                target = os.path.join(target, pos[-1])
            if _rel(target) is not None and not _in_root(target, exact=True) \
                    and _norm(target) not in _ALIASES:
                return                   # a new repository inside a scratch area
        if sub == 'worktree' and pos[:1] == ['add'] and len(pos) > 1 and \
                _rel(target) is not None:
            _alias(os.path.join(target, pos[1]))
            return
        if sub in _GIT_REFS_ONLY:
            return
        if _in_root(target):
            if sub == 'ls-files':
                # the tracked list moves only when a file comes or goes:
                # a listing of every directory
                _add('d', '')
                return
            _add('o', f'git {sub} run against the repository itself')
        return
    if _in_root(wd):
        _add('o', f'{prog} run inside the repository')
        return
    for a in args[1:]:
        if ROOT in a:
            _add('o', f'{prog} given a path inside the repository')
            return
    # A program that is not Python reads what it likes: every copy it is
    # given, or that sits where it runs, counts as read.
    norm_wd = _norm(wd)
    given = {_norm(os.path.join(wd, a)) for a in args[1:] if a}
    for dst, rel in list(_COPIES.items()):
        if dst.startswith(norm_wd + os.sep) or dst in given:
            _add('f', rel)


def _audit(event, args):
    if _state['busy']:
        return
    if _state['mode'] == 'parent' and _state['check'] is None and \
            event not in ('open', 'os.listdir', 'os.scandir'):
        return
    try:
        if event == 'open':
            if not args or args[0] is None:
                return
            mode = args[1] if len(args) > 1 else 'r'
            flags = args[2] if len(args) > 2 else 0
            if isinstance(mode, str):
                if any(c in mode for c in 'wax') and '+' not in mode:
                    return
            elif isinstance(flags, int) and (flags & 3) == 1:
                return
            rel = _rel(args[0])
            # A relative name opened against a directory handle (rmtree,
            # os.walk's fd variants) carries no directory in the event, so
            # it resolved against the working directory: keep only what is
            # really a file there.
            if not rel or not os.path.isfile(PREFIX + rel):
                return
            if rel.endswith('.py') and _from_import_system():
                return
            # A copy is not a read: what runs or is read from the copy is,
            # and is recorded as the original when it happens.
            dst = _copy_destination()
            if dst is not None:
                real = os.path.normpath(os.path.abspath(dst))
                _COPIES[real] = rel
                _rel_cache.pop(dst, None)
                _rel_cache.pop(real, None)
                _note_copy(real, rel)
                return
            _add('f', rel)
        elif event in ('os.listdir', 'os.scandir'):
            rel = _rel(args[0] if args and args[0] is not None else '.')
            if rel is not None:
                _add('d', rel)
        elif event == 'subprocess.Popen':
            exe, argv, cwd, env = (list(args) + [None] * 4)[:4]
            _popen(exe, argv, cwd, env)
        elif event == 'os.system':
            cmd = os.fsdecode(args[0]) if args else ''
            if ROOT in cmd or _rel(os.getcwd()) is not None:
                _add('o', 'a shell command run against the repository')
    except Exception:
        pass


def _watch_stat(fn):
    def wrapped(path, *a, **k):
        if not _state['busy'] and not isinstance(path, int) and k.get('dir_fd') is None:
            _state['busy'] = True
            try:
                rel = _rel(path, None)
            except Exception:
                rel = None
            finally:
                _state['busy'] = False
            if rel:
                _add('x', rel)
        return fn(path, *a, **k)
    wrapped.__wrapped__ = fn
    return wrapped


def _common(root):
    global ROOT, PREFIX, _HARNESS
    _ALIASES.extend(a for a in os.environ.get('HARNESS_REACH_ALIASES', '').split(os.pathsep) if a)
    _BASES.extend(_ALIASES)
    # The copies the processes above this one made: one file each, read
    # at start. This process adds its own file, holding only what it
    # copies itself, for the children it starts (writing the whole list
    # again in every child filled a disk, 2026-10-12).
    inherited = [f for f in os.environ.get('HARNESS_REACH_COPIES_FILES', '').split(os.pathsep) if f]
    for f in inherited:
        _load_copies(f)
    own = os.path.join(os.environ.get('HARNESS_REACH_RECORD', OUT or '.'),
                       f'copies-{os.getpid()}.tsv')
    _state['copies_file'] = own
    os.environ['HARNESS_REACH_COPIES_FILES'] = os.pathsep.join(inherited + [own])
    ROOT = os.path.realpath(root)
    PREFIX = ROOT + os.sep
    _BASES[:] = [ROOT] + ([os.path.normpath(os.path.abspath(root))]
                          if os.path.normpath(os.path.abspath(root)) != ROOT else [])
    _HARNESS = os.path.join(ROOT, 'tools', 'verify_harness.py')
    here = os.path.realpath(__file__)
    _ME.update({here, os.path.join(os.path.dirname(here), 'harness_reach.py')})
    _install_code_watch()
    sys.addaudithook(_audit)
    os.stat = _watch_stat(os.stat)
    os.lstat = _watch_stat(os.lstat)


def _plain(rec):
    return {k: sorted(map(list, v)) if k == 'c' else sorted(v)
            for k, v in rec.items() if v}


# -- a harness process ----------------------------------------------------
def start_parent(root, out_dir):
    """Record every check this process runs, into out_dir."""
    global OUT
    OUT = out_dir
    _state['mode'] = 'parent'
    _common(root)
    atexit.register(_save_parent)


def begin(name):
    # Copies an earlier check made sit in its own scratch folders: a new
    # check starts with none, or every child would read them all at start.
    _COPIES.clear()
    del _BASES[len(_BASES) - len(_ALIASES):]
    _ALIASES.clear()
    os.environ.pop('HARNESS_REACH_ALIASES', None)
    _rel_cache.clear()
    try:
        open(_state['copies_file'], 'w').close()
    except (OSError, KeyError):
        pass
    _state['check'] = name
    os.environ['HARNESS_REACH_CHECK'] = name
    _checks.setdefault(name, _new())
    _state['restart']()


def end(name, ran=True):
    _state['check'] = None
    os.environ.pop('HARNESS_REACH_CHECK', None)
    if not ran:
        _checks.pop(name, None)


def _save_parent():
    try:
        data = {'checks': {n: _plain(r) for n, r in _checks.items()},
                'imports': {m: _plain(r) for m, r in _imports.items()}}
        import json
        with open(os.path.join(OUT, f'parent-{os.getpid()}.json'), 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f'harness_reach: could not save this process\'s record: {e}',
              file=sys.stderr)


# -- a child a check started ---------------------------------------------
_CHILD_CHECK = None


def start_child():
    """Record this whole process against HARNESS_REACH_CHECK."""
    global OUT, _CHILD_CHECK, _CHILD_START
    OUT = os.environ['HARNESS_REACH_RECORD']
    _CHILD_CHECK = os.environ['HARNESS_REACH_CHECK']
    _state['mode'] = 'child'
    _CHILD_START = os.path.join(OUT, f'child-{os.getpid()}-{id(_state)}.start')
    try:
        with open(_CHILD_START, 'w') as f:
            f.write(_CHILD_CHECK)
    except OSError:
        return
    _common(os.environ['HARNESS_REACH_ROOT'])
    atexit.register(_save_child)


def _save_child():
    try:
        rec = _checks.get(_CHILD_CHECK) or _new()
        # Tab-separated, not JSON: a child that never imports json would
        # otherwise pay for it at every start (2026-10-12).
        with open(_CHILD_START[:-len('.start')] + '.tsv', 'w') as f:
            for kind, items in rec.items():
                for item in items:
                    f.write(kind + '\t' + ('\t'.join(item) if kind == 'c' else item) + '\n')
            f.write('#done\n')
    except Exception:
        pass

"""Change-scoped harness runs: which verify_harness checks a change can reach, from a ledger a full run records

harness_reach -- run only the harness checks a change can reach.

WHY (Alex, 2026-10-12: "Can we have BestPractice checks limit themselves
to checking changes that were actually made?"). verify_harness.py ran all
of its checks (677 that day) on every pull request into main and again on
main, whatever the change. A change to two engine files reached about 83
of them; GitHub ran all 677, twice. precedent_check.py already scoped its
own checks to the files a change touched; the harness, the slow part,
did not.

HOW. A full run records, per check, what it reached (harness_reach_hook.py
says exactly what): the code units it ran -- each def, keyed by its
qualified name, plus each module's top level -- the files it read, the
directories it listed, the paths it tested, and anything it could not
see. That is the ledger. A later run diffs the tree it tests against the
commit the ledger was recorded at and runs:

  * every check whose recorded reach the diff touches: a changed def or
    module top level it ran (compared as parsed code, so a comment or a
    blank line reaches nothing), a file it read whose content changed, a
    path it tested or a directory it listed where a file came or went;
  * every check the ledger does not know (a new check);
  * every check whose reach could not be seen (o: git against the
    repository itself, a non-Python child run inside it, a child without
    the hook) -- always;

and the whole suite when the ledger is missing or unusable, when the
recording machinery itself changed, or when verify_harness.py's own top
level changed.

WHAT IT DOES NOT SEE, stated rather than hidden: state one check leaves
in a cache that a later check uses without running the code that filled
it (an import's top level is covered: harness_reach_hook keeps it against
the module); a check whose verdict depends on the clock, the network or
anything outside the repository. A whole-suite run catches either and
records a fresh ledger: started by hand, or when a change reaches more than
FULL_ABOVE of the suite -- which a ledger left to age makes happen on its
own, since each change is measured from the ledger's commit.

The ledger lives at the ref LEDGER_REF (a one-file commit), written by a
full run on main and read by every run that wants to be scoped.

    python3 tools/harness_reach.py select [--base REV]   # what this change reaches
    python3 tools/harness_reach.py record                # full run, writes the ledger
    python3 tools/harness_reach.py publish               # push the ledger to LEDGER_REF
"""
import ast
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER_REF = 'refs/precedent/harness-reach'
LEDGER_NAME = 'harness_reach.json'
LOCAL_LEDGER = ROOT / '.precedent' / LEDGER_NAME
# What a change to forces the whole suite: the recording and selection
# machinery, and the workflow that runs it.
MACHINERY = ('tools/harness_reach.py', 'tools/harness_reach_hook.py',
             '.github/workflows/deep-check.yml')
HARNESS = 'tools/verify_harness.py'
# Above this share of the suite, a scoped run saves too little to be worth
# a run that is not a full one.
FULL_ABOVE = 0.6
VERSION = 1

SITECUSTOMIZE = r'''
import os as _os
if _os.environ.get("HARNESS_REACH_CHECK") and _os.environ.get("HARNESS_REACH_RECORD"):
    try:
        import importlib.util as _u
        _s = _u.spec_from_file_location("_harness_reach_hook", _os.environ["HARNESS_REACH_HOOK"])
        _m = _u.module_from_spec(_s)
        _s.loader.exec_module(_m)
        _m.start_child()
    except Exception:
        pass
# chain to the sitecustomize this one shadows, if there is one
import sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _d in _sys.path:
    if _d and _os.path.abspath(_d) != _here and _os.path.isfile(_os.path.join(_d, "sitecustomize.py")):
        try:
            exec(compile(open(_os.path.join(_d, "sitecustomize.py")).read(),
                         _os.path.join(_d, "sitecustomize.py"), "exec"), {"__name__": "sitecustomize"})
        except Exception:
            pass
        break
'''


def _git(*args, cwd=ROOT):
    return subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, text=True)


# -- recording ---------------------------------------------------------------
def record_env(out_dir, env=None):
    """-> the environment a recorded harness run gets: the hook's
    sitecustomize first on PYTHONPATH, and where the records go."""
    env = dict(os.environ if env is None else env)
    site = pathlib.Path(out_dir) / 'site'
    site.mkdir(parents=True, exist_ok=True)
    (site / 'sitecustomize.py').write_text(SITECUSTOMIZE, encoding='utf-8')
    env['PYTHONPATH'] = str(site) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    env['HARNESS_REACH_RECORD'] = str(out_dir)
    env['HARNESS_REACH_ROOT'] = str(ROOT)
    env['HARNESS_REACH_HOOK'] = str(ROOT / 'tools' / 'harness_reach_hook.py')
    env['HARNESS_REACH_SITE'] = str(site)
    env.pop('HARNESS_REACH_CHECK', None)
    env.pop('HARNESS_REACH_COPIES_FILES', None)
    env.pop('HARNESS_REACH_ALIASES', None)
    return env


def merge(out_dir, commit):
    """-> the ledger built from a recorded run's files in out_dir.
    `commit` is what a later run diffs against: a tree (what a run records)
    or a commit."""
    out_dir = pathlib.Path(out_dir)
    checks, imports = {}, {}

    def into(dst, rec):
        for k, v in rec.items():
            dst.setdefault(k, set()).update(tuple(x) if k == 'c' else x for x in v)
    for f in sorted(out_dir.glob('parent-*.json')):
        data = json.loads(f.read_text(encoding='utf-8'))
        for n, rec in data.get('checks', {}).items():
            into(checks.setdefault(n, {}), rec)
        for m, rec in data.get('imports', {}).items():
            into(imports.setdefault(m, {}), rec)
    for start in sorted(out_dir.glob('child-*.start')):
        name = start.read_text(encoding='utf-8')
        rec_file = start.with_suffix('.json')
        dst = checks.setdefault(name, {})
        try:
            into(dst, json.loads(rec_file.read_text(encoding='utf-8'))['record'])
        except (OSError, ValueError, KeyError):
            dst.setdefault('o', set()).add('a Python child ended before it wrote '
                                           'what it reached')
    # A check that ran a module's code inherits what the module's import
    # reached, and so on through the imports that import reached.
    for name, rec in checks.items():
        done = set()
        todo = {f for f, _q in rec.get('c', ())}
        while todo:
            m = todo.pop()
            if m in done:
                continue
            done.add(m)
            imp = imports.get(m)
            if imp:
                into(rec, {k: list(v) for k, v in imp.items()})
                todo |= {f for f, _q in imp.get('c', ())} - done
    out = {}
    for name, rec in sorted(checks.items()):
        code = {}
        for f, q in rec.get('c', ()):
            code.setdefault(f, set()).add(unit_of(q))
        out[name] = {'c': {f: sorted(qs) for f, qs in sorted(code.items())},
                     **{k: sorted(rec[k]) for k in 'fdxo' if rec.get(k)}}
    return {'version': VERSION, 'commit': commit,
            'python': '.'.join(map(str, sys.version_info[:2])), 'checks': out}


# -- code units ----------------------------------------------------------------
_ANON = ('<lambda>', '<genexpr>', '<listcomp>', '<dictcomp>', '<setcomp>', '<locals>')


def unit_of(qualname):
    """-> the def a code object's qualified name belongs to: '<locals>'
    and anonymous parts dropped, '<module>' for a module's top level."""
    parts = [p for p in qualname.split('.') if p not in _ANON]
    return '.'.join(parts) if parts and parts != ['<module>'] else '<module>'


def units(source):
    """-> {unit: hash} for one Python file: every def by qualified name
    (class names included), and '<module>' for everything else -- the
    top level and class bodies, without the defs.
    Parsed code, never text: a comment or a moved line changes nothing.
    None when the file does not parse."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    out = {}

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f'{prefix}{child.name}'
                h = hashlib.sha256(ast.dump(child).encode()).hexdigest()[:16]
                out[q] = h if q not in out else hashlib.sha256((out[q] + h).encode()).hexdigest()[:16]
                walk(child, q + '.')
            elif isinstance(child, ast.ClassDef):
                walk(child, f'{prefix}{child.name}.')
            else:
                walk(child, prefix)
    walk(tree, '')

    # The top level without its defs: each def, decorators and defaults
    # included, is its own unit, so adding a check function -- most
    # changes to verify_harness.py -- leaves the top level as it was.
    class Strip(ast.NodeTransformer):
        def visit_FunctionDef(self, n):
            return None
        visit_AsyncFunctionDef = visit_FunctionDef
    out['<module>'] = hashlib.sha256(ast.dump(Strip().visit(tree)).encode()).hexdigest()[:16]
    return out


def changed_units(old, new):
    """-> the set of units whose code differs between two versions of a
    file, or None when either does not parse (treat the file as changed
    everywhere)."""
    a, b = units(old), units(new)
    if a is None or b is None:
        return None
    return {u for u in set(a) | set(b) if a.get(u) != b.get(u)}


# -- selection -----------------------------------------------------------------
def _show(rev, path, root=ROOT):
    r = subprocess.run(['git', '-C', str(root), 'show', f'{rev}:{path}'],
                       capture_output=True)
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else None


def changes(base, head=None, root=ROOT):
    """-> [(status, path)] between `base` and `head` (a commit), or the
    working tree with its untracked files when head is None."""
    rng = [base, head] if head else [base]
    r = _git('diff', '--name-status', '--no-renames', *rng, cwd=root)
    if r.returncode != 0:
        return None
    out = [(ln.split('\t', 1)[0][0], ln.split('\t', 1)[1])
           for ln in r.stdout.splitlines() if '\t' in ln]
    if head is None:
        u = _git('ls-files', '--others', '--exclude-standard', cwd=root)
        out += [('A', p) for p in u.stdout.splitlines() if p]
    return out


def _parent_dirs(path):
    parts = path.split('/')[:-1]
    return {'/'.join(parts[:i]) for i in range(len(parts) + 1)}


def select(ledger, base, head=None, names=None, root=ROOT):
    """-> (selected, reasons, full): the checks a change from the ledger's
    commit reaches. `full` is a reason string when the whole suite has to
    run instead, else None. `names` is every check the harness has now."""
    if not ledger or ledger.get('version') != VERSION:
        return set(), {}, 'no usable ledger'
    diff = changes(base, head, root)
    if diff is None:
        return set(), {}, f'the ledger\'s commit {base[:12]} is not in this history'
    rec = ledger['checks']
    root = pathlib.Path(root)
    names = set(names if names is not None else rec)
    paths = {p for _s, p in diff}
    hit = sorted(paths & set(MACHINERY))
    if hit:
        return set(), {}, f'the recording machinery changed ({", ".join(hit)})'
    reasons = {}

    def add(n, why):
        if n in names:
            reasons.setdefault(n, why)
    for n in names:
        if n not in rec:
            add(n, 'new since the ledger was recorded')
        elif rec[n].get('o'):
            add(n, f'reach not fully seen: {rec[n]["o"][0]}')
    for status, p in diff:
        if status in 'AD':
            dirs = _parent_dirs(p)
            for n, r in rec.items():
                if p in r.get('f', ()) or p in r.get('x', ()) or \
                        dirs & set(r.get('d', ())):
                    add(n, f'{p} {"added" if status == "A" else "deleted"}')
                elif p.endswith('.py') and p in r.get('c', {}):
                    add(n, f'{p} {"added" if status == "A" else "deleted"}')
            continue
        # modified
        readers = [n for n, r in rec.items() if p in r.get('f', ())]
        for n in readers:
            add(n, f'reads {p}')
        if p.endswith('.py'):
            old, new = _show(base, p, root), (_show(head, p, root) if head else
                                              (root / p).read_text(encoding='utf-8', errors='replace')
                                              if (root / p).is_file() else None)
            cu = changed_units(old or '', new or '')
            if p == HARNESS and (cu is None or '<module>' in cu):
                return set(), {}, f'{HARNESS}\'s own top level changed'
            for n, r in rec.items():
                ran = set(r.get('c', {}).get(p, ()))
                if not ran:
                    continue
                if cu is None or '<module>' in cu:
                    add(n, f'{p} changed at its top level')
                    continue
                touched = sorted(ran & cu)
                if touched:
                    add(n, f'{p}: {touched[0]}' + (f' (+{len(touched) - 1})'
                                                   if len(touched) > 1 else ''))
    selected = set(reasons)
    return selected, reasons, None


# -- the ledger's home ----------------------------------------------------------
def load_ledger(fetch=True):
    """-> the ledger: the local file if there is one, else LEDGER_REF
    (fetched from origin first when `fetch`), else None."""
    if LOCAL_LEDGER.is_file():
        try:
            return json.loads(LOCAL_LEDGER.read_text(encoding='utf-8'))
        except ValueError:
            pass
    if fetch:
        _git('fetch', '--quiet', 'origin', f'+{LEDGER_REF}:{LEDGER_REF}')
    r = subprocess.run(['git', '-C', str(ROOT), 'show', f'{LEDGER_REF}:{LEDGER_NAME}'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def publish(ledger_file, push=True):
    """Store the ledger as a one-file commit at LEDGER_REF, and push it.
    Only a ledger from a green run: a failing check may have stopped before
    it reached everything it would."""
    try:
        if not json.loads(pathlib.Path(ledger_file).read_text(encoding='utf-8')).get('green'):
            print('harness_reach: not published -- this ledger is from a run '
                  'that failed')
            return 1
    except (OSError, ValueError):
        print('harness_reach: not published -- the ledger does not read')
        return 1
    blob = _git('hash-object', '-w', str(ledger_file)).stdout.strip()
    tree = subprocess.run(['git', '-C', str(ROOT), 'mktree'],
                          input=f'100644 blob {blob}\t{LEDGER_NAME}\n',
                          capture_output=True, text=True).stdout.strip()
    env = dict(os.environ, GIT_AUTHOR_NAME='harness-reach', GIT_AUTHOR_EMAIL='harness-reach@localhost',
               GIT_COMMITTER_NAME='harness-reach', GIT_COMMITTER_EMAIL='harness-reach@localhost')
    commit = subprocess.run(['git', '-C', str(ROOT), 'commit-tree', tree, '-m',
                             'harness reach ledger'],
                            capture_output=True, text=True, env=env).stdout.strip()
    _git('update-ref', LEDGER_REF, commit)
    if push:
        r = _git('push', '--quiet', '--force', 'origin', f'{LEDGER_REF}:{LEDGER_REF}')
        if r.returncode != 0:
            print(f'harness_reach: could not push the ledger: {r.stderr.strip()[-300:]}')
            return 1
    print(f'harness_reach: ledger at {LEDGER_REF} ({commit[:12]})')
    return 0


# -- what a run does --------------------------------------------------------------
def plan(names, head=None, fetch=True):
    """-> (selected or None for the whole suite, a one-line account)."""
    if os.environ.get('PRECEDENT_HARNESS_FULL') == '1':
        return None, 'the whole suite: asked for (PRECEDENT_HARNESS_FULL=1)'
    ledger = load_ledger(fetch=fetch)
    if ledger is None:
        return None, 'the whole suite: no ledger of what each check reaches yet'
    sel, reasons, full = select(ledger, ledger['commit'], head, names)
    if full:
        return None, f'the whole suite: {full}'
    if len(sel) > FULL_ABOVE * len(names):
        return None, (f'the whole suite: this change reaches {len(sel)} of '
                      f'{len(names)} checks')
    return sel, (f'{len(sel)} of {len(names)} checks: the ones this change '
                 f'reaches since {ledger["commit"][:12]}')


def _names():
    sys.path.insert(0, str(ROOT / 'tools'))
    src = (ROOT / HARNESS).read_text(encoding='utf-8')
    return sorted({ln[4:].split('(', 1)[0] for ln in src.splitlines()
                   if ln.startswith('def check_')})


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    cmd = argv[0] if argv else 'select'
    if cmd == 'select':
        base = argv[argv.index('--base') + 1] if '--base' in argv else None
        names = _names()
        ledger = load_ledger(fetch='--no-fetch' not in argv)
        if ledger is None:
            print('harness_reach: no ledger -- the whole suite would run')
            return 0
        sel, reasons, full = select(ledger, base or ledger['commit'], None, names)
        if full:
            print(f'harness_reach: the whole suite would run -- {full}')
            return 0
        print(f'harness_reach: {len(sel)} of {len(names)} checks reached '
              f'since {(base or ledger["commit"])[:12]}')
        for n in sorted(sel):
            print(f'  {n} -- {reasons[n]}')
        if '--names' in argv:
            print(','.join(sorted(sel)))
        return 0
    if cmd == 'record':
        env = dict(os.environ, PRECEDENT_HARNESS_FULL='1', PRECEDENT_HARNESS_RECORD_FULL='1')
        env.setdefault('PRECEDENT_HARNESS_ASKED', 'harness_reach record')
        return subprocess.run([sys.executable, str(ROOT / HARNESS), '--as-ci'],
                              env=env).returncode
    if cmd == 'publish':
        if not LOCAL_LEDGER.is_file():
            print('harness_reach: no local ledger to publish -- run record first')
            return 1
        return publish(LOCAL_LEDGER, push='--no-push' not in argv)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

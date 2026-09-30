#!/usr/bin/env python3
"""precedent_local_edits.py -- a consuming repo's committed edits to files it
received from BestPractice: found, resolved at Update Vendors, and sent
upstream as a ready branch.

Run it from the consuming repo, calling THIS copy -- the one in the
BestPractice clone, never a vendored one:

    python3 ../BestPractice/tools/precedent_local_edits.py status --repo .
    python3 ../BestPractice/tools/precedent_local_edits.py send --repo . --why "what went wrong"

WHY IT EXISTS (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md, 2026-09-29). A
session that hits a bug in a vendored file often fixes the local copy.
Update Vendors then refused over the edit ("Move the edit upstream, or
refresh --force"), and Morgan found most of those edits were local attempts
to fix the same bug upstream had fixed. So the refusal kept a repo on its
own patch, without upstream's fix, until someone decided by hand.

THREE LAYERS, all BestPractice's (precedent_practice_refs.received_owners()
is the one answer to who owns a received file):
  engine     every file tools/ENGINE_MANIFEST.json records by hash: tools/,
             hooks in .claude/hooks/, paths declared under engine_paths; an
             edit is what the refresh itself calls one (_local_drift,
             _hook_drift, _engine_path_drift), BASE the file at the
             manifest's source_commit. routing_scope.json is left out: the
             refresh generates it, so there is no upstream text to merge.
  catalogue  process/upstream/, in repos installed before 2026-09-14; an
             edit is what checkin.py's update guard refuses on
             (checkin.local_changes), BASE the file at upstream.commit.
  section0   a section 0 install's precedent/universal/practices/, BASE the
             commit its CATALOGUE_SYNC.json names; precedent_update.py finds
             the edits (section0_edits() only builds them), and `send` does
             not carry this layer yet.
CI workflows, received practices and checks (MANIFEST.json) and a shared
set's process/<name>/ tree are out of this version -- the plan says why.

AT UPDATE VENDORS (precedent_update.py calls Swap and resolve()). The
consumer's own old engine copy runs the refresh, and refuses on a hand edit
before it replaces itself, so the resolution cannot live in the engine. It
lives here, run from the source clone:
  1. an edit that is not committed stops the layer, nothing written
     (practice: repair-cannot-discard-work);
  2. each LOCAL is saved to a journal in the repo's git directory, and BASE
     written in its place, so the layer's own update runs clean;
  3. the layer updates as it always has, writing NEW;
  4. resolve() applies the rules below; LOCAL comes back from the journal on
     every other exit, and a journal a dead run left behind is replayed by
     recover() before the next one starts.

THE RULES, per file:
  kept      precedent.json's kept_template_divergences names the path, with
            a reason, pinned to NEW's sha256: LOCAL stays; a pin upstream
            has since moved is left for the person, LOCAL still kept
  1         NEW == BASE: LOCAL stays, reported as still a local edit
  2         a clean three-way merge: written, then each merged file must
            compile or parse and the repo's tools/checks/tests/run_all.sh
            pass; any failure puts every merged file back to NEW
  (already) the merge equals NEW: upstream already carries the change
  3         a conflict: NEW stays, with the commit that holds LOCAL named

SEND. The edits that remain go to the owner's clone as a branch off its
landing branch, three-way merged onto its tip so upstream work since
vendoring is never reverted, scrubbed on both sides, committed and pushed --
never a pull request, never a merge -- and a Prompt Please block is printed
for the session that will land it. checkin.py push delegates here.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve()
SOURCE = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import precedent_time  # noqa: E402

ENGINE, CATALOGUE, SECTION0 = 'engine', 'catalogue', 'section0'
# Written by the refresh from upstream text it transforms, so a local edit
# to it has no upstream version to merge against.
GENERATED = frozenset({'routing_scope.json'})
JOURNAL_DIR = 'precedent-local-edits'

KEPT, KEPT_STALE, STILL_LOCAL, MERGED, ALREADY, TOOK_UPSTREAM = (
    'kept', 'kept-stale', 'still-local', 'merged', 'already-upstream',
    'took-upstream')
# The closing report's groups, in this order, in plain words.
GROUPS = (
    (KEPT, 'Kept on purpose -- precedent.json says so'),
    (STILL_LOCAL, 'Still your local edit -- upstream has not changed these files'),
    (MERGED, "Merged -- upstream's change and yours, both kept"),
    (ALREADY, 'Upstream now carries your change -- nothing of yours was lost'),
    (TOOK_UPSTREAM, "Upstream's version taken -- yours is kept in git history"),
)


def _pve():
    import precedent_vendor_engine as pve
    return pve


def _checkin(repo):
    """checkin.py, bound to `repo` -- its module state names one consumer."""
    import checkin
    checkin._select_repo(repo)
    return checkin


def _sha(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def _read(path):
    try:
        return path.read_bytes() if path.is_file() else None
    except OSError:
        return None


def _write(path, data):
    """Write `data`, or remove the file when it is None."""
    if data is None:
        if path.is_file() or path.is_symlink():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _git(cwd, *args, data=None):
    return subprocess.run(['git', '-C', str(cwd), *args], input=data,
                          capture_output=True)


def _show(clone, commit, rel):
    r = _git(clone, 'show', f'{commit}:{rel}')
    return r.stdout if r.returncode == 0 else None


def _has_commit(clone, commit):
    if _git(clone, 'cat-file', '-e', f'{commit}^{{commit}}').returncode == 0:
        return True
    # A shallow or single-branch clone can lack the commit something was
    # vendored from; ask origin for it once rather than guessing a base.
    _git(clone, 'fetch', '--quiet', 'origin', commit)
    return _git(clone, 'cat-file', '-e', f'{commit}^{{commit}}').returncode == 0


class Edit:
    """One received file this repo changed. `rel` is its path here,
    `upstream_rel` its path in the owner's repository; `base` and `local`
    are its bytes, None when the file is absent."""

    def __init__(self, layer, rel, upstream_rel, base, local, base_commit):
        self.layer, self.rel, self.upstream_rel = layer, rel, upstream_rel
        self.base, self.local, self.base_commit = base, local, base_commit

    def __repr__(self):
        return f'Edit({self.layer}, {self.rel})'


def engine_edits(repo, source=SOURCE):
    """-> (edits, problems) for what the engine manifest records: its files
    in tools/, the hooks it vendored into .claude/hooks/, and the paths
    precedent.json declares under engine_paths. An edit is what the
    refresh's own drift checks call one (_local_drift, _hook_drift,
    _engine_path_drift), so a hook a source's adapter now claims, or a path
    no longer declared, is not one here either. `problems` are [(rel, why)]
    for an edited file with no upstream text to compare with; while there
    are any, nothing in the layer is swapped, and the refresh refuses as it
    always has. CI workflows are never here: a workflow changes only with
    the person's own words (practice: ci-workflow-approved)."""
    pve = _pve()
    mpath = repo / 'tools' / pve.MANIFEST_NAME
    try:
        manifest = json.loads(mpath.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return [], []
    commit = manifest.get('source_commit') or ''
    ups = manifest.get(pve.ENGINE_PATHS_KEY) or {}
    found = []      # (rel here, rel upstream, recorded sha256)
    for name, _why in pve._local_drift(repo / 'tools', manifest):
        found.append((f'tools/{name}', f'tools/{name}',
                      (manifest.get('sha256') or {}).get(name)))
    for name, _why in pve._hook_drift(repo, manifest):
        found.append((f'{pve.HOOK_DEST_DIR}/{name}', f'{pve.HOOK_SOURCE_DIR}/{name}',
                      (manifest.get('hooks_sha256') or {}).get(name)))
    for local, _why in pve._engine_path_drift(repo, manifest):
        found.append((local, ups.get(local),
                      (manifest.get('engine_paths_sha256') or {}).get(local)))
    edits, problems = [], []
    for rel, up, recorded in found:
        if rel.startswith('tools/') and rel[len('tools/'):] in GENERATED:
            problems.append((rel, 'the refresh generates this file from upstream '
                             'text it trims, so there is no upstream version '
                             'to merge an edit with'))
            continue
        if not up:
            problems.append((rel, 'the manifest does not say which upstream file '
                             'it was vendored from'))
            continue
        if not commit or not _has_commit(source, commit):
            problems.append((rel, f'the commit it was vendored from '
                             f'({commit[:12] or "none recorded"}) is not in '
                             f'{source}, so there is nothing to compare with'))
            continue
        base = _show(source, commit, up)
        if base is None or _sha(base) != recorded:
            problems.append((rel, f'{source} at {commit[:12]} does not hold the '
                             f'text the manifest recorded for it'))
            continue
        edits.append(Edit(ENGINE, rel, up, base, _read(repo / rel), commit))
    return edits, problems


def catalogue_edits(repo, source=SOURCE):
    """-> (edits, problems) for process/upstream/, by checkin.py's own
    comparison with the recorded upstream.commit."""
    if not (repo / 'process' / 'manifest.json').is_file():
        return [], []
    ck = _checkin(repo)
    up = ck._manifest().get('upstream') or {}
    recorded = up.get('commit')
    tree = ck.UPSTREAM.relative_to(repo).as_posix()
    if not ck.UPSTREAM.is_dir():
        return [], []
    if not recorded:
        return [], [('process/manifest.json', 'records no upstream.commit, so a '
                      'local change cannot be told from upstream drift')]
    if not _has_commit(source, recorded):
        return [], [(tree, f'the recorded upstream.commit {recorded[:12]} is not in '
                     f'{source}, so there is nothing to compare with')]
    changed = ck.local_changes(source, recorded)
    if changed is None:
        return [], [(tree, f'could not read {recorded[:12]} in {source}')]
    return [Edit(CATALOGUE, f'{tree}/{p.as_posix()}', p.as_posix(),
                 _show(source, recorded, p.as_posix()),
                 _read(ck.UPSTREAM / p), recorded)
            for p in changed], []


def find(repo, layer, source=SOURCE):
    return (engine_edits if layer == ENGINE else catalogue_edits)(repo, source)


def uncommitted(repo, edits):
    """-> [rel] whose working copy is not what HEAD holds: an edit nobody
    committed, which nothing here may write over."""
    out = []
    for e in edits:
        r = _git(repo, 'status', '--porcelain', '--untracked-files=all', '--', e.rel)
        if r.returncode != 0 or r.stdout.strip():
            out.append(e.rel)
    return out


def local_commit(repo, rel):
    """The commit that last changed `rel` here -- the one holding the local
    version a rule replaced."""
    r = _git(repo, 'log', '-1', '--format=%h', '--', rel)
    return r.stdout.decode().strip() or 'HEAD'


# --- the journal, and the swap it makes safe --------------------------------

def _journal(repo):
    r = _git(repo, 'rev-parse', '--absolute-git-dir')
    gitdir = r.stdout.decode().strip()
    return pathlib.Path(gitdir) / JOURNAL_DIR if gitdir else None


def _write_json(path, data):
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class Swap:
    """Write BASE over each edit for the length of a `with` block, and put
    LOCAL back on every way out of it except resolve() -- an exception, a
    refusal, SIGTERM or SIGHUP. LOCAL is first saved to a journal inside the
    repo's git directory (never the working tree, never committed), so a run
    killed outright is put right by recover() at the start of the next one.
    That git history holds the committed copy is not enough on its own
    (practice: repair-cannot-discard-work)."""

    def __init__(self, repo, edits):
        self.repo, self.edits = repo, list(edits)
        self.dir = _journal(repo)
        self.resolved = False
        self.merges = {}     # rel -> (merged bytes, upstream's bytes), by resolve()
        self._handlers = {}

    def _record(self, outcomes=None):
        files = []
        for i, e in enumerate(self.edits):
            files.append({'rel': e.rel, 'layer': e.layer, 'upstream': e.upstream_rel,
                          'local': f'{i}.local' if e.local is not None else None,
                          'base_sha256': _sha(e.base),
                          'outcome_sha256': (outcomes or {}).get(e.rel)})
        _write_json(self.dir / 'journal.json',
                    {'written': precedent_time.stamp(self.repo), 'files': files})

    def __enter__(self):
        if not self.edits:
            return self
        if self.dir is None:
            raise RuntimeError(f'{self.repo} has no git directory to journal in')
        if (self.dir / 'journal.json').exists():
            raise RuntimeError(f'a journal from an earlier run is still in '
                               f'{self.dir}; recover() first')
        self.dir.mkdir(parents=True, exist_ok=True)
        for i, e in enumerate(self.edits):
            if e.local is not None:
                (self.dir / f'{i}.local').write_bytes(e.local)
        self._record()
        for sig in (signal.SIGTERM, signal.SIGHUP):
            try:
                self._handlers[sig] = signal.signal(sig, self._stop)
            except (ValueError, OSError):       # not the main thread
                pass
        for e in self.edits:
            _write(self.repo / e.rel, e.base)
        return self

    @staticmethod
    def _stop(signum, _frame):
        raise SystemExit(128 + signum)

    def note(self, outcomes):
        """Record what resolve() is about to write, before it writes it, so
        a run killed mid-way is still recognised as this tool's output."""
        if self.edits:
            self._record(outcomes)

    def restore(self):
        for e in self.edits:
            _write(self.repo / e.rel, e.local)

    def __exit__(self, *_exc):
        for sig, h in self._handlers.items():
            signal.signal(sig, h)
        if self.edits:
            if not self.resolved:
                self.restore()
            shutil.rmtree(self.dir, ignore_errors=True)
        return False


def _upstream_sha_now(repo, entry, source):
    """sha256 of upstream's text for the file at the commit its layer now
    records -- what a layer update that finished before the run died would
    have written."""
    up = entry.get('upstream') or entry['rel']
    try:
        if entry['layer'] == ENGINE:
            commit = json.loads((repo / 'tools' / _pve().MANIFEST_NAME)
                                .read_text(encoding='utf-8')).get('source_commit')
        elif entry['layer'] == SECTION0:
            tree = entry['rel'][:-len(up)].rstrip('/')
            commit = json.loads((repo / tree / 'CATALOGUE_SYNC.json')
                                .read_text(encoding='utf-8')).get('source_commit')
        else:
            commit = (_checkin(repo)._manifest().get('upstream') or {}).get('commit')
        return _sha(_show(source, commit, up)) if commit else None
    except (OSError, ValueError, KeyError, AttributeError):
        return None


def section0_edits(repo, source, rels, tree, commit):
    """-> [Edit] for a section 0 install's universal catalogue: `rels` are
    the committed local edits precedent_update.vendor_universal_catalogue()
    found under `tree`/practices/, judged against `commit`, the catalogue's
    own CATALOGUE_SYNC.json record -- which is BASE."""
    return [Edit(SECTION0, rel, rel[len(tree) + 1:],
                 _show(source, commit, rel[len(tree) + 1:]), _read(repo / rel),
                 commit) for rel in rels]


def recover(repo, source=SOURCE):
    """Replay a journal a killed run left behind. -> (restored, left): a file
    whose content is something this tool wrote (BASE, an outcome it noted,
    or upstream's text now) gets LOCAL back; any other content is a
    person's, and is left alone with the journal kept, named in `left`."""
    d = _journal(repo)
    if d is None or not (d / 'journal.json').is_file():
        return [], []
    try:
        journal = json.loads((d / 'journal.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return [], [(str(d), 'an unreadable journal from an earlier run')]
    restored, left = [], []
    for entry in journal.get('files') or []:
        path = repo / entry['rel']
        local = _read(d / entry['local']) if entry.get('local') else None
        now = _read(path)
        if now == local:
            continue
        ours = {entry.get('base_sha256'), entry.get('outcome_sha256'),
                _upstream_sha_now(repo, entry, source)} - {None}
        if _sha(now) in ours:
            _write(path, local)
            restored.append(entry['rel'])
        else:
            left.append((entry['rel'], f'changed since an earlier Update Vendors '
                         f'was stopped mid-way; its saved local copy is in {d}'))
    if left:
        kept = d.with_name(f'{JOURNAL_DIR}-kept-{precedent_time.stamp(repo)}'
                           .replace(':', '').replace(' ', '-'))
        shutil.move(str(d), str(kept))
        left = [(rel, why.replace(str(d), str(kept))) for rel, why in left]
    else:
        shutil.rmtree(d, ignore_errors=True)
    return restored, left


# --- the rules --------------------------------------------------------------

def merge3(ours, base, theirs):
    """-> (merged bytes, clean) for a three-way merge of `ours` and `theirs`
    over `base`, by `git merge-file`. A binary file never merges clean."""
    with tempfile.TemporaryDirectory(prefix='precedent-merge-') as td:
        paths = []
        for name, data in (('ours', ours), ('base', base), ('theirs', theirs)):
            p = pathlib.Path(td) / name
            p.write_bytes(data or b'')
            paths.append(str(p))
        r = subprocess.run(['git', 'merge-file', '-p', '-q', *paths],
                           capture_output=True)
        return r.stdout, r.returncode == 0


def send_command(repo):
    # Beside the repo it is "../BestPractice"; anywhere else, the full path
    # reads better than a climb through every parent.
    try:
        where = os.path.relpath(SOURCE, repo)
    except ValueError:
        where = str(SOURCE)
    if where.startswith('../..'):
        where = str(SOURCE)
    return (f'python3 {where}/tools/precedent_local_edits.py send --repo . '
            f'--why "<what went wrong>"')


def _decide(repo, e, new):
    """-> (outcome, bytes to write, why) for one edit, NEW read from disk."""
    pve = _pve()
    verdict, reason = pve._kept_divergence(repo, e.rel, _sha(new) or '')
    if verdict == 'kept':
        return KEPT, e.local, f'"{reason}"'
    if verdict == 'stale':
        return KEPT_STALE, e.local, reason
    note = (f' (its {pve.KEPT_DIVERGENCES_KEY} entry has no reason, so it is '
            f'not honoured)' if verdict == 'unreasoned' else '')
    if new == e.base:
        return STILL_LOCAL, e.local, note
    if e.local is None:
        return TOOK_UPSTREAM, new, 'deleted here, and upstream has since changed it' + note
    if new is None:
        return TOOK_UPSTREAM, None, 'upstream has since removed it' + note
    merged, clean = merge3(e.local, e.base, new)
    if not clean:
        return TOOK_UPSTREAM, new, ('upstream changed the same lines, most likely '
                                    'fixing the same bug') + note
    if merged == new:
        return ALREADY, new, note
    return MERGED, merged, note


def checks_run(repo, rels):
    """In plain words, what check_merged() runs on `rels`."""
    kinds = sorted({'compiles' if r.endswith('.py') else 'parses'
                    for r in rels if r.endswith(('.py', '.json', '.sh'))})
    said = ' and '.join(kinds) or 'is read'
    if (repo / 'tools' / 'checks' / 'tests' / 'run_all.sh').is_file():
        return f'it {said}, and tools/checks/tests/run_all.sh passes'
    return f'it {said}; this repo has no tools/checks/tests/run_all.sh to run'


def check_merged(repo, rels):
    """-> [(what, why)] failures of the files a merge wrote: each must
    compile (Python) or parse (shell, JSON), and the repo's own received
    check tests must pass where it has them. The basic tier alone runs no
    code, so it cannot see a merge that is clean as text and broken as a
    program."""
    fails = []
    for rel in rels:
        path = repo / rel
        data = _read(path)
        if data is None:
            continue
        try:
            if rel.endswith('.py'):
                compile(data, rel, 'exec')
            elif rel.endswith('.json'):
                json.loads(data)
            elif rel.endswith('.sh'):
                r = subprocess.run(['bash', '-n', str(path)], capture_output=True,
                                   text=True)
                if r.returncode != 0:
                    raise SyntaxError(r.stderr.strip()[:200])
        except (SyntaxError, ValueError) as err:
            fails.append((rel, f'does not parse: {str(err)[:200]}'))
    tests = repo / 'tools' / 'checks' / 'tests' / 'run_all.sh'
    if rels and not fails and tests.is_file():
        try:
            r = subprocess.run(['bash', str(tests)], cwd=str(repo),
                               capture_output=True, text=True, timeout=1800)
            if r.returncode != 0:
                tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
                fails.append(('tools/checks/tests/run_all.sh',
                              'failed: ' + ' | '.join(tail)[:300]))
        except subprocess.TimeoutExpired:
            fails.append(('tools/checks/tests/run_all.sh', 'ran over 30 minutes'))
    return fails


def resolve(repo, swap):
    """Apply the rules to every edit `swap` holds, after the layer's own
    update wrote NEW. -> [(outcome, rel, text)] for the closing report."""
    decisions = []
    for e in swap.edits:
        new = _read(repo / e.rel)
        outcome, data, why = _decide(repo, e, new)
        decisions.append([e, new, outcome, data, why])
    swap.note({e.rel: _sha(data) for e, _n, _o, data, _w in decisions})
    for e, _new, _outcome, data, _why in decisions:
        _write(repo / e.rel, data)
    merged = [d for d in decisions if d[2] == MERGED]
    fails = check_merged(repo, [d[0].rel for d in merged])
    if fails:
        failed = '; '.join(f'{what} {why}' for what, why in fails)
        for d in merged:
            e, new = d[0], d[1]
            _write(repo / e.rel, new)
            d[2], d[3] = TOOK_UPSTREAM, new
            d[4] = (f'your edit and upstream\'s merged cleanly as text, but the '
                    f'result failed a check ({failed})')
    swap.resolved = True
    swap.merges = {d[0].rel: (d[3], d[1]) for d in decisions if d[2] == MERGED}
    cmd = send_command(repo)
    out = []
    for e, new, outcome, _data, why in decisions:
        if outcome == KEPT:
            text = f'kept as precedent.json records -- {why}'
        elif outcome == KEPT_STALE:
            text = (f'kept, but upstream has changed this file since precedent.json '
                    f'recorded the decision ("{why}"). Your version is still in '
                    f'place. If it should stay, record template_sha256 '
                    f'"{_sha(new) or ""}" for it; otherwise remove the entry')
        elif outcome == STILL_LOCAL:
            text = (f'upstream has not changed this file since it was vendored, so '
                    f'your edit stays{why}. If it fixes a bug, send it upstream: {cmd}')
        elif outcome == MERGED:
            text = (f'your edit and upstream\'s both kept, and the result was '
                    f'checked ({checks_run(repo, [e.rel])}){why}. Your part is still '
                    f'a local edit until it is sent upstream: {cmd}')
        elif outcome == ALREADY:
            text = f'upstream\'s version already contains your change{why}'
        else:
            text = took_upstream_text(repo, e.rel, why, e.local is not None)
        out.append((outcome, e.rel, text))
    return out


def took_upstream_text(repo, rel, why, had_local=True):
    """Rule 3's line in the report: why upstream's version was taken, the
    commit holding the local one, and how to bring it back or send it."""
    c, cmd = local_commit(repo, rel), send_command(repo)
    back = (f'see it with `git show {c}:{rel}`; if the bug is still there, '
            f'bring it back with `git show {c}:{rel} > {rel}` and send it '
            f'upstream: {cmd}' if had_local else
            f'if you still want it gone, delete it again and send that '
            f'upstream: {cmd}')
    return f'{why}, so upstream\'s version was taken. Yours is in commit {c} -- {back}'


def report_lines(outcomes):
    """The closing report's section, grouped by rule. KEPT_STALE is not
    here: it is left for the person, not a note."""
    lines = []
    for key, title in GROUPS:
        rows = [(rel, text) for outcome, rel, text in outcomes if outcome == key]
        if rows:
            lines.append(title + ':')
            lines += [f'  - {rel}: {text}' for rel, text in rows]
    return lines


# --- send ---------------------------------------------------------------------

def _run(argv, cwd, timeout=1800):
    r = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                       timeout=timeout,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    return r.returncode, r.stdout + r.stderr


def _tail(text, n=8):
    return '\n'.join('      ' + l for l in text.strip().splitlines()[-n:])


def _messages(repo, edits):
    """The messages of the commits here that made each edit: every commit
    touching the file since the manifest last recorded its layer."""
    out = []
    for e in edits:
        manifest = ('tools/ENGINE_MANIFEST.json' if e.layer == ENGINE
                    else 'process/manifest.json')
        since = _git(repo, 'log', '-1', '--format=%H', '--', manifest)
        since = since.stdout.decode().strip()
        span = [f'{since}..HEAD'] if since else ['-n', '5']
        r = _git(repo, 'log', *span, '--format=%B%x00', '--', e.rel)
        out += [m.strip() for m in r.stdout.decode(errors='replace').split('\0')
                if m.strip()]
    return list(dict.fromkeys(out))


def _word_lists(repo, source):
    """-> ([compiled pattern], [problem]): the leak gate's list (the
    committed default plus the person's private half) and this repo's own
    scrub list, when it has one. A list that cannot load is a problem, never
    an empty pass."""
    pats, problems = [], []
    sys.path.insert(0, str(source / 'tools'))
    try:
        import leak_gate
        pats += list(leak_gate.load_blocklist()[0])
    except SystemExit as err:
        problems.append(f'the leak gate word list could not load: {err}')
    except Exception as err:                    # noqa: BLE001
        problems.append(f'the leak gate word list could not load: {err}')
    up = {}
    try:
        up = json.loads((repo / 'process' / 'manifest.json')
                        .read_text(encoding='utf-8')).get('upstream') or {}
    except (OSError, ValueError):
        pass
    if 'scrub_blocklist' in up and up['scrub_blocklist'] is None:
        return pats, problems
    scrub = repo / (up.get('scrub_blocklist') or 'process/scrub_blocklist.txt')
    if scrub.is_file():
        import practice_audit
        loaded, why = practice_audit.load_blocklist(scrub)
        if loaded:
            pats += loaded[0]
        else:
            problems.append(f'{scrub.relative_to(repo)}: {why}')
    elif up.get('scrub_blocklist'):
        problems.append(f'the configured scrub list {up["scrub_blocklist"]} is missing')
    return pats, problems


def _scan(texts, pats):
    hits = []
    for label, text in texts:
        for n, line in enumerate(text.splitlines(), 1):
            for p in pats:
                if p.search(line):
                    hits.append(f'{label}:{n} matches /{p.pattern}/')
                    break
    return hits


def consumer_scrub(repo, source, texts):
    """The consuming repo's side of the privacy line, run before anything
    leaves: its own practice_audit.py where it has one -- run from ITS copy,
    so the scrub reads this repo (checkin.py push --repo used to run the
    source clone's copy, which found no process/ there and passed as NOT
    APPLICABLE) -- then every outgoing line against the word lists.
    -> [finding]."""
    found = []
    audit = repo / 'process' / 'upstream' / 'tools' / 'practice_audit.py'
    if audit.is_file():
        rc, out = _run([sys.executable, str(audit)], repo)
        if rc != 0:
            found.append('practice_audit (this repo\'s scrub) failed:\n' + _tail(out))
    pats, problems = _word_lists(repo, source)
    found += problems
    found += _scan(texts, pats)
    return found


def _slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:40] or 'edit'


def _remote_repo(owner):
    r = _git(owner, 'remote', 'get-url', 'origin')
    url = r.stdout.decode().strip()
    m = re.search(r'github\.com[:/]+([^/]+/[^/.]+)', url)
    return m.group(1) if m else (url or str(owner))


def _landing(owner):
    rc, out = _run([sys.executable, str(owner / 'tools' / 'precedent_branches.py'),
                    '--landing'], owner)
    first = out.strip().splitlines()[0].strip() if out.strip() else ''
    return first if rc == 0 and re.fullmatch(r'[\w./-]+', first or '') else None


def _apply(wt, edits):
    """Three-way merge each edit onto the owner's tip in `wt`. -> (sent,
    already, conflicts) as lists of Edit."""
    sent, already, conflicts = [], [], []
    for e in edits:
        path = wt / e.upstream_rel
        cur = _read(path)
        if e.local is None:
            if cur is None:
                already.append(e)
            elif cur == e.base:
                _write(path, None)
                sent.append(e)
            else:
                conflicts.append(e)
            continue
        if e.base is None:
            if cur is None:
                _write(path, e.local)
                sent.append(e)
            elif cur == e.local:
                already.append(e)
            else:
                conflicts.append(e)
            continue
        if cur is None:
            conflicts.append(e)
            continue
        merged, clean = merge3(cur, e.base, e.local)
        if not clean:
            conflicts.append(e)
        elif merged == cur:
            already.append(e)
        else:
            _write(path, merged)
            sent.append(e)
    return sent, already, conflicts


def _session_trailer():
    sid = os.environ.get('CLAUDE_CODE_REMOTE_SESSION_ID', '').strip()
    if sid:
        sid = sid if sid.startswith('session_') else f'session_{sid}'
        return f'Session: https://claude.ai/code/{sid}', sid
    return 'Session: none available (precedent_local_edits.py send)', None


def prompt_block(owner_repo, branch, landing, tip, sent, why, sid):
    origin = (f'Sent automatically by `precedent_local_edits.py send`, run in the '
              f'session {sid} -- https://claude.ai/code/{sid}. Nobody typed this.'
              if sid else
              'Sent automatically by `precedent_local_edits.py send`, run from a '
              'repository that vendors this one. Nobody typed this.')
    files = '\n'.join(f'- {e.upstream_rel}' for e in sent)
    return f"""{origin}

Seed root: {owner_repo}. Attach: none.

SITUATION
A repository that vendors this one fixed {len(sent)} file(s) it received from
here, in its own copy. The change is on branch {branch}, based on {landing}
at {tip[:12]} and merged three ways, so nothing upstream changed since that
repository vendored the file is reverted. Files:
{files}

WHAT WENT WRONG THERE
{why}

WHAT TO DO
Read the branch's diff and decide whether the bug is real here. If it is,
add a test that fails without the fix, then run this repository's checks
(practice: upstream-bug-stops-here -- a fix without its test is not booked).
If it is not, say why, and nothing lands. Land it only when a person says
"Booked" (step 3 of 5; "Go update" is the same word). No merge authorization
comes with this prompt.

AFTER IT LANDS
The vendoring repository keeps its local edit until its next Update Vendors,
which then finds its copy matching upstream again."""


def send(repo, why, owner=None, layers=(ENGINE, CATALOGUE), dry_run=False):
    """Part one. -> exit code: 0 sent (or nothing to send), 1 nothing sent
    because every edit conflicts or is uncommitted, 2 refused or failed."""
    owner = pathlib.Path(owner or SOURCE).resolve()
    restored, left = recover(repo, owner)
    for rel in restored:
        print(f'precedent_local_edits: put back your local {rel}, which an '
              f'earlier Update Vendors stopped mid-way had left replaced')
    for rel, why_left in left:
        print(f'precedent_local_edits: {rel}: {why_left}')
    edits, problems = [], []
    for layer in layers:
        found, probs = find(repo, layer, owner)
        edits += found
        problems += probs
    for rel, why_p in problems:
        print(f'  cannot send {rel}: {why_p}')
    if not edits:
        print('precedent_local_edits send: no local edits to received files here, '
              'so there is nothing to send.' + (' (See above for files it could '
                                                'not judge.)' if problems else ''))
        return 2 if problems else 0
    dirty = uncommitted(repo, edits)
    if dirty:
        for rel in dirty:
            print(f'  not committed: {rel}')
        print('precedent_local_edits send REFUSED: commit the edits above first. '
              'Only a committed edit is sent, so what goes upstream is exactly '
              'what this repo holds.')
        return 1
    if not why or not why.strip():
        print('precedent_local_edits send REFUSED: --why is required -- what went '
              'wrong here that the edit fixes. The diff holds the fix, not the '
              'symptom. Commit messages that made the edit, as a first draft:')
        for m in _messages(repo, edits):
            print('    ' + m.splitlines()[0])
        return 2
    landing = _landing(owner)
    if not landing:
        print(f'precedent_local_edits send FAILED: could not tell {owner}\'s '
              f'landing branch (tools/precedent_branches.py --landing).')
        return 2
    fetched = _git(owner, 'fetch', '--quiet', 'origin',
                   f'+refs/heads/{landing}:refs/remotes/origin/{landing}')
    tip = _git(owner, 'rev-parse', f'origin/{landing}').stdout.decode().strip()
    if not tip:
        print(f'precedent_local_edits send FAILED: {owner} has no origin/{landing} '
              f'({fetched.stderr.decode().strip()[:200]}).')
        return 2
    stem = pathlib.PurePosixPath(edits[0].upstream_rel).stem
    base_name = f'local-edit/{precedent_time.today(repo)}-{_slug(stem)}'
    branch, n = base_name, 1
    while (_git(owner, 'rev-parse', '--verify', '--quiet', branch).returncode == 0
           or _git(owner, 'ls-remote', '--exit-code', '--heads', 'origin',
                   branch).returncode == 0):
        n += 1
        branch = f'{base_name}-{n}'
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-send-'))
    wt = tmp / 'wt'
    added = _git(owner, 'worktree', 'add', '-q', '-b', branch, str(wt), tip)
    if added.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        print(f'precedent_local_edits send FAILED: could not make a worktree in '
              f'{owner}: {added.stderr.decode().strip()[:300]}')
        return 2
    pushed = False
    try:
        sent, already, conflicts = _apply(wt, edits)
        for e in already:
            print(f'  already upstream: {e.rel} -- {landing} carries this change')
        for e in conflicts:
            print(f'  not sent: {e.rel} -- upstream changed the same lines since '
                  f'it was vendored; Update Vendors will take upstream\'s version '
                  f'and name the commit holding yours')
        if not sent:
            print('precedent_local_edits send: nothing to send.')
            return 1 if conflicts else 0
        _git(wt, 'add', '-A')
        diff = _git(wt, 'diff', '--cached', '-U0').stdout.decode(errors='replace')
        outgoing = '\n'.join(l[1:] for l in diff.splitlines()
                             if l.startswith('+') and not l.startswith('+++'))
        texts = [('the change', outgoing), ('--why', why)]
        texts += [(f'a commit message here ({i + 1})', m)
                  for i, m in enumerate(_messages(repo, sent))]
        found = consumer_scrub(repo, owner, texts)
        if found:
            print('precedent_local_edits send REFUSED before anything left this '
                  'machine -- the scrub on this repo\'s side found:')
            for f in found:
                print(f'  - {f}')
            print('Take the word out (or add it to the right list if it is safe), '
                  'commit, and run send again. Nothing was pushed.')
            return 2
        rc, out = _run([sys.executable, str(wt / 'tools' / 'leak_gate.py'),
                        '--staged'], wt)
        if rc != 0:
            print(f'precedent_local_edits send REFUSED before anything left this '
                  f'machine -- {_remote_repo(owner)}\'s leak gate:\n{_tail(out, 15)}\n'
                  f'Nothing was pushed.')
            return 2
        trailer, sid = _session_trailer()
        files = ', '.join(pathlib.PurePosixPath(e.upstream_rel).name for e in sent)
        message = (f'Fix from a vendoring repo: {files}\n\n{why.strip()}\n\n'
                   f'Sent by tools/precedent_local_edits.py send: a local edit to '
                   f'received file(s), merged three ways onto {landing} at '
                   f'{tip[:12]}. Needs a test that fails without it before it is '
                   f'booked.\n\n{trailer}\n')
        c = _git(wt, 'commit', '-q', '-F', '-', data=message.encode())
        if c.returncode != 0:
            print(f'precedent_local_edits send FAILED: the commit in {owner} was '
                  f'refused: {c.stderr.decode().strip()[:400]}')
            return 2
        rc, out = _run([sys.executable, str(wt / 'tools' / 'precedent_push_check.py'),
                        '--tier', 'basic', '--changed-since', f'origin/{landing}'], wt)
        if rc != 0:
            print(f'precedent_local_edits send REFUSED: {_remote_repo(owner)}\'s '
                  f'basic tier failed on the branch:\n{_tail(out, 15)}\n'
                  f'Nothing was pushed.')
            return 2
        if dry_run:
            print(f'precedent_local_edits send --dry-run: branch {branch} passed '
                  f'every check; not pushed.')
            return 0
        p = _git(wt, 'push', '-u', 'origin', branch)
        if p.returncode != 0:
            print(f'precedent_local_edits send FAILED: the push was refused: '
                  f'{p.stderr.decode().strip()[:400]}\nNothing was published; the '
                  f'branch {branch} is kept in {owner}.')
            pushed = True       # keep the local branch for a retry
            return 2
        pushed = True
        print(f'precedent_local_edits send: pushed {branch} to '
              f'{_remote_repo(owner)} with {len(sent)} file(s). No pull request '
              f'was opened and nothing was merged.')
        print('\nYour local edit stays in place here. Once this fix lands upstream '
              'and this repo runs Update Vendors, the files match again and it '
              'stops being reported as a local edit.')
        print('\nPaste into: a new session rooted in '
              f'{_remote_repo(owner)}, nothing attached.\n')
        print(prompt_block(_remote_repo(owner), branch, landing, tip, sent,
                           why.strip(), sid))
        return 0
    finally:
        _git(owner, 'worktree', 'remove', '--force', str(wt))
        shutil.rmtree(tmp, ignore_errors=True)
        if not pushed:
            _git(owner, 'branch', '-D', branch)


def status(repo, source=SOURCE):
    rc = 0
    for layer in (ENGINE, CATALOGUE):
        edits, problems = find(repo, layer, source)
        dirty = set(uncommitted(repo, edits))
        for e in edits:
            print(f'{layer}: {e.rel}' + ('  (not committed)' if e.rel in dirty else ''))
        for rel, why in problems:
            print(f'{layer}: {rel}  (cannot judge: {why})')
        rc = rc or bool(edits or problems)
    if not rc:
        print('no local edits to received files')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    st = sub.add_parser('status', help='list the local edits to received files')
    st.add_argument('--repo', default='.')
    sd = sub.add_parser('send', help='send them upstream as a ready branch')
    sd.add_argument('--repo', default='.')
    sd.add_argument('--why', default='', help='what went wrong that the edit fixes')
    sd.add_argument('--owner-clone', default=None,
                    help='the clone of the owning repo (default: this clone)')
    sd.add_argument('--layer', choices=(ENGINE, CATALOGUE), action='append')
    sd.add_argument('--dry-run', action='store_true',
                    help='build and check the branch, but do not push it')
    args = ap.parse_args(argv)
    repo = pathlib.Path(args.repo).resolve()
    if repo == SOURCE.resolve() and args.cmd == 'send' and not args.owner_clone:
        print('precedent_local_edits: --repo names this BestPractice clone itself; '
              'run it from the repo that vendors BestPractice.')
        return 2
    if args.cmd == 'status':
        return status(repo)
    return send(repo, args.why, args.owner_clone,
                tuple(args.layer or (ENGINE, CATALOGUE)), args.dry_run)


if __name__ == '__main__':
    sys.exit(main())

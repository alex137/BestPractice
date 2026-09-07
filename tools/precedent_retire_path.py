#!/usr/bin/env python3
"""precedent_retire_path.py — the double-check that has to pass before a
deprecated file or directory is deleted, and the deletion itself.

(practice: retirement-deletes-files)

WHY THIS EXISTS. Retiring a mechanism -- a scheduled workflow, a tool, a
vendored tree, a config -- leaves files behind that exist only to serve it.
Nothing forces anyone to delete them, and "leave it, it's harmless" is
always the cheaper answer in the moment, so they accumulate for years until
nobody left can say which of them still do anything. The rule
(practices/retirement-deletes-files.md) is that the files go in the same
change that retires the mechanism. This tool is what makes obeying it safe:
deleting on a hunch is how a live dependency gets cut, so the rule is
deliberately not "delete when you are confident" but "delete when a
mechanical audit says nothing points at it any more."

The audit REFUSES, it does not warn. There is no --force: a blocker is
either a real dependency (fix it, then re-run) or a reference that belongs
in a historical record (declare it in exempt_files). Both are edits someone
makes on purpose; neither is a flag to push past.

WHAT IT CHECKS, AND WHY EACH ONE BLOCKS.

  tracked        An untracked or already-absent path has no deletion to
                 make. Reported, never "deleted" -- claiming a no-op
                 succeeded is how a retirement gets recorded as done
                 without having happened.
  references     Any tracked file that still mentions the path (or its
                 basename, where that basename is distinctive enough to
                 search for) blocks. This is the same property
                 precedent_check.py's rename-updates-links enforces AFTER
                 the fact, run BEFORE it, so the deletion and the
                 repointing land in one commit rather than the check
                 failing on a branch that is already broken.
  live trigger   A .github/workflows/ file whose `on:` block still carries
                 any trigger other than workflow_dispatch blocks. A
                 retirement must never be the first thing that stops a
                 running job: pause the schedule, let a cycle pass, THEN
                 retire. Deleting a live workflow means its next failure is
                 silent, and a silent absence is the failure mode this whole
                 practice exists to prevent.
  dirty          A target with uncommitted modifications blocks. Everything
                 else here is recoverable -- git history holds a deleted
                 file forever -- and uncommitted content is the one thing
                 deletion destroys outright.

WHAT IT IS BLIND TO. A reference built by string concatenation at runtime,
a path named only in something this repo does not track (a GitHub branch
protection rule, a webhook, another repo's config), and a file that nothing
references and nothing runs but that someone still needs. The audit proves
no tracked file points at the path; it cannot prove the path is useless.
That judgment stays a person's, which is why the report prints the evidence
rather than only a verdict.

Usage:
  precedent_retire_path.py PATH [PATH...]            # audit only, always start here
  precedent_retire_path.py PATH --reason "..." --apply
                                                     # git rm + record it
  precedent_retire_path.py --list                    # what this repo has retired

Exit 0 when every path audited clean (or was applied), 1 when any blocked.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

REGISTRY = 'process/retired_paths.json'

# A basename this generic means a different file in every directory, so a
# basename search on it reports the whole repo. The full path is still
# searched for; only the basename pass is skipped. Same reasoning as
# rename-updates-links' single-segment skip, and the same honesty
# requirement: the report says when a basename pass was skipped.
GENERIC_BASENAMES = {
    'README.md', 'AGENTS.md', 'CLAUDE.md', 'TODO.md', 'MAP.md',
    'GLOSSARY.md', 'INSTALL.md', 'SETUP.md', 'MANIFEST.json',
    '__init__.py', 'settings.json', 'config.json', 'index.md',
    'requirements.txt', '.gitignore',
}

# Never scanned for references: a vendored mirror is a different repo's
# tree, byte-identical by contract, and a reference inside it is not this
# repo's to repoint. The registry itself names every retired path by
# design -- scanning it would make every retirement block on its own record.
SCAN_SKIP_PREFIXES = ('process/upstream/', '.git/')


def _git(*args, cwd=None):
    return subprocess.run(['git', '-C', str(cwd or ROOT), *args],
                          capture_output=True, text=True)


def _repo_root():
    r = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('precedent_retire_path: not inside a git repository -- this '
                 'tool audits a tracked tree, so there is nothing to run it '
                 'against here')
    return pathlib.Path(r.stdout.strip())


ROOT = _repo_root()


def load_registry():
    """The retirement record, or an empty one. A malformed registry is an
    error, never an empty default: silently treating it as empty would let
    a typo erase every retirement this repo has recorded."""
    p = ROOT / REGISTRY
    if not p.is_file():
        return {'retired': [], 'exempt_files': []}
    try:
        cfg = json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        sys.exit(f'precedent_retire_path: {REGISTRY} is not valid JSON ({e}) '
                 f'-- fix it before retiring anything, or a retirement will '
                 f'be recorded into a file nothing can read')
    if not isinstance(cfg, dict):
        sys.exit(f'precedent_retire_path: {REGISTRY} must be a JSON object '
                 f'with a "retired" list, not a {type(cfg).__name__}')
    cfg.setdefault('retired', [])
    cfg.setdefault('exempt_files', [])
    return cfg


def _exempt(rel, patterns):
    for e in patterns:
        if e.endswith('/'):
            if rel == e.rstrip('/') or rel.startswith(e):
                return True
        elif rel == e:
            return True
    return False


def tracked_files():
    r = _git('ls-files')
    return [f for f in r.stdout.splitlines() if f.strip()]


def _targets_under(path, tracked):
    """Every tracked file the deletion would actually remove. A directory is
    expanded rather than judged as one entry: retiring `process/personal`
    has to answer for every reference to `process/personal/README.md` too,
    and a directory-level search alone would never see one."""
    if path in tracked:
        return [path]
    pre = path.rstrip('/') + '/'
    return [f for f in tracked if f.startswith(pre)]


def _searchable_names(paths):
    """(needle, kind) pairs to search for, plus the basenames skipped as too
    generic to be honest about."""
    tracked = tracked_files()
    basename_counts = {}
    for f in tracked:
        basename_counts[os.path.basename(f)] = \
            basename_counts.get(os.path.basename(f), 0) + 1
    needles, skipped = [], []
    for p in paths:
        needles.append((p, 'path'))
        base = os.path.basename(p.rstrip('/'))
        if base in GENERIC_BASENAMES or len(base) < 5:
            skipped.append(base)
        elif basename_counts.get(base, 0) > 1:
            # The same basename elsewhere in the tree means a hit cannot be
            # attributed to this path. Reported, not silently dropped.
            skipped.append(base)
        elif base != p:
            needles.append((base, 'basename'))
    return needles, skipped


def find_references(paths, exempt):
    """Tracked files still mentioning any of `paths` (or a distinctive
    basename), excluding the paths themselves and everything declared
    exempt. Returns (hits, skipped_basenames)."""
    tracked = tracked_files()
    removed = set()
    for p in paths:
        removed.update(_targets_under(p, tracked))
        removed.add(p)
    needles, skipped = _searchable_names(paths)
    hits = []
    for rel in tracked:
        if rel in removed or rel == REGISTRY:
            continue
        if rel.startswith(SCAN_SKIP_PREFIXES) or _exempt(rel, exempt):
            continue
        f = ROOT / rel
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for needle, kind in needles:
                if needle in line:
                    hits.append((rel, i, needle, kind, line.strip()[:110]))
                    break
    return hits, skipped


_ON_BLOCK = re.compile(r'^on:\s*(.*)$')


def live_workflow_triggers(rel):
    """Triggers other than workflow_dispatch still active in a workflow file.

    Deliberately a shallow scan, not a YAML parse: a commented-out
    `# schedule:` must read as paused, and a parser sees no such key at all,
    so the two states this check exists to tell apart look identical to it.
    Anything it cannot classify is reported as live -- the safe direction,
    since the cost of a false block is one look and the cost of a false
    clear is a job that stops without anyone noticing."""
    p = ROOT / rel
    try:
        lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
    except OSError:
        return []
    live, in_on = [], False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        m = _ON_BLOCK.match(line)
        if m:
            in_on = True
            inline = m.group(1).strip()
            if inline:
                # `on: [push, workflow_dispatch]` or `on: push`
                for t in re.findall(r'[A-Za-z_]+', inline):
                    if t != 'workflow_dispatch':
                        live.append(t)
                in_on = False
            continue
        if in_on:
            if not line.startswith((' ', '\t')):
                in_on = False
                continue
            key = stripped.split(':')[0].strip('- ')
            if key and key != 'workflow_dispatch' and not line.startswith(
                    (' ' * 4, '\t\t')):
                live.append(key)
    return sorted(set(live))


def audit(path, exempt):
    """Blockers and evidence for one path. Blockers empty == safe to delete."""
    rel = path.rstrip('/')
    blockers, evidence = [], []
    tracked = tracked_files()
    targets = _targets_under(rel, tracked)
    if not targets:
        blockers.append(f'{rel!r} is not tracked by git (or does not exist) -- '
                        f'there is no deletion to make here')
        return blockers, evidence
    evidence.append(f'{len(targets)} tracked file(s) would be deleted')

    dirty = _git('status', '--porcelain', '--', rel).stdout.strip()
    if dirty:
        blockers.append(
            f'{rel!r} has uncommitted changes -- commit or discard them '
            f'first. Git history holds a deleted file forever; it holds '
            f'nothing that was never committed')

    hits, skipped = find_references([rel], exempt)
    for h in hits:
        blockers.append(
            f'{h[0]}:{h[1]} still references {h[2]!r} (by {h[3]}) -- '
            f'repoint or remove it, or declare that file in {REGISTRY}\'s '
            f'exempt_files if it is a historical record: {h[4]}')
    if skipped:
        evidence.append(f'basename search skipped as too generic or '
                        f'ambiguous: {", ".join(sorted(set(skipped)))}')

    for t in targets:
        if t.startswith('.github/workflows/'):
            live = live_workflow_triggers(t)
            if live:
                blockers.append(
                    f'{t} is still live -- its `on:` block carries '
                    f'{", ".join(live)}. Pause it (comment the trigger out, '
                    f'leave workflow_dispatch) and let a cycle pass before '
                    f'retiring it, so the retirement is never the first '
                    f'thing that stops a running job')

    last = _git('log', '-1', '--format=%h %ad %s', '--date=short', '--', rel)
    if last.returncode == 0 and last.stdout.strip():
        evidence.append(f'last touched: {last.stdout.strip()}')
    return blockers, evidence


def apply_retirement(paths, reason, cfg):
    r = _git('rm', '-r', '-q', '--', *paths)
    if r.returncode != 0:
        sys.exit(f'precedent_retire_path: git rm failed ({r.stderr.strip()}) '
                 f'-- nothing was recorded')
    today = datetime.date.today().isoformat()
    for p in paths:
        cfg['retired'].append({'path': p.rstrip('/'), 'reason': reason,
                               'retired_at': today})
    (ROOT / REGISTRY).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / REGISTRY).write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    _git('add', '--', REGISTRY)
    return today


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Audit, then delete, a fully deprecated path.')
    ap.add_argument('paths', nargs='*', help='repo-relative file or directory')
    ap.add_argument('--reason', help='why it is deprecated -- recorded in '
                                     f'{REGISTRY}; required with --apply')
    ap.add_argument('--apply', action='store_true',
                    help='delete and record, only if the audit is clean')
    ap.add_argument('--list', action='store_true',
                    help='print what this repo has already retired')
    args = ap.parse_args(argv)

    cfg = load_registry()
    if args.list:
        if not cfg['retired']:
            print(f'{REGISTRY}: nothing retired yet')
            return 0
        for e in cfg['retired']:
            print(f"{e.get('retired_at', '?')}  {e.get('path')}\n"
                  f"    {e.get('reason', '(no reason recorded)')}")
        return 0
    if not args.paths:
        ap.error('give at least one path to audit, or --list')
    if args.apply and not args.reason:
        ap.error('--apply requires --reason: a retirement whose reason is '
                 'not written down is the record that dies first')

    blocked = False
    for p in args.paths:
        blockers, evidence = audit(p, cfg['exempt_files'])
        print(f'\n=== {p}')
        for e in evidence:
            print(f'  - {e}')
        if blockers:
            blocked = True
            print(f'  REFUSED ({len(blockers)} blocker(s)):')
            for b in blockers:
                print(f'    ! {b}')
        else:
            print('  CLEAR: nothing tracked points at this path any more')

    if blocked:
        print('\nBlocked. Fix what is listed above and run this again; there '
              'is no flag to skip it.')
        return 1
    if not args.apply:
        print(f'\nAudit clean. Re-run with --reason "..." --apply to delete '
              f'and record it in {REGISTRY}.')
        return 0
    today = apply_retirement(args.paths, args.reason, cfg)
    print(f'\nDeleted and recorded in {REGISTRY} ({today}). Commit this '
          f'together with whatever retired the mechanism.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

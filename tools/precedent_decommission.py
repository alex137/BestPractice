#!/usr/bin/env python3
"""precedent_decommission.py — the double-check that has to pass before a
deprecated file or directory is deleted, and the deletion itself.

(practice: decommission-deletes-files)

WHY THIS EXISTS. Decommissioning a mechanism -- a scheduled workflow, a tool, a
vendored tree, a config -- leaves files behind that exist only to serve it.
Nothing forces anyone to delete them, and "leave it, it's harmless" is
always the cheaper answer in the moment, so they accumulate for years until
nobody left can say which of them still do anything. The rule
(practices/decommission-deletes-files.md) is that the files go in the same
change that decommissions the mechanism. This tool is what makes obeying it safe:
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
                 succeeded is how a decommissioning gets recorded as done
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
                 decommissioning must never be the first thing that stops a
                 running job: pause the schedule, let a cycle pass, THEN
                 decommission. Deleting a live workflow means its next failure is
                 silent, and a silent absence is the failure mode this whole
                 practice exists to prevent.
  dirty          A target with uncommitted modifications blocks. Everything
                 else here is recoverable -- git history holds a deleted
                 file forever -- and uncommitted content is the one thing
                 deletion destroys outright.

A reference match is a plain substring on the LEFT, deliberately, so
decommissioning `docs.yml` also blocks on a line naming
`bestpractice-docs.yml`. That is a false positive in the safe direction, and
tightening it to a word boundary would trade a look at one printed line for
the chance of clearing a path something really does point at. The report
prints the matching line for exactly this reason: dismissing a wrong hit
costs a second, and a wrong clear costs a cut dependency.

On the RIGHT the match stops at a name boundary (2026-09-20): a needle
followed by a letter, digit, `_` or `-` is a LONGER name, never a reference
to this one -- `process/legacy` is not named by `process/legacy-tools`,
and a repo that retires the former while adopting the latter would
otherwise be blocked by every mention of its own replacement, with no
exemption that is not a lie (the file genuinely references the new path).
A following `/`, `.`, quote, bracket or end of line still matches, so
`process/legacy/tools` and `process/legacy.` do. Found retiring a vendored
pack tree in favour of a sibling whose name extended the old one: seven
hits, all on the replacement.

The basename pass has one more skip for the same reason (2026-09-20): a
basename that also occurs as a path SEGMENT elsewhere in the tree -- a
directory called `legacy` retired from a repo that keeps
`.claude/skills/legacy/` -- cannot be attributed to the retired path any
more than a duplicated file basename can, and is reported as skipped, not
searched. Before this, only FILE basenames were counted, so a retired
directory's bare-word basename was searched as if it were distinctive and
matched the word across the whole repo (5,606 lines in the origin case).

WHAT IT IS BLIND TO. A reference built by string concatenation at runtime,
a path named only in something this repo does not track (a GitHub branch
protection rule, a webhook, another repo's config), and a file that nothing
references and nothing runs but that someone still needs. The audit proves
no tracked file points at the path; it cannot prove the path is useless.
That judgment stays a person's, which is why the report prints the evidence
rather than only a verdict.

Usage:
  precedent_decommission.py PATH [PATH...]            # audit only, always start here
  precedent_decommission.py PATH --reason "..." --apply
                                                     # git rm + record it
  precedent_decommission.py --list                    # what this repo has decommissioned

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

# practice: one-formatter-per-quantity -- every moment in time this project
# writes down comes from ONE module, in the person's zone, carrying its
# offset. Never a bare datetime.date.today(): that is the container's UTC.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # noqa: E402


REGISTRY = 'process/decommissioned_paths.json'

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
# repo's to repoint. The registry itself names every decommissioned path by
# design -- scanning it would make every decommissioning block on its own record.
SCAN_SKIP_PREFIXES = ('process/upstream/', '.git/')


def _git(*args, cwd=None):
    return subprocess.run(['git', '-C', str(cwd or ROOT), *args],
                          capture_output=True, text=True)


# Resolved lazily, never at import. Doing it at import made `--help` exit 1
# from any directory that is not a git repository -- the harness's own
# "every tool answers --help with exit 0" case caught it immediately, and it
# is the same shape as the failures this tool is written to prevent: a
# dependency checked at the wrong moment, reported as the wrong thing.
ROOT = None


def _require_root():
    global ROOT
    if ROOT is None:
        r = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit('precedent_decommission: not inside a git repository -- '
                     'this tool audits a tracked tree, so there is nothing '
                     'to run it against here')
        ROOT = pathlib.Path(r.stdout.strip())
    return ROOT


def read_registry(root):
    """The decommissioning record at `root`, or an empty one. Raises
    ValueError, with the sentence to print, on a malformed registry -- never
    an empty default: silently treating it as empty would let a typo erase
    every decommissioning this repo has recorded.

    Split out of load_registry() 2026-09-24 so precedent_vendor_engine.py's
    legacy sweep records into the SAME file, in the same shape, through the
    same refusal, instead of a second writer that drifts from this one."""
    p = pathlib.Path(root) / REGISTRY
    if not p.is_file():
        return {'decommissioned': [], 'exempt_files': []}
    try:
        cfg = json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(
            f'{REGISTRY} is not valid JSON ({e}) -- fix it before '
            f'decommissioning anything, or a decommissioning will be recorded '
            f'into a file nothing can read')
    if not isinstance(cfg, dict):
        raise ValueError(f'{REGISTRY} must be a JSON object with a '
                         f'"decommissioned" list, not a {type(cfg).__name__}')
    cfg.setdefault('decommissioned', [])
    cfg.setdefault('exempt_files', [])
    return cfg


def load_registry():
    try:
        return read_registry(ROOT)
    except ValueError as e:
        sys.exit(f'precedent_decommission: {e}')


def record_decommissioned(root, paths, reason, cfg=None):
    """Append one entry per path to <root>/REGISTRY and write it. Deletes
    nothing: the caller has already removed the files (git rm here, a plain
    unlink in a refresh) and this is only the record. -> the date recorded.
    Raises ValueError on a malformed registry, like read_registry."""
    root = pathlib.Path(root)
    if cfg is None:
        cfg = read_registry(root)
    today = precedent_time.today()
    for p in paths:
        cfg['decommissioned'].append({'path': p.rstrip('/'), 'reason': reason,
                                      'decommissioned_at': today})
    (root / REGISTRY).parent.mkdir(parents=True, exist_ok=True)
    (root / REGISTRY).write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return today


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
    expanded rather than judged as one entry: decommissioning `process/personal`
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
    segment_counts = {}
    for f in tracked:
        basename_counts[os.path.basename(f)] = \
            basename_counts.get(os.path.basename(f), 0) + 1
        # Every directory on the way, counted ONCE per distinct directory:
        # a retired directory's own name has to be tested against the rest
        # of the tree the way a file basename is, and files alone never see
        # a directory name.
        parts = f.split('/')[:-1]
        for depth in range(1, len(parts) + 1):
            segment_counts.setdefault('/'.join(parts[:depth]), parts[depth - 1])
    seg_name_counts = {}
    for name in segment_counts.values():
        seg_name_counts[name] = seg_name_counts.get(name, 0) + 1
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
        elif seg_name_counts.get(base, 0) > (1 if base in segment_counts.values() else 0):
            # The same name is a directory somewhere else in the tree (a
            # retired `x/legacy/` beside a kept `y/legacy/`): a hit on the
            # bare name cannot be attributed to this path either.
            skipped.append(base)
        elif base != p:
            needles.append((base, 'basename'))
    return needles, skipped


# A needle followed by a name character is a LONGER name, not a reference
# to this one (module docstring, "On the RIGHT"). `/`, `.`, quotes,
# brackets, whitespace and end of line all still count as a match.
_NAME_CONTINUES = re.compile(r'[A-Za-z0-9_-]')


def _mentions(needle, line):
    start = 0
    while True:
        i = line.find(needle, start)
        if i < 0:
            return False
        end = i + len(needle)
        if end >= len(line) or not _NAME_CONTINUES.match(line[end]):
            return True
        start = i + 1


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
                if _mentions(needle, line):
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
        text = p.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return []
    return live_triggers_in_text(text)


def live_triggers_in_text(text):
    """live_workflow_triggers() for text already in hand -- the same scan,
    so the engine's legacy sweep and a person's audit call a workflow live
    or paused by one definition, not two."""
    lines = text.splitlines()
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


def audit(path, exempt, siblings=()):
    """`siblings` are the OTHER paths being decommissioned in this same invocation.

    They matter because a reference from a file that is itself about to be
    deleted is not a reason to refuse. Decommissioning `process/personal` and
    `process/manifest_personal.json` together, every file in the tree names
    the manifest and the manifest names the tree -- so auditing each path
    alone reported eighteen blockers, all of them mutual references between
    two things going in the same commit, and there was no flag to get past
    it. Found 2026-09-07 doing exactly that decommissioning for real.

    The fix is narrow on purpose: only paths named in THIS invocation are
    forgiven. A reference from a file nobody is deleting still blocks, which
    is the whole point of the audit.
    """

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

    blockers += _dirty_refusal(ROOT, rel)

    # Everything going in this invocation, so a mutual reference between
    # two paths being decommissioned together is not read as a survivor.
    hits, skipped = find_references([rel] + [s.rstrip('/') for s in siblings],
                                    exempt)
    for h in hits:
        blockers.append(
            f'{h[0]}:{h[1]} still references {h[2]!r} (by {h[3]}) -- '
            f'repoint or remove it, or declare that file in {REGISTRY}\'s '
            f'exempt_files if it is a historical record: {h[4]}')
    if skipped:
        evidence.append(f'basename search skipped as too generic or '
                        f'ambiguous: {", ".join(sorted(set(skipped)))}')

    for t in targets:
        blockers += _live_refusal(ROOT, t)

    last = _git('log', '-1', '--format=%h %ad %s', '--date=short', '--', rel)
    if last.returncode == 0 and last.stdout.strip():
        evidence.append(f'last touched: {last.stdout.strip()}')
    return blockers, evidence


def apply_retirement(paths, reason, cfg):
    r = _git('rm', '-r', '-q', '--', *paths)
    if r.returncode != 0:
        sys.exit(f'precedent_decommission: git rm failed ({r.stderr.strip()}) '
                 f'-- nothing was recorded')
    today = record_decommissioned(ROOT, paths, reason, cfg)
    _git('add', '--', REGISTRY)
    return today


def file_refusals(root, rel):
    """The refusals that are about the FILE itself, not about who mentions
    it: untracked, uncommitted edits, a live workflow trigger. -> [sentence].

    audit() runs these plus the reference search. precedent_vendor_engine.py's
    legacy sweep runs only these, and reports references instead of refusing
    on them, the way every other refresh deletion does (its dependents_of):
    in a consuming repo the materialized practices/ and the vendored
    manifests name every retired workflow by design, so a reference refusal
    there would refuse every time and delete nothing. These three are the
    ones deletion can actually get wrong -- content that exists nowhere
    else, and a job that stops with nobody told."""
    root = pathlib.Path(root)
    rel = rel.rstrip('/')
    ls = _git('ls-files', '--error-unmatch', '--', rel, cwd=root)
    if ls.returncode != 0:
        return [f'{rel!r} is not tracked by git -- deleting it would destroy '
                f'the only copy, so it is left for a person to look at']
    return _dirty_refusal(root, rel) + _live_refusal(root, rel)


def _dirty_refusal(root, rel):
    if _git('status', '--porcelain', '--', rel, cwd=root).stdout.strip():
        return [f'{rel!r} has uncommitted changes -- commit or discard them '
                f'first. Git history holds a deleted file forever; it holds '
                f'nothing that was never committed']
    return []


def _live_refusal(root, rel):
    if not rel.startswith('.github/workflows/'):
        return []
    try:
        text = (pathlib.Path(root) / rel).read_text(encoding='utf-8',
                                                    errors='ignore')
    except OSError:
        return []
    live = live_triggers_in_text(text)
    if not live:
        return []
    return [f'{rel} is still live -- its `on:` block carries '
            f'{", ".join(live)}. Pause it (comment the trigger out, '
            f'leave workflow_dispatch) and let a cycle pass before '
            f'decommissioning it, so the decommissioning is never the first '
            f'thing that stops a running job']


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Audit, then delete, a fully deprecated path.')
    ap.add_argument('paths', nargs='*', help='repo-relative file or directory')
    ap.add_argument('--reason', help='why it is deprecated -- recorded in '
                                     f'{REGISTRY}; required with --apply')
    ap.add_argument('--apply', action='store_true',
                    help='delete and record, only if the audit is clean')
    ap.add_argument('--list', action='store_true',
                    help='print what this repo has already decommissioned')
    args = ap.parse_args(argv)

    _require_root()
    cfg = load_registry()
    if args.list:
        if not cfg['decommissioned']:
            print(f'{REGISTRY}: nothing decommissioned yet')
            return 0
        for e in cfg['decommissioned']:
            print(f"{e.get('decommissioned_at', '?')}  {e.get('path')}\n"
                  f"    {e.get('reason', '(no reason recorded)')}")
        return 0
    if not args.paths:
        ap.error('give at least one path to audit, or --list')
    if args.apply and not args.reason:
        ap.error('--apply requires --reason: a decommissioning whose reason is '
                 'not written down is the record that dies first')

    blocked = False
    for p in args.paths:
        others = [q for q in args.paths if q != p]
        blockers, evidence = audit(p, cfg['exempt_files'], siblings=others)
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
          f'together with whatever decommissioned the mechanism.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

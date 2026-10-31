#!/usr/bin/env python3
"""Every test a repository runs, with what it costs and whether it still
earns that -- the very deep check's TEST WORTH section (practice:
very-deep-check, Pass 2's question 27).

WHY THIS EXISTS. Tests are added one at a time, each for a real reason, and
nothing ever asked the reverse question: is this one still worth running?
On 2026-10-17 the harness still carried dozens of tests about the tier below
staging three days after that tier was retired for everyone. Each still
passed, each still cost time on every full run, and none protected anything
a person still used. Morgan, 2026-10-17 (strength: decided): "review all
TESTS to see if all tests are relevant and important. Do they test something
still used and needed? Was what it tests deprecated? ... does the amount of
time it takes worth it for its level of importance?"

WHAT IT DOES. inventory() lists every test the repository owns: each
`check_*` function in its own tools/verify_harness.py, with the seconds
tools/harness_check_times.json records for it, and every tracked test script
(test_*.sh / test_*.py under a tests/ directory, or named test_* anywhere),
with the seconds that repo's tools/script_test_times.json records for it.
A file the vendored-engine manifest lists is upstream's, judged there. For
each test it reads LEADS from the test's own source: a retired thing it
names (this registry's `retired` list, tools/our_language.json's retired
words, a decommissioned tools/ path, a retired or deduplicated practice),
or a harness test with no recorded time. (A tools/ file the test names that
is not in the tree was tried as a lead and dropped the same day: nearly every
one is a fixture the test plants, tools/x.py and the like.) A lead is a question for the session, never a verdict: a test
OF a retirement names the retired thing on purpose.

WHO DECIDES. The session running the check, test by test, slowest first:
  keep     -- it protects something still used; `importance` says how much
              (high: work lost, leaked, landed in the wrong place or a
              session blocked; medium: a mechanism quietly wrong; low:
              wording, formatting, a convenience), and the time is worth it.
  cheapen  -- worth keeping, not at this price: make it cheaper in this pass,
              then record it as keep with its new time.
  retire   -- what it tests is gone, retired, or covered by another test:
              delete it in this pass (practice: decommission-deletes-files).
It records `"by": "agent"`, and asks the person only where it is genuinely
unsure or suspects they would see it differently (practice:
decision-strength). Verdicts live in tools/test_verdicts.json, so a later run
judges only what is new or changed: a test with no verdict, a keep whose
time has more than doubled (and grown by a second or more), or a keep that
now carries a lead it did not have when judged.

IT REPORTS AND NEVER REFUSES. Nothing here is a gate.

  python3 tools/test_review.py             # the review, as text
  python3 tools/test_review.py --all       # every test still to judge, not the first 40
  python3 tools/test_review.py --markdown  # the `## Test review` block
  python3 tools/test_review.py --json      # every test, for a tool
  python3 tools/test_review.py --repo PATH # another repository in force,
                                           # read against this one's retired list too
  python3 tools/test_review.py --time-scripts [--repo PATH]
      # run each test script once and record what it took

SCRIPT TIMES (2026-10-31). Nothing recorded a test script's time, so every
script read as untimed, a set's totals said "0 timed", and the rule that
judges a keep again when its time more than doubled could never fire for a
script. --time-scripts runs each test script inventory() lists once, from
the repository's root (bash for .sh, python3 for .py, SCRIPT_TIMEOUT each),
and rewrites that repository's tools/script_test_times.json with the
seconds of the ones that passed; a script that failed or timed out is
named and left out, never recorded. Exit 1 when one did. The harness's
writer for tools/harness_check_times.json was not shared: its record
carries what only --as-ci's deal needs (default_seconds, green_full_run).
Both files are read by the one reader below, _read_times.
"""
import ast
import json
import pathlib
import re
import os
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_RELPATH = 'tools/test_verdicts.json'
TIMES_RELPATH = 'tools/harness_check_times.json'
SCRIPT_TIMES_RELPATH = 'tools/script_test_times.json'
SCRIPT_TIMEOUT = 600
# This tool's own file matches test_*.py and is not a test.
SELF_RELPATH = 'tools/test_review.py'
HARNESS_RELPATH = 'tools/verify_harness.py'
VERDICTS = ('keep', 'cheapen', 'retire')
IMPORTANCE = ('high', 'medium', 'low')
ENTRY_KEYS = {'verdict', 'importance', 'why', 'date', 'by', 'strength',
              'seconds', 'leads'}
DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}$')
# A keep is judged again when its time has more than doubled AND grown by
# at least this many seconds: a 0.1 s test that becomes 0.3 s is noise.
REJUDGE_GROWTH = 2.0
REJUDGE_MIN_SECONDS = 1.0
SHOWN = 40


def _git_files(root):
    try:
        out = subprocess.run(['git', '-C', str(root), 'ls-files'],
                             capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [l for l in out.splitlines() if l]


def _vendored(root):
    """-> the tools/ paths the vendored-engine manifest lists: upstream's
    files, whose tests are judged upstream."""
    try:
        m = json.loads((root / 'tools' / 'ENGINE_MANIFEST.json')
                       .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return set()
    return {f'tools/{f}' for f in (m.get('files') or []) if isinstance(f, str)}


def _first_line(text):
    text = ' '.join((text or '').strip().split())
    m = re.match(r'(.{0,160}?[.!?])(\s|$)', text)
    return (m.group(1) if m else text[:160]).strip()


def _script_about(text):
    """-> the first comment sentence of a test script, past the shebang."""
    lines = []
    for l in text.splitlines()[1:40]:
        s = l.strip()
        if s.startswith('#') and not s.startswith('#!'):
            body = s.lstrip('#').strip()
            if body:
                lines.append(body)
            elif lines:
                break
        elif lines or (s and not s.startswith('#')):
            break
    return _first_line(' '.join(lines))


def _read_times(path):
    """-> ({test name: seconds}, measured) from a times record, either
    tools/harness_check_times.json or tools/script_test_times.json;
    ({}, '') when it is missing or unreadable."""
    try:
        rec = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
        times = rec.get('seconds') or {}
        measured = str(rec.get('measured') or '')
    except (OSError, ValueError, AttributeError):
        return {}, ''
    if not isinstance(times, dict):
        return {}, ''
    return ({k: float(v) for k, v in times.items()
             if isinstance(v, (int, float)) and not isinstance(v, bool)},
            measured)


def inventory(root):
    """-> [test]: {name, kind, file, line, seconds, about, source} for every
    test `root` owns. `seconds` is None where nothing records one."""
    root = pathlib.Path(root)
    vendored = _vendored(root)
    tests = []
    harness = root / HARNESS_RELPATH
    if harness.is_file() and HARNESS_RELPATH not in vendored:
        times, measured = _read_times(root / TIMES_RELPATH)
        text = harness.read_text(encoding='utf-8')
        lines = text.splitlines()
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        for node in (tree.body if tree else []):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('check_'):
                t = times.get(node.name)
                # By line range: ast.get_source_segment rescans the whole
                # file per call, minutes over the harness's 700-odd tests.
                tests.append({
                    'name': node.name, 'kind': 'harness', 'measured': measured,
                    'file': HARNESS_RELPATH, 'line': node.lineno,
                    'seconds': t,
                    'about': _first_line(ast.get_docstring(node) or ''),
                    'source': '\n'.join(lines[node.lineno - 1:node.end_lineno])})
    script_times, script_measured = _read_times(root / SCRIPT_TIMES_RELPATH)
    for rel in _git_files(root):
        p = pathlib.PurePosixPath(rel)
        if rel in vendored or rel == SELF_RELPATH or p.parts[0] == 'templates':
            continue
        if not (p.name.startswith('test_') and p.suffix in ('.sh', '.py')):
            continue
        try:
            text = (root / rel).read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        tests.append({'name': rel, 'kind': 'script', 'file': rel, 'line': 1,
                      'seconds': script_times.get(rel),
                      'measured': script_measured if rel in script_times else '',
                      'about': (_first_line(ast.get_docstring(ast.parse(text)) or '')
                                if p.suffix == '.py' and _parses(text)
                                else _script_about(text)),
                      'source': text})
    return tests


def _parses(text):
    try:
        ast.parse(text)
        return True
    except SyntaxError:
        return False


def load_registry(root):
    """-> (registry dict, [problem]). A missing registry is an empty one: a
    repository starts without it."""
    path = pathlib.Path(root) / REGISTRY_RELPATH
    if not path.is_file():
        return {'retired': [], 'verdicts': {}}, []
    try:
        reg = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as e:
        return {'retired': [], 'verdicts': {}}, [f'{REGISTRY_RELPATH} does not parse: {e}']
    problems = []
    verdicts = reg.get('verdicts') if isinstance(reg, dict) else None
    if not isinstance(verdicts, dict):
        return {'retired': [], 'verdicts': {}}, [
            f'{REGISTRY_RELPATH} needs a "verdicts" object, test name -> verdict']
    # A malformed verdict is a problem and is not applied: the test stays
    # unjudged until its entry is fixed.
    valid = {}
    for name, e in verdicts.items():
        if not isinstance(e, dict):
            problems.append(f'{name}: a verdict is an object')
            continue
        mine = []
        bad = set(e) - ENTRY_KEYS
        if bad:
            mine.append(f'{name}: unknown key(s) {", ".join(sorted(bad))}')
        if e.get('verdict') not in VERDICTS:
            mine.append(f'{name}: verdict must be one of {", ".join(VERDICTS)}')
        if e.get('verdict') == 'keep' and e.get('importance') not in IMPORTANCE:
            mine.append(f'{name}: a keep says its importance '
                        f'({", ".join(IMPORTANCE)})')
        if not str(e.get('why') or '').strip():
            mine.append(f'{name}: no why')
        if not DATE_RE.match(str(e.get('date') or '')):
            mine.append(f'{name}: date must be YYYY-MM-DD')
        problems += mine
        if not mine:
            valid[name] = e
    retired = reg.get('retired') or []
    if not isinstance(retired, list):
        problems.append(f'{REGISTRY_RELPATH}: "retired" is a list')
        retired = []
    return {'retired': retired, 'verdicts': valid}, problems


def retired_patterns(root, registry):
    """-> [(label, compiled pattern)]: every retired thing a test may name."""
    root = pathlib.Path(root)
    out = []

    def add(label, pat):
        try:
            out.append((label, re.compile(pat, re.I)))
        except re.error:
            pass
    for r in registry.get('retired') or []:
        if isinstance(r, dict):
            for pat in r.get('patterns') or []:
                add(f'{r.get("what")} (retired {r.get("retired")})', pat)
    try:
        ol = json.loads((root / 'tools' / 'our_language.json').read_text(encoding='utf-8'))
        for r in ol.get('retired') or []:
            for pat in r.get('patterns') or []:
                add(f'the word {r.get("word")!r} (retired {r.get("retired")})', pat)
    except (OSError, ValueError, AttributeError):
        pass
    try:
        dp = json.loads((root / 'process' / 'decommissioned_paths.json')
                        .read_text(encoding='utf-8'))
        for e in dp.get('decommissioned') or []:
            path = str(e.get('path') or '')
            if path.startswith('tools/') and not (root / path).exists():
                add(f'{path} (decommissioned)',
                    r'(?<![\w/.-])' + re.escape(pathlib.PurePosixPath(path).name) + r'(?![\w-])')
    except (OSError, ValueError, AttributeError):
        pass
    for f in sorted((root / 'practices').glob('*.md')):
        head = f.read_text(encoding='utf-8', errors='ignore')[:1500]
        m = re.search(r'^status:\s*(retired|deduplicated)\b', head, re.M)
        if m:
            add(f'practice {f.stem} ({m.group(1)})',
                r'practices/' + re.escape(f.stem) + r'\.md')
    return out


def leads(test, patterns):
    """-> [str]: what in `test` the session should look at before keeping it."""
    src = test['source']
    out = []
    for label, pat in patterns:
        if pat.search(src):
            out.append(f'names {label}')
    if test['kind'] == 'harness' and test['seconds'] is None:
        out.append('no recorded time (python3 tools/verify_harness.py --record-new-times)')
    return sorted(set(out))


def review(root, also=()):
    """-> {'tests': [...], 'stale': [...], 'problems': [...], 'totals': {...}}.
    Each test gains `leads`, `entry` and `status`: judged, unjudged,
    rejudge (a keep whose time or leads changed), or owed (cheapen or
    retire, not yet done).

    `also`: other repositories whose retired things count here too -- the
    one running the check. A practice set keeps no list of its own, so
    without this its tests were never read against what BestPractice
    retired: a set's test still about pre-staging went unflagged (Morgan,
    2026-10-18, strength: decided)."""
    root = pathlib.Path(root)
    registry, problems = load_registry(root)
    patterns = retired_patterns(root, registry)
    seen = {label for label, _p in patterns}
    for other in also:
        other = pathlib.Path(other)
        if other.resolve() == root.resolve():
            continue
        for label, pat in retired_patterns(other, load_registry(other)[0]):
            if label not in seen:
                seen.add(label)
                patterns.append((label, pat))
    tests = inventory(root)
    verdicts = registry['verdicts']
    for t in tests:
        t['leads'] = leads(t, patterns)
        e = verdicts.get(t['name'])
        t['entry'] = e if isinstance(e, dict) else None
        if not t['entry']:
            t['status'] = 'unjudged'
        elif t['entry'].get('verdict') in ('cheapen', 'retire'):
            t['status'] = 'owed'
        else:
            was = t['entry'].get('seconds')
            now = t['seconds']
            grew = (isinstance(was, (int, float)) and now is not None
                    and now > was * REJUDGE_GROWTH
                    and now - was >= REJUDGE_MIN_SECONDS)
            new_leads = set(t['leads']) - set(t['entry'].get('leads') or [])
            t['status'] = 'rejudge' if grew or new_leads else 'judged'
            t['why_rejudge'] = (['its time more than doubled, from '
                                 f'{was:.1f} s to {now:.1f} s'] if grew else []) + \
                               [f'a new lead: {l}' for l in sorted(new_leads)]
    names = {t['name'] for t in tests}
    stale = sorted(n for n in verdicts if n not in names)
    secs = lambda ts: sum(t['seconds'] or 0 for t in ts)
    by_importance = {}
    for t in tests:
        k = (t['entry'] or {}).get('importance') if t['status'] in ('judged', 'rejudge') else None
        k = k or 'not judged yet'
        n, s = by_importance.get(k, (0, 0.0))
        by_importance[k] = (n + 1, s + (t['seconds'] or 0))
    totals = {'tests': len(tests), 'seconds': secs(tests),
              'measured': next((t['measured'] for t in tests if t.get('measured')), ''),
              'timed': sum(1 for t in tests if t['seconds'] is not None),
              'by_status': {s: sum(1 for t in tests if t['status'] == s)
                            for s in ('judged', 'unjudged', 'rejudge', 'owed')},
              'with_leads': sum(1 for t in tests if t['leads']),
              'by_importance': by_importance}
    return {'tests': tests, 'stale': stale, 'problems': problems,
            'totals': totals}


def to_judge(result):
    """-> the tests a session judges this run: leads first, then slowest."""
    open_ = [t for t in result['tests'] if t['status'] in ('unjudged', 'rejudge', 'owed')]
    return sorted(open_, key=lambda t: (not t['leads'], -(t['seconds'] or 0), t['name']))


def _secs(s):
    return 'untimed' if s is None else f'{s:.1f} s'


def render_text(result, show_all=False, label=''):
    tt = result['totals']
    st = tt['by_status']
    lines = [f'  {label}{tt["tests"]} test(s), {tt["timed"]} timed, '
             f'{tt["seconds"]:.0f} s recorded in all. Judged {st["judged"]}; '
             f'to judge: {st["unjudged"]} never judged, {st["rejudge"]} to judge '
             f'again, {st["owed"]} cheapen/retire owed. {tt["with_leads"]} carry a lead.'
             + (f' Times measured {tt["measured"]}.' if tt.get('measured') else '')]
    imp = tt['by_importance']
    if imp:
        lines.append('  TIME BY IMPORTANCE: ' + '; '.join(
            f'{k} {n} test(s), {s:.0f} s' for k, (n, s) in
            sorted(imp.items(), key=lambda kv: (IMPORTANCE + ('not judged yet',)).index(kv[0])
                   if kv[0] in IMPORTANCE + ('not judged yet',) else 9)))
    for p in result['problems']:
        lines.append(f'  REGISTRY: {p}')
    if result['stale']:
        lines.append(f'  STALE VERDICTS ({len(result["stale"])}), for tests that no '
                     f'longer exist -- delete them from {REGISTRY_RELPATH}: '
                     + ', '.join(result['stale']))
    todo = to_judge(result)
    shown = todo if show_all else todo[:SHOWN]
    if todo:
        lines.append(f'  TO JUDGE ({len(todo)}), leads first, then slowest: keep '
                     f'(with importance), cheapen, or retire.')
    for t in shown:
        e = t['entry'] or {}
        tag = {'unjudged': 'new', 'rejudge': 'again', 'owed': e.get('verdict', '')}[t['status']]
        lines.append(f'    [{tag}] {t["name"]}  {_secs(t["seconds"])}  '
                     f'{t["file"]}:{t["line"]}')
        if t['about']:
            lines.append(f'        {t["about"]}')
        for l in t['leads'] + t.get('why_rejudge', []):
            lines.append(f'        lead: {l}')
    if len(todo) > len(shown):
        lines.append(f'    ... and {len(todo) - len(shown)} more: python3 '
                     f'tools/test_review.py --all')
    if not todo:
        lines.append('  Every test carries a current verdict.')
    return '\n'.join(lines)


def render_markdown(results):
    """-> the `## Test review` block for [(repo label, review())]."""
    md = ['Every test each repository owns, what it costs and whether it is '
          'still worth that (`tools/very_deep_check.py`, TEST WORTH; '
          '[test_review.py](../tools/test_review.py)). Verdicts live in each '
          'repository\'s `tools/test_verdicts.json`.', '']
    for label, r in results:
        tt = r['totals']
        st = tt['by_status']
        md += [f'### {label}', '',
               f'{tt["tests"]} test(s), {tt["timed"]} timed, '
               f'{tt["seconds"]:.0f} s recorded in all. Judged: {st["judged"]}. '
               f'Never judged: {st["unjudged"]}. To judge again: {st["rejudge"]}. '
               f'Cheapen or retire owed: {st["owed"]}. Carrying a lead: '
               f'{tt["with_leads"]}.'
               + (f' Times measured {tt["measured"]}.' if tt.get('measured') else ''),
               '']
        if tt['by_importance']:
            md += ['| Importance | Tests | Seconds |', '|---|---:|---:|']
            for k in IMPORTANCE + ('not judged yet',):
                if k in tt['by_importance']:
                    n, s = tt['by_importance'][k]
                    md.append(f'| {k} | {n} | {s:.0f} |')
            md.append('')
        slow = sorted((t for t in r['tests'] if t['seconds']),
                      key=lambda t: -t['seconds'])[:15]
        if slow:
            md += ['The slowest, against their importance:', '',
                   '| Test | Seconds | Verdict | Importance |', '|---|---:|---|---|']
            for t in slow:
                e = t['entry'] or {}
                md.append(f'| `{t["name"]}` | {t["seconds"]:.1f} | '
                          f'{e.get("verdict") or "not judged"} | '
                          f'{e.get("importance") or "-"} |')
            md.append('')
        owed = [t for t in r['tests'] if t['status'] == 'owed']
        if owed:
            md += ['Owed in this pass:', ''] + [
                f'- `{t["name"]}`: {t["entry"]["verdict"]} -- {t["entry"].get("why")}'
                for t in owed] + ['']
        led = [t for t in r['tests'] if t['leads'] and t['status'] != 'judged']
        if led:
            md += [f'Carrying a lead and not yet judged ({len(led)}):', ''] + [
                f'- `{t["name"]}`: ' + '; '.join(t['leads']) for t in led[:25]]
            if len(led) > 25:
                md.append(f'- and {len(led) - 25} more')
            md.append('')
        if r['stale']:
            md += [f'Stale verdicts to delete: {len(r["stale"])}.', '']
        if r['problems']:
            md += ['Registry problems:', ''] + [f'- {p}' for p in r['problems']] + ['']
    return '\n'.join(md).rstrip('\n')


def _today(root):
    try:
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_time
        return precedent_time.today(root)
    except Exception:  # noqa: BLE001 -- a date from the container beats none
        return time.strftime('%Y-%m-%d')


def time_scripts(root, timeout=SCRIPT_TIMEOUT, out=print):
    """--time-scripts: run every test script inventory() lists for `root`
    once, from its root, and rewrite its tools/script_test_times.json with
    the seconds of each that passed. -> [(script, why)] for the ones that
    failed or timed out, which are not recorded."""
    root = pathlib.Path(root)
    scripts = [t['name'] for t in inventory(root) if t['kind'] == 'script']
    seconds, failed = {}, []
    for rel in scripts:
        cmd = ['bash', rel] if rel.endswith('.sh') else [sys.executable, rel]
        start = time.monotonic()
        try:
            p = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, timeout=timeout)
            why = '' if p.returncode == 0 else f'exit {p.returncode}'
            tail = (p.stdout + p.stderr).strip().splitlines()[-1:] if why else []
        except subprocess.TimeoutExpired:
            why, tail = f'timed out after {timeout} s', []
        took = round(time.monotonic() - start, 1)
        if why:
            failed.append((rel, why))
            out(f'  FAILED  {took:6.1f} s  {rel} ({why}; not recorded)'
                + (f': {tail[0][:200]}' if tail else ''))
        else:
            seconds[rel] = took
            out(f'  passed  {took:6.1f} s  {rel}')
    rec = {'_comment': [
               'What each test script took, read by tools/test_review.py for '
               'the very deep check\'s test review (question 27).',
               'Rewrite with: python3 tools/test_review.py --time-scripts '
               '--repo <this repo>. Only scripts that passed are recorded.'],
           'measured': f'{_today(root)}, {os.cpu_count() or 1} cores',
           'seconds': dict(sorted(seconds.items()))}
    (root / SCRIPT_TIMES_RELPATH).parent.mkdir(parents=True, exist_ok=True)
    (root / SCRIPT_TIMES_RELPATH).write_text(json.dumps(rec, indent=1) + '\n',
                                             encoding='utf-8')
    out(f'{len(seconds)} of {len(scripts)} script(s) timed, written to '
        f'{SCRIPT_TIMES_RELPATH}' + (f'; {len(failed)} failed and are not '
                                     'recorded' if failed else ''))
    return failed


def main(argv):
    if '-h' in argv or '--help' in argv:
        print(__doc__.strip())
        return 0
    root = ROOT
    if '--repo' in argv:
        i = argv.index('--repo')
        root = pathlib.Path(argv[i + 1]).resolve()
    if '--time-scripts' in argv:
        return 1 if time_scripts(root) else 0
    result = review(root, also=(ROOT,))
    if '--json' in argv:
        for t in result['tests']:
            t.pop('source', None)
        print(json.dumps(result, indent=1))
    elif '--markdown' in argv:
        print(render_markdown([(root.name, result)]))
    else:
        print(render_text(result, show_all='--all' in argv))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

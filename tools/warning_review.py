#!/usr/bin/env python3
"""Every warning the routine checks print, gathered, matched against the
exclusions a session decided on, and counted -- the very deep check's
WARNINGS section (practice: very-deep-check).

WHY THIS EXISTS. A warning is the class of finding nothing gates on, so
nothing ever reads it twice: doc_lint's warning classes, a check registered
advisory, a tool's `WARNING:` line, a session-check row it could not
determine. Each was built to be seen in passing and then, by design, let
through. Left alone they pile up until the next one is invisible behind the
ones before it. Morgan, 2026-10-11 (strength: decided): "with the checks
that we do that are not urgent ... I like reviewing warnings to see if we
can get rid of them or explicitly exclude them and so on to over time
eliminate warnings."

WHAT IT DOES. collect() runs each source in the repo being checked, using
that repo's own copy of the tool, and reduces what it prints to GROUPS: one
kind of warning in one file (doc_lint's class and file, an advisory check's
slug and file) or one distinct line (a tool's WARNING line, digits folded).
A group is the unit a session judges -- 2,000 unlinked references in 360
files are 360 calls, not 2,000. review() matches every group against
tools/warning_exclusions.json and says, for each, whether it is open,
excluded for good, excluded until a date, or excluded until a date that has
passed (lapsed, which is open again).

WHO DECIDES. The session running the check, not the person: it fixes a
group or excludes it, permanent or temporary, with a reason, and records
`"by": "agent"`. It asks the person only where it is genuinely unsure, the
call is ambiguous, or it suspects they would see it differently -- and then
records their answer with their name and the strength of it (practice:
decision-strength). Asking about every one was rejected by name: it would
add a lot of time and frustration to the very deep check.

IT REPORTS AND NEVER REFUSES. Nothing here is a gate, and nothing may wire
it into one: a warning class promoted to a gate was built and withdrawn
within an hour on 2026-09-21, having refused a one-line edit over 111
warnings that predated it.

  python3 tools/warning_review.py             # the review, as text
  python3 tools/warning_review.py --markdown  # the block the run record embeds
  python3 tools/warning_review.py --json      # every group, for a tool
"""
import fnmatch
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTRY_RELPATH = 'tools/warning_exclusions.json'
TERMS = {'permanent': ('why',), 'temporary': ('why', 'revisit')}
ENTRY_KEYS = {'source', 'kind', 'path', 'match', 'term', 'why', 'revisit',
              'decided', 'by', 'strength'}
DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}$')

# The tools whose own output carries warning LINES, and how each marks one.
# Each runs in the repo being checked, from that repo's own tools/, and is
# cheap (seconds): doc_lint and precedent_check have collectors of their own
# below because their warnings are structured, not lines.
LINE_SOURCES = (
    ('build_views', 'WARNING', ['tools/build_views.py', '--check'],
     re.compile(r'\bWARNING:\s*(.+)')),
    ('model_audit', 'WARNING', ['tools/model_audit.py'],
     re.compile(r'^WARN:\s*(.+)')),
    ('doc_lifecycle', 'WARNING', ['tools/doc_lifecycle.py', '--warn-only'],
     re.compile(r'^\s*WARN(?:ING)?:\s*(.+)')),
    # `??` is the session check's own word for a guarantee it could not
    # determine: not a failure, and not a pass either.
    ('precedent_session_check', 'undetermined',
     ['tools/precedent_session_check.py'], re.compile(r'^\s*\?\?\s+(.+)')),
)


def _run(repo_root, argv, timeout):
    script = pathlib.Path(repo_root) / argv[0]
    if not script.is_file():
        return None, f'no {argv[0]} here'
    try:
        r = subprocess.run([sys.executable, str(script)] + argv[1:],
                           cwd=str(repo_root), capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f'{argv[0]} did not finish in {timeout}s'
    return (r.stdout or '') + (r.stderr or ''), None


def _fold(text):
    """Digits folded, so `3 files` and `4 files` are the same warning."""
    return re.sub(r'\d[\d,.]*', 'N', text.strip())


def doc_lint_groups(output):
    """-> list of groups from `doc_lint.py --strict --all --json` output, or
    None when the line is missing (an engine older than --json)."""
    for line in output.splitlines():
        if line.startswith('doc_lint strict json: '):
            data = json.loads(line.split(': ', 1)[1])
            return [{'source': 'doc_lint', 'kind': kind, 'path': path,
                     'text': '', 'count': n}
                    for kind, files in sorted(data.get('classes', {}).items())
                    for path, n in sorted(files.items())]
    return None


def precedent_check_groups(output):
    """-> groups from precedent_check.py output: every ADVISORY finding, and
    every COULD NOT VERIFY one, grouped by check and file."""
    groups = {}
    current = None
    for line in output.splitlines():
        m = re.match(r'^(ADVISORY|COULD NOT VERIFY)\s+(\S+)', line)
        if m:
            current = (m.group(2) if m.group(1) == 'ADVISORY'
                       else f'{m.group(2)} (could not verify)')
            continue
        if current and line.startswith('    '):
            finding = line.strip()
            path = finding.split(':', 1)[0].strip() if ':' in finding else ''
            key = (current, path)
            g = groups.setdefault(key, {'source': 'precedent_check',
                                        'kind': current, 'path': path,
                                        'text': finding, 'count': 0})
            g['count'] += 1
        elif current and not line.startswith('    '):
            current = None
    return list(groups.values())


def line_groups(name, kind, output, pattern):
    groups = {}
    for line in output.splitlines():
        m = pattern.search(line)
        if not m:
            continue
        text = _fold(m.group(1))
        g = groups.setdefault(text, {'source': name, 'kind': kind,
                                     'path': '', 'text': text, 'count': 0})
        g['count'] += 1
    return list(groups.values())


def collect(repo_root, precedent_check_output=None, timeout=600):
    """-> (groups, collected_sources, notes). `precedent_check_output` is a
    `precedent_check.py --full-sweep` run the caller already made in this
    repo; the very deep check's CHECK COVERAGE makes exactly that run, and
    paying for it twice would be the cost the component ledger exists to
    catch."""
    groups, collected, notes = [], [], []
    out, err = _run(repo_root, ['tools/doc_lint.py', '--strict', '--all',
                                '--json'], timeout)
    found = doc_lint_groups(out) if out is not None else None
    if found is None:
        notes.append(f'doc_lint: not read -- {err or "no --json line; its engine predates it"}')
    else:
        groups += found
        collected.append('doc_lint')
    if precedent_check_output is None:
        precedent_check_output, err = _run(
            repo_root, ['tools/precedent_check.py', '--full-sweep'], timeout)
    if precedent_check_output is None:
        notes.append(f'precedent_check: not read -- {err}')
    else:
        groups += precedent_check_groups(precedent_check_output)
        collected.append('precedent_check')
    for name, kind, argv, pattern in LINE_SOURCES:
        out, err = _run(repo_root, argv, timeout)
        if out is None:
            notes.append(f'{name}: not read -- {err}')
            continue
        groups += line_groups(name, kind, out, pattern)
        collected.append(name)
    return groups, collected, notes


def load_registry(repo_root):
    """-> (entries, problems). A malformed entry is a problem and is not
    applied: an exclusion nobody can read the reason for is not one."""
    path = pathlib.Path(repo_root) / REGISTRY_RELPATH
    if not path.is_file():
        return [], []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as e:
        return [], [f'{REGISTRY_RELPATH} is not valid JSON: {e}']
    entries, problems = [], []
    for i, e in enumerate(data.get('exclusions', [])):
        where = f'{REGISTRY_RELPATH} exclusion {i + 1}'
        if not isinstance(e, dict):
            problems.append(f'{where} is not an object')
            continue
        extra = set(e) - ENTRY_KEYS
        term = e.get('term')
        missing = [k for k in ('source', 'kind', 'term', 'decided', 'by')
                   if not str(e.get(k) or '').strip()]
        if term in TERMS:
            missing += [k for k in TERMS[term] if not str(e.get(k) or '').strip()]
        if extra:
            problems.append(f'{where} has unknown key(s) {sorted(extra)}')
        elif missing:
            problems.append(f'{where} is missing {", ".join(missing)}')
        elif term not in TERMS:
            problems.append(f'{where}: term {term!r} is neither permanent '
                            f'nor temporary')
        elif not DATE_RE.match(str(e['decided'])):
            problems.append(f'{where}: decided {e["decided"]!r} is not YYYY-MM-DD')
        elif term == 'temporary' and not DATE_RE.match(str(e['revisit'])):
            problems.append(f'{where}: revisit {e["revisit"]!r} is not YYYY-MM-DD')
        elif e['by'] != 'agent' and e.get('strength') not in ('decided', 'assented'):
            problems.append(f'{where}: a person\'s exclusion records the '
                            f'strength of it, decided or assented '
                            f'(practice: decision-strength)')
        else:
            entries.append(dict(e, _index=i + 1))
    return entries, problems


def _matches(entry, group):
    return (entry['source'] == group['source']
            and entry['kind'] == group['kind']
            and fnmatch.fnmatchcase(group['path'], entry.get('path') or '*')
            and (not entry.get('match') or entry['match'] in group['text']))


def review(groups, entries, collected, today=None):
    """-> dict: every group with its status, the totals, and the exclusions
    that matched nothing. Pure, so the harness can hand it planted groups and
    a fixed date (practice: fixture-owns-its-state)."""
    if today is None:
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_time  # practice: timestamps-carry-offset
        today = precedent_time.today()
    used = set()
    rows = []
    for g in groups:
        hit = next((e for e in entries if _matches(e, g)), None)
        if hit is None:
            status = 'open'
        else:
            used.add(hit['_index'])
            if hit['term'] == 'permanent':
                status = 'excluded, permanent'
            elif str(hit['revisit']) <= today:
                status = 'lapsed'
            else:
                status = 'excluded, temporary'
        rows.append(dict(g, status=status, exclusion=hit))
    totals = {}
    for r in rows:
        totals[r['status']] = totals.get(r['status'], 0) + r['count']
    # Only a source that was actually read can prove an exclusion stale: one
    # that failed to run matched nothing because nothing was looked at.
    stale = [e for e in entries
             if e['_index'] not in used and e['source'] in collected]
    return {'rows': rows, 'totals': totals, 'stale': stale, 'today': today}


def _open(rows):
    return [r for r in rows if r['status'] in ('open', 'lapsed')]


def render_text(result, problems, notes, previous=None, limit=40):
    rows, totals = result['rows'], result['totals']
    seen = sum(totals.values())
    out = []
    open_rows = _open(rows)
    n_open = sum(r['count'] for r in open_rows)
    out.append(f'{seen} warning(s) in {len(rows)} group(s): {n_open} open '
               f'in {len(open_rows)} group(s), '
               f'{totals.get("excluded, permanent", 0)} excluded for good, '
               f'{totals.get("excluded, temporary", 0)} excluded until a date, '
               f'{totals.get("lapsed", 0)} of them past that date.')
    if previous is not None:
        out.append(f'Open at the previous run: {previous}; now: {n_open}.')
    else:
        out.append('No earlier run recorded an open count, so there is '
                   'nothing to compare with yet.')
    for n in notes:
        out.append(f'note: {n}')
    for p in problems:
        out.append(f'REGISTRY: {p}')
    for e in result['stale']:
        out.append(f'STALE EXCLUSION {e["_index"]}: {e["source"]} / '
                   f'{e["kind"]} / {e.get("path") or "*"} matches nothing '
                   f'now -- the warning is gone; delete the entry.')
    if open_rows:
        out.append('')
        out.append('Open groups, most warnings first -- fix each, or exclude '
                   'it with a reason:')
        for r in sorted(open_rows, key=lambda r: (-r['count'], r['source'],
                                                  r['kind'], r['path']))[:limit]:
            what = r['path'] or r['text']
            lapsed = ' (exclusion lapsed)' if r['status'] == 'lapsed' else ''
            out.append(f'  {r["count"]:5d}  {r["source"]} / {r["kind"]} / '
                       f'{what}{lapsed}')
        if len(open_rows) > limit:
            out.append(f'  ... and {len(open_rows) - limit} more group(s); '
                       f'--json lists every one.')
    return '\n'.join(out)


def render_markdown(result, problems, notes, previous=None, start=None,
                    to_root='../', repo_root=None):
    """The block the run record embeds: what the run saw, what it decided,
    and what is left -- by source and kind, never every file, so the record
    stays readable at 2,000 warnings."""
    rows, today = result['rows'], result['today']
    open_rows = _open(rows)
    n_open = sum(r['count'] for r in open_rows)
    seen = sum(r['count'] for r in rows)
    lines = [f'Measured {today}: **{seen} warning(s), {n_open} still open** '
             f'(neither fixed nor excluded).']
    trail = []
    if previous is not None:
        trail.append(f'open at the previous run: {previous}')
    if start is not None:
        trail.append(f'open when this run started: {start}')
    if trail:
        lines[0] += ' For comparison, ' + '; '.join(trail) + '.'
    lines += ['', '| Source | Kind | Warnings | Open | Excluded for good | '
              'Excluded until a date |', '|---|---|---|---|---|---|']
    by = {}
    for r in rows:
        k = (r['source'], r['kind'])
        b = by.setdefault(k, [0, 0, 0, 0])
        b[0] += r['count']
        b[1] += r['count'] if r['status'] in ('open', 'lapsed') else 0
        b[2] += r['count'] if r['status'] == 'excluded, permanent' else 0
        b[3] += r['count'] if r['status'] == 'excluded, temporary' else 0
    for (src, kind), b in sorted(by.items(), key=lambda kv: -kv[1][0]):
        kind_cell = kind.replace('|', '\\|')
        lines.append(f'| {src} | {kind_cell} | {b[0]} | {b[1]} | {b[2]} | {b[3]} |')
    if not by:
        lines.append('| (none) | | 0 | 0 | 0 | 0 |')
    decided = [r['exclusion'] for r in rows
               if r['exclusion'] and r['exclusion'].get('decided') == today]
    uniq = {e['_index']: e for e in decided}
    lines += ['', f'**Exclusions decided this run: {len(uniq)}.**']
    for e in uniq.values():
        until = (f', until {e["revisit"]}' if e['term'] == 'temporary' else '')
        who = ('the session' if e['by'] == 'agent'
               else f'{e["by"]} ({e.get("strength")})')
        lines.append(f'- {e["source"]} / {e["kind"]} / '
                     f'`{e.get("path") or "*"}`: {e["term"]}{until}, by '
                     f'{who} -- {e["why"]}')
    lapsed = [r for r in rows if r['status'] == 'lapsed']
    if lapsed:
        lines += ['', f'**Past their revisit date, open again: '
                      f'{len(lapsed)} group(s).**']
    for p in problems:
        lines.append(f'- Registry problem: {p}')
    for e in result['stale']:
        lines.append(f'- Stale exclusion {e["_index"]} ({e["source"]} / '
                     f'{e["kind"]}): matches nothing now; delete it.')
    for n in notes:
        lines.append(f'- Not read: {n}')
    # Linked, not backticked: a bare path here would be an unlinked-reference
    # warning of its own, written by the section that counts them. But only
    # when the registry is there: a set with no exclusions yet has no such
    # file, the link was dead, and the light check refused the run record
    # the tool had just asked to be committed (2026-10-17, very deep check).
    has_registry = repo_root is None or \
        (pathlib.Path(repo_root) / REGISTRY_RELPATH).is_file()
    where = (f'Exclusions live in [{REGISTRY_RELPATH}]'
             f'({to_root}{REGISTRY_RELPATH}); ' if has_registry else
             'No exclusion is decided here yet; the first one creates '
             'the registry under tools/. ')
    lines += ['', where +
              f'[tools/warning_review.py]({to_root}tools/warning_review.py) '
              f'lists every open group.']
    return '\n'.join(lines)


def main(argv):
    repo_root = ROOT
    groups, collected, notes = collect(repo_root)
    entries, problems = load_registry(repo_root)
    result = review(groups, entries, collected)
    if '--json' in argv:
        print(json.dumps({'rows': [{k: v for k, v in r.items()
                                    if k != 'exclusion'} for r in result['rows']],
                          'totals': result['totals'], 'notes': notes,
                          'problems': problems}, indent=1))
    elif '--markdown' in argv:
        print(render_markdown(result, problems, notes))
    else:
        print(render_text(result, problems, notes, limit=10 ** 6
                          if '--all' in argv else 40))
    return 0


if __name__ == '__main__':
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print(__doc__)
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))

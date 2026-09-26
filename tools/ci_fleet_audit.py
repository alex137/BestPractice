#!/usr/bin/env python3
"""ci_fleet_audit.py -- every GitHub Actions workflow on every branch of
every repository this run can reach, asked of GITHUB rather than of a clone
(practice: ci-workflow-approved; run by very_deep_check.py's CI FLEET AUDIT
section).

WHY IT ASKS GITHUB. The ci-workflow-approved check runs before a session's
`git push`, over the files in that clone. Four routes never pass through
that push: a workflow edited on GitHub's website, one written through the
GitHub API (the file-write tools sessions carry), one sitting on a side
branch -- GitHub runs a branch's own workflow files when that branch is
pushed -- and one in a repository that does not use Precedent at all. The
2026-09-25 incident was a repo's own workflow billing a minute per merge
for four days; this is the view that would have named it on the first day.

FOR EACH REPOSITORY IT REACHES:

  * every workflow file on the default branch, what triggers it (push and
    pull-request branches, schedules in plain words), and whether it is the
    engine's own copy, approved in precedent.json's github_ci_approved at
    this exact content, edited since, or approved by nobody;
  * every OTHER branch whose workflow files differ from the default
    branch's, and whether pushing that branch would run them;
  * GitHub's own run count per workflow over the last 30 days, by event --
    runs, not minutes: each run bills at least one minute per job in a
    private repository;
  * a CRON REVIEW across the whole fleet, every schedule in one table.

IT WRITES NOTHING, ANYWHERE. Output goes to the session that ran it. The
report names other repositories, so it never goes into a repo, an issue or a
pull request (Morgan, 2026-09-26: "its results should go to the session not
the GitHub since it references other repos of yours").

A REPOSITORY IT CANNOT REACH IS NAMED, NEVER COUNTED CLEAN. Inside a Claude
Code session GitHub answers only for the repositories attached to that
session (measured 2026-09-26: `user/repos` and every unattached repository
answered with the proxy's refusal). Each one is listed under NOT REACHED
with what would reach it.

Usage:
  python3 tools/ci_fleet_audit.py                 # repos cloned beside this one
  python3 tools/ci_fleet_audit.py --repo owner/name [--repo owner/name ...]
  python3 tools/ci_fleet_audit.py --days 14 --max-branches 20
"""
import argparse
import base64
import datetime
import fnmatch
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

APPROVED_KEY = 'github_ci_approved'
WF_DIR = '.github/workflows'
DAYS = 30
MAX_BRANCHES = 40
RUN_PAGES = 3
WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday']


def _default_call(path):
    import github_budget
    return github_budget.call(path)


def _approval_problem(entry):
    """The one definition of a usable approval lives in precedent_check.py;
    this reads the same one rather than keeping a second."""
    import precedent_check
    return precedent_check._approval_problem(entry)


def _triggers_text(text):
    import precedent_check
    return precedent_check.workflow_triggers_text(text)


def _on(text):
    try:
        import yaml
        doc = yaml.safe_load(text)
    except Exception:                                          # noqa: BLE001
        return None
    if not isinstance(doc, dict):
        return None
    return doc.get('on', doc.get(True))


def push_fires(on, branch):
    """-> True when pushing `branch` runs a workflow with this `on:` block.
    A push trigger with only tags filters never fires for a branch push."""
    if isinstance(on, str):
        return on == 'push'
    if isinstance(on, list):
        return 'push' in on
    if not isinstance(on, dict) or 'push' not in on:
        return False
    spec = on['push']
    if not isinstance(spec, dict):
        return True
    if 'branches' in spec:
        return any(fnmatch.fnmatch(branch, str(g))
                   for g in spec.get('branches') or [])
    if 'branches-ignore' in spec:
        return not any(fnmatch.fnmatch(branch, str(g))
                       for g in spec.get('branches-ignore') or [])
    return not ('tags' in spec or 'tags-ignore' in spec)


def crons(on):
    if not isinstance(on, dict):
        return []
    spec = on.get('schedule')
    if not isinstance(spec, list):
        return []
    return [str(c.get('cron')) for c in spec
            if isinstance(c, dict) and c.get('cron')]


def cron_words(expr):
    """-> (plain words, runs per month or None). Only the common shapes are
    put into words; anything else is shown as written, never guessed at."""
    f = expr.split()
    if len(f) != 5:
        return expr, None
    mi, hr, dom, mon, dow = f
    if mi.startswith('*/') and hr == dom == mon == dow == '*':
        n = int(mi[2:]) if mi[2:].isdigit() else 0
        return (f'every {n} minutes', 43200 // n) if n else (expr, None)
    if not mi.isdigit():
        return expr, None
    if hr == '*' and dom == mon == dow == '*':
        return f'every hour at :{int(mi):02d}', 720
    if hr.startswith('*/') and hr[2:].isdigit() and dom == mon == dow == '*':
        n = int(hr[2:])
        return f'every {n} hours at :{int(mi):02d}', 720 // n
    if not hr.isdigit() or dom != '*' or mon != '*':
        return expr, None
    at = f'{int(hr):02d}:{int(mi):02d} UTC'
    if dow == '*':
        return f'daily at {at}', 30
    days = []
    for part in dow.split(','):
        if part.isdigit() and int(part) <= 7:
            days.append(WEEKDAYS[int(part) % 7])
        elif '-' in part and all(x.isdigit() for x in part.split('-')):
            a, b = (int(x) for x in part.split('-'))
            days += [WEEKDAYS[d % 7] for d in range(a, b + 1)]
        else:
            return expr, None
    return f'weekly on {", ".join(days)} at {at}', round(4.3 * len(days))


def _content(call, slug, path, ref):
    data, err = call(f'repos/{slug}/contents/{path}?ref={ref}')
    if err or not isinstance(data, dict) or 'content' not in data:
        return None
    try:
        return base64.b64decode(data['content']).decode('utf-8')
    except (ValueError, UnicodeDecodeError):
        return None


def _json_file(call, slug, path, ref):
    text = _content(call, slug, path, ref)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _workflow_listing(call, slug, ref):
    """-> {path: blob_sha} for one branch, {} when it has none, None when
    GitHub could not be asked."""
    data, err = call(f'repos/{slug}/contents/{WF_DIR}?ref={ref}')
    if err:
        return None
    if isinstance(data, dict):
        return {} if 'Not Found' in str(data.get('message', '')) else None
    return {f'{WF_DIR}/{x["name"]}': x.get('sha') for x in data
            if isinstance(x, dict) and x.get('type') == 'file'
            and x.get('name', '').endswith(('.yml', '.yaml'))}


def _blob_text(call, slug, sha, cache):
    if sha in cache:
        return cache[sha]
    data, err = call(f'repos/{slug}/git/blobs/{sha}')
    text = None
    if not err and isinstance(data, dict) and 'content' in data:
        try:
            text = base64.b64decode(data['content']).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            text = None
    cache[sha] = text
    return text


def _runs(call, slug, since, pages=RUN_PAGES):
    """-> ({path: {event: n}}, total, complete). `complete` is False when
    there were more runs than the pages read."""
    counts, seen, total = {}, 0, 0
    last = {}
    for page in range(1, pages + 1):
        data, err = call(f'repos/{slug}/actions/runs?per_page=100&page={page}'
                         f'&created=%3E%3D{since}')
        if err or not isinstance(data, dict) or 'workflow_runs' not in data:
            return None, 0, False
        total = data.get('total_count') or 0
        for r in data['workflow_runs']:
            p = str(r.get('path') or '').split('@')[0]
            ev = r.get('event') or '?'
            counts.setdefault(p, {}).setdefault(ev, 0)
            counts[p][ev] += 1
            last[p] = max(last.get(p, ''), str(r.get('created_at') or ''))
            seen += 1
        if seen >= total or not data['workflow_runs']:
            break
    for p, when in last.items():
        counts[p]['_last'] = when[:10]
    return counts, total, seen >= total


def _runs_words(by_event):
    by_event = dict(by_event or {})
    last = by_event.pop('_last', None)
    if not by_event:
        return 'no runs'
    n = sum(by_event.values())
    parts = ', '.join(f'{e} {c}' for e, c in sorted(by_event.items(),
                                                     key=lambda x: -x[1]))
    return (f'{n} run{"s" if n != 1 else ""} ({parts})'
            + (f', the last on {last}' if last else ''))


def audit_repo(slug, call=_default_call, days=DAYS,
               max_branches=MAX_BRANCHES, today=None):
    """-> dict with 'reached', 'rows' [(verdict, text)], 'crons' [...],
    'note'. Pure over `call`, so a test can plant any GitHub it likes."""
    out = {'slug': slug, 'reached': False, 'rows': [], 'crons': [],
           'note': ''}
    meta, err = call(f'repos/{slug}')
    if err or not isinstance(meta, dict) or 'default_branch' not in meta:
        msg = err or str((meta or {}).get('message', meta))[:200]
        out['note'] = msg
        return out
    out['reached'] = True
    default = meta['default_branch']
    private = bool(meta.get('private'))
    # A public repository's standard runners are not billed, so what would
    # be a finding there is a note.
    bad = 'FINDING' if private else 'NOTE'
    rows = out['rows']

    wf_meta, _ = call(f'repos/{slug}/actions/workflows?per_page=100')
    actions_off = (isinstance(wf_meta, dict) and 'workflows' not in wf_meta
                   and 'disabled' in str(wf_meta.get('message', '')).lower())
    states = {w.get('path'): w.get('state')
              for w in (wf_meta or {}).get('workflows') or []
              if isinstance(w, dict)} if isinstance(wf_meta, dict) else {}

    cfg = _json_file(call, slug, 'precedent.json', default)
    manifest = _json_file(call, slug, 'tools/ENGINE_MANIFEST.json', default)
    precedent = cfg is not None
    approved = (cfg or {}).get(APPROVED_KEY) or {}
    tracked = (manifest or {}).get('ci_workflows_sha256') or {}
    out['note'] = (f'{"private" if private else "public"}, default '
                   f'{default}, {"a Precedent install" if precedent else "not a Precedent install -- nothing here approves a workflow"}'
                   + ('; Actions is OFF, so nothing here can run' if actions_off else ''))

    if today is None:
        import precedent_time  # practice: timestamps-carry-offset
        today = precedent_time.today()
    if isinstance(today, str):
        today = datetime.date.fromisoformat(today[:10])
    since = today - datetime.timedelta(days=days)
    runs, total, complete = _runs(call, slug, since.isoformat())

    blobs = {}
    base = _workflow_listing(call, slug, default)
    if base is None:
        rows.append(('UNVERIFIED', f'could not list {WF_DIR} on {default}'))
        base = {}
    for path, sha in sorted(base.items()):
        text = _blob_text(call, slug, sha, blobs)
        if text is None:
            rows.append(('UNVERIFIED', f'{path}: could not read its content'))
            continue
        digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        on = _on(text)
        when = _triggers_text(text) or 'unreadable triggers'
        ran = _runs_words((runs or {}).get(path, {})) if runs is not None \
            else 'runs unknown'
        state = states.get(path)
        state_s = f', {state}' if state and state != 'active' else ''
        entry = approved.get(path)
        if tracked.get(path) == digest:
            status, verdict = "the engine's own copy, untouched", 'OK'
        elif entry is not None and _approval_problem(entry) is None \
                and entry.get('sha256') == digest:
            status, verdict = 'approved at this content', 'OK'
        elif not precedent:
            status, verdict = 'nothing approves it (not a Precedent install)', bad
        elif entry is not None and _approval_problem(entry) is None:
            status, verdict = 'EDITED since it was approved', bad
        elif entry is not None:
            status, verdict = f'approval unusable: {_approval_problem(entry)}', bad
        else:
            status, verdict = 'APPROVED BY NOBODY', bad
        if actions_off or state_s.startswith(', disabled'):
            verdict = 'NOTE' if verdict != 'OK' else verdict
        if verdict == 'FINDING' and push_fires(on, default):
            status += f' -- and it runs on every push to {default}, so every merge bills a run'
        rows.append((verdict, f'{path} [{default}{state_s}]: {status}. '
                              f'Runs on: {when}. Last {days} days: {ran}.'))
        for c in crons(on):
            words, per_month = cron_words(c)
            out['crons'].append((slug, path, c, words, per_month,
                                 verdict == 'OK'))

    branches, err = call(f'repos/{slug}/branches?per_page=100')
    if err or not isinstance(branches, list):
        rows.append(('UNVERIFIED', 'could not list branches, so no side '
                                   'branch was checked'))
        branches = []
    others = [b.get('name') for b in branches
              if isinstance(b, dict) and b.get('name') != default]
    if len(others) > max_branches:
        rows.append(('UNVERIFIED', f'{len(others) - max_branches} of '
                                   f'{len(others)} side branches not read '
                                   f'(--max-branches {max_branches})'))
    quiet, quiet_files = set(), 0
    for name in others[:max_branches]:
        listing = _workflow_listing(call, slug, name)
        if listing is None:
            rows.append(('UNVERIFIED', f'branch {name}: could not list '
                                       f'{WF_DIR}'))
            continue
        for path, sha in sorted(listing.items()):
            if base.get(path) == sha:
                continue
            text = _blob_text(call, slug, sha, blobs)
            on = _on(text or '')
            differs = 'not on ' + default if path not in base else \
                f'differs from {default}'
            if push_fires(on, name) and not actions_off:
                rows.append((bad, f'{path} on branch {name} ({differs}): '
                                  f'runs when {name} is pushed, and nothing '
                                  f'approves this version'))
            else:
                quiet.add(name)
                quiet_files += 1
    if quiet:
        # Named as a count: a branch whose workflow versions cannot run on
        # its own push costs nothing, and a line each buried the findings.
        rows.append(('NOTE', f'{quiet_files} workflow version(s) on '
                             f'{len(quiet)} side branch(es) differ from '
                             f'{default} and do not run on a push to their '
                             f'branch'))

    if runs is None:
        rows.append(('UNVERIFIED', 'could not read the run history'))
    else:
        recent = (today - datetime.timedelta(days=7)).isoformat()
        for path, by_event in sorted(runs.items()):
            if path and path not in base:
                # Still running this week is spending now; a file retired
                # earlier in the window is history, and says so.
                live = str(by_event.get('_last', '')) >= recent
                rows.append((bad if live else 'NOTE',
                             f'{path}: not on {default}, yet GitHub ran it -- '
                             f'{_runs_words(by_event)}, in the last {days} '
                             f'days' + ('' if live else
                                        ' (none in the last 7, so it has '
                                        'stopped)')))
        if not complete:
            rows.append(('NOTE', f'{total} runs in {days} days; only the '
                                 f'newest {RUN_PAGES * 100} were counted'))
    return out


def _origin_slug(repo_dir):
    try:
        url = subprocess.run(['git', '-C', str(repo_dir), 'config', '--get',
                              'remote.origin.url'], capture_output=True,
                             text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if 'github.com' not in url:
        return None
    tail = url.removesuffix('.git').split('github.com', 1)[1].lstrip(':/')
    parts = [x for x in tail.split('/') if x]
    return f'{parts[0]}/{parts[1]}' if len(parts) >= 2 else None


def discover(root=None):
    """-> sorted owner/name slugs for every git clone beside this checkout,
    plus the individual source the precedent config names. Cloned repos are
    only where the search starts: pass --repo for the rest."""
    root = pathlib.Path(root) if root else HERE.parent
    dirs = [p for p in root.parent.iterdir() if (p / '.git').exists()] \
        if root.parent.is_dir() else []
    try:
        cfg = json.loads((pathlib.Path.home() / '.config' / 'precedent' /
                          'config.json').read_text(encoding='utf-8'))
        for v in (cfg.get('individual'), cfg.get('individual_path')):
            if isinstance(v, str):
                dirs.append(pathlib.Path(v).expanduser())
    except (OSError, ValueError, AttributeError):
        pass
    slugs = {s for s in (_origin_slug(d) for d in dirs) if s}
    return sorted(slugs, key=str.lower)


def render(results, days=DAYS, out=sys.stdout):
    """Print the report; -> number of findings."""
    w = out.write
    w(f'CI FLEET AUDIT -- every workflow on every branch of every repo this '
      f'run reached, asked of GitHub\n(for this session only: nothing is '
      f'written to any repo or to GitHub)\n'
      f'Run counts cover the whole {days}-day window, so they include runs '
      f'of earlier versions of a file.\n\n')
    findings = 0
    unreached = [r for r in results if not r['reached']]
    for r in results:
        if not r['reached']:
            continue
        w(f"  {r['slug']} ({r['note']})\n")
        if not r['rows']:
            w('      no workflow files on any branch read\n')
        for verdict, text in r['rows']:
            findings += verdict == 'FINDING'
            w(f'      {verdict:<11} {text}\n')
        w('\n')
    allcron = [c for r in results for c in r['crons']]
    w('  CRON REVIEW -- every schedule on a default branch in the fleet\n')
    if not allcron:
        w('      none found in the repos reached\n')
    for slug, path, expr, words, per_month, ok in allcron:
        freq = f'~{per_month} runs/month' if per_month else 'frequency not put into words'
        w(f"      {slug} {path}: '{expr}' = {words}, {freq}"
          f"{'' if ok else ' -- NOT APPROVED'}\n")
    w('\n')
    if unreached:
        w('  NOT REACHED -- not checked, which is not the same as clean\n')
        for r in unreached:
            w(f"      {r['slug']}: {r['note']}\n")
        w('      In a session, attach a repo to reach it; on your own '
          'machine, a token that can read it.\n\n')
    w(f'ci_fleet_audit: {findings} finding(s) in '
      f'{len(results) - len(unreached)} repo(s) reached; '
      f'{len(unreached)} not reached.\n')
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--repo', action='append', default=[],
                    help='owner/name; repeat for more. Default: repos cloned '
                         'beside this checkout')
    ap.add_argument('--days', type=int, default=DAYS)
    ap.add_argument('--max-branches', type=int, default=MAX_BRANCHES)
    a = ap.parse_args(argv)
    slugs = a.repo or discover()
    if not slugs:
        print('ci_fleet_audit: no repository to ask about -- pass --repo '
              'owner/name. Nothing was checked, which is not clean.')
        return 0
    results = []
    for i, slug in enumerate(slugs, 1):
        print(f'[{i}/{len(slugs)}] {slug}', file=sys.stderr, flush=True)
        results.append(audit_repo(slug, days=a.days,
                                  max_branches=a.max_branches))
    render(results, days=a.days)
    try:
        import github_budget
        print(f"ci_fleet_audit: {github_budget.spend().get('calls', 0)} "
              f"GitHub API call(s) this run.")
        # Its own bill, judged against its own declared budget
        # (tools/github_api_budgets.json), not folded into its caller's.
        found, notes, rows = github_budget.audit(tool='ci_fleet_audit.py',
                                                 probe=False)
        if found:
            github_budget.render(found, notes, rows)
    except Exception:                                          # noqa: BLE001
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())

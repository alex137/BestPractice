#!/usr/bin/env python3
"""Update All Vendors: run Update Vendors across every repository on the person's list, from one session, without loading any of those repositories' instructions -- the list lives in the person's individual source (spec/UPDATE_ALL_VENDORS_PLAN.md)

precedent_update_all.py -- Update Vendors for every repository a person uses
Precedent in, one at a time, from any one session.

WHY IT EXISTS (Morgan, 2026-10-11). A session that holds twenty repositories
as roots carries twenty sets of instructions on every turn; one session per
repository costs twenty sessions. A repository's instructions load only when
it is REGISTERED as a session root, never when it is only attached and
cloned, and Update Vendors is one command (precedent_update.py) run from the
BestPractice clone. So this tool clones each repository into a work
directory, runs that command against it, commits and pushes what DONE
leaves, and prints one line per repository. The session's context grows by
a line per repository, not by a set of instructions.

THE LIST. `repos_using_precedent.json` at the root of the person's
individual source (the path in ~/.config/precedent/config.json, as
precedent_resolve.person_individual_path reads it). Each person's list sits
in their own individual source; the tool and the practice are universal.

    list                      the repositories on the list, with each one's
                              last outcome
    unknown OWNER/REPO ...    which of these the list has never classified;
                              pass every repository the harness can list
                              (Claude Code's cloud sessions: list_repos)
    probe OWNER/REPO ...      classify each one: a precedent.json at its
                              default branch puts it on the list, none puts
                              it under not_using. Attach a private one first
    skip OWNER/REPO ... --why TEXT
                              record each under not_using without opening
                              it: an archived repository, or not the person's
    run [--only OWNER/REPO]   the update itself, in list order
    record OWNER/REPO --merged PR
                              note that the update's pull request merged

WHAT `run` DOES, per repository, and the outcome word it prints:
  clone (blobless, all history), switch to the person's landing branch for
  that repository, run precedent_update.py --repo <clone>, then
    CURRENT   DONE with nothing staged: already up to date; clone deleted
    PUSHED    DONE: committed on a branch precedent_branch_name.py named,
              with the person's commit identity, and pushed; the line names
              the branch, the base and the full 40-character head for the
              merge. Clone deleted
    ASK       DONE with questions for the person; nothing committed. Clone kept
    LEFT      LEFT FOR YOU: this repository's own calls; clone kept, log named
    FAILED    a step could not run or the deep check is red; clone kept
  The session opens and merges each PUSHED pull request itself (the merge
  needs GitHub tools this script does not have), and hands an ASK, LEFT or
  FAILED repository to a subagent with a fresh context, so that repository's
  instructions never enter the main session.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import precedent_branches as pb                                 # noqa: E402
import precedent_identity                                       # noqa: E402
import precedent_resolve                                        # noqa: E402
import precedent_time                                           # noqa: E402

LIST_NAME = 'repos_using_precedent.json'
UPDATE = HERE / 'precedent_update.py'
DONE, LEFT, FAILED = 0, 1, 2
ASKS_MARK = 'DONE -- nothing left for this repo to decide. Ask the'


def today():
    return precedent_time.today()                # practice: timestamps-carry-offset


def list_path(individual=None):
    """-> the person's list file, or None when no individual source is
    configured."""
    root = pathlib.Path(individual) if individual else \
        precedent_resolve.person_individual_path()
    return root / LIST_NAME if root else None


def load(path):
    if path.is_file():
        return json.loads(path.read_text(encoding='utf-8'))
    return {'format_version': 1,
            '_comment': ['The repositories this person uses Precedent in, '
                         'read by BestPractice tools/precedent_update_all.py '
                         '("Update All Vendors"). `repos` is updated in list '
                         'order; `not_using` records repositories checked and '
                         'found without a precedent.json, so discovery does '
                         'not open them again. Written by the tool; edit by '
                         'hand only to reorder or to drop an entry.'],
            'repos': [], 'not_using': []}


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def norm(name):
    return name.strip().strip('/').lower()


def known(data):
    return {norm(e['repo']) for e in data['repos']} | \
        {norm(e['repo']) for e in data['not_using']}


def git(*args, cwd=None, env=None, check=True):
    r = subprocess.run(['git', *args], cwd=cwd, env=env, capture_output=True,
                       text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def clone(repo, dest, checkout=True):
    if dest.exists() and any(dest.iterdir()):
        raise RuntimeError(f'{dest} is in the way and is not a clone; '
                           f'move it aside and run again')
    args = ['clone', '-q', '--filter=blob:none']
    if not checkout:
        args += ['--depth', '1', '--no-checkout']
    git(*args, f'https://github.com/{repo}', str(dest))


def link_sources(clone_dir):
    """Make every source the clone declares by a relative path resolve.

    A consuming repo names a shared set as a sibling (`../precedent-shared-
    writing`), and in the work directory nothing is beside the clone; the
    update then refuses to write from an incomplete source set (the first
    run of this tool, 2026-10-11). The set is linked in from where this
    session already has it: beside the BestPractice clone, or beside the
    individual source. -> the names found nowhere, for the outcome line."""
    try:
        sources = json.loads((clone_dir / 'precedent.json').read_text(
            encoding='utf-8')).get('sources') or []
    except (OSError, ValueError):
        return []
    homes = [HERE.parent.parent]
    ind = precedent_resolve.person_individual_path()
    if ind:
        homes.append(ind.parent)
    missing = []
    for s in sources:
        raw = str(s.get('path') or '')
        if not raw or pathlib.Path(raw).is_absolute():
            continue
        target = clone_dir / raw
        if target.exists():
            continue
        found = next((h / pathlib.Path(raw).name for h in homes
                      if (h / pathlib.Path(raw).name).is_dir()), None)
        if found is None:
            missing.append(s.get('name') or raw)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        target.symlink_to(found)
    return missing


def cmd_list(data, _args):
    if not data['repos']:
        print('The list is empty. Run `probe` with the repositories '
              'list_repos returns to fill it.')
        return 0
    for e in data['repos']:
        last = e.get('last_run') or {}
        tail = (f"{last.get('outcome')} {last.get('date')}"
                + (f" PR #{last['pr']}" if last.get('pr') else '')) \
            if last else 'never run'
        print(f"{e['repo']:45} {e.get('kind', '?'):9} {tail}")
    return 0


def cmd_unknown(data, args):
    seen = known(data)
    new = [r for r in args.repos if norm(r) not in seen]
    for r in new:
        print(r)
    print(f'{len(new)} of {len(args.repos)} not classified yet.',
          file=sys.stderr)
    return 0


def cmd_probe(data, args):
    work = pathlib.Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    seen = known(data)
    for repo in args.repos:
        if norm(repo) in seen:
            print(f'KNOWN    {repo}')
            continue
        dest = work / ('probe-' + norm(repo).replace('/', '_'))
        shutil.rmtree(dest, ignore_errors=True)      # this tool's own probe
        try:
            clone(repo, dest, checkout=False)
        except RuntimeError as exc:
            print(f'ERROR    {repo}: {exc} (private? attach it first)')
            continue
        try:
            raw = git('show', 'HEAD:precedent.json', cwd=dest, check=False)
            manifest = git('show', 'HEAD:tools/ENGINE_MANIFEST.json',
                           cwd=dest, check=False)
        finally:
            shutil.rmtree(dest, ignore_errors=True)
        if raw:
            try:
                kind = json.loads(manifest).get('kind') or 'consumer'
            except ValueError:
                kind = 'consumer'
            data['repos'].append({'repo': norm(repo), 'kind': kind,
                                  'added': today(), 'last_run': None})
            print(f'ADDED    {repo} ({kind})')
        else:
            data['not_using'].append({'repo': norm(repo), 'checked': today()})
            print(f'NOT USED {repo}')
    return 0


def cmd_skip(data, args):
    seen = known(data)
    for repo in args.repos:
        if norm(repo) in seen:
            print(f'KNOWN    {repo}')
            continue
        data['not_using'].append({'repo': norm(repo), 'checked': today(),
                                  'why': args.why})
        print(f'SKIPPED  {repo} ({args.why})')
    return 0


def _outcome(code, out, clone_dir):
    if code == DONE:
        if ASKS_MARK in out:
            return 'ASK'
        staged = subprocess.run(['git', 'diff', '--cached', '--quiet'],
                                cwd=clone_dir).returncode
        return 'CURRENT' if staged == 0 else 'DONE'
    return 'LEFT' if code == LEFT else 'FAILED'


def _commit_note(out):
    for line in out.splitlines():
        if line.startswith('COMMIT MESSAGE: say this in it, in these words: '):
            return line.split('in these words: ', 1)[1].strip()
    return None


def _branch_name(clone_dir):
    namer = clone_dir / 'tools' / 'precedent_branch_name.py'
    if not namer.is_file():
        namer = HERE / 'precedent_branch_name.py'
    r = subprocess.run([sys.executable, str(namer), 'update-vendors'],
                       cwd=clone_dir, capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f'precedent_branch_name.py: {r.stderr.strip()}')
    return r.stdout.strip().splitlines()[-1]


def run_one(entry, work, args):
    """-> dict for the list's last_run, after printing one line."""
    repo = entry['repo']
    dest = work / norm(repo).replace('/', '_')
    log = work / (dest.name + '.log')
    started = time.time()
    result = {'date': today()}
    try:
        if (dest / '.git').is_dir():
            # An earlier run left this clone (ASK, LEFT, FAILED), perhaps
            # with a subagent's work in it: reuse it, never re-clone over it
            # (practice: repair-cannot-discard-work).
            git('fetch', '-q', 'origin', cwd=dest)
        else:
            clone(repo, dest)
        missing = link_sources(dest)
        if missing:
            raise RuntimeError(
                f"declared source(s) not in this session: {', '.join(missing)}"
                f" -- attach each beside the BestPractice clone and run again")
        base = pb.landing_branch(dest)[0]
        current = git('rev-parse', '--abbrev-ref', 'HEAD', cwd=dest)
        clean = not git('status', '--porcelain', cwd=dest)
        if current != base and clean:
            git('switch', '-q', base, cwd=dest)
        result['base'] = base
        r = subprocess.run([sys.executable, str(UPDATE), '--repo', str(dest)],
                           capture_output=True, text=True)
        out = r.stdout + r.stderr
        log.write_text(out, encoding='utf-8')
        outcome = _outcome(r.returncode, out, dest)
        if outcome == 'DONE' and args.no_push:
            outcome = 'READY'
        elif outcome == 'DONE':
            branch = _branch_name(dest)
            git('switch', '-q', '--no-track', '-c', branch, cwd=dest)
            note = _commit_note(out)
            msg = 'Update Vendors (Update All Vendors run)'
            if note:
                msg += f'\n\n{note}'
            if args.trailer:
                msg += '\n\n' + '\n'.join(args.trailer)
            env = precedent_identity.commit_env(dest)  # the declared author and zone
            git('commit', '-q', '-m', msg, cwd=dest, env=env)
            git('push', '-q', '-u', 'origin', branch, cwd=dest)
            result.update(branch=branch, head=git('rev-parse', 'HEAD', cwd=dest))
            outcome = 'PUSHED'
    except (RuntimeError, OSError) as exc:
        outcome = 'FAILED'
        log.write_text(f'{exc}\n', encoding='utf-8')
    result['outcome'] = outcome
    secs = int(time.time() - started)
    if outcome in ('CURRENT', 'PUSHED'):
        shutil.rmtree(dest, ignore_errors=True)
        where = ''
    else:
        where = f'  clone {dest}  log {log}'
    extra = (f"  {result['branch']} -> {result['base']}  head {result['head']}"
             if outcome == 'PUSHED' else '')
    print(f'{outcome:8} {repo}{extra}{where}  ({secs}s)', flush=True)
    return result


def cmd_run(data, args, path):
    work = pathlib.Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    only = {norm(r) for r in args.only or []}
    todo = [e for e in data['repos'] if not only or norm(e['repo']) in only]
    missing = only - {norm(e['repo']) for e in todo}
    if missing:
        print(f"Not on the list: {', '.join(sorted(missing))}", file=sys.stderr)
        return 2
    total, began = len(todo), time.time()
    counts = {}
    for i, entry in enumerate(todo, 1):
        print(f'[{i}/{total}] {entry["repo"]} ...', file=sys.stderr, flush=True)
        entry['last_run'] = run_one(entry, work, args)
        counts[entry['last_run']['outcome']] = \
            counts.get(entry['last_run']['outcome'], 0) + 1
        save(path, data)
        done = time.time() - began
        left = done / i * (total - i)
        print(f'    {int(done)}s so far, about {int(left)}s left',
              file=sys.stderr, flush=True)
    print('\n' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    return 0 if set(counts) <= {'CURRENT', 'PUSHED', 'READY'} else 1


def cmd_record(data, args):
    for e in data['repos']:
        if norm(e['repo']) == norm(args.repo):
            e['last_run'] = dict(e.get('last_run') or {})
            e['last_run'].update(outcome='MERGED', pr=args.merged,
                                 merged=today())
            print(f'{e["repo"]}: MERGED, PR #{args.merged}')
            return 0
    print(f'{args.repo} is not on the list', file=sys.stderr)
    return 2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    ap.add_argument('--individual', help='the individual source (default: '
                    'the path in ~/.config/precedent/config.json)')
    sub = ap.add_subparsers(dest='cmd')
    sub.add_parser('list')
    p = sub.add_parser('unknown')
    p.add_argument('repos', nargs='+')
    p = sub.add_parser('probe')
    p.add_argument('repos', nargs='+')
    p.add_argument('--workdir', required=True)
    p = sub.add_parser('skip')
    p.add_argument('repos', nargs='+')
    p.add_argument('--why', required=True)
    p = sub.add_parser('run')
    p.add_argument('--workdir', required=True,
                   help='where the clones go: the session scratchpad')
    p.add_argument('--only', action='append', metavar='OWNER/REPO')
    p.add_argument('--trailer', action='append', default=[],
                   help='a line to end each commit message with, such as '
                   'the session attribution; repeatable')
    p.add_argument('--no-push', action='store_true',
                   help='stop at READY, after the update, before committing')
    p = sub.add_parser('record')
    p.add_argument('repo')
    p.add_argument('--merged', type=int, required=True, metavar='PR')
    args = ap.parse_args(argv)
    path = list_path(args.individual)
    if path is None:
        print('No individual source is configured '
              '(~/.config/precedent/config.json), so there is no list to '
              'read. Set one up first: documentation/PER_MACHINE_SETUP.md.',
              file=sys.stderr)
        return 2
    data = load(path)
    cmd = args.cmd or 'list'
    if cmd == 'list':
        return cmd_list(data, args)
    if cmd == 'unknown':
        return cmd_unknown(data, args)
    if cmd == 'run':
        return cmd_run(data, args, path)
    code = {'probe': cmd_probe, 'skip': cmd_skip,
            'record': cmd_record}[cmd](data, args)
    save(path, data)
    return code


if __name__ == '__main__':
    sys.exit(main())

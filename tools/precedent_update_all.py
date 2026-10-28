#!/usr/bin/env python3
"""Update All Vendors: run Update Vendors in every repository the person names, one after another, from one session, without loading any of those repositories' instructions; a repository with no precedent.json is reported and left alone (spec/UPDATE_ALL_VENDORS_PLAN.md)

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

NO LIST (Morgan, 2026-10-11: "Is it even worth it to have a list?"). The
session passes every repository the person can reach that is not archived;
the tool decides each one fresh: a precedent.json at the landing branch means
update it, none means NOT USED. A stored list only saved checking the few
repositories without Precedent, and it went stale whenever one started or
stopped using it.

    python3 tools/precedent_update_all.py --workdir DIR [--trailer LINE]...
                                          [--no-push] OWNER/REPO ...

Each repository's line starts with one word:
    SKIPPED   the BestPractice repository itself, which is never updated
              this way
    NOT USED  no precedent.json; the clone is deleted
    CURRENT   DONE with nothing staged: already up to date; clone deleted
    PUSHED    DONE: committed on a branch precedent_branch_name.py named,
              with the person's commit identity, and pushed; the line names
              the branch, the base and the full 40-character head for the
              merge. Clone deleted
    READY     DONE with --no-push: stopped before the commit; clone kept
    ASK       DONE with questions for the person that the update does not
              call optional; nothing committed. Clone kept. Questions it
              calls optional ("the update is complete without these", a
              copy-in offer) hold nothing back: the repository goes on to
              PUSHED or CURRENT and each question is printed under its line
              as QUESTION, for the session to pass up
    LEFT      LEFT FOR YOU: this repository's own calls; clone kept, log named
    FAILED    a step could not run or the deep check is red; clone kept
Every line but SKIPPED and NOT USED names the repository's log, which the
session reads for that repository's root issues.
The session opens and merges each PUSHED pull request itself (the merge
needs GitHub tools this script does not have), and hands an ASK, LEFT or
FAILED repository to a subagent with a fresh context, so that repository's
instructions never enter the main session. A clone an earlier run kept is
reused, never cloned over (practice: repair-cannot-discard-work).
"""
import argparse
import json
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

UPDATE = HERE / 'precedent_update.py'
DONE, LEFT, FAILED = 0, 1, 2
ASKS_MARK = 'DONE -- nothing left for this repo to decide. Ask the'


def norm(name):
    return name.strip().strip('/').lower()


def source_repo():
    """-> 'owner/repo' of the BestPractice clone this tool runs from, or
    None. Its own precedent.json would otherwise make it look like a
    consumer, and the universal source is updated by its own changes."""
    r = subprocess.run(['git', '-C', str(HERE.parent), 'remote', 'get-url',
                        'origin'], capture_output=True, text=True)
    url = r.stdout.strip() if r.returncode == 0 else ''
    if not url:
        return None
    tail = url.rstrip('/').removesuffix('.git').split('github.com')[-1]
    return norm(tail.lstrip(':/'))


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


QUESTIONS_MARK = 'QUESTIONS FOR THE PERSON -- '
OPTIONAL_MARK = 'the update is complete without these'
NOTE_WORDS = 'COMMIT MESSAGE: say this in it, in these words: '
NOTE_FILES = 'COMMIT MESSAGE: name each of these in it -- '


def _indented_after(lines, i):
    """-> the indented lines that follow lines[i], up to the first other."""
    block = []
    for line in lines[i + 1:]:
        if not line.startswith('  '):
            break
        block.append(line.strip())
    return block


def _questions(out):
    """-> (questions, optional): the QUESTIONS FOR THE PERSON block's items,
    and whether its header calls them optional. Every question the update
    asks holds nothing (Report.ask), and a copy-in offer is one; 2026-10-28,
    one consumer's run stopped at ASK on one and had to be committed by hand."""
    lines = out.splitlines()
    questions, optional = [], True
    for i, line in enumerate(lines):
        if line.startswith(QUESTIONS_MARK):
            optional = optional and OPTIONAL_MARK in line
            questions += [q.removeprefix('- ') for q in _indented_after(lines, i)]
    return questions, optional


def _outcome(code, out, clone_dir):
    if code == DONE:
        questions, optional = _questions(out)
        if ASKS_MARK in out and not (questions and optional):
            return 'ASK'
        staged = subprocess.run(['git', 'diff', '--cached', '--quiet'],
                                cwd=clone_dir).returncode
        return 'CURRENT' if staged == 0 else 'DONE'
    return 'LEFT' if code == LEFT else 'FAILED'


def _commit_note(out):
    """-> what the update's COMMIT MESSAGE lines ask the commit to say, both
    forms (Report._commit_note prints them), or None. 2026-10-28: only the
    first form was read, and every Update All commit left out the files the
    update rewrote outside the vendored trees."""
    lines = out.splitlines()
    parts = []
    for i, line in enumerate(lines):
        if line.startswith(NOTE_WORDS):
            parts.append(line[len(NOTE_WORDS):].strip())
        elif line.startswith(NOTE_FILES):
            files = _indented_after(lines, i)
            if files:
                parts.append('Files this update rewrote outside the vendored '
                             'trees:\n' + '\n'.join(f'  {f}' for f in files))
    return '\n\n'.join(parts) or None


def _branch_name(clone_dir):
    namer = clone_dir / 'tools' / 'precedent_branch_name.py'
    if not namer.is_file():
        namer = HERE / 'precedent_branch_name.py'
    r = subprocess.run([sys.executable, str(namer), 'update-vendors'],
                       cwd=clone_dir, capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f'precedent_branch_name.py: {r.stderr.strip()}')
    return r.stdout.strip().splitlines()[-1]


def run_one(repo, work, args):
    """-> the outcome word, after printing one line for `repo`."""
    dest = work / norm(repo).replace('/', '_')
    log = work / (dest.name + '.log')
    started = time.time()
    result = {}
    try:
        if (dest / '.git').is_dir():
            # An earlier run left this clone (ASK, LEFT, FAILED), perhaps
            # with a subagent's work in it: reuse it, never re-clone over it
            # (practice: repair-cannot-discard-work).
            git('fetch', '-q', 'origin', cwd=dest)
        else:
            clone(repo, dest)
        if not (dest / 'precedent.json').is_file():
            # Not a Precedent repository today: nothing to update, and
            # nothing of the person's in the clone.
            shutil.rmtree(dest, ignore_errors=True)
            print(f'NOT USED {repo}  (no precedent.json)', flush=True)
            return 'NOT USED'
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
        r = subprocess.run([sys.executable, str(UPDATE), '--repo', str(dest),
                            *update_args(args)],
                           capture_output=True, text=True)
        out = r.stdout + r.stderr
        log.write_text(out, encoding='utf-8')
        outcome = _outcome(r.returncode, out, dest)
        if outcome != 'ASK':
            result['questions'] = _questions(out)[0]
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
    secs = int(time.time() - started)
    if outcome in ('CURRENT', 'PUSHED'):
        shutil.rmtree(dest, ignore_errors=True)
        # The log stays: the session reads it for this repository's root
        # issues (practice: update-all-vendors, step 6).
        where = f'  log {log}'
    else:
        where = f'  clone {dest}  log {log}'
    extra = (f"  {result['branch']} -> {result['base']}  head {result['head']}"
             if outcome == 'PUSHED' else '')
    print(f'{outcome:8} {repo}{extra}{where}  ({secs}s)', flush=True)
    for question in result.get('questions', []):
        # Optional, so they held nothing back, and still the person's to
        # answer: the session passes them up.
        print(f'         QUESTION for the person ({repo}): {question}', flush=True)
    return outcome



def update_args(args):
    """-> the flags each repository's update is given beyond --repo: the
    commit a rehearsal takes, and the person's copy-in answers."""
    out = []
    if args.rehearse:
        out += ['--from-ref', args.rehearse]
    for answer in args.copy_in:
        out += ['--copy-in', answer]
    if args.answered_by:
        out += ['--answered-by', args.answered_by]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    ap.add_argument('repos', nargs='+', metavar='OWNER/REPO',
                    help='every repository to try, archived ones left out')
    ap.add_argument('--workdir', required=True,
                    help='where the clones go: the session scratchpad')
    ap.add_argument('--trailer', action='append', default=[],
                    help='a line to end each commit message with, such as '
                    'the session attribution; repeatable')
    ap.add_argument('--no-push', action='store_true',
                    help='stop at READY, after the update, before committing')
    ap.add_argument('--rehearse', metavar='REF',
                    help='run every update against this BestPractice commit '
                    'or branch, unlanded engine code included, and push '
                    'nothing (implies --no-push): an engine change to Update '
                    'Vendors or copy-in meets every consumer state before it '
                    'lands, not one person\'s repository at a time')
    ap.add_argument('--copy-in', action='append', default=[],
                    metavar='NAME=yes|no',
                    help='passed to each update, with --answered-by')
    ap.add_argument('--answered-by', default='',
                    help='who gave the --copy-in answers, a date and their words')
    args = ap.parse_args(argv)
    if args.rehearse:
        args.no_push = True
    work = pathlib.Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    own = source_repo()
    total, began, counts = len(args.repos), time.time(), {}
    for i, repo in enumerate(args.repos, 1):
        print(f'[{i}/{total}] {repo} ...', file=sys.stderr, flush=True)
        if own and norm(repo) == own:
            print(f'SKIPPED  {repo}  (the universal source itself; it is '
                  f'updated by its own changes)', flush=True)
            outcome = 'SKIPPED'
        else:
            outcome = run_one(repo, work, args)
        counts[outcome] = counts.get(outcome, 0) + 1
        done = time.time() - began
        print(f'    {int(done)}s so far, about {int(done / i * (total - i))}s '
              f'left', file=sys.stderr, flush=True)
    print('\n' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
    fine = {'SKIPPED', 'NOT USED', 'CURRENT', 'PUSHED', 'READY'}
    return 0 if set(counts) <= fine else 1


if __name__ == '__main__':
    sys.exit(main())

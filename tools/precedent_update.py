#!/usr/bin/env python3
"""precedent_update.py -- "Update Vendors" as one command: every step of
vendor-update-runbook that needs no judgment, in order, then one report.

Run it from the consuming repo, calling THIS copy -- the one in the
BestPractice clone, never a vendored one:

    python3 ../BestPractice/tools/precedent_update.py --repo .

WHY IT EXISTS (spec/ONE_COMMAND_UPDATE_PLAN.md, practice:
vendor-update-runbook). "Update Vendors" used to authorize a runbook that a
session then carried out by hand, and every consuming repo stopped at the
same places. The case that settled it, 2026-09-27: a consumer update stopped
halfway, engine on main and catalogue on precedent-beta-v01, because
finishing it meant a hand edit a permission check held for a human -- to
re-make a decision already made two days earlier. The rule this follows: an
upstream decision that changes a consumer's files is a step here, never a
sentence in the runbook.

WHY FROM THE SOURCE CLONE. A consumer's vendored checkin.py lives inside
the catalogue it updates, so a fix to it reaches a repo only after that repo
needed it. Run from the source clone, every step is the current code: the
engine refresh, the catalogue update (checkin.py --repo), the pin repoint.

THE STEPS, with no question in between:
  1. the source clone fetches the branch every install follows
  2. the engine refresh (the consumer's own copy, which replaces itself and
     runs a second pass), then the catalogue-pin repoint from THIS copy
  3. the catalogue: checkin.py update, then record -- only where the repo
     vendors one (process/manifest.json)
  4. the views regenerated -- the loader block, and in a practice set
     MAP.md and GLOSSARY.md too -- then this repo's own citations of any
     practice the update withdrew or reworded (a withdrawn one's is a call
     left for you; a reworded one's is listed to read)
  5. the repo's own deep check (--skip-check to leave it out)

THE REPORT, and the exit code a session acts on:
  0  DONE -- nothing is left. Commit, then run Go update's chain.
  1  LEFT FOR YOU -- only the calls that belong to this repo: a hand-edited
     file upstream also changed, a line a check-in would lose, a decline to
     decide again. Each is named with the question. Work them under the
     conflicted-file review at the top of vendor-update-runbook, then run
     this again.
  2  FAILED -- a step could not run, or the deep check is red. Named, with
     what was written before it stopped.

It stages what it wrote and deleted, so the deep check judges the tree the
commit will hold, and leaves anything already uncommitted alone. It never
commits, pushes or merges. Those stay with the session, under Go update's
chain, where the authorization already lives.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
SOURCE = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import precedent_vendor_engine as pve  # noqa: E402

DONE, LEFT, FAILED = 0, 1, 2


class Report:
    def __init__(self):
        self.steps = []   # (name, one-line outcome)
        self.left = []    # (what, why)
        self.loud = []    # workflows left alone -- printed first and last

    def step(self, name, outcome):
        self.steps.append((name, outcome))
        print(f"precedent_update: {name}: {outcome}", flush=True)

    def leave(self, what, why):
        if (what, why) not in self.left:
            self.left.append((what, why))

    def _banner(self):
        # A workflow the update had to leave alone still runs in GitHub, and
        # the person asked for that to be impossible to miss (Morgan,
        # 2026-09-27: "flag it importantly ... strong language").
        bar = '!' * 72
        print(f"\n{bar}\n{pve.KEPT_LOUD_HEADER}\n{bar}")
        for line in self.loud:
            print(f"  {line}")
        print(bar)

    def close(self, failed=None):
        if self.loud:
            self._banner()
        print("\n== Update Vendors ==")
        for name, outcome in self.steps:
            print(f"  {name}: {outcome}")
        if failed:
            print(f"\nFAILED: {failed}")
            print("Nothing is committed. Fix what is named above and run this "
                  "again; files the steps before it wrote are still in the "
                  "working tree for you to review.")
            return FAILED
        if self.left:
            print("\nLEFT FOR YOU -- the calls that belong to this repo. Work "
                  "each under vendor-update-runbook's conflicted-file review, "
                  "then run this again:")
            for what, why in self.left:
                print(f"  - {what}: {why}")
            if self.loud:
                self._banner()
            return LEFT
        print("\nDONE -- nothing left to decide. Review the staged diff, "
              "commit, then run Go update's chain.")
        return DONE


def run(argv, cwd):
    r = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    return r.returncode, r.stdout + r.stderr


def tail(out, n=25):
    lines = [l for l in out.rstrip().splitlines()]
    return '\n'.join('    | ' + l for l in lines[-n:])


def left_block(out):
    """The '  - item: why' lines under the engine's own Left-for-you
    heading, and checkin's DECISIONS TO MAKE AGAIN list."""
    items, inside = [], False
    for line in out.splitlines():
        if line.startswith('Left for you') or \
                line.startswith('DECISIONS TO MAKE AGAIN'):
            inside = True
            continue
        if inside:
            if line.startswith('  - '):
                items.append(line[4:].strip())
            elif line.strip():
                inside = False
    return items


def lost_files(out):
    return [l.strip()[len('LOST from '):].rstrip(':')
            for l in out.splitlines() if l.strip().startswith('LOST from ')]


def dirty_paths(repo):
    """Every path `git status` reports, staged or not, tracked or not. A
    staged rename lists both its sides."""
    r = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain=v1', '-z',
                        '--untracked-files=all'], capture_output=True, text=True)
    fields, paths, i = r.stdout.split('\0'), set(), 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        paths.add(entry[3:])
        if entry[0] in 'RC' and i < len(fields):
            paths.add(fields[i])
            i += 1
    return paths


def stage_update(repo, before):
    """Stage what this run wrote or deleted, and nothing that was already
    uncommitted when it started. Returns how many paths it staged.

    So the deep check judges the tree the commit will hold. Found
    2026-09-27 taking main into a consumer: `checkin.py update` deleted two
    files upstream had dropped, the deletions sat unstaged, and the deep
    check -- listing files from the index -- failed the update on a file
    that was gone. A person's own unfinished work is left as it was."""
    ours = sorted(dirty_paths(repo) - before)
    for i in range(0, len(ours), 200):
        subprocess.run(['git', '-C', str(repo), 'add', '-A', '--', *ours[i:i + 200]],
                       capture_output=True, text=True)
    return len(ours)


def citations(repo):
    """-> ([(where, why)] to fix, [where] to read), or None when the lookup
    could not run. Asks the SOURCE clone's copy of the lookup, for the same
    reason every other step here does: it is the current code."""
    refs = SOURCE / 'tools' / 'precedent_practice_refs.py'
    if not refs.is_file():
        return None
    r = subprocess.run([sys.executable, str(refs), '--repo', str(repo),
                        '--withdrawn', '--changed-since', 'HEAD', '--staged',
                        '--json'], cwd=str(repo), capture_output=True,
                       text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    fix, read = [], []
    for h in data.get('hits', []):
        if h.get('source') != 'this repository' or h.get('kind') != 'live':
            continue
        where = f"{h['file']}:{h['line']}"
        if h.get('must_fix'):
            succ = data.get('successors', {}).get(h['slug'])
            fix.append((where, f"cites `{h['slug']}`, which is no longer in force"
                        + (f" -- cite `{succ}`" if succ else
                           " anywhere -- say in prose what it covered")))
        elif data.get('slugs', {}).get(h['slug']) == 'Rule reworded':
            read.append(where)
    return fix, read


def update(repo, skip_check=False, ref=None):
    rep = Report()
    before = dirty_paths(repo)
    engine_tool = repo / 'tools' / 'precedent_vendor_engine.py'
    if not (repo / 'tools' / pve.MANIFEST_NAME).is_file() or not engine_tool.is_file():
        rep.leave(str(repo), "no vendored loader engine (tools/ENGINE_MANIFEST.json), "
                  "so this is a migration, not an update -- "
                  "spec/MIGRATING_EXISTING_INSTALLS.md")
        return rep.close()

    # 1. The source clone. Both halves read committed refs, never its
    # working tree, so a fetch is what makes them current.
    if ref is None:
        rc, out = run(['git', '-C', str(SOURCE), 'fetch', 'origin',
                       pve.SOURCE_BRANCH], SOURCE)
        if rc != 0:
            return rep.close(f"could not fetch origin/{pve.SOURCE_BRANCH} in "
                             f"{SOURCE}:\n{tail(out)}")
    rc, head = run(['git', '-C', str(SOURCE), 'rev-parse',
                    ref or f'origin/{pve.SOURCE_BRANCH}'], SOURCE)
    rep.step('source', f"{pve.SOURCE_BRANCH} @ {head.strip()[:12]}" if rc == 0
             else f"could not read {ref or 'origin/' + pve.SOURCE_BRANCH}")

    # 2. The engine, by the consumer's own copy: refresh() takes ROOT from
    # where it sits. It replaces itself and re-runs, so an old copy still
    # ends on the current code.
    argv = [sys.executable, str(engine_tool), 'refresh', str(SOURCE)]
    if ref:
        argv += ['--from-ref', ref]
    rc, out = run(argv, repo)
    if rc != 0:
        if 'hand-edited since the last seed/refresh' in out:
            for line in out.splitlines():
                if line.startswith('  ') and ': ' in line and not line.startswith('    '):
                    name, why = line.strip().split(': ', 1)
                    rep.leave(name, f"hand-edited here and shipped by upstream: {why}. "
                              "Move the edit upstream, or refresh --force once "
                              "you have decided it can go")
            rep.step('engine', 'refused: a vendored file was edited here')
            return rep.close()
        return rep.close(f"the engine refresh failed:\n{tail(out)}")
    for item in left_block(out):
        what, _, why = item.partition(': ')
        rep.leave(what, why or item)
    summary = [l for l in out.splitlines()
               if l.startswith('precedent_vendor_engine refresh OK')
               or 'already current with' in l]
    rep.step('engine', summary[-1].split(': ', 1)[-1] if summary else 'refreshed')
    # A consumer's CI converges to upstream without asking (2026-09-27, see
    # precedent_vendor_engine.CI_CONVERGES_KINDS), so what the refresh
    # replaced or removed is reported here as done, never as a question.
    rep.loud += [l.strip() for l in out.splitlines()
                 if l.strip().startswith('LEFT ALONE: ')
                 and l.strip() not in rep.loud]
    ci = []
    for line in out.splitlines():
        if 'refresh: CI workflow replaced: ' in line:
            ci.append('replaced ' + line.split('replaced: ', 1)[1].split(' ', 1)[0]
                      + ' with the template')
        elif 'refresh: retired .github/workflows/' in line:
            ran = re.search(r'It ran ([^:]+):', line)
            ci.append('removed ' + line.split('retired ', 1)[1].split(' ', 1)[0]
                      + (f' (it ran {ran.group(1)}, which the local push check '
                         f'already runs)' if ran else ''))
    if ci:
        rep.step('CI workflows', '; '.join(dict.fromkeys(ci))
                 + ' -- converged to upstream, nothing to ask')
    # The repoint again, from THIS copy: a consumer whose engine was already
    # current never ran a newer refresh that knows it.
    if 'repointed the practice catalogue' in out or pve.repoint_catalogue_pin(repo):
        rep.step('catalogue pin', f'repointed to {pve.SOURCE_BRANCH} '
                 f'(decided 2026-09-25; nothing to ask)')

    # 3. The catalogue, where there is one, by the source clone's checkin.py.
    if (repo / 'process' / 'manifest.json').is_file():
        checkin = [sys.executable, str(SOURCE / 'tools' / 'checkin.py')]
        rc, out = run(checkin + ['update', str(SOURCE), '--repo', str(repo)], repo)
        for item in left_block(out):
            rep.leave('a decline to decide again', item)
        if rc != 0:
            changed = [l.strip()[len('local change: '):] for l in out.splitlines()
                       if l.strip().startswith('local change: ')]
            if changed:
                for p in changed:
                    rep.leave(f'process/upstream/{p}',
                              'changed here since the last sync, and a mirror '
                              'would overwrite it -- export it, keep it as a '
                              'manifest `diverged` entry, or let it go')
                rep.step('catalogue', 'refused: the vendored tree has local changes')
                return rep.close()
            return rep.close(f"checkin.py update failed:\n{tail(out)}")
        rep.step('catalogue', next((l for l in out.splitlines()
                                    if l.startswith('checkin update')), 'updated'))
        rc, out = run(checkin + ['record', str(SOURCE), '--repo', str(repo),
                                 '--note', 'Update Vendors'], repo)
        if rc != 0:
            lost = lost_files(out)
            if lost:
                for f in lost:
                    rep.leave(f, 'lines this repo added would be lost by the '
                              'update -- carry them upstream, or record with '
                              '--accept-loss if dropping them is deliberate')
                rep.step('catalogue record', 'held: the carry check found lines to lose')
                return rep.close()
            return rep.close(f"checkin.py record failed:\n{tail(out)}")
        rep.step('catalogue record', next((l for l in out.splitlines()
                                           if l.startswith('checkin record')),
                                          'recorded'))

    # 4. The views. A refresh changes what the loader renders.
    #
    # A practice SET renders more than a consumer does: MAP.md and
    # GLOSSARY.md too, and MAP.md lists every engine file. Its deep check is
    # `build_views.py --check`, so an update that adds an engine file and
    # regenerates only the loader block fails its own gate. 2026-09-27: all
    # four of Morgan's sets stopped on exactly that, one new MAP.md row
    # each, fixed by hand. A set has no precedent_sync_views.py anyway --
    # so it gets the full build, the same one its check compares against.
    sync = repo / 'tools' / 'precedent_sync_views.py'
    build = repo / 'tools' / 'build_views.py'
    try:
        kind = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                          .read_text(encoding='utf-8')).get('kind')
    except (OSError, ValueError):
        kind = None
    if kind == 'source' and build.is_file():
        rc, out = run([sys.executable, str(build), '--repo', '.'], repo)
        if rc != 0:
            return rep.close(f"the view build failed:\n{tail(out)}")
        rep.step('views', 'regenerated (loader block, MAP.md, GLOSSARY.md)')
    elif sync.is_file():
        rc, out = run([sys.executable, str(sync), '--repo', str(repo)], repo)
        if rc != 0:
            return rep.close(f"the view sync failed:\n{tail(out)}")
        rep.step('views', 'regenerated')

    # Staged before the check, so it judges what the commit will hold.
    n = stage_update(repo, before)
    rep.step('staged', f'{n} path(s) this update wrote or deleted'
             + (f'; {len(before)} already uncommitted before it ran, left as they were'
                if before else ''))

    # 4b. Citations of what the update withdrew or reworded, in THIS repo's
    # own files. A consumer is where a renamed practice's old name survives
    # longest: its AGENTS.md and docs were written against the name it had
    # then, and nothing the refresh touches rewrites them.
    # practice: practice-change-propagates
    cited = citations(repo)
    if cited is None:
        rep.step('citations', 'could not be looked up -- run '
                 'tools/precedent_practice_refs.py --withdrawn before pushing')
    else:
        fix, read = cited
        for where, why in fix:
            rep.leave(where, why)
        rep.step('citations',
                 (f'{len(fix)} live citation(s) of a withdrawn practice to fix '
                  f'(listed below)' if fix else
                  'no live citation of a withdrawn practice')
                 + (f'; {len(read)} citation(s) of a practice this update '
                    f'reworded -- read each, it may describe the old rule: '
                    + ', '.join(read) if read else ''))

    # 5. The repo's own deep check -- the gate before any push.
    check = repo / 'tools' / 'precedent_push_check.py'
    if skip_check:
        rep.step('deep check', 'skipped (--skip-check) -- run it before pushing')
    elif check.is_file():
        rc, out = run([sys.executable, str(check)], repo)
        if rc != 0:
            return rep.close(f"the deep check is red:\n{tail(out)}")
        rep.step('deep check', 'passed')
    else:
        rep.step('deep check', 'this repo has no tools/precedent_push_check.py')
    return rep.close()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Update Vendors as one command (spec/ONE_COMMAND_UPDATE_PLAN.md).')
    ap.add_argument('--repo', default='.', help='the consuming repo (default: .)')
    ap.add_argument('--skip-check', action='store_true',
                    help='leave the deep check out; it still gates the push')
    ap.add_argument('--from-ref', default=None,
                    help='vendor this commit of the source instead of its '
                         f'origin/{pve.SOURCE_BRANCH} -- for testing a commit')
    a = ap.parse_args(argv)
    repo = pathlib.Path(a.repo).resolve()
    if repo == SOURCE:
        print("precedent_update FAIL: --repo is this BestPractice clone itself. "
              "Run it from the consuming repo: "
              "python3 ../BestPractice/tools/precedent_update.py --repo .")
        return FAILED
    return update(repo, skip_check=a.skip_check, ref=a.from_ref)


if __name__ == '__main__':
    sys.exit(main())

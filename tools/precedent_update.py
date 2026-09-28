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
  3. the catalogue: checkin.py update, then record, where the repo vendors
     one under process/ (process/manifest.json); for a section 0 install,
     its universal source's practices/ replaced wholesale (INSTALL.md
     section 2, step 0); and where there is neither, a line saying so
     then, where precedent.json names no landing_branch, pre-staging
  4. the views regenerated -- the loader block, and in a practice set
     MAP.md and GLOSSARY.md too -- then this repo's own citations of any
     practice the update withdrew or reworded (a withdrawn one's is a call
     left for you; a reworded one's is listed to read)
  4a. any missing branch tier made on origin: staging from pre-staging,
     pre-staging from staging, both from main when neither exists
  5. the repo's own check at its landing branch's tier -- into pre-staging,
     the fast checks on what changed; the full check waits for the Promote
     (--skip-check to leave it out) -- run against a temporary commit of
     the staged update, undone right after, so it judges the tree the way
     the push will

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
commit will hold, and leaves anything already uncommitted alone -- save the
pinned engine a source refresh wrote ahead of it, which is the update's own
and is staged as such when every file matches the manifest. It never
leaves a commit behind, and never merges. The one thing it pushes is a
missing branch tier (pre-staging or staging), made at a commit origin
already has; the deep check's temporary commit is undone before it
reports. Those stay with the session, under Go update's
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
import precedent_branches as pb  # noqa: E402

DONE, LEFT, FAILED = 0, 1, 2


def universal_catalogue_path(repo):
    """-> the repo-relative path of the universal source this repository
    vendors inside itself (a section 0 install), or None: no precedent.json,
    no universal source, or one that lives outside the repository."""
    try:
        data = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    for src in data.get('sources') or []:
        if not isinstance(src, dict) or src.get('level') != 'universal':
            continue
        path = str(src.get('path') or '').strip().rstrip('/')
        if not path or path.startswith(('/', '~')) or '..' in pathlib.PurePosixPath(path).parts:
            return None
        return path
    return None


def vendor_universal_catalogue(repo, rep, rev, last_synced=None):
    """Replace a section 0 install's vendored universal catalogue with the
    source clone's practices/ at commit `rev` -- a committed ref, never the
    clone's working tree, as the engine step reads. -> True when the step
    ran or honestly had nothing to do (reported either way), None when it
    left a call for the person, or the reason the update fails."""
    import io
    import shutil
    import tarfile
    import tempfile
    rel = universal_catalogue_path(repo)
    target = repo / rel / 'practices' if rel else None
    if target is None or not target.is_dir():
        rep.step('catalogue', 'none vendored here: no process/manifest.json and '
                 'no universal source with a practices/ tree inside this repo, '
                 'so there was nothing to update')
        return True
    # Zero local variance by design (INSTALL.md section 2, step 0): a local
    # edit belongs upstream, so the replace refuses rather than eat one.
    r = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain', '--',
                        f'{rel}/practices'], capture_output=True, text=True)
    dirty = [l[3:] for l in r.stdout.splitlines() if l.strip()]
    if r.returncode != 0:
        return f'could not read git status of {rel}/practices: {r.stderr.strip()[:200]}'
    if dirty:
        for p in dirty:
            rep.leave(p, 'changed here and not committed; the catalogue is '
                      'replaced wholesale, so export the change upstream or '
                      'discard it first')
        rep.step('catalogue', f'refused: {rel}/practices has uncommitted changes')
        return None
    # Committed local edits too: a file that matches neither the version it
    # was last synced at nor the incoming one was changed here, and the
    # replace would lose it. One that matches the incoming version already
    # (a catalogue copied over by hand) loses nothing.
    edited, unread = [], False
    if last_synced:
        ok = subprocess.run(['git', '-C', str(SOURCE), 'cat-file', '-e',
                             f'{last_synced}^{{commit}}'], capture_output=True)
        unread = ok.returncode != 0
        for f in sorted(target.rglob('*')) if not unread else []:
            if not f.is_file():
                continue
            name = f.relative_to(target).as_posix()
            here = f.read_bytes()
            versions = []
            for at in (last_synced, rev):
                b = subprocess.run(['git', '-C', str(SOURCE), 'show',
                                    f'{at}:practices/{name}'], capture_output=True)
                versions.append(b.stdout if b.returncode == 0 else None)
            if here not in versions:
                edited.append(f'{rel}/practices/{name}')
    if edited:
        for p in edited:
            rep.leave(p, f'differs from upstream at {last_synced[:12]} (the last '
                      f'sync) and at {rev[:12]}: a local edit the wholesale '
                      f'replace would lose -- export it upstream, or restore '
                      f'upstream\'s text, then run this again')
        rep.step('catalogue', f'refused: {len(edited)} file(s) in {rel}/practices '
                 f'carry local edits')
        return None
    arc = subprocess.run(['git', '-C', str(SOURCE), 'archive', '--format=tar',
                          rev, 'practices'], capture_output=True)
    if arc.returncode != 0 or not arc.stdout:
        return (f'could not read practices/ at {rev[:12]} in {SOURCE}: '
                f'{arc.stderr.decode(errors="replace").strip()[:200]}')
    with tempfile.TemporaryDirectory() as td:
        with tarfile.open(fileobj=io.BytesIO(arc.stdout)) as tf:
            try:
                tf.extractall(td, filter='data')
            except TypeError:   # a Python older than 3.11.4 has no filter
                tf.extractall(td)
        shutil.rmtree(target)
        shutil.copytree(pathlib.Path(td) / 'practices', target)
    n = sum(1 for _ in target.glob('*.md'))
    note = ('' if last_synced and not unread else
            '; the last-synced commit could not be read here, so only '
            'uncommitted edits were checked for')
    rep.step('catalogue', f'{rel}/practices replaced from the source at '
             f'{rev[:12]} ({n} practice files; INSTALL.md section 2, step 0){note}')
    return True


class Report:
    def __init__(self):
        self.steps = []   # (name, one-line outcome)
        self.left = []    # (what, why)
        self.loud = []    # workflows left alone -- printed first and last
        self.details = {} # what -> lines printed under its Left-for-you item

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
                for line in self.details.get(what, []):
                    print(f"    {line}")
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


def diverged_details(out):
    """-> {what: [detail line, ...]} from the engine refresh's DIVERGED
    blocks: the blocks a locally edited file or AGENTS.md section lacks, and
    the sentences missing from each. The engine prints them and names each
    in Left-for-you as "(listed above)"; until 2026-09-28 this command kept
    only the Left-for-you line, so "listed above" listed nothing and a
    session called missing_markdown_blocks() by hand to see what to copy."""
    details, key = {}, None
    for line in out.splitlines():
        if line.startswith('DIVERGED: '):
            body = line[len('DIVERGED: '):]
            m = re.match(r'(.+?) (?:\(line \d+\) )?has local edits', body)
            key = m.group(1) if m else None
            if key is not None:
                details.setdefault(key, [])
            continue
        if key is not None and line.startswith('    '):
            details[key].append(line.rstrip())
        elif line.strip():
            key = None
    return {k: v for k, v in details.items() if v}


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


def adopt_engine_output(repo, before, pinned):
    """-> the paths in `before` that are this update's own output, written
    ahead of it, to stage as the update's; [] when any is not.

    Found 2026-09-27 on all four of Morgan's sets: a source refresh run
    first (precedent_refresh_sources.py) had already written the pinned
    engine into each repo, so the refresh here said "already current",
    stage_update left the two changed files as someone else's, and the
    report said DONE on an update that would have committed nothing. They
    are the update's when the manifest -- uncommitted -- names the pinned
    commit and every uncommitted file it tracks hashes to what it records;
    a single mismatch means someone else's edit is in the mix, and then
    nothing is taken."""
    rel = f'tools/{pve.MANIFEST_NAME}'
    if rel not in before or not pinned:
        return []
    try:
        m = json.loads((repo / rel).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    if m.get('source_commit') != pinned:
        return []
    tracked = {f'tools/{n}': h for n, h in (m.get('sha256') or {}).items()}
    tracked.update({f'{pve.HOOK_DEST_DIR}/{n}': h
                    for n, h in (m.get('hooks_sha256') or {}).items()})
    tracked.update(m.get('engine_paths_sha256') or {})
    ours = [rel]
    for path in sorted(before & set(tracked)):
        f = repo / path
        if not f.is_file() or pve._sha256(f) != tracked[path]:
            return []
        ours.append(path)
    return ours


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


TEMP_COMMIT_MESSAGE = ('precedent_update: the staged update, committed only so the '
                       'deep check judges it as committed -- undone right after')


def judged_as_committed(repo, argv):
    """-> (rc, output) of `argv`, run against the tree the commit will hold.

    WHY (2026-09-27, found taking main into a consumer): the deep check
    judged an update by what was STAGED, and a committed tree is judged
    differently in two ways. A change-scope check reads `git status`, so
    every materialized practice the update rewrote -- upstream text the repo
    cannot edit -- was judged as this repo's own new prose; once committed,
    nothing is uncommitted and the push never judges it. And a shipped test
    that clones the repo clones HEAD, so it ran the update's NEW test
    against the OLD scripts. Both failed an update that passes the moment
    it is committed.

    So the staged update is committed, the check runs, and the commit is
    undone with `git reset --soft`, which moves only HEAD: the index and the
    working tree are left exactly as the check found them, staged work and
    unstaged edits alike. The commit goes through the repository's own
    hooks, the way the real one will, and carries the person's zone.

    Nothing staged: nothing to commit, and the check runs as it is. A commit
    the hooks refuse is the answer the real commit would get, so it is
    reported, never worked around."""
    staged = subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--quiet'],
                            capture_output=True).returncode != 0
    if not staged:
        return run(argv, repo)
    rc, before = run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], repo)
    if rc != 0:
        return run(argv, repo)
    before = before.strip()
    env = {**os.environ}
    try:
        import precedent_time
        when = precedent_time.stamp_iso(repo)
        env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = when
    except Exception:                                          # noqa: BLE001
        pass
    c = subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m',
                        TEMP_COMMIT_MESSAGE], capture_output=True, text=True,
                       env=env)
    if c.returncode != 0:
        return c.returncode, ('the staged update could not be committed, so '
                              'the real commit would be refused the same way:\n'
                              + c.stdout + c.stderr)
    try:
        return run(argv, repo)
    finally:
        _rc, parent = run(['git', '-C', str(repo), 'rev-parse', 'HEAD~1'], repo)
        if parent.strip() == before:
            subprocess.run(['git', '-C', str(repo), 'reset', '-q', '--soft', before],
                           capture_output=True)


def tiers_step(repo, rep):
    """Make any missing branch tier on origin and report it on `rep` -- the
    update's step 4a, and the one thing a repository still to be migrated
    gets before it is sent to the migration (Morgan, 2026-09-27: "the same
    issue with migrations: when migrating check for these and create
    them")."""
    tier_lines = []
    has_origin = run(['git', '-C', str(repo), 'remote', 'get-url', 'origin'],
                     repo)[0] == 0
    try:
        rc = pb.ensure_tiers(repo, apply=True, say=tier_lines.append) \
            if has_origin else 0
    except Exception as e:                                     # noqa: BLE001
        rc, tier_lines = 1, [f'{type(e).__name__}: {e}']
    made = [l for l in tier_lines if l.startswith(('created ', 'wrote '))]
    if not has_origin:
        rep.step('branch tiers', 'no origin remote here, so there is nowhere to '
                 'make them')
    elif rc != 0:
        rep.leave('branch tiers', 'pre-staging and staging could not both be '
                  'made on origin -- ' + ' '.join(tier_lines)[-400:])
    else:
        rep.step('branch tiers', '; '.join(made) if made else
                 'pre-staging, staging and main all present')


def update(repo, skip_check=False, ref=None):
    rep = Report()
    before = dirty_paths(repo)
    engine_tool = repo / 'tools' / 'precedent_vendor_engine.py'
    if not (repo / 'tools' / pve.MANIFEST_NAME).is_file() or not engine_tool.is_file():
        rep.leave(str(repo), "no vendored loader engine (tools/ENGINE_MANIFEST.json), "
                  "so this is a migration, not an update -- "
                  "spec/MIGRATING_EXISTING_INSTALLS.md")
        # The migration still gets its three branches now, from here.
        tiers_step(repo, rep)
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

    # The commit the vendored engine -- and so a section 0 catalogue, which
    # moves with it -- was last synced from. Read now: step 2 rewrites it.
    try:
        last_synced = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                                 .read_text(encoding='utf-8')).get('source_commit')
    except (OSError, ValueError):
        last_synced = None

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
    details = diverged_details(out)
    for item in left_block(out):
        what, _, why = item.partition(': ')
        why = why or item
        if what in details and '(listed above)' in why:
            why = why.replace('(listed above)', '(listed below)')
            rep.details[what] = details[what]
        rep.leave(what, why)
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
    else:
        # INSTALL.md section 2, step 0: a section 0 install vendors the
        # universal catalogue at its universal source's own path
        # (precedent/universal by default) and replaces it wholesale. Until
        # 2026-09-28 this command skipped it without a word and still said
        # DONE, so a section 0 repo kept its old rules under a new engine; a
        # session caught it only by reading the diff, and copied the
        # catalogue by hand.
        done = vendor_universal_catalogue(repo, rep, head.strip(), last_synced)
        if done is not True:
            return rep.close(done)

    # 3b. Where Go update lands, for a repository that has never said.
    # Morgan, 2026-09-27 (strength: decided): every repository lands on
    # pre-staging by default, set on its first update after that day; a
    # person's own identity.json still wins, and a value already here is
    # never changed.
    if pb.ensure_repo_landing(repo):
        rep.step('landing branch', f'{pb.LANDING_SETTING} set to '
                 f'{pb.REPO_LANDING_DEFAULT} in precedent.json (the repository '
                 f'default; a person\'s own identity.json still wins)')

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

    # 4a. The branch tiers. Every repository works through pre-staging ->
    # staging -> main, so a missing tier is made here rather than reported
    # (Morgan, 2026-09-27, strength: decided: "Can we make sure update
    # vendors checks for this and if they don't exist create it").
    # ensure_tiers makes staging from pre-staging (or the old staging name),
    # pre-staging from staging, and both from main when neither exists. It
    # is the one thing this command pushes: a new branch at a commit origin
    # already has, never a change to one that exists.
    tiers_step(repo, rep)

    # Staged before the check, so it judges what the commit will hold.
    adopted = adopt_engine_output(repo, before, head.strip())
    if adopted:
        before = before - set(adopted)
        rep.step('engine, written ahead', f'{len(adopted)} uncommitted path(s) '
                 f'already held the pinned engine (a source refresh ran first); '
                 f'staged as this update\'s: ' + ', '.join(adopted))
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

    # 5. The repo's own check, at the tier of the branch the update lands
    # on -- the gate before any push. Into pre-staging that is the fast
    # checks on what the update changed; the full check waits for the
    # Promote to staging (Morgan, 2026-09-27, strength: decided: "The point
    # of pre-staging is to move fast, so I want the 10 minute checks to
    # happen at the staging level, not pre-staging." Practice:
    # checks-follow-the-tier).
    check = repo / 'tools' / 'precedent_push_check.py'
    try:
        landing = pb.landing_branch(repo)[0]
    except Exception:                                          # noqa: BLE001
        landing = None
    argv = [sys.executable, str(check)]
    if landing:
        argv += ['--push-command', f'origin HEAD:{landing}']
    label = f'check for {landing}' if landing else 'deep check'
    if skip_check:
        rep.step(label, 'skipped (--skip-check) -- run it before pushing')
    elif check.is_file():
        rc, out = judged_as_committed(repo, argv)
        if rc != 0:
            return rep.close(f"the {label} is red:\n{tail(out)}")
        rep.step(label, 'passed')
    else:
        rep.step(label, 'this repo has no tools/precedent_push_check.py')
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

#!/usr/bin/env python3
"""precedent_three_way.py -- settle a vendored file edited here against the
version upstream ships now, so Update Vendors resolves it instead of
refusing over it.

WHY (Morgan, 2026-09-29). Update Vendors used to stop on any vendored file
edited in the consuming repo -- "hand-edited here and shipped by upstream
... Move the edit upstream, or refresh --force" -- and most of those edits
were local attempts to fix the same bug upstream had fixed. The refusal kept
a repo on its own patch, without upstream's fix, until someone decided by
hand. A refusal is not a resolution (practice: repair-cannot-discard-work).

THE RULES, by three-way comparison of BASE (the version this repo last
received), LOCAL (this repo's committed copy) and NEW (upstream's now):

  1  kept        NEW == BASE: upstream did not change it. LOCAL stays, and
                 the report says it is still a local edit and how to send it
                 upstream.
  2  merged      upstream changed it and a three-way merge is clean: the
                 merged file is written. It must pass a syntax check here and
                 the repo's own check in precedent_update.py, or it falls
                 back to rule 3.
  3  replaced    the merge conflicts, or NEW already carries LOCAL's change:
                 NEW is taken. Allowed only because LOCAL is committed, and
                 the report names the commit that holds it.
  4  customized  the repo declares the file its own in precedent.json
                 (KEEP_KEY, a reason per entry): never replaced; the report
                 says when upstream changed it.

An edit that is NOT committed is never touched: settle() returns it as
refused and the caller stops, as it always did. `--force` on the refresh and
on checkin.py keeps its meaning -- overwrite everything -- and never comes
here.

Callers: tools/precedent_update.py (the engine's tools/, hooks and declared
engine paths, and a section 0 catalogue) and tools/checkin.py update (a
migrated repo's process/upstream/ tree). One copy of the rules for all three.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

# precedent.json: {"<repo-relative path>": "why this repo keeps its own"}.
KEEP_KEY = 'kept_vendored_files'

KEPT, MERGED, REPLACED, CUSTOMIZED = 'kept', 'merged', 'replaced', 'customized'
RULES = (KEPT, MERGED, REPLACED, CUSTOMIZED)

HEADINGS = {
    KEPT: "Kept your edit -- upstream has not changed these since this repo "
          "last received them, so they are still local edits",
    MERGED: "Merged -- upstream's change and yours are both in the file now",
    REPLACED: "Took upstream's version -- upstream changed the same lines, "
              "and most likely fixed the same bug",
    CUSTOMIZED: f"Your own version, declared in precedent.json's {KEEP_KEY} "
                f"-- never replaced",
}


def send_upstream_hint(path, commit):
    """How a local version reaches upstream -- in one place, so the command
    that does it, when it exists, is named here once."""
    held = f'`git show {commit[:12]}:{path}`' if commit else f'`{path}`'
    if path.startswith('process/'):
        # A migrated repo's vendored tree has its own export route.
        return (f'to send it upstream, export it (INSTALL.md section 3, '
                f'`checkin.py push`); {held} is your version')
    return (f'to send it upstream, open a pull request against BestPractice '
            f'carrying the change ({held} is your version)')


class Resolution:
    """One vendored file settled by the rules above. `content` is what the
    file must hold afterwards, None meaning it must not exist."""

    def __init__(self, path, rule, content, new, why=''):
        self.path, self.rule, self.content, self.new = path, rule, content, new
        self.why = why
        self.commit = None       # the commit holding this repo's version
        self.fell_back = ''      # why a merge was undone (rule 2 -> 3)

    def fall_back(self, why):
        self.rule, self.content, self.fell_back = REPLACED, self.new, why

    def to_json(self):
        out = {'rule': self.rule, 'commit': self.commit, 'why': self.why}
        if self.fell_back:
            out['fell_back'] = self.fell_back
        return out


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def merge3(local, base, new):
    """-> (clean, merged bytes) of `git merge-file`, which needs no
    repository. A binary file or any error counts as a conflict."""
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for name, data in (('local', local), ('base', base), ('new', new)):
            p = pathlib.Path(td) / name
            p.write_bytes(data)
            paths.append(str(p))
        r = subprocess.run(['git', 'merge-file', '-p', '-q',
                            '-L', 'yours', '-L', 'base', '-L', 'upstream',
                            *paths], capture_output=True)
    return r.returncode == 0, r.stdout


def resolve(path, base, local, new, kept_reason=None):
    """-> the Resolution for one file, or None when there is nothing to
    settle: no committed local edit (LOCAL == BASE), or LOCAL is already
    upstream's (LOCAL == NEW). Each of base/local/new is bytes, or None where
    that side has no such file."""
    if kept_reason is not None:
        why = (f'"{kept_reason}"; ' + ('upstream has not changed it'
                                       if new == base else
                                       'upstream has changed it since this '
                                       'repo last received it -- compare the '
                                       'two when you want its change'))
        return Resolution(path, CUSTOMIZED, local, new, why)
    if local == base or local == new:
        return None
    if new == base:
        return Resolution(path, KEPT, local, new, 'upstream has not changed it')
    if base is None:
        return Resolution(path, REPLACED, new, new,
                          'there is no record of the version this repo last '
                          'received, so the two cannot be merged')
    if local is None or new is None:
        return Resolution(path, REPLACED, new, new,
                          'one side deleted the file and the other changed it')
    clean, merged = merge3(local, base, new)
    if clean and merged == new:
        return Resolution(path, REPLACED, new, new,
                          "upstream's version already carries this change")
    if clean:
        return Resolution(path, MERGED, merged, new,
                          "upstream's change and yours touch different lines")
    return Resolution(path, REPLACED, new, new, 'upstream changed the same lines')


def read_kept(repo):
    """-> ({path: reason}, [path declared without a reason]) from `repo`'s
    precedent.json. An unreadable file is no declaration."""
    try:
        declared = json.loads((pathlib.Path(repo) / 'precedent.json')
                              .read_text(encoding='utf-8')).get(KEEP_KEY) or {}
    except (OSError, ValueError, AttributeError):
        return {}, []
    if not isinstance(declared, dict):
        return {}, [KEEP_KEY]
    kept, bad = {}, []
    for path, reason in declared.items():
        rel = str(path).strip()
        rel = rel[2:] if rel.startswith('./') else rel
        if isinstance(reason, str) and reason.strip():
            kept[rel] = reason.strip()
        else:
            bad.append(str(path))
    return kept, bad


def has_head(repo):
    """-> True when `repo` has a commit to read LOCAL from. Without one,
    every file would read as absent at HEAD -- a deletion -- so a caller
    settles nothing and keeps its old refusal."""
    return subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', '-q',
                           'HEAD^{commit}'], capture_output=True).returncode == 0


def head_blob(repo, rel):
    """-> `rel` as committed at HEAD in `repo`, or None."""
    r = subprocess.run(['git', '-C', str(repo), 'show', f'HEAD:{rel}'],
                       capture_output=True)
    return r.stdout if r.returncode == 0 else None


def holding_commit(repo, rel):
    """-> the commit that last changed `rel` at HEAD: where this repo's
    version of it lives."""
    r = subprocess.run(['git', '-C', str(repo), 'log', '-1', '--format=%H',
                        'HEAD', '--', rel], capture_output=True, text=True)
    return (r.stdout.strip() or None) if r.returncode == 0 else None


def working(repo, rel):
    f = pathlib.Path(repo) / rel
    return f.read_bytes() if f.is_file() else None


def settle(repo, candidates, kept, dirty):
    """-> (resolutions, refused).

    `candidates` is [(repo-relative path, base, local, new)], LOCAL read from
    HEAD. `dirty` is every path `git status` reports. A path whose working
    copy differs from HEAD is refused -- a person's uncommitted edit -- unless
    it already holds what this would write, or upstream's version: the
    output of an earlier run that stopped before its commit."""
    out, refused = [], []
    for rel, base, local, new in candidates:
        r = resolve(rel, base, local, new, kept.get(rel))
        work = working(repo, rel)
        if rel in dirty and work != local:
            if not (work == new or (r is not None and work == r.content)):
                refused.append(rel)
                continue
        if r is not None:
            r.commit = holding_commit(repo, rel)
            out.append(r)
    return out, refused


def write(repo, rel, content):
    """Make `rel` hold `content`, or not exist when it is None. The mode of
    an existing file is kept."""
    f = pathlib.Path(repo) / rel
    if content is None:
        if f.is_file():
            f.unlink()
        return
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(content)


def syntax_problem(rel, data):
    """-> why `data` cannot be `rel` (a .py that does not compile, a .json
    that does not parse, a .sh bash will not read), or ''."""
    if data is None:
        return ''
    if rel.endswith('.py'):
        try:
            compile(data, rel, 'exec')
        except (SyntaxError, ValueError) as e:
            return f'it does not compile ({e.__class__.__name__}: {e})'
    elif rel.endswith('.json'):
        try:
            json.loads(data.decode('utf-8'))
        except (ValueError, UnicodeDecodeError) as e:
            return f'it is not valid JSON ({e})'
    elif rel.endswith('.sh'):
        r = subprocess.run(['bash', '-n', '/dev/stdin'], input=data,
                           capture_output=True)
        if r.returncode != 0:
            return f'bash cannot read it ({r.stderr.decode(errors="replace").strip()[:200]})'
    return ''


def check_merges(repo, resolutions):
    """Write back upstream's version of each merged file that fails its
    syntax check. -> the resolutions that fell back."""
    fell = []
    for r in resolutions:
        if r.rule != MERGED:
            continue
        why = syntax_problem(r.path, r.content)
        if why:
            r.fall_back(f'the merged file failed its syntax check: {why}')
            write(repo, r.path, r.content)
            fell.append(r)
    return fell


def report_lines(resolutions):
    """-> the plain-words block, grouped by rule, that a closing report
    prints. [] when nothing was settled."""
    if not resolutions:
        return []
    lines = ['VENDORED FILES EDITED HERE -- each settled against upstream, '
             'none left for you:']
    for rule in RULES:
        group = [r for r in resolutions if r.rule == rule]
        if not group:
            continue
        lines.append(f'  {HEADINGS[rule]}:')
        for r in group:
            at = f'commit {r.commit[:12]}' if r.commit else 'this repo\'s history'
            if rule == KEPT:
                tail = f'{r.why}; {send_upstream_hint(r.path, r.commit)}'
            elif rule == MERGED:
                tail = (f'{r.why}; yours alone is in {at} -- '
                        f'{send_upstream_hint(r.path, r.commit)}')
            elif rule == REPLACED:
                tail = ((f'{r.fell_back}, so ' if r.fell_back else f'{r.why}; ')
                        + f'your version is in {at}. If the bug it fixed is '
                        f'still there, bring it back with `git checkout '
                        f'{(r.commit or "<commit>")[:12]} -- {r.path}`, or '
                        + send_upstream_hint(r.path, r.commit))
            else:
                tail = r.why
            lines.append(f'    - {r.path}: {tail}')
    return lines


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    print((__doc__ or '').strip())
    sys.exit(0 if not sys.argv[1:] else 2)

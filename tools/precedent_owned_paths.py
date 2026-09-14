#!/usr/bin/env python3
"""precedent_owned_paths.py -- before a pull request, say which touched files
will wait for a code owner's review, in words a contributor can act on.

WHAT IT ANSWERS. A document project draws its boundary with `CODEOWNERS`
plus branch protection (spec/CONTRIBUTOR_ACCESS.md, layer 2): a pull
request touching only unowned paths is the contributor's to merge, one
touching an owned path waits for the maintainer. The contributor cannot see
that line -- it is a file they never open, in a directory they never look
in -- so the first they hear of it is a merge button that will not press,
and an error written for a developer. This tool is the sentence the session
says INSTEAD, before the pull request exists: "this touches the project's
settings, so <owner> has to look at it before it lands; the document part
can go in on its own now." It is user experience, not enforcement -- the
boundary is GitHub's, and stays GitHub's, whatever this prints.

WHY IT KEYS ON PATHS. Nothing here asks what kind of person is running,
because nothing can answer that (practice: technical-describes-people). It
asks which files changed and what `CODEOWNERS` says about each, which both
have machine-readable answers.

WHAT IT READS. `CODEOWNERS` at `.github/`, the root, or `docs/` -- the three
places GitHub looks, in that order. The touched set is the union of what
differs from the base branch, what is modified in the working tree, and
what is untracked, so a preview before the commit and one before the push
see the same files. The base is `origin/<base_branch>` from
`precedent.json`, then `origin/main`, then nothing -- and when no base ref
resolves the preview says so and continues on the working tree alone
rather than reporting a clean pull request it could not see (practice:
fail-gracefully).

MATCHING follows GitHub's own CODEOWNERS rules as far as they are
documented: a pattern is gitignore-shaped, a leading `/` anchors it at the
repository root, a trailing `/` means the directory's contents, `*` stops
at a slash and `**` does not, a pattern with no slash matches a basename
anywhere, and the LAST matching pattern wins. A pattern this tool cannot
translate is reported, never silently skipped -- a boundary that is
"probably" honoured is the one that lets a change through.

Run:  python3 tools/precedent_owned_paths.py [--repo PATH] [--base REF]
      python3 tools/precedent_owned_paths.py --check   # exit 1 if any owned path is touched

Exit 0 always in preview mode: the tool informs, and the person decides
whether to split the change. `--check` is for a hook or a workflow that
wants "no owned path touched" as a gate.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

CODEOWNERS_LOCATIONS = ('.github/CODEOWNERS', 'CODEOWNERS', 'docs/CODEOWNERS')


def _git(repo, *args):
    """-> (exit code, stdout). Callers read the CODE: `rev-parse` echoes a
    missing ref and `diff` against one prints nothing, so stdout alone
    cannot tell "nothing changed" from "could not look" (AGENTS.md gotcha
    g2)."""
    p = subprocess.run(['git', '-C', str(repo), *args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def find_codeowners(repo):
    for rel in CODEOWNERS_LOCATIONS:
        f = pathlib.Path(repo) / rel
        if f.is_file():
            return f
    return None


def parse_codeowners(text):
    """-> list of (pattern, [owners], line number), in file order."""
    rules = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        rules.append((parts[0], parts[1:], n))
    return rules


def pattern_to_regex(pattern):
    """A CODEOWNERS pattern -> a compiled regex over a repo-relative path,
    or None for a pattern this translation does not cover."""
    pat = pattern
    if not pat or pat.startswith('!') or '[' in pat:
        return None  # negation and character classes: not supported by GitHub either
    anchored = pat.startswith('/')
    if anchored:
        pat = pat[1:]
    dir_only = pat.endswith('/')
    if dir_only:
        pat = pat[:-1]
    if not pat:
        return None
    # A pattern with no slash matches a basename at any depth; one with a
    # slash is anchored to the root, as gitignore does it.
    has_slash = '/' in pat
    out = ''
    i = 0
    while i < len(pat):
        c = pat[i]
        if c == '*':
            if pat[i:i + 2] == '**':
                out += '.*'
                i += 2
                continue
            out += '[^/]*'
        elif c == '?':
            out += '[^/]'
        else:
            out += re.escape(c)
        i += 1
    if anchored or has_slash:
        prefix = '^'
    else:
        prefix = '^(?:.*/)?'
    if dir_only:
        suffix = '/.*$'
    else:
        # `docs` matches the file `docs` and everything under `docs/`, which
        # is GitHub's behaviour for a pattern naming a directory.
        suffix = '(?:/.*)?$'
    return re.compile(prefix + out + suffix)


def owners_for(path, rules):
    """-> (owners, pattern) from the LAST matching rule, or ([], None)."""
    hit = ([], None)
    for pattern, owners, _ in rules:
        rx = pattern_to_regex(pattern)
        if rx is not None and rx.match(path):
            hit = (owners, pattern)
    return hit


def untranslatable(rules):
    return [(p, n) for p, _, n in rules if pattern_to_regex(p) is None]


def declared_base(repo):
    f = pathlib.Path(repo) / 'precedent.json'
    if f.is_file():
        try:
            b = json.loads(f.read_text(encoding='utf-8')).get('base_branch')
            if isinstance(b, str) and b.strip():
                return b.strip()
        except (OSError, json.JSONDecodeError):
            pass
    return None


def touched_paths(repo, base=None):
    """-> (sorted paths, base ref used or None, note). The union of what
    differs from the base, what is modified in the tree, and what is
    untracked."""
    paths = set()
    note = ''
    used = None
    candidates = [base] if base else []
    declared = declared_base(repo)
    if declared:
        candidates.append(f'origin/{declared}')
    if 'origin/main' not in candidates:
        candidates.append('origin/main')
    for ref in candidates:
        code, _ = _git(repo, 'rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}')
        if code == 0:
            used = ref
            break
    if used:
        code, out = _git(repo, 'diff', '--name-only', f'{used}...HEAD')
        if code != 0:
            # No merge base (a shallow clone, gotcha g12) -- fall back to a
            # two-dot diff, which is the whole difference and still an answer.
            code, out = _git(repo, 'diff', '--name-only', used, 'HEAD')
        if code == 0:
            paths.update(l for l in out.splitlines() if l)
        else:
            note = f'could not diff against {used}; previewing the working tree only'
            used = None
    else:
        note = ('no base ref resolved (tried ' + ', '.join(candidates) +
                '); previewing the working tree only -- committed changes on '
                'this branch are NOT in this preview')
    code, out = _git(repo, 'diff', '--name-only', 'HEAD')
    if code == 0:
        paths.update(l for l in out.splitlines() if l)
    code, out = _git(repo, 'ls-files', '--others', '--exclude-standard')
    if code == 0:
        paths.update(l for l in out.splitlines() if l)
    return sorted(paths), used, note


def assess(repo, base=None):
    """-> dict with 'owned' [(path, owners, pattern)], 'free' [path],
    'codeowners' path or None, 'base', 'note', 'untranslatable'."""
    f = find_codeowners(repo)
    paths, used, note = touched_paths(repo, base)
    if f is None:
        return {'codeowners': None, 'owned': [], 'free': paths, 'base': used,
                'note': note, 'untranslatable': []}
    rules = parse_codeowners(f.read_text(encoding='utf-8'))
    try:
        f = f.relative_to(pathlib.Path(repo).resolve())
    except ValueError:
        pass
    owned, free = [], []
    for p in paths:
        owners, pattern = owners_for(p, rules)
        if owners:
            owned.append((p, owners, pattern))
        else:
            free.append(p)
    return {'codeowners': f, 'owned': owned, 'free': free, 'base': used,
            'note': note, 'untranslatable': untranslatable(rules)}


def plain_words(result):
    """The sentence the session says to the contributor. Written for a
    reader who does not know what CODEOWNERS is and should not have to."""
    owned, free = result['owned'], result['free']
    if not owned and not free:
        return 'Nothing has changed yet, so there is nothing to send for review.'
    if not owned:
        n = len(free)
        return (f'All {n} changed file{"s" if n != 1 else ""} '
                f'{"are" if n != 1 else "is"} yours to merge -- nothing here '
                f'needs anyone else to look at it first.')
    owners = sorted({o for _, os_, _ in owned for o in os_})
    who = ' and '.join(owners)
    has = 'have' if len(owners) != 1 else 'has'
    n = len(owned)
    s = (f'{n} of the changed files {"are" if n != 1 else "is"} part of the '
         f'project\'s machinery, so {who} {has} to look at {"them" if n != 1 else "it"} '
         f'before this lands: ' + ', '.join(p for p, _, _ in owned) + '.')
    if free:
        m = len(free)
        s += (f' The other {m} file{"s" if m != 1 else ""} '
              f'{"are" if m != 1 else "is"} yours to merge. Want '
              f'{"those" if m != 1 else "that one"} to go in on '
              f'{"their" if m != 1 else "its"} own now, and the rest to wait '
              f'for {who}?')
    else:
        s += f' It waits for {who}; nothing in it can go in on its own.'
    return s


def report(result, out=None):
    # Resolved at call time, not definition time: a default bound to the
    # sys.stdout of import is invisible to any caller redirecting stdout.
    out = sys.stdout if out is None else out
    if result['codeowners'] is None:
        print('owned-paths: NO BOUNDARY -- no CODEOWNERS at any of '
              + ', '.join(CODEOWNERS_LOCATIONS) + '. Nothing here waits for '
              'review, which in a document project means the boundary is '
              'missing, not that the change is clean '
              '(python3 tools/precedent_boundary_check.py says whether the '
              'protection side exists).', file=out)
        return
    if result['note']:
        print(f'owned-paths: NOTE {result["note"]}', file=out)
    for pattern, n in result['untranslatable']:
        print(f'owned-paths: NOTE {result["codeowners"]} line {n}: pattern '
              f'{pattern!r} is not one this tool can match; a file it covers '
              f'may be reported as free. Simplify the pattern.', file=out)
    base = result['base'] or 'the working tree only'
    print(f'owned-paths: {len(result["owned"])} owned, {len(result["free"])} '
          f'free (against {base}; rules from {result["codeowners"]})', file=out)
    for p, owners, pattern in result['owned']:
        print(f'  OWNED  {p}  ->  {" ".join(owners)}  ({pattern})', file=out)
    for p in result['free']:
        print(f'  free   {p}', file=out)
    print('', file=out)
    print('Say to the contributor:', file=out)
    print('  ' + plain_words(result), file=out)


def main(argv):
    if any(a in ('--help', '-h') for a in argv):
        print((__doc__ or '').strip())
        return 0
    repo = pathlib.Path(os.getcwd())
    base = None
    check_only = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--repo' and i + 1 < len(argv):
            repo = pathlib.Path(argv[i + 1]).resolve()
            i += 2
        elif a == '--base' and i + 1 < len(argv):
            base = argv[i + 1]
            i += 2
        elif a == '--check':
            check_only = True
            i += 1
        else:
            print(f'owned-paths FAIL: unknown argument {a!r}. Takes --repo PATH, '
                  f'--base REF, --check.', file=sys.stderr)
            return 2
    code, _ = _git(repo, 'rev-parse', '--git-dir')
    if code != 0:
        print(f'owned-paths FAIL: {repo} is not a git repository', file=sys.stderr)
        return 2
    result = assess(repo, base)
    report(result)
    if check_only and result['owned']:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

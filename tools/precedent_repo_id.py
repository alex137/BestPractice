#!/usr/bin/env python3
"""One answer to "is this the same repository?", whatever the spelling.

Every tool that compares, looks up, counts or de-duplicates repositories by
name, URL or a clone's origin goes through here. Nothing in tools/ compares
two repository names with `==`, `in` or `.lower()` of its own; the engine
check `repo-name-compare-via-helper` fails a tool that does.

Two rules, both Morgan's (2026-10-31, strength: decided): "in any way the
repo names are used, the capitalization should never matter ... the same
repo with different capitalization should be treated equally", and every
place Precedent writes a repository's name uses "the same capitalization as
is used in the official name of the repo".

So there are two kinds of function here:

* COMPARING -- `repo_key`, `same_repo`, `find_repo`: case never matters on
  github.com, where GitHub forbids two repositories under one owner whose
  names differ only in case. Any other host keeps its case: a self-hosted
  server may be case-sensitive, and folding there could make two
  repositories one.
* WRITING -- `declared_spelling`, `owner_repo`: the spelling that goes on
  record is the one a repository's precedent.json declares, never a clone's
  origin. The platform hands sessions lowercase clone URLs (add_repo on
  `owner/SomeSet` answers `owner/someset`), so an origin is evidence of
  WHICH repository, never of how its name is spelled.

WHY (2026-10-31). A consuming repository's session asked Morgan to approve
one repository twice, SomeSet and then someset, and its records
already spelled two sources two ways (precedent.json capitalized, the copy
manifests lowercase, because checkin.py copied the clone's origin in). The
freshness check compared a declared URL to a clone's origin with `==` and
printed NOT VERIFIED for a source it could read. Four earlier fixes
(a56ef8cb, 561a37f0, a78d30dc, 8e938154) each mended one tool; the next tool
compared letter for letter again. One module and one check is the fix
(practice: upstream-fix; practice: judgment-check-or-tool -- a mechanism
gets one tool). The write-up is in that consuming repository's spec/
folder, REPO_NAME_CAPITALIZATION.md.

Usage:
    python3 tools/precedent_repo_id.py KEY URL_OR_NAME   # print its key
    python3 tools/precedent_repo_id.py SAME A B          # exit 0 if same
"""
import json
import pathlib
import re
import sys

# Hosts whose repository paths are case-insensitive. github.com only: it
# redirects and refuses a second repository that differs only in case.
CASE_INSENSITIVE_HOSTS = frozenset({'github.com', 'www.github.com'})

# The forms a GitHub repository is written in, in the wild: https with or
# without credentials, ssh (scp form and URL form), a local git proxy that
# carries the owner/repo after a /git/ segment, and a bare owner/repo.
_URL = re.compile(
    r'^(?:[a-z][a-z0-9+.-]*://)?'          # scheme
    r'(?:[^@/\s]+@)?'                       # user[:token]@
    r'(?P<host>[^/:\s]+)(?::\d+)?'          # host[:port]
    r'[/:](?P<path>.+)$', re.I)


class RepoId:
    """A parsed repository: host ('' when unknown), owner ('' for a bare
    name) and name, each in the spelling it was given."""
    __slots__ = ('host', 'owner', 'name')

    def __init__(self, host, owner, name):
        self.host, self.owner, self.name = host, owner, name

    def __repr__(self):
        return f'RepoId({self.host!r}, {self.owner!r}, {self.name!r})'

    @property
    def full(self):
        """owner/name in the given spelling, or the bare name."""
        return f'{self.owner}/{self.name}' if self.owner else self.name

    def key(self):
        host = (self.host or 'github.com').lower()
        if host == 'www.github.com':
            host = 'github.com'
        text = f'{self.owner}/{self.name}' if self.owner else self.name
        return f'{host}/' + (text.lower() if host in CASE_INSENSITIVE_HOSTS
                             else text)


def _strip(text):
    text = str(text or '').strip().rstrip('/')
    if text.endswith('.git'):
        text = text[:-4]
    return text.rstrip('/')


def parse(spec):
    """-> RepoId for a URL, an owner/repo or a bare repository name; None
    for nothing usable (an empty value, a local path)."""
    text = _strip(spec)
    if not text or text.startswith(('/', '.', '~')):
        return None
    m = _URL.match(text) if ('://' in text or '@' in text
                             or re.match(r'^[^/\s]+\.[a-z]{2,}[/:]', text, re.I)) \
        else None
    if m:
        host = m.group('host').lower()
        parts = [p for p in m.group('path').split('/') if p]
        # A local git proxy: http://proxy@127.0.0.1:PORT/git/owner/repo.
        if 'git' in parts[:-2]:
            parts = parts[parts.index('git') + 1:]
            if host in ('127.0.0.1', 'localhost') or host.startswith('127.'):
                host = 'github.com'
        if len(parts) < 2:
            return None
        return RepoId(host, parts[-2], parts[-1])
    parts = [p for p in text.split('/') if p]
    if len(parts) == 1:
        return RepoId('', '', parts[0])
    if len(parts) == 2:
        return RepoId('', parts[0], parts[1])
    return None


def repo_key(spec):
    """-> the one comparison key for `spec`, or '' when it names no
    repository. Two spellings of one github.com repository give one key; a
    bare name gives a key that only `same_repo` compares loosely."""
    rid = parse(spec)
    return rid.key() if rid else ''


def same_repo(a, b):
    """True when `a` and `b` name one repository. A bare name (no owner)
    matches any owner's repository of that name: it is all a caller knew."""
    ra, rb = parse(a), parse(b)
    if not ra or not rb:
        return False
    if ra.owner and rb.owner:
        return ra.key() == rb.key()
    host = (ra.host or rb.host or 'github.com').lower()
    if host in CASE_INSENSITIVE_HOSTS:
        return ra.name.lower() == rb.name.lower()
    return ra.name == rb.name


def same_name(a, b):
    """True when two bare names (an owner, a repository name, a folder named
    for one) are one name on GitHub: case does not matter."""
    return str(a or '').strip().lower() == str(b or '').strip().lower()


def find_repo(spec, candidates):
    """-> the first of `candidates` that names the same repository as
    `spec`, in the candidate's own spelling, or None."""
    for c in candidates or ():
        if same_repo(spec, c):
            return c
    return None


def owner_repo(spec):
    """-> 'owner/name' in the spelling `spec` gives, or '' for none."""
    rid = parse(spec)
    return rid.full if rid and rid.owner else ''


def declared_repos(root):
    """-> every `repo` URL `root`'s precedent.json declares, as written."""
    try:
        cfg = json.loads((pathlib.Path(root) / 'precedent.json').read_text(
            encoding='utf-8'))
    except (OSError, ValueError):
        return []
    out = []
    for e in (cfg.get('sources') or []) if isinstance(cfg, dict) else []:
        if isinstance(e, dict) and str(e.get('repo') or '').strip():
            out.append(str(e['repo']).strip())
    return out


def declared_spelling(spec, root=None, declared=None):
    """-> the spelling to WRITE for `spec`: the declaration in `root`'s
    precedent.json (or in `declared`) naming the same repository, else
    `spec` as given. An origin URL never decides the spelling on record
    when a declaration names its repository."""
    pool = list(declared or ()) + (declared_repos(root) if root else [])
    hit = find_repo(spec, pool)
    return hit if hit else (str(spec).strip() if spec else spec)


# THE CHECK THAT KEEPS RAW COMPARISONS OUT (engine check
# `repo-name-compare-via-helper`). It reads Python by its syntax tree and
# flags a comparison (==, !=, in, not in) or a .lower()/.casefold() applied
# to something named like a repository -- an origin, a repo URL, an
# owner/repo, a full_name, f'{owner}/{name}' -- anywhere outside this file.
# It is a name heuristic: a variable called `u` holding an origin URL gets
# past it. What it stops is the shape every earlier one-tool fix took.
_REPO_WORD = re.compile(
    r'(?:^|_)(origins?|origin_urls?|repo_urls?|remote_urls?|clone_urls?|'
    r'url_repo|owner_repos?|full_names?|repo_slugs?|origin_slugs?|'
    r'upstream_repos?|github_repos?|repo_full|nwo)(?:$|_)', re.I)
_REPO_KEYS = {'repo', 'repo_url', 'origin', 'full_name', 'clone_url',
              'owner_repo'}
_REPO_FUNCS = re.compile(r'^_?(origin_url|origin_slug|repo_slug|'
                         r'remote_owner_repo|detect_github_repo|owner_repo)$')


def _repoish(node):
    import ast
    if isinstance(node, ast.Name):
        return bool(_REPO_WORD.search(node.id))
    if isinstance(node, ast.Attribute):
        return bool(_REPO_WORD.search(node.attr))
    if isinstance(node, ast.Subscript):
        k = node.slice
        return isinstance(k, ast.Constant) and k.value in _REPO_KEYS
    if isinstance(node, ast.Call):
        f = node.func
        name = f.id if isinstance(f, ast.Name) else (
            f.attr if isinstance(f, ast.Attribute) else '')
        if _REPO_FUNCS.match(name):
            return True
        if name == 'get' and node.args and isinstance(node.args[0], ast.Constant) \
                and node.args[0].value in _REPO_KEYS:
            return True
        if isinstance(f, ast.Attribute) and name in (
                'lower', 'casefold', 'strip', 'rstrip', 'removesuffix'):
            return _repoish(f.value)
        return False
    if isinstance(node, ast.JoinedStr):
        lits = ''.join(v.value for v in node.values
                       if isinstance(v, ast.Constant) and isinstance(v.value, str))
        parts = [ast.unparse(v.value) for v in node.values
                 if isinstance(v, ast.FormattedValue)]
        return lits.strip() == '/' and len(parts) == 2 \
            and bool(re.search(r'owner|org', parts[0], re.I))
    return False


def _folded(node):
    import ast
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in ('lower', 'casefold')
            and _repoish(node.func.value))


def raw_comparisons(path):
    """-> [(line, source)] for each comparison or case fold of a
    repository name in the Python file `path` that does not go through this
    module. A line carrying `repo-name-compare: ok -- <why>` is let through:
    the why is the record that someone looked."""
    import ast
    try:
        text = pathlib.Path(path).read_text(encoding='utf-8')
        tree = ast.parse(text)
    except (OSError, SyntaxError, ValueError):
        return []
    lines = text.splitlines()
    out, seen = [], set()
    for node in ast.walk(tree):
        hit = False
        if isinstance(node, ast.Compare):
            ops = [node.left] + node.comparators
            for op, left, right in zip(node.ops, ops, ops[1:]):
                if isinstance(op, (ast.In, ast.NotIn)):
                    hit = hit or (_repoish(left)
                                  and not isinstance(left, ast.Constant))
                elif isinstance(op, (ast.Eq, ast.NotEq)):
                    if any(isinstance(o, ast.Constant) and (
                            o.value is None or not isinstance(o.value, str)
                            or '/' not in o.value and not o.value.isalpha())
                           for o in (left, right)):
                        continue
                    hit = hit or _repoish(left) or _repoish(right)
        elif _folded(node):
            hit = True
        if not hit or node.lineno in seen:
            continue
        line = lines[node.lineno - 1] if node.lineno <= len(lines) else ''
        if 'repo-name-compare: ok' in line:
            continue
        seen.add(node.lineno)
        out.append((node.lineno, ast.unparse(node)[:120]))
    return sorted(out)


def _main(argv):
    if len(argv) == 3 and argv[1].upper() == 'KEY':
        print(repo_key(argv[2]))
        return 0 if repo_key(argv[2]) else 1
    if len(argv) == 4 and argv[1].upper() == 'SAME':
        same = same_repo(argv[2], argv[3])
        print('same' if same else 'different')
        return 0 if same else 1
    print(__doc__.split('Usage:', 1)[1].rstrip(), file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(_main(sys.argv))

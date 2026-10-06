"""precedent_audience.py -- whether the person in this session is one of the
repository's code owners, so a practice marked for code owners is shown only
to them.

    python3 tools/precedent_audience.py [--repo DIR]   # the answer, and why

A practice declares `visible_to: code-owners` when it is about running the
repository rather than working in it: GitHub, branches, CI, vendoring,
installs, repo audits. Morgan, 2026-10-05 (strength: decided): "for this new
rule *as well as other rules related to repo maintenance*, they should NOT be
shown to a user who is NOT a CODEOWNER".

WHO THE PERSON IS comes from a declaration only: the `github` username in
their identity.json (precedent_identity.declared_identity), or
PRECEDENT_GITHUB_USER. Their email also counts, since a CODEOWNERS line may
name an address.

WHO OWNS THE REPOSITORY is its CODEOWNERS file, in the three places GitHub
reads it: .github/CODEOWNERS, CODEOWNERS, docs/CODEOWNERS. Any owner on any
line counts. A team (`@org/team`) cannot be resolved offline and matches no
one. With no file, the registry the file is generated from answers instead
(tools/build_codeowners.py): approvers.json, then precedent.json's
`maintainers`, then, in an individual set, its own identity.json. With none
of those, the account that owns the repository on GitHub (its origin URL)
is its owner (2026-10-06).

IN DOUBT, HIDDEN. No owners named anywhere, no username declared, or an unreadable
identity all answer "not a code owner", with the reason, so the session can
say once why the rules are hidden (Morgan, 2026-10-05: hide them, and say
why). The checks behind a hidden practice still run on every push: hiding
changes what a session is TOLD, never what the repository enforces.
"""
import os
import pathlib
import re
import sys

CODE_OWNERS = 'code-owners'
FIELD = 'visible_to'
CODEOWNERS_PLACES = ('.github/CODEOWNERS', 'CODEOWNERS', 'docs/CODEOWNERS')

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent


def codeowners_file(repo):
    """-> the CODEOWNERS path GitHub would read for `repo`, or None."""
    root = pathlib.Path(repo)
    for rel in CODEOWNERS_PLACES:
        f = root / rel
        if f.is_file():
            return f
    return None


def _registry_owners(repo):
    """-> (owners, where) from the registry CODEOWNERS is generated from, or
    (None, None). tools/build_codeowners.py builds a practice set's file from
    approvers.json and a project's from precedent.json's `maintainers`; a
    repository may declare its maintainers there without generating the file
    (BestPractice does, so GitHub requests no reviews), and an individual set
    is owned by the one person whose identity.json it holds."""
    import json
    root = pathlib.Path(repo)
    found = set()
    try:
        data = json.loads((root / 'approvers.json').read_text(encoding='utf-8'))
        for a in data.get('approvers') or []:
            if isinstance(a, dict) and a.get('github'):
                found.add('@' + str(a['github']).lstrip('@').lower())
        if found:
            return found, 'approvers.json'
    except (OSError, ValueError, AttributeError):
        pass
    try:
        data = json.loads((root / 'precedent.json').read_text(encoding='utf-8'))
        for m in data.get('maintainers') or []:
            if isinstance(m, dict) and m.get('github'):
                found.add('@' + str(m['github']).lstrip('@').lower())
        if found:
            return found, "precedent.json's maintainers"
    except (OSError, ValueError, AttributeError):
        pass
    try:
        data = json.loads((root / 'identity.json').read_text(encoding='utf-8'))
        if data.get('github'):
            found.add('@' + str(data['github']).lstrip('@').lower())
        if data.get('email'):
            found.add(str(data['email']).lower())
        if found:
            return found, 'identity.json (this is an individual practice set)'
    except (OSError, ValueError, AttributeError):
        pass
    return None, None


def _repository_owner(repo):
    """-> (['@owner'], where) for the account that owns `repo` on GitHub, read
    from its origin URL, or (None, None). The last fallback in owners():
    with nothing declared, the account the repository lives under owns it.
    Reported 2026-10-06 from a consumer: its owner and only member asked for
    the Produce rule and was told it is for code owners only, of whom the
    repository names none -- a rule hidden from the one person it was for."""
    import subprocess
    try:
        url = subprocess.run(['git', '-C', str(repo), 'remote', 'get-url',
                              'origin'], capture_output=True, text=True,
                             timeout=10).stdout.strip()
    except Exception:                                        # noqa: BLE001
        return None, None
    m = re.search(r'github\.com[:/]+([^/\s]+)/[^/\s]+?(?:\.git)?/?$', url)
    if not m:
        return None, None
    return {f'@{m.group(1).lower()}'}, f'the owner of its GitHub origin ({m.group(1)})'


def _declared_or_owner(repo):
    found, where = _registry_owners(repo)
    if found:
        return found, where
    return _repository_owner(repo)


def owners(repo):
    """-> (owners, where): the lowercased owners named in the CODEOWNERS file
    (`@user`, `@org/team`, or an email), or, with no file, in the registry it
    is generated from, or, with neither, the account that owns the
    repository on GitHub. (None, None) when none of them names anyone."""
    f = codeowners_file(repo)
    if f is None:
        return _declared_or_owner(repo)
    try:
        text = f.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return _declared_or_owner(repo)
    out = set()
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        for tok in line.split()[1:]:
            if tok.startswith('@') or '@' in tok:
                out.add(tok.lower())
    return out, str(f.relative_to(repo)) if f.is_relative_to(repo) else f.name


def viewer(repo):
    """-> (github_username, email) declared for this session's person; either
    may be ''."""
    gh = os.environ.get('PRECEDENT_GITHUB_USER', '').strip()
    email = ''
    try:
        sys.path.insert(0, str(_ENGINE_DIR))
        import precedent_identity as pid
        ident = pid.declared_identity(repo)
        gh = gh or (ident.get('github') or '').strip()
        email = (ident.get('email') or '').strip()
    except Exception:                                        # noqa: BLE001
        pass
    return gh.lstrip('@'), email


def is_code_owner(repo):
    """-> (bool, why). False whenever it cannot be shown to be True."""
    repo = pathlib.Path(repo).resolve()
    names, where = owners(repo)
    if not names:
        return False, ('this repository names no code owners: no CODEOWNERS '
                       'file, no approvers.json or `maintainers` in '
                       'precedent.json, and no GitHub origin whose owner could '
                       'stand in')
    gh, email = viewer(repo)
    if not gh and not email:
        return False, ('no GitHub username is declared for you: add '
                       '"github": "<your username>" to the identity.json in '
                       'your individual practice set')
    if gh and f'@{gh.lower()}' in names:
        return True, f'@{gh} is named in {where}'
    if email and email.lower() in names:
        return True, f'{email} is named in {where}'
    if not gh:
        return False, (f'{email} is not named in {where}, and no GitHub '
                       f'username is declared for you to match instead: add '
                       f'"github": "<your username>" to your identity.json')
    return False, f'@{gh} is not named in {where}'


def for_code_owners(fm):
    """Whether a practice's frontmatter marks it for code owners only."""
    raw = fm.get(FIELD) if isinstance(fm, dict) else None
    return str(raw or '').strip().strip('"\'') == CODE_OWNERS


_CACHE = {}


def visible(fm, repo):
    """Whether a practice with frontmatter `fm` is shown in `repo`'s session."""
    if not for_code_owners(fm):
        return True
    key = str(pathlib.Path(repo).resolve())
    if key not in _CACHE:
        _CACHE[key] = is_code_owner(repo)
    return _CACHE[key][0]


def filter_resolved(practices, repo):
    """-> (kept, hidden_slugs) for a resolve()['practices'] mapping."""
    kept, hidden = {}, []
    for slug, p in practices.items():
        if visible(p.get('fm') or {}, repo):
            kept[slug] = p
        else:
            hidden.append(slug)
    return kept, sorted(hidden)


def hidden_notice(repo, hidden):
    """-> one line saying why some practices are hidden, or '' when none are."""
    if not hidden:
        return ''
    ok, why = is_code_owner(repo)
    return (f'{len(hidden)} practice(s) about running this repository (GitHub, '
            f'branches, CI, vendoring, installs) are for its code owners only '
            f'and are not shown in this session: {why}.')


def main(argv):
    repo = '.'
    if '--repo' in argv:
        repo = argv[argv.index('--repo') + 1]
    ok, why = is_code_owner(repo)
    print(f"{'code owner' if ok else 'not a code owner'}: {why}")
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))

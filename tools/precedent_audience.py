"""precedent_audience.py -- whether the person in this session is one of the
repository's code owners, so a practice marked for code owners is shown only
to them.

    python3 tools/precedent_audience.py [--repo DIR]   # the answer, and why

A practice declares `visible_to: code-owners` when it is about running the
repository rather than working in it: GitHub, branches, CI, vendoring,
installs, repo audits. Morgan, 2026-10-05 (strength: decided): "for this new
rule *as well as other rules related to repo maintenance*, they should NOT be
shown to a user who is NOT a CODEOWNER".

WHO THE PERSON IS: PRECEDENT_GITHUB_USER, else the `github` username in
their identity.json (precedent_identity.declared_identity), else the login
this clone's git config keeps (the installer's --admin, or an earlier
lookup), else the GitHub account the session's token belongs to (2026-10-17; see
viewer_and_source). Their email also counts, since a CODEOWNERS line may
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

NOT ONLY PRACTICES: WHAT IS SAID (Morgan, 2026-10-12, strength: decided:
"Anything on the inner works of how BP works including things like file
management, dealing with temporary files, dealing with temporary repos etc
-- should only be for codeowners. We must assume that non-codeowners are
very low tech people."). A check or tool that would have a session explain
a mechanism asks is_code_owner first (practice:
inner-workings-for-code-owners).
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


# The person's GitHub login as this clone last learned it, in the clone's
# own git config (untracked, never pushed, never seen by another clone or a
# test fixture): written by the installer's --admin, or by the first lookup
# of the account the session's token belongs to.
LOGIN_CONFIG_KEY = 'precedent.githubLogin'
LOGIN_FROM_KEY = 'precedent.githubLoginFrom'


def _git_config(repo, *args):
    import subprocess
    try:
        r = subprocess.run(['git', '-C', str(repo), 'config', '--local', *args],
                           capture_output=True, text=True, timeout=10)
    except Exception:                                        # noqa: BLE001
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _cached_login(repo):
    """-> (login, where) kept in this clone's git config, or ('', '')."""
    login = _git_config(repo, '--get', LOGIN_CONFIG_KEY) or ''
    if not re.fullmatch(r'[A-Za-z0-9-]+', login):
        return '', ''
    why = _git_config(repo, '--get', LOGIN_FROM_KEY) or ''
    return login, f'this clone\'s git config ({LOGIN_CONFIG_KEY}{", " + why if why else ""})'


def remember_login(repo, login, why, replace=False):
    """Keep `login` in `repo`'s git config as the person working in it,
    unless one is kept already (or `replace`). -> True when written. Never
    raises."""
    login = str(login or '').strip().lstrip('@')
    if not re.fullmatch(r'[A-Za-z0-9-]+', login):
        return False
    if not replace and _cached_login(repo)[0]:
        return False
    if _git_config(repo, LOGIN_CONFIG_KEY, login) is None:
        return False
    _git_config(repo, LOGIN_FROM_KEY, why)
    return True


def viewer_and_source(repo, lookup=True):
    """-> (github_username, email, where the username came from). Either
    value may be ''.

    WHO "YOU" ARE, in order: PRECEDENT_GITHUB_USER; the `github` in a
    declared identity.json (this repo's own, or the individual set's); the
    login kept in this clone's git config (the installer's --admin, or an
    earlier lookup); and last the account the session's
    token belongs to -- the same api.github.com/user answer
    commit-identity.sh's fifth rung reads, with the same
    PRECEDENT_GITHUB_USER_URL override -- kept after the first lookup so it
    is asked once per clone.

    Until 2026-10-17 only the first two counted, so a person with no
    individual set was a code owner nowhere: the very deep check of that
    day installed a project as its only administrator, with --admin, and
    was shown none of the 28 practices for code owners, Update Vendors
    among them."""
    gh = os.environ.get('PRECEDENT_GITHUB_USER', '').strip()
    where = 'PRECEDENT_GITHUB_USER' if gh else ''
    email = ''
    try:
        sys.path.insert(0, str(_ENGINE_DIR))
        import precedent_identity as pid
        ident = pid.declared_identity(repo)
        if not gh and (ident.get('github') or '').strip():
            gh, where = ident['github'].strip(), ident.get('source') or 'identity.json'
        email = (ident.get('email') or '').strip()
    except Exception:                                        # noqa: BLE001
        pass
    if not gh:
        gh, where = _cached_login(repo)
    if not gh and lookup:
        try:
            import precedent_source_credentials as psc
            gh = psc.token_account(timeout=5)
        except Exception:                                    # noqa: BLE001
            gh = ''
        if gh:
            where = 'the GitHub account this session is authenticated as'
            remember_login(repo, gh, where)
    return gh.lstrip('@'), email, where


def viewer(repo):
    """-> (github_username, email) for this session's person; either may be
    ''. See viewer_and_source for where each comes from."""
    gh, email, _where = viewer_and_source(repo)
    return gh, email


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
        return False, ('no GitHub username is known for you: none was '
                       'recorded at install (--admin), the account this '
                       'session\'s GitHub token belongs to could not be read, '
                       'and none is declared -- set PRECEDENT_GITHUB_USER='
                       '<your username>, or add "github": "<your username>" '
                       'to the identity.json in your individual practice set')
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

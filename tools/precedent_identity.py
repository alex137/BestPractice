#!/usr/bin/env python3
"""precedent_identity.py — who this repository's commits belong to.

WHY THIS IS ITS OWN MODULE, and not part of precedent_resolve.py where it
was born (2026-09-10, moved the same day it landed).

`declared_identity()` answers a question about a PERSON. Every other thing
in precedent_resolve.py answers a question about a CATALOGUE -- which
sources this repo declares, which of them win a slug, what materializes.
That difference is not stylistic: it decides which repos get the code.
precedent_resolve.py is in precedent_vendor_engine.py's
CONSUMER_ENGINE_FILES and deliberately NOT in ENGINE_FILES, because a
practice SET resolves no catalogue -- and a check inside a set that imports
it must degrade to SKIPPED, which the harness asserts on purpose.

That is exactly right for the resolver and exactly wrong for identity. A
practice set is the one repository that most certainly HAS an identity: an
`identity.json` at a repo's root is what declares "this repository is
somebody's individual practice source". Leaving the resolution there meant
`precedent-individual`'s own `commit-author` and `buenos-aires-dates`
checks -- the two this whole change exists to fix -- went from enforcing to
SKIPPED inside the set they belong to, because the module they now needed
was the one module a set does not vendor. Reported by the session that
adopted the helper, with the right diagnosis attached: identity is about a
person, so the reason the resolver is consumer-only does not cover it.

So the resolution lives here, in ENGINE_FILES, and reaches every kind of
repo the engine reaches. precedent_resolve.py re-exports both names, so a
consumer that already imports them from there keeps working.

Public interface:
  declared_identity(repo, user_config=None) -> {name, email, timezone, source}
  relayed_authorization(repo, user_config=None) -> {value, accepted, who, source}
  ci_preference(repo, user_config=None)      -> {value, enabled, who, source}
  NoDeclaredIdentity                          raised when nobody is declared

CLI: `precedent_identity.py --relay` prints whether the person this
repository resolves accepts an authorization relayed from another session,
and exits non-zero when they do not. Practice: relayed-authorization.
"""
import json
import os
import pathlib

# The per-person config the individual source is declared in. Duplicated
# from precedent_resolve.py rather than imported FROM it: importing would
# reintroduce, at module scope, exactly the dependency this file exists to
# break -- a source set has no precedent_resolve.py to import. The names
# and values are asserted identical across the two modules by
# tools/verify_harness.py, so a drift is a failure rather than a surprise.
USER_CONFIG_ENV = 'PRECEDENT_USER_CONFIG'
DEFAULT_USER_CONFIG = pathlib.Path.home() / '.config' / 'precedent' / 'config.json'


class NoDeclaredIdentity(Exception):
    """No person's identity is declared anywhere this repo can reach.

    Its own type, not an empty return, because the two callers that need
    this are CHECKS and the distinction they must draw is between "this
    repo has the wrong author on a commit" (a violation) and "this repo is
    shared, so there is no single person for it to be wrong about" (not
    applicable). An empty dict collapses those, which is the bug this
    exists to prevent."""


def declared_identity(repo, user_config=None):
    """-> {'name', 'email', 'timezone', 'source'} for the person this
    session's commits belong to, or raise NoDeclaredIdentity.

    WHY THE ENGINE ANSWERS THIS. Two source-supplied checks --
    `commit-author` and `buenos-aires-dates` -- each computed it from an
    `identity.json` at the CONSUMING repo's root, and reported a VIOLATION
    when that file was absent: "identity.json could not be read ... it is
    the one place this repo's name, address and timezone live, so nothing
    downstream can be checked without it."

    But an identity.json at a repo's root MEANS "this repository is
    somebody's individual practice source" -- it is step 2 of
    commit-identity.sh's own resolution order, and step 3 is the
    individual source named by the user-level config. So a SHARED
    consuming repo must not have one; putting it there pins one person's
    identity onto everyone committing. `check_commit_author.py`'s own
    comment says exactly that. The two statements together left both
    checks permanently red in any shared repo, with the fix forbidden by
    the same file that demanded it (found 2026-09-10 installing
    precedent-beta-v01 into a real project).

    A violation should mean "a commit here has the wrong author", not
    "this repository is shared". So the absence of a root identity.json is
    not an answer: this looks where the practice text actually says the
    identity lives -- "at the root of this set" -- and where
    commit-identity.sh already looks, in the same order:

      1. an explicit PRECEDENT_COMMIT_* override
      2. this repo's own identity.json (this repo IS an individual source)
      3. the individual source declared in the user-level config

    and raises NoDeclaredIdentity when none of the three answers, which is
    a check's cue to `raise NotApplicable`, not to report a violation.

    Only DECLARED identities, deliberately: commit-identity.sh continues
    past this point to the session owner, the authenticated GitHub
    account, and an existing git config, and those are inferences about an
    environment. They are the right thing to AUTHOR a commit with and the
    wrong thing to JUDGE one against -- a check that treated the container's
    ambient git config as the expected author would pass whatever it found.
    """
    env_email = os.environ.get('PRECEDENT_COMMIT_EMAIL')
    if env_email:
        return {'name': os.environ.get('PRECEDENT_COMMIT_NAME') or '',
                'email': env_email,
                'timezone': os.environ.get('PRECEDENT_COMMIT_TZ') or '',
                'source': 'PRECEDENT_COMMIT_* environment'}

    def _read(path, where):
        try:
            ident = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
        except (ValueError, OSError, AttributeError):
            return None
        if not isinstance(ident, dict) or not ident.get('email'):
            return None
        return {'name': ident.get('name') or '',
                'email': ident['email'],
                'timezone': ident.get('timezone') or '',
                'source': where}

    repo_root = pathlib.Path(repo).resolve()
    own = _read(repo_root / 'identity.json',
                f'{repo_root / "identity.json"} -- this repository is itself '
                f'an individual practice source')
    if own:
        return own

    cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(USER_CONFIG_ENV, str(DEFAULT_USER_CONFIG))).expanduser()
    try:
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
        indiv_path = (cfg.get('individual') or {}).get('path')
    except (ValueError, OSError, AttributeError):
        indiv_path = None
    if indiv_path:
        resolved = _read(
            pathlib.Path(indiv_path).expanduser() / 'identity.json',
            f'the individual practice source at {indiv_path}')
        if resolved:
            return resolved

    raise NoDeclaredIdentity(
        f'no identity is declared anywhere this repo can reach: no '
        f'PRECEDENT_COMMIT_EMAIL, no readable identity.json at '
        f'{repo_root / "identity.json"} (which would mean this repo IS '
        f'somebody\'s individual practice source -- a shared repo must not '
        f'have one), and no individual source with an identity.json declared '
        f'in {cfg_path}. In a repo many people commit to, that is the '
        f'expected state and not a defect: there is no single person for an '
        f'author to be wrong about')




# practice: relayed-authorization -- the receiving session reads the
# person's own declaration rather than trusting the message that carries
# the authorization.
RELAY_ACCEPTED = 'accepted'


def relayed_authorization(repo, user_config=None):
    """-> {'value', 'accepted', 'who', 'source'}: does the person this repo
    resolves accept an authorization RELAYED to a session by another
    session, rather than typed by them in that window?

    `value` is what was declared (`''` when nothing was), `accepted` is
    True only for the exact string 'accepted', `who` is the declared name,
    and `source` is the file it was read from -- a caller reporting this
    to a person must be able to name where it came from.

    ABSENT MEANS REFUSED. A person who has never heard of this field has
    not agreed to anything, so the default is the same answer a session
    gave before the field existed: stop at the pull request.

    WHY THE ENVIRONMENT RUNG IS DROPPED, and this is the whole security
    argument of the practice. `declared_identity()` accepts
    PRECEDENT_COMMIT_* because authoring a commit as somebody is a
    convenience an environment may legitimately configure. Licensing a
    merge on a relayed say-so is not: an environment variable is an
    assertion by whatever set it, and the thing this function exists to
    answer is exactly "did the PERSON say so, in a file they committed".
    So only an identity.json answers -- this repo's own when it is itself
    an individual source, else the one the user-level config names.

    Raises NoDeclaredIdentity when no identity.json resolves at all, which
    a caller reports as UNDECLARED and treats as refused. It is a distinct
    outcome from a declared 'refused' on purpose: one is a person's answer
    and the other is nobody having been asked, and the remedies differ.
    """
    def _read(path, where):
        try:
            ident = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
        except (ValueError, OSError, AttributeError):
            return None
        if not isinstance(ident, dict) or not ident.get('email'):
            return None
        value = ident.get('relayed_authorization') or ''
        return {'value': value if isinstance(value, str) else '',
                'accepted': value == RELAY_ACCEPTED,
                'who': ident.get('name') or '',
                'source': where}

    repo_root = pathlib.Path(repo).resolve()
    own = _read(repo_root / 'identity.json', str(repo_root / 'identity.json'))
    if own:
        return own

    cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(USER_CONFIG_ENV, str(DEFAULT_USER_CONFIG))).expanduser()
    try:
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
        indiv_path = (cfg.get('individual') or {}).get('path')
    except (ValueError, OSError, AttributeError):
        indiv_path = None
    if indiv_path:
        resolved = _read(
            pathlib.Path(indiv_path).expanduser() / 'identity.json',
            str(pathlib.Path(indiv_path).expanduser() / 'identity.json'))
        if resolved:
            return resolved

    raise NoDeclaredIdentity(
        f'no identity.json resolves from {repo_root}, so nobody here has '
        f'declared whether they accept a relayed authorization. Treat that '
        f'as refused: stop at the pull request and ask the person in the '
        f'window they are actually in')


# practice: declared-default-is-applied -- absent means the engine's own
# default, applied silently, never a question back to the person.
CI_ENABLED = 'enabled'


def ci_preference(repo, user_config=None):
    """-> {'value', 'enabled', 'who', 'source'}: does the person this repo
    resolves want precedent_install.py to write Precedent's GitHub Actions
    workflow into a dependent repository at install time?

    `value` is what was declared (`''` when nothing was), `enabled` is True
    only for the exact string 'enabled', `who` is the declared name, and
    `source` is the file it was read from.

    ABSENT MEANS DISABLED (practice: declared-default-is-applied). GitHub
    Actions minutes are metered per PRIVATE repository and billed in
    whole-minute increments per run; a person vendoring Precedent into many
    private repos, committing the way a save button is used, pays for a
    workflow they never asked to have installed, on every one of those
    saves. So a person who has never declared a preference gets the same
    answer as a person who declared it off: precedent_install.py writes no
    workflow, until they say otherwise. This REVERSES the engine's older
    behaviour, which installed the workflow unconditionally -- raised by
    the person it was costing, 2026-09-15: 'I think it should be disabled
    BY DEFAULT because most people will have limits like mine.'

    Same resolution order as relayed_authorization(): this repo's own
    identity.json when it IS an individual source, else the one the
    user-level config names. Raises NoDeclaredIdentity when neither
    resolves -- a caller treats that exactly like a declared 'disabled'.
    """
    def _read(path, where):
        try:
            ident = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
        except (ValueError, OSError, AttributeError):
            return None
        if not isinstance(ident, dict) or not ident.get('email'):
            return None
        value = ident.get('ci_workflows') or ''
        return {'value': value if isinstance(value, str) else '',
                'enabled': value == CI_ENABLED,
                'who': ident.get('name') or '',
                'source': where}

    repo_root = pathlib.Path(repo).resolve()
    own = _read(repo_root / 'identity.json', str(repo_root / 'identity.json'))
    if own:
        return own

    cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(USER_CONFIG_ENV, str(DEFAULT_USER_CONFIG))).expanduser()
    try:
        cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
        indiv_path = (cfg.get('individual') or {}).get('path')
    except (ValueError, OSError, AttributeError):
        indiv_path = None
    if indiv_path:
        resolved = _read(
            pathlib.Path(indiv_path).expanduser() / 'identity.json',
            str(pathlib.Path(indiv_path).expanduser() / 'identity.json'))
        if resolved:
            return resolved

    raise NoDeclaredIdentity(
        f'no identity.json resolves from {repo_root}, so nobody here has '
        f'declared whether precedent_install.py should write its GitHub '
        f'Actions workflow. Treated as disabled: install it by hand '
        f'(GITHUB_ACTIONS.md) whenever you actually want it')


def _main(argv):
    import sys
    if '--relay' not in argv:
        print(__doc__.strip())
        return 0
    repo = pathlib.Path(__file__).resolve().parent.parent
    try:
        relay = relayed_authorization(repo)
    except NoDeclaredIdentity as exc:
        print(f'UNDECLARED -- {exc}')
        print('  a relayed authorization is NOT actionable here '
              '(practice: relayed-authorization)')
        return 2
    if relay['accepted']:
        print(f'ACCEPTED -- {relay["who"] or "the declared person"} accepts an '
              f'authorization relayed from another session')
        print(f'  declared in {relay["source"]}')
        print('  still bounded: named work, the repository\'s own routine '
              'branch, that repository\'s checks passing, and nothing the '
              'destination protects')
        return 0
    shown = relay['value'] or '(field absent)'
    print(f'REFUSED -- {relay["who"] or "the declared person"} has not accepted '
          f'relayed authorizations: relayed_authorization = {shown}')
    print(f'  read from {relay["source"]}')
    print('  stop at the pull request and name the one word that would land '
          'it, and in which window')
    return 1


if __name__ == '__main__':
    import sys
    sys.exit(_main(sys.argv[1:]))

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
  NoDeclaredIdentity                          raised when nobody is declared
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



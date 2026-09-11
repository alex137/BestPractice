#!/usr/bin/env python3
"""precedent_source_credentials.py -- answers one question, and supplies the
one mechanism that follows from it: does this session need a git credential
to reach its PRIVATE practice sources, and does it have one?

WHY THIS EXISTS, AND WHAT WAS MEASURED (practice: cite-the-incident).
A private practice source -- someone's precedent-individual, a team's
precedent-team-* -- reaches a hosted session by being cloned. On Claude
Code's remote harness that clone needs read access granted per session by
the agent calling `add_repo`, and `add_repo` refuses across owners. On
2026-09-09, in a session whose initial source was `alex137/bestpractice`,
that refusal was reproduced as the session's very FIRST tool call:

    cross-tier adds are not supported in v1: requested
    "themorgan/precedent-individual" but session already has repos from
    owner(s) [alex137]

which closes the question TODO.md's `attach-private-sources` item left
open -- the initial source already counts as "has repos", so no ordering
of calls inside such a session can work. That session ran on the universal
catalogue alone: 0 team, 0 individual. Nothing was broken, and every
personal rule was silently absent, which is the failure mode AGENTS.md's
"no individual source resolved" gotcha already costs a working day to.

THE ROUTE THIS OPENS, AND EXACTLY HOW FAR IT IS VERIFIED. `add_repo` is
not the only way to hold a credential: an environment can carry one, and a
SessionStart hook can then clone with it, before any turn begins -- which
is the ordering the whole incident turns on. Measured 2026-09-09, in this
container, twice:

  * An authenticated HTTPS request to github.com LEAVES the sandbox and
    reaches GitHub's own authentication. `git ls-remote` with a deliberately
    invalid token answered `remote: Invalid username or token`, from GitHub,
    not a proxy error. So the transport is not what blocks a credentialed
    clone.
  * There is NO ambient credential for an arbitrary private repo: a bare
    `git ls-remote https://github.com/<private>` failed with
    `could not read Username for 'https://github.com'`, while the same call
    against a public repo succeeded. The harness's own git access is scoped
    to the repositories it attached.

A third measurement, of this file's own mechanism rather than the
environment: `git` invoked with the credential helper below and a
deliberately invalid PRECEDENT_GIT_TOKEN did NOT prompt for a username. It
sent the credential and GitHub rejected it -- `remote: Invalid username or
token` again, from the server. So the helper genuinely delivers a
credential to git, which is the part of this that could have been silently
inert.

VERIFIED 2026-09-10, closing the gap this paragraph used to hold open. A
real read-scoped PAT was set on the environment, and a brand-new container
came up with all four private sources already cloned before the first turn:
this tool reported OK, and precedent_resolve.py reported 146 practices from
6 sources (41 team, 13 individual) where the same repo had been resolving 89
from 1. No add_repo call was made or needed. So the whole path -- environment
variable, credential helper, SessionStart clone -- works end to end.

WHAT COST THREE DAYS, and it was never the token: the account held TWO
environments with the SAME NAME, and the values had been set on the one the
sessions were not running in. Three sessions across two fresh containers
measured zero PRECEDENT_* variables and concluded the runner did not pass
them through. Nobody asked how many environments the account had until
list_environments answered it in one call. Not established: whether the twin
was the whole cause, or the first save had also failed -- both fit what was
measured. The sequence is entry 29 in record/GOTCHAS_ARCHIVE.md.

A FOURTH, 2026-09-09, of the opt-in `inherit` mode: pointed at this
container's own GITHUB_TOKEN, a clone of a real cross-owner private set was
REFUSED by GitHub ("Invalid username or token"). That is the expected answer
-- a harness credential is scoped to the repositories the harness attached --
and it is why `inherit` is something a person asks for by name and never a
silent fallback. It does, however, take the measurement one notch further
than the invalid-token test above: a real credential was delivered and
evaluated by the server.

WHAT IT DOES NOT DO. It never reads, prints, logs or stores the token. The
credential reaches git through a helper that reads the environment variable
itself, at call time -- so the secret is never in a command line (visible in
`ps`), never in a clone's .git/config, and never in the config file the
bootstrap writes. Every path here is designed on the assumption that a
token written anywhere on disk is a token that will be committed by
somebody, eventually.

Run:
  python3 tools/precedent_source_credentials.py            # report
  python3 tools/precedent_source_credentials.py --check    # exit 1 if a
                                                           # source needs a
                                                           # credential and
                                                           # none is set
  python3 tools/precedent_source_credentials.py --repo PATH
Exit: 0 always, except --check with a source that needs a credential this
environment does not have (practice: fail-gracefully -- a missing token
degrades a session, and must never be what takes one down).
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

# The name is ours rather than GITHUB_TOKEN/GH_TOKEN on purpose. Both of
# those are already set in a Claude Code Remote container, scoped to the
# repositories the harness attached -- so falling back to them SILENTLY would
# send a credential that cannot work to a host that will reject it, and report
# the failure as "your token is wrong" rather than "you have not set one".
# An explicit name makes "no token here" a fact this tool can state.
TOKEN_ENV = 'PRECEDENT_GIT_TOKEN'
TOKEN_USER_ENV = 'PRECEDENT_GIT_TOKEN_USER'
DEFAULT_TOKEN_USER = 'x-access-token'

# ...and the opt-in that keeps the silent version from being reinvented.
# `PRECEDENT_GIT_TOKEN=inherit` means "use whatever git credential this
# container already carries". It is worth having because it costs one word to
# try and the answer is unambiguous either way -- the diagnosis in
# precedent_source_bootstrap.py distinguishes a REFUSED credential from an
# absent one, so an inherited token that lacks access says so in those words
# rather than looking like a missing setting.
#
# It is opt-in and never a fallback, which is the whole distinction: a token
# nobody chose to send, sent anyway, produces a failure that reads as the
# wrong problem. Asking for it by name means the person has accepted that the
# harness's own credential is probably scoped to the repositories the harness
# attached, and wants to find out.
INHERIT = 'inherit'
INHERITED_ENVS = ('GITHUB_TOKEN', 'GH_TOKEN')


def token_var(env=None):
    """-> the NAME of the environment variable that actually holds a usable
    token, or None. The name rather than the value, because that name is what
    the credential helper interpolates: the secret is read by the helper's own
    shell, never by this process."""
    env = os.environ if env is None else env
    declared = (env.get(TOKEN_ENV) or '').strip()
    if not declared:
        return None
    if declared != INHERIT:
        return TOKEN_ENV
    for name in INHERITED_ENVS:
        if (env.get(name) or '').strip():
            return name
    # `inherit` asked for something that is not there. Deliberately None, so
    # every caller treats it as "no credential" -- and assess() below says
    # which of the two states it is, since "you asked to inherit and there was
    # nothing to inherit" is a different fix from "you set nothing".
    return None

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def have_token(env=None):
    return token_var(env) is not None


def credential_helper(repo_url, env=None):
    """-> the credential-helper shell snippet for this url, or None when
    there is no token to use or no https url to use it on.

    THE SECRET IS NOT IN WHAT THIS RETURNS. The helper NAMES an environment
    variable; git runs the snippet, and the shell expands the variable inside
    the snippet's own process. So the value appears in no argument list and
    no file -- only in the environment it already lives in. That is what
    makes the same string safe to pass on a command line (credential_args
    below) AND to write into a clone's own config
    (persist_credential_helper): neither one records the token.
    """
    env = os.environ if env is None else env
    if not have_token(env):
        return None
    url = str(repo_url or '')
    # https only. A file:// fixture needs no credential, and handing one to
    # ssh:// or an arbitrary scheme would be offering a secret to whatever
    # transport happened to be configured.
    if not url.startswith('https://'):
        return None
    user = (env.get(TOKEN_USER_ENV) or '').strip() or DEFAULT_TOKEN_USER
    # The username IS interpolated into a shell snippet, so it is validated;
    # the token never is. GitHub accepts any username alongside a PAT, so a
    # value that fails this falls back rather than failing the clone.
    if not re.fullmatch(r'[A-Za-z0-9._-]+', user):
        user = DEFAULT_TOKEN_USER
    # Whichever variable actually holds the token -- PRECEDENT_GIT_TOKEN, or
    # the inherited one it pointed at. Interpolating the literal value of
    # PRECEDENT_GIT_TOKEN here would send the word "inherit" as a password.
    var = token_var(env)
    return ('!f() { test "$1" = get || exit 0; '
            f'echo username={user}; '
            f'echo "password=${var}"; }}; f')


def credential_args(repo_url, env=None):
    """-> the `git -c ...` flags that let one git invocation authenticate,
    or [] when there is no token to use or no https URL to use it on.

    `credential.helper=` (empty) first clears any helper configured
    elsewhere, so this is the only one consulted and a stale system helper
    cannot answer first."""
    helper = credential_helper(repo_url, env)
    if helper is None:
        return []
    return ['-c', 'credential.helper=', '-c', 'credential.helper=' + helper]


# WHY A CLONE NEEDS THE HELPER WRITTEN INTO IT, AND NOT ONLY PASSED TO THE
# CLONE COMMAND (practice: cite-the-incident). credential_args above covers
# ONE git invocation. The clone it produces carries no memory of it, so every
# later git command run inside that clone -- by a hook, by a person, by a
# tool that never heard of this module -- meets a private remote with no
# credential and fails with `could not read Username for 'https://github.com'`
# even though the token is sitting right there in the environment.
#
# Measured 2026-09-11, and it cost a session its first six tool calls. All
# four private sources were on disk and PRECEDENT_GIT_TOKEN was set.
# PRECEDENT_FRESHNESS_ALSO names those clones, so the freshness guard's
# pre-write mode fetched each one; the fetch failed; and the guard blocked --
# correctly, by its own rule that a check which could not run is not a check
# that passed. It then blocked AGAIN on every retry, because its
# once-per-session sentinel is only written after the checks pass. The
# session could run nothing but `git`.
#
# The diagnosis is the expensive part: the block names the SOURCE's base
# branch (`could not fetch origin/main`) while the project dir sits on a
# different branch entirely, so it reads as the project's own checkout being
# broken and sends you to the wrong repository.
#
# Writing the snippet into the clone's local config fixes it for every later
# caller at once, and writes no secret: the config records the variable's
# NAME. `--replace-all` twice rather than `--add` so re-running is idempotent
# -- a session-start hook runs this on every session, and an accumulating
# config would grow a helper entry per session forever.
def persist_credential_helper(clone_path, repo_url, env=None, run=None):
    """Write the credential helper into an existing clone's LOCAL git config,
    so git commands run inside it later can authenticate too.

    -> True when a helper was written, False when there was nothing to write
    (no token, not an https remote) or the writes failed. Never raises: a
    clone that is usable now must not be failed over a convenience for later.
    """
    helper = credential_helper(repo_url, env)
    if helper is None:
        return False
    runner = run or (lambda args: subprocess.run(
        args, capture_output=True, text=True).returncode == 0)
    base = ['git', '-C', str(clone_path), 'config']
    # An empty value FIRST resets the helper list, exactly as the `-c` pair
    # above does, so a system- or global-level helper cannot answer before
    # this one. Then the real snippet is appended.
    if not runner([*base, '--replace-all', 'credential.helper', '']):
        return False
    if not runner([*base, '--add', 'credential.helper', helper]):
        return False
    return True


def _read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except Exception:
        return None


def _user_config_path(env=None):
    env = os.environ if env is None else env
    home = env.get('HOME') or str(pathlib.Path.home())
    return pathlib.Path(home) / '.config' / 'precedent' / 'config.json'


def unresolved_private_sources(repo_root=None, env=None):
    """-> [(level, name, why)] for every PRIVATE-level source this repo
    expects and this session does not have on disk.

    Declaration is what makes a team source expected; for an individual set
    there is nothing in any repo to declare it (that is the whole point of
    it living in a user-level config), so the expectation is structural: a
    hosted session that has no individual config has either not got one or
    could not fetch it, and the two are worth telling apart out loud."""
    env = os.environ if env is None else env
    root = pathlib.Path(repo_root or ROOT)
    out = []

    cfg = _read_json(root / 'precedent.json') or {}
    for src in cfg.get('sources', []) or []:
        if src.get('level') != 'team':
            continue
        path = (root / str(src.get('path', ''))).resolve()
        if not (path / 'practices').is_dir():
            out.append(('team', str(src.get('name') or path.name),
                        f'{path} has no practices/ directory'))

    user_cfg = _user_config_path(env)
    entry = (_read_json(user_cfg) or {}).get('individual')
    if not entry:
        out.append(('individual', 'precedent-individual',
                    f'{user_cfg} declares no individual source'))
    elif not (pathlib.Path(str(entry.get('path', ''))) / 'practices').is_dir():
        out.append(('individual', str(entry.get('name') or 'precedent-individual'),
                    f"{entry.get('path')} has no practices/ directory"))
    return out


# THE THIRD CAUSE THIS FILE CANNOT MEASURE, AND WHY IT IS SAID ANYWAY.
# Every message below assumed an unresolved source is an ACCESS problem --
# no credential, a refused one, a session rooted under the wrong owner --
# and offered the credential remedy for all of them. A source whose
# repository has been RETIRED produces an identical reading and that remedy
# is wrong for it: no token will ever clone a repo that is gone, so the
# reader is sent to configure access for something that does not exist.
#
# Telling the two apart needs a network call, and this tool must work
# offline and in continuous integration -- so it does not guess. It names
# the possibility and the different remedy, which costs one sentence and is
# the whole difference between a reader who checks precedent.json and one
# who spends an afternoon on a token.
#
# Written 2026-09-10, retiring precedent-team-tms: a set built for a pilot
# nobody started, that no repo declared in anger, whose one practice moved
# to the set whose subject it always was. The first real retirement of a
# practice source, and the first time this message was wrong.
_RETIRED_CLAUSE = (
    'AND IF THE SOURCE WAS RETIRED: a deleted repository reads exactly like '
    'an unreachable one here, and no credential fixes it. Check whether '
    'precedent.json still declares a source somebody has since retired -- if '
    'so the fix is to remove that declaration, not to configure access.')


def assess(repo_root=None, env=None):
    """-> (verdict, message). verdict is one of:
         'ok'       -- every private source this repo expects is on disk
         'missing'  -- one or more are absent AND no credential is set
         'set'      -- one or more are absent while a credential IS set, so
                       the token is not what is missing
    """
    env = os.environ if env is None else env
    unresolved = unresolved_private_sources(repo_root, env)
    if not unresolved:
        return 'ok', (f'every private practice source this repo expects is on '
                      f'disk; {TOKEN_ENV} is not needed here')
    named = ', '.join(f'{level}/{name}' for level, name, _ in unresolved)
    detail = '; '.join(why for _, _, why in unresolved)
    var = token_var(env)
    if var:
        via = ('' if var == TOKEN_ENV
               else f' (inherited from {var}, because {TOKEN_ENV}={INHERIT})')
        return 'set', (
            f'{len(unresolved)} private source(s) did not resolve ({named}), '
            f'and a credential IS set{via} -- so a missing credential is not '
            f'the explanation. Look at what git said when it tried: '
            f'precedent_source_bootstrap.py names a REFUSED credential '
            f'separately from an absent one, and an inherited harness token '
            f'is refused for most repositories because it is scoped to the '
            f'ones the harness attached. '
            + _RETIRED_CLAUSE +
            f' Sources: {detail}')
    if (env.get(TOKEN_ENV) or '').strip() == INHERIT:
        return 'missing', (
            f'{len(unresolved)} private source(s) did not resolve ({named}). '
            f'{TOKEN_ENV}={INHERIT} asked to use this container\'s own git '
            f'credential, and none of {", ".join(INHERITED_ENVS)} is set -- so '
            f'there was nothing to inherit and no credential was sent. Set '
            f'{TOKEN_ENV} to a real token instead. Sources: {detail}')
    return 'missing', (
        f'{len(unresolved)} private source(s) did not resolve ({named}), and '
        f'{TOKEN_ENV} is not set in this environment. Until one of the two is '
        f'fixed, every practice those sources hold is SILENTLY absent and this '
        f'session is applying the universal catalogue alone. Reasons: {detail}. '
        f'Set {TOKEN_ENV} in the environment configuration (INSTALL.md section 8) '
        f'so the SessionStart hook can clone without add_repo, or start a '
        f'session rooted in the private repo itself. '
        # The two cases this line CANNOT tell apart, said out loud rather than
        # left to be misread (2026-09-09: a resumed session measured zero
        # PRECEDENT_* variables in a container that predated the change, and
        # the identical MISSING line read as "the token does not work").
        f'IF YOU JUST SET IT: an environment variable does not reach a session '
        f'that is already running, and this line looks exactly the same for '
        f'"never set" and "set after this container started" -- start a NEW '
        f'session and check `env | grep -c PRECEDENT` before concluding '
        f'anything about the token itself. '
        + _RETIRED_CLAUSE)


def remind(repo_root=None, env=None, prefix='precedent_source_credentials'):
    """-> a single line for another tool to print, or None when there is
    nothing worth saying. Callers print at the moment they run: the vendor
    update, the session check, the source-freshness report. Written once
    here so three tools cannot drift into three different wordings
    (practice: engine-plus-host-shims)."""
    verdict, message = assess(repo_root, env)
    if verdict == 'ok':
        return None
    return f'{prefix}: {message}'


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=(__doc__ or '').splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default=str(ROOT),
                    help='the repository whose precedent.json declares the '
                         'sources (default: this one)')
    ap.add_argument('--check', action='store_true',
                    help='exit 1 when a private source is missing and no '
                         'credential is set')
    args = ap.parse_args(argv)

    verdict, message = assess(args.repo)
    print(f'source credentials: {verdict.upper()} -- {message}')
    if verdict == 'missing' and args.check:
        return 1
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())

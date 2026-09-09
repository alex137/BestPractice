#!/usr/bin/env python3
"""precedent_source_bootstrap.py — the retry-capable half of getting a
privately-scoped individual practice source resolvable on an ephemeral,
hosted session (INSTALL.md step 9's individual-source branch;
spec/BOOTSTRAP_NEW_SOURCES.md).

THE INCIDENT THIS CLOSES, AND A CORRECTION ON HOW (2026-09-06). Two
independent adopters hit the same failure within a day of each other: a
`SessionStart` hook clones the person's individual-set repo and writes
`~/.config/precedent/config.json` — but that clone needs the session to
already have git read access to a private repo, and on this harness that
access is granted by the AGENT calling `add_repo` as its own first tool
call, in its own turn. A `SessionStart` hook runs *entirely to completion*
before that turn starts (Claude Code's own docs for this hook: synchronous
mode "guarantees dependencies are installed before your session starts" —
a strict ordering, not a race with variable odds). INSTALL.md used to say
a *behavioral instruction* ("tell the agent to call add_repo first") closed
this gap; both incidents are direct evidence it does not.

**This file originally shipped with a bounded retry in the hook itself
("Option B") as half the fix. A follow-up testing session proved that
wrong, structurally, not just unlucky: every retry attempt this file makes
runs *inside* the `SessionStart` hook's own execution, which by
construction finishes before the agent's turn — and therefore before
`add_repo` — can start even once. There is no point during this file's
own retry loop where `add_repo` access could possibly have appeared, on a
genuinely fresh session, no matter the attempt count or delay.** Retrying
here is not a partial mitigation of the incident; it is inert for it,
full stop, and previously cost every cold session real latency (up to
~12 seconds) for zero benefit on the exact path it was meant to help.

**The only thing that actually closes the gap is
`tools/precedent_resolve.py`'s own lazy self-heal ("Option A"):** it
re-invokes this same hook lazily, on demand, the first time anything
performs a live resolve and finds the config still absent — and because
that call happens *inside* the agent's own turn, always after `add_repo`
has already run (per the standing session-start instruction), the
re-invoked hook now has the access it needed and succeeds on its first
attempt. `DEFAULT_RETRIES` below reflects this: it defaults to a single
attempt, because a retry loop earns no credit here. `--retries`/
`--retry-delay` remain real, working options — not because they help with
`add_repo`, but as ordinary defensive engineering against a genuinely
transient git/network hiccup unrelated to this specific race, for a
caller who wants that and knows why.

WHY THIS IS A SEPARATE, VENDORED, HARNESS-NEUTRAL TOOL AND NOT INLINE SHELL
(practice: engine-plus-host-shims). The actual clone-or-pull-then-write-
config mechanism is domain-neutral: every adopter's version of it differs
only in the repo URL and two paths. Before this file existed, every adopter
hand-wrote their own copy of that mechanism directly in a shell hook script
(spec/MIGRATING_EXISTING_INSTALLS.md step 4's "worked pattern"), which is
exactly how a missing fix (first the retry that didn't exist, then the
retry that couldn't have worked) went unnoticed in more than one place at
once: a bug in hand-copied shell has to be found and fixed once per
adopter. Vendoring the mechanism here means a fix reaches every adopter
through their ordinary `process/upstream/` sync, and the per-adopter shell
hook
(templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template)
shrinks to naming its own repo URL and two paths, then delegating.

Run:
  python3 precedent_source_bootstrap.py \\
      --level individual --name NAME --repo-url URL \\
      --clone PATH --config PATH \\
      [--retries N] [--retry-delay SECONDS] [--remote-only true]

Exit: always 0 (fail-gracefully — an unreachable individual source degrades
the session, per tools/precedent_resolve.py's own documented contract; it
must never be what takes a session down). A failure after every retry is
attempted is reported on stderr, not silently absorbed.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

LEVELS = {'individual', 'team'}
# An INDIVIDUAL source resolves through a $HOME clone plus a user-level
# config naming it; a TEAM source resolves as a SIBLING CHECKOUT beside the
# consuming repo, by path, with nothing to write down -- see
# tools/precedent_resolve.py's own header for why the two are wired
# differently. Both are cloned the same way, which is all this tool does, so
# 'team' is a real value here rather than the placeholder it was until
# 2026-09-09: what differs is only whether a config file is written
# afterwards (_write_config below), and the sibling path the clone lands at.
#
# Why it stopped being a placeholder: a credential carried by the
# ENVIRONMENT, rather than granted per session by add_repo, can be used
# before the agent's first turn -- and at that moment a team set is exactly
# as cloneable as an individual one. See tools/precedent_source_credentials.py
# for what was measured about that, and how far.

# A single attempt by default -- see the module docstring's 2026-09-06
# correction. A retry loop here cannot help the incident this file was
# built for (every attempt runs before the agent's turn, and therefore
# `add_repo`, can start), so defaulting to more than one attempt would
# just add latency on the exact path where it can never pay off. Raised
# explicitly via --retries/--retry-delay, it is still real, working
# defensive engineering against an unrelated, genuinely transient
# git/network failure -- a caller who wants that opts in knowing why.
DEFAULT_RETRIES = 1
DEFAULT_RETRY_DELAY = 2.0


def _load_json(path):
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return None
    return None


def _write_config(config_path, level, name, clone_path, repo_url=None):
    """Merge — never clobber — so a config file that later grows a second
    key (or a second person's individual set were this ever multi-tenant)
    isn't silently overwritten by a hook that only knows about its own
    key. Matches tools/precedent_bootstrap_source.py's write_user_config,
    kept as a small, separate copy rather than an import: that tool
    creates a *new* source from a skeleton, a one-off, human-in-the-loop
    action; this one runs unattended, every session, and the two should
    not have to change together by accident."""
    data = _load_json(config_path) or {'format_version': 1}
    entry = {'name': name, 'path': str(clone_path)}
    # RECORD THE URL, because this file is the only place it can privately
    # live. A shared repo's tracked hook must not carry a private source's
    # clone URL (2026-09-07: one public consumer did, five lines from its own
    # sentence saying that naming it "would leak its existence and location"),
    # so the hook reads `repo_url` from here instead -- and this tool already
    # had it in hand and dropped it, which is why every new machine needed a
    # human to type it back in.
    if repo_url:
        entry['repo_url'] = repo_url
    data[level] = entry
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def _credential_args(repo_url):
    """The `git -c ...` flags that let this one invocation authenticate with
    a credential the ENVIRONMENT carries, or [] when there is none.

    (practice: fail-gracefully) The import is guarded and its failure is
    ANNOUNCED rather than absorbed: a vendored tree that predates
    precedent_source_credentials.py still runs, exactly as it did before,
    but a person expecting a token to be used is told plainly why it was
    not. A silently ignored credential is indistinguishable from a wrong
    one, and this file's whole history is about failures that look like
    something else."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from precedent_source_credentials import credential_args
    except ImportError:
        if os.environ.get('PRECEDENT_GIT_TOKEN'):
            print("precedent_source_bootstrap: PRECEDENT_GIT_TOKEN is set, but "
                  "precedent_source_credentials.py is not beside this file, so "
                  "the credential CANNOT be used. Re-vendor the engine "
                  "(python3 tools/precedent_vendor_engine.py refresh <clone>).",
                  file=sys.stderr)
        return []
    return credential_args(repo_url)


def _try_sync(repo_url, clone_path):
    """One attempt: pull if already cloned, else clone. -> (ok, output).

    The clone is made from the CLEAN url -- the credential travels as a git
    helper that reads the environment itself, so no token is ever written
    into .git/config, where it would outlive this process and be pushed by
    whoever committed next."""
    cred = _credential_args(repo_url)
    if (clone_path / '.git').is_dir():
        cmd = ['git', *cred, '-C', str(clone_path), 'pull', '--ff-only', '--quiet']
    else:
        clone_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = ['git', *cred, 'clone', '--quiet', repo_url, str(clone_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def ensure_source(level, name, repo_url, clone_path, config_path,
                   retries=DEFAULT_RETRIES, retry_delay=DEFAULT_RETRY_DELAY,
                   sleep=time.sleep):
    """The mechanism, callable in-process as well as from main() below.
    (tools/precedent_resolve.py's own self-heal does NOT call this
    in-process -- it shells out to the project's session-start hook, the
    hook this file backs, so a project that customized its hook still gets
    the customized behavior on self-heal too.) `sleep` is injectable so a
    test can prove the retry count without a real wall-clock wait.

    -> (True, None) on success; (False, last_output) once every retry is
    spent. Never raises for an ordinary sync failure — a source this
    session cannot yet reach is the expected, common case (see module
    docstring), not a bug to propagate."""
    clone_path = pathlib.Path(clone_path)
    attempts = max(1, retries)
    last_output = ''
    for attempt in range(1, attempts + 1):
        ok, last_output = _try_sync(repo_url, clone_path)
        if ok:
            # A team source is resolved BY PATH, as a sibling checkout, so
            # there is nothing to record; writing a config entry for one
            # would invent a resolution route precedent_resolve.py does not
            # read (practice: no-invented-specifics, applied to code).
            if config_path is not None:
                _write_config(pathlib.Path(config_path), level, name, clone_path,
                              repo_url=repo_url)
            return True, None
        if attempt < attempts:
            sleep(retry_delay)
    return False, last_output


BASE_URL_ENV = 'PRECEDENT_SOURCE_BASE_URL'
TOKEN_ENV_NAME = 'PRECEDENT_GIT_TOKEN'  # named, not imported: this file
                                        # must run in a tree vendored
                                        # before the credentials module
                                        # existed (see _credential_args)


def teams_from_repo(repo_path, base_url=None, retries=DEFAULT_RETRIES,
                    retry_delay=DEFAULT_RETRY_DELAY):
    """Clone every TEAM source a repo's precedent.json declares, to the
    sibling path it declares, from `base_url`/<name>.

    WHY THE URL IS BUILT FROM AN ENVIRONMENT VARIABLE rather than declared
    in precedent.json beside the name: the account that owns a set is the
    half that locates it, and a tracked file in a public repository must not
    carry that (2026-09-07: one public consumer's own hook did, five lines
    from its own sentence saying it must not). The NAME is already declared
    in the open and that was a deliberate decision -- see precedent.json's
    own comment. Building `<base>/<name>` keeps it that way.

    -> [(name, ok, output)], one per declared team source. Never raises: a
    set that cannot be cloned degrades the session (practice:
    fail-gracefully), it does not stop startup."""
    repo_path = pathlib.Path(repo_path)
    base = (base_url if base_url is not None
            else os.environ.get(BASE_URL_ENV, '')).strip().rstrip('/')
    results = []
    try:
        cfg = json.loads((repo_path / 'precedent.json').read_text(encoding='utf-8'))
    except Exception as e:
        return [(None, False, f'could not read {repo_path / "precedent.json"}: {e}')]
    for src in cfg.get('sources', []) or []:
        if src.get('level') != 'team':
            continue
        name = str(src.get('name') or '').strip()
        rel = str(src.get('path') or '').strip()
        if not name or not rel:
            results.append((name or None, False,
                            'the declared source has no name or no path'))
            continue
        clone_path = (repo_path / rel).resolve()
        if (clone_path / 'practices').is_dir():
            results.append((name, True, 'already on disk'))
            continue
        if not base:
            results.append((name, False,
                            f'{BASE_URL_ENV} is not set, so there is no URL to '
                            f'clone {name} from'))
            continue
        ok, out = ensure_source('team', name, f'{base}/{name}', clone_path,
                                None, retries=retries, retry_delay=retry_delay)
        results.append((name, ok, out or 'cloned'))
    return results


def _diagnose(output):
    """Name WHICH failure git reported, since the remedies are opposite ones.

    "No token" and "the token is wrong" and "that repository does not exist"
    all end in the same silence otherwise, and the first thing anybody does
    with an unexplained failure is re-set a credential that was fine
    (practice: fail-gracefully -- match the telling to the reader)."""
    low = (output or '').lower()
    if 'invalid username or token' in low or 'authentication failed' in low:
        return ('AUTHENTICATION was refused by the server, so a credential '
                'WAS sent and it was not accepted -- check the token\'s scope '
                'and expiry rather than whether it is set.')
    if 'could not read username' in low or 'terminal prompts disabled' in low:
        return (f'NO CREDENTIAL was available -- git asked for a username and '
                f'there was nothing to answer with. Set ${TOKEN_ENV_NAME} in '
                f'the environment (INSTALL.md section 8).')
    if 'repository not found' in low or 'does not appear to be a git repo' in low:
        return ('the repository was NOT FOUND, which for a private repo is '
                'also what insufficient access looks like -- check the name '
                'and the credential\'s access to it.')
    return 'it'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--level', choices=sorted(LEVELS))
    p.add_argument('--name')
    p.add_argument('--repo-url')
    p.add_argument('--clone')
    p.add_argument('--config',
                   help='where to record the resolution (individual only -- a '
                        'team source resolves by path and records nothing)')
    p.add_argument('--teams-from', metavar='REPO',
                   help="clone every team source REPO's precedent.json "
                        f'declares, from ${BASE_URL_ENV}/<name>. Mutually '
                        'exclusive with the single-source arguments above')
    p.add_argument('--retries', type=int, default=DEFAULT_RETRIES)
    p.add_argument('--retry-delay', type=float, default=DEFAULT_RETRY_DELAY)
    p.add_argument('--remote-only', default='true',
                   help='skip entirely unless CLAUDE_CODE_REMOTE=true (a '
                        'local machine already has a persistent $HOME, so '
                        'this hook would be a no-op there anyway)')
    args = p.parse_args(argv)

    if args.remote_only.lower() == 'true' and os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        return 0

    if args.teams_from:
        for name, ok, out in teams_from_repo(args.teams_from,
                                             retries=args.retries,
                                             retry_delay=args.retry_delay):
            if not ok:
                print(f"precedent_source_bootstrap: team source "
                      f"{name!r} is not on disk -- {out[-500:]}. Its practices "
                      f"are NOT in force this session.", file=sys.stderr)
        return 0

    missing = [f'--{n}' for n, v in (('level', args.level), ('name', args.name),
                                     ('repo-url', args.repo_url),
                                     ('clone', args.clone)) if not v]
    if missing:
        p.error('needs ' + ', '.join(missing) + ' (or --teams-from REPO)')
    if args.level == 'individual' and not args.config:
        p.error('--config is required for an individual source: it is the '
                'only place its resolution is recorded')

    ok, last_output = ensure_source(args.level, args.name, args.repo_url,
                                    args.clone, args.config,
                                    retries=args.retries,
                                    retry_delay=args.retry_delay)
    if not ok:
        print(f"precedent_source_bootstrap: {_diagnose(last_output)} "
              f"could not reach {args.repo_url!r} "
              f"after {args.retries} attempt(s) -- this environment may not "
              f"(yet) have read access to it. The {args.level} source "
              f"{args.name!r} will not be in force this session unless "
              f"something re-syncs it later (tools/precedent_resolve.py "
              f"retries this itself, once, the next time anything asks for "
              f"the {args.level} source). Last attempt's output: "
              f"{last_output[-500:]}", file=sys.stderr)
    return 0  # fail-gracefully -- see module docstring


if __name__ == '__main__':
    sys.exit(main())

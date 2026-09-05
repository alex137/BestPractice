#!/usr/bin/env python3
"""precedent_source_bootstrap.py — the retry-capable half of getting a
privately-scoped individual practice source resolvable on an ephemeral,
hosted session (INSTALL.md step 9's individual-source branch;
spec/BOOTSTRAP_NEW_SOURCES.md).

THE INCIDENT THIS CLOSES. Two independent adopters hit the same failure
within a day of each other: a `SessionStart` hook clones the person's
individual-set repo and writes `~/.config/precedent/config.json` — but that
clone needs the session to already have git read access to a private repo,
and on this harness that access is granted by the AGENT calling `add_repo`
as its own first tool call, in its own turn. A `SessionStart` hook runs
before that turn starts. INSTALL.md used to say a *behavioral instruction*
("tell the agent to call add_repo first") closed this gap; both incidents
are direct evidence it does not, for the case where the hook has already
started by the time the agent's own turn begins. No token or secret closes
this either — the fix is that the clone attempt tolerates the race instead
of losing it once and giving up (Option B: bounded retry, this file), and
that anything reading the config it writes tolerates the hook still not
having finished by treating "config absent" as "try once more", not "no
individual set" (Option A: tools/precedent_resolve.py's own lazy self-heal,
which shells out to the project's session-start hook — the hook this file
backs — rather than reimplementing this file's logic a second time).

WHY THIS IS A SEPARATE, VENDORED, HARNESS-NEUTRAL TOOL AND NOT INLINE SHELL
(practice: engine-plus-host-shims). The actual clone-or-pull-then-write-
config mechanism is domain-neutral: every adopter's version of it differs
only in the repo URL and two paths. Before this file existed, every adopter
hand-wrote their own copy of that mechanism directly in a shell hook script
(spec/MIGRATING_EXISTING_INSTALLS.md step 4's "worked pattern"), which is
exactly how the missing retry went unnoticed in more than one place at
once: a bug in hand-copied shell has to be found and fixed once per
adopter. Vendoring the mechanism here means the retry (or any future fix
to it) reaches every adopter through their ordinary `process/upstream/`
sync, and the per-adopter shell hook
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

LEVELS = {'individual'}  # a team source resolves via a sibling checkout, not
                          # a $HOME clone+config -- see tools/precedent_resolve.py's
                          # own header for why the two are wired differently.
                          # This tool takes --level as a real argument (rather
                          # than assuming "individual") so a team source's own
                          # sibling-clone bootstrap can register a second value
                          # here later without a second tool -- see TODO.md
                          # item 18, "the identical gap" spec/BOOTSTRAP_NEW_SOURCES.md
                          # already names for that case.

DEFAULT_RETRIES = 6
DEFAULT_RETRY_DELAY = 2.0


def _load_json(path):
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return None
    return None


def _write_config(config_path, level, name, clone_path):
    """Merge — never clobber — so a config file that later grows a second
    key (or a second person's individual set were this ever multi-tenant)
    isn't silently overwritten by a hook that only knows about its own
    key. Matches tools/precedent_bootstrap_source.py's write_user_config,
    kept as a small, separate copy rather than an import: that tool
    creates a *new* source from a skeleton, a one-off, human-in-the-loop
    action; this one runs unattended, every session, and the two should
    not have to change together by accident."""
    data = _load_json(config_path) or {'format_version': 1}
    data[level] = {'name': name, 'path': str(clone_path)}
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def _try_sync(repo_url, clone_path):
    """One attempt: pull if already cloned, else clone. -> (ok, output)."""
    if (clone_path / '.git').is_dir():
        r = subprocess.run(['git', '-C', str(clone_path), 'pull', '--ff-only', '--quiet'],
                           capture_output=True, text=True)
    else:
        r = subprocess.run(['git', 'clone', '--quiet', repo_url, str(clone_path)],
                           capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def ensure_source(level, name, repo_url, clone_path, config_path,
                   retries=DEFAULT_RETRIES, retry_delay=DEFAULT_RETRY_DELAY,
                   sleep=time.sleep):
    """The mechanism, callable in-process (tools/precedent_resolve.py's own
    self-heal uses this directly rather than shelling back out to a second
    copy of itself) as well as from main() below. `sleep` is injectable so
    a test can prove the retry count without a real wall-clock wait.

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
            _write_config(pathlib.Path(config_path), level, name, clone_path)
            return True, None
        if attempt < attempts:
            sleep(retry_delay)
    return False, last_output


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--level', required=True, choices=sorted(LEVELS))
    p.add_argument('--name', required=True)
    p.add_argument('--repo-url', required=True)
    p.add_argument('--clone', required=True)
    p.add_argument('--config', required=True)
    p.add_argument('--retries', type=int, default=DEFAULT_RETRIES)
    p.add_argument('--retry-delay', type=float, default=DEFAULT_RETRY_DELAY)
    p.add_argument('--remote-only', default='true',
                   help='skip entirely unless CLAUDE_CODE_REMOTE=true (a '
                        'local machine already has a persistent $HOME, so '
                        'this hook would be a no-op there anyway)')
    args = p.parse_args(argv)

    if args.remote_only.lower() == 'true' and os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        return 0

    ok, last_output = ensure_source(args.level, args.name, args.repo_url,
                                    args.clone, args.config,
                                    retries=args.retries,
                                    retry_delay=args.retry_delay)
    if not ok:
        print(f"precedent_source_bootstrap: could not reach {args.repo_url!r} "
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

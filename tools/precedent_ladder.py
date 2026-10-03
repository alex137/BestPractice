#!/usr/bin/env python3
"""Says whether the five-stage ladder is in force for the person working here -- a set they bring provides it, and PRECEDENT_NO_LADDERS is not set -- so every engine line chooses the ladder wording or the plain one from one answer (spec/LADDER_OPT_IN_PLAN.md)

precedent_ladder.py -- is the five-stage ladder in force for this person,
in this repository? (spec/LADDER_OPT_IN_PLAN.md D5)

The ladder (Consider, Act, Booked, Debut, Produce, and the branch tiers it
climbs) is a working method a person opts into by BRINGING the set that
provides it, through their own individual set (D2). Everyone else gets the
same enforcement and none of the ladder's words. Every engine line that
would say a ladder word asks this module first, so the one question has one
answer:

    import precedent_ladder
    precedent_ladder.say('Booked (step 3 of 5): landed on pre-staging.',
                         'Landed on main.')

From a hook:

    python3 tools/precedent_ladder.py --in-force && echo "on the ladder"

The answer is read off a handful of small files -- the user config, the
individual set's precedent-source.json, each candidate set's own -- and never
off the full resolver, so a hook can ask on every call without paying for a
catalogue load. It is True when a source in force here provides the
`ladder` capability and the session was not started with
PRECEDENT_NO_LADDERS=1 (D13).

    python3 tools/precedent_ladder.py --status      # one plain sentence
    python3 tools/precedent_ladder.py --in-force    # exit 0 on, 1 off
"""
import argparse
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import precedent_resolve as pr                                  # noqa: E402

ROOT = HERE.parent


def _user_config(user_config=None):
    path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(pr.USER_CONFIG_ENV, str(pr.DEFAULT_USER_CONFIG))
    ).expanduser()
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def ladder_sources(repo=None, user_config=None):
    """-> [(name, path)] for every source here that provides the ladder and
    is on disk: the shared sets the repository declares, and the sets the
    person brings. Ignores PRECEDENT_NO_LADDERS; ladder_in_force applies it."""
    root = pathlib.Path(repo or ROOT).resolve()
    candidates = []
    try:
        cfg = json.loads((root / pr.REPO_CONFIG).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        cfg = {}
    for entry in (cfg.get('sources') if isinstance(cfg, dict) else None) or []:
        if not isinstance(entry, dict) or not entry.get('path'):
            continue
        if pr.normalize_level(entry.get('level')) != 'shared':
            continue
        candidates.append((entry.get('name') or '',
                           pr._declared_path(root, entry['path'])))
    ind = _user_config(user_config).get('individual')
    if isinstance(ind, dict) and ind.get('path'):
        for b in pr.brought_sources(ind['path'], warn=False):
            candidates.append((b['name'], pathlib.Path(b['path'])))
    out, seen = [], set()
    for name, path in candidates:
        real = pathlib.Path(path).resolve()
        if real in seen or not (real / 'practices').is_dir():
            continue
        seen.add(real)
        if pr.LADDER_CAPABILITY in pr.source_provides(real):
            out.append((name, str(real)))
    return out


def ladder_in_force(repo=None, user_config=None):
    """True when the ladder is in force for this person in `repo`."""
    if pr.no_ladders():
        return False
    if pr.assume_ladder():
        return True
    return bool(ladder_sources(repo, user_config))


def say(ladder_text, plain_text, repo=None):
    """The ladder wording for a person on the ladder, the plain wording for
    everyone else. Both must say what happened; only the words differ."""
    return ladder_text if ladder_in_force(repo) else plain_text


def test_session_refusal():
    """-> the refusal a push or merge gate prints in a No ladders session,
    or None. Such a session exists to show what a person off the ladder
    sees; work done in it is a test and never leaves it (D13)."""
    if not pr.no_ladders():
        return None
    return (f'{pr.NO_LADDERS_ENV} is set: this is a test session showing what '
            'a person off the ladder sees, so nothing is pushed or merged from '
            'it. Start a session without it to push.')


def status_sentence(repo=None, user_config=None):
    if pr.no_ladders():
        return ('The ladder is switched off for this session '
                f'({pr.NO_LADDERS_ENV} is set), so this session sees what a '
                'person off the ladder sees. Start a session without it to '
                'have the ladder back.')
    found = ladder_sources(repo, user_config)
    if found:
        return ('The ladder is in force here, from '
                + ', '.join(n for n, _p in found) + '.')
    return 'The ladder is not in force here.'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--repo', default=None, help='the repository to ask about '
                   '(default: the one this tool is in)')
    g = p.add_mutually_exclusive_group()
    g.add_argument('--in-force', action='store_true',
                   help='exit 0 when the ladder is in force, 1 when not')
    g.add_argument('--status', action='store_true',
                   help='say in one sentence whether it is, and why')
    args = p.parse_args(argv)
    if args.in_force:
        return 0 if ladder_in_force(args.repo) else 1
    print(status_sentence(args.repo))
    return 0


if __name__ == '__main__':
    sys.exit(main())

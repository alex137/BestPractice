#!/usr/bin/env python3
"""precedent_bootstrap_source.py — give a brand-new adopter with NO
individual or team practice repo yet a real, working one in one command.

THE GAP THIS CLOSES. Every source in PRACTICE_ENGINE_PLAN.md's three-source
model (universal/team/individual) has always assumed the team or individual
repo already exists somewhere -- INSTALL.md step 9 and SETUP.md step 2 both
ask "do you already have one?" and simply stop if the answer is no. Nothing
in this repo has ever handed a new adopter a place to start. This tool does:
it instantiates templates/practice-set-individual/ or
templates/practice-set-team/ into a target directory, fills in the owner's
name (and, for a team, its first approver), and prints -- or, opted in,
writes -- the exact wiring a consuming repo or a person's own environment
needs next. See spec/BOOTSTRAP_NEW_SOURCES.md for the full procedure this
mechanizes, including the parts (creating the actual git remote) that stay a
human/session step on purpose -- this tool never touches a git remote or
any hosting API.

It also vendors a real, tracked, refreshable engine into the new set's own
tools/ -- see tools/precedent_vendor_engine.py's docstring. This closed a
gap discovered only after precedent-individual, precedent-team-maintainers
and precedent-team-tms already existed: nothing here had ever put an
engine file in place before, so every one of them got its copy from an
undocumented, one-off hand-copy instead (precedent-team-tms's turned out
to be missing outright). New sets no longer hit that gap; the three
existing ones were migrated onto the same mechanism separately.

Usage:
  precedent_bootstrap_source.py --level individual --name NAME --dest PATH
      [--write-user-config true]     # merge the individual source into
                                      # ~/.config/precedent/config.json
                                      # (or $PRECEDENT_USER_CONFIG)

  precedent_bootstrap_source.py --level team --name NAME --dest PATH \\
      --approver "Full Name:github-handle"[,"Second Name:handle2"...]
      [--write-repo-config PATH]     # merge the team source into
                                      # PATH/precedent.json (default: cwd)

  --force true    # allow writing into a non-empty --dest

Exit: 0 on success (prints the resulting config wiring either way); 1 on a
refusal (existing non-empty dest without --force, missing --approver for a
team, an individual --write-user-config that would clobber a *different*
individual set without --force).
"""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_vendor_engine

LEVELS = {'individual', 'team'}
SKELETONS = {
    'individual': ROOT / 'templates' / 'practice-set-individual',
    'team': ROOT / 'templates' / 'practice-set-team',
}
DEFAULT_USER_CONFIG = pathlib.Path.home() / '.config' / 'precedent' / 'config.json'
USER_CONFIG_ENV = 'PRECEDENT_USER_CONFIG'


class BootstrapRefused(Exception):
    """Carries the reason -- printed verbatim, same convention as
    precedent_promote.py's PromoteRefused."""


def _parse_approvers(raw):
    """'Name:gh,Name2:gh2' -> [{'name': 'Name', 'github': 'gh'}, ...].
    Each entry must carry a name; the github handle is optional but at
    least one of the two fields is required so precedent_land.py's
    approved_by lookup (name OR github) has something to match."""
    out = []
    for chunk in raw.split(','):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ':' in chunk:
            name, github = chunk.split(':', 1)
        else:
            name, github = chunk, ''
        name, github = name.strip(), github.strip()
        if not name and not github:
            continue
        out.append({'name': name, 'github': github})
    return out


def _substitute(text, mapping):
    for key, value in mapping.items():
        text = text.replace('{{' + key + '}}', value)
    return text


def _copy_skeleton(skeleton_dir, dest, mapping):
    """Copy every file under skeleton_dir into dest, substituting
    placeholders in every text file and stripping a trailing `.template`
    from the destination filename -- the same suffix convention every
    other templates/*.template file in this repo already uses."""
    written = []
    for src in sorted(skeleton_dir.rglob('*')):
        if src.is_dir():
            continue
        rel = src.relative_to(skeleton_dir)
        rel_str = str(rel)
        if rel_str.endswith('.template'):
            rel_str = rel_str[: -len('.template')]
        out_path = dest / rel_str
        out_path.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding='utf-8')
        out_path.write_text(_substitute(text, mapping), encoding='utf-8')
        written.append(out_path)
    return written


def _seed_approvers_json(dest, approvers):
    """approvers.json is written by _copy_skeleton with only the FIRST
    approver substituted into the template's single entry (placeholder
    substitution can't multiply a JSON array element). If more than one
    --approver was given, load what was written and append the rest as
    real JSON, rather than string-substituting a second time."""
    if len(approvers) <= 1:
        return
    path = dest / 'approvers.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['approvers'] = approvers
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def bootstrap(level, name, dest, approvers=None, force=False):
    if level not in LEVELS:
        raise BootstrapRefused(f"--level must be one of {sorted(LEVELS)}, got {level!r}")
    dest = pathlib.Path(dest).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()) and not force:
        raise BootstrapRefused(
            f"{dest} already exists and is not empty -- pass --force true to "
            f"write into it anyway (existing files with the same name are "
            f"overwritten; anything else already there is left alone)")
    if level == 'team' and not approvers:
        raise BootstrapRefused(
            "a team set needs at least one approver -- pass "
            '--approver "Full Name:github-handle" (whoever is creating this '
            "set is its first approver, per PRACTICE_ENGINE_PLAN.md's Stage 4)")

    dest.mkdir(parents=True, exist_ok=True)
    mapping = {'NAME': name, 'DEST_PATH': str(dest)}
    if level == 'team':
        first = approvers[0]
        mapping['APPROVER_NAME'] = first['name']
        mapping['APPROVER_GITHUB'] = first['github']

    written = _copy_skeleton(SKELETONS[level], dest, mapping)
    if level == 'team':
        _seed_approvers_json(dest, approvers)
    written += precedent_vendor_engine.seed(dest)

    return {'dest': dest, 'written': written}


def _load_json(path):
    if path.is_file():
        return json.loads(path.read_text(encoding='utf-8'))
    return None


def write_user_config(dest, name, force=False):
    """Merge the individual source into the user-level config -- never a
    shared project's own tracked file, per PRACTICE_ENGINE_PLAN.md's
    'THE PERSON declares their own individual set in their USER-LEVEL
    config' rule (also stated in tools/precedent_resolve.py)."""
    config_path = pathlib.Path(
        os.environ.get(USER_CONFIG_ENV) or DEFAULT_USER_CONFIG).expanduser()
    data = _load_json(config_path) or {'format_version': 1}
    existing = data.get('individual')
    if existing and existing.get('name') != name and not force:
        raise BootstrapRefused(
            f"{config_path} already names a different individual set "
            f"({existing.get('name')!r}) -- pass --force true to replace it, "
            f"or edit {config_path} yourself if that was deliberate")
    data['individual'] = {'name': name, 'path': str(dest)}
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return config_path


def write_repo_config(repo_config_dir, name, dest, force=False):
    """Merge the team source into PATH/precedent.json -- a shared,
    tracked file, per INSTALL.md step 9's 'if yes to a team source' shape.
    `path` is written relative to the config file's own directory, since
    that's how every existing team/repo-local entry in this repo's own
    precedent.json is written."""
    repo_config_dir = pathlib.Path(repo_config_dir).expanduser().resolve()
    config_path = repo_config_dir / 'precedent.json'
    data = _load_json(config_path) or {'format_version': 1, 'sources': []}
    sources = data.setdefault('sources', [])
    rel_path = os.path.relpath(dest, repo_config_dir)
    existing = next((s for s in sources if s.get('level') == 'team'
                      and s.get('name') == name), None)
    if existing:
        if existing.get('path') != rel_path and not force:
            raise BootstrapRefused(
                f"{config_path} already has a team source named {name!r} at "
                f"a different path ({existing.get('path')!r}) -- pass "
                f"--force true to overwrite it")
        existing['path'] = rel_path
    else:
        sources.append({'level': 'team', 'name': name, 'path': rel_path})
    config_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return config_path


def _parse_args(argv):
    args = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith('--') or i + 1 >= len(argv):
            sys.exit(f"precedent_bootstrap_source FAIL: expected --flag value "
                      f"pairs, stuck at {tok!r}")
        args[tok] = argv[i + 1]
        i += 2
    return args


def main():
    args = _parse_args(sys.argv[1:])
    level = args.get('--level')
    name = args.get('--name')
    dest = args.get('--dest')
    if level not in LEVELS or not name or not dest:
        sys.exit("precedent_bootstrap_source FAIL: --level "
                  f"({sorted(LEVELS)}), --name NAME and --dest PATH are all required")

    force = args.get('--force', 'false').lower() == 'true'
    approvers = _parse_approvers(args['--approver']) if args.get('--approver') else []

    try:
        result = bootstrap(level, name, dest, approvers=approvers, force=force)
    except BootstrapRefused as e:
        print(f"REFUSED: {e}")
        return 1

    dest_path = result['dest']
    print(f"BOOTSTRAPPED: {level} set {name!r} at {dest_path}")
    for f in result['written']:
        print(f"  wrote {f.relative_to(dest_path)}")
    print()

    try:
        if level == 'individual':
            if args.get('--write-user-config', 'false').lower() == 'true':
                config_path = write_user_config(dest_path, name, force=force)
                print(f"WROTE user config: {config_path}")
            else:
                print("Next step -- copy this into your own user-level config "
                      f"(default {DEFAULT_USER_CONFIG}, or wherever "
                      f"${USER_CONFIG_ENV} points):")
                print(json.dumps({'individual': {'name': name, 'path': str(dest_path)}}, indent=2))
        else:
            repo_config_arg = args.get('--write-repo-config')
            if repo_config_arg:
                config_path = write_repo_config(repo_config_arg, name, dest_path, force=force)
                print(f"WROTE repo config: {config_path}")
            else:
                print("Next step -- add this to the consuming project's own "
                      "precedent.json \"sources\" list:")
                print(json.dumps({'level': 'team', 'name': name, 'path': str(dest_path)}, indent=2))
    except BootstrapRefused as e:
        print(f"REFUSED (wiring not written; the set itself is): {e}")
        return 1

    print()
    print(f"The set itself still needs a real git remote -- see "
          f"spec/BOOTSTRAP_NEW_SOURCES.md for that last, deliberately manual step.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

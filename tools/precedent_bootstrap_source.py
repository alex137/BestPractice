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
gap discovered only after precedent-individual, precedent-team-repo-maintenance
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
      [--write-session-hook CONSUMING_PROJECT_PATH --repo-url URL]
                                      # instantiate the retry-capable
                                      # SessionStart hook (Claude Code
                                      # remote/web) into that CONSUMING
                                      # project's .claude/hooks/ -- see
                                      # tools/precedent_source_bootstrap.py

  precedent_bootstrap_source.py --level individual --name NAME \\
      --write-session-hook CONSUMING_PROJECT_PATH [--repo-url URL]
                                      # hook-only mode: writes the consuming
                                      # project's hook against a set that
                                      # already exists, and creates nothing.
                                      # OMIT --repo-url in a PUBLIC consuming
                                      # repo -- the baked-in value is tracked,
                                      # and each person's own private
                                      # ~/.config/precedent/config.json is
                                      # read ahead of it anyway.

  precedent_bootstrap_source.py --level team --name NAME --dest PATH \\
      --approver "Full Name:github-handle"[,"Second Name:handle2"...]
      [--write-repo-config PATH]     # merge the team source into
                                      # PATH/precedent.json (default: cwd)

  precedent_bootstrap_source.py --verify PATH [--level individual|team]
                                      # report whether an EXISTING set still
                                      # has the shape this tool gives a new
                                      # one; writes nothing. The level is read
                                      # off the set unless you name it. Exit 1
                                      # if anything is missing.

  --force true    # allow writing into a non-empty --dest

Exit: 0 on success (prints the resulting config wiring either way); 1 on a
refusal (existing non-empty dest without --force, missing --approver for a
team, an individual --write-user-config that would clobber a *different*
individual set without --force).
"""
import json
import os
import re
import subprocess
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_resolve
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


HARNESS_HOOKS = ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
# The two session hooks every new source gets, and the ONE thing about a
# source's shape that is not read off the skeleton directory. They live in
# the harness adapter, not in either skeleton, because a skeleton would
# need its own copy of each per level and the copies would drift; and
# because _copy_skeleton() writes text files with default permissions,
# while a hook that is not executable is a hook that silently never runs.
SESSION_HOOKS = ('freshness-guard.sh', 'commit-identity.sh')
HARNESS_HOOKS_REL = 'templates/harness/claude-code/hooks/'
# Named separately rather than derived as HARNESS_HOOKS_REL + '../settings.json':
# a path a person has to mentally normalise before they can go open it is a
# worse instruction than the path itself (practice: label-describes-content).
HARNESS_SETTINGS_REL = 'templates/harness/claude-code/settings.json'


WORKFLOW_TEMPLATES = (
    # (template under templates/github-actions/, path in the new set)
    ('views-drift.yml.template', '.github/workflows/views-drift.yml'),
)
WORKFLOWS_REL = 'templates/github-actions/'


def _install_workflows(dest):
    """Give a new source the CI gate its generated views had nowhere else.

    A set that vendors the engine generates AGENTS.md's loader block, MAP.md
    and GLOSSARY.md, and until 2026-09-11 nothing checked any of them
    outside this repo: verify_harness.py is deliberately not vendored
    (precedent_vendor_engine.py's own comment), and precedent_check.py's
    `generated-artifact-provenance` -- which does run `build_views.py
    --check` -- skips itself in a source set, because that check's practice
    is universal and a source set's practices/ holds only its own. Measured:
    an individual set's MAP.md sat three practices stale under a generated
    header claiming a guard was failing the build on exactly that.

    Same reasoning as _install_session_hooks: the workflow FILES are
    rewritten on every call, so a set this is re-run against picks up the
    current template, and verify() reports a set that never got one --
    every set created before this date is in that position, and this tool
    cannot reach them on its own.
    """
    written = []
    for template, rel in WORKFLOW_TEMPLATES:
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            (ROOT / 'templates' / 'github-actions' / template)
            .read_text(encoding='utf-8'), encoding='utf-8')
        written.append(out)
    return written


def _install_session_hooks(dest, base_branch='main'):
    """Give a new source the two hooks that keep its own sessions honest:
    freshness-guard.sh (never work on, or write to, a stale checkout) and
    commit-identity.sh (commits are authored by the person running the
    session, not the container's own bot account).

    Neither hook names a person. commit-identity.sh resolves whoever is
    actually running the session -- see its own header for the order it
    tries, and why the timezone is the only thing it is ever willing to
    guess at.

    WHERE A CHANGE TO THE WIRING BELOW DOES AND DOES NOT REACH. The hook
    FILES are rewritten on every call, so a set this runs against picks up
    the current scripts. The settings.json is written only when the set has
    none -- so adding an event here reaches sets created from now on, and
    never a set that already has a settings.json, including one this tool is
    re-run against. verify()'s wiring check below is what covers those: the
    generator cannot repair them, so something has to report them."""
    hooks_dir = dest / '.claude' / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in SESSION_HOOKS:
        out = hooks_dir / name
        out.write_text((HARNESS_HOOKS / name).read_text(encoding='utf-8'),
                       encoding='utf-8')
        out.chmod(0o755)
        written.append(out)

    settings = dest / '.claude' / 'settings.json'
    if not settings.exists():
        payload = {
            '_comment': [
                "Written by tools/precedent_bootstrap_source.py. The base branch is",
                "passed to freshness-guard.sh explicitly, as its second argument, and",
                "is not detected: at least one real repo's configured default branch is",
                "not the branch its work sits on top of. Change it here if this source's",
                "is not `main`.",
                "",
                "The PreToolUse matcher includes Bash deliberately -- an agent editing",
                "files through cat/sed/python3 never touches Edit or Write at all.",
                "",
                "The guard is wired THREE times, matching",
                "templates/harness/claude-code/settings.json. SessionStart fires once",
                "at the start and pre-write fires once at the first write, so a session",
                "left open across a break has spent both and nothing rechecks the",
                "checkout however far origin moves underneath it. UserPromptSubmit is",
                "the only one that keeps firing, so it is the only one that reaches",
                "that case; it is throttled to one real check per 600s and always exits",
                "0, because a UserPromptSubmit hook that exits non-zero eats the message",
                "somebody just typed.",
                "",
                "No env identity is set here: a source repo may have more than one",
                "person committing to it, and commit-identity.sh resolves each of them",
                "at session start instead of anybody being named in a tracked file.",
            ],
            'hooks': {
                'SessionStart': [{
                    'hooks': [
                        {'type': 'command',
                         'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/freshness-guard.sh session-start ' + base_branch},
                        {'type': 'command',
                         'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/commit-identity.sh'},
                    ],
                }],
                'UserPromptSubmit': [{
                    'hooks': [
                        {'type': 'command',
                         'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/freshness-guard.sh user-prompt ' + base_branch},
                    ],
                }],
                'PreToolUse': [{
                    'matcher': 'Edit|Write|NotebookEdit|Bash',
                    'hooks': [
                        {'type': 'command',
                         'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/freshness-guard.sh pre-write ' + base_branch},
                    ],
                }],
            },
        }
        settings.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
        written.append(settings)
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


def verify(level, path):
    """-> [str] the ways `path` falls short of what this level's skeleton and
    this tool's bootstrap produce: files it does not have, files that are
    malformed, and session hooks wired for fewer moments than the harness
    adapter wires them for. Not files alone -- the wiring findings name a
    file that IS present and a moment at which it does not run.

    The tool that DEFINES a source's shape is the one that can say whether
    a source still has it, so the definition is read straight off the
    skeleton rather than restated in a list that would drift from it.

    This exists because bootstrap only ever ran for sources created BY it.
    A source that was migrated into place instead -- assembled by hand from
    an older system -- never passed through here, and nothing afterwards
    ever asked whether it came out the right shape. 2026-09-06:
    `precedent-team-repo-maintenance`, migrated rather than bootstrapped, had no
    `leak-blocklist.txt` at all, while the team skeleton ships one and the
    set bootstrapped by this tool has it. Nobody had noticed, because
    nothing was looking.

    Contents are checked too, but only against what a real consumer of the
    file actually needs -- "well-formed" defined by the tools that read it,
    not by a wish list. build_codeowners.py refuses an approvers.json with
    no approvers or an approver with no `github`, so a source carrying one
    is already broken and simply has not been run against yet;
    precedent_resolve.py needs an individual config to name a set; and a
    file still holding a `{{PLACEHOLDER}}` was bootstrapped and never
    finished, which no consumer can do anything sensible with.

    An empty blocklist stays fine on purpose (`blank-blocklist`): an empty
    one is a deliberate state, an absent one is a gap."""
    skeleton = SKELETONS.get(level)
    if skeleton is None or not skeleton.is_dir():
        return []
    path = pathlib.Path(path)
    missing = []
    for src in sorted(skeleton.rglob('*')):
        if not src.is_file():
            continue
        rel = src.relative_to(skeleton)
        # practices/ holds the skeleton's own example, which a real source
        # is expected to have deleted -- its presence is what
        # example-starter tells the adopter to remove.
        if rel.parts and rel.parts[0] == 'practices':
            continue
        for name in (rel.name, rel.name.replace('.template', '').replace('.sample', '')):
            if (path / rel.parent / name).exists():
                break
        else:
            missing.append(str(rel))
    # The session hooks are the one part of a source's shape that does NOT
    # come from the skeleton -- they live in the harness adapter, one copy,
    # so say where each missing thing actually comes from rather than
    # letting the caller assert a single origin for the whole list.
    wired = _wired_hook_paths(path)
    for name in SESSION_HOOKS:
        # What matters is that the hook is installed AND wired, not that it
        # sits at the path bootstrap() happens to write. A source that keeps
        # its hooks elsewhere and points settings.json at them is correct:
        # precedent-individual wires both from bootstrap/, which its own
        # commit-author practice documents. Checking the literal path
        # reported that working source as broken.
        if (path / '.claude' / 'hooks' / name).exists():
            continue
        if any(w.name == name and (path / w).exists() for w in wired):
            continue
        missing.append(f"{pathlib.Path('.claude') / 'hooks' / name} "
                       f"(from {HARNESS_HOOKS_REL}, and unwired: no command "
                       f"in .claude/settings.json points at a copy of it)")
    # Like the hooks, the workflows are not in either skeleton -- they come
    # from templates/github-actions/, one copy, shared with dependent repos.
    # A set bootstrapped before 2026-09-11 has none of them.
    for _template, rel in WORKFLOW_TEMPLATES:
        if not (path / rel).exists():
            missing.append(f"{rel} (from {WORKFLOWS_REL}{_template}; without "
                           f"it nothing checks this set's generated views for "
                           f"drift -- verify_harness.py is not vendored here "
                           f"and precedent_check.py's provenance check skips "
                           f"itself in a source set)")

    if not (path / '.claude' / 'settings.json').exists():
        missing.append(f"{pathlib.Path('.claude') / 'settings.json'} "
                       f"(written by this tool's bootstrap, not shipped in "
                       f"either skeleton)")
    else:
        # A hook that EXISTS and is wired can still be wired for fewer
        # moments than the adapter wires it for, and the checks above cannot
        # see that: they ask whether the file runs, not when. Every set
        # bootstrapped between 2026-09-06 and the day this check landed was
        # missing the guard's `user-prompt` wiring for exactly that reason
        # and audited clean throughout.
        want = _template_guard_modes()
        have = _source_guard_modes(path)
        for mode in sorted(want - have):
            missing.append(f"freshness-guard.sh `{mode}` is installed but NOT "
                           f"WIRED in .claude/settings.json (the adapter at "
                           f"{HARNESS_SETTINGS_REL} wires it)")
    return missing + _malformed(level, path)


def _template_guard_modes():
    """-> {str} freshness-guard modes the harness adapter's own settings.json
    wires. Read off the template rather than listed here: a hardcoded list
    would be one more copy of the wiring, and copies of this wiring drifting
    from each other is the exact failure this check exists to catch."""
    tmpl = ROOT / 'templates' / 'harness' / 'claude-code' / 'settings.json'
    try:
        data = json.loads(tmpl.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return set()
    return _guard_modes(data)


def _guard_modes(settings_data):
    """-> {str} the MODE argument of every freshness-guard.sh command in a
    parsed settings.json, whatever path it is invoked by.

    The mode, not the whole command: the base branch is passed explicitly
    and differs per repo on purpose (BestPractice's own base is not `main`),
    so comparing command strings would report that deliberate difference as
    drift."""
    out = set()

    def _walk(node):
        if isinstance(node, dict):
            cmd = node.get('command')
            if isinstance(cmd, str) and 'freshness-guard.sh' in cmd:
                parts = cmd.split()
                for i, word in enumerate(parts):
                    if word.endswith('freshness-guard.sh') and i + 1 < len(parts):
                        out.add(parts[i + 1])
                        break
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for v in node:
                _walk(v)

    _walk(settings_data.get('hooks', {}))
    return out


def _source_guard_modes(path):
    """-> {str} freshness-guard modes a source's own settings.json wires."""
    settings = path / '.claude' / 'settings.json'
    if not settings.is_file():
        return set()
    try:
        return _guard_modes(json.loads(settings.read_text(encoding='utf-8')))
    except (OSError, json.JSONDecodeError):
        return set()


def _wired_hook_paths(path):
    """-> [pathlib.Path] repo-relative paths a source's own
    .claude/settings.json actually invokes as hooks.

    Read rather than assumed, because the question the shape check is
    really asking is whether the hook RUNS, and a source is free to keep it
    somewhere other than where bootstrap() writes it."""
    settings = path / '.claude' / 'settings.json'
    if not settings.is_file():
        return []
    try:
        data = json.loads(settings.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return []
    out = []
    def _walk(node):
        if isinstance(node, dict):
            cmd = node.get('command')
            if isinstance(cmd, str):
                # Strip the harness variable and any arguments: what is left
                # is the path the hook is invoked by.
                word = cmd.split()[0] if cmd.split() else ''
                word = word.replace('$CLAUDE_PROJECT_DIR/', '')
                word = word.replace('${CLAUDE_PROJECT_DIR}/', '')
                if word:
                    out.append(pathlib.Path(word))
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for v in node:
                _walk(v)
    _walk(data)
    return out


PLACEHOLDER_RE = re.compile(r'\{\{[A-Z_]+\}\}')


def _malformed(level, path):
    """-> [str] ways this source's files are present but unusable."""
    path = pathlib.Path(path)
    out = []

    # A file bootstrapped and never filled in. Any consumer reading a
    # `{{NAME}}` gets a literal placeholder where a real value belongs.
    for rel in ('approvers.json', 'leak-blocklist.txt', 'config.json.sample',
                'README.md', 'identity.json'):
        f = path / rel
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        found = sorted(set(PLACEHOLDER_RE.findall(text)))
        if found:
            out.append(f'{rel} still holds unfilled {", ".join(found)}')

    if level == 'team':
        f = path / 'approvers.json'
        if f.is_file():
            # Exactly what build_codeowners.py refuses. A source that fails
            # here is already broken; it just has not been run against yet.
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError) as e:
                out.append(f'approvers.json is not valid JSON -- {e}')
            else:
                approvers = data.get('approvers') or []
                if not approvers:
                    out.append('approvers.json declares no approvers -- '
                               'build_codeowners.py refuses this, and a team '
                               'set always has at least one')
                for entry in approvers:
                    if not isinstance(entry, dict) or not entry.get('github'):
                        out.append(f'approvers.json entry {entry!r} has no '
                                   f'"github" -- CODEOWNERS needs a username '
                                   f'to address, not just a name')

    if level == 'individual':
        f = path / 'config.json.sample'
        if f.is_file():
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError) as e:
                out.append(f'config.json.sample is not valid JSON -- {e}')
            else:
                ind = data.get('individual') or {}
                for field in ('name', 'path'):
                    if not ind.get(field):
                        out.append(f'config.json.sample has no '
                                   f'individual.{field} -- precedent_resolve.py '
                                   f'reads exactly this shape')

    # Every source level ships practices/. A source with none resolves to
    # nothing, which the loader reports as a source contributing zero rules
    # rather than as a source that is broken.
    pdir = path / 'practices'
    if not pdir.is_dir():
        out.append('no practices/ directory')
    elif not any(pdir.glob('*.md')):
        out.append('practices/ holds no practice files')

    return out


def _warn_if_clone_is_stale():
    """Say so, loudly, if THIS checkout is behind its own origin before we
    seed a new set from it.

    practice: cite-the-incident -- seed() copies the engine from this
    checkout's HEAD, so a new set's engine version is silently whatever the
    operator's clone happened to be at. Bootstrap from a clone that is
    months behind and the set starts life months behind, with
    ENGINE_MANIFEST.json honestly recording that old commit and nobody with
    any reason to look at it. That is not hypothetical: two existing sets
    spent 2026-09-06 more than two hundred commits behind, generating a
    loader block with a defect fixed upstream days earlier, and nothing
    anywhere said so.

    A warning, never a refusal. Bootstrapping offline, or from a
    deliberately pinned checkout, is legitimate; and a network failure here
    must not stop someone creating their practice set. But silence has to
    mean "checked and current" -- so an unreachable remote says THAT,
    rather than nothing, which would be indistinguishable from a clean
    result."""
    ok, _ = _git('fetch', '--quiet', 'origin', precedent_vendor_engine.SOURCE_BRANCH)
    if not ok:
        print(f"NOTE: could not reach origin to check whether this BestPractice "
              f"checkout is current, so the engine about to be vendored is "
              f"whatever this clone holds. Not verified.", file=sys.stderr)
        return
    ok, behind = _git('rev-list', '--count',
                      f'HEAD..origin/{precedent_vendor_engine.SOURCE_BRANCH}')
    if ok and behind.isdigit() and int(behind) > 0:
        print(f"WARNING: this BestPractice checkout is {behind} commit(s) behind "
              f"origin/{precedent_vendor_engine.SOURCE_BRANCH}, and the new set's "
              f"engine is copied from THIS checkout -- it will start life "
              f"{behind} commit(s) stale. `git checkout -B "
              f"{precedent_vendor_engine.SOURCE_BRANCH} "
              f"origin/{precedent_vendor_engine.SOURCE_BRANCH}` first if you want "
              f"the current engine.", file=sys.stderr)


def _git(*args):
    """(ok, stdout), never raising, and never returning stdout on failure --
    see tools/precedent_refresh_sources.py's own _git for the rev-parse trap
    this shape exists to make impossible."""
    try:
        r = subprocess.run(['git', *args], cwd=str(ROOT),
                           capture_output=True, text=True)
    except OSError as exc:
        return False, str(exc)
    return r.returncode == 0, (r.stdout or '').strip()


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

    _warn_if_clone_is_stale()
    written = _copy_skeleton(SKELETONS[level], dest, mapping)
    if level == 'team':
        _seed_approvers_json(dest, approvers)
    written += _install_session_hooks(dest)
    written += _install_workflows(dest)
    written += precedent_vendor_engine.seed(dest)

    return {'dest': dest, 'written': written}


def _load_json(path):
    if path.is_file():
        return json.loads(path.read_text(encoding='utf-8'))
    return None


def write_user_config(dest, name, force=False, repo_url=None):
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
    entry = {'name': name, 'path': str(dest)}
    # The URL belongs here and nowhere shared: the session hook that clones
    # this set reads it from this private file rather than carrying it in a
    # consuming repo's tracked tree, where it would publish the existence and
    # location of a private repository (2026-09-07).
    if repo_url:
        entry['repo_url'] = repo_url
    data['individual'] = entry
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return config_path


SESSION_HOOK_TEMPLATE = (ROOT / 'templates' / 'harness' / 'claude-code' / 'hooks'
                         / 'individual-source-bootstrap.sh.template')
SESSION_HOOK_DEST_REL = pathlib.Path('.claude') / 'hooks' / 'precedent-individual-bootstrap.sh'


def write_session_hook(consuming_project, name, repo_url, force=False):
    """Instantiate the canonical SessionStart hook
    (templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template)
    into a CONSUMING project -- not the individual set's own repo -- at
    .claude/hooks/precedent-individual-bootstrap.sh, so an ephemeral session
    there can resolve this person's individual set with zero manual steps.
    See tools/precedent_source_bootstrap.py's module docstring for why this
    hook retries rather than cloning once, and INSTALL.md step 9's
    individual-source branch for where this fits in the install
    conversation. Never touches a git remote (same limit as bootstrap()
    itself) -- repo_url is supplied by the caller, typically right after
    creating that remote per spec/BOOTSTRAP_NEW_SOURCES.md step 2."""
    consuming_project = pathlib.Path(consuming_project).expanduser().resolve()
    dest = consuming_project / SESSION_HOOK_DEST_REL
    if dest.exists() and not force:
        raise BootstrapRefused(
            f"{dest} already exists -- pass --force true to overwrite it")
    # SOURCE_REPO_URL_SUBSTITUTED is the sentinel the hook's own guard
    # reads -- see the template's "HOW THIS FILE KNOWS ITS BAKED-IN DEFAULT
    # IS REAL" block. It must be substituted here and nowhere else: the
    # guard used to test the URL placeholder's own value, which this
    # substituter rewrote along with every other occurrence, so every hook
    # written with a real --repo-url short-circuited to "no repository URL"
    # (2026-09-10). Writing `yes` unconditionally is correct even for the
    # no-URL instantiation below: the file IS instantiated, it simply
    # carries no default, which the guard reads as an empty string.
    text = _substitute(SESSION_HOOK_TEMPLATE.read_text(encoding='utf-8'),
                       {'SOURCE_NAME': name,
                        'SOURCE_REPO_URL': repo_url or '',
                        'SOURCE_REPO_URL_SUBSTITUTED': 'yes'})
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding='utf-8')
    dest.chmod(0o755)
    return dest


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
    # `--help` is the first thing anyone types, and until 2026-09-06 every
    # tool here answered it with "FAIL: expected --flag value pairs, stuck at
    # '--help'" -- a hard error, on the exact command documentation/ tells a
    # new reader to run. The module docstring is already the usage text; print
    # it and exit 0.
    if any(a in ('--help', '-h') for a in argv):
        print((sys.modules['__main__'].__doc__ or __doc__ or '').strip())
        raise SystemExit(0)
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


def _infer_level(path):
    """-> 'team' | 'individual' | None, read off the set itself.

    Asking the operator for --level on a set that already exists is asking
    them to restate something the directory already says: a team set carries
    approvers.json (build_codeowners.py refuses one without it), an
    individual set carries an identity or a config naming its owner. Guessing
    wrong is cheap to notice and never destructive -- verify() only reads.
    """
    if (path / 'approvers.json').exists():
        return 'team'
    for name in ('identity.json', 'config.json', 'config.json.sample'):
        if (path / name).exists():
            return 'individual'
    return None


def main():
    args = _parse_args(sys.argv[1:])

    # --verify PATH: report whether an EXISTING set still has the shape this
    # tool gives a new one. verify() had no command-line route until
    # 2026-09-11, while three documents told operators to run one -- a
    # command named in a document and absent from the tool, which is the
    # same defect the views-drift work landed that day was fixing one level
    # up (practice: cite-the-incident).
    if args.get('--verify'):
        target = pathlib.Path(args['--verify']).expanduser()
        if not target.is_dir():
            sys.exit(f"precedent_bootstrap_source FAIL: --verify {target} is "
                     f"not a directory")
        level = args.get('--level') or _infer_level(target)
        if level not in LEVELS:
            sys.exit(f"precedent_bootstrap_source FAIL: cannot tell whether "
                     f"{target} is a team or an individual set (no "
                     f"approvers.json, identity.json or config.json) -- pass "
                     f"--level {sorted(LEVELS)} explicitly")
        missing = verify(level, target)
        if not missing:
            print(f"precedent_bootstrap_source --verify OK: {target} has the "
                  f"shape of a complete {level} set")
            return 0
        print(f"precedent_bootstrap_source --verify FAIL: {target} is missing "
              f"{len(missing)} thing(s) a complete {level} set has:")
        for m in missing:
            print(f"  - {m}")
        return 1

    level = args.get('--level')
    name = args.get('--name')
    dest = args.get('--dest')

    # HOOK-ONLY MODE: --write-session-hook with no --dest.
    #
    # The hook belongs to the CONSUMING project and names an individual set
    # that already exists somewhere else -- writing it has nothing to do with
    # creating a set. But until 2026-09-06 it was reachable only after
    # bootstrap() succeeded, so a project that needed the hook had to name a
    # --dest and create (or --force over) a whole individual set to get it.
    # INSTALL.md and spec/BOOTSTRAP_NEW_SOURCES.md both already told operators
    # to "run it again against an already-bootstrapped set", which the CLI
    # could not do. BestPractice itself went without the hook for that reason,
    # and a session that then could not resolve an individual source had no
    # way to say whether one existed -- the silence fixed separately in
    # tools/precedent_resolve.py.
    if args.get('--write-session-hook') and not dest:
        # --repo-url IS OPTIONAL HERE, and deliberately so (2026-09-10).
        # The hook resolves its URL from PRECEDENT_INDIVIDUAL_REPO, then
        # from the person's private ~/.config/precedent/config.json, and
        # only then from the value baked in here -- and the baked-in value
        # goes into a file the consuming repo TRACKS, which in a PUBLIC
        # consumer publishes the existence and location of somebody's
        # private practice set. The template's own header says exactly
        # that. Requiring the flag meant a public consumer had no way to
        # ask for the hook without the leak, so it either took the leak or
        # went without the hook. Omit it and the hook is still fully
        # instantiated; it simply carries no default.
        repo_url = args.get('--repo-url') or ''
        if level != 'individual' or not name:
            sys.exit("precedent_bootstrap_source FAIL: writing only the "
                     "session hook needs --level individual and --name NAME "
                     "(and optionally --repo-url URL, the set's real git "
                     "remote -- this tool never guesses a remote on your "
                     "behalf, and a PUBLIC consuming repo should omit it and "
                     "let each person's own ~/.config/precedent/config.json "
                     "supply it privately)."
                     )
        try:
            precedent_resolve.check_source_name(level, name, '--name')
            hook_path = write_session_hook(
                args['--write-session-hook'], name, repo_url,
                force=args.get('--force', 'false').lower() == 'true')
        except (precedent_resolve.ResolveError, BootstrapRefused) as e:
            sys.exit(f"precedent_bootstrap_source FAIL: {e}")
        print(f"WROTE session-start hook: {hook_path} (no individual set was "
              f"created or touched -- this mode writes the consuming "
              f"project's hook and nothing else)")
        if repo_url:
            print(f"  baked-in default URL: {repo_url} -- read LAST, after "
                  f"PRECEDENT_INDIVIDUAL_REPO and ~/.config/precedent/"
                  f"config.json. If this consuming repo is public, that URL "
                  f"is now published; re-run without --repo-url to remove it.")
        else:
            print("  no URL baked in -- each person's own "
                  "PRECEDENT_INDIVIDUAL_REPO or ~/.config/precedent/"
                  "config.json supplies it, so nothing about a private set "
                  "is published by this file.")
        return 0

    if level not in LEVELS or not name or not dest:
        sys.exit("precedent_bootstrap_source FAIL: --level "
                  f"({sorted(LEVELS)}), --name NAME and --dest PATH are all "
                  f"required (except when writing only a session hook: "
                  f"--write-session-hook PATH --repo-url URL, with --name)")

    # practice: source-naming -- this tool is where a person's chosen name
    # first becomes a real repository, so it is the last place a wrong one is
    # cheap to fix. Refuse here rather than at resolve time, when the
    # repository already exists and renaming it breaks references.
    try:
        precedent_resolve.check_source_name(level, name, '--name')
    except precedent_resolve.ResolveError as e:
        sys.exit(f"precedent_bootstrap_source FAIL: {e}")

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
                config_path = write_user_config(dest_path, name, force=force,
                                                repo_url=args.get('--repo-url'))
                print(f"WROTE user config: {config_path}")
            else:
                print("Next step -- copy this into your own user-level config "
                      f"(default {DEFAULT_USER_CONFIG}, or wherever "
                      f"${USER_CONFIG_ENV} points):")
                print(json.dumps({'individual': {'name': name, 'path': str(dest_path)}}, indent=2))
            session_hook_arg = args.get('--write-session-hook')
            if session_hook_arg:
                repo_url = args.get('--repo-url')
                if not repo_url:
                    raise BootstrapRefused(
                        "--write-session-hook also needs --repo-url (the "
                        "real git remote for this individual set, created "
                        "per spec/BOOTSTRAP_NEW_SOURCES.md step 2) -- the "
                        "hook has to name it, and this tool never guesses a "
                        "remote on your behalf")
                hook_path = write_session_hook(session_hook_arg, name, repo_url, force=force)
                print(f"WROTE session-start hook: {hook_path} "
                      f"(makes this individual set resolvable on an "
                      f"ephemeral/hosted session with zero manual steps -- "
                      f"see spec/BOOTSTRAP_NEW_SOURCES.md)")
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

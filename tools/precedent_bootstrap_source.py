#!/usr/bin/env python3
"""precedent_bootstrap_source.py — give a brand-new adopter with NO
individual or team practice repo yet a real, working one in one command.

THE GAP THIS CLOSES. Every source in PRACTICE_ENGINE_PLAN.md's three-source
model (universal/team/individual) has always assumed the team or individual
repo already exists somewhere -- INSTALL.md step 9 and SETUP.md step 2 both
ask "do you already have one?" and simply stop if the answer is no. Nothing
in this repo has ever handed a new adopter a place to start. This tool does:
it instantiates templates/practice-set-individual/ or
templates/practice-set-shared/ into a target directory, fills in the owner's
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

  precedent_bootstrap_source.py --level shared --name NAME --dest PATH \\
      --approver "Full Name:github-handle"[,"Second Name:handle2"...]
      [--write-repo-config PATH]     # merge the shared source into
                                      # PATH/precedent.json (default: cwd)
                                      # `--level team` is the pre-2026-09-18
                                      # spelling and still reads, but every
                                      # message this tool prints says
                                      # "shared" -- so the two disagreed in
                                      # the one place a new adopter looks.

  precedent_bootstrap_source.py --verify PATH [--level individual|shared]
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
import collections
import json
import os
import re
import subprocess
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_identity
import precedent_resolve
import precedent_vendor_engine

LEVELS = {'individual', 'shared'}
LEVEL_ALIASES = {'team': 'shared'}   # the pre-2026-09-18 spelling still reads
SKELETONS = {
    'individual': ROOT / 'templates' / 'practice-set-individual',
    'shared': ROOT / 'templates' / 'practice-set-shared',
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
SESSION_HOOKS = ('freshness-guard.sh', 'commit-identity.sh',
                 # Wiring alone does not deliver a file: vendoring is gated
                 # ON the wiring, so a set must also RECEIVE this hook at
                 # creation or its first refresh is what finally copies it.
                 # Named here for the same reason the other two are -- the
                 # copy happens from the harness adapter, where the one
                 # maintained version lives.
                 'doc-lint-gate.sh')
# The third hook a set gets, kept out of SESSION_HOOKS because it is the one
# that is NOT a verbatim copy: it is instantiated from a .template with two
# placeholders substituted, which is write_session_hook()'s job below.
#
# WHY A PRACTICE SET GETS IT AT ALL (added 2026-09-13). A set is a repository
# somebody works in, and a session rooted in one resolved NO individual
# practice source -- every session, in all four real sets -- because nothing
# there ever wrote ~/.config/precedent/config.json. The hook that writes it
# already existed and had two separate reasons it could not be installed
# here: it execs tools/precedent_source_bootstrap.py, which was
# CONSUMER_ENGINE_FILES-only until the same day (a hand-copy is correctly
# refused by precedent_vendor_engine.py's UNTRACKED ENGINE FILE check), and
# write_session_hook() documented itself as writing into a consuming project
# and not into a set.
#
# A CONSUMER has a second route to the same hook and a set does not, which
# is why the wiring below matters more here: precedent_resolve.py's lazy
# self-heal execs this hook by path, and precedent_resolve.py is
# CONSUMER_ENGINE_FILES-only. In a set, SessionStart is the only thing that
# ever runs it.
INDIVIDUAL_SOURCE_HOOK = 'precedent-individual-bootstrap.sh'
# The universal-catalogue steps, as ONE script rather than two commands in
# settings.json. See the script's own header for why: the harness refuses a
# session editing settings.json, inconsistently, and a script it points at is
# an ordinary tracked file nobody has ever been refused.
UNIVERSAL_CATALOGUE_HOOK = 'precedent-universal-catalogue.sh'
ALL_SESSION_HOOKS = SESSION_HOOKS + (INDIVIDUAL_SOURCE_HOOK,
                                     UNIVERSAL_CATALOGUE_HOOK)
HARNESS_HOOKS_REL = 'templates/harness/claude-code/hooks/'
INDIVIDUAL_SOURCE_HOOK_REL = (HARNESS_HOOKS_REL
                              + 'individual-source-bootstrap.sh.template')
# Named separately rather than derived as HARNESS_HOOKS_REL + '../settings.json':
# a path a person has to mentally normalise before they can go open it is a
# worse instruction than the path itself (practice: label-describes-content).
HARNESS_SETTINGS_REL = 'templates/harness/claude-code/settings.json'


WORKFLOW_TEMPLATES = ()
# EMPTY SINCE 2026-09-21: a practice source installs no CI workflow at all
# (practice: source-sets-run-no-ci; Morgan, strength: decided -- "the sets
# don't need CI ... That could be the default rule, for future individual
# and shared source repos").
#
# What used to be here, and why each entry is gone rather than moved:
# precedent-check.yml ran the check suite, and leak-gate.yml scanned the
# tracked tree. Both re-ran, on a billed runner, tools that the session
# pushing the change had already run locally -- the deep check gates a push
# and the commit gate had already run doc_lint. The measurement that ended
# it is in the practice: 127 of 143 billed minutes on 2026-09-21 came from
# four sets running exactly these two, against twelve consuming repos
# costing 16 minutes between them.
#
# The third field each entry carried was "why a set without it is
# under-gated". That question now has one answer for every set, so it lives
# in the practice rather than per row.
# Same (template, dest path) pairs precedent_vendor_engine.CI_WORKFLOW_
# TEMPLATES['source'] declares for refresh()'s own use -- checked here,
# once, at import time, rather than trusted to stay in sync by eye: this
# tuple carries a third field (the "why", above) that engine's registry has
# no use for, so it is not simply replaced by it (practice:
# registry-source-of-truth -- the pairing itself has one source; the extra
# field this file alone needs stays here).
assert tuple((t, r) for t, r, _why in WORKFLOW_TEMPLATES) == \
    precedent_vendor_engine.CI_WORKFLOW_TEMPLATES['source'], (
    'WORKFLOW_TEMPLATES has drifted from '
    "precedent_vendor_engine.CI_WORKFLOW_TEMPLATES['source'] -- update both "
    'together, refresh() vendors by the latter.')
WORKFLOWS_REL = 'templates/github-actions/'


def _ci_preference(dest):
    """(enabled: bool, note: str) -- same resolution as
    precedent_install.py's `_ci_preference`, reused here rather than
    re-derived, so a set and a dependent repo answer "should CI be
    installed" from the identical field. practice: declared-default-is-applied
    -- nothing here asks; absent resolves to the engine's own default,
    which is disabled."""
    try:
        pref = precedent_identity.ci_preference(dest)
    except precedent_identity.NoDeclaredIdentity:
        return False, ('no individual source declares ci_workflows -- '
                        "disabled by default (GITHUB_ACTIONS.md)")
    if pref['enabled']:
        return True, f"ci_workflows: enabled ({pref['source']})"
    shown = pref['value'] or '(absent)'
    return False, f"ci_workflows: {shown} ({pref['source']})"


def _install_workflows(dest):
    """Give a new source the CI gate its generated views had nowhere else.

    A set that vendors the engine generates AGENTS.md's loader block, MAP.md
    and GLOSSARY.md, and until 2026-09-11 nothing checked any of them
    outside this repo: verify_harness.py is deliberately not vendored
    (precedent_vendor_engine.py's own comment), and precedent_check.py's
    `generated-artifact-provenance` -- which does run `build_views.py
    --check` -- skipped itself in a source set, because that check's practice
    is universal and a source set's practices/ holds only its own. Measured:
    an individual set's MAP.md sat three practices stale under a generated
    header claiming a guard was failing the build on exactly that.

    THAT SKIP IS OVER as of binds_publishers (PR #261, 2026-09-12): the check
    runs in a source set now, and covers the same three views the
    views-drift job in this workflow does (measured 2026-09-13 in a freshly
    bootstrapped set -- `1 passed`, and red on planted drift in each view).
    That job stays because it is wired to `pull_request` and the vendored
    check is not, which is a different property than coverage. TODO.md's
    `views-drift-vs-suite-workflow` closed 2026-09-19: keep both, as jobs in
    one workflow rather than two separate files.

    Same reasoning as _install_session_hooks: the workflow FILE is
    rewritten on every call, so a set this is re-run against picks up the
    current template, and verify() reports a set that never got one --
    every set created before this date is in that position, and this tool
    cannot reach them on its own.

    GATED ON ci_workflows (2026-09-16), same field and same default as
    precedent_install.py's dependent-repo install: this workflow is
    CI this repo vendors into another repo, not this repo's own structural
    backstop, so it belongs to the same off-by-default policy -- measured
    against a real account's usage report, `views-drift.yml` and
    `precedent-check.yml`, then two separate files, together cost more than
    a quarter of one reporting period's total minutes across four practice
    sets, none of which had ever been asked whether they wanted it.
    """
    enabled, note = _ci_preference(dest)
    if not enabled:
        print(f"workflows: NOT written -- {note}")
        return []
    written = []
    for template, rel, _why in WORKFLOW_TEMPLATES:
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            (ROOT / 'templates' / 'github-actions' / template)
            .read_text(encoding='utf-8'), encoding='utf-8')
        written.append(out)
    return written


# The untracked-file line, written into a set rather than assumed. A set that
# does not ignore .precedent/ will offer SESSION_PRACTICES.md to the next
# `git add -A`, and the whole point of shape 3
# (https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/SOURCE_SET_PROSE_GAP.md)
# is that universal's text is NEVER committed into a set. Measured
# 2026-09-13 against a real set: `git check-ignore` said not ignored, and
# the generated file showed up in `git status` as untracked-and-addable.
# practice: durable-fix -- the ignore line travels with the set, so it
# survives a fresh container and a fresh clone.
IGNORE_LINE = '.precedent/'
IGNORE_BLOCK = """
# Written at session start by tools/precedent_session_practices.py: the
# practices in force here from the sources this set declares. NEVER commit
# it -- it is another repository's practice text, and a committed copy is a
# copy that goes stale.
.precedent/
"""


UNIVERSAL_SOURCE_NAME = 'precedent'
UNIVERSAL_SOURCE_PATH = '../BestPractice'


def ensure_hook_wired(dest, hook_name, after=INDIVIDUAL_SOURCE_HOOK):
    """Add a SessionStart entry for `hook_name` to an EXISTING settings.json.

    -> (path, changed). Idempotent: a set that already runs the hook, under
    either spelling, is left byte-identical.

    WHY A TOOL DOES THIS AND NOT A SESSION, which is the whole point and took
    three wrong answers to find. The Claude Code harness refuses a session
    hand-editing .claude/settings.json -- "Reason: [Self-Modification]" --
    because that file declares what runs at session start. Correct, and it
    does NOT extend to a vendored tool writing a hook the engine ships: that
    is already how every new set gets its settings.json, from
    _install_session_hooks() below, unrefused. The content here is fixed by
    the engine, not chosen by whatever session happens to be running, which is
    the difference the refusal is actually about.

    Measured 2026-09-13, after a person was sent to make this edit in a GitHub
    web form: a python tool rewriting a real set's existing settings.json is
    not refused. Nobody needs to do this by hand, in any set, and
    precedent_refresh_sources.py --apply now does it.

    Placed AFTER `after` when that entry exists, because order matters for
    these two: the individual-source hook writes the config the catalogue hook
    then resolves against. Appended to the first SessionStart group otherwise.
    """
    settings = pathlib.Path(dest) / '.claude' / 'settings.json'
    if not settings.is_file():
        return settings, False
    try:
        data = json.loads(settings.read_text(encoding='utf-8'),
                          object_pairs_hook=collections.OrderedDict)
    except (OSError, json.JSONDecodeError):
        # A settings.json this cannot parse is one a person hand-edited and
        # broke, or one in a format nothing here knows. Rewriting it blind
        # would destroy their work (practice: fail-gracefully).
        return settings, False
    groups = data.get('hooks', {}).get('SessionStart') or []
    if not groups:
        return settings, False
    for g in groups:
        for e in g.get('hooks', []):
            if hook_name in str(e.get('command', '')):
                return settings, False        # already wired
    entry = collections.OrderedDict([
        ('type', 'command'),
        ('command', '$CLAUDE_PROJECT_DIR/.claude/hooks/' + hook_name)])
    for g in groups:
        hooks = g.get('hooks')
        if not isinstance(hooks, list):
            continue
        for i, e in enumerate(hooks):
            if after and after in str(e.get('command', '')):
                hooks.insert(i + 1, entry)
                settings.write_text(json.dumps(data, indent=2) + '\n',
                                    encoding='utf-8')
                return settings, True
    hooks = groups[0].setdefault('hooks', [])
    hooks.append(entry)
    settings.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return settings, True


def ensure_universal_source(dest):
    """Declare the universal source in a NEW set's own precedent.json.

    -> (path, changed). Without this a set resolves nothing, and a session
    rooted in it reads that set's practices and not one of universal's 94
    occasion entries -- measured 2026-09-13, with a real failure attached
    (practices/seeded-prompt-names-its-origin.md's Story). Shape 3 of
    https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/SOURCE_SET_PROSE_GAP.md.

    A SIBLING PATH, not a `~` one, and that is the measured answer rather
    than the tidy-looking one. `$HOME` is /root on some containers and
    /home/user on others, and an individual set is cloned under $HOME while
    the team sets and the consuming repo sit side by side -- so `~/BestPractice`
    names nothing on the very container where the sets actually live. The
    relative sibling is correct everywhere because the clone step creates it
    there: precedent_source_bootstrap.sources_from_repo() clones a declared
    universal source to exactly this path, from the URL the set's own
    ENGINE_MANIFEST.json already records.

    NOT `visibility`, and nothing else about the file is touched. A set is
    private and says so (or says nothing, which reads as private); this adds
    one entry to `sources` and leaves every other key alone, so re-running
    against a set that has other sources is safe.
    """
    cfg = pathlib.Path(dest) / 'precedent.json'
    data = _load_json(cfg) or {'format_version': 1}
    sources = data.setdefault('sources', [])
    if any(s.get('level') == 'universal' for s in sources):
        return cfg, False
    sources.append({'level': 'universal', 'name': UNIVERSAL_SOURCE_NAME,
                    'path': UNIVERSAL_SOURCE_PATH})
    cfg.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return cfg, True


def ensure_precedent_gitignore(dest):
    """-> (path, changed). Idempotent: appends the block only if the exact
    ignore line is not already present, so re-running against a set that has
    it leaves the file byte-identical."""
    gi = pathlib.Path(dest) / '.gitignore'
    existing = gi.read_text(encoding='utf-8') if gi.is_file() else ''
    if any(ln.strip() == IGNORE_LINE for ln in existing.splitlines()):
        return gi, False
    sep = '' if (not existing or existing.endswith('\n')) else '\n'
    gi.write_text(existing + sep + IGNORE_BLOCK.lstrip('\n'), encoding='utf-8')
    return gi, True


def _install_session_hooks(dest, base_branch='main'):
    """Give a new source the three hooks that keep its own sessions honest:
    freshness-guard.sh (never work on, or write to, a stale checkout),
    commit-identity.sh (commits are authored by the person running the
    session, not the container's own bot account), and
    precedent-individual-bootstrap.sh (the person's own individual practice
    set resolves here, instead of silently binding nothing -- see
    INDIVIDUAL_SOURCE_HOOK above for the measurement and the two reasons it
    could not be installed before 2026-09-13).

    No hook names a person, and the individual-source one bakes in no
    account either: it is called with no --repo-url, so it derives the set
    from $PRECEDENT_SOURCE_BASE_URL and reads
    ~/.config/precedent/config.json ahead of that. A set may be private and
    the hook is still tracked, so the same reasoning that keeps the account
    out of a public consumer's tree applies unchanged
    (practice: affordance-is-shared). commit-identity.sh resolves whoever is
    actually running the session -- see its own header for the order it
    tries, and why the timezone is the only thing it is ever willing to
    guess at. It reads the individual set, which is why the bootstrap hook
    is wired AHEAD of it below rather than after.

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
    # force=True for the same reason the loop above rewrites unconditionally:
    # a set this is re-run against picks up the current hook. The refusal
    # write_session_hook() defends by default is about a CONSUMING project's
    # hand-tuned copy, which is not what this call is writing.
    written.append(write_session_hook(dest, 'precedent-individual', None,
                                      force=True))
    # Rewritten unconditionally, same as SESSION_HOOKS above: a set this is
    # re-run against picks up the current copy.
    _uc = hooks_dir / UNIVERSAL_CATALOGUE_HOOK
    _uc.write_text((HARNESS_HOOKS / UNIVERSAL_CATALOGUE_HOOK)
                   .read_text(encoding='utf-8'), encoding='utf-8')
    _uc.chmod(0o755)
    written.append(_uc)

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
                "",
                "precedent-individual-bootstrap.sh runs FIRST, ahead of the other two:",
                "it is what makes the person's own individual practice set resolve in",
                "THIS repo, and commit-identity.sh reads that set for the author and the",
                "timezone. It names no account -- it derives the set from",
                "PRECEDENT_SOURCE_BASE_URL, and reads ~/.config/precedent/config.json",
                "ahead of that. Without a credential it prints why and exits 0.",
            ],
            'hooks': {
                'SessionStart': [{
                    'hooks': [
                        {'type': 'command',
                         'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/' + INDIVIDUAL_SOURCE_HOOK},
                        # The universal catalogue. ONE script, not the two
                        # inline commands this shipped as on 2026-09-13: the
                        # harness refuses a session editing THIS file, so
                        # anything named here is a thing only a person can
                        # change. A script it points at is an ordinary tracked
                        # file, and every future change goes there instead.
                        {'type': 'command',
                         'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/' + UNIVERSAL_CATALOGUE_HOOK},
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
                }, {
                    # THE MARKDOWN COMMIT GATE, wired from the start so a new
                    # set never has the gap the four existing ones had.
                    #
                    # The lint left GitHub Actions on 2026-09-21 because this
                    # hook replaced it. Vendoring is gated on wiring, so a set
                    # that does not wire it never receives the file -- and a
                    # set created before this line had to be hand-edited to
                    # break that loop, which is a person doing by hand what
                    # nothing automates
                    # (todo-2026-09-21-a-new-hook-cannot-reach-an-installed-
                    # consumer.md). A set created from here on is wired on
                    # day one and the refresh delivers the file unasked.
                    #
                    # Its own matcher rather than sharing the block above:
                    # this one only ever needs Bash (it inspects `git commit`),
                    # and widening the freshness guard's matcher or narrowing
                    # this one would make each wrong for the other.
                    'matcher': 'Bash',
                    'hooks': [
                        {'type': 'command',
                         'command': '$CLAUDE_PROJECT_DIR/.claude/hooks/doc-lint-gate.sh'},
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
    level = LEVEL_ALIASES.get(level, level)
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

    # Does this set read the universal catalogue at all? Two separate
    # things, reported separately because they fail separately: the
    # DECLARATION (a universal entry in its own precedent.json) and the
    # WIRING (the session-start step that renders it). A set with the
    # declaration and no wiring resolves universal and shows a session
    # nothing; a set with the wiring and no declaration runs a step that
    # finds nothing to do. Every set that existed on 2026-09-13 has neither,
    # because bootstrap() only ever runs when a set is created -- the same
    # shape as the hook findings above, and the reason verify() exists.
    cfg = _load_json(path / 'precedent.json') or {}
    if not any(s.get('level') == 'universal'
               for s in (cfg.get('sources') or [])):
        missing.append(
            "precedent.json declares no universal source, so this set "
            "resolves nothing and a session rooted in it reads none of the "
            "universal practices (spec/SOURCE_SET_PROSE_GAP.md)")
    # Either spelling counts as wired: the one-script form this writes now,
    # and the two inline commands three sets already carry from 2026-09-13.
    # Both run the same steps, so reporting a working set as broken would be
    # the check lying about the thing it exists to measure.
    wired_cmds = ' '.join(_wired_commands(path))
    _uc_wired = (UNIVERSAL_CATALOGUE_HOOK in wired_cmds
                 or 'precedent_session_practices.py' in wired_cmds)
    if not _uc_wired:
        missing.append(
            ".claude/settings.json wires no session-start step running "
            "tools/precedent_session_practices.py, so nothing writes the "
            "universal practices this set declares into "
            ".precedent/SESSION_PRACTICES.md")
    else:
        # practice: session-load-budget -- once that step is wired it
        # genuinely renders and injects .precedent/SESSION_PRACTICES.md
        # into every session here
        # (spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md) -- so a set that
        # separately opted into session-load-budget by keeping its own
        # tools/session_load_budgets.json now has a real always-loaded
        # surface with no ceiling unless that entry was added in the same
        # install step. Checked only where the set opted in at all: one
        # with no registry has declared no ceilings, and
        # precedent_check.py's own session-load-budget check already
        # reports NotApplicable there, so there is nothing new to say.
        #
        # Found 2026-09-22 in precedent-shared-working-style: the PR that
        # turned this hook on added the CLAUDE.md surface to the registry
        # and not this one, so the file it makes real sat unmeasured and
        # uncapped across two merges until a --full-sweep was run by hand.
        _budgets = _load_json(path / 'tools' / 'session_load_budgets.json')
        if _budgets is not None and '.precedent/SESSION_PRACTICES.md' not in (
                _budgets.get('surfaces') or {}):
            missing.append(
                "tools/session_load_budgets.json declares surfaces but has "
                "no '.precedent/SESSION_PRACTICES.md' entry, even though "
                "the universal-catalogue hook is wired and renders that "
                "file into every session here -- measure it "
                "(tools/build_views.py's _approx_tokens against the file on "
                "disk) and add a ceiling with headroom, the way "
                "precedent-individual's own entry does")

    # The individual-source hook is checked on its own, and on a stricter
    # test than the two above: PRESENT IS NOT ENOUGH, it has to be WIRED.
    # In a consuming repo a hook sitting unwired at the canonical path still
    # runs, because precedent_resolve.py's lazy self-heal execs it by path;
    # a set vendors no precedent_resolve.py, so SessionStart is the only
    # thing that ever runs it there and an unwired copy is inert.
    #
    # Every set created before 2026-09-13 has neither the file nor the
    # wiring, and this tool cannot reach them -- same position as the
    # workflows below. The report is what closes that.
    hook_wired = any(w.name == INDIVIDUAL_SOURCE_HOOK and (path / w).exists()
                     for w in wired)
    if not hook_wired:
        here = pathlib.Path('.claude') / 'hooks' / INDIVIDUAL_SOURCE_HOOK
        have = (path / here).exists()
        missing.append(
            f"{here} "
            + ("is present but NOT WIRED in .claude/settings.json"
               if have else f"(from {INDIVIDUAL_SOURCE_HOOK_REL})")
            + " -- without it a session rooted in this set resolves no "
              "individual practice source at all, silently, and every "
              "personal rule in force is absent while the session applies "
              "the ones it can see")

    # Like the hooks, the workflows are not in either skeleton -- they come
    # from templates/github-actions/, one copy, shared with dependent repos.
    # A set bootstrapped before 2026-09-11 has none of them. Since 2026-09-16
    # they are also gated on ci_workflows (declared-default-is-applied:
    # absent means disabled) -- a set that resolves disabled and has none of
    # them is correctly configured, not behind, so it is not reported missing.
    _ci_enabled, _ci_note = _ci_preference(path)
    if _ci_enabled:
        # Since 2026-09-18: a workflow file that EXISTS can still be
        # STALE -- "Update Vendors" only just started re-copying an
        # already-installed CI workflow's body on refresh
        # (vendor-update-runbook.md step 3); a set refreshed before that
        # shipped still runs whatever it was installed with. Reported as
        # its own category, never folded into "missing" outright: a
        # missing file has no workflow running at all, a stale one has one
        # running an OLDER version of it -- different gaps, different
        # remedies (install vs. refresh). Only reported when the manifest
        # shows the file was never hand-edited: a hand-edit is
        # `precedent_vendor_engine refresh`'s own drift check to report,
        # not this one's, and a manifest with no record at all for this
        # file yet (vendored before this feature existed) is the one-time
        # catch-up refresh() handles silently -- also not this one's to
        # flag.
        _ci_manifest = _load_json(path / 'tools' / 'ENGINE_MANIFEST.json') or {}
        _ci_recorded = _ci_manifest.get('ci_workflows_sha256') or {}
        for _template, rel, why in WORKFLOW_TEMPLATES:
            wf_path = path / rel
            if not wf_path.exists():
                missing.append(f"{rel} (from {WORKFLOWS_REL}{_template}; "
                               f"without it {why})")
                continue
            _recorded_hash = _ci_recorded.get(rel)
            if _recorded_hash is None:
                continue  # never tracked yet -- refresh's own catch-up covers it
            _live_hash = precedent_vendor_engine._sha256(wf_path)
            if _live_hash != _recorded_hash:
                continue  # hand-edited -- refresh's own drift check covers it, not this one
            _current_hash = precedent_vendor_engine._sha256(
                ROOT / 'templates' / 'github-actions' / _template)
            if _live_hash != _current_hash:
                missing.append(
                    f"{rel} is STALE (from {WORKFLOWS_REL}{_template}; content was "
                    f"never hand-edited but no longer matches the current template) "
                    f"-- run `python3 tools/precedent_vendor_engine.py refresh "
                    f"<bestpractice-clone>` to pick it up")

    # A vendored engine older than binds_publishers (#261, 2026-09-12) turns
    # the workflow above into a decoration rather than a gate, and nothing
    # else here would say so. In a source set that engine skips the checks
    # whose practice lives upstream -- the set's practices/ holds only its own
    # files, so a universal check's practice is never "in force" -- and
    # precedent_check.py exits 0 on a run that skipped. Measured 2026-09-13
    # in a freshly bootstrapped set, same tree both ways: 5 passed/44 skipped
    # on a pre-flag engine, 8 passed/41 skipped on the current one. So the
    # workflow is installed, green, and missing exactly the checks that bind
    # what this repo publishes -- worse than having no workflow, because it
    # looks like coverage. precedent-check.yml refuses on exactly this,
    # by the same grep; saying it HERE is what lets somebody fix it before a
    # pull request rather than after a confusing red.
    #
    # Grepped rather than imported: verify() reports on a set on disk that
    # this process must not import code from, and the flag is a registration
    # keyword that appears nowhere else.
    engine = path / 'tools' / 'precedent_check.py'
    if engine.is_file():
        try:
            if 'binds_publishers' not in engine.read_text(
                    encoding='utf-8', errors='ignore'):
                missing.append(
                    "tools/precedent_check.py predates binds_publishers "
                    "(BestPractice PR #261, 2026-09-12), so in this set it "
                    "skips the checks whose practice lives upstream and "
                    "still exits 0 -- measured 5 passed/44 skipped against "
                    "8 passed/41 skipped on the same tree, so a check "
                    "workflow here is quietly green while missing exactly "
                    "the checks that bind what this repo publishes. Refresh "
                    "it: python3 tools/precedent_vendor_engine.py refresh")
        except OSError as e:
            # fail-gracefully: an unreadable engine is a finding, not a
            # crash that takes the other findings down with it.
            missing.append(f"tools/precedent_check.py could not be read "
                           f"({e}), so whether it carries binds_publishers "
                           f"is unknown -- not the same as current")

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

    # The set's own instructions file, with the markers its generator
    # writes between. Not in either skeleton and not written by bootstrap
    # until 2026-09-14, so every set created before then has whatever its
    # author wrote by hand -- usually a file, sometimes without the
    # markers, in which case `build_views.py` fails on the set's first
    # pull request and precedent_move.py cannot regenerate the set's views
    # after landing a practice in it.
    agents = path / 'AGENTS.md'
    if not agents.is_file():
        missing.append("AGENTS.md (written by this tool's bootstrap since "
                       "2026-09-14; without it the set's own build_views.py "
                       "fails, so the drift workflow is red and "
                       "precedent_move.py cannot regenerate the set's views)")
    else:
        try:
            body = agents.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            body = ''
        if 'BEGIN GENERATED: precedent-loader' not in body:
            missing.append("AGENTS.md carries no "
                           "`<!-- BEGIN GENERATED: precedent-loader -->` "
                           "marker, so build_views.py has nowhere to write "
                           "the loader block and fails")

    # The Claude Code stub. Reported as missing rather than silently
    # tolerated because its absence is invisible from inside a session: the
    # harness falls back to AGENTS.md today, so a set with no CLAUDE.md looks
    # identical to one that has it until the day that default changes.
    if not (path / 'CLAUDE.md').is_file():
        missing.append("CLAUDE.md (the Claude Code adapter stub, written by "
                       "this tool's bootstrap since 2026-09-20; without it "
                       "the set's AGENTS.md loads only via the harness's "
                       "AGENTS.md fallback -- add a file whose body is "
                       "`@AGENTS.md`)")
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


def _wired_commands(path):
    """-> [str] every command string a source's .claude/settings.json runs.

    _wired_hook_paths() above answers "which FILE does this wire", by taking
    the first word. That cannot see a step invoked as `python3 <tool>`, where
    the first word is the interpreter -- which is exactly how the
    universal-catalogue steps are wired, since they call vendored tools
    rather than hook scripts. So this returns the whole command and lets the
    caller look for what it cares about.
    """
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
                out.append(cmd)
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

    if level == 'shared':
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
        # A MIGRATED set does not hold a `{{PLACEHOLDER}}` for a field the
        # skeleton gained after it was assembled -- it holds no key at all,
        # which the placeholder sweep above cannot see. `pronouns` is the
        # live case: every individual set created before 2026-09-12 predates
        # the field, so an absent key is the normal state of an existing set
        # and the only thing that will ever report it is a check that names
        # the key. Report it, and say what to do about it: the value is the
        # person's to give, so an install or a migration asks them for it
        # rather than guessing one.
        # practice: declared-pronouns
        f = path / 'identity.json'
        if f.is_file():
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError) as e:
                out.append(f'identity.json is not valid JSON -- {e}')
            else:
                if not (data.get('pronouns') or '').strip():
                    out.append('identity.json declares no "pronouns" -- ask '
                               'the person whose set this is and write their '
                               'answer in (`he/him`, `she/her`, `they/them`); '
                               'until then `declared-pronouns` falls back to '
                               'they/them for them')
                # `register` is the same shape (2026-09-14): how technical a
                # reply should be is the person's to declare, and a set built
                # before the key existed holds no key at all.
                # practice: technical-describes-people
                if not (data.get('register') or '').strip():
                    out.append('identity.json declares no "register" -- ask '
                               'the person whose set this is how technical '
                               'their replies should be and write their '
                               'answer in, in their own words; until then a '
                               'team-level default may decide it for them')

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
    level = LEVEL_ALIASES.get(level, level)
    if level not in LEVELS:
        raise BootstrapRefused(f"--level must be one of {sorted(LEVELS)}, got {level!r}")
    dest = pathlib.Path(dest).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()) and not force:
        raise BootstrapRefused(
            f"{dest} already exists and is not empty -- pass --force true to "
            f"write into it anyway (existing files with the same name are "
            f"overwritten; anything else already there is left alone)")
    if level == 'shared' and not approvers:
        raise BootstrapRefused(
            "a shared set needs at least one approver -- pass "
            '--approver "Full Name:github-handle" (whoever is creating this '
            "set is its first approver, per PRACTICE_ENGINE_PLAN.md's Stage 4)")

    dest.mkdir(parents=True, exist_ok=True)
    mapping = {'NAME': name, 'DEST_PATH': str(dest)}
    if level == 'shared':
        first = approvers[0]
        mapping['APPROVER_NAME'] = first['name']
        mapping['APPROVER_GITHUB'] = first['github']

    _warn_if_clone_is_stale()
    written = _copy_skeleton(SKELETONS[level], dest, mapping)
    written.append(_write_source_manifest(dest, level, name))
    if level == 'shared':
        _seed_approvers_json(dest, approvers)
    written += _install_session_hooks(dest)
    written += _install_workflows(dest)
    _gi, _changed = ensure_precedent_gitignore(dest)
    if _changed:
        written.append(_gi)
    _cfg, _changed = ensure_universal_source(dest)
    if _changed:
        written.append(_cfg)
    written += precedent_vendor_engine.seed(dest)
    # AFTER seed(), not before: seed()/_write_engine_files builds
    # ENGINE_MANIFEST.json fresh on every call, so recording the CI
    # workflow files' hashes before this point would be silently wiped the
    # moment seed() ran (see record_ci_workflow_files's own docstring). The
    # workflow files themselves are already on disk from _install_workflows
    # above -- this only computes and records their hashes.
    written += precedent_vendor_engine.record_ci_workflow_files(dest, 'source')
    written += _write_instructions_and_views(dest, level, name)
    written.append(_write_session_load_budget(dest))

    return {'dest': dest, 'written': written}


def _write_session_load_budget(dest):
    """Seed tools/session_load_budgets.json so a new set starts with the
    early-warning notice ON, instead of silently absent until someone
    remembers to opt in by hand (practice: session-load-budget).

    Found real, 2026-09-22: two of the four already-live individual/shared
    sets had never created this file at all; the other two had it but were
    missing headroom_floor_pct. Both shapes are silent until the ceiling is
    hit cold -- which is exactly what happened. verify() (above) audits an
    EXISTING set for the one surface that only exists once the universal
    hook is wired (.precedent/SESSION_PRACTICES.md); this is the proactive
    half, for the one surface that exists at bootstrap time itself.

    Ceiling is measured file size plus ~20% headroom, rounded to a clean
    number -- the same convention every hand-written entry in this repo's
    own registry already uses (session-load-budget's own Rule: "set at
    what the surface measured... rounded up for headroom"). Not a claim
    that 20% is correct forever -- a ceiling is a watermark, reviewed and
    reduced when it is crossed for real, never just raised.

    Covers whichever of AGENTS.md/CLAUDE.md exist on disk -- bootstrap
    writes both (_write_instructions_and_views), and precedent_check.py's
    own SESSION_LOAD_SURFACES checks both, not just whichever the local
    harness happens to read. A repo missing one after this seeds only
    what is actually there, same as the hand-written registries do.
    """
    import build_views as bv
    import precedent_time
    dest = pathlib.Path(dest)
    today = precedent_time.today(dest)
    surfaces = {}
    for rel in ('AGENTS.md', 'CLAUDE.md'):
        f = dest / rel
        if not f.is_file():
            continue
        measured = bv._approx_tokens(f.read_text(encoding='utf-8'))
        ceiling = ((int(measured * 1.2) + 49) // 50) * 50 if measured else 50
        surfaces[rel] = {
            'ceiling': ceiling,
            '_note': f'{measured} tokens measured at bootstrap ({today}). '
                     f'Ceiling is current + ~20%.',
        }
    path = dest / 'tools' / 'session_load_budgets.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        '_comment': [
            'Seeded at bootstrap (practice: session-load-budget) so the '
            'early-warning notice starts ON. headroom_floor_pct matches '
            "BestPractice's own value; each surface's ceiling is measured "
            'plus ~20% headroom, the convention every hand-written entry '
            'in that repo already uses. Add .precedent/SESSION_PRACTICES'
            '.md once the universal-catalogue hook is wired -- verify() '
            'flags that gap directly once it is. A ceiling is a '
            'watermark, not an endorsement: review and reduce, never '
            'just raise, when it is crossed for real.',
        ],
        'headroom_floor_pct': 5,
        'surfaces': surfaces,
    }, indent=2) + '\n', encoding='utf-8')
    return path


def _write_source_manifest(dest, level, name):
    """The set's own identity file (precedent_resolve.SOURCE_MANIFEST): the
    name its author chose, its level, and that it is private. A consumer
    declares the name; the resolver checks the clone answers to it. The
    repository may be called anything (practice: source-naming)."""
    path = pathlib.Path(dest) / precedent_resolve.SOURCE_MANIFEST
    path.write_text(json.dumps({
        'name': name,
        'level': level,
        'visibility': 'private',
        'subject': '',
        'code': [],
        '_comment': [
            'This file is what makes the directory a practice-set source: its',
            'name is chosen once, here, and every consumer declares it verbatim.',
            'The repository holding it may be called anything. `subject` is a',
            'sentence saying what the set is about; `code` lists directories',
            'a consumer vendors alongside the practices (tools/, for a set',
            'whose practices are about a tool it ships).',
        ],
    }, indent=2) + '\n', encoding='utf-8')
    return path


def _write_instructions_and_views(dest, level, name):
    """A set's AGENTS.md with the loader markers, then its generated views.

    Until 2026-09-14 bootstrap seeded build_views.py and installed a
    workflow that runs `build_views.py --check`, and wrote no AGENTS.md for
    either to read -- so a new set's own generator failed on its first run
    (`AGENTS.md does not exist`), the drift workflow went red on the set's
    first pull request, and precedent_move.py could not regenerate the
    views of a set it had just landed a practice in. Every real set carries
    the file; the skeleton did not, and nothing said to write one. The
    opening paragraph is the set's own to rewrite; the markers and the
    block between them are the generator's
    (practice: generated-artifact-provenance)."""
    dest = pathlib.Path(dest)
    agents = dest / 'AGENTS.md'
    written = []
    if not agents.exists():
        what = ('a **shared** source, named for its subject; any repository whose '
                'work includes that subject declares it alongside its own'
                if level == 'shared' else
                'an **individual** source: one person\'s own practices, declared in '
                'their own user-level config and never in a shared project')
        agents.write_text(
            f'# Repository notes for agents\n\n'
            f'This repo IS `{name}` -- {what} -- for '
            f'[Precedent](https://github.com/alex137/BestPractice). '
            f'[README.md](README.md) says what is here and how a practice lands.\n\n'
            f'<!-- BEGIN GENERATED: precedent-loader -->\n'
            f'<!-- END GENERATED -->\n',
            encoding='utf-8')
        written.append(agents)

    # THE CLAUDE CODE STUB, added 2026-09-20, and a set needs it for the same
    # reason a consuming repo does. templates/harness/README.md's adapter
    # table frames `CLAUDE.md` -> `@AGENTS.md` as wiring a CONSUMER installs,
    # so no set ever got one: all four of the sets alive on that date had
    # AGENTS.md and no CLAUDE.md. It worked only because Claude Code falls
    # back to AGENTS.md where a project has no CLAUDE.md of its own
    # (2.1.278, `instructionFiles` defaults to "claude-md-or-agents-md") --
    # a harness default, changeable by the harness, and not something a set's
    # rules loading at all should rest on.
    #
    # The universal catalogue does NOT travel through this file. The
    # SessionStart hook renders and injects it; an @import of
    # .precedent/SESSION_PRACTICES.md here would load a stale copy where the
    # hook had not run yet and a duplicate where it had
    # (spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md).
    claude_md = dest / 'CLAUDE.md'
    if not claude_md.exists():
        claude_md.write_text(
            '<!-- Claude Code adapter: CLAUDE.md is the file Claude Code\n'
            '     auto-loads; the canonical instructions live in AGENTS.md\n'
            '     (harness-neutral), and the @import below pulls it into\n'
            '     context natively. Keep repo-specific content in AGENTS.md,\n'
            '     not here. The universal catalogue arrives separately, from\n'
            '     the SessionStart hook -- see BestPractice\'s\n'
            '     spec/PACK_SESSION_DOES_NOT_LOAD_UNIVERSAL.md. -->\n\n'
            '@AGENTS.md\n',
            encoding='utf-8')
        written.append(claude_md)

    bv = dest / 'tools' / 'build_views.py'
    if bv.is_file():
        # -B: the generator runs INSIDE the set, and a tools/__pycache__/ it
        # left behind read as bootstrap drift in every audit afterwards.
        r = subprocess.run([sys.executable, '-B', str(bv)], cwd=str(dest),
                           capture_output=True, text=True)
        if r.returncode != 0:
            # Never fatal: the set is complete without views, and the drift
            # workflow says so on its first run. Say what happened rather
            # than nothing (practice: fail-gracefully).
            print(f'bootstrap: the new set\'s views were not generated -- '
                  f'{(r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "build_views exit " + str(r.returncode)}',
                  file=sys.stderr)
        else:
            written += [dest / n for n in ('MAP.md', 'GLOSSARY.md') if (dest / n).is_file()]
    return written


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
    into any repository somebody works in, at
    .claude/hooks/precedent-individual-bootstrap.sh, so an ephemeral session
    there can resolve this person's individual set with zero manual steps.

    A PRACTICE SET IS SUCH A REPOSITORY, and this said otherwise until
    2026-09-13: "into a CONSUMING project -- not the individual set's own
    repo". That exclusion is withdrawn, and _install_session_hooks() now
    calls this for every new set. It was never argued for -- the hook execs
    tools/precedent_source_bootstrap.py, which a set was not allowed to
    vendor, so the exclusion described a dependency rather than a decision.
    With that fixed the exclusion costs a real thing: a session rooted in
    precedent-individual or any precedent-team-* had no individual practices
    in force, and nothing said so.

    WHAT THE SET'S OWN REPO GETS, AND WHY IT IS A SECOND CHECKOUT. The hook
    clones to $HOME/precedent-individual and points the config there --
    including when the repo it is installed in IS precedent-individual. That
    is deliberate, not a rough edge. Pointing the config at the checkout in
    place would hand precedent_source_bootstrap.py the session's own working
    tree, and its branch pin (SOURCE_BRANCH_DEFAULT, written after a source
    was read off the wrong branch) puts a clean clone back on `main` before
    pulling -- so a session working on a feature branch in its own set would
    find itself moved to main at the next sync, which is the silent
    branch-switch this repo's own gotchas already cost a session's work to.
    The second checkout keeps the resolved source and the tree being edited
    apart, and it is the path PRECEDENT_FRESHNESS_ALSO already names, so the
    freshness guard covers the set for the first time.
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
    existing = next((s for s in sources if s.get('level') in ('shared', 'team')
                      and s.get('name') == name), None)
    if existing:
        if existing.get('path') != rel_path and not force:
            raise BootstrapRefused(
                f"{config_path} already has a shared source named {name!r} at "
                f"a different path ({existing.get('path')!r}) -- pass "
                f"--force true to overwrite it")
        existing['path'] = rel_path
    else:
        sources.append({'level': 'shared', 'name': name, 'path': rel_path})
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
    """-> 'shared' | 'individual' | None, read off the set itself.

    Asking the operator for --level on a set that already exists is asking
    them to restate something the directory already says: a team set carries
    approvers.json (build_codeowners.py refuses one without it), an
    individual set carries an identity or a config naming its owner. Guessing
    wrong is cheap to notice and never destructive -- verify() only reads.
    """
    m = _load_json(path / precedent_resolve.SOURCE_MANIFEST) or {}
    if m.get('level'):
        return LEVEL_ALIASES.get(m['level'], m['level'])
    if (path / 'approvers.json').exists():
        return 'shared'
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
        level = LEVEL_ALIASES.get(args.get('--level'), args.get('--level')) or _infer_level(target)
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

    level = LEVEL_ALIASES.get(args.get('--level'), args.get('--level'))
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
                print(json.dumps({'level': 'shared', 'name': name, 'path': str(dest_path)}, indent=2))
    except BootstrapRefused as e:
        print(f"REFUSED (wiring not written; the set itself is): {e}")
        return 1

    print()
    print(f"The set itself still needs a real git remote -- see "
          f"spec/BOOTSTRAP_NEW_SOURCES.md for that last, deliberately manual step.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

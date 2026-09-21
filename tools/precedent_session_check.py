#!/usr/bin/env python3
"""Did this session's SessionStart hooks actually run? -- and repair it.

practice: session-bootstrap, fail-gracefully

THE INCIDENT, 2026-09-08. A session opened with four Precedent repositories
side by side under a parent directory -- this project's own required layout,
since a team source resolves as a SIBLING CLONE -- and the harness rooted the
session at that PARENT. `$CLAUDE_PROJECT_DIR` was therefore `/home/user`,
which has no `.claude/` of its own, so every hook in every one of the four
repositories' `settings.json` pointed at a path that does not exist. None of
them ran. Silently: a hook that cannot be found is not an error anybody sees.

What was missing, all at once, for a session doing a full review before the
work was shown to its reviewer: the commit identity (so commits would have
been authored by the container's bot and refused by this repo's own check),
the global commit backstop, the freshness guard, the package installs, the
path-trigger channel, the Stop-time git check, and
`.precedent/SESSION_PRACTICES.md` -- which is the ONLY route by which the
team and individual practices in force reach a session at all. AGENTS.md's
Standing Instruction tells every session to read that file; there was no file.

WHY THE EXISTING GOTCHA DID NOT COVER IT. AGENTS.md already records that a
repo ATTACHED mid-session never runs its own SessionStart hook. This is the
sibling failure and reads as its opposite: the repository is the one the
session is working in, its hooks are correctly wired, committed and
executable, and they still never fire -- because the session's root is one
directory ABOVE the repository. The multi-repo layout that causes it is not
exotic, it is what Precedent's own source resolution requires.

WHY THIS IS A TOOL AND NOT A HOOK. It cannot be a hook. The failure IS that
hooks do not run, so anything that waits to be triggered is the one thing
guaranteed not to fire (the same shape AGENTS.md records for a freshness
guard shipped inside the checkout it guards). It is reachable three ways
instead: AGENTS.md names it in the first-tool-call banner a session reads
before anything else, `--apply` makes the repair one command rather than
three remembered ones, and `remind()` below is printed by every
tools/precedent_gate.py moment.

THE THIRD ROUTE EXISTS BECAUSE THE FIRST TWO ARE SKIPPABLE, 2026-09-14. A
session read that banner, did not run this tool, and worked for hours with
four guarantees down -- no session-practices file, no commit backstop, two
uninstalled packages -- noticing only when the packages surfaced as three
unrelated-looking verify_harness failures (record/GOTCHAS.md#g1). Guidance a
session can skip is not a mechanism; a gate it runs at a named moment is.

Exit 0 when every guarantee holds, 1 otherwise, so it can gate a run.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOT_EMAILS = {'noreply@anthropic.com'}


def _run(*args, cwd=None):
    p = subprocess.run(args, capture_output=True, text=True,
                       cwd=str(cwd or ROOT))
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def _git(*args):
    return _run('git', '-C', str(ROOT), *args)


def _declared_branch():
    try:
        cfg = json.loads((ROOT / 'precedent.json').read_text())
        return cfg.get('base_branch')
    except Exception:
        return None


def _identity_is_declared():
    """Whether a PERSON declared who they are, as commit-identity.sh means it.

    Mirrors that hook's `declared` flag: an explicit PRECEDENT_COMMIT_EMAIL,
    this repo's own identity.json (it IS somebody's individual source), or the
    individual practice source's identity.json. An identity merely INFERRED
    from an existing git config, the session account or the authenticated
    GitHub account is NOT a declaration and does not install the global
    backstop -- which is the whole reason the backstop row needs to tell the
    two apart before naming a remedy.
    """
    if os.environ.get('PRECEDENT_COMMIT_EMAIL'):
        return True
    if (ROOT / 'identity.json').exists():
        return True
    cfg = pathlib.Path(os.environ.get('PRECEDENT_USER_CONFIG')
                       or '~/.config/precedent/config.json').expanduser()
    try:
        path = json.loads(cfg.read_text(encoding='utf-8'))['individual']['path']
    except Exception:
        return False
    return (pathlib.Path(path).expanduser() / 'identity.json').exists()


def checks(offline=False):
    """-> [(name, ok, detail)]. Each is a guarantee a SessionStart hook is
    supposed to have established, tested by its EFFECT rather than by
    whether some hook reported success -- a hook that never ran reports
    nothing at all, which is exactly the state being detected
    (practice: verify-postcondition).

    `offline=True` drops the one row that talks to the network -- the
    freshness comparison, which fetches -- so a caller on a hot path can
    afford to ask. Everything else is local file and git-config reads.
    A dropped row is simply absent from the list, never reported as OK:
    a guarantee nobody measured is not a guarantee that holds."""
    out = []

    # 1. The project dir the harness actually handed the hooks.
    proj = os.environ.get('CLAUDE_PROJECT_DIR')
    if proj is None:
        detail = ('CLAUDE_PROJECT_DIR is not set in this shell, so this '
                  'cannot be read directly -- the checks below test the '
                  'effects instead, which is the reliable signal either way')
        out.append(('the harness rooted the session at this repository',
                    None, detail))
    else:
        ok = pathlib.Path(proj).resolve() == ROOT
        detail = '' if ok else (
            f'CLAUDE_PROJECT_DIR={proj!r}, but this repository is {ROOT}. '
            f'Every hook in .claude/settings.json is written as '
            f'$CLAUDE_PROJECT_DIR/.claude/hooks/... so NONE of them resolve, '
            f'and none of them ran. This is the incident in the docstring')
        out.append(('the harness rooted the session at this repository',
                    ok, detail))

    # 2. The practices in force from private sources reached the session.
    sp = ROOT / '.precedent' / 'SESSION_PRACTICES.md'
    ok = sp.is_file()
    out.append(('the team and individual practices in force were written to '
                '.precedent/SESSION_PRACTICES.md', ok,
                '' if ok else
                'the file does not exist, so every team and individual '
                'practice binding work here is SILENTLY absent -- AGENTS.md '
                "tells this session to read it and there is nothing to read. "
                'Regenerate: python3 tools/precedent_session_practices.py'))

    # 2b. ...and if they did not, whether a credential could have helped.
    # The row above says the FILE is missing; this one says whether the
    # sources themselves resolved, which is the thing that actually binds
    # work here. Both matter: the file can exist and honestly report that
    # every private source was unreachable, which is the state a whole
    # working day was once lost to (AGENTS.md's "no individual source
    # resolved" gotcha).
    try:
        import precedent_source_credentials as psc
        verdict, message = psc.assess(ROOT)
        # 'unconfigured' PASSES the row and still says its piece: no
        # credential is missing, so failing would be false -- but "your
        # user config is the reason, and no token will fix it" is exactly
        # the sentence a reader of this row needs, and a silent green row
        # is where it would otherwise go (practice: fail-gracefully).
        out.append(('the private practice sources resolved, or a credential '
                    'is set that could reach them', verdict != 'missing',
                    message if verdict in ('missing', 'unconfigured') else ''))
    except ImportError:
        out.append(('the private practice sources resolved, or a credential '
                    'is set that could reach them', None,
                    'tools/precedent_source_credentials.py is not importable '
                    'from here, so this could not be evaluated'))

    # 3. Commit identity is a person, not the container's bot.
    _, email, _ = _git('config', 'user.email')
    ok = bool(email) and email not in BOT_EMAILS
    out.append(('commits from this checkout are authored by a person', ok,
                '' if ok else
                f'user.email is {email!r}, the container\'s own agent '
                f'account. Commits made now are wrong-author commits, and '
                f'this repo\'s own check refuses them'))

    # 3b. The same question for every PRACTICE SOURCE on this disk, which is
    # a different question from row 3 and was answered wrongly for months.
    #
    # Row 3 asks about THIS checkout. The session-start hook's identity block
    # applies commit-identity.sh to a LIST of repositories, and until
    # 2026-09-14 that list was the primary repo plus its siblings -- which
    # silently excluded an individual set cloned somewhere else, i.e. the one
    # repository the block reads the identity FROM (record/GOTCHAS.md#g40).
    # Nothing reported it, because nothing had ever asked the question of any
    # repo but this one, and a normal session never commits to a source set.
    #
    # Deliberately reads `git config user.email` rather than
    # `--local user.email`: an unset local value is not a clean state here, it
    # is the state that falls through to the container's global bot identity,
    # which is exactly what a commit would then be authored as.
    offenders = []
    for _written, _base in _attachable_sources():
        _path = pathlib.Path(_expand_source_path(_written))
        if not (_path / '.git').exists():
            continue
        _code, _email, _ = _run('git', '-C', str(_path), 'config',
                                'user.email')
        if _code == 0 and _email in BOT_EMAILS:
            offenders.append(f'{_written} ({_email})')
    out.append(('every practice source on this disk commits as a person too',
                not offenders,
                '' if not offenders else
                ', '.join(offenders) + ' -- a commit made in that source would '
                'be a wrong-author commit, and the global backstop will refuse '
                'it. The session-start identity block is meant to have covered '
                'it; a source outside the primary repo\'s own parent directory '
                'is how it gets missed (record/GOTCHAS.md#g40)'))

    # 4. The global backstop reaches repositories attached later.
    #
    # WHY THIS ROW NAMES ITS OWN REMEDY INSTEAD OF LEANING ON --apply.
    # commit-identity.sh installs the backstop only when somebody DECLARED an
    # identity (`_install_global_backstop`'s first line is
    # `[ "$declared" -eq 1 ] || return 0`). Where the hook merely INFERRED one
    # -- from an existing git config, the session account, the authenticated
    # GitHub account -- it deliberately installs nothing. So on a session with
    # no reachable individual source, which is most of them while that source
    # is a private repo, `--apply` re-runs the hook, the hook declines again,
    # and the row stays FAIL forever.
    #
    # 2026-09-09, the incident: a session was told by another session that
    # `--apply` repairs this. It ran it, watched the row stay red, and spent
    # the time working out that the summary's own `Repair:` line was naming a
    # command that cannot fix this particular guarantee. A remedy that does
    # not work is worse than none, because it is tried first and believed.
    _, hp, _ = _run('git', 'config', '--global', 'core.hooksPath')
    ok = bool(hp) and pathlib.Path(hp).is_dir()
    detail = ''
    if not ok:
        detail = ('core.hooksPath is unset, so a repository attached LATER in '
                  'this session inherits the container identity with nothing '
                  'to refuse it')
        if not _identity_is_declared():
            detail += (
                '. --apply CANNOT fix this: the backstop installs only for a '
                'DECLARED identity, and nothing here declares one (no '
                'PRECEDENT_COMMIT_EMAIL, no identity.json in this repo, no '
                'individual practice source carrying one). Declare one and '
                're-run the hook:\n'
                '       PRECEDENT_COMMIT_NAME="<you>" '
                'PRECEDENT_COMMIT_EMAIL="<you@example.com>" bash '
                '.claude/hooks/commit-identity.sh\n'
                '       -- or set PRECEDENT_GIT_TOKEN so the individual '
                'source resolves and declares it for you '
                '(tools/precedent_source_credentials.py)')
    out.append(('the global commit backstop is installed', ok, detail))

    # 5. The packages this repo's own gates import.
    missing = []
    for mod in ('cmarkgfm', 'markdown'):
        if subprocess.run([sys.executable, '-c', f'import {mod}'],
                          capture_output=True).returncode != 0:
            missing.append(mod)
    out.append(('the packages the gates import are installed', not missing,
                '' if not missing else
                f'missing {", ".join(missing)} -- doc_lint\'s strikethrough '
                f'check and tools/doc_html.py degrade rather than fail, so '
                f'they pass while checking less than they claim. '
                f'verify_harness does NOT degrade: it fails the checks that '
                f'need them, naming what each was testing and never what is '
                f'absent, which cost two full re-runs to attribute on '
                f'2026-09-14. Remedy: pip install {" ".join(missing)} -- '
                f'--apply re-runs the hook that installs them, which is the '
                f'same fix only when the hook can run at all'))

    # 6. A single-branch clone's refspec, without which every branch reads
    #    as unpushed forever (AGENTS.md's add_repo entry).
    _, spec, _ = _git('config', '--get-all', 'remote.origin.fetch')
    ok = 'refs/heads/*' in spec
    out.append(('this clone can see every branch on origin', ok,
                '' if ok else
                f'remote.origin.fetch is {spec!r} -- a single-branch clone, '
                f'so branch scans see two or three refs on a repo that has '
                f'forty and report the rest as absent'))

    # 7. The branch this session started on is still the one checked out.
    #
    #    THE INCIDENT, 2026-09-08. Mid-session, this checkout was moved off
    #    its working branch onto `precedent-beta-v01` and fast-forwarded --
    #    `checkout: moving from claude/... to precedent-beta-v01` followed by
    #    `pull origin precedent-beta-v01: Fast-forward`, three minutes after a
    #    commit. The commit survived on the abandoned branch; the next twenty
    #    minutes of edits were made on the wrong one, and the loss showed up
    #    only as a check that had silently stopped existing.
    #
    #    THE CAUSE IS NOT KNOWN, and this says so rather than implying it is
    #    fixed. `precedent_vendor_engine.py seed`, `precedent_refresh_sources
    #    --apply` and `checkin.py fresh` were each replayed against a
    #    throwaway clone on a feature branch and NONE of them moved HEAD, so
    #    the three obvious suspects are ruled out. Whatever did it is outside
    #    this repo's own tools. Detection is therefore the whole remedy
    #    available: a stamp written on the first run of a session, compared on
    #    every later one.
    stamp = ROOT / '.git' / 'precedent-session-branch'
    rc, cur, _ = _git('rev-parse', '--abbrev-ref', 'HEAD')
    if rc == 0 and cur:
        if stamp.is_file():
            started = stamp.read_text().strip()
            ok = (started == cur)
            out.append(('this session is still on the branch it started on',
                        ok,
                        '' if ok else
                        f'started on {started!r}, now on {cur!r}. Work '
                        f'committed before the move is on {started!r} and is '
                        f'NOT lost -- `git checkout {started}` and check '
                        f'`git reflog` for anything after it. Work done SINCE '
                        f'the move is on the wrong branch'))
        else:
            try:
                stamp.write_text(cur + '\n')
            except OSError:
                pass
            out.append(('this session is still on the branch it started on',
                        None, f'first run this session -- recorded {cur!r} as '
                              f'the baseline to compare against later'))

    # 8. Freshness. Reported, never repaired here: discarding work is worse
    #    than a stale tree, so this only ever tells (practice: fail-gracefully).
    #    The only row that fetches, so the only one `offline` drops.
    branch = _declared_branch()
    rc, cur, _ = _git('rev-parse', '--abbrev-ref', 'HEAD')
    if branch and rc == 0 and not offline:
        _git('fetch', '--quiet', 'origin', branch)
        rc2, behind, _ = _git('rev-list', '--count', f'HEAD..origin/{branch}')
        if rc2 == 0 and behind.isdigit():
            ok = int(behind) == 0
            out.append((f'this checkout is not behind origin/{branch}', ok,
                        '' if ok else
                        f'{behind} commit(s) behind on branch {cur!r}. Work '
                        f'that landed reads as missing and fixed bugs read '
                        f'as open'))
        else:
            out.append((f'this checkout is not behind origin/{branch}', None,
                        'could not compare -- origin/'
                        f'{branch} did not resolve'))

    # 8. The also-list actually names repositories that are there.
    #
    # PRECEDENT_FRESHNESS_ALSO is the one route by which an ATTACHED
    # repository gets freshness-checked at all, since its own hooks never
    # fire. An entry naming a path that is not there is skipped with a note
    # and never blocked on -- deliberately, because a config typo must not
    # wedge a session -- so the failure mode is a variable that looks set,
    # reads as coverage, and covers nothing. Measured 2026-09-11: this
    # project's own environment named /home/user/precedent-individual while
    # the clone was at /root/precedent-individual, and had been skipping it
    # every session since the variable was first set. The guard expands
    # $HOME now, which makes one value correct on every container; this row
    # is what says so out loud when it still is not
    # (practice: checkable-gets-checked).
    raw = os.environ.get('PRECEDENT_FRESHNESS_ALSO')
    name = 'PRECEDENT_FRESHNESS_ALSO names repositories that are there'
    want = _attachable_sources()
    # COMPUTED FOR THIS DISK, and that sentence is load-bearing.
    #
    # 2026-09-21: a known-good value was passed from one container to
    # another and was wrong in the second one. Both had a duplicated
    # source; they duplicated DIFFERENT ones. In the first, `~` held the
    # only copy of the individual set and the stale copies of the shared
    # sets; in the second, `~` held the STALE individual set and the shared
    # sets were single. So a line that correctly names `~/precedent-
    # individual` on one machine names the copy holding no work on the
    # other -- silently, because an also-list entry that resolves to a real
    # git repository is never questioned again.
    #
    # The value below is read off the directories actually present here,
    # which is the only way it can be right; the warning is what stops it
    # being copied somewhere it is not.
    suggestion = ('Set it to (computed from the clones on THIS disk -- never '
                  'paste a value from another container, even a known-good '
                  'one, because which copy of a source is the live one '
                  'differs per machine): PRECEDENT_FRESHNESS_ALSO='
                  + ';'.join(f'{path}={base}' for path, base in want)) if want else ''
    if raw is None:
        out.append((name, None,
                    'not set, so every repository this session merely has '
                    'ATTACHED goes unchecked -- their own hooks never fire. '
                    'That is a real gap, not a clean result. '
                    + suggestion))
    else:
        bad = []
        for entry in (e.strip() for e in raw.split(';')):
            if not entry:
                continue
            if '=' not in entry:
                bad.append(f'{entry!r} has no =<base branch>')
                continue
            written = entry.split('=', 1)[0].strip()
            resolved = _expand_source_path(written)
            if not (pathlib.Path(resolved) / '.git').exists():
                shown = (f'{written!r}' if resolved == written
                         else f'{written!r} (-> {resolved!r})')
                bad.append(f'{shown} is not a git repository')
        ok = not bad
        out.append((name, ok, '' if ok else
                    '; '.join(bad) + '. Each of these is SKIPPED, silently by '
                    'design -- the variable reads as coverage and covers '
                    'nothing. ' + suggestion))

    # 9. One source, one clone.
    #
    # Two clones of the SAME practice source on one disk is the quietest
    # failure in this file. Everything keeps working: the resolver picks
    # one, the freshness guard checks whichever the also-list names, a
    # session edits whichever it happened to cd into, and nothing anywhere
    # says the other exists. Then they diverge, and a practice somebody
    # wrote this morning is simply not in force, with no error to read.
    #
    # Measured 2026-09-21 on this project's own container: three shared
    # sets were cloned twice, once under $HOME and once beside this repo,
    # and one of the three (`precedent-shared-writing`) had ALREADY
    # diverged between its two copies. The also-list suggestion above was
    # dutifully naming both, which is honest and is also the tell -- a
    # suggestion listing seven entries for four sources is reporting a
    # duplicate nobody had noticed.
    #
    # Reports and never repairs: which copy is canonical is a judgment
    # about which one holds work (practice: fail-gracefully). Deleting the
    # wrong one loses commits.
    #
    # THE REMEDY THIS ROW USED TO GIVE WAS WRONG, and a session proved it by
    # experiment the same day. It said to remove the copy that does not hold
    # the work. That cannot hold: the source self-heal re-clones whatever
    # path the user-level config names, so the directory reappeared within
    # the minute, twice. The directory was never the cause --
    # ~/.config/precedent/config.json's individual.path pointed at one copy
    # while the working tree was the other. Repointing that one field is
    # what closed it. (The session that found it named leak_gate.py as the
    # re-cloner; leak_gate.py runs one bounded `git pull --ff-only` and
    # clones nothing, so the re-clone is the resolve-time self-heal running
    # underneath it -- worth stating, because the next person will go
    # looking in leak_gate.py for a clone call that is not there.)
    name = 'each practice source is cloned exactly once on this disk'
    by_name = {}
    for shown, _base in _attachable_sources():
        by_name.setdefault(pathlib.Path(shown).name, []).append(shown)
    dupes = {n: paths for n, paths in by_name.items() if len(paths) > 1}
    if not dupes:
        out.append((name, True, ''))
    else:
        detail = []
        for n, paths in sorted(dupes.items()):
            heads = []
            for shown in paths:
                real = _expand_source_path(shown)
                code, head = _git_head(real)
                heads.append(f'{shown} @ {head or "unreadable"}')
            agree = len({h.split(" @ ")[1] for h in heads}) == 1
            detail.append(f'{n}: ' + ', '.join(heads)
                          + ('' if agree else
                             ' -- THESE HAVE DIVERGED; work is in one copy '
                             'and not the other'))
        out.append((name, False, '; '.join(detail) + '. Nothing reports '
                    'which copy the loader read, so a practice written in '
                    'one may simply not be in force. THE FIX IS THE CONFIG, '
                    'NOT THE DIRECTORY: point '
                    '~/.config/precedent/config.json\'s individual.path (and '
                    'any sibling source path) at the copy that holds the '
                    'work. Moving or deleting the other one does not hold -- '
                    'the source self-heal re-clones whatever path the config '
                    'still names, within the same session. Then confirm from '
                    'a tool\'s OWN output which path it loaded, rather than '
                    'assuming the change took. This tool never deletes a '
                    'clone and never rewrites your config'))
    # THE CATALOGUE IS READ OFF THESE WORKING TREES, and nothing fetches
    # before it reads: precedent_materialize.py has no fetch call in it at
    # all. So a clone sitting behind its own origin does not fail anything,
    # it quietly puts an older set of practices in force. Measured
    # 2026-09-21: all four sources on this disk were 17 to 34 commits
    # behind, every dirty path was engine output nobody had hand-edited, and
    # every session start had reported success
    # (todo-2026-09-21-refresh-output-blocks-the-next-pull).
    #
    # Said HERE as well as in the refresh, deliberately: a session is told at
    # its start rather than six steps into a vendor-update runbook, which is
    # the difference between a fix and a post-mortem. Morgan, 2026-09-21
    # (strength: assented).
    name = 'each practice source clone is current with its own origin'
    behind = []
    for shown, _base in _attachable_sources():
        real = _expand_source_path(shown)
        state = _clone_behind(real)
        if state:
            behind.append(f'{shown} is {state}')
    if not behind:
        out.append((name, True, ''))
    else:
        out.append((name, False, '; '.join(behind) + '. The catalogue in '
                    'force is read from these working trees and nothing '
                    'fetches first, so the practices this session is '
                    'following may be the older ones. Run '
                    '`python3 tools/precedent_refresh_sources.py --apply`, '
                    'which now brings each clone current before refreshing '
                    'it and refuses to report success when it cannot.'))
    return out


def _clone_behind(path):
    """-> a short phrase describing how this clone differs from its own
    origin, or '' when it is current (or cannot be told, which is not a
    finding -- practice: fail-gracefully).

    Compares against the clone's DECLARED base_branch where it has one,
    never origin/HEAD: origin/HEAD answers "what does GitHub show first",
    and this repository is the standing counterexample -- default `main`,
    work on `precedent-beta-v01`."""
    try:
        cfg = json.loads((pathlib.Path(path) / 'precedent.json')
                         .read_text(encoding='utf-8'))
        branch = cfg.get('base_branch')
    except Exception:
        branch = None
    if not isinstance(branch, str) or not branch.strip():
        branch = 'main'
    try:
        proc = subprocess.run(
            ['git', '-C', str(path), 'rev-list', '--left-right', '--count',
             f'origin/{branch}...HEAD'], capture_output=True, text=True)
    except OSError:
        return ''
    if proc.returncode != 0:
        return ''
    parts = proc.stdout.split()
    if len(parts) != 2:
        return ''
    back, ahead = parts
    if back == '0' and ahead == '0':
        return ''
    bits = []
    if back != '0':
        bits.append(f'{back} commit(s) behind origin/{branch}')
    if ahead != '0':
        bits.append(f'{ahead} unpushed commit(s) ahead')
    return ' and '.join(bits)


def _git_head(path):
    """-> (code, short sha) for a clone, or (1, '') when it cannot be read.
    Never raises: a directory that vanished between the scan and here is a
    row that says 'unreadable', not a traceback in a session-start check."""
    try:
        proc = subprocess.run(['git', '-C', str(path), 'rev-parse', '--short',
                               'HEAD'], capture_output=True, text=True)
    except OSError:
        return 1, ''
    return proc.returncode, proc.stdout.strip()



def failing_guarantees(offline=True):
    """-> [(name, detail)] for every guarantee measured as NOT in effect.

    For callers that are not this tool: a gate, a runbook step, anything a
    session actually runs. `None` (undetermined) is deliberately not
    included -- a nag that fires on "cannot tell" is a nag that gets
    ignored, and the rows that matter here report False with certainty.
    """
    return [(name, detail) for name, ok, detail in checks(offline=offline)
            if ok is False]


def remind(offline=True, prefix='precedent'):
    """-> a short block naming the broken guarantees, or '' when none are.

    WHY THIS EXISTS, 2026-09-14. The module docstring above says this tool
    is reachable two ways: AGENTS.md's opening banner, and `--apply`. A
    session that day read that banner, did not run the tool, and worked for
    hours with FOUR guarantees down -- no session-practices file, no commit
    backstop, two uninstalled packages -- noticing only when the packages
    surfaced as three unrelated-looking harness failures. Guidance a session
    can skip is not a mechanism. So the tool now also speaks from somewhere
    a session cannot skip: the gates it runs at named moments
    (tools/precedent_gate.py), which is the third route
    (practice: checkable-gets-checked).
    """
    bad = failing_guarantees(offline=offline)
    if not bad:
        return ''
    lines = [f'{prefix}: {len(bad)} SessionStart guarantee(s) NOT in effect '
             f'-- this session is not set up the way its instructions assume:']
    for name, detail in bad:
        lines.append(f'  - {name}')
        if detail:
            first = detail.split('. ')[0].strip()
            lines.append(f'      {first}')
    lines.append('  full report: python3 tools/precedent_session_check.py '
                 '(--apply repairs most, unless a row names its own remedy)')
    return '\n'.join(lines)


def _expand_source_path(path):
    """The same expansion the guard's _also_resolve does, so this row agrees
    with the thing it is reporting on rather than approximating it."""
    home = os.environ.get('HOME', '')
    proj = os.environ.get('CLAUDE_PROJECT_DIR', str(ROOT))
    if path == '~':
        path = home
    elif path.startswith('~/'):
        path = home + path[1:]
    for token, value in (('${HOME}', home), ('$HOME', home),
                         ('${CLAUDE_PROJECT_DIR}', proj),
                         ('$CLAUDE_PROJECT_DIR', proj)):
        path = path.replace(token, value)
    return path


def _attachable_sources():
    """-> [(path, base_branch)] for every practice source on this disk that
    the also-list could name, written $HOME-relative where that is what it
    is, so the suggested value survives a container whose $HOME differs --
    which is the whole bug this reports on.

    Read off the disk rather than from a list here: a source set is added by
    editing precedent.json, and a suggestion that had to be kept in step by
    hand would go stale the first time one was."""
    home = os.environ.get('HOME', '')
    found, seen = [], set()
    roots = [pathlib.Path(home)] if home else []
    roots.append(ROOT.parent)
    for parent in roots:
        try:
            entries = sorted(parent.iterdir())
        except OSError:
            continue
        for d in entries:
            if not d.name.startswith('precedent-'):
                continue
            if not (d / '.git').exists() or d.resolve() == ROOT:
                continue
            real = str(d.resolve())
            if real in seen:
                continue
            seen.add(real)
            base = 'main'
            manifest = d / 'precedent.json'
            if manifest.is_file():
                try:
                    base = json.loads(manifest.read_text(
                        encoding='utf-8')).get('base_branch') or 'main'
                except (OSError, ValueError):
                    pass
            shown = str(d)
            if home and shown.startswith(home + '/'):
                shown = '~' + shown[len(home):]
            found.append((shown, base))
    return found


def apply_repair():
    """Run the three SessionStart hooks by hand, in settings.json's order."""
    branch = _declared_branch() or 'main'
    hooks = [
        ('session-start.sh', []),
        ('freshness-guard.sh', ['session-start', branch]),
        ('commit-identity.sh', []),
    ]
    failed = []
    for name, args in hooks:
        path = ROOT / '.claude' / 'hooks' / name
        if not path.is_file():
            print(f'  SKIP {name} -- not present in this checkout')
            continue
        print(f'  running {name} {" ".join(args)}')
        p = subprocess.run(['bash', str(path), *args], cwd=str(ROOT))
        if p.returncode != 0:
            failed.append(name)
    # Never silent: a repair that half-worked is the state this whole tool
    # exists to make visible.
    for name in failed:
        print(f'  WARN: {name} exited non-zero -- re-run it directly to see why')
    return not failed


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true',
                    help='run this repo\'s SessionStart hooks by hand, then '
                         're-check')
    args = ap.parse_args()

    if args.apply:
        print('applying the SessionStart hooks by hand:\n')
        apply_repair()
        print()

    rows = checks()
    bad = [r for r in rows if r[1] is False]
    unknown = [r for r in rows if r[1] is None]
    for name, ok, detail in rows:
        mark = 'OK  ' if ok else ('FAIL' if ok is False else '??  ')
        print(f'  {mark} {name}')
        if detail:
            print(f'       {detail}')
    print()
    if bad:
        print(f'session check: {len(bad)} guarantee(s) NOT in effect'
              + (f', {len(unknown)} undetermined' if unknown else '') + '.')
        if not args.apply:
            print('Repair: python3 tools/precedent_session_check.py --apply')
            # Not every guarantee is --apply's to restore, and a remedy that
            # cannot work is worse than none because it is tried first and
            # believed (2026-09-09, the backstop row's own comment). A row
            # that knows better says so in its detail.
            print('       -- unless a row above names a different remedy in '
                  'its own detail, which is the one that will actually work')
        return 1
    print(f'session check OK: {len(rows) - len(unknown)} guarantee(s) in '
          f'effect' + (f', {len(unknown)} undetermined' if unknown else '') + '.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

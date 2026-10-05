#!/usr/bin/env python3
"""Reports whether this session's SessionStart guarantees are actually in effect -- practices file, commit identity, backstop, packages, refspec, freshness, and the branch it started on -- and `--apply` runs the hooks by hand when the harness never did

Did this session's SessionStart hooks actually run? -- and repair it.

practice: session-bootstrap, fail-gracefully

THE INCIDENT, 2026-09-08. A session opened with four Precedent repositories
side by side under a parent directory -- this project's own required layout,
since a shared source resolves as a SIBLING CLONE -- and the harness rooted the
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
shared and individual practices in force reach a session at all. AGENTS.md's
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
    """The branch this checkout is measured against: the repository's
    declared base_branch -- or, for a person off the ladder, main, the only
    branch their work lands on (spec/LADDER_OPT_IN_PLAN.md D3)."""
    try:
        import precedent_branches as _pb
        if _pb.ladder_in_force(ROOT) is False:
            return _pb.MAIN
    except Exception:                                       # noqa: BLE001
        pass
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
    from an existing git config or the session account is NOT a declaration
    and does not install the global backstop; the authenticated GitHub
    account does, but only when its lookup succeeds, which this cannot see --
    so the backstop row uses this to name a remedy only once the backstop is
    already missing.
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


def _own_new_branch(git, cur, start_sha, stamp):
    """-> True when `cur` is a branch this session made itself from where it
    started (`git checkout -b`, stage 2, Act): the oldest entry in its
    reflog is its creation, dated no earlier than the stamp, at a commit
    that carries the start. A branch that existed before the session -- the
    base branch HEAD was once moved onto mid-turn -- has an older reflog,
    and still fails the row (2026-09-30)."""
    if not start_sha:
        return False
    rc, log, _ = git('reflog', 'show', '--date=unix', '--format=%H %gd %gs',
                     f'refs/heads/{cur}', '--')
    lines = [l for l in (log or '').splitlines() if l.strip()]
    if rc != 0 or not lines:
        return False
    sha, gd, *msg = lines[-1].split(' ', 2)
    if not (msg and msg[0].startswith('branch: Created from')):
        return False
    try:
        created = int(gd.rsplit('{', 1)[1].rstrip('}'))
        if created < int(stamp.stat().st_mtime):
            return False
    except (IndexError, ValueError, OSError):
        return False
    # Made from a declared tier branch: the ladder's own move. A cloud
    # session starts on main and branches from origin/pre-staging, which
    # lacks main's newest merge commit until the next back-merge -- so the
    # start commit is not in it, and every ladder session was warned on
    # every prompt (2026-10-01, from a consumer's session).
    source = msg[0][len('branch: Created from'):].strip()
    if _is_tier_ref(git, source):
        return git('merge-base', '--is-ancestor', sha, 'HEAD')[0] == 0
    return (git('merge-base', '--is-ancestor', start_sha, sha)[0] == 0
            and git('merge-base', '--is-ancestor', start_sha, 'HEAD')[0] == 0)


_TIER_NAMES = ('main', 'staging', 'pre-staging', 'precedent-beta-v01')


def _is_tier_ref(git, ref):
    """True when `ref` (a branch's "Created from" source) names a tier
    branch here, local or origin's: main, staging, pre-staging, or a branch
    precedent.json declares as base, staging or landing branch."""
    name = ref
    for prefix in ('refs/remotes/', 'refs/heads/', 'origin/'):
        if name.startswith(prefix):
            name = name[len(prefix):]
    names = set(_TIER_NAMES)
    rc, top, _ = git('rev-parse', '--show-toplevel')
    if rc == 0 and top:
        try:
            cfg = json.loads((pathlib.Path(top.strip()) / 'precedent.json')
                             .read_text(encoding='utf-8'))
            names |= {str(cfg.get(k)) for k in ('base_branch', 'staging_branch',
                                                 'landing_branch') if cfg.get(k)}
        except (OSError, ValueError, AttributeError):
            pass
    return name in names


def _session_branch_row(stamp, git):
    """The "still on the branch it started on" row, or None when HEAD cannot
    be read. The stamp is two lines, the branch and the commit the session
    started on (an older one-line stamp carries the branch alone).

    A session that STARTED DETACHED (`HEAD`) and is now on a named branch has
    made the move every cloud session makes: it adopts the branch as its
    start and passes, provided the commit it started on is in that branch's
    history -- work made detached is then carried, not stranded. A detached
    start whose commit is NOT in the branch it moved to is still a finding,
    and so is a move back to detached, or between two named branches --
    except onto a branch this session created from where it started
    (_own_new_branch), which is its own feature branch."""
    rc, cur, _ = git('rev-parse', '--abbrev-ref', 'HEAD')
    if rc != 0 or not cur:
        return None
    name = 'this session is still on the branch it started on'
    _, sha, _ = git('rev-parse', 'HEAD')

    def write():
        try:
            stamp.write_text(f'{cur}\n{sha}\n')
        except OSError:
            pass

    if not stamp.is_file():
        write()
        return (name, None, f'first run this session -- recorded {cur!r} as '
                            f'the baseline to compare against later')
    lines = stamp.read_text().split()
    started = lines[0] if lines else ''
    start_sha = lines[1] if len(lines) > 1 else ''
    if started == cur:
        return (name, True, '')
    if started == 'HEAD' and cur != 'HEAD':
        carried = (not start_sha
                   or git('merge-base', '--is-ancestor', start_sha, 'HEAD')[0] == 0)
        if carried:
            write()
            return (name, True, f'started detached at '
                                f'{start_sha[:12] or "an unrecorded commit"} and '
                                f'moved onto {cur!r}, which carries it -- the '
                                f'normal first step; {cur!r} is now the baseline')
        return (name, False,
                f'started detached at {start_sha[:12]}, now on {cur!r}, which '
                f'does NOT contain that commit. Anything committed while '
                f'detached is reachable only from `git reflog` -- check it '
                f'before it is garbage-collected')
    if started != 'HEAD' and cur != 'HEAD' and _own_new_branch(git, cur, start_sha, stamp):
        write()
        return (name, True, f'started on {started!r} and moved onto {cur!r}, a '
                            f'branch this session created from where it started '
                            f'-- its own feature branch; {cur!r} is now the baseline')
    # The branch it started on is wholly inside the one it is on now: work
    # carried, not stranded. Measured 2026-10-01: a container restarted
    # while the checkout sat on a feature branch, so the stamp named that
    # branch; after Booked merged it into pre-staging and the session moved
    # there, every turn said the SessionStart guarantee was not in effect.
    # The start branch's tip as it is NOW, so a commit made there after the
    # stamp counts too; its recorded commit when the branch is gone. Only a
    # start on a working branch: a start on a tier branch moving onto an
    # older one that holds it is still the jump this row exists for.
    if started != 'HEAD' and cur != 'HEAD' and not _is_tier_ref(git, started):
        rc_t, tip, _ = git('rev-parse', '--verify', '-q', f'refs/heads/{started}')
        tip = tip if rc_t == 0 and tip else start_sha
        if tip and git('merge-base', '--is-ancestor', tip, 'HEAD')[0] == 0:
            write()
            return (name, True, f'started on {started!r} and moved onto {cur!r}, '
                                f'which carries all of it -- nothing is stranded; '
                                f'{cur!r} is now the baseline')
    return (name, False,
            f'started on {started!r}, now on {cur!r}. Work committed before '
            f'the move is on {started!r} and is NOT lost -- `git checkout '
            f'{started}` and check `git reflog` for anything after it. Work '
            f'done SINCE the move is on the wrong branch')


SOURCES_RESOLVED_ROW = 'every private practice source this repo declares resolved'


def sources_resolved_row(verdict, message, unresolved=()):
    """-> the (name, ok, detail) row for precedent_source_credentials.assess()'s
    verdict; `unresolved` is its unresolved_private_sources() list.

    The row judges whether the sources RESOLVED, not whether a credential
    exists. Until 2026-10-02 it read "resolved, or a credential is set that
    could reach them" and passed on 'set' -- a source missing while a token
    IS set -- with an empty detail. So a precedent.json naming a shared set
    that does not exist, or was renamed or retired, showed a green row here
    while that set's practices were absent all session; only the resolver's
    stderr and SESSION_PRACTICES.md said so. A shared set this repository
    DECLARES and does not have now fails the row, token or no token, with
    assess()'s own message, which names it and points at a retired
    declaration as well as a refused credential.

    'set' with only the individual set unresolved still passes, now saying
    its piece: a token is itself read as a sign that the person has an
    individual set (individual_signals), so a person who set one for their
    shared sets and has no individual set would otherwise see this row red
    every session. 'unconfigured' passes with its message for the same kind
    of reason -- no repository or credential is in the wrong state, the
    user-level config is, and no token fixes it (practice: fail-gracefully)."""
    if verdict == 'ok':
        return (SOURCES_RESOLVED_ROW, True, '')
    shared_missing = any(level == 'shared' for level, _, _ in unresolved)
    ok = verdict == 'unconfigured' or (verdict == 'set' and not shared_missing)
    return (SOURCES_RESOLVED_ROW, ok, message)


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
            f'and none of them ran. This is the incident in the docstring. '
            f'For a session opened above several repos, the environment '
            f'setup-script step in documentation/CLOUD_SETUP.md ("When a '
            f'Session Opens Above Your Repos") runs them')
        out.append(('the harness rooted the session at this repository',
                    ok, detail))

    # 2. The practices in force from private sources reached the session.
    sp = ROOT / '.precedent' / 'SESSION_PRACTICES.md'
    ok = sp.is_file()
    out.append(('the shared and individual practices in force were written to '
                '.precedent/SESSION_PRACTICES.md', ok,
                '' if ok else
                'the file does not exist, so every shared and individual '
                'practice binding work here is SILENTLY absent -- AGENTS.md '
                "tells this session to read it and there is nothing to read. "
                'Regenerate: python3 tools/precedent_session_practices.py'))

    # 2b. ...and whether the sources themselves resolved, and if not, why.
    # The row above says the FILE is missing; this one says whether the
    # sources themselves resolved, which is the thing that actually binds
    # work here. Both matter: the file can exist and honestly report that
    # every private source was unreachable, which is the state a whole
    # working day was once lost to (AGENTS.md's "no individual source
    # resolved" gotcha).
    try:
        import precedent_source_credentials as psc
        out.append(sources_resolved_row(*psc.assess(ROOT),
                                        psc.unresolved_private_sources(ROOT)))
    except ImportError:
        out.append((SOURCES_RESOLVED_ROW, None,
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
    # identity, or when the identity is the GitHub account the session is
    # AUTHENTICATED as, numeric id included (since 2026-09-30). Where the hook
    # merely INFERRED one -- from an existing git config or the session
    # account -- it deliberately installs nothing. So when the GitHub lookup
    # fails and no individual source is reachable, `--apply` re-runs the hook,
    # the hook declines again, and the row stays FAIL.
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
                'DECLARED identity or the GitHub account the session is '
                'authenticated as, and here the account lookup found no id and '
                'nothing declares one (no PRECEDENT_COMMIT_EMAIL, no '
                'identity.json in this repo, no individual practice source '
                'carrying one). Declare one and re-run the hook:\n'
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
    #
    #    A SECOND, INDEPENDENT OCCURRENCE, 2026-09-25 -- gotchas/gotcha-2026-
    #    09-25-a-session-rooted-above-every-repo-it-touches-gets-hooks-and.md.
    #    Same shape (HEAD moved to the base branch mid-turn, none of the
    #    three suspects above in play), in a session where every repo's own
    #    hooks were provably inert throughout (none of the four attached
    #    repos was $CLAUDE_PROJECT_DIR). That same session also caught the
    #    global git identity in ~/.gitconfig flip back to the container's
    #    bot account mid-session with no `git config` command run in
    #    between, and traced `gpg.ssh.program` to the container's own
    #    session orchestrator (`environment-manager`) as the best-fit
    #    suspect for both -- flagged there as a theory, not confirmed. Read
    #    that gotcha before extending this row: the stamp below only catches
    #    a move on a run AFTER the one that recorded the baseline, so run
    #    this check as close to session start as possible when rooted above
    #    every repo you touch.
    #
    #    A FALSE ALARM ON EVERY CLOUD SESSION, 2026-09-30. A cloud session is
    #    cloned onto a bare commit (detached HEAD, which git names `HEAD`) and
    #    then moved onto the branch the harness assigns it. The stamp recorded
    #    `HEAD`, so that expected first move failed this row on every prompt
    #    for the life of the session, which teaches everyone to skim past it
    #    -- including the day it catches a real jump. The stamp now carries
    #    the commit too; see _session_branch_row.
    row = _session_branch_row(ROOT / '.git' / 'precedent-session-branch', _git)
    if row:
        out.append(row)

    # 8. Freshness. Reported, never repaired here: discarding work is worse
    #    than a stale tree, so this only ever tells (practice: fail-gracefully).
    #    The only row that fetches, so the only one `offline` drops.
    branch = _declared_branch()
    rc, cur, _ = _git('rev-parse', '--abbrev-ref', 'HEAD')
    if branch and rc == 0 and not offline:
        _git('fetch', '--quiet', 'origin', branch)
        rc2, behind, _ = _git('rev-list', '--count', f'HEAD..origin/{branch}')
        # Behind only by commits that change no file is not behind (Morgan,
        # 2026-09-27, strength: decided); the count read is the real ones.
        if rc2 == 0 and behind.isdigit() and behind != '0':
            if _git('diff', '--quiet', 'HEAD', f'origin/{branch}')[0] == 0:
                behind = '0'
            else:
                rc3, real, _ = _git('rev-list', '--count', '--no-merges',
                                    f'HEAD..origin/{branch}', '--', '.')
                if rc3 == 0 and real.isdigit() and real != '0':
                    behind = real
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
    name = 'PRECEDENT_FRESHNESS_ALSO, if set, names repositories that are there'
    # The row once offered a value to set, naming every attachable practice
    # set, computed for this disk (2026-09-21). Since 2026-09-30 the guard
    # checks every declared set on its own, so that value was the stale
    # advice a session reported on 2026-10-03; the row now never offers one.
    if raw is None:
        # Not a gap any more (2026-09-30): the freshness guard checks every
        # practice set this repo and this person declare, from the
        # resolver's own paths. The variable is only for extra repositories.
        out.append((name, True,
                    'not set, which is fine: the freshness guard checks every '
                    'practice set this repo and you declare on its own. Set it '
                    'only for a repository nothing declares'))
    else:
        # WHEN THE ANSWER IS "DELETE IT" (2026-10-03). Since 2026-09-30 the
        # guard checks every practice set this repo and the person declare on
        # its own, so an entry naming one is redundant, and an entry naming a
        # retired precedent-team-* set (renamed precedent-shared-* on
        # 2026-09-28) names nothing at all. A session reported this row
        # warning at the top of every turn about a variable still naming the
        # old team paths, and offering a corrected value -- for a variable
        # nobody needs. When every entry is one of the two, the remedy is to
        # delete it; a replacement value is only offered for entries naming a
        # repository nothing else covers.
        bad, retired, redundant, extra = [], [], [], []
        for entry in (e.strip() for e in raw.split(';')):
            if not entry:
                continue
            if '=' not in entry:
                bad.append(f'{entry!r} has no =<base branch>')
                extra.append(entry)
                continue
            written = entry.split('=', 1)[0].strip()
            resolved = _expand_source_path(written)
            if pathlib.Path(written).name.startswith('precedent-team-'):
                retired.append(written)
                continue
            if (pathlib.Path(resolved) / 'precedent-source.json').is_file():
                redundant.append(written)
                continue
            extra.append(entry)
            if not (pathlib.Path(resolved) / '.git').exists():
                shown = (f'{written!r}' if resolved == written
                         else f'{written!r} (-> {resolved!r})')
                bad.append(f'{shown} is not a git repository')
        if not extra:
            said = []
            if retired:
                said.append(f'{len(retired)} name{"s" if len(retired) == 1 else ""} '
                            f'the retired precedent-team-* '
                            f'sets, renamed precedent-shared-* on 2026-09-28')
            if redundant:
                said.append(f'{len(redundant)} name{"s" if len(redundant) == 1 else ""} '
                            f'a practice set, which the '
                            f'freshness guard checks on its own when this repo '
                            f'or you declare it')
            out.append((name, not retired,
                        'set, and not needed: ' + '; '.join(said) + '. Delete '
                        'PRECEDENT_FRESHNESS_ALSO from your environment\'s '
                        'settings, where it was set -- do not replace it.'))
        else:
            ok = not bad and not retired
            out.append((name, ok, '' if ok else
                        '; '.join(bad + [f'{r!r} is a retired precedent-team-* '
                                         f'name -- drop it' for r in retired])
                        + '. Each of these is SKIPPED, silently by design -- the '
                        'variable reads as coverage and covers nothing. Drop each '
                        'one; keep only repositories that exist and that nothing '
                        'declares -- a practice set needs no entry.'))

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
    # diverged between its two copies. The also-list suggestion this row
    # then offered was dutifully naming both, which is honest and is also the tell -- a
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
    #
    # 2026-09-28, the individual set's own cause, reported by two consumer
    # sessions: the attach tool's reply puts a clone in the project's
    # directory while the bootstrap's is in $HOME. The bootstrap now links
    # the empty one of the two to the tree that exists
    # (precedent_source_bootstrap._one_individual_tree), which also makes
    # "remove the emptied copy" hold -- the next run links that path rather
    # than cloning it again. Two trees already present are still only
    # reported, by the bootstrap and by this row.
    name = 'each practice source is cloned exactly once on this disk'
    by_name = {}
    for shown, _base in _attachable_sources():
        by_name.setdefault(pathlib.Path(shown).name, []).append(shown)
    # COUNT WORKING TREES, NOT PATH NAMES. Two paths for one source are only a
    # duplicate when they are two separate clones; when one is a symlink to
    # the other there is a single tree, a single place to commit into, and
    # nothing that can silently diverge -- which is the entire failure this
    # row exists to catch. precedent_source_bootstrap._clone_elsewhere_on_disk
    # resolves the sibling-path collision that way on purpose (2026-09-22), so
    # a row that still called the result a duplicate would be red forever on
    # exactly the containers that had just fixed it -- and a row that is never
    # green is a row sessions stop reading.
    def _tree(shown):
        try:
            return str(_expand_source_path(shown).resolve())
        except Exception:
            return shown
    dupes = {n: paths for n, paths in by_name.items()
             if len({_tree(p) for p in paths}) > 1}
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
                    'one may simply not be in force. FOR A SHARED SET, THE '
                    'CAUSE IS USUALLY THE SIBLING PATH: every repo declares '
                    'its sources at ../<name>, so a consumer and an '
                    'individual set with different parents each resolve the '
                    'same set into their own parent and clone it twice. '
                    'Re-running the source bootstrap links the second path '
                    'to the first tree instead of cloning it again '
                    '(precedent_source_bootstrap._clone_elsewhere_on_disk); '
                    'deleting a stray by hand does not hold, because '
                    'whatever resolved that path re-creates it next session. '
                    'FOR THE INDIVIDUAL SET, THE USUAL CAUSE IS THE ATTACH '
                    'TOOL: its reply says to clone into the directory the '
                    'project lives in, while the bootstrap clones to '
                    '$HOME. The bootstrap now links whichever of those two '
                    'paths is empty to the tree that exists, so a pair on '
                    'disk predates that or was cloned by hand. Carry any '
                    'work (unpushed commits, uncommitted files) out of one '
                    'copy into the other, remove the emptied one, and re-run '
                    'the individual bootstrap (--apply): it links that path '
                    'to the remaining tree and points '
                    '~/.config/precedent/config.json\'s individual.path at '
                    'it. Then confirm from a tool\'s OWN output which path it '
                    'loaded, rather than assuming the change took. This tool '
                    'never deletes a clone and never rewrites your config'))
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
    #
    # THREE STATES, NOT TWO, and the third is why this row was rewritten on
    # 2026-09-23. `_clone_behind` compared against the clone's own
    # remote-tracking ref and never fetched, so a clone that had not fetched
    # since it was made measured itself against its own stale `origin/main`,
    # counted zero commits, and reported CURRENT. The row could not detect
    # the condition it names.
    #
    # It cost a real wrong answer the same day: this container's
    # precedent-shared-working-style clone sat six commits behind for a whole
    # session, two practices that had been moved into that set read as
    # present in NO source, and a session reported to its user, three times,
    # that two rules had been silently switched off. They had not. The copies
    # had landed upstream hours earlier. Absent-from-disk was reported as
    # absent-full-stop, which is the exact confusion the shared set's
    # `drift-notice` names: tell "could not verify" apart from
    # "confirmed".
    #
    # So: BEHIND is still a hard False, including when read off a stale ref
    # -- a clone that already looks behind against an old ref is behind for
    # certain, and that reading is worth keeping on the cheap offline path.
    # "Looks current" is only True when a fetch actually succeeded; otherwise
    # it is None, undetermined, which `failing_guarantees` deliberately does
    # not nag about. What it must never be again is True.
    #
    # EVERY CLONE A DECLARED SOURCE RESOLVES TO, the universal one included
    # (2026-09-30). The row read only directories named precedent-*, so a
    # practice set's ../BestPractice sat 224 commits behind its origin while
    # the four sets reported current, and the set's session-start file and
    # its budget check were built from two-day-old universal text.
    name = 'each practice source clone is current with its own origin'
    behind, unverified, universal_behind, seen = [], [], [], set()
    set_behind = []
    targets = [(shown, None, False) for shown, _base in _attachable_sources()]
    targets += [(path, branch, branch is not None)
                for path, branch in _declared_source_clones()]
    for shown, branch, universal in targets:
        real = _expand_source_path(shown)
        key = str(pathlib.Path(real).resolve())
        if key in seen:
            continue
        seen.add(key)
        verdict, phrase = (_clone_behind(real, fetch=not offline)
                           if branch is None else
                           _clone_behind(real, fetch=not offline, branch=branch))
        if verdict == 'behind':
            behind.append(f'{shown} is {phrase}')
            if universal:
                universal_behind.append(real)
            else:
                set_behind.append(str(pathlib.Path(real).resolve()))
        elif verdict == 'unverified':
            unverified.append(f'{shown} ({phrase})')
    if behind:
        ff = ''.join(f' For the universal catalogue at {u}: `git -C {u} fetch '
                     f'origin main && git -C {u} merge --ff-only origin/main` '
                     f'-- fast-forward only, so it refuses rather than '
                     f'discard a commit of its own there.'
                     for u in universal_behind)
        # The command that exists from here: precedent_refresh_sources.py
        # ships only in a BestPractice clone, not to a consumer or a set
        # (2026-09-30), so the remedy names the copy it can find.
        try:
            import precedent_engine_freshness as _pef
            run = '; '.join(f'`{_pef.refresh_remedy(ROOT, c)}`' for c in set_behind)
        except Exception:                                    # noqa: BLE001
            run = ''
        run = run or '`python3 tools/precedent_refresh_sources.py --apply`'
        out.append((name, False, '; '.join(behind) + '. The catalogue in '
                    'force is read from these working trees and nothing '
                    'fetches first, so the practices this session is '
                    'following may be the older ones. Run ' + run + ', '
                    'which brings each clone current (discarding only the '
                    'engine output a refresh left there) and refuses to '
                    'report success when it cannot.' + ff))
    elif unverified:
        out.append((name, None, 'could not compare: ' + '; '.join(unverified)
                    + '. This is UNMEASURED, not clean -- a clone compared '
                    'against a remote-tracking ref nothing refreshed reports '
                    'itself current however far behind it is. Run `python3 '
                    'tools/precedent_session_check.py` (which fetches) '
                    'before concluding a practice is absent from a source'))
    else:
        out.append((name, True, ''))

    # 10. The CI cadence this repository resolves (spec/CI_CADENCE_PLAN.md).
    #
    # Said out loud at every check because the retired ci_debounce_minutes
    # taught what a quiet knob costs: somebody tunes it, sees nothing change,
    # and concludes the lever does not work. So this names the value in
    # force, where it came from, and why a commit here would or would not be
    # tagged -- and fails only when a cadence was asked for and nothing on
    # this machine can apply it.
    out.append(_ci_cadence_row())

    # 11-13. The sets a person brings, where their work lands, and what this
    # session loads against this repository's ceilings
    # (spec/LADDER_OPT_IN_PLAN.md D8).
    out.extend(_brought_sets_rows())
    out.append(_landing_row())
    out.extend(_session_load_rows())
    return out


def _individual_path():
    """The individual set's path from the user config, or None."""
    try:
        import precedent_resolve as pr
        cfg_path = pathlib.Path(os.environ.get(
            pr.USER_CONFIG_ENV, str(pr.DEFAULT_USER_CONFIG))).expanduser()
        ind = json.loads(cfg_path.read_text(encoding='utf-8')).get('individual')
        return pathlib.Path(ind['path']).expanduser() if ind and ind.get(
            'path') else None
    except Exception:                                        # noqa: BLE001
        return None


def _brought_sets_rows():
    """One row, and only for a person whose individual set brings other
    sets: every one of them is cloned and carries practices. A set that
    failed to arrive takes its rules out of every session of theirs, with
    nothing else saying so."""
    try:
        import precedent_resolve as pr
    except Exception:                                        # noqa: BLE001
        return []
    brought = pr.brought_sources(_individual_path(), warn=False)
    if not brought:
        return []
    name = 'every set your individual set brings is here'
    missing = [b for b in brought
               if not (pathlib.Path(b['path']) / 'practices').is_dir()]
    if not missing:
        return [(name, True, '')]
    return [(name, False,
             'not here: ' + ', '.join(f"{b['name']} (expected at {b['path']})"
                                       for b in missing)
             + '. Its rules are absent from this session, and nothing else '
             'says so. Fetch it: python3 tools/precedent_source_bootstrap.py')]


def _landing_row():
    """Where this person's work lands here, said once (D3)."""
    name = 'where your work lands here'
    try:
        import precedent_branches as pb
        branch, why = pb.landing_branch(ROOT)
    except Exception as e:                                   # noqa: BLE001
        return (name, None, f'could not be worked out: {e}')
    return (name, True, f'{branch} -- {why}' if why else branch)


def _session_load_rows():
    """What this person's session loads before any work, against the
    ceilings this repository declares. The session file is rendered per
    person, so a set one person brings can take theirs over a ceiling the
    repository's own check, run by someone else, never sees."""
    try:
        import session_load_trend as slt
    except Exception:                                        # noqa: BLE001
        return []
    reg = slt.registry() or {}
    surfaces = reg.get('surfaces') or {}
    over, measured = [], []
    for rel in ('AGENTS.md', '.precedent/SESSION_PRACTICES.md'):
        f = ROOT / rel
        cap = (surfaces.get(rel) or {}).get('ceiling')
        if not f.is_file() or not cap:
            continue
        n = slt.approx_tokens(slt.as_measured(
            rel, f.read_text(encoding='utf-8', errors='replace')))
        measured.append(f'{rel} ~{n:,} of {cap:,}')
        if n > cap:
            over.append(f'{rel} is ~{n:,} tokens, over its ceiling of {cap:,}')
    if not measured:
        return []
    name = "what this session loads fits this repository's ceilings"
    if over:
        return [(name, False, '; '.join(over) + '. Each of these is read '
                 'before any work; a reduction pass brings it back '
                 '(practice: session-load-budget)')]
    return [(name, True, '; '.join(measured))]


def _ci_cadence_row():
    name = 'the CI cadence this repository resolves is the one applied'
    def _load(path):
        try:
            return json.loads(pathlib.Path(path).expanduser()
                              .read_text(encoding='utf-8'))
        except Exception:
            return None

    def _hours(v):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
            return 0
        return v

    cfg = _load(ROOT / 'precedent.json') or {}
    if not isinstance(cfg, dict):
        cfg = {}
    idents = [ROOT / 'identity.json']
    ucfg = _load(os.environ.get('PRECEDENT_USER_CONFIG')
                 or '~/.config/precedent/config.json')
    if isinstance(ucfg, dict):
        path = (ucfg.get('individual') or {}).get('path')
        if isinstance(path, str) and path:
            idents.append(pathlib.Path(os.path.expandvars(path))
                          .expanduser() / 'identity.json')

    # The github_ci_ name first, the old ci_ name where it is absent
    # (spec/BRANCH_TIERS_PLAN.md) -- the same order the cadence script reads.
    def _repo(name):
        for key in ('github_ci_' + name, 'ci_' + name):
            if key in cfg:
                return True, cfg[key]
        return False, None

    def _personal(name):
        for c in idents:
            d = _load(c)
            for key in ('github_ci_' + name, 'ci_' + name):
                if isinstance(d, dict) and key in d:
                    return d[key], f'{c}'
        return None, 'the default'

    has_hours, repo_hours = _repo('every_hours')
    if has_hours:
        hours, where = _hours(repo_hours), "this repo's precedent.json"
    else:
        v, where = _personal('every_hours')
        hours = _hours(v)
    # Mirrors the cadence script's on_branches(): the repo's own switch, else
    # a repo-declared github_ci_every_hours of 0 (every push, branches too), else
    # the person's; anything but a literal false means CI runs on branches.
    has_br, repo_br = _repo('on_branches')
    if has_br:
        branches, bwhere = repo_br is not False, "this repo's precedent.json"
    elif has_hours and not hours:
        branches, bwhere = True, "this repo's precedent.json (github_ci_every_hours 0)"
    else:
        v, bwhere = _personal('on_branches')
        branches = v is not False
    if not hours and branches:
        return (name, True, f'every push runs CI (github_ci_every_hours is 0, from '
                            f'{where}; github_ci_on_branches is true, from {bwhere})')
    asked = []
    if hours:
        asked.append(f'github_ci_every_hours is {hours:g} (from {where})')
    if not branches:
        asked.append(f'github_ci_on_branches is false (from {bwhere})')
    asked = ' and '.join(asked)
    if cfg.get('visibility') != 'private':
        return (name, True, f'every push runs CI: {asked}, but this repo does '
                            f'not declare "visibility": "private"')
    base = cfg.get('base_branch')
    if not isinstance(base, str) or not base:
        return (name, True, f'every push runs CI: {asked}, but this repo '
                            f'declares no base_branch to apply it on')
    rc, hooks, _ = _git('config', '--get', 'core.hooksPath')
    if rc != 0 or not hooks:
        rc, hooks, _ = _git('rev-parse', '--git-path', 'hooks')
        hooks = str((ROOT / hooks).resolve()) if rc == 0 and hooks else ''
    cad = pathlib.Path(hooks).expanduser() / 'precedent-ci-cadence' if hooks else None
    if not (cad and os.access(cad, os.X_OK)):
        return (name, False, f'{asked}, but no precedent-ci-cadence script '
                             f'sits beside the commit hooks here, so every '
                             f'push still runs CI. commit-identity.sh writes '
                             f'it at session start, and only for a declared '
                             f'identity')
    on_base = (f'CI runs at most once every {hours:g}h (from {where})'
               if hours else 'every push runs CI')
    on_other = ('other branches never run CI (github_ci_on_branches false, from '
                f'{bwhere})' if not branches else 'other branches run CI on '
                'every push')
    return (name, True, f'private, primary branch {base}: {on_base}; '
                        f'{on_other}. PRECEDENT_CI_NOW=1 git commit ... '
                        f'forces a run')


def _clone_behind(path, fetch=True, branch=None):
    """-> (verdict, phrase), verdict one of 'current', 'behind',
    'unverified'.

    Compares against the clone's DECLARED base_branch where it has one,
    never origin/HEAD: origin/HEAD answers "what does GitHub show first",
    and this repository is the standing counterexample -- default `main`,
    work on `precedent-beta-v01`.

    FETCHES FIRST, which it did not until 2026-09-23. Without that, the
    comparison is against whatever the remote-tracking ref last saw, so a
    clone that never fetched is measured against its own stale copy of
    origin and always counts zero. The caller's comment records what that
    cost.

    `fetch=False` is the cheap path for a caller on a gate. It does not
    make the answer safe to trust: a zero count then means "no difference
    against a ref nobody refreshed", which is 'unverified', never
    'current'. A NON-zero count is still 'behind' -- being behind an old
    ref means being at least that far behind the real one.

    `branch`, when given, is the branch the caller reads this clone at,
    and wins over the clone's own base_branch: a consumer reads the
    universal catalogue at main whatever BestPractice declares for its own
    work."""
    if branch is None:
        try:
            cfg = json.loads((pathlib.Path(path) / 'precedent.json')
                             .read_text(encoding='utf-8'))
            branch = cfg.get('base_branch')
        except Exception:
            branch = None
    if not isinstance(branch, str) or not branch.strip():
        branch = 'main'
    fetched, why = False, 'not fetched -- offline path'
    if fetch:
        try:
            f = subprocess.run(
                ['git', '-C', str(path), 'fetch', '--quiet', 'origin',
                 branch], capture_output=True, text=True)
            fetched = f.returncode == 0
            if not fetched:
                why = (f'fetch of origin/{branch} failed: '
                       + (f.stderr.strip().splitlines() or [''])[-1][:120])
        except OSError as e:
            why = f'fetch of origin/{branch} could not run ({e})'
    try:
        proc = subprocess.run(
            ['git', '-C', str(path), 'rev-list', '--left-right', '--count',
             f'origin/{branch}...HEAD'], capture_output=True, text=True)
    except OSError as e:
        return 'unverified', f'origin/{branch} could not be read ({e})'
    if proc.returncode != 0:
        return 'unverified', f'origin/{branch} did not resolve'
    parts = proc.stdout.split()
    if len(parts) != 2:
        return 'unverified', f'origin/{branch} comparison returned nothing'
    back, ahead = parts
    # Commits that change no file are never counted or reported (Morgan,
    # 2026-09-27, strength: decided): identical files mean current.
    if (back, ahead) != ('0', '0'):
        same = subprocess.run(['git', '-C', str(path), 'diff', '--quiet',
                               f'origin/{branch}', 'HEAD'], capture_output=True)
        if same.returncode == 0:
            back, ahead = '0', '0'
        else:
            for side, rng in (('back', f'HEAD..origin/{branch}'),
                              ('ahead', f'origin/{branch}..HEAD')):
                r = subprocess.run(['git', '-C', str(path), 'rev-list', '--count',
                                    '--no-merges', rng, '--', '.'],
                                   capture_output=True, text=True)
                n = r.stdout.strip()
                if r.returncode == 0 and n.isdigit() and n != '0':
                    if side == 'back':
                        back = n
                    else:
                        ahead = n
    # AHEAD IS NOT UNPUSHED (2026-10-05). A set's clone checked out on
    # purpose at the set's staging read as "6 unpushed commit(s) ahead" of
    # main: those commits were on origin, only not on main yet. Unpushed is
    # what no origin branch has; the rest is named by the branch carrying
    # it, and never by itself makes the clone stale.
    unpushed, on_origin, carrier = ahead, '0', ''
    if ahead != '0':
        r = subprocess.run(['git', '-C', str(path), 'rev-list', '--count',
                            '--no-merges', 'HEAD', '--not', '--remotes=origin',
                            '--', '.'], capture_output=True, text=True)
        n = r.stdout.strip()
        if r.returncode == 0 and n.isdigit():
            unpushed = n
            on_origin = str(max(int(ahead) - int(n), 0))
        r = subprocess.run(['git', '-C', str(path), 'for-each-ref', '--contains',
                            'HEAD', '--format=%(refname:short)',
                            'refs/remotes/origin'], capture_output=True, text=True)
        carrier = next((x for x in r.stdout.split() if x != 'origin/HEAD'), '')
    bits = []
    if back != '0':
        bits.append(f'{back} commit(s) behind origin/{branch}')
    if unpushed != '0':
        bits.append(f'{unpushed} unpushed commit(s) ahead')
    held = (f'checked out off {branch}: {on_origin} commit(s) ahead of '
            f'origin/{branch} that are on origin'
            + (f' ({carrier})' if carrier else '')) if on_origin != '0' else ''
    if bits:
        # True even off a stale ref: behind an old origin is behind.
        return 'behind', ' and '.join(bits) + (f'; {held}' if held else '')
    return ('current', held) if fetched else ('unverified', why)


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


def _declared_source_clones():
    """-> [(path, branch)] for each clone this repo's precedent.json declares
    as a source, other than this repo itself. `branch` is 'main' for the
    universal source -- what every consumer reads it at -- and None for the
    rest, which _clone_behind judges at their own base_branch. Read off the
    config without resolving it: resolving can fetch a missing source, and
    a check that says what is on disk must not change it."""
    try:
        cfg = json.loads((ROOT / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    out = []
    for src in (cfg.get('sources') if isinstance(cfg, dict) else None) or []:
        raw = isinstance(src, dict) and src.get('path')
        if not isinstance(raw, str) or not raw:
            continue
        path = pathlib.Path(os.path.expandvars(raw)).expanduser()
        path = (path if path.is_absolute() else ROOT / path).resolve()
        if path == ROOT.resolve() or not (path / '.git').exists():
            continue
        out.append((str(path), 'main' if src.get('level') == 'universal'
                    else None))
    # AND THE UNIVERSAL CLONE EACH ATTACHED SET READS (2026-10-02). A set
    # under another parent -- the individual set in $HOME beside a project
    # elsewhere -- declares ../BestPractice as a clone of its own, which this
    # row never named from the project: /root/BestPractice sat 131 commits
    # behind while every row here passed. Session start now pulls it
    # (precedent_source_bootstrap.sources_from_attached_sets); this is the
    # row that says so when it could not.
    for shown, _base in _attachable_sources():
        set_root = pathlib.Path(_expand_source_path(shown)).resolve()
        try:
            scfg = json.loads((set_root / 'precedent.json')
                              .read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        for src in (scfg.get('sources') if isinstance(scfg, dict) else None) or []:
            if not isinstance(src, dict) or src.get('level') != 'universal':
                continue
            raw = src.get('path')
            if not isinstance(raw, str) or not raw:
                continue
            path = pathlib.Path(os.path.expandvars(raw)).expanduser()
            path = (path if path.is_absolute() else set_root / path).resolve()
            if path in (ROOT.resolve(), set_root) or not (path / '.git').exists():
                continue
            # Only a clone the bootstrap made (its marker in .git). A person's
            # own BestPractice working copy at that path is on whatever branch
            # their work is, and naming it "behind main" would be a false
            # alarm about their work -- the sync leaves it alone for the same
            # reason (precedent_source_bootstrap.CLONE_MARKER).
            if not (path / '.git' / 'precedent-source-clone').is_file():
                continue
            out.append((str(path), 'main'))
    return out


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
            # ANCHORED WHERE EACH KIND OF SET LIVES, never an absolute path
            # (2026-09-30). A shared set sits beside the project because
            # every repo declares it as ../<name>, so it is written
            # $CLAUDE_PROJECT_DIR/../<name>; the individual set lives in
            # $HOME, so ~/<name>. One value is then right in every repo and
            # on every container. The absolute paths this used to print
            # were right only on the disk they came from, and sessions kept
            # flipping the variable between two of them.
            shown = str(d)
            if d.parent.resolve() == ROOT.parent.resolve():
                shown = f'$CLAUDE_PROJECT_DIR/../{d.name}'
            elif home and shown.startswith(home + '/'):
                shown = '~' + shown[len(home):]
            found.append((shown, base))
    return found


def apply_repair():
    """Run this repo's SessionStart hooks by hand, in settings.json's own order.

    Reads .claude/settings.json rather than naming hooks in this function --
    a hook named here is one more place a NEW hook has to be remembered, and
    that is exactly what went stale: 2026-09-20's additionalContext-emitting
    hook (precedent-universal-catalogue.sh) shipped to every Precedent SET's
    settings.json while this function still ran the three hooks BestPractice
    itself happens to have, which do not include it -- so `--apply` on a set
    repaired everything except the one guarantee this tool was written for.
    settings.json is the one place a hook's presence is already declared;
    reading it means a repair here stays correct for whatever hooks a repo
    actually has, with no per-repo edit to this file, ever.
    """
    settings_path = ROOT / '.claude' / 'settings.json'
    try:
        settings = json.loads(settings_path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        print(f'  SKIP -- could not read .claude/settings.json ({e})')
        return True
    commands = []
    for matcher in settings.get('hooks', {}).get('SessionStart', []):
        for h in matcher.get('hooks', []):
            if h.get('type') == 'command' and h.get('command'):
                commands.append(h['command'])
    if not commands:
        print('  SKIP -- no SessionStart hooks declared in .claude/settings.json')
        return True
    failed = []
    # A shell tool call carries no project-dir variable, and the individual
    # bootstrap finds the attach tool's clone through one
    # (precedent_source_bootstrap.attach_workspace). Without it a repair run
    # from here would clone a second copy beside the one already attached.
    env = dict(os.environ)
    env.setdefault('PRECEDENT_PROJECT_DIR', str(ROOT))
    for cmd in commands:
        resolved = cmd.replace('$CLAUDE_PROJECT_DIR', str(ROOT))
        print(f'  running: {resolved}')
        p = subprocess.run(resolved, shell=True, cwd=str(ROOT), env=env)
        if p.returncode != 0:
            failed.append(resolved)
    # Never silent: a repair that half-worked is the state this whole tool
    # exists to make visible.
    for cmd in failed:
        print(f'  WARN: exited non-zero -- re-run it directly to see why: {cmd}')
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

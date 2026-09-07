#!/usr/bin/env python3
"""checkin.py — drive the periodic check-in (INSTALL.md §4) mechanically.

Runs from a dependent repo (script lives at process/upstream/tools/). The
check-in loop — sync the vendored tree into a clone of the upstream repo,
land it there, then record the landed commit in the manifest — was performed
by hand several times and each pass repeated the same steps with the same
two failure modes: forgetting the scrub before content left the private
repo, and recording a hash that didn't actually match the tree that landed.
Per the convention-becomes-audit rule, the steps are now a tool; every
mutation it performs is gated by a check that fails loudly.

Four subcommands — update takes upstream changes IN, the other three drive
a check-in OUT:

  status <upstream-clone>   Compare the vendored tree against the clone's
                            working tree: list Added/Modified/Deleted files
                            (vendored perspective), show the manifest's
                            recorded upstream.commit vs the clone's HEAD.
                            Exit 1 if the trees differ (so it can gate).

  update <upstream-clone> [--force]
                            The INSTALL.md §2 direction: pull the clone's
                            default branch and mirror it into the vendored
                            tree. REFUSES if the vendored tree differs from
                            the recorded upstream.commit — that difference
                            is unexported local work the mirror would
                            silently clobber; export it first (§3/§4) or
                            pass --force to overwrite. (Origin: a session
                            hand-rolled this mirror with git archive | tar
                            — rsync is absent in hosted containers, as of
                            2026-08 — and a stale local default-branch ref
                            nearly mirrored an old tree; the tool pulls
                            fresh and guards the overwrite.)

  push <upstream-clone> [--force]
                            REFUSES if upstream's default branch has moved
                            past what the vendored tree was mirrored from —
                            the tree is then behind, and this mirror DELETES
                            files it lacks, so it would revert upstream work
                            (run `update` first). Then run the scrub/practice
                            audit — it must
                            pass, THIS is the gate that keeps proprietary
                            content out of the public repo — then mirror the
                            vendored tree into the clone's working tree
                            (deleting files that no longer exist upstream,
                            .git untouched). Committing, opening the PR, and
                            merging remain deliberate manual steps: the PR
                            review is the second scrub line.

  record <upstream-clone> [--note "..."]
                            After the upstream merge: pull the clone's
                            default branch, verify it is byte-identical to
                            the vendored tree (fail loudly if not — never
                            record a hash that doesn't match the tree), then
                            write the clone's HEAD hash into
                            process/manifest.json upstream.commit. Commit
                            the manifest change in the dependent repo
                            yourself.

  fresh                     Clone-free staleness notice for session starts:
                            one `git ls-remote` of the manifest's upstream
                            repo, compared to the recorded upstream.commit.
                            Prints one line only when upstream has moved;
                            always exits 0 (a notice, never a gate) and
                            stays silent on network failure — detection is
                            automated, taking the update stays deliberate
                            (INSTALL.md sec.2).

Run:  python3 process/upstream/tools/checkin.py fresh
      python3 process/upstream/tools/checkin.py status ../BestPractice
      python3 process/upstream/tools/checkin.py update ../BestPractice
      python3 process/upstream/tools/checkin.py push   ../BestPractice
      python3 process/upstream/tools/checkin.py record ../BestPractice --note "PR #4"
"""
import datetime, filecmp, io, json, os, pathlib, shutil, subprocess, sys, tarfile, tempfile

HERE = pathlib.Path(__file__).resolve()
_top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=HERE.parent,
                      capture_output=True, text=True).stdout.strip()
ROOT = pathlib.Path(_top) if _top else HERE.parents[3]
UPSTREAM = ROOT / 'process' / 'upstream'
MANIFEST = ROOT / 'process' / 'manifest.json'


def _same_commit(a, b):
    """True when two commit strings name the same commit.

    A manifest may legitimately record a SHORT hash -- a person writing one
    by hand does, and nothing ever required the full 40 -- while `git
    rev-parse` and `ls-remote` return the full one. Compared as strings
    those never match, so a perfectly current repo reports
    "(!= recorded)" and an unmoved upstream reports "has moved".
    Reproduced 2026-09-06 against a real consumer: recorded 6ac06f6, clone
    HEAD 6ac06f6eb166..., reported as different. Prefix comparison, in
    whichever direction is shorter, with a floor so a truncation to
    nothing cannot match everything."""
    a, b = (a or '').strip(), (b or '').strip()
    if not a or not b:
        return False
    n = min(len(a), len(b))
    if n < 7:            # shorter than git's own minimum abbreviation
        return False
    return a[:n] == b[:n]


def _git(clone, *args):
    return subprocess.run(['git', '-C', str(clone)] + list(args),
                          capture_output=True, text=True).stdout.strip()


def _rev_parse_quiet(clone, ref):
    """-> the commit hash for `ref`, or None. Never the ref's own name.

    `git rev-parse <missing-ref>` exits non-zero but ECHOES THE REF ON
    STDOUT, so the plain `_git(...)` above hands back the string
    'origin/precedent-beta-v01' where a hash belongs -- AGENTS.md's gotchas
    section, which has this reaching CI once already. --verify --quiet is
    silent and exits 1.
    """
    r = subprocess.run(['git', '-C', str(clone), 'rev-parse', '--verify',
                        '--quiet', ref], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


# Directories that exist in BestPractice and have no business in a dependent
# repo. `evals/` is this project's own routing-quality measurement corpus --
# the fixtures behind spec/LOADER.md's recall and precision figures. It answers
# a question about BUILDING Precedent, not about using it, and nothing a
# consumer runs reads any of it (checked across both real consumers,
# 2026-09-06: the only mention outside the vendored tree is a comment in
# precedent_check.py). Every session in every consuming repo was cloning,
# scanning and scrubbing it for nothing.
#
# NOTE, because this reads like a deletion and is not: nothing here removes a
# PRACTICE. Practices live in practices/ and every one of them still vendors.
# This excludes measurement fixtures only.
#
# The share it accounts for is measured, never typed: `python3
# tools/checkin.py not-vendored` prints it against the tree in front of you.
# An earlier version of this comment froze the figures inline and they were
# stale within a day, which is the same rot that practice
# `computed-numbers-in-scripts` exists to stop -- in prose it is a gate, and in
# a code comment nothing checks it at all, so the honest form is a command the
# reader can run.
#
# Excluded from the comparison, so an existing consumer that already has the
# directory simply stops being told it drifted; deleting the stale copy is
# the consumer's own next re-vendor, not something this tool reaches in and
# does.
NOT_VENDORED = frozenset({'evals'})


def not_vendored_share(base=None):
    """-> (excluded_files, total_files, excluded_bytes) for the tree at `base`.

    Measures rather than recites. `_files()` already applies the exclusion, so
    this counts both ways over the same walk it uses, and the two can never
    disagree.
    """
    base = pathlib.Path(base or ROOT)
    total = excluded = 0
    excluded_bytes = 0
    for p in base.rglob('*'):
        if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts:
            continue
        if p.suffix in ('.pyc', '.pyo'):
            continue
        total += 1
        if any(part in NOT_VENDORED for part in p.parts):
            excluded += 1
            try:
                excluded_bytes += p.stat().st_size
            except OSError:
                pass                          # a race or a broken link: not fatal
    return excluded, total, excluded_bytes


def _files(base):
    # Skip interpreter droppings alongside .git: running the vendored audits
    # leaves __pycache__/ behind (ignored by git on both sides via the
    # baseline .gitignore), and counting them as tree drift made every
    # status/record noisy with files no repo tracks. (Ported from `main`,
    # PR #62, 2026-09-01 -- this branch's own checkin.py had already
    # diverged from main's with its own fixes and never picked this one up;
    # see AGENTS.md's gotchas section on re-checking main for drift before
    # phase 5.)
    return {p.relative_to(base) for p in base.rglob('*')
            if p.is_file() and '.git' not in p.parts
            and '__pycache__' not in p.parts
            and not any(part in NOT_VENDORED for part in p.parts)
            and p.suffix not in ('.pyc', '.pyo')}


def _diff(clone):
    """(added, modified, deleted) of the vendored tree vs the clone tree."""
    ours, theirs = _files(UPSTREAM), _files(clone)
    added = sorted(ours - theirs)
    deleted = sorted(theirs - ours)
    modified = sorted(p for p in ours & theirs
                      if not filecmp.cmp(UPSTREAM / p, clone / p, shallow=False))
    return added, modified, deleted


def _manifest():
    # Graceful degradation, not a crash: every caller wants "what does this
    # install record", and a repo with no manifest has a real answer to that
    # -- nothing -- rather than a FileNotFoundError raised from three frames
    # down. A malformed one is different and still fails loudly, because
    # silently treating unreadable JSON as an empty install would let a
    # mirror clobber a tree it could not read the provenance of.
    if not MANIFEST.is_file():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding='utf-8'))
    except ValueError as e:
        sys.exit(f"checkin FAIL: {MANIFEST} is not valid JSON ({e}). Fix it "
                 f"before running anything that mirrors files.")


def _clone_or_die(arg):
    clone = pathlib.Path(arg).resolve()
    if not (clone / '.git').exists():
        sys.exit(f"checkin FAIL: {clone} is not a git clone")
    return clone


def fresh():
    """Session-start staleness notice: automated detection, deliberate take.

    Tells two failure modes apart. A genuinely unreachable remote (offline,
    a slow timeout — no output, no fast error) stays silent, same as
    "nothing has moved" — that was the original behavior and is unchanged.
    But a fast, clean `git ls-remote` failure (non-zero exit — no
    credentials for a private repo in this environment, a 403, "repository
    not found") is a different thing: the check did not run, not that it
    ran and found nothing. The old code treated both the same way (silent),
    which reads a standing credential gap — the same failure, every single
    session, forever in some environments — as "confirmed fresh" in
    perpetuity. (Ported from a fix already made downstream, once, in a
    dependent repo's own wrapper around this same gap — see
    PRACTICE_ENGINE_PLAN.md's evidence table: "checkin.py fresh is silent on
    failure, so unreachable reads as 'current'". Fixing it here, in the
    engine, means every consumer gets it instead of each one re-patching
    its own copy.)
    """
    try:
        up = _manifest().get('upstream', {})
        repo, recorded = up.get('repo'), up.get('commit')
        if not repo or not recorded:
            return 0
        # Ask for the branch this install is PINNED to, not the remote's
        # default. `ls-remote <repo> HEAD` resolves origin/HEAD -- `main` --
        # so on every consumer tracking precedent-beta-v01 this compared the
        # pinned branch's recorded commit against an unrelated lineage and
        # printed "upstream has moved" every single session, forever. It is
        # the most-run instance of the whole family, since tools/bootstrap.sh
        # calls it at session start; spec/MIGRATING_EXISTING_INSTALLS.md's
        # "The default-branch gotcha" describes exactly this, and prescribed
        # recording upstream.branch in the manifest as the workaround. That
        # field is now what the code reads.
        branch = up.get('branch')
        ref = f'refs/heads/{branch}' if branch else 'HEAD'
        try:
            out = subprocess.run(['git', 'ls-remote', repo, ref],
                                 capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            return 0  # genuinely unreachable -- stays silent, unchanged
        head = out.stdout.split()[0] if out.returncode == 0 and out.stdout else ''
        if branch and out.returncode == 0 and not out.stdout.strip():
            # The pin names a branch the remote does not have. Silence here
            # would read as "current" forever, which is the failure this
            # whole function exists to avoid.
            print(f"COULD NOT VERIFY: this install is pinned to upstream "
                  f"branch {branch!r}, which {repo} does not have. Freshness "
                  f"is NOT checked until process/manifest.json's "
                  f"upstream.branch names a branch that exists there.")
            return 0
        if head and not _same_commit(head, recorded):
            print(f"NOTICE: BestPractice upstream has moved ({head[:12]}; your base "
                  f"{recorded[:12]}) — review at the next check-in "
                  f"(process/upstream/INSTALL.md sec.2/sec.4).")
        elif not head and out.returncode != 0:
            err = (out.stderr or '').strip().splitlines()
            err = err[-1] if err else 'no output'
            print(f"COULD NOT VERIFY: couldn't reach BestPractice upstream ({repo}) to check "
                  f"freshness — `git ls-remote` failed ({err}). This is NOT the same as "
                  f"'confirmed fresh': if you need to know, verify directly instead of trusting "
                  f"this silence.")
    except Exception:
        pass
    return 0


def status(clone):
    added, modified, deleted = _diff(clone)
    recorded = _manifest().get('upstream', {}).get('commit')
    head = _git(clone, 'rev-parse', 'HEAD')
    for p in added:
        print(f"  A {p}")
    for p in modified:
        print(f"  M {p}")
    for p in deleted:
        print(f"  D {p}")
    n = len(added) + len(modified) + len(deleted)
    print(f"vendored vs clone: {n} file(s) differ "
          f"({len(added)} added, {len(modified)} modified, {len(deleted)} deleted)")
    print(f"manifest upstream.commit: {recorded}")
    print(f"clone HEAD:               {head}"
          + ("  (== recorded)" if _same_commit(head, recorded)
             else "  (!= recorded)"))
    return 1 if n else 0


def _stamp_synced_from(commit):
    """Record which upstream commit the vendored tree was last mirrored from.

    Distinct from upstream.commit, which record() writes only after verifying
    the vendored tree is byte-identical to what actually landed upstream. That
    invariant is deliberate and untouched; this field answers a different
    question -- "is the vendored tree current with upstream?" -- which push()
    needs and which upstream.commit cannot answer during the normal cycle,
    because it legitimately lags from update() until the merge is recorded.
    """
    path = ROOT / 'process' / 'manifest.json'
    m = json.loads(path.read_text(encoding='utf-8'))
    m.setdefault('upstream', {})['synced_from'] = commit
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n",
                    encoding='utf-8')


def _declared_base_branch(root):
    """The branch a repo DECLARES its work is measured against, in its own
    precedent.json `base_branch` -- not inferred from `origin/HEAD`.

    Those are two different questions with usually the same answer, which is
    why asking the wrong one survives so long. `origin/HEAD` answers "what
    does GitHub show first"; callers mean "what lineage does this work
    belong to". Returns None when undeclared or unreadable, so callers fall
    back to the old inference rather than breaking (fail-gracefully).
    Enforced by precedent_check.py's `declared-base-branch`.
    """
    try:
        import json as _json, pathlib as _pathlib
        v = _json.loads((_pathlib.Path(root) / 'precedent.json')
                        .read_text(encoding='utf-8')).get('base_branch')
        return v if isinstance(v, str) and v.strip() else None
    except Exception:
        return None


def _default_branch(clone):
    return (_git(clone, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD').rsplit('/', 1)[-1]
            or 'main')


def _tree_at(clone, ref, into):
    """Extract `clone`'s tree at `ref` into `into`, without touching `clone`.

    `git archive` reads objects and writes a tar; it never moves HEAD, never
    changes a branch, and never touches a working tree. update() used to
    reach its source the other way -- `git checkout <branch>` followed by
    `git pull` INSIDE the caller's clone -- which is a mutation of a
    repository the caller passed only as a SOURCE.

    2026-09-06, found by being on the receiving end of it: a session running
    `checkin.py update <bestpractice-clone>` from a consumer repo had its
    BestPractice checkout silently moved off `precedent-beta-v01` onto
    `main`, mid-session, and only noticed because a file it expected was
    suddenly missing. The command had already FAILED its own guard by then,
    so the mutation was pure collateral. On a dirty tree the checkout would
    have failed instead and left the pull half-applied.

    Its sibling precedent_vendor_engine.py makes exactly the opposite
    guarantee in as many words -- "it reads blobs, it never checks the clone
    out" -- and verify_harness.py asserts it. This one now does the same.
    """
    tar = subprocess.run(['git', '-C', str(clone), 'archive', ref],
                         capture_output=True)
    if tar.returncode != 0:
        sys.exit(f"checkin FAIL: cannot read {ref!r} in {clone} "
                 f"({tar.stderr.decode('utf-8', 'replace').strip()}). Fetch it "
                 f"there first -- this tool will not check the clone out.")
    tarfile.open(fileobj=io.BytesIO(tar.stdout)).extractall(into)
    return pathlib.Path(into)


def _tracked_branch(clone):
    """The branch this install actually tracks, which is NOT always the
    clone's default branch.

    The manifest records `upstream.branch` precisely because the two can
    differ -- every consumer of BestPractice tracks `precedent-beta-v01`
    today while `main` is still the configured default. update() read
    `_default_branch(clone)` and would have mirrored `main` over a tree
    vendored from the beta branch: a silent, wholesale revert dressed as an
    update. Same assumption AGENTS.md's own standing rule warns about in the
    merge direction -- never assume `main` just because it is the default.
    """
    recorded = (_manifest().get('upstream', {}) or {}).get('branch')
    return recorded or _default_branch(clone)


def _pinned_branch_hold(clone):
    """Refuse `update` while this install is pinned to a non-default branch.

    spec/MIGRATING_EXISTING_INSTALLS.md's "The default-branch gotcha" has
    said, since 2026-09-06, in as many words: *"Do the vendor as a one-off
    manual mirror ... not `checkin.py update`."* Until now nothing enforced
    it. The document mandated a procedure and the tool cheerfully did the
    thing the document forbade -- exactly the advisory-only state
    checkable-gets-checked exists to end, and the reason a session on
    2026-09-07 had to reason its way to the manual mirror from a paragraph
    instead of being stopped by a guard.

    THE CONDITION IS THE HOLD'S OWN CONDITION, so this retires itself. The
    hold applies "while a non-default branch is pinned"; this fires exactly
    when the manifest's `upstream.branch` differs from the clone's default.
    When precedent-beta-v01 merges to main and each consumer's manifest is
    repointed, pinned == default and the guard stops firing on its own --
    nobody has to remember to delete it, which is how a temporary guard
    usually outlives its reason.

    WHAT IT CANNOT REACH, and this is the important limit: a consumer still
    carrying a PRE-FIX vendored copy of this file. That copy has no guard,
    resolves the remote's default branch unconditionally, and would mirror
    `main` over a beta-vendored tree -- a silent wholesale revert. A guard
    shipped inside the tree it guards is missing from precisely the copies
    that need it, the same shape as the freshness-guard incident in
    AGENTS.md's gotchas. Such a consumer is only covered after one manual
    mirror brings this file in; the manual mirror is therefore still the
    entry point, not an alternative to it.

    An unknown default branch REFUSES rather than proceeding. The asymmetry
    is the hold's own, recorded by Morgan 2026-09-06: guessing wrong here
    costs a silent overwrite of a repo's practices, and refusing wrongly
    costs one manual mirror.
    """
    if os.environ.get('PRECEDENT_ALLOW_PINNED_UPDATE') == '1':
        return
    pinned = (_manifest().get('upstream', {}) or {}).get('branch')
    if not pinned:
        return
    default = _default_branch(clone)
    if default and pinned == default:
        return
    named = f"the clone's default branch ({default})" if default else         "this clone's default branch, which could not be determined"
    sys.exit(
        f"checkin FAIL: this install is PINNED to {pinned!r}, which is not "
        f"{named}.\n"
        f"  spec/MIGRATING_EXISTING_INSTALLS.md's \"The default-branch "
        f"gotcha\" holds `checkin.py update` while a non-default branch is "
        f"pinned: vendor as a one-off manual mirror instead -- replace the "
        f"vendored tree wholesale from a checkout of {pinned!r} -- and leave "
        f"the scheduled sync's `schedule:` block commented out.\n"
        f"  The hold lifts when {pinned!r} merges into the default branch and "
        f"this repo's process/manifest.json is repointed there; this guard "
        f"then stops firing by itself.\n"
        f"  Deliberate override, for one run: "
        f"PRECEDENT_ALLOW_PINNED_UPDATE=1 checkin.py update ...")


def update(clone, force=False):
    """INSTALL.md §2 step 5: mirror the clone's tree at the branch this
    install tracks into the vendored tree, refusing to clobber unexported
    local work. Reads the clone; never checks it out, pulls in it, or moves
    its HEAD."""
    _pinned_branch_hold(clone)
    branch = _tracked_branch(clone)
    # Fetch updates remote-tracking refs only -- it does not touch the
    # clone's working tree, HEAD, or any local branch.
    fetched = subprocess.run(['git', '-C', str(clone), 'fetch', 'origin', branch],
                             capture_output=True, text=True)
    if fetched.returncode != 0:
        print(f"NOTICE: could not fetch origin/{branch} in {clone} "
              f"({fetched.stderr.strip()}) -- mirroring whatever that clone "
              f"already has for {branch}, which may be behind.")
    src_ref = _rev_parse_quiet(clone, f'origin/{branch}') or \
        _rev_parse_quiet(clone, branch)
    if not src_ref:
        sys.exit(f"checkin FAIL: {clone} has no {branch} or origin/{branch} to "
                 f"mirror from. This install records upstream.branch = "
                 f"{branch!r}; fetch that branch in the clone first.")
    if not force:
        recorded = _manifest().get('upstream', {}).get('commit')
        if not recorded:
            sys.exit("checkin FAIL: no upstream.commit recorded in the manifest — "
                     "cannot tell local work from upstream drift; pass --force to mirror anyway")
        tar = subprocess.run(['git', '-C', str(clone), 'archive', recorded],
                             capture_output=True)
        if tar.returncode != 0:
            sys.exit(f"checkin FAIL: recorded commit {recorded[:12]} not found in the clone — "
                     f"fetch it there, or pass --force")
        with tempfile.TemporaryDirectory() as td:
            tarfile.open(fileobj=io.BytesIO(tar.stdout)).extractall(td)
            base = pathlib.Path(td)
            ours, theirs = _files(UPSTREAM), _files(base)
            drift = sorted(ours ^ theirs) + sorted(
                p for p in ours & theirs
                if not filecmp.cmp(UPSTREAM / p, base / p, shallow=False))
        if drift:
            for p in drift:
                print(f"  local change: {p}")
            sys.exit("checkin FAIL: vendored tree differs from the recorded upstream commit — "
                     "that is unexported work the mirror would clobber. Export it first "
                     "(INSTALL.md §3/§4) or pass --force to overwrite.")
    # Mirrored from the SOURCE REF's tree, extracted to a scratch directory --
    # not from the clone's working tree, which this tool no longer moves and
    # which may sit on some entirely different branch.
    with tempfile.TemporaryDirectory() as srcdir:
        src = _tree_at(clone, src_ref, srcdir)
        vendored_only, differing, src_only = _diff(src)
        if not (vendored_only or differing or src_only):
            _stamp_synced_from(src_ref)
            print(f"checkin update: vendored tree already identical to "
                  f"{branch} @ {src_ref[:12]} — nothing to do.")
            return 0
        for p in vendored_only:
            (UPSTREAM / p).unlink()
        for p in differing + src_only:
            (UPSTREAM / p).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / p, UPSTREAM / p)
    _stamp_synced_from(src_ref)
    print(f"checkin update OK: mirrored {len(differing) + len(src_only)} file(s), "
          f"deleted {len(vendored_only)} from the vendored tree ({branch} @ "
          f"{src_ref[:12]})")
    print("next: propagate template changes into instantiated files (INSTALL.md §2),")
    print("      update manifest entries, then run:  checkin.py record " + str(clone))
    return 0


def push(clone, force=False):
    # Guard 1: the vendored tree must be CURRENT with upstream. This mirror
    # DELETES any file the vendored tree lacks, so pushing from a tree that is
    # behind silently reverts whatever upstream gained. Symmetric to update()'s
    # guard: that one refuses to clobber unexported LOCAL work, this one
    # refuses to clobber unimported UPSTREAM work.
    #
    # Origin (2026-08-12): a session's vendored tree was behind by two upstream
    # merges; a plain push would have reverted two practices, and it was caught
    # only by a human reading `status` output. In the same session the *other*
    # direction then bit as well -- an `update --force`, passed specifically to
    # bypass update()'s guard, silently reverted three unexported additions
    # including this function. Both directions of this mirror destroy work;
    # both now warn, and --force means what it says.
    if not force:
        up = _manifest().get('upstream', {})
        # synced_from is what update() mirrored; fall back to commit for a
        # manifest written before that field existed.
        base = up.get('synced_from') or up.get('commit')
        # The branch this install is PINNED to, not the clone's configured
        # default. Same bug update() carried: every consumer tracks
        # precedent-beta-v01 while main is still BestPractice's default, so
        # this guard was comparing the vendored tree's base against the wrong
        # branch's head entirely -- refusing or allowing a push on evidence
        # about a branch the install does not follow.
        branch = _tracked_branch(clone)
        _git(clone, 'fetch', 'origin', branch)
        head = _rev_parse_quiet(clone, f'origin/{branch}')
        if head is None:
            sys.exit(f"checkin FAIL: {clone} has no origin/{branch} to compare "
                     f"against. This install records upstream.branch = "
                     f"{branch!r}; fetch that branch in the clone first.")
        if base and head != base:
            sys.exit(
                f"checkin FAIL: upstream origin/{branch} is at {head[:12]} but "
                f"the vendored tree was last mirrored from {base[:12]} — it is "
                "behind, and this mirror DELETES files it does not have, so it "
                "would revert upstream work. Run `checkin.py update` first (it "
                "refuses if that would clobber unexported local work — export "
                "that, or `update --force` and RE-APPLY your additions on top, "
                "keeping a copy first), then push. `--force` overrides if you "
                "are certain the vendored tree is the intended upstream state.")

    # Guard 2: the scrub gates every export of content toward the public repo.
    audit = HERE.parent / 'practice_audit.py'
    if subprocess.run([sys.executable, str(audit)]).returncode != 0:
        sys.exit("checkin FAIL: practice_audit (scrub) failed — nothing was copied")
    added, modified, deleted = _diff(clone)
    if not (added or modified or deleted):
        print("checkin push: vendored tree and clone already identical — nothing to do.")
        return 0
    for p in deleted:
        (clone / p).unlink()
    for p in added + modified:
        (clone / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(UPSTREAM / p, clone / p)
    print(f"checkin push OK: mirrored {len(added) + len(modified)} file(s), "
          f"deleted {len(deleted)} into {clone}")
    print("next: commit there on a branch, open the PR (review = second scrub line),")
    print("      merge, pull the default branch, then run:  checkin.py record " + str(clone))
    return 0



def _dep_git(*args):
    return subprocess.run(['git', '-C', str(ROOT)] + list(args),
                          capture_output=True, text=True).stdout


def _carry_check(clone, accept_loss):
    """No pending vendored addition may vanish across a check-in cycle.

    The failure this kills (2026-08-19, real): the vendored tree carried
    other threads' committed additions; a sync session hand-merged upstream's
    copy over them, push mirrored the lossy result, and record's
    tree-identical verification then STAMPED the loss as the new truth --
    detection was luck (the erased thread's session happened to be open).
    The carry-all-pending rule (INSTALL sec.4 step 1) states the obligation;
    this check enforces it at the chokepoint every cycle must pass through.

    Mechanism: every line ADDED in the dependent repo's committed default-
    branch vendored tree relative to the recorded base must be present in
    the landed upstream tree (same file, or anywhere in the tree to tolerate
    moves). A deliberate removal needs --accept-loss, which prints exactly
    what is being let go.
    """
    base = _manifest().get('upstream', {}).get('commit')
    if not base:
        return
    _dep_git('fetch', 'origin')
    # The DEPENDENT repo's own declared base branch first. Inferring it was
    # wrong twice over. `origin/HEAD` is unset on a great many clones --
    # every repo attached mid-session gets a --depth 1 --single-branch clone
    # without it, reproduced on a real consumer 2026-09-06 -- and the
    # fallback then named `origin/master`, a ref GitHub has not created by
    # default since 2020 and which does not exist in any consumer here. With
    # neither resolving, `ls-tree origin/master` errors, `names` comes back
    # EMPTY, and this loop inspects nothing and returns clean: a silent pass
    # from the one guard standing between a check-in cycle and the 2026-08-19
    # data loss this function's own docstring describes. A declared value
    # cannot go missing this way, and the inference fallback now at least
    # names a branch that exists.
    dep_branch = (_declared_base_branch(ROOT)
                  or _dep_git('symbolic-ref', '--short',
                              'refs/remotes/origin/HEAD').strip().rsplit('/', 1)[-1]
                  or 'main')
    prefix = UPSTREAM.relative_to(ROOT).as_posix()
    names = _dep_git('ls-tree', '-r', '--name-only', f'origin/{dep_branch}', prefix).split()
    landed_all = None
    lost = []
    for name in names:
        rel = name[len(prefix) + 1:]
        committed = _dep_git('show', f'origin/{dep_branch}:{name}')
        base_txt = subprocess.run(['git', '-C', str(clone), 'show', f'{base}:{rel}'],
                                  capture_output=True, text=True).stdout
        pending = set(committed.splitlines()) - set(base_txt.splitlines())
        pending = {l for l in pending if len(l.strip()) > 3}
        if not pending:
            continue
        landed = (clone / rel).read_text(encoding='utf-8', errors='replace') \
            if (clone / rel).exists() else ''
        missing = {l for l in pending if l not in landed.splitlines()}
        if missing:
            if landed_all is None:
                landed_all = '\n'.join((clone / f).read_text(encoding='utf-8', errors='replace')
                                        for f in _files(clone) if (clone / f).suffix
                                        in ('.md', '.py', '.sh', '.json', '.yml', '.template'))
            missing = {l for l in missing if l not in landed_all}
        if missing:
            lost.append((rel, sorted(missing)))
    if not lost:
        return
    for rel, lines in lost:
        print(f"  LOST from {rel}:")
        for l in lines[:8]:
            print(f"    | {l}")
        if len(lines) > 8:
            print(f"    | ... and {len(lines) - 8} more line(s)")
    if accept_loss:
        print(f"carry check: {sum(len(l) for _, l in lost)} pending line(s) NOT in the landed "
              f"tree -- accepted deliberately (--accept-loss).")
        return
    sys.exit("checkin FAIL: pending vendored additions are MISSING from the landed upstream "
             "tree -- a check-in dropped committed content (the 2026-08-19 failure). Carry "
             "them in another PR and re-record, or pass --accept-loss if the removal is "
             "deliberate; nothing recorded.")

def record(clone, note, accept_loss=False):
    # Neither a checkout nor a pull, for the same two reasons update() no
    # longer does either: the clone is a SOURCE the caller passed, not this
    # tool's to move (it silently relocated a session's checkout off
    # precedent-beta-v01 onto main on 2026-09-06 -- AGENTS.md's gotchas), and
    # the branch that matters is the one this install is pinned to, which is
    # not the clone's configured default. `fetch` updates remote-tracking
    # refs only; it never touches the working tree, HEAD, or a local branch.
    branch = _tracked_branch(clone)
    fetched = subprocess.run(['git', '-C', str(clone), 'fetch', 'origin', branch],
                             capture_output=True, text=True)
    if fetched.returncode != 0:
        print(f"NOTICE: could not fetch origin/{branch} in {clone} "
              f"({fetched.stderr.strip()}) -- recording against whatever that "
              f"clone already has for {branch}, which may be behind.")
    _carry_check(clone, accept_loss)
    added, modified, deleted = _diff(clone)
    if added or modified or deleted:
        for p in added + modified + deleted:
            print(f"  differs: {p}")
        sys.exit(f"checkin FAIL: clone {branch} is not identical to the vendored tree — "
                 f"merge/pull upstream first (or push the missing export); nothing recorded")
    head = _git(clone, 'rev-parse', 'HEAD')
    manifest = _manifest()
    old = manifest['upstream'].get('commit')
    manifest['upstream']['commit'] = head
    # record() has just verified the vendored tree is byte-identical to what
    # landed upstream -- which is STRONGER evidence of currency than the mirror
    # stamp update() writes. So advance synced_from too, or push()'s currency
    # guard reports a false positive on the very next export: the tree is
    # provably current while the stamp still points at the pre-merge commit.
    # (Found immediately after the guard shipped, by running the normal cycle
    # through to the end -- a reminder that a new gate is not done until the
    # whole loop has been walked with it in place.)
    manifest['upstream']['synced_from'] = head
    manifest['upstream']['_note'] = (
        f"commit = upstream hash last synced ({note or 'check-in'}, "
        f"recorded {datetime.date.today().isoformat()}; verified tree-identical).")
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8')
    print(f"checkin record OK: upstream.commit {old} -> {head}")
    print("next: commit process/manifest.json in this repo.")
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == 'fresh':
        return fresh()
    if args and args[0] == 'not-vendored':
        # Measures the NOT_VENDORED share against the tree in front of you,
        # so no document or comment has to freeze the numbers. Reports which
        # tree it measured, because the answer differs between this repo and
        # a consumer's process/upstream/ copy.
        base = pathlib.Path(args[1]) if len(args) > 1 else (
            UPSTREAM if UPSTREAM.is_dir() else ROOT)
        excluded, total, nbytes = not_vendored_share(base)
        if not total:
            print(f"checkin not-vendored: nothing to measure under {base} -- "
                  f"no files found, so this figure is not zero, it is unknown")
            return 1
        names = ', '.join(sorted(NOT_VENDORED)) or '(nothing excluded)'
        print(f"tree measured:  {base}")
        print(f"excluded dirs:  {names}")
        # Bytes, explicitly labelled: `du` reports DISK BLOCKS, and 557 small
        # files round up to roughly four times their real size at a 4K block.
        # A session quoting "2.4 MB" from `du` next to "557 files" from here
        # is quoting two different quantities as if they were one -- practice
        # `one-formatter-per-quantity`, learned the same day this was written.
        print(f"excluded files: {excluded} of {total} "
              f"({excluded / total * 100:.0f}%), "
              f"{nbytes / 1e6:.1f} MB of content "
              f"(byte sum, not `du` disk usage -- `du` counts 4K blocks and "
              f"reports several times this for many small files)")
        print("practices/ is never excluded -- this is measurement fixtures, "
              "not rules.")
        return 0
    if len(args) < 2 or args[0] not in ('status', 'update', 'push', 'record'):
        sys.exit(__doc__)
    clone = _clone_or_die(args[1])
    if args[0] == 'status':
        return status(clone)
    if args[0] == 'update':
        return update(clone, force='--force' in args)
    if args[0] == 'push':
        return push(clone, force='--force' in args)
    note = args[args.index('--note') + 1] if '--note' in args else ''
    return record(clone, note, accept_loss='--accept-loss' in sys.argv)


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/HOW_TO_USE_THIS_TECHNICAL.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())

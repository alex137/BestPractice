#!/usr/bin/env python3
"""precedent_materialize.py — bridges precedent_resolve.py's multi-source
resolution to the single-tree CONTENT tools (build_views.py,
precedent_paths.py, precedent_gate.py, precedent_check.py), none of which
understand more than one local practices/ directory.

spec/PHASE5_BRIEF.md named this gap explicitly: "precedent_resolve.py is
the ONLY multi-source-aware tool in this codebase... none of them accept
multiple source directories the way precedent_resolve.py does," and named
"materialize a merged tree" as the fastest of two shapes worth trying —
"a short script that calls precedent_resolve.py's own resolve() and writes
each winning practice's file into one local practices/-shaped directory,
then points build_views.py/precedent_paths.py/precedent_gate.py/
precedent_check.py at that directory unchanged."

THIS TOOL WRITES WHAT A SOURCE PUBLISHES, NOT THE ENGINE: the resolved
practices/ tree, each source's own tools/checks/ (a checked_by claim has
nothing behind it if only practices/ is copied — engine-plus-host-shims: the
engine travels with what it enforces), and since 2026-09-12 each source's
declared HARNESS ADAPTERS — the `bootstrap/*.sh` scripts its own practices
tell every consuming repo to wire into `.claude/hooks/`, which until then
travelled by hand-copy and so went silently stale (see the "Harness adapters"
section below for the two measured incidents and for what deliberately does
NOT travel). It does NOT vendor the engine scripts themselves
(build_views.py, precedent_paths.py, etc.) — that half is
already a solved, existing concern (INSTALL.md's vendoring model, or
cloning/copying this repo's tools/ into a consumer repo), unrelated to the
content-merging gap this tool closes.

THE HONEST COST, named rather than hidden (generated-artifact-provenance):
the materialized tree is a DERIVED ARTIFACT that needs regenerating on
every source update. A MANIFEST.json is written alongside it recording
what produced it and when, so drift is visible rather than silent — this
tool never claims the output is anything but a snapshot.

A filename collision between two sources' tools/checks/ scripts (or
tests/) is refused rather than silently overwritten — pick one, or rename
one of them; the resolver's own "two same-level practices cannot both
claim one slug" refusal is the same discipline applied here.

Usage:
  precedent_materialize.py --out DIR [--repo REPO] [--user-config PATH]
Exit: 0 on a clean materialization, 1 on a resolve conflict, an over-budget
resident set, a checks/ filename collision, or a harness adapter declaration
that is malformed or collides on its destination.
"""
import datetime
import hashlib
import os
import re
import subprocess
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr  # noqa: E402

# practice: one-formatter-per-quantity -- every moment in time this project
# writes down comes from ONE module, in the person's zone, carrying its
# offset. Never a bare datetime.date.today(): that is the container's UTC.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # noqa: E402



class MaterializeError(Exception):
    pass


def _self_referential_sources(sources, out_dir):
    """A source whose declared `path` resolves to THIS run's own `out_dir`
    is not a separate tree materialize() can safely delete-and-rewrite: it
    is someone's hand-authored content, with no other copy anywhere.
    precedent_resolve.py's load_config now REQUIRES a repo-local source's
    path to be exactly "local" (2026-09-04), which rules out the most
    common way this used to happen -- a repo-local source declared at the
    bare root, colliding with a materialize run pointed at that same root
    -- before it ever reaches this function. This guard stays, unaffected,
    as the backstop for every OTHER level: a repo may legitimately declare
    universal or team at `path: "."` (this repo's own self-hosted
    precedent.json does exactly that), and load_config has no reason to
    forbid that on its own -- only a materialize() run whose --out happens
    to equal that same path makes it unsafe, which is a fact about the
    materialize INVOCATION, not the source declaration, and so has to be
    caught here rather than at resolve time.

    Two real, reproduced bugs came from allowing this combination through
    to materialize() anyway (2026-09-03 deep-check audit): (1) the moment a
    higher-precedence source shadows a slug this source also holds, ITS
    file is deleted and the winner's content is written over it, with no
    trace left that anything different was ever there -- the earlier
    "read every resolved practice into memory before deleting" fix only
    protects the file of the practice that WINS, not one that loses right
    where it lives; (2) once materialize() has run once, its own output
    (a check script or practice file belonging to a DIFFERENT source)
    sits physically inside this source's declared tree, so the NEXT run's
    resolve()/`_plan_checks` reads it back as if this source had authored
    it -- corrupting the resolved set itself, not just materialize()'s
    output, and not something a clean run today rules out for the run
    after it. Both are structural to source == destination, not fixable
    by reading harder before deleting -- refused unconditionally, whether
    or not today's resolved set happens to collide."""
    out_dir = pathlib.Path(out_dir).resolve()
    return [s for s in sources if pathlib.Path(s['path']).resolve() == out_dir]


# --------------------------------------------------------------------------
# Link rewriting
# --------------------------------------------------------------------------
#
# A practice file's relative links are written relative to ITS OWN
# directory in ITS OWN repository. Copied verbatim into a consuming repo's
# practices/, they point at nothing: `../tools/very_deep_check.py` and
# `../spec/ATTENTION_CEILING.md` are real paths in Precedent and absent
# from every repo that installs it. So every consuming repo was shipping
# ~60 practice files whose internal links 404 -- and the practice files are
# the product. precedent-team-repo-maintenance' own light check had already had
# to exempt materialized practices/ from its broken-link scan to stay
# green, which is the workaround this replaces.
#
# Two cases, decided by where the target actually lands:
#
#   inside the consuming repo   -- a repo-local source, whose files are
#                                  right there. Recompute the relative path
#                                  from the new location. (This half is a
#                                  bug in the same family and the opposite
#                                  direction: a repo-local practice at
#                                  local/practices/x.md writing `../tools/`
#                                  means local/tools/, which is NOT what
#                                  the same link means once the file is at
#                                  practices/x.md.)
#   anywhere else               -- another repository. Only an absolute URL
#                                  can reach it, so link the source repo's
#                                  own web view at the branch the source
#                                  checkout is actually on.
#
# A sibling practice link (`[some-slug](some-slug.md)`, the catalogue's own
# citation form) already resolves in the materialized tree and is left
# exactly as it is -- checked by resolution, not by pattern, so nothing has
# to stay in sync with the citation convention.
_LINK_RE = re.compile(r'(\]\()([^)\s]+?)(\))')


def _remote_web_base(repo_root):
    """`https://host/owner/repo/blob/<commit>` for a source checkout, or
    None when that cannot be established (no git, no `origin`, an unborn
    HEAD). None means "leave the links alone": a wrong URL is worse than a
    relative path that at least says what it was reaching for.

    THE COMMIT, NOT THE BRANCH. A materialized tree is a snapshot -- the
    manifest beside it says so -- and a commit URL matches that exactly:
    it shows the content the snapshot was taken from, and it cannot rot,
    because GitHub keeps a blob reachable by SHA long after any branch
    pointing at it is deleted. The first version of this used the source
    checkout's current branch and promptly wrote a feature branch nobody
    else would ever have into every link of every materialized practice.
    A default-branch URL is no better here: the content a consumer just
    resolved may only exist on a release branch, and would 404 on the
    default one."""
    def git(*args):
        r = subprocess.run(['git', '-C', str(repo_root), *args],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ''

    url = git('remote', 'get-url', 'origin')
    # --verify --quiet: a plain `rev-parse HEAD` prints "HEAD" back on an
    # unborn HEAD, and that string would be carried straight into every
    # URL (this repo's own gotchas section records the same trap costing a
    # continuous-integration run).
    commit = git('rev-parse', '--verify', '--quiet', 'HEAD')
    if not url or not commit:
        return None
    url = re.sub(r'^git@([^:]+):', r'https://\1/', url)
    url = re.sub(r'\.git$', '', url).rstrip('/')
    if not url.startswith('http'):
        return None
    return f'{url}/blob/{commit}'


# Directories materialize() owns: it deletes and rewrites both on every
# run, so what is sitting in them right now is last run's output, never
# evidence about this one.
_MANAGED_DIRS = ('practices/', 'tools/checks/')


def _rewrite_links(data, source_file, out_dir, sibling_slugs=(), planned_out=(),
                   may_name_source_repo=True):
    """Repoint one practice file's relative links for its new home.

    Returns the rewritten bytes. Any link this cannot place confidently is
    left untouched -- the output is a copy of somebody's content, and
    silently mangling it would be a worse failure than the dead link this
    fixes.

    `sibling_slugs` is every slug THIS materialize run is writing, and it
    has to be passed rather than discovered on disk: practices are written
    in slug order, so at the moment an early one is rewritten a later
    sibling it cites does not exist yet. Checking the filesystem alone made
    a sibling citation survive or get turned into a URL depending on
    alphabetical order, which is the kind of bug that looks like it works
    until somebody adds a practice.

    `planned_out` is every path this run will write, relative to out_dir,
    and it is the same argument for a wider case. A practice that cites
    its own check script -- `../tools/checks/check_x.py`, the single most
    common cross-reference a practice makes -- was asking the filesystem,
    and the answer was always no: materialize() empties tools/checks/
    before it writes practices/ and only fills it afterwards. So the link
    got "placed" as an absolute URL into the source repository, which for
    a team or individual source is a PRIVATE repository, replacing a
    relative link that would have worked perfectly once the run finished.
    Observed in a real four-source consumer, 2026-09-06. Asking the plan
    instead of the disk also makes a dry run and a real run agree by
    construction, which is what drift() needs to be trustworthy.

    `may_name_source_repo` is false for an INDIVIDUAL source, and that is a
    privacy boundary rather than a preference. precedent_resolve.load_config
    refuses an individual source declared in a shared repo's tracked config
    by name: a person's own set is named only in their user-level config, so
    that its existence and location cannot leak to everyone who can read the
    repo. Minting `https://github.com/<owner>/<private repo>/blob/...` into
    a tracked practices/ tree hands over exactly what that refusal protects,
    and a consuming repo can be public -- the project's own prior notes repository is. Caught
    2026-09-06 by a consuming repo's own private-repo-scrub check, on a link
    this rewriter had just created. The link is left as it was written
    instead: a relative link that does not resolve is a smaller failure than
    a disclosure that cannot be taken back."""
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return data
    src_dir = pathlib.Path(source_file).resolve().parent
    dest_dir = (pathlib.Path(out_dir) / 'practices').resolve()
    out_root = pathlib.Path(out_dir).resolve()
    web_base = None
    web_root = None

    def sub(m):
        nonlocal web_base, web_root
        open_paren, target, close = m.groups()
        if target.startswith(('http://', 'https://', 'mailto:', '#')):
            return m.group(0)
        bare, _, anchor = target.partition('#')
        if not bare:
            return m.group(0)
        if bare[:-3] in sibling_slugs and bare.endswith('.md') and '/' not in bare:
            return m.group(0)            # a sibling this run is also writing
        cand = dest_dir / bare
        try:
            rel_out = cand.resolve().relative_to(out_root).as_posix()
        except ValueError:
            rel_out = None               # points outside the consuming repo
        if rel_out is not None and rel_out in planned_out:
            return m.group(0)            # this run writes exactly that file
        if cand.exists() and not (rel_out or '').startswith(_MANAGED_DIRS):
            return m.group(0)            # already resolves where it lands
        resolved = (src_dir / bare).resolve()
        try:
            src_rel_out = resolved.relative_to(out_root).as_posix()
        except ValueError:
            src_rel_out = None
        # "Broken at the source" has to ask the plan too, for the same
        # reason: a repo-local source's own practice citing its own check
        # script resolves into tools/checks/, which this run emptied a
        # moment ago. On disk that reads as a broken link nobody should
        # touch, so the citation was left pointing one directory too far
        # up -- correct from local/practices/, dead from practices/.
        if not resolved.exists() and src_rel_out not in planned_out:
            return m.group(0)            # broken at the source; not ours to invent
        if resolved.is_relative_to(out_root):
            new = os.path.relpath(resolved, dest_dir)
        else:
            if not may_name_source_repo:
                return m.group(0)        # naming it is the disclosure
            if web_root is None:
                web_root = _git_toplevel(src_dir) or False
                web_base = _remote_web_base(web_root) if web_root else None
            if not web_base:
                return m.group(0)
            try:
                rel = resolved.relative_to(web_root)
            except ValueError:
                return m.group(0)
            new = f'{web_base}/{rel.as_posix()}'
        return f'{open_paren}{new}{("#" + anchor) if anchor else ""}{close}'

    return _LINK_RE.sub(sub, text).encode('utf-8')


def _git_toplevel(start):
    r = subprocess.run(['git', '-C', str(start), 'rev-parse', '--show-toplevel'],
                       capture_output=True, text=True)
    return pathlib.Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


# The test driver this tool generates rather than copies -- see _plan_checks'
# docstring for why. Recorded in MANIFEST.json like every other materialized
# file, under a source name no real source can collide with: a consuming
# repo's own orphan detection reads that manifest to tell a legitimately
# materialized file from a hand-dropped one, and an unrecorded file would
# read as hand-dropped.
#
# Deliberately NOT carrying a `practice:` citation, though this code exists to
# satisfy one: the deep-check rule that requires the driver is a TEAM-level
# practice, and this repo's catalogue is the universal one, so the slug does
# not resolve here and code-cites-practice correctly reads the citation as a
# dangling reference. The citation form has no way to say "a practice from a
# source this repo does not carry", so the reason is given in prose instead.
RUN_ALL_NAME = 'run_all.sh'
GENERATED_SOURCE = '(generated)'
# What a source's OWN run_all.sh must carry to show its author knows this tool
# replaces it. Checked, never written: this tool has no business editing a
# source's tree, and a marker inserted for an author would prove nothing about
# whether anyone understood the replacement. See _plan_checks' docstring.
LOCAL_DRIVER_MARKER = 'LOCAL DRIVER -- not shipped to consumers'
RUN_ALL_SCRIPT = """#!/bin/bash
# GENERATED FILE -- do not hand-edit. Written by tools/precedent_materialize.py
# on every sync; any edit here is overwritten without warning.
#
# Runs every materialized check's two-direction test. The glob is the point:
# this driver runs whatever tests this repo actually materialized, which is
# why it is generated here rather than copied from any one practice source.
set -uo pipefail
cd "$(dirname "$0")"
status=0
for t in test_*.sh; do
  # A repo that materialized no tests leaves the glob unexpanded; without
  # this the driver would try to run a file literally named test_*.sh and
  # report a failure that is really an empty set.
  [ -e "$t" ] || continue
  echo "--- $t ---"
  if ! bash "$t"; then
    status=1
  fi
done
exit $status
"""

def _plan_checks(sources, res=None):
    """Read every source's per-check tools/checks/check_*.py and
    tools/checks/tests/test_*.sh INTO MEMORY, refusing a same-name
    collision across different sources rather than letting the last one
    silently win. Returns a write plan (rel_label, filename, source_name,
    bytes) and does not touch the filesystem at all -- see materialize()
    for why reading has to fully finish before anything is deleted.

    `res` is the resolution this materialize is writing. When given, a
    check script no resolved practice CLAIMS via `checked_by` is left
    behind rather than copied: a script whose practice is retired, or
    lost a slug to a higher-precedence source, has nothing left to
    enforce here. Found on the first real run against
    precedent-team-repo-maintenance, whose `deep-check` practice is retired --
    its `check_deep_check.py` was still copied into the consuming repo,
    where it registered under its own filename (no practice to name it),
    reported "not in force", and counted as an unexplained file against
    the consuming repo's own materialized-tree audit.

    Deliberately narrower than 'every file in tools/checks/': a source's
    own tools/checks/tests/run_all.sh (found colliding on the very first
    real run of this tool, both private sets carry one) is a per-repo test
    DRIVER, not a per-check test a `checked_by` claim could ever name --
    merging it would be a false collision over a file nothing actually
    needs merged. It is not REPORTED as a skip, though, because it is
    not dropped -- it is REPLACED by the generated driver below. A routine
    line saying a source's copy "was not vendored", printed on every sync
    for every source that ships one, forever, stated the true half and
    invited a false second half: "so this repo has no driver." Two written
    records ended up contradicting each other on that plain fact, and
    settling it took a cross-repo investigation against this file. The
    line also named no action anyone could take, since the skip is correct
    and permanent. Provenance is recorded where a reader can consult it
    instead -- the generated file's own `GENERATED FILE -- do not
    hand-edit` header, and its `(generated)` entry in MANIFEST.json -- so
    silence about the driver now correctly means nothing was dropped, and
    the "not a per-check file, not vendored" line keeps its honest
    meaning: those files really were dropped, and really are gone.

    What IS reported about the driver is actionable, and goes silent once
    acted on: a source whose own run_all.sh does not DECLARE itself local
    -- by carrying LOCAL_DRIVER_MARKER somewhere in the file -- gets a
    stderr warning naming that source and the line to add. Here is the
    right home for that check because this function reads every source's
    driver on every sync, so one place covers every source of every
    consumer, present and future; a per-source check script would reach
    only its own set. It warns rather than raising: a MaterializeError
    here would break every consumer's sync the moment the engine was
    upgraded, over a defect in a comment.

    The driver is GENERATED instead, at the end of this function. Skipping
    the sources' copies is right; leaving the consumer without one was not.
    The `deep-check` practice requires tools/checks/tests/run_all.sh to
    exist -- so before 2026-09-06 that practice was unsatisfiable in every
    consuming repo, and its far more useful half (does each check_*.py have
    a test? is any test left behind after its check was deleted?) never ran
    at all, because the check returns early on the missing file. Supplying
    it by hand does not work either: tools/checks/ is this function's own
    output, wiped on every sync, and routing the file through a repo-local
    source hits this same filename rule.

    Generating rather than copying is not a workaround, it is the more
    honest description. The driver carries no source-specific content --
    it globs test_*.sh in its own directory, so it must run whatever THIS
    repo materialized, which is a property of the output, not of any one
    source. That is also why the collision disappears: a generated file is
    claimed by nobody, so there is no winner to pick."""
    owner_of = {}   # 'rel_label/filename' -> source name that already claimed it
    plan, skipped, orphaned, undeclared = [], [], [], []
    claimed_names = None
    if res is not None:
        claimed_names = set()
        for practice in res['practices'].values():
            cb = (practice.get('fm', {}).get('checked_by') or '').strip().strip('"').strip("'")
            if cb.endswith('.py') and '/checks/' in cb:
                stem = pathlib.PurePath(cb).stem
                claimed_names.add(f'{stem}.py')
                claimed_names.add(f'{stem.replace("check_", "test_", 1)}.sh')

    def claim(src_file, rel_label, source_name):
        key = f'{rel_label}/{src_file.name}'
        prior = owner_of.get(key)
        if prior is not None and prior != source_name:
            raise MaterializeError(
                f"tools/checks/{key} exists in both {prior!r} and "
                f"{source_name!r} -- a filename collision across sources. "
                f"Pick one, or rename one of them before materializing.")
        owner_of[key] = source_name
        plan.append((rel_label, src_file.name, source_name, src_file.read_bytes()))

    for s in sources:
        src_checks = pathlib.Path(s['path']) / 'tools' / 'checks'
        if not src_checks.is_dir():
            continue
        for f in sorted(src_checks.glob('*.py')):
            if not f.name.startswith('check_'):
                skipped.append(f'tools/checks/{f.name} ({s["name"]})')
            elif claimed_names is not None and f.name not in claimed_names:
                orphaned.append(f'tools/checks/{f.name} ({s["name"]})')
            else:
                claim(f, 'checks', s['name'])
        src_tests = src_checks / 'tests'
        if src_tests.is_dir():
            for f in sorted(src_tests.glob('*.sh')):
                if f.name == RUN_ALL_NAME:
                    # Replaced, not dropped -- so not a `skipped` entry. The
                    # generated driver is appended to the plan below.
                    if LOCAL_DRIVER_MARKER not in f.read_bytes().decode(
                            'utf-8', 'replace'):
                        undeclared.append(f'{s["name"]} ({f})')
                elif not f.name.startswith('test_'):
                    skipped.append(f'tools/checks/tests/{f.name} ({s["name"]})')
                elif claimed_names is not None and f.name not in claimed_names:
                    orphaned.append(f'tools/checks/tests/{f.name} ({s["name"]})')
                else:
                    claim(f, 'checks/tests', s['name'])
    if skipped:
        print(f"precedent_materialize: not a per-check file, not vendored: "
              + ', '.join(skipped), file=sys.stderr)
    if orphaned:
        print(f"precedent_materialize: no practice in force here claims these, "
              f"not vendored: " + ', '.join(orphaned), file=sys.stderr)
    if undeclared:
        print(f"precedent_materialize: replaced here by the generated "
              f"driver, and the source's own tools/checks/tests/"
              f"{RUN_ALL_NAME} does not say so -- add a header line "
              f"containing \"{LOCAL_DRIVER_MARKER}\" to each of: "
              + ', '.join(undeclared), file=sys.stderr)
    plan.append(('checks/tests', RUN_ALL_NAME, GENERATED_SOURCE,
                 RUN_ALL_SCRIPT.encode('utf-8')))
    return plan


# --------------------------------------------------------------------------
# Harness adapters
# --------------------------------------------------------------------------
#
# practice: engine-plus-host-shims -- the engine travels with what it
# enforces, and a harness adapter is the host shim half of exactly that.
# practice: registry-source-of-truth -- the declaration lives in the ONE
# machine-readable registry a source already has, and drift() is the audit
# that detects the disagreement.
# practice: checkable-gets-checked -- "the settings wiring does not travel"
# is a refusal below, not a paragraph anyone has to remember.
#
# A practice source publishes three kinds of thing, and until 2026-09-12 only
# two of them travelled mechanically: the engine, by
# precedent_vendor_engine.py with a sha256 per file, so a hand-edit is refused
# as drift; and practices plus their checks, by this tool. The third is the
# HARNESS ADAPTERS a source's own practices tell every consuming repo to
# install -- `bootstrap/freshness-guard.sh` copied into
# `.claude/hooks/freshness-guard.sh`, and the same for the commit-identity and
# session-start hooks. Those travelled by somebody remembering, per each
# practice's own Install section. So a repo carrying a copy went silently
# behind the moment the source's script changed: nothing announced the change,
# and nothing could report which repos were stale.
#
# Twice in two days, measured rather than imagined. A consuming repo's check
# produced two findings against its freshness guard; both had already been
# fixed in the source set, so they were true statements about that repo's own
# stale copy and were briefed as open defects in the source, and a session
# spent its first hour disproving them. Separately, the same repo's
# `commit-identity.sh` sat about five kilobytes behind its source -- a hundred
# lines present canonically and absent there, no local adaptation, just old --
# with its own check passing, because every check it had was reading the stale
# copy.
#
# WHY THIS TOOL. The argument is the one already in this file's docstring, one
# step further out: a checked_by claim has nothing behind it if only
# practices/ is copied. An adapter is the same shape. `fresh-before-write`'s
# Rule IS an adapter -- "every project I work in gets both halves of
# bootstrap/freshness-guard.sh wired into its own .claude/settings.json" -- and
# a materialized practices/fresh-before-write.md sitting beside a months-old
# .claude/hooks/freshness-guard.sh is exactly the failure that sentence already
# rejects for checks. This tool is also the only one that runs on every
# consumer's sync, already resolves the sources, and already writes the
# MANIFEST.json that makes a derived file a declared artifact rather than an
# untracked hand-copy that a consumer's own orphan detection reads as
# hand-dropped. A sibling tool would have had to duplicate all three.
#
# WHAT DOES NOT TRAVEL, AND IS REFUSED RATHER THAN DOCUMENTED: the settings
# wiring. A source's `bootstrap/*.snippet.json` carries `main` as the base
# branch and each consuming repo substitutes its own, so the install step
# stays "copy the script; merge the snippet by hand, replacing the base
# branch". Copying a consumer's `.claude/settings.json` would silently repoint
# its base branch -- the one inference the freshness guard refuses to make for
# itself, since a wrong base branch is how a guard reports everything fine
# about a checkout cut from a stale base. A declared destination whose
# basename is settings.json or settings.local.json is refused below, because a
# rule that only the prose enforces is a rule somebody eventually types past
# (checkable-gets-checked).
#
# HOW A SOURCE DECLARES THEM -- in its own precedent.json, which is the
# registry it already has (registry-source-of-truth: state lives in ONE
# machine-readable registry). A second bootstrap/ADAPTERS.json would be a
# second place to look and a second format to keep in step, for a list that is
# three lines long:
#
#   "adapters": [
#     {"from": "bootstrap/freshness-guard.sh",
#      "to":   ".claude/hooks/freshness-guard.sh"}
#   ]
#
# A CONSUMER THAT EDITED ITS COPY is overwritten, deliberately, and told. The
# adaptation point for an adapter is the settings wiring, which does not
# travel; the script itself is a derived artifact like every other file this
# tool writes, and a consumer holding a private edit of it is the state this
# whole mechanism exists to end. What is NOT acceptable is doing that
# silently, so the first replacement of content this tree never recorded as
# materialized -- a hand-copy being adopted, or a local edit being reverted --
# prints a notice naming the file, while an ordinary update from a source that
# moved stays quiet. Afterwards the manifest hash makes a later hand-edit a
# drift() finding, which is the audit half the same change would otherwise
# still be owed.
ADAPTER_DECL_KEY = 'adapters'
# Refused as an adapter destination: see "WHAT DOES NOT TRAVEL" above.
_RESERVED_ADAPTER_BASENAMES = ('settings.json', 'settings.local.json')
# Refused for the plainer reason that another mechanism owns the file and
# would overwrite it right back, or has already deleted it this run.
_RESERVED_ADAPTER_PATHS = ('MANIFEST.json', 'AGENTS.md', 'precedent.json')


def _adapter_dest(to, cfg, i):
    """-> the validated destination as a relative POSIX string, or raises.

    Every refusal here is about a path that would reach outside what a source
    may write in a consumer, or into a file some other mechanism owns."""
    def bad(why):
        return MaterializeError(
            f"{cfg}: adapters[{i}]'s \"to\" ({to!r}) {why}. An adapter "
            f"destination is a relative path inside the consuming repo, "
            f"naming the file the source's own Install step would have had "
            f"someone copy by hand.")
    if not to or to != to.strip():
        raise bad('is empty or carries surrounding whitespace')
    p = pathlib.PurePosixPath(to)
    if to.startswith('/') or p.is_absolute():
        raise bad('is an absolute path')
    if '..' in p.parts:
        raise bad('walks above the consuming repo with ".."')
    if p.name in _RESERVED_ADAPTER_BASENAMES:
        raise bad("is the harness settings file, which deliberately does not "
                  "travel -- each consuming repo substitutes its own base "
                  "branch there, and copying it would silently repoint that")
    norm = p.as_posix()
    if norm in _RESERVED_ADAPTER_PATHS:
        raise bad('is a file this tool or build_views.py writes itself')
    if norm.startswith(_MANAGED_DIRS):
        raise bad('lands in a directory materialize() deletes and rewrites on '
                  'every run, so the file would not survive its own sync')
    return norm


def _plan_adapters(sources):
    """Read every source's declared harness adapters INTO MEMORY, refusing a
    destination collision across sources rather than letting the last one
    silently win. Returns a write plan (dest, source_name, bytes, executable)
    and touches nothing -- same contract as _plan_checks, and for the same
    reason materialize() spells out: reading has to finish before anything is
    deleted or written.

    A declared adapter whose file is not in the source tree WARNS and is
    skipped rather than raising. The file is in another repository, and the
    ordinary cause is a stale source clone -- refusing there would break
    every consumer's sync over a state a `git pull` in a directory the
    consumer does not own would fix. A malformed DECLARATION does raise: that
    is somebody's edit to a config file, made just now, and the whole point
    of the refusal is that they hear about it before a consumer does."""
    owner_of = {}
    plan, missing = [], []
    for s in sources:
        root = pathlib.Path(s['path'])
        cfg = root / 'precedent.json'
        if not cfg.is_file():
            continue
        try:
            data = json.loads(cfg.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise MaterializeError(
                f"{cfg} is not readable JSON ({e}), so this run cannot tell "
                f"whether the source {s['name']!r} publishes harness adapters "
                f"or not. Fix that file in that source before syncing.")
        if not isinstance(data, dict):
            raise MaterializeError(f"{cfg} is not a JSON object.")
        decl = data.get(ADAPTER_DECL_KEY)
        if decl is None:
            continue
        if not isinstance(decl, list):
            raise MaterializeError(
                f"{cfg}: \"{ADAPTER_DECL_KEY}\" must be a list of "
                f"{{\"from\": ..., \"to\": ...}} objects.")
        for i, entry in enumerate(decl):
            if (not isinstance(entry, dict)
                    or not isinstance(entry.get('from'), str)
                    or not isinstance(entry.get('to'), str)):
                raise MaterializeError(
                    f"{cfg}: adapters[{i}] must be an object with a string "
                    f"\"from\" (the file in this source) and a string "
                    f"\"to\" (where it is installed in a consuming repo).")
            dest = _adapter_dest(entry['to'], cfg, i)
            src_file = root / entry['from']
            try:
                src_file.resolve().relative_to(root.resolve())
            except ValueError:
                raise MaterializeError(
                    f"{cfg}: adapters[{i}]'s \"from\" ({entry['from']!r}) "
                    f"resolves outside the source tree at {root} -- a source "
                    f"publishes its own files.")
            prior = owner_of.get(dest)
            if prior is not None:
                raise MaterializeError(
                    f"{dest} is declared as a harness adapter destination by "
                    f"both {prior!r} and {s['name']!r} -- a destination "
                    f"collision. Pick one, or change one of their declared "
                    f"\"to\" paths before materializing.")
            owner_of[dest] = s['name']
            if not src_file.is_file():
                missing.append(f'{entry["from"]} -> {dest} ({s["name"]})')
                continue
            plan.append((dest, s['name'], src_file.read_bytes(),
                         os.access(src_file, os.X_OK)))
    if missing:
        print("precedent_materialize: declared harness adapter(s) whose file "
              "is not in the source tree, NOT installed -- the source names a "
              "file it does not ship, or its clone here is stale: "
              + ', '.join(missing), file=sys.stderr)
    return plan


def _prior_adapter_hashes(out_dir):
    """{destination: sha256_16} from the manifest this tree ALREADY carries --
    what the last sync says it installed, which is what separates an ordinary
    update from replacing something nobody recorded. An unreadable or absent
    manifest answers `{}`, which errs toward printing the notice."""
    mf = pathlib.Path(out_dir) / 'MANIFEST.json'
    if not mf.is_file():
        return {}
    try:
        data = json.loads(mf.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {a['path']: a.get('sha256_16') for a in data.get('adapters', [])
            if isinstance(a, dict) and isinstance(a.get('path'), str)}


def materialize(sources, res, out_dir, dry_run=False, withheld=None):
    """Reads every resolved practice file and every source's check/test
    file INTO MEMORY before deleting or writing anything in out_dir.

    WHY THE READ HAS TO FINISH BEFORE ANY DELETE. A repo-local source's
    own `path` can be -- and, per its whole point, often is -- the SAME
    repo this tool is materializing INTO: a consuming repo's own
    hand-authored practices/ is both a real source (its repo-local level)
    and the directory this tool's output also lands in. The original
    version of this function did `shutil.rmtree(practices_dir)` first and
    only THEN read each resolved practice's file to copy it -- which, for
    any slug repo-local contributed, deleted the file and then tried to
    read it from the path just deleted. Reading everything up front makes
    the delete/write order irrelevant to correctness: by the time
    anything is removed, every byte this function still needs is already
    held in memory, whether or not its original path just got wiped.

    dry_run computes the identical plan -- same out_dir, so the link
    rewriting resolves to the same paths -- and touches nothing on disk.
    It exists because --check has to be able to answer "is the committed
    tree current?" without being the thing that changes it; see drift()."""
    out_dir = pathlib.Path(out_dir)
    self_referential = _self_referential_sources(sources, out_dir)
    if self_referential:
        names = ', '.join(f"{s['name']!r} ({s['level']})" for s in self_referential)
        raise MaterializeError(
            f"{names} declares its `path` as this run's --out directory "
            f"itself ({out_dir.resolve()}). materialize() deletes and "
            f"rewrites practices/ and tools/checks/ in --out on every run; "
            f"a source living at that exact path has no other copy of its "
            f"own hand-authored content and will eventually be destroyed "
            f"or corrupted by a future run even if this one is clean (a "
            f"slug it loses to a higher-precedence source is deleted for "
            f"good; a file materialize() itself writes for a DIFFERENT "
            f"source is read back on the next run as if this source had "
            f"authored it). Move {names}'s declared `path` to a "
            f"subdirectory (a repo-local source must use \"local\", "
            f"holding local/practices/ -- see PRACTICE_ENGINE_PLAN.md's "
            f"\"Source\" section; a non-repo-local source may pick any "
            f"other subdirectory) so its tree and materialize()'s output "
            f"are physically separate.")

    practices_dir = out_dir / 'practices'
    checks_dir = out_dir / 'tools' / 'checks'

    practice_plan = {slug: (practice, pathlib.Path(practice['file']).read_bytes())
                      for slug, practice in res['practices'].items()}
    checks_plan = _plan_checks(sources, res)   # raises MaterializeError before any write
    adapters_plan = _plan_adapters(sources)    # same -- reads, never writes

    if not dry_run:
        if practices_dir.exists():
            shutil.rmtree(practices_dir)
        if checks_dir.exists():
            shutil.rmtree(checks_dir)
        practices_dir.mkdir(parents=True)

    written = []
    all_slugs = set(practice_plan)
    planned_out = {f'practices/{slug}.md' for slug in practice_plan}
    planned_out.update(f'tools/{rel_label}/{filename}'
                       for rel_label, filename, _src, _data in checks_plan)
    for slug, (practice, data) in sorted(practice_plan.items()):
        dest = practices_dir / f'{slug}.md'
        # Rewritten, not copied: a practice's relative links are written
        # relative to its own repository and point at nothing here. See
        # _rewrite_links. The recorded hash is of what was WRITTEN, so the
        # manifest still describes the file that exists; `source_sha256_16`
        # keeps the untouched original's hash beside it, so a later
        # comparison can tell a rewrite from a drift.
        placed = _rewrite_links(data, practice['file'], out_dir,
                                sibling_slugs=all_slugs,
                                planned_out=planned_out,
                                may_name_source_repo=practice['level'] != 'individual')
        if not dry_run:
            dest.write_bytes(placed)
        written.append({'slug': slug, 'level': practice['level'],
                         'source': practice['source'],
                         'sha256_16': hashlib.sha256(placed).hexdigest()[:16],
                         'source_sha256_16': hashlib.sha256(data).hexdigest()[:16],
                         'links_rewritten': placed != data})

    checks_written = []
    for rel_label, filename, source_name, data in checks_plan:
        dest_dir = checks_dir if rel_label == 'checks' else checks_dir / 'tests'
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            (dest_dir / filename).write_bytes(data)
        checks_written.append({'path': f'tools/{rel_label}/{filename}',
                                'source': source_name,
                                'sha256_16': hashlib.sha256(data).hexdigest()[:16]})

    # Adapters are written FILE BY FILE, never by emptying their directory
    # first the way practices/ and tools/checks/ are. `.claude/hooks/` is not
    # this tool's to own: a consuming repo's own hooks live there beside the
    # ones a source publishes, and a repo can install more than one harness
    # adapter family side by side (templates/harness/README.md). Deleting the
    # directory would take a consumer's own work with it.
    adapters_written = []
    prior_adapters = _prior_adapter_hashes(out_dir)
    adopted = []
    for dest_rel, source_name, data, executable in adapters_plan:
        dest = out_dir / dest_rel
        want = hashlib.sha256(data).hexdigest()[:16]
        if dest.is_file():
            have = hashlib.sha256(dest.read_bytes()).hexdigest()[:16]
            if have != want and prior_adapters.get(dest_rel) != have:
                adopted.append(f'{dest_rel} ({source_name})')
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            # The executable bit is content here: a hook that is not
            # executable is a hook the harness silently never runs, which is
            # the failure this repo's own declared-hooks-exist check exists
            # for. Set explicitly in both directions so the result does not
            # depend on the umask of whoever ran the sync.
            os.chmod(dest, 0o755 if executable else 0o644)
        adapters_written.append({'path': dest_rel, 'source': source_name,
                                  'sha256_16': want, 'executable': executable})
    # An adapter this tree installed and no source declares any more is
    # REPORTED, never deleted. The equivalent sweep for practices/ and
    # tools/checks/ can delete, because materialize() owns those directories
    # outright; `.claude/hooks/` it does not, and by the time a declaration
    # goes away the file may have been wired into a settings.json this tool
    # deliberately never reads. Reporting is also all the prior manifest can
    # honestly support: it says this tree installed the file, not that
    # nothing else has come to depend on it (decommission-deletes-files wants
    # an audit before a delete, and that audit is not this tool's to run).
    stale_adapters = sorted(set(prior_adapters) -
                            {a['path'] for a in adapters_written})
    if stale_adapters and not dry_run:
        print("precedent_materialize: harness adapter(s) this tree installed "
              "that no declared source publishes any more -- left in place, "
              "not deleted. Remove each by hand once you have checked nothing "
              "still wires it: " + ', '.join(stale_adapters), file=sys.stderr)

    if adopted and not dry_run:
        print("precedent_materialize: harness adapter(s) whose previous "
              "content this tree had not recorded as materialized were "
              "REPLACED -- a hand-copy being adopted, or a local edit being "
              "reverted. `git diff` shows exactly what went, before you "
              "commit: " + ', '.join(adopted), file=sys.stderr)

    rstats = pr.resident_stats(res)
    if rstats['over_budget']:
        raise MaterializeError(
            f"combined resident block is ~{rstats['tokens']} tokens, over "
            f"the {rstats['budget']}-token cross-source cap -- not "
            f"materializing an over-budget set. Demote or retire a "
            f"resident practice in one of the sources first.")

    manifest = _build_manifest(sources, written, checks_written, rstats,
                               adapters_written, withheld=withheld)
    if not dry_run:
        (out_dir / 'MANIFEST.json').write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return written, checks_written, adapters_written, rstats


def _build_manifest(sources, written, checks_written, rstats,
                    adapters_written=(), withheld=None):
    """`withheld` names the slugs a PUBLIC repo's visibility keeps out of this
    tree -- recorded because "absent" and "never existed" look identical on
    disk, and several checks turn that difference into a finding.

    Without it, `rename-updates-links` reads a document's link to a withheld
    practice as a reference to a file "this branch deleted" and asks for it to
    be repointed -- at something that cannot exist here. Found 2026-09-07:
    excluding a public consumer's private practices produced 26 such findings
    in one repo, six of them inside a vendored tree nobody can edit there. The
    practices were not renamed or deleted; they are published elsewhere and
    withheld here, which is a third state those checks had no way to see."""
    return {
        'generated_by': 'tools/precedent_materialize.py',
        'generated_at_utc': precedent_time.utc_iso(),
        'note': 'DERIVED ARTIFACT -- never hand-edit. Regenerate by re-running '
                'precedent_materialize.py with the same --repo/--user-config; '
                'this file records exactly what produced the snapshot so drift '
                'is visible, per generated-artifact-provenance.',
        'sources': [{'level': s['level'], 'name': s['name'], 'path': s['path']}
                    for s in sources],
        'resident': rstats,
        'practices': written,
        'checks': checks_written,
        'adapters': list(adapters_written),
        'withheld': sorted(withheld or []),
    }


# The read-only half. A check that mutates what it is checking is worse
# than no check: it destroys the evidence it exists to report.
#
# 2026-09-06, found against a real four-source consumer install. Its
# AGENTS.md tells every session to run `precedent_sync_views.py --check` at
# session start, and --check guarded only the AGENTS.md write -- materialize()
# ran unconditionally underneath it, so every "check" silently rewrote
# practices/, tools/checks/ and MANIFEST.json in the working tree. Two
# consequences, both observed, not reasoned about:
#
#   * A consuming repo's own light check correctly failed on a materialized
#     check script that had drifted from its source. Running --check made
#     the failure disappear -- not by fixing the drift, by overwriting the
#     drifted file from the live source. The next run reported clean.
#   * With one source temporarily unreachable -- the ordinary state of a
#     fresh session before `add_repo` has run, which both consuming repos'
#     own instructions describe -- a --check run DELETED 57 tracked files:
#     every practice and check script that source contributed. It printed
#     a check verdict while doing it.
#
# So --check now plans everything (same out_dir, so link rewriting resolves
# identically) and compares against disk instead of writing.
def drift(sources, res, out_dir, withheld=None):
    """-> [str] findings describing how out_dir differs from a fresh sync.

    Writes nothing. An empty list means the committed materialized tree is
    exactly what a sync would produce right now.

    `withheld` must be what the CALLER excluded, for the same reason the
    manifest records it: recomputing here without it produces a manifest
    whose `withheld` list is empty, which differs from the committed one on
    every run -- so --check could never come back clean in the one kind of
    repo the exclusion exists for. Caught the day the exclusion landed."""
    out_dir = pathlib.Path(out_dir)
    written, checks_written, adapters_written, rstats = materialize(
        sources, res, out_dir, withheld=withheld, dry_run=True)
    found = []

    def _compare(rel_dir, planned, label):
        d = out_dir / rel_dir
        on_disk = {f.name: f for f in d.iterdir() if f.is_file()} if d.is_dir() else {}
        for name, want in sorted(planned.items()):
            have = on_disk.pop(name, None)
            if have is None:
                found.append(f"{rel_dir}/{name} is missing -- a fresh sync writes it ({label})")
            elif hashlib.sha256(have.read_bytes()).hexdigest()[:16] != want:
                found.append(f"{rel_dir}/{name} differs from what a fresh sync writes ({label})")
        for name in sorted(on_disk):
            found.append(f"{rel_dir}/{name} is not produced by any declared source -- "
                          f"a sync would delete it ({label})")

    _compare('practices', {f"{w['slug']}.md": w['sha256_16'] for w in written},
             'practice')
    planned_checks = {}
    for c in checks_written:
        planned_checks.setdefault(str(pathlib.PurePosixPath(c['path']).parent),
                                  {})[pathlib.PurePosixPath(c['path']).name] = c['sha256_16']
    for rel_dir, planned in sorted(planned_checks.items()):
        _compare(rel_dir, planned, 'check script')

    # Adapters get the content comparison but NOT _compare's sweep for files
    # the plan does not name: that sweep says "a sync would delete it", which
    # is true of practices/ and tools/checks/ and false of `.claude/hooks/`,
    # where a consumer's own hooks legitimately sit beside a source's. See
    # materialize() for why that directory is written file by file.
    for a in adapters_written:
        dest = out_dir / a['path']
        if not dest.is_file():
            found.append(f"{a['path']} is missing -- a fresh sync installs it "
                          f"(harness adapter, {a['source']})")
        elif hashlib.sha256(dest.read_bytes()).hexdigest()[:16] != a['sha256_16']:
            found.append(f"{a['path']} differs from what a fresh sync installs "
                          f"(harness adapter, {a['source']})")
        elif os.access(dest, os.X_OK) != a['executable']:
            want = 'executable' if a['executable'] else 'not executable'
            found.append(f"{a['path']} is {'not ' if a['executable'] else ''}"
                          f"executable and a fresh sync installs it {want} "
                          f"(harness adapter, {a['source']})")

    for path in sorted(set(_prior_adapter_hashes(out_dir)) -
                       {a['path'] for a in adapters_written}):
        found.append(f"{path} was installed as a harness adapter and no "
                      f"declared source publishes it any more -- a sync "
                      f"leaves it in place and reports it")

    # generated_at_utc is a timestamp, not state -- comparing it would make
    # every run report drift against itself.
    mf = out_dir / 'MANIFEST.json'
    want = _build_manifest(sources, written, checks_written, rstats,
                           adapters_written, withheld=withheld)
    if not mf.is_file():
        found.append('MANIFEST.json is missing -- a fresh sync writes it')
    else:
        try:
            have = json.loads(mf.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            found.append('MANIFEST.json is not valid JSON')
            have = None
        if have is not None:
            have.pop('generated_at_utc', None)
            want_cmp = dict(want)
            want_cmp.pop('generated_at_utc', None)
            if have != want_cmp:
                found.append('MANIFEST.json differs from what a fresh sync writes '
                              '(ignoring its generated_at_utc timestamp)')
    return found


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
            sys.exit(f"precedent_materialize FAIL: expected --flag value pairs, stuck at {tok!r}")
        args[tok] = argv[i + 1]
        i += 2
    return args


def main():
    args = _parse_args(sys.argv[1:])
    out = args.get('--out')
    if not out:
        sys.exit("precedent_materialize FAIL: --out DIR is required")
    repo = args.get('--repo', str(ROOT))
    user_config = args.get('--user-config')

    try:
        sources = pr.load_config(repo, user_config)
        if not sources:
            sys.exit(f"precedent_materialize FAIL: no practice sources are "
                      f"declared for {repo} (see precedent_resolve.py's own "
                      f"error for the same case).")
        res = pr.resolve(sources)
    except pr.ResolveError as e:
        sys.exit(f"precedent_materialize FAIL: {e}")

    for m in res['missing']:
        print(f"precedent_materialize: the {m['level']} source {m['name']!r} "
              f"is not available ({m['reason']}). Materializing WITHOUT it.",
              file=sys.stderr)

    try:
        written, checks_written, adapters_written, rstats = materialize(
            sources, res, pathlib.Path(out))
    except MaterializeError as e:
        sys.exit(f"precedent_materialize FAIL: {e}")

    print(f"materialized {len(written)} practice(s), {len(checks_written)} "
          f"check script(s)/test(s) and {len(adapters_written)} harness "
          f"adapter(s) from {len(sources)} source(s) into {out}")
    print(f"resident block: ~{rstats['tokens']} of {rstats['budget']} token budget")
    print(f"manifest: {pathlib.Path(out) / 'MANIFEST.json'}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

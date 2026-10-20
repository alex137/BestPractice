#!/usr/bin/env python3
"""Bridges precedent_resolve.py's multi-source resolution to the single-tree loader tools

precedent_materialize.py — bridges precedent_resolve.py's multi-source
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
engine travels with what it enforces), since 2026-09-26 every file a resolved
practice declares in its `ships:` field (see "Shipped files" below), and
since 2026-09-12 each source's
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
                           [--allow-missing-sources]
A consuming repo syncs through precedent_sync_views.py, which wraps this
tool and keeps two things out of a tracked tree that this tool, run on its
own, cannot: a private (shared or individual) source's practice text in a
public repo, and the silent removal an unreachable source causes. Run
directly, this tool REFUSES both (2026-10-17) and names the wrapper;
--allow-missing-sources lets a run proceed past an unreachable source when
that removal is meant. There is no flag for the first: the wrapper is the
route.
Exit: 0 on a clean materialization, 1 on a resolve conflict, an over-budget
resident set, a checks/ filename collision, a harness adapter declaration
that is malformed or collides on its destination, or a `ships:` declaration
(or a `declined_ships` entry in this repo's precedent.json) that is malformed
or collides on its destination.
"""
import datetime
import hashlib
import os
import re
import subprocess
import json
import pathlib
import shlex
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
import precedent_source_pins as psp  # noqa: E402



class MaterializeError(Exception):
    pass


# practice: session-load-budget -- a practice whose occasion can only ever
# fire inside the engine's own repository (auditing the loader, the routing
# table, the harness adapter tree) still cost every adopter an occasion-index
# line for a trigger it could never say. THIS TOOL WRITES WHAT A SOURCE
# PUBLISHES, NOT THE ENGINE (see module docstring) -- so an engine-dev
# practice is withheld here, at the boundary where a source's content
# becomes a consumer's tree. ENGINE_DEV_SCOPE and the predicate itself live
# in build_views.py now (relocated 2026-09-15, not duplicated: this module
# already imports it as `pr.bv` for `_json_str`), because build_views.py's
# own loader_practices() resolves the identical multi-source set a SECOND
# time, independently, for a repo's AGENTS.md -- and disagreed with what
# this tool writes until it had the same predicate to filter with. See the
# `scope` field: spec/PRACTICE_FORMAT.md.
ENGINE_DEV_SCOPE = pr.bv.ENGINE_DEV_SCOPE


def _is_engine_dev_scoped(practice):
    return pr.bv._is_engine_dev_scoped(practice['fm'])


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
# the product. precedent-shared-repo-maintenance' own light check had already had
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
                   may_name_source_repo=True, forwards=None, forward_files=None):
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
    a shared or individual source is a PRIVATE repository, replacing a
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
    a disclosure that cannot be taken back.

    `forwards` ({slug: live slug}, from precedent_resolve.forwarding_map)
    and `forward_files` ({resolved source path: live slug}) repoint a link
    to a renamed or deduplicated practice at the practice it forwards to.
    A consumer materializes only what is in force, so the stub such a link
    names is never written there: renaming go-merge to go-update on
    2026-09-26 left every `go-merge.md` citation in the private sets dead in
    every consumer. Only a live slug this run writes is used, so the new
    link is a sibling by construction."""
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
        live = None
        if bare.endswith('.md') and '/' not in bare:
            live = (forwards or {}).get(bare[:-3])
        if live is None and forward_files:
            live = forward_files.get(str((src_dir / bare).resolve()))
        if live is not None and live in sibling_slugs:
            anchor_part = ('#' + anchor) if anchor else ''
            return f'{open_paren}{live}.md{anchor_part}{close}'   # the rule's new home
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
# satisfy one: the deep-check rule that requires the driver is a SHARED-level
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
RUN_ALL_HEAD = """#!/bin/bash
# GENERATED FILE -- do not hand-edit. Written by tools/precedent_materialize.py
# on every sync; any edit here is overwritten without warning.
#
# Runs every materialized check's two-direction test. The glob is the point:
# this driver runs whatever tests this repo actually materialized, which is
# why it is generated here rather than copied from any one practice source.
#
# Every test here belongs to the source that shipped it -- owner_of below,
# the same source MANIFEST.json records for it under checks[]. A failing one
# is a bug in THAT source, and the summary at the end says so by name.
set -uo pipefail
cd "$(dirname "$0")"

owner_of() {
  owner=''
  level=''
  check=''
  tsha=''
  csha=''
  case "$1" in
"""
RUN_ALL_TAIL = """  esac
}

# The first 16 hex digits of a file's sha256, as MANIFEST.json records it.
_sha16() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -c1-16
  else
    shasum -a 256 "$1" | cut -c1-16
  fi
}

status=0
failed=()
found=()
ran=0
trusted=0
for t in test_*.sh; do
  # A repo that materialized no tests leaves the glob unexpanded; without
  # this the driver would try to run a file literally named test_*.sh and
  # report a failure that is really an empty set.
  [ -e "$t" ] || continue
  ran=$((ran + 1))
  owner_of "$t"
  # A test a source shipped, still byte-for-byte what it shipped, beside the
  # check it tests, likewise unchanged: its source already ran it before
  # shipping, at home and consumer-shaped (precedent_consumer_shape.py). Its
  # fixtures test the CHECK's code, which nobody here changed; the part that
  # judges this repo is the check itself, so that is what runs, in seconds
  # where the self-test took minutes (2026-10-06, a consumer whose every
  # Update Vendors spent about 7 of its minutes here, nearly all of it
  # re-testing unchanged shipped checks). A repo-local test, an edited test
  # or check, and PRECEDENT_RUN_ALL_SELF_TESTS=1 all run the self-test.
  if [ -n "$owner" ] && [ "$level" != repo-local ] && [ -n "$check" ] \
     && [ -z "${PRECEDENT_RUN_ALL_SELF_TESTS:-}" ] && [ -f "../$check" ] \
     && [ "$(_sha16 "$t")" = "$tsha" ] && [ "$(_sha16 "../$check")" = "$csha" ]; then
    echo "--- $t: unchanged from '$owner', which ran it before shipping; running $check on this repo instead ---"
    trusted=$((trusted + 1))
    ( cd ../../.. && python3 "tools/checks/$check" )
    rc=$?
    # 2 is a check's "does not apply here" -- a skip, never a failure.
    if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
      status=1
      found+=("$check")
    fi
    continue
  fi
  echo "--- $t ---"
  if ! bash "$t"; then
    status=1
    failed+=("$t")
  fi
done

# Say what ran, so silence is never read as a pass (2026-09-28: a fresh
# install materializes no tests, and this driver used to print nothing).
if [ "$ran" -eq 0 ]; then
  echo "run_all: 0 materialized tests -- nothing ran"
elif [ "$status" -eq 0 ]; then
  echo "run_all: $ran test(s) run, 0 failed"
fi
if [ "$trusted" -gt 0 ]; then
  echo "run_all: $trusted of them unchanged from their source, so only their check ran on this repo;"
  echo "    PRECEDENT_RUN_ALL_SELF_TESTS=1 runs their self-tests too"
fi

if [ "${#found[@]}" -gt 0 ]; then
  echo
  echo "=== ${#found[@]} check(s) found problems in this repo's own files ==="
  for c in "${found[@]}"; do
    echo "FAILED: $c -- its findings are above; they are this repo's to fix, not the source's"
  done
fi

if [ "${#failed[@]}" -gt 0 ]; then
  echo
  # A test that clones this repo runs the COMMITTED checks, not the ones on
  # disk. With tools/checks/ changed and not committed -- the state an
  # update is in before its commit -- such a test pairs new cases with old
  # scripts and can fail on nothing. Seen 2026-09-28 (test_file_header.sh,
  # fixed in its source); several shipped tests still clone the repo.
  if [ -n "$(git -C ../../.. status --porcelain -- tools/checks 2>/dev/null)" ]; then
    echo "NOTE: tools/checks/ has uncommitted changes. A test that clones this"
    echo "repo runs the committed scripts, not these, so a failure below may"
    echo "vanish once they are committed. Commit (or judge a temporary commit,"
    echo "as Update Vendors does) before treating it as real."
    echo
  fi
  echo "=== ${#failed[@]} materialized test(s) failed -- who owns each ==="
  shipped=0
  for t in "${failed[@]}"; do
    owner_of "$t"
    if [ -z "$owner" ]; then
      echo "FAILED: $t -- no source shipped it: the last sync did not write it"
      echo "    and MANIFEST.json does not list it. Find out who put it here."
    elif [ "$level" = repo-local ]; then
      echo "FAILED: $t -- this repo's own repo-local source (local/): fix it here"
    else
      echo "FAILED: $t -- shipped by source '$owner' ($level level)"
      shipped=1
    fi
  done
  if [ "$shipped" -eq 1 ]; then
    echo
    echo "A test shipped by a source is not this repo's to own, and a failing one"
    echo "is a bug in that source: fix it there and report it there -- from a"
    echo "session rooted in that source's repository, or with a hand-off to one"
    echo "if this session cannot reach it. Never record it here as pre-existing,"
    echo "or as failing on the base branch too: that is true, and it is how a"
    echo "shipped test stays red for days in every repo that carries it."
  fi
fi
exit $status
"""


def _run_all_script(test_owners, fingerprints=None):
    """The generated driver, with `test_owners` ({test filename: (source
    name, level)}) written into its owner_of table.

    Why the owner is baked in rather than looked up at run time: the driver
    has to name the owner in exactly the case where something is already
    wrong, and a lookup that parses MANIFEST.json in bash is one more thing
    to be wrong then. The table is built from the same plan the manifest's
    checks[] entries are, in the same run, so the two cannot disagree -- and
    drift() compares this file like any other, so a stale table is caught.

    Why it exists at all (2026-09-25): consuming repos kept reporting "N
    tests fail, but they fail on the base branch too, so not this change"
    and moving on. That sentence is true and ends the conversation, and
    nothing routed the failure back to the source that shipped the test,
    so the same red test sat in a consumer for days. One case measured
    that day: a test planted a fixture under vendor/ and ran `git add` on
    it; the consumer's .gitignore ignored vendor/ (a dependency manager's
    directory), so git refused the add -- in every consumer shaped like
    that one, and in none of the source's own runs. Naming the owner, and
    saying that a failure is that owner's bug, is what turns the red line
    into a report someone can act on."""
    fingerprints = fingerprints or {}
    lines = []
    for name in sorted(test_owners):
        src, level = test_owners[name]
        extra = ''
        if name in fingerprints:
            check, tsha, csha = fingerprints[name]
            extra = (f" check={shlex.quote(check)}; tsha={tsha}; "
                     f"csha={csha};")
        lines.append(f"    {shlex.quote(name)}) owner={shlex.quote(src)}; "
                     f"level={shlex.quote(level)};{extra} ;;\n")
    return RUN_ALL_HEAD + ''.join(lines) + RUN_ALL_TAIL

_CLAIMED_CACHE = {}


def _claimed_in_source(source_path):
    """-> {check and test file names} that any practice file in the source at
    `source_path` names in `checked_by`, whatever its status."""
    key = str(pathlib.Path(source_path).resolve())
    if key in _CLAIMED_CACHE:
        return _CLAIMED_CACHE[key]
    names = set()
    pdir = pathlib.Path(source_path) / 'practices'
    for pf in (sorted(pdir.glob('*.md')) if pdir.is_dir() else []):
        try:
            head = pf.read_text(encoding='utf-8', errors='replace')[:4000]
        except OSError:
            continue
        m = re.search(r'^checked_by:\s*(\S+)', head, re.M)
        if not m:
            continue
        cb = m.group(1).strip('"\'')
        if cb.endswith('.py') and '/checks/' in cb:
            stem = pathlib.PurePath(cb).stem
            names.update({f'{stem}.py', f'{stem.replace("check_", "test_", 1)}.sh'})
    _CLAIMED_CACHE[key] = names
    return names


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
    # Which SOURCE claims each file, not only whether anyone does. A check
    # is taken from the source whose resolved practice names it in
    # `checked_by`, and another source's same-named copy is left behind as
    # unclaimed rather than colliding with it. Found 2026-09-23, migrating a
    # consumer onto the loader, twice in one sync: the universal tree had
    # begun carrying its own scrubbed copies of the individual set's two
    # commit checks (BestPractice's own push gate, 2026-09-22), and the
    # individual set still carried check_fresh_before_write.py after its
    # practice moved to a shared set and was marked deduplicated. Either
    # one refused the whole sync -- which, for a repo migrating onto the
    # loader, meant no practice in force at all. A file two sources BOTH
    # claim is still a real collision and still refuses.
    claimed_by = {}
    if res is not None:
        claimed_names = set()
        for practice in res['practices'].values():
            cb = (practice.get('fm', {}).get('checked_by') or '').strip().strip('"').strip("'")
            if cb.endswith('.py') and '/checks/' in cb:
                stem = pathlib.PurePath(cb).stem
                for name in (f'{stem}.py', f'{stem.replace("check_", "test_", 1)}.sh'):
                    claimed_names.add(name)
                    claimed_by.setdefault(name, set()).add(practice.get('source'))
            # A tool a practice SHIPS can have a test of its own,
            # tools/checks/tests/test_<tool>.sh, and nothing else claims it:
            # until 2026-10-15 every sync of a set shipping tools/typography.py
            # said its test_typography.sh was claimed by no practice and left
            # it behind, so the tool reached consumers untested.
            try:
                shipped_paths = pr.bv.ships_paths(practice.get('fm', {}))
            except ValueError:
                shipped_paths = []        # _plan_ships refuses it, by name
            for shipped in shipped_paths:
                if shipped.startswith('tools/') and shipped.endswith('.py'):
                    name = f'test_{pathlib.PurePath(shipped).stem}.sh'
                    claimed_names.add(name)
                    claimed_by.setdefault(name, set()).add(practice.get('source'))

    def unclaimed_here(name, source_name):
        """True when a resolved practice claims `name`, but from another
        source -- this source's copy has nothing to enforce here."""
        owners = claimed_by.get(name)
        return bool(owners) and None not in owners and source_name not in owners

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

    def held_back(name, source_path):
        """True when a practice file in the script's OWN source names it in
        `checked_by` -- a rule that source keeps out of force here on
        purpose (deduplicated, retired), whose check still runs in that
        source's own repository. Not an orphan, and not worth a line on
        every sync (reported from a consumer, 2026-10-06: every sync listed
        the individual set's three such checks)."""
        return name in _claimed_in_source(source_path)

    # Which sources ship each check and test, so a copy claimed from another
    # source is judged by whether that source ships one too (claimed_elsewhere).
    ships = {}
    for s in sources:
        d = pathlib.Path(s['path']) / 'tools' / 'checks'
        for f in ((list(d.glob('check_*.py')) + list((d / 'tests').glob('test_*.sh')))
                  if d.is_dir() else []):
            ships.setdefault(f.name, []).append(s['name'])
    shadowed = []   # (label, the source whose copy runs, the one left behind)

    def claimed_elsewhere(f, label, s):
        """A copy whose name a practice in force claims from ANOTHER source
        (unclaimed_here). Claimed is claimed, whichever source supplies the
        file: where a claiming source ships its own copy, that one runs and
        this one is left behind, said plainly below unless this source's own
        practice file keeps it out on purpose (held_back); where none does,
        this copy is the one the practice in force needs, and is vendored.
        2026-10-08, a consumer: universal ships scrubbed copies of the
        individual set's commit-author and buenos-aires-dates checks, the
        individual set's practices claim them in force there, and every sync
        listed universal's copies as claimed by nothing."""
        # A check and its test go together: a claiming source that ships
        # either one keeps both, so another source's test is never run
        # against this source's check.
        stem = f.name[len('check_'):-len('.py')] if f.name.endswith('.py') \
            else f.name[len('test_'):-len('.sh')]
        pair = (f'check_{stem}.py', f'test_{stem}.sh')
        owners = sorted(o for o in claimed_by.get(f.name, ())
                        if any(o in ships.get(n, ()) for n in pair))
        if owners:
            if not held_back(f.name, s['path']):
                shadowed.append((f'tools/{label}/{f.name}', owners[0], s['name']))
        elif f'{label}/{f.name}' not in owner_of:
            claim(f, label, s['name'])

    for s in sources:
        src_checks = pathlib.Path(s['path']) / 'tools' / 'checks'
        if not src_checks.is_dir():
            continue
        for f in sorted(src_checks.glob('*.py')):
            if not f.name.startswith('check_'):
                skipped.append(f'tools/checks/{f.name} ({s["name"]})')
            elif claimed_names is not None and f.name not in claimed_names:
                if not held_back(f.name, s['path']):
                    orphaned.append(f'tools/checks/{f.name} ({s["name"]})')
            elif claimed_names is not None and unclaimed_here(f.name, s['name']):
                claimed_elsewhere(f, 'checks', s)
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
                    if not held_back(f.name, s['path']):
                        orphaned.append(f'tools/checks/tests/{f.name} ({s["name"]})')
                elif claimed_names is not None and unclaimed_here(f.name, s['name']):
                    claimed_elsewhere(f, 'checks/tests', s)
                else:
                    claim(f, 'checks/tests', s['name'])
    if skipped:
        print(f"precedent_materialize: not a per-check file, not vendored: "
              + ', '.join(skipped), file=sys.stderr)
    if orphaned:
        print(f"precedent_materialize: no practice in force here claims these, "
              f"not vendored: " + ', '.join(orphaned), file=sys.stderr)
    checks_shadowed = [x for x in shadowed if '/tests/' not in x[0]]
    if checks_shadowed:
        print("precedent_materialize: " + '; '.join(
            f"{label} runs from {runs}, whose practice in force claims it "
            f"({left}'s copy is not vendored)" for label, runs, left in checks_shadowed),
            file=sys.stderr)
    if undeclared:
        print(f"precedent_materialize: replaced here by the generated "
              f"driver, and the source's own tools/checks/tests/"
              f"{RUN_ALL_NAME} does not say so -- add a header line "
              f"containing \"{LOCAL_DRIVER_MARKER}\" to each of: "
              + ', '.join(undeclared), file=sys.stderr)
    level_of = {s['name']: s['level'] for s in sources}
    test_owners = {filename: (source_name, level_of.get(source_name, 'unknown'))
                   for rel_label, filename, source_name, _data in plan
                   if rel_label == 'checks/tests'}
    # Each shipped test's fingerprint, and its check's, as shipped: the
    # driver runs only the check where both still match (RUN_ALL_TAIL says
    # why). Hashed exactly as MANIFEST.json's checks[] records them.
    shipped = {(rel, fn): data for rel, fn, _src, data in plan}
    fingerprints = {}
    for filename in test_owners:
        check = 'check_' + filename[len('test_'):-len('.sh')] + '.py'
        if ('checks', check) in shipped:
            fingerprints[filename] = (
                check,
                hashlib.sha256(shipped[('checks/tests', filename)]).hexdigest()[:16],
                hashlib.sha256(shipped[('checks', check)]).hexdigest()[:16])
    plan.append(('checks/tests', RUN_ALL_NAME, GENERATED_SOURCE,
                 _run_all_script(test_owners, fingerprints).encode('utf-8')))
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


# --------------------------------------------------------------------------
# Shipped files
# --------------------------------------------------------------------------
#
# practice: practice-carries-its-files -- a practice declares the files it
# owns besides its checked_by script and test, in `ships:`, and this is what
# delivers them.
#
# THE INCIDENT (2026-09-26). precedent-shared-writing's create-word-doc
# practice owns tools/create_word_doc.py: its Rule tells a session to run the
# script, and its shipped test copies it (`cp "$SET_ROOT/tools/
# create_word_doc.py" ...`). This tool shipped the practice and the test and
# never the script, so in a consumer without a hand-copy the consumer's deep
# check went red on a test it could neither fix nor satisfy. The practice's
# own Detail said consumers "copy it in by hand" -- the same arrangement the
# harness adapters above had until their two measured incidents, and the
# same outcome. Nothing declared the dependency, so nothing could deliver it,
# and nothing noticed when a practice moved between sets without it.
#
# SAME CONTRACT AS THE ADAPTERS, for the same reasons: read everything
# before writing anything; refuse a destination two sources both claim;
# write file by file, never by emptying a directory (tools/ holds the
# consumer's own scripts and the vendored engine); record each file in
# MANIFEST.json so drift() can compare it; replace a copy the manifest never
# recorded, loudly; remove a file no practice ships any more while it is
# exactly what was shipped and nothing names it, and report any other.
#
# ONE DIFFERENCE: a consumer may DECLINE one, in its own precedent.json,
# with a reason. An adapter is part of the machinery every consumer runs; a
# shipped file serves a practice's Rule, and a repository may have decided
# it does not want the half of that Rule the file serves -- create-word-doc
# itself allows every export to be a hand-built one-off. The reason is
# required and recorded in the manifest, so "declined" and "never
# delivered" stay distinguishable:
#
#   "declined_ships": {"tools/create_word_doc.py": "we never export .docx"}
DECLINED_SHIPS_KEY = 'declined_ships'


def _declined_ships(out_dir):
    """{path: reason} from the consuming repo's own precedent.json.

    Raises on a malformed declaration: it is this repo's own edit, and a
    decline nobody can read must not silently become a delivery."""
    cfg = pathlib.Path(out_dir) / 'precedent.json'
    if not cfg.is_file():
        return {}
    try:
        data = json.loads(cfg.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}      # load_config already refused an unreadable config
    decl = data.get(DECLINED_SHIPS_KEY) if isinstance(data, dict) else None
    if decl is None:
        return {}
    if not isinstance(decl, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and v.strip()
            for k, v in decl.items()):
        raise MaterializeError(
            f"{cfg}: \"{DECLINED_SHIPS_KEY}\" must be an object mapping each "
            f"declined path to a non-empty reason, e.g. "
            f"{{\"tools/create_word_doc.py\": \"we never export .docx\"}}.")
    return dict(decl)


def _plan_ships(res, declined=None, adapter_dests=()):
    """-> (plan, declined_rows). `plan` is [(dest, source_name, slug, bytes,
    executable)], `declined_rows` [{'path', 'reason', 'slug'}]. Reads, never
    writes -- same contract as _plan_checks and _plan_adapters.

    Only a practice this run actually materializes ships anything: one that
    lost its slug to a higher-precedence source, or is withdrawn, or is
    engine-dev scoped, is not in force here and its files have nothing to
    serve. A declared file missing from its source WARNS and is skipped, as
    an adapter's does -- the ordinary cause is a stale clone. A malformed
    declaration raises, as an adapter's does; practice-carries-its-files
    refuses it at the source's own push first, so a consumer should never
    be the one to hear about it."""
    declined = dict(declined or {})
    adapter_dests = set(adapter_dests)
    owner_of, plan, missing, declined_rows = {}, [], [], []
    for slug, practice in sorted(res['practices'].items()):
        if _is_engine_dev_scoped(practice):
            continue
        try:
            paths = pr.bv.ships_paths(practice.get('fm', {}))
        except ValueError as e:
            raise MaterializeError(f"{practice['file']}: {e}")
        root = pathlib.Path(practice['file']).resolve().parent.parent
        for rel in paths:
            why = pr.bv.ship_path_problem(rel)
            if why:
                raise MaterializeError(
                    f"{practice['file']}: `ships:` entry {rel!r} {why}.")
            dest = pathlib.PurePosixPath(rel).as_posix()
            if dest in adapter_dests:
                raise MaterializeError(
                    f"{dest} is both a harness adapter destination and a file "
                    f"{slug!r} ships -- two mechanisms cannot own one file. "
                    f"Drop one of the two declarations.")
            prior = owner_of.get(dest)
            if prior is not None:
                if prior[0] != practice['source']:
                    raise MaterializeError(
                        f"{dest} is shipped by both {prior[1]!r} (source "
                        f"{prior[0]!r}) and {slug!r} (source "
                        f"{practice['source']!r}) -- a destination collision. "
                        f"Pick one, or rename one of the files.")
                continue        # two practices of one source share a file
            owner_of[dest] = (practice['source'], slug)
            if dest in declined:
                declined_rows.append({'path': dest, 'slug': slug,
                                      'reason': declined.pop(dest).strip()})
                continue
            src_file = root / rel
            if not src_file.is_file():
                missing.append(f'{rel} ({slug}, {practice["source"]})')
                continue
            plan.append((dest, practice['source'], slug, src_file.read_bytes(),
                         os.access(src_file, os.X_OK)))
    if missing:
        print("precedent_materialize: shipped file(s) a practice declares "
              "that are not in its source tree, NOT delivered -- the source "
              "names a file it does not carry, or its clone here is stale: "
              + ', '.join(missing), file=sys.stderr)
    if declined:
        print(f"precedent_materialize: precedent.json declines "
              f"{', '.join(sorted(declined))} under \"{DECLINED_SHIPS_KEY}\", "
              f"and no practice in force here ships it -- the decline is "
              f"stale; remove it", file=sys.stderr)
    return plan, declined_rows


def _ship_drift_advice(out_dir, source_name, rel, dest):
    """-> what to do about a shipped file whose copy here differs from the
    one its source's sync delivers. When the source's own clone carries
    these exact bytes on a branch, the copy here is that change arriving
    early: land it in the source first (2026-10-16, a consumer took a fix
    to a shipped file while the same fix sat on the set's working branch,
    and this told it to decline the file -- the wrong move). Only when the
    source has nothing matching is declining offered."""
    # An edit to a shipped file is answered, not declined (practice:
    # upstream-bug-stops-here, 2026-10-17): a decline says this repository
    # does not want the file at all, and was the side door every edit took.
    decline = (f"{_three_answers()}; decline it under "
               f"\"{DECLINED_SHIPS_KEY}\" in precedent.json only if this "
               f"repository does not want the file at all")
    try:
        clone = next((pathlib.Path(p) for p, _lvl, name, _n in
                      pr.declared_source_paths(out_dir)
                      if name == source_name and p), None)
    except Exception:                                        # noqa: BLE001
        clone = None
    if clone is None or not (clone / '.git').exists():
        return decline

    def git(*a):
        r = subprocess.run(['git', '-C', str(clone), *a], capture_output=True,
                           text=True)
        return r.stdout.strip() if r.returncode == 0 else ''
    blob = subprocess.run(['git', 'hash-object', str(dest)], capture_output=True,
                          text=True).stdout.strip()
    if not blob:
        return decline
    refs = git('for-each-ref', '--format=%(refname:short)', 'refs/heads',
               'refs/remotes').split()
    # The source's own declared base branch, never origin/HEAD.
    base = f"origin/{pr._base_branch_of(clone)}"
    carrying = [r for r in refs if not r.endswith('/HEAD')
                and git('rev-parse', '-q', '--verify', f'{r}:{rel}') == blob]
    if not carrying:
        return decline
    if base in carrying:
        return (f"{source_name}'s {base} already carries exactly this; the "
                f"pin here is older -- run the sync to take it")
    shown = ', '.join(sorted(carrying)[:3])
    return (f"{source_name} has exactly this on {shown}, not yet on its "
            f"{base}: land it there first, then sync -- declining it here "
            f"would keep a copy that drifts from the fix")


def mention_names_another_repo(line, path, own_slug):
    """qualified_mention's rule (one copy), loaded lazily: a tree without
    the module reads every mention as plain, as before 2026-10-19."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    try:
        import qualified_mention
    except ImportError:
        return False
    finally:
        sys.path.pop(0)
    return qualified_mention.mention_names_another_repo(line, path, own_slug)


def _stale_ship_keep_reason(out_dir, rel, shipped_hash):
    """-> None when shipped file `rel`, which no practice ships any more, may
    be removed: it is byte for byte what the manifest says was shipped, and
    no other tracked file names it. Otherwise why it stays: 'gone',
    'edited here', or 'named by <file>'."""
    out_dir = pathlib.Path(out_dir)
    dest = out_dir / rel
    if not dest.is_file():
        return 'gone'
    if not shipped_hash or hashlib.sha256(dest.read_bytes()).hexdigest()[:16] != shipped_hash:
        return 'edited here'
    r = subprocess.run(['git', '-C', str(out_dir), 'grep', '-l', '-F', '-e',
                        pathlib.PurePath(rel).name, '--', '.', f':(exclude){rel}',
                        ':(exclude)MANIFEST.json'], capture_output=True, text=True)
    if r.returncode not in (0, 1):
        return 'not checked: git grep failed'
    users = [l for l in r.stdout.splitlines() if l.strip()]
    # A file that names it only as another repository's names that
    # repository's copy (mention_names_another_repo).
    slug = _origin_slug(out_dir)
    users = [u for u in users if not all(
        mention_names_another_repo(line, rel, slug)
        for line in _lines_naming(out_dir / u, pathlib.PurePath(rel).name))]
    if users:
        return f'named by {users[0]}' + (f' and {len(users) - 1} more' if len(users) > 1 else '')
    return None


def _origin_slug(root):
    r = subprocess.run(['git', '-C', str(root), 'remote', 'get-url', 'origin'],
                       capture_output=True, text=True)
    m = re.search(r'github\.com[:/]+([^/]+/[^/\s]+?)(?:\.git)?/*$', r.stdout.strip())
    return m.group(1) if r.returncode == 0 and m else None


def _lines_naming(path, needle):
    try:
        return [l for l in path.read_text(encoding='utf-8', errors='ignore').splitlines()
                if needle in l]
    except OSError:
        return [needle]                 # unreadable: counts as a plain mention


def _prior_ship_hashes(out_dir):
    """{destination: sha256_16} from the manifest this tree already carries
    -- the same question _prior_adapter_hashes answers, for shipped files."""
    mf = pathlib.Path(out_dir) / 'MANIFEST.json'
    if not mf.is_file():
        return {}
    try:
        data = json.loads(mf.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {s['path']: s.get('sha256_16') for s in data.get('ships', [])
            if isinstance(s, dict) and isinstance(s.get('path'), str)}


# --------------------------------------------------------------------------
# Shipped files of a set this repository does not track
# --------------------------------------------------------------------------
#
# practice: practice-carries-its-files -- a set the PERSON brings (their
# individual set's `brings` list), or one this repository declares but its
# tracked tree leaves out (a public repository's private set, a practice
# set's declared sets), reaches a session through the untracked
# .precedent/SESSION_PRACTICES.md and never through the sync above. Its
# `ships:` files and `hooks:` therefore never arrived either.
#
# THE INCIDENT (2026-10-13). A consuming repository got the writing set only
# through the person's individual set: create-word-doc told every session to
# run `python3 tools/create_word_doc.py`, and dated-download-names' hook ran
# tools/dated_name.py, and neither file was there. BestPractice declares the
# same set, and as the universal source itself never materializes, so the
# same two files were missing here too.
#
# WHY NOT THE TRACKED DELIVERY. A brought set comes through one person's
# user-level config, so delivering its files into the tracked tree would
# make a repository's tracked content depend on who ran the sync -- the
# exact line build_views.sources_for_tracked_block and
# precedent_sync_views._sync draw for practice text (spec/LADDER_OPT_IN_PLAN.md
# D6). So the file goes to the path the practice names, where its Rule and
# its hook expect it, and stays OUT of git: listed in this clone's own
# .git/info/exclude (never the tracked .gitignore), recorded in
# .precedent/session_ships.json, refreshed at every session start by
# precedent_session_practices.py. Its hook goes to .precedent/practice_hooks.json,
# which precedent_hooks.py runs beside process/practice_hooks.json.
#
# NEVER TAKES A FILE THAT IS NOT ITS OWN (practice: repair-cannot-discard-work):
# a path git tracks, one the tracked sync delivered (MANIFEST.json `ships`),
# one precedent.json declines, and an untracked file this never wrote, or
# wrote and somebody since edited, are each left exactly as they are. A file
# it wrote that no practice ships any more is removed only while unchanged.
def _engine_owned(repo):
    """-> the tools/ paths this repository's vendored engine owns, read off
    tools/ENGINE_MANIFEST.json; empty where there is none.

    A file a set used to ship and the engine now carries is the engine's,
    not a leftover: the stale-ships notice below tells a person to remove
    each file it names by hand, and on 2026-10-16 typography.py moved from
    the writing set into the engine -- that notice would have named it on
    every sync, inviting the deletion of an engine file."""
    try:
        files = json.loads((pathlib.Path(repo) / 'tools' / 'ENGINE_MANIFEST.json')
                           .read_text(encoding='utf-8')).get('files') or []
    except (OSError, ValueError, AttributeError):
        return set()
    return {f'tools/{f}' for f in files}


SESSION_SHIPS_RECORD = pr.bv.SESSION_SHIPS_RECORD
SESSION_HOOKS_FILE = '.precedent/practice_hooks.json'
_EXCLUDE_BEGIN = ('# BEGIN precedent session ships -- files a practice set '
                  'this repository does not track ships; written by '
                  'precedent_materialize.deliver_session_ships, never by hand')
_EXCLUDE_END = '# END precedent session ships'


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args],
                          capture_output=True, text=True)


def _git_tracks(repo, rel):
    return _git(repo, 'ls-files', '--error-unmatch', '--', rel).returncode == 0


def _exclude_file(repo):
    """-> this clone's info/exclude, or None outside a git work tree. Asked
    of git, so a linked worktree gets the common one every worktree reads."""
    r = _git(repo, 'rev-parse', '--git-path', 'info/exclude')
    if r.returncode != 0 or not r.stdout.strip():
        return None
    p = pathlib.Path(r.stdout.strip())
    return p if p.is_absolute() else pathlib.Path(repo) / p


def _worktree_roots(repo):
    """-> every work tree of the clone `repo` belongs to, main and linked."""
    r = _git(repo, 'worktree', 'list', '--porcelain')
    roots = [pathlib.Path(l[len('worktree '):]) for l in r.stdout.splitlines()
             if l.startswith('worktree ')] if r.returncode == 0 else []
    return roots or [pathlib.Path(repo)]


def _still_shipped_elsewhere(repo, rel):
    """True when another work tree of this clone still holds `rel`,
    untracked: a ship delivered there, which this checkout did not deliver."""
    here = pathlib.Path(repo).resolve()
    for root in _worktree_roots(repo):
        if root.resolve() == here or not (root / rel).is_file():
            continue
        if not _git_tracks(root, rel):
            return True
    return False


def _set_excluded(repo, paths):
    """Make the precedent block of info/exclude list `paths`, plus any entry
    another work tree of this clone still holds.

    ONE LIST, MANY WORK TREES (2026-10-17). info/exclude lives in the common
    git directory, so every linked worktree reads and writes the same file.
    Writing exactly this checkout's ships dropped the others': a session
    file built in a helper's worktree, where fewer sets resolved, took three
    shipped tools off the list while they sat on disk in the main checkout,
    one of them from a private repository -- a `git add -A` there would have
    committed it. An entry now stays while some work tree still has its
    file untracked, and goes once none does."""
    ex = _exclude_file(repo)
    if ex is None:
        return
    try:
        old = ex.read_text(encoding='utf-8') if ex.is_file() else ''
    except OSError:
        return
    keep, inside, listed = [], False, []
    for line in old.splitlines():
        if line == _EXCLUDE_BEGIN:
            inside = True
            continue
        if inside:
            if line == _EXCLUDE_END:
                inside = False
            elif line.startswith('/'):
                listed.append(line[1:])
            continue
        keep.append(line)
    paths = set(paths) | {rel for rel in listed if rel not in paths
                          and _still_shipped_elsewhere(repo, rel)}
    if paths:
        keep += [_EXCLUDE_BEGIN, *(f'/{p}' for p in sorted(paths)), _EXCLUDE_END]
    new = '\n'.join(keep) + ('\n' if keep else '')
    if new != old:
        try:
            ex.parent.mkdir(parents=True, exist_ok=True)
            ex.write_text(new, encoding='utf-8')
        except OSError:
            pass


def _session_ship_record(repo):
    try:
        data = json.loads((pathlib.Path(repo) / SESSION_SHIPS_RECORD)
                          .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    files = data.get('files') if isinstance(data, dict) else None
    return {k: v for k, v in (files or {}).items()
            if isinstance(k, str) and isinstance(v, dict)}


def _write_session_ship_record(repo, files):
    path = pathlib.Path(repo) / SESSION_SHIPS_RECORD
    if not files and not path.is_file():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        '_comment': 'Untracked, per clone: the files a practice set this '
                    'repository does not track ships, delivered by '
                    'tools/precedent_materialize.py (deliver_session_ships) '
                    'and kept out of git by .git/info/exclude.',
        'files': {k: files[k] for k in sorted(files)}}, indent=2) + '\n',
        encoding='utf-8')


def release_session_ships(repo, paths):
    """The tracked sync now delivers `paths`: they stop being this clone's
    untracked copies, so git sees them and they get committed."""
    rec = _session_ship_record(repo)
    if not any(p in rec for p in paths):
        return
    for p in paths:
        rec.pop(p, None)
    _write_session_ship_record(repo, rec)
    _set_excluded(repo, set(rec))


def deliver_session_ships(repo, practices, dry_run=False):
    """Deliver the `ships:` files and wire the `hooks:` of `practices` -- the
    [(fm, practice_file)] a session carries from sources this repository
    does not track -- without touching the tracked tree. See the section
    comment above. -> {'delivered', 'removed', 'left', 'hooks', 'notes'},
    each a list of strings. Never raises for a practice's own declaration:
    this runs from a session-start hook, where an exception takes the
    session with it (practice: fail-gracefully)."""
    repo = pathlib.Path(repo).resolve()
    out = {'delivered': [], 'removed': [], 'left': [], 'hooks': [], 'notes': []}
    def _ships(fm):
        try:
            return pr.bv.ships_paths(fm)
        except ValueError:
            return ['?']
    if not any(_ships(fm) for fm, _f in practices) \
            and not (repo / SESSION_SHIPS_RECORD).is_file() \
            and not (repo / SESSION_HOOKS_FILE).is_file():
        return out                 # nothing to deliver and nothing delivered
    if _exclude_file(repo) is None:
        out['notes'].append(f'{repo} is not a git work tree, so the files a '
                            f'set it does not track ships were not delivered')
        return out
    try:
        declined = _declined_ships(repo)
    except MaterializeError as e:
        out['notes'].append(str(e))
        declined = {}
    tracked_ships = set(_prior_ship_hashes(repo))
    prior = _session_ship_record(repo)
    files, owner, hook_rows = {}, {}, []
    for fm, pfile in practices:
        pfile = pathlib.Path(pfile)
        slug = pr.bv._json_str(fm.get('slug', '')) or pfile.stem
        if pr.bv._is_engine_dev_scoped(fm):
            continue
        try:
            paths = pr.bv.ships_paths(fm)
            hooks = pr.bv.practice_hooks(fm)
        except ValueError as e:
            out['notes'].append(f'{slug}: {e} -- nothing of it delivered')
            continue
        root = pfile.resolve().parent.parent
        # `here`: shipped files this repository already holds as its own --
        # a set's own practice, or an engine file it vendors. Nothing is
        # delivered for them, and their hooks are still registered: a set's
        # own `hooks:` never ran in a session rooted in it (2026-10-17).
        mine, here = set(), set()
        for rel in paths:
            why = pr.bv.ship_path_problem(rel)
            if why:
                out['notes'].append(f'{slug}: `ships:` entry {rel!r} {why}')
                continue
            dest_rel = pathlib.PurePosixPath(rel).as_posix()
            src, dest = root / rel, repo / dest_rel
            if dest_rel in declined:
                continue
            if dest_rel in tracked_ships:
                here.add(dest_rel)
                continue
            if dest_rel in owner and owner[dest_rel] != str(root):
                out['notes'].append(f'{dest_rel} is shipped by two sets; the '
                                    f'first one read is kept')
                continue
            if not src.is_file():
                out['notes'].append(f'{dest_rel} ({slug}) is not in its set at '
                                    f'{root} -- a stale clone; not delivered')
                continue
            if src.resolve() == dest.resolve() or _git_tracks(repo, dest_rel):
                here.add(dest_rel)
                continue           # the repository's own file
            owner[dest_rel] = str(root)
            data = src.read_bytes()
            want = hashlib.sha256(data).hexdigest()[:16]
            if dest.is_file():
                have = hashlib.sha256(dest.read_bytes()).hexdigest()[:16]
                ours = (prior.get(dest_rel) or {}).get('sha256_16') == have
                if have != want and not ours:
                    out['left'].append(dest_rel)
                    continue
            if not dest.is_file() or dest.read_bytes() != data:
                out['delivered'].append(dest_rel)
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
                    os.chmod(dest, 0o755 if os.access(src, os.X_OK) else 0o644)
            files[dest_rel] = {'sha256_16': want, 'practice': slug,
                               'set': root.name}
            mine.add(dest_rel)
        for h in hooks:
            if h['run'] in mine or h['run'] in here:
                hook_rows.append((h['event'], h['matcher'], pr.bv.hook_command(h)))
    for dest_rel, row in sorted(prior.items()):
        if dest_rel in files or dest_rel in tracked_ships:
            continue
        dest = repo / dest_rel
        if not dest.is_file() or _git_tracks(repo, dest_rel):
            continue
        if hashlib.sha256(dest.read_bytes()).hexdigest()[:16] == row.get('sha256_16'):
            out['removed'].append(dest_rel)
            if not dry_run:
                dest.unlink()
        else:
            out['left'].append(dest_rel)
    if not dry_run:
        _write_session_ship_record(repo, files)
        _set_excluded(repo, set(files))
    out['hooks'] = _write_session_hooks(repo, hook_rows, dry_run=dry_run)
    return out


def _write_session_hooks(repo, rows, dry_run=False):
    """.precedent/practice_hooks.json, in process/practice_hooks.json's shape,
    less any hook .claude/settings.json or that tracked file already runs.
    -> the commands it lists. A repository with no .claude/settings.json runs
    no Claude Code hooks, so it gets none, as add_practice_hooks does."""
    import precedent_vendor_engine as pve
    todo = pve._practice_hooks_to_register(repo, rows) or []
    tracked = {c for _e, _m, c in pve._registered_practice_hooks(repo)}
    todo = [t for t in todo if t[2] not in tracked]
    path = pathlib.Path(repo) / SESSION_HOOKS_FILE
    if not dry_run and (todo or path.is_file()):
        text = json.dumps({
            '_comment': 'Untracked, per clone: hooks the practices of a set '
                        'this repository does not track declare. Written by '
                        'tools/precedent_materialize.py at session start; '
                        'run by tools/precedent_hooks.py.',
            'hooks': [{'event': e, 'matcher': m, 'command': c}
                      for e, m, c in todo]}, indent=2) + '\n'
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or path.read_text(encoding='utf-8') != text:
            path.write_text(text, encoding='utf-8')
    return [c for _e, _m, c in todo]


# The permanent hook stub (templates/harness/claude-code/hooks/, since
# 2026-10-07) runs tools/<its own name> and does nothing when that script is
# missing. A source's adapters started shipping it on 2026-10-08, so a sync
# in a repo whose engine predates the move replaced three working hooks
# (commit identity, freshness guard, individual-set setup) with pointers to
# scripts the repo did not have: each then printed one NOTE and let
# everything through. Found by a session that read the diff before
# committing; nothing in the sync said so.
HOOK_STUB_MARKER = b'# PRECEDENT HOOK STUB.'


def _stub_target(data, dest_rel):
    """-> the script under tools/ a stub runs: the one it names outright
    (the individual-source form runs tools/individual-source-bootstrap.sh
    whatever it is installed as), else tools/<its own name>, which the
    generic stub reads from $0."""
    named = re.findall(rb'/tools/([A-Za-z0-9_.-]+\.sh)\b', data)
    if named:
        return named[0].decode('ascii')
    return pathlib.PurePosixPath(dest_rel).name


def _held_adapter(out_dir, dest_rel, data):
    """-> (bytes, executable) of the hook to keep in place of `data`, or None
    to install `data` as usual.

    Kept only when all three hold: `data` is the pointer stub; the script it
    would run, tools/<basename>, is not in this repo; and a hook that is not
    itself the stub is installed at the destination. With nothing installed
    there, the stub loses nothing and is written, and says itself what it
    is waiting for every time it runs."""
    if HOOK_STUB_MARKER not in data:
        return None
    out_dir = pathlib.Path(out_dir)
    dest = out_dir / dest_rel
    if (out_dir / 'tools' / _stub_target(data, dest_rel)).is_file():
        return None
    if not dest.is_file():
        return None
    have = dest.read_bytes()
    if HOOK_STUB_MARKER in have:
        return None
    return have, os.access(dest, os.X_OK)


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


_DEDUP_STATUS_RE = re.compile(rb'^status:([ \t]+)deduplicated[ \t]*$', re.M)
_IN_FORCE_AT_RE = re.compile(rb'^in_force_at:([ \t]+)\S.*$', re.M)


def _as_written(practice):
    """-> the bytes practices/<slug>.md gets: the source file, except that a
    deduplicated copy the resolver kept in force (its target not here yet;
    precedent_resolve.resolve, `kept_in_force`) is written active, so every
    view and check binds it exactly as the copy it stands in for will."""
    data = pathlib.Path(practice['file']).read_bytes()
    if not practice.get('kept_in_force'):
        return data
    data = _DEDUP_STATUS_RE.sub(lambda m: b'status:' + m.group(1) + b'active', data, count=1)
    return _IN_FORCE_AT_RE.sub(lambda m: b'in_force_at:' + m.group(1) + b'null', data, count=1)


def materialize(sources, res, out_dir, dry_run=False, withheld=None,
                declined_ships=None):
    """-> (written, checks_written, adapters_written, rstats) -- see
    _materialize, which does the work and also returns what drift() needs
    about shipped files. The four-tuple is what every caller already
    unpacks, so it stays."""
    r = _materialize(sources, res, out_dir, dry_run=dry_run,
                     withheld=withheld, declined_ships=declined_ships)
    return r['written'], r['checks'], r['adapters'], r['rstats']


def _materialize(sources, res, out_dir, dry_run=False, withheld=None,
                 declined_ships=None):
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

    # A PRACTICE SET'S practices/ HOLDS ONLY ITS OWN RULES (2026-10-19,
    # spec/A_SET_EXPORTS_ONLY_ITS_OWN_RULES.md). Every consumer that declares
    # the set reads that folder as the set's rules, so copies written there
    # would be handed on as the set's own, at the set's level, and frozen.
    # The same bug as a source at --out above, one repository removed. A
    # set's views come from build_views.py, which defers what it declares
    # to .precedent/SESSION_PRACTICES.md.
    if (out_dir / pr.SOURCE_MANIFEST).is_file():
        try:
            own = json.loads((out_dir / pr.SOURCE_MANIFEST)
                             .read_text(encoding='utf-8')).get('name')
        except (OSError, ValueError, AttributeError):
            own = None
        raise MaterializeError(
            f"{out_dir.resolve()} is the practice set {own or '(unnamed)'!s}: "
            f"it has a {pr.SOURCE_MANIFEST} at its root. Its practices/ is "
            f"read by every repository that declares it as the set's own "
            f"rules, so an install never writes another source's practices "
            f"there. Build its views with its own tools/build_views.py; the "
            f"rules it declares reach its sessions through "
            f".precedent/SESSION_PRACTICES.md. A repository that both uses "
            f"Precedent and holds a set keeps the set in a folder of its own "
            f"(`set_root`, spec/VENDORED_SHARED_SETS.md).")

    practices_dir = out_dir / 'practices'
    checks_dir = out_dir / 'tools' / 'checks'

    excluded_engine_dev = sorted(slug for slug, practice in res['practices'].items()
                                  if _is_engine_dev_scoped(practice))
    practice_plan = {slug: (practice, _as_written(practice))
                      for slug, practice in res['practices'].items()
                      if not _is_engine_dev_scoped(practice)}
    checks_plan = _plan_checks(sources, res)   # raises MaterializeError before any write
    adapters_plan = _plan_adapters(sources)    # same -- reads, never writes
    ships_plan, declined_rows = _plan_ships(   # same
        res, _declined_ships(out_dir) if declined_ships is None else declined_ships,
        adapter_dests=[a[0] for a in adapters_plan])

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
    # A practice citing the script it ships (`../tools/create_word_doc.py`)
    # keeps its relative link: this run writes that file.
    planned_out.update(dest for dest, *_rest in ships_plan)
    # A link to a renamed or deduplicated practice points at the stub, which
    # is not in force and so is never written here; send it on to the live
    # slug instead, when this run writes that one.
    forwards = {slug: live for slug, live in pr.forwarding_map(res).items()
                if live in all_slugs}
    forward_files = {str(pathlib.Path(p['file']).resolve()): forwards[p['slug']]
                     for p in res.get('retired', []) if p['slug'] in forwards}
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
                                may_name_source_repo=pr.normalize_level(practice['level']) != 'individual',
                                forwards=forwards, forward_files=forward_files)
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
    adapters_unsaved = []
    held = []
    for dest_rel, source_name, data, executable in adapters_plan:
        dest = out_dir / dest_rel
        keep = _held_adapter(out_dir, dest_rel, data)
        if keep is not None:
            # The working hook stays, recorded as what this tree installed,
            # so --check agrees with it and the next sync after Update
            # Vendors replaces it as an ordinary update.
            data, executable = keep
            held.append(f'{dest_rel} ({source_name})')
        want = hashlib.sha256(data).hexdigest()[:16]
        unsaved = False
        if dest.is_file():
            have = hashlib.sha256(dest.read_bytes()).hexdigest()[:16]
            if have != want and prior_adapters.get(dest_rel) != have:
                # practice: repair-cannot-discard-work -- the shipped files'
                # rule below, 'unsaved' half only: an adapter is machinery
                # every consumer runs, so a committed local copy is still
                # replaced, with git holding what went.
                unsaved = _ship_keep_reason(out_dir, dest_rel, data,
                                            True) == 'unsaved'
                (adapters_unsaved if unsaved else adopted).append(
                    f'{dest_rel} ({source_name})')
        if not dry_run and not unsaved:
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

    if held:
        print("precedent_materialize: KEPT the current hook(s) "
              + ', '.join(held) + ": the source's new version is the "
              "pointer stub, which runs tools/<the hook's name>, and this "
              "repo does not have that script yet -- installing it would "
              "switch the hook off. Run Update Vendors: it brings the "
              "scripts, and the next sync installs the pointer.",
              file=sys.stderr)

    if adopted and not dry_run:
        print("precedent_materialize: harness adapter(s) whose previous "
              "content this tree had not recorded as materialized were "
              "REPLACED -- a hand-copy being adopted, or a committed local "
              "edit being reverted. `git diff` shows exactly what went, "
              "before you commit: " + ', '.join(adopted), file=sys.stderr)
    if adapters_unsaved and not dry_run:
        print("precedent_materialize: harness adapter(s) LEFT UNTOUCHED, not "
              "replaced -- each holds changes no git commit has, and "
              "replacing it would lose them for good. Commit it (the next "
              "sync then replaces it, with git keeping your version), or "
              "delete it and sync again: " + ', '.join(adapters_unsaved),
              file=sys.stderr)

    # Shipped files: written file by file for the reason adapters are, since
    # tools/ also holds the vendored engine and the consumer's own scripts.
    ships_written = []
    prior_ships = _prior_ship_hashes(out_dir)
    ships_adopted = []
    ships_kept = []
    for dest_rel, source_name, slug, data, executable in ships_plan:
        dest = out_dir / dest_rel
        want = hashlib.sha256(data).hexdigest()[:16]
        kept = None
        if dest.is_file():
            have = hashlib.sha256(dest.read_bytes()).hexdigest()[:16]
            if have != want and prior_ships.get(dest_rel) != have:
                kept = _ship_keep_reason(out_dir, dest_rel, data,
                                         dest_rel in prior_ships)
                if kept is None:
                    ships_adopted.append(f'{dest_rel} ({slug}, {source_name})')
        if kept is not None:
            # Recorded with the source's hash, not the kept file's: the
            # manifest says what the set ships, so the next sync asks this
            # same question again rather than taking the kept file for its
            # own and replacing it quietly.
            ships_kept.append({'path': dest_rel, 'why': kept,
                               'label': f'{dest_rel} ({slug}, {source_name})'})
        elif not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            os.chmod(dest, 0o755 if executable else 0o644)
        ships_written.append({'path': dest_rel, 'source': source_name,
                              'practice': slug, 'sha256_16': want,
                              'executable': executable})
    if ships_written and not dry_run:
        # A file this clone had as an untracked session copy (a set the
        # person brought, now declared here) is the tracked tree's from now
        # on: out of info/exclude, so it is committed with the sync.
        release_session_ships(out_dir, [s['path'] for s in ships_written])
    stale_ships = sorted(set(prior_ships) - {s['path'] for s in ships_written}
                         - {d['path'] for d in declined_rows}
                         - _engine_owned(out_dir))
    # A file no practice ships any more is removed in the same sync when it is
    # exactly what was shipped and nothing else here names it
    # (decommission-deletes-files: the audit is those two facts). Left in
    # place, it dropped out of the manifest with this sync and from then on
    # read as the repository's own file, which nobody wrote (a consumer's
    # root-issues report, 2026-10-19: a retired practice's tool). A copy
    # edited here, or one something still names, stays, with the warning.
    removed_ships, stale_kept = [], []
    for rel in stale_ships:
        why = _stale_ship_keep_reason(out_dir, rel, prior_ships.get(rel))
        if why is None:
            removed_ships.append(rel)
            if not dry_run:
                (out_dir / rel).unlink()
        elif why != 'gone':
            stale_kept.append(f'{rel} ({why})')
    if removed_ships and not dry_run:
        print("precedent_materialize: removed shipped file(s) no practice in "
              "force here ships any more -- each unchanged since it was "
              "shipped, and named by nothing else here: "
              + ', '.join(removed_ships), file=sys.stderr)
    if stale_kept and not dry_run:
        print("precedent_materialize: shipped file(s) this tree received that "
              "no practice in force here ships any more -- left in place, not "
              "deleted. Remove each by hand once nothing here uses it: "
              + ', '.join(stale_kept), file=sys.stderr)
    if ships_adopted and not dry_run:
        print("precedent_materialize: shipped file(s) whose previous content "
              "this tree had not recorded as materialized were REPLACED -- a "
              "hand-copy being adopted. Its committed version is in git "
              "(`git diff` shows exactly what went, before you commit). If "
              "that version was a fix, it is owed upstream (practice: "
              "upstream-bug-stops-here); decline the file under "
              f"\"{DECLINED_SHIPS_KEY}\" in precedent.json only if this "
              "repository does not want it at all: "
              + ', '.join(ships_adopted), file=sys.stderr)
    unsaved = [k['label'] for k in ships_kept if k['why'] == 'unsaved']
    ahead = [k['label'] for k in ships_kept if k['why'] == 'ahead']
    if unsaved and not dry_run:
        print("precedent_materialize: shipped file(s) LEFT UNTOUCHED, not "
              "replaced -- each holds changes no git commit has, and "
              "replacing it would lose them for good. Commit it to keep it "
              "as this repository's own version (and carry it to the set "
              "that ships it), or delete it and sync again to take the set's "
              "copy: " + ', '.join(unsaved), file=sys.stderr)
    if ahead and not dry_run:
        print("precedent_materialize: shipped file(s) LEFT UNTOUCHED, not "
              "replaced -- this repository committed its own version after "
              "the set's copy. It is drift until it has its answer (practice: "
              "upstream-bug-stops-here) -- " + _three_answers() + ": "
              + ', '.join(ahead), file=sys.stderr)

    rstats = pr.resident_stats(res)
    if rstats['over_budget']:
        raise MaterializeError(
            f"combined resident block is ~{rstats['tokens']} tokens, over "
            f"the {rstats['budget']}-token cross-source cap -- not "
            f"materializing an over-budget set. Demote or retire a "
            f"resident practice in one of the sources first.")

    manifest = _build_manifest(sources, written, checks_written, rstats,
                               adapters_written, withheld=withheld,
                               excluded_engine_dev=excluded_engine_dev,
                               ships_written=ships_written,
                               declined_ships=declined_rows, base=out_dir)
    if not dry_run:
        write_manifest(out_dir / 'MANIFEST.json', manifest)
    return {'written': written, 'checks': checks_written,
            'adapters': adapters_written, 'rstats': rstats,
            'ships': ships_written, 'declined_ships': declined_rows,
            'ships_kept': ships_kept}


def _three_answers():
    """The three answers an edited upstream-owned file needs, in the words
    tools/upstream_edits.py gives them -- one wording, wherever it is said."""
    try:
        import upstream_edits
        return upstream_edits.THREE_ANSWERS
    except ImportError:
        return ('answer it under "upstream_edits" in precedent.json: '
                'take the set\'s copy, carry the fix upstream, or record a '
                'local need with the person\'s approval')


def _answered_upstream_edits(out_dir):
    """-> the paths that carry a valid answer under "upstream_edits"."""
    try:
        import upstream_edits
        return set(upstream_edits.registry(out_dir)[0])
    except ImportError:
        return set()


def _ship_keep_reason(out_dir, rel, data, delivered_before):
    """Why a shipped file whose content this tree did not write must stay as
    it is -- 'unsaved' or 'ahead' -- or None when replacing it loses nothing.

    practice: repair-cannot-discard-work -- a sync replaces a file only
    where the content it removes survives somewhere: in git, as the version
    HEAD holds. THE INCIDENT (2026-10-16): a repository had an uncommitted
    edit to a file its person's individual set ships a copy of; a sync
    replaced it with the set's older copy and said "`git diff` shows
    exactly what went". It showed nothing -- the file now matched HEAD --
    and the edit was gone.

    'unsaved': git holds no copy of what is there -- the file is untracked,
    the tree is not a git checkout, or the file has uncommitted changes.

    'ahead': the file is committed, and this repository moved it on from
    the set's copy -- the manifest already records a delivery (so the
    commit came after it), or this file's own history holds the set's exact
    bytes. That is a repository that is the ORIGIN of a file a set ships
    back to it: replacing it would revert its own newer work on every
    sync, and it should not need a hand-written `declined_ships` entry to
    stop that loop. Read from the committed manifest wherever it can be, so
    a shallow clone in CI reaches the same answer as the full one."""
    def git(*args, **kw):
        return subprocess.run(['git', '-C', str(out_dir), *args],
                              capture_output=True, **kw)
    if git('ls-files', '--error-unmatch', '--', rel).returncode != 0:
        return 'unsaved'
    if git('diff', '--quiet', 'HEAD', '--', rel).returncode != 0:
        return 'unsaved'
    if delivered_before:
        return 'ahead'
    blob = git('hash-object', '--stdin', input=data)
    if blob.returncode != 0:
        return None
    blob = blob.stdout.decode().strip()
    history = git('log', '--format=', '--raw', '--no-abbrev', 'HEAD', '--', rel)
    if history.returncode == 0 and any(
            line.split()[3:4] == [blob]
            for line in history.stdout.decode(errors='replace').splitlines()
            if line.startswith(':')):
        return 'ahead'
    return None


def write_manifest(mf, manifest):
    """Write MANIFEST.json, keeping the old generated_at_utc when nothing
    else changed. The stamp says when this snapshot was produced, and a run
    that produced the same snapshot did not produce a new one. 2026-09-28:
    every Update Vendors rewrote only this field, leaving a one-line diff to
    commit or throw away each time."""
    try:
        old = json.loads(mf.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        old = None
    if isinstance(old, dict) and old.get('generated_at_utc'):
        strip = lambda d: {k: v for k, v in d.items() if k != 'generated_at_utc'}
        if strip(old) == strip(manifest):
            manifest = dict(manifest, generated_at_utc=old['generated_at_utc'])
    mf.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n',
                  encoding='utf-8')


# Where a source sits, as the manifest records it. A source inside the
# directory the manifest describes is recorded relative to it, as
# precedent.json declares it: the resolved absolute path named the checkout
# that ran the sync, so the same commit checked from another checkout --
# the throwaway worktree a Promote checks its composition in, or another
# machine -- "differed from what a fresh sync writes" with nothing stale
# (a consumer's Promote, 2026-10-04). A source outside it keeps its absolute
# path: that is where this machine found it, nothing else can say so, and
# _check compares only its level and name.
def _manifest_source_path(path, base):
    try:
        rel = pathlib.Path(path).resolve().relative_to(pathlib.Path(base).resolve())
    except (ValueError, OSError, TypeError):
        return path
    return rel.as_posix() or '.'


def _outside(entry):
    """True for a recorded source path outside the manifest's directory."""
    path = str((entry or {}).get('path') or '')
    return path.startswith(('/', '~')) or '..' in pathlib.PurePosixPath(path).parts


def _source_entry(source, base):
    """One `sources` entry. A source read from a git checkout outside this
    tree also records the COMMIT it was read at (precedent_source_pins.py):
    the views check reads the source back at that commit, so its answer
    depends on neither the clone's checkout nor how far the source has moved
    since. A checkout with uncommitted changes records none -- those changes
    are on no commit anybody else can read."""
    shown = source.get('clone_path') or source['path']
    entry = {'level': source['level'], 'name': source['name'],
             'path': (shown if base is None
                      else _manifest_source_path(shown, base))}
    if base is not None and _outside(entry):
        commit = psp.head_commit(source['path'])
        if commit and not psp.is_dirty(source['path']):
            entry['commit'] = commit
    return entry


def _with_owner(entry, source, written):
    """An individual source's entry, with whose set it is: {github, name,
    email, timezone} from the set's own identity.json, when this tree holds
    at least one of its practices. That tracked copy is a saved copy of one
    person's rules, and a session loads it only for that person
    (precedent_audience.saved_copy_state; spec/VENDORED_SHARED_SETS.md,
    2026-10-19). A set whose identity.json names no GitHub login gets no
    record, so its saved copy loads for nobody -- said here, once."""
    if pr.normalize_level(source.get('level')) != 'individual':
        return entry
    if not any(pr.normalize_level(w.get('level')) == 'individual'
               and w.get('source') == source.get('name') for w in written):
        return entry
    try:
        import precedent_identity as _pid
        ident = _pid.read_identity_file(
            pathlib.Path(source['path']) / 'identity.json') or {}
    except Exception:                                         # noqa: BLE001
        ident = {}
    if not ident.get('github'):
        print(f"precedent_materialize: {source.get('name')}'s identity.json "
              f"names no github login, so its saved copy here will load for "
              f"nobody", file=sys.stderr)
        return entry
    entry['owner'] = {'github': ident['github'], 'name': ident.get('name') or '',
                      'email': ident.get('email') or '',
                      'timezone': ident.get('timezone') or ''}
    return entry


def _build_manifest(sources, written, checks_written, rstats,
                    adapters_written=(), withheld=None,
                    excluded_engine_dev=None, ships_written=(),
                    declined_ships=(), base=None):
    """`withheld` names the slugs a PUBLIC repo's visibility keeps out of this
    tree -- recorded because "absent" and "never existed" look identical on
    disk, and several checks turn that difference into a finding.

    Without it, `rename-updates-links` reads a document's link to a withheld
    practice as a reference to a file "this branch deleted" and asks for it to
    be repointed -- at something that cannot exist here. Found 2026-09-07:
    excluding a public consumer's private practices produced 26 such findings
    in one repo, six of them inside a vendored tree nobody can edit there. The
    practices were not renamed or deleted; they are published elsewhere and
    withheld here, which is a third state those checks had no way to see.

    `excluded_engine_dev` is a DIFFERENT third state, on a different axis:
    slugs resolved with `scope: engine-dev`, which this repo (whichever one
    this run is materializing INTO) is deliberately never given, regardless
    of that repo's visibility. Recorded separately from `withheld` rather
    than folded into it -- one is about who may see a practice, the other
    about who could ever act on it, and the two lists can overlap for
    unrelated reasons (name-both-sides-of-ledger: keep what is excluded and
    why distinguishable, not just the fact that something was)."""
    manifest = {
        'generated_by': 'tools/precedent_materialize.py',
        'generated_at_utc': precedent_time.utc_iso(),
        'note': 'DERIVED ARTIFACT -- never hand-edit. Regenerate by re-running '
                'precedent_materialize.py with the same --repo/--user-config; '
                'this file records exactly what produced the snapshot so drift '
                'is visible, per generated-artifact-provenance.',
        'sources': [_with_owner(_source_entry(s, base), s, written)
                    for s in sources],
        'resident': rstats,
        'practices': written,
        'checks': checks_written,
        'adapters': list(adapters_written),
        'withheld': sorted(withheld or []),
        'excluded_engine_dev': sorted(excluded_engine_dev or []),
    }
    # Written only when there is something to say. Every consumer that ships
    # nothing would otherwise see its MANIFEST.json change on the first sync
    # after this engine arrives, over two empty lists.
    if ships_written:
        manifest['ships'] = list(ships_written)
    if declined_ships:
        manifest[DECLINED_SHIPS_KEY] = sorted(declined_ships,
                                              key=lambda d: d['path'])
    return manifest


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
    plan = _materialize(sources, res, out_dir, withheld=withheld, dry_run=True)
    written, checks_written = plan['written'], plan['checks']
    adapters_written, rstats = plan['adapters'], plan['rstats']
    # Derived from res alone, so -- unlike withheld -- it is safe to
    # recompute here rather than thread through: the same bug shape as the
    # withheld one above, caught the same way, by --check refusing to agree
    # with itself.
    excluded_engine_dev = sorted(slug for slug, practice in res['practices'].items()
                                  if _is_engine_dev_scoped(practice))
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

    # Shipped files: the adapters' comparison, for the adapters' reason --
    # tools/ is not this tool's to sweep.
    kept = {k['path']: k['why'] for k in plan['ships_kept']}
    for f in plan['ships']:
        dest = out_dir / f['path']
        label = f"shipped by {f['practice']}, {f['source']}"
        if kept.get(f['path']) == 'ahead':
            # This repository committed its own version after the set's. A
            # sync keeps it (practice: repair-cannot-discard-work), and it is
            # still drift until it has its answer (practice:
            # upstream-bug-stops-here, 2026-10-17): usually the fix belongs
            # in the set, or the set already has another one.
            if f['path'] not in _answered_upstream_edits(out_dir):
                found.append(f"{f['path']} was committed here after the set's "
                              f"copy ({label}), so a sync keeps it -- "
                              f"{_three_answers()}")
            continue
        if kept.get(f['path']) == 'unsaved':
            found.append(f"{f['path']} holds changes no git commit has, so a "
                          f"sync leaves it untouched ({label}) -- commit it "
                          f"to keep it as this repository's own version, or "
                          f"delete it and sync again to take the set's copy")
            continue
        if not dest.is_file():
            found.append(f"{f['path']} is missing -- a fresh sync delivers it "
                          f"({label})")
        elif hashlib.sha256(dest.read_bytes()).hexdigest()[:16] != f['sha256_16']:
            found.append(f"{f['path']} differs from what a fresh sync delivers "
                          f"({label}) -- "
                          + _ship_drift_advice(out_dir, f['source'], f['path'], dest))
        elif os.access(dest, os.X_OK) != f['executable']:
            want_x = 'executable' if f['executable'] else 'not executable'
            found.append(f"{f['path']} is {'not ' if f['executable'] else ''}"
                          f"executable and a fresh sync delivers it {want_x} "
                          f"({label})")
    for path in sorted(set(_prior_ship_hashes(out_dir))
                       - {f['path'] for f in plan['ships']}
                       - {d['path'] for d in plan['declined_ships']}):
        found.append(f"{path} was delivered as a shipped file and no practice "
                      f"in force here ships it any more -- a sync leaves it in "
                      f"place and reports it")

    # generated_at_utc is a timestamp, not state -- comparing it would make
    # every run report drift against itself.
    mf = out_dir / 'MANIFEST.json'
    want = _build_manifest(sources, written, checks_written, rstats,
                           adapters_written, withheld=withheld,
                           excluded_engine_dev=excluded_engine_dev,
                           ships_written=plan['ships'],
                           declined_ships=plan['declined_ships'], base=out_dir)
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
            # A source outside this directory is compared by level and name:
            # its path is where the checkout that synced found it, which
            # another machine's layout changes with nothing stale. Its
            # commit is provenance, like the timestamp: the content it
            # produced is what is compared, file by file, above.
            for side in (have, want_cmp):
                if isinstance(side.get('sources'), list):
                    side['sources'] = [
                        {k: v for k, v in e.items() if k not in ('path', 'commit')}
                        if isinstance(e, dict) and _outside(e) else e
                        for e in side['sources']]
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
        if tok in _BARE_FLAGS:
            args[tok] = True
            i += 1
            continue
        if not tok.startswith('--') or i + 1 >= len(argv):
            sys.exit(f"precedent_materialize FAIL: expected --flag value pairs, stuck at {tok!r}")
        args[tok] = argv[i + 1]
        i += 2
    return args


# Flags that take no value.
_BARE_FLAGS = ('--allow-missing-sources',)


def _refuse_direct_run(repo, sources, res, allow_missing=False):
    """-> a refusal message, or None when a direct run may write.

    precedent_sync_views.py is the route a consuming repo syncs by, and the
    only one that (a) withholds a private source's practice text from a
    PUBLIC repo's tracked tree and (b) refuses to write from a source set
    missing a member. Run directly, this tool did neither: reproduced on
    2026-10-17, a scratch consumer declaring `visibility: public` with an
    individual source got that set's practices and check scripts under its
    tracked tree, and MANIFEST.json recorded `withheld: []` beside the
    individual source's name, absolute path and commit; with a source
    unreachable it said "Materializing WITHOUT it" and rewrote practices/
    anyway. Refusing here, rather than duplicating the wrapper's withholding,
    keeps one implementation of it (judgment-check-or-tool)."""
    if pr.bv.repo_is_practice_source(pathlib.Path(repo)):
        # A set carries this module for its session file (2026-10-17), never
        # to materialize into: its practices/ is its own, and a write here
        # replaces it with every source it resolves.
        return (f"refusing to materialize into {repo}, which is a practice "
                f"set: its practices/ is its own catalogue, and materializing "
                f"would replace it with every source it resolves. The sets' "
                f"session file is tools/precedent_session_practices.py")
    route = (f"Sync through tools/precedent_sync_views.py --repo {repo} "
             f"instead: it is the route a consuming repo syncs by")
    if pr.bv.repo_is_public(pathlib.Path(repo)):
        private = sorted({pr.declared_level(p) for p in res['practices'].values()
                          if pr.declared_level(p) in pr.bv.PRIVATE_LEVELS})
        if private:
            return (f"refusing to materialize {', '.join(private)}-level "
                    f"practice text into {repo}, which is public (its "
                    f"precedent.json declares `visibility: public`, or "
                    f"declares none, which counts as public). Its practices/ "
                    f"tree is tracked, so the text would be published. "
                    f"{route}, and it withholds that text while those "
                    f"practices still bind through "
                    f".precedent/SESSION_PRACTICES.md.")
    if res['missing'] and not allow_missing:
        names = ', '.join(f"{m['level']}/{m['name']} ({m['reason']})"
                          for m in res['missing'])
        return (f"refusing to WRITE from an incomplete source set: {names} "
                f"did not resolve. Writing anyway DELETES every practice "
                f"those sources contribute from {repo}'s tracked tree. Make "
                f"them resolvable and re-run. {route}, and it refuses the "
                f"same way; pass --allow-missing-sources here only if the "
                f"removal is what you mean.")
    return None



def main():
    args = _parse_args(sys.argv[1:])
    out = args.get('--out')
    if not out:
        sys.exit("precedent_materialize FAIL: --out DIR is required")
    repo = args.get('--repo', str(ROOT))
    user_config = args.get('--user-config')

    try:
        loaded = pr.load_config(repo, user_config)
        # A set a person brings is theirs, never the repository's: like the
        # wrapper (precedent_sync_views._sync), write only the declared
        # sources, with a brought set as context for what is in force.
        sources = [s for s in loaded if not s.get('brought')]
        brought = [s for s in loaded if s.get('brought')]
        if not sources:
            sys.exit(f"precedent_materialize FAIL: no practice sources are "
                      f"declared for {repo} (see precedent_resolve.py's own "
                      f"error for the same case).")
        res = pr.resolve(sources, context=brought)
    except pr.ResolveError as e:
        sys.exit(f"precedent_materialize FAIL: {e}")

    why = _refuse_direct_run(repo, sources, res,
                             allow_missing=bool(args.get('--allow-missing-sources')))
    if why:
        sys.exit(f"precedent_materialize FAIL: {why}")
    for m in res['missing']:
        print(f"precedent_materialize: the {m['level']} source {m['name']!r} "
              f"is not available ({m['reason']}). Materializing WITHOUT it "
              f"(--allow-missing-sources).",
              file=sys.stderr)

    try:
        r = _materialize(sources, res, pathlib.Path(out))
    except MaterializeError as e:
        sys.exit(f"precedent_materialize FAIL: {e}")
    written, checks_written = r['written'], r['checks']
    adapters_written, rstats = r['adapters'], r['rstats']

    print(f"materialized {len(written)} practice(s), {len(checks_written)} "
          f"check script(s)/test(s), {len(adapters_written)} harness "
          f"adapter(s) and {len(r['ships'])} shipped file(s) from "
          f"{len(sources)} source(s) into {out}")
    if r['declined_ships']:
        print('declined here: ' + ', '.join(
            f"{d['path']} ({d['reason']})" for d in r['declined_ships']))
    print(f"resident block: ~{rstats['tokens']} of {rstats['budget']} token budget")
    print(f"manifest: {pathlib.Path(out) / 'MANIFEST.json'}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

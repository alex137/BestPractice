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

THIS TOOL DOES THE CONTENT HALF ONLY: it writes the resolved practices/
tree plus each source's own tools/checks/ (a checked_by claim has nothing
behind it if only practices/ is copied — engine-plus-host-shims: the engine
travels with what it enforces). It does NOT vendor the engine scripts
themselves (build_views.py, precedent_paths.py, etc.) — that half is
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
resident set, or a checks/ filename collision.
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
# the product. precedent-team-maintainers' own light check had already had
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
    and a consuming repo can be public -- themorgan/WorkingWithAI is. Caught
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
    precedent-team-maintainers, whose `deep-check` practice is retired --
    its `check_deep_check.py` was still copied into the consuming repo,
    where it registered under its own filename (no practice to name it),
    reported "not in force", and counted as an unexplained file against
    the consuming repo's own materialized-tree audit.

    Deliberately narrower than 'every file in tools/checks/': a source's
    own tools/checks/tests/run_all.sh (found colliding on the very first
    real run of this tool, both private sets carry one) is a per-repo test
    DRIVER, not a per-check test a `checked_by` claim could ever name --
    merging it would be a false collision over a file nothing actually
    needs merged. Skipped explicitly and reported, never silently."""
    owner_of = {}   # 'rel_label/filename' -> source name that already claimed it
    plan, skipped, orphaned = [], [], []
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
                if not f.name.startswith('test_'):
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
    return plan


def materialize(sources, res, out_dir, dry_run=False):
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

    rstats = pr.resident_stats(res)
    if rstats['over_budget']:
        raise MaterializeError(
            f"combined resident block is ~{rstats['tokens']} tokens, over "
            f"the {rstats['budget']}-token cross-source cap -- not "
            f"materializing an over-budget set. Demote or retire a "
            f"resident practice in one of the sources first.")

    manifest = _build_manifest(sources, written, checks_written, rstats)
    if not dry_run:
        (out_dir / 'MANIFEST.json').write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return written, checks_written, rstats


def _build_manifest(sources, written, checks_written, rstats):
    return {
        'generated_by': 'tools/precedent_materialize.py',
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc)
                                 .isoformat(timespec='seconds'),
        'note': 'DERIVED ARTIFACT -- never hand-edit. Regenerate by re-running '
                'precedent_materialize.py with the same --repo/--user-config; '
                'this file records exactly what produced the snapshot so drift '
                'is visible, per generated-artifact-provenance.',
        'sources': [{'level': s['level'], 'name': s['name'], 'path': s['path']}
                    for s in sources],
        'resident': rstats,
        'practices': written,
        'checks': checks_written,
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
def drift(sources, res, out_dir):
    """-> [str] findings describing how out_dir differs from a fresh sync.

    Writes nothing. An empty list means the committed materialized tree is
    exactly what a sync would produce right now."""
    out_dir = pathlib.Path(out_dir)
    written, checks_written, rstats = materialize(sources, res, out_dir,
                                                  dry_run=True)
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

    # generated_at_utc is a timestamp, not state -- comparing it would make
    # every run report drift against itself.
    mf = out_dir / 'MANIFEST.json'
    want = _build_manifest(sources, written, checks_written, rstats)
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
        written, checks_written, rstats = materialize(sources, res, pathlib.Path(out))
    except MaterializeError as e:
        sys.exit(f"precedent_materialize FAIL: {e}")

    print(f"materialized {len(written)} practice(s) and {len(checks_written)} "
          f"check script(s)/test(s) from {len(sources)} source(s) into {out}")
    print(f"resident block: ~{rstats['tokens']} of {rstats['budget']} token budget")
    print(f"manifest: {pathlib.Path(out) / 'MANIFEST.json'}")
    return 0


if __name__ == '__main__':
    sys.exit(main())

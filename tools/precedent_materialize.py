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
    is someone's hand-authored content, with no other copy anywhere
    (precedent_resolve.py's load_config only guarantees a repo-local
    source's path stays INSIDE the declaring repo, not that it differs
    from the sync target -- `path: "."` still resolves there by design,
    since a subdirectory is a convention, not a safety rule the resolver
    itself enforces).

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


def _plan_checks(sources):
    """Read every source's per-check tools/checks/check_*.py and
    tools/checks/tests/test_*.sh INTO MEMORY, refusing a same-name
    collision across different sources rather than letting the last one
    silently win. Returns a write plan (rel_label, filename, source_name,
    bytes) and does not touch the filesystem at all -- see materialize()
    for why reading has to fully finish before anything is deleted.

    Deliberately narrower than 'every file in tools/checks/': a source's
    own tools/checks/tests/run_all.sh (found colliding on the very first
    real run of this tool, both private sets carry one) is a per-repo test
    DRIVER, not a per-check test a `checked_by` claim could ever name --
    merging it would be a false collision over a file nothing actually
    needs merged. Skipped explicitly and reported, never silently."""
    owner_of = {}   # 'rel_label/filename' -> source name that already claimed it
    plan, skipped = [], []

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
            if f.name.startswith('check_'):
                claim(f, 'checks', s['name'])
            else:
                skipped.append(f'tools/checks/{f.name} ({s["name"]})')
        src_tests = src_checks / 'tests'
        if src_tests.is_dir():
            for f in sorted(src_tests.glob('*.sh')):
                if f.name.startswith('test_'):
                    claim(f, 'checks/tests', s['name'])
                else:
                    skipped.append(f'tools/checks/tests/{f.name} ({s["name"]})')
    if skipped:
        print(f"precedent_materialize: not a per-check file, not vendored: "
              + ', '.join(skipped), file=sys.stderr)
    return plan


def materialize(sources, res, out_dir):
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
    held in memory, whether or not its original path just got wiped."""
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
            f"subdirectory (e.g. \"local\", holding local/practices/ -- "
            f"the repo-local convention PRACTICE_ENGINE_PLAN.md's "
            f"\"Source\" section recommends) so its tree and "
            f"materialize()'s output are physically separate.")

    practices_dir = out_dir / 'practices'
    checks_dir = out_dir / 'tools' / 'checks'

    practice_plan = {slug: (practice, pathlib.Path(practice['file']).read_bytes())
                      for slug, practice in res['practices'].items()}
    checks_plan = _plan_checks(sources)   # raises MaterializeError before any write

    if practices_dir.exists():
        shutil.rmtree(practices_dir)
    if checks_dir.exists():
        shutil.rmtree(checks_dir)
    practices_dir.mkdir(parents=True)

    written = []
    for slug, (practice, data) in sorted(practice_plan.items()):
        dest = practices_dir / f'{slug}.md'
        dest.write_bytes(data)
        written.append({'slug': slug, 'level': practice['level'],
                         'source': practice['source'],
                         'sha256_16': hashlib.sha256(data).hexdigest()[:16]})

    checks_written = []
    for rel_label, filename, source_name, data in checks_plan:
        dest_dir = checks_dir if rel_label == 'checks' else checks_dir / 'tests'
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

    manifest = {
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
    (out_dir / 'MANIFEST.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return written, checks_written, rstats


def _parse_args(argv):
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

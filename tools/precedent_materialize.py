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


def _hash_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:16]


def _copy_checks(sources, out_dir):
    """Merge every source's per-check tools/checks/check_*.py and
    tools/checks/tests/test_*.sh into out_dir/tools/checks/, refusing a
    same-name collision across different sources rather than letting the
    last one silently win.

    Deliberately narrower than 'every file in tools/checks/': a source's
    own tools/checks/tests/run_all.sh (found colliding on the very first
    real run of this tool, both private sets carry one) is a per-repo test
    DRIVER, not a per-check test a `checked_by` claim could ever name --
    merging it would be a false collision over a file nothing actually
    needs merged. Skipped explicitly and reported, never silently."""
    checks_dir = out_dir / 'tools' / 'checks'
    tests_dir = checks_dir / 'tests'
    owner_of = {}   # filename -> source name that already placed it
    copied, skipped = [], []

    def place(src_file, dest_dir, rel_label):
        dest_dir.mkdir(parents=True, exist_ok=True)
        key = f'{rel_label}/{src_file.name}'
        prior = owner_of.get(key)
        if prior is not None and prior != s['name']:
            raise MaterializeError(
                f"tools/checks/{key} exists in both {prior!r} and "
                f"{s['name']!r} -- a filename collision across sources. "
                f"Pick one, or rename one of them before materializing.")
        owner_of[key] = s['name']
        dest = dest_dir / src_file.name
        shutil.copyfile(src_file, dest)
        copied.append({'path': f'tools/checks/{key}', 'source': s['name'],
                        'sha256_16': _hash_file(src_file)})

    for s in sources:
        src_checks = pathlib.Path(s['path']) / 'tools' / 'checks'
        if not src_checks.is_dir():
            continue
        for f in sorted(src_checks.glob('*.py')):
            if f.name.startswith('check_'):
                place(f, checks_dir, 'checks')
            else:
                skipped.append(f'tools/checks/{f.name} ({s["name"]})')
        src_tests = src_checks / 'tests'
        if src_tests.is_dir():
            for f in sorted(src_tests.glob('*.sh')):
                if f.name.startswith('test_'):
                    place(f, tests_dir, 'checks/tests')
                else:
                    skipped.append(f'tools/checks/tests/{f.name} ({s["name"]})')
    if skipped:
        print(f"precedent_materialize: not a per-check file, not vendored: "
              + ', '.join(skipped), file=sys.stderr)
    return copied


def materialize(sources, res, out_dir):
    out_dir = pathlib.Path(out_dir)
    practices_dir = out_dir / 'practices'
    checks_dir = out_dir / 'tools' / 'checks'
    if practices_dir.exists():
        shutil.rmtree(practices_dir)
    if checks_dir.exists():
        shutil.rmtree(checks_dir)
    practices_dir.mkdir(parents=True)

    written = []
    for slug, practice in sorted(res['practices'].items()):
        dest = practices_dir / f'{slug}.md'
        shutil.copyfile(practice['file'], dest)
        written.append({'slug': slug, 'level': practice['level'],
                         'source': practice['source'],
                         'sha256_16': _hash_file(dest)})

    checks_written = _copy_checks(sources, out_dir)

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

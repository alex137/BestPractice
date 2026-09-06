#!/usr/bin/env python3
"""parse_check.py -- does every machine-readable file in scope still parse?

ONE validator, TWO scopes, because the two checks it serves answer
different questions:

  deep check (tools/verify_harness.py) -- the files this change TOUCHED.
      It gates a push, runs constantly, and its job is "did I just break
      something", not "is the whole repo well".
  very deep check (tools/very_deep_check.py) -- every tracked file.
      On-demand, whole-repo, and the only place a file nobody has touched
      in months gets looked at again.

WHY THIS EXISTS. Nothing here parsed a YAML or JSON file at all until
2026-09-06 -- not .github/workflows/deep-check.yml, the file that RUNS the
deep check in CI, and not precedent.json, MANIFEST.json,
ENGINE_MANIFEST.json or routing_scope.json, each of which is read by
exactly one tool that would report its own confusing failure rather than
"this file is malformed". A broken workflow is the worst of these: GitHub
skips it silently, so the gate stops running and every push looks as green
as the day before.

The general question is "does anything validate this file type at all",
and it is worth asking of every format a repo commits, not just these two.
JSON and YAML are what this repo actually has.

affordance-is-shared: consuming repos get equivalent coverage on changed
files from the team set's own light check, so this is not vendored. If a
consumer ever wants the whole-tree sweep, this is the module to vendor.
"""
import json
import pathlib
import subprocess
import sys

JSON_SUFFIXES = ('.json',)
YAML_SUFFIXES = ('.yml', '.yaml')


def _is_candidate(rel):
    base = rel[:-len('.template')] if rel.endswith('.template') else rel
    return base.endswith(JSON_SUFFIXES + YAML_SUFFIXES)


def candidates(root, paths):
    """The subset of `paths` this module knows how to parse."""
    return [p for p in paths if _is_candidate(p)]


def validate(root, paths):
    """-> ([(rel, reason)] failures, [kinds actually parsed], [skipped kinds]).

    A format with no parser available is reported as SKIPPED, never as
    passing: a file nobody parsed is not a file that parses.
    """
    root = pathlib.Path(root)
    try:
        import yaml
    except ImportError:
        yaml = None

    failures, parsed, skipped = [], set(), set()
    for rel in candidates(root, paths):
        p = root / rel
        if not p.is_file():
            continue                      # deleted in this change
        base = rel[:-len('.template')] if rel.endswith('.template') else rel
        try:
            text = p.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError) as e:
            failures.append((rel, f'could not be read: {e}'))
            continue
        if base.endswith(JSON_SUFFIXES):
            parsed.add('JSON')
            try:
                json.loads(text)
            except json.JSONDecodeError as e:
                failures.append((rel, f'not valid JSON -- {e}'))
        else:
            if yaml is None:
                skipped.add('YAML')
                continue
            parsed.add('YAML')
            try:
                yaml.safe_load(text)
            except Exception as e:
                failures.append((rel, f'not valid YAML -- {str(e).splitlines()[0]}'))
    return failures, sorted(parsed), sorted(skipped)


def tracked(root):
    r = subprocess.run(['git', '-C', str(root), 'ls-files'],
                       capture_output=True, text=True)
    return r.stdout.split() if r.returncode == 0 else []


def _base_ref(root):
    head = subprocess.run(
        ['git', '-C', str(root), 'symbolic-ref', 'refs/remotes/origin/HEAD'],
        capture_output=True, text=True)
    if head.returncode == 0 and head.stdout.strip():
        return head.stdout.strip().replace('refs/remotes/', '', 1)
    for cand in ('origin/main', 'origin/master'):
        if subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify',
                           '--quiet', cand],
                          capture_output=True).returncode == 0:
            return cand
    return None


def changed(root):
    """-> (paths, scope_label). Falls back to the whole tree, and SAYS so.

    Never silently narrows: a check that quietly scoped itself to nothing
    is the failure mode this repo has hit repeatedly (see AGENTS.md's
    gotchas on doc_lint's changed-vs-default-branch scope on a shallow
    clone). If there is no base to diff against, the honest answer is to
    scan everything and label it.
    """
    root = pathlib.Path(root)
    base = _base_ref(root)
    if base is None:
        return tracked(root), 'whole tree (no published default branch to diff against)'
    out = set()
    for args in (['diff', '--name-only', '--diff-filter=d', f'{base}...HEAD'],
                 ['diff', '--name-only', '--diff-filter=d'],
                 ['diff', '--name-only', '--diff-filter=d', '--cached'],
                 ['ls-files', '--others', '--exclude-standard']):
        r = subprocess.run(['git', '-C', str(root)] + args,
                           capture_output=True, text=True)
        if r.returncode == 0:
            out.update(x for x in r.stdout.split() if x)
    return sorted(out), f'changed vs {base}'


def main():
    root = pathlib.Path(__file__).resolve().parents[1]
    if '--all' in sys.argv[1:]:
        paths, scope = tracked(root), 'whole tree'
    else:
        paths, scope = changed(root)
    failures, parsed, skipped = validate(root, paths)
    n = len(candidates(root, paths))
    for rel, why in failures:
        print(f"  {rel}: {why}")
    if skipped:
        print(f"parse_check SKIPPED {', '.join(skipped)}: no parser installed "
              f"(pip install pyyaml). A file nobody parsed is not a file that parses.")
    if failures:
        print(f"parse_check FAIL: {len(failures)} of {n} file(s) in scope "
              f"({scope}) do not parse.")
        return 1
    print(f"parse_check OK: {n} file(s) parse ({', '.join(parsed) or 'none in scope'}; "
          f"scope: {scope}).")
    return 0


if __name__ == '__main__':
    sys.exit(main())

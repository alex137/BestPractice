#!/usr/bin/env python3
"""precedent_vendor_engine.py — vendors Precedent's minimal SOURCE-repo
engine into a repo that is an individual or team practice SET, not a
four-source consumer.

THE GAP THIS CLOSES. tools/precedent_bootstrap_source.py has only ever
written practice content, config, approvers and the leak-blocklist — never
an engine file. Every individual/team set that exists today
(precedent-individual, precedent-team-maintainers, precedent-team-tms) got
its tools/build_views.py, precedent_gate.py, precedent_paths.py,
precedent_show.py and split_practices.py into place by an undocumented,
one-off hand-copy, so none of them can tell a stale copy from a current
one, and precedent-team-tms's copy is simply missing outright. This tool
makes that copy a real, tracked, mechanically-refreshable one instead.

Distinct from tools/checkin.py, which mirrors a CONSUMER's whole
process/upstream/ tree, deleting anything the tree no longer has, in BOTH
directions (a consumer pulls upstream content AND pushes its own
check-ins back). A pure source repo's engine is one-directional —
downstream from BestPractice only, since a source has no content of its
own to contribute back to the engine — and it sits inside tools/
ALONGSIDE non-vendored, repo-owned files (tools/checks/, routing_scope.json
is vendored but trimmed, precedent-team-maintainers' own
build_codeowners.py) that a whole-directory mirror-and-delete would
destroy. So this is a NEW, narrower tool, not an extension of checkin.py:
it touches only the files it knows about, by name.

ENGINE_FILES is what a source repo needs to run its own AGENTS.md loader
block (precedent_show.py's Rule/Detail/Why/Story/Install split,
build_views.py's `--agents-only` regeneration, precedent_paths.py's
path-trigger channel, precedent_gate.py's closed gate vocabulary) — never
precedent_materialize.py/precedent_resolve.py/precedent_sync_views.py,
which only a four-source CONSUMER needs (see spec/BOOTSTRAP_NEW_SOURCES.md
and this repo's own practice engine-plus-host-shims: "domain-neutral
mechanism lives in the vendored tree ... host-specific ... lives in a thin
shim"). This script names itself last in ENGINE_FILES, on purpose: it
travels WITH the engine it defines, so a future improvement to the
vendoring mechanism itself reaches every already-bootstrapped source the
same way an improvement to build_views.py does — not a second,
undocumented gap one layer up from the one this tool closes.

routing_scope.json is vendored too, but it is not a byte-identical copy:
precedent_gate.py's SCOPE file carries two things in this repo — the
closed GATE vocabulary (`gates_meta`/`gates`, the moments a practice can
fire at, which is the same everywhere Precedent's loader runs) and a
`practices` key documenting the routing reason for every one of
BestPractice's OWN 60-odd practices, which has no meaning in a source
repo with a different catalogue entirely. `_trim_routing_scope` below
keeps only the first and drops the second — the same trim a prior,
undocumented hand-copy already applied to precedent-individual and
precedent-team-maintainers (confirmed byte-identical to each other before
this tool existed); this tool just makes that trim mechanical instead of
a fact only the session that did it once remembered.

Four subcommands:

  seed <dest-dir>                Run from BESTPRACTICE'S OWN checkout (the
                                  case tools/precedent_bootstrap_source.py
                                  needs — no clone required, the source IS
                                  this checkout). Copies ENGINE_FILES and a
                                  trimmed routing_scope.json into
                                  <dest-dir>/tools/, and writes
                                  <dest-dir>/tools/ENGINE_MANIFEST.json
                                  recording this checkout's HEAD commit and
                                  a sha256 per vendored file.

  status <bestpractice-clone>    Run from an ALREADY-BOOTSTRAPPED source
                                  repo (same shape checkin.py's verbs use):
                                  compares the vendored files against
                                  ENGINE_MANIFEST.json's recorded hashes
                                  (local hand-edit?) and against the
                                  clone's current tools/ (upstream moved?).
                                  Exit 1 if either differs.

  refresh <bestpractice-clone> [--force]
                                  Pulls the clone's SOURCE_BRANCH (see
                                  below — NOT the clone's configured
                                  default branch), refuses if a vendored
                                  file was hand-edited since the last
                                  seed/refresh (its sha256 no longer
                                  matches ENGINE_MANIFEST.json) unless
                                  --force, then re-copies + re-trims and
                                  updates the manifest.

  fresh                          Clone-free staleness notice, no argument
                                  needed: one `git ls-remote` of
                                  ENGINE_MANIFEST.json's recorded repo,
                                  compared to the recorded commit. Always
                                  exits 0 (a notice, never a gate); silent
                                  on network failure vs. loud on a fast,
                                  clean failure (checkin.py's fresh() carries
                                  the same distinction and the same reason:
                                  an unreachable remote must never read as
                                  "confirmed fresh").

Run (from a source repo's own checkout, once vendored):
  python3 tools/precedent_vendor_engine.py fresh
  python3 tools/precedent_vendor_engine.py status  ../BestPractice
  python3 tools/precedent_vendor_engine.py refresh ../BestPractice

SOURCE_BRANCH is 'precedent-beta-v01', not BestPractice's configured
default branch ('main') — see local/practices/merge-target-is-beta-branch.md:
until Alex's deliberate phase-7 fold-in, routine engine work lands on
precedent-beta-v01, and 'main' is stale for this purpose. That practice's
own retirement clause applies here too: the moment the fold-in happens,
change SOURCE_BRANCH to 'main' in this one place, in the same PR.
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
ENGINE_DIR = HERE.parent
ROOT = ENGINE_DIR.parent
SOURCE_REPO = 'https://github.com/alex137/BestPractice'
SOURCE_BRANCH = 'precedent-beta-v01'  # see docstring: NOT the configured default

ENGINE_FILES = [
    'build_views.py',
    'precedent_gate.py',
    'precedent_paths.py',
    'precedent_show.py',
    'split_practices.py',
    'precedent_vendor_engine.py',
]
MANIFEST_NAME = 'ENGINE_MANIFEST.json'


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _trim_routing_scope(engine_dir):
    """BestPractice's own tools/routing_scope.json, reduced to just the
    closed gate vocabulary — see docstring. Read from wherever THIS script
    physically sits (engine_dir), not from a fixed ROOT, so it works
    identically whether called during `seed` (engine_dir == BestPractice's
    own tools/) or, in principle, from a future clone-based path."""
    full = json.loads((engine_dir / 'routing_scope.json').read_text(encoding='utf-8'))
    return {
        '_note': [
            'Vendored from alex137/BestPractice (tools/routing_scope.json), trimmed to',
            'just the closed gate vocabulary tools/precedent_gate.py needs -- the',
            "source file's own `practices` key documents the routing reason for every",
            "one of BestPractice's OWN practices, which has no meaning here. The gate",
            'vocabulary itself (moments a practice can fire at, independent of which',
            'catalogue it belongs to) is the same everywhere Precedent\'s loader runs.',
        ],
        'gates': full['gates'],
    }


def _write_engine_files(dest_tools, engine_dir, source_commit):
    dest_tools.mkdir(parents=True, exist_ok=True)
    written = []
    hashes = {}
    for name in ENGINE_FILES:
        src = engine_dir / name
        out = dest_tools / name
        shutil.copy2(src, out)
        written.append(out)
        hashes[name] = _sha256(out)

    trimmed = _trim_routing_scope(engine_dir)
    routing_out = dest_tools / 'routing_scope.json'
    routing_out.write_text(json.dumps(trimmed, indent=2, ensure_ascii=False) + '\n',
                            encoding='utf-8')
    written.append(routing_out)
    hashes['routing_scope.json'] = _sha256(routing_out)

    manifest = {
        'format_version': 1,
        'source_repo': SOURCE_REPO,
        'source_branch': SOURCE_BRANCH,
        'source_commit': source_commit,
        'files': ENGINE_FILES + ['routing_scope.json'],
        'sha256': hashes,
        '_note': ("The vendored Precedent source-repo engine (see "
                  "tools/precedent_vendor_engine.py's own docstring, and "
                  "spec/BOOTSTRAP_NEW_SOURCES.md). Never hand-edit a file "
                  "this manifest lists -- run "
                  "'python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>' "
                  "instead; a hand-edit is detected as drift (sha256 mismatch) and "
                  "refused without --force."),
    }
    manifest_path = dest_tools / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    written.append(manifest_path)
    return written


def _git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd)] + list(args),
                          capture_output=True, text=True).stdout.strip()


def _head_commit(repo_dir):
    return _git(repo_dir, 'rev-parse', 'HEAD')


def seed(dest):
    """Run from BestPractice's own checkout: dest is a NEW source repo's
    root (tools/precedent_bootstrap_source.py's own --dest). No clone
    needed -- the source IS this checkout."""
    dest = pathlib.Path(dest).resolve()
    commit = _head_commit(ROOT) or 'unknown'
    return _write_engine_files(dest / 'tools', ENGINE_DIR, commit)


def _load_manifest(dest_tools):
    path = dest_tools / MANIFEST_NAME
    if not path.is_file():
        sys.exit(f"precedent_vendor_engine FAIL: {path} does not exist -- this repo has "
                 f"no vendored engine yet (run `seed`, or bootstrap a fresh set instead "
                 f"of migrating this one by hand)")
    return json.loads(path.read_text(encoding='utf-8'))


def _local_drift(dest_tools, manifest):
    """Files whose on-disk sha256 no longer matches what the manifest
    recorded -- a hand-edit since the last seed/refresh."""
    drifted = []
    for name, recorded_hash in manifest.get('sha256', {}).items():
        path = dest_tools / name
        if not path.is_file():
            drifted.append((name, 'missing'))
            continue
        actual = _sha256(path)
        if actual != recorded_hash:
            drifted.append((name, 'hand-edited (sha256 differs from manifest)'))
    return drifted


def _clone_or_die(arg):
    clone = pathlib.Path(arg).resolve()
    if not (clone / '.git').exists():
        sys.exit(f"precedent_vendor_engine FAIL: {clone} is not a git clone")
    return clone


def status(clone):
    dest_tools = ROOT / 'tools'
    manifest = _load_manifest(dest_tools)
    drift = _local_drift(dest_tools, manifest)
    for name, why in drift:
        print(f"  LOCAL DRIFT: {name} -- {why}")

    clone_head = _git(clone, 'rev-parse', f'origin/{SOURCE_BRANCH}') \
        or _git(clone, 'rev-parse', SOURCE_BRANCH)
    recorded = manifest.get('source_commit')
    behind = bool(clone_head) and clone_head != recorded
    print(f"manifest source_commit: {recorded}")
    print(f"clone origin/{SOURCE_BRANCH}: {clone_head}"
          + ("  (== recorded)" if clone_head == recorded else "  (!= recorded)"))
    if behind:
        print(f"NOTICE: BestPractice's {SOURCE_BRANCH} has moved since this engine was "
              f"last vendored -- run `refresh` to pick it up.")
    return 1 if drift else 0


def refresh(clone, force=False):
    dest_tools = ROOT / 'tools'
    manifest = _load_manifest(dest_tools)

    if not force:
        drift = _local_drift(dest_tools, manifest)
        if drift:
            for name, why in drift:
                print(f"  {name}: {why}")
            sys.exit("precedent_vendor_engine FAIL: a vendored engine file was hand-edited "
                     "since the last seed/refresh -- refreshing would silently discard that "
                     "edit. Move the edit upstream into BestPractice instead (this engine has "
                     "no local variance by design), or pass --force to overwrite anyway.")

    _git(clone, 'fetch', 'origin', SOURCE_BRANCH)
    _git(clone, 'checkout', SOURCE_BRANCH)
    _git(clone, 'pull', 'origin', SOURCE_BRANCH)
    new_commit = _head_commit(clone)
    if new_commit == manifest.get('source_commit'):
        print(f"precedent_vendor_engine refresh: already current with {SOURCE_BRANCH} "
              f"@ {new_commit[:12]} -- nothing to do.")
        return 0

    written = _write_engine_files(dest_tools, clone / 'tools', new_commit)
    print(f"precedent_vendor_engine refresh OK: {len(written)} file(s) refreshed from "
          f"{SOURCE_BRANCH} @ {new_commit[:12]} (was {manifest.get('source_commit', '?')[:12]})")
    print("next: review the diff, run this repo's own light check, then commit.")
    return 0


def fresh():
    try:
        manifest_path = ROOT / 'tools' / MANIFEST_NAME
        if not manifest_path.is_file():
            return 0
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        repo, recorded = manifest.get('source_repo'), manifest.get('source_commit')
        if not repo or not recorded:
            return 0
        try:
            out = subprocess.run(['git', 'ls-remote', repo, SOURCE_BRANCH],
                                 capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            return 0  # genuinely unreachable -- stays silent, same as checkin.py's fresh()
        head = out.stdout.split()[0] if out.returncode == 0 and out.stdout else ''
        if head and head != recorded:
            print(f"NOTICE: BestPractice's vendored engine has moved ({head[:12]}; your base "
                  f"{recorded[:12]}) -- refresh with "
                  f"`python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`.")
        elif not head and out.returncode != 0:
            err = (out.stderr or '').strip().splitlines()
            err = err[-1] if err else 'no output'
            print(f"COULD NOT VERIFY: couldn't reach {repo} to check the vendored engine's "
                  f"freshness -- `git ls-remote` failed ({err}). This is NOT the same as "
                  f"'confirmed fresh': if you need to know, verify directly instead of "
                  f"trusting this silence.")
    except Exception:
        pass
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == 'fresh':
        return fresh()
    if len(args) < 2 or args[0] not in ('seed', 'status', 'refresh'):
        sys.exit(__doc__)
    if args[0] == 'seed':
        written = seed(args[1])
        print(f"SEEDED: {len(written)} engine file(s) into {pathlib.Path(args[1]).resolve() / 'tools'}")
        for f in written:
            print(f"  wrote {f}")
        return 0
    clone = _clone_or_die(args[1])
    if args[0] == 'status':
        return status(clone)
    return refresh(clone, force='--force' in args)


if __name__ == '__main__':
    sys.exit(main())

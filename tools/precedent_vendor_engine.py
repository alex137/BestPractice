#!/usr/bin/env python3
"""precedent_vendor_engine.py — vendors Precedent's engine into a repo that
consumes it, as real tracked files instead of an undocumented hand-copy.
Two KINDS, sharing one mechanism:

  'source'   — an individual or team practice SET (precedent-individual,
               precedent-team-maintainers, precedent-team-tms). Needs only
               ENGINE_FILES: enough to run its own AGENTS.md loader block
               (precedent_show.py's Rule/Detail/Why/Story/Install split,
               build_views.py's `--agents-only` regeneration,
               precedent_paths.py's path-trigger channel, precedent_gate.py's
               closed gate vocabulary). This is the original, narrower case
               this tool closed first — see spec/BOOTSTRAP_NEW_SOURCES.md.

  'consumer' — a real four-source CONSUMER repo (universal + team +
               individual + repo-local, a vendored process/upstream/, the
               full precedent_materialize.py/precedent_resolve.py/
               precedent_sync_views.py toolchain that resolves all of them
               into one materialized tree). Needs CONSUMER_ENGINE_FILES:
               everything 'source' needs, PLUS those three multi-source
               tools — see TODO.md item 18 and this repo's own
               engine-plus-host-shims practice ("domain-neutral mechanism
               lives in the vendored tree"). Piloted 2026-09-05 against
               themorgan/HavrutaBrainstorm — INSTALL.md §1 step 12 and §2
               step 6 document the consumer-repo procedure this closes.

THE GAP 'source' CLOSED FIRST. tools/precedent_bootstrap_source.py has only
ever written practice content, config, approvers and the leak-blocklist —
never an engine file. Every individual/team set that existed before this
tool got its tools/build_views.py, precedent_gate.py, precedent_paths.py,
precedent_show.py and split_practices.py into place by an undocumented,
one-off hand-copy, so none of them could tell a stale copy from a current
one, and precedent-team-tms's copy was simply missing outright.

THE GAP 'consumer' CLOSES. A real consumer's own tools/ needing the same
treatment was named explicitly as future work when 'source' shipped
(TODO.md item 18: "not piloted... deliberately not folded into the
source-repo fix"). themorgan/HavrutaBrainstorm — a real four-source
consumer, not a fixture — had the identical undocumented-hand-copy problem
'source' closed for practice sets: its top-level tools/ held
build_views.py, precedent_gate.py, precedent_paths.py, precedent_show.py,
split_practices.py, precedent_materialize.py, precedent_resolve.py and
precedent_sync_views.py, all copied in by hand at some point in the past
with no manifest, no recorded source commit, and (confirmed 2026-09-05) six
of those eight files had already drifted from BestPractice's current
tools/ — including the --repo-awareness fix (commit 7c8d33d) and the
repo-local `path: "."` safety fix (commit 29148bc's sibling changes to
precedent_resolve.py/precedent_materialize.py), silently missing from the
consumer's copy the whole time.

Distinct from tools/checkin.py, which mirrors a CONSUMER's whole
process/upstream/ tree, deleting anything the tree no longer has, in BOTH
directions (a consumer pulls upstream content AND pushes its own
check-ins back). This engine is one-directional in both kinds —
downstream from BestPractice only, since neither a source set nor a
consumer's own tools/ has engine code of its own to contribute back — and
it sits inside tools/ ALONGSIDE non-vendored, repo-owned files (tools/checks/,
routing_scope.json is vendored but trimmed, a source set's own
build_codeowners.py, a consumer's own bootstrap.sh/light_check.py/
report_automation_issue.py) that a whole-directory mirror-and-delete would
destroy. So this is a NEW, narrower tool, not an extension of checkin.py:
it touches only the files it knows about, by name, per kind.

ENGINE_FILES / CONSUMER_ENGINE_FILES both name this script itself last, on
purpose: it travels WITH the engine it defines, so a future improvement to
the vendoring mechanism itself reaches every already-vendored repo the same
way an improvement to build_views.py does — not a second, undocumented gap
one layer up from the one this tool closes. precedent_materialize.py/
precedent_resolve.py/precedent_sync_views.py are never in ENGINE_FILES
(source) — a source set has no process/upstream/ and nothing to resolve
against more than one tree — but they ARE in CONSUMER_ENGINE_FILES
(consumer), where resolving four sources into one materialized tree is the
entire point.

routing_scope.json is vendored in both kinds too, but it is not a
byte-identical copy: precedent_gate.py's SCOPE file carries two things in
this repo — the closed GATE vocabulary (`gates`, the moments a practice can
fire at, which is the same everywhere Precedent's loader runs, regardless
of kind) and a `practices` key documenting the routing reason for every one
of BestPractice's OWN 60-odd practices, which has no meaning in either a
source set or a consumer repo with a different catalogue entirely.
`_trim_routing_scope` below keeps only the first and drops the second — the
same trim a prior, undocumented hand-copy already applied by hand to every
repo that needed it (precedent-individual, precedent-team-maintainers, and
HavrutaBrainstorm's own top-level tools/routing_scope.json, all three
confirmed byte-identical to this function's output before this tool
existed, or was extended to the consumer kind); this tool just makes that
trim mechanical instead of a fact only the session that did it once
remembered.

Four subcommands:

  seed <dest-dir> [--kind source|consumer]
                                  Run from BESTPRACTICE'S OWN checkout (the
                                  case tools/precedent_bootstrap_source.py
                                  needs — no clone required, the source IS
                                  this checkout). --kind defaults to
                                  'source' (unchanged CLI/API for every
                                  existing caller — precedent_bootstrap_
                                  source.py calls seed(dest) with no kind
                                  argument at all, and gets the same
                                  narrower set it always has). Copies the
                                  kind's file list and a trimmed
                                  routing_scope.json into <dest-dir>/tools/,
                                  and writes
                                  <dest-dir>/tools/ENGINE_MANIFEST.json
                                  recording this checkout's HEAD commit,
                                  the kind, and a sha256 per vendored file.

  status <bestpractice-clone>    Run from an ALREADY-VENDORED repo of
                                  either kind (same shape checkin.py's
                                  verbs use): reads `kind` back out of
                                  ENGINE_MANIFEST.json (no --kind flag
                                  needed — the manifest already says which
                                  file list applies) and compares the
                                  vendored files against its recorded
                                  hashes (local hand-edit?) and against the
                                  clone's current tools/ (upstream moved?).
                                  Exit 1 if either differs.

  refresh <bestpractice-clone> [--force]
                                  Same kind auto-detection as status. Pulls
                                  the clone's SOURCE_BRANCH (see below —
                                  NOT the clone's configured default
                                  branch), refuses if a vendored file was
                                  hand-edited since the last seed/refresh
                                  (its sha256 no longer matches
                                  ENGINE_MANIFEST.json) unless --force, then
                                  re-copies + re-trims (the kind's own file
                                  list) and updates the manifest.

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

Run (from an already-vendored repo's own checkout, either kind):
  python3 tools/precedent_vendor_engine.py fresh
  python3 tools/precedent_vendor_engine.py status  ../BestPractice
  python3 tools/precedent_vendor_engine.py refresh ../BestPractice

Run once, from BestPractice's own checkout, to vendor a NEW consumer repo
(status/refresh above then work unchanged, kind auto-detected):
  python3 tools/precedent_vendor_engine.py seed <consumer-repo> --kind consumer

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

# A consumer needs everything a source set does, PLUS the three multi-source
# tools that only make sense once more than one tree is being resolved
# together -- see the docstring's "'consumer' closes" section. Built by
# extending ENGINE_FILES rather than listing all nine names flat, so a
# future addition to the shared engine (a new file every kind needs) only
# has to be added in one place.
CONSUMER_ENGINE_FILES = ENGINE_FILES[:-1] + [
    'precedent_materialize.py',
    'precedent_resolve.py',
    'precedent_sync_views.py',
    'precedent_vendor_engine.py',  # last, same reason as ENGINE_FILES above
]

KINDS = {'source': ENGINE_FILES, 'consumer': CONSUMER_ENGINE_FILES}
DEFAULT_KIND = 'source'  # unchanged default -- see seed()'s docstring note
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


def _write_engine_files(dest_tools, engine_dir, source_commit, kind=DEFAULT_KIND):
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    files = KINDS[kind]
    dest_tools.mkdir(parents=True, exist_ok=True)
    written = []
    hashes = {}
    for name in files:
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
        'kind': kind,
        'source_repo': SOURCE_REPO,
        'source_branch': SOURCE_BRANCH,
        'source_commit': source_commit,
        'files': files + ['routing_scope.json'],
        'sha256': hashes,
        '_note': (f"The vendored Precedent {kind}-repo engine (see "
                  "tools/precedent_vendor_engine.py's own docstring, and "
                  "spec/BOOTSTRAP_NEW_SOURCES.md / INSTALL.md). Never hand-edit a file "
                  "this manifest lists -- run "
                  "'python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>' "
                  "instead (kind is read back from this manifest -- no --kind flag needed "
                  "for status/refresh); a hand-edit is detected as drift (sha256 mismatch) "
                  "and refused without --force."),
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


def seed(dest, kind=DEFAULT_KIND):
    """Run from BestPractice's own checkout: dest is a NEW source-set or
    consumer repo's root (tools/precedent_bootstrap_source.py's own --dest,
    for kind='source' only -- a consumer has no bootstrap tool of its own,
    it is vendored directly into an existing repo, per INSTALL.md). No clone
    needed -- the source IS this checkout.

    kind defaults to 'source' so every existing caller (precedent_bootstrap_
    source.py calls `seed(dest)` with no kind argument at all) keeps getting
    exactly the file set it always has -- this default is what makes the
    consumer kind purely additive rather than a breaking change to the
    source-repo case."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    dest = pathlib.Path(dest).resolve()
    commit = _head_commit(ROOT) or 'unknown'
    return _write_engine_files(dest / 'tools', ENGINE_DIR, commit, kind)


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
    kind = manifest.get('kind', DEFAULT_KIND)  # older manifests predate 'kind' -- 'source'
    drift = _local_drift(dest_tools, manifest)
    for name, why in drift:
        print(f"  LOCAL DRIFT: {name} -- {why}")

    clone_head = _git(clone, 'rev-parse', f'origin/{SOURCE_BRANCH}') \
        or _git(clone, 'rev-parse', SOURCE_BRANCH)
    recorded = manifest.get('source_commit')
    behind = bool(clone_head) and clone_head != recorded
    print(f"kind: {kind}")
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
    kind = manifest.get('kind', DEFAULT_KIND)  # older manifests predate 'kind' -- 'source'

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
    # `and not force`: found reproduced while testing this against the consumer
    # kind -- without it, `refresh --force` on a repo with a hand-edited
    # vendored file silently did NOTHING when BestPractice's SOURCE_BRANCH
    # hadn't moved, because this short-circuit ran before --force ever got a
    # chance to matter. --force exists specifically to repair a hand-edited
    # file; "the upstream commit is unchanged" must not override that.
    if new_commit == manifest.get('source_commit') and not force:
        print(f"precedent_vendor_engine refresh: already current with {SOURCE_BRANCH} "
              f"@ {new_commit[:12]} -- nothing to do.")
        return 0

    written = _write_engine_files(dest_tools, clone / 'tools', new_commit, kind)
    print(f"precedent_vendor_engine refresh OK ({kind}): {len(written)} file(s) refreshed "
          f"from {SOURCE_BRANCH} @ {new_commit[:12]} (was {manifest.get('source_commit', '?')[:12]})")
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
        rest = args[2:]
        kind = DEFAULT_KIND
        if '--kind' in rest:
            i = rest.index('--kind')
            if i + 1 >= len(rest):
                sys.exit("precedent_vendor_engine FAIL: --kind needs a value "
                         f"({', '.join(sorted(KINDS))}).")
            kind = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        if kind not in KINDS:
            sys.exit(f"precedent_vendor_engine FAIL: --kind must be one of "
                     f"{', '.join(sorted(KINDS))}, got {kind!r}.")
        if rest:
            sys.exit(f"precedent_vendor_engine FAIL: unknown argument(s) to seed: "
                     f"{', '.join(rest)}.")
        written = seed(args[1], kind=kind)
        print(f"SEEDED ({kind}): {len(written)} engine file(s) into "
              f"{pathlib.Path(args[1]).resolve() / 'tools'}")
        for f in written:
            print(f"  wrote {f}")
        return 0
    clone = _clone_or_die(args[1])
    if args[0] == 'status':
        return status(clone)
    return refresh(clone, force='--force' in args)


if __name__ == '__main__':
    sys.exit(main())

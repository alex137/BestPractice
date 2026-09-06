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

  refresh <bestpractice-clone> [--force] [--from-ref REF]
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
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve()
ENGINE_DIR = HERE.parent
ROOT = ENGINE_DIR.parent
SOURCE_REPO = 'https://github.com/alex137/BestPractice'
SOURCE_BRANCH = 'precedent-beta-v01'  # see docstring: NOT the configured default

ENGINE_FILES = [
    'build_views.py',
    # A team set's approvers.json -> CODEOWNERS generator. In the engine
    # rather than in one team set's own tools/ because that is where it
    # was, and the consequence was a second team set with declared
    # approvers and no way to enforce them (2026-09-06). No-ops in an
    # individual set, which has no approvers.json and needs none.
    'build_codeowners.py',
    'precedent_gate.py',
    'precedent_paths.py',
    'precedent_show.py',
    'split_practices.py',
    # Classifies practices carrying the OLD status vocabulary, where
    # `retired` meant both "the copy here is redundant" and "nobody wants
    # this rule anywhere" (2026-09-06). The legacy records are in the
    # private sets, never in BestPractice's own catalogue, so a migration
    # that only existed upstream could not reach the repos that need it.
    # It is also the only compliance signal a SOURCE set has for this:
    # verify_harness.py is deliberately not vendored, so
    # check_status_contract never runs there.
    'precedent_migrate_status.py',
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
    # Named by a universal practice's own Install, so a consumer that
    # resolves that practice needs the file (added 2026-09-06, after
    # installing into a scratch repo exactly as INSTALL.md section 0
    # describes and running precedent_check.py on the result):
    #
    #   doc_lint.py      -- four enforced checks import it
    #                       (acronyms-glossary, deliverables-look-like-output,
    #                       doc-references-are-links, search-by-purpose).
    #                       Without it all four reported "did not import: No
    #                       module named 'doc_lint'" -- SKIPPED, which is
    #                       honest, and useless. It is also the light check
    #                       AGENTS.md tells every session to run before every
    #                       commit.
    #   doc_sync.py      -- two more (computed-numbers-in-scripts,
    #                       docs-track-models). Its PAIRS list is empty until
    #                       a repo fills it in, so it reports NOT APPLICABLE
    #                       there rather than failing.
    #   routing_audit.py -- routing-audit's Install names it as the practice's
    #                       implementation, so the check flagged its absence
    #                       as a violation in every consuming repo. It needs
    #                       only split_practices and precedent_paths, both
    #                       already here.
    'doc_lint.py',
    'doc_sync.py',
    'routing_audit.py',
    # headline-capitalization's check imports it. Added 2026-09-06, after a
    # consumer that re-vendored the catalogue got the practice but not the
    # module, and precedent_check.py reported the check as ERRORED
    # ("ModuleNotFoundError: No module named 'title_case'") rather than
    # passed or skipped -- honest, and useless. Same class as doc_lint.py
    # above: a universal practice's own Install names a module, so every
    # repo that resolves that practice needs it vendored alongside.
    'title_case.py',
    # The individual-source SessionStart hook this repo ships as a
    # template (templates/harness/claude-code/hooks/
    # individual-source-bootstrap.sh.template) execs this file, and
    # precedent_resolve.py's own lazy self-heal re-invokes that hook. It
    # was never vendored, so in a consuming repo the hook exec'd a path
    # that did not exist -- and both callers swallow the failure by
    # design, so the individual source simply never resolved and nothing
    # said why.
    'precedent_source_bootstrap.py',
    # The enforced channel itself. INSTALL.md section 0 step 1 used to say
    # "copy precedent_check.py by hand" -- on the reasoning that it belongs
    # to phase 4's enforced-checks channel rather than to the loader engine.
    # True as taxonomy, and exactly the undocumented hand-copy this tool
    # exists to end: no manifest, no recorded commit, no way to tell a
    # stale copy from a current one, which is how six of eight engine files
    # in the first real consumer repo had silently drifted. It travels with
    # the engine now, and the hand-copy step is gone from INSTALL.md.
    'precedent_check.py',
    'precedent_vendor_engine.py',  # last, same reason as ENGINE_FILES above
]

KINDS = {'source': ENGINE_FILES, 'consumer': CONSUMER_ENGINE_FILES}
DEFAULT_KIND = 'source'  # unchanged default -- see seed()'s docstring note
MANIFEST_NAME = 'ENGINE_MANIFEST.json'
_SECOND_PASS_ENV = 'PRECEDENT_VENDOR_ENGINE_SECOND_PASS'


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
    """Run git and return stdout, DISCARDING the exit code.

    Only for commands whose failure is genuinely acceptable, and then only
    where the discard is commented at the call site. Never for resolving a
    ref: `git rev-parse <missing-ref>` fails AND prints the ref name, so this
    returns a truthy non-commit -- use _rev() instead. Never to decide whether
    something worked: a failure here is indistinguishable from success with no
    output. `fresh()` below is the model for a command that may legitimately
    fail -- it checks returncode and says "COULD NOT VERIFY" rather than
    letting silence read as confirmation."""
    return subprocess.run(['git', '-C', str(cwd)] + list(args),
                          capture_output=True, text=True).stdout.strip()


def _git_read(cwd, *args):
    """Run git and return (ok, stdout) so a caller can tell empty output apart
    from a failed command."""
    r = subprocess.run(['git', '-C', str(cwd)] + list(args),
                       capture_output=True, text=True)
    return r.returncode == 0, r.stdout


def _rev(repo_dir, ref):
    """Resolve `ref` to a commit, or '' if it does not exist.

    `--verify --quiet` matters: plain `git rev-parse <missing-ref>` exits
    non-zero but ECHOES THE REF NAME on stdout, and _git() below returns
    stdout while discarding the exit code. A caller doing
    `_git(..., 'rev-parse', ref) or <fallback>` therefore gets the truthy
    string 'origin/precedent-beta-v01' instead of falling back, and carries
    that non-commit forward as if it were a hash. Caught in CI (2026-09-06):
    a clone whose origin lacked SOURCE_BRANCH failed downstream with
    "precedent-beta-v01 @ origin/prece has no tools/build_views.py" -- the
    12-char truncation of the ref name being printed where a commit belonged.
    """
    r = subprocess.run(['git', '-C', str(repo_dir), 'rev-parse', '--verify',
                        '--quiet', ref], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ''


def _blob_exists(repo_dir, commit, rel):
    """Does `rel` exist at `commit` in `repo_dir`? Used by seed() to tell
    "this engine file is new and not committed yet" from "this checkout is
    broken", which are the same `git show` failure otherwise."""
    r = subprocess.run(['git', '-C', str(repo_dir), 'cat-file', '-e',
                        f'{commit}:{rel}'], capture_output=True)
    return r.returncode == 0


def _head_commit(repo_dir):
    # _rev, not _git: a failed `rev-parse HEAD` prints 'HEAD' back, which is
    # truthy, so seed()'s `_head_commit(ROOT) or 'unknown'` silently recorded
    # source_commit: "HEAD" in ENGINE_MANIFEST.json instead of 'unknown' --
    # and every later status()/refresh() then compared a real hash against the
    # string "HEAD" and reported upstream as moved, forever.
    return _rev(repo_dir, 'HEAD')


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
    # From the COMMIT, not the working tree. This used to copy whatever
    # was on disk in ENGINE_DIR while stamping HEAD's hash into
    # ENGINE_MANIFEST.json, so seeding from a checkout with any
    # uncommitted engine change wrote a manifest that named a commit the
    # vendored bytes did not come from. `status` and `refresh` in the
    # adopter's repo then compared those bytes against that commit's real
    # content and reported drift forever, with nothing in the adopter's
    # repo to explain it -- the provenance record silently made false,
    # which is the one thing a provenance record must not do (practice:
    # generated-artifact-provenance). An uncommitted change is also not
    # something an adopter should be shipped: it is, by definition, not
    # yet part of the engine.
    wanted = KINDS[kind] + ['routing_scope.json']
    missing_at_head = [n for n in wanted
                       if commit != 'unknown'
                       and not _blob_exists(ROOT, commit, f'tools/{n}')]
    if commit == 'unknown' or missing_at_head:
        # Either there is no commit to read from (an unborn HEAD, or not a
        # git checkout), or a file this kind needs does not exist at HEAD
        # yet -- the ordinary state while an engine file is being ADDED.
        # Vendor the working tree, and mark the recorded commit `+dirty` so
        # the manifest never claims bytes came from a commit they did not:
        # status() and refresh() both compare against source_commit, and a
        # `+dirty` value can never equal a real hash, so they correctly
        # report the copy as not-current until a clean re-seed.
        if missing_at_head:
            print(f"precedent_vendor_engine seed: NOTE -- "
                  f"{', '.join(missing_at_head)} is not in {commit[:12]} yet, "
                  f"so this seeds from the WORKING TREE and records "
                  f"{commit[:12]}+dirty. Commit and re-seed for a clean "
                  f"provenance record.", file=sys.stderr)
        stamp = commit if commit == 'unknown' else f'{commit}+dirty'
        return _write_engine_files(dest / 'tools', ENGINE_DIR, stamp, kind)
    _c, engine_dir = _source_tools_at(ROOT, kind=kind, ref=commit, fetch=False)
    try:
        dirty = [n for n in wanted
                 if (ENGINE_DIR / n).is_file()
                 and (ENGINE_DIR / n).read_bytes() != (engine_dir / n).read_bytes()]
        if dirty:
            print(f"precedent_vendor_engine seed: NOTE -- vendoring "
                  f"{commit[:12]}, not this working tree. Uncommitted "
                  f"changes to {', '.join(dirty)} are NOT in what was "
                  f"written; commit them and re-run to ship them.",
                  file=sys.stderr)
        return _write_engine_files(dest / 'tools', engine_dir, commit, kind)
    finally:
        shutil.rmtree(engine_dir, ignore_errors=True)


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


def _untracked_engine_files(dest_tools, manifest):
    """Engine files present on disk that the manifest does not record -- a
    hand-copy dropped in beside a properly vendored engine.

    _local_drift() above walks the manifest and asks "is each recorded file
    still what we wrote?" That direction is blind to a file nobody recorded,
    and the blind spot is not hypothetical. 2026-09-06, in
    precedent-team-maintainers: its engine was a faithful, internally
    consistent vendoring of one upstream commit -- seven files, every hash
    matching -- and beside it sat a hand-copied `build_codeowners.py` from a
    LATER upstream commit. build_views.py scans `tools/*.py` and requires a
    description for each, so the newer stray broke the older engine outright:
    `build_views.py` failed, and that repo could not regenerate its own
    AGENTS.md at all. Every mechanism reported healthy -- `status` compared
    only recorded files and saw no drift -- because the one file causing it
    was invisible to all of them.

    Deliberately keyed on the engine's OWN file lists rather than on "any
    .py we did not vendor": a repo's own tools/ legitimately holds its own
    scripts, and flagging those would make this noise. A name that appears
    in ENGINE_FILES or CONSUMER_ENGINE_FILES but not in this repo's manifest
    is the precise signature of a hand-drop -- and `refresh` is its fix,
    since vendoring the file properly is exactly what records it."""
    recorded = set(manifest.get('files', []))
    known = set(ENGINE_FILES) | set(CONSUMER_ENGINE_FILES)
    return sorted(n for n in (known - recorded) if (dest_tools / n).is_file())


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
    untracked = _untracked_engine_files(dest_tools, manifest)
    for name in untracked:
        print(f"  UNTRACKED ENGINE FILE: {name} is an engine file this "
              f"manifest does not record -- a hand-copy dropped in beside "
              f"the vendored engine. It can be from a different upstream "
              f"commit than the rest, which is how a correctly vendored "
              f"engine ends up unable to run at all. `refresh` vendors it "
              f"properly and records it.")

    # _rev, not _git: plain rev-parse of a missing ref prints the REF NAME, so
    # this used to bind clone_head='origin/precedent-beta-v01' -- truthy, and
    # != recorded -- and then told the reader upstream had moved and to run
    # refresh, when the truth was that this clone has no such ref at all.
    clone_head = (_rev(clone, f'origin/{SOURCE_BRANCH}')
                  or _rev(clone, SOURCE_BRANCH))
    recorded = manifest.get('source_commit')
    print(f"kind: {kind}")
    print(f"manifest source_commit: {recorded}")
    if not clone_head:
        # Not "fresh" and not "moved" -- unknown. Same discipline as fresh().
        print(f"COULD NOT VERIFY: {clone} has no {SOURCE_BRANCH} "
              f"(neither origin/{SOURCE_BRANCH} nor a local branch of that name), so "
              f"whether this vendored engine is current is UNKNOWN -- this is not "
              f"'confirmed current'. Fetch that branch in the clone, or point at a "
              f"clone of {SOURCE_REPO}.")
        return 1 if (drift or untracked) else 0
    print(f"clone origin/{SOURCE_BRANCH}: {clone_head}"
          + ("  (== recorded)" if clone_head == recorded else "  (!= recorded)"))
    if clone_head != recorded:
        print(f"NOTICE: BestPractice's {SOURCE_BRANCH} has moved since this engine was "
              f"last vendored -- run `refresh` to pick it up.")
    return 1 if (drift or untracked) else 0


def _source_tools_at(clone, kind=DEFAULT_KIND, ref=None, fetch=True):
    """Materialize SOURCE_BRANCH's tools/ out of `clone` into a throwaway
    directory, and return (commit, that directory).

    READ-ONLY with respect to `clone`, deliberately and load-bearingly so.
    This used to run `git checkout SOURCE_BRANCH` and `git pull` in `clone`
    to get the files off disk, which moved the caller's repository:

      * for a person, it silently switched their own BestPractice checkout
        onto SOURCE_BRANCH, abandoning whatever branch they were on;
      * in CI, `clone` is the job's own workspace, so the checkout moved the
        workspace mid-job and every LATER step in that job silently ran
        against SOURCE_BRANCH instead of the commit under test. That cost
        several sessions of investigation on PR #110, where the step after
        this one reported a violation that was true of SOURCE_BRANCH and
        false of the commit being tested, with `git status` clean throughout
        (a branch checkout leaves no dirty file to notice).

    Blobs, not the working tree -- the same discipline tools/leak_gate.py
    holds, for the same reason: reading history must not disturb the tree
    the caller is standing in. A vendoring read needs file CONTENT at a
    commit, which `git show` gives without touching HEAD or the index.

    `kind` selects which file list to materialize -- the consumer kind
    vendors precedent_materialize/resolve/sync_views on top of the source
    kind's list, and _write_engine_files() will look for every one of them
    in the directory returned here."""
    # Exit code deliberately discarded: an offline clone, or one whose origin
    # has no SOURCE_BRANCH, is a supported case -- the _rev fallback below
    # handles it, and a hard failure here would break vendoring from a local
    # clone that is already up to date.
    if fetch:
        _git(clone, 'fetch', '--quiet', 'origin', SOURCE_BRANCH)
    # `ref`, when given, names the exact commit to read (seed() passes this
    # checkout's own HEAD -- it is not vendoring from a branch at all).
    # Otherwise: origin/<branch> first, then a local branch of that name --
    # a CI workspace carries only the ref under test, so a clone taken from
    # it legitimately has no origin/<SOURCE_BRANCH> at all.
    commit = ref or (_rev(clone, f'origin/{SOURCE_BRANCH}')
                     or _rev(clone, SOURCE_BRANCH))
    if not commit:
        sys.exit(f"precedent_vendor_engine FAIL: {clone} has no {SOURCE_BRANCH} "
                 f"(neither origin/{SOURCE_BRANCH} nor a local branch of that name) "
                 f"-- is it a clone of {SOURCE_REPO}?")

    # file mode per entry, so a vendored file keeps the executable bit it has
    # upstream (shutil.copy2 used to carry it over from the checked-out tree).
    modes = {}
    ok, tree = _git_read(clone, 'ls-tree', f'{commit}:tools')
    if not ok:
        # No tempdir yet at this point -- nothing to clean up.
        sys.exit(f"precedent_vendor_engine FAIL: could not list tools/ at "
                 f"{SOURCE_BRANCH} @ {commit[:12]} in {clone}. Refusing rather than "
                 f"vendoring with every executable bit silently dropped.")
    for line in tree.splitlines():
        meta, _tab, name = line.partition('\t')
        if meta and name:
            modes[name] = meta.split()[0]

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-engine-source-'))
    for name in KINDS[kind] + ['routing_scope.json']:
        blob = subprocess.run(['git', '-C', str(clone), 'show', f'{commit}:tools/{name}'],
                              capture_output=True)
        if blob.returncode != 0:
            shutil.rmtree(tmp, ignore_errors=True)
            sys.exit(f"precedent_vendor_engine FAIL: {SOURCE_BRANCH} @ {commit[:12]} has no "
                     f"tools/{name} -- "
                     f"{blob.stderr.decode('utf-8', 'replace').strip()}")
        out = tmp / name
        out.write_bytes(blob.stdout)          # bytes, not text: no newline munging
        if modes.get(name, '').endswith('755'):
            out.chmod(0o755)
    return commit, tmp


def _warn_legacy_status_records(dest):
    """Say when this repo still holds practices written under the OLD status
    vocabulary, at the moment the new one arrives.

    A refresh is exactly when the vocabulary changes underneath a set, and
    the set has no other way to find out: verify_harness.py is not vendored,
    so check_status_contract never runs here. Without this the new engine
    simply starts treating `retired` records differently -- correctly, but
    silently -- and the one thing a legacy record cannot tell anyone is
    whether its rule survives somewhere. Same principle build_views already
    applies when it drops a practice from the generated views: the drop is
    announced rather than silently skipped.

    A notice, never a gate. Refreshing the engine must not fail because the
    CATALOGUE needs a separate, human-decided migration -- that is the same
    separation _warn_catalogue_skew exists to respect."""
    try:
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_migrate_status as pms
        records = pms.legacy_records(pathlib.Path(dest) / 'practices')
    except Exception:                                        # noqa: BLE001
        return                                               # never break a refresh
    if not records:
        return
    slugs = ', '.join(fm.get('slug', f.stem) for f, fm, _s in records)
    print(f"\nNOTICE: {len(records)} practice(s) here still carry the pre-2026-09-06 "
          f"status vocabulary, where `retired` meant BOTH 'the copy here is "
          f"redundant, the rule is in force elsewhere' AND 'nobody wants this "
          f"rule anywhere': {slugs}.")
    print("  The engine you just vendored treats them as not in force -- which is "
          "correct either way -- but they carry no `in_force_at:`, so nothing can "
          "say which kind they are, and precedent_show.py will decline to guess.")
    print("  Classify them:  python3 tools/precedent_migrate_status.py "
          "--repo . --against <sibling-source-dirs>")


def _warn_catalogue_skew(dest, engine_commit):
    """Say when the engine just moved past the catalogue it runs against.

    `refresh` updates the ENGINE and nothing else, by design -- taking the
    practice catalogue is a separate, deliberate step (INSTALL.md section 2),
    because installs are adapted and an unattended mirror is the mechanism
    class that loses content. The cost of that separation is a skew nobody
    was told about: engine code that cites a practice slug the vendored
    catalogue predates.

    THE REMEDY THIS NOTICE NAMES IS DELIBERATELY NOT `checkin.py update`.
    Its first version suggested exactly that, and the suggestion was worse
    than silence: checkin.py's `_default_branch()` resolves
    `refs/remotes/origin/HEAD` unconditionally, so on every consumer pinned
    to `precedent-beta-v01` -- which is all of them, until the phase-7
    fold-in -- following the advice mirrors `main` over the vendored tree
    and DELETES the very practices this notice says are missing. Caught
    2026-09-06 by the consumer session that read the notice, recognized the
    trap, and did the manual mirror instead; spec/MIGRATING_EXISTING_INSTALLS.md's
    "The default-branch gotcha" is the same finding from the other side.
    UPDATE, later the same day: checkin.py HAS since been taught the pin.
    All four of its commands -- `fresh`, `update`, `record`, `push` -- now
    read `upstream.branch` from the consuming repo's own
    `process/manifest.json` and fall back to the clone's default only when
    no pin is recorded, and `record` no longer checks the clone out either.
    Seven harness cases assert it, each with a negative control.

    The remedy named below still points at the manual mirror anyway, and
    that is a deliberate hold rather than an oversight. What these two
    documents guard against is an UNATTENDED job overwriting a repo's
    vendored tree; the fix that would let them relax is hours old at the
    time of writing, and the two error directions are not symmetric --
    telling people the automation is safe when it is not costs a silent
    overnight wipe, while staying cautious costs a stale sentence. Morgan's
    call, 2026-09-06: record that the pin works, keep the manual remedy,
    and revisit once the fix has survived real sync cycles. So this is now
    a "not yet", not a "cannot" -- do not read it as the latter and do not
    quietly flip it either; that flip is a decision, and it has an owner.

    Reached a real consumer on 2026-09-06. A refresh took the engine to a
    commit whose `precedent_resolve.py` cites `source-naming` three times,
    while `process/upstream/` still sat 5 commits back and had no
    `practices/source-naming.md` -- so the repo's own `code-cites-practice`
    check reported three violations for a slug that does exist upstream, in
    code the consumer is not allowed to edit. Nothing in the refresh had
    said the two halves were now different ages.

    Reports, never fails: the skew is legitimate between an engine refresh
    and the catalogue update that follows it, and this runs at the moment
    the person is right there to act on it. Practice fail-gracefully: keep
    going, and tell the human.
    """
    manifest = dest / 'process' / 'manifest.json'
    if not manifest.is_file():
        return                              # not the classic vendoring layout
    try:
        recorded = json.loads(manifest.read_text(
            encoding='utf-8'))['upstream']['commit']
    except (ValueError, KeyError, OSError):
        return                              # nothing reliable to compare
    if not recorded or recorded.startswith(engine_commit[:len(recorded)]) \
            or engine_commit.startswith(recorded[:len(engine_commit)]):
        return                              # same commit, however abbreviated
    print(f"NOTICE: the engine is now at {engine_commit[:12]}, but this "
          f"repo's vendored practice catalogue (process/upstream/) is still "
          f"at {recorded[:12]}. Engine code can cite practices that "
          f"catalogue does not carry yet -- if a check reports a slug as "
          f"'not a real practice', this skew is why. Take the catalogue "
          f"update too -- INSTALL.md section 2, which for a repo pinned to "
          f"a named branch means the manual mirror it describes, NOT "
          f"`checkin.py update`.")


def refresh(clone, force=False, ref=None):
    """`ref`, when given, names the exact commit or ref inside `clone` to
    vendor from, instead of resolving SOURCE_BRANCH there.

    Two callers need it. A verification fixture must vendor from the tree
    it is testing, not from whatever `origin/precedent-beta-v01` happens
    to hold -- without that, adding a file to the engine turns the harness
    red until the addition is published, and a stale local branch in a
    contributor's checkout produces a failure message about a missing
    engine file that has nothing to do with the property under test (both
    reproduced, 2026-09-06). And a person can legitimately want to vendor
    a specific commit -- pinning to a known-good one, or picking up a fix
    before it lands on the branch."""
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

    new_commit, engine_dir = _source_tools_at(clone, kind, ref=ref,
                                              fetch=ref is None)
    try:
        # `and not force`: found reproduced while testing this against the consumer
        # kind -- without it, `refresh --force` on a repo with a hand-edited
        # vendored file silently did NOTHING when BestPractice's SOURCE_BRANCH
        # hadn't moved, because this short-circuit ran before --force ever got a
        # chance to matter. --force exists specifically to repair a hand-edited
        # file; "the upstream commit is unchanged" must not override that.
        # An equal commit is not enough to call this current: the vendored
        # FILE SET has to match this kind's list too. Without that second
        # half, a repo whose engine predates a newly-added engine file could
        # never acquire it -- and would be told it was current forever.
        #
        # THE TRAP, reproduced end to end 2026-09-06 across all three of this
        # account's practice sets. `refresh` runs the VENDOREE's own copy of
        # this tool, which carries the file list it was vendored with. A
        # first run therefore writes the OLD set, replaces this file with the
        # new one, and stamps the NEW commit into the manifest. A second run
        # -- now executing the newer tool, which does know about the added
        # file -- hit this short-circuit on the matching commit and reported
        # "nothing to do", so the file never arrived and the manifest
        # asserted current the whole time. build_codeowners.py joined the
        # engine on 2026-09-06 for a stated reason (a team set with declared
        # approvers and no way to enforce them); none of the three sets ever
        # received it, and someone hand-copied it into one of them, which is
        # what broke that repo's build_views.py. The hand-copy was a symptom.
        # Refresh still takes two passes when the tool must replace itself
        # first -- that is inherent to a self-updating tool -- but the second
        # pass now converges instead of lying.
        wanted_set = set(KINDS[kind]) | {'routing_scope.json'}
        set_incomplete = sorted(
            n for n in wanted_set
            if n not in set(manifest.get('files', []))
            or not (dest_tools / n).is_file())
        if new_commit == manifest.get('source_commit') and not force \
                and not set_incomplete:
            print(f"precedent_vendor_engine refresh: already current with {SOURCE_BRANCH} "
                  f"@ {new_commit[:12]} -- nothing to do.")
            # Reported here too, and this is the case that matters MOST: a
            # session re-running refresh and being told "nothing to do" is
            # exactly the session that would otherwise conclude both halves
            # are current. Missed on the first version of this notice, which
            # only reported after a write -- so the second pass of a
            # self-replacing refresh, and every later re-run, stayed silent.
            _warn_catalogue_skew(ROOT, new_commit)  # ROOT, not `dest` -- see below
            _warn_legacy_status_records(ROOT)
            return 0

        if set_incomplete and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but this "
                  f"repo's vendored engine is missing {len(set_incomplete)} "
                  f"file(s) this kind now includes "
                  f"({', '.join(set_incomplete)}) -- refreshing anyway.")

        self_before = _sha256(HERE) if HERE.is_file() else None
        written = _write_engine_files(dest_tools, engine_dir, new_commit, kind)
    finally:
        shutil.rmtree(engine_dir, ignore_errors=True)
    print(f"precedent_vendor_engine refresh OK ({kind}): {len(written)} file(s) refreshed "
          f"from {SOURCE_BRANCH} @ {new_commit[:12]} (was {manifest.get('source_commit', '?')[:12]})")
    # ROOT, not `dest`: refresh()'s local for the repo being refreshed is
    # `dest_tools` (ROOT / 'tools'), and there has never been a `dest` here.
    # Landed 2026-09-06 as a NameError that crashed EVERY refresh, after the
    # files were already written and "refresh OK" already printed -- so the
    # run looked half-successful and its exit code was the only tell. Fixed
    # concurrently and identically by two sessions; the harness case for the
    # already-current branch came from this one.
    _warn_catalogue_skew(ROOT, new_commit)
    _warn_legacy_status_records(ROOT)

    # THE SECOND PASS, and why it is not optional. The file list for a kind
    # lives in THIS module, and a refresh runs the copy that is already
    # vendored -- the stale one. So the run that first brings a newly added
    # engine file's name into the repo is also the run that cannot copy it:
    # it works from the old list, writes the new tool, and stops one file
    # short, silently. Seen twice in one day (2026-09-06): `kind` stayed
    # absent from three sets' manifests for a whole cycle, and
    # build_codeowners.py reached none of them. Re-running once, with the
    # just-written tool, closes it. Guarded by an environment variable so
    # the second pass cannot start a third.
    if (self_before is not None and _sha256(HERE) != self_before
            and not os.environ.get(_SECOND_PASS_ENV)):
        print("precedent_vendor_engine refresh: this refresh replaced the "
              "vendoring tool itself, so its own file list may have changed "
              "-- running once more with the new copy.")
        r = subprocess.run(
            [sys.executable, str(HERE), 'refresh', str(clone), '--force']
            + (['--from-ref', ref] if ref else []),
            env={**os.environ, _SECOND_PASS_ENV: '1'})
        if r.returncode != 0:
            return r.returncode

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
    rest = args[2:]
    ref = None
    if '--from-ref' in rest:
        i = rest.index('--from-ref')
        if i + 1 >= len(rest):
            sys.exit("precedent_vendor_engine FAIL: --from-ref needs a value "
                     "(a commit or ref inside the clone).")
        ref = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]
    unknown = [a for a in rest if a != '--force']
    if unknown:
        sys.exit(f"precedent_vendor_engine FAIL: unknown argument(s) to "
                 f"refresh: {', '.join(unknown)}.")
    if ref is not None:
        resolved = _rev(clone, ref)
        if not resolved:
            sys.exit(f"precedent_vendor_engine FAIL: --from-ref {ref!r} does "
                     f"not resolve in {clone}.")
        ref = resolved
    return refresh(clone, force='--force' in args, ref=ref)


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

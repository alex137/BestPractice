#!/usr/bin/env python3
"""check_session_trailer.py -- the mechanical check for
practices/session-trailer.md.

# practice: session-trailer

Scope: tree, judged on what a push would carry. Every non-merge commit
reachable from HEAD that origin does not have yet must carry a session
trailer line -- `Session: <url>`, `Claude-Session: <url>`
(the trailer key Claude Code Remote's own harness actually emits as of
2026-09; functionally the same trailer the practice's Rule describes,
under a different key), or the explicit `Session: none available (<tool>)`
opt-out. A commit with none of these is the "forgotten" case the
practice's own Why section exists to make distinguishable from "considered
and skipped."

Merge commits are excluded: a merge doesn't represent new planned work of
its own (the substantive commits underneath it already carry their own
trailers), and GitHub's own merge-via-API/UI commits never carry a custom
trailer at all -- checking them would fail on every single PR merge,
forever, for a reason that has nothing to do with this practice's actual
intent ("committing anything" in the occasion sense means authoring a
change, not the structural act of merging one).

WHICH COMMITS (2026-09-29, Morgan, strength: decided). This walked every
commit reachable from HEAD, so a commit that reached main before this check
ran anywhere failed every later full sweep -- a consumer's Promote refused
over one such commit already on main, which nothing a session could do
would fix without rewriting published history. It now judges only what is
not on origin yet (`HEAD --not --remotes=origin`): each commit is judged at
the first push that carries it -- Booked into pre-staging included -- the
same way the author and date checks judge only what a push brings. Nothing
already on origin needs grandfathering. `--range A..B` (or the
PRECEDENT_CHECK_RANGE environment variable) judges exactly that range, and
`--all-history` restores the whole walk for a deliberate audit.

Two kinds of commit are exempt besides merges:
  - one GitHub made with its own buttons (committer `noreply@github.com`:
    a merge, squash or revert button, a web edit) -- no session wrote it,
    and there is nowhere to add a trailer;
  - a revert (`Revert "..."` / `This reverts commit <sha>.`), but only where
    `revert-needs-no-trailer` (universal since 2026-10-05) is in force.
    Where it is not in force, a revert still needs the trailer.

Exit 0 and print nothing when clean. Exit 1 and print the practice's own
Rule text (never a paraphrase) plus the specific finding(s) on a violation.
Exit 2 -- SKIPPED, the NotApplicable convention -- when the history this
scope needs is not all here to be walked. See truncated_history().
"""
import json
import os
import pathlib
import re
import subprocess
import sys

# TWO different questions, which used to share one name -- and that is exactly
# how a practice file went missing. SOURCE_ROOT is the practice set this script
# ships in; ROOT is the repository it AUDITS.
#
# They are the same directory in both normal cases: run in place inside its own
# set, and materialized into a consuming repo (where precedent_materialize.py
# has written practices/ and tools/checks/ side by side). They differ in the
# third case -- a repo that DECLARES this source but never materializes it, and
# runs the script in place against itself. Precedent's own repo is exactly
# that: its practices/ is the universal catalogue, so `parents[2]/practices/`
# resolved to a directory this practice was never in, and rule_text() raised
# FileNotFoundError from inside the violation printer (2026-09-06). The rule
# text always ships beside the script, so it is looked up against SOURCE_ROOT
# and can no longer be absent; only what to audit is overridable.
SOURCE_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ROOT = pathlib.Path(os.environ.get("PRECEDENT_CHECK_ROOT") or SOURCE_ROOT)
PRACTICE_FILE = SOURCE_ROOT / "practices" / "session-trailer.md"

TRAILER_RE = re.compile(r"^(?:Session|Claude-Session):\s+(\S.*)$", re.MULTILINE)

# practice: no-rewrite-for-warnings -- this one commit predates the
# practice's own check, is not a merge, and isn't ours to rewrite (authored
# before this exemption mechanism existed). Rewriting already-published
# history to silence a check is exactly what that practice forbids; its
# own Install section calls for scoping the check instead, which is what
# this list does. Found and left as a noted, unfixed backlog item
# 2026-09-03. Every non-merge commit made after this list was added is
# still fully checked -- this exempts exactly this one SHA, nothing else.
GRANDFATHERED_SHAS = {
    "61f2ed8b24020eaaedc03336e262709bb7725176",  # 2026-09-02, pre-check
}

# PER-REPO exemptions, 2026-09-14. The set above is this SOURCE's own
# history -- hardcoded, because this check was written when it only ever ran
# against the repo it ships in. Materialized into a CONSUMER it audits
# `ROOT`'s history instead, and no consumer can add to a set living in a file
# precedent_materialize.py overwrites on every sync.
#
# check_commit_author.py and check_buenos_aires_dates.py closed exactly this
# gap for themselves on 2026-09-07 and 2026-09-10. This check did not, and
# nothing recorded that the three had diverged -- so a consumer could exempt
# a pre-hook commit from two of the three sibling checks and was simply stuck
# with the third. Found 2026-09-14 in a consumer with 21 commits predating
# its own commit-identity wiring: 14 of them could be declared, and the 7
# this check flags could not, for no reason either check could state.
#
# Same mechanism, deliberately identical rather than merely similar, so the
# three stay comparable: {"sha": <40-hex>, "note": <why>} entries, additive
# to the set above and never a replacement for it, read from BOTH
# identity.json (a source repo, which is somebody's individual practice set)
# and precedent.json (a shared consuming repo, which must not carry an
# identity.json -- that file MEANS "this repository is somebody's individual
# source" and would pin one person's identity onto everyone committing
# there). A malformed entry is reported as a finding rather than silently
# ignored: a grandfather list that drops an entry quietly is
# indistinguishable from one that was never declared.
IDENTITY_FILE = ROOT / "identity.json"


def _declaration_files():
    """(path, label) for every file that may carry a grandfather list here."""
    return [(IDENTITY_FILE, "identity.json"),
            (ROOT / "precedent.json", "precedent.json")]


def _repo_grandfathered_shas() -> tuple:
    shas = set()
    findings = []
    for path, label in _declaration_files():
        # Read from the FILE, not from a resolved identity: this list is a
        # property of the repository being audited (which of ITS commits are
        # exempt), while a resolved identity may legitimately come from a
        # user-level config pointing somewhere else entirely. Another
        # person's practice source must never hand exemptions to this repo.
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            # Absent or unreadable is not a finding HERE: a repo with no
            # precedent.json simply has no consumer-level declaration, a
            # shared repo correctly has no identity.json at all, and a
            # malformed one is another check's business.
            continue
        for entry in (data or {}).get("grandfathered_commit_shas") or []:
            sha = entry.get("sha") if isinstance(entry, dict) else None
            if not sha or not re.fullmatch(r"[0-9a-f]{40}", sha):
                findings.append(
                    f"{label}: grandfathered_commit_shas entry {entry!r} "
                    f"is not a {{\"sha\": <40 lowercase hex chars>, \"note\": ...}} "
                    f"object -- ignored, not exempted")
                continue
            if not (isinstance(entry, dict) and entry.get("note")):
                findings.append(
                    f"{label}: grandfathered_commit_shas entry for "
                    f"{sha[:12]} has no \"note\" -- every exemption records why "
                    f"(practice: cite-the-incident)")
            shas.add(sha)
    return shas, findings


_REPO_GRANDFATHERED_SHAS, _REPO_GRANDFATHERED_FINDINGS = _repo_grandfathered_shas()
EFFECTIVE_GRANDFATHERED_SHAS = GRANDFATHERED_SHAS | _REPO_GRANDFATHERED_SHAS


class NotApplicable(Exception):
    pass


def truncated_history() -> str:
    """-> a reason string when this clone does NOT hold the whole history
    `Scope: tree` claims to audit, or "" when it does.

    WHY A CLEAN RUN WAS NOT EVIDENCE (2026-09-10). find_violations() walks
    `git log` and reports what it finds. On a SHALLOW clone the walk simply
    stops at the graft boundary, finds nothing beyond it, and the check
    exits 0 -- reporting "every non-merge commit reachable from HEAD carries
    a trailer" when what actually happened is that most commits were never
    looked at. "Nothing to report" and "could not look" produced the same
    green, which is the failure this function exists to separate.

    Measured in this repo, on the clone this session started from:
    `git log` saw 101 commits and the check said clean; after
    `git fetch --depth=1000 origin main` it saw 114. Thirteen commits had
    been out of reach, and nothing said so. None of the thirteen turned out
    to violate -- which is luck, and exactly why it is worth a guard: the
    green looked identical either way.

    Note that this is NOT the same hazard `_is_merge` documents below.
    That one is about how git PRETTY-PRINTS a commit at the boundary; this
    one is about which commits the traversal reaches at all. Both come from
    shallowness and they need different answers, which is why fixing that
    one in 2026-09-06 did not fix this one."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--is-shallow-repository"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip() == "true":
        return ("this is a shallow clone, so `git log` reaches only part of "
                "the history this tree-scope check is supposed to walk -- "
                "run `git fetch --depth=1000 origin <branch>` (or a deeper "
                "value) and re-run to get a real answer")
    return ""


def rule_text() -> str:
    # A materialized check runs in whatever repo its source was resolved
    # into, and the practice file it quotes is not guaranteed to be there:
    # a repo that declares the source but never materializes it, or a
    # practice retired out of the tree, both leave PRACTICE_FILE absent.
    # Unguarded, this raised FileNotFoundError from inside the violation
    # PRINTER -- so the finding was correctly detected, correctly printed,
    # and then buried under a traceback. Found 2026-09-06 running every
    # source-supplied check against BestPractice; 14 of the 16 shared this
    # exact body. The Rule text being unavailable is not the check failing.
    if not PRACTICE_FILE.is_file():
        return "(practice file not found at %s)" % PRACTICE_FILE
    text = PRACTICE_FILE.read_text(encoding="utf-8")
    m = re.search(r"## Rule\n(.*?)\n## ", text, re.S)
    return m.group(1).strip() if m else "(no Rule found)"


def _is_merge(sha: str) -> bool:
    """Parent count, read from the raw commit object rather than
    `git log`/`show --format=%P`. On a shallow clone (this repo's own
    documented default -- see AGENTS.md's environment-gotchas), git's
    pretty-printers report a commit at the shallow boundary as parentless
    for TRAVERSAL purposes, even when its object header genuinely records
    two parents: `git log --format=%P` on this repo's own root-looking
    commit silently came back empty at depth 1, and only `git cat-file -p`
    -- which reads the object's own header, unaffected by shallow grafting
    -- showed the real `parent`/`parent` pair. Using `%P` here would have
    made this exact check wrongly re-flag a real merge commit as a bare,
    trailer-missing one on the next fresh shallow clone."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "-p", sha],
        capture_output=True,
        text=True,
        check=True,
    )
    return sum(1 for line in result.stdout.splitlines() if line.startswith("parent ")) >= 2


WEB_FLOW_COMMITTER = "noreply@github.com"
REVERT_RE = re.compile(r"^Revert \"|^This reverts commit [0-9a-f]{7,40}\b", re.M)
REVERT_PRACTICE = "revert-needs-no-trailer"


def revert_exemption_in_force() -> bool:
    """True when `revert-needs-no-trailer` resolves in force for ROOT.

    Asked through the engine's own resolver, which every repository this
    script runs in carries under tools/, so "in force" means exactly what it
    means to every other tool: declared by a source this repo resolves, and
    `status: active` there. Anything that goes wrong asking is False -- the
    exemption is opt-in, so failing to confirm it keeps the stricter rule."""
    import contextlib
    import io
    for tools in (ROOT / "tools", SOURCE_ROOT / "tools"):
        if not (tools / "precedent_resolve.py").is_file():
            continue
        sys.path.insert(0, str(tools))
        try:
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                import precedent_resolve as pr
                res = pr.resolve(pr.load_config(str(ROOT)))
            return REVERT_PRACTICE in (res.get("practices") or {})
        except (Exception, SystemExit):
            return False
        finally:
            sys.path.pop(0)
    return False


def _walk_args(argv) -> tuple:
    """-> (git log revision arguments, mode). Modes: 'range', 'all',
    'unpushed' (the default)."""
    rng = None
    if "--range" in argv:
        i = argv.index("--range")
        rng = argv[i + 1] if i + 1 < len(argv) else None
    rng = rng or os.environ.get("PRECEDENT_CHECK_RANGE") or None
    if rng:
        # A symmetric `A...B` would also list A's side; a push carries B's.
        return [rng.replace("...", "..")], "range"
    if "--all-history" in argv:
        return ["HEAD"], "all"
    return ["HEAD", "--not", "--remotes=origin"], "unpushed"


def find_violations(argv=()) -> list[str]:
    revs, mode = _walk_args(list(argv))
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "--format=%H%x00%ce%x00%B%x01", *revs],
        capture_output=True,
        text=True,
        check=True,
    )
    findings = list(_REPO_GRANDFATHERED_FINDINGS)
    examined = 0
    reverts_ok = None
    for entry in result.stdout.split("\x01"):
        entry = entry.strip("\n")
        if not entry.strip():
            continue
        sha, _, rest = entry.partition("\x00")
        committer, _, body = rest.partition("\x00")
        examined += 1
        if sha in EFFECTIVE_GRANDFATHERED_SHAS:
            continue
        if _is_merge(sha):
            continue  # see the module docstring
        if committer.strip().lower() == WEB_FLOW_COMMITTER:
            continue  # made with GitHub's own buttons; see the docstring
        if TRAILER_RE.search(body):
            continue
        if REVERT_RE.search(body):
            if reverts_ok is None:
                reverts_ok = revert_exemption_in_force()
            if reverts_ok:
                continue
        findings.append(f"commit {sha[:12]}: no `Session:` trailer in the commit message")
    # An empty walk of the WHOLE history is never a pass: a repo with no
    # commits, or a `git log` that came back empty for any other reason,
    # used to fall straight through to exit 0. An empty walk of what a push
    # carries is the ordinary case -- everything is already on origin.
    if examined == 0 and mode == "all":
        raise NotApplicable("`git log` reached no commits at all in "
                            f"{ROOT}, so nothing was actually checked")
    return findings, mode


if __name__ == "__main__":
    try:
        findings, mode = find_violations(sys.argv[1:])
    except NotApplicable as e:
        print(f"SKIPPED: {PRACTICE_FILE.stem}: {e}")
        sys.exit(2)

    # ORDER MATTERS, and this is the whole point of the 2026-09-10 change.
    # A violation found in the part of the history that IS here is a real
    # violation and still fails -- a partial view can only cost findings,
    # never invent them, so what it did see is trustworthy. What a partial
    # view must never do is report the repo CLEAN.
    if findings:
        print(f"VIOLATION: {PRACTICE_FILE.stem}")
        for f in findings:
            print(f"  {f}")
        print("\nthe rule:")
        print("  " + rule_text().replace("\n", "\n  "))
        sys.exit(1)

    # Only a walk of the whole history can be cut short by a shallow clone:
    # what a push carries is local by definition, and an explicit range
    # names its own ends.
    reason = truncated_history() if mode == "all" else ""
    if reason:
        print(f"SKIPPED: {PRACTICE_FILE.stem}: {reason}")
        sys.exit(2)
    sys.exit(0)

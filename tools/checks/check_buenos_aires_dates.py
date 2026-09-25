#!/usr/bin/env python3
"""check_buenos_aires_dates.py -- the mechanical check for
practices/buenos-aires-dates.md.

# practice: buenos-aires-dates

Scope: tree. Covers only the mechanically checkable half of the practice:
the git-commit mechanism. `git` records each commit's author-date UTC
offset verbatim from the environment's `TZ` at commit time, so a commit
made under `TZ="America/Argentina/Buenos_Aires"` always carries a fixed
"-0300" offset (Argentina has held UTC-3 with no DST since 2009 -- see the
practice's own Detail section). Every commit reachable from HEAD must carry
that offset.

The prose-date mechanism ("a doc's as-of note uses the Buenos Aires
calendar date on the day the text was written") has no mechanical
signature: nothing in the repo lets a check independently know what the
actual Buenos Aires wall-clock date was at write time, so it cannot be
verified here. See the practice file's own Install section for this split.

Exit 0 and print nothing when clean. Exit 1 and print the practice's own
Rule text (never a paraphrase) plus the specific finding(s) on a violation.
Exit 2, printing SKIPPED and a reason, when the check could not run at all
-- no identity is declared anywhere reachable (a shared repo, the expected
state there and not a defect), or the engine module is absent. That is
precedent_check.py's own convention for a source-supplied script, and its
runner turns exit 2 into SKIPPED rather than into a pass.
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import zoneinfo

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
PRACTICE_FILE = SOURCE_ROOT / "practices" / "buenos-aires-dates.md"

# Still named here, and still read directly, for two questions that are
# genuinely about THIS repository rather than about whose zone a commit
# should carry: the per-repo grandfather list below, and telling a broken
# declaration apart from an absent one in _resolve().
IDENTITY_FILE = ROOT / "identity.json"

# THE TIMEZONE IS NOT WRITTEN HERE. It comes from the DECLARED IDENTITY --
# the person this repo resolves, whose zone is a person-level fact
# (practice: registry-source-of-truth) -- and the offset is computed from
# it. That makes this file generic: materialized into anybody's repo, it
# checks the commits there against whichever person that repo can resolve.
#
# The offset is computed for NOW, and compared against every commit in
# history. For this repo's declared zone that is exact -- Argentina has held
# UTC-3 with no daylight saving since 2009, which is what made a hardcoded
# "-0300" defensible before this. A zone that DOES observe daylight saving
# would make this check wrong for half the year, and the honest fix there is
# per-commit resolution rather than one offset; said out loud here rather
# than discovered by whoever adopts this file next.

# --------------------------------------------------------------------------
# THE DECLARED IDENTITY IS THE ENGINE'S ANSWER, NOT THIS SCRIPT'S (2026-09-10)
#
# This check used to read `identity.json` at ROOT itself and report a
# VIOLATION when it was absent. But an identity.json at a repo's root MEANS
# "this repository is somebody's individual practice source" -- it is step 2
# of commit-identity.sh's own resolution order -- so a SHARED consuming repo
# must not have one, which is exactly what the per-repo grandfathering
# comment in check_commit_author.py already said at length. The two
# statements together left this check permanently red in every shared
# consuming repo, with the fix forbidden by the same file that demanded it.
# Found 2026-09-10 installing precedent-beta-v01 into a real private project
# via INSTALL.md section 0: the install ended on exactly these two checks,
# and writing reasoned `not_binding` exemptions for them did not help either.
#
# precedent_identity.declared_identity() answers it now, looking where
# commit-identity.sh looks and in the same order -- a PRECEDENT_COMMIT_*
# override, this repo's own identity.json, the individual source named by the
# user-level config -- and raising NoDeclaredIdentity when none of the three
# does. That is this check's cue to STAND DOWN, never to report a violation:
# a violation here must mean "a commit has the wrong author", not "this
# repository is shared". It deliberately stops there rather than falling
# through to the session owner, the authenticated GitHub account or an
# existing git config, the way commit-identity.sh continues to for AUTHORING
# a commit: those are inferences about an environment, and a check that
# judged a commit against the ambient git config would pass whatever it found.
#
# WHICH MODULE, 2026-09-10 (same day, second revision): the resolution
# moved upstream out of precedent_resolve.py into precedent_identity.py,
# which is in ENGINE_FILES rather than CONSUMER_ENGINE_FILES, so a practice
# SET vendors it too -- see _identity_module() below for why that matters and
# why the resolver is still tried second. mirrored_prefixes() stayed in the
# resolver, so the other checks here that use it are unaffected.
#
# THIS BLOCK IS DUPLICATED, verbatim, in the other identity check
# (check_commit_author.py), and that is forced rather than sloppy:
# precedent_materialize.py
# copies only the `check_*.py` scripts a practice's `checked_by:` claims, so
# a shared helper module beside them would never travel into a consuming
# repo. rule_text() is duplicated across all eight checks here for the same
# reason.


class NotApplicable(Exception):
    """This check cannot run here: reported as SKIPPED, exit 2.

    precedent_check.py's runner for source-supplied scripts turns exit 2
    into its own NotApplicable, which prints SKIPPED with the reason. A
    check that could not run says so rather than passing -- that module's
    own rule ("A CHECK THAT CANNOT RUN REPORTS THAT IT DID NOT RUN"), and
    this repo has been bitten by the opposite."""


def _identity_module():
    """The engine module that answers who this repo's commits belong to, or
    NotApplicable.

    `precedent_identity` FIRST, `precedent_resolve` second, and the order is
    the whole point. `declared_identity()` was born in the resolver and moved
    out of it the same day (upstream 2026-09-10): the resolver is in
    precedent_vendor_engine.py's CONSUMER_ENGINE_FILES and deliberately NOT
    in its ENGINE_FILES, because a practice SET resolves no catalogue -- so a
    set does not vendor it, and these two checks went from enforcing to
    SKIPPED inside the very set they belong to, which is not a state anyone
    wanted. Identity is a question about a PERSON, and a practice set is the
    one repository that most certainly has one: an `identity.json` at a
    repo's root is what declares "this repository is somebody's individual
    practice source". So the resolution now lives in `precedent_identity.py`,
    which IS in ENGINE_FILES and reaches every kind of repo the engine
    reaches.

    The resolver keeps re-exporting both names, so the fallback below is for
    a CONSUMING repo whose vendored engine predates the split -- a
    compatibility path, never a preference. Anything in these sets that needs
    an identity imports `precedent_identity`; the resolver answers questions
    about a catalogue.

    Two install layouts, both real: INSTALL.md section 0 puts the engine at
    `<repo>/tools/`, and the classic section 1 vendoring puts it at
    `<repo>/process/upstream/tools/`. Both are searched, plus the tools/
    directory this script itself sits under, so neither layout silently loses
    the module."""
    tried = []
    for name in ("precedent_identity", "precedent_resolve"):
        for d in (ROOT / "tools",
                  ROOT / "process" / "upstream" / "tools",
                  pathlib.Path(__file__).resolve().parent.parent,
                  SOURCE_ROOT / "tools"):
            if (d / (name + ".py")).is_file():
                sys.path.insert(0, str(d))
                break
        try:
            module = __import__(name)
        except Exception as e:
            tried.append(f"{name}.py ({e})")
            continue
        # A module that imported but does not carry the two names is an
        # engine mid-migration, not an answer. Reported as could-not-run
        # rather than crashed on the AttributeError further down.
        if hasattr(module, "declared_identity") and \
                hasattr(module, "NoDeclaredIdentity"):
            return module
        tried.append(f"{name}.py imported but declares no declared_identity()")
    raise NotApplicable(
        "no engine module could supply the declared identity, so no commit "
        "here can be judged against one (tried " + "; ".join(tried) + "). "
        "`precedent_identity.py` is in upstream's ENGINE_FILES, so every kind "
        "of repo should vendor it -- an engine that predates it needs a "
        "refresh (`python3 tools/precedent_vendor_engine.py refresh "
        "<bestpractice-clone>`). Reporting SKIPPED is the honest answer where "
        "a silent pass would not be")


def _resolve():
    """-> (identity, violation, stand_down); exactly one is truthy.

    `identity` is declared_identity()'s dict --
    {'name', 'email', 'timezone', 'source'} -- when a person is declared
    somewhere this repo can reach.

    `violation` is set for the one case where nothing resolved but the
    absence is NOT the shared-repo case: an identity.json sitting at this
    root, which means this repository IS an individual practice source, that
    no identity could be read out of. Present-but-unusable is a broken
    declaration, and this check is the thing that reports it.

    `stand_down` is a NotApplicable for every other non-answer."""
    # NO SHARED REPO'S HISTORY IS AUDITED AGAINST ONE PERSON'S ZONE (Morgan,
    # 2026-09-25): other people's commits live there. A repo without its own
    # identity.json -- every shared and consuming repo -- stands down here
    # instead of resolving the person through the user-level config. The
    # person's own NEW commits there still carry their zone: that is
    # enforced at commit time by commit-identity.sh's backstop ("I meant the
    # repo timezone to be a fallback, in case there is no defined individual
    # timezone defined", the same day), not by auditing history.
    if not IDENTITY_FILE.is_file():
        return None, "", NotApplicable(
            "this repo has no identity.json of its own, so it is not "
            "anybody's individual practice source, and a person's timezone "
            "is enforced only in their own individual source")
    try:
        engine = _identity_module()
    except NotApplicable as e:
        return None, "", e
    try:
        return engine.declared_identity(ROOT), "", None
    except engine.NoDeclaredIdentity as e:
        if IDENTITY_FILE.is_file():
            return None, (
                f"identity.json exists at this repo's root -- which means "
                f"this repository IS somebody's individual practice source "
                f"-- but no identity could be resolved from it ({e})"), None
        return None, "", NotApplicable(
            f"{e}. So this check stands down instead of reporting a "
            f"violation: a violation here must mean \"a commit has the wrong "
            f"author\", never \"this repository is shared\"")


_IDENT, _IDENT_VIOLATION, _STAND_DOWN = _resolve()
_ZONE = (_IDENT or {}).get("timezone") or ""
IDENTITY_SOURCE = (_IDENT or {}).get("source") or ""
try:
    EXPECTED_OFFSET = datetime.datetime.now(
        zoneinfo.ZoneInfo(_ZONE)).strftime("%z") if _ZONE else ""
    _ZONE_ERROR = "" if EXPECTED_OFFSET else "declares no timezone"
except Exception as _e:   # a zone name no tzdata here knows
    EXPECTED_OFFSET = ""
    _ZONE_ERROR = (f"declares the timezone {_ZONE!r}, which this machine's "
                   f"zone database does not know ({_e})")

# GRANDFATHERED_SHAS, SCRUBBED FOR THIS REPO, 2026-09-22. The upstream copy
# of this file (precedent-individual, this practice's SOURCE) hardcodes that
# SOURCE's own historical exemptions here -- its own commit SHAs, with the
# incident story behind each, including references to other private
# repositories by name. Those SHAs belong to a different repository's
# history and can never appear in this one; the private references must
# never be published here regardless. Empty rather than populated with this
# repo's own history for the same reason check_commit_author.py's own
# PER-REPO mechanism exists: a hardcoded set is right for a SOURCE auditing
# itself, wrong for a CONSUMER, and BestPractice is a consumer of this check
# the same way any other repo materializing it is. Also moot under the
# default scope as of 2026-09-22 (PRECEDENT_CHECK_FULL_HISTORY, see
# _log_scope_args() below): a routine run only ever looks at commits not yet
# on a remote, so an old, already-published incident in this repo's own
# history is out of scope by construction and never needs an entry here.
GRANDFATHERED_SHAS: set[str] = set()

# PER-REPO exemptions. This repo's OWN exemptions, if it ever needs one, go
# in precedent.json's `grandfathered_commit_shas` array -- {"sha": <40-hex>,
# "note": <why>} entries -- read by _declaration_files() below, shared
# verbatim with check_commit_author.py's identical mechanism (a commit
# grandfathered for one reason is very often grandfathered for the other
# too, same incident, so one declaration covers both checks). A malformed
# entry (no "sha", or not 40 hex characters) is reported as a finding rather
# than silently ignored.
def _declaration_files():
    """(path, label) for every file that may carry a grandfather list here."""
    return [(IDENTITY_FILE, "identity.json"),
            (ROOT / "precedent.json", "precedent.json")]


def _repo_grandfathered_shas() -> tuple[set[str], list[str]]:
    shas: set[str] = set()
    findings: list[str] = []
    for path, label in _declaration_files():
        # Read from the FILE, not from the resolved identity: this list is a
        # property of the repository being audited (which of ITS commits are
        # exempt), while the resolved identity may legitimately come from a
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


# ---------------------------------------------------------------------------
# A REPOSITORY WITH NO COMMITS IS NOT A VIOLATION OF ANYTHING (2026-09-14)
#
# `git log` exits 128 on an unborn HEAD, and this file's call used to carry
# check=True: the CalledProcessError escaped find_violations(), and
# tools/precedent_check.py printed the traceback as a VIOLATION of the
# practice itself -- the check crashing, reported as the repository
# misbehaving. A FRESH INSTALL IS EXACTLY A REPOSITORY WITH NO COMMITS, so
# every INSTALL.md section 0 install hit this, and hit it in both identity
# checks at once. Reported 2026-09-14 from the first section 0 install into
# a real project with subject matter of its own; invisible from inside a
# practice set, which has years of history to log.
#
# No history is a COULD-NOT-RUN -- never a pass, never a violation. There is
# no commit here yet to have the wrong author or the wrong offset, and the
# first one made is checked the moment it exists. So this raises the file's
# own NotApplicable (SKIPPED, exit 2) and SAYS WHICH could-not-run it is: a
# repository that declares no identity already skips for a different reason,
# and the two are only tellable apart by their message -- which is why the
# test for this asserts the wording and not just the exit code.
#
# DUPLICATED, verbatim, in the other identity check, for the reason the
# block above gives: precedent_materialize.py copies only the `check_*.py`
# scripts a practice's `checked_by:` claims, so a shared helper module
# sitting beside them would never travel into a consuming repo.
def _log_scope_args() -> list[str]:
    """Which commits this run audits: local-only (not yet on any remote) by
    default, or everything reachable from HEAD under
    PRECEDENT_CHECK_FULL_HISTORY=1.

    DUPLICATED, verbatim, from check_commit_author.py's copy of this
    function, for the reason this file's header already gives at length:
    precedent_materialize.py copies only the check_*.py scripts a practice's
    checked_by: claims, so a shared helper module beside them would never
    travel into a consuming repo. See that file's copy for the full
    reasoning (Morgan, 2026-09-22: "Whole history reviews are good for
    things like very deep check but not for daily practice")."""
    if os.environ.get("PRECEDENT_CHECK_FULL_HISTORY") == "1":
        return []
    has_remotes = subprocess.run(
        ["git", "-C", str(ROOT), "remote"],
        capture_output=True, text=True,
    ).stdout.strip()
    if not has_remotes:
        return []
    return ["HEAD", "--not", "--remotes"]


def _git_log_lines(*fmt: str) -> list[str]:
    """ROOT's `git log` output line by line, or NotApplicable saying why not."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", *fmt, *_log_scope_args()],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.splitlines()

    def _git_ok(*args: str) -> bool:
        return subprocess.run(["git", "-C", str(ROOT), *args],
                              capture_output=True, text=True).returncode == 0

    # --git-dir FIRST: a directory that is not a repository at all fails the
    # HEAD probe too, and answering "no commits yet" there would name the
    # wrong cause and send whoever reads it looking for the wrong fix.
    if not _git_ok("rev-parse", "--git-dir"):
        raise NotApplicable(
            f"{ROOT} is not a git repository, so it has no history for this "
            f"check to read")
    if not _git_ok("rev-parse", "--verify", "--quiet", "HEAD"):
        raise NotApplicable(
            "this repository has no commits yet, so there is no commit here "
            "to judge -- a fresh install is exactly this, and the first "
            "commit made will be checked as soon as it exists")
    raise NotApplicable(
        "`git log` exited %d and this repository's history could not be "
        "read: %s" % (result.returncode,
                      (result.stderr or "").strip() or "no error output"))


def find_violations() -> list[str]:
    if _STAND_DOWN is not None:
        raise _STAND_DOWN
    if _IDENT_VIOLATION:
        return [_IDENT_VIOLATION]
    if not EXPECTED_OFFSET:
        return [f"the declared identity ({IDENTITY_SOURCE}) {_ZONE_ERROR} -- "
                f"the zone is what every commit's offset is checked against, "
                f"so no offset can be checked without it"]
    findings = list(_REPO_GRANDFATHERED_FINDINGS)
    for line in _git_log_lines("--format=%H|%ad", "--date=format:%z"):
        if not line.strip():
            continue
        sha, offset = line.split("|", 1)
        if sha in EFFECTIVE_GRANDFATHERED_SHAS:
            continue
        if offset != EXPECTED_OFFSET:
            findings.append(
                f"commit {sha[:12]}: author-date offset is {offset!r}, "
                f"expected {EXPECTED_OFFSET!r} "
                f"(commit was not made under TZ={_ZONE}, the zone declared "
                f"by {IDENTITY_SOURCE})"
            )
    return findings


if __name__ == "__main__":
    try:
        findings = find_violations()
    except NotApplicable as e:
        # SKIPPED, exit 2 -- never a violation and never a silent pass. See
        # the NotApplicable docstring for the runner contract.
        print(f"SKIPPED: {e}")
        sys.exit(2)
    if findings:
        print(f"VIOLATION: {PRACTICE_FILE.stem}")
        for f in findings:
            print(f"  {f}")
        print("\nthe rule:")
        print("  " + rule_text().replace("\n", "\n  "))
        sys.exit(1)
    sys.exit(0)

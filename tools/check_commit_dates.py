#!/usr/bin/env python3
"""Each commit carries the declared person's time zone (practice buenos-aires-dates)

The engine's one copy of this check, for every kind of repository.

Its rule, buenos-aires-dates, lives in a person's own practice set, not in the
universal catalogue, so it is named here without a citation: engine code
cites only the catalogue it ships with (code-cites-practice).
the practice's checked_by ties the
two together.

ONE COPY, SHIPPED BY THE ENGINE (Morgan, 2026-10-10: "yes ... build the
shared check"). This file and its twin, check_commit_author.py, live in tools/ as engine
files, so every repository runs the same copy: BestPractice, every practice
set and every consumer. Until that day the practice's own set (the person's
individual set) shipped a copy in tools/checks/, which every consumer
materialized, while BestPractice kept a port of its own. The two drifted:
the set's copies lacked the bot-author warning, PRECEDENT_CHECK_RANGE and
the skip of commits GitHub makes, and a consumer's merge gate refused every
GitHub-button merge for it. Nothing personal is written here: the zone and
the author come from the declared identity, and a repository's own
exemptions from its identity.json or precedent.json.

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

# The helpers both commit-identity checks share, in one copy beside them.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import commit_checks_common as _common  # noqa: E402
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
SOURCE_ROOT = pathlib.Path(__file__).resolve().parent.parent
ROOT = pathlib.Path(os.environ.get("PRECEDENT_CHECK_ROOT") or SOURCE_ROOT)


def practice_file():
    """The practice that names this script as its check, or None
    (commit_checks_common.practice_file)."""
    return _common.practice_file(pathlib.Path(__file__).name, ROOT)

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
# SHARED WITH THE OTHER IDENTITY CHECK (check_commit_author.py) through
# tools/commit_checks_common.py, since 2026-10-17. This block used to be
# duplicated verbatim in both, with a comment calling that forced: the
# materializer copied only the `check_*.py` scripts a practice claimed, so a
# helper beside them would never have reached a consumer. Both checks have
# been engine files since 2026-10-10, shipped with the rest of the engine,
# so the helpers now live once, beside them, and each check keeps only what
# is its own.


NotApplicable = _common.NotApplicable


def _identity_module():
    """The engine module that answers who this repo's commits belong to, or
    NotApplicable (commit_checks_common.identity_module says why the order)."""
    return _common.identity_module(ROOT, SOURCE_ROOT,
                                   pathlib.Path(__file__).resolve().parent)


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
    return _common.declaration_files(ROOT, IDENTITY_FILE)


def _repo_grandfathered_shas() -> tuple[set[str], list[str]]:
    return _common.repo_grandfathered_shas(_declaration_files())


_REPO_GRANDFATHERED_SHAS, _REPO_GRANDFATHERED_FINDINGS = _repo_grandfathered_shas()
EFFECTIVE_GRANDFATHERED_SHAS = GRANDFATHERED_SHAS | _REPO_GRANDFATHERED_SHAS


def rule_text() -> str:
    return _common.rule_text(practice_file())


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
    # AN EXPLICIT RANGE WINS, as in check_commit_author.py's copy (added
    # there 2026-10-06 and missed here until 2026-10-10).
    rng = os.environ.get("PRECEDENT_CHECK_RANGE")
    if rng:
        return [rng.replace("...", "..")]
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
    return _common.git_log_lines(ROOT, _log_scope_args(), *fmt)


def _bot_emails() -> set[str]:
    """The harness's bot addresses (precedent_session_check.BOT_EMAILS), or
    an empty set when they cannot be read -- then every commit is judged, as
    before. A bot-authored commit is check_commit_author.py's WARNING, an
    emergency fallback allowed by Morgan on 2026-10-06; it carries the
    container's offset, so judging it here would refuse the very commit that
    rule allows."""
    for d in (ROOT / "tools", ROOT / "process" / "upstream" / "tools",
              pathlib.Path(__file__).resolve().parent):
        if (d / "precedent_session_check.py").is_file():
            sys.path.insert(0, str(d))
            break
    try:
        import precedent_session_check
        return {e.lower() for e in precedent_session_check.BOT_EMAILS}
    except Exception:                                        # noqa: BLE001
        return set()


# A commit GitHub itself committed -- its merge button, a squash, or the
# test merge refs/pull/N/merge the merge gate judges -- carries the date
# GitHub gave it, in UTC, whoever it names as author. The person never chose
# that offset, so it is no finding here, the way check_session_trailer.py
# skips the same committer. Found 2026-10-10: a consumer's merge gate
# refused every GitHub-button merge over the test merge's "+0000". Morgan,
# the same day: "it's fine if github does things in UTC, the buenos aires
# timezone is just for me."
WEB_FLOW_COMMITTER = "noreply@github.com"


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
    bots = _bot_emails()
    for line in _git_log_lines("--format=%H|%ae|%ce|%ad", "--date=format:%z"):
        if not line.strip():
            continue
        sha, email, committer, offset = line.split("|", 3)
        if sha in EFFECTIVE_GRANDFATHERED_SHAS or email.lower() in bots:
            continue
        if committer.strip().lower() == WEB_FLOW_COMMITTER:
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
    # Every engine tool answers --help (verify_harness: every tool answers
    # --help with exit 0); this one has lived in tools/ since 2026-10-10.
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(__doc__.strip())
        sys.exit(0)
    try:
        findings = find_violations()
    except NotApplicable as e:
        # SKIPPED, exit 2 -- never a violation and never a silent pass. See
        # the NotApplicable docstring for the runner contract.
        print(f"SKIPPED: {e}")
        sys.exit(2)
    if findings:
        print(f"VIOLATION: {(practice_file() or pathlib.Path('the declared-identity rule')).stem}")
        for f in findings:
            print(f"  {f}")
        print("\nthe rule:")
        print("  " + rule_text().replace("\n", "\n  "))
        sys.exit(1)
    sys.exit(0)

#!/usr/bin/env python3
"""check_commit_author.py -- the mechanical check for practices/commit-author.md.

# practice: commit-author

Scope: tree. Every commit reachable from HEAD in this repo must be authored
as the person this repo's DECLARED IDENTITY names -- both the git-recorded
author name and email, which is what `git config user.name`/`user.email`
actually produces on every subsequent commit once set correctly.

THE NAME AND ADDRESS ARE NOT WRITTEN HERE, and since 2026-09-10 they are
not read from a root `identity.json` here either: they come from
`precedent_identity.declared_identity()`, which resolves them the way
commit-identity.sh does. See the long block above `_resolve()` for why that
matters -- in short, an `identity.json` at a repo's root means "this repo
is somebody's individual practice source", so requiring one made this check
permanently red in every SHARED consuming repo. This check is therefore
generic: the same file, materialized into anybody's repo, checks the
commits there against whichever person that repo can actually resolve, and
stands down where nobody is declared. It also verifies that everything else
which needs those values -- the `env` block in `.claude/settings.json` --
still agrees with that one declaration, which is the half that keeps "one
place" true rather than merely intended.

Exit 0 and print nothing when clean. Exit 1 and print the practice's own
Rule text (never a paraphrase) plus the specific finding(s) on a violation.
Exit 2, printing SKIPPED and a reason, when the check could not run at all
-- no identity is declared anywhere reachable (a shared repo, the expected
state there and not a defect), or the engine module is absent. That is
precedent_check.py's own convention for a source-supplied script, and its
runner turns exit 2 into SKIPPED rather than into a pass.
"""
import pathlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# A fixture commit is not a person's commit. The global commit backstop
# (commit-identity.sh, 2026-09-07) reaches every repository on the
# machine, including the throwaway ones this script builds, and refused
# them with an error naming only the git command. This is the override
# that backstop documents.
os.environ.setdefault('PRECEDENT_ALLOW_ANY_AUTHOR', '1')

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
PRACTICE_FILE = SOURCE_ROOT / "practices" / "commit-author.md"

# Still named here, and still read directly, for two questions that are
# genuinely about THIS repository rather than about which person a commit
# should belong to: the per-repo grandfather list below, and telling a
# broken declaration apart from an absent one in _resolve().
IDENTITY_FILE = ROOT / "identity.json"


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
# (check_buenos_aires_dates.py), and that is forced rather than sloppy:
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

EXPECTED_NAME = (_IDENT or {}).get("name") or ""
EXPECTED_EMAIL = (_IDENT or {}).get("email") or ""
EXPECTED_TZ = (_IDENT or {}).get("timezone") or ""
IDENTITY_SOURCE = (_IDENT or {}).get("source") or ""

# GRANDFATHERED_SHAS, SCRUBBED FOR THIS REPO, 2026-09-22. The upstream copy
# of this file (precedent-individual, this practice's SOURCE) hardcodes that
# SOURCE's own historical exemptions here -- its own commit SHAs, with the
# incident story behind each. Those SHAs belong to a different repository's
# history and can never appear in this one, so carrying them here is dead
# weight at best; the incident notes also name other private repositories by
# name, which this repo -- public -- must never publish. Empty rather than
# populated with this repo's own history for the same reason
# check_commit_author.py's own PER-REPO mechanism exists: a hardcoded set is
# right for a SOURCE auditing itself, wrong for a CONSUMER, and BestPractice
# is a consumer of this check the same way any other repo materializing it
# is. Also moot under the default scope as of 2026-09-22
# (PRECEDENT_CHECK_FULL_HISTORY, see _log_scope_args() below): a routine run
# only ever looks at commits not yet on a remote, so an old, already-published
# incident in this repo's own history is out of scope by construction and
# never needs an entry here at all.
GRANDFATHERED_SHAS: set[str] = set()

# PER-REPO exemptions. This repo's OWN exemptions, if it ever needs one, go
# in precedent.json's `grandfathered_commit_shas` array -- {"sha": <40-hex>,
# "note": <why>} entries -- read by _declaration_files() below, same
# mechanism precedent-individual documents at length in its own copy of this
# file. _declaration_files() also checks IDENTITY_FILE, but that path is not
# expected to exist here: an identity.json at a repo's root means that
# repository IS somebody's individual practice source, which BestPractice
# deliberately is not (it names nobody) -- the check is generic and looks
# anyway, the same way it does in any other consuming repo. A malformed
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
# The prevention half (added 2026-09-06, with the five grandfathered SHAs
# above). Checking only the commits already made is checking the outcome
# after it is too late to fix -- no-rewrite-for-warnings means a wrong
# author that reaches a published branch stays there. So this half checks
# the mechanism that stops one being made: bootstrap/commit-identity.sh and
# the `env` block that carries the same identity into repositories the hook
# cannot reach.
#
# DELIBERATE LIMIT: this half runs only where that mechanism is present --
# the publisher (bootstrap/commit-identity.sh) or a consumer that has
# copied it into .claude/hooks/. A consuming repo that has not adopted it
# yet is not failed for that: the commit-scan half above still runs there,
# and it is the half that actually catches the mistake. Failing every
# consumer for a mechanism they have not installed is how a suite goes red
# for reasons nobody can act on, which two earlier commits here already had
# to undo.
MARKER = "precedent:commit-identity"
PUBLISHER_IDENTITY = ROOT / "bootstrap" / "commit-identity.sh"
SETTINGS = ROOT / ".claude" / "settings.json"
CONSUMER_HOOKS_DIR = ROOT / ".claude" / "hooks"


def tracked_mode(path: pathlib.Path) -> str | None:
    rel = path.relative_to(ROOT)
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-s", str(rel)],
        capture_output=True, text=True, check=True,
    )
    line = result.stdout.strip()
    return line.split()[0] if line else None


def find_identity_script() -> pathlib.Path | None:
    if PUBLISHER_IDENTITY.exists():
        return PUBLISHER_IDENTITY
    if CONSUMER_HOOKS_DIR.is_dir():
        for script in sorted(CONSUMER_HOOKS_DIR.glob("*.sh")):
            try:
                if MARKER in script.read_text(encoding="utf-8"):
                    return script
            except (UnicodeDecodeError, OSError):
                continue
    return None


def env_findings(script: pathlib.Path) -> list[str]:
    """Some settings file must wire the script into SessionStart. Whether it
    must ALSO carry a literal identity in `env` depends on what ROOT is
    (2026-09-19, replacing an unconditional literal check):

    ROOT is an individual practice source (IDENTITY_FILE at its root --
    commit-identity.sh rung 2) -- self-declaring is correct there BY
    DESIGN, and tools/precedent_check.py's own `no-hardcoded-git-identity`
    check exempts exactly this case for exactly that reason (it detects the
    exemption the same way: a root identity.json). There, a literal `env`
    block is the one place these three values are allowed to repeat
    identity.json's, and drift between them is a plain bug this still
    asserts, literally, below.

    ROOT is a SHARED consuming repo (no root identity.json) -- a literal
    name or address in `env` there is precisely the anti-pattern
    `no-hardcoded-git-identity` exists to catch: GIT_AUTHOR_* outranks
    `git config user.*`, so it would silently override
    commit-identity.sh's per-person resolution for every collaborator who
    ever loads this file, not only the one who declared it. Demanding that
    duplication made the two checks fight each other -- a consumer could
    satisfy one only by violating the other. This check no longer demands
    it. What it demands instead -- the actual property the literal check
    was ever a proxy for -- is proved BEHAVIORALLY, in
    mid_session_attach_findings(): that a repository attached mid-session,
    which never runs this repo's own SessionStart hook, still resolves the
    right author from whatever mechanism this environment actually has (a
    declared PRECEDENT_COMMIT_* plus commit-identity.sh's own
    global-identity write, or an already-correct global git config).
    commit-identity.sh's own generated backstop states the principle this
    follows in so many words: check the value, not the settings that were
    supposed to produce it."""
    candidates = [p for p in (SETTINGS,) if p.exists()]
    if not candidates:
        return [f"{SETTINGS.relative_to(ROOT)} does not exist -- {script.relative_to(ROOT)} is not wired into anything"]

    per_file = {}
    for path in candidates:
        rel = path.relative_to(ROOT)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            per_file[rel] = [f"{rel}: not valid JSON ({e})"]
            continue

        findings = []
        entries = (data.get("hooks") or {}).get("SessionStart") or []
        wired = [h for entry in entries for h in entry.get("hooks", [])
                 if script.name in h.get("command", "")]
        if not wired:
            findings.append(f"{rel}: no SessionStart hook runs {script.name}")
        for hook in wired:
            if hook.get("async") is True:
                findings.append(f"{rel}: the {script.name} entry sets \"async\": true -- the identity must be set before anything commits")

        env = data.get("env") or {}
        if IDENTITY_FILE.is_file():
            # DERIVED, and checked against the one declaration -- only
            # enforced here because ROOT is itself the individual source
            # these values belong to (see the docstring above).
            for key, expected in (("GIT_AUTHOR_NAME", EXPECTED_NAME),
                                  ("GIT_AUTHOR_EMAIL", EXPECTED_EMAIL),
                                  ("TZ", EXPECTED_TZ)):
                if env.get(key) != expected:
                    findings.append(f"{rel}: env.{key} is {env.get(key)!r}, but the declared identity ({IDENTITY_SOURCE}) says {expected!r} -- that declaration is the one place these live; this block derives from it")
        if "GIT_COMMITTER_NAME" in env or "GIT_COMMITTER_EMAIL" in env:
            findings.append(f"{rel}: env sets GIT_COMMITTER_* -- deliberately out of scope; overriding the committer makes commits show as Unverified on GitHub and changes nothing about authorship")

        per_file[rel] = findings

    if any(not f for f in per_file.values()):
        return []
    return min(per_file.items(), key=lambda kv: len(kv[1]))[1]


def mid_session_attach_findings(script: pathlib.Path) -> list[str]:
    """Behavioral proof of the one property env_findings()'s literal check
    used to stand in for, in a SHARED consuming repo (no root
    identity.json -- see env_findings()'s docstring): that a repository
    attached mid-session -- one that never runs THIS repo's own
    SessionStart hook -- still resolves the declared author, from whatever
    mechanism this environment actually has in place. Skipped where ROOT
    IS an individual source: env_findings() asserts that case directly and
    literally, and this session's real PRECEDENT_COMMIT_*/global-identity
    chain is not the mechanism doing the work there, so there is nothing
    of this environment's to prove.

    Deliberately runs against the REAL ambient environment (this session's
    own os.environ), never a planted identity.json: mechanism_findings()'s
    own fixture plants one, in a DIFFERENT throwaway repo, to test "does
    the script apply a declaration correctly" independent of the network
    or of any one account -- a different and narrower property. Reusing
    that plant here would force declared=1 unconditionally and make this
    check pass regardless of whether THIS environment's real resolution
    chain (which is what an actually-attached repo would hit) closes the
    gap at all. HOME is still redirected to a throwaway directory, so a
    real global ~/.gitconfig on this machine is never read or written by
    the probe below."""
    if IDENTITY_FILE.is_file() or not EXPECTED_EMAIL:
        return []

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="commit-identity-attach-check-"))
    try:
        home = tmp / "home"
        home.mkdir()
        rooted = tmp / "rooted"
        subprocess.run(["git", "init", "-q", "-b", "work", str(rooted)],
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(rooted), "config", "core.hooksPath",
                        str(rooted / ".git" / "hooks")],
                       capture_output=True, check=True)

        env = dict(os.environ)
        env.update({"CLAUDE_PROJECT_DIR": str(rooted), "HOME": str(home)})
        run = subprocess.run(["bash", str(script)], capture_output=True, text=True, env=env)
        if run.returncode != 0:
            return [f"{script.relative_to(ROOT)}: exited {run.returncode} resolving this session's own real identity, so the mid-session-attach property below could not be tested"]

        attached = tmp / "attached"
        subprocess.run(["git", "init", "-q", "-b", "work", str(attached)],
                       capture_output=True, check=True)
        ident = subprocess.run(["git", "-C", str(attached), "var", "GIT_AUTHOR_IDENT"],
                               capture_output=True, text=True, env=env).stdout.strip()
        name = ident.split(" <", 1)[0] if " <" in ident else ""
        email = ident.split("<", 1)[1].split(">", 1)[0] if "<" in ident else ""
        if name != EXPECTED_NAME or email != EXPECTED_EMAIL:
            return [
                f"a repository attached mid-session -- one that never runs "
                f"{script.relative_to(ROOT)}'s own SessionStart hook -- would "
                f"resolve author {name!r} <{email}>, not the declared "
                f"{EXPECTED_NAME!r} <{EXPECTED_EMAIL}> ({IDENTITY_SOURCE}). "
                f"Neither this session's real PRECEDENT_COMMIT_*/"
                f"global-identity chain nor a literal env block closes that "
                f"gap here."]
        return []
    except subprocess.CalledProcessError as e:
        return [f"could not build the throwaway repositories for the mid-session-attach check: {e}"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def mechanism_findings() -> list[str]:
    script = find_identity_script()
    if script is None:
        return []

    findings = []
    rel = script.relative_to(ROOT)
    if tracked_mode(script) != "100755":
        findings.append(f"{rel}: git-tracked mode is {tracked_mode(script)}, expected 100755 (executable)")

    findings.extend(env_findings(script))
    findings.extend(mid_session_attach_findings(script))

    # Behavioral, not textual: run it, then try to make the exact mistake
    # it exists to prevent. core.hooksPath is pinned to the throwaway
    # repo's own hooks directory so that a global one -- a hosted container
    # sets one -- cannot decide the outcome either way.
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="commit-identity-check-"))
    try:
        repo = tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "work", str(repo)],
                       capture_output=True, check=True)
        hooks = repo / ".git" / "hooks"
        subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath", str(hooks)],
                       capture_output=True, check=True)
        # Write the RESOLVED declaration in, so the hook resolves from a
        # file rather than from the network or from whatever account
        # happens to be authenticated -- the property under test is "it
        # reads the declaration", and a test that needs the internet to
        # pass is a test that fails for reasons that are not the code's.
        #
        # Written rather than copied (2026-09-10): ROOT/identity.json is
        # exactly what a consuming repo must NOT have, and this half of the
        # check runs there whenever the hook has been copied into
        # .claude/hooks/. `shutil.copy(IDENTITY_FILE, ...)` raised
        # FileNotFoundError from inside the fixture builder in that case --
        # unreachable before, because an absent identity.json returned a
        # violation long before this line, and reachable the moment that
        # stopped being a violation.
        (repo / "identity.json").write_text(
            json.dumps({"name": EXPECTED_NAME, "email": EXPECTED_EMAIL,
                        "timezone": EXPECTED_TZ}, indent=2) + "\n",
            encoding="utf-8")
        (repo / "f.txt").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], capture_output=True, check=True)

        env = dict(os.environ)
        env.update({"CLAUDE_PROJECT_DIR": str(repo), "HOME": str(tmp)})
        run = subprocess.run(["bash", str(script)], capture_output=True, text=True, env=env)
        if run.returncode != 0:
            findings.append(f"{rel}: exited {run.returncode} -- a SessionStart hook must fail gracefully rather than take a session down over a git-config question")

        for key, expected in (("user.name", EXPECTED_NAME), ("user.email", EXPECTED_EMAIL)):
            got = subprocess.run(["git", "-C", str(repo), "config", "--local", "--get", key],
                                 capture_output=True, text=True).stdout.strip()
            if got != expected:
                findings.append(f"{rel}: after running, local {key} is {got!r}, expected {expected!r}")

        # THE TWO ASSERTIONS BELOW EXIST TO PROVE THE BACKSTOP REFUSES, so
        # they must not inherit the module-level PRECEDENT_ALLOW_ANY_AUTHOR
        # that lets this script BUILD its fixture. Setting it once at the top
        # and letting it reach here turned both assertions into no-ops: the
        # wrong-author commit was "accepted", and the check reported the
        # backstop broken when it was the test that had been disarmed.
        # Blanket overrides gut the tests that prove a refusal; scope them.
        commit_env = dict(env)
        commit_env.pop("PRECEDENT_ALLOW_ANY_AUTHOR", None)
        commit_env.update({"GIT_AUTHOR_NAME": "Someone Else",
                           # example.com, not .invalid: this repo is public
                           # and its own leak gate exempts the reserved
                           # documentation domains .com/.org but not
                           # .invalid, so the RFC 2606 domain that is
                           # actually exempted here is the one to use.
                           "GIT_AUTHOR_EMAIL": "someone@example.com",
                           "TZ": "UTC"})
        bad = subprocess.run(["git", "-C", str(repo), "commit", "-qm", "wrong author"],
                             capture_output=True, text=True, env=commit_env)
        if bad.returncode == 0:
            findings.append(f"{rel}: a commit authored by someone else, on a UTC clock, was accepted -- the pre-commit backstop is the layer that catches what the other two only configure")

        good_env = dict(env)
        good_env.pop("PRECEDENT_ALLOW_ANY_AUTHOR", None)
        good_env.update({"TZ": EXPECTED_TZ or "UTC"})
        good = subprocess.run(["git", "-C", str(repo), "commit", "-qm", "right"],
                              capture_output=True, text=True, env=good_env)
        if good.returncode != 0:
            findings.append(f"{rel}: a correct commit was REFUSED -- a backstop that blocks legitimate work would be worse than the mistake ({good.stderr.strip()[:200]})")
    except subprocess.CalledProcessError as e:
        findings.append(f"could not build the throwaway repository for the behavioral check: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return findings


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

    ADDED 2026-09-22 (Morgan, same day: "Whole history reviews are good for
    things like very deep check but not for daily practice" -- practice:
    durable-fix, cite-the-incident). commit-identity-push-gate.sh calls this
    script directly on every `git push`, bypassing precedent_check.py's own
    rotation slice on purpose (see that hook's header) -- and until now that
    meant EVERY commit reachable from HEAD was re-read and re-judged on
    EVERY push, forever. A commit already grandfathered paid that cost
    forever too; one that was fixed forward without a formal grandfather
    entry looked, from the next push on, exactly like a fresh violation --
    "an ancient issue that keeps coming back" is what that looks like from
    the outside, whether or not an entry was ever missing.

    `HEAD --not --remotes` is the same scoping the platform's own stop hook
    (outside this repo, not ours to edit) already uses, for the identical
    reason its own comment gives: once a commit is on a remote, checking it
    again on the NEXT push audits nothing new. Every commit still gets
    checked exactly once, at the one moment that is actually useful -- right
    before it is first published -- and never again after that: a STRICTER
    guarantee of eventual coverage than the old unconditional scan gave in
    practice anywhere else in this engine, since precedent_check.py's own
    ordinary runs only ever sampled these tree-scope checks on a rotation.

    A repo with no remote at all has no "already published" to exclude, so
    `git remote` coming back empty means the same thing PRECEDENT_CHECK_FULL_
    HISTORY=1 does: scope is everything reachable from HEAD."""
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
    if not EXPECTED_NAME or not EXPECTED_EMAIL:
        return [f"the declared identity ({IDENTITY_SOURCE}) supplies no name "
                f"or no email -- both are required; every commit here is "
                f"checked against them"]
    findings = list(_REPO_GRANDFATHERED_FINDINGS)
    for line in _git_log_lines("--format=%H|%an|%ae"):
        if not line.strip():
            continue
        sha, name, email = line.split("|", 2)
        if sha in EFFECTIVE_GRANDFATHERED_SHAS:
            continue
        if name != EXPECTED_NAME or email != EXPECTED_EMAIL:
            findings.append(
                f"commit {sha[:12]}: author is {name!r} <{email}>, "
                f"expected {EXPECTED_NAME!r} <{EXPECTED_EMAIL}> "
                f"(the identity declared by {IDENTITY_SOURCE})"
            )
    findings.extend(mechanism_findings())
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

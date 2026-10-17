#!/usr/bin/env python3
"""What the two commit-identity checks share: the identity module, the grandfather list, the log reader, the Rule text

commit_checks_common.py -- the helpers check_commit_author.py and
check_commit_dates.py both need, in one copy.

ONE COPY, IMPORTED (2026-10-17). Both checks carried these verbatim, under
a comment calling the duplication forced: precedent_materialize.py copied
only the `check_*.py` scripts a practice's `checked_by:` claimed, so a
helper module beside them would never have reached a consuming repo. That
stopped being true on 2026-10-10, when both checks became engine files in
tools/ (precedent_vendor_engine.py's ENGINE_FILES), shipped to every kind of
repository with the rest of the engine; this module ships beside them in the
same list. The very deep check of 2026-10-17 found the comment stale. What
still differs between the two checks -- which commits each reads, and how it
resolves an identity -- stays in each.

Every function takes the paths it needs instead of reading a module global,
so each check passes its own ROOT (the repository audited) and SOURCE_ROOT
(the engine it ships in). Standard library only.
"""
import json
import re
import subprocess
import sys


class NotApplicable(Exception):
    """This check cannot run here: reported as SKIPPED, exit 2.

    precedent_check.py's runner for source-supplied scripts turns exit 2
    into its own NotApplicable, which prints SKIPPED with the reason. A
    check that could not run says so rather than passing -- that module's
    own rule ("A CHECK THAT CANNOT RUN REPORTS THAT IT DID NOT RUN"), and
    this repo has been bitten by the opposite."""


def identity_module(root, source_root, script_dir):
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
        for d in (root / "tools",
                  root / "process" / "upstream" / "tools",
                  script_dir,
                  source_root / "tools"):
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


def declaration_files(root, identity_file):
    """(path, label) for every file that may carry a grandfather list here."""
    return [(identity_file, "identity.json"),
            (root / "precedent.json", "precedent.json")]


def repo_grandfathered_shas(declaration_files) -> tuple[set[str], list[str]]:
    """(exempt shas, findings) from every (path, label) in `declaration_files`."""
    shas: set[str] = set()
    findings: list[str] = []
    for path, label in declaration_files:
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


def git_log_lines(root, scope_args, *fmt: str) -> list[str]:
    """`root`'s `git log` output line by line, or NotApplicable saying why not."""
    result = subprocess.run(
        ["git", "-C", str(root), "log", *fmt, *scope_args],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.splitlines()

    def _git_ok(*args: str) -> bool:
        return subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, text=True).returncode == 0

    # --git-dir FIRST: a directory that is not a repository at all fails the
    # HEAD probe too, and answering "no commits yet" there would name the
    # wrong cause and send whoever reads it looking for the wrong fix.
    if not _git_ok("rev-parse", "--git-dir"):
        raise NotApplicable(
            f"{root} is not a git repository, so it has no history for this "
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


def practice_file(script_name, root):
    """The practice that names `script_name` as its check -- a person's own
    set says which of its practices this enforces, and the engine never
    names it (Morgan, 2026-10-16: "sets practice names should NOT be in
    BestPractice"). None where no practice in force here names it."""
    try:
        import precedent_identity
        return precedent_identity.practice_checked_by(script_name, root)[1]
    except Exception:                                        # noqa: BLE001
        return None


def rule_text(path) -> str:
    """The Rule text of the practice file at `path` (None: no practice)."""
    # A materialized check runs in whatever repo its source was resolved
    # into, and the practice file it quotes is not guaranteed to be there:
    # a repo that declares the source but never materializes it, or a
    # practice retired out of the tree, both leave PRACTICE_FILE absent.
    # Unguarded, this raised FileNotFoundError from inside the violation
    # PRINTER -- so the finding was correctly detected, correctly printed,
    # and then buried under a traceback. Found 2026-09-06 running every
    # source-supplied check against BestPractice; 14 of the 16 shared this
    # exact body. The Rule text being unavailable is not the check failing.
    if path is None or not path.is_file():
        return "(no practice in force here names this check as its checked_by)"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"## Rule\n(.*?)\n## ", text, re.S)
    return m.group(1).strip() if m else "(no Rule found)"

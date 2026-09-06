#!/usr/bin/env python3
"""build_codeowners.py -- generate CODEOWNERS from approvers.json.

PRACTICE_ENGINE_PLAN.md, "Who the Approvers Are, and How They Get That Job":
"Approvers are declared in the practice set's own config, not in a
host-specific file... GitHub's CODEOWNERS is then generated from that list,
the same way every other view in this system is generated, so there is one
source and the platform enforcement derives from it rather than competing
with it."

approvers.json is that config; CODEOWNERS is the generated GitHub-specific
view. Never hand-edit CODEOWNERS -- edit approvers.json and rerun this
script. The generated file carries a derived-file header naming its source,
its recipe and the command that rebuilds it, since it is exactly the case
that calls for one: a file a later regeneration overwrites wholesale.

WHY THIS IS PART OF THE VENDORED SOURCE-SET ENGINE. It was written inside
one team set and lived only there, which meant the plan's own approval
mechanism -- "approvers are declared in the set's own config, and
CODEOWNERS is generated from that list" -- had exactly one implementation,
in a private repo, reachable by nobody else. A second team set
(bootstrapped 2026-09-05 from templates/practice-set-team/) got its
approvers.json and no way to turn it into enforcement: approvers declared,
approvals unenforced, and nothing saying so. Promoted here 2026-09-06 so
every team set the bootstrap tool creates has it from the first commit
(practice: affordance-is-shared).

An individual set has no approvers.json and needs none -- one person is
the whole approval mechanism -- so this exits 0 with a note there rather
than failing.

Run: python3 tools/build_codeowners.py            # write
     python3 tools/build_codeowners.py --check    # verify, never write

TWO DEFECTS FIXED 2026-09-06, both found by a caller trying to VERIFY that
CODEOWNERS was current and instead dirtying the tree:

  1. `--check` was not a flag. main() ignored argv entirely, so the flag
     fell through and the tool WROTE. A caller asking "is this current?"
     got "it is now" -- the one answer that cannot be wrong, and the one
     that makes the question pointless. There is now a real --check that
     compares and exits non-zero without writing.

  2. The header stamped `git rev-parse HEAD`, so the generated file changed
     after EVERY commit whether or not approvers changed, and regenerating
     always produced a diff. A derived file must be a function of its
     SOURCE, not of when it was built -- otherwise "is it current?" has no
     stable answer and every check is a false positive. It now stamps a
     sha256 of approvers.json's own content, so an unchanged approver list
     regenerates byte-identically, forever. That also drops this tool's
     dependency on git entirely, which matters for a vendored tool that may
     run in a tarball or a shallow checkout.

This is exactly the "verify-postcondition" failure one level up: the check
reported success by causing the state it was asked to confirm.
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
APPROVERS_FILE = ROOT / "approvers.json"
CODEOWNERS_FILE = ROOT / "CODEOWNERS"


def _source_hash() -> str:
    """A sha256 of approvers.json's own bytes, not the repo's HEAD.

    The point of a derived-file stamp is to answer "was this built from the
    current source?" -- a question only the SOURCE can answer. Stamping the
    commit made every regeneration a diff, so the stamp reported "different"
    on every commit that touched anything at all, which is indistinguishable
    from never reporting anything."""
    return hashlib.sha256(APPROVERS_FILE.read_bytes()).hexdigest()[:12]


def load_approvers() -> list[dict]:
    data = json.loads(APPROVERS_FILE.read_text(encoding="utf-8"))
    approvers = data.get("approvers", [])
    if not approvers:
        raise SystemExit(f"{APPROVERS_FILE}: no approvers declared -- a team "
                          f"set needs at least one (PRACTICE_ENGINE_PLAN.md: "
                          f"'at creation, whoever creates a team set is its "
                          f"first approver; no ceremony, and there is always "
                          f"at least one').")
    for entry in approvers:
        if not entry.get("github"):
            raise SystemExit(f"{APPROVERS_FILE}: approver {entry!r} has no "
                              f"'github' field -- CODEOWNERS needs a GitHub "
                              f"username to address, not just a name.")
    return approvers


def render(approvers: list[dict], sha: str) -> str:
    owners = " ".join(f"@{a['github']}" for a in approvers)
    lines = [
        f"# DERIVED from approvers.json (sha256 {sha}) -- a hash of that",
        "# file's own content, NOT a commit: an unchanged approver list",
        "# regenerates byte-identically, so --check has a stable answer.",
        "# Recipe: tools/build_codeowners.py",
        "# Regenerate with: python3 tools/build_codeowners.py",
        "# edits here are safe to make but not durable -- regeneration replaces this file;",
        "# to make a change stick, edit the source or the recipe.",
        "#",
        "# Every approver reviews every change to this practice set -- there is",
        "# no per-path split; the whole repo is the thing being approved.",
        "",
        f"*  {owners}",
        "",
    ]
    return "\n".join(lines)


def main(check_only: bool = False):
    if not APPROVERS_FILE.is_file():
        # An individual set, or a repo that vendors this engine without
        # being a team set at all. Not an error: there is nothing to
        # generate, and saying so beats a traceback.
        print(f"no {APPROVERS_FILE.name} here, so there is no approver list "
              f"to generate CODEOWNERS from -- nothing to do. (A team set "
              f"declares its approvers there; an individual set has no "
              f"approval step to enforce.)")
        return 0
    approvers = load_approvers()
    wanted = render(approvers, _source_hash())

    if check_only:
        # Never writes -- not even to "helpfully" fix what it found. A
        # checker that repairs is a builder, and a caller cannot tell a
        # clean tree from a repaired one afterwards.
        if not CODEOWNERS_FILE.is_file():
            print(f"build_codeowners --check FAIL: {CODEOWNERS_FILE.name} does "
                  f"not exist, but {APPROVERS_FILE.name} declares "
                  f"{len(approvers)} approver(s). Run "
                  f"`python3 tools/build_codeowners.py` to generate it.")
            return 1
        current = CODEOWNERS_FILE.read_text(encoding="utf-8")
        if current == wanted:
            print(f"build_codeowners --check OK: {CODEOWNERS_FILE.name} is "
                  f"current with {APPROVERS_FILE.name} "
                  f"({len(approvers)} approver(s)).")
            return 0
        print(f"build_codeowners --check FAIL: {CODEOWNERS_FILE.name} does not "
              f"match what {APPROVERS_FILE.name} would generate -- either it "
              f"was hand-edited, or the approver list changed and it was not "
              f"regenerated. Run `python3 tools/build_codeowners.py`.")
        return 1

    CODEOWNERS_FILE.write_text(wanted, encoding="utf-8")
    print(f"wrote {CODEOWNERS_FILE.relative_to(ROOT)} from {len(approvers)} "
          f"approver(s): {', '.join('@' + a['github'] for a in approvers)}")
    return 0


if __name__ == "__main__":
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/HOW_TO_USE_THIS_TECHNICAL.md points readers straight at
    # these commands. The module docstring is the usage text.
    _argv = sys.argv[1:]
    if any(a in ('--help', '-h') for a in _argv):
        print((__doc__ or '').strip())
        sys.exit(0)
    # An unknown flag must not fall through and WRITE -- that fall-through
    # is defect 1 above, and silently doing the destructive thing on a
    # misspelled flag is how it stayed invisible.
    _unknown = [a for a in _argv if a != '--check']
    if _unknown:
        sys.exit(f"build_codeowners FAIL: unknown argument(s) "
                 f"{', '.join(repr(a) for a in _unknown)}. This tool takes "
                 f"--check (verify, never write) or no arguments (write).")
    sys.exit(main(check_only='--check' in _argv))

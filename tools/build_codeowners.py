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

Run: python3 tools/build_codeowners.py
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
APPROVERS_FILE = ROOT / "approvers.json"
CODEOWNERS_FILE = ROOT / "CODEOWNERS"


def _source_sha() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


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
        f"# DERIVED from approvers.json @ {sha}",
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


def main():
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
    sha = _source_sha()
    CODEOWNERS_FILE.write_text(render(approvers, sha), encoding="utf-8")
    print(f"wrote {CODEOWNERS_FILE.relative_to(ROOT)} from {len(approvers)} "
          f"approver(s): {', '.join('@' + a['github'] for a in approvers)}")


if __name__ == "__main__":
    sys.exit(main())

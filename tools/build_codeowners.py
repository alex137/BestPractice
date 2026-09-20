#!/usr/bin/env python3
"""build_codeowners.py -- generate CODEOWNERS from the registry that owns it.

PRACTICE_ENGINE_PLAN.md, "Who the Approvers Are, and How They Get That Job":
"Approvers are declared in the practice set's own config, not in a
host-specific file... GitHub's CODEOWNERS is then generated from that list,
the same way every other view in this system is generated, so there is one
source and the platform enforcement derives from it rather than competing
with it."

TWO KINDS OF REPOSITORY, ONE TOOL (practice: registry-source-of-truth):

  A PRACTICE SET has `approvers.json`. Every approver owns the whole tree --
  the thing being approved IS the practice text -- so the generated file is
  one line, `*  @approver...`, at the repository root.

  A PROJECT (a document project instantiated from templates/document-project/,
  or any repo drawing spec/CONTRIBUTOR_ACCESS.md's boundary) has no
  approvers.json. Its registry is two fields in `precedent.json`:
  `maintainers` (who reviews the machinery) and `owned_paths` (which paths
  are the machinery, each with a `why`). The generated file is
  `.github/CODEOWNERS`, one row per owned path, all maintainers on each.
  Everything not listed is content, and content is any contributor's.
  Added 2026-09-14: until then the project file was written by hand while
  the set file was generated, and the hand-written one is the one a
  maintainer forgets to update.

Never hand-edit CODEOWNERS -- edit the registry and rerun this script. The
generated file carries a derived-file header naming its source, its recipe
and the command that rebuilds it, since it is exactly the case that calls
for one: a file a later regeneration overwrites wholesale.

WHY THIS IS PART OF THE VENDORED SOURCE-SET ENGINE. It was written inside
one team set and lived only there, which meant the plan's own approval
mechanism -- "approvers are declared in the set's own config, and
CODEOWNERS is generated from that list" -- had exactly one implementation,
in a private repo, reachable by nobody else. A second team set
(bootstrapped 2026-09-05 from templates/practice-set-shared/) got its
approvers.json and no way to turn it into enforcement: approvers declared,
approvals unenforced, and nothing saying so. Promoted here 2026-09-06 so
every team set the bootstrap tool creates has it from the first commit
(practice: affordance-is-shared).

An individual set has no approvers.json and needs none -- one person is
the whole approval mechanism -- and a repository with neither registry has
nothing to generate; both exit 0 with a note rather than failing.

Run: python3 tools/build_codeowners.py                 # write
     python3 tools/build_codeowners.py --check         # verify, never write
     python3 tools/build_codeowners.py --repo PATH     # a repository other than this tool's own

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
     sha256 of the registry's own content, so an unchanged list
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


def _source_hash(source: pathlib.Path) -> str:
    """A sha256 of the registry file's own bytes, not the repo's HEAD.

    The point of a derived-file stamp is to answer "was this built from the
    current source?" -- a question only the SOURCE can answer. Stamping the
    commit made every regeneration a diff, so the stamp reported "different"
    on every commit that touched anything at all, which is indistinguishable
    from never reporting anything."""
    return hashlib.sha256(source.read_bytes()).hexdigest()[:12]


def load_approvers(approvers_file: pathlib.Path) -> list[dict]:
    data = json.loads(approvers_file.read_text(encoding="utf-8"))
    approvers = data.get("approvers", [])
    if not approvers:
        raise SystemExit(f"{approvers_file}: no approvers declared -- a team "
                          f"set needs at least one (PRACTICE_ENGINE_PLAN.md: "
                          f"'at creation, whoever creates a team set is its "
                          f"first approver; no ceremony, and there is always "
                          f"at least one').")
    for entry in approvers:
        if not entry.get("github"):
            raise SystemExit(f"{approvers_file}: approver {entry!r} has no "
                              f"'github' field -- CODEOWNERS needs a GitHub "
                              f"username to address, not just a name.")
    return approvers


def load_project(config_file: pathlib.Path):
    """-> (maintainers, owned_paths) from precedent.json, or None when the
    file declares no `owned_paths` (an ordinary consumer, not a project
    drawing the boundary)."""
    data = json.loads(config_file.read_text(encoding="utf-8"))
    owned = data.get("owned_paths")
    if owned is None:
        return None
    maintainers = data.get("maintainers") or []
    if not maintainers:
        raise SystemExit(f"{config_file}: `owned_paths` is declared but "
                          f"`maintainers` is empty -- an owned path with nobody "
                          f"to review it is a path nobody can change.")
    for m in maintainers:
        if not isinstance(m, dict) or not m.get("github"):
            raise SystemExit(f"{config_file}: maintainer {m!r} has no 'github' "
                              f"field -- CODEOWNERS needs a GitHub username to "
                              f"address, not just a name.")
    if not owned:
        raise SystemExit(f"{config_file}: `owned_paths` is empty -- declare the "
                          f"paths a contributor must not change alone, or remove "
                          f"the key to say this repository draws no boundary.")
    for o in owned:
        if not isinstance(o, dict) or not o.get("path") or not o.get("why"):
            # An owned path with no reason is the silence this registry
            # replaces: nobody can judge later whether it still belongs.
            raise SystemExit(f"{config_file}: owned path {o!r} needs both a "
                              f"'path' and a 'why'.")
    return maintainers, owned


def render(approvers: list[dict], sha: str) -> str:
    """A practice set's file. Byte-for-byte what it rendered before project
    mode existed: every set's committed CODEOWNERS must still --check OK."""
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


def render_project(maintainers: list[dict], owned: list[dict], sha: str) -> str:
    owners = " ".join(f"@{m['github']}" for m in maintainers)
    width = max(len(o["path"]) for o in owned)
    lines = [
        f"# DERIVED from precedent.json (sha256 {sha}) -- a hash of that",
        "# file's own content, NOT a commit: an unchanged registry",
        "# regenerates byte-identically, so --check has a stable answer.",
        "# Recipe: tools/build_codeowners.py",
        "# Regenerate with: python3 tools/build_codeowners.py",
        "# edits here are safe to make but not durable -- regeneration replaces this file;",
        "# to make a change stick, edit the source or the recipe.",
        "#",
        "# The path boundary for this project (spec/CONTRIBUTOR_ACCESS.md, layer 2).",
        "# Everything listed here waits for a maintainer's review; everything NOT",
        "# listed is content, and content is any contributor's to write and merge.",
        "# The paths are `owned_paths` in precedent.json and the owners are its",
        "# `maintainers`. This file is a boundary only with branch protection on",
        "# the base branch -- python3 tools/precedent_boundary_check.py says",
        "# whether that is on.",
        "",
    ]
    for o in owned:
        lines.append(f"# {o['why']}")
        lines.append(f"{o['path'].ljust(width)}  {owners}")
        lines.append("")
    return "\n".join(lines)


def main(check_only: bool = False, root: pathlib.Path = ROOT):
    approvers_file = root / "approvers.json"
    config_file = root / "precedent.json"
    if approvers_file.is_file():
        source, kind = approvers_file, "approver"
        approvers = load_approvers(approvers_file)
        wanted = render(approvers, _source_hash(approvers_file))
        target = root / "CODEOWNERS"
        count = len(approvers)
        names = ", ".join("@" + a["github"] for a in approvers)
    else:
        project = load_project(config_file) if config_file.is_file() else None
        if project is None:
            # An individual set, an ordinary consumer, or a repo that vendors
            # this engine without drawing any boundary. Not an error: there
            # is nothing to generate, and saying so beats a traceback.
            print(f"no approvers.json and no `owned_paths` in precedent.json "
                  f"under {root}, so there is no registry to generate "
                  f"CODEOWNERS from -- nothing to do. (A team set declares "
                  f"its approvers in approvers.json; a project drawing the "
                  f"contributor boundary declares `maintainers` and "
                  f"`owned_paths` in precedent.json; an individual set has "
                  f"no approval step to enforce.)")
            return 0
        maintainers, owned = project
        source, kind = config_file, "owned path"
        wanted = render_project(maintainers, owned, _source_hash(config_file))
        target = root / ".github" / "CODEOWNERS"
        count = len(owned)
        names = ", ".join("@" + m["github"] for m in maintainers)

    if check_only:
        # Never writes -- not even to "helpfully" fix what it found. A
        # checker that repairs is a builder, and a caller cannot tell a
        # clean tree from a repaired one afterwards.
        if not target.is_file():
            print(f"build_codeowners --check FAIL: {target.relative_to(root)} "
                  f"does not exist, but {source.name} declares {count} "
                  f"{kind}(s). Run `python3 tools/build_codeowners.py` to "
                  f"generate it.")
            return 1
        current = target.read_text(encoding="utf-8")
        if current == wanted:
            print(f"build_codeowners --check OK: {target.relative_to(root)} is "
                  f"current with {source.name} ({count} {kind}(s)).")
            return 0
        print(f"build_codeowners --check FAIL: {target.relative_to(root)} does "
              f"not match what {source.name} would generate -- either it was "
              f"hand-edited, or the registry changed and it was not "
              f"regenerated. Run `python3 tools/build_codeowners.py`.")
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(wanted, encoding="utf-8")
    print(f"wrote {target.relative_to(root)} from {count} {kind}(s): {names}")
    return 0


if __name__ == "__main__":
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/FOR_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    _argv = sys.argv[1:]
    if any(a in ('--help', '-h') for a in _argv):
        print((__doc__ or '').strip())
        sys.exit(0)
    _root = ROOT
    if '--repo' in _argv:
        _i = _argv.index('--repo')
        if _i + 1 >= len(_argv):
            sys.exit("build_codeowners FAIL: --repo needs a path.")
        _root = pathlib.Path(_argv[_i + 1]).resolve()
        del _argv[_i:_i + 2]
    # An unknown flag must not fall through and WRITE -- that fall-through
    # is defect 1 above, and silently doing the destructive thing on a
    # misspelled flag is how it stayed invisible.
    _unknown = [a for a in _argv if a != '--check']
    if _unknown:
        sys.exit(f"build_codeowners FAIL: unknown argument(s) "
                 f"{', '.join(repr(a) for a in _unknown)}. This tool takes "
                 f"--check (verify, never write), --repo PATH, or no "
                 f"arguments (write).")
    sys.exit(main(check_only='--check' in _argv, root=_root))

#!/usr/bin/env python3
"""Say, at session start, whether the upstream branch has moved since the last carry.

`precedent-beta-v01` is a long-lived restructuring branch of a repository
whose `main` its owner still works on. Work does not flow between them by
merge -- it is CARRIED, converted into this branch's practice-file format on
the way -- so a session cannot ask git "is main an ancestor" and get a useful
answer. It has to ask a different question: has `main` moved since the last
time somebody carried it? That is what tools/upstream_watermark.json records
and what this script compares against.

Morgan, 2026-09-08, asked for this shape specifically, and the requirement is
what makes it a notice rather than a job: *"I don't want it to merge
invisibly, I'd like to do it in a session when I'm there."* So this script
NEVER merges, cherry-picks, or writes to any branch. It prints, and a person
decides.

  python3 tools/precedent_upstream_check.py            # the notice
  python3 tools/precedent_upstream_check.py --no-fetch  # local refs only
  python3 tools/precedent_upstream_check.py --record --by "PR #150"

Exit status is 0 in every case, including a failed fetch (practice:
fail-gracefully clause 2 -- a session start that a network hiccup can block
is worse than the staleness it was guarding against). What clause 1 requires
instead is that the three outcomes never render alike, so each prints its own
first word: MOVED, current, or UNKNOWN.
"""

import argparse
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

# practice: one-formatter-per-quantity -- every moment in time this project
# writes down comes from ONE module, in the person's zone, carrying its
# offset. Never a bare datetime.date.today(): that is the container's UTC.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # noqa: E402


REPO = pathlib.Path(__file__).resolve().parent.parent

# The registry path is overridable so a test can hand this script a watermark
# it owns rather than editing the repository's real one (practice:
# fixture-owns-its-state -- a fixture that mutates real state is testing the
# environment too, and leaves it changed when it fails).
REGISTRY = pathlib.Path(
    os.environ.get("PRECEDENT_UPSTREAM_WATERMARK", REPO / "tools" / "upstream_watermark.json")
)

# practice: registry-source-of-truth -- the watermark is the one machine-readable
# home for "what has been carried". Nothing here reads it out of a document.


def git(*args, check=False):
    """Run git and return (returncode, stdout).

    Callers MUST look at the return code. `git rev-parse <missing-ref>` exits
    non-zero and still PRINTS the ref you handed it, so a helper that returns
    stdout alone hands back the string "origin/main" where a hash belongs --
    the single most repeated bug in this project, and the reason this returns
    a pair instead of a string.
    """
    proc = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.returncode, proc.stdout.strip()


def resolve(ref):
    """The commit a ref points at, or None. Never the ref's own name."""
    code, out = git("rev-parse", "--verify", "--quiet", ref)
    return out if code == 0 and out else None


def have_commit(sha):
    """Is this commit actually IN this clone?

    Not the same question as `resolve()`, and the difference bit while this
    script was being written. `git rev-parse --verify --quiet` exits 0 and
    echoes back ANY well-formed 40-hex string, present or not: it verifies
    that the argument names a single revision, not that the object exists.
    A watermark pointing at a commit no longer in a shallow clone therefore
    read as "present", and the notice claimed a change it could not list.
    `cat-file -e` asks the object database.
    """
    code, _ = git("cat-file", "-e", f"{sha}^{{commit}}")
    return code == 0


def load_registry():
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        print(f"upstream check UNKNOWN: {REGISTRY.name} is not valid JSON ({exc}) "
              f"-- cannot tell whether upstream moved", file=sys.stderr)
        return None


def pr_number(subject):
    """The pull request a commit subject names, if it names one."""
    match = re.search(r"#(\d+)", subject)
    return match.group(1) if match else None


def describe(sha_from, sha_to):
    """One line per commit between the watermark and upstream's head."""
    code, out = git("log", "--oneline", "--no-decorate", f"{sha_from}..{sha_to}")
    if code != 0:
        return None
    return [line for line in out.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-fetch", action="store_true",
                        help="compare against local refs only; do not talk to the remote")
    parser.add_argument("--record", action="store_true",
                        help="move the watermark to upstream's current head")
    parser.add_argument("--by", default="",
                        help="with --record: what carried it (a PR number, a commit subject)")
    args = parser.parse_args()

    registry = load_registry()
    if registry is None:
        print(f"upstream check UNKNOWN: no readable {REGISTRY.name}; "
              f"nothing to compare upstream against")
        return 0

    upstream = registry.get("upstream_branch", "main")
    carried = (registry.get("last_carried") or {}).get("sha")

    if not args.no_fetch:
        # Bounded, never --unshallow: some git policy hooks refuse that, and a
        # depth-limited fetch works on a shallow clone either way.
        code, _ = git("fetch", "--depth=50", "origin", upstream)
        if code != 0:
            print(f"upstream check UNKNOWN: could not fetch origin/{upstream} "
                  f"(offline, or no access) -- this says nothing about whether "
                  f"{upstream} moved")
            return 0

    head = resolve(f"origin/{upstream}")
    if head is None:
        print(f"upstream check UNKNOWN: origin/{upstream} does not resolve in "
              f"this clone -- cannot tell whether it moved")
        return 0

    if args.record:
        return record(registry, head, args.by)

    if not carried:
        print(f"upstream check UNKNOWN: {REGISTRY.name} records no carried "
              f"commit, so origin/{upstream} at {head[:9]} cannot be compared")
        return 0

    if head == carried:
        print(f"upstream check: origin/{upstream} is unchanged since the last "
              f"carry ({head[:9]}, {registry['last_carried'].get('recorded', 'undated')}).")
        return 0

    if not have_commit(carried):
        print(f"upstream check UNKNOWN: origin/{upstream} is now {head[:9]}, but "
              f"the carried commit {carried[:9]} is not in this clone (shallow "
              f"fetch) -- fetch deeper to see what changed")
        return 0

    commits = describe(carried, head)
    print()
    print(f"UPSTREAM MOVED: origin/{upstream} is at {head[:9]}, "
          f"{len(commits) if commits else 'some'} commit(s) past the last carry "
          f"({carried[:9]}, {registry['last_carried'].get('recorded', 'undated')}).")
    for line in commits or []:
        number = pr_number(line)
        print(f"  {line}" + (f"   [PR #{number}]" if number else ""))
    print()
    print("  Nothing has been merged or carried -- that is a person's call, in a "
          "session, on purpose.")
    print(f"  To see it:     git log -p {carried[:9]}..origin/{upstream}")
    print("  After carrying: python3 tools/precedent_upstream_check.py --record "
          "--by \"PR #NNN\"")
    print()
    return 0


def record(registry, head, by):
    previous = (registry.get("last_carried") or {}).get("sha", "")
    if previous == head:
        print(f"upstream check: watermark already at {head[:9]}; nothing recorded.")
        return 0
    code, subject = git("log", "-1", "--format=%s", head)
    registry["last_carried"] = {
        "sha": head,
        # The contributor's calendar date, which is what every other dated
        # record in this repo uses (practice: volatile-rules-carry-dates).
        "recorded": precedent_time.today(),
        "carried_by": by or "unrecorded -- pass --by next time",
        "note": subject if code == 0 else "",
    }
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"upstream check: watermark moved {previous[:9] or '(none)'} -> {head[:9]}. "
          f"Commit {REGISTRY.name} with the carry it records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

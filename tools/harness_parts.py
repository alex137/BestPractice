#!/usr/bin/env python3
"""Where the harness's tests live -- the one answer every reader of them uses

harness_parts.py -- since 2026-10-31 the verification harness is
tools/verify_harness.py (the runner and the shared fixtures) plus one file
per area under tools/harness/, which verify_harness.py executes into its own
namespace at load time. A tool that reads the harness's source -- to list its
checks, find a check's body, or judge a change to it -- reads every one of
these files, through this module, never tools/verify_harness.py alone: a
reader left on the one file would quietly see a tenth of the suite and pass.

    python3 tools/harness_parts.py            # the files, one per line
"""
import pathlib
import re
import sys

HARNESS = 'tools/verify_harness.py'
PARTS_DIR = 'tools/harness'
PART_PREFIX = 'vh_'
_CHECK_DEF = re.compile(r'^def (check_\w+)\(', re.M)


def is_harness(rel):
    """True when the repository-relative path `rel` is part of the harness:
    the runner itself or an area file, tools/harness/vh_<area>.py."""
    rel = str(rel).replace('\\', '/')
    if rel == HARNESS:
        return True
    head, _, name = rel.rpartition('/')
    return head == PARTS_DIR and is_part_name(name)


def is_part_name(name):
    """True for an area file's basename: vh_<area>.py. The prefix keeps a
    part's name off every tool's (tools/harness/vh_checkin.py, never a
    second checkin.py), so a rule keyed on a basename cannot mistake one."""
    return name.startswith(PART_PREFIX) and name.endswith('.py')


def is_harness_name(name):
    """True for a harness file's basename: verify_harness.py or a part's.
    For the rules that exempt the harness by name while walking tools/."""
    return name == 'verify_harness.py' or is_part_name(name)


def part_paths(root):
    """-> the area files under tools/harness/ of the tree at `root`, sorted
    (the order verify_harness.py executes them in)."""
    d = pathlib.Path(root) / PARTS_DIR
    return sorted(p for p in d.glob(PART_PREFIX + '*.py') if p.is_file()) \
        if d.is_dir() else []


def paths(root):
    """-> every harness file of the tree at `root`, runner first; [] when
    the tree has no harness at all."""
    runner = pathlib.Path(root) / HARNESS
    return ([runner] if runner.is_file() else []) + part_paths(root)


def relpaths(root):
    """-> paths(root), repository-relative, as strings."""
    root = pathlib.Path(root)
    return [p.relative_to(root).as_posix() for p in paths(root)]


def read_all(root):
    """-> the source of every harness file of the tree at `root`, runner
    first, joined by blank lines: '' when there is none."""
    return '\n\n'.join(p.read_text(encoding='utf-8', errors='replace')
                       for p in paths(root))


def check_names(text):
    """-> the set of top-level `def check_*` names in harness source text."""
    return set(_CHECK_DEF.findall(text or ''))


def changed(files):
    """-> the harness files among the repository-relative `files`."""
    return [f for f in files if is_harness(f)]


if __name__ == '__main__':
    if sys.argv[1:2] in (['-h'], ['--help']):
        print(__doc__)
        sys.exit(0)
    root = pathlib.Path(__file__).resolve().parents[1]
    for rel in relpaths(root):
        print(rel)
    sys.exit(0)

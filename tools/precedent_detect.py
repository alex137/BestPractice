#!/usr/bin/env python3
"""precedent_detect.py — Stage 1 of PRACTICE_ENGINE_PLAN.md's creation
pipeline: the mechanical half of detection. Every subcommand REPORTS a
detection; none of them raises a candidate automatically — "detection
produces a candidate, never a practice" (Stage 2) means a human decides
whether to act on what this prints, the same way `precedent_check.py`
reports a violation without writing the fix itself.

What is and is not built here, stated plainly (this repo's own convention
for a check that resists full coverage — see spec/ATTENTION_CEILING.md's
enforcement section):

  explicit-instruction   BUILT. A phrase detector over supplied text (a
                          message, a commit body) — "from now on," "always,"
                          "never," "going forward." No script can read a
                          live conversation; a session pipes the relevant
                          text through this itself.
  reverted-or-corrected  BUILT. A git-log scan for revert-shaped commits.
  restated-in-second-scope  BUILT. Cross-source duplicate-Rule-text scan —
                          reuses precedent_promote.py's own word-overlap
                          logic, which is the actual promotion signal this
                          detects (Stage 1: "a practice has been restated in
                          a second scope, which is the promotion signal").
  repeated-instruction   NOT a separate detector. Raising a second candidate
                          file for the same slug already IS how this signal
                          is captured — precedent_promote.py's recurrence
                          criterion counts files, by design
                          (spec/CANDIDATE_FORMAT.md).
  repeated-check-failure NOT BUILT. Needs a persistent log of check runs
                          over time; none exists in this codebase (no tool
                          here records pass/fail history across runs, only
                          the current run's result). Left as a real gap
                          rather than faked with a single-run proxy.
  review-found-defect    NOT a separate detector. Already the
                          `mistakes-become-rules` practice's own trigger,
                          reached via the existing `review` gate
                          (precedent_gate.py review) — a review that finds a
                          defect raises a candidate via precedent_candidate.py
                          directly; there is no separate mechanical signature
                          to detect beyond what that gate already surfaces.

Usage:
  precedent_detect.py explicit-instruction --text TEXT
  precedent_detect.py reverted --repo PATH [--since REF]
  precedent_detect.py restated --against PATH[,PATH...]
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp  # noqa: E402
import precedent_promote as pp  # noqa: E402

# Deliberately specific phrasing, not bare "always"/"never" -- those words
# are ordinary English and would fire on most prose. Each pattern requires
# the standing-rule SHAPE ("from now on X", "always Y", not just the word).
INSTRUCTION_PATTERNS = [
    re.compile(r'\bfrom now on\b', re.I),
    re.compile(r'\bgoing forward\b', re.I),
    re.compile(r'\balways\s+\w+', re.I),
    re.compile(r'\bnever\s+\w+', re.I),
    re.compile(r'\bevery time\b', re.I),
    re.compile(r'\bfrom here on\b', re.I),
]
_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')


def cmd_explicit_instruction(args):
    text = args.get('--text')
    if text is None:
        sys.exit("precedent_detect FAIL: --text TEXT is required")
    hits = []
    for sent in _SENT_SPLIT.split(text):
        for pat in INSTRUCTION_PATTERNS:
            if pat.search(sent):
                hits.append((pat.pattern, sent.strip()))
                break
    if not hits:
        print("no explicit-instruction phrasing detected")
        return 0
    print(f"{len(hits)} possible explicit-instruction signal(s) — "
          f"Stage 1's highest-signal trigger. Consider "
          f"`precedent_candidate.py create --signal explicit-instruction`:")
    for pattern, sent in hits:
        print(f"  [{pattern}] {sent}")
    return 0


def cmd_reverted(args):
    repo = args.get('--repo')
    since = args.get('--since')
    if not repo:
        sys.exit("precedent_detect FAIL: --repo PATH is required")
    cmd = ['git', '-C', repo, 'log', '--format=%H%x00%s%x00%b%x01']
    if since:
        cmd.append(f'{since}..HEAD')
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    hits = []
    for entry in out.split('\x01'):
        entry = entry.strip('\n')
        if not entry:
            continue
        sha, _, rest = entry.partition('\x00')
        subject, _, body = rest.partition('\x00')
        if re.match(r'^revert\b', subject, re.I) or 'this reverts commit' in body.lower():
            hits.append((sha[:12], subject.strip()))
    if not hits:
        print(f"no revert-shaped commits found in {repo}"
              f"{' since ' + since if since else ''}")
        return 0
    print(f"{len(hits)} revert-shaped commit(s) — Stage 1's "
          f"'user reverted, rewrote, or corrected work a session produced' "
          f"signal. Worth asking why the reverted work was wrong, and "
          f"whether that's a candidate:")
    for sha, subject in hits:
        print(f"  {sha} {subject}")
    return 0


def cmd_restated(args):
    against = args.get('--against')
    if not against:
        sys.exit("precedent_detect FAIL: --against PATH[,PATH...] is required")
    paths = against.split(',')
    by_source = {}
    for p in paths:
        d = pathlib.Path(p) / 'practices'
        if not d.is_dir():
            continue
        entries = {}
        for f in sorted(d.glob('*.md')):
            try:
                fm, sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            if fm.get('status') == 'retired':
                continue
            entries[fm.get('slug', f.stem)] = sections.get('rule', '')
        by_source[p] = entries

    hits = []
    sources = list(by_source.items())
    for i, (src_a, entries_a) in enumerate(sources):
        for src_b, entries_b in sources[i + 1:]:
            for slug_a, rule_a in entries_a.items():
                words_a = pp._word_set(rule_a)
                if not words_a:
                    continue
                for slug_b, rule_b in entries_b.items():
                    if slug_a == slug_b:
                        continue  # same slug across sources is an intended override, not a restatement
                    words_b = pp._word_set(rule_b)
                    if not words_b:
                        continue
                    overlap = len(words_a & words_b) / len(words_a | words_b)
                    if overlap > 0.5:
                        hits.append((src_a, slug_a, src_b, slug_b, overlap))
    if not hits:
        print(f"no restated-in-a-second-scope pairs found across {len(paths)} source(s)")
        return 0
    print(f"{len(hits)} pair(s) with substantial Rule-text overlap across "
          f"different sources — Stage 1's 'restated in a second scope' "
          f"promotion signal. This means an existing NARROWER practice may "
          f"belong at a wider level, not that a new candidate should be raised:")
    for src_a, slug_a, src_b, slug_b, overlap in sorted(hits, key=lambda h: -h[4]):
        print(f"  {overlap:.0%} overlap: {slug_a!r} ({src_a}) <-> {slug_b!r} ({src_b})")
    return 0


COMMANDS = {
    'explicit-instruction': cmd_explicit_instruction,
    'reverted': cmd_reverted,
    'restated': cmd_restated,
}


def _parse_args(argv):
    if not argv or argv[0] not in COMMANDS:
        sys.exit(f"precedent_detect FAIL: first argument must be one of "
                  f"{sorted(COMMANDS)}, got {argv[0] if argv else None!r}")
    cmd, rest = argv[0], argv[1:]
    args = {}
    i = 0
    while i < len(rest):
        tok = rest[i]
        if not tok.startswith('--') or i + 1 >= len(rest):
            sys.exit(f"precedent_detect FAIL: expected --flag value pairs, stuck at {tok!r}")
        args[tok] = rest[i + 1]
        i += 2
    return cmd, args


def main():
    cmd, args = _parse_args(sys.argv[1:])
    return COMMANDS[cmd](args)


if __name__ == '__main__':
    sys.exit(main())

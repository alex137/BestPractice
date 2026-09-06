#!/usr/bin/env python3
"""check_merge_target_is_beta_branch.py -- the mechanical check for
local/practices/merge-target-is-beta-branch.md.

# practice: merge-target-is-beta-branch

Scope: tree. While this repository is mid-restructure, every pull request
targets `precedent-beta-v01`, never `main`. That is checkable after the
fact as a graph property: `origin/precedent-beta-v01` must NOT be an
ancestor of `origin/main`. If it is, the restructuring work has landed on
`main` -- expected exactly once, when Alex reviews and merges it for real
(and retires this practice in the same pull request), and otherwise the
PR #89 mistake happening again.

WHY THIS LIVES UNDER local/, NOT IN tools/precedent_check.py. It used to
be one of that module's registered checks, and `precedent_check.py` is
vendored verbatim into every consuming repo (INSTALL.md section 0, step
1). So every brand-new install ran a check about THIS repository's own
temporary beta branch: SKIPPED at best, and -- because the module also
carried a `# practice: merge-target-is-beta-branch` citation for it --
a permanent `code-cites-practice` VIOLATION naming a slug no consumer's
catalogue has, which no consumer could act on, satisfy, or read the Rule
of. A repo-local practice's check belongs to the repo-local source, which
is what this directory is.

Contract, shared with every other per-source check script (the nine in
precedent-team-maintainers, the five in precedent-individual): no
arguments; ROOT derived from this file's own location; exit 0 and print
nothing when clean; exit 1 and print the finding plus the Rule when
violated; exit 2 when the check cannot run at all -- reported as SKIPPED,
never as a pass.
"""
import pathlib
import subprocess
import sys

# local/tools/checks/<this file> -> the repo root, four levels up.
ROOT = pathlib.Path(__file__).resolve().parents[3]
PRACTICE_FILE = ROOT / 'local' / 'practices' / 'merge-target-is-beta-branch.md'


class NotApplicable(Exception):
    """The check could not run. Exit 2, never a silent pass."""


def rule_text():
    """The practice's own ## Rule, read from the file rather than
    paraphrased here -- a failure message that drifts from the rule it
    quotes is worse than no message."""
    if not PRACTICE_FILE.is_file():
        return f'(no practice file at {PRACTICE_FILE.relative_to(ROOT)})'
    lines = PRACTICE_FILE.read_text(encoding='utf-8').splitlines()
    out, inrule = [], False
    for line in lines:
        if line.startswith('## Rule'):
            inrule = True
            continue
        if inrule and line.startswith('## '):
            break
        if inrule:
            out.append(line)
    return '\n'.join(out).strip() or '(no Rule recorded)'


def _rev_parse(ref):
    # --verify --quiet: a plain `git rev-parse <missing-ref>` exits non-zero
    # but ECHOES THE REF NAME on stdout, which is how a ref name once got
    # carried forward as a commit hash here (AGENTS.md's gotchas section).
    r = subprocess.run(['git', 'rev-parse', '--verify', '--quiet', ref],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def find_violations():
    main = _rev_parse('origin/main')
    beta = _rev_parse('origin/precedent-beta-v01')
    if not main or not beta:
        raise NotApplicable(
            'origin/main and origin/precedent-beta-v01 must both be fetched '
            'locally to compare them -- run `git fetch origin main '
            'precedent-beta-v01` first')
    is_ancestor = subprocess.run(
        ['git', 'merge-base', '--is-ancestor', beta, main],
        cwd=ROOT).returncode == 0
    if is_ancestor:
        return [f'main: contains origin/precedent-beta-v01 ({beta[:8]}) as an '
                f'ancestor -- the restructuring work has been merged into '
                f'main. Expected ONLY once Alex has reviewed and merged '
                f'precedent-beta-v01 into main for real (in which case retire '
                f'this practice in the same PR); otherwise this is the PR #89 '
                f'mistake happening again.']
    return []


if __name__ == '__main__':
    try:
        findings = find_violations()
    except NotApplicable as e:
        print(f'SKIPPED: {PRACTICE_FILE.stem}: {e}')
        sys.exit(2)
    if findings:
        print(f'VIOLATION: {PRACTICE_FILE.stem}')
        for f in findings:
            print(f'  {f}')
        print('\nthe rule:')
        print('  ' + rule_text().replace('\n', '\n  '))
        sys.exit(1)
    sys.exit(0)

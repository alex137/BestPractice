#!/usr/bin/env python3
"""check_philosophy_is_not_repo_policy.py -- the mechanical check for
local/practices/philosophy-is-not-repo-policy.md.

# practice: philosophy-is-not-repo-policy

Scope: tree. The philosophy/ tree is argument, not policy. Two properties,
both checkable with no false positives:

  1. No practice's ## Rule cites a philosophy/ path, and no practice's
     checked_by points at a script under philosophy/. A rule may EXPLAIN
     itself with an essay (## Why, ## Story, ## Detail, ## Install are all
     fair game and deliberately not scanned) -- it may not be one.
  2. No practice in the exported catalogue (practices/) names philosophy
     in its applies_to. A rule about this repo's own philosophy directory
     is repo-local by construction and belongs in local/practices/.

WHY ONLY THESE TWO. The obvious check -- scan philosophy/ for imperative
prose -- was written first and thrown away. These essays argue for a way
of working, so they are full of correct imperatives ("Argue a genuine
counter-case before building on a stated stance"). A check that fires on
legitimate work teaches the next session to ignore the gate, which
checkable-gets-checked names as worse than no check at all. What IS
crisply checkable is the direction of authority: what a rule is allowed
to lean on.

WHY THIS LIVES UNDER local/, NOT IN tools/precedent_check.py. Same reason
as check_merge_target_is_beta_branch.py beside it: precedent_check.py is
vendored verbatim into every consuming repo, and a check about THIS
repository's philosophy/ directory would be a permanent unfixable finding
in repos that have no such directory. A repo-local practice's check
belongs to the repo-local source.

Contract, shared with every other per-source check script: no arguments;
ROOT derived from this file's own location; exit 0 and print nothing when
clean; exit 1 and print the finding plus the Rule when violated; exit 2
when the check cannot run at all -- reported as SKIPPED, never as a pass.
"""
import os
import pathlib
import re
import sys

# local/tools/checks/<this file> -> the repo root, four levels up.
# SOURCE_ROOT is the practice set this script ships in (here, `local/`'s
# parent: this repo, since a repo-local source lives inside the repo it
# serves); ROOT is what gets audited. PRECEDENT_CHECK_ROOT overrides the
# latter only.
SOURCE_ROOT = pathlib.Path(__file__).resolve().parents[3]
ROOT = pathlib.Path(os.environ.get('PRECEDENT_CHECK_ROOT') or SOURCE_ROOT)
PRACTICE_FILE = (SOURCE_ROOT / 'local' / 'practices'
                 / 'philosophy-is-not-repo-policy.md')

PHILOSOPHY_DIR = 'philosophy'


class NotApplicable(Exception):
    """The check could not run. Exit 2, never a silent pass."""


def rule_text():
    """The practice's own ## Rule, read from the file rather than
    paraphrased here -- a failure message that drifts from the rule it
    quotes is worse than no message."""
    if not PRACTICE_FILE.is_file():
        return f'(no practice file at {PRACTICE_FILE})'
    out, inrule = [], False
    for line in PRACTICE_FILE.read_text(encoding='utf-8').splitlines():
        if line.startswith('## Rule'):
            inrule = True
            continue
        if inrule and line.startswith('## '):
            break
        if inrule:
            out.append(line)
    return '\n'.join(out).strip() or '(no Rule recorded)'


def _frontmatter(text):
    """The practice file's YAML-ish frontmatter as a raw {key: value} map of
    strings. Deliberately not a YAML parse: these files are written to one
    fixed shape, and adding a dependency to read two fields would be the
    only reason this script needed one."""
    if not text.startswith('---'):
        return {}
    end = text.find('\n---', 3)
    if end == -1:
        return {}
    fields = {}
    for line in text[3:end].splitlines():
        m = re.match(r'^([a-z_]+):\s*(.*)$', line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def _rule_section(text):
    out, inrule = [], False
    for line in text.splitlines():
        if line.startswith('## Rule'):
            inrule = True
            continue
        if inrule and line.startswith('## '):
            break
        if inrule:
            out.append(line)
    return '\n'.join(out)


def _practice_files():
    """Every practice file whose applies_to or Rule this check governs:
    the exported catalogue and this repo's own repo-local set."""
    for d in ('practices', os.path.join('local', 'practices')):
        directory = ROOT / d
        if directory.is_dir():
            for f in sorted(directory.glob('*.md')):
                yield f


def find_violations():
    if not (ROOT / PHILOSOPHY_DIR).is_dir():
        raise NotApplicable(
            f'{PHILOSOPHY_DIR}/ does not exist in this repository, so no '
            f'rule can lean on it')
    files = list(_practice_files())
    if not files:
        raise NotApplicable(
            'no practice files found under practices/ or local/practices/')

    findings = []
    # A philosophy/ path, however it is written: bare, as a relative link
    # from the repo root, or as ../philosophy/ from inside practices/.
    cite = re.compile(r'(?:\.\./)*' + PHILOSOPHY_DIR + r'/[\w./#-]+')

    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        text = f.read_text(encoding='utf-8')
        fm = _frontmatter(text)

        # Clause 1a -- the ## Rule may not cite an essay as its authority.
        for hit in sorted(set(cite.findall(_rule_section(text)))):
            findings.append(
                f'{rel}: its ## Rule cites `{hit}`. An essay may explain a '
                f'rule (## Why, ## Story, ## Detail and ## Install are not '
                f'scanned) but may not BE one -- write the rule out as a '
                f'practice in the source it belongs to instead.')

        # Clause 1b -- nor may a check script live in the essays.
        checked_by = fm.get('checked_by', '').strip('"\' ')
        if checked_by and PHILOSOPHY_DIR + '/' in checked_by:
            findings.append(
                f'{rel}: checked_by points at `{checked_by}`, inside '
                f'{PHILOSOPHY_DIR}/. Enforcement code is not philosophy; '
                f'move the script under the practice set that owns it.')

        # Clause 2 -- the exported catalogue never carries a philosophy-
        # scoped rule, because a consumer has no philosophy/ to apply it to.
        if rel.startswith('practices/') and PHILOSOPHY_DIR in fm.get(
                'applies_to', ''):
            findings.append(
                f'{rel}: applies_to names {PHILOSOPHY_DIR}, but practices/ is '
                f'the catalogue this repo EXPORTS. A rule about this repo\'s '
                f'own {PHILOSOPHY_DIR}/ is repo-local -- move it to '
                f'local/practices/, as check_merge_target_is_beta_branch.py '
                f'had to be moved for the same reason.')
    return findings


if __name__ == '__main__':
    try:
        results = find_violations()
    except NotApplicable as e:
        print(f'SKIPPED: {PRACTICE_FILE.stem}: {e}')
        sys.exit(2)
    if results:
        print(f'VIOLATION: {PRACTICE_FILE.stem}')
        for r in results:
            print(f'  {r}')
        print('\nthe rule:')
        print('  ' + rule_text().replace('\n', '\n  '))
        sys.exit(1)
    sys.exit(0)

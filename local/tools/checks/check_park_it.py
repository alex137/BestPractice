#!/usr/bin/env python3
"""check_park_it.py -- the mechanical check for local/practices/park-it.md.

# practice: park-it

Scope: tree. The instructions file a session actually reads before it works
(AGENTS.md, or CLAUDE.md where that is the entry point) has to define the
phrase "Park it" and say what it writes.

Why this is the property worth checking, when the practice itself is about
a conversational trigger: the failure it prevents already happened here to
the other standing phrase. "Go merge" lived in Morgan's private individual
set, a session that had not attached that set met the phrase cold, and --
following AGENTS.md's own instruction at the time -- went and asked him
what it meant. Being asked the same question across sessions is the exact
thing a standing phrase exists to stop, so the phrase generated the
annoyance it was invented to remove. A phrase is only worth having if it
is written where a session reads before it works; this check is that
sentence, made mechanical.

What it cannot see: whether a session that HEARD "Park it" actually wrote
the disposition line. Nothing in the tree records the utterance, so that
half stays advisory by nature. The grammar of the line it should have
written is enforced separately, by tools/precedent_check.py's
open-item-disposition check.

Contract, shared with every other per-source check script: no arguments;
ROOT derived from this file's own location; exit 0 and print nothing when
clean; exit 1 and print the finding plus the Rule when violated; exit 2
when the check cannot run at all -- reported as SKIPPED, never as a pass.
"""
import os
import pathlib
import sys

SOURCE_ROOT = pathlib.Path(__file__).resolve().parents[3]
ROOT = pathlib.Path(os.environ.get('PRECEDENT_CHECK_ROOT') or SOURCE_ROOT)
PRACTICE_FILE = SOURCE_ROOT / 'local' / 'practices' / 'park-it.md'

# In this repo CLAUDE.md is a one-line include of AGENTS.md, so AGENTS.md is
# where the prose has to be. Both spellings are accepted because a consuming
# repo may run the other way round.
INSTRUCTIONS_FILES = ('AGENTS.md', 'CLAUDE.md')

# Both halves, because either alone leaves a session guessing: the phrase
# so it is recognized, and what it does so it can be acted on without
# asking.
REQUIRED = (
    ('Park it', 'the phrase itself, so a session recognizes it'),
    ('parked', 'the disposition the phrase writes, so a session knows what to do'),
)


class NotApplicable(Exception):
    """The check could not run. Exit 2, never a silent pass."""


def rule_text():
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


def find_violations():
    present = [n for n in INSTRUCTIONS_FILES if (ROOT / n).is_file()]
    if not present:
        raise NotApplicable(
            'no instructions file (' + ' or '.join(INSTRUCTIONS_FILES)
            + ') in this repository, so there is nowhere the phrase could be '
              'defined')

    # Concatenated, not per-file: a repo that splits its instructions across
    # AGENTS.md and CLAUDE.md has still defined the phrase once a session
    # reading its entry point reaches it.
    text = '\n'.join((ROOT / n).read_text(encoding='utf-8', errors='ignore')
                     for n in present)
    where = ' + '.join(present)
    return [f'{where}: does not carry {needle!r} -- {why}. A standing phrase '
            f'nobody can look up sends the next session to ask what it means, '
            f'which is the interruption the phrase exists to stop.'
            for needle, why in REQUIRED if needle not in text]


def main():
    try:
        findings = find_violations()
    except NotApplicable as e:
        print(f'park-it: NOT APPLICABLE -- {e}', file=sys.stderr)
        return 2
    if not findings:
        return 0
    for f in findings:
        print(f'VIOLATION  park-it: {f}')
    print('  the rule:')
    for line in rule_text().splitlines():
        print(f'    {line}')
    return 1


if __name__ == '__main__':
    sys.exit(main())

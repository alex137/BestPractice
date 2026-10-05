#!/usr/bin/env python3
"""a practice's standing: how binding it is, and who may set it

The one place the three standings are defined, read by every channel that
shows a practice and by the `practice-standing` check, so the words and the
authority rule exist once.

code-cites-practice: practice-standing

THE THREE (spec/PRACTICE_STANDING_AND_RECHECK_PLAN.md; Morgan, 2026-10-05,
strength: decided):

  protocol    must be followed. The default: a practice with no
              `standing:` field is a Protocol, so only the exceptions carry
              a label.
  principle   a standing philosophy, applied with judgment.
  preference  someone's way of doing things: followed by default, and set
              aside only with the reason said.

WHO MAY SET ONE. A Protocol or a Principle is set by someone with authority
over the source that publishes it: in BestPractice (the universal set) the
`maintainers` in precedent.json, Morgan and Alex; in a shared set its
approvers.json; in an individual set the person whose identity.json it
holds. That is the registry tools/precedent_audience.py already reads to
decide who owns a repository, so one list answers both questions and
nothing here can drift from it. `standing_by:` records who set it, as the
GitHub username (or, in an individual set, the email) that registry uses.
A Preference is whoever's preference it is; its `standing_by:` names them,
and they need not be in the registry.

WHAT THIS DOES NOT DECIDE. Whether a label is RIGHT, and whether the person
named actually said so in a message of their own -- a session never sets a
Protocol or a Principle on its own say-so, nor on a summary relayed from
another session. Both live in the conversation, not the tree.

Run:
  python3 tools/practice_standing.py [--repo DIR]    who may set a standing here
"""
import pathlib
import sys

STANDINGS = ('protocol', 'principle', 'preference')
DEFAULT = 'protocol'
# Standings that only someone the source's registry names may set.
NEEDS_AUTHORITY = ('protocol', 'principle')

# What a session reads beside the label. One wording, used by every channel.
MEANING = {
    'protocol': 'must be followed',
    'principle': 'apply it with judgment',
    'preference': 'followed by default; set it aside only with the reason said',
}

# The three numbers steps 7 and 8 of the plan run on. None is a fact about
# the world: each is a guess at where the line should sit, so each is an
# input to revisit, not a settled value (practice: constants-are-risk-inputs).
# Proposed by a session and accepted as proposed -- Morgan, 2026-10-05:
# "Book it, and use your picks for the numbers" (strength: assented).
# Change one here, with the date, who and why; nothing else holds a copy.
CONSTANTS = {
    # Times a Preference is restated in conversation, each noted in the
    # person's own set, before a session suggests making it a Protocol.
    'restatements_to_suggest_protocol': 3,
    # Months with no sign of use in a repository's history before a practice
    # becomes a recheck candidate there.
    'months_unused_to_recheck': 6,
    # Months a "keep" answer to a recheck quiets that practice in that
    # repository before it can be a candidate again.
    'months_keep_quiets': 12,
}

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent


def _raw(fm, key):
    v = fm.get(key) if isinstance(fm, dict) else None
    if v is None:
        return ''
    v = str(v).strip().strip('"\'').strip()
    return '' if v in ('null', '~') else v


def declared(fm):
    """The `standing:` value as written, lowercased; '' when absent or null."""
    return _raw(fm, 'standing').lower()


def standing(fm):
    """The practice's standing, with absence meaning Protocol. A value this
    engine does not know is returned as written, so the check can name it;
    no channel shows a label for it."""
    return declared(fm) or DEFAULT


def label(fm):
    """'Principle' or 'Preference' for a labelled exception, '' for a
    Protocol (the default needs no label) or an unknown value."""
    s = standing(fm)
    return s.capitalize() if s in STANDINGS and s != DEFAULT else ''


def heading_note(fm):
    """Appended to a practice's heading where its Rule is shown in full:
    ' -- Preference: followed by default; ...', or ''."""
    lab = label(fm)
    return f" -- {lab}: {MEANING[lab.lower()]}" if lab else ''


def inline_note(fm):
    """Put before a Rule printed inline (the resident block):
    '*Preference: followed by default; ...* ', or ''."""
    lab = label(fm)
    return f"*{lab}: {MEANING[lab.lower()]}.* " if lab else ''


def clause_prefix(fm):
    """Put before a one-line index clause: 'Preference: ', or ''."""
    lab = label(fm)
    return f"{lab}: " if lab else ''


def _norm(who):
    who = str(who or '').strip().lower()
    if not who or '@' in who[1:]:
        return who                       # empty, or an email
    return '@' + who.lstrip('@')


def authority(repo):
    """-> (names, where): who may set a Protocol or a Principle here, as the
    lowercased `@user` / email set precedent_audience reads, and the file it
    came from; (None, None) when no registry names anyone."""
    sys.path.insert(0, str(_ENGINE_DIR))
    try:
        import precedent_audience as pa
    except ImportError:
        return None, None
    return pa.owners(repo)


def problems(fm, repo, _authority=None):
    """-> list of strings, one per thing wrong with this practice's standing
    fields. Empty for a practice that carries neither field."""
    s, by = declared(fm), _raw(fm, 'standing_by')
    if not s and not by:
        return []
    if not s:
        return [f'names `standing_by: {by}` but carries no `standing:` -- '
                f'record the standing that person set, or remove the line']
    if s not in STANDINGS:
        return [f'`standing: {s}` is not one of {", ".join(STANDINGS)}']
    if not by:
        return [f'is a {s.capitalize()} but `standing_by:` names nobody -- '
                f'record who set it, as the GitHub username the authority '
                f'registry uses']
    if s not in NEEDS_AUTHORITY:
        return []
    names, where = _authority if _authority is not None else authority(repo)
    if not names:
        return [f'is a {s.capitalize()}, which only someone with authority '
                f'over this source may set, and no registry here names '
                f'anyone (precedent.json `maintainers`, approvers.json, or an '
                f'individual set\'s identity.json)']
    if _norm(by) not in names:
        return [f'is a {s.capitalize()} set by {by!r}, who is not named in '
                f'{where} -- only those people may set a Protocol or a '
                f'Principle in this source']
    return []


def main(argv):
    if '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0
    repo = '.'
    if '--repo' in argv:
        repo = argv[argv.index('--repo') + 1]
    names, where = authority(repo)
    if not names:
        print('No registry here names anyone who may set a Protocol or a '
              'Principle.')
        return 1
    print(f"May set a Protocol or a Principle here (from {where}): "
          f"{', '.join(sorted(names))}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

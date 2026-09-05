#!/usr/bin/env python3
"""very_deep_check.py -- the very deep check (practice: very-deep-check).

Enumerates this checkout's own scope -- its top-level documents plus every
active source's `practices/*.md` tree, resolved via
tools/precedent_resolve.py the same way ordinary loading is -- and hands the
invoking session a fixed checklist of drift categories to read that scope
against. On-demand only, invoked explicitly by a person; never wired into a
commit, push, or merge gate.

NOT `full_practice_audit.py` under another name. That tool asks, one
practice at a time, "is this specific Rule satisfied?" -- a closed question
against one document's own text. This one asks a question no single
practice's Rule can be checked against: does the repo's OWN WRITING, taken as
a set, still hold together? A contradiction between two documents or a
cross-reference gone stale is not a violation of any one practice's Rule; it
is a property of the documents together, which a per-practice sweep -- run
any number of times -- cannot see.

WHAT THIS TOOL DOES AND DOES NOT DO. It enumerates; it does not read or
judge. Enumerating requires no model judgment (it is a directory walk), so
it is done here, mechanically, the same reasoning `full_practice_audit.py`
gives for enumerating practices instead of leaving that to the session too.
Reading the enumerated scope for contradiction, staleness, repetition,
disproportion, formatting drift, self-application gaps, and backlog drift
is the part only a session can do -- see practices/very-deep-check.md's
Detail section for the fixed checklist, printed again at the end of this
tool's own output so it travels with the enumeration.

READ practices/very-deep-check.md's Why section before trusting this
mechanism's own reliability -- it has not been evaluated the way
full-practice-audit and routing-audit have.

Run:
  python3 tools/very_deep_check.py [--repo PATH] [--user-config PATH]
      -- the scope to read, plus the checklist, as plain text.
  python3 tools/very_deep_check.py --json [--repo PATH] [--user-config PATH]
      -- the same enumeration as structured data.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr

# Top-level documents worth reading for coherence, if a given scope has them.
# Not every source will carry every name; only files that actually exist are
# reported. Deliberately a fixed, generic list rather than reflection over
# "every markdown file at the root" -- that would also sweep in one-off
# planning documents no session should be reading for whole-repo coherence.
CANDIDATE_DOCS = [
    "README.md", "AGENTS.md", "CLAUDE.md", "MAP.md", "GLOSSARY.md",
    "TODO.md", "GETTING_STARTED.md",
]

CHECKLIST = """\
What to look for -- a starting point, not a specification. Report anything
that makes the repo harder to trust or follow, whether or not a bullet below
names it:

- Contradictions -- two rules, or two documents, that can't both be
  followed; a rule whose own carve-outs have eaten it.
- Stale references -- a slug, practice number, filename, heading, or
  click-path pointing at something moved or gone; a positional number cited
  as if it were a name; numbering that skips, repeats, or runs out of order;
  an orphaned name a rename elsewhere left behind in this repo's own prose.
- Fragments -- a sentence, note, or heading left behind by an earlier edit:
  a "temporary" caveat whose occasion has passed, a note about a
  reorganization that already happened.
- Needless repetition -- the same rule stated in full in several places,
  where one statement plus pointers would do.
- Disproportion -- paragraphs of detail on a minor point, prose that
  emphasizes an aside more than the point it supports, a rule grouped where
  it no longer fits.
- Process-cost disproportion -- a rule that's minor in the scheme of things
  but costs a disproportionate amount of tokens, time, or friction each time
  it applies, especially one re-researched from scratch on every occurrence
  instead of following a written-down answer.
- Formatting and spacing drift -- inconsistent heading levels and
  capitalization, a bullet missing the blank line its neighbors have, mixed
  list markers, a ragged table, stray blank lines or trailing whitespace, a
  stale "last updated" header.
- Self-application -- a rule this repo asks of every project it's installed
  into that this repo doesn't yet follow itself.
- Backlog drift -- a TODO.md (or equivalent open-items document) entry
  already done, no longer relevant, or never actually decided.
- Anything else the read turns up -- if something is wrong and none of the
  categories above name it, it is still a finding; if it will recur, add a
  bullet to practices/very-deep-check.md so the next run looks for it
  deliberately.

Fix what the review turns up in the same pass -- these are almost always
small -- then re-run the mechanical audits, since the fixes themselves can
break a link. Anything deliberately left alone gets a line in TODO.md saying
so, rather than being silently dropped.\
"""


def enumerate_scope(repo=None, user_config=None):
    """-> {'checkout': {...}, 'sources': [...], 'missing': [...]}"""
    repo_root = pathlib.Path(repo or ROOT).resolve()
    sources = pr.load_config(str(repo_root), user_config)

    def _docs_and_practice_count(base):
        base = pathlib.Path(base)
        docs = [d for d in CANDIDATE_DOCS if (base / d).is_file()]
        practices_dir = base / 'practices'
        n_practices = len(list(practices_dir.glob('*.md'))) if practices_dir.is_dir() else 0
        return docs, n_practices

    checkout_docs, checkout_practices = _docs_and_practice_count(repo_root)
    checkout = {'path': str(repo_root), 'docs': checkout_docs,
                'practice_count': checkout_practices}

    missing = []
    source_rows = []
    for s in sources:
        docs, n_practices = _docs_and_practice_count(s['path'])
        if not docs and n_practices == 0:
            missing.append({'level': s['level'], 'name': s['name'],
                            'reason': f"{s['path']} has neither a "
                                       f"recognized top-level document nor "
                                       f"a practices/ directory -- source "
                                       f"unreachable or empty"})
            continue
        source_rows.append({'level': s['level'], 'name': s['name'],
                            'path': s['path'], 'docs': docs,
                            'practice_count': n_practices})

    return {'checkout': checkout, 'sources': source_rows, 'missing': missing}


def main():
    args = sys.argv[1:]
    repo, user_config = None, None
    for flag, dest in (('--repo', 'repo'), ('--user-config', 'user_config')):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f"very deep check FAIL: {flag} needs a value.")
            value = args[i + 1]
            args = args[:i] + args[i + 2:]
            if dest == 'repo':
                repo = value
            else:
                user_config = value
    as_json = '--json' in args

    data = enumerate_scope(repo, user_config)
    for m in data['missing']:
        print(f"very deep check: the {m['level']} source {m['name']!r} "
             f"is not available ({m['reason']}) -- running WITHOUT it.",
             file=sys.stderr)

    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    c = data['checkout']
    print(f"very deep check -- scope to read (not enforcement, judgment):\n")
    print(f"this checkout ({c['path']}):")
    print(f"  documents: {', '.join(c['docs']) if c['docs'] else '(none of the recognized names present)'}")
    print(f"  practices/: {c['practice_count']} file(s)\n")

    for s in data['sources']:
        print(f"{s['level']} source {s['name']!r} ({s['path']}):")
        print(f"  documents: {', '.join(s['docs']) if s['docs'] else '(none of the recognized names present)'}")
        print(f"  practices/: {s['practice_count']} file(s)\n")

    print(CHECKLIST)
    return 0


if __name__ == '__main__':
    sys.exit(main())

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

A missing declared team or individual source FAILS this tool by default
(practice: very-deep-check) -- the ordinary loader degrades gracefully when
one is absent, which is right for routine loading but wrong here: a very
deep check that silently runs without a source it was told to check is not
a very deep check. Pass --allow-missing-sources for the rare case where
that is actually intended.

Also scans this checkout and every team/individual source that is its own
git checkout for branches fully merged into that repo's integration branch
and not yet deleted (git merge-base --is-ancestor -- true regardless of
whether GitHub's own "merged" flag is set, which it is not for a repo that
lands PRs by direct push). Reported for the invoking session to cross-check
against each branch's PR history and report with a direct link, per
practice: very-deep-check and the branch-cleanup method
next-steps-after-commit (in a repo running that practice) already defines --
this offline scan has no GitHub access, so it can prove "merged" but never
"who opened this" or "which PR", the same limits practice: next-steps-after-
commit already lays out for that lookup.

Run:
  python3 tools/very_deep_check.py [--repo PATH] [--user-config PATH]
      -- the scope to read, plus the checklist, as plain text.
  python3 tools/very_deep_check.py --json [--repo PATH] [--user-config PATH]
      -- the same enumeration as structured data.
  python3 tools/very_deep_check.py --target BRANCH
      -- override the checkout's own integration branch for the merge scan
      (e.g. "precedent-beta-v01" in this repo, while the sweep still
      defaults to "main" for every other source).
  python3 tools/very_deep_check.py --allow-missing-sources
      -- proceed even if a declared team/individual source isn't present.
  python3 tools/very_deep_check.py --skip-branch-scan
      -- enumerate and check sources only; skip the git merge scan.
Exit: 1 if a declared team/individual source is missing and
--allow-missing-sources was not given; 0 otherwise.
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_resolve as pr

FATAL_MISSING_LEVELS = ('team', 'individual')

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


def _run_git(repo_dir, *args):
    try:
        r = subprocess.run(['git', '-C', str(repo_dir), *args],
                            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return 1, '', 'git unavailable or timed out'
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _default_remote_branch(repo_dir):
    """-> the short branch name origin/HEAD points at ('main', typically),
    or None if it can't be determined. `refs/remotes/origin/HEAD` is not set
    on every clone this tool will see -- reproduced directly on this repo's
    own sibling checkouts of precedent-team-maintainers and
    precedent-individual, both attached (not `git clone`d normally) without
    it, where `git symbolic-ref --short refs/remotes/origin/HEAD` just fails
    rather than degrading -- so fall back to checking for a same-named
    remote-tracking branch among the common default names before giving up."""
    rc, out, _ = _run_git(repo_dir, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD')
    if rc == 0 and '/' in out:
        return out.split('/', 1)[1]
    for candidate in ('main', 'master'):
        rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet', f'origin/{candidate}')
        if rc == 0:
            return candidate
    return None


def scan_branches(repo_dir, target=None, exclude=()):
    """-> None if repo_dir isn't its own git checkout (a repo-local source
    living inside the parent checkout shares the parent's branches and has
    none of its own to scan) or its integration branch can't be resolved.
    Otherwise {'target': str, 'merged': [...], 'unmerged': [...]}: 'merged'
    branches are mechanically PROVEN safe to delete (every commit on them is
    already an ancestor of target); 'unmerged' is everything else remaining
    (default branch and target itself excluded) -- some of those may still
    be safe (closed because a later PR superseded them) but that call needs
    the branch's PR history, which this offline check cannot see. See
    practices/very-deep-check.md's Install section.

    `exclude` names branches never to report either way regardless of merge
    status -- the branch the invoking session is itself working on, which
    can be trivially "merged" (an ancestor of target) simply because no
    commits have landed on it yet, long before it is actually done."""
    repo_dir = pathlib.Path(repo_dir)
    if not (repo_dir / '.git').is_dir():
        return None
    default_branch = _default_remote_branch(repo_dir)
    target = target or default_branch
    if not target:
        return None
    # A repo whose integration branch isn't its default (this repo's own
    # precedent-beta-v01, per AGENTS.md) still has that default branch
    # (main) sitting around -- never report it as a deletion candidate just
    # because it happens not to be an ancestor of the *other* protected
    # branch.
    protected = {target, default_branch} - {None}
    target_ref = f'origin/{target}'
    rc, _, _ = _run_git(repo_dir, 'rev-parse', '--verify', '--quiet', target_ref)
    if rc != 0:
        return None
    rc, out, _ = _run_git(repo_dir, 'for-each-ref', '--format=%(refname:short)',
                           'refs/remotes/origin')
    if rc != 0:
        return None
    merged, unmerged = [], []
    for ref in out.splitlines():
        if '/' not in ref:
            continue
        name = ref.split('/', 1)[1]
        if name == 'HEAD' or name in protected or name in exclude:
            continue
        rc, _, _ = _run_git(repo_dir, 'merge-base', '--is-ancestor', ref, target_ref)
        (merged if rc == 0 else unmerged).append(name)
    return {'target': target, 'merged': sorted(merged), 'unmerged': sorted(unmerged)}


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
    repo, user_config, checkout_target = None, None, None
    for flag, dest in (('--repo', 'repo'), ('--user-config', 'user_config'),
                       ('--target', 'checkout_target')):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f"very deep check FAIL: {flag} needs a value.")
            value = args[i + 1]
            args = args[:i] + args[i + 2:]
            if dest == 'repo':
                repo = value
            elif dest == 'user_config':
                user_config = value
            else:
                checkout_target = value
    as_json = '--json' in args
    allow_missing = '--allow-missing-sources' in args
    skip_branch_scan = '--skip-branch-scan' in args

    data = enumerate_scope(repo, user_config)
    repo_root = pathlib.Path(repo or ROOT).resolve()

    fatal_missing = [m for m in data['missing'] if m['level'] in FATAL_MISSING_LEVELS]
    other_missing = [m for m in data['missing'] if m not in fatal_missing]
    for m in other_missing:
        print(f"very deep check: the {m['level']} source {m['name']!r} "
             f"is not available ({m['reason']}) -- running WITHOUT it.",
             file=sys.stderr)
    if fatal_missing and not allow_missing:
        for m in fatal_missing:
            print(f"very deep check FAIL: the {m['level']} source {m['name']!r} "
                 f"is declared but not present in this session "
                 f"({m['reason']}). A very deep check that silently runs "
                 f"without a declared team or individual source defeats the "
                 f"reason it was asked for -- attach or clone it into this "
                 f"session (this harness's own repo-attachment mechanism, "
                 f"or a plain `git clone` of the source's repo) and re-run. "
                 f"Pass --allow-missing-sources only if proceeding without "
                 f"it is actually intended.", file=sys.stderr)
        return 1

    branch_scans = {}
    if not skip_branch_scan:
        _, checkout_branch, _ = _run_git(repo_root, 'rev-parse', '--abbrev-ref', 'HEAD')
        branch_scans['checkout'] = scan_branches(
            repo_root, checkout_target, exclude=(checkout_branch,) if checkout_branch else ())
        for s in data['sources']:
            if s['level'] in FATAL_MISSING_LEVELS:
                _, src_branch, _ = _run_git(s['path'], 'rev-parse', '--abbrev-ref', 'HEAD')
                branch_scans[s['name']] = scan_branches(
                    s['path'], exclude=(src_branch,) if src_branch else ())

    if as_json:
        data['branches'] = branch_scans
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

    if not skip_branch_scan:
        print("\nSTALE BRANCHES -- mechanically merged, not yet deleted (still\n"
              "needs a PR link and an authorship check before reporting any of\n"
              "these as safe to delete -- see practices/very-deep-check.md):\n")
        for name, scan in branch_scans.items():
            if scan is None:
                print(f"{name}: not its own git checkout, or integration "
                      f"branch could not be resolved -- skipped.\n")
                continue
            print(f"{name} (integration branch: {scan['target']}):")
            if scan['merged']:
                for b in scan['merged']:
                    print(f"  MERGED, undeleted: {b}")
            else:
                print(f"  (none)")
            if scan['unmerged']:
                print(f"  not mechanically provable merged -- check each "
                      f"one's own PR history for a superseded case: "
                      f"{', '.join(scan['unmerged'])}")
            print()

    return 0


if __name__ == '__main__':
    sys.exit(main())

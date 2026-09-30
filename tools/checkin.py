#!/usr/bin/env python3
"""checkin.py — drive the periodic check-in (INSTALL.md §4) mechanically.

Runs from a dependent repo (script lives at process/upstream/tools/). The
check-in loop — sync the vendored tree into a clone of the upstream repo,
land it there, then record the landed commit in the manifest — was performed
by hand several times and each pass repeated the same steps with the same
two failure modes: forgetting the scrub before content left the private
repo, and recording a hash that didn't actually match the tree that landed.
Per the convention-becomes-audit rule, the steps are now a tool; every
mutation it performs is gated by a check that fails loudly.

Four subcommands — update takes upstream changes IN, the other three drive
a check-in OUT. Each takes `--source NAME` to run the same loop for a SHARED
practice set that ships code (practice: source-naming, 2026-09-18): the
vendored tree is then process/<name>/, the manifest process/manifest_<name>.json,
and only the directories the set's own precedent-source.json lists under
`code` are mirrored; its practices resolve live and are never vendored.
Without --source the universal set is mirrored whole, as always.

Each also takes `--repo PATH`: the consuming repo to act on, instead of the
repo this file sits in (2026-09-27). It lets the SOURCE clone's current copy
of this tool update a consumer, which is how tools/precedent_update.py runs
it -- the consumer's own vendored copy lives inside the very catalogue it is
updating, so a fix to it would otherwise reach a repo only after that repo
had already needed it.

  status <upstream-clone>   Compare the vendored tree against the clone's
                            working tree: list Added/Modified/Deleted files
                            (vendored perspective), show the manifest's
                            recorded upstream.commit vs the clone's HEAD.
                            Exit 1 if the trees differ (so it can gate).

  update <upstream-clone> [--force] [--allow-pinned]
                            The INSTALL.md §2 direction: mirror the clone's
                            tree, at the branch THIS install tracks
                            (manifest `upstream.branch`, else the clone's
                            default), into the vendored tree. Reads the
                            clone with `git archive` -- never checks it out,
                            pulls in it, or moves its HEAD.
                            REFUSES while `upstream.branch` names a branch
                            other than the clone's default: that is
                            spec/MIGRATING_EXISTING_INSTALLS.md's pinned-
                            branch hold, and the remedy is a one-off manual
                            mirror (override for one run with --allow-pinned,
                            or the equivalent PRECEDENT_ALLOW_PINNED_UPDATE=1
                            -- prefer the flag: the env var's name reads as a
                            safety-bypass pattern to at least one harness's
                            own permission classifier, which refuses it
                            before checkin.py ever runs).
                            Also REFUSES if the vendored tree differs from
                            the recorded upstream.commit — that difference
                            is unexported local work the mirror would
                            silently clobber; export it first (§3/§4) or
                            pass --force to overwrite. (Origin: a session
                            hand-rolled this mirror with git archive | tar
                            — rsync is absent in hosted containers, as of
                            2026-08 — and a stale local default-branch ref
                            nearly mirrored an old tree; the tool pulls
                            fresh and guards the overwrite.)

  rules [REF]               In the repo that ships the copy: each file
                            added since REF (default: the landing branch)
                            and whether it ships to consumers, by the
                            VENDORING_RULES rule that decides it. Exit 1
                            if a file has no rule.

  push <upstream-clone> --why "what went wrong"
                            Send this repo's committed changes to the
                            vendored tree upstream, as a branch in the
                            clone: tools/precedent_local_edits.py send
                            merges each file three ways onto upstream's
                            landing branch (so upstream work since the
                            mirror is never reverted), runs this repo's
                            scrub and upstream's leak gate and basic tier,
                            commits, and pushes the branch -- never a pull
                            request, never a merge -- then prints the prompt
                            for the session that lands it. With --source,
                            a shared set's code tree still takes the old
                            mirror into the clone's working tree.

  record <upstream-clone> [--note "..."] [--resolving PATH ...]
                            After the upstream merge: pull the clone's
                            default branch, verify it is byte-identical to
                            the vendored tree (fail loudly if not — never
                            record a hash that doesn't match the tree), then
                            write the clone's HEAD hash into
                            process/manifest.json upstream.commit. Commit
                            the manifest change in the dependent repo
                            yourself. --resolving names a file (relative
                            to the vendored tree) whose local edit Update
                            Vendors is resolving itself; the carry check
                            skips exactly those, and says how many.

  fresh                    Clone-free staleness notice for session starts:
                            one `git ls-remote` of the manifest's upstream
                            repo, compared to the recorded upstream.commit.
                            Prints one line only when upstream has moved;
                            always exits 0 (a notice, never a gate) and
                            stays silent on network failure — detection is
                            automated, taking the update stays deliberate
                            (INSTALL.md sec.2).

Run:  python3 process/upstream/tools/checkin.py fresh
      python3 process/upstream/tools/checkin.py status ../BestPractice
      python3 process/upstream/tools/checkin.py update ../BestPractice
      python3 process/upstream/tools/checkin.py push   ../BestPractice
      python3 process/upstream/tools/checkin.py record ../BestPractice --note "PR #4"
      python3 ../BestPractice/tools/checkin.py update ../BestPractice --repo .
"""
import collections, datetime, filecmp, io, json, os, pathlib, shutil, subprocess, sys, tarfile, tempfile

# practice: one-formatter-per-quantity -- every moment in time this project
# writes down comes from ONE module, in the person's zone, carrying its
# offset. Never a bare datetime.date.today(): that is the container's UTC.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_time  # noqa: E402


HERE = pathlib.Path(__file__).resolve()
_top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=HERE.parent,
                      capture_output=True, text=True).stdout.strip()
ROOT = pathlib.Path(_top) if _top else HERE.parents[3]
UPSTREAM = ROOT / 'process' / 'upstream'
MANIFEST = ROOT / 'process' / 'manifest.json'
# `--source NAME` (2026-09-18, practice: source-naming): the same loop for a
# SHARED practice set that ships code alongside its practices. The
# vendored tree is process/<name>/, its manifest process/manifest_<name>.json,
# and only the directories the set's own precedent-source.json lists under
# `code` are mirrored -- the practices themselves resolve live from the
# sibling clone and are never vendored. With no --source the universal set
# is mirrored whole, exactly as before.
SOURCE = None
SOURCE_MANIFEST = 'precedent-source.json'
CODE_DIRS = None


def _select_source(name):
    global SOURCE, UPSTREAM, MANIFEST
    SOURCE = name
    UPSTREAM = ROOT / 'process' / name
    MANIFEST = ROOT / 'process' / f'manifest_{name}.json'


def _read_source_manifest(clone):
    """-> the clone's own precedent-source.json (dict) or {}. Read from the
    tracked branch's remote ref when it has one, so the working tree's state
    is never what decides what gets mirrored."""
    for ref in (f'origin/{_tracked_branch(clone)}', 'HEAD'):
        rc, out = _git_rc(clone, 'show', f'{ref}:{SOURCE_MANIFEST}')
        if rc == 0 and out.strip():
            try:
                return json.loads(out)
            except ValueError:
                sys.exit(f"checkin FAIL: {clone}'s {SOURCE_MANIFEST} at {ref} is not "
                         f"valid JSON")
    f = clone / SOURCE_MANIFEST
    if f.is_file():
        try:
            return json.loads(f.read_text(encoding='utf-8'))
        except ValueError:
            sys.exit(f"checkin FAIL: {f} is not valid JSON")
    return {}


def _bind_source(clone):
    """With --source: the clone must be the set it is declared to be, and
    its manifest decides which directories are code. Identity is read off
    the source, never inferred from a name."""
    global CODE_DIRS
    if SOURCE is None:
        return
    m = _read_source_manifest(clone)
    own = m.get('name')
    if own and own != SOURCE:
        sys.exit(f"checkin FAIL: {clone} calls itself {own!r} in its "
                 f"{SOURCE_MANIFEST}; --source named {SOURCE!r}. Point at the "
                 f"right clone, or declare the source by the name it gives itself.")
    dirs = [str(d).strip().strip('/') for d in (m.get('code') or []) if str(d).strip()]
    if not dirs:
        sys.exit(f"checkin FAIL: {clone}'s {SOURCE_MANIFEST} lists no `code` "
                 f"directories, so there is nothing to vendor -- a set whose "
                 f"practices resolve live needs no mirror at all.")
    # A consumer may opt in to vendoring the set's PRACTICES too, by setting
    # `vendor_practices: true` under `upstream` in its own
    # process/manifest_<name>.json. Then practices/ and the set's
    # precedent-source.json are mirrored beside its code, the consumer's
    # precedent.json points the source at process/<name>, and a fresh
    # container resolves the set with no sibling clone and no repository
    # access granted mid-session. Only for a private consumer: a private
    # set's rules in a public tree are exactly what the leak gate refuses.
    # Why: a consumer whose sessions cannot reach the set until the agent
    # attaches it by hand ran every fresh session without the set's rules
    # until someone asked why a repository was being added (2026-09-29).
    try:
        own = json.loads(MANIFEST.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        own = {}
    if (own.get('upstream') or {}).get('vendor_practices'):
        dirs += ['practices', SOURCE_MANIFEST]
    CODE_DIRS = dirs


def _same_commit(a, b):
    """True when two commit strings name the same commit.

    A manifest may legitimately record a SHORT hash -- a person writing one
    by hand does, and nothing ever required the full 40 -- while `git
    rev-parse` and `ls-remote` return the full one. Compared as strings
    those never match, so a perfectly current repo reports
    "(!= recorded)" and an unmoved upstream reports "has moved".
    Reproduced 2026-09-06 against a real consumer: recorded 6ac06f6, clone
    HEAD 6ac06f6eb166..., reported as different. Prefix comparison, in
    whichever direction is shorter, with a floor so a truncation to
    nothing cannot match everything."""
    a, b = (a or '').strip(), (b or '').strip()
    if not a or not b:
        return False
    n = min(len(a), len(b))
    if n < 7:            # shorter than git's own minimum abbreviation
        return False
    return a[:n] == b[:n]


def _git(clone, *args):
    return subprocess.run(['git', '-C', str(clone)] + list(args),
                          capture_output=True, text=True).stdout.strip()


def _rev_parse_quiet(clone, ref):
    """-> the commit hash for `ref`, or None. Never the ref's own name.

    `git rev-parse <missing-ref>` exits non-zero but ECHOES THE REF ON
    STDOUT, so the plain `_git(...)` above hands back the string
    'origin/precedent-beta-v01' where a hash belongs -- AGENTS.md's gotchas
    section, which has this reaching CI once already. --verify --quiet is
    silent and exits 1.
    """
    r = subprocess.run(['git', '-C', str(clone), 'rev-parse', '--verify',
                        '--quiet', ref], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


# Directories that exist in BestPractice and have no business in a dependent
# repo. `evals/` is this project's own routing-quality measurement corpus --
# the fixtures behind spec/LOADER.md's recall and precision figures. It answers
# a question about BUILDING Precedent, not about using it, and nothing a
# consumer runs reads any of it (checked across both real consumers,
# 2026-09-06: the only mention outside the vendored tree is a comment in
# precedent_check.py). Every session in every consuming repo was cloning,
# scanning and scrubbing it for nothing.
#
# NOTE, because this reads like a deletion and is not: nothing here removes a
# PRACTICE. Practices live in practices/ and every one of them still vendors.
# This excludes measurement fixtures only.
#
# The share it accounts for is measured, never typed: `python3
# tools/checkin.py not-vendored` prints it against the tree in front of you.
# An earlier version of this comment froze the figures inline and they were
# stale within a day, which is the same rot that practice
# `computed-numbers-in-scripts` exists to stop -- in prose it is a gate, and in
# a code comment nothing checks it at all, so the honest form is a command the
# reader can run.
#
# Excluded from the comparison, so an existing consumer that already has the
# directory simply stops being told it drifted; deleting the stale copy is
# the consumer's own next re-vendor, not something this tool reaches in and
# does.
# `philosophy/` is the second entry, added 2026-09-14 after Morgan read the
# vendoring instructions and asked why it was in them at all: it is the
# argument FOR the ideas Precedent implements -- essays, notes, rules being
# tried -- and it is neither part of the system nor instructions for using it.
# The repo already says so in two places and had not joined them up:
# local/practices/philosophy-is-not-repo-policy.md says philosophy/ binds
# nothing outside itself, and spec/DOCUMENT_LIFECYCLE.md's placement table
# sorts every directory by AUDIENCE -- documentation/ is "someone using
# Precedent on their own project", which is exactly who a vendored tree is
# for, and philosophy/ is not in that table at all. A consumer was cloning,
# scanning and scrubbing a case for adopting a thing they had adopted.
#
# No link goes dead: doc_lint.py skips the link check inside a mirrored tree
# outright (see check_broken_links), so the references into philosophy/ from
# the vendored README.md, METHOD.md and MAP.md report nothing in a consumer.
# The two checks that read philosophy/ (verify_harness.py) already report
# not-applicable when the directory is absent rather than passing blind.
#
# Five more joined 2026-09-17, checked against spec/DOCUMENT_LIFECYCLE.md's
# own audience table (contributor/session-building-Precedent = cut,
# adopter/session-using-Precedent = keep) -- but the table alone is not what
# decided any of these; each was verified against its ACTUAL current
# content first, because the table's classification of one candidate
# (gotchas/, considered and rejected -- see below) turned out to be wrong on
# a real consumer and nearly cost 52 lines of live content:
#
#   spec/, todo/, decisions/, deck/ -- BestPractice's own build plans,
#   backlog and dated design decisions about the ENGINE, plus pitch-deck
#   tooling. Every citation into these four from a vendored (resident or
#   universal) practice file is a full external github.com URL, not a local
#   relative link -- the same pattern already accepted for philosophy/ -- so
#   a consumer session can always follow the citation over the network; it
#   never depends on a local copy under process/upstream/.
#
#   record/ -- the closer call of the five, flagged rather than asserted.
#   It is NOT what spec/DOCUMENT_LIFECYCLE.md's still-unexecuted migration
#   proposal describes (that would move BestPractice's own phase briefs
#   here; none of that has landed). What actually lives in record/ today is
#   record/GOTCHAS.md and record/GOTCHAS_ARCHIVE.md -- the pre-migration,
#   monolithic predecessor to the current gotchas/*.md per-file split, kept
#   as the fuller story text and cited by #gN anchor from several resident
#   practices (session-text.md, very-deep-check.md, grep-before-search.md,
#   chief-of-staff.md, vendor-update-runbook.md). Those citations are also
#   full external URLs (same reasoning as above), and the LIVE, current
#   mechanism -- gotchas/*.md -- is not excluded (below). record/GOTCHAS.md
#   itself carries `audience: session` in its own frontmatter, which reads
#   against excluding it; this was weighed and record/ was excluded anyway
#   on the strength of the external-URL pattern and the gotchas/*.md split
#   already covering the live/operational half. Reopen this one specifically
#   if a session hits a case where the local copy was actually needed.
#
# CONSIDERED AND REJECTED: gotchas/. The original candidate list (drafted
# from a check-in session's own experience in a consumer repo) grouped it
# with todo/decisions/ by name-association, but its actual content is
# troubleshooting for RUNNING the vendored tooling (checkin.py itself,
# freshness-guard.sh, add_repo interactions, precedent_check.py), not
# planning for building it -- and it is reached the one way none of the
# above are: environment-gotchas.md, a RESIDENT universal practice, has its
# own Rule say "hit an unexplained failure, grep `gotchas/` before
# concluding it's new." A grep is a local filesystem operation; it finds
# nothing that is not actually vendored. Excluding gotchas/ would have left
# that instruction pointing at an empty directory in every consumer.
#
# ALSO CONSIDERED, kept IN: examples/ (now documentation/examples/, moved
# 2026-09-19 -- see below). Its README says plainly what it is for -- "here
# so that someone setting up their own [personal practice set] has
# something concrete to copy" -- which is an adopter activity (a consumer
# building their OWN practice set), not a contributor activity. Because it
# now lives under documentation/, which was never itself a NOT_VENDORED
# candidate, it is not even reachable by this comment's own top-level
# component-match test any more -- the move settles the audience question
# structurally instead of by a name-based judgment call.
#
# The move followed a relayed, unverified claim that a consumer repo was
# hand-deleting this directory after every Update Vendors pass; rather than
# exclude adopter-facing content on hearsay, it was relocated into
# documentation/ (the tree the repo's own audience table already assigns to
# "someone using Precedent on their own project") and a revisit was filed:
# todo/todo-2026-09-19-revisit-examples-vendoring.md. The staleness worry
# behind the same claim is separately covered by
# tools/verify_harness.py's check_example_set, which parses and resolves
# this example against the CURRENT format on every deep check and fails if
# it drifts -- so nothing new was built for that half of the concern.
#
# ALSO CONSIDERED, but out of THIS mechanism's scope: top-level .claude/ and
# .github/ (BestPractice's own dev/CI config, distinct from
# templates/harness/claude-code/ and templates/github-actions/, the actual
# instantiation sources -- confirmed absent from
# precedent_vendor_engine.py's CONSUMER_ENGINE_FILES and unreferenced
# anywhere as process/upstream/.claude or process/upstream/.github) and
# local/ (BestPractice's own repo-local practice layer -- vendoring a
# repo-local layer into another repo is a category error by definition; no
# reference to "upstream/local" or "upstream.local" found anywhere in this
# repo's own tooling). Both read as clear NOT_VENDORED candidates on the
# same audience test, but adding them is deferred rather than folded in
# here silently -- flag for confirmation before extending NOT_VENDORED to
# non-spec-lifecycle top-level directories.
NOT_VENDORED = frozenset({'evals', 'philosophy', 'spec', 'todo', 'decisions',
                          'deck', 'record'})

# Root-only exclusions -- matched by exact top-level path, NEVER as a path
# component the way NOT_VENDORED is. `_files()`'s component match is right
# for a subject-matter directory (the same "gotchas" can only ever mean
# BestPractice's own gotchas/ at the top level) but wrong here: component
# matching on 'AGENTS.md'/'CLAUDE.md' would ALSO catch
# templates/harness/claude-code/CLAUDE.md and
# templates/document-project/AGENTS.md -- real TEMPLATE SOURCES a consumer
# instantiates from (INSTALL.md sec.2), not copies of this repo's own root
# files. Confirmed both exist and must stay vendored before adding this.
#
# Why exclude the root files at all, added 2026-09-17: AGENTS.md/CLAUDE.md
# are the one class of vendored file a harness auto-loads BY FILENAME as
# live instructions for whatever directory a session is working in --
# every other vendored file is read only when something goes looking for
# it. This repo's own root AGENTS.md has an explicit internal divider
# ("The rest of this file (below) is BestPractice's own pre-fork
# orientation") separating a generic loader section from content that is
# BestPractice talking about itself ("Default branch is main... this repo
# is public and is the shared upstream", "Most changes arrive as check-in
# PRs from dependent repos") -- and the whole file, tail included, was
# vendored as an ordinary byte-for-byte mirror. On 2026-09-17 that tail
# bled into a real consumer session as if it were live instructions about
# THAT repo's own workflow.
#
# Truncating just the tail at that divider was the first design tried and
# was rejected: _diff() and everything built on it (record()'s
# byte-identical verification, push()'s mirror-BACK guard, _carry_check())
# assume the vendored tree is either byte-identical to source or fully
# absent -- nothing in this tool has a third state of "present but
# deliberately transformed". Giving AGENTS.md that third state means
# teaching every one of those functions to compare through a transform
# instead of raw bytes, for one file, forever -- and getting push() wrong
# once means a consumer's local truncated copy overwrites this repo's own
# real AGENTS.md. Full exclusion costs nothing a consumer needs: their own
# root AGENTS.md already carries ITS OWN generic loader section, generated
# fresh from ITS OWN attached sources (templates/AGENTS.md.template),
# never derived from this file -- so there is no loader content to lose,
# only the self-referential tail that was the actual problem.
NOT_VENDORED_ROOT_FILES = frozenset({'AGENTS.md', 'CLAUDE.md'})
_NOT_VENDORED_ROOT_PATHS = frozenset(pathlib.Path(n) for n in NOT_VENDORED_ROOT_FILES)


# THE COPY CARRIES WHAT A CONSUMER USES, NAMED (2026-09-30). Everything
# outside NOT_VENDORED used to go, so a consumer's process/upstream/ held
# 543 files: this repo's test suite (verify_harness.py, 2.6 MB), its own
# environment-trap notes (gotchas/), its repo-local practices (local/), the
# chat bridge, its own .claude/ and .github/ config, its MAP, index and
# to-do stub, and a second copy of the engine the repo already vendors
# into its own tools/. Morgan, 2026-09-30, asking what is normal: an
# allowlist, the way a package names the files it publishes -- "Consumers
# just want to use it not see our todo lists etc." ... "let's do. Act!".
#
# THE RULESET, and every file is decided by it (Morgan, 2026-09-30: "make
# sure that *every new file* is evaluated to see if it should be vendored
# in or not, and you should determine the ruleset"). The test:
#
#   SHIPS: what a consumer runs, instantiates, or its people read to adopt
#          and use Precedent -- the catalogue, templates, adopter guides,
#          the engine, and the settings files the engine reads from a
#          universal source's directory.
#   STAYS: how this repo is built -- its plans, open items, decisions,
#          reasoning, tests, run records, environment traps, repo-local
#          rules, its own settings and CI, its own sessions' instructions
#          and index, and separate tools it also builds.
#
# A document that is ours but that a consumer's reader needs is linked on
# GitHub from a shipped one, never shipped itself.
#
# First match wins; a path ending in '/' is a folder and everything in it.
# There is no catch-all: a path no rule covers is UNDECIDED, is left out of
# the copy, and fails precedent_check.py's `vendoring-decided` check in
# this repo until somebody adds the rule that decides it.
# `python3 tools/checkin.py rules` prints the decision for each file added
# since the landing branch (practice: vendor-rollout-disclosed, question 5).
VENDORING_RULES = (
    ('WHATS_NEW.md', False,
     "a project's own news log; each project writes its own (practice: whats-new)"),
    # Exceptions inside a shipped folder come first.
    ('templates/harness/LEDGER.md', False,
     "this repo's change log for the harness adapters"),
    ('tools/verify_harness.py', False,
     "this repo's test suite (2.6 MB); a consumer never runs it"),
    ('practices/', True, 'the catalogue: the loader reads every file'),
    ('templates/', True,
     'what a consumer instantiates at install, or when it makes a new repo'),
    ('documentation/', True,
     'guides written for the people who adopt and use Precedent'),
    ('tools/', True,
     "the engine -- in the copy only until the consumer's own tools/ has "
     "one that includes checkin.py (_copy_carries_tools)"),
    ('README.md', True, 'what Precedent is, for an adopter'),
    ('INSTALL.md', True, 'the install and update runbook'),
    ('SETUP.md', True, 'the guided setup, for a person who is not technical'),
    ('GLOSSARY.md', True, "the catalogue's terms"),
    ('PRACTICES.md', True, 'the catalogue, one page'),
    ('precedent-source.json', True,
     "the engine reads it from a universal source's directory"),
    ('precedent.json', True,
     "the engine reads it from a universal source's directory"),
    ('reply_check.json', True,
     "the reply check reads it from a universal source's directory"),
    ('close_detect.json', True,
     "close detection reads it from a universal source's directory"),
    ('AGENTS.md', False, "this repo's own session instructions"),
    ('CLAUDE.md', False, "this repo's own session instructions"),
    ('GEMINI.md', False, "this repo's own session instructions"),
    ('MAP.md', False, "this repo's own map"),
    ('WHERE_THINGS_ARE.md', False, "this repo's own index"),
    ('TODO.md', False, "this repo's to-do redirect stub"),
    ('MANIFEST.json', False, "a materialization record: which sources' "
                             "practices were copied into this repo"),
    ('.claude/', False, "this repo's own Claude Code settings and hooks"),
    ('.github/', False, "this repo's own GitHub settings and CI"),
    ('.gitignore', False, "this repo's own ignore list"),
    ('process/', False, "this repo's own process bookkeeping"),
    ('spec/', False, 'plans and designs: how Precedent is built'),
    ('todo/', False, "this repo's open items"),
    ('decisions/', False, "this repo's decision records"),
    ('philosophy/', False, 'the reasoning behind Precedent, for its builders'),
    ('evals/', False, "this repo's evaluations"),
    ('record/', False, "this repo's run records and ledgers"),
    ('gotchas/', False, "traps this repo's own environment hit"),
    ('local/', False, "this repo's own practices, by definition not a "
                      "consumer's"),
    ('bridge/', False, 'the chat bridge, a separate tool this repo builds'),
    ('deck/', False, 'the deck builder, a separate tool this repo builds'),
)


def vendoring_rule(rel):
    """-> (pattern, ships, why) deciding repo-relative path `rel`, or None
    when no rule covers it (undecided)."""
    rel = pathlib.PurePosixPath(pathlib.Path(rel).as_posix()).as_posix()
    for rule in VENDORING_RULES:
        pat = rule[0]
        if rel == pat or (pat.endswith('/') and rel.startswith(pat)):
            return rule
    return None


def _copy_carries_tools(root=None):
    """True while this repo (or `root`) still needs the mirror's tools/:
    until its own tools/ holds a vendored engine that includes checkin.py,
    some of its scripts can only run the mirror's copy. Once it does, tools/
    stays home, so the repo keeps ONE copy of the engine (2026-09-30)."""
    own = pathlib.Path(root or ROOT) / 'tools'
    return not ((own / 'ENGINE_MANIFEST.json').is_file()
                and (own / 'checkin.py').is_file())


def _in_copy(rel, carries_tools=None):
    """True when repo-relative path `rel` belongs in the catalogue copy.
    `carries_tools` answers _copy_carries_tools() for a repo other than
    this one (very_deep_check.py asks it of each consumer it reads).

    A shared set's mirror (CODE_DIRS set by _bind_source) is its declared
    code folders, not universal's catalogue, so VENDORING_RULES do not
    apply to it: only NOT_VENDORED does, as before 2026-09-30, and _files()
    narrows it to CODE_DIRS."""
    rel = pathlib.PurePosixPath(pathlib.Path(rel).as_posix())
    if any(part in NOT_VENDORED for part in rel.parts):
        return False
    if CODE_DIRS is not None:
        if pathlib.Path(rel) in _NOT_VENDORED_ROOT_PATHS:
            return False
        return any(rel.as_posix() == d or rel.as_posix().startswith(d + '/')
                   for d in CODE_DIRS)
    rule = vendoring_rule(rel)
    if rule is None or not rule[1]:
        return False
    if carries_tools is None:
        carries_tools = _copy_carries_tools()
    return rel.parts[0] != 'tools' or carries_tools


def rules_report(since=None):
    """`checkin.py rules [REF]`: print, for each file added since REF (the
    landing branch by default), whether it ships and the rule that says so.
    -> the number of files no rule decides."""
    if since is None:
        try:
            import precedent_branches as _pb
            since = 'origin/' + _pb.landing_branch(str(ROOT))[0]
        except Exception:                                     # noqa: BLE001
            since = 'origin/main'
    r = subprocess.run(['git', '-C', str(ROOT), 'diff', '--name-only',
                        '--diff-filter=A', f'{since}...HEAD'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"checkin rules: could not diff against {since} -- "
              f"{r.stderr.strip()}")
        return 1
    added = [l for l in r.stdout.splitlines() if l.strip()]
    if not added:
        print(f"checkin rules: no file added since {since}.")
        return 0
    try:
        import precedent_vendor_engine as _pve
        engine = set(_pve.CONSUMER_ENGINE_FILES)
    except Exception:                                         # noqa: BLE001
        engine = None
    undecided = practices = 0
    stays = collections.Counter()
    print(f"checkin rules: {len(added)} file(s) added since {since}, and "
          f"whether each ships to consumers:")
    for rel in added:
        rule = vendoring_rule(rel)
        if rule is None:
            undecided += 1
            print(f"  UNDECIDED  {rel} -- no rule covers it: add one to "
                  f"VENDORING_RULES")
        elif rule[1] and rule[0] == 'tools/' and engine is not None:
            # A consumer with its own engine takes tools/ from the engine
            # list, not the copy, so that list is the real decision.
            name = rel[len('tools/'):]
            if name in engine:
                print(f"  SHIPS      {rel} (on CONSUMER_ENGINE_FILES: every "
                      f"consumer's tools/ gets it)")
            else:
                stays['tools/ (not on CONSUMER_ENGINE_FILES)'] += 1
        elif rule[0] == 'practices/':
            practices += 1          # the catalogue: shipping is its purpose
        elif rule[1]:
            print(f"  SHIPS      {rel} ({rule[0]}: {rule[2]})")
        else:
            stays[rule[0]] += 1
    if practices:
        print(f"  ships      {practices} practice file(s): the catalogue, "
              f"which is what the copy is for")
    for pat, n in sorted(stays.items()):
        print(f"  stays      {n} under {pat}")
    print("Judge each SHIPS line: does a consumer run it, instantiate it, or "
          "read it to use Precedent?\n"
          "If not, add a rule saying it stays "
          "(practice: vendor-rollout-disclosed, question 5).")
    return 1 if undecided else 0


def not_vendored_share(base=None):
    """-> (excluded_files, total_files, excluded_bytes) for the tree at `base`.

    Measures rather than recites. `_files()` already applies the exclusion, so
    this counts both ways over the same walk it uses, and the two can never
    disagree.
    """
    base = pathlib.Path(base or ROOT)
    total = excluded = 0
    excluded_bytes = 0
    for p in base.rglob('*'):
        if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts:
            continue
        if p.suffix in ('.pyc', '.pyo'):
            continue
        total += 1
        rel = p.relative_to(base)
        if not _in_copy(rel):
            excluded += 1
            try:
                excluded_bytes += p.stat().st_size
            except OSError:
                pass                          # a race or a broken link: not fatal
    return excluded, total, excluded_bytes


def _files(base):
    # Skip interpreter droppings alongside .git: running the vendored audits
    # leaves __pycache__/ behind (ignored by git on both sides via the
    # baseline .gitignore), and counting them as tree drift made every
    # status/record noisy with files no repo tracks. (Ported from `main`,
    # PR #62, 2026-09-01 -- this branch's own checkin.py had already
    # diverged from main's with its own fixes and never picked this one up;
    # see AGENTS.md's gotchas section on re-checking main for drift before
    # phase 5.)
    files = {p.relative_to(base) for p in base.rglob('*')
             if p.is_file() and '.git' not in p.parts
             and '__pycache__' not in p.parts
             and _in_copy(p.relative_to(base))
             and p.suffix not in ('.pyc', '.pyo')}
    if CODE_DIRS is not None:
        # A shared set's mirror is its declared code directories and nothing
        # else -- never its manifest (a private set's manifest in a consumer's
        # tree is what the leak gate refuses), never its practices -- unless
        # the consumer opted in with `vendor_practices` (see _bind_source).
        files = {f for f in files
                 if any(f.as_posix() == d or f.as_posix().startswith(d + '/')
                        for d in CODE_DIRS)}
    return files


def _diff(clone):
    """(added, modified, deleted) of the vendored tree vs the clone tree."""
    ours, theirs = _files(UPSTREAM), _files(clone)
    added = sorted(ours - theirs)
    deleted = sorted(theirs - ours)
    modified = sorted(p for p in ours & theirs
                      if not filecmp.cmp(UPSTREAM / p, clone / p, shallow=False))
    return added, modified, deleted


def local_changes(clone, recorded):
    """-> sorted [Path] under the vendored tree that differ from the tree at
    `recorded` in `clone` -- added, deleted or changed here since it was
    mirrored -- or None when `recorded` is not in the clone.

    THE ONE ANSWER to "what did this repo change in its mirror?": update()'s
    guard refuses on it, and tools/precedent_local_edits.py resolves and
    sends exactly these files (2026-09-29), so the two can never disagree
    about what counts as a local edit."""
    tar = subprocess.run(['git', '-C', str(clone), 'archive', recorded],
                         capture_output=True)
    if tar.returncode != 0:
        return None
    with tempfile.TemporaryDirectory() as td:
        tarfile.open(fileobj=io.BytesIO(tar.stdout)).extractall(td)
        base = pathlib.Path(td)
        ours, theirs = _files(UPSTREAM), _files(base)
        return sorted(ours ^ theirs) + sorted(
            p for p in ours & theirs
            if not filecmp.cmp(UPSTREAM / p, base / p, shallow=False))


def _manifest():
    # Graceful degradation, not a crash: every caller wants "what does this
    # install record", and a repo with no manifest has a real answer to that
    # -- nothing -- rather than a FileNotFoundError raised from three frames
    # down. A malformed one is different and still fails loudly, because
    # silently treating unreadable JSON as an empty install would let a
    # mirror clobber a tree it could not read the provenance of.
    if not MANIFEST.is_file():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding='utf-8'))
    except ValueError as e:
        sys.exit(f"checkin FAIL: {MANIFEST} is not valid JSON ({e}). Fix it "
                 f"before running anything that mirrors files.")


def _clone_or_die(arg):
    clone = pathlib.Path(arg).resolve()
    if not (clone / '.git').exists():
        sys.exit(f"checkin FAIL: {clone} is not a git clone")
    return clone


def fresh():
    """Session-start staleness notice: automated detection, deliberate take.

    Tells two failure modes apart. A genuinely unreachable remote (offline,
    a slow timeout — no output, no fast error) stays silent, same as
    "nothing has moved" — that was the original behavior and is unchanged.
    But a fast, clean `git ls-remote` failure (non-zero exit — no
    credentials for a private repo in this environment, a 403, "repository
    not found") is a different thing: the check did not run, not that it
    ran and found nothing. The old code treated both the same way (silent),
    which reads a standing credential gap — the same failure, every single
    session, forever in some environments — as "confirmed fresh" in
    perpetuity. (Ported from a fix already made downstream, once, in a
    dependent repo's own wrapper around this same gap — see
    PRACTICE_ENGINE_PLAN.md's evidence table: "checkin.py fresh is silent on
    failure, so unreachable reads as 'current'". Fixing it here, in the
    engine, means every consumer gets it instead of each one re-patching
    its own copy.)
    """
    try:
        up = _manifest().get('upstream', {})
        repo, recorded = up.get('repo'), up.get('commit')
        if not repo or not recorded:
            return 0
        # Ask for the branch this install is PINNED to, not the remote's
        # default. `ls-remote <repo> HEAD` resolves origin/HEAD -- `main` --
        # so on every consumer tracking precedent-beta-v01 this compared the
        # pinned branch's recorded commit against an unrelated lineage and
        # printed "upstream has moved" every single session, forever. It is
        # the most-run instance of the whole family, since tools/bootstrap.sh
        # calls it at session start; spec/MIGRATING_EXISTING_INSTALLS.md's
        # "The default-branch gotcha" describes exactly this, and prescribed
        # recording upstream.branch in the manifest as the workaround. That
        # field is now what the code reads.
        branch = up.get('branch')
        ref = f'refs/heads/{branch}' if branch else 'HEAD'
        try:
            out = subprocess.run(['git', 'ls-remote', repo, ref],
                                 capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            return 0  # genuinely unreachable -- stays silent, unchanged
        head = out.stdout.split()[0] if out.returncode == 0 and out.stdout else ''
        if branch and out.returncode == 0 and not out.stdout.strip():
            # The pin names a branch the remote does not have. Silence here
            # would read as "current" forever, which is the failure this
            # whole function exists to avoid.
            print(f"COULD NOT VERIFY: this install is pinned to upstream "
                  f"branch {branch!r}, which {repo} does not have. Freshness "
                  f"is NOT checked until process/manifest.json's "
                  f"upstream.branch names a branch that exists there.")
            return 0
        if head and not _same_commit(head, recorded):
            print(f"NOTICE: BestPractice upstream has moved ({head[:12]}; your base "
                  f"{recorded[:12]}) — review at the next check-in "
                  f"(process/upstream/INSTALL.md sec.2/sec.4).")
        elif not head and out.returncode != 0:
            err = (out.stderr or '').strip().splitlines()
            err = err[-1] if err else 'no output'
            print(f"COULD NOT VERIFY: couldn't reach BestPractice upstream ({repo}) to check "
                  f"freshness — `git ls-remote` failed ({err}). This is NOT the same as "
                  f"'confirmed fresh': if you need to know, verify directly instead of trusting "
                  f"this silence.")
    except Exception:
        pass
    return 0


def status(clone):
    # A fetch moves remote-tracking refs only; the clone's HEAD, branch and
    # working tree are untouched. Without it, status would compare against
    # whatever origin/<branch> was at the last fetch.
    subprocess.run(['git', '-C', str(clone), 'fetch', 'origin',
                    _tracking_refspec(_tracked_branch(clone))],
                   capture_output=True, text=True)
    ref, head = _landed_commit(clone)
    with tempfile.TemporaryDirectory() as landed_dir:
        added, modified, deleted = _diff(_tree_at(clone, head, landed_dir))
    recorded = _manifest().get('upstream', {}).get('commit')
    for p in added:
        print(f"  A {p}")
    for p in modified:
        print(f"  M {p}")
    for p in deleted:
        print(f"  D {p}")
    n = len(added) + len(modified) + len(deleted)
    print(f"vendored vs {ref} (committed content only): {n} file(s) differ "
          f"({len(added)} added, {len(modified)} modified, {len(deleted)} deleted)")
    print(f"manifest upstream.commit: {recorded}")
    print(f"{ref}:{' ' * max(1, 25 - len(ref))}{head}"
          + ("  (== recorded)" if _same_commit(head, recorded)
             else "  (!= recorded)"))
    return 1 if n else 0


def _stamp_synced_from(commit):
    """Record which upstream commit the vendored tree was last mirrored from.

    Distinct from upstream.commit, which record() writes only after verifying
    the vendored tree is byte-identical to what actually landed upstream. That
    invariant is deliberate and untouched; this field answers a different
    question -- "is the vendored tree current with upstream?" -- which push()
    needs and which upstream.commit cannot answer during the normal cycle,
    because it legitimately lags from update() until the merge is recorded.
    """
    # MANIFEST, never a hard-coded process/manifest.json: with --source the
    # stamp belongs to that set's own manifest. The hard-coded path wrote a
    # shared set's commit into the universal manifest's synced_from, which
    # then named a commit the universal upstream does not have (2026-09-29).
    path = MANIFEST
    m = json.loads(path.read_text(encoding='utf-8'))
    m.setdefault('upstream', {})['synced_from'] = commit
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n",
                    encoding='utf-8')


def _declared_base_branch(root):
    """The branch a repo DECLARES its work is measured against, in its own
    precedent.json `base_branch` -- not inferred from `origin/HEAD`.

    Those are two different questions with usually the same answer, which is
    why asking the wrong one survives so long. `origin/HEAD` answers "what
    does GitHub show first"; callers mean "what lineage does this work
    belong to". Returns None when undeclared or unreadable, so callers fall
    back to the old inference rather than breaking (fail-gracefully).
    Enforced by precedent_check.py's `declared-base-branch`.
    """
    try:
        import json as _json, pathlib as _pathlib
        v = _json.loads((_pathlib.Path(root) / 'precedent.json')
                        .read_text(encoding='utf-8')).get('base_branch')
        return v if isinstance(v, str) and v.strip() else None
    except Exception:
        return None


def _default_branch(clone):
    # Everything after the remote's name, not after the last slash: a
    # default branch can carry slashes of its own, and `origin/claude/x`
    # read as `x` named a branch that does not exist (2026-09-28).
    ref = _git(clone, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD')
    return (ref.split('/', 1)[1] if '/' in ref else ref) or 'main'


def _followed_branch():
    """The branch every install follows (precedent_vendor_engine.SOURCE_BRANCH),
    or 'main' where that module is not beside this one -- an old vendored
    tree, or a fixture that copies this file alone."""
    try:
        import precedent_vendor_engine
        return precedent_vendor_engine.SOURCE_BRANCH
    except Exception:                                          # noqa: BLE001
        return 'main'


def _tree_at(clone, ref, into):
    """Extract `clone`'s tree at `ref` into `into`, without touching `clone`.

    `git archive` reads objects and writes a tar; it never moves HEAD, never
    changes a branch, and never touches a working tree. update() used to
    reach its source the other way -- `git checkout <branch>` followed by
    `git pull` INSIDE the caller's clone -- which is a mutation of a
    repository the caller passed only as a SOURCE.

    2026-09-06, found by being on the receiving end of it: a session running
    `checkin.py update <bestpractice-clone>` from a consumer repo had its
    BestPractice checkout silently moved off `precedent-beta-v01` onto
    `main`, mid-session, and only noticed because a file it expected was
    suddenly missing. The command had already FAILED its own guard by then,
    so the mutation was pure collateral. On a dirty tree the checkout would
    have failed instead and left the pull half-applied.

    Its sibling precedent_vendor_engine.py makes exactly the opposite
    guarantee in as many words -- "it reads blobs, it never checks the clone
    out" -- and verify_harness.py asserts it. This one now does the same.
    """
    tar = subprocess.run(['git', '-C', str(clone), 'archive', ref],
                         capture_output=True)
    if tar.returncode != 0:
        sys.exit(f"checkin FAIL: cannot read {ref!r} in {clone} "
                 f"({tar.stderr.decode('utf-8', 'replace').strip()}). Fetch it "
                 f"there first -- this tool will not check the clone out.")
    tarfile.open(fileobj=io.BytesIO(tar.stdout)).extractall(into)
    return pathlib.Path(into)


def _tracked_branch(clone):
    """The branch this install actually tracks, which is NOT always the
    clone's default branch.

    The manifest records `upstream.branch` precisely because the two can
    differ -- every consumer of BestPractice tracks `precedent-beta-v01`
    today while `main` is still the configured default. update() read
    `_default_branch(clone)` and would have mirrored `main` over a tree
    vendored from the beta branch: a silent, wholesale revert dressed as an
    update. Same assumption AGENTS.md's own standing rule warns about in the
    merge direction -- never assume `main` just because it is the default.
    """
    recorded = (_manifest().get('upstream', {}) or {}).get('branch')
    return recorded or _default_branch(clone)


def _tracking_refspec(branch):
    """Fetch `branch` into origin/<branch> explicitly. A single-branch clone
    (`git clone --branch X --depth 1`) is configured to track X alone, so a
    bare `fetch origin <branch>` there writes only FETCH_HEAD and every
    origin/<branch> lookup after it finds nothing (2026-09-28, a consumer's
    update against a clone taken at precedent-beta-v01)."""
    return f'+refs/heads/{branch}:refs/remotes/origin/{branch}'


def _landed_commit(clone):
    """-> (ref, commit): what is COMMITTED on the branch this install is
    pinned to -- `origin/<branch>`, or the local branch when the clone has no
    remote-tracking copy of it. record() and status() compare against the
    tree at this commit, extracted by _tree_at(), and never against the
    clone's working tree.

    The working tree is not upstream content. A SessionStart hook writes
    per-machine, gitignored files into every clone it runs in --
    commit-identity.sh's `.claude/settings.local.json` (the person's TZ),
    precedent_session_practices.py's `.precedent/` -- and _files() walked
    the folder, so each one read as "the clone has a file the vendored tree
    lacks" and record refused. 2026-09-27, a real consumer's Update Vendors:
    the session deleted the file and re-recorded, and the next session start
    wrote it straight back. Reading the committed tree answers the question
    record is actually asking -- does the vendored tree match what landed
    upstream -- for every ignored or uncommitted file, present and future.
    update() has read its source this way since 2026-09-06.
    """
    branch = _tracked_branch(clone)
    for ref in (f'origin/{branch}', branch):
        commit = _rev_parse_quiet(clone, ref)
        if commit:
            return ref, commit
    sys.exit(f"checkin FAIL: {clone} has no {branch} or origin/{branch} to "
             f"compare against. This install records upstream.branch = "
             f"{branch!r}; fetch that branch in the clone first.")


def _pinned_branch_hold(clone, allow=False):
    """Refuse `update` while this install is pinned to a non-default branch.

    spec/MIGRATING_EXISTING_INSTALLS.md's "The default-branch gotcha" has
    said, since 2026-09-06, in as many words: *"Do the vendor as a one-off
    manual mirror ... not `checkin.py update`."* Until now nothing enforced
    it. The document mandated a procedure and the tool cheerfully did the
    thing the document forbade -- exactly the advisory-only state
    checkable-gets-checked exists to end, and the reason a session on
    2026-09-07 had to reason its way to the manual mirror from a paragraph
    instead of being stopped by a guard.

    THE CONDITION IS THE HOLD'S OWN CONDITION, so this retires itself. The
    hold applies "while a non-default branch is pinned"; this fires exactly
    when the manifest's `upstream.branch` differs from the clone's default.
    When precedent-beta-v01 merges to main and each consumer's manifest is
    repointed, pinned == default and the guard stops firing on its own --
    nobody has to remember to delete it, which is how a temporary guard
    usually outlives its reason.

    WHAT IT CANNOT REACH, and this is the important limit: a consumer still
    carrying a PRE-FIX vendored copy of this file. That copy has no guard,
    resolves the remote's default branch unconditionally, and would mirror
    `main` over a beta-vendored tree -- a silent wholesale revert. A guard
    shipped inside the tree it guards is missing from precisely the copies
    that need it, the same shape as the freshness-guard incident in
    AGENTS.md's gotchas. Such a consumer is only covered after one manual
    mirror brings this file in; the manual mirror is therefore still the
    entry point, not an alternative to it.

    An unknown default branch REFUSES rather than proceeding. The asymmetry
    is the hold's own, recorded by Morgan 2026-09-06: guessing wrong here
    costs a silent overwrite of a repo's practices, and refusing wrongly
    costs one manual mirror.

    THE OVERRIDE HAS TWO SPELLINGS, and the CLI one is the one to reach for
    first. `--allow-pinned` and `PRECEDENT_ALLOW_PINNED_UPDATE=1` do the
    same thing; the flag exists because the env var alone doesn't. Reproduced
    2026-09-17 from a real pinned-branch consumer: Claude Code Web's own
    permission classifier refused the env-var form outright, before
    checkin.py ever ran -- the name matches the shape it looks for ("ALLOW"
    overriding a hold) closely enough to read as a safety-bypass flag to the
    harness, not just to this tool. Every pinned-branch consumer running
    under it hit that same refusal on every Update Vendors pass. The env var
    still works for scripts and other harnesses that don't classify it that
    way; the flag is what a session running under a classifier like that
    should type instead.
    """
    if allow or os.environ.get('PRECEDENT_ALLOW_PINNED_UPDATE') == '1':
        return
    pinned = (_manifest().get('upstream', {}) or {}).get('branch')
    if not pinned:
        return
    # The branch every install follows is never a pin to hold, whatever a
    # clone's origin/HEAD says: a clone whose default is some working branch
    # held a correctly pointed install (2026-09-28).
    if pinned == _followed_branch():
        return
    default = _default_branch(clone)
    if default and pinned == default:
        return
    named = f"the clone's default branch ({default})" if default else         "this clone's default branch, which could not be determined"
    sys.exit(
        f"checkin FAIL: this install is PINNED to {pinned!r}, which is not "
        f"{named}.\n"
        f"  spec/MIGRATING_EXISTING_INSTALLS.md's \"The default-branch "
        f"gotcha\" holds `checkin.py update` while a non-default branch is "
        f"pinned: vendor as a one-off manual mirror instead -- replace the "
        f"vendored tree wholesale from a checkout of {pinned!r} -- and leave "
        f"the sync workflow on `workflow_dispatch` only. Its `schedule:` "
        f"block is gone for good since 2026-09-14, not paused pending this "
        f"hold: nothing schedules a vendor update any more, so lifting the "
        f"hold does not bring a clock back.\n"
        f"  The hold lifts when {pinned!r} merges into the default branch and "
        f"this repo's process/manifest.json is repointed there; this guard "
        f"then stops firing by itself.\n"
        f"  Deliberate override, for one run: "
        f"checkin.py update ... --allow-pinned (or, if you're not running "
        f"under a harness that flags the env var as a bypass: "
        f"PRECEDENT_ALLOW_PINNED_UPDATE=1 checkin.py update ...)")


def _report_excluded_content():
    """Print what is sitting under a NOT_VENDORED path in the vendored tree,
    every `update` run, whether or not anything else changed this hop.

    Never deletes anything -- this is the mechanism fix for the failure
    that motivated it: `_files()`'s NOT_VENDORED filter already stops
    comparing an excluded path going forward, but a path excluded AFTER a
    tree was already vendored just sits there, invisible to every later
    `update`, because nothing ever looked at it again. That is exactly what
    happened to philosophy/ and evals/ in a real consumer repo -- vendored
    2026-09-12, excluded 2026-09-14, still sitting there three days later
    with nothing pointing at them, until an unrelated check (record()'s
    _carry_check, which walks the tree unfiltered) flagged 52 real lines as
    "lost" and nearly had them discarded by an --accept-loss call before a
    human caught it.
    (practice: durable-fix -- this is the mechanism fix, not the one-time
    manual cleanup a consumer's own re-vendor would otherwise have to
    remember to do.)

    Deliberately NOT auto-delete: NOT_VENDORED is a per-repo judgment call
    about what is operational, and it has already been wrong once on a real
    consumer (gotchas/ was drafted for exclusion, then confirmed to still be
    load-bearing -- see the comment on NOT_VENDORED itself). Pairing a
    fallible judgment call with automatic, silent deletion across every
    consumer on every run is a worse failure mode than the stale-content
    problem this closes: a wrong exclusion would DESTROY content instead of
    merely ignoring it. Reporting loudly and leaving removal to a human
    keeps the fix reversible. tools/very_deep_check.py's matching finding
    is the audit-time half of the same signal, for a consumer that never
    happens to run `update` again.
    """
    if not UPSTREAM.is_dir():
        return
    hits = {}
    for p in UPSTREAM.rglob('*'):
        if not p.is_file() or '.git' in p.parts:
            continue
        rel = p.relative_to(UPSTREAM)
        excluded = [part for part in rel.parts if part in NOT_VENDORED]
        if not excluded and rel in _NOT_VENDORED_ROOT_PATHS:
            excluded = [str(rel)]
        if excluded:
            hits[excluded[0]] = hits.get(excluded[0], 0) + 1
    if not hits:
        return
    names = ', '.join(sorted(hits))
    total = sum(hits.values())
    rm = ' '.join(f'process/upstream/{n}' for n in sorted(hits))
    print(f"checkin update: {total} stale file(s) under excluded path(s) still in "
          f"the vendored tree: {names} (excluded from vendoring, so no longer "
          f"compared or refreshed -- present because they were vendored before "
          f"being excluded, or copied in by hand). Not removed automatically: "
          f"confirm nothing there is still needed, then  git rm -r {rm}  and commit.")


def update(clone, force=False, allow_pinned=False):
    """INSTALL.md §2 step 5: mirror the clone's tree at the branch this
    install tracks into the vendored tree, refusing to clobber unexported
    local work. Reads the clone; never checks it out, pulls in it, or moves
    its HEAD."""
    _pinned_branch_hold(clone, allow=allow_pinned)
    branch = _tracked_branch(clone)
    # Fetch updates remote-tracking refs only -- it does not touch the
    # clone's working tree, HEAD, or any local branch.
    fetched = subprocess.run(['git', '-C', str(clone), 'fetch', 'origin',
                              _tracking_refspec(branch)],
                             capture_output=True, text=True)
    if fetched.returncode != 0:
        print(f"NOTICE: could not fetch origin/{branch} in {clone} "
              f"({fetched.stderr.strip()}) -- mirroring whatever that clone "
              f"already has for {branch}, which may be behind.")
    src_ref = _rev_parse_quiet(clone, f'origin/{branch}') or \
        _rev_parse_quiet(clone, branch)
    if not src_ref:
        sys.exit(f"checkin FAIL: {clone} has no {branch} or origin/{branch} to "
                 f"mirror from. This install records upstream.branch = "
                 f"{branch!r}; fetch that branch in the clone first.")
    if not force:
        recorded = _manifest().get('upstream', {}).get('commit')
        if not recorded:
            sys.exit("checkin FAIL: no upstream.commit recorded in the manifest — "
                     "cannot tell local work from upstream drift; pass --force to mirror anyway")
        drift = local_changes(clone, recorded)
        if drift is None:
            sys.exit(f"checkin FAIL: recorded commit {recorded[:12]} not found in the clone — "
                     f"fetch it there, or pass --force")
        if drift:
            for p in drift:
                print(f"  local change: {p}")
            sys.exit("checkin FAIL: vendored tree differs from the recorded upstream commit — "
                     "that is unexported work the mirror would clobber. Update Vendors "
                     "(tools/precedent_update.py, run from the BestPractice clone) resolves "
                     "each committed change itself -- keeps it, merges it, or takes "
                     "upstream's version and says so -- and "
                     "tools/precedent_local_edits.py send carries one upstream. Or pass "
                     "--force to overwrite -- but only after reviewing each file above.")
    # Mirrored from the SOURCE REF's tree, extracted to a scratch directory --
    # not from the clone's working tree, which this tool no longer moves and
    # which may sit on some entirely different branch.
    with tempfile.TemporaryDirectory() as srcdir:
        src = _tree_at(clone, src_ref, srcdir)
        dropped, kept = _drop_what_the_copy_no_longer_carries(clone, src)
        vendored_only, differing, src_only = _diff(src)
        if not (vendored_only or differing or src_only):
            if dropped:
                _stamp_synced_from(src_ref)
                print(f"checkin update OK: removed {len(dropped)} file(s) the "
                      f"copy no longer carries ({branch} @ {src_ref[:12]}); "
                      f"nothing else to mirror.")
                _report_excluded_content()
                return 0
            _stamp_synced_from(src_ref)
            print(f"checkin update: vendored tree already identical to "
                  f"{branch} @ {src_ref[:12]} — nothing to do.")
            _report_excluded_content()
            return 0
        for p in vendored_only:
            (UPSTREAM / p).unlink()
        for p in differing + src_only:
            (UPSTREAM / p).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / p, UPSTREAM / p)
    _stamp_synced_from(src_ref)
    print(f"checkin update OK: mirrored {len(differing) + len(src_only)} file(s), "
          f"deleted {len(vendored_only)} from the vendored tree ({branch} @ "
          f"{src_ref[:12]})")
    print("next: propagate template changes into instantiated files (INSTALL.md §2),")
    print("      update manifest entries, then run:  checkin.py record " + str(clone))
    _report_excluded_content()
    return 0


def _drop_what_the_copy_no_longer_carries(clone, src):
    """Remove each file under the vendored tree that the copy no longer
    carries (_in_copy), when it is byte-identical to upstream's copy -- the
    tree being mirrored now, or the one recorded last time. -> (dropped,
    kept), repo-relative. A file that differs from both holds this repo's
    own edit, so it is left where it is and named (practice:
    repair-cannot-discard-work); git history keeps every removed one.

    WHY (2026-09-30). The copy became an allowlist, and once a consumer's
    own engine carries checkin.py its tools/ stays home too. _diff() reads
    both sides through _in_copy, so a file the copy stopped carrying is
    invisible to it and would never be deleted: process/upstream/tools/,
    gotchas/, local/ and the rest would sit there as stale second copies
    forever -- the thing this change exists to end."""
    if not UPSTREAM.is_dir():
        return [], []
    recorded = _manifest().get('upstream', {}).get('commit')
    stale = sorted(p for p in UPSTREAM.rglob('*')
                   if p.is_file() and '.git' not in p.parts
                   and '__pycache__' not in p.parts
                   and p.suffix not in ('.pyc', '.pyo')
                   and not _in_copy(p.relative_to(UPSTREAM)))
    if not stale:
        return [], []
    dropped, kept = [], []
    with tempfile.TemporaryDirectory() as td:
        base = None
        if recorded:
            tar = subprocess.run(['git', '-C', str(clone), 'archive', recorded],
                                 capture_output=True)
            if tar.returncode == 0:
                tarfile.open(fileobj=io.BytesIO(tar.stdout)).extractall(td)
                base = pathlib.Path(td)
        for p in stale:
            rel = p.relative_to(UPSTREAM)
            same = any(t is not None and (t / rel).is_file()
                       and filecmp.cmp(p, t / rel, shallow=False)
                       for t in (src, base))
            if same:
                p.unlink()
                dropped.append(rel)
            else:
                kept.append(rel)
    for d in sorted({p.parent for p in stale}, key=lambda d: -len(d.parts)):
        try:
            d.rmdir()             # only when now empty
        except OSError:
            pass
    if dropped:
        print(f"checkin update: removed {len(dropped)} file(s) the copy no "
              f"longer carries (it holds what a consumer uses since "
              f"2026-09-30, and this repo's own tools/ now holds the engine); "
              f"each was upstream's text, unchanged here.")
    for rel in kept:
        print(f"NOTICE: {UPSTREAM.relative_to(ROOT) / rel} is no longer part "
              f"of the copy, but differs from upstream's -- a local edit, "
              f"left where it is. Carry what it holds somewhere this repo "
              f"owns, then delete it.")
    return dropped, kept


def push(clone, why='', force=False):
    """Send this repo's committed changes to its mirror upstream, as a branch
    in `clone`: tools/precedent_local_edits.py send merges each changed file
    three ways onto upstream's landing branch, so nothing upstream changed
    since the mirror is reverted, scrubs it on this repo's side and on
    upstream's, commits and pushes the branch, and prints the prompt for the
    session that will land it. It never opens a pull request or merges.

    Until 2026-09-29 this copied the whole vendored tree into the clone's
    working tree and stopped there -- no branch, no commit, no merge -- and,
    run with --repo from the source clone, its scrub ran the SOURCE clone's
    practice_audit.py, which found no process/ there and passed as NOT
    APPLICABLE. One tool now owns sending
    (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md). --force is accepted and
    changes nothing on this path: what it overrode was a guard against
    reverting upstream work, which a three-way merge cannot do.

    A shared set's code tree (--source) is outside that plan's first version,
    so it keeps the old mirror below, with its scrub read from this repo."""
    if CODE_DIRS is None:
        sys.path.insert(0, str(HERE.parent))
        try:
            import precedent_local_edits
        except ImportError:
            sys.exit(f"checkin FAIL: push hands its work to "
                     f"precedent_local_edits.py, which is not beside this copy "
                     f"in {HERE.parent}. Run the BestPractice clone's own: "
                     f"python3 ../BestPractice/tools/precedent_local_edits.py "
                     f"send --repo . --why \"...\"")
        return precedent_local_edits.send(ROOT, why, owner=clone,
                                          layers=(precedent_local_edits.CATALOGUE,))
    return _mirror_push(clone, force)


def _mirror_push(clone, force=False):
    # Guard 1: the vendored tree must be CURRENT with upstream. This mirror
    # DELETES any file the vendored tree lacks, so pushing from a tree that is
    # behind silently reverts whatever upstream gained. Symmetric to update()'s
    # guard: that one refuses to clobber unexported LOCAL work, this one
    # refuses to clobber unimported UPSTREAM work.
    #
    # Origin (2026-08-12): a session's vendored tree was behind by two upstream
    # merges; a plain push would have reverted two practices, and it was caught
    # only by a human reading `status` output. In the same session the *other*
    # direction then bit as well -- an `update --force`, passed specifically to
    # bypass update()'s guard, silently reverted three unexported additions
    # including this function. Both directions of this mirror destroy work;
    # both now warn, and --force means what it says.
    if not force:
        up = _manifest().get('upstream', {})
        # synced_from is what update() mirrored; fall back to commit for a
        # manifest written before that field existed.
        base = up.get('synced_from') or up.get('commit')
        # The branch this install is PINNED to, not the clone's configured
        # default. Same bug update() carried: every consumer tracks
        # precedent-beta-v01 while main is still BestPractice's default, so
        # this guard was comparing the vendored tree's base against the wrong
        # branch's head entirely -- refusing or allowing a push on evidence
        # about a branch the install does not follow.
        branch = _tracked_branch(clone)
        _git(clone, 'fetch', 'origin', _tracking_refspec(branch))
        head = _rev_parse_quiet(clone, f'origin/{branch}')
        if head is None:
            sys.exit(f"checkin FAIL: {clone} has no origin/{branch} to compare "
                     f"against. This install records upstream.branch = "
                     f"{branch!r}; fetch that branch in the clone first.")
        if base and head != base:
            sys.exit(
                f"checkin FAIL: upstream origin/{branch} is at {head[:12]} but "
                f"the vendored tree was last mirrored from {base[:12]} — it is "
                "behind, and this mirror DELETES files it does not have, so it "
                "would revert upstream work. Run `checkin.py update` first (it "
                "refuses if that would clobber unexported local work — export "
                "that, or `update --force` and RE-APPLY your additions on top, "
                "keeping a copy first), then push. `--force` overrides if you "
                "are certain the vendored tree is the intended upstream state.")

    # Guard 2: the scrub gates every export of content toward the public repo.
    # This repo's own copy, so the scrub reads this repo: practice_audit.py
    # finds its root from where it sits, and the source clone's copy, run
    # under --repo, audited the source clone instead (2026-09-29).
    audit = next((a for a in (UPSTREAM / 'tools' / 'practice_audit.py',
                              HERE.parent / 'practice_audit.py') if a.is_file()),
                 HERE.parent / 'practice_audit.py')
    if subprocess.run([sys.executable, str(audit)], cwd=str(ROOT)).returncode != 0:
        sys.exit("checkin FAIL: practice_audit (scrub) failed — nothing was copied")
    added, modified, deleted = _diff(clone)
    # Delete only what git tracks in the clone (practice:
    # repair-cannot-discard-work). An untracked or gitignored file there is
    # not upstream content -- a per-machine `.claude/settings.local.json`, a
    # session's `.precedent/`, a person's uncommitted work -- and the mirror
    # used to unlink every one of them as "not in the vendored tree". A
    # failed ls-files leaves `tracked` empty, which deletes nothing.
    rc, listed = _git_rc(clone, 'ls-files', '-z')
    tracked = set(listed.split('\0')) if rc == 0 else set()
    untracked = [p for p in deleted if p.as_posix() not in tracked]
    deleted = [p for p in deleted if p.as_posix() in tracked]
    if untracked:
        print(f"checkin push: left {len(untracked)} file(s) git does not track "
              f"in {clone} alone: "
              + ', '.join(p.as_posix() for p in untracked[:5])
              + (' ...' if len(untracked) > 5 else ''))
    if not (added or modified or deleted):
        print("checkin push: vendored tree and clone already identical — nothing to do.")
        return 0
    for p in deleted:
        (clone / p).unlink()
    for p in added + modified:
        (clone / p).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(UPSTREAM / p, clone / p)
    print(f"checkin push OK: mirrored {len(added) + len(modified)} file(s), "
          f"deleted {len(deleted)} into {clone}")
    print("next: commit there on a branch, open the PR (review = second scrub line),")
    print("      merge, pull the default branch, then run:  checkin.py record " + str(clone))
    return 0



def _dep_git(*args):
    return subprocess.run(['git', '-C', str(ROOT)] + list(args),
                          capture_output=True, text=True).stdout


def _git_rc(cwd, *args):
    """-> (returncode, stdout). The exit-code-aware sibling of _git/_dep_git.

    Both of those return `.stdout` and drop the exit code, which is fine
    where a command cannot meaningfully fail and catastrophic where it can.
    `git show <commit>:<path>` is the catastrophic case: it exits 128 with
    EMPTY STDOUT for two entirely different situations, and reading stdout
    alone cannot tell them apart --

      * the commit is not in this clone (a --depth 1 checkout, which is what
        every mid-session `add_repo` hands you), and
      * the path did not exist at that commit (a genuinely new file).

    The first is unanswerable; the second means every line is new. Treating
    the first as the second is what made _carry_check report a whole
    vendored tree as LOST. (AGENTS.md's gotchas carry three separate
    instances of this exact shape.)
    """
    r = subprocess.run(['git', '-C', str(cwd), *args],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def _base_is_present(clone, base):
    """-> True when `base` is a commit object this clone actually holds."""
    return _git_rc(clone, 'cat-file', '-e', f'{base}^{{commit}}')[0] == 0


def _committed_tree_bases(clone, base, dep_ref):
    """-> every upstream commit the vendored tree committed on `dep_ref`
    could have been mirrored from: `base` (the working manifest's
    upstream.commit) plus the `synced_from` and `commit` the manifest
    committed on that same ref records. Each one is checked present in the
    clone, deepening once, for the same reason `base` is; a committed stamp
    that still is not there is named and left out, never guessed at."""
    rel = MANIFEST.relative_to(ROOT).as_posix()
    rc, text = _git_rc(ROOT, 'show', f'{dep_ref}:{rel}')
    stamps = []
    if rc == 0:
        try:
            up = json.loads(text).get('upstream', {})
            stamps = [up.get('synced_from'), up.get('commit')]
        except ValueError:
            pass
    bases = [base]
    for s in stamps:
        if not isinstance(s, str) or not s.strip() or any(_same_commit(s, b) for b in bases):
            continue
        if not _base_is_present(clone, s):
            subprocess.run(['git', '-C', str(clone), 'fetch', '--depth=1000', 'origin',
                            _tracked_branch(clone)], capture_output=True, text=True)
        if _base_is_present(clone, s):
            bases.append(s)
        else:
            print(f"NOTICE: carry check: {dep_ref}'s committed {rel} records upstream "
                  f"{s[:12]}, which is not in {clone} even after deepening -- lines "
                  f"upstream changed since then may be reported as lost; each one is "
                  f"still checked against upstream's own deletions.")
    return bases


def _upstream_deleted_lines(clone, bases, rel, tip='HEAD'):
    """-> every line an upstream commit between any of `bases` and `tip`
    (the landed commit record() compares against) removed from `rel`. A line
    in that set that the committed tree has and the landed tree lacks is
    upstream's own deletion."""
    out = set()
    for b in bases:
        rc, log = _git_rc(clone, 'log', '-p', '--format=', '--no-renames',
                          f'{b}..{tip}', '--', rel)
        if rc != 0:
            continue
        out.update(l[1:] for l in log.splitlines()
                   if l.startswith('-') and not l.startswith('---'))
    return out


def _upstream_ever_wrote(clone, rel, tip='HEAD'):
    """-> every line any upstream version of `rel` up to `tip` carried: the
    lines each commit in its history added. A shallow clone's boundary
    commit shows its whole file as added, so the oldest version the clone
    holds counts too."""
    rc, log = _git_rc(clone, 'log', '-p', '--format=', '--no-renames', tip, '--', rel)
    if rc != 0:
        return set()
    return {l[1:] for l in log.splitlines()
            if l.startswith('+') and not l.startswith('+++')}


def _carry_check(clone, accept_loss, landed_root=None, tip='HEAD', resolving=()):
    """No pending vendored addition may vanish across a check-in cycle.

    The failure this kills (2026-08-19, real): the vendored tree carried
    other threads' committed additions; a sync session hand-merged upstream's
    copy over them, push mirrored the lossy result, and record's
    tree-identical verification then STAMPED the loss as the new truth --
    detection was luck (the erased thread's session happened to be open).
    The carry-all-pending rule (INSTALL sec.4 step 1) states the obligation;
    this check enforces it at the chokepoint every cycle must pass through.

    Mechanism: every line ADDED in the dependent repo's committed default-
    branch vendored tree relative to the recorded base must be present in
    the landed upstream tree (same file, or anywhere in the tree to tolerate
    moves). A deliberate removal needs --accept-loss, which prints exactly
    what is being let go.

    THE BASE COMMIT MUST BE PRESENT FIRST, and that precondition is the
    whole difference between this check and a random-number generator. Read
    `_git_rc`'s docstring for why: without it, a clone that simply does not
    contain the recorded base reports EVERY line of the vendored tree as
    lost. Measured 2026-09-08 on a real consumer repo -- 69 "LOST" lines,
    all false, disprovable only by extracting both trees and diffing them by
    hand. That manual verification is the half a session skips, and the
    tempting shortcut is `--accept-loss`, which would accept a loss nobody
    measured -- turning the guard against silent data loss into its cause.

    UPSTREAM'S OWN DELETIONS ARE NEVER A LOSS, and two things make sure of
    it (2026-09-26, a real consumer: 301 "LOST" lines, every one a line
    BestPractice had deleted itself). The committed tree is read from the
    dependent's base branch, and under the branch tiers that branch takes
    work by Promote, later -- so it routinely holds an OLDER sync than the
    manifest names, and a hand-written `upstream.commit` widens the gap.
    Diffing it against the manifest's commit alone made every line upstream
    changed in between look local, and every one upstream deleted look lost.
    So: (1) a line is pending only if it is absent from the upstream tree at
    EVERY commit the committed tree could have come from -- the working
    manifest's commit and the committed manifest's own `synced_from` and
    `commit`, read off the same ref; and (2) a line still missing after that
    which an upstream commit between one of those and the landed HEAD
    deleted is reported as upstream's deletion and not counted. A line
    upstream never wrote still fails the check, exactly as before.

    (3) A LINE ANY EARLIER UPSTREAM VERSION OF THE FILE CARRIED IS
    UPSTREAM'S TOO (2026-09-30, a real consumer: 75 vendored files
    byte-identical to upstream versions OLDER than every stamp, because
    earlier syncs never refreshed them). No stamp reaches back to those
    versions, so (1) and (2) cannot see them; the file's own history can.
    Recording with --accept-loss did not end it either: the next run reads
    the base branch again, which does not hold the sync yet.

    THE LANDED SIDE IS READ FROM `landed_root`, the committed tree record()
    extracted at `tip`, never from the clone's working tree -- for the same
    reason record()'s tree comparison is (see _landed_commit). With neither
    given it falls back to the clone's working tree and HEAD, which only a
    direct caller that has no landed commit to name should rely on.
    """
    landed_root = pathlib.Path(landed_root) if landed_root else clone
    base = _manifest().get('upstream', {}).get('commit')
    if not base:
        return
    # A file Update Vendors is resolving is not a loss either way: its local
    # lines are kept, merged, or replaced by upstream's with the commit that
    # holds them named (tools/precedent_local_edits.py, 2026-09-29). Only
    # those files are skipped, and the count is said.
    resolving = set(resolving)
    if resolving:
        print(f"carry check: {len(resolving)} file(s) skipped -- Update Vendors "
              f"resolves each of this repo's local edits itself and reports it")
    _dep_git('fetch', 'origin')

    # -- the precondition, before a single line is compared ---------------
    if not _base_is_present(clone, base):
        # One bounded deepen, then re-ask. Bounded rather than --unshallow:
        # some git policy hooks refuse that outright, and a fetch that is
        # refused leaves the clone exactly as shallow as before.
        branch = _tracked_branch(clone)
        subprocess.run(['git', '-C', str(clone), 'fetch', '--depth=1000',
                        'origin', branch], capture_output=True, text=True)
    if not _base_is_present(clone, base):
        sys.exit(
            f"checkin FAIL: the carry check cannot run -- the recorded base "
            f"commit {base[:12]} is not in this clone of the upstream repo, "
            f"even after deepening it.\n"
            f"  This is NOT a report of lost content and --accept-loss does "
            f"not apply: accepting a loss nobody measured is how the guard "
            f"becomes the failure.\n"
            f"  Deepen the clone and run again:\n"
            f"    git -C {clone} fetch --depth=5000 origin\n"
            f"  If the base commit genuinely no longer exists upstream "
            f"(a rewritten history), re-record against a base that does.")

    # The DEPENDENT repo's own declared base branch first. Inferring it was
    # wrong twice over. `origin/HEAD` is unset on a great many clones --
    # every repo attached mid-session gets a --depth 1 --single-branch clone
    # without it, reproduced on a real consumer 2026-09-06 -- and the
    # fallback then named `origin/master`, a ref GitHub has not created by
    # default since 2020 and which does not exist in any consumer here. With
    # neither resolving, `ls-tree origin/master` errors, `names` comes back
    # EMPTY, and this loop inspects nothing and returns clean: a silent pass
    # from the one guard standing between a check-in cycle and the 2026-08-19
    # data loss this function's own docstring describes. A declared value
    # cannot go missing this way, and the inference fallback now at least
    # names a branch that exists.
    dep_branch = (_declared_base_branch(ROOT)
                  or _dep_git('symbolic-ref', '--short',
                              'refs/remotes/origin/HEAD').strip().rsplit('/', 1)[-1]
                  or 'main')
    prefix = UPSTREAM.relative_to(ROOT).as_posix()
    bases = _committed_tree_bases(clone, base, f'origin/{dep_branch}')
    names = _dep_git('ls-tree', '-r', '--name-only', f'origin/{dep_branch}', prefix).split()
    landed_all = None
    lost = []
    upstream_deleted = upstream_older = 0
    for name in names:
        rel = name[len(prefix) + 1:]
        if rel in resolving:
            continue
        committed = _dep_git('show', f'origin/{dep_branch}:{name}')
        # rc is now consulted, and it can only mean one thing: every base
        # is present (asserted above and in _committed_tree_bases), so a
        # non-zero exit here says this path did not exist at that base -- a
        # genuinely new file there, every line of which really is pending.
        from_upstream = set()
        for b in bases:
            rc, base_txt = _git_rc(clone, 'show', f'{b}:{rel}')
            if rc == 0:
                from_upstream.update(base_txt.splitlines())
        pending = set(committed.splitlines()) - from_upstream
        pending = {l for l in pending if len(l.strip()) > 3}
        if not pending:
            continue
        landed = (landed_root / rel).read_text(encoding='utf-8', errors='replace') \
            if (landed_root / rel).exists() else ''
        missing = {l for l in pending if l not in landed.splitlines()}
        if missing:
            if landed_all is None:
                landed_all = '\n'.join((landed_root / f).read_text(encoding='utf-8', errors='replace')
                                        for f in _files(landed_root) if (landed_root / f).suffix
                                        in ('.md', '.py', '.sh', '.json', '.yml', '.template'))
            missing = {l for l in missing if l not in landed_all}
        if missing:
            deleted_upstream = _upstream_deleted_lines(clone, bases, rel, tip)
            upstream_deleted += len(missing & deleted_upstream)
            missing -= deleted_upstream
        if missing:
            older = missing & _upstream_ever_wrote(clone, rel, tip)
            upstream_older += len(older)
            missing -= older
        if missing:
            lost.append((rel, sorted(missing)))
    if upstream_deleted:
        print(f"carry check: {upstream_deleted} line(s) the committed tree has and the "
              f"landed tree lacks were deleted by upstream itself (git log between "
              f"{', '.join(b[:12] for b in bases)} and the clone's HEAD) -- upstream's "
              f"own deletions, not a loss; not counted.")
    if upstream_older:
        print(f"carry check: {upstream_older} line(s) the committed tree has and the "
              f"landed tree lacks are in an earlier upstream version of the same file "
              f"-- a copy earlier syncs never refreshed, not local work; not counted.")
    if not lost:
        return
    for rel, lines in lost:
        print(f"  LOST from {rel}:")
        for l in lines[:8]:
            print(f"    | {l}")
        if len(lines) > 8:
            print(f"    | ... and {len(lines) - 8} more line(s)")
    if accept_loss:
        print(f"carry check: {sum(len(l) for _, l in lost)} pending line(s) NOT in the landed "
              f"tree -- accepted deliberately (--accept-loss).")
        return
    sys.exit("checkin FAIL: pending vendored additions are MISSING from the landed upstream "
             "tree -- a check-in dropped committed content (the 2026-08-19 failure). Carry "
             "them in another PR and re-record, or pass --accept-loss if the removal is "
             "deliberate; nothing recorded.")


def record(clone, note, accept_loss=False, resolving=()):
    # Neither a checkout nor a pull, for the same two reasons update() no
    # longer does either: the clone is a SOURCE the caller passed, not this
    # tool's to move (it silently relocated a session's checkout off
    # precedent-beta-v01 onto main on 2026-09-06 -- AGENTS.md's gotchas), and
    # the branch that matters is the one this install is pinned to, which is
    # not the clone's configured default. `fetch` updates remote-tracking
    # refs only; it never touches the working tree, HEAD, or a local branch.
    branch = _tracked_branch(clone)
    fetched = subprocess.run(['git', '-C', str(clone), 'fetch', 'origin',
                              _tracking_refspec(branch)],
                             capture_output=True, text=True)
    if fetched.returncode != 0:
        print(f"NOTICE: could not fetch origin/{branch} in {clone} "
              f"({fetched.stderr.strip()}) -- recording against whatever that "
              f"clone already has for {branch}, which may be behind.")
    # What LANDED is the committed tree on the pinned branch, not the clone's
    # working tree and not its HEAD, which may sit on any branch (see
    # _landed_commit). Recording HEAD stamped whatever branch the clone
    # happened to be on as the upstream commit.
    ref, head = _landed_commit(clone)
    with tempfile.TemporaryDirectory() as landed_dir:
        landed = _tree_at(clone, head, landed_dir)
        _carry_check(clone, accept_loss, landed, head, resolving)
        added, modified, deleted = _diff(landed)
    if added or modified or deleted:
        for p in added + modified + deleted:
            print(f"  differs: {p}")
        sys.exit(f"checkin FAIL: {ref} @ {head[:12]} is not identical to the vendored "
                 f"tree — merge/pull upstream first (or push the missing export); "
                 f"nothing recorded. Compared against what is committed there, so a "
                 f"gitignored or uncommitted file in the clone is never the cause.")
    manifest = _manifest()
    up = manifest.setdefault('upstream', {})
    if SOURCE and 'source' not in manifest:
        manifest['source'] = SOURCE
        up.setdefault('branch', _tracked_branch(clone))
    old = up.get('commit')
    manifest['upstream']['commit'] = head
    # record() has just verified the vendored tree is byte-identical to what
    # landed upstream -- which is STRONGER evidence of currency than the mirror
    # stamp update() writes. So advance synced_from too, or push()'s currency
    # guard reports a false positive on the very next export: the tree is
    # provably current while the stamp still points at the pre-merge commit.
    # (Found immediately after the guard shipped, by running the normal cycle
    # through to the end -- a reminder that a new gate is not done until the
    # whole loop has been walked with it in place.)
    manifest['upstream']['synced_from'] = head
    manifest['upstream']['_note'] = (
        f"commit = upstream hash last synced ({note or 'check-in'}, "
        f"recorded {precedent_time.today()}; verified tree-identical).")
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8')
    print(f"checkin record OK: upstream.commit {old} -> {head}")
    print(f"next: commit {MANIFEST.relative_to(ROOT)} in this repo.")
    return 0


def _loader_notice():
    """Say, after every status/update/record, when the catalogue this tool
    just vendored is in force nowhere. practice_audit.py FAILS on the same
    condition (its check 5); this is the same sentence arriving at the
    moment a person is already thinking about Precedent, instead of one
    command later. Retired-classic-install incident, 2026-09-23: an update
    ran clean here and the repo's sessions still loaded none of it."""
    try:
        from practice_audit import loader_gaps, MIGRATION_DOC
    except Exception:  # an older vendored audit; the audit itself still runs
        return
    try:
        from practice_audit import engine_gap
    except Exception:
        engine_gap = None
    gap = engine_gap(ROOT) if engine_gap else None
    if gap:
        # practice_audit's check 8, said at the update that could not reach
        # the engine: this mirror refreshed the catalogue and nothing else.
        bar = '!' * 72
        print(f"\n{bar}\nTHIS UPDATE REFRESHED THE CATALOGUE ONLY. {gap}\n"
              f"Follow vendor-update-runbook's \"Retire legacy leftovers\" "
              f"step: say so, confirm with the person, and finish the "
              f"migration in this same change.\n{bar}", file=sys.stderr)
    gaps = loader_gaps(ROOT)
    if gaps:
        bar = '!' * 72
        print(f"\n{bar}\nPRECEDENT IS NOT RUNNING IN THIS REPO. It vendors the practice "
              f"catalogue, but {'; and '.join(gaps)}.\nNone of those practices is in "
              f"force in any session here. This is the retired classic install: "
              f"migrate it onto the loader, whole, before calling this update "
              f"done --\n{MIGRATION_DOC}\n{bar}", file=sys.stderr)


def _declined_notice():
    """Name every recorded decline this update just moved past (practice:
    current-rule-governs). practice_audit.py's check 6 FAILS on the same
    condition; saying it here puts it in front of the person taking the
    update, which is when step 4 of the vendor-update runbook asks for the
    decision to be made again. Incident, 2026-09-24: a decline recorded as
    a "duplicate" rode through two syncs unread while the practice it
    declined was replaced upstream."""
    try:
        from practice_audit import stale_declines
    except Exception:  # an older vendored audit; the audit itself still runs
        return
    stale = []
    for m in sorted((ROOT / 'process').glob('manifest*.json')):
        try:
            stale += stale_declines(m)
        except (OSError, ValueError):
            continue
    if stale:
        print('\nDECISIONS TO MAKE AGAIN: upstream changed a practice this repo '
              'declined. Re-decide each in this same change (adopt it, or record '
              'why it is still declined and run practice_audit.py --redecide):',
              file=sys.stderr)
        for name, sentence in stale:
            print(f'  - [{name}] {sentence}', file=sys.stderr)


def main():
    rc = _main()
    if {'status', 'update', 'record'} & set(sys.argv[1:]):
        _loader_notice()
        _declined_notice()
    return rc


def _select_repo(path):
    """`--repo PATH`: act on that consuming repo rather than the one this
    file sits in. Rebinds what the module derived from its own location, so
    it must run before _select_source, which builds on ROOT."""
    global ROOT, UPSTREAM, MANIFEST
    repo = pathlib.Path(path).resolve()
    if not repo.is_dir():
        sys.exit(f"checkin FAIL: --repo {path}: no such directory")
    ROOT = repo
    UPSTREAM = ROOT / 'process' / 'upstream'
    MANIFEST = ROOT / 'process' / 'manifest.json'


def _main():
    args = sys.argv[1:]
    if '--repo' in args:
        i = args.index('--repo')
        if i + 1 >= len(args):
            sys.exit('checkin FAIL: --repo needs the consuming repo\'s path')
        _select_repo(args[i + 1])
        args = args[:i] + args[i + 2:]
    if args and args[0] == 'fresh':
        return fresh()
    if args and args[0] == 'rules':
        return rules_report(args[1] if len(args) > 1 else None)
    if args and args[0] == 'not-vendored':
        # Measures the NOT_VENDORED share against the tree in front of you,
        # so no document or comment has to freeze the numbers. Reports which
        # tree it measured, because the answer differs between this repo and
        # a consumer's process/upstream/ copy.
        base = pathlib.Path(args[1]) if len(args) > 1 else (
            UPSTREAM if UPSTREAM.is_dir() else ROOT)
        excluded, total, nbytes = not_vendored_share(base)
        if not total:
            print(f"checkin not-vendored: nothing to measure under {base} -- "
                  f"no files found, so this figure is not zero, it is unknown")
            return 1
        names = ', '.join(sorted(NOT_VENDORED) + sorted(NOT_VENDORED_ROOT_FILES)) \
            or '(nothing excluded)'
        print(f"tree measured:  {base}")
        print(f"excluded:       {names}")
        # Bytes, explicitly labelled: `du` reports DISK BLOCKS, and 557 small
        # files round up to roughly four times their real size at a 4K block.
        # A session quoting "2.4 MB" from `du` next to "557 files" from here
        # is quoting two different quantities as if they were one -- practice
        # `one-formatter-per-quantity`, learned the same day this was written.
        print(f"excluded files: {excluded} of {total} "
              f"({excluded / total * 100:.0f}%), "
              f"{nbytes / 1e6:.1f} MB of content "
              f"(byte sum, not `du` disk usage -- `du` counts 4K blocks and "
              f"reports several times this for many small files)")
        print("practices/ is never excluded -- this is measurement fixtures, "
              "not rules.")
        return 0
    if '--source' in args:
        i = args.index('--source')
        if i + 1 >= len(args):
            sys.exit('checkin FAIL: --source needs the set\'s name')
        _select_source(args[i + 1])
        args = args[:i] + args[i + 2:]
    if len(args) < 2 or args[0] not in ('status', 'update', 'push', 'record'):
        sys.exit(__doc__)
    clone = _clone_or_die(args[1])
    _bind_source(clone)
    if args[0] == 'status':
        return status(clone)
    if args[0] == 'update':
        return update(clone, force='--force' in args,
                     allow_pinned='--allow-pinned' in args)
    if args[0] == 'push':
        why = args[args.index('--why') + 1] if '--why' in args[:-1] else ''
        return push(clone, why=why, force='--force' in args)
    note = args[args.index('--note') + 1] if '--note' in args else ''
    resolving = [args[i + 1] for i, a in enumerate(args[:-1]) if a == '--resolving']
    return record(clone, note, accept_loss='--accept-loss' in sys.argv,
                  resolving=resolving)


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/FOR_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())

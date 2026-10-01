#!/usr/bin/env python3
"""precedent_update.py -- "Update Vendors" as one command: every step of
vendor-update-runbook that needs no judgment, in order, then one report.

Run it from the consuming repo, calling THIS copy -- the one in the
BestPractice clone, never a vendored one:

    python3 ../BestPractice/tools/precedent_update.py --repo .

WHY IT EXISTS (spec/ONE_COMMAND_UPDATE_PLAN.md, practice:
vendor-update-runbook). "Update Vendors" used to authorize a runbook that a
session then carried out by hand, and every consuming repo stopped at the
same places. The case that settled it, 2026-09-27: a consumer update stopped
halfway, engine on main and catalogue on precedent-beta-v01, because
finishing it meant a hand edit a permission check held for a human -- to
re-make a decision already made two days earlier. The rule this follows: an
upstream decision that changes a consumer's files is a step here, never a
sentence in the runbook.

WHY FROM THE SOURCE CLONE. A consumer's vendored checkin.py lives inside
the catalogue it updates, so a fix to it reaches a repo only after that repo
needed it. Run from the source clone, every step is the current code: the
engine refresh, the catalogue update (checkin.py --repo), the pin repoint.

THE STEPS, with no question in between:
  0. a journal an earlier run left when it was killed mid-swap is
     replayed, so this repo's local edits are back before anything reads
     the tree
  1. the source clone fetches the branch every install follows
  2. the engine refresh (the consumer's own copy, which replaces itself and
     runs a second pass), with each committed local edit to an engine file
     resolved around it by precedent_local_edits.py -- kept, merged, or
     replaced by upstream's with the commit holding it named -- then the catalogue-pin repoint and the renamed
     precedent-team-* -> precedent-shared-* sources from THIS copy; it
     stops if, with no --from-ref, the engine landed anywhere but the tip
     step 1 fetched, and leaves for you a run budget upstream gives a
     vendored tool that this repo's github_api_budgets.json lacks
  3. the catalogue: checkin.py update, then record, where the repo vendors
     one under process/ (process/manifest.json), its committed local
     changes resolved the same way; for a section 0 install,
     its universal source's practices/ replaced wholesale (INSTALL.md
     section 2, step 0) and the commit recorded in CATALOGUE_SYNC.json
     beside it; and where there is neither, a line saying so
     then a root VOICE.md or STYLEGUIDE.md left for you to convert, and
     any line templates/gitignore.template gained appended to .gitignore,
     and each line of an install-once file (the PR template, TODO.md, MAP.md
     ...) that is still, verbatim, wording its template has since dropped,
     left for you -- reported, never rewritten
     then, where precedent.json names no landing_branch, pre-staging
  4. the views regenerated -- the loader block, and in a practice set
     MAP.md and GLOSSARY.md too -- then manifest baselines moved for files
     now identical to upstream, a missing headroom_floor_pct defaulted,
     each file still naming one the refresh deleted left for you, and this
     repo's own citations of any practice the update withdrew or reworded
     (a withdrawn one's pointer is a call left for you; a bare mention of
     one, and a reworded one's citation, are listed to read)
  4a. any missing branch tier made on origin: staging from pre-staging,
     pre-staging from staging, both from main when neither exists
  5. the repo's own check at its landing branch's tier -- into pre-staging,
     the fast checks on what changed; the full check waits for the Promote
     (--skip-check to leave it out) -- run against a temporary commit of
     the staged update, undone right after, so it judges the tree the way
     the push will

THE REPORT, and the exit code a session acts on:
  0  DONE -- nothing is left. Commit, then run Go update's chain.
  1  LEFT FOR YOU -- only the calls that belong to this repo: an
     uncommitted edit to a received file, a kept-on-purpose file upstream
     has since changed, a line a check-in would lose, a decline to decide
     again. A committed local edit is no longer one of them: it is resolved,
     and listed under LOCAL EDITS in every outcome. Each is named with the question. Work them under the
     conflicted-file review at the top of vendor-update-runbook, then run
     this again.
  2  FAILED -- a step could not run, or the deep check is red. Named, with
     what was written before it stopped.

It stages what it wrote and deleted, so the deep check judges the tree the
commit will hold, and leaves anything already uncommitted alone -- save the
pinned engine a source refresh wrote ahead of it, which is the update's own
and is staged as such when every file matches the manifest. It never
leaves a commit behind, and never merges. The one thing it pushes is a
missing branch tier (pre-staging or staging), made at a commit origin
already has; the deep check's temporary commit is undone before it
reports. Those stay with the session, under Go update's
chain, where the authorization already lives.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
SOURCE = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import precedent_vendor_engine as pve  # noqa: E402
import precedent_branches as pb  # noqa: E402
import precedent_local_edits as le  # noqa: E402

DONE, LEFT, FAILED = 0, 1, 2


def rebaseline_vendored_entries(repo):
    """-> [local_path] whose recorded local_sha256 was re-recorded.

    A `synced` manifest entry whose local file sits INSIDE the vendored
    tree is not this repo's copy of anything: the catalogue mirror rewrites
    it wholesale, and refuses to run over a local edit. So after the mirror
    its old hash is stale by construction, and practice_audit read that as
    DRIFT -- "changed since baseline" -- on a file upstream changed, not
    this repo (2026-09-28, a consumer's doc-lint entry at
    process/upstream/tools/doc_lint.py). The pre-staging check does not run
    the audit, so the update said done and the Promote would have gone red.

    A synced entry OUTSIDE the tree is re-recorded on one condition only:
    its file is now byte-for-byte its upstream_path in the vendored tree.
    That is a file the update itself replaced with the current template --
    2026-09-28, a consumer's .claude/hooks/session-start.sh, identical to
    process/upstream/templates/harness/claude-code/hooks/session-start.sh
    and still carrying the old hash. Any other drift outside the tree is
    still an unexported local change, and still fails (practice:
    registry-source-of-truth)."""
    import hashlib
    mf = repo / 'process' / 'manifest.json'
    try:
        raw = mf.read_text(encoding='utf-8')
        data = json.loads(raw)
    except (OSError, ValueError):
        return []
    tree = str((data.get('upstream') or {}).get('vendored_at')
               or 'process/upstream').rstrip('/') + '/'
    done = []
    for e in data.get('entries') or []:
        rel = str(e.get('local_path') or '')
        if e.get('status') != 'synced' or e.get('granularity', 'file') != 'file':
            continue
        f = repo / rel
        if not rel or not f.is_file():
            continue
        if not rel.startswith(tree):
            up = str(e.get('upstream_path') or '')
            if not up or not (repo / tree / up).is_file() \
                    or (repo / tree / up).read_bytes() != f.read_bytes():
                continue
        cur = hashlib.sha256(f.read_bytes()).hexdigest()
        if e.get('local_sha256') and e['local_sha256'] != cur:
            e['local_sha256'] = cur
            done.append(rel)
    if done:
        mf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                      encoding='utf-8')
    return done


HEADROOM_FLOOR_DEFAULT = 5


def ensure_headroom_floor(repo):
    """Give tools/session_load_budgets.json the `headroom_floor_pct` the
    session-load-budget check now requires of any registry that declares
    ceilings. -> True when it wrote one.

    The check is full-tier only, so an update into pre-staging passed and
    the Promote to staging went red on a key nothing had ever written
    (2026-09-28, a consumer's update). 5 is the value BestPractice declares
    and precedent_bootstrap_source.py seeds. A value already there, `false`
    included -- a deliberate decline -- is never touched (practice:
    session-load-budget)."""
    path = repo / 'tools' / 'session_load_budgets.json'
    try:
        text = path.read_text(encoding='utf-8')
        data = json.loads(text)
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict) or not data.get('surfaces') \
            or 'headroom_floor_pct' in data:
        return False
    # Inserted as the first key, as text, so the rest of the file comes back
    # byte for byte; rewritten whole only if that does not parse to the
    # same registry plus the one key.
    new = re.sub(r'^\s*\{', '{\n  "headroom_floor_pct": %d,' % HEADROOM_FLOOR_DEFAULT,
                 text, count=1)
    try:
        ok = json.loads(new) == {**data, 'headroom_floor_pct': HEADROOM_FLOOR_DEFAULT}
    except ValueError:
        ok = False
    if not ok:
        new = json.dumps({'headroom_floor_pct': HEADROOM_FLOOR_DEFAULT, **data},
                         indent=2, ensure_ascii=False) + '\n'
    path.write_text(new, encoding='utf-8')
    return True


# precedent_resolve.check_source_manifest's refusal, as the view sync prints it.
SOURCE_NAME_MISMATCH = re.compile(
    r"the source at (?P<path>\S+) calls itself '(?P<own>[^']+)' in its \S+, "
    r"but this repository declares it as '(?P<declared>[^']+)'")
_REPOINTED = re.compile(r"repointed precedent\.json source '([^']+)' to '([^']+)'")


def renamed_sources_step(repo, rep, engine_out):
    """Repoint every precedent-team-* source to its precedent-shared-* name,
    path and level, from THIS copy of the engine -- a consumer whose own
    engine predates the repoint still gets it -- and report it as done.

    2026-09-28: the refresh listed the renamed sets under Left for you, and
    the view sync then stopped the update on the resolver's name check
    before any report was printed. The rename is fixed and known, so it is a
    step, never a question. Whatever an older engine's first pass left on
    the list about a source now repointed is already answered, and is
    dropped."""
    done = [(m.group(1), m.group(2)) for m in _REPOINTED.finditer(engine_out)]
    for old, new, old_path, new_path, kept in pve.repoint_renamed_sources(repo):
        if (old, old_path) != (new, new_path):
            done.append((old, new))
        if kept:
            rep.leave(f'precedent.json source {new!r} at {old_path}',
                      f'its clone is still at {old_path} and nothing is at '
                      f'{pve.renamed_set_path(old_path)} yet, so the path was '
                      f'left alone -- clone the set there (or rename the '
                      f'directory), then run this again')
    if not done:
        return
    olds = {o for o, _n in done}
    rep.left = [(w, y) for w, y in rep.left
                if not any(w.startswith(f'precedent.json source {o!r}') for o in olds)]
    rep.step('shared sets', 'precedent.json repointed from the old '
             'precedent-team-* names (name, path and level team -> shared): '
             + ', '.join(f'{o} -> {n}' for o, n in dict(done).items())
             + ' -- nothing to decide')


# The engine's WARN for a file that still names one it just deleted
# (precedent_vendor_engine._warn_about_dependents).
_MENTION = re.compile(r"^WARN: precedent_vendor_engine: (?P<gone>\S+) was .+?, "
                      r"and (?P<path>\S+?):(?P<line>\d+) still names it -- ")


def retired_mentions(repo, engine_out):
    """-> [(where, gone)] for each file that still names something the
    engine refresh deleted, and still does now that the rest of the update
    has run.

    The engine only WARNs about these, on stderr, and says nothing refuses
    over a mention. The pre-staging check agreed; the full check at the
    Promote to staging did not, and refused on them (practice:
    rename-updates-links; 2026-09-28: a retired bestpractice-docs.yml still
    named in a consumer's docs). So each one goes on Left for you, inside
    the update.
    Read from the WARN lines rather than asked of the engine because the
    deletion usually happens in the first pass, which is the consumer's own
    older copy. A file this repo receives rather than writes -- the
    vendored tree, practices/, tools/checks/ -- is skipped: the check skips
    it too, and the next sync overwrites it."""
    try:
        tree = str(json.loads((repo / 'process' / 'manifest.json').read_text(
            encoding='utf-8')).get('upstream', {}).get('vendored_at')
            or 'process/upstream')
    except (OSError, ValueError, AttributeError):
        tree = 'process/upstream'
    received = (tree.rstrip('/') + '/', 'practices/', 'tools/checks/')
    # A section 0 install's vendored catalogue is received too: a mention
    # there is upstream's to fix, never this repo's (2026-09-28).
    rel = universal_catalogue_path(repo)
    if rel:
        received += (rel.rstrip('/') + '/',)
    out = []
    for line in engine_out.splitlines():
        m = _MENTION.match(line.strip())
        if not m or m.group('path').startswith(received):
            continue
        gone, path = m.group('gone'), m.group('path')
        try:
            text = (repo / path).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        base = pathlib.PurePosixPath(gone).name
        hit = next((n for n, l in enumerate(text.splitlines(), 1)
                    if gone in l or base in l), None)
        if hit is not None and (f'{path}:{hit}', gone) not in out:
            out.append((f'{path}:{hit}', gone))
    return out


FULL_VIEWS = ('MAP.md', 'GLOSSARY.md')
_GENERATED_BY_BUILD_VIEWS = re.compile(
    r'\A---\n(?:.*\n)*?generated_by:\s*["\']?tools/build_views\.py', re.M)


def generated_full_views(repo):
    """-> the FULL_VIEWS this repo's own header says build_views.py
    generates, in order. A hand-written MAP.md is the repo's, and left
    alone."""
    out = []
    for name in FULL_VIEWS:
        try:
            head = (pathlib.Path(repo) / name).read_text(encoding='utf-8')[:2000]
        except (OSError, UnicodeDecodeError):
            continue
        if _GENERATED_BY_BUILD_VIEWS.match(head):
            out.append(name)
    return out


def source_is_its_own_clone():
    """-> None when SOURCE, the tree this file sits in, is the top of its own
    git repository -- a BestPractice clone -- else what it is instead.

    A consumer's vendored tree carries a copy of this file at
    process/upstream/tools/. Run from there, SOURCE is process/upstream and
    `git fetch` reaches the CONSUMER's origin, so the update failed late, on
    a fetch of a branch the consumer does not have (2026-09-28)."""
    r = subprocess.run(['git', '-C', str(SOURCE), 'rev-parse', '--show-toplevel'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return 'not inside a git repository at all'
    top = pathlib.Path(r.stdout.strip()).resolve()
    return None if top == SOURCE else f'a directory inside {top}'


# The two plain documents that became repo-local practices, and the
# migration step that converts each (spec/MIGRATING_EXISTING_INSTALLS.md).
# INSTALL.md: an update that lands on a repo still carrying the old file is
# a migration, and "do not leave the old file sitting beside the new
# practice file". Until 2026-09-28 the update said DONE on such a repo.
LEGACY_ROOT_DOCS = (
    ('VOICE.md', 'local/practices/project-voice.md', '3a'),
    ('STYLEGUIDE.md', 'local/practices/project-visual-identity.md', '3b'),
)
# The retired template each old root document was written from.
LEGACY_ROOT_TEMPLATES = {
    'VOICE.md': 'templates/VOICE.md.template',
    'STYLEGUIDE.md': 'templates/STYLEGUIDE.md.template',
}
_HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)


def _as_shipped(text):
    """`text` with its HTML comments dropped and its whitespace evened out:
    an instantiated template loses the template's header comment, and
    nothing else about it says the person decided anything."""
    text = _HTML_COMMENT.sub('', text)
    lines = [l.rstrip() for l in text.strip().splitlines()]
    out = []
    for l in lines:
        if l or (out and out[-1]):
            out.append(l)
    return '\n'.join(out).strip()


def shipped_unchanged(repo, old, rev):
    """True when the repo's `old` (VOICE.md, STYLEGUIDE.md) is a version of
    its retired template exactly as it shipped, comments aside -- so it
    carries no decision of the person's. Every version reachable from `rev`
    in the source clone counts (2026-10-01: a consumer's VOICE.md matched the
    2026-08-16 template, and converting it produced a practice file of
    `<undecided>` sections)."""
    tmpl = LEGACY_ROOT_TEMPLATES.get(old)
    try:
        mine = _as_shipped((repo / old).read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError):
        return False
    if not tmpl or not rev or not mine:
        return False
    r = subprocess.run(['git', '-C', str(SOURCE), 'rev-list', rev, '--', tmpl],
                       capture_output=True, text=True)
    for commit in (r.stdout.split() if r.returncode == 0 else ()):
        text = _source_text(commit, tmpl)
        if text is not None and _as_shipped(text) == mine:
            return True
    return False


def retire_shipped_root_doc(repo, old):
    """Delete an unchanged `old` and drop the process/manifest.json entry
    that points at it -> True when deleted. A deleted file's entry is
    what made practice_audit fail a consumer's staging check with UPSTREAM
    NOT VENDORED (2026-10-01)."""
    r = subprocess.run(['git', '-C', str(repo), 'rm', '-q', '--', old],
                       capture_output=True, text=True)
    if r.returncode != 0:
        try:
            (repo / old).unlink()
        except OSError:
            return False
    man = repo / 'process' / 'manifest.json'
    try:
        data = json.loads(man.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return True
    entries = data.get('entries')
    if isinstance(entries, list):
        kept = [e for e in entries
                if not (isinstance(e, dict) and e.get('local_path') == old)]
        if len(kept) != len(entries):
            data['entries'] = kept
            man.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                           encoding='utf-8')
    return True


def legacy_root_docs(repo, rev=None, rep=None):
    """-> [(old, why)] for each root document LEGACY_ROOT_DOCS names that is
    still here: to convert when its practice file is missing, to delete when
    both are present. One that is still the template exactly as it shipped
    carries nothing to convert, so with `rev` it is deleted here and said in
    one line on `rep` instead."""
    out = []
    for old, new, step in LEGACY_ROOT_DOCS:
        if not (repo / old).is_file():
            continue
        if rev and shipped_unchanged(repo, old, rev):
            if retire_shipped_root_doc(repo, old) and rep is not None:
                rep.step(old, f'deleted: it was the shipped default, unchanged, '
                              f'so it carried no decision to convert into {new}; '
                              f'its process/manifest.json entry went with it')
            continue
        where = f'spec/MIGRATING_EXISTING_INSTALLS.md step {step}'
        if (repo / new).is_file():
            out.append((old, f'{new} exists too, and a repo carrying both has no '
                             f'way to say which binds -- carry anything still '
                             f'only in {old} into {new}, then delete {old} '
                             f'({where})'))
        else:
            out.append((old, f'is now the repo-local practice {new}, which this '
                             f'repo lacks -- convert it and delete {old} in the '
                             f'same commit ({where}; INSTALL.md calls this a '
                             f'migration step)'))
    return out


def _source_text(rev, rel):
    """-> `rel`'s text at commit `rev` of the source clone, or None."""
    r = subprocess.run(['git', '-C', str(SOURCE), 'show', f'{rev}:{rel}'],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def gitignore_step(repo, rep, rev):
    """Append to .gitignore each line templates/gitignore.template (at `rev`)
    carries and it lacks -- additive, never an edit or a removal -- and
    report it. .gitignore is installed once, so a line the template gained
    later reached no installed repo: 2026-09-28, `.claude/worktrees/`, whose
    absence makes the stop hook refuse over a background agent's worktree."""
    tmpl = _source_text(rev, 'templates/gitignore.template') if rev else None
    if tmpl is None:
        return
    import precedent_install
    added = precedent_install.merge_gitignore(repo / '.gitignore', tmpl,
                                              'Added by Update Vendors')
    if added is None:
        rep.step('.gitignore', 'written from templates/gitignore.template '
                 '(there was none)')
    elif added:
        rep.step('.gitignore', f'{len(added)} line(s) the template now carries '
                 f'appended: ' + ', '.join(added))


# The files an install writes ONCE from a template and never looks at again,
# each with the template it came from. .gitignore is gitignore_step's;
# AGENTS.md and tools/bootstrap.sh are the engine refresh's, which already
# compares them to their templates' history (precedent_vendor_engine's
# AGENTS_MD_TEMPLATES and TEMPLATE_INSTANCES), so they are not here twice.
INSTALL_ONCE_TEMPLATES = (
    ('.github/pull_request_template.md', 'templates/pull_request_template.md.template'),
    ('TODO.md', 'templates/TODO.md.template'),
    ('MAP.md', 'templates/MAP.md.template'),
    ('GLOSSARY.md', 'templates/GLOSSARY.md.template'),
    ('GETTING_STARTED.md', 'templates/GETTING_STARTED.md'),
    ('README.md', 'templates/README_AGENT_ENTRY.md.template'),
    ('local/practices/project-voice.md',
     'templates/local-practices/project-voice.md.template'),
    ('local/practices/project-visual-identity.md',
     'templates/local-practices/project-visual-identity.md.template'),
)
# Per file, so a TODO.md still in the old checkbox format does not bury the
# rest of the report; the count of the rest is said.
DROPPED_LINES_SHOWN = 10


def _substantive(line):
    """A line worth matching: three words or more. A heading, a rule, a
    fence or a table divider is too generic to say where it came from."""
    return len(re.findall(r'[A-Za-z]{2,}', line)) >= 3


def _template_lines_ever(rev, rel):
    """-> {stripped line} every version of `rel` reachable from `rev` in the
    source clone ever carried: the lines its commits added, `--follow`ed
    through renames. A shallow clone sees less, which only flags less."""
    # `-m`: lines a merge commit added are template wording too.
    r = subprocess.run(['git', '-C', str(SOURCE), 'log', '--follow', '-p', '-m',
                        '-U0', '--format=', '--no-color', '--no-ext-diff',
                        rev, '--', rel], capture_output=True, text=True,
                       errors='replace')
    out, in_hunk = set(), False
    for line in r.stdout.splitlines() if r.returncode == 0 else []:
        if line.startswith('diff --git '):
            in_hunk = False
        elif line.startswith('@@'):
            in_hunk = True
        elif in_hunk and line.startswith('+'):
            out.add(line[1:].strip())
    return out


# A template's `<placeholder>`: anything in angle brackets that is not an
# HTML comment or tag. The install replaces each with the project's value.
_PLACEHOLDER_RE = re.compile(r'<(?![!/])[^<>\n]+>')


def _filled_forms(text):
    """-> [compiled pattern] for each line of a template that carries a
    placeholder, matching that line with every placeholder filled in.

    A consumer's line can equal an OLDER template line and still be the
    current one, filled in: GETTING_STARTED.md once wrote
    `process/upstream/` where it now writes `<upstream-docs>/`, and a §1
    install is told to replace the second with the first -- so a correct
    install read back as dropped wording (2026-10-01, from a consumer's
    Update Vendors). The values are the consumer's, unknowable here, so
    each placeholder matches any text."""
    out = []
    for line in {l.strip() for l in text.splitlines()}:
        parts = _PLACEHOLDER_RE.split(line)
        if len(parts) > 1:
            out.append(re.compile('.+?'.join(re.escape(x) for x in parts)))
    return out


def dropped_template_lines(repo, rev):
    """-> [(consumer_rel, template_rel, template_sha256, [(line_no, text)])]
    for each install-once file still carrying, verbatim, a line an OLDER
    version of its template had and the current one (at `rev`) does not.

    A REPORT, never a write. These files are the repo's own from the moment
    they are written, so a line the repo wrote itself is never flagged: only
    an exact match of a line upstream's own history carried and has since
    dropped or reworded. 2026-09-28: a real consumer's pull request template
    still asked for "TODO.md updated", and links in its install-once files
    still pointed at a branch that had been retired, with nothing saying so.

    Not agents-md-history: that record is keyed by AGENTS.md section and
    built inside the refresh's scratch directory; this needs every line a
    template ever carried, which one `git log -p` per template gives."""
    import hashlib
    found = []
    for rel, tmpl in INSTALL_ONCE_TEMPLATES:
        target = repo / rel
        if not rev or not target.is_file():
            continue
        current = _source_text(rev, tmpl)
        if current is None:
            continue
        now = {l.strip() for l in current.splitlines()}
        gone = {l for l in _template_lines_ever(rev, tmpl) - now if _substantive(l)}
        if not gone:
            continue
        try:
            text = target.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        filled = _filled_forms(current)
        hits = [(n, l.strip()) for n, l in enumerate(text.splitlines(), 1)
                if l.strip() in gone
                and not any(f.fullmatch(l.strip()) for f in filled)]
        if hits:
            found.append((rel, tmpl, hashlib.sha256(current.encode('utf-8')).hexdigest(),
                          hits))
    return found


def dropped_template_lines_step(repo, rep, rev):
    """Put each line dropped_template_lines finds on the Left-for-you list.
    A file precedent.json's kept_template_divergences records as kept on
    purpose, against the current template's text, is said once and not
    listed -- the same declaration the engine honours for tools/bootstrap.sh,
    so a repo that keeps an old line deliberately can still finish."""
    for rel, tmpl, sha, hits in dropped_template_lines(repo, rev):
        verdict, reason = pve._kept_divergence(repo, rel, sha)
        if verdict == 'kept':
            rep.step('kept on purpose', f'{rel} keeps wording {tmpl} dropped, '
                     f'as precedent.json records -- "{reason}"')
            continue
        for n, line in hits[:DROPPED_LINES_SHOWN]:
            shown = line if len(line) <= 160 else line[:157] + '...'
            rep.leave(f'{rel}:{n}', f'is template wording the current template '
                      f'dropped: {shown}')
        first = f'{rel}:{hits[0][0]}'
        more = len(hits) - DROPPED_LINES_SHOWN
        if more > 0:
            rep.leave(f'{rel} (more)', f'{more} more line(s) the current {tmpl} '
                      f'dropped -- compare the file with it')
        note = [f'bring it in line with {tmpl}, or drop the line; kept on '
                f'purpose? record "{rel}" in precedent.json\'s '
                f'{pve.KEPT_DIVERGENCES_KEY} with a reason and template_sha256 '
                f'{sha}']
        if verdict == 'stale':
            note.insert(0, f'recorded as kept ("{reason}"), but {tmpl} has '
                        f'changed since -- read it again')
        elif verdict == 'unreasoned':
            note.insert(0, 'recorded as kept with no reason, so not honoured')
        rep.details.setdefault(first, []).extend(note)


def unbudgeted_engine_tools(repo, rev):
    """-> [(tool, calls)] for each vendored engine file upstream's
    tools/github_api_budgets.json (at `rev`) gives a run budget that this
    repo's own registry lacks. Only where this repo keeps a registry: one
    that has none declares nothing, and the github-api-budget check leaves a
    vendored caller to the repo that wrote it. A report, never a write -- a
    budget is the repo's own declaration."""
    try:
        own = json.loads((repo / 'tools' / 'github_api_budgets.json')
                         .read_text(encoding='utf-8'))
        vendored = set(json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                                  .read_text(encoding='utf-8')).get('files') or ())
        up = json.loads(_source_text(rev, 'tools/github_api_budgets.json') or '')
    except (OSError, ValueError, TypeError):
        return []
    if not isinstance(own, dict) or not isinstance(up, dict):
        return []
    have = own.get('run_budgets') or {}
    return [(t, n) for t, n in sorted((up.get('run_budgets') or {}).items())
            if not t.startswith('_') and t in vendored and t not in have]


def universal_catalogue_path(repo):
    """-> the repo-relative path of the universal source this repository
    vendors inside itself (a section 0 install), or None: no precedent.json,
    no universal source, or one that lives outside the repository."""
    try:
        data = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    for src in data.get('sources') or []:
        if not isinstance(src, dict) or src.get('level') != 'universal':
            continue
        path = str(src.get('path') or '').strip().rstrip('/')
        if not path or path.startswith(('/', '~')) or '..' in pathlib.PurePosixPath(path).parts:
            return None
        return path
    return None


# The section 0 catalogue's own sync record, beside its practices/: the
# upstream commit the catalogue was last replaced from. The engine manifest's
# source_commit is the ENGINE's, and the two part ways whenever the engine
# refresh is committed before the catalogue step succeeds, or the two were
# ever vendored from different commits. 2026-09-28, a consumer: engine at
# one commit, catalogue at an older one recorded only in README prose, and
# 52 files refused as local edits that were every one upstream's own text.
CATALOGUE_SYNC_NAME = 'CATALOGUE_SYNC.json'


def _blob_id(data):
    """-> the git object id of `data` as a blob (git's default sha1 format)."""
    import hashlib
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def _tree_blobs(where, ref, prefix):
    """-> {path under `prefix`: blob id} at commit `ref` of the repo at
    `where`; {} when `ref` cannot be read there."""
    r = subprocess.run(['git', '-C', str(where), 'ls-tree', '-r', '-z', ref,
                        '--', f'{prefix}/'], capture_output=True, text=True)
    out = {}
    for entry in r.stdout.split('\0') if r.returncode == 0 else []:
        meta, _, path = entry.partition('\t')
        parts = meta.split()
        if len(parts) == 3 and parts[1] == 'blob' and path.startswith(prefix + '/'):
            out[path[len(prefix) + 1:]] = parts[2]
    return out


def _upstream_history_blobs(rev):
    """-> {(path under practices/, blob id)} for every version any upstream
    commit -- `rev`'s history and every ref the source clone holds -- ever
    carried. The same allowance the carry check makes for upstream's own
    history: a file equal to one of these is upstream's text, not a local
    edit, whichever commit it was vendored from."""
    # `-m`: a version a merge commit introduced is upstream's text too.
    r = subprocess.run(['git', '-C', str(SOURCE), 'log', '--format=', '--raw', '-m',
                        '--no-abbrev', '--no-renames', rev, '--all', '--',
                        'practices/'], capture_output=True, text=True)
    out = set()
    for line in r.stdout.splitlines() if r.returncode == 0 else []:
        meta, _, path = line.partition('\t')
        parts = meta.split()
        if not line.startswith(':') or len(parts) < 4 or not path.startswith('practices/'):
            continue
        for oid in parts[2:4]:
            if oid.strip('0'):
                out.add((path[len('practices/'):], oid))
    return out


def _catalogue_record(text):
    """-> the source_commit a CATALOGUE_SYNC.json's text names, or None."""
    try:
        c = json.loads(text).get('source_commit')
    except (ValueError, AttributeError):
        return None
    return c if isinstance(c, str) and re.fullmatch(r'[0-9a-f]{7,64}', c) else None


def _is_commit(rev):
    return rev and subprocess.run(['git', '-C', str(SOURCE), 'cat-file', '-e',
                                   f'{rev}^{{commit}}'], capture_output=True).returncode == 0


def vendor_universal_catalogue(repo, rep, rev, last_synced=None):
    """Replace a section 0 install's vendored universal catalogue with the
    source clone's practices/ at commit `rev` -- a committed ref, never the
    clone's working tree, as the engine step reads -- and record `rev` in
    CATALOGUE_SYNC.json beside it. -> True when the step ran or honestly had
    nothing to do (reported either way), None when it left a call for the
    person, or the reason the update fails.

    `last_synced` is the engine manifest's commit, which says only that this
    repo has synced before: the catalogue's local edits are judged against
    its own committed record, or, where it has none yet, against every
    version upstream ever had at each path."""
    import io
    import shutil
    import tarfile
    import tempfile
    rel = universal_catalogue_path(repo)
    target = repo / rel / 'practices' if rel else None
    if target is None or not target.is_dir():
        rep.step('catalogue', 'none vendored here: no process/manifest.json and '
                 'no universal source with a practices/ tree inside this repo, '
                 'so there was nothing to update')
        return True
    # Zero local variance by design (INSTALL.md section 2, step 0): a local
    # edit belongs upstream, so the replace refuses rather than eat one.
    dirty, err = status_paths(repo, f'{rel}/practices')
    if dirty is None:
        return f'could not read git status of {rel}/practices: {err}'
    dirty = sorted(dirty)
    # Except this command's own output. A run that failed after this step
    # (the view sync, the check) leaves the replaced catalogue uncommitted,
    # and "run this again" refused over it (2026-09-28). A path whose working
    # state is exactly upstream's at `rev`, or at the commit the uncommitted
    # record names, is what the replace writes -- not a change of anyone's.
    if dirty:
        try:
            pending = _catalogue_record((repo / rel / CATALOGUE_SYNC_NAME)
                                        .read_text(encoding='utf-8'))
        except OSError:
            pending = None
        at = [_tree_blobs(SOURCE, c, 'practices') for c in dict.fromkeys(
            c for c in (rev, pending) if c)]
        prefix = f'{rel}/practices/'
        foreign = []
        for p in dirty:
            f = repo / p
            here = _blob_id(f.read_bytes()) if f.is_file() else None
            if not any(here == blobs.get(p[len(prefix):]) for blobs in at):
                foreign.append(p)
        dirty = foreign
    if dirty:
        for p in dirty:
            rep.leave(p, 'changed here and not committed; the catalogue is '
                      'replaced wholesale, so export the change upstream or '
                      'discard it first')
        rep.step('catalogue', f'refused: {rel}/practices has uncommitted changes')
        return None
    # Committed local edits too: a committed file that matches neither the
    # upstream text it was last synced from nor the incoming one was changed
    # here, and the replace would lose it. One that matches the incoming
    # version already (a catalogue copied over by hand) loses nothing.
    shown = subprocess.run(['git', '-C', str(repo), 'show',
                            f'HEAD:{rel}/{CATALOGUE_SYNC_NAME}'],
                           capture_output=True, text=True)
    recorded = _catalogue_record(shown.stdout) if shown.returncode == 0 else None
    edited, basis, unread = [], None, False
    if recorded and _is_commit(recorded):
        base = _tree_blobs(SOURCE, recorded, 'practices')
        basis = f'{recorded[:12]} (the catalogue\'s own last sync)'
        upstream = lambda name, oid: base.get(name) == oid          # noqa: E731
    elif recorded or last_synced:
        history = _upstream_history_blobs(rev)
        basis = ('any upstream commit (the catalogue\'s recorded sync, '
                 f'{recorded[:12]}, is not in the source clone)' if recorded else
                 f'any upstream commit (no {CATALOGUE_SYNC_NAME} yet)')
        upstream = lambda name, oid: (name, oid) in history         # noqa: E731
    else:
        unread = True
    if not unread:
        incoming = _tree_blobs(SOURCE, rev, 'practices')
        for name, oid in sorted(_tree_blobs(repo, 'HEAD', f'{rel}/practices').items()):
            if incoming.get(name) != oid and not upstream(name, oid):
                edited.append(f'{rel}/practices/{name}')
    # A committed local edit is resolved, not refused, when the catalogue's
    # own sync record names the commit it came from -- that commit is BASE
    # (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md). Judged only against
    # upstream's history, there is no one BASE to merge with, so it stays a
    # call for the person, as before.
    swap_edits = []
    if edited and recorded and _is_commit(recorded):
        swap_edits = le.section0_edits(repo, SOURCE, edited, rel, recorded)
    elif edited:
        for p in edited:
            rep.leave(p, f'differs from upstream at {basis} and at {rev[:12]}: a '
                      f'local edit the wholesale replace would lose, and with no '
                      f'{CATALOGUE_SYNC_NAME} naming the commit it was synced '
                      f'from there is nothing to merge it with -- send it '
                      f'upstream ({le.send_command(repo)}), or restore '
                      f'upstream\'s text, then run this again')
        rep.step('catalogue', f'refused: {len(edited)} file(s) in {rel}/practices '
                 f'carry local edits')
        return None
    with le.Swap(repo, swap_edits) as swap:
        arc = subprocess.run(['git', '-C', str(SOURCE), 'archive', '--format=tar',
                              rev, 'practices'], capture_output=True)
        if arc.returncode != 0 or not arc.stdout:
            return (f'could not read practices/ at {rev[:12]} in {SOURCE}: '
                    f'{arc.stderr.decode(errors="replace").strip()[:200]}')
        with tempfile.TemporaryDirectory() as td:
            with tarfile.open(fileobj=io.BytesIO(arc.stdout)) as tf:
                try:
                    tf.extractall(td, filter='data')
                except TypeError:   # a Python older than 3.11.4 has no filter
                    tf.extractall(td)
            shutil.rmtree(target)
            shutil.copytree(pathlib.Path(td) / 'practices', target)
        (repo / rel / CATALOGUE_SYNC_NAME).write_text(json.dumps({
            'source_commit': rev,
            'written_by': 'tools/precedent_update.py (Update Vendors)',
            'why': 'the upstream commit practices/ here was last replaced from; '
                   'the next update judges local edits against it'}, indent=2) + '\n',
            encoding='utf-8')
        # THE SOURCE'S OWN MANIFEST travels with its catalogue (2026-09-29). A
        # consumer's occasion-index cap is the sum of what its sources declare
        # in their precedent-source.json, and the vendored universal tree never
        # carried that file, so universal's allowance was unreadable here.
        shown = subprocess.run(['git', '-C', str(SOURCE), 'show',
                                f'{rev}:precedent-source.json'],
                               capture_output=True, text=True)
        if shown.returncode == 0 and shown.stdout.strip():
            (repo / rel / 'precedent-source.json').write_text(shown.stdout,
                                                              encoding='utf-8')
        n = sum(1 for _ in target.glob('*.md'))
        note = (f'; local edits judged against {basis}' if not unread else
                '; no record of the last sync here, so only uncommitted edits '
                'were checked for')
        rep.step('catalogue', f'{rel}/practices replaced from the source at '
                 f'{rev[:12]} ({n} practice files; INSTALL.md section 2, step 0){note}')
        rep.add_edits(le.resolve(repo, swap), swap.merges)
        return True


class Report:
    def __init__(self):
        self.steps = []   # (name, one-line outcome)
        self.left = []    # (what, why)
        self.loud = []    # workflows left alone -- printed first and last
        self.details = {} # what -> lines printed under its Left-for-you item
        self.asks = []    # (what, question) -- for the person, not this repo
        self.edits = []   # (outcome, rel, text) -- precedent_local_edits.resolve()
        self.merges = {}  # rel -> (merged, upstream's) -- judged again at step 5

    def step(self, name, outcome):
        self.steps.append((name, outcome))
        print(f"precedent_update: {name}: {outcome}", flush=True)

    def leave(self, what, why):
        if (what, why) not in self.left:
            self.left.append((what, why))

    def ask(self, what, question):
        """A question only the person can answer and this repo cannot act
        on -- so it holds nothing (the exit code is unchanged), and it is
        printed in every outcome, never left in a step's scrollback."""
        if (what, question) not in self.asks:
            self.asks.append((what, question))

    def _questions(self):
        if self.asks:
            print("\nQUESTIONS FOR THE PERSON -- nothing here blocks the update, "
                  "and none is this repo's call; ask before Go update:")
            for what, question in self.asks:
                print(f"  - {what}: {question}")

    def _banner(self):
        # A workflow the update had to leave alone still runs in GitHub, and
        # the person asked for that to be impossible to miss (Morgan,
        # 2026-09-27: "flag it importantly ... strong language").
        bar = '!' * 72
        print(f"\n{bar}\n{pve.KEPT_LOUD_HEADER}\n{bar}")
        for line in self.loud:
            print(f"  {line}")
        print(bar)

    def add_edits(self, outcomes, merges=None):
        """What precedent_local_edits.resolve() did. A file kept on purpose
        that upstream has since changed is a call for the person, so it is
        left for them; the rest are notes."""
        for outcome, rel, text in outcomes:
            if outcome == le.KEPT_STALE:
                self.leave(rel, text)
            else:
                self.edits.append((outcome, rel, text))
        self.merges.update(merges or {})

    def _local_edits(self):
        # Every received file this repo had changed, and what the update did
        # with it, in every outcome -- a replaced local fix is never only in
        # a step's scrollback (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md).
        lines = le.report_lines(self.edits)
        if lines:
            print("\nLOCAL EDITS -- files this repo received and changed, and "
                  "what the update did with each:")
            for line in lines:
                print(f"  {line}")

    def close(self, failed=None):
        if self.loud:
            self._banner()
        print("\n== Update Vendors ==")
        for name, outcome in self.steps:
            print(f"  {name}: {outcome}")
        self._local_edits()
        self._questions()
        if failed:
            # What the update left for the person is printed on a failure
            # too. 2026-09-28: a consumer's refresh named its bootstrap.sh as
            # lacking the shared-set clone block, the check then failed on
            # exactly that, and the report printed the failure alone -- the
            # line that explained it was on this list and was dropped.
            if self.left:
                print("\nLEFT FOR YOU -- found before the failure, and likely "
                      "part of it:")
                for what, why in self.left:
                    print(f"  - {what}: {why}")
                    for line in self.details.get(what, []):
                        print(f"    {line}")
            print(f"\nFAILED: {failed}")
            print("Nothing is committed. Fix what is named above and run this "
                  "again; files the steps before it wrote are still in the "
                  "working tree for you to review.")
            return FAILED
        if self.left:
            print("\nLEFT FOR YOU -- the calls that belong to this repo. Work "
                  "each under vendor-update-runbook's conflicted-file review, "
                  "then run this again:")
            for what, why in self.left:
                print(f"  - {what}: {why}")
                for line in self.details.get(what, []):
                    print(f"    {line}")
            if self.loud:
                self._banner()
            return LEFT
        if self.asks:
            print("\nDONE -- nothing left for this repo to decide. Ask the "
                  "question(s) above, review the staged diff, commit, then run "
                  "Go update's chain.")
            return DONE
        print("\nDONE -- nothing left to decide. Review the staged diff, "
              "commit, then run Go update's chain.")
        return DONE


def run(argv, cwd):
    r = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    return r.returncode, r.stdout + r.stderr


# A red check's verdict lines: a check's FAILED, a VIOLATION and the
# findings under it, and the one-line summary per failing check.
_VERDICT_LINE = re.compile(r'FAIL|VIOLATION|^\s+\S+ \|\s|^\s*\|\s{2,}\S')


FULL_OUTPUT_NAME = '.precedent/update-failure.log'


def tail(out, n=25, repo=None):
    """`out`'s verdict lines, every one of them, then its last two lines; or,
    with no verdict line, its last `n`. A plain tail showed only routine
    notices when a build printed them after the verdict: an update reported
    "the check is red" and nothing about why (2026-09-29).

    Never a partial list of findings. The verdict lines were capped at 22
    until 2026-09-30, when a consumer's update ended FAILED three times in a
    row, each showing a few more stranded files than the last, and two full
    runs went on reading the rest. With `repo`, whatever this leaves out is
    in FULL_OUTPUT_NAME (untracked), and the last line names it."""
    lines = [l for l in out.rstrip().splitlines()]
    verdict = [l for l in lines if _VERDICT_LINE.search(l)
               and 'build_views:' not in l]
    shown = (verdict + ['...'] + lines[-2:]) if verdict else lines[-n:]
    text = '\n'.join('    | ' + l for l in shown)
    if repo is not None and len(shown) < len(lines):
        path = pathlib.Path(repo) / FULL_OUTPUT_NAME
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(out, encoding='utf-8')
            text += (f'\n    (the whole output, {len(lines)} lines, is in '
                     f'{FULL_OUTPUT_NAME})')
        except OSError:
            pass
    return text


def left_block(out):
    """The '  - item: why' lines under the engine's own Left-for-you
    heading, and checkin's DECISIONS TO MAKE AGAIN list."""
    items, inside = [], False
    for line in out.splitlines():
        if line.startswith('Left for you') or \
                line.startswith('DECISIONS TO MAKE AGAIN'):
            inside = True
            continue
        if inside:
            if line.startswith('  - '):
                items.append(line[4:].strip())
            elif line.strip():
                inside = False
    return items


def engine_summary(out, last_synced):
    """-> the one-line engine outcome for the report. The last summary line
    is the second pass's, whose "(was ...)" an engine older than
    2026-09-28 reads from the manifest the first pass already rewrote --
    "(was e8a2bc67cc8d)" on a repo that had been at 37fc3b55. This command
    read the real commit before the refresh began, so that one is shown."""
    summary = [l for l in out.splitlines()
               if l.startswith('precedent_vendor_engine refresh OK')
               or 'already current with' in l]
    line = summary[-1].split(': ', 1)[-1] if summary else 'refreshed'
    if last_synced:
        line = re.sub(r'\(was [0-9a-f?]+\)', f'(was {last_synced[:12]})', line)
    return line


def diverged_details(out):
    """-> {what: [detail line, ...]} from the engine refresh's DIVERGED
    blocks: the blocks a locally edited file or AGENTS.md section lacks, and
    the sentences missing from each. The engine prints them and names each
    in Left-for-you as "(listed above)"; until 2026-09-28 this command kept
    only the Left-for-you line, so "listed above" listed nothing and a
    session called missing_markdown_blocks() by hand to see what to copy."""
    details, key = {}, None
    for line in out.splitlines():
        if line.startswith('DIVERGED: '):
            body = line[len('DIVERGED: '):]
            m = re.match(r'(.+?) (?:\(line \d+\) )?has local edits', body)
            key = m.group(1) if m else None
            if key is not None:
                # A refresh that replaced itself runs a second pass, which
                # prints every block again: the later list is the one that
                # stands.
                details[key] = []
            continue
        if key is not None and line.startswith('    '):
            details[key].append(line.rstrip())
        elif line.strip():
            key = None
    return {k: v for k, v in details.items() if v}


def in_force_nowhere(out):
    """-> the view sync's IN FORCE NOWHERE warnings, each 'slug (source):
    why'. The sync prints them and still passes, and until 2026-09-28 this
    command said DONE with them left in the sync's own output: a
    deduplication whose forwarding address names a set this repo does not
    declare, so the rule binds nowhere here. Whether that is acceptable is
    the person's call, never this repo's."""
    mark = 'IN FORCE NOWHERE -- '
    return list(dict.fromkeys(l.split(mark, 1)[1].strip()
                              for l in out.splitlines() if mark in l))


def lost_files(out):
    return [l.strip()[len('LOST from '):].rstrip(':')
            for l in out.splitlines() if l.strip().startswith('LOST from ')]


def dirty_paths(repo):
    """Every path `git status` reports, staged or not, tracked or not. A
    staged rename lists both its sides."""
    return status_paths(repo)[0] or set()


def status_paths(repo, *pathspec):
    """-> (dirty_paths()'s set, limited to `pathspec` when given, '') -- or
    (None, the error) when `git status` could not run."""
    r = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain=v1', '-z',
                        '--untracked-files=all', '--', *pathspec],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr.strip()[:200]
    fields, paths, i = r.stdout.split('\0'), set(), 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        paths.add(entry[3:])
        if entry[0] in 'RC' and i < len(fields):
            paths.add(fields[i])
            i += 1
    return paths, ''


def stage_update(repo, before):
    """Stage what this run wrote or deleted, and nothing that was already
    uncommitted when it started. Returns how many paths it staged.

    So the deep check judges the tree the commit will hold. Found
    2026-09-27 taking main into a consumer: `checkin.py update` deleted two
    files upstream had dropped, the deletions sat unstaged, and the deep
    check -- listing files from the index -- failed the update on a file
    that was gone. A person's own unfinished work is left as it was."""
    ours = sorted(dirty_paths(repo) - before)
    for i in range(0, len(ours), 200):
        subprocess.run(['git', '-C', str(repo), 'add', '-A', '--', *ours[i:i + 200]],
                       capture_output=True, text=True)
    return len(ours)


def adopt_engine_output(repo, before, pinned):
    """-> the paths in `before` that are this update's own output, written
    ahead of it, to stage as the update's; [] when any is not.

    Found 2026-09-27 on all four of Morgan's sets: a source refresh run
    first (precedent_refresh_sources.py) had already written the pinned
    engine into each repo, so the refresh here said "already current",
    stage_update left the two changed files as someone else's, and the
    report said DONE on an update that would have committed nothing. They
    are the update's when the manifest -- uncommitted -- names the pinned
    commit and every uncommitted file it tracks hashes to what it records;
    a single mismatch means someone else's edit is in the mix, and then
    nothing is taken."""
    rel = f'tools/{pve.MANIFEST_NAME}'
    if rel not in before or not pinned:
        return []
    try:
        m = json.loads((repo / rel).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    if m.get('source_commit') != pinned:
        return []
    tracked = {f'tools/{n}': h for n, h in (m.get('sha256') or {}).items()}
    tracked.update({f'{pve.HOOK_DEST_DIR}/{n}': h
                    for n, h in (m.get('hooks_sha256') or {}).items()})
    tracked.update(m.get('engine_paths_sha256') or {})
    ours = [rel]
    for path in sorted(before & set(tracked)):
        f = repo / path
        if not f.is_file() or pve._sha256(f) != tracked[path]:
            return []
        ours.append(path)
    return ours


def citations(repo):
    """-> ([(where, why)] to fix, [where] to read), or None when the lookup
    could not run. Asks the SOURCE clone's copy of the lookup, for the same
    reason every other step here does: it is the current code."""
    refs = SOURCE / 'tools' / 'precedent_practice_refs.py'
    if not refs.is_file():
        return None
    r = subprocess.run([sys.executable, str(refs), '--repo', str(repo),
                        '--withdrawn', '--changed-since', 'HEAD', '--staged',
                        '--json'], cwd=str(repo), capture_output=True,
                       text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    fix, read = [], []
    slugs, successors = data.get('slugs', {}), data.get('successors', {})
    for h in data.get('hits', []):
        if h.get('source') != 'this repository' or h.get('kind') != 'live':
            continue
        where = f"{h['file']}:{h['line']}"
        succ = successors.get(h['slug'])
        if h.get('must_fix'):
            fix.append((where, f"cites `{h['slug']}`, which is no longer in force"
                        + (f" -- cite `{succ}`" if succ else
                           " anywhere -- say in prose what it covered")))
        elif slugs.get(h['slug']) == 'Rule reworded':
            read.append(where)
        elif h['slug'] in slugs:
            # A bare mention of a renamed or withdrawn slug. The check
            # does not refuse it (it may be lineage), but it is a citation
            # all the same. Until 2026-09-28 it was dropped here, and the
            # update said "no live citation of a withdrawn practice" while
            # precedent_practice_refs.py --withdrawn listed one (`go-merge`,
            # renamed `go-update`, in a consumer's own docs).
            read.append(f"{where} (`{h['slug']}`, {slugs[h['slug']]}"
                        + (f", now `{succ}`)" if succ else ")"))
    return fix, read


TEMP_COMMIT_MESSAGE = ('precedent_update: the staged update, committed only so the '
                       'deep check judges it as committed -- undone right after')


def standin_message():
    """-> the stand-in commit's whole message: TEMP_COMMIT_MESSAGE and a
    `Session:` trailer.

    WHY THE TRAILER (2026-09-30, a consumer's update). Without one, every
    update in a repo that declares the session-trailer check ended FAILED on
    "commit <stand-in>: no Session: trailer", however clean the tree. The
    push check already let its own copy of that check stand aside for the
    stand-in (precedent_push_check.py, STANDIN_COMMIT_ENV), but the same
    check also runs as an enforced practice inside precedent_check.py, and
    the set's own test runs it against the real history. Those judge the
    commit, not the environment, so the commit now carries the line the real
    one will. It is never pushed: judged_as_committed() undoes it.

    PRECEDENT_SESSION_URL hands over a real link, the way
    precedent_refresh_sources.py takes one; otherwise it is the practice's
    own explicit opt-out form."""
    url = (os.environ.get('PRECEDENT_SESSION_URL') or '').strip()
    trailer = (f'Session: {url}' if url else
               'Session: none available (tools/precedent_update.py stand-in)')
    return f'{TEMP_COMMIT_MESSAGE}\n\n{trailer}\n'


def stamp_headers(repo):
    """-> [path] whose version header the repo's own header check stamped.

    A regenerated AGENTS.md changes content, and the commit is where its
    header gets bumped -- after the check. So the check failed the update on
    file-header ("content changed ... but version stayed at 9") for a stamp
    the real commit would have made (2026-09-28, a consumer's update). The
    repo's own tools/checks/check_file_header.py --fix stamps the working
    tree first, and only paths already staged -- the update's own -- are
    staged again; anything the person left unstaged stays unstaged."""
    fixer = repo / 'tools' / 'checks' / 'check_file_header.py'
    if not fixer.is_file():
        return []
    staged = [l for l in subprocess.run(
        ['git', '-C', str(repo), 'diff', '--cached', '--name-only'],
        capture_output=True, text=True).stdout.splitlines() if l]
    if not staged:
        return []
    subprocess.run([sys.executable, str(fixer), '--fix'], cwd=repo,
                   capture_output=True, text=True)
    changed = set(subprocess.run(['git', '-C', str(repo), 'diff', '--name-only'],
                                 capture_output=True, text=True).stdout.split())
    stamped = [p for p in staged if p in changed]
    if stamped:
        subprocess.run(['git', '-C', str(repo), 'add', '--', *stamped],
                       capture_output=True)
    return stamped


def judged_as_committed(repo, argv):
    """-> (rc, output) of `argv`, run against the tree the commit will hold.

    WHY (2026-09-27, found taking main into a consumer): the deep check
    judged an update by what was STAGED, and a committed tree is judged
    differently in two ways. A change-scope check reads `git status`, so
    every materialized practice the update rewrote -- upstream text the repo
    cannot edit -- was judged as this repo's own new prose; once committed,
    nothing is uncommitted and the push never judges it. And a shipped test
    that clones the repo clones HEAD, so it ran the update's NEW test
    against the OLD scripts. Both failed an update that passes the moment
    it is committed.

    So the staged update is committed, the check runs, and the commit is
    undone with `git reset --soft`, which moves only HEAD: the index and the
    working tree are left exactly as the check found them, staged work and
    unstaged edits alike. The commit goes through the repository's own
    hooks, the way the real one will, and carries the person's zone.

    Nothing staged: nothing to commit, and the check runs as it is. A commit
    the hooks refuse is the answer the real commit would get, so it is
    reported, never worked around."""
    staged = subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--quiet'],
                            capture_output=True).returncode != 0
    if not staged:
        return run(argv, repo)
    rc, before = run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], repo)
    if rc != 0:
        return run(argv, repo)
    before = before.strip()
    env = {**os.environ}
    try:
        import precedent_time
        when = precedent_time.stamp_iso(repo)
        env['GIT_AUTHOR_DATE'] = env['GIT_COMMITTER_DATE'] = when
    except Exception:                                          # noqa: BLE001
        pass
    c = subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m',
                        standin_message()], capture_output=True, text=True,
                       env=env)
    if c.returncode != 0:
        return c.returncode, ('the staged update could not be committed, so '
                              'the real commit would be refused the same way:\n'
                              + c.stdout + c.stderr)
    try:
        # The stand-in's message, author and date are this tool's, so the
        # commit-judging checks stand aside (precedent_push_check.py,
        # STANDIN_COMMIT_ENV) and the push gate judges the real commit.
        os.environ['PRECEDENT_STANDIN_COMMIT'] = '1'
        try:
            return run(argv, repo)
        finally:
            os.environ.pop('PRECEDENT_STANDIN_COMMIT', None)
    finally:
        _rc, parent = run(['git', '-C', str(repo), 'rev-parse', 'HEAD~1'], repo)
        if parent.strip() == before:
            subprocess.run(['git', '-C', str(repo), 'reset', '-q', '--soft', before],
                           capture_output=True)


def _write_staged(repo, files):
    """Write {rel: bytes} and stage exactly those paths."""
    for rel, data in files.items():
        (repo / rel).write_bytes(data)
    subprocess.run(['git', '-C', str(repo), 'add', '--', *files],
                   capture_output=True, text=True)


def check_with_merge_fallback(repo, rep, argv, label):
    """-> (rc, output) of the repo's own check, run as committed. A merge
    made by precedent_local_edits.resolve() has passed its own compile and
    test run; this is the repo's real gate. Red with a merged file in place:
    every merge takes upstream's version and the check runs once more. Green
    then, the merges were the cause and upstream's version stands (rule 3,
    reported with the commit holding the local one); red either way, they
    were not, and they are put back so the failure is reported on the tree
    the rules made. (Suggested by the parallel session that built the same
    resolution, 2026-09-29.)"""
    rc, out = judged_as_committed(repo, argv)
    if rc == 0 or not rep.merges:
        return rc, out
    _write_staged(repo, {rel: new for rel, (_m, new) in rep.merges.items()})
    rc2, out2 = judged_as_committed(repo, argv)
    if rc2 == 0:
        why = (f'your edit and upstream\'s merged cleanly and passed their own '
               f'checks, but this repo\'s {label} failed with the merge in place '
               f'and passes without it')
        rep.edits = [(le.TOOK_UPSTREAM, rel, le.took_upstream_text(repo, rel, why))
                     if outcome == le.MERGED and rel in rep.merges
                     else (outcome, rel, text) for outcome, rel, text in rep.edits]
        rep.step('merges', f'{len(rep.merges)} merged file(s) took upstream\'s '
                 f'version instead: the {label} failed with them and passes '
                 f'without them')
        rep.merges = {}
        return rc2, out2
    _write_staged(repo, {rel: merged for rel, (merged, _n) in rep.merges.items()})
    rep.step('merges', f'kept: the {label} is red with or without the '
             f'{len(rep.merges)} merged file(s), so they are not the cause')
    return rc, out


def tiers_step(repo, rep):
    """Make any missing branch tier on origin and report it on `rep` -- the
    update's step 4a, and the one thing a repository still to be migrated
    gets before it is sent to the migration (Morgan, 2026-09-27: "the same
    issue with migrations: when migrating check for these and create
    them")."""
    tier_lines = []
    has_origin = run(['git', '-C', str(repo), 'remote', 'get-url', 'origin'],
                     repo)[0] == 0
    try:
        rc = pb.ensure_tiers(repo, apply=True, say=tier_lines.append) \
            if has_origin else 0
    except Exception as e:                                     # noqa: BLE001
        rc, tier_lines = 1, [f'{type(e).__name__}: {e}']
    made = [l for l in tier_lines if l.startswith(('created ', 'wrote '))]
    if not has_origin:
        rep.step('branch tiers', 'no origin remote here, so there is nowhere to '
                 'make them')
    elif rc != 0:
        rep.leave('branch tiers', 'pre-staging and staging could not both be '
                  'made on origin -- ' + ' '.join(tier_lines)[-400:])
    else:
        rep.step('branch tiers', '; '.join(made) if made else
                 'pre-staging, staging and main all present')


def update(repo, skip_check=False, ref=None):
    rep = Report()
    elsewhere = source_is_its_own_clone()
    if elsewhere:
        return rep.close(f"this copy of precedent_update.py sits in {SOURCE}, "
                         f"which is {elsewhere} -- a vendored copy, not a "
                         f"BestPractice clone, so it would fetch the wrong "
                         f"repository. Run the clone's own copy from the "
                         f"consuming repo: python3 ../BestPractice/tools/"
                         f"precedent_update.py --repo .")
    # A run killed between swapping upstream's text in and putting this
    # repo's edits back left a journal; replay it before anything else reads
    # the tree (spec/LOCAL_EDITS_TO_RECEIVED_FILES_PLAN.md).
    restored, stranded = le.recover(repo, SOURCE)
    for rel in restored:
        rep.step('local edits', f'put back your local {rel}, which an earlier '
                 f'Update Vendors stopped mid-way had left replaced')
    if stranded:
        for rel, why in stranded:
            rep.leave(rel, why)
        return rep.close()
    before = dirty_paths(repo)
    engine_tool = repo / 'tools' / 'precedent_vendor_engine.py'
    if not (repo / 'tools' / pve.MANIFEST_NAME).is_file() or not engine_tool.is_file():
        rep.leave(str(repo), "no vendored loader engine (tools/ENGINE_MANIFEST.json), "
                  "so this is a migration, not an update -- "
                  "spec/MIGRATING_EXISTING_INSTALLS.md")
        # The migration still gets its three branches now, from here.
        tiers_step(repo, rep)
        return rep.close()

    # 1. The source clone. Both halves read committed refs, never its
    # working tree, so a fetch is what makes them current.
    # With an explicit refspec, so a single-branch clone of the source gets
    # an origin/<branch> to read, not only a FETCH_HEAD.
    if ref is None:
        rc, out = run(['git', '-C', str(SOURCE), 'fetch', 'origin',
                       pve.tracking_refspec(pve.SOURCE_BRANCH)], SOURCE)
        if rc != 0:
            return rep.close(f"could not fetch origin/{pve.SOURCE_BRANCH} in "
                             f"{SOURCE}:\n{tail(out, repo=repo)}")
    rc, head = run(['git', '-C', str(SOURCE), 'rev-parse',
                    ref or f'origin/{pve.SOURCE_BRANCH}'], SOURCE)
    head_ok = rc == 0
    rep.step('source', f"{pve.SOURCE_BRANCH} @ {head.strip()[:12]}" if head_ok
             else f"could not read {ref or 'origin/' + pve.SOURCE_BRANCH}")

    # The commit the vendored engine -- and so a section 0 catalogue, which
    # moves with it -- was last synced from. Read now: step 2 rewrites it.
    try:
        last_synced = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                                 .read_text(encoding='utf-8')).get('source_commit')
    except (OSError, ValueError):
        last_synced = None

    # 2. The engine, by the consumer's own copy: refresh() takes ROOT from
    # where it sits. It replaces itself and re-runs, so an old copy still
    # ends on the current code.
    argv = [sys.executable, str(engine_tool), 'refresh', str(SOURCE)]
    if ref:
        argv += ['--from-ref', ref]
    # A committed edit to an engine file in tools/ is resolved here, not by
    # the refresh: the repo's own old engine copy runs the refresh and
    # refuses on a hand edit before it replaces itself. So upstream's text
    # goes in for the refresh, and the rules run after it
    # (precedent_local_edits.py). Anything uncommitted stops it untouched.
    edits, unjudged = le.engine_edits(repo, SOURCE)
    dirty = le.uncommitted(repo, edits)
    if dirty:
        for rel in dirty:
            rep.leave(rel, 'a vendored file edited here and not committed. Commit '
                      'it, and the next run keeps, merges or replaces it and says '
                      'which; or undo the edit. Nothing was written')
        rep.step('engine', 'refused: a vendored file has an uncommitted edit')
        return rep.close()
    unjudged = dict(unjudged)
    with le.Swap(repo, [] if unjudged else edits) as swap:
        rc, out = run(argv, repo)
        if rc == 0:
            rep.add_edits(le.resolve(repo, swap), swap.merges)
    if rc != 0:
        if 'hand-edited since the last seed/refresh' in out:
            for line in out.splitlines():
                if line.startswith('  ') and ': ' in line and not line.startswith('    '):
                    name, why = line.strip().split(': ', 1)
                    rel = name if '/' in name else f'tools/{name}'
                    reason = (f' Update Vendors resolves an edited engine file '
                              f'itself, but not this one: {unjudged[rel]}.'
                              if rel in unjudged else '')
                    rep.leave(name, f"hand-edited here and shipped by upstream: {why}.{reason} "
                              f"Send the edit upstream ({le.send_command(repo)}), "
                              "or refresh --force once you have decided it can go")
            rep.step('engine', 'refused: a vendored file was edited here')
            return rep.close()
        return rep.close(f"the engine refresh failed:\n{tail(out, repo=repo)}")
    engine_out = out
    details = diverged_details(out)
    for item in left_block(out):
        what, _, why = item.partition(': ')
        why = why or item
        if what in details and '(listed above)' in why:
            why = why.replace('(listed above)', '(listed below)')
            rep.details[what] = details[what]
        rep.leave(what, why)
    rep.step('engine', engine_summary(out, last_synced))
    # Where the engine actually landed. With no --from-ref the whole update
    # is main's, and a consumer's own older engine copy can resolve some
    # other ref for itself -- then the catalogue would be taken from main
    # and the engine from somewhere else, the half-and-half state this
    # command exists to end (2026-09-28).
    try:
        landed = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                            .read_text(encoding='utf-8')).get('source_commit') or ''
    except (OSError, ValueError):
        landed = ''
    tip = head.strip()
    if ref is None and head_ok and tip and not (
            landed and (tip.startswith(landed) or landed.startswith(tip))):
        return rep.close(f"the engine landed at {landed[:12] or 'an unrecorded commit'}"
                         f", not {pve.SOURCE_BRANCH} @ {tip[:12]}: this repo's "
                         f"own engine copy vendored from another ref. Run this "
                         f"again with --from-ref {tip[:12]} to take "
                         f"{pve.SOURCE_BRANCH}'s engine, then review the diff")
    for tool, calls in unbudgeted_engine_tools(repo, tip):
        rep.leave(f'tools/github_api_budgets.json: {tool}',
                  f'upstream budgets the vendored tools/{tool} at {calls} API '
                  f'call(s) a run and this repo\'s registry has no budget for '
                  f'it, so its runs here are judged against nothing -- add a '
                  f'run budget for it (upstream\'s figure, or this repo\'s own)')
    # A difference precedent.json records as kept on purpose, and a legacy
    # bootstrap wrapper the refresh replaced, are said once each as a note
    # -- never a call to make (precedent_vendor_engine.KEPT_DIVERGENCES_KEY).
    # A self-replacing refresh prints them on both passes.
    for line in dict.fromkeys(l.strip() for l in out.splitlines()):
        if line.startswith('KEPT ON PURPOSE: '):
            rep.step('kept on purpose', line[len('KEPT ON PURPOSE: '):])
        elif line.startswith('PIN NARROWED: '):
            rep.step('kept pin narrowed', line[len('PIN NARROWED: '):])
        elif line.startswith('precedent_vendor_engine refresh: REPLACED '):
            rep.step('replaced', line.split('REPLACED ', 1)[1])
    # A consumer's CI converges to upstream without asking (2026-09-27, see
    # precedent_vendor_engine.CI_CONVERGES_KINDS), so what the refresh
    # replaced or removed is reported here as done, never as a question.
    rep.loud += [l.strip() for l in out.splitlines()
                 if l.strip().startswith('LEFT ALONE: ')
                 and l.strip() not in rep.loud]
    ci = []
    for line in out.splitlines():
        if 'refresh: CI workflow replaced: ' in line:
            ci.append('replaced ' + line.split('replaced: ', 1)[1].split(' ', 1)[0]
                      + ' with the template')
        elif 'refresh: retired .github/workflows/' in line:
            ran = re.search(r'It ran ([^:]+):', line)
            ci.append('removed ' + line.split('retired ', 1)[1].split(' ', 1)[0]
                      + (f' (it ran {ran.group(1)}, which the local push check '
                         f'already runs)' if ran else ''))
    if ci:
        rep.step('CI workflows', '; '.join(dict.fromkeys(ci))
                 + ' -- converged to upstream, nothing to ask')
    # The repoint again, from THIS copy: a consumer whose engine was already
    # current never ran a newer refresh that knows it.
    if 'repointed the practice catalogue' in out or pve.repoint_catalogue_pin(repo):
        rep.step('catalogue pin', f'repointed to {pve.SOURCE_BRANCH} '
                 f'(decided 2026-09-25; nothing to ask)')
    renamed_sources_step(repo, rep, out)

    # 3. The catalogue, where there is one, by the source clone's checkin.py.
    if (repo / 'process' / 'manifest.json').is_file():
        checkin = [sys.executable, str(SOURCE / 'tools' / 'checkin.py')]
        # The same resolution as the engine's, around the mirror and the
        # record: upstream's text in, the layer updated, then the rules.
        edits, unjudged = le.catalogue_edits(repo, SOURCE)
        dirty = le.uncommitted(repo, edits)
        if dirty:
            for rel in dirty:
                rep.leave(rel, 'changed here and not committed. Commit it, and '
                          'the next run keeps, merges or replaces it and says '
                          'which; or undo the change. Nothing was written')
            rep.step('catalogue', 'refused: the vendored tree has an uncommitted change')
            return rep.close()
        swap = le.Swap(repo, [] if unjudged else edits)
        with swap:
            rc, out = run(checkin + ['update', str(SOURCE), '--repo', str(repo)], repo)
            for item in left_block(out):
                rep.leave('a decline to decide again', item)
            if rc == 0:
                rep.step('catalogue', next((l for l in out.splitlines()
                                            if l.startswith('checkin update')),
                                           'updated'))
                resolving = []
                for e in swap.edits:
                    resolving += ['--resolving', e.upstream_rel]
                rc2, out2 = run(checkin + ['record', str(SOURCE), '--repo', str(repo),
                                           '--note', 'Update Vendors'] + resolving, repo)
                if rc2 == 0:
                    rep.add_edits(le.resolve(repo, swap), swap.merges)
        if rc != 0:
            changed = [l.strip()[len('local change: '):] for l in out.splitlines()
                       if l.strip().startswith('local change: ')]
            if changed:
                for rel, why in unjudged:
                    rep.leave(rel, why)
                for p in changed:
                    rep.leave(f'process/upstream/{p}',
                              'changed here since the last sync, and a mirror '
                              'would overwrite it. Update Vendors resolves a '
                              'committed change itself only while it can read '
                              'what the file was mirrored from -- see above -- '
                              f'so send it upstream ({le.send_command(repo)}) '
                              'or let it go')
                rep.step('catalogue', 'refused: the vendored tree has local changes')
                return rep.close()
            return rep.close(f"checkin.py update failed:\n{tail(out, repo=repo)}")
        rc, out = rc2, out2
        if rc != 0:
            lost = lost_files(out)
            if lost:
                for f in lost:
                    rep.leave(f, 'lines this repo added would be lost by the '
                              'update -- carry them upstream, or record with '
                              '--accept-loss if dropping them is deliberate')
                rep.step('catalogue record', 'held: the carry check found lines to lose')
                return rep.close()
            return rep.close(f"checkin.py record failed:\n{tail(out, repo=repo)}")
        rep.step('catalogue record', next((l for l in out.splitlines()
                                           if l.startswith('checkin record')),
                                          'recorded'))
    else:
        # INSTALL.md section 2, step 0: a section 0 install vendors the
        # universal catalogue at its universal source's own path
        # (precedent/universal by default) and replaces it wholesale. Until
        # 2026-09-28 this command skipped it without a word and still said
        # DONE, so a section 0 repo kept its old rules under a new engine; a
        # session caught it only by reading the diff, and copied the
        # catalogue by hand.
        done = vendor_universal_catalogue(repo, rep, head.strip(), last_synced)
        if done is not True:
            return rep.close(done)
        # What was uncommitted there when this began was a failed run's own
        # output -- the step refuses anything else -- and is now replaced:
        # the update's to stage, not someone's work to leave alone.
        rel = universal_catalogue_path(repo)
        if rel:
            before = {p for p in before if not (p.startswith(f'{rel}/practices/')
                                                or p == f'{rel}/{CATALOGUE_SYNC_NAME}'
                                                or p == f'{rel}/precedent-source.json')}

    # After the templates have moved: what they replaced that an update
    # cannot convert for the repo, the install-once file an update can
    # bring forward on its own, and the install-once files it can only
    # report on, since each is the repo's own once written.
    for old, why in legacy_root_docs(repo, head.strip() if head_ok else None, rep):
        rep.leave(old, why)
    gitignore_step(repo, rep, head.strip() if head_ok else None)
    dropped_template_lines_step(repo, rep, head.strip() if head_ok else None)

    # 3b. Where Go update lands, for a repository that has never said.
    # Morgan, 2026-09-27 (strength: decided): every repository lands on
    # pre-staging by default, set on its first update after that day; a
    # person's own identity.json still wins, and a value already here is
    # never changed.
    if pb.ensure_repo_landing(repo):
        rep.step('landing branch', f'{pb.LANDING_SETTING} set to '
                 f'{pb.REPO_LANDING_DEFAULT} in precedent.json (the repository '
                 f'default; a person\'s own identity.json still wins)')

    # 4. The views. A refresh changes what the loader renders.
    #
    # A practice SET renders more than a consumer does: MAP.md and
    # GLOSSARY.md too, and MAP.md lists every engine file. Its deep check is
    # `build_views.py --check`, so an update that adds an engine file and
    # regenerates only the loader block fails its own gate. 2026-09-27: all
    # four of Morgan's sets stopped on exactly that, one new MAP.md row
    # each, fixed by hand. A set has no precedent_sync_views.py anyway --
    # so it gets the full build, the same one its check compares against.
    sync = repo / 'tools' / 'precedent_sync_views.py'
    build = repo / 'tools' / 'build_views.py'
    try:
        kind = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                          .read_text(encoding='utf-8')).get('kind')
    except (OSError, ValueError):
        kind = None
    if kind == 'source' and build.is_file():
        rc, out = run([sys.executable, str(build), '--repo', '.'], repo)
        if rc != 0:
            return rep.close(f"the view build failed:\n{tail(out, repo=repo)}")
        rep.step('views', 'regenerated (loader block, MAP.md, GLOSSARY.md)')
    elif sync.is_file():
        rc, out = run([sys.executable, str(sync), '--repo', str(repo)], repo)
        for found in in_force_nowhere(out):
            rep.ask('IN FORCE NOWHERE', f'{found} -- the rule binds nowhere in '
                    f'this repo. Declare the set it forwards to, or accept that '
                    f'it does not apply here?')
        if rc != 0:
            # A declared source whose clone answers to another name is a
            # call about this repo's own precedent.json, so it is left for
            # the person by name rather than failing the run on a traceback
            # tail. The renamed shared sets never get here any more
            # (renamed_sources_step); anything else that does is named.
            m = SOURCE_NAME_MISMATCH.search(out)
            if m:
                rep.leave(f'precedent.json source {m.group("declared")!r}',
                          f'the clone at {m.group("path")} calls itself '
                          f'{m.group("own")!r} -- declare it by that name, or '
                          f'point `path` at the right clone; the views cannot '
                          f'be regenerated until the two agree')
                rep.step('views', 'not regenerated: a declared source answers '
                         'to another name')
                return rep.close()
            return rep.close(f"the view sync failed:\n{tail(out, repo=repo)}")
        built = generated_full_views(repo)
        if built and build.is_file():
            # A consumer whose MAP.md or GLOSSARY.md says build_views.py
            # generates it gets the full build too: the sync renders the
            # loader block only, so a practice the update stopped
            # materializing stayed linked from the glossary, and the lint
            # failed on the dead links (2026-09-30, three practices).
            rc, out = run([sys.executable, str(build), '--repo', '.'], repo)
            if rc != 0:
                return rep.close(f"the view build failed:\n{tail(out, repo=repo)}")
            rep.step('views', 'regenerated (loader block, and '
                     + ', '.join(built) + ', which build_views.py generates here)')
        else:
            rep.step('views', 'regenerated')

    # After the views, because the view sync writes harness adapters too.
    rebased = rebaseline_vendored_entries(repo)
    if rebased:
        rep.step('manifest baselines', 're-recorded for files this update '
                 'rewrote to exactly what upstream ships: ' + ', '.join(rebased))
    if ensure_headroom_floor(repo):
        rep.step('session-load budget', f'headroom_floor_pct set to '
                 f'{HEADROOM_FLOOR_DEFAULT} in tools/session_load_budgets.json '
                 f'(the default; the full check requires the key)')

    # 4a. The branch tiers. Every repository works through pre-staging ->
    # staging -> main, so a missing tier is made here rather than reported
    # (Morgan, 2026-09-27, strength: decided: "Can we make sure update
    # vendors checks for this and if they don't exist create it").
    # ensure_tiers makes staging from pre-staging (or the old staging name),
    # pre-staging from staging, and both from main when neither exists. It
    # is the one thing this command pushes: a new branch at a commit origin
    # already has, never a change to one that exists.
    tiers_step(repo, rep)

    # Staged before the check, so it judges what the commit will hold.
    adopted = adopt_engine_output(repo, before, head.strip())
    if adopted:
        before = before - set(adopted)
        rep.step('engine, written ahead', f'{len(adopted)} uncommitted path(s) '
                 f'already held the pinned engine (a source refresh ran first); '
                 f'staged as this update\'s: ' + ', '.join(adopted))
    n = stage_update(repo, before)
    rep.step('staged', f'{n} path(s) this update wrote or deleted'
             + (f'; {len(before)} already uncommitted before it ran, left as they were'
                if before else ''))

    # 4b. Files that still name what the refresh deleted: the full check's
    # rename-updates-links refuses each one at the Promote, so they are
    # worked here (retired_mentions).
    for where, gone in retired_mentions(repo, engine_out):
        rep.leave(where, f'still names {gone}, which this update deleted -- '
                  f'repoint or remove the mention; the full check '
                  f'(rename-updates-links) refuses it at the Promote to staging')

    # Citations of what the update withdrew or reworded, in THIS repo's
    # own files. A consumer is where a renamed practice's old name survives
    # longest: its AGENTS.md and docs were written against the name it had
    # then, and nothing the refresh touches rewrites them.
    # practice: practice-change-propagates
    cited = citations(repo)
    if cited is None:
        rep.step('citations', 'could not be looked up -- run '
                 'tools/precedent_practice_refs.py --withdrawn before pushing')
    else:
        fix, read = cited
        for where, why in fix:
            rep.leave(where, why)
        rep.step('citations',
                 (f'{len(fix)} live citation(s) of a withdrawn practice to fix '
                  f'(listed below)' if fix else
                  'no live citation of a withdrawn practice to fix')
                 + (f'; {len(read)} citation(s) of a practice reworded or '
                    f'withdrawn -- read each, it may describe the old rule '
                    f'or name the old slug: '
                    + ', '.join(read) if read else ''))

    # 5. The repo's own check, at the tier of the branch the update lands
    # on -- the gate before any push. Into pre-staging that is the fast
    # checks on what the update changed; the full check waits for the
    # Promote to staging (Morgan, 2026-09-27, strength: decided: "The point
    # of pre-staging is to move fast, so I want the 10 minute checks to
    # happen at the staging level, not pre-staging." Practice:
    # checks-follow-the-tier).
    check = repo / 'tools' / 'precedent_push_check.py'
    try:
        landing = pb.landing_branch(repo)[0]
    except Exception:                                          # noqa: BLE001
        landing = None
    argv = [sys.executable, str(check)]
    if landing:
        argv += ['--push-command', f'origin HEAD:{landing}']
    label = f'check for {landing}' if landing else 'deep check'
    if skip_check:
        rep.step(label, 'skipped (--skip-check) -- run it before pushing')
    elif check.is_file():
        stamped = stamp_headers(repo)
        if stamped:
            rep.step('file headers', 'stamped before the check, as the commit '
                     'would: ' + ', '.join(stamped))
        rc, out = check_with_merge_fallback(repo, rep, argv, label)
        if rc != 0:
            return rep.close(f"the {label} is red:\n{tail(out, repo=repo)}")
        rep.step(label, 'passed')
    else:
        rep.step(label, 'this repo has no tools/precedent_push_check.py')
    return rep.close()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Update Vendors as one command (spec/ONE_COMMAND_UPDATE_PLAN.md).')
    ap.add_argument('--repo', default='.', help='the consuming repo (default: .)')
    ap.add_argument('--skip-check', action='store_true',
                    help='leave the deep check out; it still gates the push')
    ap.add_argument('--from-ref', default=None,
                    help='vendor this commit of the source instead of its '
                         f'origin/{pve.SOURCE_BRANCH} -- for testing a commit')
    a = ap.parse_args(argv)
    repo = pathlib.Path(a.repo).resolve()
    if repo == SOURCE:
        print("precedent_update FAIL: --repo is this BestPractice clone itself. "
              "Run it from the consuming repo: "
              "python3 ../BestPractice/tools/precedent_update.py --repo .")
        return FAILED
    return update(repo, skip_check=a.skip_check, ref=a.from_ref)


if __name__ == '__main__':
    sys.exit(main())

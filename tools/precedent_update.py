#!/usr/bin/env python3
"""Update Vendors as one command: run from the BestPractice clone against a consuming repo, it refreshes the engine and catalogue, regenerates the views and runs the deep check, then reports DONE, LEFT FOR YOU (only that repo's own calls) or FAILED (spec/ONE_COMMAND_UPDATE_PLAN.md)

precedent_update.py -- "Update Vendors" as one command: every step of
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
  1. the source clone fetches the branch every install follows, and on
     main takes the newest commit whose GitHub test passed, saying so when
     that is not the newest (source_commit; --take-anyway takes a named
     commit on the person's word), and the
     commit this run takes is recorded: until a run reports DONE, a rerun
     takes that same commit, so an update worked over several rounds does
     not chase a moving branch (--move takes the newest commit instead)
  2. the engine refresh (the consumer's own copy, which replaces itself and
     runs a second pass), with each committed local edit to an engine file
     resolved around it by precedent_local_edits.py -- kept, or replaced
     by upstream's with the commit holding it named -- then the catalogue-pin repoint and the renamed
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
  3c. for a person whose own identity.json lands them straight on staging,
     in a repository whose precedent.json does not make pre-staging the
     landing branch for others (switched to staging first when they are
     its only maintainer), while origin still has pre-staging: its waiting work merged into staging (--land's
     composition, quick checks), this repo's own instructions and links
     that send work to pre-staging repointed, and the branch offered for
     deletion as a link once it holds nothing staging lacks -- never
     deleted. Silent for everyone else
  4. the views regenerated -- the loader block, and in a practice set
     MAP.md and GLOSSARY.md too; in a repository that uses Precedent, a
     hand-written MAP.md or GLOSSARY.md moved into MAP.source.md /
     GLOSSARY.source.md word for word and generated from then on (or left
     as it was, and said, when that would lose text) -- then manifest baselines moved for files
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
  0  DONE -- nothing is left. Commit on a branch of its own (DONE prints
     the command when the checkout sits on a tier branch), then land it on
     your landing branch.
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
reports. Those stay with the session, which lands the update the way the
repository lands work, where the authorization already lives.
"""
import argparse
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve()
SOURCE = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import precedent_vendor_engine as pve  # noqa: E402
import precedent_branches as pb  # noqa: E402
import precedent_local_edits as le  # noqa: E402

DONE, LEFT, FAILED = 0, 1, 2


def rebaseline_vendored_entries(repo, rewritten=()):
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
    registry-source-of-truth).

    `rewritten` (2026-10-02): the paths THIS run changed -- dirty now and
    not before it began. An entry instantiated from a template
    (upstream_path under templates/) whose file is among them is
    re-recorded too: the update rewrote it on purpose, as a migration onto
    the loader rewrites AGENTS.md, .claude/settings.json and .gitignore, so
    its old hash is stale by construction exactly like the mirror's. Until
    then such a file kept the classic install's baseline, the pre-staging
    check never ran the audit, and the first Debut refused it as DRIFT."""
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
            ours = (rel in rewritten and up.startswith('templates/')) \
                or _is_generated_view(repo, rel)
            if not ours and (not up or not (repo / tree / up).is_file()
                             or (repo / tree / up).read_bytes() != f.read_bytes()):
                continue
        cur = hashlib.sha256(f.read_bytes()).hexdigest()
        if e.get('local_sha256') and e['local_sha256'] != cur:
            e['local_sha256'] = cur
            done.append(rel)
    if done:
        mf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                      encoding='utf-8')
    return done


def _is_generated_view(repo, rel):
    """True when `rel` is a view a generator writes wholesale: listed in the
    repo's tools/generated_files.json, or opening with a `generated_by:`
    label. Its content answers to that generator's own --check, not to a
    recorded hash, so its baseline is re-recorded whenever it differs.
    2026-10-04, a consumer: MAP.md, regenerated between two runs after its
    source's headings were fixed, kept the hash an earlier run recorded,
    and the practice audit failed it as DRIFT; the only way past re-recorded
    every other baseline too."""
    try:
        reg = json.loads((repo / 'tools' / 'generated_files.json').read_text(
            encoding='utf-8')).get('files') or []
        if any(isinstance(x, dict) and x.get('path') == rel and not x.get('part')
               for x in reg):
            return True
    except (OSError, ValueError, AttributeError):
        pass
    if not rel.endswith('.md'):
        return False
    try:
        head = (repo / rel).read_text(encoding='utf-8', errors='ignore')[:3000]
    except OSError:
        return False
    if not head.startswith('---\n'):
        return False
    end = head.find('\n---', 4)
    return bool(re.search(r'^generated_by:[ \t]*\S', head[:end if end > 0 else len(head)],
                          re.M))


# A DEAD LINK THE OLD INSTALL PACK WROTE (2026-10-06). It opened a repo's
# scrub blocklist with "# Left blank at install ([`blank-blocklist`](personal/
# README.md#blank-blocklist)): ...". The practice is retired and
# personal/README.md exists nowhere, so every repository installed that way
# carries the same dead link; one consumer fixed it by hand by dropping the
# link and keeping the sentence. No live template writes it any more, so
# Update Vendors makes the same edit wherever it is still there.
_DEAD_BLANK_BLOCKLIST_LINK = re.compile(
    r' ?\(\[`blank-blocklist`\]\(personal/README\.md#blank-blocklist\)\)')


def drop_dead_blank_blocklist_link(repo):
    """-> the repo-relative files under process/ it rewrote, dropping the
    retired install pack's dead `blank-blocklist` link and keeping the
    sentence around it. Nothing else in a file changes."""
    fixed = []
    base = repo / 'process'
    if not base.is_dir():
        return fixed
    for f in sorted(base.rglob('*')):
        if not f.is_file() or f.suffix not in ('.txt', '.md'):
            continue
        try:
            text = f.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        new = _DEAD_BLANK_BLOCKLIST_LINK.sub('', text)
        if new != text:
            f.write_text(new, encoding='utf-8')
            fixed.append(str(f.relative_to(repo)))
    return fixed


def ensure_scrub_blocklist_decision(repo):
    """-> 'null' when it recorded `scrub_blocklist: null` for a public repo,
    'ask' when the repo has to decide, None when nothing is owed. 'ask' is
    not listed as left for the person here: the practice audit, which runs
    at every pre-staging push of a consumer, refuses it with the remedy in
    its own words, so the update would only be saying it twice.

    practice_audit.py fails a manifest with no `scrub_blocklist` key whose
    default process/scrub_blocklist.txt does not exist: configured by
    default, missing on disk, a scrub that did not run. Older engines
    skipped it, so a classic install that never needed a list first met
    the failure at its Debut after a migration (2026-10-02). For a repo
    that declares itself public in precedent.json, every tracked file is a
    publication already and there is no private vocabulary for the
    vendored tree to leak, so the update records the opt-out with its
    reason. Any other repo is told, never decided for: a private repo may
    have words to list."""
    mf = repo / 'process' / 'manifest.json'
    try:
        data = json.loads(mf.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    up = data.get('upstream')
    if not isinstance(up, dict) or 'scrub_blocklist' in up \
            or (repo / 'process' / 'scrub_blocklist.txt').exists():
        return None
    try:
        vis = json.loads((repo / 'precedent.json').read_text(encoding='utf-8')) \
            .get('visibility')
    except (OSError, ValueError, AttributeError):
        vis = None
    if vis != 'public':
        return 'ask'
    up['scrub_blocklist'] = None
    up['_scrub_blocklist_note'] = (
        'null on purpose, written by Update Vendors: precedent.json declares '
        'this repo public, so it has no private vocabulary for the vendored '
        'tree to leak. Name a blocklist file here instead if that changes.')
    mf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                  encoding='utf-8')
    return 'null'


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



def seed_baseline_approvals(repo, data, path):
    """Record every budget in force as a `"strength": "baseline"` approval in
    a registry Update Vendors has JUST seeded, so budget-within-approval
    binds from the first run instead of reporting SKIPPED for ever. Only
    there: in a registry that already existed, a number may have been raised
    by hand, and writing it down as approved would launder the raise --
    approval_gap() names that case for a person instead. Reported from a
    consumer, 2026-10-06: no approved_budgets, so the check skipped on every
    run and nothing said so."""
    if not isinstance(data, dict) or isinstance(data.get('approved_budgets'), dict):
        return False
    try:
        import build_views as _bv
        # The repo's registry, not the one beside this clone's engine
        # (effective_budgets says why).
        now = _bv.effective_budgets(repo, registry=path)
    except Exception:                                        # noqa: BLE001
        return False
    import time as _time
    day = _time.strftime('%Y-%m-%d')
    data['approved_budgets'] = {
        k: {'max': v, 'strength': 'baseline',
            'approved_by': f'baseline {day}: seeded by Update Vendors with the '
                           f'registry, at the values in force'}
        for k, v in sorted(now.items()) if isinstance(v, int)}
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return True


def approval_gap(repo):
    """-> a sentence for the report when the registry exists and has no
    approved_budgets (so budget-within-approval skips every run), else None."""
    path = repo / 'tools' / 'session_load_budgets.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or isinstance(data.get('approved_budgets'), dict):
        return None
    return ('tools/session_load_budgets.json has no approved_budgets, so the '
            'check that no budget was raised without approval skips on every '
            'run. Ask the person to confirm the numbers in force are ones '
            'they chose, then record each as "strength": "baseline" '
            '(practice: session-load-budget)')


def ensure_session_load_registry(repo):
    """Seed tools/session_load_budgets.json in a repository that has none.
    -> {surface: measured tokens} when it wrote one, else None.

    The session-load-budget check binds only where the registry exists, so a
    repository installed without one skipped it on every run, and a skip
    reads like a pass. A consumer's instructions file grew to about 38,000
    tokens that way, loaded into every session with no ceiling, and nobody
    was told (Alex, 2026-10-04: "If it is already a best practice, why
    didn't we adopt?"). New practice sets have been seeded at bootstrap
    since 2026-09-22; this is the same seed for a repository that uses
    Precedent. Each ceiling is what the surface measures now plus ~20%:
    a watermark declaring the status quo, never a judgment that it is the
    right size -- reducing it is the reduction pass the practice asks for.

    Called only by the run that reports DONE (seed_budgets_step), on the
    files that run produced."""
    path = repo / 'tools' / 'session_load_budgets.json'
    if path.exists():
        return None
    import precedent_bootstrap_source as _pbs
    _pbs._write_session_load_budget(repo, occasion='Update Vendors')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    seed_baseline_approvals(repo, data, path)
    out = {}
    for rel, e in (data.get('surfaces') or {}).items():
        m = re.match(r'(\d+) tokens', e.get('_note', ''))
        out[rel] = int(m.group(1)) if m else None
    return out

# precedent_resolve.check_source_manifest's refusal, as the view sync prints it.
SOURCE_NAME_MISMATCH = re.compile(
    r"the source at (?P<path>\S+) calls itself '(?P<own>[^']+)' in its \S+, "
    r"but this repository declares it as '(?P<declared>[^']+)'")
_REPOINTED = re.compile(r"repointed precedent\.json source '([^']+)' to '([^']+)'")


def tidy_field_order(repo, kind):
    """Put this repository's OWN practice files in the field order the spec
    sets, and -> the repo-relative paths it rewrote. Never refuses anything.

    WHY (Morgan, 2026-10-05): "be flexible and graceful in grandfathering in
    old practices, updating them as needed but not stopping them from being
    used." The field-order check only warns, so something has to do the
    updating, and the update is where every repository already takes new
    format rules. Only whole field blocks move (frontmatter_yaml.reorder_fields);
    a file whose order the fixer cannot settle -- a repeated key -- is left
    for the warning to name. The source files are tidied, never a
    materialized copy: a project repo's own practices live in
    local/practices/ and the view sync copies them into practices/, so
    tidying the copy would be undone by the next sync (practice:
    format-rules-grandfather)."""
    try:
        import frontmatter_yaml as fy
    except ImportError:
        return []
    root = pathlib.Path(repo)
    files = sorted((root / 'local' / 'practices').glob('*.md'))
    if kind == 'source':
        files += sorted((root / 'practices').glob('*.md'))
    done = []
    for f in files:
        try:
            text = f.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        if not fy.field_order_problem(text):
            continue
        fixed = fy.reorder_fields(text)
        if fixed != text and not fy.field_order_problem(fixed):
            f.write_text(fixed, encoding='utf-8')
            done.append(f.relative_to(root).as_posix())
    return done


def brought_sets_step(rep, fetch=None, repo=None):
    """Clone or pull the sets the person's individual set brings, before
    the views are synced against them. Session start does this
    (precedent_source_bootstrap.sources_from_brings), but only from an engine
    that has the step: the first update that brings the step in syncs in a
    session that started without it, and a brought set not on disk read as
    every one of its rules lost (2026-10-04, a consumer's first update after
    the ladder moved into a brought set). Reports what it did; never fails
    the update -- a set it cannot fetch is said, and the sync judges the rest."""
    if fetch is None:
        try:
            import precedent_source_bootstrap as psb
            fetch = (lambda: psb.sources_from_brings(skip=[repo])) if repo \
                else psb.sources_from_brings
        except Exception:                                   # noqa: BLE001
            return
    try:
        results = fetch()
    except Exception as e:                                  # noqa: BLE001
        results = [('brought sets', False, f'{type(e).__name__}: {e}')]
    if not results:
        return
    try:
        import precedent_source_bootstrap as psb
        on_branch = psb.READ_ON_ITS_BRANCH
    except Exception:                                       # noqa: BLE001
        on_branch = None
    # A set read from a working branch is in force as that branch has it,
    # and the report says which branch, rather than calling it current.
    branched = [(n, o) for n, ok, o in results
                if ok and on_branch and str(o).startswith(on_branch)]
    good = [n for n, ok, o in results
            if ok and not (on_branch and str(o).startswith(on_branch))]
    bad = [(n, o) for n, ok, o in results if not ok]
    if good:
        rep.step('brought sets', 'on disk and current: ' + ', '.join(good))
    if branched:
        rep.step('brought sets on a working branch',
                 '; '.join(f'{n} {o}' for n, o in branched))
    for name, out in bad:
        rep.leave(f'brought set {name}', f'could not be fetched ({str(out)[-200:]}), '
                  f'so its rules are not in force for this sync; attach it '
                  f'and run this again')


def removed_links_step(rep, out):
    """List, for the person, each link in this repo's own files that the
    sync reported dangling: to a practice the sync removed, or an earlier
    update did (2026-10-04: a hook's link from a rename weeks before went
    unlisted, and the push after the update was refused for it), with no
    successor here to repoint it to -- the repo's call."""
    for line in re.findall(r'precedent_sync_views: (\S+:\d+): links `([^`]+)`, '
                           r'which (this sync removed|is not in practices/ -- an '
                           r'earlier update removed it) -- (.*?)\. Repoint', out):
        when = ('this update removed' if line[2] == 'this sync removed'
                else 'an earlier update removed')
        rep.leave(line[0], f'links `{line[1]}`, which {when} '
                           f'({line[3]}). Repoint it or remove it')


def retired_sources_step(repo, rep):
    """Drop every declared set that says it is retired, or that GitHub
    reports archived, when every active rule it holds is in force in another
    declared source; keep the rest and name the rule each would lose.
    Morgan, 2026-10-06 (strength: decided): "have update vendors and very
    deep check see if any repos are declared to be included that no longer
    exist and remove them", option C. GitHub's "Not Found" is a note and
    never a drop: it is also what lost access looks like."""
    archived, notes = pve.archived_declared_sources(repo)
    dropped, kept = pve.drop_retired_sources(repo, archived)
    names = [n for n, _p, _w in dropped]
    for name, path, why in dropped:
        if getattr(pve, 'DELETED_WHY', '\0') in why:
            rep.step('retired set', f'{name} ({path}) is no longer declared in '
                     f'precedent.json: {why}')
            continue
        rep.step('retired set', f'{name} ({path}) is no longer declared in '
                 f'precedent.json: {why}, and every active rule it held is in '
                 f'force in another declared source')
    for succ, froms, brought in (pve.undeclared_successors(repo, dropped)
                                 if hasattr(pve, 'undeclared_successors') else []):
        whose = ', '.join(froms)
        if brought:
            rep.step('retired set', f'some of {whose}\'s rules now live in '
                     f'{succ}, which this repository does not declare; your '
                     f'individual set brings it, so they are in force for you '
                     f'only -- declare it in precedent.json if anyone else '
                     f'works here')
            continue
        rep.leave(f'precedent.json: declare {succ}?',
                  f'some of {whose}\'s rules now live in {succ}, which this '
                  f'repository does not declare and your individual set does '
                  f'not bring, so those rules are no longer in force here. '
                  f'Declaring it in precedent.json puts them in force for '
                  f'everyone who works in this repository; bringing it from '
                  f'your individual set covers only you. Declare it, bring it, '
                  f'or decide this repository does without them')
    for name, path, why, lost in kept:
        rep.leave(f'precedent.json source {name!r}',
                  f'{why}, but {", ".join(lost)} is in force nowhere else, '
                  f'so it stays declared -- move those rules, or decide to let '
                  f'them go, then run Update Vendors again')
    for name in pve.drop_deleted_brings(repo) if hasattr(pve, 'drop_deleted_brings') else []:
        rep.step('retired set', f'{name} is no longer in precedent-source.json '
                 f'`brings`: it is on the list of deleted sets')
        names.append(name)
    for where, name in (pve.person_names_deleted(repo)
                        if hasattr(pve, 'person_names_deleted') else []):
        rep.leave(where, f'still names {name}, which is on the list of deleted sets. '
                         f'Nothing loads it any more; run Update Vendors in your '
                         f'individual set to drop it there')
    for where, text, why in prose_about_dropped_sets(repo, names):
        rep.leave(where, f'{why}: "{text}" -- reword it or remove it')
    proxied = [n for n in notes if n.endswith(getattr(pve, 'PROXY_NOTE', '\0'))]
    notes = [n for n in notes if n not in proxied]
    if proxied:
        # Every run in a hosted session, for every set: one plain line, not
        # a warning (2026-10-07, from a consuming repository's two updates).
        rep.step('retired set', 'archive status not checked here (this '
                 'environment\'s proxy refuses GitHub\'s API); a set that '
                 'marks itself retired is still found')
    if notes:
        rep.step('retired set', f'{len(notes)} declared set(s) could not be '
                 f'asked on GitHub whether they are archived, so they stay '
                 f'declared; a set that marks itself retired is still found '
                 f'(first: {notes[0]})')
    return names


# A dropped set lives on in the repository's own prose: a comment in
# precedent.json describing "Three team sets", AGENTS.md telling a session
# what to do when "four of five sources" resolve (a consuming repository's
# two updates, 2026-10-07; one was fixed by hand, a band-aid). The sync
# regenerates its own blocks, so what is left is the hand-written text:
# every string in precedent.json (its comments, a kept_template_divergences
# reason, any other note) and the Markdown files at the repository's root,
# outside any generated block (generated_blocks.py, the one definition of
# where those are). Listed for the person, never edited -- whether a
# sentence still holds is a reading, not a pattern.
#
# 2026-10-08, from the same repository's next update: a set is also named
# by its family ("the two precedent-shared-* sets"), by its name before the
# 2026-09-28 rename (precedent-team-...), and, once no shared set is left,
# by "the shared sources" -- each was found by hand after a clean scan.
_SET_COUNT_RE = re.compile(
    r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b'
    r'(?:\s+of\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+))?'
    r'(?:\s+[\w*-]+){0,2}?\s+(?:practice\s+)?(?:sets|sources)\b', re.I)
_SET_FAMILY_RE = re.compile(r'\b([a-z0-9]+(?:-[a-z0-9]+)*-)\*')
_SHARED_SETS_RE = re.compile(r'\bshared\s+(?:practice\s+)?(?:sets|sources)\b', re.I)
# Fields of a precedent.json source the engine owns, not prose.
_SOURCE_FIELDS = frozenset({'name', 'path', 'level', 'repo_url'})


def _dropped_set_matcher(names, shared_left):
    """-> a function line -> (start, why) for the first way `line` speaks of
    a dropped set, or None: by name, by its pre-rename name, by a family
    wildcard that covers it, by counting the sets, or -- when no shared set
    is left declared -- by speaking of the shared sets at all."""
    team, shared = (getattr(pve, 'TEAM_SET_PREFIX', 'precedent-team-'),
                    getattr(pve, 'SHARED_SET_PREFIX', 'precedent-shared-'))
    old = {team + n[len(shared):]: n for n in names if n.startswith(shared)}

    def match(line):
        for n in names:
            if n in line:
                return line.index(n), f'names {n}, which this update stopped declaring'
        for o, n in old.items():
            if o in line:
                return line.index(o), (f'names {o}, the name {n} had before '
                                       f'2026-09-28, which this update stopped '
                                       f'declaring')
        for m in _SET_FAMILY_RE.finditer(line):
            covered = [n for n in names if n.startswith(m.group(1))] + \
                      [n for o, n in old.items() if o.startswith(m.group(1))]
            if covered:
                return m.start(), (f'speaks of {m.group(0)}, which covers '
                                   f'{", ".join(sorted(set(covered)))}, '
                                   f'which this update stopped declaring')
        m = _SET_COUNT_RE.search(line)
        if m:
            return m.start(), (f'counts the declared sets, and this update '
                               f'dropped {len(names)}')
        m = None if shared_left else _SHARED_SETS_RE.search(line)
        if m:
            return m.start(), ('speaks of the shared sets, and this repository '
                               'declares none now')
        return None
    return match


def _excerpt(text, at, width=160):
    """-> up to `width` characters of `text` that show position `at`."""
    text = text.strip()
    if len(text) <= width:
        return text
    lo = max(0, min(at - width // 3, len(text) - width))
    return ('...' if lo else '') + text[lo:lo + width].strip() + \
        ('...' if lo + width < len(text) else '')


def _precedent_json_strings(data, at=()):
    """-> [(key path, text)] for every string value in precedent.json except
    the engine-owned fields of a `sources` entry."""
    if isinstance(data, dict):
        out = []
        for k, v in data.items():
            if len(at) == 2 and at[0] == 'sources' and k in _SOURCE_FIELDS:
                continue
            out += _precedent_json_strings(v, at + (k,))
        return out
    if isinstance(data, list):
        return [x for i, v in enumerate(data)
                for x in _precedent_json_strings(v, at + (i,))]
    return [(at, data)] if isinstance(data, str) else []


def prose_about_dropped_sets(repo, dropped):
    """-> [(path:line, text, why)] for each hand-written string in
    precedent.json, and each hand-written line in a root Markdown file, that
    speaks of a set this update dropped (_dropped_set_matcher) or counts the
    declared sets or sources. [] when nothing was dropped."""
    if not dropped:
        return []
    import generated_blocks
    repo = pathlib.Path(repo)
    names = sorted({str(n) for n in dropped if n}, key=len, reverse=True)
    pj = repo / 'precedent.json'
    try:
        raw = pj.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        raw = None
    try:
        cfg = json.loads(raw) if raw is not None else None
    except ValueError:
        cfg = None
    srcs = cfg.get('sources') if isinstance(cfg, dict) else None
    import precedent_resolve as pr
    shared_left = any(pr.declared_level(s) == 'shared' for s in srcs or [])
    match = _dropped_set_matcher(names, shared_left)
    out = []
    if cfg is not None:
        lines = raw.splitlines()
        for at, text in _precedent_json_strings(cfg):
            hit = match(text)
            if not hit:
                continue
            # The line it is written on: as the file spells it, or escaped.
            needles = {json.dumps(text, ensure_ascii=False)[1:-1][:80],
                       json.dumps(text)[1:-1][:80]}
            n = next((i for i, line in enumerate(lines, 1)
                      if any(x and x in line for x in needles)), None)
            where = (f'precedent.json:{n}' if n else
                     'precedent.json ' + '.'.join(map(str, at)))
            out.append((where, _excerpt(text, hit[0]), hit[1]))
    elif raw is not None:
        for i, line in enumerate(raw.splitlines(), 1):   # unparsable: as text
            hit = match(line)
            if hit:
                out.append((f'precedent.json:{i}', _excerpt(line, hit[0]), hit[1]))
    for f in sorted(repo.glob('*.md')):
        try:
            lines = f.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        blocks = generated_blocks.spans(lines)
        if f.suffix == '.md' and re.search(r'GENERATED|generated by',
                                           '\n'.join(lines[:5])) \
                and not any(a < 5 for a, _b in blocks):
            continue                     # a whole generated view: the sync redoes it
        hidden = generated_blocks.mask(lines)
        for i, line in enumerate(lines, 1):
            if hidden[i - 1]:
                continue
            hit = match(line)
            if hit:
                out.append((f'{f.name}:{i}', _excerpt(line, hit[0]), hit[1]))
    return out


_SOURCE_DROPPED_REFUSAL = re.compile(
    r"whose source name is not among the sources precedent\.json declares -- "
    r"(.*?)\. THREE things", re.S)


def removals_this_update_caused(out, dropped):
    """-> the practices the view sync refused to remove, when every one was
    recorded from a set this update itself dropped (retired_sources_step);
    [] otherwise -- any other refusal, including one about a source still
    declared, is left to the person."""
    m = _SOURCE_DROPPED_REFUSAL.search(out or '')
    if not m or not dropped or 'whose source is still declared' in out:
        return []
    pairs = re.findall(r'(\S+) \(recorded from ([^)]+)\)', m.group(1))
    if pairs and all(src in set(dropped) for _s, src in pairs):
        return [s for s, _src in pairs]
    return []


def maintainers_step(repo, rep):
    """Name the repository's code owners when it names none: everyone who
    can edit it on GitHub now, in precedent.json's `maintainers`
    (pve.seed_maintainers). Morgan, 2026-10-06 (strength: decided): defined
    at "setup, vendored in, upgraded, migrated, etc" -- a starting default
    the repository changes after."""
    written, how = pve.seed_maintainers(repo)
    if written:
        rep.step('code owners', f'named {", ".join("@" + w for w in written)} '
                 f'in precedent.json\'s maintainers ({how}); change the list '
                 f'there any time -- it is never rewritten once set')
    # A single owner's own zone, offered for the records nobody's identity
    # reaches (2026-10-08) -- a question for the person, never written here.
    try:
        offer = pve.timezone_offer(repo)
    except Exception:                                          # noqa: BLE001
        offer = None
    if offer:
        rep.ask('time zone', offer)


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
    # The rename's one loose end outside the repository: an environment
    # variable still naming the old paths, which the session check then
    # warned about at every turn (reported 2026-10-03). The variable has not
    # been needed since 2026-09-30, so the note says to delete it. A note, not
    # a call left for the person: an environment setting never holds up a
    # repository's update.
    stale = [e.split('=', 1)[0] for e in
             os.environ.get('PRECEDENT_FRESHNESS_ALSO', '').split(';')
             if 'precedent-team-' in e]
    if stale:
        rep.step('environment', 'PRECEDENT_FRESHNESS_ALSO still names the retired '
                 'precedent-team-* sets (' + ', '.join(stale) + '). It has not been '
                 'needed since 2026-09-30 -- the freshness guard checks every '
                 'declared set on its own -- so delete it from your environment\'s '
                 'settings rather than repointing it')
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


def level_alias_step(repo, rep):
    """Rewrite every `"level": "team"` in precedent.json to `"shared"`, on
    every run that finds one, and say so in one line. The old word still
    resolves; the file just stops saying something the tools have to
    translate (pve.retire_level_aliases). Runs after renamed_sources_step,
    which already re-levels a renamed set, so this names the rest. The
    write is staged with the rest of the update (stage_update)."""
    names = pve.retire_level_aliases(repo)
    if names:
        rep.step('source levels', 'precedent.json now declares '
                 + ', '.join(names) + ' at level "shared", the current word '
                 'for the older "team" -- the same level, nothing to decide')


# The engine's WARN for a file that still names one it just deleted
# (precedent_vendor_engine._warn_about_dependents).
_MENTION = re.compile(r"^WARN: precedent_vendor_engine: (?P<gone>\S+) was .+?, "
                      r"and (?P<path>\S+?):(?P<line>\d+) still names it -- ")


# Files whose mentions of a mirrored engine path are commands a session
# runs or a harness allows, not prose about the past.
MOVED_ENGINE_FILES = ('AGENTS.md', 'CLAUDE.md', '.claude/settings.json')
MIRRORED_TOOL_RE = re.compile(r'(?<![\w./-])process/upstream/tools/([\w.-]+)')


def _own_shell_scripts(repo):
    """-> the repo's own tracked *.sh files: not .claude/hooks/, which the
    engine vendors and rewrites, not an engine file it received, and not a
    mirrored copy (precedent_resolve.mirrored_prefixes), which this repo may
    not edit -- a rewrite there reads to the catalogue sync as a local
    change, and it refuses the whole update over it."""
    import precedent_resolve as pr
    r = subprocess.run(['git', '-C', str(repo), 'ls-files', '*.sh'],
                       capture_output=True, text=True)
    try:
        received = set(json.loads((repo / 'tools' / 'ENGINE_MANIFEST.json')
                                  .read_text(encoding='utf-8')).get('files') or ())
    except (OSError, ValueError, AttributeError):
        received = set()
    mirrors = tuple(pr.mirrored_prefixes(repo) or ())
    return [rel for rel in (r.stdout.split() if r.returncode == 0 else [])
            if not rel.startswith('.claude/hooks/')
            and not (mirrors and rel.startswith(mirrors))
            and not (rel.startswith('tools/') and rel[len('tools/'):] in received)]


def repoint_moved_engine_mentions(repo):
    """-> ([(rel, n)] repointed, [(rel, line_no, path)] stranded): rewrite
    `process/upstream/tools/X` to `tools/X` in AGENTS.md, CLAUDE.md,
    .claude/settings.json and the repo's own shell scripts, wherever
    tools/X is there and the mirrored copy is gone. A guarded fallback (a
    `[ -f` test, or a line naming tools/X beside it) is left alone, and so
    is a generated block, which build_views.py rewrites. A call to a file
    tools/ does not hold either is stranded: it is returned, not rewritten.

    The shell scripts since 2026-10-01, from a consumer's Update Vendors:
    its tools/bootstrap.sh ran `process/upstream/tools/checkin.py` and
    `practice_audit.py` after the update removed both, and the update said
    only that the file "diverged from templates/bootstrap.sh" -- those
    steps then stopped, silently.

    2026-10-01, from a consumer's Update Vendors: the catalogue copy dropped
    process/upstream/tools/, and AGENTS.md went on telling sessions to run
    practice_audit.py at that mirrored path in three places,
    with .claude/settings.json allowing it -- found only by running it and
    getting "No such file". The new path is certain, so it is written, and
    the staged diff shows it."""
    import generated_blocks
    import precedent_check as pc
    done, stranded = [], []
    for rel in list(MOVED_ENGINE_FILES) + _own_shell_scripts(repo):
        f = repo / rel
        try:
            text = f.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.split('\n')
        mask = generated_blocks.mask(lines) if rel.endswith('.md') else [False] * len(lines)
        n = 0
        for i, line in enumerate(lines):
            if mask[i]:
                continue

            def swap(m, line=line, i=i):
                name = m.group(1)
                # tools/X naming itself would be a script that runs itself:
                # the old install's wrapper tools/bootstrap.sh, which calls
                # upstream's own bootstrap at the mirrored path, is replaced
                # whole by the template step, never repointed.
                if (repo / 'process' / 'upstream' / 'tools' / name).exists() \
                        or f'tools/{name}' == rel \
                        or pc.is_guarded_fallback(rel, line, m.group(0)):
                    return m.group(0)
                if not (repo / 'tools' / name).is_file():
                    stranded.append((rel, i + 1, m.group(0)))
                    return m.group(0)
                return f'tools/{name}'
            new = MIRRORED_TOOL_RE.sub(swap, line)
            if new != line:
                n += 1
                lines[i] = new
        if n:
            text = '\n'.join(lines)
            if rel == '.claude/settings.json':
                text = _without_duplicate_permissions(text)
            f.write_text(text, encoding='utf-8')
            done.append((rel, n))
    return done, stranded


def _without_duplicate_permissions(text):
    """settings.json's text with each permission list keeping one copy of
    each entry, first place kept. Repointing process/upstream/tools/X to
    tools/X made a second copy wherever the repo already allowed tools/X --
    a consumer had both forms of its doc_lint.py allow rules twice
    (2026-10-04). Unparseable, or nothing repeated: the text as it was."""
    try:
        data = json.loads(text)
        perms = data.get('permissions') or {}
    except (ValueError, AttributeError):
        return text
    changed = False
    for key in ('allow', 'ask', 'deny'):
        rules = perms.get(key)
        if isinstance(rules, list):
            kept = list(dict.fromkeys(r for r in rules if isinstance(r, str)))
            kept += [r for r in rules if not isinstance(r, str)]
            if len(kept) != len(rules):
                perms[key] = kept
                changed = True
    if not changed:
        return text
    indent = next((len(l) - len(l.lstrip(' ')) for l in text.split('\n')
                   if l.startswith(' ')), 2)
    return json.dumps(data, indent=indent, ensure_ascii=False) + '\n'


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


# UPGRADING OFF PRE-STAGING (2026-10-09). A person who lands straight on
# staging (precedent_branches.lands_on_staging) no longer uses pre-staging.
# Morgan, 2026-10-09: when this reaches the repositories that vendor the
# engine, "make sure we have a smooth upgrade process for each. Merging the
# branches, telling he can delete pre-staging, updating previous mentions/
# links within each repo, etc etc." So, for that person only -- their own
# identity.json declares landing_branch "staging", never a default, and the
# repository's precedent.json does not still make pre-staging the landing
# branch for others (precedent_branches.pre_staging_unused; that case says
# in one line why it waited) -- and only while origin still has pre-staging:
#   1. work waiting on pre-staging is brought into staging by --land's own
#      composition (precedent_branches.land: staging, then main's direct
#      work, then pre-staging, by merge commits, the quick checks, a push
#      never forced). A conflict or a red check moves nothing and says what
#      to do (practice: repair-cannot-discard-work);
#   2. once it holds nothing staging lacks, it is offered for deletion as a
#      link, never deleted (practice: never-delete-a-remote-branch);
#   3. this repository's own Markdown that tells a reader work lands on
#      pre-staging, or links to this repository's pre-staging tree, is
#      repointed to staging (practice: rename-updates-links). Conservative:
#      only the clear instructions and links below are rewritten; every
#      other mention is listed with why it was left.
# It runs before the views are regenerated, so they render the reworded
# sources. For anyone else it does nothing and says nothing.
RETIRE_PRE_STAGING_HEADER = 'PRE-STAGING IS RETIRED -- your work lands on staging now:'

# A clear instruction: a verb that sends work somewhere, then the branch.
_PS_TOKEN = r'(?P<q>[`"\']?)pre-staging(?P=q)(?![\w-])'
_PS_INSTRUCTION = re.compile(
    r'(?i)\b(?:(?:land|lands|landing|push|pushes|pushing|merge|merges|merging'
    r'|target|targets|targeting|retarget|retargets|base|bases)'
    r'(?:\s+(?:it|them|this|work|your\s+work|the\s+work|the\s+change|'
    r'changes|your\s+changes|the\s+branch|your\s+branch))?'
    r'|(?:a\s+|the\s+)?(?:pull\s+requests?|PRs?))'
    r'\s+(?:on|onto|to|into|against|at)\s+' + _PS_TOKEN)
# A link into a tree, file or history on a GitHub branch.
_PS_LINK = re.compile(r'github\.com/(?P<slug>[^/\s()]+/[^/\s()]+)/'
                      r'(?P<kind>tree|blob|commits)/pre-staging(?=[/)\s#?"\'>\]]|$)')
_DATED = re.compile(r'\b20\d\d-\d\d-\d\d\b')
_QUOTED = re.compile(r'"[^"\n]*"|\u201c[^\u201d\n]*\u201d')
# Words that make a line read as history or a comparison, not an instruction.
_HISTORY_WORDS = re.compile(
    r'(?i)\b(?:today|until|used\s+to|no\s+longer|was|were|had|before|'
    r'formerly|previously|retired|old|instead\s+of|rather\s+than)\b')
_HEADING = re.compile(r'^(#{1,6})\s+(.*)$')
# Whole files that are history: what they record stays as it was.
_HISTORY_DIRS = ('gotchas/', 'record/')


def _retire_scope(repo):
    """-> (files, history): this repository's own hand-written Markdown to
    read, and the tracked Markdown left whole as history. Vendored copies
    (the catalogue mirror, a vendored universal source, engine files) and
    generated views are neither: they are not this repository's to word."""
    r = subprocess.run(['git', '-C', str(repo), 'ls-files', '-z', '--', '*.md'],
                       capture_output=True, text=True)
    tracked = [p for p in r.stdout.split('\0') if p] if r.returncode == 0 else []
    vendored = ['process/upstream/']
    try:
        uni = universal_catalogue_path(repo)
    except Exception:                                        # noqa: BLE001
        uni = None
    if uni:
        vendored.append(uni.rstrip('/') + '/')
    engine = _engine_owned(repo) | set(_materialized_practices(repo))
    try:
        import precedent_resolve as pr
        records = list(pr.declared_record_paths(repo))
    except Exception:                                        # noqa: BLE001
        records = []
    files, history = [], []
    for rel in tracked:
        if rel in engine or any(rel.startswith(v) for v in vendored):
            continue
        if _is_generated_view(repo, rel):
            continue
        if (rel.startswith(_HISTORY_DIRS)
                or any(rel == p or (p.endswith('/') and rel.startswith(p))
                       for p in records)
                or (rel.startswith('todo/') and _closed_item(repo / rel))):
            history.append(rel)
            continue
        files.append(rel)
    return files, history


def _materialized_practices(repo):
    """-> {repo-relative path: source name} for each practices/<slug>.md
    MANIFEST.json says the sync wrote. Each is a copy of a practice that
    lives elsewhere (a source repository, or this repository's own local/
    tree), so the next sync puts back whatever is written into it: the
    retire step words the original, never the copy. On 2026-10-09 it
    "reworded" a copy of the person's promote-only rule that the same run's
    view regeneration then put back."""
    try:
        mf = json.loads((pathlib.Path(repo) / 'MANIFEST.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    out = {}
    for p in mf.get('practices') or []:
        if isinstance(p, dict) and p.get('slug'):
            out[f"practices/{p['slug']}.md"] = str(p.get('source') or '')
    return out


def _closed_item(path):
    """True for an open-item file whose frontmatter status is not open."""
    try:
        head = path.read_text(encoding='utf-8', errors='ignore')[:2000]
    except OSError:
        return False
    if not head.startswith('---\n'):
        return False
    m = re.search(r'^status:[ \t]*(\S+)', head[:max(head.find('\n---', 4), 0)], re.M)
    return bool(m) and m.group(1).strip('"\'') not in ('open', 'claimed')


def reword_pre_staging(text, slug):
    """-> (new_text, changed, left): `text` (one Markdown file) with each clear
    instruction to land on pre-staging, and each link to `slug`'s pre-staging
    tree, file or history, repointed to staging. `changed` is [(line, why)]
    and `left` [(line, why)] for every other line that names pre-staging,
    1-based. Front matter, generated blocks, code blocks, a Story section and
    anything under a dated heading are never rewritten.

    An INDENTED code block counts as code too (CommonMark: four spaces or a
    tab, after a blank line or another such line, and not a list item's
    continuation). On 2026-10-09 a handoff prompt quoted that way in an open
    item's Notes had its "Push to `pre-staging` (Booked) refused" reworded
    to staging -- a record of where a push went, made false -- because only
    fenced blocks were recognized."""
    import generated_blocks
    lines = text.split('\n')
    hidden = generated_blocks.mask(lines)
    code = generated_blocks.code_mask(lines)
    # A dated SENTENCE is history on every line it wraps onto: on
    # 2026-10-09 a note whose date sat two lines above its quote of an old
    # instruction was reworded. By sentence, not by paragraph: a paragraph
    # can hold a dated sentence beside a live instruction, and the
    # instruction is still reworded.
    para_dated = [False] * len(lines)
    carry = False
    for k, ln in enumerate(lines):
        if not ln.strip() or code[k]:
            carry = False
            continue
        if carry:
            para_dated[k] = True
        if _DATED.search(ln) or carry:
            carry = not ln.rstrip().endswith(('.', '!', '?'))
    changed, left = [], []
    story = None          # heading level of an open Story section
    dated = None          # heading level of an open dated section
    front = lines[:1] == ['---']
    for i, line in enumerate(lines):
        if front:
            if i and line.strip() == '---':
                front = False
            continue
        if code[i]:
            if 'pre-staging' in line and not hidden[i]:
                left.append((i + 1, 'code block'))
            continue
        h = _HEADING.match(line)
        if h:
            level = len(h.group(1))
            if story is not None and level <= story:
                story = None
            if dated is not None and level <= dated:
                dated = None
            if re.match(r'(?i)story\b', h.group(2).strip()):
                story = level
            elif _DATED.search(h.group(2)):
                dated = level
        if 'pre-staging' not in line or hidden[i]:
            continue
        why = ('Story section, history' if story is not None else
               'under a dated heading, history' if dated is not None else
               'dated line, history' if _DATED.search(line) else
               'dated sentence, history' if para_dated[i] else
               'quotation' if line.lstrip().startswith('>') else
               'table row' if line.lstrip().startswith('|') else
               'reads as history or a comparison' if _HISTORY_WORDS.search(line)
               else None)
        if why:
            left.append((i + 1, why))
            continue
        # A phrase inside double quotes is a report of what something said,
        # never an instruction (2026-10-09: "Push to `pre-staging` (Booked)
        # refused" was reworded in a note about the bug).
        quoted = [(q.start(), q.end()) for q in _QUOTED.finditer(line)]

        def to_staging(m):
            if any(a <= m.start() < b for a, b in quoted):
                return m.group(0)
            return (m.group(0)[:m.start('q') - m.start(0)]
                    + f'{m.group("q")}staging{m.group("q")}')
        said = _PS_INSTRUCTION.sub(to_staging, line)
        new = _PS_LINK.sub(lambda m: (m.group(0).replace('/pre-staging', '/staging')
                                      if slug and m.group('slug').lower() == slug.lower()
                                      else m.group(0)), said)
        if new != line:
            lines[i] = new
            changed.append((i + 1, ' and '.join(
                w for w, did in (('instruction', said != line), ('link', new != said))
                if did)))
        if 'pre-staging' in new:
            other = _PS_LINK.search(new)
            in_quote = any(a <= new.find('pre-staging') < b for a, b in
                           [(q.start(), q.end()) for q in _QUOTED.finditer(new)])
            left.append((i + 1, 'link into another repository' if other
                         else 'quotation, history' if in_quote
                         else 'not a clear instruction'))
    return '\n'.join(lines), changed, left


# THE SOLE MAINTAINER MAY SWITCH THE REPOSITORY (2026-10-09). The one thing
# that keeps pre-staging for an explicit staging lander is precedent.json
# making it the landing branch for others. Where precedent.json's
# `maintainers` names exactly one person and that person is the one running
# this -- matched as timezone_offer matches them, by the GitHub username
# precedent_audience.viewer reads -- nobody else can be landing there, so
# the value is switched to staging, that one value and nothing else, and the
# retirement goes on in the same run. Two maintainers, or none named, keep
# the one-line wait: the call is theirs together.
_REPO_LANDS_ON_PRE_STAGING = re.compile(
    r'("' + re.escape(pb.LANDING_SETTING) + r'"\s*:\s*)"' + re.escape(pb.PRE_STAGING) + '"')


def sole_maintainer_is_you(repo):
    """-> '@login' when precedent.json's `maintainers` names exactly one
    person and the person running this is that one, else None."""
    people = [m for m in pb.precedent_json(repo).get('maintainers') or []
              if isinstance(m, dict) and str(m.get('github') or '').strip()]
    if len(people) != 1:
        return None
    login = str(people[0]['github']).strip().lstrip('@').lower()
    try:
        import precedent_audience as pa
        gh, _email = pa.viewer(repo)
    except Exception:                                        # noqa: BLE001
        return None
    return f'@{login}' if gh and gh.lower() == login else None


def rewords_this_run(repo, switched, merged_now):
    """-> True when this run is the one moving the repository off
    pre-staging, so stale instructions to land there are reworded: it
    switched precedent.json, it brought pre-staging's work into staging, or
    the switch is not committed yet (a rerun before the commit). After that,
    a new mention of pre-staging is usually deliberate, and a reword would
    rewrite it on every later update (2026-10-09, reported by another
    session: a note quoting the old instruction was reworded a run later)."""
    if switched or merged_now:
        return True
    rc, out = run(['git', 'show', 'HEAD:precedent.json'], repo)
    try:
        committed = json.loads(out).get(pb.LANDING_SETTING) if rc == 0 else None
    except ValueError:
        committed = None
    return committed != pb.STAGING


def committed_engine_lands_on_staging(repo):
    """-> True when the engine this repository has committed (HEAD's
    tools/precedent_branches.py) can land work straight on staging: one
    that predates it would refuse every landing there once precedent.json
    says staging."""
    rc, out = run(['git', 'show', 'HEAD:tools/precedent_branches.py'], repo)
    return rc == 0 and 'def lands_on_staging(' in out


def switch_repo_landing_to_staging(repo):
    """Change precedent.json's `landing_branch` from pre-staging to staging,
    every other byte kept. -> True when written; False, writing nothing,
    unless the value appears exactly once and the result still parses."""
    path = pathlib.Path(repo) / 'precedent.json'
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return False
    found = list(_REPO_LANDS_ON_PRE_STAGING.finditer(text))
    if len(found) != 1:
        return False
    m = found[0]
    new = text[:m.start()] + m.group(1) + f'"{pb.STAGING}"' + text[m.end():]
    try:
        if json.loads(new).get(pb.LANDING_SETTING) != pb.STAGING:
            return False
    except ValueError:
        return False
    path.write_text(new, encoding='utf-8')
    return True


def retire_pre_staging_step(repo, rep):
    """Update Vendors' upgrade off pre-staging, for a person who lands on
    staging (see RETIRE_PRE_STAGING_HEADER above). Reports on `rep`: one
    step line, and the block close() prints in every outcome (rep.retired).
    Silent for anyone else, and once origin has no pre-staging."""
    repo = pathlib.Path(repo)
    # Only the person's own identity.json declaring staging retires it, and
    # never while the repository makes it others' landing branch
    # (precedent_branches.pre_staging_unused): one line says it waited.
    unused, waits = pb.pre_staging_unused(repo)
    switched = False
    if waits and pb._remote_tip(repo, pb.PRE_STAGING):
        if not committed_engine_lands_on_staging(repo):
            # The first pass brings the engine and nothing else; the switch
            # waits for the next run, once that engine has landed (Morgan,
            # 2026-10-09: "do the vendor updates, tell you, then I'll do
            # the vendor updates again").
            rep.step('pre-staging', f'kept for now: this update brings the '
                     f'engine that lands work straight on {pb.STAGING}. Land '
                     f'it, then run Update Vendors again: that run moves this '
                     f'repository onto {pb.STAGING}')
        elif (sole_maintainer_is_you(repo)
                and 'precedent.json' not in set(rep.before or ())
                and switch_repo_landing_to_staging(repo)):
            switched = True
            rep.step('precedent.json', f'{pb.LANDING_SETTING} {pb.PRE_STAGING} '
                     f'-> {pb.STAGING}, since you are this repository\'s only '
                     f'maintainer')
            unused, waits = pb.pre_staging_unused(repo)
        else:
            rep.step('pre-staging', f'kept, not retired: {waits}')
    if not unused:
        return
    state, _ptip = pb.pre_staging_retired(repo, fetch=True)
    if state is None:
        return
    staging = pb.staging_branch(repo)
    block = []
    if state == pb.RETIRED_WAITING:
        said = []
        rc = pb.land(repo, work=f'origin/{pb.PRE_STAGING}', say=said.append)
        text = '\n'.join(said)
        result = next((l for l in reversed(said)
                       if l.startswith(pb.LAND_RESULT)), '')
        if rc != 0:
            rep.step('pre-staging', f'not brought into {staging}; nothing moved')
            if 'conflicts with' in result:
                why = (f'{pb.PRE_STAGING} holds work {staging} lacks, and it does '
                       f'not merge cleanly: the same lines changed on both sides. '
                       f'Nothing moved, and nothing was dropped')
            elif 'quick checks failed' in result:
                why = (f'{pb.PRE_STAGING} holds work {staging} lacks, and the quick '
                       f'checks failed on {staging} with it merged in. Nothing moved')
            else:
                why = (f'{pb.PRE_STAGING} holds work {staging} lacks, and it could '
                       f'not be brought in ({result or "see the lines below"}). '
                       f'Nothing moved')
            rep.leave(pb.PRE_STAGING, why + '. To bring it in: '
                      f'`git switch --no-track -c "$(python3 tools/precedent_branch_name.py '
                      f'merge pre-staging)" origin/{pb.PRE_STAGING}`, then '
                      f'`git merge origin/{staging} origin/{pb.MAIN}`, fix what '
                      f'it names and commit, `git push -u origin HEAD`, then '
                      f'`python3 tools/precedent_branches.py --land '
                      f'"$(git branch --show-current)"`, and run Update Vendors '
                      f'again')
            rep.details[pb.PRE_STAGING] = [l for l in text.splitlines()
                                           if l.strip()][-12:]
            return
        moved = [l.split('   <- ', 1)[0].rstrip() for l in text.splitlines()
                 if l.startswith(('LANDED ', 'BROUGHT IN ', 'REBUILT ', '  '))]
        block.append(f'merged into {staging}, with the quick checks:')
        block += [f'  {l}' for l in moved]
        state, _ptip = pb.pre_staging_retired(repo, fetch=True)
        if state != pb.RETIRED_MERGED:
            rep.step('pre-staging', f'its work brought into {staging}; it gained '
                     f'more meanwhile')
            block.append(f'{pb.PRE_STAGING} gained work while this ran; run Update '
                         f'Vendors again to bring that in too.')
            rep.retired = block
            return
    slug = pb._slug(repo)
    files, history = _retire_scope(repo)
    before = set(rep.before or ())
    changed, left = [], []
    reword = rewords_this_run(repo, switched, bool(block))
    deliberate = []
    for rel in files:
        path = repo / rel
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        if 'pre-staging' not in text:
            continue
        new, did, kept = reword_pre_staging(text, slug)
        if did and not reword:
            # Moved onto staging in an earlier update: a mention written
            # since is read as deliberate, reported and never rewritten.
            deliberate += [(rel, n) for n, _w in did]
        elif did and rel in before:
            # Never mixed into somebody's uncommitted work.
            left += [(rel, n, 'uncommitted edits in this file') for n, _w in did]
        elif did:
            path.write_text(new, encoding='utf-8')
            changed += [(rel, n, w) for n, w in did]
        left += [(rel, n, w) for n, w in kept]
    in_history = []
    for rel in history:
        try:
            n = (repo / rel).read_text(encoding='utf-8', errors='ignore').count('pre-staging')
        except OSError:
            n = 0
        if n:
            in_history.append(n)
    if deliberate:
        shown = deliberate[:10]
        block.append('not reworded -- this repository moved onto staging in an '
                     'earlier update, so a mention of pre-staging now reads as '
                     'deliberate; change it by hand if it is a stale '
                     'instruction: ' + ', '.join(f'{rel}:{n}' for rel, n in shown)
                     + (f'; and {len(deliberate) - len(shown)} more'
                        if len(deliberate) > len(shown) else ''))
    if changed:
        block.append('reworded to staging: ' + ', '.join(
            f'{rel}:{n} ({w})' for rel, n, w in changed))
    if left:
        shown = left[:10]
        block.append('left as they are: ' + '; '.join(
            f'{rel}:{n} ({w})' for rel, n, w in shown)
            + (f'; and {len(left) - len(shown)} more' if len(left) > len(shown) else ''))
    if in_history:
        block.append(f'left as history: {sum(in_history)} mention(s) in '
                     f'{len(in_history)} record file(s) (gotchas/, record/, closed '
                     f'todo items, declared record paths)')
    elsewhere = []
    for rel, source in sorted(_materialized_practices(repo).items()):
        if source in ('', 'local'):
            continue                    # its original is under local/, read above
        try:
            body = (repo / rel).read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        if reword_pre_staging(body, slug)[1]:
            elsewhere.append(f'{rel} (from {source})')
    if elsewhere:
        block.append('copies of practices from other sources still name '
                     'pre-staging as an instruction; reword each in its own '
                     'source, never here: ' + ', '.join(elsewhere))
    if switched and 'pre-staging' in json.dumps(
            pb.precedent_json(repo).get('_landing_branch_comment') or ''):
        block.append('precedent.json: landing_branch is now staging, and its '
                     '_landing_branch_comment still describes pre-staging; '
                     'reword it in this same commit')
    link = (f'https://github.com/{slug}/branches/all?query='
            + urllib.parse.quote(pb.PRE_STAGING, safe='')) if slug else None
    block.append(f'{pb.PRE_STAGING} holds nothing {staging} lacks and is no '
                 f'longer used, so it is safe to delete: '
                 + (link or "GitHub's branches page, with its trash icon"))
    rep.retired = block
    rep.step('pre-staging', 'retired'
             + (f', its work merged into {staging}' if len(block) and
                block[0].startswith('merged into') else '')
             + (f', {len(changed)} mention(s) reworded' if changed else '')
             + '; safe to delete')


FULL_VIEWS = ('MAP.md', 'GLOSSARY.md')


def migrate_views_step(repo, rep):
    """Run the repository's own precedent_migrate_views.py and report it: a
    hand-written MAP.md or GLOSSARY.md moves into its source file, word for
    word, and is generated from then on (spec/GENERATED_FILES_PLAN.md step
    5; Morgan, 2026-10-03). The tool puts everything back and says so rather
    than lose a word, and then the view is the repository's call."""
    repo = pathlib.Path(repo)
    migrate = repo / 'tools' / 'precedent_migrate_views.py'
    if migrate.is_file():
        rc, out = run([sys.executable, str(migrate), '--repo', '.'], repo)
        if rc != 0:
            rep.leave('MAP.md / GLOSSARY.md',
                      'could not be moved into MAP.source.md / '
                      'GLOSSARY.source.md without losing text, so they were '
                      'left exactly as they were: ' + tail(out, repo=repo))
        elif 'nothing to migrate' not in out:
            moved = [n for n in FULL_VIEWS if f'{n} -> ' in out]
            rep.step('views migrated', 'the hand-written '
                     + ' and '.join(moved)
                     + ' moved into their source files word for word, and '
                     'are generated from them from now on')
            # The text moved unchanged, so its headings are what they
            # were; but the source files are new, and a rule that judges
            # every heading of a changed document now reaches them. The
            # repository's call, with the tool that applies the rule.
            srcs = [n.replace('.md', '.source.md') for n in moved]
            tc = repo / 'tools' / 'title_case.py'
            # A repository that declares headline-capitalization not binding
            # (precedent.json `not_binding`, with its written reason) has
            # already answered this question; asking it again blocked an
            # update for a call the repo had made (consumer repo, 2026-10-04).
            try:
                import precedent_resolve as pr
                exempt = pr.load_not_binding(repo).get('headline-capitalization')
            except Exception:
                exempt = None
            # Only a file the check itself reaches: one the repository
            # treats as published (title_case.is_outward -- output_paths,
            # internal_paths and the defaults). Naming a file to title_case.py
            # judges it whatever the repo declared, so a repo with
            # `"output_paths": []` was asked to recase two internal files
            # (2026-10-04, a consumer).
            try:
                import title_case as _tc
                inward = [n for n in srcs if not _tc.is_outward(n, repo)]
            except Exception:
                inward = []
            if inward:
                rep.step('headings kept', ' and '.join(inward) + ' keep their '
                         'headings as moved: this repository does not publish '
                         'them (precedent.json output_paths / internal_paths)')
            srcs = [n for n in srcs if n not in inward]
            if exempt and srcs:
                rep.step('headings kept', ' and '.join(srcs) + ' keep their '
                         'headings as moved: this repository declares '
                         'headline-capitalization not binding (' + exempt + ')')
            elif srcs and tc.is_file():
                rc2, out2 = run([sys.executable, str(tc), *srcs], repo)
                if rc2 != 0:
                    rep.leave(' and '.join(srcs),
                              'its headings, moved word for word, are not in '
                              'headline case, which the headline-capitalization '
                              'check now applies because the file is new. Apply '
                              'it with python3 tools/title_case.py --write '
                              + ' '.join(srcs) + ', or keep them and say why')


def generated_full_views(repo):
    """-> the FULL_VIEWS this repo's own header says build_views.py
    generates, or whose source file it has (MAP.source.md, GLOSSARY.source.md),
    in order. A hand-written MAP.md with no source is the repo's, and left
    alone."""
    import build_views as _bv
    srcs = {'MAP.md': getattr(_bv, 'MAP_SOURCE', None),
            'GLOSSARY.md': getattr(_bv, 'GLOSSARY_SOURCE', None)}
    return [name for name in FULL_VIEWS
            if (pathlib.Path(repo) / name).is_file()
            and (_bv.is_generated_view(pathlib.Path(repo) / name)
                 or (srcs.get(name) and _bv.has_own_source(repo, srcs[name])))]


def clone_command(repo):
    """-> the command that runs the BestPractice clone's own copy of this
    file for `repo`: the clone found by its origin beside the repo
    (pve.find_source_clones -- the attach tool's lowercase
    alex137/bestpractice path included, 2026-10-08), else ../BestPractice."""
    try:
        found = pve.find_source_clones(repo)
    except Exception:                                          # noqa: BLE001
        found = []
    where = (os.path.relpath(found[0], repo) if found else '../BestPractice')
    return f'python3 {where}/tools/precedent_update.py --repo .'


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
    pve._drop_process_manifest_entries(repo, old)
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


GOTCHA_SEED_TEMPLATE = 'templates/gotchas/stale-checkout.md.template'
GOTCHA_SEED = 'gotchas/gotcha-2026-09-01-a-stale-checkout-looks-complete-with-no-error.md'
# The bullet AGENTS.md carried before the trap moved into gotchas/.
GOTCHA_SEED_INLINE = 'stale enough to look complete'


def gotchas_seed_step(repo, rep, rev):
    """Start gotchas/ with the trap every install inherits, where it is
    missing, and name an inline copy of that trap left in AGENTS.md.

    The template's AGENTS.md links gotchas/, and INSTALL.md section 1 seeds
    it -- but only at install, so a consumer installed before the catalogue
    had no gotchas/. Taking the template's paragraph into its AGENTS.md put
    in a link to nothing, and the push check failed on it (2026-10-04, a
    consumer's Update Vendors). A practice set keeps no gotchas/ of its own."""
    import build_views as _bv
    if _bv.repo_is_practice_source(repo):
        return
    seed = repo / GOTCHA_SEED
    if not (repo / 'gotchas').exists():
        text = _source_text(rev, GOTCHA_SEED_TEMPLATE) if rev else None
        if text is None:
            return
        seed.parent.mkdir(parents=True, exist_ok=True)
        seed.write_text(text, encoding='utf-8')
        rep.step('gotchas', f'started with {GOTCHA_SEED}, the trap every '
                 f'install inherits (INSTALL.md section 1), so the template\'s '
                 f'link to gotchas/ has somewhere to go')
    try:
        agents = (repo / 'AGENTS.md').read_text(encoding='utf-8')
    except OSError:
        return
    if seed.is_file() and GOTCHA_SEED_INLINE in agents:
        rep.leave('AGENTS.md', f'still carries the stale-checkout trap inline; '
                  f'{GOTCHA_SEED} holds it now, so remove the inline bullet')


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
        if not rev or not (repo / rel).is_file():
            continue
        current = _source_text(rev, tmpl)
        if current is None:
            continue
        now = {l.strip() for l in current.splitlines()}
        gone = {l for l in _template_lines_ever(rev, tmpl) - now if _substantive(l)}
        if not gone:
            continue
        filled = _filled_forms(current)
        for target in _hand_kept_files(repo, rel):
            try:
                text = target.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            hits = [(n, l.strip()) for n, l in enumerate(text.splitlines(), 1)
                    if l.strip() in gone
                    and not any(f.fullmatch(l.strip()) for f in filled)]
            if hits:
                found.append((str(target.relative_to(repo)), tmpl,
                              hashlib.sha256(current.encode('utf-8')).hexdigest(),
                              hits))
    return found


def _hand_kept_files(repo, rel):
    """-> [path] the files a person edits to change install-once file `rel`.

    Itself, except for a generated MAP.md or GLOSSARY.md: those are rebuilt
    from MAP.source.md / GLOSSARY.source.md (or the directory form, one file
    per entry) since 2026-10-03, so a line found in the view had to be fixed
    in the source. Reading the view sent a consumer to delete lines the next
    sync wrote straight back, and the update never finished (very deep
    check's install rehearsal, 2026-10-05). A generated view with no source
    has nothing a person can edit, and is skipped."""
    target = pathlib.Path(repo) / rel
    if rel not in FULL_VIEWS:
        return [target]
    try:
        import build_views as _bv
    except Exception:                                             # noqa: BLE001
        return [target]
    src = {'MAP.md': getattr(_bv, 'MAP_SOURCE', None),
           'GLOSSARY.md': getattr(_bv, 'GLOSSARY_SOURCE', None)}.get(rel)
    if src:
        own = pathlib.Path(repo) / src
        if own.is_file():
            return [own]
        folder = pathlib.Path(repo) / _bv.source_dir_name(src)
        if folder.is_dir():
            return sorted(p for p in folder.rglob('*.md') if p.is_file())
    if _bv.is_generated_view(target):
        return []
    return [target]


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


def budget_note_key(tool):
    """The registry's note key for a tool's run budget:
    'precedent_vendor_engine.py' -> '_precedent_vendor_engine_note'."""
    return '_' + tool[:-3] + '_note' if tool.endswith('.py') else f'_{tool}_note'


def seed_engine_budgets(repo, rev, last_synced=None):
    """Write into this repo's tools/github_api_budgets.json the run budget,
    and its note, of every vendored engine tool upstream budgets and this
    repo does not. -> (seeded [(tool, calls)], asks [(tool, ours, theirs)]).

    2026-10-07, a consuming repository: upstream added a budget for the
    vendored precedent_vendor_engine.py, and the update stopped to leave it
    for the person, who copied upstream's 12 and note in by hand -- a figure
    with nothing to decide, which every consumer would copy the same way.
    The engine is upstream's code, so upstream's budget for it is the
    starting figure. Only where this repo already has a DIFFERENT figure, and
    upstream's own moved since the last sync, is there a call to make: keep
    the repo's own, or take upstream's new one. A repo with no registry
    declares nothing, and still gets nothing."""
    path = repo / 'tools' / 'github_api_budgets.json'
    try:
        own = json.loads(path.read_text(encoding='utf-8'))
        vendored = set(json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                                  .read_text(encoding='utf-8')).get('files') or ())
        up = json.loads(_source_text(rev, 'tools/github_api_budgets.json') or '')
    except (OSError, ValueError, TypeError):
        return [], []
    if not isinstance(own, dict) or not isinstance(up, dict):
        return [], []
    try:
        before = json.loads(_source_text(last_synced, 'tools/github_api_budgets.json')
                            or '') if last_synced else {}
    except ValueError:
        before = {}
    up_b = up.get('run_budgets') or {}
    was_b = (before.get('run_budgets') or {}) if isinstance(before, dict) else {}
    have = own.setdefault('run_budgets', {})
    seeded, asks = [], []
    for tool, calls in sorted(up_b.items()):
        if tool.startswith('_') or tool not in vendored:
            continue
        if tool not in have:
            have[tool] = calls
            note = up_b.get(budget_note_key(tool))
            if note:
                have[budget_note_key(tool)] = note
            seeded.append((tool, calls))
        elif have[tool] != calls and was_b.get(tool) != calls:
            asks.append((tool, have[tool], calls))
    if seeded:
        path.write_text(json.dumps(own, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8')
    return seeded, asks


def universal_catalogue_path(repo):
    """-> the repo-relative path of the universal source this repository
    vendors inside itself (a section 0 install), or None: no precedent.json,
    no universal source, or one that lives outside the repository."""
    try:
        data = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    import precedent_resolve as pr
    for src in data.get('sources') or []:
        if not isinstance(src, dict) or pr.declared_level(src) != 'universal':
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

# The source's own files that travel with its catalogue, beside practices/,
# read at the same commit. precedent-source.json carries universal's
# occasion-index allowance (2026-09-29). The withdrawal record is the
# forwarding address of every rule deleted from universal on purpose, which
# a sync's removal guard reads at <universal source>/record/ -- here, inside
# this vendored tree. Without it the first update after the ladder left
# universal refused all fourteen of its rules as lost in every repository
# that vendors the catalogue this way (2026-10-04); the process/upstream/
# mirror already carried it (checkin.py's VENDORED_DESPITE_DIR).
CATALOGUE_COMPANIONS = ('precedent-source.json', 'record/WITHDRAWN_FROM_UNIVERSAL.md')


def _blob_id(data):
    """-> the git object id of `data` as a blob (checkin.blob_id)."""
    import checkin
    return checkin.blob_id(data)


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
    edit, whichever commit it was vendored from. One reading of upstream's
    history for every layer (checkin.upstream_blobs)."""
    import checkin
    return {(path[len('practices/'):], oid)
            for path, oid in checkin.upstream_blobs(SOURCE, rev)
            if path.startswith('practices/')}


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
        # The source's own files that travel with it (CATALOGUE_COMPANIONS),
        # by the same read at the same commit.
        for comp in CATALOGUE_COMPANIONS:
            shown = subprocess.run(['git', '-C', str(SOURCE), 'show', f'{rev}:{comp}'],
                                   capture_output=True, text=True)
            if shown.returncode == 0 and shown.stdout.strip():
                dest = repo / rel / comp
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(shown.stdout, encoding='utf-8')
        n = sum(1 for _ in target.glob('*.md'))
        note = (f'; local edits judged against {basis}' if not unread else
                '; no record of the last sync here, so only uncommitted edits '
                'were checked for')
        rep.step('catalogue', f'{rel}/practices replaced from the source at '
                 f'{rev[:12]} ({n} practice files; INSTALL.md section 2, step 0){note}')
        rep.add_edits(le.resolve(repo, swap), swap.merges)
        return True


# What DONE says about the merge that lands the update. 2026-10-08, a
# consumer: the session merged Update Vendors' own pull request with a
# 7-character expected head; GitHub's merge refused it, and the failed merge
# left Claude Code's auto mode refusing even reads until the person spoke
# (gotchas/gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge.md).
MERGE_HEAD_NOTE = (
    "Merging its pull request: give the merge tool the full 40-character "
    "head commit, never a short one -- `git rev-parse HEAD` right after the "
    "push, or `git ls-remote origin refs/heads/<branch>` -- or no expected "
    "head at all. GitHub refuses a short one, and a failed merge leaves auto "
    "mode refusing even reads until the person speaks.")


# THE BRANCH THE UPDATE IS COMMITTED ON (2026-10-09). An update run on a
# tier branch -- main, staging, pre-staging -- ended "commit, then land it"
# without naming a branch, and a consumer's session made one by hand; the
# push check refused it, since a session branch is named by
# tools/precedent_branch_name.py. The update does not move the checkout
# itself: it reads the current branch at several steps, and a switch in the
# middle of a run is a state nothing else here expects. `git switch -c` from
# HEAD keeps the staged diff exactly as it is, so the command is printed for
# the session to run before it commits.
SWITCH_COMMAND = ('git switch --no-track -c '
                  '"$(python3 tools/precedent_branch_name.py update-vendors)"')


def feature_branch_line(repo):
    """-> the line DONE prints when `repo`'s checkout is on a tier branch
    (precedent_branches.tier_branches, its landing branch, or its declared
    base), or None on any other branch or when it cannot be read."""
    if repo is None:
        return None
    try:
        r = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--abbrev-ref',
                            'HEAD'], capture_output=True, text=True)
    except OSError:
        return None
    cur = r.stdout.strip() if r.returncode == 0 else ''
    if not cur or cur == 'HEAD':
        return None
    tiers = set(pb.tier_branches(repo))
    for read in (lambda: pb.landing_branch(repo)[0], lambda: pb.base_branch(repo)):
        try:
            name = read()
        except Exception:                                    # noqa: BLE001
            name = None
        if name:
            tiers.add(name)
    if cur not in tiers:
        return None
    return (f"This checkout is on {cur}, a tier branch. Before committing, move "
            f"the staged update onto a branch of its own (it carries the staged "
            f"diff as it is): {SWITCH_COMMAND}")


class Report:
    def __init__(self):
        self.steps = []   # (name, one-line outcome)
        self.left = []    # (what, why)
        self.loud = []    # workflows left alone -- printed first and last
        self.details = {} # what -> lines printed under its Left-for-you item
        self.asks = []    # (what, question) -- for the person, not this repo
        self.edits = []   # (outcome, rel, text) -- precedent_local_edits.resolve()
        self.merges = {}  # rel -> (merged, upstream's) -- judged again at step 5
        self.not_run = None  # what the closing check left to a later tier
        self.copy_verified = False  # the catalogue copy matched its record
        self.warnings = []   # passed now, refused at a later tier
        self.repo = None     # set with `staged` once stage_update has run
        self.staged = []     # the paths this run staged as its own
        self.pin = None      # (repo, commit, branch): the commit reruns take
        self.pin_repo = None # whose pin a DONE drops, --from-ref runs included
        self.before = None   # what was uncommitted when the run started writing
        self.earlier = set() # of `before`, what an earlier run staged, unchanged
        self.retired = []    # retire_pre_staging_step's block, every outcome
        self.commit_note = None  # a --take-anyway: said in the commit message

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
            print("\nQUESTIONS FOR THE PERSON -- the update is complete "
                  "without these; only the person can answer them, so put "
                  "them in your reply:")
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
        # Upstream's version is the default, and what it replaced is the
        # session's call (Morgan, 2026-10-08), so it is said beside every
        # outcome, DONE included, never only inside the list above.
        judge = [rel for outcome, rel, _t in self.edits if outcome == le.PREFERRED]
        if judge:
            print(f"\nJUDGE: upstream's version replaced what was left of this "
                  f"repo's own edit to {', '.join(judge)} (LOCAL EDITS above, "
                  f"with the diff). Keep yours only where it does something "
                  f"different and important, with the keep command printed "
                  f"there; ask the person when it is a close call.")

    def _retired_block(self):
        # Said in every outcome: a merge into staging has already been
        # pushed by then, and the delete link is the person's to act on.
        if self.retired:
            print(f"\n{RETIRE_PRE_STAGING_HEADER}")
            for line in self.retired:
                print(f"  {line}")

    def _commit_note(self):
        if self.commit_note:
            print(f"\nCOMMIT MESSAGE: say this in it, in these words: "
                  f"{self.commit_note}")

    def _pinned(self):
        if self.pin:
            _repo, commit, branch = self.pin
            print(f"\nPINNED: a rerun takes {branch} @ {commit[:12]} again, the "
                  f"commit this update started from, until a run reports DONE "
                  f"-- so the target does not move while you work what is "
                  f"left. To take {branch}'s newest commit instead, run it "
                  f"with --move.")

    def close(self, failed=None):
        if self.pin_repo is not None and not failed and not self.left:
            clear_pin(self.pin_repo)   # DONE: the next update starts fresh
        if failed and self.repo is None and self.before is not None:
            # A run that failed before its staging step (the view sync, the
            # catalogue record) wrote as much as one that failed after it,
            # and recorded none of it, so its rerun took its output for
            # someone's: a consuming repository's next run refused 41 files
            # of its mirror as "changed here and not committed" (2026-10-08).
            # Staged and recorded the same way, so the rerun puts it back.
            ours = sorted(dirty_paths(self.pin_repo) - self.before)
            if ours:
                stage_update(self.pin_repo, self.before)
                self.repo, self.staged = self.pin_repo, ours
        if failed and self.repo is not None and self.staged:
            # Only a FAILED run's output is put back by the next one. A run
            # that left items for the person staged answers the next run
            # builds on (sections recorded as left out on purpose), and a
            # FAILED one asked nothing new: with any item left, the check
            # that fails is never started.
            record_staged_output(self.repo, self.staged)
        if self.before is not None and (self.repo or self.pin_repo) is not None:
            # Every outcome: a LEFT or DONE run's staged output is what a
            # rerun before the commit finds uncommitted, and is not someone's
            # work (earlier_runs_output).
            record_kept_output(self.repo or self.pin_repo,
                               set(self.staged) | self.earlier)
        if self.loud:
            self._banner()
        print("\n== Update Vendors ==")
        for name, outcome in self.steps:
            print(f"  {name}: {outcome}")
        self._local_edits()
        self._questions()
        self._retired_block()
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
            self._pinned()
            print(f"\nFAILED: {failed}")
            print("Nothing is committed. Fix what is named above and run this "
                  "again as it is: what this run staged and you have not "
                  "changed since is its own output, so the next run puts it "
                  "back and writes it again. A staged file you HAVE changed "
                  "is yours -- commit it first, or the next run refuses to "
                  "write over it.")
            return FAILED
        if self.left:
            print("\nLEFT FOR YOU -- the calls that belong to this repo. Work "
                  "each under vendor-update-runbook's conflicted-file review, "
                  "then run this again:")
            for what, why in self.left:
                print(f"  - {what}: {why}")
                for line in self.details.get(what, []):
                    print(f"    {line}")
            self._pinned()
            self._commit_note()
            if self.loud:
                self._banner()
            return LEFT
        for line in self.warnings:
            print(f"\nWARNING: {line}")
        switch = feature_branch_line(self.pin_repo)
        if self.asks:
            print("\nDONE -- nothing left for this repo to decide. Ask the "
                  "question(s) above, review the staged diff, commit, then land "
                  "it the way this repository lands work.")
        else:
            print("\nDONE -- nothing left to decide. Review the staged diff, "
                  "commit, then land it on your landing branch.")
        if switch:
            print(switch)
        self._commit_note()
        print(MERGE_HEAD_NOTE)
        if self.not_run:
            print(self.not_run)
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


def engine_refresh_ref(source, tip, follow, last_synced):
    """-> the commit the consumer's own engine refresh is told to vendor
    (`--from-ref`), or None to let it resolve one itself.

    Always the tip of the branch this repo follows, which this command has
    just read. The refresh is run by the consumer's OWN engine copy, and an
    older copy resolves whatever branch it was written to follow: a
    beta-era consumer's first update vendored from precedent-beta-v01 and
    reported `refreshed from precedent-beta-v01 @ b45fcf1f` under
    `source: main` (very deep check, 2026-10-05, pass 1). The end state
    matched main only because the replaced copy's second pass corrected it.
    Until 2026-10-06 the commit was passed only to a repo following a branch
    other than SOURCE_BRANCH.

    The one exception: an engine recorded at a commit the tip does not
    contain (pve.engine_is_ahead) on a repo following SOURCE_BRANCH. Told
    to vendor the tip, the refresh would roll that newer work back without
    a word; left to itself it keeps it, and this command then stops and
    says how to take the tip on purpose, as before."""
    if not tip:
        return None
    if (follow == pve.SOURCE_BRANCH and last_synced
            and pve.engine_is_ahead(source, last_synced, tip)):
        return None
    return tip


_REFRESHED_FROM = re.compile(r'(refreshed from )(\S+)( @ )([0-9a-f]+)')
_LEG_COMMIT = re.compile(r' @ ([0-9a-f]{7,40})\b')


def engine_summary(out, last_synced, follow=None, tip=None):
    """-> the one-line engine outcome for the report.

    The FINAL leg: a refresh that replaces itself runs twice, and each pass
    prints a summary line. With `tip` (the commit this command handed the
    refresh), the last line that landed there is the one shown, so a first
    pass by an older copy never stands for where the engine ended up; with
    `follow`, a `from <commit>` this command supplied reads as the branch it
    is the tip of. A pass that only found the engine current is shown only
    when no pass refreshed anything, so the report never says "nothing to
    do" over a run that wrote or removed files.

    "(was ...)": an engine older than 2026-09-28 reads it from the manifest
    the first pass already rewrote -- "(was e8a2bc67cc8d)" on a repo that
    had been at 37fc3b55. This command read the real commit before the
    refresh began, so that one is shown."""
    lines = out.splitlines()
    refreshed = [l for l in lines if l.startswith('precedent_vendor_engine refresh OK')]
    current = [l for l in lines if 'already current with' in l]

    def landed(l):
        m = _LEG_COMMIT.search(l)
        return bool(tip and m and tip.startswith(m.group(1)))
    summary = refreshed or current
    if tip and any(landed(l) for l in summary):
        summary = [l for l in summary if landed(l)]
    line = summary[-1].split(': ', 1)[-1] if summary else 'refreshed'
    if last_synced:
        line = re.sub(r'\(was [0-9a-f?]+\)', f'(was {last_synced[:12]})', line)
    if follow and tip:
        m = _REFRESHED_FROM.search(line)
        if m and m.group(2) == tip:
            line = line[:m.start(2)] + follow + line[m.end(2):]
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
            m = (re.match(r'(.+?) (?:\(line \d+\) )?has local edits', body)
                 or re.match(r'(.+?) is kept on purpose \(', body))
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


# precedent.json's record of rules that bind nowhere here ON PURPOSE: a key
# is a practice slug, or the name of the set its live copy is in.
NOT_IN_FORCE_KEY = 'not_in_force_here'
_IN_FORCE_IN_RE = re.compile(r'in force (?:only )?(?:in|from the \w+ set) `([^`]+)`')


def in_force_nowhere_step(repo, rep, out):
    """Ask about each rule the view sync found in force nowhere -- once.
    A rule precedent.json's `not_in_force_here` records, by slug or by the
    set it lives in, is said in one step line and never asked again.

    2026-10-01, from a consumer's Update Vendors: sixteen deduplicated
    rules whose live copy is in a shared set the consumer had dropped on
    purpose were asked about on every update, under a header that said
    both "none is this repo's call" and "ask before Go update"."""
    try:
        kept = json.loads((repo / 'precedent.json').read_text(
            encoding='utf-8')).get(NOT_IN_FORCE_KEY) or {}
    except (OSError, ValueError, AttributeError):
        kept = {}
    if not isinstance(kept, dict):
        kept = {}
    quiet = []
    for found in in_force_nowhere(out):
        slug = found.split(' (', 1)[0].strip()
        m = _IN_FORCE_IN_RE.search(found)
        where = m.group(1) if m else None
        if slug in kept or (where and where in kept):
            quiet.append(slug)
            continue
        key = where or slug
        rep.ask('IN FORCE NOWHERE',
                f'{found} -- it binds nowhere in this repo. Declare '
                + (f'`{where}`' if where else 'the set it forwards to')
                + f' in precedent.json, or record that it does not apply '
                f'here: "{NOT_IN_FORCE_KEY}": {{"{key}": "<why>"}}')
    if quiet:
        rep.step('not in force here, on purpose',
                 f'{len(quiet)} rule(s) precedent.json\'s {NOT_IN_FORCE_KEY} '
                 f'records: {", ".join(quiet)}')


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


HARNESS_GO_AHEAD = 'PRECEDENT_HARNESS_GO_AHEAD'


def harness_changes(repo):
    """-> the staged paths under .claude/ (hooks, settings): what Claude
    Code's auto mode holds a commit over until the person approves it."""
    r = subprocess.run(['git', '-C', str(repo), 'diff', '--cached',
                        '--name-only', '--', '.claude/'],
                       capture_output=True, text=True)
    return sorted(n for n in r.stdout.splitlines() if n)


STUB_MARKER = '# PRECEDENT HOOK STUB.'


def migrates_to_stubs(repo, paths):
    """True when this update turns the repo's hooks into the permanent stubs
    (2026-10-07): some staged .claude/hooks/ file is a stub now and was not
    one before. Read from the index and HEAD, never the working tree."""
    for rel in paths:
        if not rel.startswith('.claude/hooks/'):
            continue
        now = subprocess.run(['git', '-C', str(repo), 'show', f':{rel}'],
                             capture_output=True, text=True).stdout
        was = subprocess.run(['git', '-C', str(repo), 'show', f'HEAD:{rel}'],
                             capture_output=True, text=True).stdout
        if STUB_MARKER in now and STUB_MARKER not in was:
            return True
    return False


def _git_show(repo, spec):
    r = subprocess.run(['git', '-C', str(repo), 'show', spec],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


_HOOK_NAME = re.compile(r'([A-Za-z0-9_.-]+\.sh)\b')


def _settings_entries(text):
    """-> {(event, matcher, command)} in a settings.json's `hooks`, or None
    when it is not JSON."""
    try:
        data = json.loads(text) if text else {}
    except ValueError:
        return None
    out = set()
    hooks = data.get('hooks') if isinstance(data, dict) else None
    for event, groups in (hooks or {}).items() if isinstance(hooks, dict) else ():
        for g in groups if isinstance(groups, list) else ():
            if not isinstance(g, dict):
                continue
            for h in g.get('hooks') or []:
                if isinstance(h, dict) and h.get('command'):
                    out.add((event, g.get('matcher') or '', h['command']))
    return out


def _settings_cases(was, now):
    """What a settings.json change is, in words: a hook for an event type it
    had no entry for, a hook's command path rewritten, an entry added or
    dropped, or a change outside the hooks."""
    before, after = _settings_entries(was), _settings_entries(now)
    if before is None or after is None:
        return ['settings.json changed (it does not read as JSON)']
    cases = []
    old_events = {e for e, _m, _c in before}
    new_events = sorted({e for e, _m, _c in after} - old_events)
    for ev in new_events:
        names = sorted({(_HOOK_NAME.search(c) or [None, c])[1]
                        for e, _m, c in after if e == ev})
        cases.append(f'settings.json gains a hook for a new event type, {ev} '
                     f'({", ".join(names)})')
    added = {x for x in after - before if x[0] not in new_events}
    removed = before - after
    name = lambda c: (_HOOK_NAME.search(c) or [None, c])[1]
    for a in sorted(added):
        twin = next((r for r in sorted(removed)
                     if r[0] == a[0] and name(r[2]) == name(a[2])), None)
        if twin:
            removed.discard(twin)
            cases.append(f'settings.json rewrites the path of {name(a[2])} '
                         f'({a[0]}): {twin[2]} -> {a[2]}')
        else:
            cases.append(f'settings.json gains an entry for {name(a[2])} ({a[0]})')
    for r in sorted(removed):
        cases.append(f'settings.json drops its entry for {name(r[2])} ({r[0]})')
    if not cases and (was or '') != (now or ''):
        cases.append('settings.json changes outside its hook entries')
    return cases


def harness_cases(repo, paths):
    """-> what each staged .claude/ path is, in plain words, read from the
    index against HEAD. With hooks as permanent stubs (2026-10-07), an
    ordinary update stages nothing under .claude/, so whatever is left is
    one of a few known cases, and the person is told which."""
    cases = []
    for rel in paths:
        now, was = _git_show(repo, f':{rel}'), _git_show(repo, f'HEAD:{rel}')
        name = rel.rsplit('/', 1)[-1]
        if rel == '.claude/settings.json':
            cases.extend(_settings_cases(was, now))
        elif rel.startswith('.claude/hooks/'):
            if was is None:
                cases.append(f'a new hook file, {name}')
            elif now is None:
                cases.append(f'a hook file removed, {name}')
            elif STUB_MARKER in now and STUB_MARKER not in was:
                cases.append(f'{name} becomes the permanent stub')
            elif STUB_MARKER in now:
                cases.append(f'the hook stub itself changed, {name}')
            else:
                cases.append(f'a hook that is not yet a stub changed, {name}')
        else:
            cases.append(f'{rel} changed')
    return cases


# The fixed per-event entry every hook added since 2026-10-07 runs through.
# It is not itself a gate: it runs what tools/hook_wiring.json lists.
DISPATCH_HOOK = 'precedent-hooks.sh'


def hook_purpose(repo, name):
    """-> what hook `name` does, in its own words: the first sentence of its
    header comment that says so, from the engine copy in tools/ (or the hook
    beside the settings), skipping the "Claude Code adapter:" prefix, a bare
    "Stop hook." and an "Install to ..." line. Read from the script so the
    question never carries a second, drifting description."""
    filler = re.compile(r'^(\w+ hook\.?|Install to .*)$')
    for where in (pathlib.Path(repo) / 'tools' / name,
                  pathlib.Path(repo) / '.claude' / 'hooks' / name):
        try:
            lines = where.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        if any(STUB_MARKER in line for line in lines[:3]):
            continue                    # a stub only points at tools/<name>
        header = []
        for line in lines[1:] if lines and lines[0].startswith('#!') else lines:
            if not line.startswith('#'):
                break
            header.append(line.lstrip('#').strip())
        text = re.sub(r'\bClaude Code adapter:\s*', '', ' '.join(header))
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            sentence = sentence.strip()
            if sentence and not filler.match(sentence):
                return sentence.rstrip('.')
    return f'what it does is in tools/{name}'


def harness_new_gates(repo, paths):
    """-> [(name, event, purpose)]: each hook settings.json now runs at an
    event where HEAD's settings.json did not run it -- a new entry, never a
    path rewrite of one already there, and never the per-event dispatch
    entry. Read from the index against HEAD.

    WHY (2026-10-10, a consumer's Update Vendors). The last-time question
    said "nothing changes about when anything is blocked" while the same
    update wired artifact-publish-gate.sh into settings.json, a gate that
    refuses a hand-written page; the person's yes to that sentence was what
    let the commit through."""
    if '.claude/settings.json' not in paths:
        return []
    before = _settings_entries(_git_show(repo, 'HEAD:.claude/settings.json')) or set()
    after = _settings_entries(_git_show(repo, ':.claude/settings.json')) or set()
    name = lambda c: (_HOOK_NAME.search(c) or [None, c])[1]
    had = {(e, name(c)) for e, _m, c in before}
    out = []
    for e, _m, c in sorted(after - before):
        n = name(c)
        if n == DISPATCH_HOOK or (e, n) in had or any(x[:2] == (n, e) for x in out):
            continue
        out.append((n, e, hook_purpose(repo, n)))
    return out


def harness_ask(paths, last=False, cases=None, gates=None):
    """The question for the person when an update changes hooks or settings.
    `last`: this is the update that turns the hooks into permanent stubs, so
    the question says, in plain words, that it is the last one. `cases`:
    harness_cases(), so any other question says which kind of change it is
    rather than only that something under .claude/ moved. `gates`:
    harness_new_gates(), each hook newly wired and what it does -- so the
    question never says nothing new is blocked when something is."""
    new = ''
    if gates:
        new = (f'It also wires {len(gates)} hook(s) this repository did not '
               f'run before, and each can refuse what it names: '
               + '; '.join(f'{n} ({e}): {w}' for n, e, w in gates) + '. ')
    if last:
        blocked = (new if gates else
                   'Nothing changes about when anything is blocked. ')
        return (f'this update changes {len(paths)} file(s) under .claude/ one '
                f'last time: each hook becomes a permanent pointer to the '
                f'engine, and settings.json gains one fixed entry per event '
                f'for hooks added later. {blocked}From now on hook changes '
                f'arrive with the engine without this question. Ask the '
                f'person in those words before committing; their yes is what '
                f'lets the commit through, and a merge that takes the update '
                f'by itself needs it as {HARNESS_GO_AHEAD}="<their words>". '
                f'Files: {", ".join(paths)}')
    what = f' -- {"; ".join(cases)}' if cases else ''
    return (f'this update changes {", ".join(paths)}{what}. {new}Claude Code\'s '
            f'auto mode holds a commit that changes hooks or settings until '
            f'the person says yes, so ask now, naming these files and what '
            f'each change is, before committing. Their yes is what lets the '
            f'commit through; a merge that takes the update by itself needs '
            f'it as {HARNESS_GO_AHEAD}="<their words>"')


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


def regenerated_step(repo, rep):
    """Rebuild the generated files whose inputs this update staged -- the
    commit backstop's own rule (precedent_regenerate.py), run here so the
    update's check judges current files.

    An update that refreshed tools/build_todo_index.py rebuilt MAP.md and
    GLOSSARY.md but not todo/TODO.md, whose new header the new tool writes;
    the basic check passed, and only the Debut's full check failed on it
    (2026-10-04, a consumer's Update Vendors). Only what the update staged
    is matched, so a person's own unstaged work is never swept in -- the
    regenerator stages a rebuilt file only where nothing of theirs is
    unstaged there, and says so where something is."""
    import precedent_regenerate as preg
    entries = preg._entries(repo)
    if not entries:
        return []
    staged = [l for l in subprocess.run(
        ['git', '-C', str(repo), 'diff', '--cached', '--name-only'],
        capture_output=True, text=True).stdout.splitlines() if l]
    todo = preg.due(entries, staged)
    if not todo:
        return []
    said = []
    rebuilt = preg.regenerate(repo, todo, say=said.append)
    if rebuilt:
        rep.step('generated files', 'rebuilt from this update\'s inputs: '
                 + ', '.join(rebuilt))
    for line in said:
        if 'failed' in line or 'NOT added' in line:
            rep.leave('generated files', line.split(': ', 1)[-1])
    return rebuilt


STAGED_RECORD = 'precedent-update-staged.json'


def _staged_record_path(repo):
    r = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--absolute-git-dir'],
                       capture_output=True, text=True)
    gitdir = r.stdout.strip()
    return pathlib.Path(gitdir) / STAGED_RECORD if r.returncode == 0 and gitdir else None


def _content_hash(path):
    import hashlib
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (IsADirectoryError, FileNotFoundError):
        return None


def _read_record(repo):
    """-> the run-to-run record in the git directory, {} when there is none.
    One file for everything a rerun takes from an earlier run of the same
    update: `paths`, what a FAILED run staged (record_staged_output), and
    `pin`, the source commit the update started from (record_pin)."""
    rec = _staged_record_path(repo)
    try:
        data = json.loads(rec.read_text(encoding='utf-8')) if rec else {}
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_record(repo, data):
    rec = _staged_record_path(repo)
    if rec is None:
        return
    try:
        if data:
            rec.write_text(json.dumps(data, indent=1) + '\n', encoding='utf-8')
        elif rec.is_file():
            rec.unlink()
    except OSError:
        pass


def record_staged_output(repo, paths):
    """Write down, in the git directory, what this run staged and what each
    path held when it stopped: the hash of its content, or None for a path
    it deleted. restore_own_staged_output() reads it at the next run."""
    data = _read_record(repo)
    data['paths'] = {p: _content_hash(repo / p) for p in sorted(paths)}
    _write_record(repo, data)


def record_kept_output(repo, paths):
    """Write down what this run leaves staged as the update's output, in
    every outcome, under the record's `staged` key: each path and the hash
    it holds, for earlier_runs_output() at the next run. A path with an
    unstaged change on top is left out -- what is on top is not the
    update's. Unlike `paths` (record_staged_output), nothing is put back
    from this; it is only how a rerun tells its own output from yours."""
    data = _read_record(repo)
    g = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True)
    kept = {p: _content_hash(repo / p) for p in sorted(paths)
            if g('diff', '--quiet', '--', p).returncode == 0}
    if kept:
        data['staged'] = kept
    else:
        data.pop('staged', None)
    _write_record(repo, data)


def earlier_runs_output(repo, before, failed_paths=None):
    """-> the paths of `before` an earlier run of this update staged and
    nobody has changed since: staged, no unstaged change on top, and holding
    the content the record names (record_kept_output's `staged`, or the
    `paths` a FAILED run recorded, read before restore_own_staged_output
    pops them, as `failed_paths`).

    WHY (2026-10-08, a consuming repository). A second run before the
    commit said "116 already uncommitted before it ran, left as they were",
    and every one was the first run's own staged output; git status showed
    nothing unstaged. The staged line now counts these apart from what was
    really uncommitted before any run of the update."""
    known = dict(_read_record(repo).get('staged') or {})
    known.update(failed_paths or {})
    g = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True)
    out = set()
    for rel in sorted(set(before) & set(known)):
        if _content_hash(repo / rel) != known[rel]:
            continue
        if g('diff', '--quiet', '--', rel).returncode != 0:
            continue        # an unstaged change on top: someone's
        if g('diff', '--cached', '--quiet', '--', rel).returncode == 0:
            continue        # not staged (untracked, or back to HEAD)
        out.add(rel)
    return out


def staged_line(n, before, earlier):
    """-> the `staged` step's outcome: what this run wrote, what an earlier
    run of it staged and left, and what was uncommitted before either."""
    kept = set(earlier) & set(before)
    theirs = set(before) - kept
    return (f'{n} path(s) this update wrote or deleted'
            + (f'; {len(kept)} staged by an earlier run of this update and '
               f'unchanged since, still staged as its output' if kept else '')
            + (f'; {len(theirs)} already uncommitted before it ran, left as '
               f'they were' if theirs else ''))


def held_pin(repo):
    """-> {'commit', 'branch'} an unfinished update of `repo` is pinned to,
    or None.

    WHY (2026-10-08, a consuming repository). Every run fetched the branch
    it follows again, so an update that took several rounds of LEFT FOR YOU
    chased a moving target: it started at one commit of main and finished
    against another, and a decline already settled came back, because
    upstream had changed that file again in between. The first run of an
    update now records the commit it read; each rerun takes that same
    commit until one reports DONE, or until it is told to move (--move)."""
    pin = _read_record(repo).get('pin')
    if isinstance(pin, dict) and pin.get('commit') and pin.get('branch'):
        return pin
    return None


def record_pin(repo, commit, branch, note=None):
    """`note`: what the commit message must say about how the commit was
    chosen (a --take-anyway), so a rerun says it again."""
    data = _read_record(repo)
    data['pin'] = {'commit': commit, 'branch': branch}
    if note:
        data['pin']['note'] = note
    _write_record(repo, data)


def take_pin(repo, follow, move=False):
    """-> (commit or None, what to say on the source line) for a run with no
    --from-ref: the commit an unfinished update of `repo` is pinned to, or
    None to read `follow`'s tip as before. A pin on another branch (the repo
    now follows a different one), one the source clone no longer holds, and
    one --move was asked to drop, are dropped, and said."""
    pin = held_pin(repo)
    if not pin:
        return None, None
    commit, branch = pin['commit'], pin['branch']
    rc, tip = run(['git', '-C', str(SOURCE), 'rev-parse', f'origin/{follow}'], SOURCE)
    tip = tip.strip() if rc == 0 else ''
    if move:
        clear_pin(repo)
        return None, (f'moved, as asked, off {commit[:12]}, the commit an earlier '
                      f'run of this update started from')
    if branch != follow:
        clear_pin(repo)
        return None, (f'an earlier run was pinned to {branch} @ {commit[:12]}, and '
                      f'this repo now follows {follow}, so it starts from {follow}')
    if run(['git', '-C', str(SOURCE), 'cat-file', '-e', f'{commit}^{{commit}}'],
           SOURCE)[0] != 0:
        clear_pin(repo)
        return None, (f'the commit an earlier run was pinned to, {commit[:12]}, is '
                      f'not in {SOURCE}, so it starts from the tip')
    if tip and tip != commit:
        return commit, (f'pinned: the commit this update started from. {follow} '
                        f'has moved on to {tip[:12]}; --move takes it, or the '
                        f'newest commit before it whose GitHub test passed')
    return commit, 'pinned: the commit this update started from, still the tip'


def clear_pin(repo):
    data = _read_record(repo)
    if data.pop('pin', None) is not None:
        _write_record(repo, data)


def vendored_layer_paths(repo, paths):
    """-> those of `paths` that belong to the two vendored layers: the
    engine (tools/, its vendored hooks, the paths precedent.json declares
    under engine_paths) and the mirrored catalogue (what
    precedent_resolve.mirrored_prefixes() names, and its manifest)."""
    declared = set()
    for spec in ('HEAD:tools/' + pve.MANIFEST_NAME, None):
        try:
            text = (subprocess.run(['git', '-C', str(repo), 'show', spec],
                                   capture_output=True, text=True).stdout if spec
                    else (repo / 'tools' / pve.MANIFEST_NAME).read_text(encoding='utf-8'))
            declared |= set((json.loads(text) or {}).get(pve.ENGINE_PATHS_KEY) or {})
        except (OSError, ValueError, AttributeError):
            pass
    try:
        import precedent_resolve as pr
        mirrors = tuple(pr.mirrored_prefixes(repo) or ())
    except Exception:                                          # noqa: BLE001
        mirrors = ()
    engine = ('tools/', f'{pve.HOOK_DEST_DIR}/') + mirrors
    return [p for p in paths if p.startswith(engine)
            or p == 'process/manifest.json' or p in declared]


def restore_own_staged_output(repo, select):
    """-> the paths of `rels` put back to HEAD: each one an earlier run
    staged and left, still holding exactly what that run wrote, staged and
    working copies alike. A path changed since is someone's work and is
    left alone, for the refusal to name.

    Found 2026-10-02, taking main into a large consumer: a run ended FAILED
    on its deep check with its refreshed engine files staged, as the report
    says it leaves them, and the rerun the FAILED message asked for stopped
    at once on one of them -- "a vendored file edited here and not
    committed" -- the very file the first run had merged with the repo's
    committed local edit. Its own output, refused as somebody's edit.

    Only the two vendored layers are put back (`select(repo, paths)` picks
    them): the local-edit resolution needs the committed local version and
    the committed manifest in place to merge again, and this command writes
    every file of both layers again from HEAD. Everything else an earlier
    run staged stays, because a later run builds on it -- the template
    sections a run recorded as left out on purpose are how the next run
    knows not to ask again."""
    data = _read_record(repo)
    paths = data.pop('paths', None) or {}
    if not paths:
        return []
    g = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                  capture_output=True, text=True)
    back = []
    for rel in sorted(select(repo, paths)):
        f = repo / rel
        if _content_hash(f) != paths[rel] or g('diff', '--quiet', '--', rel).returncode != 0:
            continue
        if g('cat-file', '-e', f'HEAD:{rel}').returncode == 0:
            g('checkout', '-q', 'HEAD', '--', rel)
        else:
            g('rm', '-q', '--cached', '--ignore-unmatch', '--', rel)
            if f.is_file():
                f.unlink()
        back.append(rel)
    _write_record(repo, data)    # what else it holds (the pin) stays
    return back


def realign_catalogue_record(repo, wrote, back):
    """Keep the catalogue copy and its record together across a put-back.
    -> the commit the record was put back to, or None.

    restore_own_staged_output() puts back each file an earlier run wrote and
    nobody has touched since. process/manifest.json is often touched since:
    practice_audit.py --redecide writes a decline there between a FAILED run
    and its rerun. Then the copy went back to HEAD and the manifest kept
    naming the commit the failed run mirrored, and the rerun judged HEAD's
    older copy against that commit -- every file "a local edit upstream has
    not changed", kept (2026-10-08, a consuming repository: 440 files).
    Only the keys checkin.py record writes (commit, synced_from, _note,
    copy_tree) go back to HEAD's, and only when no other key of `upstream`
    differs, so a decline or any other change of the person's stays."""
    rel = 'process/manifest.json'
    if rel not in wrote or rel in back:
        return None
    try:
        import precedent_resolve as pr
        mirrors = tuple(pr.mirrored_prefixes(repo) or ())
    except Exception:                                          # noqa: BLE001
        mirrors = ()
    if not mirrors or not any(p.startswith(mirrors) for p in back):
        return None
    shown = subprocess.run(['git', '-C', str(repo), 'show', f'HEAD:{rel}'],
                           capture_output=True, text=True)
    try:
        head = (json.loads(shown.stdout).get('upstream') or {}) if shown.returncode == 0 else {}
        data = json.loads((repo / rel).read_text(encoding='utf-8'))
    except (OSError, ValueError, AttributeError):
        return None
    now = data.get('upstream') if isinstance(data, dict) else None
    own = ('commit', 'synced_from', '_note', 'copy_tree')
    if not isinstance(now, dict) or not head.get('commit') or now == head:
        return None
    if {k: v for k, v in now.items() if k not in own} != \
            {k: v for k, v in head.items() if k not in own}:
        return None
    fixed = {k: (head[k] if k in own else v) for k, v in now.items()
             if k not in own or k in head}
    fixed.update({k: head[k] for k in own if k in head and k not in fixed})
    data['upstream'] = fixed
    (repo / rel).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                            encoding='utf-8')
    return head['commit']


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


def adopt_catalogue_output(repo, before, pinned):
    """-> the paths in `before` under the vendored catalogue tree that are
    this update's own mirror, written by an earlier run, to stage as the
    update's; [] when any is not.

    2026-10-04, a consumer's fourth run: 80 process/upstream/ files an
    earlier run's mirror wrote (62 modified, 18 deleted) were "already
    uncommitted before it ran, left as they were", every one byte for byte
    upstream's, while process/manifest.json was staged naming the new
    commit -- so committing what was staged would have recorded that commit
    over the old tree. A path is the update's when the catalogue manifest
    names the pinned commit and the file is upstream's blob at that commit,
    or is gone where upstream has none or the mirror leaves it out. One
    mismatch means someone else's edit is in the mix, and nothing is taken."""
    mf = repo / 'process' / 'manifest.json'
    try:
        up = json.loads(mf.read_text(encoding='utf-8')).get('upstream') or {}
    except (OSError, ValueError, AttributeError):
        return []
    if pinned not in (up.get('synced_from'), up.get('commit')):
        return []
    tree = str(up.get('vendored_at') or 'process/upstream').rstrip('/')
    mine = sorted(p for p in before if p.startswith(tree + '/'))
    if not mine:
        return []
    try:
        import checkin as _ci
        in_copy = _ci._in_copy
    except Exception:                                       # noqa: BLE001
        return []
    for path in mine:
        rel = path[len(tree) + 1:]
        here = repo / path
        shown = subprocess.run(['git', '-C', str(SOURCE), 'show', f'{pinned}:{rel}'],
                               capture_output=True)
        theirs = shown.stdout if shown.returncode == 0 and in_copy(rel) else None
        if here.is_file():
            if theirs is None or here.read_bytes() != theirs:
                return []
        elif theirs is not None:
            return []
    if 'process/manifest.json' in before:
        mine.append('process/manifest.json')
    return mine


def _engine_owned(repo):
    """-> the repo-relative paths tools/ENGINE_MANIFEST.json says the engine
    vendored here (its files under tools/, its hooks under .claude/hooks/),
    or an empty set where there is no readable manifest."""
    try:
        mf = json.loads((pathlib.Path(repo) / 'tools' / 'ENGINE_MANIFEST.json')
                        .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return set()
    return ({f'tools/{f}' for f in mf.get('files') or []}
            | {f'.claude/hooks/{f}' for f in mf.get('hook_files') or []})


def citations(repo):
    """-> ([(where, why)] to fix, [where] to read), or None when the lookup
    could not run. Asks the SOURCE clone's copy of the lookup, for the same
    reason every other step here does: it is the current code."""
    refs = SOURCE / 'tools' / 'precedent_practice_refs.py'
    if not refs.is_file():
        return None
    # --code: a citation in a tool the update never touched is as live as
    # one in a document (2026-10-04: a consumer's tools/*.py kept citing a
    # slug a shared set had deduplicated, this said there was nothing to
    # fix, and only the full check at Debut found it).
    r = subprocess.run([sys.executable, str(refs), '--repo', str(repo),
                        '--withdrawn', '--code', '--changed-since', 'HEAD', '--staged',
                        '--json'], cwd=str(repo), capture_output=True,
                       text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    return citation_findings(data, _engine_owned(repo))


def citation_findings(data, engine=frozenset()):
    """-> ([(where, why)] to fix, [where] to read) from
    precedent_practice_refs.py's JSON, leaving out the paths in `engine`."""
    fix, read = [], []
    slugs, successors = data.get('slugs', {}), data.get('successors', {})
    for h in data.get('hits', []):
        if h.get('source') != 'this repository' or h.get('kind') != 'live':
            continue
        # A file the engine owns is not this repo's to edit: the next
        # refresh rewrites it, and its citations are upstream's to keep
        # current (2026-10-04: a consumer was sent to read four lines of a
        # vendored hook and one of tools/bootstrap.sh).
        if h['file'] in engine:
            continue
        where = f"{h['file']}:{h['line']}"
        succ = successors.get(h['slug'])
        if h.get('must_fix'):
            fix.append((where, f"cites `{h['slug']}`, which is no longer in force"
                        + (f" -- cite `{succ}`" if succ else
                           " anywhere -- say in prose what it covered")))
        elif slugs.get(h['slug']) == 'Rule reworded':
            # Still in force under the same name: only prose can carry the
            # old rule's wording, so only a document is worth a read. A
            # `practice: SLUG` comment in code names the rule, whatever its
            # wording -- the same consumer was sent to read five of those.
            if h['file'].endswith('.md'):
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


def rebuild_views_after_stamp(repo, stamped):
    """-> [view] build_views.py built again because stamp_headers() bumped
    its source.

    MAP.md and GLOSSARY.md copy their source's version header, and the views
    step built them BEFORE stamp_headers() bumped MAP.source.md, so the check
    failed on a stale MAP.md on every run (2026-10-04, a consumer's Update
    Vendors). The views are built again; only a view the update had staged is
    staged again, the way stamp_headers() treats what it stamps."""
    build = pathlib.Path(repo) / 'tools' / 'build_views.py'
    if not build.is_file():
        return []
    import build_views as _bv
    sources = {getattr(_bv, 'MAP_SOURCE', None),
               getattr(_bv, 'GLOSSARY_SOURCE', None)} - {None}
    # A source can be a file or its directory form (MAP.source/).
    prefixes = {_bv.source_dir_name(s) + '/' for s in sources}
    if not any(p in sources or p.startswith(tuple(prefixes)) for p in stamped):
        return []
    views = generated_full_views(repo)
    if not views:
        return []
    staged = set(subprocess.run(
        ['git', '-C', str(repo), 'diff', '--cached', '--name-only'],
        capture_output=True, text=True).stdout.split())
    rc, out = run([sys.executable, str(build), '--repo', '.', '--views-only'], repo)
    if rc != 0:
        # Said, never swallowed: the check would then fail on the stale view
        # with nothing pointing at why.
        raise RuntimeError(tail(out, repo=repo))
    changed = set(subprocess.run(['git', '-C', str(repo), 'diff', '--name-only'],
                                 capture_output=True, text=True).stdout.split())
    rebuilt = [v for v in views if v in changed and v in staged]
    if rebuilt:
        subprocess.run(['git', '-C', str(repo), 'add', '--', *rebuilt],
                       capture_output=True)
    return rebuilt

def undo_leftover_standin(repo):
    """-> the short hash of a stand-in commit an interrupted run left at
    HEAD, now undone, or None.

    WHY (2026-10-06, a consumer repository): an Update Vendors run under
    `timeout 590` was sent SIGTERM during the deep check. Python's default
    SIGTERM handling exits without running `finally`, so the stand-in commit
    judged_as_committed() makes stayed at HEAD. The rerun found nothing to
    stage and never looked at HEAD; a commit made on top would have been
    the one the next undo removed.

    Only HEAD, and only when its message starts with TEMP_COMMIT_MESSAGE.
    `git reset --soft HEAD~1` moves HEAD alone, so the stand-in's content
    comes back as staged changes: nothing is discarded."""
    r = subprocess.run(['git', '-C', str(repo), 'log', '-1', '--format=%h%x00%B', 'HEAD'],
                       capture_output=True, text=True)
    if r.returncode != 0 or '\0' not in r.stdout:
        return None
    short, message = r.stdout.split('\0', 1)
    if not message.startswith(TEMP_COMMIT_MESSAGE):
        return None
    if subprocess.run(['git', '-C', str(repo), 'rev-parse', '-q', '--verify', 'HEAD~1'],
                      capture_output=True).returncode != 0:
        return None
    if subprocess.run(['git', '-C', str(repo), 'reset', '-q', '--soft', 'HEAD~1'],
                      capture_output=True).returncode != 0:
        return None
    return short.strip()


class _Terminated(SystemExit):
    """SIGTERM, turned into an exception so `finally` blocks run."""


def _raise_on_sigterm(signum, _frame):
    raise _Terminated(128 + signum)


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
    # A run killed by SIGTERM (`timeout`, a closed terminal) exits without
    # running `finally` under Python's default handling, which left the
    # stand-in at HEAD on 2026-10-06. For as long as it exists, SIGTERM
    # raises instead, so the undo below runs.
    try:
        previous, installed = signal.signal(signal.SIGTERM, _raise_on_sigterm), True
    except ValueError:              # not the main thread: leave it as it was
        previous, installed = None, False
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
        if installed:
            signal.signal(signal.SIGTERM, previous if previous is not None
                          else signal.SIG_DFL)


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
    # Tiers are a ladder user's, in a repository that has them (D3). For
    # anyone else this step says nothing at all: a report line about
    # pre-staging and staging is the ladder's words in their session.
    ladder = pb.ladder_in_force(repo)
    if ladder is False or (ladder and not pb.repo_has_tiers(repo)):
        return
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
        # pre-staging is no tier for a person who lands on staging
        # (precedent_branches.pre_staging_retired), so it is not named.
        rep.step('branch tiers', '; '.join(made) if made else
                 'staging and main both present' if pb.pre_staging_unused(repo)[0]
                 else 'pre-staging, staging and main all present')


# ONLY A MAIN THAT PASSED GITHUB'S TEST IS TAKEN (2026-10-09, the main
# landing plan, piece A; Morgan, the same day: "Act on the ... plan").
# The risk of a fast route to main is not main being red for half an hour; it
# is another repository running Update Vendors in that half hour and taking
# a broken engine into itself. On 2026-10-09 a test that no longer fit sat on
# main for about an hour. So the update takes the newest main commit whose
# GitHub test passed, and when that is not the newest, says which it took,
# how far behind, and why -- for everyone, Alex included (decision 1).
#
# Main's first-parent line only: each of those commits is a push to main,
# which the test runs on; a commit inside a merged branch was tested, if at
# all, as part of its pull request. GREEN_WINDOW bounds the look back, and
# with it the API calls (two or three a commit, github_test_state).
GREEN_WINDOW = 10
# The emergency override, in the person's own words ("take <commit>
# anyway"), recorded in the report and the commit message.
TAKE_FLAG = '--take-anyway'
_STATE_WORDS = {'failed': 'failed on', 'running': 'is still running on',
                'none': 'has not run on',
                'unmarked': 'left no passed marker, and GitHub could not be asked, on'}


def main_test_state(sha, tests):
    """-> (state, detail): main's GitHub test on `sha` of the source clone,
    as precedent_branches.github_test_state reads it. Its own name so the
    harness can stand GitHub in."""
    return pb.github_test_state(SOURCE, sha, tests)


def passed_trees():
    """-> the trees main's GitHub test marked as passed (git refs under
    precedent_branches.PASSED_PREFIX on the source's origin), or None when
    they could not be read. Its own name so the harness can stand it in."""
    try:
        return pb.passed_markers(SOURCE)
    except (OSError, subprocess.SubprocessError):
        return None


def _tree(sha):
    rc, out = run(['git', '-C', str(SOURCE), 'rev-parse', f'{sha}^{{tree}}'], SOURCE)
    return out.strip() if rc == 0 else None


def _why_not_newer(skipped):
    """-> "GitHub's test is still running on X and failed on Y" for the
    newer commits passed over, newest first, grouped by state."""
    groups = {}
    for sha, state in skipped:
        groups.setdefault(state, []).append(sha[:12])
    parts = []
    for state, shas in groups.items():
        named = ', '.join(shas[:3]) + (f' and {len(shas) - 3} more' if len(shas) > 3 else '')
        parts.append(f'{_STATE_WORDS.get(state, state + " on")} {named}')
    return "GitHub's test " + ' and '.join(parts)


def source_commit(follow, tip, take=None):
    """-> {'commit', 'step', 'warning', 'commit_note', 'failed'}: the commit
    of the source clone this update takes when no --from-ref names one.

    `tip` is `follow`'s newest commit. Off main, or with no GitHub test in
    the source (precedent_branches.github_tests), the tip, as before. On
    main, the newest first-parent commit whose test passed; a 'step' line
    when that is not the tip. GitHub not answering about the tip: the tip,
    with a 'warning', never silently. Nothing passed within GREEN_WINDOW, or
    GitHub stopping partway: 'failed', and nothing is taken.

    With `take`, the person named a commit of `follow` to take anyway: it is
    taken whatever its test says, and the step and 'commit_note' record that
    it was their word."""
    out = {'commit': tip, 'step': None, 'warning': None, 'commit_note': None,
           'failed': None}
    if take:
        rc, sha = run(['git', '-C', str(SOURCE), 'rev-parse', '--verify', '-q',
                       f'{take}^{{commit}}'], SOURCE)
        sha = sha.strip()
        if rc != 0 or not sha:
            out['failed'] = f'{TAKE_FLAG} {take}: no such commit in {SOURCE}'
            return out
        if tip and run(['git', '-C', str(SOURCE), 'merge-base', '--is-ancestor',
                        sha, tip], SOURCE)[0] != 0:
            out['failed'] = (f'{TAKE_FLAG} {take}: {sha[:12]} is not on {follow}, so '
                             f'it is not a {follow} commit to take anyway. '
                             f'--from-ref vendors any commit, for testing')
            return out
        tests = pb.github_tests(SOURCE, sha)
        state, detail = main_test_state(sha, tests) if tests else (
            'none', 'no GitHub test is installed')
        out['commit'] = sha
        if state == 'passed':
            out['step'] = (f"took {follow} @ {sha[:12]} on the person's word "
                           f"({TAKE_FLAG}); its GitHub test passed")
            out['commit_note'] = (f"Took BestPractice {follow} @ {sha[:12]} on the "
                                  f"person's word ({TAKE_FLAG}).")
        else:
            out['step'] = (f"took {follow} @ {sha[:12]} on the person's word "
                           f"({TAKE_FLAG}), although its GitHub test had not "
                           f"passed ({state}: {detail})")
            out['commit_note'] = (f"Took BestPractice {follow} @ {sha[:12]} on the "
                                  f"person's word ({TAKE_FLAG}), although its "
                                  f"GitHub test had not passed.")
        return out
    if follow != pb.MAIN or not tip:
        return out
    tests = pb.github_tests(SOURCE, tip)
    if not tests:
        return out
    rc, listed = run(['git', '-C', str(SOURCE), 'rev-list', '--first-parent',
                      f'--max-count={GREEN_WINDOW}', tip], SOURCE)
    commits = listed.split() if rc == 0 else [tip]
    skipped = []
    # The git marker first: no API call, and it answers where the API cannot
    # (a session with no GitHub access to BestPractice). An unmarked commit
    # falls back to asking GitHub.
    marked = passed_trees() or set()
    for sha in commits:
        if marked and _tree(sha) in marked:
            state, detail = 'passed', 'its passed marker'
        else:
            state, detail = main_test_state(sha, tests)
        if state == 'unknown' and marked:
            # GitHub cannot be asked, and the markers can: a commit without
            # one is not known to have passed, so look further back for the
            # newest that is. Before the first marker existed there is none
            # to find, and the tip is taken with a warning, as before.
            skipped.append((sha, 'unmarked'))
            unknown = detail
            continue
        if state == 'passed':
            out['commit'] = sha
            if skipped:
                n = len(skipped)
                out['step'] = (f"took {follow} @ {sha[:12]}, {n} commit"
                               f"{'s' if n != 1 else ''} behind the newest {follow}, "
                               f"{tip[:12]}, because {_why_not_newer(skipped)}. This "
                               f"repo gets the newer ones once their test passes")
            return out
        if state == 'unknown':
            if not skipped:
                again = ("Run it again once GitHub answers")
                if 'add_repo' in (detail or '') or 'not enabled for this session' in (detail or ''):
                    # The session has no GitHub access to the source: no
                    # wait fixes that, attaching it does (practice:
                    # reach-or-ask).
                    again = (f"This session has no GitHub access to "
                             f"{pb._slug(SOURCE) or 'BestPractice'}: attach it "
                             f"(add_repo, read access), then run it again")
                out['warning'] = (f"could not ask GitHub whether {follow}'s test "
                                  f"passed ({detail}), so this took the newest "
                                  f"{follow}, {tip[:12]}, without knowing. {again}")
                return out
            out['failed'] = (f"GitHub stopped answering ({detail}) while this "
                             f"looked for the newest {follow} whose test passed, "
                             f"after finding that {_why_not_newer(skipped)}. "
                             f"Nothing was taken. Run "
                             f"it again, or take a commit anyway in the person's "
                             f"own words with {TAKE_FLAG} <commit>")
            out['commit'] = None
            return out
        skipped.append((sha, state))
    if any(state == 'unmarked' for _, state in skipped):
        out['warning'] = (f"could not ask GitHub whether {follow}'s test passed "
                          f"({unknown}), and none of {follow}'s newest "
                          f"{len(commits)} commits carries a passed marker, so "
                          f"this took the newest {follow}, {tip[:12]}, without "
                          f"knowing")
        return out
    out['commit'] = None
    out['failed'] = (f"none of {follow}'s newest {len(commits)} commits passed "
                     f"GitHub's test: {_why_not_newer(skipped)}. Nothing was "
                     f"taken. Run it again once {follow}'s test passes, or take "
                     f"a commit anyway in the person's own words with "
                     f"{TAKE_FLAG} <commit>")
    return out


def update(repo, skip_check=False, ref=None, move=False, take=None):
    rep = Report()
    rep.pin_repo = repo
    elsewhere = source_is_its_own_clone()
    if elsewhere:
        return rep.close(f"this copy of precedent_update.py sits in {SOURCE}, "
                         f"which is {elsewhere} -- a vendored copy, not a "
                         f"BestPractice clone, so it would fetch the wrong "
                         f"repository. Run the clone's own copy from the "
                         f"consuming repo: {clone_command(repo)}")
    # A run killed during the deep check can leave its stand-in commit at
    # HEAD; undo it before anything is staged (undo_leftover_standin).
    leftover = undo_leftover_standin(repo)
    if leftover:
        rep.step('earlier run', f'undid stand-in commit {leftover} an interrupted '
                 'run left at HEAD; its changes are staged again, nothing lost')
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
    # A vendored file an earlier run staged and nobody has touched since is
    # this command's own output, written again below -- never an edit to
    # refuse. Put back before `before` is read, so it is not counted as
    # someone's uncommitted work either.
    # Which of them the earlier run had deleted: put back to HEAD so the
    # local-edit rules see the committed state, they are deleted again once
    # the copy is checked against its record (catalogue_copy_postcondition).
    wrote = _read_record(repo).get('paths') or {}
    back = restore_own_staged_output(repo, vendored_layer_paths)
    put_back_deleted = {p for p in back if wrote.get(p) is None}
    if back:
        rep.step('earlier run', 'put back to HEAD, to be resolved and written '
                 'again: ' + ', '.join(back) + ' -- staged by an earlier run '
                 'and unchanged since, so its own output, not an edit')
    realigned = realign_catalogue_record(repo, wrote, back)
    if realigned:
        rep.step('earlier run', f'process/manifest.json changed after that run, '
                 f'so it was not put back with the copy; its record of the copy '
                 f'goes back to {realigned[:12]}, the commit the copy now holds, '
                 f'and your other changes to it stay')
    before = dirty_paths(repo)
    rep.before = before
    rep.earlier = earlier_runs_output(repo, before, wrote)
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
    # The branch this repo follows: SOURCE_BRANCH, or the `upstream_branch`
    # its precedent.json names (pve.followed_branch, 2026-10-05).
    follow = pve.followed_branch(repo)
    problem = pve.upstream_branch_problem(repo)
    if problem:
        rep.leave('precedent.json', problem)
    if ref is None:
        rc, out = run(['git', '-C', str(SOURCE), 'fetch', 'origin',
                       pve.tracking_refspec(follow)], SOURCE)
        if rc != 0:
            return rep.close(f"could not fetch origin/{follow} in "
                             f"{SOURCE}:\n{tail(out, repo=repo)}")
    # An unfinished update keeps the commit it started from (held_pin); an
    # explicit --from-ref neither reads nor moves it, and --take-anyway
    # moves it to the commit the person named.
    pinned, said = (None, None) if ref else take_pin(repo, follow, move or bool(take))
    rc, head = run(['git', '-C', str(SOURCE), 'rev-parse',
                    ref or pinned or f'origin/{follow}'], SOURCE)
    head_ok = rc == 0
    # The commit the vendored engine -- and so a section 0 catalogue, which
    # moves with it -- was last synced from. Read now: step 2 rewrites it.
    try:
        last_synced = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                                 .read_text(encoding='utf-8')).get('source_commit')
    except (OSError, ValueError):
        last_synced = None
    # Main is taken only where its GitHub test passed (source_commit), once,
    # here: a pinned rerun takes the commit its first run chose.
    chosen = {}
    if ref is None and head_ok and not pinned:
        newest = head.strip()
        chosen = source_commit(follow, newest, take)
        if chosen['failed']:
            return rep.close(chosen['failed'])
        if (chosen['commit'] != newest and not take and last_synced
                and pve.engine_is_ahead(SOURCE, last_synced, chosen['commit'])
                and not pve.engine_is_ahead(SOURCE, last_synced, newest)):
            return rep.close(
                f"this repo's engine is already at {follow} @ {last_synced[:12]}, "
                f"newer than {chosen['commit'][:12]}, the newest {follow} whose "
                f"GitHub test passed: {chosen['step']}. Nothing was taken. Run it "
                f"again once {follow}'s test passes, or take a commit anyway in "
                f"the person's own words with {TAKE_FLAG} <commit>")
        head = chosen['commit'] + '\n'
    elif ref is None and pinned:
        chosen = {'commit_note': (held_pin(repo) or {}).get('note')}
        if chosen['commit_note']:
            chosen['step'] = f"kept from the run that started it: {chosen['commit_note']}"
    rep.step('source', (f"{follow} @ {head.strip()[:12]}" if head_ok
                        else f"could not read {ref or pinned or 'origin/' + follow}")
             + (f" -- {said}" if said else ''))
    if chosen.get('step'):
        rep.step('GitHub test', chosen['step'])
    if chosen.get('warning'):
        rep.step('GitHub test', f"WARNING: {chosen['warning']}")
        rep.warnings.append(chosen['warning'])
    rep.commit_note = chosen.get('commit_note')
    if ref is None and head_ok:
        record_pin(repo, head.strip(), follow, note=rep.commit_note)
        rep.pin = (repo, head.strip(), follow)
    # What the catalogue is mirrored from: the commit read just above, the
    # one the engine is handed too -- never a second read of the branch by
    # checkin.py update's own fetch, which a pinned rerun would undo.
    take = ref or (head.strip() if head_ok else None)

    # 2. The engine, by the consumer's own copy: refresh() takes ROOT from
    # where it sits. It replaces itself and re-runs, so an old copy still
    # ends on the current code.
    argv = [sys.executable, str(engine_tool), 'refresh', str(SOURCE)]
    engine_ref = ref or engine_refresh_ref(SOURCE, head.strip() if head_ok else '',
                                           follow, last_synced)
    if engine_ref:
        argv += ['--from-ref', engine_ref]
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
                      'it, and the next run keeps or replaces it and says '
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
    rep.step('engine', engine_summary(out, last_synced,
                                      follow=None if ref else follow,
                                      tip=engine_ref))
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
                         f", not {follow} @ {tip[:12]}: this repo's "
                         f"own engine copy vendored from another ref. Run this "
                         f"again with --from-ref {tip[:12]} to take "
                         f"{follow}'s engine, then review the diff")
    seeded, asks = seed_engine_budgets(repo, tip, last_synced)
    if seeded:
        rep.step('API budgets', 'tools/github_api_budgets.json now budgets '
                 + ', '.join(f'{t} at {n} call(s) a run' for t, n in seeded)
                 + ' -- upstream\'s figure and note for a tool upstream ships; '
                 'change it there if this repo needs its own')
    for tool, ours, theirs in asks:
        rep.leave(f'tools/github_api_budgets.json: {tool}',
                  f'upstream now budgets the vendored tools/{tool} at {theirs} '
                  f'API call(s) a run and this repo at {ours}; keep this repo\'s '
                  f'figure, or take upstream\'s new one')
    # A difference precedent.json records as kept on purpose, and a legacy
    # bootstrap wrapper the refresh replaced, are said once each as a note
    # -- never a call to make (precedent_vendor_engine.KEPT_DIVERGENCES_KEY).
    # A self-replacing refresh prints them on both passes.
    for line in dict.fromkeys(l.strip() for l in out.splitlines()):
        if line.startswith('KEPT ON PURPOSE: '):
            rep.step('kept on purpose', line[len('KEPT ON PURPOSE: '):])
        elif line.startswith(('PIN NARROWED: ', 'PIN UPDATED: ')):
            rep.step('kept pin updated', line.split(': ', 1)[1])
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
        rep.step('catalogue pin', f'repointed to {follow} '
                 f'(the branch this repo follows; nothing to ask)')
    renamed_sources_step(repo, rep, out)
    level_alias_step(repo, rep)
    maintainers_step(repo, rep)

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
                          'the next run keeps or replaces it and says '
                          'which; or undo the change. Nothing was written')
            rep.step('catalogue', 'refused: the vendored tree has an uncommitted change')
            return rep.close()
        swap = le.Swap(repo, [] if unjudged else edits)
        with swap:
            rc, out = run(checkin + ['update', str(SOURCE), '--repo', str(repo)]
                          + (['--from-ref', take] if take else []), repo)
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
                                           '--note', 'Update Vendors'] + resolving
                                + (['--from-ref', take] if take else []), repo)
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
        # After the local-edit rules, which write back what they keep: the
        # copy is the commit its record names, or the report says why not.
        catalogue_copy_postcondition(repo, rep, put_back_deleted)
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
                                                or p in {f'{rel}/{c}' for c in
                                                         CATALOGUE_COMPANIONS})}
            rep.before = before

    # After the templates have moved: what they replaced that an update
    # cannot convert for the repo, the install-once file an update can
    # bring forward on its own, and the install-once files it can only
    # report on, since each is the repo's own once written.
    for old, why in legacy_root_docs(repo, head.strip() if head_ok else None, rep):
        rep.leave(old, why)
    gitignore_step(repo, rep, head.strip() if head_ok else None)
    gotchas_seed_step(repo, rep, head.strip() if head_ok else None)
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

    # A retired set is judged AFTER the catalogue: a rule it held may be
    # folded into universal by this very update, and judged before, against
    # the old catalogue, it read as "in force nowhere else" and the set was
    # kept (a consumer's update, 2026-10-06).
    dropped_sets = retired_sources_step(repo, rep)

    # 3c. Off pre-staging, for a person who lands on staging: what waits there
    # merged into staging, this repo's own instructions and links repointed,
    # the branch offered for deletion. Before the views, so they render the
    # reworded sources.
    retire_pre_staging_step(repo, rep)

    # 4. The views. A refresh changes what the loader renders.
    #
    # A practice SET renders more than a consumer does: MAP.md and
    # GLOSSARY.md too, and MAP.md lists every engine file. Its deep check is
    # `build_views.py --check`, so an update that adds an engine file and
    # regenerates only the loader block fails its own gate. 2026-09-27: all
    # four of Morgan's sets stopped on exactly that, one new MAP.md row
    # each, fixed by hand. A set has no precedent_sync_views.py anyway --
    # so it gets the full build, the same one its check compares against.
    brought_sets_step(rep, repo=repo)
    sync = repo / 'tools' / 'precedent_sync_views.py'
    build = repo / 'tools' / 'build_views.py'
    try:
        kind = json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                          .read_text(encoding='utf-8')).get('kind')
    except (OSError, ValueError):
        kind = None
    # Before the views, so the copies the views render come out tidy too.
    tidied = tidy_field_order(repo, kind)
    if tidied:
        rep.step('field order', f'{len(tidied)} of this repo\'s own practice '
                 f'file(s) put in the spec\'s order, whole fields moved and '
                 f'nothing else: ' + ', '.join(tidied))
    if kind == 'source' and build.is_file():
        rc, out = run([sys.executable, str(build), '--repo', '.'], repo)
        if rc != 0:
            return rep.close(f"the view build failed:\n{tail(out, repo=repo)}")
        rep.step('views', 'regenerated (loader block, MAP.md, GLOSSARY.md)')
    elif sync.is_file():
        rc, out = run([sys.executable, str(sync), '--repo', str(repo)], repo)
        caused = removals_this_update_caused(out, dropped_sets) if rc else []
        if caused:
            # The sync refuses to remove what a source no longer declared
            # held, since it cannot tell a drop from a rename. This update
            # dropped that source itself, having checked every active rule
            # it held is in force elsewhere, so the removal is the one asked
            # for. Only when every refused practice came from a set it
            # dropped (a consumer's update, 2026-10-06).
            rc, out = run([sys.executable, str(sync), '--repo', str(repo),
                           '--allow-removals'], repo)
            rep.step('retired set', f'removed {len(caused)} practice(s) the '
                     f'dropped set(s) held, each in force elsewhere or '
                     f'retired: {", ".join(sorted(caused))}')
        in_force_nowhere_step(repo, rep, out)
        removed_links_step(rep, out)
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
        migrate_views_step(repo, rep)
        built = generated_full_views(repo)
        if built and build.is_file():
            # A consumer whose MAP.md or GLOSSARY.md says build_views.py
            # generates it gets the full build too: the sync renders the
            # loader block only, so a practice the update stopped
            # materializing stayed linked from the glossary, and the lint
            # failed on the dead links (2026-09-30, three practices).
            # --views-only: the loader block is the sync's, just written.
            rc, out = run([sys.executable, str(build), '--repo', '.',
                           '--views-only'], repo)
            if rc != 0:
                return rep.close(f"the view build failed:\n{tail(out, repo=repo)}")
            rep.step('views', 'regenerated (loader block, and '
                     + ', '.join(built) + ', which build_views.py generates here)')
        else:
            rep.step('views', 'regenerated')

    # After the views, because the view sync writes harness adapters too.
    rebased = rebaseline_vendored_entries(repo, dirty_paths(repo) - before)
    if rebased:
        rep.step('manifest baselines', 're-recorded for files this update '
                 'rewrote, to upstream or from a template: ' + ', '.join(rebased))
    scrub = ensure_scrub_blocklist_decision(repo)
    if scrub == 'null':
        rep.step('scrub blocklist', 'scrub_blocklist: null recorded in '
                 'process/manifest.json, with its reason -- precedent.json '
                 'declares this repo public, so there is nothing private to '
                 'list, and the practice audit fails a list that is neither '
                 'present nor declined')

    dead = drop_dead_blank_blocklist_link(repo)
    if dead:
        rep.step('dead link', f"dropped the retired install pack's link to "
                 f"personal/README.md#blank-blocklist from {', '.join(dead)}, "
                 f"keeping the sentence (that file exists nowhere)")

    # A missing tools/session_load_budgets.json is seeded at the close, by
    # the run that reports DONE (seed_budgets_step), not here.
    gap = approval_gap(repo)
    if gap:
        rep.step('session-load budget', gap)
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

    # 4c. Commands that name an engine file at the mirrored path the
    # catalogue copy no longer carries (repoint_moved_engine_mentions).
    # Before the staging below, so the commit the report asks for carries
    # the repoint: run after it, tools/bootstrap.sh kept calling
    # process/upstream/tools/... `|| true` in that commit, and the
    # session-start step silently did nothing (a consumer rehearsal,
    # 2026-10-03).
    moved, stranded = repoint_moved_engine_mentions(repo)
    for rel, n, path in stranded:
        rep.leave(f'{rel}:{n}', f'calls {path}, which is gone, and tools/ has '
                  f'no copy -- that step no longer runs. Remove it, or point '
                  f'it at what replaced it')
    if moved:
        rep.step('repointed', 'process/upstream/tools/ is gone and tools/ holds '
                 'the engine, so these now name tools/: '
                 + ', '.join(f'{rel} ({n} line{"s" if n != 1 else ""})'
                             for rel, n in moved))

    # Staged before the check, so it judges what the commit will hold.
    adopted = adopt_engine_output(repo, before, head.strip())
    if adopted:
        before = before - set(adopted)
        rep.step('engine, written ahead', f'{len(adopted)} uncommitted path(s) '
                 f'already held the pinned engine (a source refresh ran first); '
                 f'staged as this update\'s: ' + ', '.join(adopted))
    mirrored = adopt_catalogue_output(repo, before, head.strip())
    if mirrored:
        before = before - set(mirrored)
        rep.step('catalogue, written ahead', f'{len(mirrored)} uncommitted '
                 f'path(s) were an earlier run\'s mirror of the pinned commit, '
                 f'byte for byte; staged as this update\'s')
    record_copy_fingerprint(repo, rep)
    n = stage_update(repo, before)
    regenerated_step(repo, rep)
    rep.repo, rep.staged = repo, sorted(dirty_paths(repo) - before)
    rep.step('staged', staged_line(n, before, rep.earlier))

    # Hooks and settings: said before the commit, never found at it
    # (2026-10-06). Claude Code's auto mode holds a commit that changes
    # .claude/ as self-modification, so an update that changed a hook got
    # all the way to the commit and stopped there. It is a question for the
    # person, not a call for the repo, so the update still finishes: the
    # question is printed in every outcome, ahead of the commit.
    harness = harness_changes(repo)
    if harness:
        words = os.environ.get(HARNESS_GO_AHEAD, '').strip()
        if words:
            rep.step('hooks and settings', f'{", ".join(harness)} changed, with '
                     f'the person\'s go-ahead: "{words}"')
        else:
            rep.ask('hooks and settings',
                    harness_ask(harness, last=migrates_to_stubs(repo, harness),
                                cases=harness_cases(repo, harness),
                                gates=harness_new_gates(repo, harness)))

    # 4b. Files that still name what the refresh deleted: the full check's
    # rename-updates-links refuses each one at the Promote, so they are
    # worked here (retired_mentions).
    for where, gone in retired_mentions(repo, engine_out):
        rep.leave(where, f'still names {gone}, which this update deleted -- '
                  f'repoint or remove the mention; the full check '
                  f'(rename-updates-links) refuses it')

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

    manifest_postcondition(repo, rep)
    return closing_check(repo, rep, skip_check)


def catalogue_copy_postcondition(repo, rep, put_back=()):
    """The vendored catalogue copy is what the commit its record names gives
    under the copy rules, when the update ends -- apart from what the
    repository keeps different on purpose: a local edit this run resolved
    and kept (LOCAL EDITS says which), one left for the person, and a path
    precedent.json's kept_template_divergences names. A file that differs
    otherwise is re-mirrored from that commit when it holds text upstream
    itself shipped at that path (checkin.upstream_text), or when it is a
    deletion an earlier run made that this run's put-back restored
    (`put_back`, still holding HEAD's text); any other is a local edit
    nothing resolved, so it is left for the person, never overwritten
    (practice: repair-cannot-discard-work). DONE follows only a match.

    WHY (2026-10-08, a consuming repository). Its process/manifest.json and
    engine manifest both recorded one commit while 440 of the 604 files
    under process/upstream/ were other upstream versions and process/upstream/
    tools/ still held 99 files the copy no longer carries, and the update
    had said DONE. checkin.py record verifies the tree, but before the
    local-edit rules put the "edits" back; nothing asked again at the end.
    -> the repo-relative paths re-mirrored."""
    import checkin as ck
    import filecmp
    import shutil
    import tempfile
    ck._select_repo(repo)
    commit = (ck._manifest().get('upstream') or {}).get('commit')
    if not commit or not ck.UPSTREAM.is_dir():
        return []
    tree = ck.UPSTREAM.relative_to(repo).as_posix()
    known = {rel for outcome, rel, _t in rep.edits
             if outcome in (le.KEPT, le.STILL_LOCAL, le.MERGED)}
    known |= {what for what, _why in rep.left}
    known |= set(pve.kept_template_divergences(repo))
    put_back = set(put_back)

    def head_text(rel):
        return (subprocess.run(['git', '-C', str(repo), 'diff', '--quiet', 'HEAD',
                                '--', rel], capture_output=True).returncode == 0
                and subprocess.run(['git', '-C', str(repo), 'cat-file', '-e',
                                    f'HEAD:{rel}'], capture_output=True).returncode == 0)

    fixed, left, kept = [], [], []
    with tempfile.TemporaryDirectory() as td:
        tar = subprocess.run(['git', '-C', str(le._where(SOURCE, commit)), 'archive',
                              commit], capture_output=True)
        if tar.returncode != 0:
            rep.leave(tree, f'could not read {commit[:12]}, the commit '
                      f'process/manifest.json records, to confirm the copy is it')
            return []
        import io
        import tarfile
        with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as tf:
            try:
                tf.extractall(td, filter='data')
            except TypeError:   # a Python older than 3.11.4 has no filter
                tf.extractall(td)
        src = pathlib.Path(td)
        theirs = ck._files(src)
        ours = {p.relative_to(ck.UPSTREAM) for p in ck.UPSTREAM.rglob('*')
                if p.is_file() and '__pycache__' not in p.parts
                and p.suffix not in ('.pyc', '.pyo')}
        for p in sorted(ours | theirs):
            rel = f'{tree}/{p.as_posix()}'
            here, there = ck.UPSTREAM / p, src / p
            if p in ours and p in theirs and filecmp.cmp(here, there, shallow=False):
                continue
            if rel in known:
                kept.append(rel)
                continue
            if p in theirs and p not in ours:
                ok = not ck.deleted_here(here)
            else:
                ok = (ck.upstream_text(le._where(SOURCE, commit), here, p, commit)
                      or (rel in put_back and head_text(rel)))
            if not ok:
                left.append(rel)
                continue
            if p in theirs:
                here.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(there, here)
            else:
                here.unlink()
            fixed.append(rel)
    for d in sorted({(repo / r).parent for r in fixed}, key=lambda d: -len(d.parts)):
        while d != ck.UPSTREAM and d.is_dir() and not any(d.iterdir()):
            d.rmdir()
            d = d.parent
    for rel in left:
        rep.leave(rel, f'differs from {commit[:12]}, the commit process/manifest.json '
                  f'records for the copy, and holds text upstream never shipped '
                  f'there -- a local edit this update did not resolve, so it is '
                  f'left as it is. Send it upstream ({le.send_command(repo)}), '
                  f'record it under precedent.json\'s kept_template_divergences '
                  f'with a reason, or restore upstream\'s text, then run this again')
    if fixed:
        shown = ', '.join(fixed[:12]) + (f' and {len(fixed) - 12} more'
                                         if len(fixed) > 12 else '')
        rep.step('catalogue copy', f're-mirrored {len(fixed)} file(s) from '
                 f'{commit[:12]}, the commit its record names, that did not '
                 f'match it -- each upstream\'s own text from another commit, '
                 f'nothing of this repo\'s: {shown}')
    elif not left:
        rep.step('catalogue copy', f'matches {commit[:12]}, the commit its '
                 f'record names' + (f', apart from {len(kept)} file(s) kept on '
                                    f'purpose or left for you' if kept else ''))
    # Only a copy that matches its record gets a fingerprint recorded
    # (record_copy_fingerprint, before staging); one with a file in it left
    # for the person keeps checkin.py record's, so the check names that file.
    open_calls = {what for what, _why in rep.left}
    rep.copy_verified = not left and not any(rel in open_calls for rel in kept)
    return fixed


def record_copy_fingerprint(repo, rep):
    """Record the fingerprint of the vendored copy in process/manifest.json,
    once catalogue_copy_postcondition() found it matches its record and every
    later step that writes has run -- so the consumer's own check
    (vendored-copy-matches-record) can tell, with no BestPractice clone, that
    the copy drifted afterwards (checkin.COPY_TREE_KEY)."""
    if not getattr(rep, 'copy_verified', False):
        return
    import checkin as ck
    tid = ck.stamp_copy_tree(repo / 'process' / 'manifest.json')
    if tid:
        rep.step('catalogue fingerprint', f'recorded ({tid[:12]}), so this '
                 f'repository\'s own check can see the copy drift from now on')


def manifest_postcondition(repo, rep):
    """No manifest entry names a missing file when the update ends.

    Asked of the result, not of each step: every step that deletes a file
    used to have to remember its process/manifest.json entry, and the one
    that forgot left the update saying DONE while practice_audit.py failed
    (2026-10-01, from a consumer's Update Vendors). An entry for a file
    this update deleted, or one inside the mirrored upstream tree the
    consumer does not own, goes with its file and is said in a step line.
    Any other is the repo's own, so it is left for the person by name --
    DONE never prints over a manifest the audit would refuse."""
    dead = pve.dead_manifest_entries(repo)
    if not dead:
        return
    r = subprocess.run(['git', '-C', str(repo), 'diff', 'HEAD', '--name-only',
                        '--diff-filter=D'], capture_output=True, text=True)
    deleted = set(r.stdout.split()) if r.returncode == 0 else set()
    try:
        import precedent_resolve as pr
        mirrors = tuple(pr.mirrored_prefixes(repo) or ())
    except Exception:                                          # noqa: BLE001
        mirrors = ()
    dropped = []
    for manifest, name, rel in dead:
        if rel in deleted or (mirrors and rel.startswith(mirrors)):
            pve._drop_process_manifest_entries(repo, rel)
            dropped.append(f'{name} ({rel})')
        else:
            rep.leave(f'process/{manifest}: {name}',
                      f'names {rel}, which does not exist -- practice_audit.py '
                      f'fails on it. Restore the file, or drop the entry if '
                      f'the file is gone on purpose')
    if dropped:
        rep.step('manifest', 'dropped the entries for files this update '
                 'removed: ' + ', '.join(dropped))


def seed_budgets_step(repo, rep):
    """Seed tools/session_load_budgets.json where there is none -- only on
    the run that reports DONE, measuring the files that run produced, and
    staged as this update's.

    WHY (2026-10-08, a consuming repository). Run 1 seeded the registry at
    the sizes the tree had mid-update: AGENTS.md before the template
    sections the same run listed for copying in (taking them put it at
    8,101 against a ceiling of 8,100), and .precedent/SESSION_PRACTICES.md
    as the OLD engine had rendered it at the last session start (150
    tokens, ceiling 200); the first session start on the new engine
    rendered 341. Any run with items left for the person ends before the
    tree is final, so it seeds nothing; the run that reports DONE first
    renders the session-start file with the engine it just vendored, then
    measures. Seeding a registry that did not exist is not raising a
    budget (practice: session-load-budget): an existing registry is never
    re-measured here, so a ceiling already set only moves by the person's
    own words or an offset."""
    if (repo / 'tools' / 'session_load_budgets.json').exists():
        return
    if rep.left:
        rep.step('session-load budget', 'tools/session_load_budgets.json not '
                 'seeded yet: the run that reports DONE seeds it, measuring '
                 'what that run produces, so what you copy in from the list '
                 'below is counted')
        return
    renderer = repo / 'tools' / 'precedent_session_practices.py'
    if renderer.is_file():
        # The session-start file as the next session will have it: rendered
        # by the engine this update just vendored, not the one before it.
        run([sys.executable, str(renderer), '--repo', '.', '--quiet'], repo)
    seeded = ensure_session_load_registry(repo)
    if not seeded:
        return
    rel = 'tools/session_load_budgets.json'
    subprocess.run(['git', '-C', str(repo), 'add', '--', rel],
                   capture_output=True, text=True)
    if rel not in rep.staged:
        rep.staged = sorted(rep.staged + [rel])
    big = max(seeded.items(), key=lambda kv: kv[1] or 0)
    rep.step('session-load budget', f'{rel} seeded at the sizes this update '
             f'produced (' + ', '.join(
                 f'{k} {v:,} tokens' for k, v in seeded.items() if v) +
             f'; the sets a person brings are held to their own budget and '
             f'not counted), so the load check now binds here; {big[0]} is '
             f'the largest, and a reduction pass is how it comes down')


def full_check_after(repo):
    """precedent.json's `update_full_check` is "after": the update runs the
    basic check only, and the full one runs after the push, in the
    background, with tools/precedent_check_after.py, which files a failure
    under todo/ (tools/open_failures.py). Opt-in per repository, for one
    where someone is sure to hear of a failure (Alex, 2026-10-08, decided:
    "Yes let's do that", on running the update's full check after it
    lands)."""
    try:
        data = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and data.get('update_full_check') == 'after'


def closing_check(repo, rep, skip_check=False):
    """Step 5, and the report's close: -> the exit code."""
    seed_budgets_step(repo, rep)
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
    # DONE says which check it was. The basic tier is right for
    # pre-staging, but "check for pre-staging: passed" read as the push
    # gate's all-clear, and a consumer's full check then failed three ways
    # on the same tree (2026-10-01, from a consumer's Update Vendors).
    tier = pb.FULL
    if landing:
        try:
            tier = pb.tier_for_branch(repo, landing)[0]
        except Exception:                                      # noqa: BLE001
            tier = pb.FULL
    label = f'{tier} check for {landing}' if landing else 'deep check'
    if skip_check:
        rep.step(label, 'skipped (--skip-check) -- run it before pushing')
    elif check.is_file() and rep.left:
        # Every blocker in one run, the slow check last (practice:
        # gates-fail-fast). 2026-10-02, taking main into a large consumer:
        # run 1 spent half an hour on the full check, failed it, and only
        # run 3 stopped on a template divergence the refresh had known
        # about before run 1's check began. Whatever is left for the
        # person is cleared before the check, so the check waits for it.
        rep.step(label, f'not run: {len(rep.left)} item(s) left for you, '
                 f'listed below, come first. Clear them and run this again; '
                 f'the check runs once nothing is left')
    elif check.is_file():
        stamped = stamp_headers(repo)
        if stamped:
            rep.step('file headers', 'stamped before the check, as the commit '
                     'would: ' + ', '.join(stamped))
            try:
                rebuilt = rebuild_views_after_stamp(repo, stamped)
            except RuntimeError as e:
                return rep.close(f"the view build after the header stamp "
                                 f"failed:\n{e}")
            if rebuilt:
                rep.step('views', 'built again from the stamped source: '
                         + ', '.join(rebuilt))
        if tier == pb.FULL:
            # The basic tier first: seconds, where the full one is minutes,
            # and a finding there is reported without paying for the rest.
            quick = [sys.executable, str(check), '--tier', pb.BASIC]
            rc, out = check_with_merge_fallback(repo, rep, quick, f'{pb.BASIC} check')
            if rc != 0:
                rep.step(label, f'not run: the {pb.BASIC} check found the '
                         f'problems below first')
                return rep.close(f"the {pb.BASIC} check is red, so the {label} "
                                 f"was not started:\n{tail(out, repo=repo)}")
            if full_check_after(repo):
                rep.step(label, 'runs after the push (update_full_check: after)')
                rep.not_run = (
                    "The full check was NOT run before the push: precedent.json "
                    "says `update_full_check: after`. Commit and push the update, "
                    "then start in the background: python3 tools/precedent_check_after.py"
                    " -- a failure is filed under todo/ and pushed.")
                return rep.close()
            rep.step(f'{pb.BASIC} check', 'passed, so the full one runs')
        rc, out = check_with_merge_fallback(repo, rep, argv, label)
        if rc != 0:
            return rep.close(f"the {label} is red:\n{tail(out, repo=repo)}")
        rep.step(label, 'passed')
        # A size cap over -- this update's own regenerated block can be what
        # pushed it -- passes the basic tier and is refused at the Debut.
        cap = next((l.strip() for l in out.splitlines()
                    if l.startswith('WARNING: over a session-load size cap')), None)
        # The check's own line carries the file, its size, the limit and the
        # check that measured it (precedent_push_check._cap_warning_last);
        # a check vendored before 2026-10-08 said only "(<step>, above)",
        # and nothing of that step's output is in this report, so that
        # "above" is dropped rather than left pointing at nothing.
        if cap:
            cap = re.sub(r',\s*above\)', ')', cap[len('WARNING: '):])
            rep.warnings.append(cap + ' This update\'s own regenerated blocks '
                                'count toward it.')
        if tier != pb.FULL:
            rep.not_run = (f"Only the {tier} check ran, the one {landing} takes. "
                           f"The full check was NOT run; "
                           f"`python3 tools/precedent_push_check.py --tier full` "
                           f"shows what the Debut into staging will refuse.")
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
    ap.add_argument(TAKE_FLAG, dest='take', default=None, metavar='COMMIT',
                    help='take this commit of the followed branch although its '
                         'GitHub test has not passed -- only on the person\'s '
                         'own word, in an emergency; recorded in the report and '
                         'the commit message. Without it, main is taken at its '
                         'newest commit whose GitHub test passed')
    ap.add_argument('--move', action='store_true',
                    help='an unfinished update reruns against the commit it '
                         'started from until it reports DONE; take the '
                         'followed branch\'s newest commit instead (on main, '
                         'the newest whose GitHub test passed)')
    a = ap.parse_args(argv)
    repo = pathlib.Path(a.repo).resolve()
    if repo == SOURCE:
        print("precedent_update FAIL: --repo is this BestPractice clone itself. "
              "Run it from the consuming repo: python3 <this clone>/tools/"
              "precedent_update.py --repo . -- the clone is whichever "
              "checkout's origin is alex137/BestPractice, wherever it sits.")
        return FAILED
    if a.move and a.from_ref:
        print("precedent_update FAIL: --move and --from-ref both say which "
              "commit to take; pass one.")
        return FAILED
    if a.take and a.from_ref:
        print(f"precedent_update FAIL: {TAKE_FLAG} and --from-ref both say which "
              "commit to take; pass one.")
        return FAILED
    return update(repo, skip_check=a.skip_check, ref=a.from_ref, move=a.move,
                  take=a.take)


if __name__ == '__main__':
    sys.exit(main())

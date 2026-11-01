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
That holds only while the clone itself is current, and until 2026-10-11
nothing checked it: the fetch moves origin's refs, never the code running.
So bootstrap() runs first, before anything writes, and when the clone's
code is older than the commit this run applies, it runs that commit's copy
of this file from a temporary worktree instead, leaving the clone as it was
(precedent_update_driver.py; todo-2026-10-11-update-vendors-runs-stale-
driver-code). The report's `code:` line says which commit's code ran.

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
     and each install-once file (the PR template, TODO.md, MAP.md ...)
     still exactly as an install wrote it brought onto the current
     template; in one the repository edited, each line that is still,
     verbatim, wording its template has since dropped, left for you --
     reported, never rewritten
     then, where precedent.json names no landing_branch, staging
  3c. the migrations: each tools/migration_*.py moves the repository off
     an arrangement the engine has dropped
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
  4a. a missing staging made on origin, from main
  5. the repo's own check at its landing branch's tier -- into staging,
     the quick checks on what changed; the full check waits for Debut or Produce
     (--skip-check to leave it out) -- run against a temporary commit of
     the staged update, undone right after, so it judges the tree the way
     the push will

THE REPORT, and the exit code a session acts on:
  0  DONE -- nothing is left. Commit on a branch of its own (DONE prints
     the command when the checkout sits on a tier branch), then land it on
     your landing branch -- or, when it changes a CI workflow, open a pull
     request into it, which DONE says.
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
missing branch tier (staging), made at a commit origin
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

HERE = pathlib.Path(__file__).resolve()
SOURCE = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import precedent_vendor_engine as pve  # noqa: E402
import precedent_branches as pb  # noqa: E402
import precedent_local_edits as le  # noqa: E402

# Everything the steps' commands printed, for the upstream review at DONE
# (the ladder set's upstream-review practice): a warning a step met and
# passed over is read from here, not from the session's scrollback.
OUTPUTS = []
from precedent_clone_lock import held  # noqa: E402
import precedent_update_driver as drv  # noqa: E402

# The clone to NAME in anything a person reads. The same as SOURCE, except
# in a run started from a driver worktree, which is deleted when the run
# ends (precedent_update_driver.display_root): git reads use SOURCE, words
# use CLONE.
CLONE = drv.display_root(SOURCE)

DONE, LEFT, FAILED = 0, 1, 2


def rebaseline_vendored_entries(repo, rewritten=(), hold=()):
    """-> [local_path] whose recorded local_sha256 was re-recorded.

    A `synced` manifest entry whose local file sits INSIDE the vendored
    tree is not this repo's copy of anything: the catalogue mirror rewrites
    it wholesale, and refuses to run over a local edit. So after the mirror
    its old hash is stale by construction, and practice_audit read that as
    DRIFT -- "changed since baseline" -- on a file upstream changed, not
    this repo (2026-09-28, a consumer's doc-lint entry at
    process/upstream/tools/doc_lint.py). The quick check does not run the
    audit, so the update said done and the Promote would have gone red.

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
    then such a file kept the classic install's baseline, the quick check
    never ran the audit, and the first Debut refused it as DRIFT.

    `hold` (2026-10-16): paths never re-recorded on this run, whatever else
    holds -- a .claude/ change still waiting on the person's words
    (held_harness_paths). Re-recorded while held, a session that set the
    change aside as the question asks left the manifest naming content the
    file no longer had, and the practice audit failed it as DRIFT."""
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
        if not rel or not f.is_file() or rel in hold:
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


def this_updates_output(repo, before, earlier):
    """-> the paths this update wrote: changed by this run, plus what an
    earlier run of it staged and nobody has touched since (`earlier`, from
    earlier_runs_output).

    WHY THE SECOND HALF (2026-10-10, two consumers). A run that stopped LEFT
    FOR YOU had rewritten .claude/settings.json from its template and staged
    it. Its rerun found the file already uncommitted, so not among what IT
    changed, and left the manifest's old hash in place; the practice audit
    then failed the file as DRIFT until it was re-recorded by hand. A file
    the person changed between the runs has an unstaged change on top, is
    not in `earlier`, and still fails the audit as theirs."""
    return (dirty_paths(repo) - set(before)) | set(earlier or ())


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
    at every push of a consumer, refuses it with the remedy in
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

    The check is full-tier only, so an update's quick check passed and
    the full check went red on a key nothing had ever written
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



def seed_baseline_approvals(repo, data, path, approved_by=None):
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
            'approved_by': f'baseline {day}: ' + (approved_by or
                           'seeded by Update Vendors with the registry, at the '
                           'values in force')}
        for k, v in sorted(now.items()) if isinstance(v, int)}
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return True


def record_copy_in_budget(repo, today=None):
    """-> a sentence for the report when a budget in force is above its
    approval only by what the sets copied in here bring, after recording the
    new number as approved on the person's own copy-in answer; else None.
    Morgan, 2026-10-28 (strength: decided): "Go, fix it at the engine root
    issue" -- approved_budgets is the repository's own, so each repository
    that copied a set in failed in turn and asked again for words the
    copy-in had already given.

    Two budgets move with a copy-in. The occasion cap gains each copied
    set's declared occasion_share_tokens. The ceiling of
    .precedent/SESSION_PRACTICES.md gains what the copied sets now add to
    the repository's charge for that file, measured as the file rendered
    with and without them (precedent_session_practices.copied_share): a set
    the person brought was charged to their own budget, and copied in it is
    the repository's. A rise beyond what the copies bring is not explained
    by the copy-in and still waits for the person's words: nothing is
    recorded for it. Only sets precedent.json's copy_in says yes to count,
    with the words that yes was given in."""
    path = repo / 'tools' / 'session_load_budgets.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    approved = data.get('approved_budgets') if isinstance(data, dict) else None
    if not isinstance(approved, dict) or not isinstance(cfg, dict):
        return None
    # Under a session-load total a copy-in moves tokens between parts that
    # carry no budget, so there is nothing to record (record_person_total).
    if isinstance(data.get('session_load_tokens'), int):
        return None
    answers = cfg.get('copy_in') if isinstance(cfg.get('copy_in'), dict) else {}
    shares, words, unanswered = {}, [], []
    for e in cfg.get('sources') or []:
        if not (isinstance(e, dict) and e.get('vendored') is True and e.get('path')):
            continue
        ans = answers.get(e.get('name'))
        if not (isinstance(ans, dict) and ans.get('answer') == 'yes'
                and ans.get('answered_by')):
            unanswered.append(e.get('name'))
            continue
        if ans['answered_by'] not in words:
            words.append(ans['answered_by'])
        try:
            v = json.loads((repo / str(e['path']) / 'precedent-source.json')
                           .read_text(encoding='utf-8')).get('occasion_share_tokens')
        except (OSError, ValueError, AttributeError):
            v = None
        shares[e['name']] = v if isinstance(v, int) else 0
    if not words:
        return None
    import time as _time
    day = today or _time.strftime('%Y-%m-%d')
    copies = ', '.join(sorted(shares))
    said = []

    def approve(key, was, now, why):
        approved[key] = {
            'max': now, 'strength': 'decided',
            'approved_by': ' / '.join(words) + (
                f' -- the copy-in of {copies}; recorded by Update Vendors on '
                f'{day}, raising {was:,} to {now:,}, {why}'),
            'previous_max': was, 'copy_in': sorted(shares)}

    try:
        import build_views as _bv
        now = _bv.effective_budgets(repo, registry=path).get('occasion_index')
    except Exception:                                        # noqa: BLE001
        now = None
    entry = approved.get('occasion_index')
    if (isinstance(now, int) and isinstance(entry, dict)
            and isinstance(entry.get('max'), int) and now > entry['max']
            and now - entry['max'] <= sum(shares.values())):
        was = entry['max']
        named = ', '.join(f'{n} {v:,}' for n, v in sorted(shares.items()))
        approve('occasion_index', was, now,
                f'within the occasion shares those copies bring ({named})')
        said.append(f'occasion_index approved at {now:,} (was {was:,}), within '
                    f'the occasion shares of the sets copied in ({named})')

    # The session file's ceiling, only when every copied set was answered
    # yes: the share is measured for all of them at once.
    surface = '.precedent/SESSION_PRACTICES.md'
    row = (data.get('surfaces') or {}).get(surface)
    if not unanswered and isinstance(row, dict) and isinstance(row.get('ceiling'), int):
        try:
            import contextlib, io
            import precedent_session_practices as _psp
            with contextlib.redirect_stderr(io.StringIO()):
                n = _bv._approx_tokens(_psp.render(*_psp.collect(str(repo)),
                                                   repo=str(repo)))
                charged = _psp.charged_to_repo(str(repo), n)[0]
                share = _psp.copied_share(str(repo))
        except Exception:                                    # noqa: BLE001
            charged, share = None, 0
        ceiling = row['ceiling']
        if isinstance(charged, int) and share and ceiling < charged <= ceiling + share:
            new = ceiling + share
            row['ceiling'] = new
            approve(f'surfaces/{surface}', ceiling, new,
                    f'by the ~{share:,} tokens those copies add to this '
                    f'repository\'s charge for the file (measured with and '
                    f'without them)')
            said.append(f'{surface} ceiling raised to {new:,} (was {ceiling:,}; '
                        f'~{charged:,} in force), by the ~{share:,} the copied '
                        f'sets add to it')
    if not said:
        return None
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return ('; '.join(said) + ': it stands on the person\'s copy-in answer, '
            'recorded with it')


def record_person_total(repo, today=None, occasion='Update Vendors'):
    """-> a sentence for the report when it wrote the person's session-load
    total into this repository's registry, else None.

    code-cites-practice: session-load-budget

    The person declares one total for every repository they work in --
    `session_load_tokens` in their individual set's precedent-source.json,
    with their words for it in `session_load_approval` -- and it binds here
    only once it is in THIS repository's tools/session_load_budgets.json:
    the daily and post-merge checks run without the individual set, so a
    total that lived only there would leave every per-part budget refusing
    in CI (spec/SESSION_LOAD_ONE_TOTAL_PLAN.md, from its review). Morgan,
    2026-10-28 (strength: decided): "Go, one number everywhere".

    The approval is copied with the number, so budget-within-approval reads
    the person's own words here; a total with no valid approval beside it is
    not copied. A registry that does not exist yet is left to
    seed_budgets_step, and the next run records the total."""
    path = repo / 'tools' / 'session_load_budgets.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        import precedent_session_practices as _psp
        total, ind_path = _psp.brought_budget(str(repo), 'session_load_tokens')
    except Exception:                                        # noqa: BLE001
        return None
    if not isinstance(total, int) or isinstance(total, bool) or not ind_path:
        return None
    try:
        man = json.loads((pathlib.Path(ind_path) / 'precedent-source.json')
                         .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    appr = man.get('session_load_approval') if isinstance(man, dict) else None
    if not (isinstance(appr, dict) and appr.get('strength') in ('decided', 'assented')
            and str(appr.get('approved_by') or '').strip()):
        return None
    approved = data.get('approved_budgets')
    if not isinstance(approved, dict):
        approved = data['approved_budgets'] = {}
    was = data.get('session_load_tokens')
    entry = approved.get('session_load_tokens')
    if was == total and isinstance(entry, dict) and entry.get('max') == total:
        return None
    import time as _time
    day = today or _time.strftime('%Y-%m-%d')
    data['session_load_tokens'] = total
    approved['session_load_tokens'] = {
        'max': total, 'strength': appr['strength'],
        'approved_by': (f"{appr['approved_by']} -- the person's one total, "
                        f"copied from their individual set by {occasion} "
                        f"on {day}")}
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    said = (f'session_load_tokens set to {total:,} from the person\'s individual '
            f'set' + (f' (was {was:,})' if isinstance(was, int) else '')
            + ': the one session-load total that refuses here; the parts are '
            'measured and reported')
    # 2026-10-29: two repositories already loading more than the person's
    # total were told only "set to 10,000", and every session check after
    # it was red. Say so here, with the next step.
    try:
        import session_load_trend as _slt
        _sizes, loads = _slt.total_tokens(repo)
    except Exception:                                        # noqa: BLE001
        loads = None
    if isinstance(loads, int) and loads > total:
        said += (f'. This repository already loads ~{loads:,}, over it, so '
                 f'every session check here is red until a "Reduction pass" '
                 f'brings it under (practice: reduction-pass)')
    return said


def approval_gap(repo):
    """-> a sentence for the report when the registry exists and has no
    approved_budgets (so budget-within-approval skips every run), else None.
    Where no budget went up since the registry was first committed, it
    records them as the baseline itself and the sentence says so; it asks
    the person only about a budget that did go up."""
    path = repo / 'tools' / 'session_load_budgets.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or isinstance(data.get('approved_budgets'), dict):
        return None
    first, raised = _raised_since_first_commit(repo, path)
    if first and not raised:
        # Nothing went up since the registry was first committed, so there is
        # no raise to launder: record the numbers in force and say so, rather
        # than asking the person to confirm numbers nobody changed (Morgan,
        # 2026-10-10: "How do we AVOID this becoming a constant hassle that
        # the user has to think about all the time?").
        if seed_baseline_approvals(repo, data, path, approved_by=(
                f'no budget went up since this registry was first committed '
                f'({first[:12]}); recorded by Update Vendors at the values in '
                f'force')):
            return ('recorded the budgets in force as the baseline in '
                          'tools/session_load_budgets.json: none went up since '
                          f'the registry was first committed ({first[:12]})')
    which = (f' Raised since its first commit ({first[:12]}): '
             f'{", ".join(raised)} -- ask only about those.' if first and raised
             else '')
    return ('tools/session_load_budgets.json has no approved_budgets, so the '
            'check that no budget was raised without approval skips on every '
            'run. Ask the person to confirm the numbers in force are ones '
            'they chose, then record each as "strength": "baseline" '
            f'(practice: session-load-budget).{which}')


def _raised_since_first_commit(repo, path):
    """-> (sha of the commit that added the registry, [budget keys whose
    number in force is higher now than in that commit]), or (None, None)
    when there is no history to read. Each side is read through
    build_views.effective_budgets, the function that enforces it; a budget
    the first commit did not have counts as raised."""
    import subprocess as _sp
    import tempfile as _tf
    rel = path.relative_to(repo).as_posix()
    log = _sp.run(['git', '-C', str(repo), 'log', '--diff-filter=A',
                   '--format=%H', '--', rel], capture_output=True, text=True)
    shas = log.stdout.split() if log.returncode == 0 else []
    if not shas:
        return None, None
    first = shas[-1]
    old = _sp.run(['git', '-C', str(repo), 'show', f'{first}:{rel}'],
                  capture_output=True, text=True)
    if old.returncode != 0:
        return None, None
    try:
        import build_views as _bv
        with _tf.TemporaryDirectory() as td:
            then_path = pathlib.Path(td) / 'session_load_budgets.json'
            then_path.write_text(old.stdout, encoding='utf-8')
            then = _bv.effective_budgets(repo, registry=then_path)
        now = _bv.effective_budgets(repo, registry=path)
    except Exception:                                        # noqa: BLE001
        return None, None
    raised = sorted(k for k, v in now.items() if isinstance(v, int)
                    and not (isinstance(then.get(k), int) and v <= then[k]))
    return first, raised


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
    # Writes the baseline approvals too (seed_baseline_approvals), as it
    # does for a newly bootstrapped set: one writer for a new registry.
    _pbs._write_session_load_budget(repo, occasion='Update Vendors')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
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


_HOOK_NOT_HERE = re.compile(
    r'precedent_sync_views: (\S+): its (\S+) hook runs (\S+), which is not '
    r'in this repository yet')


def hooks_not_here_step(rep, out):
    """Say each hook a practice in force declares whose script this
    repository does not have yet (precedent_sync_views notes it).

    WHY (2026-10-17, the session moving enforcement into the sets). The
    engine dropped a refusal that a practice set now ships as its own hook;
    a repository that took the engine half without that set's files lost the
    old refusal before it had the new one, and nothing said so."""
    for slug, event, run in _HOOK_NOT_HERE.findall(out or ''):
        rep.step('a check not here yet',
                 f'WARNING: {slug} declares a {event} hook running {run}, which '
                 f'this repository does not have yet, so that check is off here. '
                 f'Take its source\'s sync in this same update (the sets layer), '
                 f'or the engine half lands without the check that replaced it')


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
    # A check script or test the sync took out, named by path or by name
    # (precedent_sync_views._mentions_of_removed_files). Until 2026-10-15
    # these were printed and nothing more: a consumer's update deleted a
    # retired check, said DONE, and the light check and rename-updates-links
    # then refused the landing for a precedent.json key, a repo-local stub
    # and a closed open item that still named it.
    for where, path in re.findall(r'precedent_sync_views: (\S+:\d+) still names '
                                  r'(\S+), which this sync removed', out):
        rep.leave(where, f'still names {path}, which this update removed. '
                         f'Repoint it or remove it; the full check '
                         f'(rename-updates-links) refuses it')


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
    # NOTHING SAID WHERE NOTHING CAN BE DONE (2026-10-12, a consuming
    # repository's Update Vendors): a set this session has no GitHub API
    # access to, or one the environment's proxy will not ask about, was a
    # line on every run, and no one can act on it. Whether a set is archived
    # is a bonus -- a set that marks itself retired is dropped all the same
    # -- so those two are left unsaid here; `precedent_vendor_engine.py
    # drop-retired`, which is asked, still says them. Any other failure is
    # still reported: it may be one worth looking at.
    quiet = tuple(m for m in (getattr(pve, 'PROXY_NOTE', None),
                              getattr(pve, 'NO_ACCESS_NOTE', None)) if m)
    notes = [n for n in notes if not any(m in n for m in quiet)]
    if notes:
        rep.step('retired set', f'{len(notes)} declared set(s) could not be '
                 f'asked on GitHub whether they are archived, so they stay '
                 f'declared; a set that marks itself retired is still found '
                 f'(first: {notes[0]})')
    if names:
        record_dropped_sets(repo, names)
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
# "sources" alone is a common word -- "two sources reveal them" was about
# kinds of review evidence (a consumer's update, 2026-10-10) -- so a count of
# sources is a count of practice sets only beside a word that says so.
_SET_CONTEXT_RE = re.compile(
    r'practice|precedent|shared|declar|resolv|loader|catalogue|\bsets?\b', re.I)
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
        if m and m.group(0).lower().endswith('sources') and \
                not _SET_CONTEXT_RE.search(line):
            m = None
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


def sets_this_update_dropped(repo, dropped):
    """-> every set this update may count as dropped when the view sync
    refuses to remove what one held: `dropped` (this run's
    retired_sources_step), the sets an earlier run of this same update
    dropped (record_dropped_sets), and every set on a deleted-set record
    (precedent_resolve.deleted_sets) -- less any precedent.json still
    declares.

    WHY (2026-10-10, a consumer's Update Vendors). The first run dropped two
    deleted sets from precedent.json and stopped LEFT FOR YOU; the rerun
    found nothing left to drop, while the committed MANIFEST.json still
    recorded their practices, so the sync refused every rerun."""
    out = set(dropped or ())
    out |= set(_read_record(repo).get('dropped_sets') or ())
    try:
        out |= set(pve._person_sets()[0])
    except Exception:                                          # noqa: BLE001
        pass
    try:
        cfg = json.loads((pathlib.Path(repo) / 'precedent.json')
                         .read_text(encoding='utf-8'))
        declared = {str(x.get('name') or '') for x in cfg.get('sources') or []
                    if isinstance(x, dict)}
    except (OSError, ValueError, AttributeError):
        declared = set()
    return sorted(out - declared)


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


_STILL_DECLARED_REFUSAL = re.compile(
    r"whose source is still declared -- (.*?)\. Two causes", re.S)


def decommissioned_removals(out, rev):
    """-> the practices the view sync refused to remove whose source is
    still declared, when every one is a universal practice the source
    recorded as decommissioned (process/decommissioned_paths.json) at `rev`,
    the commit this update takes; [] otherwise.

    WHY (2026-10-11). BestPractice deleted a temporary rule whose time was
    up and recorded the deletion there, as decommission-deletes-files says.
    Every consumer's next update then FAILED on it: the sync refuses to drop
    a practice its committed MANIFEST.json records unless the source marks
    it retired, and the remedy it names, --allow-removals, is a person's
    call made repo by repo. The record already says the deletion was meant,
    so the update reads it and names those practices, and only those, to
    the sync (--allow-removal SLUG). Found by Update All Vendors' first run."""
    m = _STILL_DECLARED_REFUSAL.search(out or '')
    if not m or not rev:
        return []
    pairs = re.findall(r'(\S+) \(from ([^)]+)\)', m.group(1))
    if not pairs or any(src != 'precedent' for _s, src in pairs):
        return []
    r = subprocess.run(['git', '-C', str(SOURCE), 'show',
                        f'{rev}:process/decommissioned_paths.json'],
                       capture_output=True, text=True)
    try:
        gone = {e.get('path') for e in
                json.loads(r.stdout).get('decommissioned') or []
                if isinstance(e, dict)} if r.returncode == 0 else set()
    except ValueError:
        gone = set()
    slugs = [s for s, _src in pairs]
    return slugs if all(f'practices/{s}.md' in gone for s in slugs) else []


def vendored_accepts(tool, option):
    """Does the vendored `tool` take `option`? Read from its own text: an
    update can take a commit older than the clone it runs from, and the
    tools it vendors then come from that commit, so an option this file
    knows can be one the repo's copy has never heard of."""
    try:
        text = pathlib.Path(tool).read_text(encoding='utf-8')
    except OSError:
        return False
    return re.search(r"(['\"])" + re.escape(option) + r"\1", text) is not None


def _manifest_pairs(text):
    """-> {(slug, source)} a practice MANIFEST.json's text records, or None."""
    try:
        recs = json.loads(text).get('practices') or []
    except (ValueError, AttributeError):
        return None
    return {(e.get('slug'), e.get('source')) for e in recs
            if isinstance(e, dict) and e.get('slug')}


def removed_beyond(repo, gone, dropped):
    """After a view sync run with --allow-removals: -> the (slug, source)
    pairs it removed that the flag may have waved through besides `gone`,
    or None when that cannot be read.

    Committed MANIFEST.json against the one the sync just wrote. A removed
    practice whose source still records practices was not one of the
    refusals --allow-removals waives: every refusal about a source still
    declared was listed in full, and decommissioned_removals took the run
    only when all were in `gone`. One whose source records nothing any more
    may be a source DROPPED or RENAMED, which that run never showed (the
    sync stops on the first refusal); it passes only from a set this update
    dropped itself, as removals_this_update_caused does."""
    r = subprocess.run(['git', '-C', str(repo), 'show', 'HEAD:MANIFEST.json'],
                       capture_output=True, text=True)
    before = _manifest_pairs(r.stdout) if r.returncode == 0 else None
    try:
        after = _manifest_pairs((repo / 'MANIFEST.json').read_text(encoding='utf-8'))
    except OSError:
        after = None
    if before is None or after is None:
        return None
    kept = {s for s, _src in after}
    sources = {src for _s, src in after}
    return sorted((s, src) for s, src in before
                  if s not in kept and s not in set(gone)
                  and src not in sources and src not in set(dropped))


def take_decommissioned(repo, sync, gone, dropped, rep):
    """Run the view sync again, letting through only the practices in
    `gone`, which the source decommissioned on purpose. -> (rc, out).

    WHY THE FALLBACK (2026-10-11, two consuming repositories). An update
    pinned to 33f77a7, older than the clone it ran from, vendored that
    commit's sync, and the run then passed it --allow-removal, which that
    sync rejected as an unknown option. A sync too old for --allow-removal
    gets --allow-removals instead, and then what it removed is checked
    against `gone` (removed_beyond); anything else is reported, never
    silently taken."""
    named = vendored_accepts(sync, '--allow-removal')
    rc, out = run([sys.executable, str(sync), '--repo', str(repo)]
                  + ([a for s in gone for a in ('--allow-removal', s)] if named
                     else ['--allow-removals']), repo)
    if rc != 0:
        rep.step('decommissioned', f'the view sync failed when told to remove '
                 f'{", ".join(gone)}, which the source deleted on purpose')
        return rc, out
    beyond = [] if named else removed_beyond(repo, gone, dropped)
    if beyond is None or beyond:
        what = ('it could not be checked: MANIFEST.json could not be read '
                'before or after' if beyond is None else
                'it also removed ' + '; '.join(f'{s} (from {src})'
                                              for s, src in beyond))
        rep.step('decommissioned', 'refused: this repo\'s view sync is too old '
                 'for --allow-removal, so it ran with --allow-removals, and '
                 + what)
        return 1, (out + f"\nprecedent_update: the view sync was told to remove "
                   f"only {', '.join(gone)}, and {what}. Nothing is committed: "
                   f"restore anything wrongly removed from HEAD (git checkout "
                   f"HEAD -- MANIFEST.json and each practice's file), then "
                   f"decide those removals yourself.")
    rep.step('decommissioned', f'removed {len(gone)} practice(s) the source '
             f'deleted on purpose and recorded in process/decommissioned_'
             f'paths.json: {", ".join(gone)}'
             + ('' if named else ' (this repo\'s view sync predates '
                '--allow-removal, so it ran with --allow-removals, and removed '
                'nothing else)'))
    return rc, out


def approved_workflows_step(repo, rep):
    """Say which steps of the repo's own approved workflows the push check
    runs here, and name each one only GitHub runs (2026-10-10: a consumer's
    platform-docs-check.yml failed only as GitHub's test on the pull request
    into main, after every local tier passed). Said once per update, never
    on every push."""
    try:
        import precedent_push_check as ppc
        checks, unrun = ppc.approved_workflow_checks(repo)
    except Exception:                                          # noqa: BLE001
        return
    if checks:
        rep.step('approved workflows', f'{len(checks)} step(s) of this repo\'s '
                 f'own approved workflows run in the push check\'s full tier '
                 f'(the Debut and around Produce, never before a push): '
                 + ', '.join(n.split(': ', 1)[-1] for n, _a, _r in checks))
    if unrun:
        # One line, said once (2026-10-10: one line per step, each printed
        # again in the summary, read as a wall). The steps are the
        # check-like ones of workflows GitHub runs on a change; the product
        # itself is never here (approved_workflow_checks).
        files = sorted({pathlib.Path(wf).name for wf, _s, _c in unrun})
        rep.step('approved workflows', f'{len(unrun)} check step(s) in '
                 f'{", ".join(files)} run only on GitHub, so a failure there is '
                 f'first seen after the merge. To run one here too, make it a '
                 f'plain `python3 tools/<x>.py` call; a workflow that is the '
                 f'product, not a test, takes `"role": "{ppc.DELIVERABLE_ROLE}"` '
                 f'in its precedent.json github_ci_approved entry')


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
    named = pve.name_the_persons_maintainer(repo)
    if named:
        rep.step('code owners', f'wrote your declared name to @{named}\'s entry '
                 f'in precedent.json\'s maintainers, so an approval that names '
                 f'you ("Name, YYYY-MM-DD: ...") is read as yours')
    # A single owner's own zone, for the records nobody's identity reaches
    # (2026-10-08): written, since the owner's identity already declares it
    # (Morgan, 2026-10-28; pve.apply_owner_timezone).
    try:
        tz = pve.apply_owner_timezone(repo)
    except Exception:                                          # noqa: BLE001
        tz = None
    if tz:
        rep.step('time zone', f'wrote "fallback_timezone": "{tz[1]}" to '
                 f'precedent.json -- @{tz[0]}\'s declared zone, for what runs '
                 f'where no identity reaches (a GitHub Actions job); change it '
                 f'there any time')


def copy_in_step(repo, rep, answers=None, answered_by=''):
    """Part 6 of spec/VENDORED_SHARED_SETS.md: whether to copy each set the
    person brings (or offers) into this repository is asked once, here and
    at install, and the answer is recorded in precedent.json. Answers given
    on this run (--copy-in NAME=yes|no, --answered-by) are recorded first;
    every set still unanswered becomes one question for the person. A
    recorded answer is never asked again."""
    answers = answers or {}
    try:
        for what in pve.fetch_offered_clones(
                repo, [n for n, a in answers.items() if a == 'yes']):
            rep.step('copy in', what)
    except Exception as exc:                                  # noqa: BLE001
        rep.step('copy in', f'an offered set could not be cloned ({exc})')
    try:
        for _ok, what in pve.copy_in_pending(repo):
            rep.step('copy in', what)
    except Exception as exc:                                  # noqa: BLE001
        rep.step('copy in', f'a waiting yes could not be checked ({exc})')
    try:
        offers = {o['name']: o for o in pve.copy_in_offers(repo)}
    except Exception as exc:                                  # noqa: BLE001
        rep.step('copy in', f'not asked: the offers could not be read ({exc})')
        return
    for name, answer in answers.items():
        offer = offers.pop(name, None)
        if offer is None:
            rep.step('copy in', f'{name}: no answer recorded -- it is not a set '
                     f'you bring or offer, or it was answered here already')
            continue
        if answer == 'yes' and pve.copy_in_unchecked(offer):
            rep.ask('copy in', f'{name}: the yes was not recorded. '
                    f'{pve.copy_in_question(offer)}')
            continue
        waits = pve.copy_in_waits_on(offer.get('clone'),
                                     offer.get('set_root', '')) \
            if answer == 'yes' else ''
        ok, what = pve.record_copy_in(repo, name, answer, answered_by,
                                      repo_url=offer['repo_url'],
                                      ladder=offer['ladder'],
                                      set_root=offer.get('set_root', ''),
                                      waits_on=waits)
        if ok:
            rep.step('copy in', what)
        else:
            rep.ask('copy in', f'{what}. {pve.copy_in_question(offer)}')
    for offer in offers.values():
        rep.ask('copy in', pve.copy_in_question(offer))


def refresh_copies_step(repo, rep, take_sets=()):
    """Refresh every shared set this repository copies in, from the
    person's own clone of it, with checkin.py --source: the same mirror and
    record the universal catalogue gets. Every copied-in set is refreshed
    on every run, a voice pack included, and the report says how far it
    moved (Morgan, 2026-10-20, strength: decided: "Voice packs (and [the
    writing rules they carry]) should be marked to refresh upon a normal
    vendor update").
    Whether to freeze a copy is the repository's call, not the set's: a
    source entry in precedent.json carrying "hold": "<why>" is only reported
    when its origin moves, and taken this once when the run names it in
    --take-set. The set-side "copy_refresh": "on-go-ahead" it replaces is
    ignored, and named so its owner can delete it.
    A copy taken for its exports alone (`"exports_only": true`) is refreshed
    the same way, and so is every file a set exports (Morgan, 2026-10-30,
    strength: decided: Update Vendors "gets the new version of everything
    that's vendored in"). A copy that moved has its changed files listed:
    "Update Vendors" is the go-ahead for a change to a voice, so the report
    is where it is heard.
    A copy that could not be refreshed -- no clone on this machine, or the
    copy failed -- is left for the person, never DONE: an update that cannot
    say a declared copy is current has not finished (2026-10-29, a
    consumer's copy of a voice repository's prompts sat behind while Update
    Vendors said DONE)."""
    try:
        import precedent_resolve as pr
        cfg = json.loads((repo / 'precedent.json').read_text(encoding='utf-8'))
    except Exception:                                         # noqa: BLE001
        return
    entries = [e for e in (cfg.get('sources') or []) if pr.is_vendored(e)]
    if not entries:
        return
    ind = pr.person_individual_path()
    brought = {b['name']: pathlib.Path(b['path'])
               for b in (pr.brought_sources(ind, warn=False) if ind else [])}
    checkin = [sys.executable, str(SOURCE / 'tools' / 'checkin.py')]
    for e in entries:
        name = e.get('name')
        clone = brought.get(name)
        if clone is None or not (clone / '.git').exists():
            # Beside the individual set first, then wherever sessions clone
            # to; by folder name in any case, or by origin (clone_elsewhere).
            clone = pr.clone_elsewhere(
                name, str(repo / str(e['path'])), any_clone=True,
                repo=e.get('repo'),
                near=[ind.resolve().parent] if ind else ())
        held = str(e.get('hold') or '').strip()
        if clone is None or not (pathlib.Path(clone) / '.git').exists():
            if held:
                rep.step(f'copy of {name}', f'held by this repository ({held}); '
                         f'no clone of it on this machine to compare with')
            else:
                rep.leave(f'copy of {name}', 'not refreshed: no clone of it on '
                          'this machine, so nothing here can say the copy is '
                          'current. Attach it (read access) and run Update '
                          'Vendors again')
            continue
        clone = pathlib.Path(clone)
        # A set in a folder of its repository keeps its manifest there.
        set_dir = clone / str(e.get('set_root') or '').strip('/') \
            if e.get('set_root') else clone
        try:
            man = json.loads((set_dir / pr.SOURCE_MANIFEST).read_text(
                encoding='utf-8'))
        except (OSError, ValueError):
            man = {}
        mpath = repo / 'process' / f'manifest_{name}.json'
        try:
            up = json.loads(mpath.read_text(encoding='utf-8')).get('upstream') or {}
        except (OSError, ValueError, AttributeError):
            up = {}
        # A copy whose files are not there is made again, whatever its
        # record says: a failed update's rerun can leave the record and
        # clear the tree, and a go-ahead set was then never re-copied
        # (2026-10-19, a voice pack left empty in a consumer). A backstop:
        # the cause, the put-back taking the copy for engine output, is
        # fixed in vendored_layer_paths(); this still covers a copy lost
        # any other way.
        here = repo / str(e['path'])
        first = not up.get('commit') or not (
            (here / pr.SOURCE_MANIFEST).is_file()
            # A copy of a source with no precedent-source.json is there
            # when any of its files is.
            or (pr.is_exports_only(e) and here.is_dir() and any(here.iterdir())))
        if man.get('copy_refresh'):
            rep.step(f'copy of {name}', f'its precedent-source.json still says '
                     f'"copy_refresh": {json.dumps(man["copy_refresh"])}, which '
                     f'is retired (2026-10-20): every copy is refreshed, and a '
                     f'repository that wants one frozen says "hold" in its own '
                     f'precedent.json. Delete the line in {name}')
        hold = held
        if hold and not first and name not in take_sets:
            # The copy is taken from the set's main, so "has it moved" asks
            # main too, never the branch this clone happens to be on.
            head = ''
            for ref in ('origin/main', 'main', 'HEAD'):
                rc, head = run(['git', '-C', str(clone), 'rev-parse', '--verify',
                                '--quiet', ref], repo)
                if rc == 0 and head.strip():
                    break
            if rc == 0 and head.strip() and not head.strip().startswith(
                    str(up.get('commit'))[:12]):
                rep.step(f'copy of {name}', f'held by this repository ({hold}), '
                         f'so not refreshed, though {name} has moved since it '
                         f'was copied in ({str(up.get("commit"))[:12]} -> '
                         f'{head.strip()[:12]}). Take it this once with '
                         f'--take-set {name}, or delete the hold')
            else:
                rep.step(f'copy of {name}', f'current; held by this repository '
                         f'({hold})')
            continue
        was = _copy_digest(here)
        # A source declared in precedent.json by hand, not by the copy-in
        # question, has no record yet; start it the way that answer does.
        if not mpath.exists():
            mpath.parent.mkdir(parents=True, exist_ok=True)
            mpath.write_text(json.dumps({'upstream': {}}, indent=2) + '\n',
                             encoding='utf-8')
        rc, out = run(checkin + ['--source', name, 'update', str(clone),
                                 '--repo', str(repo)]
                      + (['--force'] if first else []), repo)
        if rc != 0:
            rep.leave(f'copy of {name}', 'not refreshed: ' + tail(out, repo=repo))
            continue
        rc, out = run(checkin + ['--source', name, 'record', str(clone),
                                 '--repo', str(repo), '--note', 'Update Vendors'],
                      repo)
        # A copy made before copy-in wrote the scrub opt-out gets it here.
        if pve.copy_skips_scrub(repo, name):
            rep.step(f'copy of {name}', 'its manifest now opts out of the '
                     'outbound scrub: a copy is never sent up from here')
        rep.step(f'copy of {name}', next(
            (l for l in out.splitlines() if l.startswith('checkin record')),
            'recorded') if rc == 0 else 'not recorded: ' + tail(out, repo=repo))
        # Refreshed without asking, so the report says it moved: a voice
        # copy that changes is heard about, never found later in the prose.
        try:
            now = json.loads(mpath.read_text(encoding='utf-8')).get(
                'upstream', {}).get('commit')
        except (OSError, ValueError, AttributeError):
            now = None
        if rc == 0 and now and up.get('commit') and now != up.get('commit'):
            rep.step(f'copy of {name}', f'moved {str(up["commit"])[:12]} -> '
                     f'{str(now)[:12]}')
        changed = _copy_changes(was, _copy_digest(here))
        if changed:
            shown = changed[:20]
            rep.step(f'copy of {name}', 'changed: ' + ', '.join(shown) + (
                f' and {len(changed) - len(shown)} more' if changed[20:] else ''))
        refresh_installed_templates(repo, rep, e, clone, set_dir, man,
                                    up.get('commit'))


# WHAT A SOURCE SHIPS TO BE INSTALLED IS REFRESHED TOO (Morgan, 2026-10-30,
# strength: decided: Update Vendors refreshes everything a repository took
# from another). A source names each template a consumer installs outside
# its copy -- a workflow its prompts' check runs in -- in precedent-source.json,
# `"installs": [{"from": "templates/x.yml", "to": ".github/workflows/x.yml"}]`,
# or a consumer names it in its own source entry the same way. Until then
# the installed copy drifted from the template with nothing saying so.
#
# An installed copy still holding the text last installed (recorded under
# `installed` in process/manifest_<source>.json, else the template at the
# copy's previous commit) is rewritten with the new template. For a
# workflow, the approval pinned to the old text moves to the new one: the
# Update Vendors go-ahead approves it (Morgan, 2026-10-30, strength:
# decided: "yes absolutely", to "should Update Vendors count as approval for
# the new text ... when the installed copy still matches the old template
# exactly"). A copy changed here is left alone: KEPT ON PURPOSE when
# precedent.json's kept_template_divergences gives a reason for its path,
# LEFT FOR YOU otherwise. One never installed here is only named.
INSTALLED_KEY = 'installed'


def declared_installs(entry, man):
    """-> [(from, to)] a copied-in source installs: its precedent-source.json's
    `installs`, then its precedent.json entry's, the entry winning on `to`.
    A path that is absolute or climbs out with `..` is dropped."""
    out = {}
    for rows in ((man or {}).get('installs'), (entry or {}).get('installs')):
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            frm = str(row.get('from') or '').strip().strip('/')
            to = str(row.get('to') or '').strip().strip('/')
            if frm and to and not any('..' in x.split('/') for x in (frm, to)):
                out[to] = frm
    return [(f, t) for t, f in out.items()]


def refresh_installed_templates(repo, rep, entry, clone, set_dir, man, prev):
    """Refresh each template `entry`'s source installs in `repo` (see the
    block comment above), and record what was installed."""
    import hashlib
    installs = declared_installs(entry, man)
    if not installs:
        return
    name = entry.get('name')
    mpath = repo / 'process' / f'manifest_{name}.json'
    try:
        record = json.loads(mpath.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        record = {}
    if not isinstance(record, dict):
        record = {}
    installed = record.get(INSTALLED_KEY) if isinstance(
        record.get(INSTALLED_KEY), dict) else {}
    sha = lambda b: hashlib.sha256(b).hexdigest()               # noqa: E731
    kept = pve.kept_template_divergences(repo)
    root = str(entry.get('set_root') or '').strip('/')
    for frm, to in installs:
        what = f'{to} (from {name}\'s {frm})'
        src = pathlib.Path(set_dir) / frm
        if not src.is_file():
            rep.step(f'copy of {name}', f'{what}: {name} no longer ships '
                     f'{frm}, so the installed copy was left as it is')
            continue
        new = src.read_bytes()
        dest = repo / to
        if not dest.is_file():
            rep.step(f'copy of {name}', f'{what}: not installed here' + (
                ' (removed since it was installed), so not put back'
                if to in installed else '; copy it in to take it'))
            continue
        cur = dest.read_bytes()
        if cur == new:
            installed[to] = sha(new)
            continue
        base = installed.get(to)
        if not base and prev:
            # Nothing recorded yet: what was installed is the template as it
            # stood at the commit the copy was last taken from.
            r = subprocess.run(['git', '-C', str(clone), 'show',
                                f'{prev}:{root + "/" if root else ""}{frm}'],
                               capture_output=True)
            base = sha(r.stdout) if r.returncode == 0 else None
        if base == sha(cur):
            dest.write_bytes(new)
            installed[to] = sha(new)
            repinned = _repin_installed_workflow(repo, to, sha(cur), sha(new), name)
            rep.step(f'copy of {name}', f'{what}: refreshed to the template\'s '
                     f'new text' + ('; its workflow approval moved to the new '
                                    'text with it' if repinned else ''))
            continue
        reason = (kept.get(to) or {}).get('reason')
        if reason:
            rep.step(f'copy of {name}', f'{what}: KEPT ON PURPOSE, as '
                     f'precedent.json\'s kept_template_divergences records -- '
                     f'"{reason}"; the template moved, so read its change')
            continue
        rep.leave(what, f'changed here, so not refreshed to the template\'s new '
                  f'text. Take the template ({frm} in {name}) if the change '
                  f'here was not on purpose; or record why under '
                  f'kept_template_divergences in precedent.json, keyed "{to}"')
    if installed != record.get(INSTALLED_KEY):
        record[INSTALLED_KEY] = installed
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


def _repin_installed_workflow(repo, rel, old_sha, new_sha, source):
    """Move precedent.json's github_ci_approved pin for `rel` from `old_sha`
    to `new_sha`, saying why in its approved_by. -> True when it moved. An
    entry pinned to anything else -- the old text never approved -- is left
    for the approval check to judge, as it was."""
    import precedent_time
    path = repo / 'precedent.json'
    try:
        cfg = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    entry = (cfg.get('github_ci_approved') or {}).get(rel) \
        if isinstance(cfg, dict) else None
    if not isinstance(entry, dict) or entry.get('sha256') != old_sha:
        return False
    entry['sha256'] = new_sha
    entry['approved_by'] = (
        f'{entry.get("approved_by") or ""}; Update Vendors, '
        f'{precedent_time.today(repo)}: refreshed from {source}\'s template, '
        f'unedited here (Morgan, 2026-10-30: "yes absolutely", Update Vendors '
        f'approves an unedited installed copy\'s new template text)').lstrip('; ')
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8')
    return True


def _copy_digest(folder):
    """-> {relative path: content hash} of every file under `folder`."""
    import hashlib
    folder = pathlib.Path(folder)
    if not folder.is_dir():
        return {}
    return {f.relative_to(folder).as_posix(): hashlib.sha1(f.read_bytes()).hexdigest()
            for f in folder.rglob('*') if f.is_file()}


def _copy_changes(was, now):
    """-> sorted 'path (added|changed|removed)' lines between two digests."""
    out = []
    for rel in sorted(set(was) | set(now)):
        if rel not in was:
            out.append(f'{rel} (added)')
        elif rel not in now:
            out.append(f'{rel} (removed)')
        elif was[rel] != now[rel]:
            out.append(f'{rel} (changed)')
    return out


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

# Engine paths that moved, old -> new: every consumer that named an old one
# fails its next push on rename-updates-links unless the update repoints it
# (repoint_renamed_engine_paths). Git sees most moves itself
# (engine_path_moves); a row here is only for one it cannot see between a
# consumer's two commits.
# 2026-10-10: the commit checks became engine files (49b31179); a
# consumer's second Update Vendors run failed on four live mentions of the
# old paths that the first run never listed. Both rows stay: a consumer
# had these checks materialized from a practice set, from before BestPractice
# carried them (9d16b6ae), so its own range can start where git has no
# old file to see renamed.
ENGINE_PATH_MOVES = {
    'tools/checks/check_commit_author.py': 'tools/check_commit_author.py',
    'tools/checks/check_buenos_aires_dates.py': 'tools/check_commit_dates.py',
}
TEXT_SUFFIXES = ('.md', '.json', '.sh', '.py', '.yml', '.yaml', '.txt', '.toml')


def engine_path_moves(source, old, new):
    """-> ({old path: new path}, note): every rename git sees under tools/
    -- the engine and the materialized checks a consumer receives -- between
    the source commits an update goes from and to, with ENGINE_PATH_MOVES
    over them. The note is None, or says why git could not be asked.

    A HAND-KEPT MAP MISSES A RENAME NOBODY ADDED A ROW FOR (2026-10-14): the
    next push of every consumer naming the old path then failed on
    rename-updates-links. Renames that never reached a consumer cost
    nothing: repoint_renamed_engine_paths acts only where the old path is
    gone and the new one is there."""
    moves, note = {}, None
    if not old or not new:
        note = 'no earlier engine commit recorded, so only the hand-kept moves apply'
    elif old != new:
        r = subprocess.run(['git', '-C', str(source), 'diff', '-M', '--name-status',
                            '--diff-filter=R', old, new, '--', 'tools/'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            note = (f'git could not diff {old[:12]}..{new[:12]} in {source}, so '
                    f'only the hand-kept moves apply')
        for ln in (r.stdout.splitlines() if r.returncode == 0 else []):
            parts = ln.split('\t')
            if len(parts) == 3 and parts[0].startswith('R'):
                moves[parts[1]] = parts[2]
    moves.update(ENGINE_PATH_MOVES)
    return moves, note


def repoint_renamed_engine_paths(repo, moves=None):
    """-> [(rel, n)]: rewrite each live mention of an ENGINE_PATH_MOVES old
    path to its new one, in the repo's own tracked text, where the old path
    is gone and the new one is there. Left as written, exactly as
    rename-updates-links leaves them: history (a closed todo item, a
    generated view, a finished document, a Story section), a generated
    block, a sentence saying the thing moved or is gone, and a line that
    already names the new path. Vendored and engine files are never
    touched: their own source rewrites them.

    A LINK IS NOT HISTORY (2026-10-14, a consumer's Update Vendors). A
    closed todo item linked `../tools/checks/check_buenos_aires_dates.py`.
    This left the item alone as history, the link check then failed the
    update on the dead link, and the session repointed it by hand. Two gaps:
    a history file was skipped whole, and a relative link (`../tools/...`)
    never matched the repo-root path at all. So a Markdown link's TARGET is
    repointed wherever it resolves to a moved path -- history and Story
    sections included, since a link has to resolve whatever it records --
    and its visible text, like every other mention there, stays as
    written."""
    import generated_blocks
    import precedent_check as pc
    moves = {o: n for o, n in (ENGINE_PATH_MOVES if moves is None else moves).items()
             if not (repo / o).exists() and (repo / n).exists()}
    if not moves:
        return []
    r = subprocess.run(['git', '-C', str(repo), 'ls-files'],
                       capture_output=True, text=True)
    own = set(_own_shell_scripts(repo))
    try:
        received = set(json.loads((repo / 'tools' / 'ENGINE_MANIFEST.json')
                                  .read_text(encoding='utf-8')).get('files') or ())
    except (OSError, ValueError, AttributeError):
        received = set()
    import precedent_resolve as pr
    mirrors = tuple(pr.mirrored_prefixes(repo) or ())
    pats = {o: re.compile(r'(?<![\w./-])' + re.escape(o) + r'(?![\w/-])')
            for o in moves}
    done = []
    for rel in (r.stdout.split() if r.returncode == 0 else []):
        if not rel.endswith(TEXT_SUFFIXES) and rel not in own:
            continue
        if (mirrors and rel.startswith(mirrors)) or rel.startswith(
                ('practices/', '.precedent/', '.claude/hooks/')) \
                or (rel.startswith('tools/') and rel[len('tools/'):] in received):
            continue
        f = repo / rel
        try:
            text = f.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        if not any(o in text for o in moves):
            continue
        history = pc._is_history(rel, text)
        lines = text.split('\n')
        gen = generated_blocks.mask(lines) if rel.endswith('.md') else [False] * len(lines)
        story = pc._story_mask(lines) if rel.endswith('.md') else [False] * len(lines)
        n = 0
        for i, line in enumerate(lines):
            if gen[i]:
                continue
            new_line = (_repoint_link_targets(line, rel, moves)
                        if rel.endswith('.md') else line)
            if history or story[i]:
                if new_line != line:
                    lines[i] = new_line
                    n += 1
                continue
            for o, nw in moves.items():
                if not pats[o].search(new_line) or nw in line \
                        or pc._sentences_saying_gone(lines, i, o):
                    continue
                new_line = pats[o].sub(nw, new_line)
            if new_line != line:
                lines[i] = new_line
                n += 1
        if n:
            f.write_text('\n'.join(lines), encoding='utf-8')
            done.append((rel, n))
    return done


_MD_LINK_TARGET_RE = re.compile(r'(\]\()([^)\s#]+)(#[^)\s]*)?(\))')


def _repoint_link_targets(line, rel, moves):
    """`line` with each Markdown link target that resolves, from `rel`'s
    directory, to an old path in `moves` rewritten to the new path relative
    to the same directory. Only the target; the link text is not touched."""
    base = os.path.dirname(rel)

    def sub(m):
        target = m.group(2)
        if '://' in target or target.startswith(('/', 'mailto:')):
            return m.group(0)
        resolved = os.path.normpath(os.path.join(base, target))
        if resolved not in moves:
            return m.group(0)
        new = os.path.relpath(moves[resolved], base or '.')
        return m.group(1) + new + (m.group(3) or '') + m.group(4)
    return _MD_LINK_TARGET_RE.sub(sub, line)


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


def names_full_path(line, path):
    """True when `line` names `path` the way rename-updates-links reads a
    line: the whole path, or with ./ or ../ in front, never as the tail of a
    longer path and never by its file name alone.

    WHY (2026-10-17, a document project's Update Vendors): the first run
    left precedent.json lines that the same run had already repointed from
    tools/checks/check_commit_author.py to tools/check_commit_author.py, and
    the engine manifest's bare "check_commit_author.py" at its new home, as
    still naming the old path: this matched the file name alone. Nothing
    refuses those lines, and the next run, with no edit, did not list
    them."""
    start = 0
    while True:
        i = line.find(path, start)
        if i < 0:
            return False
        start = i + 1
        k = i
        while k > 0 and (line[k - 1].isalnum() or line[k - 1] in '._-/'):
            k -= 1
        prefix = line[k:i]
        if not prefix or (prefix.endswith('/') and all(
                seg in ('.', '..') for seg in prefix[:-1].split('/'))):
            return True


def retired_mentions(repo, engine_out):
    """-> [(where, gone)] for each file that still names something the
    engine refresh deleted, and still does now that the rest of the update
    has run.

    The engine only WARNs about these, on stderr, and says nothing refuses
    over a mention. The quick check agreed; the full check did not, and
    refused on them (practice:
    rename-updates-links; 2026-09-28: a retired bestpractice-docs.yml still
    named in a consumer's docs). So each one goes on Left for you, inside
    the update.
    Read from the WARN lines rather than asked of the engine because the
    deletion usually happens in the first pass, which is the consumer's own
    older copy. A file this repo receives rather than writes -- the
    vendored tree, practices/, tools/checks/, the engine's own files and
    hooks -- is skipped: the check skips it too, and the next sync or
    refresh overwrites it."""
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
    # So is the engine itself, and whatever else another tool writes here
    # (pve.received_paths): until 2026-10-17 this told a session to edit
    # tools/precedent_vendor_engine.py, precedent_bootstrap_source.py and
    # very_deep_check.py, vendored files the full check refuses to see
    # edited, because they name the file they just retired.
    files, under = pve.received_paths(repo)
    received += under
    out = []
    for line in engine_out.splitlines():
        m = _MENTION.match(line.strip())
        if not m or m.group('path').startswith(received) or m.group('path') in files:
            continue
        gone, path = m.group('gone'), m.group('path')
        try:
            text = (repo / path).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        hit = next((n for n, l in enumerate(text.splitlines(), 1)
                    if names_full_path(l, gone)), None)
        if hit is not None and (f'{path}:{hit}', gone) not in out:
            out.append((f'{path}:{hit}', gone))
    return out


def migrations_step(repo, rep):
    """Run every tools/migration_*.py beside this file, in name order,
    without naming any: each exposes migrate(repo, rep, update), `update`
    being this module. A migration is how a repository whose vendors were
    not updated is moved off something the engine no longer knows; it is
    deleted once nobody needs it, and nothing here changes when it is."""
    import importlib.util
    for path in sorted(HERE.parent.glob('migration_*.py')):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.migrate(pathlib.Path(repo), rep, sys.modules[__name__])


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
    if hasattr(_bv, 'view_owner'):   # the one answer to whose a view is
        return [name for name in FULL_VIEWS
                if (pathlib.Path(repo) / name).is_file()
                and _bv.view_owner(repo, name) in _bv.ENGINE_WRITES]
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


def instantiate_local_practice(repo, rel, rev):
    """Write repo-local practice `rel` (local/practices/project-voice.md ...)
    from its template at `rev`, exactly as an install writes it, when it is
    missing and precedent.json declares the repo-local source it belongs
    to. -> whether it was written.

    WHY (2026-10-17, very deep check's migration rehearsal). Deleting a
    default VOICE.md left no project-voice.md at all, while
    local/practices/project-visual-identity.md -- installed or converted
    from STYLEGUIDE.md -- links it, so the repo carried a link to nothing.
    An install always writes both."""
    import precedent_install as pi
    import precedent_time
    tmpl = pi.LOCAL_PRACTICE_FILES.get(rel)
    target = pathlib.Path(repo) / rel
    if not tmpl or not rev or target.exists():
        return False
    try:
        sources = json.loads((pathlib.Path(repo) / 'precedent.json').read_text(
            encoding='utf-8')).get('sources') or []
    except (OSError, ValueError, AttributeError):
        return False
    root = pathlib.PurePosixPath(rel).parts[0]
    if not any(isinstance(src, dict) and src.get('level') == 'repo-local'
               and str(src.get('path', '')).strip('/') == root for src in sources):
        return False
    text = _source_text(rev, f'templates/{tmpl}')
    if text is None:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(pi._substitute(text, {'<install date>': precedent_time.today(SOURCE)}),
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
            if retire_shipped_root_doc(repo, old):
                made = instantiate_local_practice(repo, new, rev)
                if rep is not None:
                    rep.step(old, f'deleted: it was the shipped default, unchanged, '
                                  f'so it carried no decision to convert into {new}; '
                                  f'its process/manifest.json entry went with it'
                             + (f'; {new} was written from its template, as an '
                                f'install writes it' if made else ''))
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


# The key precedent_install.per_file_substitutions() gives each install-once
# file under, where it is not the file's own name: the install writes the
# map's text to MAP.source.md, which MAP.md is generated from.
_INSTALL_KEYS = {'MAP.md': 'MAP.source.md', 'GLOSSARY.md': 'GLOSSARY.source.md'}


def _template_versions(rev, tmpl, limit=200):
    """-> [text] each version `tmpl` had in the source's history up to
    `rev`, newest first, `--follow`ed through renames, each text once."""
    r = subprocess.run(['git', '-C', str(SOURCE), 'log', '--follow', f'-{limit}',
                        '--format=%x00%H', '--name-only', rev, '--', tmpl],
                       capture_output=True, text=True, errors='replace')
    seen, out = set(), []
    for chunk in (r.stdout.split('\0')[1:] if r.returncode == 0 else []):
        lines = [l for l in chunk.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        text = _source_text(lines[0], lines[-1])
        if text is not None and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _placeholder_values(template, filled):
    """-> {placeholder: value} read off `filled`, an install's copy of
    `template`, or None when `filled` is not one. The two are aligned line
    by line; every line that differs must be its template line with each
    placeholder filled in, a placeholder reading the same wherever it
    recurs. Lines with one placeholder are read first, so a line with
    several splits on values already known. A placeholder the install left
    as it was reads back as itself, by matching its line unchanged."""
    import difflib
    t_lines, f_lines = template.splitlines(), filled.splitlines()
    pairs = []
    sm = difflib.SequenceMatcher(None, t_lines, f_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        if tag != 'replace' or i2 - i1 != j2 - j1:
            return None
        pairs += list(zip(t_lines[i1:i2], f_lines[j1:j2]))
    values = {}
    pairs.sort(key=lambda tc: len(set(_PLACEHOLDER_RE.findall(tc[0]))))
    for t, c in pairs:
        t = _render(t, values)
        found = _PLACEHOLDER_RE.findall(t)
        if not found:
            if t != c:
                return None
            continue
        parts = _PLACEHOLDER_RE.split(t)
        groups, pat = {}, re.escape(parts[0])
        for name, part in zip(found, parts[1:]):
            if name in groups:
                pat += f'(?P={groups[name]})'
            else:
                groups[name] = f'g{len(groups)}'
                pat += f'(?P<{groups[name]}>.+?)'
            pat += re.escape(part)
        m = re.fullmatch(pat, c)
        if not m:
            return None
        for name, g in groups.items():
            values[name] = m.group(g)
    return values


def _render(text, values):
    for name, value in values.items():
        text = text.replace(name, value)
    return text


def untouched_install_copy(repo, rel, tmpl, rev, committed=None):
    """Write the current `tmpl` (at `rev`), filled in as the install filled
    it, over install-once file `rel` when `rel` is still exactly what an
    install wrote from some version of `tmpl` in the source's history -- the
    version at the commit the install recorded among them: the same
    placeholders filled with the same values (read off the file itself) and
    the same per-file text precedent_install.per_file_substitutions() puts
    in. -> whether it was written. A file with any edit of the repository's
    own matches no version, and is left for the person as before (practice:
    repair-cannot-discard-work); so is a view's source in the directory
    form, which no install writes. `committed`, when given, is the text the
    file had before this update wrote anything (HEAD's, for a file that was
    clean when the run started), and is what is judged: the engine refresh
    adds its own disclosures to GETTING_STARTED.md first, and those are the
    current template's, not the repository's.

    WHY (2026-10-17, very deep check, an update of a two-week-old install).
    An install that nobody had touched stopped on seven LEFT FOR YOU lines,
    every one of them upstream rewording GETTING_STARTED.md, MAP.md or
    local/practices/project-voice.md, because only a template copied
    verbatim was recognised as unedited, and these three have placeholders
    an install fills. That narrower test (2026-10-13: a consumer's pull
    request template matched an old template exactly and was still left for
    a person to copy in by hand) is the case of this one with no
    placeholders, and was folded into it. Morgan's rule of 2026-10-14
    is to take upstream's version by default; the decision to compare with
    the template as installed was the session's, under Morgan's delegation
    of 2026-10-17 ("Fix the other issues you found including the checks
    that never run. Tell me what you decide. I will be offline so don't
    wait for me. Approved, act, and Booked.")."""
    import precedent_install as pi
    target = pathlib.Path(repo) / rel
    key = _INSTALL_KEYS.get(rel, rel)
    if rel == 'README.md' or rel not in (
            {r for r, _t in INSTALL_ONCE_TEMPLATES} | set(_INSTALL_KEYS.values())):
        return False
    if rel in _INSTALL_KEYS and _hand_kept_files(repo, rel) != [target]:
        return False
    current = _source_text(rev, tmpl) if rev else None
    if current is None:
        return False
    try:
        now = target.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    ours = now if committed is None else committed
    variants = []
    for ci in (True, False):
        subs = pi.per_file_substitutions(ci).get(key, {})
        if subs not in variants:
            variants.append(subs)
    versions = _template_versions(rev, tmpl)
    for subs in variants:
        for old in versions:
            base = pi._substitute(old, subs)
            values = _placeholder_values(base, ours)
            if values is None or _render(base, values) != ours:
                continue
            new = _render(pi._substitute(current, subs), values)
            if new == now:
                return False
            target.write_text(new, encoding='utf-8')
            return True
    return False


# The template's own instruction comment: the first HTML comment that opens
# "<!-- Template" (GETTING_STARTED.md's opens "<!-- Template AND ...").
_TEMPLATE_COMMENT = re.compile(r'^\s*<!--\s*Template\b')


def _template_comment_span(lines):
    """-> (start, end), 0-based and end-exclusive, of the template's own
    instruction comment in `lines`, or None when there is none."""
    for i, line in enumerate(lines):
        if _TEMPLATE_COMMENT.match(line):
            for j in range(i, len(lines)):
                if '-->' in lines[j]:
                    return i, j + 1
            return None
    return None


def refresh_template_comment(repo, rel, tmpl, rev, hits):
    """Replace install-once file `rel`'s template instruction comment with
    the current `tmpl`'s (at `rev`) when a dropped line `hits` found sits in
    it. -> the hits left outside it, renumbered to the file as written, or
    None when nothing was written.

    The comment is the template's, not the repository's: it tells whoever
    installs the file what to do with it. Only a comment whose every line
    some version of the template carried is replaced, so a word the
    repository added there is never lost (practice:
    repair-cannot-discard-work); otherwise the lines are left for the person
    as before, and so is anything outside the comment.

    WHY (2026-10-15, a consumer's Update Vendors). Upstream renumbered
    "INSTALL.md §1" to "§0" inside the comment of four templates, and the
    update stopped on four LEFT FOR YOU lines until a person edited one line
    in each file by hand -- the same four in every consuming repository."""
    target = pathlib.Path(repo) / rel
    current = _source_text(rev, tmpl)
    try:
        text = target.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None
    if current is None:
        return None
    lines, theirs = text.splitlines(keepends=True), current.splitlines(keepends=True)
    ours, now = _template_comment_span(lines), _template_comment_span(theirs)
    if not ours or not now:
        return None
    a, b = ours
    if not any(a < n <= b for n, _l in hits):
        return None
    upstream = _template_lines_ever(rev, tmpl) | {l.strip() for l in theirs}
    if any(l.strip() not in upstream for l in lines[a:b] if l.strip()):
        return None
    new = theirs[now[0]:now[1]]
    if new and not new[-1].endswith('\n') and lines[b:]:
        new[-1] += '\n'
    if new == lines[a:b]:
        return None
    target.write_text(''.join(lines[:a] + new + lines[b:]), encoding='utf-8')
    shift = len(new) - (b - a)
    return [(n + shift if n > b else n, l) for n, l in hits if not a < n <= b]


# A command line of the generated occasion index, and the slug lines under it.
_COMMAND_OCCASION = re.compile(r'^When a (?:person|message) says (.+):\s*$')
_INDEX_SLUG = re.compile(r'^\s+([a-z0-9][a-z0-9-]*) — ')
_WITHDRAWN_TO_SET = re.compile(r'`([a-z0-9][a-z0-9-]*)` withdrawn from universal, '
                               r'deliberately; in force only from the shared set '
                               r'`([\w.-]+)`')
WITHDRAWN_RECORD = 'record/WITHDRAWN_FROM_UNIVERSAL.md'
_RESIDENT_SLUG = re.compile(r'^\*\*([a-z0-9][a-z0-9-]*)\.\*\*')


def _listed_commands(agents_text):
    """-> {slug: [phrase]} for each standing command an AGENTS.md's occasion
    index lists: the quoted phrases of a `When a person says "..."` line,
    under each slug that line introduces."""
    out, phrases = {}, None
    for line in (agents_text or '').splitlines():
        m = _COMMAND_OCCASION.match(line)
        if m:
            phrases = re.findall(r'"([^"]+)"', m.group(1))
            continue
        m = _INDEX_SLUG.match(line)
        if m and phrases:
            out.setdefault(m.group(1), list(phrases))
        elif not m:
            phrases = None
    return out


def moved_commands_step(repo, rep, old_agents, rev):
    """Say, in one line, how many standing-command phrases this repository's
    AGENTS.md listed before the update that are in force nowhere here now,
    because upstream moved their practices to an optional set this
    repository does not declare -- without the phrases themselves.

    WHY (2026-10-17, very deep check): an update of an install from before
    2026-10-02 removed every ladder command from its instructions, silently.
    By design for a repository off the ladder, so nothing is put back; the
    decision (the session's, under Morgan's delegation of 2026-10-17) is
    that the update says so once, and never prints the words, which a
    person off the ladder has no use for. Where they went is read from
    upstream's record/WITHDRAWN_FROM_UNIVERSAL.md at the commit taken."""
    before = _listed_commands(old_agents)
    if not before or not rev:
        return
    try:
        now = (repo / 'AGENTS.md').read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return
    # In force here: an occasion-index entry or a resident-block rule of the
    # new AGENTS.md, which lists every source this repository declares.
    listed = {m.group(1) for line in now.splitlines()
              for m in (_INDEX_SLUG.match(line), _RESIDENT_SLUG.match(line)) if m}
    gone = set(before) - listed
    if not gone:
        return
    moved = dict(_WITHDRAWN_TO_SET.findall(_source_text(rev, WITHDRAWN_RECORD) or ''))
    try:
        declared = {str(src.get('name')) for src in json.loads(
            (repo / 'precedent.json').read_text(encoding='utf-8')).get('sources') or []
            if isinstance(src, dict)}
    except (OSError, ValueError, AttributeError):
        declared = set()
    by_set = {}
    for slug in sorted(gone):
        where = moved.get(slug)
        if where and where not in declared:
            by_set.setdefault(where, []).extend(before[slug])
    for where, phrases in sorted(by_set.items()):
        n = len(dict.fromkeys(phrases))
        rep.step('standing commands', f'{n} command phrase(s) this '
                 f'repository\'s AGENTS.md listed before this update are no '
                 f'longer in force here: upstream moved them to {where}, an '
                 f'optional practice set this repository does not declare '
                 f'({WITHDRAWN_RECORD} upstream). Nothing to do unless '
                 f'someone here uses them; declaring that set in '
                 f'precedent.json brings them back')


def dropped_template_lines_step(repo, rep, rev):
    """Put each line dropped_template_lines finds on the Left-for-you list.
    A file precedent.json's kept_template_divergences records as kept on
    purpose, against the current template's text, is said once and not
    listed -- the same declaration the engine honours for tools/bootstrap.sh,
    so a repo that keeps an old line deliberately can still finish.

    A PIN MOVES BY ITSELF ACROSS A COMMENT-ONLY CHANGE (2026-10-12, a
    consuming repository's Update Vendors): a kept GETTING_STARTED.md was
    asked about again because templates/GETTING_STARTED.md's only change
    was inside an HTML comment, which no reader of the file sees. When the
    pinned text can be found in the template's history and differs from
    today's only in comments, the pin is moved and said once; otherwise the
    question shows what changed, so it is answered on the change.

    AN UNTOUCHED COPY TAKES UPSTREAM'S VERSION FIRST (2026-10-17): each
    install-once file still exactly as an install wrote it is brought onto
    the current template before any line is read (untouched_install_copy),
    so only a file the repository edited can leave a line for the person."""
    taken = []
    kept = set(pve.kept_template_divergences(repo)) if rev else set()
    for rel, tmpl in INSTALL_ONCE_TEMPLATES if rev else ():
        files = _hand_kept_files(repo, rel)
        if len(files) != 1 or not files[0].is_file():
            continue
        own = files[0].relative_to(repo).as_posix()
        committed = (_git_show(repo, f'HEAD:{own}')
                     if rep.before is not None and own not in rep.before else None)
        if own not in kept and untouched_install_copy(repo, own, tmpl, rev,
                                                      committed):
            taken.append(own)
    if taken:
        rep.step('templates taken', f'{", ".join(taken)}: still exactly as '
                 f'the install wrote them from an older template, with no edit '
                 f'of this repository\'s own, so each now carries the current '
                 f'template, filled in with the same values')
    for rel, tmpl, sha, hits in dropped_template_lines(repo, rev):
        verdict, reason = pve._kept_divergence(repo, rel, sha)
        old = None
        if verdict == 'stale':
            pinned = (pve.kept_template_divergences(repo).get(rel) or {}).get(
                'template_sha256', '')
            old = pve.template_text_at(SOURCE, rev, tmpl, pinned)
            current = _source_text(rev, tmpl)
            if (old is not None and current is not None
                    and pve.without_comments(old) == pve.without_comments(current)
                    and pve._repin_after_formatting(repo, rel, sha, None)):
                rep.step('kept pin updated', f'{rel} is kept on purpose '
                         f'("{reason}"), and {tmpl} changed only inside HTML '
                         f'comments since, so the pin now records today\'s text')
                continue
        if verdict == 'kept':
            rep.step('kept on purpose', f'{rel} keeps wording {tmpl} dropped, '
                     f'as precedent.json records -- "{reason}"')
            continue
        if verdict == 'stale':
            kept_file_question(repo, rep, rel, tmpl, sha, reason, old, rev)
            continue
        if verdict in (None, 'unreasoned'):
            left = refresh_template_comment(repo, rel, tmpl, rev, hits)
            if left is not None:
                rep.step('template comment refreshed', f'{rel}: the '
                         f'instruction comment {tmpl} opens with was an older '
                         f'version of the template\'s own, so it now carries '
                         f'the current one; nothing outside it was touched')
                hits = left
                if not hits:
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
        if verdict == 'unreasoned':
            note.insert(0, 'recorded as kept with no reason, so not honoured')
        rep.details.setdefault(first, []).extend(note)


def _lines_this_update_added(repo, rel, rep):
    """-> [line] the file `rel` has now and had at HEAD, which this run
    wrote: only when the file was clean when the run started writing, so a
    person's own uncommitted edit is never called the update's."""
    if rep.before is None or rel in rep.before:
        return []
    committed = _git_show(repo, f'HEAD:{rel}')
    if committed is None:
        return []
    try:
        now = (repo / rel).read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return []
    import difflib
    return [l[1:] for l in difflib.unified_diff(
                committed.splitlines(), now.splitlines(), lineterm='', n=0)
            if l.startswith('+') and not l.startswith('+++') and l[1:].strip()]


def kept_file_question(repo, rep, rel, tmpl, sha, reason, old, rev):
    """ONE question for a file kept whole on purpose whose template has
    changed since that was recorded: what changed in the template, what
    this update already carried into the file, and the one edit that
    records it as still kept.

    WHY (2026-10-17, a consuming repository's Update Vendors): its
    GETTING_STARTED.md is rewritten on purpose and recorded as kept. The
    template gained a bullet and a reworded line. The update carried the
    bullet into the file itself, said nothing about it, and then left ten
    items, one per line of the repository's own rewrite, each saying "bring
    it in line with templates/GETTING_STARTED.md, or drop the line". A
    session doing what it was told would have cut lines from a file the
    repository keeps on purpose. The lines are the repository's; the
    question is only whether the decision still holds."""
    change = (pve._template_change(old, _source_text(rev, tmpl) or '')
              if old is not None else [])
    carried = _lines_this_update_added(repo, rel, rep)

    def clip(line):
        return '  ' + (line if len(line) <= 160 else line[:157] + '...')
    rep.leave(rel, f'kept on purpose ("{reason}"), and {tmpl} has changed '
              f'since that was recorded: is it still kept as it is? Its own '
              f'lines are this repository\'s; none of them is to be dropped '
              f'for this question')
    note = []
    if change:
        note.append(f'what changed in {tmpl} since the recorded version:')
        note += [clip(l) for l in change[:20]]
        if len(change) > 20:
            note.append(f'  ... and {len(change) - 20} more line(s)')
    else:
        note.append(f'the recorded version of {tmpl} could not be found in '
                    f'its history, so read the current template against the '
                    f'file')
    if carried:
        note.append(f'this update already carried {len(carried)} line(s) of '
                    f'it into {rel}, uncommitted:')
        note += [clip(l) for l in carried[:10]]
    note.append(f'still kept? in precedent.json, set '
                f'{pve.KEPT_DIVERGENCES_KEY}["{rel}"].template_sha256 to {sha} '
                f'and run again; not kept? bring {rel} in line with {tmpl} by '
                f'hand, then remove its entry')
    rep.details.setdefault(rel, []).extend(note)


def budget_note_key(tool):
    """The registry's note key for a tool's run budget:
    'precedent_vendor_engine.py' -> '_precedent_vendor_engine_note'."""
    return '_' + tool[:-3] + '_note' if tool.endswith('.py') else f'_{tool}_note'


def seed_engine_budgets(repo, rev, last_synced=None):
    """Write into this repo's tools/github_api_budgets.json the run budget,
    and its note, of every vendored engine tool upstream budgets and this
    repo does not. -> (seeded [(tool, calls)], asks [(tool, ours, theirs)],
    followed [(tool, was, now)]).

    2026-10-07, a consuming repository: upstream added a budget for the
    vendored precedent_vendor_engine.py, and the update stopped to leave it
    for the person, who copied upstream's 12 and note in by hand -- a figure
    with nothing to decide, which every consumer would copy the same way.
    The engine is upstream's code, so upstream's budget for it is the
    starting figure. Only where this repo already has a DIFFERENT figure, and
    upstream's own moved since the last sync, is there a call to make: keep
    the repo's own, or take upstream's new one. A repo with no registry
    declares nothing, and still gets nothing.

    A THREE-WAY READ (2026-10-12, a consuming repository's Update Vendors):
    a figure equal to upstream's at the last sync is upstream's old figure,
    never this repo's choice, so when upstream moves it the repo follows,
    its note too while the note is upstream's old one, and nothing is
    asked. The update had asked about 400 and 120, upstream's own figures
    before it raised them."""
    path = repo / 'tools' / 'github_api_budgets.json'
    try:
        own = json.loads(path.read_text(encoding='utf-8'))
        vendored = set(json.loads((repo / 'tools' / pve.MANIFEST_NAME)
                                  .read_text(encoding='utf-8')).get('files') or ())
        up = json.loads(_source_text(rev, 'tools/github_api_budgets.json') or '')
    except (OSError, ValueError, TypeError):
        return [], [], []
    if not isinstance(own, dict) or not isinstance(up, dict):
        return [], [], []
    try:
        before = json.loads(_source_text(last_synced, 'tools/github_api_budgets.json')
                            or '') if last_synced else {}
    except ValueError:
        before = {}
    up_b = up.get('run_budgets') or {}
    was_b = (before.get('run_budgets') or {}) if isinstance(before, dict) else {}
    have = own.setdefault('run_budgets', {})
    seeded, asks, followed = [], [], []
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
            if tool in was_b and have[tool] == was_b[tool]:
                note = budget_note_key(tool)
                if note in up_b and have.get(note) in (None, was_b.get(note)):
                    have[note] = up_b[note]
                followed.append((tool, have[tool], calls))
                have[tool] = calls
            else:
                asks.append((tool, have[tool], calls))
    if seeded or followed:
        path.write_text(json.dumps(own, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8')
    return seeded, asks, followed


def range_readable(clone, old, new):
    """-> (True, '') when `clone` holds `old` as an ancestor of `new`, after
    fetching more history if it has to; else (False, why and the fix).

    WHY (2026-10-12, a consuming repository's Update Vendors): cloud sessions
    clone BestPractice with --depth 1, so the commit the repository last
    vendored was not in the clone, `git log old..new` failed, and the report
    said "could not be read here" over 110 commits, most of them a
    colleague's. The fetch is the engine's one way,
    precedent_local_edits.fetch_commit, in its range-read mode: deepened in
    bounded steps, then unshallowed as a last resort."""
    if le.fetch_commit(clone, old, ancestor_of=new):
        return True, ''
    return False, (f'{pathlib.Path(clone).name} does not hold {str(old)[:12]} as '
                   f'an ancestor of {str(new)[:12]}, even after fetching more '
                   f'history; `git -C {clone} fetch --unshallow origin` and a '
                   f'second run read it')


def upstream_by_others(repo, old, new, clone=None):
    """-> (others, unsure) for the commits a source gained between `old`,
    the commit this repository last took from it, and `new`, the one it
    takes now, made by anyone but the person running the update; None when
    it cannot be read (no identity, or a commit the clone lacks). `clone`
    is the source's checkout, BestPractice's (SOURCE) when not given.
    The same sorting a set's daily report uses (precedent_commit_owners):
    a commit signed only by Claude counts as its session's owner's."""
    import precedent_identity as pi
    import precedent_commit_owners as od
    clone = clone or SOURCE
    if not old or not new or old == new:
        return [], []
    try:
        me = pi.declared_identity(repo)
    except Exception:                                             # noqa: BLE001
        return None
    if not range_readable(clone, old, new)[0]:
        return None
    code, out = od.git(clone, 'log', '--no-merges', od.LOG_FORMAT, f'{old}..{new}')
    if code != 0:
        return None
    return od.classify(clone, od.records(out), me.get('email'), {'new': new})


def set_pins(repo):
    """-> {name: (clone path, commit)} for every shared or individual set
    this repository's MANIFEST.json records syncing at a commit
    (precedent_source_pins): what a views sync took from each set."""
    import precedent_resolve as pr
    import precedent_source_pins as psp
    out = {}
    for e in psp._manifest(repo).get('sources') or []:
        if (not isinstance(e, dict) or pr.declared_level(e) == 'universal'
                or not e.get('name') or not e.get('commit') or not e.get('path')):
            continue
        path = pathlib.Path(str(e['path'])).expanduser()
        out[e['name']] = ((path if path.is_absolute() else repo / path).resolve(),
                          e['commit'])
    return out


def sets_moved(before, after):
    """-> [(name, clone, old, new)] for each set whose recorded commit this
    update moved."""
    return [(name, after[name][0], before[name][1], after[name][1])
            for name in sorted(after)
            if name in before and before[name][1] != after[name][1]]


def _off_ladder(repo):
    """True for a person off the ladder, whose Update Vendors report carries
    no note of what others changed upstream (the ladder set turns it on)."""
    try:
        import precedent_ladder
        return precedent_ladder.ladder_in_force(repo) is False
    except Exception:                                             # noqa: BLE001
        return False


def upstream_changes_block(repo, old, new, sets=()):
    """-> the block Update Vendors' report carries about what OTHER people
    changed upstream in what this update brings in -- BestPractice's range
    `old`..`new`, and each practice set in `sets` [(name, clone, old, new)]
    -- or '' when there is nothing to say or the person is off the ladder.

    WHY (Morgan, 2026-10-12: "Yes, build it"). The morning report says what
    others landed in the repository a session works in, so an Update Vendors
    in a consuming repository took in Alex's new rules without a word about
    them; the person asked the same day whether he had missed them. The
    update is when upstream's changes reach a repository, so its report
    says the few that matter, the morning report's way (the others-did
    practice, in the ladder set, which is what turns both on). The shared
    and individual sets came the same evening (Morgan: "yes extend it"):
    their changes reach a repository by the same update."""
    import precedent_commit_owners as od
    if _off_ladder(repo):
        return ''
    sections, unread, total = [], [], 0
    for name, clone, a, b in [(SOURCE.name, SOURCE, old, new), *sets]:
        found = upstream_by_others(repo, a, b, clone)
        if found is None:
            why = range_readable(clone, a, b)[1] if a and b else ''
            unread.append(f'{name} ({str(a)[:12]}..{str(b)[:12]})'
                          + (f' -- {why}' if why else ''))
            continue
        others, unsure = found
        if others or unsure:
            total += len(others) + len(unsure)
            sections.append(f'{name} ({str(a)[:12]}..{str(b)[:12]}):\n'
                            + od.commit_listing(others, unsure))
    note = (f'could not be read here: {", ".join(unread)}.\n' if unread else '')
    if not sections:
        return f'WHAT OTHERS CHANGED UPSTREAM: {note}' if note else ''
    return '\n'.join([
        f'WHAT OTHERS CHANGED UPSTREAM in what this update brings in -- '
        f'{total} commit(s) by people other than you.',
        '',
        'OPEN YOUR REPORT OF THIS UPDATE WITH THE THREE OR FOUR THAT MATTER '
        "MOST, never the whole list: What's New style, each opening with its "
        'key phrase in bold, saying who did it and what it changes for this '
        'repository and its sessions. A change to a rule or to how sessions '
        'behave always makes the cut (the others-did practice, in the ladder '
        'set; Morgan, 2026-10-12).',
        '']) + '\n' + '\n'.join(sections) + note


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
# close_detect.json is universal's declaration for its own the-boildown, which
# precedent_close_detect.py reads at <universal source>/close_detect.json; it
# never travelled, so "it notices and offers a rule" did nothing on a fresh
# install (very deep check, 2026-10-17). It is universal's rule, so it goes
# where universal's practices go -- what stays home is a team's or a
# person's own declaration (precedent_vendor_engine's note on the detector).
# reply_check.json is the same case for the reply gate: universal's
# declaration for its own the-boildown, fence-block-for-paste, prompt-please
# and the rest, read at <universal source>/reply_check.json. The classic
# process/upstream/ mirror carried it; this layout never did, so a new
# install declared no reply requirements and checks that read them, such as
# todo-is-a-handoff's, skipped there (very deep check, 2026-10-30; shipped
# 2026-10-31 after the requirements were judged against one person's
# conventions, Morgan, strength: assented).
CATALOGUE_COMPANIONS = ('precedent-source.json', 'record/WITHDRAWN_FROM_UNIVERSAL.md',
                        'close_detect.json', 'reply_check.json')


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
    import shutil
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
            return (f'could not read practices/ at {rev[:12]} in {CLONE}: '
                    f'{arc.stderr.decode(errors="replace").strip()[:200]}')
        with tempfile.TemporaryDirectory() as td:
            import checkin
            checkin.extract_archive(arc.stdout, td)
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
# tier branch -- main or staging -- ended "commit, then land it"
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
    base), or, for a person on the ladder, on the harness's own branch name;
    None on any other branch or when it cannot be read."""
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
    if cur in tiers:
        return (f"This checkout is on {cur}, a tier branch. Before committing, move "
                f"the staged update onto a branch of its own (it carries the staged "
                f"diff as it is): {SWITCH_COMMAND}")
    return None


# GOING LIVE (2026-10-28). On the ladder, DONE's "land it on your landing
# branch" put the update on staging and the session stopped there, so it
# never reached main without a second command. Morgan: "I just want to run a
# command and have it update and go live" (strength: decided). The ladder
# set's vendor-update-on-the-ladder makes the phrase carry the move into main;
# DONE says so where the session reads its next step.
def live_line(repo):
    """-> the line DONE prints when the update lands below main for a person
    on the ladder: the move into main follows; None otherwise."""
    if repo is None or pb.ladder_in_force(repo) is not True:
        return None
    try:
        landing = pb.landing_branch(repo)[0]
    except Exception:                                        # noqa: BLE001
        return None
    if not landing or landing == pb.MAIN:
        return None
    return (f"Then take it live: once it is on {landing}, move {landing} into "
            f"{pb.MAIN} -- the phrase carries that too "
            f"(vendor-update-on-the-ladder). It moves everything waiting on "
            f"{landing}, so name what else goes live with the update.")


def _person_is_code_owner(repo):
    """True when the person running the update is one of `repo`'s code
    owners; False in doubt (precedent_audience)."""
    if repo is None:
        return True
    try:
        import precedent_audience
        return bool(precedent_audience.is_code_owner(repo)[0])
    except Exception:                                             # noqa: BLE001
        return False


class Report:
    def __init__(self):
        self.steps = []   # (name, one-line outcome)
        self.left = []    # (what, why)
        self.loud = []    # workflows left alone -- printed first and last
        self.details = {} # what -> lines printed under its Left-for-you item
        self.upstream_changes = ''  # upstream_changes_block, printed on close
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
        self.old_agents = None   # HEAD's AGENTS.md, read before anything writes
        self.earlier = set() # of `before`, what an earlier run staged, unchanged
        self.migration_notes = {}  # header -> lines, from each migration; every outcome
        self.commit_note = None  # a --take-anyway: said in the commit message
        self.code_warning = None  # the code this run ran may be older than its data

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

    def _migration_notes(self):
        # Said in every outcome: what a migration did (a merge it pushed, a
        # link that is the person's to act on) has happened by then.
        for header, lines in self.migration_notes.items():
            if lines:
                print(f"\n{header}")
                for line in lines:
                    print(f"  {line}")

    def _commit_note(self):
        if self.commit_note:
            print(f"\nCOMMIT MESSAGE: say this in it, in these words: "
                  f"{self.commit_note}")
        outside = rewritten_outside_vendored(self.repo or self.pin_repo)
        if outside:
            print("\nCOMMIT MESSAGE: name each of these in it -- files this update "
                  "rewrote outside the vendored trees, which nobody reading the "
                  "commit would guess it touched:")
            for line in outside:
                print(f"  {line}")

    def _pinned(self):
        if self.pin:
            _repo, commit, branch = self.pin
            print(f"\nPINNED: a rerun takes {branch} @ {commit[:12]} again, the "
                  f"commit this update started from, until a run reports DONE "
                  f"-- so the target does not move while you work what is "
                  f"left. To take {branch}'s newest commit instead, run it "
                  f"with --move.")

    def _upstream_review(self):
        # What the update met, less what this branch's commits already
        # record, with the lines for the commit that lands it. Only on the
        # ladder and only for a code owner (ur.prepare answers None
        # otherwise, and nothing is printed). A local edit still local or
        # merged is an item: it is the fix that belongs upstream. Printed on
        # DONE only -- a LEFT or FAILED update runs again.
        if self.pin_repo is None:
            return
        # The review is a set's (step_review in its precedent-source.json,
        # 2026-10-17); with no set providing one there is nothing to show.
        import precedent_resolve as _pr
        ur = _pr.load_set_tool(self.pin_repo, 'step_review')
        if ur is None:
            return
        extra = [f'local edit {outcome}: {rel} -- {text}'
                 for outcome, rel, text in self.edits
                 if outcome in (le.STILL_LOCAL, le.MERGED)]
        extra += [f'WARNING: {w}' for w in self.warnings]
        try:
            new, old = ur.prepare(self.pin_repo, 'update', '\n'.join(OUTPUTS), extra)
        except Exception:                                      # noqa: BLE001
            return
        if new is None:
            return
        print()
        for line in ur.report('update', new, old, 'commit'):
            print(line)

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
            record_asked(self.repo or self.pin_repo,
                         asked_paths(self.left, self.repo or self.pin_repo))
        if self.loud:
            self._banner()
        print("\n== Update Vendors ==")
        if not _person_is_code_owner(self.repo or self.pin_repo):
            print("  FOR YOU, NOT THE PERSON: they are not one of this "
                  "repository's code owners, so none of this report reaches "
                  "them. Settle what you can; tell them only, in everyday "
                  "words, whether their project is up to date and whether "
                  "someone who looks after it needs to step in "
                  "(practice: inner-workings-for-code-owners).")
        if self.code_warning:
            # First, in every outcome: a stop read without it is the
            # misdiagnosis the driver bootstrap exists to prevent.
            print(f"  WARNING: {self.code_warning}")
        for name, outcome in self.steps:
            print(f"  {name}: {outcome}")
        self._local_edits()
        self._questions()
        self._migration_notes()
        if self.upstream_changes and not failed:
            print('\n' + self.upstream_changes.rstrip())
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
        self._upstream_review()
        switch = feature_branch_line(self.pin_repo)
        if self.asks:
            print("\nDONE -- nothing left for this repo to decide. Ask the "
                  "question(s) above, review the staged diff, commit, then land "
                  "it the way this repository lands work.")
        elif staged_workflows(self.pin_repo):
            print("\nDONE -- nothing left to decide. Review the staged diff "
                  "and commit. It changes a CI workflow ("
                  + ", ".join(staged_workflows(self.pin_repo)) + "), so it "
                  "takes a pull request into your landing branch, not a direct "
                  "landing: a workflow runs on this repository's own Actions, "
                  "and only a run there shows it works here. Push the branch, "
                  "open the pull request, and merge it once its checks pass.")
        else:
            print("\nDONE -- nothing left to decide. Review the staged diff, "
                  "commit, then land it on your landing branch.")
        if switch:
            print(switch)
        live = live_line(self.pin_repo)
        if live:
            print(live)
        self._commit_note()
        print(MERGE_HEAD_NOTE)
        if self.not_run:
            print(self.not_run)
        return DONE


# Where an update is expected to write: the vendored catalogue, the engine,
# and the practice files the catalogue materializes. Anything else it
# rewrites is news to whoever reads the commit. On 2026-09-15 an update
# replaced a consumer's hand-written MAP.md and GLOSSARY.md with generated
# ones under a message that named neither, and the loss went unnoticed for a
# month (a consumer's root-issues report, 2026-10-19).
VENDORED_PREFIXES = ('process/upstream/', 'tools/')
MATERIALIZED_PREFIX = 'practices/'


def rewritten_outside_vendored(repo):
    """-> lines naming every staged file outside VENDORED_PREFIXES, with git's
    status letter; the materialized practices/ files as one line with their
    count."""
    if repo is None:
        return []
    r = subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--name-status',
                        '--no-renames'], capture_output=True, text=True)
    if r.returncode != 0:
        return []
    # A section 0 install vendors its catalogue wherever precedent.json's
    # universal source says (precedent/universal/ by default), and that tree
    # is exactly as vendored as tools/. Left out, every practice upstream
    # changed was listed one by one as a file "outside the vendored trees"
    # (very deep check pass 1, 2026-10-31 update rehearsal).
    prefixes = VENDORED_PREFIXES
    universal = universal_catalogue_path(pathlib.Path(repo))
    if universal:
        prefixes = prefixes + (universal.rstrip('/') + '/',)
    out, practices = [], 0
    for line in r.stdout.splitlines():
        status, _tab, rel = line.partition('\t')
        if not rel or rel.startswith(prefixes):
            continue
        if rel.startswith(MATERIALIZED_PREFIX):
            practices += 1
            continue
        out.append(f"{status[:1]} {rel}")
    if practices:
        out.append(f"{MATERIALIZED_PREFIX} ({practices} practice file(s) "
                   f"materialized from the sources)")
    return out


def staged_workflows(repo):
    """-> the staged .github/workflows/ files, for DONE to say the update
    takes a pull request (2026-10-16: an update bringing a new workflow was
    landed straight on staging because DONE said "land it")."""
    if repo is None:
        return []
    r = subprocess.run(['git', '-C', str(repo), 'diff', '--cached', '--name-only',
                        '--', '.github/workflows/'], capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()] if r.returncode == 0 else []


def run(argv, cwd):
    r = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    if not _is_git(argv):
        OUTPUTS.append(r.stdout + r.stderr)
    return r.returncode, r.stdout + r.stderr


def _is_git(argv):
    """Is `argv` a git command? What git prints is data -- a file's
    content, a hash, a log -- never a message from a step, so the upstream
    review never reads it. 2026-10-11: `git show HEAD:tools/
    precedent_branches.py` put the whole engine source into the review, and
    a consumer's Update Vendors listed 22 lines of it ("say(f'could not
    create ...')") as warnings to judge, out of 29."""
    return bool(argv) and pathlib.Path(str(argv[0])).name in ('git', 'git.exe')


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


def kept_older_note(line, follow, newest, taken, take=None):
    """-> the engine line, saying plainly when it is not the newest `follow`.

    2026-10-18: the newest main's test was still running, so this command
    kept the last tested one and the engine line read a bare "already
    current with main @ 1a426298cd85". A session took that for a bug, ran
    the refresh by hand and vendored the untested commit. The line now says
    why it is not the newest, in its own words."""
    if take or not newest or not taken or newest == taken:
        return line
    return (f"{line} -- the newest {follow}, {newest[:12]}, has no passing "
            f"GitHub test yet, so this kept {taken[:12]}; a rerun takes the "
            f"newer one once its test passes")


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
            m = (re.match(r'(.+?) (?:\((?:line \d+|in [^)]+)\) )?has local edits', body)
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
        if 'an individual set' in found:
            # An individual set comes from a person's own user config; no
            # repository declares one, so "Declare it in precedent.json" was
            # advice nobody could take (2026-10-17).
            rep.ask('IN FORCE NOWHERE',
                    f'{found} -- it binds nowhere in this repo, and only for '
                    f'the person whose individual set carries it; no '
                    f'precedent.json can declare that set. Record that it does '
                    f'not apply here: "{NOT_IN_FORCE_KEY}": {{"{slug}": "<why>"}}, '
                    f'or ask for it to come back to universal')
            continue
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


def _harness_diff(repo):
    r = subprocess.run(['git', '-C', str(repo), 'diff', 'HEAD', '--name-only',
                        '--', '.claude/'], capture_output=True, text=True)
    return {n for n in r.stdout.splitlines() if n}


def _content_hashes(repo, paths):
    import hashlib
    out = {}
    for rel in sorted(paths):
        f = pathlib.Path(repo) / rel
        out[rel] = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
    return out


# THE GO-AHEAD IS KEPT WITH WHAT IT APPROVED (2026-10-19). The person's words
# reached the update only as HARNESS_GO_AHEAD in one run's environment, and
# the baselines they unlock were re-recorded near the end of that run. Two
# consuming repositories' runs stopped before the end, the words were gone,
# and the practice audit failed settings.json as DRIFT until it was
# re-recorded by hand. Now the run that has the words writes them into the
# update's record, keyed to the content they approved, and re-records those
# baselines at once; a rerun on the same content reads them back.
def record_harness_go_ahead(repo, words, paths):
    data = _read_record(repo)
    data['harness_go_ahead'] = {'words': words, 'paths': _content_hashes(repo, paths)}
    _write_record(repo, data)


def harness_go_ahead(repo):
    """-> the person's words for the .claude/ change in the tree now: this
    run's HARNESS_GO_AHEAD, else the words an earlier run recorded for
    exactly this content, else ''."""
    words = os.environ.get(HARNESS_GO_AHEAD, '').strip()
    if words:
        return words
    kept = _read_record(repo).get('harness_go_ahead') or {}
    diff = _harness_diff(repo)
    if diff and isinstance(kept, dict) and kept.get('words') and \
            kept.get('paths') == _content_hashes(repo, diff):
        return str(kept['words'])
    return ''


def held_harness_paths(repo):
    """-> the .claude/ paths this run changed from HEAD while the person's
    words for them are not given (harness_go_ahead): what the update asks
    about and may not commit yet, so their baselines wait for the run that
    has the words (rebaseline_vendored_entries' `hold`)."""
    if harness_go_ahead(repo):
        return set()
    return _harness_diff(repo)


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
    # The read-only tool rules a refresh adds (2026-10-14,
    # pve._apply_read_only_allow): said by name, so the yes is to what it is.
    try:
        allow = lambda t: ((json.loads(t) if t else {}).get('permissions') or {}).get('allow') or []
        more = [r for r in allow(now) if r not in allow(was)]
    except (ValueError, AttributeError, TypeError):
        more = []
    if more:
        broad = pve.ENGINE_ALLOW_RULE in more
        ro = all(pve.is_read_only_allow_rule(r) for r in more)
        cases.append(f'settings.json allows {len(more)} more '
                     + ('Precedent tool ' if ro else '')
                     + f'command(s): {", ".join(more)}'
                     + (' -- the first covers every engine tool'
                        if broad else ''))
    # The rules that always ask (2026-10-17): said by name too.
    try:
        ask = lambda t: ((json.loads(t) if t else {}).get('permissions') or {}).get('ask') or []
        asks = [r for r in ask(now) if r not in ask(was)]
    except (ValueError, AttributeError, TypeError):
        asks = []
    if asks:
        cases.append(f'settings.json makes {len(asks)} command(s) always ask the '
                     f'person first: {", ".join(asks)}')
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


# What each kind of .claude/ change is called in the sentence the person
# says to approve it: (pattern on a harness_cases() line, short name).
_APPROVAL_NAMES = (
    (re.compile(r'^settings\.json allows '), 'allow-list'),
    (re.compile(r'^settings\.json (gains|drops|rewrites)'), 'hook wiring'),
    (re.compile(r'becomes the permanent stub|hook stub itself'), 'hook stub'),
    (re.compile(r'^a (new )?hook file'), 'hook file'),
    (re.compile(r'^a hook that is not yet a stub'), 'hook'),
)


def harness_approval(paths, last=False, cases=None):
    """-> the sentence the person says to approve the commit of these
    .claude/ changes, naming the files and the change.

    WHY (2026-10-15, a consumer's Update Vendors). The question asked for a
    yes; the person answered "Yes approved. Booked" and auto mode still
    refused the commit of .claude/settings.json as [Self-Modification]. His
    next words, "Commit the .claude/settings.json allow-list change", went
    through first time. Auto mode clears an action only on words that name
    it, the same as the merge, so the report hands the session those words
    rather than a yes-or-no question. The gotcha:
    gotchas/gotcha-2026-10-15-auto-mode-clears-only-words-that-name-the-action.md"""
    files = ' and '.join(paths) if len(paths) <= 2 else f'{len(paths)} .claude/ files'
    if last:
        return f'Commit the {files} change that makes the hooks permanent stubs'
    kinds = []
    for case in cases or ():
        name = next((n for rx, n in _APPROVAL_NAMES if rx.search(case)), 'settings')
        if name not in kinds:
            kinds.append(name)
    kind = ' and '.join(kinds) if kinds else 'hooks and settings'
    return f'Commit the {files} {kind} change'


ENGINE_MANIFEST_REL = 'tools/ENGINE_MANIFEST.json'


def _head_json(repo, rel):
    text = _git_show(repo, f'HEAD:{rel}')
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def hold_hook_hashes(repo, paths, approved):
    """-> [hook names] whose hash in tools/ENGINE_MANIFEST.json this call set.

    WHY (2026-10-17, a document project's update). The refresh writes the
    NEW hooks' hashes into the engine manifest at once, while the hooks
    themselves wait on the person's words. Committed without the hooks, as
    the question invited, the manifest named content the files did not
    have, and the next run called the 14 old hooks "your local edit" and
    would not replace them. So while the words are missing, a held hook's
    hash goes back to the one HEAD records (or out, for a hook HEAD did not
    have); the run that has the words records each staged hook's own hash.
    Either way the manifest is re-staged, so what is committed agrees with
    itself."""
    import hashlib
    hooks = sorted({pathlib.PurePosixPath(p).name for p in paths
                    if p.startswith('.claude/hooks/')})
    mf = pathlib.Path(repo) / ENGINE_MANIFEST_REL
    if not hooks or not mf.is_file():
        return []
    try:
        data = json.loads(mf.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    hashes = dict(data.get('hooks_sha256') or {})
    head = (_head_json(repo, ENGINE_MANIFEST_REL) or {}).get('hooks_sha256') or {}
    done = []
    for name in hooks:
        if name not in hashes and name not in head:
            continue
        if approved:
            f = pathlib.Path(repo) / '.claude' / 'hooks' / name
            want = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
        else:
            want = head.get(name)
        if hashes.get(name) == want:
            continue
        if want is None:
            hashes.pop(name, None)
        else:
            hashes[name] = want
        done.append(name)
    if done:
        data['hooks_sha256'] = hashes
        mf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                      encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '--', ENGINE_MANIFEST_REL],
                       capture_output=True, text=True)
    return done


def harness_baselines(repo, paths):
    """-> ([path], [path]): the held .claude/ paths that have a recorded
    baseline (a synced entry in process/manifest.json, or a hook's hash in
    the engine manifest), and those that have none -- so the question says
    what the go-ahead run records, never a baseline that does not exist
    (2026-10-17: a consumer's .claude/settings.json had none, and the
    question promised one)."""
    repo = pathlib.Path(repo)
    entries = set()
    try:
        data = json.loads((repo / 'process' / 'manifest.json').read_text(encoding='utf-8'))
        entries = {str(e.get('local_path') or '') for e in data.get('entries') or []
                   if e.get('status') == 'synced' and e.get('local_sha256')}
    except (OSError, ValueError):
        pass
    try:
        hooks = set((json.loads((repo / ENGINE_MANIFEST_REL).read_text(
            encoding='utf-8')).get('hooks_sha256') or {}))
    except (OSError, ValueError):
        hooks = set()
    has, none = [], []
    for p in paths:
        named = p in entries or (p.startswith('.claude/hooks/')
                                 and pathlib.PurePosixPath(p).name in hooks)
        (has if named else none).append(p)
    return has, none


def harness_ask(paths, last=False, cases=None, gates=None, baselines=None):
    """The question for the person when an update changes hooks or settings.
    `last`: this is the update that turns the hooks into permanent stubs, so
    the question says, in plain words, that it is the last one. `cases`:
    harness_cases(), so any other question says which kind of change it is
    rather than only that something under .claude/ moved. `gates`:
    harness_new_gates(), each hook newly wired and what it does -- so the
    question never says nothing new is blocked when something is. It ends on
    harness_approval()'s sentence: a bare yes does not clear the commit."""
    new = ''
    if gates:
        new = (f'It also wires {len(gates)} hook(s) this repository did not '
               f'run before, and each can refuse what it names: '
               + '; '.join(f'{n} ({e}): {w}' for n, e, w in gates) + '. ')
    say = harness_approval(paths, last=last, cases=cases)
    has, none = baselines if baselines is not None else (list(paths), [])
    records = []
    if has:
        records.append(f'records the new baselines of {", ".join(has)}')
    if none:
        records.append(f'has no baseline to record for {", ".join(none)} '
                       f'(none is kept for it)')
    approve = (f'Claude Code\'s auto mode lets this commit through only on the '
               f'person\'s words naming it, never on a bare yes, so tell them '
               f'what changes and give them the sentence, not a yes-or-no '
               f'question. To approve, say: "{say}". Then run this update '
               f'again with {HARNESS_GO_AHEAD}="<their words>": that run '
               f'{" and ".join(records) or "stages them"}. In auto mode the '
               f'rerun can still be refused as self-modification even with their '
               f'words; then the person approves the one permission prompt, or '
               f'switches to default permissions for it -- the sentence alone '
               f'is not always enough. Get the words before committing: '
               f'committed without these files, the repository\'s push check '
               f'can refuse the push, because the hooks the view sync writes '
               f'no longer match the committed ones. Left out, the change is '
               f'offered again on the next update')
    if last:
        blocked = (new if gates else
                   'Nothing changes about when anything is blocked. ')
        return (f'this update changes {len(paths)} file(s) under .claude/ one '
                f'last time: each hook becomes a permanent pointer to the '
                f'engine, and settings.json gains one fixed entry per event '
                f'for hooks added later. {blocked}From now on hook changes '
                f'arrive with the engine without this question. {approve}. '
                f'Files: {", ".join(paths)}')
    what = f' -- {"; ".join(cases)}' if cases else ''
    return (f'this update changes {", ".join(paths)}{what}. {new}{approve}')


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


def stage_late_output(repo, before):
    """Stage what this run wrote after its `staged` step, and nothing that
    was uncommitted when it started. -> the paths it staged.

    WHY (2026-10-10, a consumer). The records step, added that day, moved a
    record from process/retired_vocabulary.json into precedent.json after
    every path had been staged; the update said DONE with both files
    modified and unstaged, and a session committing what was staged would
    have left the move behind. A step added after the staging step can
    always do this, so the update stages late output once more, at the end,
    rather than trusting each step to remember."""
    r = subprocess.run(['git', '-C', str(repo), 'diff', '--name-only', '-z'],
                       capture_output=True, text=True)
    u = subprocess.run(['git', '-C', str(repo), 'ls-files', '--others',
                        '--exclude-standard', '-z'], capture_output=True, text=True)
    loose = {x for x in (r.stdout + u.stdout).split('\0') if x}
    late = sorted((loose & dirty_paths(repo)) - set(before))
    for i in range(0, len(late), 200):
        subprocess.run(['git', '-C', str(repo), 'add', '-A', '--', *late[i:i + 200]],
                       capture_output=True, text=True)
    return late


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


def _changed_paths(repo, cached=False):
    """-> the set of paths `git diff [--cached]` reports in `repo`: what
    `git diff [--cached] --quiet -- PATH` fails on, for every path at once.
    One process instead of one per file: the per-file calls were 1,490 of
    4,710 git processes in one Update Vendors test (2026-10-29).
    --no-renames, so a staged rename names both paths, as the per-path
    form judges each."""
    r = subprocess.run(['git', '-C', str(repo), 'diff', '--name-only', '-z',
                        '--no-renames', *(['--cached'] if cached else [])],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return {p for p in r.stdout.split('\0') if p}


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
    unstaged = _changed_paths(repo)
    kept = {p: _content_hash(repo / p) for p in sorted(paths)
            if (p not in unstaged if unstaged is not None
                else g('diff', '--quiet', '--', p).returncode == 0)}
    if kept:
        data['staged'] = kept
    else:
        data.pop('staged', None)
    _write_record(repo, data)


def asked_paths(left, repo):
    """-> the repo files a LEFT FOR YOU list names, each item's leading
    path (`AGENTS.md "### Two check levels"`, `local/x.md:142`), kept only
    where the file exists."""
    out = set()
    for what, _why in left or ():
        m = re.match(r'([\w.][\w./-]*?)(?=:\d|\s"|\s|$)', str(what))
        if m and (repo / m.group(1)).is_file():
            out.add(m.group(1))
    return sorted(out)


def record_asked(repo, paths):
    """Write down the files a LEFT FOR YOU run asked the person to edit,
    under the record's `asked` key; a run that asks nothing clears it."""
    data = _read_record(repo)
    if paths:
        data['asked'] = sorted(paths)
    else:
        data.pop('asked', None)
    _write_record(repo, data)


def earlier_asked(repo):
    """-> the files the last run of this update asked the person to edit.

    WHY (2026-10-11, a consuming repository). The first run stopped LEFT FOR
    YOU on two AGENTS.md sections and some template wording; the person
    edited them as asked, and the rerun took those edits for a local change
    of theirs -- AGENTS.md had an unstaged change on top, so it was neither
    this run's output nor the earlier run's -- left the classic manifest's
    old hash, and the basic check failed it as DRIFT. An edit that answers
    the update's own question is part of the update, so its file's baseline
    is re-recorded with the rest (rebaseline_vendored_entries)."""
    return set(_read_record(repo).get('asked') or ())


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
    unstaged, staged = _changed_paths(repo), _changed_paths(repo, cached=True)
    for rel in sorted(set(before) & set(known)):
        if _content_hash(repo / rel) != known[rel]:
            continue
        if (rel in unstaged if unstaged is not None
                else g('diff', '--quiet', '--', rel).returncode != 0):
            continue        # an unstaged change on top: someone's
        if (rel not in staged if staged is not None
                else g('diff', '--cached', '--quiet', '--', rel).returncode == 0):
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
                      f'not in {CLONE}, so it starts from the tip')
    if tip and tip != commit:
        return commit, (f'pinned: the commit this update started from. {follow} '
                        f'has moved on to {tip[:12]}; --move takes it, or the '
                        f'newest commit before it whose GitHub test passed')
    return commit, 'pinned: the commit this update started from, still the tip'


def clear_pin(repo):
    data = _read_record(repo)
    had = [data.pop(k, None) for k in ('pin', 'dropped_sets')]
    if any(h is not None for h in had):
        _write_record(repo, data)


def record_dropped_sets(repo, names):
    """Write down, in the run-to-run record, the sets this run dropped from
    precedent.json, so a rerun after LEFT FOR YOU still counts them as the
    update's own drop (sets_this_update_dropped). Cleared with the pin."""
    data = _read_record(repo)
    data['dropped_sets'] = sorted(set(data.get('dropped_sets') or ()) | set(names))
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
    # The engine's own workflow files are its output too (CI_CONVERGES_KINDS),
    # and must go back with it: a rerun puts tools/ back to HEAD, so the
    # repo's OLD engine runs first, and a workflow the earlier run added
    # that its list lacks reads to it as unshipped and unapproved -- left
    # for the person, the update never DONE (2026-10-16, a consumer taking
    # precedent-branch-cleanup.yml). Put back, the new engine writes it again.
    shipped = {rel for rows in pve.CI_WORKFLOW_TEMPLATES.values() for _t, rel in rows}
    # A copied-in set is a mirror too, but nothing writes it again from HEAD:
    # its refresh copies only a set that moved or has no record, and its
    # record (process/manifest_<set>.json) is outside its folder, so it is
    # never put back with it. Put back, an uncommitted copy was deleted and
    # its record kept, and the set read as copied and empty (2026-10-19, a
    # voice pack in a consumer).
    copies = tuple(p.rstrip('/') + '/' for p in copied_in_paths(repo))
    return [p for p in paths if not p.startswith(copies) and (
            p.startswith(engine) or p == 'process/manifest.json'
            or p in declared or p in shipped)]


def copied_in_paths(repo):
    """-> the folders precedent.json, as committed or as the run left it,
    declares as copied-in sets (`"vendored": true`)."""
    out = set()
    for spec in ('HEAD:precedent.json', None):
        try:
            text = (subprocess.run(['git', '-C', str(repo), 'show', spec],
                                   capture_output=True, text=True).stdout if spec
                    else (repo / 'precedent.json').read_text(encoding='utf-8'))
            for e in (json.loads(text) or {}).get('sources') or []:
                if isinstance(e, dict) and e.get('vendored') is True and e.get('path'):
                    out.add(str(e['path']).strip('/'))
        except (OSError, ValueError, AttributeError):
            pass
    return sorted(p for p in out if p not in ('', '.'))


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
    unstaged = _changed_paths(repo)
    for rel in sorted(select(repo, paths)):
        f = repo / rel
        if _content_hash(f) != paths[rel] or (
                rel in unstaged if unstaged is not None
                else g('diff', '--quiet', '--', rel).returncode != 0):
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


# THE SESSION-START REFRESH BRANCH IS THIS UPDATE'S TO CLEAR (2026-11-01).
# In a practice set, session start's precedent_refresh_sources.py commits the
# engine refresh on a local branch of its own and leaves the set's base clean,
# for "Update Vendors in this set" to land. This command then wrote the same
# engine again and staged it on the base, so the refresh branch was never
# landed and never removed: every run left one more local branch, never
# pushed, which every archive check then had to reason about. Once the update
# has staged the engine, each branch carrying nothing but a refresh commit
# (precedent_container_safe.refresh_only_branches, strict) holds engine
# output this update has just written again, so it goes, and is said.
def superseded_refresh_step(repo, rep):
    """Clear the local refresh-only branches the update supersedes; one
    step line when any went."""
    try:
        import precedent_container_safe as pcs
        removed = pcs.clear_refresh_only_branches(repo, 'HEAD')
    except Exception:                                        # noqa: BLE001
        return []
    if removed:
        rep.step('superseded refresh', f'removed {len(removed)} local '
                 f'branch(es) holding only the engine refresh session start '
                 f'committed, which this update has just staged again: '
                 + ', '.join(removed))
    return removed


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


def citations(repo, rev=None):
    """-> ([(where, why)] to fix, [where] to read), or None when the lookup
    could not run. Asks the SOURCE clone's copy of the lookup, for the same
    reason every other step here does: it is the current code. With `rev`,
    a line that is word for word a line of the current AGENTS.md template
    (at `rev`) is left out: it is upstream's wording, which the refresh
    keeps, not this repository's (2026-10-17, very deep check: every
    consumer's update listed two such lines to read)."""
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
    stock = {}
    for tmpl in (pve.agents_md_templates(repo, 'consumer') or ())[:1]:
        text = _source_text(rev, tmpl) if rev else None
        if text:
            stock['AGENTS.md'] = {l.strip() for l in text.splitlines() if l.strip()}
    return citation_findings(data, _engine_owned(repo),
                             stock=_stock_line_test(repo, stock))


def _stock_line_test(repo, stock):
    """-> is_stock(file, line_no): whether that line of the repo's `file`
    is, stripped, one of the template lines `stock` holds for it."""
    cache = {}

    def is_stock(rel, n):
        lines = stock.get(rel)
        if not lines:
            return False
        if rel not in cache:
            try:
                cache[rel] = (pathlib.Path(repo) / rel).read_text(
                    encoding='utf-8').splitlines()
            except (OSError, UnicodeDecodeError):
                cache[rel] = []
        text = cache[rel]
        try:
            return 0 < int(n) <= len(text) and text[int(n) - 1].strip() in lines
        except (TypeError, ValueError):
            return False
    return is_stock


def citation_findings(data, engine=frozenset(), stock=None):
    """-> ([(where, why)] to fix, [where] to read) from
    precedent_practice_refs.py's JSON, leaving out the paths in `engine`
    and every line `stock(file, line)` says is upstream's template wording."""
    fix, read = [], []
    slugs, successors = data.get('slugs', {}), data.get('successors', {})
    for h in data.get('hits', []):
        if h.get('source') != 'this repository' or h.get('kind') != 'live':
            continue
        if stock is not None and stock(h.get('file'), h.get('line')):
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
        elif slugs.get(h['slug'], '').startswith('Rule reworded'):
            # Its title and index_clause, the one line a citation
            # paraphrases, did not change: the Rule only grew or was
            # reworded under it, so the citation still reads true
            # (precedent_practice_refs.RULE_BODY_ONLY; 2026-10-15, a
            # consumer sent to read two such citations, both still correct).
            continue
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


def adopt_listed_records(repo, flagged):
    """Move each file the citations step `flagged` that process/
    retired_vocabulary.json's exempt_files names into precedent.json's
    record_paths, and take it off exempt_files -> [the paths moved].

    WHY (2026-10-10, a consumer; Morgan: "that is a good suggestion for
    upstream"). A file could be declared history in two places, each read
    by its own check: the citation check flagged six old practice names in
    a migration record that the old-names scrub already exempted, and
    silencing both meant naming the file twice -- two declarations of one
    fact, which drift. record_paths is now the one list (the scrub reads it
    too), so an entry the person already made is carried over: their
    declaration, moved, never a guess. Only an exact file the citation step
    flagged moves: a directory entry (a materialized tree) and a live file
    exempt for another reason (an open item that must name a retired
    secret) are not records, and stay.
    precedent.json is rewritten only where it reads back byte for byte as
    two-space JSON, and the registry only in a layout it reads back in
    (two-space or one line); otherwise that file is left as it is."""
    root = pathlib.Path(repo)
    vpath, cpath = root / 'process' / 'retired_vocabulary.json', root / 'precedent.json'
    try:
        vtext, ctext = vpath.read_text(encoding='utf-8'), cpath.read_text(encoding='utf-8')
        vocab, cfg = json.loads(vtext), json.loads(ctext)
    except (OSError, ValueError):
        return []
    if not (isinstance(vocab, dict) and isinstance(cfg, dict)):
        return []

    def dumps(obj):
        return json.dumps(obj, indent=2, ensure_ascii=False) + '\n'
    if dumps(cfg) != ctext:
        return []
    exempt = vocab.get('exempt_files') or []
    records = cfg.get('record_paths') or []
    have = {(e.get('path') if isinstance(e, dict) else e) for e in records}
    moved = [e for e in exempt if isinstance(e, str) and e in flagged
             and e not in have and (root / e).is_file()]
    if not moved:
        return []
    reason = ('a dated record, kept as written: listed in process/'
              'retired_vocabulary.json\'s exempt_files as a file where the '
              'retired names stay, and moved here by Update Vendors so it is '
              'declared once')
    cfg['record_paths'] = list(records) + [{'path': m, 'reason': reason} for m in moved]
    cpath.write_text(dumps(cfg), encoding='utf-8')
    for shape in (dumps, lambda o: json.dumps(o, ensure_ascii=False) + '\n',
                  lambda o: json.dumps(o, ensure_ascii=False)):
        if shape(vocab) == vtext:           # its own layout, kept
            vocab['exempt_files'] = [e for e in exempt if e not in moved]
            vpath.write_text(shape(vocab), encoding='utf-8')
            break
    return moved


def record_paths_hint(read):
    """-> how to stop a dated record being listed again, naming the files
    the read list points into, or ''.

    WHY (2026-10-10, a consumer's update). Six of its seven citations were
    in its 2026-09-24 migration record, correct as written and never to
    change, and nothing said how to stop them coming back at every update.
    A file declared in precedent.json's record_paths is history to this
    lookup (precedent_practice_refs.py); nothing is guessed from a name."""
    files = sorted({w.split(':', 1)[0] for w in read
                    if w.split(':', 1)[0].endswith('.md')})
    if not files:
        return ''
    return (f'. If {", ".join(files)} {"is" if len(files) == 1 else "are"} a '
            f'dated record that stays as written, list it in precedent.json\'s '
            f'record_paths ({{"path": ..., "reason": ...}}) and it is not '
            f'listed again')


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
    # staging is the ladder's words in their session.
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
        rep.leave('branch tiers', 'staging could not be made on origin -- '
                  + ' '.join(tier_lines)[-400:])
    else:
        rep.step('branch tiers', '; '.join(made) if made else
                 'staging and main both present')


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


def _why_not_newer(skipped, details=None):
    """-> "GitHub's test is still running on X and failed on Y" for the
    newer commits passed over, newest first, grouped by state. A commit
    still being tested carries where (`details`, sha -> github_test_state's
    detail): its own run can be finished while its pull request's decides."""
    groups = {}
    for sha, state in skipped:
        where = (details or {}).get(sha) if state == 'running' else None
        groups.setdefault(state, []).append(sha[:12] + (f' ({where})' if where else ''))
    parts = []
    for state, shas in groups.items():
        named = ', '.join(shas[:3]) + (f' and {len(shas) - 3} more' if len(shas) > 3 else '')
        parts.append(f'{_STATE_WORDS.get(state, state + " on")} {named}')
    return "GitHub's test " + ' and '.join(parts)


def _attach_remedy(detail):
    """-> how to give this session GitHub access to the source, when
    `detail` says it has none; '' otherwise (github_budget.attach_remedy)."""
    try:
        import github_budget as _gb
    except ImportError:
        return ''
    return _gb.attach_remedy(detail, pb._slug(SOURCE) or 'alex137/BestPractice')


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
            out['failed'] = f'{TAKE_FLAG} {take}: no such commit in {CLONE}'
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
    details = {}
    for sha in commits:
        if marked and _tree(sha) in marked:
            state, detail = 'passed', 'its passed marker'
        else:
            state, detail = main_test_state(sha, tests)
        details[sha] = detail
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
                # No attach advice here (2026-10-17, a consumer's session):
                # the commit taken is the newest with a recorded pass, which
                # is right, and the advice pushed a read-only session toward
                # a push grant only to read a public check's status.
                unread = any(st == 'unmarked' for _s, st in skipped)
                out['step'] = (f"took {follow} @ {sha[:12]}"
                               + (", the newest with a recorded pass" if unread else '')
                               + f", {n} commit"
                               f"{'s' if n != 1 else ''} behind the newest {follow}, "
                               f"{tip[:12]}, because {_why_not_newer(skipped, details)}. This "
                               f"repo gets the newer ones once their test passes")
            return out
        if state == 'unknown':
            if not skipped:
                again = ("Run it again once GitHub answers")
                fix = _attach_remedy(detail)
                if fix:
                    # The session has no GitHub access to the source: no
                    # wait fixes that, attaching it does (practice:
                    # reach-or-ask).
                    again = fix[0].upper() + fix[1:]
                out['warning'] = (f"could not ask GitHub whether {follow}'s test "
                                  f"passed ({detail}), so this took the newest "
                                  f"{follow}, {tip[:12]}, without knowing. {again}")
                return out
            out['failed'] = (f"GitHub stopped answering ({detail}) while this "
                             f"looked for the newest {follow} whose test passed, "
                             f"after finding that {_why_not_newer(skipped, details)}. "
                             f"Nothing was taken. Run "
                             f"it again, or take a commit anyway in the person's "
                             f"own words with {TAKE_FLAG} <commit>")
            out['commit'] = None
            return out
        skipped.append((sha, state))
    if any(state == 'unmarked' for _, state in skipped):
        fix = _attach_remedy(unknown)
        out['warning'] = (f"could not ask GitHub whether {follow}'s test passed "
                          f"({unknown}), and none of {follow}'s newest "
                          f"{len(commits)} commits carries a passed marker, so "
                          f"this took the newest {follow}, {tip[:12]}, without "
                          f"knowing" + (f". {fix[0].upper() + fix[1:]}" if fix else ''))
        return out
    out['commit'] = None
    out['failed'] = (f"none of {follow}'s newest {len(commits)} commits passed "
                     f"GitHub's test: {_why_not_newer(skipped, details)}. Nothing was "
                     f"taken. Run it again once {follow}'s test passes, or take "
                     f"a commit anyway in the person's own words with "
                     f"{TAKE_FLAG} <commit>")
    return out


def update(repo, skip_check=False, ref=None, move=False, take=None, code=None,
           copy_in=None, answered_by='', take_sets=(), keep_workflows=()):
    rep = Report()
    rep.pin_repo = repo
    if code:
        # Which commit's code this run is, first (bootstrap).
        rep.step('code', code['line'])
        if code.get('warning'):
            rep.code_warning = code['warning']
            print(f"precedent_update: WARNING: {code['warning']}", flush=True)
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
    # Read before anything writes: the commands it listed (moved_commands_step).
    rep.old_agents = _git_show(repo, 'HEAD:AGENTS.md')
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
        # Held while it fetches: every repo's update fetches into this one
        # clone, and two at once lose a ref lock (precedent_clone_lock).
        try:
            with held(SOURCE):
                rc, out = run(['git', '-C', str(SOURCE), 'fetch', 'origin',
                               pve.tracking_refspec(follow)], SOURCE)
        except TimeoutError as e:
            rc, out = 1, str(e)
        if rc != 0:
            return rep.close(f"could not fetch origin/{follow} in "
                             f"{CLONE}:\n{tail(out, repo=repo)}")
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
    newest = None
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
    # Before the refresh, so its CI judgment reads the person's answer.
    for rel in keep_workflows:
        ok, what = pve.record_ci_keep(repo, rel, answered_by)
        (rep.step if ok else rep.leave)(*(('CI workflow', what) if ok
                                          else (rel, what)))
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
    rep.step('engine', kept_older_note(
        engine_summary(out, last_synced, follow=None if ref else follow,
                       tip=engine_ref),
        follow, newest, chosen.get('commit'), take))
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
    rep.upstream_changes = upstream_changes_block(repo, last_synced, tip)
    seeded, asks, followed = seed_engine_budgets(repo, tip, last_synced)
    if seeded:
        rep.step('API budgets', 'tools/github_api_budgets.json now budgets '
                 + ', '.join(f'{t} at {n} call(s) a run' for t, n in seeded)
                 + ' -- upstream\'s figure and note for a tool upstream ships; '
                 'change it there if this repo needs its own')
    if followed:
        rep.step('API budgets', 'tools/github_api_budgets.json follows '
                 'upstream for ' + ', '.join(f'{t} ({was} -> {now} call(s) a run)'
                                             for t, was, now in followed)
                 + ' -- this repo carried upstream\'s previous figure, not '
                 'one of its own')
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
        elif line.startswith(('RETIRED: ', 'MOVED: ')):
            # An AGENTS.md template section that became a practice, or one
            # compared where a reduction pass moved it (2026-10-31).
            rep.step(line.split(':', 1)[0].lower(), line.split(': ', 1)[1])
        elif line.startswith('precedent_vendor_engine refresh: REPLACED '):
            rep.step('replaced', line.split('REPLACED ', 1)[1])
        elif line.startswith(pve.KEEP_WORKFLOW_ASK):
            rep.ask('CI workflow', line[len(pve.KEEP_WORKFLOW_ASK):])
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
    copy_in_step(repo, rep, copy_in or {}, answered_by)

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
    # Morgan, 2026-09-27 (strength: decided): every repository gets a
    # default, set on its first update after that day; a person's own
    # identity.json still wins, and a value already here is never changed.
    # The default is staging.
    if pb.ensure_repo_landing(repo):
        rep.step('landing branch', f'{pb.LANDING_SETTING} set to '
                 f'{pb.REPO_LANDING_DEFAULT} in precedent.json (the repository '
                 f'default; a person\'s own identity.json still wins)')

    # A retired set is judged AFTER the catalogue: a rule it held may be
    # folded into universal by this very update, and judged before, against
    # the old catalogue, it read as "in force nowhere else" and the set was
    # kept (a consumer's update, 2026-10-06).
    dropped_sets = retired_sources_step(repo, rep)
    approved_workflows_step(repo, rep)

    # 3c. The migrations: each tools/migration_*.py moves a repository off
    # an arrangement the engine has dropped. Before the views, so they
    # render what a migration rewords.
    migrations_step(repo, rep)

    # 3d. The shared sets this repository copies in, refreshed the way the
    # catalogue is (spec/VENDORED_SHARED_SETS.md). Before the views, which
    # render their rules.
    refresh_copies_step(repo, rep, take_sets)

    # 4. The views. A refresh changes what the loader renders.
    #
    # A practice SET renders more than a consumer does: MAP.md and
    # GLOSSARY.md too, and MAP.md lists every engine file. Its deep check is
    # `build_views.py --check`, so an update that adds an engine file and
    # regenerates only the loader block fails its own gate. 2026-09-27: all
    # four of Morgan's sets stopped on exactly that, one new MAP.md row
    # each, fixed by hand. A set has no precedent_sync_views.py anyway --
    # so it gets the full build, the same one its check compares against.
    sets_before = set_pins(repo)
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
        caused = (removals_this_update_caused(
            out, sets_this_update_dropped(repo, dropped_sets)) if rc else [])
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
        gone = decommissioned_removals(out, head.strip() if head_ok else None) \
            if rc else []
        if gone:
            rc, out = take_decommissioned(
                repo, sync, gone, sets_this_update_dropped(repo, dropped_sets),
                rep)
        in_force_nowhere_step(repo, rep, out)
        removed_links_step(rep, out)
        hooks_not_here_step(rep, out)
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
    moved_commands_step(repo, rep, rep.old_agents, head.strip() if head_ok else None)

    # After the views, because the view sync writes harness adapters too.
    rebased = rebaseline_vendored_entries(
        repo, this_updates_output(repo, before, rep.earlier)
        | earlier_asked(repo), hold=held_harness_paths(repo))
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
    total = record_person_total(repo)
    if total:
        rep.step('session-load budget', total)
    raised = record_copy_in_budget(repo)
    if raised:
        rep.step('session-load budget', raised)
    if ensure_headroom_floor(repo):
        rep.step('session-load budget', f'headroom_floor_pct set to '
                 f'{HEADROOM_FLOOR_DEFAULT} in tools/session_load_budgets.json '
                 f'(the default; the full check requires the key)')

    # 4a. The branch tiers. A ladder repository works through staging ->
    # main, so a missing tier is
    # made here rather than reported (Morgan, 2026-09-27, strength: decided:
    # "Can we make sure update vendors checks for this and if they don't
    # exist create it"). ensure_tiers makes staging from the old
    # staging name if one is left, else from main. It
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
    path_moves, moves_note = engine_path_moves(SOURCE, last_synced, tip)
    if moves_note:
        rep.step('engine moves', moves_note)
    renamed = repoint_renamed_engine_paths(repo, path_moves)
    if renamed:
        rep.step('repointed', 'engine paths that moved now name their new '
                 'place: ' + ', '.join(
                     f'{rel} ({n} line{"s" if n != 1 else ""})'
                     for rel, n in renamed) + ' -- '
                 + '; '.join(f'{o} -> {n}' for o, n in path_moves.items()
                             if not (repo / o).exists() and (repo / n).exists()))
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
                 f'already held the pinned engine (an earlier Update Vendors run here, or a '
                 f'source refresh, wrote them and did not commit); '
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
    superseded_refresh_step(repo, rep)

    # Hooks and settings: said before the commit, never found at it
    # (2026-10-06). Claude Code's auto mode holds a commit that changes
    # .claude/ as self-modification, so an update that changed a hook got
    # all the way to the commit and stopped there. It is a question for the
    # person, not a call for the repo, so the update still finishes: the
    # question is printed in every outcome, ahead of the commit.
    harness = harness_changes(repo)
    if harness:
        words = harness_go_ahead(repo)
        rehashed = hold_hook_hashes(repo, harness, approved=bool(words))
        if words:
            # At the step the words are given, not at the end of the run.
            record_harness_go_ahead(repo, words, _harness_diff(repo))
            rebased = rebaseline_vendored_entries(repo, set(harness), hold=set())
            rep.step('hooks and settings', f'{", ".join(harness)} changed, with '
                     f'the person\'s go-ahead: "{words}"'
                     + (f'; recorded the hash of {", ".join(rehashed)} in '
                        f'{ENGINE_MANIFEST_REL}' if rehashed else '')
                     + (f'; re-recorded the baseline of {", ".join(rebased)}'
                        if rebased else ''))
        else:
            if rehashed:
                rep.step('hooks and settings', f'{ENGINE_MANIFEST_REL} keeps '
                         f'the committed hash of {", ".join(rehashed)} until the '
                         f'run with the person\'s words')
            rep.ask('hooks and settings',
                    harness_ask(harness, last=migrates_to_stubs(repo, harness),
                                cases=harness_cases(repo, harness),
                                gates=harness_new_gates(repo, harness),
                                baselines=harness_baselines(repo, harness)))

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
    cited = citations(repo, head.strip() if head_ok else None)
    if cited is None:
        rep.step('citations', 'could not be looked up -- run '
                 'tools/precedent_practice_refs.py --withdrawn before pushing')
    else:
        fix, read = cited
        adopted = adopt_listed_records(
            repo, {w.split(':', 1)[0] for w in read})
        if adopted:
            rep.step('records', f'{", ".join(adopted)} '
                     f'{"is" if len(adopted) == 1 else "are"} now declared in '
                     f'precedent.json\'s record_paths, moved from '
                     f'process/retired_vocabulary.json\'s exempt_files: one '
                     f'list of records, which every check reads')
            read = [w for w in read if w.split(':', 1)[0] not in adopted]
        for where, why in fix:
            rep.leave(where, why)
        rep.step('citations',
                 (f'{len(fix)} live citation(s) of a withdrawn practice to fix '
                  f'(listed below)' if fix else
                  'no live citation of a withdrawn practice to fix')
                 + (f'; {len(read)} citation(s) of a practice reworded or '
                    f'withdrawn -- read each, it may describe the old rule '
                    f'or name the old slug: '
                    + ', '.join(read) if read else '')
                 + record_paths_hint(read))

    manifest_postcondition(repo, rep)
    late = stage_late_output(repo, before)
    if late:
        rep.staged = sorted(set(rep.staged or ()) | set(late))
        rep.step('staged, written later', f'{len(late)} path(s) a step after '
                 f'the staging wrote, staged with the rest: ' + ', '.join(late))
    moved = sets_moved(sets_before, set_pins(repo))
    if moved:
        rep.upstream_changes = upstream_changes_block(repo, last_synced, tip, moved)
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
        ck.extract_archive(tar.stdout, td)
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


def session_load_total_step(repo, rep):
    """Measure what a session in `repo` loads against the
    `session_load_tokens` total, after everything this run writes, and put
    an overrun to the person.

    WHY (2026-10-29, a consuming repository). The update set the total to
    10,000 from the person's individual set and reported DONE; the next
    session check failed "what this session loads fits this repository's
    session-load total" at ~10,886 (AGENTS.md ~9,751 +
    .precedent/SESSION_PRACTICES.md ~1,134). The full check refuses only a
    change that grew a part, so a total that arrives under a repository
    already over it passed every gate here. The measurement is
    session_load_trend.total_against_cap, the one the session check's row
    reads. A question, not an item left for the repository: bringing it
    under is a reduction pass, and only the person raises the total
    (practice: session-load-budget)."""
    try:
        import session_load_trend as _slt
    except Exception:                                        # noqa: BLE001
        return
    renderer = repo / 'tools' / 'precedent_session_practices.py'
    if renderer.is_file():
        # The session-start file as the next session will have it, rendered
        # by the engine this update just vendored.
        run([sys.executable, str(renderer), '--repo', '.', '--quiet'], repo)
    measured = _slt.total_against_cap(repo)
    if measured is None:
        return
    sizes, total, cap = measured
    parts = ' + '.join(f'{rel} ~{n:,}' for rel, n in sizes.items())
    if total <= cap:
        rep.step('session-load total', f'~{total:,} of {cap:,} ({parts})')
        return
    rep.step('session-load total', f'OVER: ~{total:,} of {cap:,} ({parts})')
    rep.ask('session-load total',
            f'a session here loads ~{total:,} tokens before it works '
            f'({parts}), over the {cap:,}-token session_load_tokens total, so '
            f'every session check here fails until it comes under. A '
            f'reduction pass on the largest part brings it back (`python3 '
            f'tools/precedent_show.py reduction-pass`); only you can raise '
            f'the total instead (practice: session-load-budget).')


def stale_exemption_warnings(repo):
    """One line per `not_binding` entry the repo's own precedent_check.py
    finds it no longer needs (its --stale-exemptions), for the update's
    closing WARNING list. Empty when the engine there predates the flag or
    the run fails: a missing warning, never a failed update."""
    tool = repo / 'tools' / 'precedent_check.py'
    try:
        if '--stale-exemptions' not in tool.read_text(encoding='utf-8'):
            return []
        r = subprocess.run([sys.executable, str(tool), '--stale-exemptions'],
                           cwd=repo, capture_output=True, text=True,
                           timeout=600)
    except (OSError, subprocess.SubprocessError):
        return []
    return [line.split('  ', 1)[1].strip() for line in r.stdout.splitlines()
            if line.startswith('STALE EXEMPTION  ')]


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


NOT_APPLICABLE_RE = re.compile(r'^\s*N/A:')


def set_tests_step(repo, rep):
    """A practice set's own tests, every tools/checks/tests/test_*.sh, when
    this update changed the set's engine copy: -> None when they pass or do
    not apply, else the failure text for rep.close().

    2026-10-19: Update Vendors refreshed the ladder set's engine copy, the
    set's quick check passed, and the update merged; the set's own
    test_ladder_branches.sh first ran on main after it and was red. Its
    tests are the set's contract with the engine it calls, and an engine
    refresh touches the engine's files, never the tests', so the quick
    tier's "the tests a change touches" never picks them. They run here
    instead: the one moment the engine under them moves. Measured that day:
    about 70 seconds for all nine of the ladder set's."""
    if not (repo / 'precedent-source.json').is_file():
        return None
    tests = sorted((repo / 'tools' / 'checks' / 'tests').glob('test_*.sh'))
    changed, _err = status_paths(repo, 'tools/')
    engine = {f for f in (changed or ()) if not f.startswith('tools/checks/')}
    if not tests or not engine:
        return None
    red = []
    for t in tests:
        r = subprocess.run(['bash', str(t)], cwd=str(repo), capture_output=True,
                           text=True)
        out = (r.stdout + r.stderr).strip()
        # A case "not applicable" here never runs anywhere that matters:
        # this is the set's own repository, on the engine it was just
        # given. 2026-10-28: five of the ladder set's cases had reported
        # N/A in its own repository since they moved there, because they
        # read BestPractice-only files, and every run counted that as a
        # pass. So here it is red, with its reason.
        skipped = [l.strip() for l in out.splitlines() if NOT_APPLICABLE_RE.match(l)]
        if r.returncode != 0:
            red.append((t.name, out))
        elif skipped:
            red.append((t.name, 'passed, but did not run here, in its own '
                                'repository:\n' + '\n'.join(skipped)))
    if not red:
        rep.step('the set\'s own tests', f'all {len(tests)} pass on the '
                 f'refreshed engine')
        return None
    rep.step('the set\'s own tests', f'{len(red)} of {len(tests)} red or not run '
             f'on the refreshed engine: ' + ', '.join(n for n, _o in red))
    return ('the set\'s own tests are red on the refreshed engine, so this '
            'update would break the set where it lands:\n'
            + '\n'.join(f'--- {n} ---\n{tail(o, repo=repo)}' for n, o in red))


def closing_check(repo, rep, skip_check=False):
    """Step 5, and the report's close: -> the exit code."""
    seed_budgets_step(repo, rep)
    session_load_total_step(repo, rep)
    # An exemption whose reason went away: the update is the moment the
    # engine a repo exempted itself from changes, and the check never runs
    # an exempted rule, so nothing else would say so (2026-11-01: a shared
    # set's deep-check entry, whose root fix landed the same day). Asked of
    # the repo's own, just-updated engine; one vendored before the flag is
    # not asked, since it would run its rotation instead.
    rep.warnings.extend(stale_exemption_warnings(repo))

    # 5. The repo's own check, at the tier of the branch the update lands
    # on -- the gate before any push. Into staging, for a person who lands
    # there, that is the quick checks on what the update changed; the full
    # suite is Debut's (--run-tests) and Produce's (practice:
    # checks-follow-the-tier).
    check = repo / 'tools' / 'precedent_push_check.py'
    try:
        landing = pb.landing_branch(repo)[0]
    except Exception:                                          # noqa: BLE001
        landing = None
    argv = [sys.executable, str(check)]
    if landing:
        argv += ['--push-command', f'origin HEAD:{landing}']
    # DONE says which check it was: a bare "passed" from the basic tier
    # read as the push gate's all-clear, and a consumer's full check then
    # failed three ways on the same tree (2026-10-01, from a consumer's
    # Update Vendors).
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
            red = set_tests_step(repo, rep)
            if red:
                return rep.close(red)
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
        red = set_tests_step(repo, rep) if tier != pb.FULL else None
        if red:
            return rep.close(red)
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
    # No abbreviations: `--take` was ambiguous between --take-anyway and
    # --take-set, and argparse's own refusal named neither usefully
    # (2026-10-19, Update Vendors in a consumer). A shortened flag is
    # refused below with every flag it could mean, spelled out.
    ap = argparse.ArgumentParser(
        description='Update Vendors as one command (spec/ONE_COMMAND_UPDATE_PLAN.md).',
        allow_abbrev=False)
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
    ap.add_argument('--copy-in', action='append', default=[],
                    metavar='NAME=yes|no',
                    help='the person\'s answer to "copy this set into this '
                         'repository?", recorded in precedent.json and never '
                         'asked again; repeat per set')
    ap.add_argument('--keep-workflow', action='append', default=[],
                    metavar='PATH',
                    help='the person said to keep this workflow of the '
                         'repository\'s own: recorded in github_ci_approved, '
                         'pinned to its content, and never asked again; '
                         'needs --answered-by')
    ap.add_argument('--answered-by', default='',
                    help='who answered --copy-in or --keep-workflow, with a '
                         'date and their own words: \'Name, YYYY-MM-DD: "..."\'')
    ap.add_argument('--take-set', action='append', default=[], metavar='NAME',
                    help='refresh this copied-in set this once although '
                         'this repository holds it ("hold" in precedent.json)')
    flags = [f for f in ap._option_string_actions if f.startswith('--')]
    for tok in (sys.argv[1:] if argv is None else argv):
        word = tok.split('=', 1)[0]
        if word.startswith('--') and word not in flags:
            meant = sorted(f for f in flags if f.startswith(word))
            if meant:
                print(f'precedent_update FAIL: {word} is not a flag; say which '
                      f'you mean in full: {" or ".join(meant)}')
                return FAILED
    a = ap.parse_args(argv)
    repo = pathlib.Path(a.repo).resolve()
    copy_in, bad = pve.parse_copy_in_answers(a.copy_in)
    if bad:
        print('precedent_update FAIL: ' + '; '.join(bad))
        return FAILED
    if a.keep_workflow and not a.answered_by:
        print('precedent_update FAIL: --keep-workflow needs --answered-by: who '
              'answered, the date and their words in quotes.')
        return FAILED
    if copy_in and not a.answered_by:
        print('precedent_update FAIL: --copy-in needs --answered-by: who '
              'answered, the date and their words in quotes.')
        return FAILED
    if repo in (SOURCE, CLONE):
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
    code = bootstrap(repo, a, sys.argv[1:] if argv is None else list(argv))
    if isinstance(code, int):
        return code
    return update(repo, skip_check=a.skip_check, ref=a.from_ref, move=a.move,
                  take=a.take, code=code, copy_in=copy_in,
                  answered_by=a.answered_by, take_sets=tuple(a.take_set),
                  keep_workflows=tuple(a.keep_workflow))


def bootstrap(repo, a, argv):
    """-> the exit code of the run started from a driver worktree, or the
    {'line', 'warning'} to run in place with: precedent_update_driver's two
    tables, before anything here writes into `repo` (undo_leftover_standin,
    the journal replay and the put-back steps all do). It reads only:
    held_pin, never take_pin."""
    if os.environ.get(drv.GUARD_ENV):
        return {'line': drv.child_line(SOURCE), 'warning': None}
    only = os.environ.get(drv.ONLY_ENV)
    rc, head = run(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], SOURCE)
    head = head.strip()[:12] if rc == 0 and head.strip() else 'an unknown commit'
    if os.environ.get(drv.OPT_OUT_ENV) and not only:
        # No fetch: nothing it could find would change the answer.
        return {'line': f"ran this clone's own code, {CLONE} @ {head}, as "
                        f"{drv.OPT_OUT_ENV} asks", 'warning': None}
    follow = pve.followed_branch(repo)
    try:
        with held(SOURCE):
            rc, out = run(['git', '-C', str(SOURCE), 'fetch', 'origin',
                           pve.tracking_refspec(follow)], SOURCE)
    except TimeoutError as e:
        rc, out = 1, str(e)
    if rc != 0:
        v = {'row': 'no-fetch', 'in_place': True,
             'line': f"ran this clone's own code, {CLONE} @ {head}",
             'warning': (f"could not fetch origin/{follow} "
                         f"({out.strip().splitlines()[-1] if out.strip() else 'no output'}), "
                         f"so could not tell whether this clone's code is "
                         f"current")}
    else:
        markers = None
        if follow == 'main':
            try:
                markers = pb.passed_markers(SOURCE)
            except (OSError, subprocess.SubprocessError):
                markers = None
        v = drv.decide(SOURCE, repo, follow, markers=markers, window=GREEN_WINDOW,
                       ref=a.from_ref, take=a.take, move=a.move,
                       pin=held_pin(repo))
    if only:
        for key in ('row', 'in_place', 'g', 'data', 'driver', 'head', 'line',
                    'warning'):
            print(f"precedent_update_driver: {key}: {v.get(key)}")
        return DONE
    if v['in_place']:
        return v
    rc, why = drv.run_from_worktree(SOURCE, v['driver'], argv, held)
    if rc is not None:
        return rc
    drv_short = v['driver'][:12]
    return {'line': f"ran this clone's own code, {CLONE} @ {head}",
            'warning': (f"could not set up a temporary checkout of {drv_short} "
                        f"({why}), so this ran the clone's own code at {head}, "
                        f"which is older than {drv_short}. If it stops on what "
                        f"looks like a BestPractice bug, pull the clone first: "
                        f"git -C {CLONE} pull --ff-only")}


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Update Vendors' migration off a retired branch tier: brings work still waiting there into staging, rewords this repository's instructions and links to it, and offers the old branch for deletion

migration_retire_pre_staging.py -- a migration, run by Update Vendors
(precedent_update.migrations_step), which runs every tools/migration_*.py
it finds and names none of them. Each one exposes migrate(repo, rep, pu):
`rep` is the update's Report and `pu` the precedent_update module running
it, whose helpers a migration borrows. A migration is the one place the
engine still knows an old arrangement, so a repository whose vendors have
not been updated can be moved off it; once no repository needs it, the
file is deleted (practice: decommission-deletes-files).

This one was inline in precedent_update.py from 2026-10-09 until
2026-10-17, when it moved here (Morgan, 2026-10-17: "there should be no
mention anywhere of pre-staging except in migrations or history").
"""
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import precedent_branches as pb  # noqa: E402

# The precedent_update module running this migration, set by migrate().
pu = None


def migrate(repo, rep, update):
    """Update Vendors' entry point (precedent_update.migrations_step)."""
    global pu
    pu = update
    _retire(repo, rep)


# UPGRADING OFF PRE-STAGING (2026-10-09). A person who lands straight on
# staging (precedent_branches.lands_on_staging) no longer uses pre-staging.
# Morgan, 2026-10-09: when this reaches the repositories that vendor the
# engine, "make sure we have a smooth upgrade process for each. Merging the
# branches, telling he can delete pre-staging, updating previous mentions/
# links within each repo, etc etc." Since 2026-10-14 that is everyone on
# the ladder (_pre_staging_unused below; spec/PRE_STAGING_RETIREMENT_PLAN.md),
# and while origin still has pre-staging:
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
# sources. Off the ladder it does nothing and says nothing.
# The engine's branch code knows nothing of pre-staging since 2026-10-17
# (Morgan: "WE SHOULD DELETE PRE-STAGING EVERYWHERE"); this upgrade is the
# one place that still does, because a repository whose vendors have not
# been updated still has it, and updating them is what takes it away
# (Morgan, 2026-10-17: "there is no pre-staging IN REPOS WHERE WE HAVE
# UPDATED THE VENDORS that is the goal").
PRE_STAGING = 'pre-staging'
RETIRED_WAITING = 'waiting'
RETIRED_MERGED = 'merged'


def _pre_staging_unused(repo):
    """-> (unused, waits): unused is True for a person on the ladder, unless
    this repository's precedent.json still names pre-staging, when `waits`
    says so and this step switches it. Off the ladder nobody ever landed on
    pre-staging: (False, None)."""
    if not pb.ladder_in_force(repo):
        return False, None
    if pb.precedent_json(repo).get(pb.LANDING_SETTING) == PRE_STAGING:
        return False, (f'precedent.json still names {PRE_STAGING} as the '
                       f'landing branch; it is retired, and work already '
                       f'lands on {pb.STAGING}. Update Vendors switches it')
    return True, None


def _pre_staging_retired(repo, fetch=False):
    """-> (state, tip) for origin's pre-staging: None when it is not retired
    here or origin has none; RETIRED_WAITING when it holds work staging
    lacks; RETIRED_MERGED when merging it would change no file. Never
    raises."""
    try:
        if not _pre_staging_unused(repo)[0]:
            return None, None
        staging = pb.staging_branch(repo)
        if fetch:
            if not pb._remote_tip(repo, PRE_STAGING):
                return None, None
            pb._run(repo, 'fetch', '-q', 'origin', PRE_STAGING, staging)
        ptip = pb._git(repo, 'rev-parse', '--verify', '-q',
                       f'refs/remotes/origin/{PRE_STAGING}^{{commit}}')
        if not ptip:
            return None, None
        stip = pb._git(repo, 'rev-parse', '--verify', '-q',
                       f'refs/remotes/origin/{staging}^{{commit}}')
        if stip and pb._brings_nothing(repo, stip, ptip):
            return RETIRED_MERGED, ptip
        return RETIRED_WAITING, ptip
    except Exception:                                       # noqa: BLE001
        return None, None


HEADER = 'PRE-STAGING IS RETIRED -- your work lands on staging now:'

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
        uni = pu.universal_catalogue_path(repo)
    except Exception:                                        # noqa: BLE001
        uni = None
    if uni:
        vendored.append(uni.rstrip('/') + '/')
    engine = pu._engine_owned(repo) | set(_materialized_practices(repo))
    try:
        import precedent_resolve as pr
        records = list(pr.declared_record_paths(repo))
    except Exception:                                        # noqa: BLE001
        records = []
    files, history = [], []
    for rel in tracked:
        if rel in engine or any(rel.startswith(v) for v in vendored):
            continue
        if pu._is_generated_view(repo, rel):
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


# THE REPOSITORY'S OWN VALUE IS SWITCHED (2026-10-14). A precedent.json
# that still names pre-staging is switched to staging, that one value and
# nothing else, and the retirement goes on in the same run. From 2026-10-09
# only a repository's sole maintainer could switch it, since others might
# still land there; since pre-staging was retired for everyone
# (spec/PRE_STAGING_RETIREMENT_PLAN.md) nobody does.
_REPO_LANDS_ON_PRE_STAGING = re.compile(
    r'("' + re.escape(pb.LANDING_SETTING) + r'"\s*:\s*)"' + re.escape(PRE_STAGING) + '"')


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
    rc, out = pu.run(['git', 'show', 'HEAD:precedent.json'], repo)
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
    rc, out = pu.run(['git', 'show', 'HEAD:tools/precedent_branches.py'], repo)
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


def _retire(repo, rep):
    """Update Vendors' upgrade off pre-staging, for anyone on the ladder
    (see HEADER above). Reports on `rep`: one step line,
    and the block close() prints in every outcome (rep.migration_notes). Silent off
    the ladder, and once origin has no pre-staging."""
    repo = pathlib.Path(repo)
    # A precedent.json still naming pre-staging is switched first
    # (_pre_staging_unused says it waits until then).
    unused, waits = _pre_staging_unused(repo)
    switched = False
    if waits:
        if not committed_engine_lands_on_staging(repo):
            # The first pass brings the engine and nothing else; the switch
            # waits for the next run, once that engine has landed (Morgan,
            # 2026-10-09: "do the vendor updates, tell you, then I'll do
            # the vendor updates again").
            rep.step('pre-staging', f'kept for now: this update brings the '
                     f'engine that lands work straight on {pb.STAGING}. Land '
                     f'it, then run Update Vendors again: that run moves this '
                     f'repository onto {pb.STAGING}')
        elif ('precedent.json' not in set(rep.before or ())
                and switch_repo_landing_to_staging(repo)):
            switched = True
            rep.step('precedent.json', f'{pb.LANDING_SETTING} {PRE_STAGING} '
                     f'-> {pb.STAGING}: pre-staging is retired for everyone')
            unused, waits = _pre_staging_unused(repo)
        else:
            rep.step('pre-staging', f'kept, not retired: {waits}')
    if not unused:
        return
    state, _ptip = _pre_staging_retired(repo, fetch=True)
    if state is None:
        return
    staging = pb.staging_branch(repo)
    block = []
    if state == RETIRED_WAITING:
        said = []
        rc = pb.land(repo, work=f'origin/{PRE_STAGING}', say=said.append)
        text = '\n'.join(said)
        result = next((l for l in reversed(said)
                       if l.startswith(pb.LAND_RESULT)), '')
        if rc != 0:
            rep.step('pre-staging', f'not brought into {staging}; nothing moved')
            if 'conflicts with' in result:
                why = (f'{PRE_STAGING} holds work {staging} lacks, and it does '
                       f'not merge cleanly: the same lines changed on both sides. '
                       f'Nothing moved, and nothing was dropped')
            elif 'quick checks failed' in result:
                why = (f'{PRE_STAGING} holds work {staging} lacks, and the quick '
                       f'checks failed on {staging} with it merged in. Nothing moved')
            else:
                why = (f'{PRE_STAGING} holds work {staging} lacks, and it could '
                       f'not be brought in ({result or "see the lines below"}). '
                       f'Nothing moved')
            rep.leave(PRE_STAGING, why + '. To bring it in: '
                      f'`git switch --no-track -c "$(python3 tools/precedent_branch_name.py '
                      f'merge pre-staging)" origin/{PRE_STAGING}`, then '
                      f'`git merge origin/{staging} origin/{pb.MAIN}`, fix what '
                      f'it names and commit, `git push -u origin HEAD`, then '
                      f'`python3 tools/precedent_branches.py --land '
                      f'"$(git branch --show-current)"`, and run Update Vendors '
                      f'again')
            rep.details[PRE_STAGING] = [l for l in text.splitlines()
                                           if l.strip()][-12:]
            return
        moved = [l.split('   <- ', 1)[0].rstrip() for l in text.splitlines()
                 if l.startswith(('LANDED ', 'BROUGHT IN ', 'REBUILT ', '  '))]
        block.append(f'merged into {staging}, with the quick checks:')
        block += [f'  {l}' for l in moved]
        state, _ptip = _pre_staging_retired(repo, fetch=True)
        if state != RETIRED_MERGED:
            rep.step('pre-staging', f'its work brought into {staging}; it gained '
                     f'more meanwhile')
            block.append(f'{PRE_STAGING} gained work while this ran; run Update '
                         f'Vendors again to bring that in too.')
            rep.migration_notes[HEADER] = block
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
            + urllib.parse.quote(PRE_STAGING, safe='')) if slug else None
    block.append(f'{PRE_STAGING} holds nothing {staging} lacks and is no '
                 f'longer used, so it is safe to delete: '
                 + (link or "GitHub's branches page, with its trash icon"))
    rep.migration_notes[HEADER] = block
    rep.step('pre-staging', 'retired'
             + (f', its work merged into {staging}' if len(block) and
                block[0].startswith('merged into') else '')
             + (f', {len(changed)} mention(s) reworded' if changed else '')
             + '; safe to delete')

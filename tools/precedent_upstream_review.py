#!/usr/bin/env python3
"""Upstream review: what a ladder step ran into, less what an earlier stage reviewed.

Practice `upstream-review`, in the ladder set (precedent-shared-ladder),
for code owners only. When Update Vendors, a migration or an upgrade
finishes, and at Booked, Debut and Produce, the session reviews every
warning, error, note, exemption, kept local edit and workaround the step met
-- fixed or not -- and hands the ones that can be fixed upstream to another
session. This module is the mechanical half: it pulls the warning-shaped
lines out of a run's output and drops the ones already reviewed. The
judgment -- is the cause in a repository we own, is the fix bounded -- stays
with the session (practice: judgment-check-or-tool).

ONLY ON THE LADDER, ONLY FOR A CODE OWNER (Morgan, 2026-10-11: "let's
rebuild it but only in ladders and also only when the user is a code
owner"). applies() is the one test: the ladder in force for this person
(precedent_ladder.ladder_in_force) and the person one of this repository's
code owners (precedent_audience.is_code_owner). Anyone else gets nothing at
all -- not a line saying it was skipped -- because a person who only works
in the repository never sees its mechanics. Built 2026-09-30 on a branch
that never landed; rebuilt on today's ladder, where Booked lands straight
on staging.

THE RECORD IS THE COMMITS, NOT A LIST (Morgan, 2026-09-30, strength:
decided: "I like the ledger idea, I'm sold. Let's do it with C."). Each
stage writes one line per item it reviewed into the commit it lands:

    Upstream-seen: <fingerprint> <the line, shortened>

and the next stage reads those lines back from exactly the batch it moves --
Debut from pre-staging's commits staging lacks, Produce from staging's
commits main lacks. So "only what is new since the last stage" is the batch
itself, and nothing grows beyond git history, which is kept anyway. Booked
writes the lines into the commit it lands on staging, Debut into its merge
commit; Produce only lists them (main moves by a pull request); Update
Vendors prints them for the session's commit.

A fingerprint is the line with what changes from run to run taken out --
digits, commit hashes, temporary paths -- so the same warning printed at
Booked and again at Debut is one item.

  python3 tools/precedent_upstream_review.py --stage booked [--from FILE|-]
          [--note TEXT ...] [--range A..B]
  python3 tools/precedent_upstream_review.py --self-check

--from reads a run's output (a check, an update); --note adds something the
session met that no tool printed. The range defaults to the batch the stage
moves: origin/<landing>..HEAD for booked and update, origin/<staging>..
origin/pre-staging for debut, origin/main..origin/<staging> for produce.
Exit 0 always -- a review is a report, never a gate. Off the ladder, or for
someone who is not a code owner, it prints one line saying why and nothing
else.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

TRAILER = 'Upstream-seen:'
STAGES = ('update', 'booked', 'debut', 'produce')
STAGE_NAMES = {'update': 'Update Vendors', 'booked': 'Booked, step 3 of 5',
               'debut': 'Debut, step 4 of 5', 'produce': 'Produce, step 5 of 5'}
PRACTICE = "the ladder set's upstream-review practice"
_HERE = Path(__file__).resolve().parent
MAX_TEXT = 110

# What a warning looks like in this project's tools and in the Python and git
# tooling under them. Deliberately loose: a false positive costs the session
# one line of judgment, a miss costs the review its point.
_WARNING = re.compile(
    r'\bWARN(?:ING)?\b|\b[Ww]arning:|\b(?:Deprecation|Future|User|Runtime)Warning\b'
    r'|\bNOTE:|\bSKIPPED\b|\bADVISORY\b|\(advisory\)|\bdeprecated\b'
    r'|\bcould not\b|\bcannot\b.*\bskipp', re.IGNORECASE)
# A line this review printed itself is never an item of the next one.
_OWN = re.compile(r'^\s*(?:' + re.escape(TRAILER) + r'|UPSTREAM REVIEW\b|- \[[0-9a-f]{10}\])')
_TMP_PATH = re.compile(r'(?:/tmp|/var/folders|/private/var)/\S*')
_HOME_PATH = re.compile(r'(?:/home/[^/\s]+|/root|/Users/[^/\s]+)/')
_HEX = re.compile(r'\b[0-9a-f]{7,40}\b')
_NUM = re.compile(r'\d+(?:\.\d+)?')


def fingerprint(line):
    """-> ten hex characters naming the warning, not this printing of it."""
    s = line.strip().lower()
    s = _TMP_PATH.sub('<tmp>', s)
    s = _HOME_PATH.sub('~/', s)
    s = _HEX.sub('#', s)
    s = _NUM.sub('0', s)
    s = re.sub(r'\s+', ' ', s)
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:10]


def extract(text):
    """-> the warning-shaped lines of `text`, each once, in order."""
    out, seen = [], set()
    for raw in (text or '').splitlines():
        line = raw.strip()
        if not line or _OWN.search(line) or not _WARNING.search(line):
            continue
        fp = fingerprint(line)
        if fp not in seen:
            seen.add(fp)
            out.append((fp, line))
    return out


def notes(items):
    """Free-text items the session met that no tool printed."""
    return [(fingerprint(t), t.strip()) for t in items if t and t.strip()]


def _git(root, *args):
    p = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def recorded(root, rev_range):
    """-> {fingerprint} written as Upstream-seen lines on the commits in
    `rev_range`. A range git cannot read records nothing: the review then
    shows everything, which is the safe side."""
    if not rev_range:
        return set()
    log = _git(root, 'log', '--format=%B', rev_range)
    got = set()
    for line in (log or '').splitlines():
        m = re.match(r'\s*' + re.escape(TRAILER) + r'\s+([0-9a-f]{10})\b', line)
        if m:
            got.add(m.group(1))
    return got


def split(items, already):
    """-> (new, old): items not yet reviewed at an earlier stage, and the rest."""
    new = [i for i in items if i[0] not in already]
    old = [i for i in items if i[0] in already]
    return new, old


def _short(text):
    text = ' '.join(text.split())
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT - 3] + '...'


def trailer_lines(items):
    return [f'{TRAILER} {fp} {_short(text)}' for fp, text in items]


def _engine(name):
    """-> the engine module `name` beside this file, or None."""
    sys.path.insert(0, str(_HERE))
    try:
        return __import__(name)
    except Exception:                                          # noqa: BLE001
        return None
    finally:
        sys.path.pop(0)


def applies(root):
    """-> (on, why): whether the review is shown here -- the ladder in force
    for this person AND the person one of this repository's code owners.
    False whenever either cannot be shown, like every code-owner rule."""
    pl, pa = _engine('precedent_ladder'), _engine('precedent_audience')
    if pl is None or pa is None:
        return False, 'the ladder or audience module is not here'
    try:
        if pl.ladder_in_force(Path(root)) is False:
            return False, 'the ladder is not in force for you here'
        owner, why = pa.is_code_owner(Path(root))
    except Exception as exc:                                   # noqa: BLE001
        return False, f'could not tell ({exc})'
    if not owner:
        return False, f'you are not a code owner here ({why})'
    return True, why


def default_range(root, stage):
    """The batch the stage moves, as origin last showed it."""
    pb = _engine('precedent_branches')
    staging = 'staging'
    landing = None
    if pb is not None:
        try:
            staging = pb.staging_branch(Path(root)) or staging
            landing = pb.landing_branch(Path(root))[0]
        except Exception:                                      # noqa: BLE001
            pass
    if stage == 'debut':
        return f'origin/{staging}..origin/pre-staging'
    if stage == 'produce':
        return f'origin/main..origin/{staging}'
    return f'origin/{landing or staging}..HEAD'


def report(stage, new, old, recording):
    """-> the lines a session reads. `recording` says where the Upstream-seen
    lines go: 'written' (the tool put them in its own commit), 'commit' (the
    session adds them to the commit it makes), or None (the last stage)."""
    name = STAGE_NAMES.get(stage, stage)
    lines = [f'UPSTREAM REVIEW ({name}): {len(new)} item(s) to review'
             + (f'; {len(old)} already reviewed at an earlier stage, skipped'
                if old else '') + '.']
    if not new:
        lines.append(f'  Nothing new: say so in one line ({PRACTICE}).')
        return lines
    lines.append('  Judge each: is the cause in a repository we own or a '
                 'version we pin, and is the fix bounded? Yes -> one Prompt '
                 'Please block per upstream repo, in the Boildown. No -> one line '
                 'saying why. A warning our own tool prints with nothing to do '
                 f'counts as fixable: stop it printing ({PRACTICE}).')
    for fp, text in new:
        lines.append(f'  - [{fp}] {_short(text)}')
    if recording == 'written':
        lines.append('  Recorded as Upstream-seen lines in this step\'s own '
                     'commit, so the next stage skips them.')
    elif recording == 'commit':
        lines.append('  Put these lines at the end of the commit message this '
                     'step lands, so the next stage skips them:')
        lines.extend('    ' + t for t in trailer_lines(new))
    return lines


def review(root, stage, text='', extra=(), rev_range=None):
    """-> (new, old) for a step's output `text` plus `extra` notes. Asks
    nothing about who is reading: callers go through prepare()."""
    items = extract(text) + [i for i in notes(extra)
                             if i[0] not in {fp for fp, _ in extract(text)}]
    rng = rev_range if rev_range is not None else default_range(root, stage)
    return split(items, recorded(root, rng))


def prepare(root, stage, text='', extra=(), rev_range=None):
    """-> (new, old), or (None, None) where the review does not apply (off
    the ladder, or not a code owner). The one entry point the tools use, so
    nobody else sees a line of it."""
    if not applies(root)[0]:
        return None, None
    return review(root, stage, text, extra, rev_range)


def self_check():
    import tempfile
    bad = []
    a = fingerprint('WARN: precedent_vendor_engine: 6 hook script(s) at /tmp/x-123/tree/a.sh')
    b = fingerprint('WARN: precedent_vendor_engine: 7 hook script(s) at /tmp/y-9/tree/a.sh')
    if a != b:
        bad.append('the same warning with other numbers and temp paths fingerprinted twice')
    if fingerprint('NOTE: could not release lock') == fingerprint('NOTE: could not take lock'):
        bad.append('two different warnings shared a fingerprint')
    got = extract('ok\nWARN: one\nall passed\nWARN: one\n'
                  'Upstream-seen: 0123456789 WARN: old\nsome DeprecationWarning here\n')
    if [t for _, t in got] != ['WARN: one', 'some DeprecationWarning here']:
        bad.append(f'extract kept {[t for _, t in got]!r}')
    with tempfile.TemporaryDirectory() as tmp:
        g = lambda *a: subprocess.run(['git', '-C', tmp, '-c', 'user.name=x',
                                       '-c', 'user.email=x@example.invalid', *a],
                                      capture_output=True, text=True, check=True)
        g('init', '-q')
        g('commit', '-q', '--allow-empty', '-m', 'base')
        base = g('rev-parse', 'HEAD').stdout.strip()
        seen = extract('WARN: one')
        g('commit', '-q', '--allow-empty', '-m', 'work\n\n' + '\n'.join(trailer_lines(seen)))
        new, old = review(tmp, 'booked', 'WARN: one\nWARN: two', rev_range=f'{base}..HEAD')
        if [t for _, t in new] != ['WARN: two'] or [t for _, t in old] != ['WARN: one']:
            bad.append(f'a recorded item was not skipped: new={new!r} old={old!r}')
        new, _ = review(tmp, 'booked', 'WARN: one', rev_range='nosuchref..HEAD')
        if len(new) != 1:
            bad.append('an unreadable range hid an item instead of showing it')
    if bad:
        print('precedent_upstream_review self-check FAILED: ' + '; '.join(bad))
        return 1
    print('precedent_upstream_review self-check: ok')
    return 0


def main(argv):
    if argv == ['--self-check']:
        return self_check()
    stage, src, extra, rng = None, None, [], None
    rest = list(argv)
    while rest:
        flag = rest.pop(0)
        if flag in ('--stage', '--from', '--note', '--range') and rest:
            val = rest.pop(0)
            if flag == '--stage':
                stage = val
            elif flag == '--from':
                src = val
            elif flag == '--note':
                extra.append(val)
            else:
                rng = val
        else:
            stage = None
            break
    if stage not in STAGES:
        print('usage: precedent_upstream_review.py --stage update|booked|debut|produce '
              '[--from FILE|-] [--note TEXT ...] [--range A..B]', file=sys.stderr)
        return 2
    text = ''
    if src == '-':
        text = sys.stdin.read()
    elif src:
        text = Path(src).read_text(encoding='utf-8', errors='replace')
    root = (_git(Path.cwd(), 'rev-parse', '--show-toplevel') or '.').strip()
    on, why = applies(root)
    if not on:
        print(f'upstream review: not shown here -- {why}.')
        return 0
    new, old = review(root, stage, text, extra, rng)
    for line in report(stage, new, old, None if stage == 'produce' else 'commit'):
        print(line)
    return 0


if __name__ == '__main__':
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""One formatter for the quantity kind "a moment in time" (practice: one-formatter-per-quantity).

WHAT THIS IS FOR. Two records say "Morgan 19:00" and "John 18:00" and
nobody can order them, because neither says which zone it is. That is not
a formatting nicety — it is a lost fact, and it cannot be recovered later
from the file. So: **every moment this project writes down carries its
offset**, and every emitter goes through this module rather than calling
`datetime` itself.

practice: volatile-rules-carry-dates — a date in a document is the
contributor's local calendar date, not the agent's system clock. A hosted
container runs on UTC, so a bare `datetime.date.today()` silently writes
the container's date, which is the wrong one for part of every day.

THE INCIDENT (practice: cite-the-incident). 2026-09-09: fourteen call
sites across `tools/` stamped dates and times three different ways —
`date.today()` (the container's zone, i.e. UTC), `datetime.now(utc)`
(honest but not the person's), and one `utcfromtimestamp()` (deprecated
and naive). Nothing said which of the three any given stamp was, so a
reader comparing two records from different tools could not order them.
The same root cause had by then produced a run of separate commit-offset
incidents; the durable fix is one module, not another careful session
(practice: durable-fix).

THE ZONE LADDER, and why it ends where it does. Same order as
`.claude/hooks/commit-identity.sh` resolves a committer's zone, and for
the same reason: `identity.json` is the ONE place a person's zone is
declared and everything else derives from it (practice:
registry-source-of-truth).

  1. PRECEDENT_COMMIT_TZ            — an explicit override
  2. this repo's own identity.json  — the repo IS somebody's individual source
  3. the individual source's identity.json, via ~/.config/precedent/config.json
  4. TZ in the environment          — the harness `env` block, itself derived
                                      from identity.json at session start
  5. precedent.json's `fallback_timezone` — THIS REPOSITORY's declared fallback
  6. America/New_York — the engine's own last resort

Rungs 5 and 6 are a decision, not a guess. Morgan, 2026-09-09, asked for a
real offset rather than UTC-because-nobody-said — *"if you can't find/get my
timezone then use buenos aires timezone"* — because any consistent real
offset lets a reader order two records. He narrowed it on 2026-09-10, and
rung 6 is what changed: *"The Buenos Aires fallback should be just for me
personally."* Buenos Aires is his zone and belongs at rungs 2-3, in his own
identity.json, where it is his and is enforced. This is a PUBLIC, generic
engine whose whole contract is to name no person, and an unidentified
committer here is not him. Rung 6 is New York; rung 5 lets any repo say
otherwise.

Rung 5 exists so that choice is a repo's to make rather than the engine's
to impose (practice: layered-practice-packs). A person's zone is
person-level and lives in their identity.json; the fallback for a person
this project could not identify is REPO-level, so it is declared in
precedent.json where an adopting repo can set its own without editing
vendored code (practice: registry-source-of-truth). Rung 6 is what a repo
that declared nothing gets, and it is deliberately a real zone rather than
UTC: see WHAT IS DELIBERATELY NOT IN THE LADDER below.

WHAT IS DELIBERATELY NOT IN THE LADDER: the system zone (`/etc/localtime`,
or a naive `datetime.now()`). On a hosted container that reads UTC, and
"UTC because nobody configured anything" is precisely the state the
fallback exists to replace. A session that genuinely wants the machine's
own clock is asking a different question and should say so in its own code.

FAILS GRACEFULLY (practice: fail-gracefully). If `zoneinfo` cannot load a
name — a container with no tzdata, a typo in an identity.json — this falls
back to the fallback zone's fixed offset and says so through
`resolved()`, rather than dropping to a naive datetime. A stamp without an
offset is the bug; a stamp with a slightly wrong offset is still orderable.
"""

import datetime
import json
import os
import pathlib

try:  # pragma: no cover - exercised by the tzdata-less path below
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

# The engine's last-resort zone, for a repo that declared no
# `fallback_timezone` of its own. Morgan, 2026-09-09. Kept in lockstep with
# DEFAULT_TZ in .claude/hooks/commit-identity.sh and its harness template
# copy; tools/precedent_check.py's `timestamps-carry-offset` check asserts
# all three agree, so this constant cannot drift from the hook that applies
# it to the session.
FALLBACK_TZ = 'America/New_York'

# Used only when zoneinfo itself cannot answer -- this is returned PAIRED with
# FALLBACK_TZ, as "the declared fallback", so the two must name the same place
# or the engine reports a zone it is not applying.
#
# It moved with the fallback on 2026-09-10 and the reasoning had to change with
# it, not just the number. The old value was -0300, and its justification was
# that Argentina has not observed DST since 2009, so a fixed offset was a TRUE
# statement about that zone. New York observes DST, so no fixed offset is true
# about it all year: -0500 is Eastern Standard Time and is wrong by an hour
# during Eastern Daylight Time. That is accepted rather than hidden. This rung
# fires only on a machine with no timezone database at all, where the choice is
# between an offset that is right most of the year and none at all -- and a
# stamp carrying a real offset still orders correctly against other stamps,
# which is what timestamps-carry-offset is for.
FALLBACK_OFFSET = datetime.timezone(datetime.timedelta(hours=-5), 'EST')

_USER_CONFIG = '~/.config/precedent/config.json'


def _read_identity_zone(path):
    """The `timezone` field of an identity.json, or None."""
    return _read_key(path, 'timezone')


def _individual_identity_zone():
    """The individual practice source's declared zone, if that source resolves."""
    cfg = os.environ.get('PRECEDENT_USER_CONFIG') or _USER_CONFIG
    try:
        data = json.loads(pathlib.Path(cfg).expanduser().read_text(encoding='utf-8'))
        path = data['individual']['path']
    except Exception:
        return None
    return _read_identity_zone(pathlib.Path(path).expanduser() / 'identity.json')


def _repo_fallback_zone(root):
    """precedent.json's `fallback_timezone` -- the repository's own choice."""
    return _read_key(pathlib.Path(root) / 'precedent.json', 'fallback_timezone')


def _read_key(path, key):
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    return value if isinstance(value, str) and value.strip() else None


def resolved(root=None):
    """(tzinfo, name, source) — the zone in force, and where it came from.

    `source` is a phrase for a human, so a tool can say which rung of the
    ladder answered instead of leaving the reader to guess whether a stamp
    was declared or defaulted.
    """
    root = pathlib.Path(root or os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd())

    candidates = [
        (os.environ.get('PRECEDENT_COMMIT_TZ'), 'the PRECEDENT_COMMIT_TZ override'),
        (_read_identity_zone(root / 'identity.json'),
         "this repository's own identity.json"),
        (_individual_identity_zone(),
         "the individual practice source's identity.json"),
        (os.environ.get('TZ'), 'TZ in the environment'),
        (_repo_fallback_zone(root),
         "this repository's declared fallback_timezone (no zone was found for this person)"),
        (FALLBACK_TZ,
         'the engine fallback (no zone was found, and this repo declared none)'),
    ]

    for name, source in candidates:
        if not name or not str(name).strip():
            continue
        name = str(name).strip()
        if ZoneInfo is not None:
            try:
                return ZoneInfo(name), name, source
            except Exception:
                continue  # an unloadable name is not an answer; try the next rung
    return FALLBACK_OFFSET, FALLBACK_TZ, 'the declared fallback (zoneinfo unavailable)'


def zone(root=None):
    """The tzinfo alone, for callers that do not need to explain themselves."""
    return resolved(root)[0]


def now(root=None):
    """An AWARE datetime in the person's zone. Never naive."""
    return datetime.datetime.now(zone(root))


def today(root=None):
    """Today's calendar date in the person's zone, as YYYY-MM-DD.

    The drop-in for `datetime.date.today().isoformat()`. A date carries no
    offset, which is exactly why the ZONE it was computed in has to be the
    person's rather than the container's: for part of every day the two
    disagree by one day.
    """
    return now(root).date().isoformat()


def stamp(root=None, seconds=False):
    """A moment a human reads: `2026-09-09 13:50 -0300`.

    The offset is not optional and there is no flag to drop it — a stamp
    without one is the failure this module exists to prevent.
    """
    fmt = '%Y-%m-%d %H:%M:%S %z' if seconds else '%Y-%m-%d %H:%M %z'
    return now(root).strftime(fmt)


def stamp_iso(root=None):
    """A moment a machine reads: ISO 8601, offset included, seconds precision."""
    return now(root).replace(microsecond=0).isoformat()


def compact(root=None):
    """A filename-safe moment: `20260909T135000-0300`. Sorts lexically."""
    return now(root).strftime('%Y%m%dT%H%M%S%z')


def utc_iso():
    """ISO 8601 in UTC, offset included: `2026-09-09T16:53:36+00:00`.

    For a machine-readable field whose NAME already says UTC (a build
    manifest's `generated_at_utc`, a simulation record's `timestamp_utc`).
    Those are not the bug this module exists for -- an explicit `+00:00` is
    orderable and honest -- but they are the same quantity kind, so they
    come from here rather than from a second inline `datetime.now(utc)`
    that can drift (practice: one-formatter-per-quantity). Anything a PERSON
    reads wants `stamp()` instead: nobody should have to convert a build
    time out of UTC in their head.
    """
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()


def from_unix(unix_ts, root=None):
    """An AWARE datetime in the person's zone, from a POSIX timestamp.

    For git's own commit timestamps, among others. `utcfromtimestamp` is
    deprecated in 3.12 and returns a NAIVE datetime, which is how a git
    date became an unlabelled string in the first place.
    """
    return datetime.datetime.fromtimestamp(int(unix_ts), zone(root))


def date_from_unix(unix_ts, root=None):
    """The calendar date of a POSIX timestamp, in the person's zone."""
    return from_unix(unix_ts, root).date().isoformat()


def main(argv=None):
    """`python3 tools/precedent_time.py` — say what the zone is and where it came from.

    A person debugging a wrong-looking date needs the RUNG, not just the
    answer: "declared in your identity.json" and "nobody said, so Buenos
    Aires" produce the same offset on a good day and mean opposite things.
    """
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--format', choices=['human', 'iso', 'date', 'compact'],
                    default='human')
    ap.add_argument('--quiet', action='store_true',
                    help='print the stamp alone, for use in a script')
    args = ap.parse_args(argv)

    _, name, source = resolved()
    value = {'human': stamp, 'iso': stamp_iso, 'date': today,
             'compact': compact}[args.format]()
    print(value)
    if not args.quiet:
        print(f'  zone: {name} -- from {source}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

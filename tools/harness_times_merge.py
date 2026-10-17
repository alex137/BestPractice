#!/usr/bin/env python3
"""Git merge driver for tools/harness_check_times.json: a three-way merge of
its per-test times, so two branches that each record a test never conflict.

    git config merge.precedent-harness-times.driver \
        'python3 tools/harness_times_merge.py %O %A %B'

with `tools/harness_check_times.json merge=precedent-harness-times` in
.gitattributes. tools/bootstrap.sh writes that config at session start, in
the clone's own config, wherever .gitattributes names the driver.

WHY (2026-10-17). The file conflicted on nearly every merge that day, in
three places at once: every --record-new-times appended to one shared
"measured" line, rewrote default_seconds, and inserted its test into a
sorted list beside someone else's. Sessions resolved it by hand or with a
union of both sides, and a union brings back a test the other side
deleted: #1181's merge restored five timings #1180 had removed, and the
--as-ci partition case went red on staging. The session proposed that the
engine rebuild the file on a merge instead; Morgan, 2026-10-17: "PLEASE DO
THIS IMMEDIATELY".

THE MERGE, per test: deleted on either side (in the base, missing on that
side) stays deleted; added or changed on one side takes that side's time;
changed on both takes the larger, so a part is never dealt short. The other
fields come from our side unless only theirs changed them. Writes the
result over %A and exits 0; anything unreadable exits 1, and git leaves an
ordinary conflict, never a guess.
"""
import json
import sys


def merge(base, ours, theirs):
    """-> the merged record, from three parsed records."""
    b = base.get('seconds') or {}
    o = ours.get('seconds') or {}
    t = theirs.get('seconds') or {}
    out = {}
    for name in set(b) | set(o) | set(t):
        if name in b and (name not in o or name not in t):
            continue                      # deleted on a side: stays deleted
        if name not in o:
            out[name] = t[name]
        elif name not in t:
            out[name] = o[name]
        elif o[name] == b.get(name):
            out[name] = t[name]
        elif t[name] == b.get(name):
            out[name] = o[name]
        else:
            out[name] = max(o[name], t[name])
    rec = {}
    for key in list(ours) + [k for k in theirs if k not in ours]:
        if key == 'seconds':
            continue
        mine, other = ours.get(key), theirs.get(key)
        rec[key] = other if (key not in ours or (mine == base.get(key)
                                                 and key in theirs)) else mine
    rec['seconds'] = dict(sorted(out.items()))
    return rec


def main(argv):
    if len(argv) != 4:
        print('usage: harness_times_merge.py BASE OURS THEIRS', file=sys.stderr)
        return 2
    try:
        base, ours, theirs = (json.load(open(p, encoding='utf-8')) for p in argv[1:])
        if not all(isinstance(r, dict) for r in (base, ours, theirs)):
            raise ValueError('not a JSON object')
        rec = merge(base, ours, theirs)
    except (OSError, ValueError) as exc:
        print(f'harness_times_merge: left as a conflict ({exc})', file=sys.stderr)
        return 1
    with open(argv[2], 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(rec, indent=1, ensure_ascii=False) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

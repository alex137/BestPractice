#!/usr/bin/env python3
"""precedent_candidate.py — Stage 2 of PRACTICE_ENGINE_PLAN.md's creation
pipeline: raise, list, and expire candidates. See spec/CANDIDATE_FORMAT.md
for the file schema this reads and writes.

A candidate is NEVER a practice and is NEVER loaded into context by any
loader tool (build_views.py, precedent_paths.py, precedent_resolve.py all
ignore candidates/ entirely) — creating one costs nothing, ignoring one
costs nothing, per the plan's own text.

LEVEL DECIDES STORAGE, exactly like a practice's level decides which
repository it lives in (spec/SOURCES.md):

  individual / team  ->  a dated file in <repo path>/candidates/*.md
  universal          ->  a GitHub Issue, never a file -- tools/leak_gate.py's
                          FORBIDDEN_PATHS already bans any candidates/ or
                          outbox/ directory in Precedent, unconditionally, by
                          shape rather than content (spec/SOURCES.md,
                          "Universal candidates are GitHub Issues"). This
                          tool can only draft the Issue body -- opening it
                          needs a GitHub credential this tool does not carry,
                          which is the plan's own "Per-repo credentials...
                          not day one" deferral, not an oversight.

Usage:
  precedent_candidate.py create --level individual|team --path REPO
      --slug SLUG --title TITLE --signal SIGNAL --raised-by NAME
      --observed TEXT --proposed-rule TEXT
      [--recurrence N] [--cost-if-once TEXT] [--tier resident|on-demand]
      [--checked-by PATH] [--applies-to GLOB[,GLOB...]] [--occasion TEXT]
      [--gates NAME[,NAME...]]
  precedent_candidate.py create --level universal
      --slug SLUG --title TITLE --signal SIGNAL --raised-by NAME
      --observed TEXT --proposed-rule TEXT [--out FILE] [same optional flags]
  precedent_candidate.py list --level individual|team --path REPO [--status S]
  precedent_candidate.py list --level universal
  precedent_candidate.py expire --level individual|team --path REPO --file NAME
"""
import datetime
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# spec/CANDIDATE_FORMAT.md#signals -- closed vocabulary, same discipline
# precedent_gate.py already applies to its own `gates:` field. An unknown
# signal is a typo or an undocumented new source, and both should fail
# loudly rather than being filed as prose nobody can query later.
SIGNALS = {
    'session-judgment-at-a-gate', 'explicit-instruction', 'reverted-or-corrected',
    'repeated-instruction', 'repeated-check-failure', 'review-found-defect',
    'restated-in-second-scope',
}
LEVELS = {'individual', 'team', 'universal'}
STATUSES = {'open', 'promoted', 'expired', 'declined'}
SLUG_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


class CandidateError(Exception):
    pass


def _yaml_scalar(v):
    """Minimal, deliberate: candidate frontmatter values are all either
    plain scalars, null, or a flat list of strings -- the same restricted
    shape split_practices.py already assumes for practice frontmatter, so
    no YAML library dependency is added for a format this narrow."""
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return '[' + ', '.join(f'"{x}"' for x in v) + ']'
    v = str(v)
    if v == '' or any(c in v for c in ':#"\n') or v != v.strip():
        return '"' + v.replace('"', '\\"') + '"'
    return v


def render_candidate(fields, observed, proposed_rule):
    order = [
        'slug', 'title', 'date', 'status', 'signal', 'raised_by',
        'recurrence_count', 'cost_if_once', 'tier_requested',
        'proposed_checked_by', 'proposed_applies_to', 'proposed_occasion',
        'proposed_gates',
    ]
    lines = ['---']
    for k in order:
        lines.append(f'{k}: {_yaml_scalar(fields[k])}')
    lines.append('---')
    lines.append('## Observed')
    lines.append(observed.strip())
    lines.append('')
    lines.append('## Proposed Rule')
    lines.append(proposed_rule.strip())
    lines.append('')
    return '\n'.join(lines)


def _parse_frontmatter(text):
    """Deliberately tolerant of the same narrow shape render_candidate()
    produces -- this is a read path for files this tool itself wrote (or a
    person hand-edited following spec/CANDIDATE_FORMAT.md), not a general
    YAML parser. A malformed file fails loudly rather than silently
    misreading, the same choice split_practices.py makes for practices."""
    if not text.startswith('---\n'):
        raise CandidateError('missing frontmatter (no leading "---")')
    end = text.index('\n---', 4)
    fm_text, body = text[4:end], text[end + 4:]
    fm = {}
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        key, _, val = line.partition(':')
        key, val = key.strip(), val.strip()
        if val.startswith('[') and val.endswith(']'):
            inner = val[1:-1].strip()
            fm[key] = [] if not inner else [
                s.strip().strip('"') for s in inner.split(',')]
        elif val == 'null':
            fm[key] = None
        elif val.startswith('"') and val.endswith('"'):
            fm[key] = val[1:-1].replace('\\"', '"')
        else:
            fm[key] = val
    return fm, body.strip('\n')


def cmd_create(args):
    level = args.get('--level')
    if level not in LEVELS:
        raise CandidateError(f"--level must be one of {sorted(LEVELS)}, got {level!r}")
    slug = args.get('--slug')
    if not slug or not SLUG_RE.match(slug):
        raise CandidateError(f"--slug must be kebab-case, got {slug!r}")
    signal = args.get('--signal')
    if signal not in SIGNALS:
        raise CandidateError(
            f"--signal must be one of {sorted(SIGNALS)} (spec/CANDIDATE_FORMAT.md#signals), "
            f"got {signal!r}")
    for req in ('--title', '--raised-by', '--observed', '--proposed-rule'):
        if not args.get(req):
            raise CandidateError(f"{req} is required")
    tier = args.get('--tier', 'on-demand')
    if tier not in ('resident', 'on-demand'):
        raise CandidateError(f"--tier must be resident or on-demand, got {tier!r}")

    date = datetime.date.today().isoformat()
    fields = {
        'slug': slug,
        'title': args['--title'],
        'date': date,
        'status': 'open',
        'signal': signal,
        'raised_by': args['--raised-by'],
        'recurrence_count': int(args.get('--recurrence', '1')),
        'cost_if_once': args.get('--cost-if-once'),
        'tier_requested': tier,
        'proposed_checked_by': args.get('--checked-by'),
        'proposed_applies_to': (args['--applies-to'].split(',')
                                 if args.get('--applies-to') else ['**']),
        'proposed_occasion': args.get('--occasion'),
        'proposed_gates': args['--gates'].split(',') if args.get('--gates') else [],
    }
    if fields['recurrence_count'] < 2 and not fields['cost_if_once']:
        print(f"warning: recurrence_count is {fields['recurrence_count']} and "
              f"--cost-if-once is not set -- this candidate will fail Stage 3's "
              f"recurrence-or-cost criterion as written. Filing it anyway is "
              f"fine (creating one costs nothing); promotion will refuse it "
              f"until either recurs or a cost is stated.", file=sys.stderr)

    text = render_candidate(fields, args['--observed'], args['--proposed-rule'])

    if level == 'universal':
        out = args.get('--out')
        dest = pathlib.Path(out) if out else None
        if dest:
            dest.write_text(text, encoding='utf-8')
            print(f"drafted universal candidate body written to {dest}")
        else:
            print(text)
        print(
            "\nThis tool does NOT open a GitHub Issue -- universal candidates "
            "are filed at https://github.com/alex137/BestPractice/issues/new"
            "?template=practice-candidate.md, labeled precedent-candidate "
            "(spec/SOURCES.md#universal-candidates-are-github-issues-not-a-"
            "fourth-candidates). Paste the drafted body above into the Issue.",
            file=sys.stderr)
        return 0

    path = args.get('--path')
    if not path:
        raise CandidateError('--path REPO is required for --level individual/team')
    cand_dir = pathlib.Path(path) / 'candidates'
    cand_dir.mkdir(parents=True, exist_ok=True)
    dest = cand_dir / f'{slug}-{date}.md'
    if dest.exists():
        raise CandidateError(f'{dest} already exists -- a candidate for this '
                              f'slug was already raised today')
    dest.write_text(text, encoding='utf-8')
    print(f"candidate written: {dest}")
    return 0


def _iter_candidates(path):
    cand_dir = pathlib.Path(path) / 'candidates'
    if not cand_dir.is_dir():
        return
    for f in sorted(cand_dir.glob('*.md')):
        fm, body = _parse_frontmatter(f.read_text(encoding='utf-8'))
        yield f, fm, body


def cmd_list(args):
    level = args.get('--level')
    if level not in LEVELS:
        raise CandidateError(f"--level must be one of {sorted(LEVELS)}, got {level!r}")
    if level == 'universal':
        print("Universal candidates are GitHub Issues, not files -- this tool "
              "has no credential to list them (Per-repo credentials, deferred "
              "in PRACTICE_ENGINE_PLAN.md). Check "
              "https://github.com/alex137/BestPractice/issues?q=is%3Aissue+"
              "label%3Aprecedent-candidate directly.")
        return 0
    path = args.get('--path')
    if not path:
        raise CandidateError('--path REPO is required for --level individual/team')
    status_filter = args.get('--status')
    if status_filter and status_filter not in STATUSES:
        raise CandidateError(f"--status must be one of {sorted(STATUSES)}, got {status_filter!r}")
    n = 0
    by_slug = {}
    for f, fm, _body in _iter_candidates(path):
        if status_filter and fm.get('status') != status_filter:
            continue
        n += 1
        by_slug.setdefault(fm.get('slug'), []).append(fm)
        print(f"{f.name}: slug={fm.get('slug')!r} status={fm.get('status')!r} "
              f"signal={fm.get('signal')!r} recurrence_count={fm.get('recurrence_count')!r} "
              f"raised_by={fm.get('raised_by')!r}")
    for slug, entries in by_slug.items():
        if len(entries) > 1:
            print(f"  note: {slug!r} raised {len(entries)} times -- real recurrence "
                  f"for Stage 3, not something to hand-merge into one file "
                  f"(spec/CANDIDATE_FORMAT.md: 'a count of files, not a field "
                  f"a session has to remember to increment')")
    if n == 0:
        print(f"no candidates{' with status ' + status_filter if status_filter else ''} in {path}")
    return 0


def cmd_expire(args):
    level = args.get('--level')
    if level not in ('individual', 'team'):
        raise CandidateError("--level must be individual or team for expire "
                              "(a universal candidate is an Issue -- close it there)")
    path = args.get('--path')
    fname = args.get('--file')
    if not path or not fname:
        raise CandidateError('--path REPO and --file NAME are both required')
    target = pathlib.Path(path) / 'candidates' / fname
    if not target.exists():
        raise CandidateError(f'{target} does not exist')
    fm, body = _parse_frontmatter(target.read_text(encoding='utf-8'))
    if fm.get('status') != 'open':
        raise CandidateError(f"{target} has status {fm.get('status')!r}, not 'open' "
                              f"-- only an open candidate can be expired")
    text = target.read_text(encoding='utf-8')
    new_text = re.sub(r'^status:\s*open\s*$', 'status: expired', text,
                       count=1, flags=re.MULTILINE)
    if new_text == text:
        raise CandidateError(f"could not find 'status: open' line in {target} to rewrite")
    target.write_text(new_text, encoding='utf-8')
    print(f"expired: {target}")
    return 0


COMMANDS = {'create': cmd_create, 'list': cmd_list, 'expire': cmd_expire}


def _parse_args(argv):
    if not argv or argv[0] not in COMMANDS:
        sys.exit(f"precedent_candidate FAIL: first argument must be one of "
                  f"{sorted(COMMANDS)}, got {argv[0] if argv else None!r}")
    cmd, rest = argv[0], argv[1:]
    args = {}
    i = 0
    while i < len(rest):
        tok = rest[i]
        if not tok.startswith('--'):
            sys.exit(f"precedent_candidate FAIL: unexpected argument {tok!r} "
                      f"(expected a --flag)")
        if i + 1 >= len(rest):
            sys.exit(f"precedent_candidate FAIL: {tok} needs a value")
        args[tok] = rest[i + 1]
        i += 2
    return cmd, args


def main():
    cmd, args = _parse_args(sys.argv[1:])
    try:
        return COMMANDS[cmd](args)
    except CandidateError as e:
        sys.exit(f"precedent_candidate FAIL: {e}")


if __name__ == '__main__':
    sys.exit(main())

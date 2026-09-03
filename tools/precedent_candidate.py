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

  individual         ->  always a dated file in <repo path>/candidates/*.md.
                          There is no one else whose approval could be
                          missing -- you own the set, so a candidate here is
                          for deferring a decision, never for asking someone
                          else's permission.
  team               ->  a dated file in <repo path>/candidates/*.md BY
                          DEFAULT, same as individual -- but pass --as-issue
                          to draft a GitHub Issue on that team repo instead.
                          WHICH ONE TO USE IS ABOUT AUTHORITY, NOT ACCESS
                          (2026-09-02, added after a real dependent-repo
                          session worked through this): if whoever is
                          raising this is already a listed approver in the
                          team repo's approvers.json, their own say-so is
                          the approval PRACTICE_ENGINE_PLAN.md already
                          describes ("for a small team ... the session
                          commits it directly") -- promote and land it now,
                          skip raising a candidate at all. Raise a candidate
                          only when you're deliberately deferring, or when
                          --as-issue's real case applies: the person raising
                          it is NOT a listed approver, so no amount of git
                          write access changes the fact that someone else's
                          yes is actually needed. A quiet candidates/ file
                          nobody is watching for doesn't accomplish that; an
                          Issue does. This tool nudges (does not require)
                          landing directly instead, when --raised-by is
                          already on the approvers list.
  universal          ->  a GitHub Issue, never a file -- tools/leak_gate.py's
                          FORBIDDEN_PATHS already bans any candidates/ or
                          outbox/ directory in Precedent, unconditionally, by
                          shape rather than content (spec/SOURCES.md,
                          "Universal candidates are GitHub Issues"). This
                          tool can only draft the Issue body -- opening it
                          needs a GitHub credential this tool does not carry,
                          which is the plan's own "Per-repo credentials...
                          not day one" deferral, not an oversight. The same
                          is true of a team --as-issue draft: this tool
                          drafts the body and, best-effort, the target URL --
                          it never calls the GitHub API itself.

Usage:
  precedent_candidate.py create --level individual|team --path REPO
      --slug SLUG --title TITLE --signal SIGNAL --raised-by NAME
      --observed TEXT --proposed-rule TEXT
      [--recurrence N] [--cost-if-once TEXT] [--tier resident|on-demand]
      [--checked-by PATH] [--applies-to GLOB[,GLOB...]] [--occasion TEXT]
      [--gates NAME[,NAME...]]
  precedent_candidate.py create --level team --path REPO --as-issue true
      [--github-repo OWNER/REPO] [--out FILE] [same required/optional flags
      as above except --path's candidates/ dir is not written to]
  precedent_candidate.py create --level universal
      --slug SLUG --title TITLE --signal SIGNAL --raised-by NAME
      --observed TEXT --proposed-rule TEXT [--out FILE] [same optional flags]
  precedent_candidate.py list --level individual|team --path REPO [--status S]
  precedent_candidate.py list --level universal
  precedent_candidate.py expire --level individual|team --path REPO --file NAME
"""
import datetime
import json
import pathlib
import re
import subprocess
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


def _escape_scalar(v):
    """Shared by the plain-scalar and list-item paths: backslash-escape a
    quote or embedded newline so a value containing either survives being
    written inside a double-quoted frontmatter scalar. Does not escape a
    bare backslash itself -- narrow and deliberate, same as the rest of
    this parser; a value containing a literal backslash followed by `n` or
    `"` is a known, accepted gap for a format this restricted."""
    return v.replace('"', '\\"').replace('\n', '\\n')


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
        return '[' + ', '.join('"' + _escape_scalar(str(x)) + '"' for x in v) + ']'
    v = str(v)
    if v == '' or any(c in v for c in ':#"\n,[]') or v != v.strip():
        return '"' + _escape_scalar(v) + '"'
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


_GITHUB_REMOTE_RE = re.compile(
    r'^(?:https://github\.com/|git@github\.com:)([^/]+)/([^/]+?)(?:\.git)?$')


def _detect_github_repo(path):
    """Best-effort owner/repo for the clone at `path`, read from its own
    'origin' remote -- never guessed from `path`'s name or from
    approvers.json, since neither reliably names the actual GitHub location.
    Returns None on anything short of a clean match (no git, no origin, a
    non-GitHub remote); the caller falls back to requiring --github-repo
    explicitly rather than drafting a URL that might be wrong."""
    try:
        r = subprocess.run(['git', '-C', str(path), 'remote', 'get-url', 'origin'],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    m = _GITHUB_REMOTE_RE.match(r.stdout.strip())
    return (m.group(1), m.group(2)) if m else None


def _approver_names(path):
    """Every name/github-handle approvers.json lists for the team repo at
    `path`, or an empty set if it has none / isn't parseable -- a missing or
    broken approvers.json is not this function's problem to raise, only
    precedent_land.py's when it actually tries to land against it."""
    approvers_path = pathlib.Path(path) / 'approvers.json'
    if not approvers_path.is_file():
        return set()
    try:
        data = json.loads(approvers_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return set()
    names = set()
    for a in data.get('approvers', []):
        if a.get('name'):
            names.add(a['name'])
        if a.get('github'):
            names.add(a['github'])
    return names


def _nudge_if_already_approver(path, raised_by):
    """Print a note (never a refusal -- deferring a decision is a legitimate
    reason to raise a candidate even as an approver) when `raised_by` is
    already a listed approver: PRACTICE_ENGINE_PLAN.md's own allowance for a
    small team is that a listed approver's say-so lands a practice directly,
    so raising a candidate at all is the slower path for them specifically."""
    if raised_by in _approver_names(path):
        print(
            f"note: {raised_by!r} is already a listed approver for this team "
            f"set. If you're landing this yourself right now, "
            f"precedent_promote.py then precedent_land.py --approved-by "
            f"{raised_by!r} lands it directly -- no candidate needed. "
            f"Raising one anyway is fine if you'd rather defer the decision "
            f"or leave a record first.", file=sys.stderr)


def _split_list_items(inner):
    """Comma-split `inner` (the text between a list's `[` and `]`) without
    breaking on a comma that falls inside a quoted item -- a glob or gate
    name is unlikely to contain one, but a hand-edited or adversarial
    candidate might (spec/CANDIDATE_FORMAT.md's own list fields are plain
    strings, not enums, so nothing stops it)."""
    items, buf, in_quotes = [], [], False
    i = 0
    while i < len(inner):
        c = inner[i]
        if c == '"' and (i == 0 or inner[i - 1] != '\\'):
            in_quotes = not in_quotes
            buf.append(c)
        elif c == ',' and not in_quotes:
            items.append(''.join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    items.append(''.join(buf))
    return items


def _unescape_scalar(v):
    return v.replace('\\"', '"').replace('\\n', '\n')


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
                _unescape_scalar(s.strip().strip('"')) for s in _split_list_items(inner)]
        elif val == 'null':
            fm[key] = None
        elif val.startswith('"') and val.endswith('"'):
            fm[key] = _unescape_scalar(val[1:-1])
        else:
            fm[key] = val
    return fm, body.strip('\n')


def split_candidate_sections(body):
    """Split a candidate's post-frontmatter body into (observed, proposed_rule).

    Splits on the LAST line that is exactly `## Proposed Rule`, not the
    first. A naive first-match split breaks the moment Observed prose
    quotes that heading verbatim -- a real risk, not a hypothetical one: a
    candidate about a heading-collision bug, or one that pastes markdown
    containing that literal line, truncates Observed and folds the rest of
    it into Proposed Rule. render_candidate() only ever writes the heading
    once, so the last (only) real match is always the actual section
    boundary regardless of what Observed contains earlier."""
    matches = list(re.finditer(r'^## Proposed Rule\s*$', body, re.M))
    if not matches:
        return body.strip(), ''
    split_at = matches[-1]
    observed_part = re.sub(r'^## Observed\s*\n', '', body[:split_at.start()], count=1)
    proposed_rule = body[split_at.end():].strip()
    return observed_part.strip(), proposed_rule


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
    # Every flag in this tool's arg parser takes a value (_parse_args has no
    # bare-boolean-flag support) -- so this is `--as-issue true`, not a bare
    # `--as-issue`, for consistency with the rest of the tool's own style.
    as_issue = args.get('--as-issue') == 'true'
    if as_issue and level != 'team':
        raise CandidateError(
            "--as-issue only applies to --level team. Individual is always "
            "your own to land directly -- there's no one else whose "
            "permission a candidate could stand in for, so an Issue has no "
            "one to notify. Universal is already always an Issue; --as-issue "
            "would be redundant.")

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
            "\nDISCLOSE TO THE HUMAN: this is a proposal for EVERYONE using "
            "Precedent, not yet a practice and not yet in force for anyone. "
            "This tool does NOT open a GitHub Issue -- universal candidates "
            "are filed at https://github.com/alex137/BestPractice/issues/new"
            "?template=practice-candidate.md, labeled precedent-candidate "
            "(spec/SOURCES.md#universal-candidates-are-github-issues-not-a-"
            "fourth-candidates). Paste the drafted body above into the Issue.",
            file=sys.stderr)
        return 0

    path = args.get('--path')
    if not path:
        raise CandidateError('--path REPO is required for --level individual/team')

    if level == 'team':
        _nudge_if_already_approver(path, fields['raised_by'])

    if as_issue:
        owner_repo = args.get('--github-repo')
        if owner_repo:
            if '/' not in owner_repo:
                raise CandidateError(f"--github-repo must be OWNER/REPO, got {owner_repo!r}")
            owner, repo_name = owner_repo.split('/', 1)
        else:
            detected = _detect_github_repo(path)
            if not detected:
                raise CandidateError(
                    f"could not detect a GitHub owner/repo from {path}'s "
                    f"'origin' remote -- pass --github-repo OWNER/REPO "
                    f"explicitly.")
            owner, repo_name = detected
        out = args.get('--out')
        dest = pathlib.Path(out) if out else None
        if dest:
            dest.write_text(text, encoding='utf-8')
            print(f"drafted team candidate body written to {dest}")
        else:
            print(text)
        print(
            f"\nDISCLOSE TO THE HUMAN: this is a proposal for the TEAM set "
            f"at {path}, not yet a practice and not yet in force for "
            f"anyone. This tool does NOT open a GitHub Issue -- file this at "
            f"https://github.com/{owner}/{repo_name}/issues/new"
            f"?labels=precedent-candidate (add a matching issue template "
            f"there if you want the form pre-structured; none is required "
            f"for this to work). Paste the drafted body above into the "
            f"Issue. Nothing was written to {path}/candidates/ -- this is "
            f"the alternative to that, for when whoever's raising it is not "
            f"a listed approver (spec/CANDIDATE_FORMAT.md#where-a-"
            f"candidate-lives).", file=sys.stderr)
        return 0

    cand_dir = pathlib.Path(path) / 'candidates'
    cand_dir.mkdir(parents=True, exist_ok=True)
    dest = cand_dir / f'{slug}-{date}.md'
    if dest.exists():
        # A same-day, same-slug raise is a genuine recurrence, not an error
        # (spec/CANDIDATE_FORMAT.md: "a count of files, not a field a
        # session has to remember to increment") -- suffix a sequence number
        # rather than refusing outright, which used to silently drop the
        # signal Stage 3's recurrence criterion is built to capture.
        n = 2
        while (cand_dir / f'{slug}-{date}-{n}.md').exists():
            n += 1
        dest = cand_dir / f'{slug}-{date}-{n}.md'
    dest.write_text(text, encoding='utf-8')
    print(f"candidate written: {dest}")
    if level == 'individual':
        print(f"DISCLOSE TO THE HUMAN: this is a proposal only, sitting in "
              f"YOUR OWN individual set ({path}) -- not yet a practice, and "
              f"not yet in force. You are the only one who can promote and "
              f"land it (precedent_promote.py then "
              f"precedent_land.py --approved-by NAME); nothing happens to "
              f"it until you do.")
    elif fields['raised_by'] in _approver_names(path):
        print(f"DISCLOSE TO THE HUMAN: this is a proposal only, filed in "
              f"the TEAM set at {path} -- not yet a practice, and not yet "
              f"in force for anyone. It needs a listed approver's yes "
              f"(precedent_land.py --approved-by NAME) before it lands; "
              f"raised_by ({fields['raised_by']!r}) is already an approver "
              f"here, so that yes can happen in this same conversation if "
              f"that is what's wanted instead of leaving it queued.")
    else:
        print(f"DISCLOSE TO THE HUMAN, PLAINLY: {fields['raised_by']!r} is "
              f"NOT a listed approver for the TEAM set at {path}, and "
              f"nothing is watching this candidates/ directory for a new "
              f"file -- this proposal will very likely sit unseen. Say so, "
              f"and suggest --as-issue true instead so an approver actually "
              f"gets notified (spec/CANDIDATE_FORMAT.md#which-one-for-team-"
              f"file-or-issue).")
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


def set_candidate_status(target, new_status, required_current='open'):
    """Rewrite a candidate file's `status:` field in place -- shared by
    cmd_expire and precedent_land.py's post-landing update, so a candidate
    that has actually been landed does not sit reading `status: open`
    forever (list --status open would otherwise keep surfacing it as if it
    still needed a decision, and nothing would stop a second promote/land
    of the same already-landed file)."""
    target = pathlib.Path(target)
    if not target.exists():
        raise CandidateError(f'{target} does not exist')
    text = target.read_text(encoding='utf-8')
    fm, _body = _parse_frontmatter(text)
    if required_current is not None and fm.get('status') != required_current:
        raise CandidateError(
            f"{target} has status {fm.get('status')!r}, not {required_current!r} "
            f"-- only a {required_current!r} candidate can become {new_status!r}")
    new_text = re.sub(rf'^status:\s*{re.escape(fm.get("status"))}\s*$',
                       f'status: {new_status}', text, count=1, flags=re.MULTILINE)
    if new_text == text:
        raise CandidateError(f"could not find the status line in {target} to rewrite")
    target.write_text(new_text, encoding='utf-8')


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
    set_candidate_status(target, 'expired', required_current='open')
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

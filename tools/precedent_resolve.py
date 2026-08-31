#!/usr/bin/env python3
"""precedent_resolve.py — resolve the three sources into one set of practices
(PRACTICE_ENGINE_PLAN.md, "Source — Who a Practice Belongs To" and
"Precedence, and the One Case Where the Individual Does Not Win").

A practice's LEVEL is not a field. It is implied by which repository the file
lives in, "so it cannot drift from reality" — universal in Precedent, team in
one private repo per team, individual in one private repo per person. This
tool is what turns "three repositories" into "the practices in force here".

WHO DECLARES WHICH SOURCE, AND WHY THAT SPLIT IS A PRIVACY BOUNDARY RATHER
THAN A CONVENIENCE.

  The CONSUMER REPO declares universal plus its team set, in a tracked config
  file (precedent.json). Everyone working there gets those, and everyone
  working there can already read them.

  THE PERSON declares their own individual set in their USER-LEVEL config,
  outside any shared repo (~/.config/precedent/config.json, or wherever
  PRECEDENT_USER_CONFIG points). If a project repo named someone's individual
  set it would leak that set's existence and location to everyone on the
  team, and their sessions would try to fetch a repository they cannot read.

  So two people working in the same repo resolve DIFFERENT sets, each seeing
  their own personal practices and neither seeing the other's. That falls out
  of where the declaration lives; it is not a rule anyone has to remember.

PRECEDENCE is individual > team > universal, by slug — RPP's `bestpractice-
wins` generalized into the engine, so it is a property of the resolver rather
than a rule written down and hoped to be read. A practice may also name a
lower-source slug in `overrides:` to replace a practice it does not share a
name with.

THE ONE CASE WHERE THE INDIVIDUAL DOES NOT WIN. A team or universal practice
marked `severity: blocking` cannot be overridden by a higher-precedence
source. Plain precedence would let a personal "keep the tone casual" beat a
team's "this client work is always formal", which is right for how a person
works and wrong for what a shared deliverable looks like. This is the
difference between a practice about HOW I WORK and one about WHAT WE SHIP.

DEGRADING GRACEFULLY IS PART OF THE CONTRACT, not an error path. A fresh
cloud session with no persistent home directory has no local individual set.
When a declared source is missing, the resolver runs on what it has and SAYS
SO — it never silently pretends personal practices were applied. A missing
source is reported on stderr and in `--json` under "missing"; only a
malformed source, or two practices at the same level claiming one slug, is
fatal.

Run:
  python3 tools/precedent_resolve.py                 # resolve, human-readable
  python3 tools/precedent_resolve.py --json          # the resolved set as data
  python3 tools/precedent_resolve.py --repo DIR      # resolve for another repo
  python3 tools/precedent_resolve.py --explain SLUG  # how one slug resolved
  python3 tools/precedent_resolve.py --strict        # a missing source is fatal
Exit: 0 on a resolved set, 1 on a conflict, a malformed source, or --strict
with a source missing.
"""
import json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import build_views as bv

REPO_CONFIG = 'precedent.json'
USER_CONFIG_ENV = 'PRECEDENT_USER_CONFIG'
DEFAULT_USER_CONFIG = pathlib.Path.home() / '.config' / 'precedent' / 'config.json'

# Lowest first: later sources win, which is what makes `PRECEDENCE.index()`
# the whole precedence rule rather than a chain of comparisons.
PRECEDENCE = ('universal', 'team', 'individual')

# A practice that is not active is resolvable by slug -- so `supersedes:`
# still points somewhere real -- but is not in force.
IN_FORCE_STATUS = 'active'


class ResolveError(Exception):
    """A source that cannot be resolved at all, as opposed to one that is
    merely absent. Raised rather than sys.exit()ed so the verification
    harness can call this module in-process without an uncaught SystemExit
    taking the whole run down (the same fix phase 2 made for build_views)."""


def _read_json(path, what):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ResolveError(f"{what} at {path} is not valid JSON ({e}). A config the "
                           f"resolver cannot read is not an empty config.")


def load_config(repo, user_config=None):
    """-> list of {level, name, path}, lowest precedence first.

    The repo config may name universal and team sources only. An individual
    source declared in a SHARED repo is refused by name, because that is the
    privacy boundary above, and a mistake that is silent here is a mistake
    nobody finds."""
    sources = []
    repo_cfg_path = pathlib.Path(repo) / REPO_CONFIG
    if repo_cfg_path.exists():
        cfg = _read_json(repo_cfg_path, 'the repository config')
        for entry in cfg.get('sources', []):
            level = entry.get('level')
            if level == 'individual':
                raise ResolveError(
                    f"{repo_cfg_path} declares an individual source "
                    f"({entry.get('name')!r}). A shared repository may only name "
                    f"sources everyone in it can read -- naming an individual set "
                    f"here leaks its existence and location to the whole team, and "
                    f"every other person's session would try to fetch a repository "
                    f"they cannot read. Declare it in your user-level config "
                    f"instead ({DEFAULT_USER_CONFIG}).")
            if level not in PRECEDENCE:
                raise ResolveError(
                    f"{repo_cfg_path}: source {entry.get('name')!r} has level "
                    f"{level!r}; expected one of {', '.join(PRECEDENCE)}.")
            sources.append({'level': level, 'name': entry.get('name', level),
                            'path': str((pathlib.Path(repo) / entry['path']).resolve())})

    user_cfg_path = pathlib.Path(user_config) if user_config else pathlib.Path(
        os.environ.get(USER_CONFIG_ENV, str(DEFAULT_USER_CONFIG))).expanduser()
    if user_cfg_path.exists():
        cfg = _read_json(user_cfg_path, 'the user config')
        ind = cfg.get('individual')
        if ind:
            sources.append({'level': 'individual',
                            'name': ind.get('name', 'precedent-individual'),
                            'path': str(pathlib.Path(ind['path']).expanduser())})
    sources.sort(key=lambda s: PRECEDENCE.index(s['level']))
    return sources


def load_source(source):
    """-> ({slug: practice}, missing_reason or None). A source directory holds
    its practices in practices/, the same layout Precedent itself uses."""
    d = pathlib.Path(source['path']) / 'practices'
    if not d.is_dir():
        return {}, f"{source['path']} has no practices/ directory"
    out = {}
    for f in sorted(d.glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError as e:
            raise ResolveError(f"{source['name']}: {e}")
        slug = fm.get('slug', f.stem)
        if slug in out:
            raise ResolveError(
                f"{source['name']}: two practices claim the slug {slug!r} "
                f"({out[slug]['file']} and {f}). Slugs are identities; the "
                f"resolver cannot choose between two at the same level.")
        out[slug] = {'slug': slug, 'level': source['level'],
                     'source': source['name'], 'file': str(f), 'fm': fm,
                     'sections': sections}
    return out, None


def resolve(sources):
    """-> {'practices': {slug: practice}, 'shadowed': [...], 'blocked': [...],
           'missing': [...], 'retired': [...]}

    Sources are walked lowest precedence first, so a later source simply
    replaces what an earlier one put in place -- except where the practice it
    would replace is `severity: blocking` at team or universal level, which is
    the one case the individual does not win."""
    by_source, missing = [], []
    for s in sources:
        loaded, why = load_source(s)
        if why:
            missing.append({'level': s['level'], 'name': s['name'], 'reason': why})
            continue
        by_source.append((s, loaded))

    resolved, shadowed, blocked, retired = {}, [], [], []
    for _s, loaded in by_source:                      # lowest precedence first
        for slug, practice in sorted(loaded.items()):
            if bv._json_str(practice['fm'].get('status', 'active')) != IN_FORCE_STATUS:
                retired.append(practice)
                continue
            # A practice replaces the same slug from a lower source, and may
            # additionally name a differently-named lower practice in
            # `overrides:`.
            targets = [slug]
            ov = bv._json_str(practice['fm'].get('overrides', 'null'))
            if ov and ov != 'null' and ov != slug:
                targets.append(ov)

            own_slug_refused = False
            for target in targets:
                prior = resolved.get(target)
                if prior is None:
                    continue
                if _is_blocking(prior):
                    blocked.append({'slug': target, 'kept': prior,
                                    'refused': practice})
                    if target == slug:
                        own_slug_refused = True
                    continue
                shadowed.append({'slug': target, 'shadowed': prior, 'by': practice})
                del resolved[target]
            if not own_slug_refused:
                resolved[slug] = practice
    return {'practices': resolved, 'shadowed': shadowed, 'blocked': blocked,
            'missing': missing, 'retired': retired}


def _is_blocking(practice):
    return (bv._json_str(practice['fm'].get('severity', 'default')) == 'blocking'
            and practice['level'] in ('team', 'universal'))


def _report(res, sources, out=sys.stdout):
    counts = {}
    for p in res['practices'].values():
        counts[p['level']] = counts.get(p['level'], 0) + 1
    print(f"resolved {len(res['practices'])} practice(s) from "
          f"{len(sources) - len(res['missing'])} source(s): "
          + ', '.join(f"{counts.get(l, 0)} {l}" for l in reversed(PRECEDENCE)), file=out)
    for s in res['shadowed']:
        print(f"  overridden: {s['slug']} -- {s['by']['level']} "
              f"({s['by']['source']}) replaces {s['shadowed']['level']} "
              f"({s['shadowed']['source']})", file=out)
    for b in res['blocked']:
        print(f"  NOT overridden: {b['slug']} -- {b['kept']['level']} "
              f"({b['kept']['source']}) is severity: blocking, so the "
              f"{b['refused']['level']} practice does not replace it", file=out)
    for r in res['retired']:
        print(f"  not in force: {r['slug']} ({r['source']}) is status: "
              f"{bv._json_str(r['fm'].get('status'))}", file=out)


def main():
    args = sys.argv[1:]
    known = {'--json', '--repo', '--explain', '--strict', '--user-config'}
    repo, explain, user_config = str(ROOT), None, None
    for flag, target in (('--repo', 'repo'), ('--explain', 'explain'),
                         ('--user-config', 'user_config')):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                sys.exit(f"precedent resolve FAIL: {flag} needs a value.")
            value = args[i + 1]
            args = args[:i] + args[i + 2:]
            if target == 'repo':
                repo = value
            elif target == 'explain':
                explain = value
            else:
                user_config = value
    unknown = [a for a in args if a.startswith('--') and a not in known]
    if unknown:
        sys.exit(f"precedent resolve FAIL: unknown option(s) {', '.join(unknown)} -- "
                 f"known options are {', '.join(sorted(known))}.")

    try:
        sources = load_config(repo, user_config)
        # NO sources at all is not an empty resolved set, it is an unconfigured
        # repository -- and "resolved 0 practices" printed with exit 0 is the
        # same confident all-clear from a check that never ran that this
        # project has now been bitten by three times.
        if not sources:
            sys.exit(
                f"precedent resolve FAIL: no practice sources are declared for "
                f"{repo}. A repository using Precedent declares its universal and "
                f"team sources in a tracked {REPO_CONFIG}; a person declares their "
                f"own individual set in their user-level config "
                f"({DEFAULT_USER_CONFIG}, or {USER_CONFIG_ENV}). Nothing was "
                f"resolved because nothing was asked for -- that is not an empty "
                f"answer, it is no question.")
        res = resolve(sources)
    except ResolveError as e:
        sys.exit(f"precedent resolve FAIL: {e}")

    # A missing source is reported, never silently absorbed: "personal
    # practices are missing" and "you have no personal practices" must not
    # look the same.
    for m in res['missing']:
        print(f"precedent resolve: the {m['level']} source {m['name']!r} is not "
              f"available ({m['reason']}). Running WITHOUT it -- the practices it "
              f"holds are not in force in this session.", file=sys.stderr)
    if res['missing'] and '--strict' in args:
        return 1

    if explain:
        return _explain(explain, res, sources)
    if '--json' in args:
        rows = [{'slug': p['slug'], 'level': p['level'], 'source': p['source'],
                 'tier': bv._json_str(p['fm'].get('tier', 'on-demand')),
                 'severity': bv._json_str(p['fm'].get('severity', 'default'))}
                for p in res['practices'].values()]
        print(json.dumps({
            'sources': sources,
            'practices': sorted(rows, key=lambda r: r['slug']),
            'overridden': [{'slug': s['slug'], 'by': s['by']['level'],
                            'was': s['shadowed']['level']} for s in res['shadowed']],
            'blocked': [{'slug': b['slug'], 'kept': b['kept']['level'],
                         'refused': b['refused']['level']} for b in res['blocked']],
            'missing': res['missing'],
        }, indent=2, sort_keys=True))
        return 0
    _report(res, sources)
    return 0


def _explain(slug, res, sources):
    p = res['practices'].get(slug)
    if p:
        print(f"{slug}: in force from the {p['level']} source "
              f"({p['source']}), {p['file']}")
    for s in res['shadowed']:
        # Match on BOTH ends: `--explain` on the practice that did the
        # overriding is the more natural question, and matching only the
        # target slug answered it with silence.
        if s['by']['slug'] == slug:
            print(f"  overrides the {s['shadowed']['level']} practice "
                  f"{s['shadowed']['slug']!r} at {s['shadowed']['file']}")
        elif s['slug'] == slug:
            print(f"  the {s['by']['level']} practice {s['by']['slug']!r} at "
                  f"{s['by']['file']} replaced this one; it is not in force")
    for b in res['blocked']:
        if b['slug'] == slug:
            print(f"  a {b['refused']['level']} practice at {b['refused']['file']} "
                  f"tried to override this and was refused: the "
                  f"{b['kept']['level']} practice is severity: blocking")
    if not p and not any(b['slug'] == slug for b in res['blocked']) \
            and not any(s['slug'] == slug for s in res['shadowed']):
        print(f"precedent resolve: no practice with slug {slug!r} in the resolved "
              f"set ({len(res['practices'])} practices from "
              f"{len(sources)} source(s)).")
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""practice_simulation.py -- phase 2 of spec/SIMULATION_BRIEF.md: synthetic
scenario generation, replacing tools/routing_eval.py's fixed 20-commit case
set with cases that are INVENTED, not replayed.

WHY. Morgan's own objection to phase 1's plan: replaying the same historical
commits over and over is not a simulation, and tunes the loader's own inputs
(globs, occasion wording) against the exact set that scores it -- the v5
round in spec/LOADER.md already shows this happening ("a glob pass converted
reach failures into judgment failures on the SAME 20 cases"). A fixed
benchmark you optimize against stops being evidence.

WHAT THIS DOES INSTEAD. For a sample of on-demand practices (fresh each
batch -- see "new-batch" below), a generation prompt asks for THREE
scenarios per practice, never reused across batches:
  positive     a fictional situation that should trigger the practice.
  negative     a near-miss that resembles the trigger on the surface but
               should NOT trigger it.
  adversarial  a situation that genuinely calls for the practice, framed to
               look like something else or easy to miss -- this is the case
               the plain positive case does not test.
Each scenario also names 1-3 plausible file paths it touches, so the REAL
path-triggered channel (tools/precedent_paths.py, not a re-implementation of
it) can be exercised mechanically, exactly as spec/LOADER.md's other evals
do.

THIS TOOL NEVER GENERATES OR JUDGES ANYTHING ITSELF. Like
tools/routing_eval.py before it, it only manages the file-based handoff: it
writes prompts, and a person -- directly, or by explicitly asking an agent
session to in that turn -- runs them and saves the results back. Nothing
here calls a model API, imports a model client, or is invoked from a hook,
gate, or session-start script, and it must never be wired to one: every
step below is a file written by this tool and a file a PERSON chooses to
fill in by running the prompt. See "Never automatic" in
spec/SIMULATION_BRIEF.md.

WHAT V1 DOES NOT DO, STATED PLAINLY. It measures ROUTING (did the loader's
real resident block + occasion index + real path-channel output lead to
naming the right practice), single-hop only (the cheapest arm
spec/ATTENTION_CEILING.md already validates as legitimate, not an ad hoc
shortcut). It does NOT yet have the treatment agent perform the synthetic
task and run a real checked_by script against the output (behavioral_replay
--with-checks phase 1's mechanical-correctness idea, extended to synthetic
work) -- that needs a real sandboxed workspace for the agent to edit files
in, which this file-based prompt/answer handoff does not provide. That is
real, separate, harder follow-on work, not silently folded in here.

PHASE 3: MULTI-REPO (spec/SIMULATION_BRIEF.md section 6). `new-batch` and
`route` accept `--repo-root PATH`, pointing every step at a DIFFERENT
repo's own materialized practice set and its own generated loader block --
not BestPractice's. This is the test a single-repo simulation structurally
cannot do: whether routing AND source precedence (a repo-local override
correctly taking priority over the universal practice it overrides) hold
somewhere other than here. No real dependent repo was attached to the
session that built this, so `build-fixture-repo` constructs one: a small,
committed, honestly-labeled FIXTURE consumer repo at
evals/simulation/fixtures/demo-consumer-repo/, with its own fictional file
tree and one repo-local override, materialized through the real
tools/precedent_sync_views.py / tools/precedent_materialize.py pipeline
this repo already ships and already tests -- never a re-implementation of
source resolution. A REAL dependent repo works exactly the same way: attach
it, point --repo-root at its checkout (it needs its own precedent.json and
a synced AGENTS.md already, the way any real Precedent install does), and
everything below runs unchanged. Batches against different repos are
reported separately, never pooled into one score -- see "score" below.

Run:
  python3 tools/practice_simulation.py new-batch [--count N] [--seed S]
                                                  [--practices SLUG,SLUG,...]
                                                  [--repo-root PATH]
  python3 tools/practice_simulation.py route --batch BATCH_ID
  python3 tools/practice_simulation.py score --batch BATCH_ID
  python3 tools/practice_simulation.py build-fixture-repo [--out DIR]
  python3 tools/practice_simulation.py --list-batches
"""
import datetime, json, pathlib, random, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import build_views as bv
import precedent_paths as pp

SIM_DIR = ROOT / 'evals' / 'simulation'
BATCHES_DIR = SIM_DIR / 'batches'
DEFAULT_FIXTURE_REPO = SIM_DIR / 'fixtures' / 'demo-consumer-repo'
KINDS = ('positive', 'negative', 'adversarial')


def _practices_from(practices_dir):
    """(fm, sections) for every active, on-demand practice under an
    arbitrary practices/ directory -- generalizes _active_on_demand_practices
    to a materialized CONSUMER repo's own resolved set, not just this
    repo's. Reuses split_practices._read_practice_file, the one code path
    every other loader in this codebase reads a practice file through."""
    out = []
    for f in sorted(pathlib.Path(practices_dir).glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError:
            continue
        if fm.get('tier') == 'on-demand' and fm.get('status') == 'active':
            out.append((fm, sections))
    return out


def _on_demand_narrow_from(practices_dir):
    """(slug, narrow_globs, rule) for a directory's own on-demand
    practices -- the same shape tools/precedent_paths.py's own
    load_on_demand_practices() returns, generalized off this repo's
    hardcoded practices/. Matching itself still goes through
    pp.path_matches -- the real glob semantics, not a second
    implementation of them."""
    out = []
    for fm, sections in _practices_from(practices_dir):
        globs = pp._globs(fm.get('applies_to', '[]'))
        narrow = [g for g in globs if g != '**']
        if narrow:
            out.append((fm['slug'], narrow, sections.get('rule', '')))
    return out


def _matches_for_paths_against(paths, on_demand_narrow):
    hits = []
    for slug, globs, _rule in on_demand_narrow:
        for path in paths:
            if any(pp.path_matches(path, g) for g in globs):
                hits.append((slug, path))
                break
    return hits


def _loader_block_text_at(repo_root):
    """The real generated loader block from a given repo's own AGENTS.md --
    BestPractice's when repo_root is this repo, a consumer repo's own
    materialized one otherwise. Same extraction _loader_block_text() below
    does for this repo; kept as one parameterized function rather than two
    copies."""
    agents_md = pathlib.Path(repo_root) / 'AGENTS.md'
    if not agents_md.exists():
        sys.exit(f'practice_simulation FAIL: no AGENTS.md at {agents_md} -- '
                 f'has this repo been synced (tools/precedent_sync_views.py '
                 f'--repo {repo_root}), or the fixture built '
                 f'(build-fixture-repo)?')
    text = agents_md.read_text(encoding='utf-8', errors='ignore')
    m = re.search(re.escape(bv.BEGIN_MARKER) + r'.*?' + re.escape(bv.END_MARKER),
                  text, re.S)
    if not m:
        sys.exit(f'practice_simulation FAIL: {agents_md} has no generated loader '
                 f'block to read -- has it been synced yet?')
    return m.group(0)


def _real_file_sample(repo_root, limit=40):
    """A sample of this repo's OWN real committed file paths, for grounding
    a generation prompt in its actual conventions (spec/SIMULATION_BRIEF.md
    section 6: "using that repo's actual file tree and conventions... not
    BestPractice's own"). Derived paths (precedent_materialize.py's own
    output) are excluded -- they're an artifact of running this tool, not a
    convention of the repo being simulated."""
    repo_root = pathlib.Path(repo_root)
    r = subprocess.run(['git', 'ls-files'], cwd=str(repo_root),
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        files = r.stdout.split()
    else:
        files = [str(p.relative_to(repo_root)) for p in repo_root.rglob('*')
                 if p.is_file()]
    excluded_dirs = ('practices/', 'local/practices/')
    excluded_names = {'precedent.json', 'AGENTS.md', 'MANIFEST.json'}
    files = [f for f in files if not any(f.startswith(d) for d in excluded_dirs)
             and pathlib.PurePath(f).name not in excluded_names]
    return sorted(files)[:limit]


def _active_on_demand_practices():
    """(fm, sections) for every active, on-demand practice -- the pool a
    batch samples from. Resident practices are excluded: they are never
    reached through routing at all (never loaded, or always loaded),
    which is exactly what this eval is testing."""
    out = []
    for fm, sections, _f in bv.load_practices():
        if fm.get('tier') == 'on-demand' and fm.get('status') == 'active':
            out.append((fm, sections))
    return out


def _loader_block_text():
    """The REAL resident block + occasion index + standing instruction, read
    from AGENTS.md's own generated block -- not a re-derivation of it. If
    the block were regenerated with build_views.py instead, a routing
    prompt built from a stale copy would silently test something that no
    longer matches what a real session sees; reading the committed file
    keeps this honest by construction."""
    text = (ROOT / 'AGENTS.md').read_text(encoding='utf-8', errors='ignore')
    m = re.search(re.escape(bv.BEGIN_MARKER) + r'.*?' + re.escape(bv.END_MARKER),
                  text, re.S)
    if not m:
        sys.exit('practice_simulation FAIL: could not find the generated loader '
                 'block in AGENTS.md -- has the marker been renamed?')
    return m.group(0)


GENERATE_PROMPT_TEMPLATE = """\
You are helping build a routing-quality simulation for a practice-loading \
system. Below is one practice's full Rule. Invent THREE SHORT, independent, \
fictional work scenarios for it, each 3-6 sentences, as if describing a \
real task someone is partway through in a software repository.

Do not mention the practice's name, slug, or quote its Rule back. A \
reader must recognize the practice applies (or doesn't) from the situation \
alone, the way a real session would.

PRACTICE RULE (for your reference only -- do not reveal it in your answer):
---
{rule}
---

Write exactly this JSON object and nothing else (no markdown fence, no \
commentary before or after):

{{
  "positive": {{
    "scenario": "<a situation where this practice's Rule clearly applies>",
    "files": ["<1-3 plausible file paths this work touches>"]
  }},
  "negative": {{
    "scenario": "<a situation that superficially RESEMBLES the trigger -- similar words, similar setting -- but where the Rule does NOT actually apply, and a careful reader should say so>",
    "files": ["<1-3 plausible file paths>"]
  }},
  "adversarial": {{
    "scenario": "<a situation where the Rule genuinely DOES apply, but framed to look like a different kind of task, or easy to miss on a quick read -- the hardest true positive you can construct>",
    "files": ["<1-3 plausible file paths>"]
  }}
}}

{file_hint} Do not invent a path that would trivially give away the answer \
by naming the practice.
"""

GENERIC_FILE_HINT = (
    "File paths should look like real paths in a software repository (this "
    "repository's own conventions -- practices/, tools/, spec/, docs, etc. -- "
    "are fine to draw on, or plausible equivalents)."
)


def _repo_file_hint(repo_root):
    sample = _real_file_sample(repo_root)
    if not sample:
        return GENERIC_FILE_HINT
    listing = ', '.join(sample)
    return (f"File paths must fit THIS repository's own real conventions -- "
            f"here is a sample of its actual committed files, to draw on or "
            f"extend in the same style (invent new paths under the same "
            f"directories rather than reusing these exact files verbatim): "
            f"{listing}.")

ROUTE_PROMPT_TEMPLATE = """\
{loader_block}

Path-triggered channel output for the files this task touches ({files}):
{path_hits}

TASK:
{scenario}

Which practice slug(s) from the occasion index or the path-triggered \
output above actually apply to this task? Read the ones you think might \
apply (mentally, or by naming them) before deciding. Answer with a bare \
list of slugs that apply, or the single word NONE if none do. One slug per \
line, no other commentary.
"""


def _new_batch_id(seed):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return f'{stamp}-seed{seed}'


def cmd_new_batch(args):
    count = 6
    if '--count' in args:
        count = int(args[args.index('--count') + 1])
    seed = None
    if '--seed' in args:
        seed = int(args[args.index('--seed') + 1])
    explicit = None
    if '--practices' in args:
        explicit = args[args.index('--practices') + 1].split(',')
    repo_root = None
    if '--repo-root' in args:
        repo_root = pathlib.Path(args[args.index('--repo-root') + 1]).resolve()
        if not (repo_root / 'practices').is_dir():
            sys.exit(f'practice_simulation FAIL: no practices/ under {repo_root} -- '
                     f'sync or materialize that repo first (tools/precedent_sync_views.py '
                     f'--repo {repo_root}, or build-fixture-repo for the demo fixture).')

    pool = (_practices_from(repo_root / 'practices') if repo_root
            else _active_on_demand_practices())
    by_slug = {fm['slug']: (fm, sections) for fm, sections in pool}

    if explicit:
        missing = [s for s in explicit if s not in by_slug]
        if missing:
            sys.exit(f'practice_simulation FAIL: not an active on-demand practice: '
                     f'{", ".join(missing)}')
        chosen = explicit
        # An explicit --practices list is a deliberate exception to rotation
        # (debugging one practice's prompts), so a seed is recorded but not
        # used to pick anything -- there is nothing left to randomize.
        seed = seed if seed is not None else 0
    else:
        # No seed given: derive one from the current time, NOT a fixed
        # default -- a fixed default seed would make "fresh batch" a lie,
        # since random.Random(same seed) samples the same practices every
        # time. Rotation is the whole point (see the module docstring).
        if seed is None:
            seed = random.SystemRandom().randrange(1_000_000)
        rng = random.Random(seed)
        chosen = rng.sample(sorted(by_slug), min(count, len(by_slug)))

    batch_id = _new_batch_id(seed)
    batch_dir = BATCHES_DIR / batch_id
    (batch_dir / 'generate').mkdir(parents=True)
    (batch_dir / 'scenarios').mkdir()
    (batch_dir / 'route').mkdir()
    (batch_dir / 'answers').mkdir()

    file_hint = _repo_file_hint(repo_root) if repo_root else GENERIC_FILE_HINT
    for slug in chosen:
        fm, sections = by_slug[slug]
        prompt = GENERATE_PROMPT_TEMPLATE.format(
            rule=sections.get('rule', '').strip(), file_hint=file_hint)
        (batch_dir / 'generate' / f'{slug}.prompt.txt').write_text(prompt, encoding='utf-8')

    manifest = {
        'batch_id': batch_id,
        'seed': seed,
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'practices': chosen,
        'repo_root': str(repo_root) if repo_root else None,
        'status': 'generated-prompts-written',
    }
    (batch_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',
                                             encoding='utf-8')

    print(f'New batch: {batch_id}')
    if repo_root:
        print(f'  Target repo: {repo_root} (not this repo -- phase 3 multi-repo)')
    print(f'  {len(chosen)} practice(s) sampled (seed {seed}): {", ".join(chosen)}')
    print(f'  Generation prompts written to {batch_dir / "generate"}/<slug>.prompt.txt')
    print(f'  Next: run each prompt (a person, or an agent session explicitly asked '
          f'to) and save its JSON reply to {batch_dir / "scenarios"}/<slug>.json')
    print(f'  This never happens on its own -- nothing here is wired to a hook or '
          f'gate. See "Never automatic" in spec/SIMULATION_BRIEF.md.')
    return 0


def cmd_route(args):
    batch_id = args[args.index('--batch') + 1]
    batch_dir = BATCHES_DIR / batch_id
    manifest_path = batch_dir / 'manifest.json'
    if not manifest_path.exists():
        sys.exit(f'practice_simulation FAIL: no batch at {batch_dir}')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    repo_root = manifest.get('repo_root')

    if repo_root:
        loader_block = _loader_block_text_at(repo_root)
        on_demand_narrow = _on_demand_narrow_from(pathlib.Path(repo_root) / 'practices')
    else:
        loader_block = _loader_block_text()
        on_demand_narrow = pp.load_on_demand_practices()

    written, missing = 0, []
    for slug in manifest['practices']:
        scen_path = batch_dir / 'scenarios' / f'{slug}.json'
        if not scen_path.exists():
            missing.append(slug)
            continue
        scenarios = json.loads(scen_path.read_text(encoding='utf-8'))
        for kind in KINDS:
            if kind not in scenarios:
                continue
            files = scenarios[kind].get('files', [])
            hits = _matches_for_paths_against(files, on_demand_narrow)
            hits_text = ('\n'.join(f'  {s} (matched {p})' for s, p in hits)
                        if hits else '  (none)')
            prompt = ROUTE_PROMPT_TEMPLATE.format(
                loader_block=loader_block,
                files=', '.join(files) or '(none given)',
                path_hits=hits_text,
                scenario=scenarios[kind]['scenario'],
            )
            (batch_dir / 'route' / f'{slug}-{kind}.prompt.txt').write_text(
                prompt, encoding='utf-8')
            written += 1

    print(f'{written} routing prompt(s) written to {batch_dir / "route"}/.')
    if repo_root:
        print(f'  Target repo: {repo_root} (this batch\'s loader block and path '
              f'channel are THAT repo\'s own, not this repo\'s)')
    if missing:
        print(f'  {len(missing)} practice(s) have no filled-in scenario yet, skipped: '
              f'{", ".join(missing)} (fill in {batch_dir / "scenarios"}/<slug>.json first)')
    print(f'  Next: run each prompt and save the raw answer to '
          f'{batch_dir / "answers"}/<slug>-<kind>.txt, then run `score --batch {batch_id}`.')
    return 0


_SLUG_RE = re.compile(r'\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b')


def _mentions_slug(answer_text, slug):
    return slug in set(_SLUG_RE.findall(answer_text.lower()))


def cmd_score(args):
    batch_id = args[args.index('--batch') + 1]
    batch_dir = BATCHES_DIR / batch_id
    manifest = json.loads((batch_dir / 'manifest.json').read_text(encoding='utf-8'))
    repo_root = manifest.get('repo_root')

    # expected: positive and adversarial should name the target slug;
    # negative should NOT.
    counts = {k: {'expected_named': 0, 'named': 0} for k in KINDS}
    rows = []
    scored, unscored = 0, []
    for slug in manifest['practices']:
        for kind in KINDS:
            ans_path = batch_dir / 'answers' / f'{slug}-{kind}.txt'
            if not ans_path.exists():
                unscored.append(f'{slug}-{kind}')
                continue
            answer = ans_path.read_text(encoding='utf-8')
            named = _mentions_slug(answer, slug)
            expect_named = kind in ('positive', 'adversarial')
            counts[kind]['expected_named'] += 1 if expect_named else 0
            correct = (named == expect_named)
            if kind == 'negative':
                # for 'negative' the "expected" event is CORRECT REJECTION,
                # not naming -- tallied the same way but the meaning differs,
                # see the printed report below.
                counts[kind]['named'] += 1 if not named else 0
            else:
                counts[kind]['named'] += 1 if named else 0
            scored += 1
            rows.append((slug, kind, named, correct))

    print(f'Batch {batch_id}: {scored} scored, {len(unscored)} not yet answered.')
    if repo_root:
        print(f'  Target repo: {repo_root}')
        print(f'  Score this per repo, never pooled with a batch against a different '
              f'repo or against this repo itself -- different repos resolve different '
              f'practice sets (spec/SIMULATION_BRIEF.md section 6). A practice sampled '
              f'here whose frontmatter carries `overrides:` also implicitly tests '
              f'precedence: it can only be correctly named at all if the override '
              f'actually won resolution and reached this repo\'s materialized loader '
              f'block in the first place.')
    if unscored:
        print(f'  Missing answers: {", ".join(unscored)}')
    print()
    for kind in KINDS:
        total = sum(1 for s, k, _n, _c in rows if k == kind)
        if not total:
            continue
        if kind == 'negative':
            correct = counts['negative']['named']   # correct REJECTIONS
            print(f'  negative (should NOT name the practice): '
                  f'{correct}/{total} correctly rejected '
                  f'({100 * correct / total:.0f}%)')
        else:
            hit = counts[kind]['named']
            label = 'positive (plain case)' if kind == 'positive' else \
                    'adversarial (hardened case)'
            print(f'  {label}: {hit}/{total} correctly named '
                  f'({100 * hit / total:.0f}%)')
    if 'positive' in [k for _s, k, _n, _c in rows] and \
       'adversarial' in [k for _s, k, _n, _c in rows]:
        pos_total = sum(1 for s, k, _n, _c in rows if k == 'positive')
        adv_total = sum(1 for s, k, _n, _c in rows if k == 'adversarial')
        if pos_total and adv_total:
            pos_rate = counts['positive']['named'] / pos_total
            adv_rate = counts['adversarial']['named'] / adv_total
            print(f'\n  Plain-vs-hardened gap: {100 * (pos_rate - adv_rate):.0f} '
                  f'point(s) -- this is the number a fixed replay set cannot show, '
                  f'and the reason this batch was invented rather than replayed.')
    print('\n  Read this per batch, never cumulatively across batches: each batch '
          'samples different practices and invents fresh scenarios, by design (see '
          'the module docstring) -- a score here is not comparable commit-for-commit '
          'the way behavioral_replay.py\'s numbers are across runs of the SAME '
          'history. Track the trend across batches, not a single absolute number. A '
          'batch against one repo is never comparable to a batch against another, '
          'either -- see the repo note above if this batch named one.')
    return 0


def cmd_build_fixture_repo(args):
    """Materializes evals/simulation/fixtures/demo-consumer-repo/ into a real,
    synced consumer repo: this repo's own universal catalogue plus that
    fixture's one repo-local override, through the actual
    tools/precedent_sync_views.py / tools/precedent_materialize.py pipeline
    -- never a re-implementation of source resolution. See that fixture's
    own README.md for why it exists (no real dependent repo was attached to
    the session that built phase 3) and what stays committed there versus
    what this regenerates every time."""
    out = pathlib.Path(args[args.index('--out') + 1]).resolve() if '--out' in args \
        else DEFAULT_FIXTURE_REPO
    if not (out / 'local' / 'practices').is_dir():
        sys.exit(f'practice_simulation FAIL: {out} has no local/practices/ -- this '
                 f'does not look like the demo-consumer-repo fixture (or an '
                 f'equivalent hand-authored repo-local source). Refusing to write '
                 f'a fresh precedent.json/AGENTS.md into a directory that was not '
                 f'set up for this.')

    (out / 'precedent.json').write_text(json.dumps({
        'sources': [
            {'level': 'universal', 'name': 'precedent', 'path': str(ROOT)},
            {'level': 'repo-local', 'name': 'demo-consumer-repo', 'path': 'local'},
        ],
    }, indent=2) + '\n', encoding='utf-8')
    agents_md = out / 'AGENTS.md'
    if not agents_md.exists():
        agents_md.write_text(
            '# demo-consumer-repo (phase-3 simulation fixture)\n\n'
            'See README.md. The block below is written by '
            '`tools/precedent_sync_views.py` -- do not hand-edit it.\n\n'
            + bv.BEGIN_MARKER + '\n' + bv.END_MARKER + '\n', encoding='utf-8')

    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'precedent_sync_views.py'),
                        '--repo', str(out)], capture_output=True, text=True)
    print(r.stdout + r.stderr)
    if r.returncode != 0:
        sys.exit(f'practice_simulation FAIL: precedent_sync_views.py exited '
                 f'{r.returncode} materializing {out}.')
    print(f'\nFixture repo ready at {out}.')
    print(f'  python3 tools/practice_simulation.py new-batch --repo-root {out} '
          f'--practices vendored-engine-is-local-path')
    return 0


def main():
    args = sys.argv[1:]
    if not args or args[0] == '--list-batches':
        if not BATCHES_DIR.exists() or not any(BATCHES_DIR.iterdir()):
            print('No batches yet. Run: python3 tools/practice_simulation.py new-batch')
            return 0
        for d in sorted(BATCHES_DIR.iterdir()):
            m = d / 'manifest.json'
            if m.exists():
                manifest = json.loads(m.read_text(encoding='utf-8'))
                repo_note = f"  repo={manifest['repo_root']}" if manifest.get('repo_root') else ''
                print(f"{manifest['batch_id']}  seed={manifest['seed']}  "
                      f"{len(manifest['practices'])} practice(s){repo_note}")
        return 0
    cmd = args[0]
    rest = args[1:]
    if cmd == 'new-batch':
        return cmd_new_batch(rest)
    if cmd == 'build-fixture-repo':
        return cmd_build_fixture_repo(rest)
    if cmd == 'route':
        return cmd_route(rest)
    if cmd == 'score':
        return cmd_score(rest)
    sys.exit(f'practice_simulation FAIL: unknown command {cmd!r} -- '
             f'new-batch, build-fixture-repo, route, score, or --list-batches.')


if __name__ == '__main__':
    sys.exit(main())

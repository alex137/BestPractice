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

Run:
  python3 tools/practice_simulation.py new-batch [--count N] [--seed S]
                                                  [--practices SLUG,SLUG,...]
  python3 tools/practice_simulation.py route --batch BATCH_ID
  python3 tools/practice_simulation.py score --batch BATCH_ID
  python3 tools/practice_simulation.py --list-batches
"""
import datetime, json, pathlib, random, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import build_views as bv
import precedent_paths as pp

SIM_DIR = ROOT / 'evals' / 'simulation'
BATCHES_DIR = SIM_DIR / 'batches'
KINDS = ('positive', 'negative', 'adversarial')


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

File paths should look like real paths in a software repository (this \
repository's own conventions -- practices/, tools/, spec/, docs, etc. -- \
are fine to draw on, or plausible equivalents). Do not invent a path that \
would trivially give away the answer by naming the practice.
"""

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

    pool = _active_on_demand_practices()
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

    for slug in chosen:
        fm, sections = by_slug[slug]
        prompt = GENERATE_PROMPT_TEMPLATE.format(rule=sections.get('rule', '').strip())
        (batch_dir / 'generate' / f'{slug}.prompt.txt').write_text(prompt, encoding='utf-8')

    manifest = {
        'batch_id': batch_id,
        'seed': seed,
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'practices': chosen,
        'status': 'generated-prompts-written',
    }
    (batch_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',
                                             encoding='utf-8')

    print(f'New batch: {batch_id}')
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
            hits = pp.matches_for_paths(files, on_demand_narrow)
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
          'history. Track the trend across batches, not a single absolute number.')
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
                print(f"{manifest['batch_id']}  seed={manifest['seed']}  "
                      f"{len(manifest['practices'])} practice(s)")
        return 0
    cmd = args[0]
    rest = args[1:]
    if cmd == 'new-batch':
        return cmd_new_batch(rest)
    if cmd == 'route':
        return cmd_route(rest)
    if cmd == 'score':
        return cmd_score(rest)
    sys.exit(f'practice_simulation FAIL: unknown command {cmd!r} -- '
             f'new-batch, route, score, or --list-batches.')


if __name__ == '__main__':
    sys.exit(main())

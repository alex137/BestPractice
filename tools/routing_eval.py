#!/usr/bin/env python3
"""routing_eval.py — does trigger-based loading actually beat residency?

This is PRACTICE_ENGINE_PLAN.md's phase-2 done-when condition, the half
tools/behavioral_replay.py cannot reach. The replay proves the MECHANICAL
channel (path globs) is correct and cheaper. It says nothing about the
channel that routes 34 of the 46 on-demand practices: the occasion index's
prose. The plan is explicit that this is the assumption everything rests on:

    "This plan has hard evidence that residency does *not* produce
     compliance -- four defects from sessions carrying the relevant rule in
     context. It has no evidence yet that trigger-based loading does
     better. That is an assumption, not a finding... If triggering does not
     beat residency, the plan needs rethinking rather than building on."

V2, AND WHY V1'S NUMBER WAS NOT THE SYSTEM'S NUMBER. The first run scored
the treatment arm at a 52% miss rate against the control's 32%, and two of
its choices were responsible for a large part of that gap:

  - **It tested one channel out of three.** The plan's loader is a resident
    block PLUS an occasion index PLUS a path-triggered channel that fires
    automatically on the files being touched. v1 gave the treatment arm only
    the first two. Measured after the fact, `precedent_paths.py` surfaces
    8-9 practices per case on this case set, with no session judgment
    involved at all. Leaving it out did not make the test conservative, it
    made it wrong.
  - **It stopped after one hop.** The real sequence is: read the index, OPEN
    the candidates, read their Rules, then decide. v1 scored the arm on
    deciding from a one-line clause, because letting it read practices/
    freely would have let it sidestep the index under test. v2 runs the two
    hops as two separate sessions with the harness in between, so the arm
    gets exactly the Rules it asked for and nothing else -- the real system,
    with no way to cheat.

Both corrections cut in the treatment arm's favour, so v1's gap is an upper
bound on the real one, not an estimate of it.

THE DESIGN. Twenty real commits from this repo's own history, from before the
Precedent work began. For each, three sessions answer the same underlying
question -- which practices apply to this change? -- under three conditions:

  ORACLE     sees all 52 Rules and is asked ONLY to classify, one case at a
             time, with nothing else competing for attention. This is the
             ground truth. It is not an arm; it is the answer key.
  CONTROL    sees all 52 Rules and is asked to do the WORK, naming the
             practices it will apply. This is the pre-migration
             arrangement. The difference from the oracle is attention under
             task load, which is precisely the plan's thesis.
  TREATMENT  the real loader, in two hops.
             Hop 1 sees the resident block, the occasion index, AND the
             path-triggered channel's output for the files this change
             touches, and names the practices it wants to open.
             Hop 2 sees exactly those Rules -- resolved by this harness, not
             fetched by the agent -- and gives the final answer.

Neither treatment hop has repository access. The arm cannot read practices/
and sidestep the very index under test; it can only ask, and be given what
it asked for. That is the system as built, with the cheating path closed.

COST IS PART OF THE ANSWER, NOT A FOOTNOTE. The goal is to miss few or no
applicable practices WITHOUT carrying the whole catalogue in context. An arm
that surfaces everything by loading everything has not solved the problem it
was built for. So every arm's prompt is measured in tokens and reported
beside its miss rate: the question is recall per token, not recall.

WHAT THIS CAN AND CANNOT SETTLE. It measures routing -- whether the right
practices are surfaced. It does not measure whether a session then follows
a practice it surfaced. Ten cases is a pilot: it can show a large effect,
and it cannot resolve a small one. Both limits are printed with the result
rather than left to the reader.

Run:
  python3 tools/routing_eval.py --emit          # write one prompt per (case, arm)
  python3 tools/routing_eval.py --score         # score answers/ against the oracle
  python3 tools/routing_eval.py --enforcement  # what covers the misses that remain
"""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVAL = ROOT / 'evals' / 'routing'
PROMPTS = EVAL / 'prompts'
ANSWERS = EVAL / 'answers'
ARMS = ('oracle', 'control', 'treatment1', 'review', 'review-gloss')
# One hop, deliberately -- spec/ATTENTION_CEILING.md permits either "the same
# two hops as the treatment if you want the comparison clean, or one hop if
# you want the cheapest version" and asks only that the choice be stated. The
# cheapest version is what the recommendation actually proposes (a prefilter
# feeding a judge pass, not a second round of the session's own judgment
# about what to open), so this arm reads the loader's hop-1 context in one
# shot rather than replaying a request/open cycle whose second half was never
# in question -- the loader has already decided what it surfaces.

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import build_views as bv
import precedent_paths as pp

DIFF_LINES = 160


def load_practices():
    out = {}
    for f in sorted((ROOT / 'practices').glob('*.md')):
        fm, sections = sp._read_practice_file(f)
        out[fm['slug']] = (fm, sections)
    return out


def all_rules_block(practices):
    return '\n\n'.join(
        f"### {slug}\n{sections.get('rule','').strip()}"
        for slug, (fm, sections) in sorted(practices.items()))


def loader_block():
    text = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    start = text.index(bv.BEGIN_MARKER)
    end = text.index(bv.END_MARKER) + len(bv.END_MARKER)
    return text[start:end]


def changed_files(commit):
    # --root, because without it a ROOT commit (no parent) diffs against
    # nothing and returns an empty list. Case c16 is this repo's initial
    # commit: for the whole of v1, v2 and v3 the treatment arm was handed
    # "(no files)" and zero path-channel practices for a change touching 48
    # of them, while the control saw the same diff either way. The arm under
    # test was starved on that case and the control was not, which is a bias
    # in the measurement, not a property of the loader.
    out = subprocess.run(['git', '-C', str(ROOT), 'diff-tree', '--root',
                          '--no-commit-id', '--name-only', '-r', commit],
                         capture_output=True, text=True).stdout.split()
    return [f for f in out if f.strip()]


def path_channel(commit, practices):
    """What tools/precedent_paths.py prints for the files this change touches.
    This fires with no session judgment involved -- it is the channel a
    PreToolUse hook runs -- so the treatment arm gets it for free, exactly as
    a real session would."""
    files = changed_files(commit)
    if not files:
        return '(no files)', []
    hits = pp.matches_for_paths(files)
    slugs = []
    for slug, _path in hits:
        if slug not in slugs:
            slugs.append(slug)
    if not slugs:
        return "(no practice's applies_to matched the files this change touches)", []
    body = '\n\n'.join(f"### {s}\n{practices[s][1].get('rule','').strip()}" for s in slugs)
    return body, slugs


GLOSS_WORDS = 55


def gloss_of(sections):
    """Evals/routing/PREDICTION_GLOSS_TIER.md's gloss tier: one paragraph per
    practice, mechanically extracted (first GLOSS_WORDS words of ## Detail,
    or ## Rule if Detail is empty) -- never hand-fitted per practice, since
    that would be exactly the tuning-after-seeing-cases this eval line
    exists to prevent."""
    text = sections.get('detail', '').strip() or sections.get('rule', '').strip()
    text = re.sub(r'\*\*|`', '', text)
    words = text.split()
    snippet = ' '.join(words[:GLOSS_WORDS])
    if len(words) > GLOSS_WORDS:
        snippet += ' …'
    return snippet


def gloss_block(practices):
    """Gloss for every on-demand (non-resident) practice, keyed by slug so it
    reads next to the occasion index's one-line clause for the same slug."""
    return '\n'.join(
        f"- **{slug}**: {gloss_of(sections)}"
        for slug, (fm, sections) in sorted(practices.items())
        if fm.get('tier') != 'resident')


def approx_tokens(text):
    return int(len(text.split()) * 1.3)


def commit_context(commit):
    show = subprocess.run(['git', '-C', str(ROOT), 'show', '--stat', '--format=%s%n%n%b', commit],
                          capture_output=True, text=True).stdout
    diff = subprocess.run(['git', '-C', str(ROOT), 'show', '--format=', commit],
                          capture_output=True, text=True).stdout.splitlines()
    truncated = '\n'.join(diff[:DIFF_LINES])
    if len(diff) > DIFF_LINES:
        truncated += f"\n... [diff truncated at {DIFF_LINES} of {len(diff)} lines]"
    return show.strip(), truncated


ANSWER_FORMAT = """
Answer with a JSON object and nothing else:

  {"slugs": ["slug-one", "slug-two"], "reasoning": "one or two sentences"}

Use the exact slugs as given. List every practice that genuinely applies and
none that does not -- over-listing is as wrong as under-listing. Do not pad
the list to look thorough."""


def build_prompt(arm, case, practices):
    subject, diff = commit_context(case['commit'])
    task = case['task']
    if arm == 'oracle':
        return f"""You are building an answer key for an evaluation.

Below is the complete catalogue of 52 engineering practices, each as its
imperative Rule. Below that is a real change made to a repository.

Your ONLY job is to decide, carefully and without time pressure, which of
these practices genuinely applied to that change -- which ones a reviewer
would say the author should have had in mind. Judge on the substance of the
change, not on keyword overlap.

## The full practice catalogue

{all_rules_block(practices)}

## The change

Commit message and files touched:

{subject}

Diff:

```
{diff}
```
{ANSWER_FORMAT}
"""
    if arm == 'control':
        return f"""You are a session about to do a piece of work in a repository.

Your project instructions carry the full catalogue of 52 engineering
practices, reproduced in full below, as they always are at session start.

## Practices (always loaded)

{all_rules_block(practices)}

## Your task

{task}

Here is the change you are about to make, for context:

Commit message and files touched:

{subject}

Diff:

```
{diff}
```

Before you begin: which of the practices above are you going to apply to
this work?
{ANSWER_FORMAT}
"""
    if arm == 'review':
        path_block, _path_slugs = path_channel(case['commit'], practices)
        return f"""You are reviewing a change that is already finished. You are not doing
the work and you have no task of your own -- you are judging a diff someone
else already wrote.

Your project instructions carry the block below: the practices that are
always resident, plus an index of every other practice grouped by the
occasion on which it applies.

{loader_block()}

## Automatically surfaced for the files this change touches

Your harness matched the files below against every practice's `applies_to`
and surfaced these Rules without being asked. They are already in front of
you.

{path_block}

## The change, already complete

Commit message and files touched:

{subject}

Diff:

```
{diff}
```

Your ONLY job is to decide, carefully and without time pressure, which of the
practices shown above -- resident, indexed, or surfaced -- genuinely applied
to this change: which ones a reviewer would say the author should have had
in mind. Judge only what is in front of you in this prompt. Do not name a
practice whose Rule you have not seen here -- this prompt holds exactly what
the loader surfaces for this change and nothing else, and that is the thing
under test.
{ANSWER_FORMAT}
"""
    if arm == 'review-gloss':
        path_block, _path_slugs = path_channel(case['commit'], practices)
        return f"""You are reviewing a change that is already finished. You are not doing
the work and you have no task of your own -- you are judging a diff someone
else already wrote.

Your project instructions carry the block below: the practices that are
always resident, plus an index of every other practice grouped by the
occasion on which it applies.

{loader_block()}

## A short gloss for every practice named in the occasion index above

For each practice above the index only names in a one-line clause, here is a
slightly longer paragraph -- more than the clause, still far short of the
full Rule -- so you have more than one line to judge each candidate against.

{gloss_block(practices)}

## Automatically surfaced for the files this change touches

Your harness matched the files below against every practice's `applies_to`
and surfaced these Rules without being asked. They are already in front of
you.

{path_block}

## The change, already complete

Commit message and files touched:

{subject}

Diff:

```
{diff}
```

Your ONLY job is to decide, carefully and without time pressure, which of the
practices shown above -- resident, indexed, glossed, or surfaced -- genuinely
applied to this change: which ones a reviewer would say the author should
have had in mind. Judge only what is in front of you in this prompt. Do not
name a practice whose Rule or gloss you have not seen here.
{ANSWER_FORMAT}
"""
    path_block, path_slugs = path_channel(case['commit'], practices)
    return f"""You are a session about to do a piece of work in a repository.

Your project instructions carry the block below: the practices that are
always resident, plus an index of every other practice grouped by the
occasion on which it applies.

{loader_block()}

## Automatically surfaced for the files this change touches

Your harness matched the files below against every practice's `applies_to`
and surfaced these Rules without being asked. They are already in front of
you.

{path_block}

## Your task

{task}

Here is the change you are about to make, for context:

Commit message and files touched:

{subject}

Diff:

```
{diff}
```

Before you begin: name the practices you want to load. You will be given the
full Rule of each one you name, and then asked for a final answer -- so name
anything you think might apply, and anything already surfaced above that you
believe genuinely applies. Judge each index entry on its own; entries share
an occasion heading, but sharing a heading does not mean they apply together.
{ANSWER_FORMAT}
"""


def build_hop2_prompt(case, practices, requested):
    subject, diff = commit_context(case['commit'])
    path_block, _ = path_channel(case['commit'], practices)
    known = [s for s in requested if s in practices]
    opened = '\n\n'.join(f"### {s}\n{practices[s][1].get('rule','').strip()}" for s in known)
    if not opened:
        opened = '(you named no practices, so nothing was opened)'
    return f"""You are the same session, one step further on.

You named the practices you wanted, and here are their full Rules. This is
everything you asked for and nothing else.

{opened}

## Also already in front of you, surfaced automatically by file path

{path_block}

## Your task

{case['task']}

Commit message and files touched:

{subject}

Diff:

```
{diff}
```

Now give your FINAL answer: which practices genuinely apply to this change?
You may drop any you named that turn out not to fit once you have read the
Rule -- that is the point of having read it -- and you may keep any that were
surfaced automatically. Do not add a practice whose Rule you have not seen.
{ANSWER_FORMAT}
"""


def cmd_emit():
    cases = json.loads((EVAL / 'cases.json').read_text())['cases']
    practices = load_practices()
    PROMPTS.mkdir(parents=True, exist_ok=True)
    ANSWERS.mkdir(parents=True, exist_ok=True)
    n = 0
    cost = {a: [] for a in ARMS}
    for case in cases:
        for arm in ARMS:
            text = build_prompt('treatment' if arm == 'treatment1' else arm, case, practices)
            (PROMPTS / f"{case['id']}.{arm}.md").write_text(text, encoding='utf-8')
            cost[arm].append(approx_tokens(text))
            n += 1
    (EVAL / 'cost.json').write_text(json.dumps(
        {a: round(sum(v) / len(v)) for a, v in cost.items()}, indent=2) + "\n")
    print(f"routing_eval: wrote {n} prompts to {PROMPTS.relative_to(ROOT)}/")
    for a, v in cost.items():
        print(f"  {a:11} ~{round(sum(v)/len(v)):>6} tokens of practice context per case (mean)")
    print(f"  answers go in {ANSWERS.relative_to(ROOT)}/<case>.<arm>.json as "
          f'{{"slugs": [...], "reasoning": "..."}}')
    return 0


def cmd_emit_hop2():
    """Resolve what each hop-1 answer asked for, and build the hop-2 prompt
    holding exactly those Rules. The harness does the resolving, not the
    agent, so the arm cannot reach past what it named."""
    cases = json.loads((EVAL / 'cases.json').read_text())['cases']
    practices = load_practices()
    written, skipped, cost = 0, [], []
    for case in cases:
        got = _read_answer(case['id'], 'treatment1', set(practices), quiet=True)
        if got is None:
            skipped.append(case['id'])
            continue
        text = build_hop2_prompt(case, practices, sorted(got))
        (PROMPTS / f"{case['id']}.treatment2.md").write_text(text, encoding='utf-8')
        cost.append(approx_tokens(text))
        written += 1
    print(f"routing_eval: wrote {written} hop-2 prompt(s)"
          + (f"; no hop-1 answer yet for {skipped}" if skipped else ""))
    if cost:
        print(f"  treatment2  ~{round(sum(cost)/len(cost)):>6} tokens of practice context "
              f"per case (mean)")
    return 0


def cmd_enforcement():
    """What now catches the practices the loader still misses.

    Phase 4's done-when says "the routing eval re-run shows the converted
    practices no longer missed". Read literally that is not a thing conversion
    can do, and the plan says so itself two sections earlier: an enforced
    practice is "never loaded at all -- the check's failure message IS the
    rule, delivered at the moment of violation". A practice with a working
    check is deliberately absent from the routing question, so the arm that
    routes will keep missing it and should.

    So this reports the miss set by WHAT NOW COVERS IT, which is the question
    the done-when was reaching for. Stated plainly, because it is easy to
    over-read: a check being in scope means the violation would be CAUGHT if
    the change committed one. It does not mean these particular commits
    violated anything -- most did not -- and it is not evidence that the
    session would have complied. It is coverage, not compliance.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        '_pc', ROOT / 'tools' / 'precedent_check.py')
    pc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc)

    cases = json.loads((EVAL / 'cases.json').read_text())['cases']
    practices = load_practices()
    valid = set(practices)
    rows = []
    for case in cases:
        truth = _read_answer(case['id'], 'oracle', valid, quiet=True)
        if truth is None:
            continue
        got = _read_answer(case['id'], 'treatment2', valid, quiet=True)
        if got is None:
            got = _read_answer(case['id'], 'treatment1', valid, quiet=True)
        if got is None:
            continue
        _block, path_slugs = path_channel(case['commit'], practices)
        for slug in sorted(truth - got):
            fm = practices[slug][0]
            rows.append({
                'case': case['id'], 'slug': slug,
                'enforced': slug in pc.CHECKS,
                'scope': pc.CHECKS[slug]['scope'] if slug in pc.CHECKS else '',
                'resident': fm.get('tier') == 'resident',
                'path': slug in path_slugs,
            })

    if not rows:
        print('routing_eval: no misses to attribute (need oracle and treatment '
              'answers).')
        return 0
    enforced = [r for r in rows if r['enforced']]
    print(f'Miss attribution — {len(rows)} (case, practice) misses by the '
          f'treatment arm.\n')
    print(f"{'case':6} {'practice':32} {'enforced':10} {'scope':9} {'surfaced by path':17}")
    for r in rows:
        print(f"{r['case']:6} {r['slug']:32} "
              f"{'check' if r['enforced'] else '—':10} {r['scope']:9} "
              f"{'yes' if r['path'] else 'no':17}")
    by_slug = {}
    for r in rows:
        by_slug.setdefault(r['slug'], []).append(r)
    print(f'\n{len(enforced)} of {len(rows)} misses are on practices that now '
          f'carry a check '
          f'({100 * len(enforced) / len(rows):.0f}%).')
    print('  covered by a check:     '
          + ', '.join(f"{s} x{len(v)}" for s, v in sorted(by_slug.items())
                      if v[0]['enforced']))
    uncovered = [(s, v) for s, v in sorted(by_slug.items()) if not v[0]['enforced']]
    print('  still prose-only:       '
          + (', '.join(f"{s} x{len(v)}" for s, v in uncovered) or 'none'))
    print('\nA check in scope means the violation would be caught if the change')
    print('committed one. It is not evidence that these commits violated')
    print('anything, nor that a session complied. Coverage, not compliance.')
    return 0


def _read_answer(case_id, arm, valid, quiet=False):
    path = ANSWERS / f"{case_id}.{arm}.json"
    if not path.exists():
        return None
    raw = path.read_text(encoding='utf-8').strip()
    m = re.search(r'\{.*\}', raw, re.S)
    if not m:
        sys.exit(f"routing_eval FAIL: {path} holds no complete JSON object -- most "
                 f"likely a truncated write (check whether the closing brace is "
                 f"there). Repair or re-run that one case; do not drop it silently, "
                 f"or the arm quietly scores on fewer cases than the other.")
    slugs = json.loads(m.group(0)).get('slugs', [])
    unknown = [s for s in slugs if s not in valid]
    if unknown and not quiet:
        print(f"  WARN {path.name}: {len(unknown)} slug(s) are not in the catalogue "
              f"and are counted as false positives: {unknown}")
    return set(slugs)


def cmd_score():
    cases = json.loads((EVAL / 'cases.json').read_text())['cases']
    valid = set(load_practices())
    rows, totals = [], {a: [0, 0, 0] for a in ('control', 'treatment', 'review')}  # hit, miss, extra
    h2h = {'control_only': 0, 'treatment_only': 0}
    # The review arm shares the oracle's judge-only framing, and the oracle
    # DEFINES truth here, so a truth-filtered comparison between review and
    # control is partly agreement by construction. This second head-to-head
    # is the mitigation spec/ATTENTION_CEILING.md names: raw answer sets,
    # never touching the oracle, so it cannot inherit that bias.
    rc_h2h = {'review_only': 0, 'control_only': 0}
    scored = 0
    for case in cases:
        truth = _read_answer(case['id'], 'oracle', valid)
        if truth is None:
            continue
        row = {'id': case['id'], 'truth': len(truth)}
        any_arm = False
        arm_sets = {}
        for arm in ('control', 'treatment', 'review'):
            got = None
            candidates = {'control': ('control',), 'treatment': ('treatment2', 'treatment1'),
                          'review': ('review',)}[arm]
            for candidate in candidates:
                got = _read_answer(case['id'], candidate, valid)
                if got is not None:
                    break
            arm_sets[arm] = got
            if got is None:
                row[arm] = None
                continue
            any_arm = True
            hit, miss, extra = len(truth & got), len(truth - got), len(got - truth)
            row[arm] = (hit, miss, extra, sorted(truth - got))
            t = totals[arm]
            t[0] += hit; t[1] += miss; t[2] += extra
        if arm_sets.get('control') is not None and arm_sets.get('treatment') is not None:
            # oracle-independent: what each arm found that the other did not
            h2h['control_only'] += len(arm_sets['control'] - arm_sets['treatment'] & truth
                                       if False else (truth & arm_sets['control']) - arm_sets['treatment'])
            h2h['treatment_only'] += len((truth & arm_sets['treatment']) - arm_sets['control'])
        if arm_sets.get('control') is not None and arm_sets.get('review') is not None:
            # Deliberately NOT filtered by truth -- raw set difference only.
            rc_h2h['review_only'] += len(arm_sets['review'] - arm_sets['control'])
            rc_h2h['control_only'] += len(arm_sets['control'] - arm_sets['review'])
        if any_arm:
            scored += 1
        rows.append(row)

    if not scored:
        print("routing_eval: no scoreable cases yet (need an oracle answer and at "
              "least one arm per case).")
        return 0

    # A reported result has to be tied to the exact answer set it came from.
    # During the v2 run a redundantly-launched agent rewrote one cell AFTER a
    # score had already been printed -- harmlessly, as it happened, but the
    # printed number and the files on disk were briefly two different things.
    # One answer per cell, and a digest so any quoted figure can be traced
    # back to the set that produced it.
    import hashlib
    files = sorted(ANSWERS.glob('*.json'))
    digest = hashlib.sha256(b''.join(f.read_bytes() for f in files)).hexdigest()[:12]
    print(f"Routing eval — {scored} case(s) scored against the oracle answer key.")
    print(f"answer set: {len(files)} files, digest {digest}\n")
    print(f"{'case':6} {'applies':>7}   {'CONTROL (all 52 loaded)':<28} {'TREATMENT (index only)':<28} {'REVIEW (loader, judge-only)':<28}")
    print(f"{'':6} {'':>7}   {'hit/miss/extra':<28} {'hit/miss/extra':<28} {'hit/miss/extra':<28}")
    for r in rows:
        if r.get('control') is None and r.get('treatment') is None and r.get('review') is None:
            continue
        def fmt(v):
            return '—' if v is None else f"{v[0]}/{v[1]}/{v[2]}"
        print(f"{r['id']:6} {r['truth']:>7}   {fmt(r.get('control')):<28} {fmt(r.get('treatment')):<28} {fmt(r.get('review')):<28}")

    print()
    for arm in ('control', 'treatment', 'review'):
        hit, miss, extra = totals[arm]
        applicable = hit + miss
        if not applicable:
            continue
        recall = 100 * hit / applicable
        precision = 100 * hit / (hit + extra) if (hit + extra) else 0.0
        label = {'control': 'CONTROL  (all 52 always loaded)',
                 'treatment': 'TREATMENT (resident block + occasion index)',
                 'review': 'REVIEW   (the loader, judge-only framing)'}[arm]
        print(f"{label}")
        print(f"   surfaced {hit} of {applicable} applicable practices — "
              f"recall {recall:.0f}%, MISS RATE {100 - recall:.0f}%")
        print(f"   precision {precision:.0f}% ({extra} surfaced that did not apply)")

    try:
        cost = json.loads((EVAL / 'cost.json').read_text())
    except (OSError, json.JSONDecodeError):
        cost = {}
    if cost:
        print("\nCost -- the other half of the goal. Missing nothing by loading")
        print("everything is not a solution to the problem this plan exists to solve.")
        c_ctl = cost.get('control')
        c_trt = cost.get('treatment2') or cost.get('treatment1')
        c_rev = cost.get('review')
        cost_rows = [('CONTROL  ', c_ctl, 'control'), ('TREATMENT', c_trt, 'treatment')]
        if c_rev:
            cost_rows.append(('REVIEW   ', c_rev, 'review'))
        if c_ctl and c_trt:
            for label, tok, arm in cost_rows:
                if not tok:
                    continue
                hit, miss, _e = totals[arm]
                app = hit + miss
                rec = 100 * hit / app if app else 0
                print(f"  {label} ~{tok:>6} tokens/case, recall {rec:.0f}%"
                      f"  ->  {10 * rec / tok * 100:.2f} recall-points per 1k tokens")
            print(f"  the treatment arm carries {100 * (1 - c_trt / c_ctl):.0f}% less "
                  f"practice context per case.")
            if c_rev:
                print(f"  the review arm carries {100 * (1 - c_rev / c_ctl):.0f}% less "
                      f"practice context per case than control ({c_rev} vs {c_ctl} tok).")

    print(f"\nHead to head, without using the oracle at all:")
    print(f"  applicable practices CONTROL found and TREATMENT missed: {h2h['control_only']}")
    print(f"  applicable practices TREATMENT found and CONTROL missed: {h2h['treatment_only']}")

    if rc_h2h['review_only'] or rc_h2h['control_only']:
        print(f"\nReview vs control, oracle-free (raw answer sets, no truth filter --")
        print(f"the confound mitigation spec/ATTENTION_CEILING.md names, since the review")
        print(f"arm shares the oracle's framing and the oracle defines truth here):")
        print(f"  practices CONTROL named that REVIEW did not: {rc_h2h['control_only']}")
        print(f"  practices REVIEW named that CONTROL did not: {rc_h2h['review_only']}")
        rev_hit, rev_miss, _e = totals['review']
        ctl_hit, ctl_miss, _e2 = totals['control']
        if rev_hit + rev_miss and ctl_hit + ctl_miss:
            rev_recall = 100 * rev_hit / (rev_hit + rev_miss)
            ctl_recall = 100 * ctl_hit / (ctl_hit + ctl_miss)
            gap = rev_recall - ctl_recall
            print(f"\n  review recall {rev_recall:.0f}% vs control {ctl_recall:.0f}% "
                  f"(gap {gap:+.0f} points).")
            print(f"  Per spec/ATTENTION_CEILING.md: read a gap under about 10 points as")
            print(f"  unconvincing, not as a win, precisely because of the framing confound")
            print(f"  above.")

    print("\nWhat this settles, and what it does not:")
    print("  It measures ROUTING -- whether the right practices are surfaced. It does")
    print("  not measure whether a session then follows a practice it surfaced.")
    print(f"  {scored} cases is a pilot: it can show a large effect and cannot resolve")
    print("  a small one. Read a difference under roughly 15 points as 'not measured'.")
    return 0


def main():
    args = sys.argv[1:]
    if '--emit-hop2' in args:
        return cmd_emit_hop2()
    if '--emit' in args:
        return cmd_emit()
    if '--score' in args:
        return cmd_score()
    if '--enforcement' in args:
        return cmd_enforcement()
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main())

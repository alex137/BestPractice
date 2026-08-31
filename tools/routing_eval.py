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

THE DESIGN. Ten real commits from this repo's own history, from before the
Precedent work began. For each, three sessions answer the same underlying
question -- which practices apply to this change? -- under three conditions:

  ORACLE     sees all 52 Rules and is asked ONLY to classify, one case at a
             time, with nothing else competing for attention. This is the
             ground truth. It is not an arm; it is the answer key.
  CONTROL    sees all 52 Rules and is asked to do the WORK, naming the
             practices it will apply. This is the pre-migration
             arrangement. The difference from the oracle is attention under
             task load, which is precisely the plan's thesis.
  TREATMENT  sees only the resident block and the occasion index -- what a
             session actually gets at session start after phase 2 -- and
             names the practices it would open before starting.

The treatment arm is given NO repository access on purpose. If it could
read practices/ it could sidestep the index, and the index is the thing
under test. Naming a slug it would open is exactly the routing decision;
what happens next (precedent_show returns that Rule) is already proven
deterministic, so nothing is lost by stopping there.

WHAT THIS CAN AND CANNOT SETTLE. It measures routing -- whether the right
practices are surfaced. It does not measure whether a session then follows
a practice it surfaced. Ten cases is a pilot: it can show a large effect,
and it cannot resolve a small one. Both limits are printed with the result
rather than left to the reader.

Run:
  python3 tools/routing_eval.py --emit          # write one prompt per (case, arm)
  python3 tools/routing_eval.py --score         # score answers/ against the oracle
"""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVAL = ROOT / 'evals' / 'routing'
PROMPTS = EVAL / 'prompts'
ANSWERS = EVAL / 'answers'
ARMS = ('oracle', 'control', 'treatment')

sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp
import build_views as bv

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
    return f"""You are a session about to do a piece of work in a repository.

Your project instructions carry the block below. It holds the practices that
are always resident, plus an index of every other practice grouped by the
occasion on which it applies. You can load the full Rule of any practice by
naming its slug -- assume that returns its full text.

{loader_block()}

## Your task

{task}

Here is the change you are about to make, for context:

Commit message and files touched:

{subject}

Diff:

```
{diff}
```

Before you begin: which practices would you load before doing this work?
{ANSWER_FORMAT}
"""


def cmd_emit():
    cases = json.loads((EVAL / 'cases.json').read_text())['cases']
    practices = load_practices()
    PROMPTS.mkdir(parents=True, exist_ok=True)
    ANSWERS.mkdir(parents=True, exist_ok=True)
    n = 0
    for case in cases:
        for arm in ARMS:
            path = PROMPTS / f"{case['id']}.{arm}.md"
            path.write_text(build_prompt(arm, case, practices), encoding='utf-8')
            n += 1
    print(f"routing_eval: wrote {n} prompts to {PROMPTS.relative_to(ROOT)}/")
    print(f"  answers go in {ANSWERS.relative_to(ROOT)}/<case>.<arm>.json as "
          f'{{"slugs": [...], "reasoning": "..."}}')
    return 0


def _read_answer(case_id, arm, valid):
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
    if unknown:
        print(f"  WARN {path.name}: {len(unknown)} slug(s) are not in the catalogue "
              f"and are counted as false positives: {unknown}")
    return set(slugs)


def cmd_score():
    cases = json.loads((EVAL / 'cases.json').read_text())['cases']
    valid = set(load_practices())
    rows, totals = [], {a: [0, 0, 0] for a in ('control', 'treatment')}  # hit, miss, extra
    scored = 0
    for case in cases:
        truth = _read_answer(case['id'], 'oracle', valid)
        if truth is None:
            continue
        row = {'id': case['id'], 'truth': len(truth)}
        any_arm = False
        for arm in ('control', 'treatment'):
            got = _read_answer(case['id'], arm, valid)
            if got is None:
                row[arm] = None
                continue
            any_arm = True
            hit, miss, extra = len(truth & got), len(truth - got), len(got - truth)
            row[arm] = (hit, miss, extra, sorted(truth - got))
            t = totals[arm]
            t[0] += hit; t[1] += miss; t[2] += extra
        if any_arm:
            scored += 1
        rows.append(row)

    if not scored:
        print("routing_eval: no scoreable cases yet (need an oracle answer and at "
              "least one arm per case).")
        return 0

    print(f"Routing eval — {scored} case(s) scored against the oracle answer key.\n")
    print(f"{'case':6} {'applies':>7}   {'CONTROL (all 52 loaded)':<28} {'TREATMENT (index only)':<28}")
    print(f"{'':6} {'':>7}   {'hit/miss/extra':<28} {'hit/miss/extra':<28}")
    for r in rows:
        if r.get('control') is None and r.get('treatment') is None:
            continue
        def fmt(v):
            return '—' if v is None else f"{v[0]}/{v[1]}/{v[2]}"
        print(f"{r['id']:6} {r['truth']:>7}   {fmt(r.get('control')):<28} {fmt(r.get('treatment')):<28}")

    print()
    for arm in ('control', 'treatment'):
        hit, miss, extra = totals[arm]
        applicable = hit + miss
        if not applicable:
            continue
        recall = 100 * hit / applicable
        precision = 100 * hit / (hit + extra) if (hit + extra) else 0.0
        label = 'CONTROL  (all 52 always loaded)' if arm == 'control' else \
                'TREATMENT (resident block + occasion index)'
        print(f"{label}")
        print(f"   surfaced {hit} of {applicable} applicable practices — "
              f"recall {recall:.0f}%, MISS RATE {100 - recall:.0f}%")
        print(f"   precision {precision:.0f}% ({extra} surfaced that did not apply)")

    print("\nWhat this settles, and what it does not:")
    print("  It measures ROUTING -- whether the right practices are surfaced. It does")
    print("  not measure whether a session then follows a practice it surfaced.")
    print(f"  {scored} cases is a pilot: it can show a large effect and cannot resolve")
    print("  a small one. Read a difference under roughly 15 points as 'not measured'.")
    return 0


def main():
    args = sys.argv[1:]
    if '--emit' in args:
        return cmd_emit()
    if '--score' in args:
        return cmd_score()
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""routing_eval_synthetic.py -- a targeted stress test of the occasion-index
channel, using eight hand-written synthetic tasks instead of real commits.

See evals/routing_synthetic/PREDICTION.md for why this exists, what it can
and cannot establish, and the pre-registered prediction it is scored
against. It reuses routing_eval.py's practice loader, loader block, and
answer-format machinery rather than re-deriving them -- only the case
source (synthetic, not git) and the oracle/control prompt text (built
around a synthetic diff instead of `git show`) are new.

Run:
  python3 tools/routing_eval_synthetic.py --emit         # oracle/control/treatment1
  python3 tools/routing_eval_synthetic.py --emit-hop2    # treatment2, after hop-1 answers exist
  python3 tools/routing_eval_synthetic.py --score        # score against the oracle
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVAL = ROOT / 'evals' / 'routing_synthetic'
PROMPTS = EVAL / 'prompts'
ANSWERS = EVAL / 'answers'

sys.path.insert(0, str(ROOT / 'tools'))
import routing_eval as re_  # reuse load_practices, loader_block, ANSWER_FORMAT, approx_tokens
import precedent_paths as pp

ANSWER_FORMAT = re_.ANSWER_FORMAT


def path_channel_synthetic(files, practices):
    hits = pp.matches_for_paths(files)
    slugs = []
    for slug, _path in hits:
        if slug not in slugs:
            slugs.append(slug)
    if not slugs:
        return "(no practice's applies_to matched the files this change touches)", []
    body = '\n\n'.join(f"### {s}\n{practices[s][1].get('rule','').strip()}" for s in slugs)
    return body, slugs


def build_prompt(arm, case, practices):
    task = case['task']
    diff = case['diff']
    files = ', '.join(case['files'])
    if arm == 'oracle':
        return f"""You are building an answer key for an evaluation.

Below is the complete catalogue of {len(practices)} engineering practices,
each as its imperative Rule. Below that is a real (though small,
constructed for this test) change made to a repository.

Your ONLY job is to decide, carefully and without time pressure, which of
these practices genuinely applied to that change -- which ones a reviewer
would say the author should have had in mind. Judge on the substance of the
change, not on keyword overlap.

## The full practice catalogue

{re_.all_rules_block(practices)}

## The change

Files touched: {files}

Task: {task}

Diff:

```
{diff}
```
{ANSWER_FORMAT}
"""
    if arm == 'control':
        return f"""You are a session about to do a piece of work in a repository.

Your project instructions carry the full catalogue of {len(practices)}
engineering practices, reproduced in full below, as they always are at
session start.

## Practices (always loaded)

{re_.all_rules_block(practices)}

## Your task

{task}

Here is the change you are about to make, for context:

Files touched: {files}

Diff:

```
{diff}
```

Before you begin: which of the practices above are you going to apply to
this work?
{ANSWER_FORMAT}
"""
    path_block, _path_slugs = path_channel_synthetic(case['files'], practices)
    return f"""You are a session about to do a piece of work in a repository.

Your project instructions carry the block below: the practices that are
always resident, plus an index of every other practice grouped by the
occasion on which it applies.

{re_.loader_block()}

## Automatically surfaced for the files this change touches

Your harness matched the files below against every practice's `applies_to`
and surfaced these Rules without being asked. They are already in front of
you.

{path_block}

## Your task

{task}

Here is the change you are about to make, for context:

Files touched: {files}

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
    path_block, _ = path_channel_synthetic(case['files'], practices)
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

Files touched: {', '.join(case['files'])}

Diff:

```
{case['diff']}
```

Now give your FINAL answer: which practices genuinely apply to this change?
You may drop any you named that turn out not to fit once you have read the
Rule -- that is the point of having read it -- and you may keep any that were
surfaced automatically. Do not add a practice whose Rule you have not seen.
{ANSWER_FORMAT}
"""


def load_cases():
    return json.loads((EVAL / 'cases.json').read_text())['cases']


def cmd_emit():
    cases = load_cases()
    practices = re_.load_practices()
    PROMPTS.mkdir(parents=True, exist_ok=True)
    ANSWERS.mkdir(parents=True, exist_ok=True)
    n = 0
    cost = {a: [] for a in ('oracle', 'control', 'treatment1')}
    for case in cases:
        for arm in ('oracle', 'control', 'treatment1'):
            text = build_prompt('treatment' if arm == 'treatment1' else arm, case, practices)
            (PROMPTS / f"{case['id']}.{arm}.md").write_text(text, encoding='utf-8')
            cost[arm].append(re_.approx_tokens(text))
            n += 1
    print(f"routing_eval_synthetic: wrote {n} prompts to {PROMPTS.relative_to(ROOT)}/")
    for a, v in cost.items():
        print(f"  {a:11} ~{round(sum(v)/len(v)):>6} tokens of practice context per case (mean)")
    return 0


def _read_answer(case_id, arm, valid, quiet=False):
    import re as _re
    path = ANSWERS / f"{case_id}.{arm}.json"
    if not path.exists():
        return None
    raw = path.read_text(encoding='utf-8').strip()
    m = _re.search(r'\{.*\}', raw, _re.S)
    if not m:
        sys.exit(f"routing_eval_synthetic FAIL: {path} holds no complete JSON object.")
    slugs = json.loads(m.group(0)).get('slugs', [])
    unknown = [s for s in slugs if s not in valid]
    if unknown and not quiet:
        print(f"  WARN {path.name}: {len(unknown)} slug(s) not in the catalogue: {unknown}")
    return set(slugs)


def cmd_emit_hop2():
    cases = load_cases()
    practices = re_.load_practices()
    written, skipped = 0, []
    for case in cases:
        got = _read_answer(case['id'], 'treatment1', set(practices), quiet=True)
        if got is None:
            skipped.append(case['id'])
            continue
        text = build_hop2_prompt(case, practices, sorted(got))
        (PROMPTS / f"{case['id']}.treatment2.md").write_text(text, encoding='utf-8')
        written += 1
    print(f"routing_eval_synthetic: wrote {written} hop-2 prompt(s)"
          + (f"; no hop-1 answer yet for {skipped}" if skipped else ""))
    return 0


def cmd_score():
    cases = load_cases()
    valid = set(re_.load_practices())
    totals = {a: [0, 0, 0] for a in ('control', 'treatment')}
    target_hits = {'control': 0, 'treatment': 0, 'total': 0}
    rows = []
    scored = 0
    for case in cases:
        truth = _read_answer(case['id'], 'oracle', valid)
        if truth is None:
            continue
        row = {'id': case['id'], 'truth': len(truth), 'target': case.get('target_slug')}
        got_control = _read_answer(case['id'], 'control', valid)
        got_t2 = _read_answer(case['id'], 'treatment2', valid)
        got_t1 = _read_answer(case['id'], 'treatment1', valid)
        got_treatment = got_t2 if got_t2 is not None else got_t1
        any_arm = False
        for arm, got in (('control', got_control), ('treatment', got_treatment)):
            if got is None:
                row[arm] = None
                continue
            any_arm = True
            hit, miss, extra = len(truth & got), len(truth - got), len(got - truth)
            row[arm] = (hit, miss, extra)
            t = totals[arm]
            t[0] += hit; t[1] += miss; t[2] += extra
            target = case.get('target_slug')
            if target:
                target_hits['total'] += 1 if arm == 'control' else 0
                if target in got:
                    target_hits[arm] += 1
        if any_arm:
            scored += 1
        rows.append(row)

    if not scored:
        print("routing_eval_synthetic: no scoreable cases yet.")
        return 0

    print(f"Synthetic occasion-routing stress test -- {scored} of {len(cases)} case(s) scored.\n")
    print(f"{'case':6} {'target practice':28} {'applies':>7}   {'CONTROL':<16} {'TREATMENT':<16}")
    for r in rows:
        def fmt(v):
            return '—' if v is None else f"{v[0]}/{v[1]}/{v[2]}"
        print(f"{r['id']:6} {str(r['target'] or ''):28} {r['truth']:>7}   "
              f"{fmt(r.get('control')):<16} {fmt(r.get('treatment')):<16}")

    print()
    for arm in ('control', 'treatment'):
        hit, miss, extra = totals[arm]
        applicable = hit + miss
        if not applicable:
            continue
        recall = 100 * hit / applicable
        print(f"{arm.upper()}: surfaced {hit} of {applicable} applicable practices — "
              f"recall {recall:.0f}%, miss {100 - recall:.0f}%")

    n_targets = sum(1 for c in cases if c.get('target_slug'))
    if n_targets:
        print(f"\nOn the {n_targets} designed-for target practices specifically "
              f"(one per case, the occasion the case was written to exercise):")
        print(f"  control caught its target:   {target_hits['control']} of {n_targets}")
        print(f"  treatment caught its target: {target_hits['treatment']} of {n_targets}")

    print("\nRead this against evals/routing_synthetic/PREDICTION.md's pre-registered")
    print("bands, not as a replacement for the 16%/23% headline in spec/ATTENTION_CEILING.md.")
    return 0


def main():
    args = sys.argv[1:]
    if '--emit-hop2' in args:
        return cmd_emit_hop2()
    if '--emit' in args:
        return cmd_emit()
    if '--score' in args:
        return cmd_score()
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main())

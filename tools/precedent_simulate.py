#!/usr/bin/env python3
"""precedent_simulate.py -- phase 4 of spec/SIMULATION_BRIEF.md: one command
over the two tiers phases 1-3 built, plus the running trend log neither of
them kept on its own.

THE TWO TIERS, UNCHANGED, JUST GIVEN ONE FRONT DOOR:
  quick   tools/behavioral_replay.py's reach measurement plus --with-checks
          mechanical correctness (phase 1) -- free, fast, no LLM calls, one
          command start to finish. `precedent_simulate.py quick`.
  record  tools/practice_simulation.py's synthetic-batch scoring (phases
          2-3) -- costs real LLM calls and a person's judgment at the
          generate/route steps, so it CANNOT be one synchronous command.
          What this wires up instead: once a batch has been scored
          (`practice_simulation.py new-batch` -> fill scenarios -> `route`
          -> fill answers -> `score`), `precedent_simulate.py record
          --batch ID` reads that real result (score_batch(), not a second
          computation of it) and logs it next to the quick-tier numbers.

THE TREND LOG. evals/simulation/trend.jsonl, one JSON object appended per
run -- never overwritten, never averaged into a single restated number
(exactly the failure docs-track-models exists to prevent). `trend` reads it
back and prints recent runs, split by mode and by repo, because a quick-tier
number, a this-repo batch, and a different-repo batch are not the same
measurement and pooling them would misstate all three (see
spec/SIMULATION_BRIEF.md sections 6-7). Committing the log (or not) is an
ordinary git decision like any other file this session touches -- this tool
does not commit anything itself.

NEVER AUTOMATIC, SAME AS EVERY TOOL THIS BRIEF HAS PRODUCED. This is a
plain CLI script. It is not named in any practice's `occasion` field, any
gate, or any hook -- `grep -rn "precedent_simulate" practices/
tools/precedent_gate.py .claude/` returns nothing, and must keep returning
nothing. It runs only when a person runs it, or explicitly asks an agent
session to in that turn. See "Never automatic" in spec/SIMULATION_BRIEF.md.

Run:
  python3 tools/precedent_simulate.py quick [--max-commits N]
                                             [--max-correctness-commits N]
  python3 tools/precedent_simulate.py record --batch BATCH_ID
  python3 tools/precedent_simulate.py trend [--last N]
"""
import datetime, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import practice_simulation as psim

TREND_LOG = ROOT / 'evals' / 'simulation' / 'trend.jsonl'

# -------------------------------------------------- parsing behavioral_replay
# Subprocess + parse its labeled output lines, the same pattern
# tools/precedent_check.py's own delegating checks already use for
# doc_lint.py/doc_sync.py/practice_audit.py/model_audit.py -- NOT a second
# implementation of the replay's arithmetic, just reading the numbers that
# arithmetic already printed. A refactor exposing behavioral_replay's
# internals as an importable function would be cleaner still, but this repo
# has an existing convention for exactly this shape and re-parsing
# clearly-labeled output is far lower risk than reworking an already-tested
# tool's internals for a caller that only needs five numbers out of it.
_HIT_RATE_RE = re.compile(
    r'Commits where at least one such practice.s applies_to matched a '
    r'changed file: (\d+) of (\d+) \((\d+)%\)')
_REDUCTION_RE = re.compile(r'Reduction: (\d+)%')
_REPLAY_STATUS_RE = re.compile(r'REPLAY_STATUS: (\S+)')
_MECH_RE = re.compile(
    r'(\d+) \(commit, proven-check\) data point\(s\): (\d+) clean, (\d+) violated, '
    r'(\d+) errored')


def _run_behavioral_replay(max_commits, max_correctness_commits):
    args = [sys.executable, str(ROOT / 'tools' / 'behavioral_replay.py'),
            '--with-checks']
    if max_commits is not None:
        args += ['--max-commits', str(max_commits)]
    if max_correctness_commits is not None:
        args += ['--max-correctness-commits', str(max_correctness_commits)]
    r = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True)
    out = r.stdout + r.stderr

    result = {'exit_code': r.returncode, 'raw_tail': '\n'.join(out.splitlines()[-40:])}
    m = _REPLAY_STATUS_RE.search(out)
    result['replay_status'] = m.group(1) if m else None
    m = _HIT_RATE_RE.search(out)
    if m:
        result['reach'] = {'hit_commits': int(m.group(1)), 'total_commits': int(m.group(2)),
                           'hit_rate_pct': int(m.group(3))}
    m = _REDUCTION_RE.search(out)
    result['context_reduction_pct'] = int(m.group(1)) if m else None
    m = _MECH_RE.search(out)
    if m:
        result['mechanical_correctness'] = {
            'data_points': int(m.group(1)), 'clean': int(m.group(2)),
            'violated': int(m.group(3)), 'errored': int(m.group(4)),
        }
    return result


def _append_trend(entry):
    TREND_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(TREND_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')


def cmd_quick(args):
    max_commits = int(args[args.index('--max-commits') + 1]) if '--max-commits' in args else None
    max_cc = (int(args[args.index('--max-correctness-commits') + 1])
             if '--max-correctness-commits' in args else None)

    print('Running the quick tier: tools/behavioral_replay.py --with-checks '
          '(mechanical, no LLM calls)...')
    replay = _run_behavioral_replay(max_commits, max_cc)

    entry = {
        'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'mode': 'quick',
        'repo_root': None,
        'replay_status': replay.get('replay_status'),
        'reach': replay.get('reach'),
        'context_reduction_pct': replay.get('context_reduction_pct'),
        'mechanical_correctness': replay.get('mechanical_correctness'),
    }
    _append_trend(entry)

    print(f"\nreplay status: {entry['replay_status']}")
    if entry['reach']:
        r = entry['reach']
        print(f"reach: {r['hit_commits']}/{r['total_commits']} commits "
              f"({r['hit_rate_pct']}%) had a path-triggered hit")
    if entry['context_reduction_pct'] is not None:
        print(f"context reduction vs. always-everything: {entry['context_reduction_pct']}%")
    if entry['mechanical_correctness']:
        mc = entry['mechanical_correctness']
        print(f"mechanical correctness: {mc['clean']}/{mc['data_points']} clean, "
              f"{mc['violated']} violated, {mc['errored']} errored")
    else:
        print('mechanical correctness: no data (behavioral_replay.py degraded, or no '
              'proven checked_by applied to any sampled commit) -- see raw output below')
    if replay['exit_code'] != 0 or not entry['reach']:
        print(f"\nbehavioral_replay.py exit code {replay['exit_code']}. Tail of its "
              f"output:\n{replay['raw_tail']}")
    print(f'\nLogged to {TREND_LOG}. Run `trend` to see this alongside past runs.')
    return 0


def cmd_record(args):
    batch_id = args[args.index('--batch') + 1]
    summary = psim.score_batch(batch_id)
    if summary['unscored']:
        sys.exit(f"precedent_simulate FAIL: batch {batch_id} has "
                 f"{len(summary['unscored'])} unanswered scenario(s) "
                 f"({', '.join(summary['unscored'])}) -- finish `route` and fill in "
                 f"answers/ before recording it to the trend log. A partially-scored "
                 f"batch logged now would misreport as a smaller, misleadingly-clean "
                 f"sample.")

    entry = {
        'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'mode': 'full',
        'batch_id': batch_id,
        'repo_root': summary['repo_root'],
        'scored': summary['scored'],
        'per_kind': {k: {'hit': v['hit'], 'total': v['total']}
                    for k, v in summary['per_kind'].items()},
        'plain_vs_adversarial_gap_points': summary['plain_vs_adversarial_gap_points'],
    }
    _append_trend(entry)
    print(f'Recorded batch {batch_id} to {TREND_LOG}'
          + (f' (repo: {summary["repo_root"]})' if summary['repo_root'] else ' (this repo)')
          + '.')
    return 0


def cmd_trend(args):
    last = int(args[args.index('--last') + 1]) if '--last' in args else None
    if not TREND_LOG.exists():
        print(f'No trend log yet at {TREND_LOG}. Run `quick`, or `record` a scored '
              f'batch, first.')
        return 0
    entries = [json.loads(l) for l in TREND_LOG.read_text(encoding='utf-8').splitlines()
              if l.strip()]
    if last:
        entries = entries[-last:]
    if not entries:
        print('Trend log exists but is empty.')
        return 0

    quick = [e for e in entries if e['mode'] == 'quick']
    full = [e for e in entries if e['mode'] == 'full']

    if quick:
        print(f'== quick tier -- {len(quick)} run(s), most recent last ==')
        for e in quick:
            reach = e.get('reach')
            reach_s = f"{reach['hit_rate_pct']}% reach" if reach else 'reach: n/a'
            mc = e.get('mechanical_correctness')
            mc_s = (f"{mc['clean']}/{mc['data_points']} clean" if mc else 'mechanical: n/a')
            print(f"  {e['timestamp_utc']}  status={e['replay_status']}  {reach_s}  "
                  f"{mc_s}  reduction={e.get('context_reduction_pct')}%")

    if full:
        print(f'\n== full tier -- {len(full)} batch(es), most recent last ==')
        # Grouped by repo, per spec/SIMULATION_BRIEF.md sections 6-7: a batch
        # against one repo is never comparable to a batch against another.
        by_repo = {}
        for e in full:
            by_repo.setdefault(e.get('repo_root') or '(this repo)', []).append(e)
        for repo, es in by_repo.items():
            print(f'  -- {repo} --')
            for e in es:
                bits = []
                for kind in ('positive', 'negative', 'adversarial'):
                    pk = e['per_kind'].get(kind)
                    if pk:
                        bits.append(f"{kind}={pk['hit']}/{pk['total']}")
                gap = e.get('plain_vs_adversarial_gap_points')
                gap_s = f", gap={gap:.0f}pt" if gap is not None else ''
                print(f"    {e['timestamp_utc']}  batch={e['batch_id']}  "
                      f"{', '.join(bits)}{gap_s}")

    if not quick and not full:
        print('Trend log has entries in an unrecognized shape.')
    return 0


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit('precedent_simulate FAIL: quick, record --batch ID, or trend.')
    cmd, rest = args[0], args[1:]
    if cmd == 'quick':
        return cmd_quick(rest)
    if cmd == 'record':
        return cmd_record(rest)
    if cmd == 'trend':
        return cmd_trend(rest)
    sys.exit(f'precedent_simulate FAIL: unknown command {cmd!r} -- '
             f'quick, record, or trend.')


if __name__ == '__main__':
    sys.exit(main())

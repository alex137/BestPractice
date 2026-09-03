#!/usr/bin/env python3
"""precedent_gate.py — the GATE-TRIGGERED loading channel.

PRACTICE_ENGINE_PLAN.md, "How an Agent Knows Which Practices to Load", names
four channels. This is the last one to be built:

    **Gate-triggered.** Runbook steps cite slugs; reaching the step loads
    them. A merge loads exactly the merge practices, at the moment of merging.

WHY IT HAD TO EXIST, measured rather than assumed. After phase 4's glob pass,
24 of the 46 on-demand practices still carry `applies_to: ["**"]`, and
tools/routing_scope.json records a reason for every one. A recurring reason:
**the practice fires at a moment, not in a place.** `merge-runbook` fires when
merging. `mistakes-become-rules` — the largest prose-only miss in the routing
eval, judged applicable in nine cases and found in five — fires when a review
turns up a defect. No glob reaches a moment, however well written, and the
plan forbids tuning the occasion index to compensate. A gate is the channel
those practices were always supposed to have.

WHAT THIS CHANNEL DOES AND DOES NOT PROMISE. Reach here is deterministic: if
the gate is invoked, the practice's Rule is in context, with no session
judgment involved. That is strictly stronger than the occasion index, which
requires a session to recognise the occasion, read a one-line clause, and
choose to open it. What it moves rather than solves is the question of
**whether the gate gets invoked** — a wiring problem, not a routing one. The
push gate is wired into templates/hooks/pre-push, so it fires whether or not
anyone remembers it. The others are cited by runbook steps and by the standing
instruction in the loader block, which is weaker, and is worth being plain
about rather than counting as solved.

**The routing eval cannot measure any of this.** It simulates the resident
block, the occasion index and the path channel against twenty commits; a gate
fires at a moment a commit does not record. No recall figure anywhere should
be attributed to this channel.

Run:
  python3 tools/precedent_gate.py merge      # the Rules for that moment
  python3 tools/precedent_gate.py --list     # gates, and what each one holds
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import split_practices as sp

SCOPE = ROOT / 'tools' / 'routing_scope.json'


def gate_vocabulary():
    """The closed set of gate names, and what moment each one is."""
    d = json.loads(SCOPE.read_text(encoding='utf-8'))
    return {k: v for k, v in d.get('gates', {}).items() if not k.startswith('_')}


def practices_by_gate():
    out = {g: [] for g in gate_vocabulary()}
    for f in sorted((ROOT / 'practices').glob('*.md')):
        try:
            fm, _sections = sp._read_practice_file(f)
        except sp.PracticeFileError:
            continue
        for g in json.loads(fm.get('gates', '[]') or '[]'):
            out.setdefault(g, []).append(fm['slug'])
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = {a for a in sys.argv[1:] if a.startswith('--')}
    vocab = gate_vocabulary()
    by_gate = practices_by_gate()

    unknown = flags - {'--list'}
    if unknown:
        sys.exit(f"precedent gate FAIL: unknown option(s) {', '.join(sorted(unknown))} "
                 f"-- the only option is --list.")
    if '--list' in flags:
        if args:
            sys.exit(f"precedent gate FAIL: --list takes no arguments, got "
                     f"{', '.join(args)!r}. Did you mean to drop --list and "
                     f"name a gate instead?")
        for g, moment in sorted(vocab.items()):
            print(f"  {g:8} {moment}")
            for s in by_gate.get(g, []):
                print(f"           - {s}")
        return 0
    if len(args) != 1:
        sys.exit(__doc__)
    gate = args[0]
    if gate not in vocab:
        # A silently-empty gate is the failure this whole design is most prone
        # to: a runbook step citing a gate nobody registered would load
        # nothing and report nothing, which reads exactly like a gate with no
        # practices. Name it instead.
        sys.exit(f"precedent gate FAIL: no gate named {gate!r}. Known gates: "
                 f"{', '.join(sorted(vocab))}. A gate is a MOMENT, declared in "
                 f"tools/routing_scope.json and named in each practice's "
                 f"`gates:` field.")
    slugs = by_gate.get(gate, [])
    if not slugs:
        sys.exit(f"precedent gate FAIL: gate {gate!r} ({vocab[gate]}) has no "
                 f"practices registered to it. An empty gate is a step that "
                 f"loads nothing and looks like it worked.")
    print(f"# Practices for the {gate} gate — {vocab[gate]}\n")
    for slug in slugs:
        fm, sections = sp._read_practice_file(ROOT / 'practices' / f'{slug}.md')
        print(f"### {slug}\n{sections.get('rule', '').strip()}\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())

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
**whether the gate gets invoked** — a wiring problem, not a routing one.

A 2026-09-04 gate audit applied the same skepticism phase 4 applied to
`checked_by` (see spec/ENFORCEMENT.md's "What phase 4 found before it built
anything") to this channel, and found the identical failure class once:
`push` and `reply`
are the only two gates with an actual invocation point anywhere in this
repo's templates (a git pre-push hook, a Claude Code Stop hook — the only
two adapter mechanisms that exist to interrupt a session at all; see
templates/harness/README.md's table). `push` was wired, into
templates/hooks/pre-push. `reply` was not: routing_scope.json's own
vocabulary names its moment as "the stop hook", and
templates/harness/claude-code/hooks/stop-git-check.sh — the only stop-hook
script any adapter ships — never called this file. The claim and the wiring
had drifted apart, unnoticed, the same way seven of eight `checked_by`
claims had. It is fixed now (both that template and this repo's own
`.claude/hooks/stop-git-check.sh`), and `check_gate_channel` in
tools/verify_harness.py asserts it stays fixed, the same way it already
asserted `push`'s wiring.

`merge` and `review` remain cited only — by runbook steps and by the
standing instruction in the loader block — and that is not a TODO to close,
it is this channel's honest, permanent shape: no adapter here has a
merge-time or review-time hook to interrupt a session the way Stop and
pre-push do, so there is nothing to wire. Weaker than `push`/`reply`, and
worth staying plain about rather than counting as solved.

**The routing eval cannot measure any of this.** It simulates the resident
block, the occasion index and the path channel against twenty commits; a gate
fires at a moment a commit does not record. No recall figure anywhere should
be attributed to this channel.

Run:
  python3 tools/precedent_gate.py merge          # the Rules for that moment
  python3 tools/precedent_gate.py --list         # gates, and what each one holds
  python3 tools/precedent_gate.py --repo DIR merge
      # the Rules for that moment, from DIR's practices/ instead of this
      # repo's own
"""
import json, pathlib, sys

# _ENGINE_DIR (where this file itself lives) is only for the sibling-module
# import and for routing_scope.json below -- both ship as one fixed unit
# with the engine code, not with whichever repo's content --repo points at
# (the closed gate vocabulary and which moments have a real invocation
# point are a property of the engine, not of one repo's practice catalogue).
# ROOT is which repo's practices/ to read, defaulting to the engine's own
# parent directory but overridable with --repo in main() -- see
# precedent_show.py for the fuller rationale.
_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = _ENGINE_DIR.parent  # unchanged default when --repo is omitted
sys.path.insert(0, str(_ENGINE_DIR))
import split_practices as sp

SCOPE = _ENGINE_DIR / 'routing_scope.json'


def gate_vocabulary():
    """The closed set of gate names, and what moment each one is."""
    d = json.loads(SCOPE.read_text(encoding='utf-8'))
    return {k: v for k, v in d.get('gates', {}).items() if not k.startswith('_')}


def practices_by_gate(practices_dir=None):
    practices_dir = practices_dir if practices_dir is not None else ROOT / 'practices'
    out = {g: [] for g in gate_vocabulary()}
    for f in sorted(practices_dir.glob('*.md')):
        try:
            fm, _sections = sp._read_practice_file(f)
        except sp.PracticeFileError:
            continue
        for g in json.loads(fm.get('gates', '[]') or '[]'):
            out.setdefault(g, []).append(fm['slug'])
    return out


def main():
    argv = sys.argv[1:]
    repo = None
    if '--repo' in argv:
        i = argv.index('--repo')
        if i + 1 >= len(argv):
            sys.exit("precedent gate FAIL: --repo needs a value.")
        repo = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    root = pathlib.Path(repo).resolve() if repo else ROOT
    practices_dir = root / 'practices'

    args = [a for a in argv if not a.startswith('--')]
    flags = {a for a in argv if a.startswith('--')}
    vocab = gate_vocabulary()
    by_gate = practices_by_gate(practices_dir)

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
        fm, sections = sp._read_practice_file(practices_dir / f'{slug}.md')
        print(f"### {slug}\n{sections.get('rule', '').strip()}\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())

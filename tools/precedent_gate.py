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
import json, pathlib, subprocess, sys

# _ENGINE_DIR (where this file itself lives) is only for the sibling-module
# import and for routing_scope.json below -- both ship as one fixed unit
# with the engine code, not with whichever repo's content --repo points at
# (the closed gate vocabulary and which moments have a real invocation
# point are a property of the engine, not of one repo's practice catalogue).
# ROOT is which repo's practices/ to read, defaulting to the engine's own
# parent directory but overridable with --repo in main() -- see
# precedent_show.py for the fuller rationale.
_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
# practice: fix-the-original -- ROOT is the repo whose CONTENT this reads, and
# `_ENGINE_DIR.parent` is the wrong answer for exactly one layout: an engine
# copy vendored inside a consuming repo at process/upstream/tools/. There ROOT
# lands on the VENDORED tree, whose practices/ is the universal catalogue
# alone, so every team and individual practice reads as absent -- silently,
# which is the one failure mode this project exists to prevent. Reproduced
# 2026-09-14 in a real consumer: `precedent_show.py default-register` answered
# "unknown slug", for a team practice that repo has in force.
# consuming_repo_root() returns _ENGINE_DIR.parent unchanged everywhere else.
try:                                            # noqa: E402
    import sys as _sys
    _sys.path.insert(0, str(_ENGINE_DIR))
    from precedent_source_credentials import consuming_repo_root as _consuming
except Exception:                  # a vendored tree older than that module --
    def _consuming(engine_root):   # keep the historical default rather than
        return engine_root         # fail (practice: fail-gracefully)
ROOT = _consuming(_ENGINE_DIR.parent)  # unchanged default when --repo is omitted
sys.path.insert(0, str(_ENGINE_DIR))
import split_practices as sp
# Closed and pruned from TODO.md (was the `gate-and-paths-unreachable-source` item): this channel read practices/*.md directly,
# bypassing precedent_show.py's materialized-source reachability note
# (PR #114) the same way precedent_paths.py did. Fixed by importing
# precedent_show.py's two helpers directly -- same discipline this file
# already uses for split_practices.py, not a subprocess call (which would
# mean re-parsing precedent_show.py's own "### slug\n<body>" stdout format
# back into structured data here, solely to get a note this file can
# already print itself once it has the same two functions) and not a
# copy-pasted second implementation (which is exactly the kind of drift
# this repo's own engine-plus-host-shims practice exists to prevent).
import precedent_show as ps
import build_views as bv

SCOPE = _ENGINE_DIR / 'routing_scope.json'


def gate_vocabulary():
    """The closed set of gate names, and what moment each one is."""
    # Graceful degradation, not a crash: this engine file is vendored into
    # consuming repos, where routing_scope.json is a separate copy that a
    # partial vendor can leave out. Absent, this used to raise a bare
    # FileNotFoundError from inside a gate the session runs at a named
    # moment (merge, push, reply), which reads as the gate itself being
    # broken rather than as one missing file with a one-line fix.
    if not SCOPE.is_file():
        sys.exit(f"precedent gate FAIL: {SCOPE} is missing. It ships beside "
                 f"this script as one unit; re-vendor the engine "
                 f"(python3 tools/precedent_vendor_engine.py refresh "
                 f"<bestpractice-clone>) or copy routing_scope.json from "
                 f"the source repo's tools/.")
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
        # A practice not in force is not registered to any gate. This is
        # the channel where getting it wrong costs most -- the gates are
        # the blocking path, so an unfiltered `status:` here means a
        # dropped rule keeps being served as a requirement at merge time
        # (which is exactly what masked a bad drop for a day: the gate
        # kept serving the practice the index had already removed).
        if not bv.is_in_force(fm):
            continue
        for g in json.loads(fm.get('gates', '[]') or '[]'):
            out.setdefault(g, []).append(fm['slug'])
    return out


# Levels whose practice TEXT is private -- their sources are private
# repositories, and this repo is public. Imported from build_views where it
# is declared, with a literal fallback for a partial vendor: the two
# answering differently is the failure this whole split exists to prevent.
PRIVATE_LEVELS = getattr(bv, 'PRIVATE_LEVELS', ('shared', 'team', 'individual'))


def resolved_gate_practices(root, gate):
    """-> (entries, notes). Every IN-FORCE practice registered to `gate` in
    any source this repo resolves -- team, individual and repo-local as well
    as universal -- as (slug, level, source_name, path) tuples.

    WHY THIS EXISTS, and what it cost to leave out. Until 2026-09-13 this
    file read exactly one directory: `<root>/practices/`. In a consuming
    repo that is the materialized union of every source, so nothing was
    missing. In THIS repo -- and in any repo whose sources resolve as
    sibling clones rather than through precedent_materialize.py -- it is the
    universal catalogue alone, so a team or individual practice declaring
    `gates: ["reply"]` had no invocation point anywhere: the stop hook ran
    the gate, the gate read a directory those practices are not in, and
    printed the universal three. Measured here that day: three individual
    practices about how a reply is written (`next-steps-after-commit`,
    `closing-items-are-this-thread`, `handoff-only-when-blocked`) were
    registered to the reply gate and reached a session only through the
    one-line occasion clause in `.precedent/SESSION_PRACTICES.md` -- which
    fires only if the session recognises the occasion, which is exactly the
    "sometimes it does, sometimes it does not" Morgan reported.

    A gate is the channel whose whole promise is that reach does not depend
    on session judgment (see this module's header). A gate that serves one
    source silently keeps that promise for one level and breaks it for the
    other three.

    Failure here is never fatal: a repo with no resolvable source still gets
    its own practices/ -- the caller unions the two -- and the reason is
    NAMED rather than swallowed (practice: fail-gracefully).
    """
    notes = []
    try:
        import precedent_resolve as pr
    except ImportError:
        return [], ['precedent_resolve.py is not vendored beside this script, '
                    'so only this repo\'s own practices/ is below.']
    try:
        sources = pr.load_config(root)
        res = pr.resolve(sources)
    except Exception as e:                                   # noqa: BLE001
        return [], [f'the declared sources could not be resolved ({e}), so '
                    f'only this repo\'s own practices/ is below.']

    for m in res.get('missing', []):
        notes.append(
            f"{m['level']}/{m['name']} did NOT resolve this session "
            f"({m.get('reason', 'no reason given')}) -- any {gate}-gate "
            f"practice of its own is NOT below. Treat that as unknown, not "
            f"as 'that source has nothing for this gate'.")

    entries = []
    for slug, practice in sorted(res['practices'].items()):
        try:
            gates = json.loads(practice['fm'].get('gates', '[]') or '[]')
        except json.JSONDecodeError:
            continue
        if gate in gates:
            entries.append((slug, practice['level'], practice.get('source', ''),
                            pathlib.Path(practice['file'])))
    return entries, notes


def _unlanded_work(root):
    """-> [str] one line per repo in this session whose committed work is not
    on the branch that repo actually merges into. Never raises.

    WHY THE REPLY GATE AND NOT THE STOP HOOK (Morgan, 2026-09-21, strength:
    decided): "if there are changes that are committed but NOT YET ON
    main/precedent-beta-v01/primary-branch-in-that-repo, then the Boildown
    section MUST MUST tell me that and recommend I do that, so I don't miss
    doing it."

    The stop hook already refuses a turn that ends with uncommitted or
    unpushed work, and that is a different question with a different timing.
    It fires AFTER the reply is written, so it cannot put a line in the
    Boildown -- it can only reject the turn and cost the reply twice. And it
    asks whether a branch is PUSHED, which a feature branch can be while the
    work still sits nowhere anybody merges from.

    This fires BEFORE the reply, at the one moment a session can still write
    the sentence, and asks the question a person actually cares about: is
    this on the branch the repo lands work on, or is it parked on a branch
    somebody has to remember to merge?
    """
    import subprocess as _sp

    def _git(cwd, *args):
        try:
            r = _sp.run(['git', '-C', str(cwd), *args], capture_output=True,
                        text=True, timeout=20)
        except Exception:                                     # noqa: BLE001
            return ''
        return r.stdout.strip() if r.returncode == 0 else ''

    out = []
    roots = [pathlib.Path(root)]
    # Sibling Precedent repos this session may also have committed in. A
    # session that made a commit in a source set and left it on a branch has
    # the same problem, and nothing else in this preamble looks there.
    for parent in {pathlib.Path(root).parent, pathlib.Path.home()}:
        try:
            entries = sorted(parent.iterdir())
        except OSError:
            continue
        for d in entries:
            if d.name.startswith('precedent-') and (d / '.git').exists():
                if d.resolve() not in {r.resolve() for r in roots}:
                    roots.append(d)

    for repo in roots:
        head = _git(repo, 'rev-parse', '--abbrev-ref', 'HEAD')
        if not head or head == 'HEAD':
            continue
        # The branch this repo actually lands work on. precedent.json's
        # base_branch is the declaration; origin/HEAD is the fallback.
        base = ''
        try:
            import json as _j
            base = (_j.loads((repo / 'precedent.json').read_text(
                encoding='utf-8')).get('base_branch') or '').strip()
        except Exception:                                     # noqa: BLE001
            base = ''
        if not base:
            ref = _git(repo, 'symbolic-ref', '--quiet', 'refs/remotes/origin/HEAD')
            base = ref.rsplit('/', 1)[-1] if ref else 'main'
        if head == base:
            continue
        ahead = _git(repo, 'rev-list', '--count', f'origin/{base}..HEAD')
        if not ahead or ahead == '0':
            continue
        name = repo.name if repo.resolve() != pathlib.Path(root).resolve() \
            else 'this checkout'
        out.append(f"{name}: {ahead} commit(s) on '{head}' that are NOT on "
                   f"'{base}' -- the branch this repo lands work on")
    return out


def _print_hard_requirements(root):
    """The reply requirements a source DECLARES, printed verbatim at the
    start of the turn.

    WHY, measured 2026-09-13, the day the blocking half landed. A Stop hook
    fires after the reply has already been rendered to the person, so
    refusing the stop cannot un-render it: every refusal costs them the same
    reply twice, once wrong and once rewritten. Morgan saw that repeatedly
    within hours of the check going in -- "you posted your message to me
    twice ... many times. That never happened before."

    The refusals were not the check being wrong. They were the requirement
    arriving after the only moment it could have been applied. This channel
    fires BEFORE the reply, and it carried one-line practice clauses only --
    summaries, written by hand, which is exactly how one of them came to say
    "in bold" about a rule whose whole point is that bold is not enough. A
    summary cannot be what a mechanical check is read from; the check's own
    input can. So the literal heading pattern and the literal sentences go
    here, from the same reply_check.json the hook reads, and the block
    stays a backstop instead of the primary channel.

    Silent when no source declares any, which is most repos -- and never
    fatal: a reminder that cannot be built must not take the gate down with
    it (practice: fail-gracefully).
    """
    try:
        import precedent_reply_check as prc
    except ImportError:
        # A PARTIAL VENDOR, named as one. This module ships beside this file
        # as one unit; absent, the requirements cannot be read AND the stop
        # hook that enforces them is not running either, so the reply is
        # unchecked in both directions. Say which, and how to fix it.
        print("\nNOTE: precedent_reply_check.py is not vendored beside this "
              "script, so no declared reply requirement is below AND none is "
              "being enforced. Re-vendor the engine (python3 "
              "tools/precedent_vendor_engine.py refresh <bestpractice-clone>).")
        return
    try:
        reqs, notes = prc.declared_requirements(root)
    except Exception as e:                                   # noqa: BLE001
        print(f"\nNOTE: the declared reply requirements could not be read "
              f"({e}), so they are not below. Treat that as unknown, not as "
              f"'there are none'.")
        return
    if not reqs and not notes:
        return
    print("\n## Hard requirements — the stop hook REFUSES the turn without "
          "these\n")
    for r in reqs:
        src = r.get('_source', 'a source')
        pat = r.get('require_heading_matching')
        if pat:
            print(f"- [{src}] the reply carries a real markdown heading "
                  f"(`## `) matching /{pat}/i. Bold text is not a heading.")
        one_of = r.get('require_one_of') or []
        if one_of:
            quoted = ' or '.join(f'"{s}"' for s in one_of)
            every = r.get('require_when_context_grew_tokens')
            when = ('' if not every else
                    f" -- but ONLY once this conversation has grown "
                    f"{int(every):,} tokens since one of them was last said, "
                    f"and the stop hook is the thing that knows whether it "
                    f"has. Below that it is silent, so do not add the line "
                    f"out of caution")
            print(f"- [{src}] the reply contains one of these, verbatim: "
                  f"{quoted}{when}")
        # THE TWO PREDICATES THIS BLOCK USED TO OMIT, both of them
        # BLOCKING. Until 2026-09-21 this printer handled
        # require_heading_matching and require_one_of and silently dropped
        # the rest, so require_no_contradiction refused turns that had
        # never been told it existed -- which is precisely the failure this
        # function's own docstring above describes and was written to end.
        # A blocking requirement absent from the pre-reply print costs the
        # person the reply twice: once wrong, once rewritten.
        for pair in (r.get('require_no_contradiction') or []):
            if pair.get('if_says') and pair.get('must_not_say_matching'):
                print(f"- [{src}] a reply saying \"{pair['if_says']}\" must "
                      f"not ALSO match /{pair['must_not_say_matching']}/i -- "
                      f"the two cannot both be true. Say the one that is.")
        for pair in (r.get('require_paired_with') or []):
            if pair.get('if_matches') and pair.get('must_also_match'):
                print(f"- [{src}] a reply matching /{pair['if_matches']}/ "
                      f"must ALSO match /{pair['must_also_match']}/"
                      + (f" -- {pair['why']}" if pair.get('why') else ''))
        # THE ONE PREDICATE WHOSE ANSWER IS ALREADY KNOWABLE HERE, so this
        # prints the ANSWER and not just the rule (2026-09-22). Every other
        # line in this block states a requirement the reply has yet to meet;
        # this one is a fact about the disk, true or false before a word of
        # the reply is written. Printing "do not say the archive line if the
        # container is unsafe" and leaving the session to wonder which it is
        # would reproduce, one rung up, exactly the failure this whole
        # function exists to end -- the person paying for the reply twice.
        # Silent when the container is clean, which is the ordinary case.
        for _ph in (r.get('require_container_safe_if_says') or []):
            _verdict = _container_report()
            if _verdict is None:
                print(f"- [{src}] a reply saying \"{_ph}\" requires a "
                      f"container with nothing uncommitted and nothing off a "
                      f"remote -- and the scanner that checks it "
                      f"(tools/precedent_container_safe.py) is not vendored "
                      f"beside this script, so it is NOT being enforced here.")
            elif _verdict:
                print(f"- [{src}] DO NOT SAY \"{_ph}\" IN THIS REPLY -- "
                      f"the stop hook will refuse it. This container holds "
                      f"work that exists nowhere else:\n{_verdict}")

        # A REQUIREMENT THIS ENGINE CANNOT EVALUATE, named here rather than
        # left silent. A source's reply_check.json is read live; the engine
        # is vendored; they go stale independently, so a source can declare
        # a blocking rule this copy has never heard of. getattr, because
        # this file and precedent_reply_check.py are vendored as one unit
        # but a partial or older vendor is exactly the state this reports.
        _unk_fn = getattr(prc, '_unknown_predicates', None)
        for _k in (_unk_fn(r) if _unk_fn else ()):
            print(f"- NOT ENFORCED HERE: [{src}] declares {_k}, which this "
                  f"engine cannot evaluate. Its requirement is NOT in force "
                  f"in this repo. Refresh the vendored engine: python3 "
                  f"tools/precedent_vendor_engine.py refresh "
                  f"<bestpractice-clone>")
    for n in notes:
        print(f"- NOTE: {n}")


def _container_report():
    """-> the scanner's report when this container is NOT safe to lose, '' when
    it is, or None when there is no scanner to run.

    Deliberately three-valued. '' and None both print nothing, but they mean
    opposite things -- "checked, clean" and "not checked at all" -- and the
    caller says so for the second, because a requirement nobody is evaluating
    is not a requirement that is being met.
    """
    tool = pathlib.Path(__file__).resolve().parent / 'precedent_container_safe.py'
    if not tool.is_file():
        return None
    try:
        p = subprocess.run([sys.executable, str(tool)],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode == 0:
        return ''
    return '\n'.join('    ' + ln for ln in (p.stdout or '').strip().splitlines())


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

    unknown = flags - {'--list', '--brief'}
    if unknown:
        sys.exit(f"precedent gate FAIL: unknown option(s) {', '.join(sorted(unknown))} "
                 f"-- the options are --list and --brief.")
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
    # Own tree first, then every other source this repo resolves. The union
    # is what "the practices in force at this moment" means; reading the
    # directory alone answered it for one level only (see
    # resolved_gate_practices). Resolution WINS on a slug both carry, since
    # it has applied precedence across the sources and the directory has
    # not.
    registered = {s: ('universal', '', practices_dir / f'{s}.md')
                  for s in by_gate.get(gate, [])}
    entries, source_notes = resolved_gate_practices(root, gate)
    for slug, level, name, path in entries:
        registered[slug] = (level, name, path)
    slugs = sorted(registered)
    if not slugs:
        sys.exit(f"precedent gate FAIL: gate {gate!r} ({vocab[gate]}) has no "
                 f"practices registered to it. An empty gate is a step that "
                 f"loads nothing and looks like it worked.")
    manifest = ps._materialize_manifest(root)
    # A session about to WRITE A REPLY under the wrong rules is the costliest
    # form of the missing-sources failure, and the one nobody notices: the
    # rules that did not load are disproportionately about how a reply is
    # written. So the reply gate says it, at the moment it matters
    # (practice: fail-gracefully -- never look complete).
    if gate == 'reply':
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            import precedent_source_credentials as psc
            line = psc.remind(root, prefix='precedent gate')
            if line:
                print(f"{line}\n")
        except ImportError:
            pass

        # Whether anyone other than Morgan has pushed to precedent-beta-v01
        # since he was last told -- silent except on a real alert, which is
        # the whole point: the always-printed status line lives in
        # .claude/hooks/session-start.sh's own call to the same module,
        # once per session, not here on every single reply. This module is
        # repo-local to alex137/BestPractice (its own two-branch carry
        # model), not a vendored engine file, so a consuming repo's copy of
        # this gate script simply has no sibling to import and stays quiet.
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            import precedent_beta_watermark_check as pbw
            alert = pbw.remind(root)
            if alert:
                print(f"{alert}\n")
        except ImportError:
            pass

    # EVERY gate, not one of them: a session whose SessionStart hooks never
    # ran is working under rules it cannot see, with an identity it did not
    # choose, and nothing in its own output says so.
    #
    # tools/precedent_session_check.py has answered this since 2026-09-08,
    # and its own docstring names its two routes: AGENTS.md's opening banner,
    # and somebody remembering to run it. On 2026-09-14 a session read that
    # banner, did not run it, and spent hours with four guarantees down --
    # noticing only when two uninstalled packages surfaced as three
    # unrelated-looking verify_harness failures (record/GOTCHAS.md#g1,
    # #g17). Guidance a session can skip is not a mechanism. A gate is
    # something it runs at a named moment, so the gate is where this belongs.
    #
    # Offline, so it costs a tenth of a second and never fetches; silent
    # when every guarantee holds, which is the normal case and prints
    # nothing at all. Never fatal: the gate's job is the practices, and a
    # session with a broken environment still needs them (fail-gracefully).
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_session_check as psck
        block = psck.remind(prefix='precedent gate')
        if block:
            print(f"{block}\n")
    except Exception:
        # This tool reads git config and the filesystem; on a repo shape it
        # does not expect it may raise, and a gate that dies because its
        # ADVISORY block failed would be worse than one that stays quiet.
        pass
    # A session about to PUBLISH is the last point at which the always-loaded
    # surfaces can still be looked at cheaply, and the only point at which
    # somebody is certainly paying attention to gates. The ceiling check is
    # binary -- green at 11,999 tokens and red at 12,001 -- so it reports the
    # wall only once a session has hit it, which on 2026-09-13/14 happened
    # four times in two days to three sessions that had come to do something
    # else (practice: session-load-budget). This says the DISTANCE instead.
    # Never fatal, never a finding: it is a number to know, and a gate that
    # blocks on approaching a ceiling would be the raise-it pressure the
    # practice exists to resist (practice: fail-gracefully).
    if gate in ('merge', 'push'):
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            import session_load_trend as slt
            line = slt.headroom_notice(root)
            if line:
                print(f"{line}\n")
        except ImportError:
            # A partial vendor: expected, and the block above treats a missing
            # sibling the same way. Silent because there is nothing the reader
            # can act on at this moment.
            pass
        except Exception as e:                               # noqa: BLE001
            # Anything ELSE is said out loud. Swallowing it would print no
            # notice, which reads exactly like "you have plenty of room" --
            # a wrong answer wearing the shape of a right one
            # (practice: fail-gracefully -- never look complete).
            print(f"NOTE: the session-load headroom could not be computed "
                  f"({e}). Treat that as unknown, not as room to spare; "
                  f"`python3 tools/session_load_trend.py` reports it "
                  f"directly.\n")
    # THE VENDORED ENGINE'S OWN FRESHNESS, at the two moments work leaves
    # this repo (2026-09-21). Every other check here compares a repo
    # against itself; this one compares this repo's manifest against live
    # upstream and says whether the engine it is enforcing with has fallen
    # behind. Pushing or merging on a months-old engine is the case that
    # kept happening silently -- 18 of 22 repositories had never taken an
    # update, measured 2026-09-20.
    #
    # --quiet: it prints ONLY when this repo is actually behind. A gate
    # that says "current" at every push is a gate people stop reading, and
    # the notice has to stay worth noticing. Never fatal, and the tool
    # itself exits 0 on no network, no manifest and a malformed one, so
    # this cannot block a push over a hiccup (practice: fail-gracefully).
    if gate in ('merge', 'push'):
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            import precedent_engine_freshness as pef
            pef.report(root, quiet=True)
        except ImportError:
            pass          # partial vendor, same as the block above
        except Exception as e:                               # noqa: BLE001
            print(f"NOTE: the vendored engine's freshness could not be "
                  f"checked ({e}). Treat that as unknown, not as current; "
                  f"`python3 tools/precedent_engine_freshness.py` reports "
                  f"it directly.\n")

    for n in source_notes:
        print(f"NOTE: {n}\n")
    if any(registered[s][0] in PRIVATE_LEVELS for s in slugs):
        # Same standing rule as .precedent/SESSION_PRACTICES.md's header,
        # said at the other place this text now surfaces: a private source's
        # practice text has never been published, and this repo is public.
        print("NOTE: some rules below come from PRIVATE sources (team, "
              "individual). They bind this work exactly as the universal "
              "ones do; never quote their text into a commit message, a "
              "pull request or an issue.\n")

    print(f"# Practices for the {gate} gate — {vocab[gate]}\n")
    for slug in slugs:
        level, name, path = registered[slug]
        fm, sections = sp._read_practice_file(path)
        where = level if level in ('universal', 'repo-local') else f'{level}/{name}'
        if '--brief' in flags:
            # One line per practice, for the per-turn channel: the full Rules
            # of a busy gate are thousands of tokens, and a reminder a session
            # pays for on every prompt has to be cheap enough to keep
            # (practice: session-load-budget).
            #
            # A RESIDENT practice is skipped here rather than abbreviated: it
            # is in the session's loader block already, in full, from the
            # first turn. Repeating it per prompt buys nothing and is exactly
            # the drift that makes a per-turn reminder too expensive to keep.
            # It is also why three of them rendered as an empty clause -- a
            # resident practice has no index_clause, because the index is the
            # channel it does not use.
            if bv._json_str(fm.get('tier', '')).strip() == 'resident':
                continue
            clause = (bv._json_str(fm.get('index_clause', '')).strip()
                      or bv._json_str(fm.get('title', '')).strip())
            print(f"- **{slug}** ({where}) — {clause}")
            continue
        block = f"### {slug} ({where})\n{sections.get('rule', '').strip()}"
        if manifest is not None:
            note = ps._source_unreachable_note(manifest, slug)
            if note:
                block += f"\n{note}"
        print(f"{block}\n")
    if gate == 'reply':
        _print_hard_requirements(root)
        # COMMITTED, BUT NOT WHERE WORK LANDS. Printed with the hard
        # requirements because for this person it is one: a reply that does
        # not say so is how a branch gets forgotten.
        try:
            _unlanded = _unlanded_work(root)
        except Exception:                                     # noqa: BLE001
            _unlanded = []
        for _line in _unlanded:
            print(f"- NOT YET LANDED: {_line}. The Boildown MUST say so and "
                  f"recommend merging it -- do not close a turn leaving this "
                  f"unsaid (practice: the-boildown).")
    if '--brief' in flags:
        print(f"\nFull text: `python3 tools/precedent_gate.py {gate}`.")
    return 0


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/FOR_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())

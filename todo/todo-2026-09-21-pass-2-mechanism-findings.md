---
slug:              todo-2026-09-21-pass-2-mechanism-findings
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "three of these are one-file edits in tools/very_deep_check.py and tools/verify_harness.py; another session was editing the first of those while this run was going on"
noted:             2026-09-21
closed:            null
---
## What

Pass 2 of the 2026-09-21 very deep check: the half a script cannot do —
reading each mechanism against its own description and asking whether it
does what it says. The mechanical layer was already green when this
started. What was fixed in the same pass is at the bottom.

## 1. `very_deep_check.py` accepts any unrecognised flag, runs the whole check, and writes a tracked file

**The one tool in `tools/` that writes to the tree on a read-only verb.**
`main()` reads every option by membership test (`'--json' in args`, …) and
never validates `args` against a known set, so `--check`, `--explain` and
`--list` — verbs every sibling tool takes — fall through to a full run:
about 90 seconds, 57 GitHub API calls, and a write to the tracked
[record/very-deep-check-ledger.json](../record/very-deep-check-ledger.json).

Measured by sweeping all 69 tools in `tools/` with `--help`, `--check`,
`--explain` and `--list` against a throwaway copy of the tracked tree.
Every other write anywhere in that sweep was a `.pyc`:

    --check   : very_deep_check.py rc=1  changed: ['record/very-deep-check-ledger.json']
    --explain : very_deep_check.py rc=1  changed: ['record/very-deep-check-ledger.json']
    --list    : very_deep_check.py rc=1  changed: ['record/very-deep-check-ledger.json']
    --help    : (no tool changed or deleted any tracked file)

This is the exact shape the `--help` planted case exists to forbid — *"a
tool that simply ignores an unrecognised flag runs its whole normal job and
exits 0"* — and the exact question pass 2 asks ("does anything named
`--check`, `--dry-run` or `--verify` write?"). **Fix:** collect the
recognised flags and refuse anything else with exit 2.

## 2. The `--help` planted case cannot see a deletion, and one arm of it is dead code

`check_tools_answer_help_without_writing` compares hash snapshots over the
intersection of before and after, plus after-minus-before. **A tool that
deletes a tracked file lands in `before - after` and is never reported** —
which is the more dangerous half of the incident the practice itself cites
(*"deleted 57 tracked files when one source was unreachable, while printing
a check verdict"*). Demonstrated on a case that deleted one file and
modified another: `reported as written: ['b.md']`, `actually deleted and
never reported: ['c.md']`.

Separately, `wrote += sorted(set(after) - set(before))` can never be
non-empty: `snapshot()` iterates only the tracked-file list and every
tracked regular file is copied before `before` is taken, so `after ⊆
before` always.

**Fix:** report `changed`, `removed` and `added` separately in the same
assertion — and widen the sweep past `--help`, which is the durable fix for
finding 1 as well. The case's own docstring already argues the principle:
*"the safe mode has to be the one you get by accident."*

## 3. `verify_harness.py`'s baseline case throws away the evidence

`tools/verify_harness.py:6817` binds `out` to the empty string rather than
the subprocess output, and nothing reads `out` afterwards. So when the
baseline fails, the harness prints *"an unplanted copy of this tree passes
every check"* with no reason — which is why the start of this very run had
to reproduce the failure by hand to learn what was red.

The reporter already accepts a third tuple element as `detail`, so the fix
is three lines: keep `stdout + stderr` and pass the last dozen non-blank
lines as that element.

## 4. `merge-target-is-beta-branch`'s check tests a property its own Rule now contradicts

**This is the repository's most load-bearing governance rule, and the check
behind it goes red on the sanctioned state.**

`local/tools/checks/check_merge_target_is_beta_branch.py` asserts that
`origin/precedent-beta-v01` must NOT be an ancestor of `origin/main`, on
the premise — in its own message — that this happens *"ONLY once Alex has
reviewed and merged precedent-beta-v01 into main for real (in which case
retire this practice in the same PR)"*.

[AGENTS.md](../AGENTS.md)'s opening paragraph and the practice's own
`expires:` field have said the opposite since 2026-09-14: Morgan merges
beta into main **regularly**, and *"that does not retire this rule"*. A
regular fold-in makes beta an ancestor **by construction**. Verified on
today's tip:

    $ git log --oneline -1 origin/main
    fb1e0a5f9 Merge precedent-beta-v01 into main — regular fold-in, 2026-09-21 (#532)
    $ git merge-base --is-ancestor $(git rev-parse origin/main^2) origin/main; echo $?
    0                                    # -> the check returns VIOLATION
    $ git rev-list --count $(git rev-parse origin/main^2)..origin/precedent-beta-v01
    23                                   # only these later commits make it green now

So it is green at this instant **purely by accident of timing**, and was
red from the moment PR #532 landed until the branch moved on — printing a
message telling the reader to retire a practice that must not be retired.

**Not patched here, deliberately.** Ancestry can no longer express the
rule. The narrowest honest replacement is to flag only beta content
arriving on `main`'s own **first-parent** line, which is what a pull
request mis-based on `main` produces and what the PR #89 incident actually
was. But the right property is a judgment call about what "targets main"
means after 2026-09-14, and the docstring's whole premise has to be
rewritten with it.

## 5. `--with-harness` records in the ledger, but "owed" and "ran and failed" are the same row

The help claim is true — the section is bracketed by `led.start`/`led.end`
on both paths and rows are in the ledger today. But `led.end` maps `'owed'`
to `findings=1`/`status: findings`, and a run that DID fire `--all` and
failed maps to exactly the same thing. The section exists to settle *when
was the full set last actually run*, and the cross-run read cannot answer
that from the component rows. `end()` already takes a `status=` parameter;
passing it explicitly is the fix.

## Not a Finding, Recorded Because It Was Asked

`/root/precedent-individual/.github/workflows/engine-refresh.yml`, flagged
by `CI WORKFLOW FILES OUTSIDE VENDORING`, was verified **by content, not by
name**, as `workflow-file-outside-vendoring` requires. It is a live,
hand-authored, deliberately-not-templated workflow belonging to that
practice set; its header records that the weekly cron ran 2026-09-06 to
2026-09-14 and was removed by Morgan (report rate 100%, landing rate 0%),
that `workflow_dispatch` was kept on purpose, and why it is not in
Precedent's templates. The scan's own docstring predicts this exact row as
legitimate. **The mechanism is honest; the candidate is correctly reported
as a candidate and correctly not reported as a verdict.**

## Fixed in This Pass

  - **[AGENTS.md](../AGENTS.md)'s quick index named a heading the blocking
    reply gate refuses.** The row told every session the closing section of
    a reply is **Next Steps**; `precedent_reply_check.py --explain` says the
    blocking requirement is a heading matching `/boildown/i`, and
    `next-steps-after-commit` is `status: deduplicated`,
    `in_force_at: the-boildown`. A session trusting the row writes
    `## Next Steps` and the Stop hook refuses the turn. Now reads
    **Boildown**.
  - **[tools/doc_coverage.json](../tools/doc_coverage.json) named
    `identity.json` twice.** It has never been tracked here, by design — it
    lives inside a person's individual set, as `PER_MACHINE_SETUP.md`
    itself says. The path resolution was correct and the documents were
    correct; **the registry was wrong**, and taught the currency check to
    cry wolf twice a run. Both entries dropped; each already names
    `.claude/hooks/commit-identity.sh`, which is the in-tree file that
    actually moves when `identity.json`'s shape changes.
  - **The same registry still named `.github/workflows/docs.yml`**, deleted
    in `0252979d`. That commit updated `documentation/GIT.md`'s prose and
    not the registry naming the file. Dropped.
  - **`documentation/SHARED_PRACTICE_SETS.md` was missing from the
    registry** (landed 2026-09-21, reader-facing), so nothing could tell
    whether it had gone stale. Added.

## Claims Checked and Found Honest

Recorded because a claim nobody has watched fire reads as coverage:
`precedent_gate.py`'s wiring claims hold by content (the pre-push hook and
both stop hooks really do call it; `merge`/`review` are honestly described
as cited-only); `leak_gate.py` refuses an in-repo blocklist by path, live,
and `--structural-only` genuinely drops the private half on all three
routes; `precedent_resolve.py`'s "certain vs not certain" diagnosis is
really implemented and its message was accurate for the state it was in;
`build_views.py --check` exits 0 and writes nothing; `routing_audit.py`,
`precedent_reply_check.py` and `doc_sync.py` each disclose their own limits
rather than overclaiming.

## What Pass 2 Did Not Cover

Eight of the practice's twenty numbered questions were not attempted
(reproduce every documented gotcha; enumerate every registered check in
every repo in force; read the harness-adapter ledger against all four
harness trees; the per-incident recurrence sweep). Eight more are covered
only by the mechanical run, not by a fresh read. **Question 11 — each
enforced check read against its own Rule — was sampled at three of about
fifty-five, and one of those three is finding 4 above.** That hit rate is
the argument for the full sweep being worth somebody's time.

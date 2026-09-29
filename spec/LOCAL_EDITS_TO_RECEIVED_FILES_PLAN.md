---
title:         Local edits to received files
kind:          proposal
status:        accepted
opened:        2026-09-29
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Update Vendors stops refusing over a committed local edit to a received file. It compares the edit with what the file was vendored from and what upstream has now, keeps it, merges it or takes upstream's version, and says which. A second command turns the edits that remain into a branch in BestPractice, scrubbed on both sides, with a paste-ready prompt for the session that will land it."
---

# Local edits to received files

**The problem.** A repo that vendors Precedent receives files it did not
write: the engine in `tools/` (listed in `tools/ENGINE_MANIFEST.json`), and,
in repos installed before 2026-09-14 and migrated, the universal catalogue
mirrored under `process/upstream/`. When a session in such a repo hits a
bug in one of those files, it often fixes the local copy.
[upstream-bug-stops-here](../practices/upstream-bug-stops-here.md) says to
stop and hand the fix upstream instead, but that handoff is carried between
sessions by hand. And when Update Vendors later meets the edit, it refuses:
"hand-edited here and shipped by upstream ... Move the edit upstream, or
refresh --force." Morgan, 2026-09-29: most of those edits are local attempts
to fix the same bug upstream fixes. So **the refusal keeps a repo on its own
patch, without upstream's fix,** until somebody decides by hand.

**The fix, in two parts, one tool.** Update Vendors resolves each committed
local edit itself (part two, below, built first because every consumer runs
it). A new command sends the edits that remain upstream as a ready branch
(part one). Both live in one new file,
[tools/precedent_local_edits.py](../tools/precedent_local_edits.py), which
runs from the BestPractice clone the way
[tools/precedent_update.py](../tools/precedent_update.py) does.

**Lineage.** Two prompts from the session "Precedent check engine fixes"
(2026-09-29) proposed the two parts. A review in the session "Precedent ONCE
LIVE 2 check engine fixes" found five changes; the proposing session accepted
all five, checked the two load-bearing claims against pre-staging, and added
four more. Morgan then said to build it (strength: decided), on a feature
branch, not yet into pre-staging.

## What counts as a local edit, and who owns it

**Two layers in version 1.**

- **Engine files in `tools/`.** A local edit is what the refresh already
  calls one: a file whose sha256 differs from the hash
  `tools/ENGINE_MANIFEST.json` recorded (`precedent_vendor_engine._local_drift`,
  reused, not copied). `routing_scope.json` is left out: the refresh
  generates it, so it has no upstream text to merge against. BASE is the
  file at the manifest's `source_commit`, read from the source clone.
- **`process/upstream/`.** A local edit is what `checkin.py update`'s guard
  already refuses on: a file whose content differs from the tree at the
  manifest's recorded `upstream.commit`. That comparison moves out of
  `update()` into one function both callers use. BASE is the file at
  `upstream.commit`.

**Who owns each file** comes from
[tools/precedent_practice_refs.py](../tools/precedent_practice_refs.py)'s
`received_owners()`, the one answer to that question. Both version 1 layers
belong to BestPractice.

**Left out of version 1, on purpose.**

- **Hooks and CI workflows keep today's refusal.** Merging a
  `.github/workflows` file automatically would change a workflow without the
  person's words ([ci-workflow-approved](../practices/ci-workflow-approved.md)).
  Hooks can join later.
- **Practices and checks listed in `MANIFEST.json`.** They are rebuilt from
  live sources on every sync, and nothing records per file what was written,
  so there is no BASE to merge against. An edit there is silently
  overwritten, which is worse than a refusal. Filed as
  [todo/todo-2026-09-29-received-practice-edits-are-overwritten.md](../todo/todo-2026-09-29-received-practice-edits-are-overwritten.md).
- **A shared set's mirrored tree (`process/<name>/`)**, the same way;
  `checkin.py push --source` keeps its old mirror into the clone until then.
- **A section 0 install's universal catalogue** (`precedent/universal/`),
  which Update Vendors replaces wholesale and which already treats a file
  equal to any version upstream ever carried as upstream's text.

## Part two: Update Vendors resolves the edit

**Where it runs.** In `precedent_update.py`, not in the engine. A consumer's
own old copy of `precedent_vendor_engine.py` runs the refresh, and its
`refresh()` refuses on a hand edit (`_local_drift`, near its top) before it
replaces itself with the new copy. Logic placed in the engine would never
run in the repos that have an edit. `precedent_update.py` runs from the
source clone, so it is always current.

**How, for each layer:**

1. **Find the edits.** Any that is not committed stops the layer: nothing
   is written, and it is reported as today
   ([repair-cannot-discard-work](../practices/repair-cannot-discard-work.md)).
2. **Swap BASE in.** Save each LOCAL to a journal inside the repo's git
   directory (never the working tree, never committed), then write BASE, so
   the old refresh or the mirror sees nothing edited and runs clean.
3. **Let the layer update as it always has.** The refresh writes NEW;
   `checkin.py update` mirrors NEW and `record` stamps it.
4. **Apply the rules** to each file, then clear the journal.

**Restore on every exit path.** If the refresh fails, the process is
stopped, or anything raises between the swap and the rules, LOCAL is written
back from the journal byte for byte (a `finally`, plus handlers for the termination
and hangup signals during that window). If the process dies outright, the next run finds
the journal and restores from it before doing anything else, and says so.
That git history holds the committed version is not enough on its own.

**The rules.** BASE is what the file was vendored from, LOCAL is the repo's
committed copy, NEW is upstream's version now.

- **Kept on purpose (rule 4).** The file has an entry in `precedent.json`'s
  `kept_template_divergences`, keyed by its path, with a reason, and with
  `template_sha256` set to NEW's sha256. LOCAL is written back. When upstream
  has since changed the file, the pin no longer matches: LOCAL is still
  kept, and the file is left for the person with the new hash to record.
  An entry with no reason is not honoured, and the report says so. This is
  the key the refresh already reads for template files, widened rather than
  duplicated.
- **Upstream did not change it (rule 1).** NEW equals BASE: LOCAL is written
  back and reported as still a local edit, with the command that sends it
  upstream.
- **A clean three-way merge (rule 2).** `git merge-file` of LOCAL, BASE and
  NEW. When the result equals NEW, upstream already carries the change: NEW
  stays, and the report says so. Otherwise the merged file is written, then
  checked: each merged file must compile (Python), parse (shell, JSON), and
  the repo's own `tools/checks/tests/run_all.sh` must pass where it has one.
  The repo's basic tier alone runs no code, so it cannot catch a merge that
  is clean as text and broken as a program. **On any failure, every merged
  file goes back to NEW at once,** reported under rule 3 with what failed;
  a per-file retry would multiply the run.
- **A conflict (rule 3).** NEW stays. The report names the file, says that
  upstream changed the same lines and most likely fixed the same bug, names
  the commit that holds the local version, and gives the command to bring it
  back or send it upstream if the bug is still there.

**The closing report** lists every file handled, grouped by rule, in plain
words. Rules 1 to 3 are notes: the update still finishes. A stale rule 4 pin
and an uncommitted edit are left for the person, as before. `refresh --force`
is never passed and keeps its meaning.

## Part one: send the edit upstream

    python3 ../BestPractice/tools/precedent_local_edits.py send --repo . --why "what went wrong"

1. **Run from the source clone,** because the consumer's vendored copy may
   be old.
2. **Find the committed edits** by the same detection as part two.
   Uncommitted edits are refused.
3. **Branch in the owner's clone without moving its checkout.** Fetch the
   owner's landing branch (`tools/precedent_branches.py --landing`, run in
   that clone), add a temporary worktree on a new branch, and apply each
   edit as a three-way merge of LOCAL and BASE onto the landing branch's
   tip. Upstream work since vendoring is merged, never reverted. A file that
   conflicts is not sent, and is named. **The branch name carries a date and
   the first file's name, never the consumer's name,** because the consumer
   may be private and the owner public.
4. **Scrub on both sides before anything leaves.** First the consumer's
   side: its own `process/upstream/tools/practice_audit.py` where it has one
   (run from the consumer's copy, so it scrubs the consumer; see the note
   below), and every added line, the `--why` text and the local commit
   messages scanned against the leak gate's word list and the consumer's
   scrub list. Then the owner's side, in the worktree: its
   `tools/leak_gate.py --staged`, then its basic tier. A branch pushed to a
   public repo is published at once, and a remote branch is never deleted,
   so a hit found after the push cannot be undone. **Any hit: nothing is
   pushed** and the local branch is removed.
5. **Commit and push the branch.** The owner clone's configured identity; a
   `Session:` trailer from the session, or `Session: none available` when
   there is none. Never a pull request, never a merge.
6. **Print one Prompt Please block per owner**
   ([prompt-please](../practices/prompt-please.md)): the branch, the files,
   what the consumer saw go wrong, and that the receiving session must add a
   test that fails without the fix before booking it.
7. **Leave the consumer's edit in place, and say so.** Once the fix lands
   upstream and the consumer runs Update Vendors, the files match again.

**`checkin.py push` delegates to this command.** It copied the whole
vendored tree into the clone's working tree and stopped: no branch, no
commit, no three-way merge. Now it calls `send` for the `process/upstream/`
layer, so one tool owns each direction: `checkin.py` keeps `status`,
`update` and `record`, and the new file owns sending. **Found while planning:**
`checkin.py push --repo` ran the source clone's own `practice_audit.py`,
which locates its root from where it sits, found no `process/` there and
passed as "NOT APPLICABLE". So a check-in run from the source clone was never
scrubbed. Running the consumer's own copy closes that.

## Tests (tools/verify_harness.py)

Consumer-shaped fixtures, seeded from this tree, with a fixture upstream
made by committing a change onto the ref under test (no ref moves, nothing
leaves the machine). Each case is shown to fail without the code it tests.

- Part two, engine layer: rule 1 kept and reported; rule 2 merged, with the
  checks run; rule 2 with a failing check falls back to NEW; rule 3 takes
  NEW and names the local commit; upstream already carrying the change; rule
  4 never replaced, and a stale pin left for the person; an uncommitted
  edit, with nothing written; the refresh failing after the swap, with LOCAL
  back byte for byte; a journal left by a run that died, restored on the
  next.
- Part two, `process/upstream/`: one merge case end to end, with `record`
  passing.
- Part one: the branch appears upstream carrying the diff; an upstream
  change since vendoring is merged, not reverted; a leak-gate hit is refused
  before anything is pushed; a repo with no edits does nothing and says so;
  the branch name does not carry the consumer's name.

## Follow-on items filed with this work

- [todo/todo-2026-09-29-received-practice-edits-are-overwritten.md](../todo/todo-2026-09-29-received-practice-edits-are-overwritten.md)
- [todo/todo-2026-09-29-pre-staging-tier-skips-doc-sync.md](../todo/todo-2026-09-29-pre-staging-tier-skips-doc-sync.md)
- [todo/todo-2026-09-29-push-gate-reads-a-quoted-pipe-as-a-command.md](../todo/todo-2026-09-29-push-gate-reads-a-quoted-pipe-as-a-command.md)

## Shipping

The four questions of
[vendor-rollout-disclosed](../practices/vendor-rollout-disclosed.md):

1. **Does it need to reach consumers?** Yes, and all but one line of the
   changed code is outside the engine. The exception is the wording of the
   engine refresh's own refusal in `precedent_vendor_engine.py`, which now
   names Update Vendors and `send` instead of "move the edit upstream"; a
   consumer gets it on its next refresh, and until then sees the old
   wording, which still refuses correctly. `precedent_local_edits.py`, `precedent_update.py` and
   `checkin.py` are run from the BestPractice clone (`python3
   ../BestPractice/tools/... --repo .`). The two practice edits
   ([upstream-bug-stops-here](../practices/upstream-bug-stops-here.md),
   [vendor-update-runbook](../practices/vendor-update-runbook.md)) reach
   consumers as practice text, the usual way.
2. **Will the update mechanism carry it?** Yes, with nothing to wait for:
   a consumer's next Update Vendors runs the new code, whatever engine copy
   it carries. The one gap: a repo that runs `checkin.py` from its own
   vendored `process/upstream/tools/` copy gets the new `push` only when its
   catalogue mirror brings `checkin.py` and `precedent_local_edits.py` in,
   and the mirror brings both at once.
3. **Does it work where the update has not arrived?** Yes. None of the new
   logic is in the engine, and the consumer's own refresh sees exactly the
   text it recorded, because the swap writes BASE before it runs. Everything
   new is optional: no `kept_template_divergences` entry means nothing is
   kept on purpose, no journal means nothing to replay, and a
   `process/manifest.json` with no `upstream.commit` gets today's refusal.
   The fixtures seed from this checkout, so the engine a fixture runs is
   the one it was seeded with; no fixture seeds from an older engine
   commit, and that is safe to leave because no step reads a new field
   from the engine.
4. **A new check in a consumer holding received files?** None is added.
   `record`'s carry check changes only to skip the files named with
   `--resolving`, which Update Vendors passes for exactly the files it is
   resolving.

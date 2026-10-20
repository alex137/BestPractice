---
slug:              todo-2026-10-20-update-all-vendors-root-issues
kind:              analysis
domain:            mechanism
severity:          medium
status:            open
disposition:       null
remind_on:         null
blocked_on:        the names of the four repositories whose add_repo was refused, in the session that ran Update All Vendors
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-20
closed:            null
---
## What

What one Update All Vendors run on 2026-10-20 (engine at `main` @
75970f4a0f18, 18 repositories: 4 pushed, 6 stopped at questions, 7 left
calls for their own repository, 1 does not use Precedent) showed about the
engine itself, most harmful first. Each was checked against the source
before it was written here.

1. **Could break: a public repository is asked to copy in a set nobody
   scanned.** In a public consumer, the copy-in question for a person's
   own set says "The leak check could not run: there is no clone of the
   set on this machine", and still offers the copy. A yes publishes rules
   no leak check read. The update should take read access to the set and
   run the check (reach-or-ask), or refuse to offer the copy in a public
   repository until it can.
2. **Could break: decommissioning others-did left the file it wrote.**
   d50e09ee1 moved others-did into the ladder set and deleted
   the old engine tool `precedent_others_did`, but a consumer still carries
   `tools/others_did_watermark.json`, whose header names the deleted tool;
   the ladder's [others_did.py](https://github.com/themorgan/precedent-shared-ladder/blob/staging/tools/ladder/others_did.py) no longer reads or writes it.
   The update now stops that repository on a rename-updates-links finding
   for a file only the engine ever wrote. The fix belongs in the update:
   retire the file it owned (decommission-deletes-files), not a hand edit
   in each repository.
3. **Warning: a `local_ci_workflows` declaration is reported on every
   update and never resolved.** Three private consumers declare their own
   workflows there; [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) prints "the declaration
   was not honoured; remove it from precedent.json" each run, and the push
   check then says those workflows' tools "could not run". The update
   could ask the person once whether to keep each workflow and record the
   approval in `github_ci_approved`, which ends the warning.
4. **Warning: every consumer is asked to copy in a person's own set.**
   Repositories unrelated to it get the question each run, with the
   suggestion "no". A suggested no that repeats every run is noise:
   record the answer the first time, or stop offering a set the person
   offers per repository.
5. **Warning, cause not measured: auto mode refused 4 of 22 `add_repo`
   calls** sent in one batch, with only "[Permission Grant]" as the
   reason, so those repositories got no update. Retry them one at a time
   before changing anything; if that passes, say so in update-all-vendors.

(needs: decision -- Morgan, who asked for these as a Root issues prompt and runs the updates one by one; out of scope here, where the ask was the report.)

## Outcome, 2026-10-20

A root-fix session reviewed each finding against the source; all five
held as written.

1. **Fixed.** In a public repository a yes is refused while the leak
   check has not read the set (no clone, or the check failed); the
   question says where to clone it and offers only a no. A yes recorded
   before the set could be read waits again in a public repository while
   the check finds a line. Test: `check_public_copy_in_needs_the_leak_check`.
2. **Fixed.** The update deletes files a decommissioned engine tool wrote
   at run time (the others-did and beta-branch marks), recognised by their
   header, through the same refusals as a legacy workflow, and records
   each. Test: `check_engine_written_leftovers_leave_by_content`.
3. **Fixed.** The every-run note is gone. A declaration beside an approval
   is dropped; one without becomes a keep-or-delete question, and
   `precedent_update.py --keep-workflow PATH --answered-by '...'` records
   the keep. Test: `check_local_workflow_declaration_is_asked_once`. The
   push check's "could not run" line had a cause of its own, found here in
   BestPractice too: it looked for a script named `-c` inside the budget
   wrapper of every approved workflow step, so none of them ever ran before
   staging. Fixed (`script_arg`), with a case in
   `check_push_to_staging_runs_own_checks_inside_a_budget`.
4. **Partly.** Asking once per repository is Morgan's decided design
   (2026-10-19), and a recorded answer already ends it, so that stays; the
   asking session has since recorded his answers. What was wrong is
   fixed: for a set the person only offers, the "No" no longer claims it
   is loaded here when this repository does not declare it.
5. **Not measured.** Still open: retry the four refused `add_repo` calls
   one at a time, and only if that passes, say in update-all-vendors to
   attach one repository at a time.


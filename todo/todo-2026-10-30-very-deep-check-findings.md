---
slug:              todo-2026-10-30-very-deep-check-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       null
remind_on:         null
blocked_on:        "every line under Left names why this run left it"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-30
closed:            null
---
## What

What the 2026-10-30 very deep check found and did not fix in the same run.
Scope: BestPractice and the three sets it declares, on the phrase. What the
run fixed is in its commits; the account is
[VERY_DEEP_CHECK_LATEST_RUN.md](../spec/VERY_DEEP_CHECK_LATEST_RUN.md).

### Calls for Morgan

Each with the session's pick. **Answered 2026-10-31: every pick taken**
(Morgan, strength: assented: "On your questions above: do your suggestions. On
your question in the doc you did ...: do your recommendations for all", with
"You can attach the Pesty consumer"). Call 11 he also asked about in his own
words: "Those sound huge like 9400 words is a lot, maybe we should do a cleanup
of the long rules?" -- the split is that cleanup, moving and never deleting.
What each answer became is noted at the end of this item.

1. **Ship universal's `reply_check.json` to every installed repository?**
   The reply checker's own notes say it binds every adopter and the classic
   layout shipped it, but neither the installer nor Update Vendors carries it
   today, so a new install has no reply requirements at all. Pick: yes, after
   moving the requirements that read as one person's conventions into the
   individual set, so adopters get only the universal ones.
2. **Re-approve `deep-check.yml`, `precedent-branch-cleanup.yml` and the
   cleanup template at their current content?** Both changed after approval
   (2026-10-29 and 2026-10-17); neither adds CI work. Pick: yes.
3. **Exempt all of `spec/` from no-stale-counts?** Every count there read as
   a dated measurement; the cost is that a future stale total in a `spec/`
   reference file goes unflagged. Pick: yes.
4. **Narrow the session-start deepen to `--deepen=1000`?** Unshallowing now
   costs about 20 seconds and about 25 MB, against about 4 seconds and 7 MB
   when it was approved. Pick: yes.
5. **Close `todo-2026-09-08-retired-practice-filenames` as evaluated?** The
   cheaper alternative it proposed is in place. Pick: yes.
6. **Park the four speculative 2026-09-06 items** (companion mobile app,
   individual-practice scoping, out-of-chat notifications, reducing the GitHub
   dependency)? Pick: yes.
7. **Reword the thirteen practices moved from the individual set into the
   ladder set out of the first person?** The writing set did the same for
   `name-the-branch` on 2026-10-17. Pick: yes.
8. **Should the ladder set's `file-header` take the name and time zone from
   the person's own settings file**, instead of hardcoding one person's in a
   public shared set? Pick: yes.
9. **Wire the writing set's dated-file-name hook in BestPractice, or exempt
   BestPractice with a reason?** BestPractice declares the writing set but
   wires its hook only through an untracked file. Pick: wire it.
10. **Should the set generator do what a set's first Update Vendors does**
    (budgets, the staging branch, the very deep check's registry entries), so
    a new set does not start out of date? Pick: yes.
11. **Split the four longest Rule sections** (`vendor-update-runbook` about
    9,400 words, `the-boildown` about 7,700, `very-deep-check` about 3,800,
    `prompt-please` about 2,700; the median is about 150)? Pick: yes, by hand,
    the runbook first.
12. **Attach about nine repositories read-only, once, so the visibility audit
    can say which are private?** Pick: yes.
13. **Keep the retired `precedent-check-receipts` branch off the deletion
    list until no older engine writes to it** (one did on 2026-10-28), and
    correct `tools/precedent_data_branches.py`'s docstring to match? Pick:
    yes.
14. **Attach a real consumer for Pass 1** next run; this run had none.

### Left, with the reason

- **Test review (Pass 2, question 27).** 889 tests, none ever judged; the
  times date from 2026-10-09 and re-timing needs a whole-suite run of its
  own (needs: a whole-suite run in a session of its own -- this run had no room for one beside seven helpers).
- **Pass 2 questions not attempted:** 8b, 9, 10, 12, 15, 15a, 16, 17 (needs: the next run -- out of this run's time-box).
- **Pass 3, BestPractice:** a whole read of the 188 practices against each
  other (searches only); `templates/harness/LEDGER.md`, `tools/bootstrap.sh`;
  the documentation-currency prompts for nine pages under
  [documentation/](../documentation/) (the git, GitHub settings, method, phone,
  language, ten-things, why, cloud setup and per-machine setup pages)
  (needs: the next run -- out of this run's time-box).
- **Pass 3, sets:** the individual set's practice Rules, every set's Detail
  and Story sections, each set's `spec/WORKING_IN_THIS_REPO.md`, the three
  occasion-index reviews; strict-lint unlinked references (individual 258,
  writing 44, ladder 12) (needs: the next run -- out of this run's time-box).
- **Pass 4:** the whole-catalogue read; the 34 BestPractice practices changed
  since 2026-10-17; the 14 bullets of
  [todo-2026-10-11-very-deep-check-findings](todo-2026-10-11-very-deep-check-findings.md);
  four unblocked items that could be done now
  (`source-clause-check-reads-only-html-comments`, `no-origin-is-not-stale`,
  `the-load-budget-registry-asserts-loads-nothing-verifies`,
  `session-practices-slug-can-render-twice`) (needs: a session of its own -- out of this run's time-box).
- **Engine defects not fixed, out of scope for this run (each needs a session of its own):** four checks that skip with "no
  changed markdown file is in scope" never read untouched markdown in a set,
  even under `--full-sweep`; the set generator writes `CLAUDE.md` only when it
  is missing and no refresh updates it; CONVERGENT DRIFT and MOVED CLAIMS
  report generated files and history registries as findings. Each is a code
  change with planted cases.
- **Planted cases owed** for two incidents: a citation of a set's practice
  that passes locally and fails on GitHub, and the endgame merge rehearsal.
  `todo-2026-10-14-delete-pre-staging-code` was closed before its condition
  was met and should be reopened or its closing note corrected (needs: a session of its own -- out of this run's time-box).
- **Documents:** [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md) step 1 never says to
  run `checkin.py record`; a private repo's session-file line still speaks of
  "a public repo's tracked loader block"; the writing set's
  `internal-link-pattern-assumes-section-1-layout` item names a blocker its
  rules do not accept; the ladder's `go-update` puts "open a pull request and
  merge it" before the default direct push; `rule-links` says "first mention"
  and "every mention" in two places (needs: a session of its own -- out of this run's time-box; the set ones need that set's approver).
- **A planted case to re-add by hand:** a practice with no `## Install`, from
  the unlanded `2026-10-11-fix-shape-test-fixture-sections-11fwt-bum5v`
  branch, whose fix otherwise landed another way (needs: a session of its own -- out of this run's time-box).

## Notes

2026-10-31: Morgan's answers acted on the same day. Call 3 needed nothing more
(the exemption was already in place). Calls 2, 5 and 6 are on the branch
`2026-10-31-themorgan-vdc-approved-calls-hv5gd-i86bb`. The rest went to helpers
of the same session; each one's outcome is added here when it lands.

2026-10-31, call 12 (the visibility probe): answered without attaching
anything. The account's own repository list carries each repository's
visibility. Of the 13 real-owner names the audit could not check,
`alex137/GitAround` is private and is named in
[WHERE_THINGS_ARE.md](../WHERE_THINGS_ARE.md) on purpose, as a row that says
so; the other twelve are not repositories on either account any more (retired
set names, fixtures and placeholders), so naming them discloses nothing. No
change to the tree.

2026-10-31, after Booked: the landing's harness run failed two cases
(`check_a_brought_sets_spoken_trigger_reaches_the_session_at_start`,
`check_session_file_says_each_command_once`) only because the session had
left the three set clones on their landing branches; with each clone back on
`main` both pass on the same staging. The two tests read the real set clones
rather than planting their own (practice: fixture-owns-its-state), so a clone
on any other branch turns them red (needs: a session of its own -- out of
scope for this run).

2026-10-31, what each answer became:

- **1 (reply rules for adopters):** done. All 19 universal requirements were
  read against their practices and every one binds any adopter, so none
  moved to the individual set; install and Update Vendors now carry
  `reply_check.json`, and the open-item check reads it from every source.
- **2, 5, 6, 12:** done by the session (above).
- **4 (session-start deepen):** not made. Measured from a fresh clone,
  `--deepen=1000` cost the same as `--unshallow` (about 27 s and 31 MB each),
  because 1,000 steps reach every commit here; deepening only the current
  branch by about 100 came in near 10 s and 15 MB. Asked again (needs: a
  decision -- Morgan's), with the session's pick in the run's reply.
- **7 and 8 (the ladder set):** done, ladder #155.
- **9 (the writing set's hook here):** no change. Wiring it in the tracked
  setup would point at a script that arrives untracked, and a missing
  script blocks every file hand-over; the set's check already accepts the
  untracked wiring. Asked to close as already right.
- **10 (the set generator):** done: budgets and the person's total, by the
  same functions Update Vendors uses; the staging branch is printed as a
  command, since the generator never writes to a remote.
- **11 (the four longest Rules):** done, every moved line kept: the runbook
  9,301 words to 1,773, the-boildown 7,690 to 2,128, very-deep-check 3,724
  to 1,305, prompt-please 2,714 to 903.
- **13 (the old receipts branch):** done, kept off every deletion list.
- **14 (a real consumer):** done on a private consumer, on a branch there and
  not merged. It found two engine traps, fixed here: the push check passing
  silently when a single-branch clone lacks the base, and the very deep
  check's own run record tripping two checks in a consumer. Its update ends
  "left for you" until two private copied-in sets are attached.

2026-10-31, live on `main` in all four repositories (BestPractice #1450, ladder
#156, writing #214, individual #374); GitHub's test passed on BestPractice's
`main`, and each set's full suite passed on its own. Still open, each asked of
Morgan with the session's pick (needs: a decision -- Morgan's):

- **The session-start deepen (call 4):** deepen only the current branch by
  about 100, after measuring that the three history-reading tools still see
  enough, and change `freshness-guard.sh` with it -- or keep the full fetch
  and close this. Pick: measure first, in a session of its own.
- **The writing set's hook here (call 9):** close as already right. Pick: yes.
- **The consumer's update:** its branch stops at "left for you" until two
  private copied-in sets are attached read-only. Pick: attach them next run,
  then land it by Update Vendors.
- **"Never leave work on a branch":** its reply check is still in the
  individual set while its practice moved to the ladder set, so nobody else
  bringing the ladder gets it. Pick: move it.
- **The ladder's words in universal's finished-plan rule** (`plan_words`):
  inert without the ladder's `stage_line`. Pick: move them to the ladder set.
- **An assumption made on Morgan's behalf:** the ladder's file header is now
  re-stamped with whoever edits the file, where before only one person's
  headers were read. A one-line change reverts it.

2026-10-31, Morgan on the open questions above (strength: assented): "On all of
these, use your judgment, and act booked produce". Acted on each the same day:
the writing set's hook here is closed as already right (no change: the
untracked wiring is where a set's hook belongs); the archive guard moved to
the ladder set with `ladder-required`; universal's finished-plan rule dropped
the ladder's words; the two private sources the consumer copies in were
attached read-only so its update could finish; the session-start deepen was
measured against the history-reading tools before any change; the file-header
assumption stands. He also asked for the very deep check to review the
longest quarter of every repo's Rules every run; it now does, and the first
review ran the same day.

2026-10-31, the incident verdicts (Pass 2, question 20) redone, because the
run's first set was lost with a helper's scratch file: 62 incidents, 43
covered, 14 judgment-only, 5 with a planted case owed. The table is under
`## Incidents` in
[VERY_DEEP_CHECK_LATEST_RUN.md](../spec/VERY_DEEP_CHECK_LATEST_RUN.md). The
endgame merge rehearsal, listed above as owed, is planted now
(`check_endgame_merge_finds_the_silent_drop` runs it with no global git
identity), so that half of the "Planted cases owed" line is done. The five
still owed, none written today because another helper held
[tools/verify_harness.py](../tools/verify_harness.py) (needs: a session that
owns the harness):

- **`todo-2026-09-06-nine-practices-carry-an-empty-why`:** nothing refuses an
  empty `## Why`. Spec: `practice-file-shape` treats an empty `## Why` as it
  treats an empty `## Rule`, planted in `check_precedent_check_fires`.
- **`todo-2026-09-06-upstream-only-registries-ride-along-in-vendored-engine-files`:**
  only the doc_sync half is planted. Spec: in a fixture with
  `tools/ENGINE_MANIFEST.json`, a vendored [model_audit.py](../tools/model_audit.py) with no
  `tools/model_audit_host.json` audits nothing, and with one audits that list
  and never names [tools/catalogue_stats.py](../tools/catalogue_stats.py).
- **`todo-2026-09-14-no-history-checks-unpushed`:** the code says a test
  asserts the no-history wording, and none exists. Spec: in a fresh `git init`
  with a declared identity, [check_commit_author.py](../tools/check_commit_author.py) and
  [check_commit_dates.py](../tools/check_commit_dates.py)
  each exit 2 saying the repository has no commits yet, never a traceback or a
  violation.
- **`todo-2026-09-14-set-cannot-show-a-universal-practice`:** the show case
  plants a consumer only. Spec: in a fixture set whose own `practices/` lacks
  a universal slug, [precedent_show.py](../tools/precedent_show.py) with that slug prints its Rule
  labelled universal.
- **`gotcha-2026-10-27-a-citation-of-a-set-practice-passes-locally-and-fails-on-github`:**
  two directions nothing plants. Spec: (a) `practice: <a set's slug>` in
  `tools/`, with that set cloned beside the fixture, still fails
  `code-cites-practice`; (b) a relative link to a file under `tools/ladder/`
  that git does not track fails the light check locally, as it does on
  GitHub's runner.

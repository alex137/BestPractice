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

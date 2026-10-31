---
slug:              todo-2026-09-28-very-deep-check-pass-4-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan: whether a very deep check or Update Vendors takes a lease"
noted:             2026-09-28
closed:            null
---
## What

What the 2026-09-28 very deep check's pass 4 found and did not act on.
Response Please landed, eight backlog items closed, the BLOCKED-ON-GONE
scanner and net-empty branches fixed, the YAML-anchor gotcha retired, and
the full catalogue judgment completed, all the same day.

- **Branches, for Morgan's click** (a session never deletes a remote
  branch): 156 fully landed branches across the five repos, and the
  unlanded ones each given a summary and a recommendation, were handed to
  him in the session on 2026-09-28.
- **`claude/graduate-synonym`** carries two synonyms Morgan asked for on
  2026-09-26 ("Graduate" for Promote, "Spec it out" for Write it up) that
  never landed. Land it; a session's attempt to fold it in was refused by
  the permission layer.
- **From the catalogue judgment, left for a decision:**
  - `deep-check.yml` runs four jobs per trigger where one would do
    (actions-minutes-are-scarce), and two of its comments are stale. A
    workflow edit needs the person's own words (ci-workflow-approved).
  - About 2,300 links in BestPractice use the filename as link text
    (doc-link-text). Fixed on touch; a sweep needs a go-ahead
    (wide-search-needs-asking).
  - branch-links has no carve-out for a generic statement or for a file
    that travels out of a private set, unlike name-the-branch. A rule
    change in the writing set.
  - blank-blocklist targets a blocklist only the retired section 1
    install created, and new-rule-placement assumes a numbered rules
    document no repo here uses. Both are candidates to retire.
  - very-deep-check's Rule is about 3,400 words, mostly story
    (proportional-emphasis, trim-prose): move the incidents to Story and
    the mechanism to Detail.
  - Whether a very deep check or an Update Vendors should take a lease
    (lease-in-flight-work) is a judgment call.

## Notes

2026-10-17, very deep check pass 4 (still live, narrowed): done since: claude/graduate-synonym's two synonyms are in force ("Graduate" in the ladder's promote, "Spec it out" in write-it-up) and the branch is gone; deep-check.yml now has 2 jobs; doc-link-text was folded into rule-links; blank-blocklist and new-rule-placement no longer exist in any source. Left: very-deep-check's Rule is still about 3,700 words, and the lease question is unanswered.
2026-10-31, very deep check of 2026-10-30, pass 4 (still live): very-deep-check's
Rule section measured 3,724 words today, so the trim it asks for has not
happened; the lease question is still unanswered.
2026-10-31, call 11 of the 2026-10-30 very deep check (Morgan, strength:
assented): very-deep-check's Rule cut from 3,724 to 1,305 words (`wc -w`
over the section), every paragraph moved whole into Detail or Story, on
branch `2026-10-31-themorgan-split-very-deep-check-rule-hv5gd-25fwt`
(BestPractice). That half closes when it lands; the lease question is
still unanswered.

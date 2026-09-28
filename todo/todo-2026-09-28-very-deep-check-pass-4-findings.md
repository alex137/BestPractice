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
waiting_on:        null
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

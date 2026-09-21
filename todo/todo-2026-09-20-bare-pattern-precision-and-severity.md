---
slug:              todo-2026-09-20-bare-pattern-precision-and-severity
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-20
closed:            null
---
## What

- <a id="bare-pattern-precision-and-severity"></a>**`require_no_bare_pattern`
  (tools/precedent_reply_check.py) landed 2026-09-20 declared `advisory` for
  rule-links and branch-links in this repo's own reply_check.json, and two
  follow-ups are open.**

  **Precision.** The predicate strips every markdown link out of the whole
  reply once, up front, then tests each declared pattern against what is
  left. A thing correctly linked on its FIRST mention and named bare again
  later in the same reply still matches, even though rule-links only
  requires the first mention to carry the link -- a false positive, not a
  bug. Tightening this needs the predicate to know, per matched string,
  whether it ever appeared inside a link anywhere in the reply (not just
  whether the current occurrence is inside one), which is why the entry was
  declared advisory rather than blocking on landing.

  **Severity.** Once the precision gap above is closed, whether to promote
  the rule-links and branch-links entries from `advisory` to blocking (the
  way the-boildown's contradiction check is) is a call for whoever owns
  this repo's reply gate, not one made unilaterally by the session that
  added the predicate.

  **Related, not the same gap:** rule-links and branch-links themselves
  live in `precedent-shared-writing` (level: shared), not in this repo's
  own universal `practices/`, so the two new citations in
  tools/precedent_reply_check.py had to be written unanchored (no
  `practice:` prefix) rather than in the checked `practice: SLUG` form --
  the same accommodation
  [todo-2026-09-07-universal-code-cites-team-slug](todo-2026-09-07-universal-code-cites-team-slug.md)
  already describes for `fail-gracefully`, which was resolved by promoting
  that practice to universal. The same promotion may be the right fix here
  too, but is a separate call from the two above and not requested by this
  item.

## How It Closes

Not yet designed. Closes once a session either (a) reworks the predicate to
track per-string link coverage across the whole reply rather than a single
up-front strip, and the rule-links/branch-links entries are upgraded from
`advisory` to blocking, or (b) an owner of this repo's reply gate decides
`advisory` is where these should stay.

## Notes

2026-09-20: filed alongside the `require_no_bare_pattern` predicate itself,
per todo-gate -- the imprecision and the severity call were both named
in-line in reply_check.json's own `why` fields at landing, and are recorded
here as the open follow-up rather than left only in prose comments.

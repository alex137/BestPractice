---
date:        2026-09-03
question:    "Session: vs. Claude-Session: — which key does the
             session-trailer check actually want on a commit?"
decision:    Teach the check to accept both. Claude-Session as well as
             Session.
alternatives: ["Require only Session:, and fix any tooling or agent
               producing Claude-Session: instead", "Require only
               Claude-Session:, since that is what the current harness
               actually emits"]
decided_by:  Morgan
---

## Why this needed a decision

`check_session_trailer.py` already accepted `Claude-Session:` (commit
`ba49ea2`), but the practice's own Rule text still named only `Session:` —
so the check and the documented rule disagreed about what the rule was,
undercutting the standing instruction to check the Rule text itself rather
than a paraphrase of it. That mismatch needed a call on which key is
canonical, not just a code fix.

## Outcome

Both keys are accepted, and the practice's Rule text was updated to name
both explicitly rather than leaving `check_session_trailer.py`'s broader
behavior undocumented. Landed via
[precedent-team-maintainers#10](https://github.com/themorgan/precedent-team-maintainers/pull/10),
merged.

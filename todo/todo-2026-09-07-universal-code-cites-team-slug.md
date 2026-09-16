---
slug:              todo-2026-09-07-universal-code-cites-team-slug
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "Morgan's call on the level, and nothing else. An earlier version of this item also named \"a session rooted at `themorgan/precedent-team-repo-maintenance`\" — that was wrong, and written without checking: all three private sets are attached to *this* session and were when it was written. The [AGENTS.m"
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-07
closed:            null
---
## What

- <a id="universal-code-cites-team-slug"></a>**Five universal engine files depend on a rule the universal catalogue
  does not have, and cite it in the one form the check cannot see.** Found
  2026-09-07 by the [very deep check](../spec/VERY_DEEP_CHECK.md)'s pass 3.
  [tools/routing_audit.py](../tools/routing_audit.py),
  [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
  (twice), [tools/precedent_show.py](../tools/precedent_show.py) and
  [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) each
  name `fail-gracefully` to explain why they degrade rather than fail.
  `python3 tools/precedent_show.py fail-gracefully` exits 1: the practice
  lives in `precedent-team-repo-maintenance`, a private set, so no reader of this
  public repo — and no consumer that vendors this engine — can look it up.
  Nothing in [practices/](../practices/) covers graceful degradation.

  Both halves were confirmed by running them, not reasoned about. All five
  use an *unanchored* mention (`(fail-gracefully)`, `# fail-gracefully`),
  which [practices/code-cites-practice.md](../practices/code-cites-practice.md)'s
  own Rule already forbids as "a bare mention of the practice's subject with
  no way to look it up" — and which its check cannot detect, since no scanner
  tells a bare slug from ordinary hyphenated prose. Rewriting one to the
  sanctioned `practice: fail-gracefully` was tried:
  [precedent_check.py](../tools/precedent_check.py) went
  from `1 passed` to `1 violated`. So the sanctioned form is *unavailable*
  here, and the rule pushes its own users into the unchecked form. The
  blindness is now declared in that check's `blind_to`; the citations are
  deliberately left alone, because rewording them is the wrong direction if
  the recommendation below is taken.

  **Recommendation: promote `fail-gracefully` to universal**
  ([spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md)), then anchor all
  five citations. A rule that five pieces of *universal engine code* depend
  on is not a team preference — the team set is simply where it was first
  written down, and
  [tools/precedent_show.py](../tools/precedent_show.py)'s own comment concedes
  as much, calling itself a generalization of the personal-pack rule.

  **The practice's own `## Story` already anticipated this and named the
  condition.** It records that it was kept at team level "for a stated
  reason — general enough to want in every project, but simple enough that a
  persuasive, attributed upstream submission was not judged worth the effort
  yet. That remains the outlet if it changes." That was a cost/benefit call
  made when nothing upstream depended on the rule. Five universal engine
  files and every consumer that vendors them now do, and each inherits a
  citation that resolves nowhere. The condition the practice set for itself
  has been met, so this is no longer a novel judgment — it is the outlet the
  rule already named. It would also land complete: Detail, Why and Story are
  all substantial (an earlier version of this item claimed they were empty,
  copying a figure from
  `migrated-practices-lost-their-stories`
  that was itself stale — corrected there).

  **Blocked on:** Morgan's call on the level, and nothing else. An earlier
  version of this item also named "a session rooted at
  `themorgan/precedent-team-repo-maintenance`" — that was wrong, and written
  without checking: all three private sets are attached to *this* session and
  were when it was written. The
  [AGENTS.md](../AGENTS.md) gotcha it was reasoning from says `add_repo` cannot
  attach them *mid-session from a BestPractice-rooted session*, which is a
  different statement from "they are unreachable". Check what is on disk
  before recording a blocker from a remembered rule.

## How It Closes

Not open until: Morgan's call on the level, and nothing else. An earlier version of this item also named "a session rooted at `themorgan/precedent-team-repo-maintenance`" — that was wrong, and written without checking: all three private sets are attached to *this* session and were when it was written. The [AGENTS.m

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

---
slug:              todo-2026-09-14-close-detect-declaration-unpushed
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       parked
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="close-detect-declaration-unpushed"></a>**The individual set's
  `close_detect.json` was written and could not be pushed from a session
  rooted here. CLOSED 2026-09-14 — it is pushed, and close detection is
  live.** Close detection
  ([tools/precedent_close_detect.py](../tools/precedent_close_detect.py),
  built 2026-09-14) is inert until a source declares the phrases it fires
  on, and the source that carries Morgan's closing convention is his
  individual set — a different GitHub owner from this repository. The git
  proxy refused to inject a credential across owners (*"not in this
  session's authorized repository set"*), and `add_repo` was denied here
  too, so the declaration existed as a local commit on a branch named
  `close-detect-declaration` in a clone that died with the container.

  **What unblocked it, and the correction worth keeping.** The wall is not a
  property of this repository — it is a property of a session's **authorized
  repository set**. A session started with BOTH owners in scope reaches the
  individual set and pushes to it normally, and one did on 2026-09-14,
  landing this as that set's pull request #131. It measured the access
  rather than assuming it, which is the only reason it looked at all: the
  clone was present, its remote was the individual set, and a dry-run push
  of a new branch was accepted. **So the thing to ask for is a session
  scoped to both owners**, not a session "rooted in" the other one — the
  phrasing this item and its sibling both used, which reads as though the
  starting repository were what decides.

  **What landed is five keys and no logic**, at that source's root and never
  vendored: `practice`, `archive_ready_one_of`, `closing_heading_matching`,
  `candidate_marker`, `why`. The phrase it declares is deliberately the same
  one that set's `reply_check.json` already requires, so one sentence marks
  both *this session is finished* and *a practice may be offered here*,
  rather than adding a second convention that would go unused.

  **The closing condition is met, measured from the clone a fresh session
  actually reads** (not the editable one — see the gotcha about the
  individual source resolving to a clone you are probably not editing):
  after fetching that set's `main`, `python3
  tools/precedent_close_detect.py --explain` prints
  `individual/precedent-individual: ready-to-archive ['You can archive this
  session'], one candidate per session marked 'Practice candidate', in the
  /next step/i section`, where it previously said no source declares a
  `close_detect.json`.

  **Then it moved up a level, hours later and in the same day's work.** The
  blocker was never the declaration's content; it was that the phrase it
  fires on (*"You can archive this session"*) belonged to a private set, so
  the declaration had to live beside it. Moving
  [next-steps-after-commit](../practices/next-steps-after-commit.md) to
  universal took that phrase with it, and a phrase that is universal can
  carry a universal declaration. `close_detect.json` now sits at the root of
  THIS repository, next to `reply_check.json`, and the individual set's copy
  goes with the practice's other declaration in that move's second step --
  [precedent_close_detect.py](../tools/precedent_close_detect.py) accumulates
  every source's declaration rather than overriding, so two identical ones
  would both fire and `--explain` would report the rule twice.

  So `--explain` now prints `universal/precedent`, not the individual source
  the closing condition above asked for. **Recorded rather than ticked off**,
  per [item-closes-on-its-condition](../practices/item-closes-on-its-condition.md):
  the literal condition was met on 2026-09-14 and then stopped being true,
  and what replaced it is better than what it asked for — close detection is
  live for every adopter running Precedent, not for one person, and nothing
  about it is blocked on a repository under another owner.

  **Disposition:** parked (2026-09-14, closed as done)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

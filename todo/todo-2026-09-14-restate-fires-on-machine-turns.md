---
slug:              todo-2026-09-14-restate-fires-on-machine-turns
kind:              manual
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
noted:             2026-09-14
closed:            null
---
## What

- <a id="restate-fires-on-machine-turns"></a>**The closing-list restate rule
  fires on turns no human asked for, so a background event makes the person
  read the same Next Steps twice.**
  No disposition, so it is `wait`.

  **Seen 2026-09-14, by Morgan, in the session that landed
  [practice-links-travel](../practices/practice-links-travel.md)'s
  withdrawn-sibling check:** *"you sent me the message twice here; but didn't
  we make a change to fix that?"* He had two near-identical `## Next Steps`
  blocks ninety seconds apart.

  **The change he remembered is real, and it is not this.**
  [tools/precedent_reply_check.py](../tools/precedent_reply_check.py) tells a
  session whose reply the gate refused that the person has ALREADY SEEN that
  reply and to emit only the missing closing. Its own comment records the
  2026-09-13 failure it was written for. It worked here: the refused turn
  emitted the closing alone.

  **A THIRD door was found and closed 2026-09-14, and it is not this one
  either.** That block message asked for *"the missing closing section(s)"*
  whatever was actually missing. The individual set revised its required
  closing sentence that morning -- close a session to archive one -- so every
  reply already carrying the heading was refused for the SENTENCE alone, and
  got exactly what the message asked for: a whole second `## Next Steps` block
  written under the first. Morgan: *"In various recent sessions of the last few
  minutes, you repeated the 'next steps' section two times."* A sentence-only
  failure now says sentence-only, in the imperative, and names the repeat as
  the thing not to do; three harness cases hold it, each with its control.
  **The door below is still open** -- a machine-opened turn restates the list
  in full, and nothing in that fix touches it.

  **The second copy came from a different door.** A continuous-integration
  notification arrived as its own turn, and the individual practice governing
  the closing list requires the outstanding items be restated **in full on
  every reply** — a rule written for a human tangent, where restating is
  exactly right. Nothing in it distinguishes a turn a person opened from one a
  machine opened, and the hard requirement that every reply carry the heading
  means the second turn cannot simply omit it.

  **Not fixed here, deliberately** (`dont-race-another-window`, an
  individual practice — unlinked on purpose, since a private set's name does
  not belong in a public tree):
  two sessions were live on these rules when this was found —
  `claude/spawned-sessions-in-closing-list` in this repository and a pull
  request in the individual set — and the rule itself lives in an individual
  set this session cannot push to. Recorded here so the finding survives the
  window that found it
  ([findings-return-through-repo](../practices/findings-return-through-repo.md)),
  not as a claim about what the fix should be.

  **What a fix would have to decide**, since it is not obvious: whether a
  machine-opened turn should carry the closing list at all, or carry a short
  form pointing at the last full one. Suppressing it entirely has a real cost
  — the background turn is often the one carrying the result the person was
  waiting for, and a turn that reports a red check with no closing list is
  worse than one that repeats itself.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

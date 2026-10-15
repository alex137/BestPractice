---
slug:            gotcha-2026-10-15-auto-mode-clears-only-words-that-name-the-action
status:          live
noted:           2026-10-15
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A session asks the person a yes-or-no question before a step Claude Code's
auto mode holds -- committing a change under `.claude/`, merging a pull
request, moving work into `main` -- the person says yes, and the step is
still refused: `[Self-Modification]`, `[Merge Without Review]` or a
production push. Nothing in the repository refused it. The same step goes
through once the person's message names it.

## Story

**2026-10-15, a consumer's Update Vendors.** The update staged an
allow-list change to `.claude/settings.json`, and its report said to ask
the person, adding "their yes is what lets the commit through". The
session asked; Morgan answered "Yes approved. Booked", and the commit was
refused as `[Self-Modification]`. His next message, "Commit the
.claude/settings.json allow-list change", went through first time.

That is the same rule the family below already hit, one action at a time:

- the merge Update Vendors carries
  ([gotcha-2026-10-04](gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge.md)),
  cleared by "Merge PR #N into <branch>" or "Land `<branch>` on <branch>";
- a promote into `main` that never says main
  ([gotcha-2026-09-30](gotcha-2026-09-30-auto-mode-refuses-a-bare-promote-into-main-as-a-production.md));
- a commit of hooks or settings, cleared only by words naming the file and
  the change (this one).

The classifier clears an action when the person's own message "directly and
specifically describes the exact action". A yes answers the session's
question; it does not describe the action, so it does not count, however
plainly the question named it.

## Fix

**Ask for the words, not for a yes.** Hand the person the sentence to say,
naming the action and its target -- "Commit the .claude/settings.json
allow-list change", "Merge PR #N into staging" -- and never put it as a
yes-or-no question.

Update Vendors does this itself since 2026-10-15:
[tools/precedent_update.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update.py)'s
`harness_approval` writes the sentence into the hooks-and-settings
question, and
[tools/precedent_merge_vendors.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_merge_vendors.py)
prints the same sentence when it takes such a change back.

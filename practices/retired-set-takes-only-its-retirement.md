---
slug:        retired-set-takes-only-its-retirement
title:       A retired set takes only the edits that retire it
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "The occasion is editing a practice set that says it is retired -- a moment in another repository, not a path in this one. Reached through the push gate, which refuses the edit in the retired set's own push check. Decided: Morgan, 2026-10-06."
occasion:    "editing a practice set that says it is retired"
gates:       ["push"]
gates_why:   "tools/precedent_push_check.py refuses a push to a set whose precedent-source.json says it is retired when the push changes anything but its retirement (_retired_set_refusal), and the push gate prints this rule. index_required: false: the refusal names the rule at the one moment it matters."
index_clause: "a retired set takes only the edits that retire it"
index_required: false
checked_by:  null
defines:     []
status:      active
in_force_at: null
expires:     "when no repository declares precedent-shared-repo-maintenance or precedent-shared-working-style, and both are archived on GitHub"
supersedes:  []
overrides:   null
added:       "2026-10-06"
approved_by: "Morgan, 2026-10-06 (strength: decided): \"you should not make edits to them unless the edits relate to their deprecation or graceful deprecation ... Please don't forget this. This is important.\" Temporary by his word the same day: \"Once we fully upgraded and eliminated that, then we need to make sure we remove that rule.\""
---
## Rule
A practice set that says it is retired -- `"retired"` in its own `precedent-source.json` -- takes only the edits that retire it: deleting files, saying so in its README and `precedent-source.json`, moving a rule off `status: active`, and regenerating its views and todo index. A finding in a retired set is fixed where the rule lives now, or recorded and left. **It is not moved toward its main branch either**, unless the person asks for that exact move as essential to retiring it gracefully. A set counts as retired once any of its branches on GitHub says so, since a retirement is saved on a lower branch long before it reaches main.

## Detail
The push check refuses anything else, and the promotion tool does nothing in a retired set (`retired_set_hold` in [tools/precedent_branches.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branches.py)). If the person asks for one exact edit anyway, run the push again with `PRECEDENT_RETIRED_SET_EDIT="<their words>"`; the push check prints those words with what they let through. An edit that keeps the retiring copy from contradicting the live rule while repositories still declare the set counts as retiring it gracefully, and is still the exception: say why in the commit.

**This rule is temporary.** It exists while precedent-shared-repo-maintenance and precedent-shared-working-style are being retired. When its `expires:` condition holds, decommission it: this file, `retired_set_hold` in tools/precedent_branches.py and its use in tools/precedent_gate.py (no reminder to move a retired set up), `retirement_on_any_tier` in tools/precedent_vendor_engine.py, `_retired_set_refusal` and its helpers in [tools/precedent_push_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_push_check.py), and `check_retired_set_takes_only_its_retirement` in [tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py) ([decommission-deletes-files](decommission-deletes-files.md)).

## Why
A retired set's rules are in force somewhere else. An edit to its copy reaches only the repositories that have not updated yet, and only until they do, while it costs a full review and promotion like any other change.

## Story
**2026-10-06.** Morgan decided on 2026-10-05 to fold the repo-maintenance and working-style sets into universal and the writing set. On 2026-10-06 a session running the very deep check's fix pass rewrote a rule and its check inside the repo-maintenance set and promoted it toward main. Morgan: *"We are deprecating repo maintenance and working style. So I think you should not make edits to them unless the edits relate to their deprecation or graceful deprecation ... We keep on going back to editing these files. And we shouldn't."* The push check gained the refusal on 2026-10-06, and Morgan added that the rule is temporary: *"Once we fully upgraded and eliminated that, then we need to make sure we remove that rule. This is a good example of temporary rules."* Within the hour a session read "Promote all" as every set, retiring ones included, and stopped only when Morgan said: *"I just told you a few minutes ago to not edit nor promote nor touch repo maintenance or working style, unless it is essential to their graceful deprecation."* Neither retiring set had moved. The promote tool now refuses a retired set, and both guards read the retirement from any tier branch, because both sets carried it only on pre-staging and the guards, reading the checked-out main, had not seen it. So it carries an `expires:` condition, which the very deep check prints every run until a person judges it has come true ([spec/PRACTICE_FORMAT.md](https://github.com/alex137/BestPractice/blob/staging/spec/PRACTICE_FORMAT.md)).

## Install
Nothing to install. The refusal is part of the engine's push check
(`_retired_set_refusal` in
[tools/precedent_push_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_push_check.py)),
so a set gets it with its next engine refresh, and a session pushing from
here gets it now. `checked_by` stays null because the check judges what a
push brings, not the tree as it stands, which is the only thing a
`checked_by` script sees; its planted test is
`check_retired_set_takes_only_its_retirement` in
[tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py).

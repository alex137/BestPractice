---
slug:        session-trailer
title:       Commit messages link the session where the change was planned
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "The occasion is committing anything -- a moment, not a place, and every path is committed. Reached through the occasion index. Decided: 2026-09-28, when the practice landed at universal from the shared set precedent-shared-repo-maintenance."
occasion:    "committing anything"
gates:       ["push"]
gates_why:   "The push check runs tools/checks/check_session_trailer.py (the engine's own since 2026-10-06, before that the repo-maintenance set's) and refuses a commit without the trailer, and the push gate prints this rule. index_required: false records that judgment, with its cost said plainly: in a repo with no trailer check, a missing trailer is first named at push, after the commit exists. Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: assented -- one yes over a batch; corrected 2026-10-05)."
index_clause: "a Session: <url> trailer on every commit"
index_required: false
checked_by:  tools/checks/check_session_trailer.py
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "landed via PR #721 -- moved 2026-09-28 from the shared set precedent-shared-repo-maintenance, Morgan F accepting the session's recommendation to move it (the move: strength assented); the rule itself: Morgan F, migrated from RepoPersonalPreferences by the private-set migration session; push gate, index line dropped: Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: assented -- one yes over a batch; corrected 2026-10-05)"
---
## Rule
A `Session: <url>` trailer on every commit -- for Claude Code, `https://claude.ai/code/session_<ID>`. `Claude-Session: <url>` is also accepted -- the key Claude Code Remote's own harness actually emits as of 2026-09, functionally the same trailer under a different name. For unattended automation with no chat session behind it, the workflow run's own URL stands in. If there is no link to give -- a person committed without an AI assistant, a tool has no shareable link, or the session's own link is hidden from it -- the trailer says so explicitly (`Session: none available (<tool or reason>)`) rather than being silently omitted.

## Detail
A commit GitHub makes with its own buttons -- a merge, squash or revert button, an edit made on the website -- needs no trailer: no session wrote it, and there is nowhere to put one. A revert needs none either ([revert-needs-no-trailer](revert-needs-no-trailer.md)). A practice set may exempt more; what it exempts applies only where that set is declared.

## Why
So a reviewer can tell "considered and skipped" from "forgotten" at a glance, and can trace a change back to the conversation that reasoned it through.

## Story
Migrated from RepoPersonalPreferences by the phase-3 private-set
migration. No incident was recorded, and none is invented here.

The one design detail with a stated reason is the explicit
no-link-available form. A trailer that is simply omitted when a tool has no
shareable session link is indistinguishable from one that was forgotten, so
the rule requires saying so in the trailer itself -- which lets a reviewer
tell "considered and skipped" from "forgotten" at a glance. The same
reasoning covers unattended automation, where the workflow run's own URL
stands in rather than the field going blank.

**Moved to the universal catalogue on 2026-09-28**, from the shared set for
repository maintenance, on Morgan's accepting a session's recommendation
that it applies to any repository and not only to maintaining practice
sets. The rule text is unchanged. Its mechanical check did not move with
it -- see Install for why.

**Push gate, and off the occasion index, from 2026-10-01.** The reduction pass for precedent-individual's session-start file ([the session-file open item](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-30-session-file-cut-to-4000.md)) counted this among the lines a mechanical check already refuses at push: [check_session_trailer.py](https://github.com/alex137/BestPractice/blob/staging/tools/checks/check_session_trailer.py) runs in the push check wherever precedent-shared-repo-maintenance is declared. Where it is not, the push gate still prints this rule, after the commit exists; the Rule's own remedy is a reworded commit before it is shared. Morgan approved (strength: decided): *"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)"*

**Kept, with its exception spelled out, 2026-10-06.** Folding the
repository-maintenance set away, the very deep check found that the
trailer's check lived only in that set. Morgan, 2026-10-06 (strength:
decided): *"with the link back to the session: then yes let's always include
that with an exception of if somehow you can't access it (maybe a user
didn't use an LLM for example, or somehow hid the URL from you)"*. The
check moved into the engine, and the Rule names both cases.

## Install
**The mechanical check ships with the engine:**
[tools/checks/check_session_trailer.py](https://github.com/alex137/BestPractice/blob/staging/tools/checks/check_session_trailer.py)
(until 2026-10-06 it lived only in the repository-maintenance set, so a
repository that stopped declaring that set stopped checking trailers). It
is a tree-scope script that requires a trailer line in one of the valid
shapes, reading the raw commit object for
merge detection (a shallow clone's boundary commit loses its real parents
under `git log --format=%P`). Since 2026-09-29 it judges only the commits a
push carries -- those origin does not have yet -- so a repository adopting it
no longer has to exempt its existing history first: old commits are never
judged, and every new one is judged at the first push that carries it. It
checks presence only, never that the URL resolves to a real session --
which is exactly the "considered and skipped" versus "forgotten" distinction
the Why names.

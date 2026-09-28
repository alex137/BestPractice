---
slug:        session-trailer
title:       Commit messages link the session where the change was planned
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "committing anything"
gates:       []
index_clause: "a Session: <url> trailer on every commit"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "pending PR review -- moved 2026-09-28 from the shared set precedent-shared-repo-maintenance, Morgan F accepting the session's recommendation to move it (the move: strength assented); the rule itself: Morgan F, migrated from RepoPersonalPreferences by the private-set migration session"
---
## Rule
A `Session: <url>` trailer on every commit -- for Claude Code, `https://claude.ai/code/session_<ID>`. `Claude-Session: <url>` is also accepted -- the key Claude Code Remote's own harness actually emits as of 2026-09, functionally the same trailer under a different name. For unattended automation with no chat session behind it, the workflow run's own URL stands in. If a tool has no shareable link at all, the trailer says so explicitly (`Session: none available (<tool>)`) rather than being silently omitted.

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

## Install
**No mechanical check at this level, and the reason is specific.** The
shared set this rule moved from carries one: a tree-scope script that walks
every non-merge commit reachable from HEAD and requires a trailer line in
one of the valid shapes, reading the raw commit object for merge detection
(a shallow clone's boundary commit loses its real parents under
`git log --format=%P`), with the commits that predate it exempted by hash
rather than rewritten. Shipped from universal it would run in every
consuming repository at once, against histories that predate the rule, and
fail on every old commit in each of them. A repository that wants the
mechanical check adopts it deliberately: exempt its existing history first,
then turn it on. It checks presence only, never that the URL resolves to a
real session -- which is exactly the "considered and skipped" versus
"forgotten" distinction the Why names.

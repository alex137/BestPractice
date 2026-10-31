---
slug:        working-in-parallel
title:       "Several members' threads: claim first, flag who the diff touches, warn your own member"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A moment -- starting work, and packaging a change for review, in a repository several members work in. No path reaches it."
occasion:    "starting work, or packaging a change for review, in a repository several members work in"
gates:       []
gates_why:   "No gate fits better than the occasion: the moments are the start of work and the packaging of a pull request, and neither is a merge, a push or a reply on its own."
index_clause: "claim first; flag who the diff touches; warn your own member first"
checked_by:  null
defines:     ["review sensitivities"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-31"
approved_by: "Morgan, 2026-10-31 (strength: decided): moved from the AGENTS.md template's \"Working in parallel\" section into a practice -- \"With all this approved, act booked.\""
---
## Rule
These conventions exist so several members' threads don't duplicate or
silently trample each other's work.

- **Claim before you start.** When a member takes on an open item (or any
  sizable change), mark the item claimed -- *(claimed: NAME, date,
  branch)* -- as the branch's first commit. Before starting any work,
  check the open items' claims and the repo's open branches and PRs for
  overlap with what your member wants; if someone is already on it, say so
  before duplicating their work.
- **Flag changes to the people they matter to -- inferred, not
  declared.** Before packaging changes for review, work out who has
  stakes in the diff and name them in the PR description, requesting
  their review instead of letting the change ride a routine merge.
  Nobody has to articulate their sensitivities up front; two sources
  reveal them:
  1. **Authorship.** Commits are credited to the humans who drove them
     ([commits-credit-the-driver](commits-credit-the-driver.md)), so the
     history says whose work a diff reworks -- substantially rewriting or
     re-toning text another member authored gets flagged to that member by
     default.
  2. **The accumulated list,** which agents maintain from evidence: when a
     member pushes back in review, reverts a change, or objects in
     conversation, that session appends a one-line entry -- what this
     member wants flagged, citing the incident that showed it
     ([cite-the-incident](cite-the-incident.md)). Members may seed entries
     directly, but the list grows mainly by observation.

  (For path-based ownership, GitHub's CODEOWNERS enforces review
  requests natively -- as of 2026-08. The list also covers concerns no
  path expresses, like tone.)
- **Warn your own member first.** Before proposing, compare their change
  against the project's recorded decisions, glossary, and prevailing
  tone. If it cuts against something already decided or established, tell
  them -- "this conflicts in spirit with X; propose anyway, or discuss?" --
  rather than packaging it silently. Disagreement then happens in review,
  on purpose, not by surprise.

## Detail
**Where the accumulated list lives.** In the repository's own AGENTS.md,
under `### Review sensitivities (accumulated)`: one line per member per
concern, each citing the incident that revealed it --
`- <member>: <what to flag> -- <incident that showed it, date>`. The
repository owns that section; no template writes it. A repository with no
entries yet has no section, and authorship-based flagging works from day
one without one: the first session that records an entry adds it.

## Why
Several members' assistants working the same repository see only their
own thread. Without a claim, two of them build the same thing; without
the stakes named, a rewrite of someone's text lands on a routine merge
they never saw; and without the spirit check, a change that cuts against
a recorded decision arrives in review as a surprise rather than a
proposal.

## Story
These were the AGENTS.md template's "Working in parallel (multi-member
repos)" section and its "Review sensitivities (accumulated)" list from the
start. On 2026-10-31 a reduction pass in a consuming repository found
its session load at about 9,975 of the 10,000 tokens allowed, almost all
of AGENTS.md being upstream text; a second consuming repository had already
trimmed this section locally into a side file, where its copy lacked lines
the template carried (the review-request clause, the spirit check's own
words, the CODEOWNERS note). Morgan approved moving the section into a
practice, so every repository carries it once, upstream, and loads it when
the moment comes (strength: decided). The template's own wording is kept
here; "TODO.md" became "open items", since a repository's open items may
live under `todo/`.

## Install
Nothing to install: Update Vendors removes the template's copy of the
section from AGENTS.md where it is unedited, and moves a repository's own
lines from an edited one into a local add-on practice (`adds_to:
working-in-parallel`). A repository's review-sensitivities entries stay
where they are, in its own `### Review sensitivities (accumulated)`.

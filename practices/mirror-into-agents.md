---
slug:        mirror-into-agents
title:       Agent-relevant instructions in a README or other key file also go in AGENTS.md
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Any file can be the one that gains an instruction (a README, a CONTRIBUTING file, a guide), so no narrower glob names them; the occasion index reaches it."
occasion:    "a key file gains an operational instruction"
gates:       ["merge"]
index_clause: "it lands in both AGENTS.md and its human home"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan F, drafted 2026-10-05, moved from the shared set precedent-shared-repo-maintenance; merged in PR #880 on 2026-10-05"
strength: decided
---
## Rule
`AGENTS.md` is the file a session is told to read first. A README, `CONTRIBUTING.md`, a getting-started guide, or any other key file can still pick up its own operational instructions over time -- a setup step, a gotcha, a rule about how to work in the repo -- written where a human reader would look, not where an agent is told to look. When any such file gains an instruction useful for an agent to know (the operational kind: how to build it, a constraint on how to work, a step an agent would otherwise miss -- not general project description), fold the same instruction into `AGENTS.md` too, in its own words if that reads better there.

## Detail
This runs both directions: whether the instruction lands first in the README and needs pulling into `AGENTS.md`, or is written into `AGENTS.md` directly and never mirrored back to where a human would expect to read it. It does not run the other way for content that only belongs in one place -- a README's marketing framing has no business in `AGENTS.md`, and `AGENTS.md`'s own meta-structure has no business padding out a README.

## Why
A stray instruction left in only one file is exactly the kind of drift a capture gate exists to catch -- check for it at the same checkpoint any other captured decision gets folded in.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. That pack recorded the reasoning rather than an incident.

The reasoning turns on where people write things versus where sessions are
told to look. A README, a contributing guide or a getting-started page
accumulates operational instructions over time -- a setup step, a gotcha, a
constraint on how to work -- written where a human reader would look for
them. A session reads the agent instructions file first, so an instruction
that lands only in the other file is found by accident or not at all.

Two boundaries keep it from becoming a mandate to duplicate everything. It
runs in both directions, since the instruction is as likely to be written
straight into the agents file and never mirrored back to where a human would
expect it. And it explicitly does not run for content that belongs in one
place only -- a README's marketing framing and screenshots have no business
in the agents file, and that file's own meta-structure has no business
padding out a README.

## Install
No mechanical check: deciding whether a given addition to a README or other key file is "the operational kind... not general project description" is the judgment the rule's own Rule text names explicitly. A check could flag any `AGENTS.md`/README divergence at all, but that would fire constantly on content that correctly belongs in only one place, which the rule's own Detail section says is normal.


---
slug:        vendor-neutral-by-default
title:       New code and rules here default to provider-neutral, since this repo ships out whole
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing a hook, script, or practice-file rule in this repository that a dependent repo will vendor or install"
index_clause: "this repo ships out whole -- default new code and rules to provider-neutral"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-16"
approved_by: "Morgan, 2026-09-16 -- coined in the same conversation that
  implemented spec/PROVIDER_PORTABILITY_PLAN.md's Phase 3, in his own
  words: \"we should note... that going forward, when we make code changes,
  we should do it in a vendor-neutral way to prepare for other repos.\"
  (strength: decided)."
strength:    decided
---
## Rule
**Before writing a hook, script, or practice-file rule here, ask whether it
assumes Claude Code specifically — and if it does, ask whether it needs
to.** This repository is not a normal codebase with one deployment target:
every file under `templates/`, every `practices/*.md`, and the engine
under `tools/` ships out whole, vendored into every dependent repo that
installs or updates from here. A Claude-only assumption written here does
not stay here — it travels into every repo that vendors this one, whether
or not that repo runs Claude Code at all.

**The test, concretely**: does this depend on a specific tool call
(`ListAgents`, `SendMessage`, `create_trigger`, a Model Context Protocol
(MCP) server only one harness's session provides), a specific hook
protocol (Claude Code's `SessionStart`/`Stop` JSON payload shape), or a
specific default identity (`Claude <noreply@anthropic.com>`)? If yes, either
the dependency is genuinely unavoidable and gets named as a Claude Code
binding explicitly rather than presented as universal (`session-text`'s old
waking mechanism was this case, before it was removed rather than
labelled), or it belongs behind a guard that degrades gracefully when the
tool isn't there (`templates/bootstrap.sh`'s own `if [ -f ... ]` pattern
before calling `commit-identity.sh`).

**Default is not the same as required.** Nothing here says every change
must work identically on every provider — some things genuinely can't
(Phase 4 of [spec/PROVIDER_PORTABILITY_PLAN.md](../../spec/PROVIDER_PORTABILITY_PLAN.md)
is still an open question for exactly that reason). What this rule asks is
that provider-neutral be the assumption a session starts from, checked and
consciously departed from when there's a real reason, rather than
Claude-only being the unexamined default because this repo happens to be
edited from inside Claude Code most of the time.

## Detail
**This is not a new principle — [templates/harness/README.md](../../templates/harness/README.md)
already states it as this repo's design goal.** What this practice adds is
making it a standing check at the moment of writing new code, rather than
something only visible to a session that goes looking for it in a spec
document.

**"Would it hold in a repo running a different kind of program?" is the
wrong question here — the right one is "would it hold under a different
harness."** [rule-level-by-reach](../../practices/rule-level-by-reach.md)'s
three tests (team, person, unrelated repo) answer where a *rule* belongs;
this practice is about a different axis entirely — not who the rule is
for, but which tool is running the session applying it.

## Why
The cost of skipping this check lands downstream, in a repo that installed
Precedent specifically to reduce its own Claude-only surface, and finds a
freshly-vendored practice file naming `ListAgents` in its rule text with no
warning that it won't work there. Nobody notices at write time, because the
session writing it is, almost always, a Claude Code session for whom the
dependency is invisible — it just works, silently, which is exactly the
condition under which an assumption gets baked in without anyone deciding
to bake it in.

## Story
Surfaced 2026-09-16, mid-implementation of
[spec/PROVIDER_PORTABILITY_PLAN.md](../../spec/PROVIDER_PORTABILITY_PLAN.md)'s
Phase 3. A session drafting that phase held back from editing
`templates/bootstrap.sh` — the file every dependent repo vendors — out of
caution that widening it would affect every consumer, not just this one.
Morgan corrected the caution rather than the instinct behind it: *"this
repo works by being vendored in to others so of course it is repo-ed out;
knowing that, what is the reason to not do your change?"* The instinct to
worry about blast radius was right; where it went wrong was treating "this
propagates everywhere" as a reason to hesitate rather than the ordinary,
expected shape of a change here — propagation happens deliberately, one
repo at a time, through
[vendor-update-runbook](../../practices/vendor-update-runbook.md),
never automatically. Naming the general rule in the same conversation —
*"going forward, when we make code changes, we should do it in a
vendor-neutral way to prepare for other repos"* — is what turns one
corrected instance into a standing check for the next one.

## Install
**No mechanical check, and this is a considered gap, not an unexamined
one** ([checkable-gets-checked](../../practices/checkable-gets-checked.md)).
"Does this code assume Claude Code" is a judgment call over arbitrary new
code, not a fixed pattern a script can grep for reliably — the concrete
tool names that make a dependency real
([session-text](../../practices/session-text.md)'s
own inventory: `ListAgents`, `SendMessage`, `create_trigger`,
`fire_trigger`, `add_repo`, plus Claude Code's specific hook JSON fields
and its default bot identity) drift over time and a stale list gives false
confidence. What can be checked, and should be if this recurs: a specific
new dependency, once identified, is exactly what
[spec/PROVIDER_PORTABILITY_PLAN.md](../../spec/PROVIDER_PORTABILITY_PLAN.md)'s
own inventory should be updated to name — this practice governs the check
at write time, that document is the durable record of what was found.

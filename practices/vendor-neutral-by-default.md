---
slug:        vendor-neutral-by-default
title:       New code and rules default to provider-neutral, in any repo that vendors a layer out
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Which files ship out differs by repository (practices, tools, templates), so no single glob names them; the occasion index reaches it."
occasion:    "writing a hook, script or rule another repo will vendor"
gates:       []
index_clause: "default new code and rules to provider-neutral"
checked_by:  null
defines:     []
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan F, drafted 2026-10-05, moved from the shared set precedent-shared-repo-maintenance; merged in PR #880 on 2026-10-05"
strength:    decided
---
## Rule
**Before writing a hook, script, or practice-file rule in a repository that
vendors a layer out to other repos, ask whether it
assumes Claude Code specifically — and if it does, ask whether it needs
to.** Some repos are not a normal codebase with one
deployment target: everything a dependent repo vendors or installs from
them — a practice set's `practices/*.md`, an engine's `tools/`, a template
tree — ships out whole, into every repo that installs from that source.
**Precedent and every practice set's own repository are among them**:
their `practices/*.md` and `tools/` vendor into every project repo that
installs them. A
Claude-only assumption written in a vendor-source repo does not
stay there — it travels into every repo that vendors it, whether or not
that repo runs Claude Code at all.

**The test, concretely**: does this depend on a specific tool call
(`ListAgents`, `SendMessage`, `create_trigger`, a Model Context Protocol
(MCP) server only one harness's session provides), a specific hook
protocol (Claude Code's `SessionStart`/`Stop` JSON payload shape), or a
specific default identity (`Claude <noreply@anthropic.com>`)? If yes,
either the dependency is genuinely unavoidable and gets named as a Claude
Code binding explicitly rather than presented as universal, or it belongs
behind a guard that degrades gracefully when the tool isn't there.

**Default is not the same as required.** Nothing here says every change
must work identically on every provider — some things genuinely can't.
What this rule asks is that provider-neutral be the assumption a session
starts from, checked and consciously departed from when there's a real
reason, rather than Claude-only being the unexamined default because the
repo happens to be edited from inside Claude Code most of the time.

## Detail
**This is not a new principle in the repo it was coined in** — BestPractice's
own `templates/harness/README.md` already stated it as that repo's design
goal before this practice existed to make it a standing check at the
moment of writing new code. Generalized here, the principle holds the same
way wherever it applies: any repo whose files are
vendored or installed elsewhere inherits every assumption baked into
them, so the assumption a session starts from should be checked rather
than defaulted to Claude-only, in that repo or the next one shaped the
same way.

**"Would it hold in a repo running a different kind of program?" is the
wrong question here — the right one is "would it hold under a different
harness."** This practice is about a different axis than where a rule
belongs (that question is [rule-scope-ask](rule-scope-ask.md)'s) — not who
the rule is for, but which tool is running the session applying it.

## Why
The cost of skipping this check lands downstream, in a repo that installed
a practice set (or Precedent itself) specifically to reduce its own
Claude-only surface, and finds a freshly-vendored file naming `ListAgents`
in its rule text or its hook wiring with no warning that it won't work
there. Nobody notices at write time, because the session writing it is,
almost always, a Claude Code session for whom the dependency is invisible
— it just works, silently, which is exactly the condition under which an
assumption gets baked in without anyone deciding to bake it in.

## Story
Coined 2026-09-16 in `alex137/BestPractice`, mid-implementation of that
repo's own Provider Portability plan's Phase 3, as
[`local/practices/vendor-neutral-by-default`](https://github.com/alex137/BestPractice/blob/staging/local/practices/vendor-neutral-by-default.md)
— filed repo-local there, since its own text described only itself:
"this repo ships out whole." A session drafting that phase had held back
from editing a file every dependent repo vendors, out of caution that
widening it would affect every consumer, not just that one; Morgan
corrected the caution rather than the instinct behind it — *"this repo
works by being vendored in to others so of course it is repo-ed out;
knowing that, what is the reason to not do your change?"* — and named the
general rule in the same conversation: *"going forward, when we make code
changes, we should do it in a vendor-neutral way to prepare for other
repos."*

Brought here 2026-09-17, from a session rooted in `alex137/BestPractice`
working an LLM-portability plan for `precedent-beta-v01`. Morgan decided
the rule belongs in this team's own catalogue too, generalized beyond
BestPractice specifically: *"vendor-neutral-by-default should be in
precedent-team-repo-maintenance."* The reasoning underneath it was never
actually specific to BestPractice — this repo vendors its own
`practices/*.md` and `tools/` out to every project repo that installs
this team's set, the identical shape the source practice named for
itself — so the Rule was rewritten from "this repo" to "a repository this
team maintains that vendors a layer out," to hold for this repo and for
any future one shaped the same way, rather than staying readable only as
a citation to BestPractice's own text.

**Reviewed on 2026-09-28 for a merge into universal, and left here.** Universal has no practice by this name: BestPractice's `vendor-neutral-by-default` is repo-local (`local/practices/`), true only of that repository, and this copy is its generalization to any repository that vendors a layer out -- which is maintaining practice sets and their engine, this set's subject. Merging would have meant promoting it to universal, which the reach test does not support: a repository that ships nothing out has no use for it.

## Install
**No mechanical check, and this is a considered gap, not an unexamined
one** (per [`checkable-gets-checked`](https://github.com/alex137/BestPractice/blob/staging/practices/checkable-gets-checked.md)).
"Does this code assume Claude Code" is a judgment call over arbitrary new
code, not a fixed pattern a script can grep for reliably — the concrete
tool names that make a dependency real
(the retired `session-text` practice's
own inventory: `ListAgents`, `SendMessage`, `create_trigger`,
`fire_trigger`, `add_repo`, plus Claude Code's specific hook JSON fields
and its default bot identity) drift over time and a stale list gives
false confidence. What can be checked, and should be if this recurs: a
specific new dependency, once identified, is worth naming in a tracked
record the way BestPractice's own `spec/PROVIDER_PORTABILITY_PLAN.md`
does for that repo -- this practice governs the check at write time, a
durable record in whichever vendor-source repo hit the case is where what
was found should live.

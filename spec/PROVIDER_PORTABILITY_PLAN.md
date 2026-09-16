---
title:         Provider portability — what this repo owes Claude Code today, and the plan to close the gap
kind:          proposal
status:        drafted
opened:        2026-09-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Inventories every place Precedent's own repo is coupled to Claude Code specifically, and lays out a phased plan to bring ChatGPT/Codex, Grok and other coding-capable LLMs to the same level of automation, building on the harness-adapter pattern that already exists in templates/harness/.
---

# Provider portability — what this repo owes Claude Code today, and the plan to close the gap

Morgan asked which parts of `precedent-beta-v01` depend on Claude
specifically, and for a plan to bring other cloud LLMs — ChatGPT/Codex, Grok,
and by extension Gemini — up to the same level of smoothness. This document
answers the first question with citations and proposes the second as a
phased plan. Nobody has approved it yet; **`status: drafted`** means exactly
that.

**This is not starting from zero.** [templates/harness/README.md](../templates/harness/README.md)
already states the design goal plainly — "the practice layer is
agent-agnostic" — and already ships working adapters for
[templates/harness/codex/](../templates/harness/codex/) and
[templates/harness/gemini-cli/](../templates/harness/gemini-cli/) alongside
[templates/harness/claude-code/](../templates/harness/claude-code/). Two
open items already name pieces of this gap:
[todo/todo-2026-09-06-actions-as-enforcement-layer.md](../todo/todo-2026-09-06-actions-as-enforcement-layer.md)
diagnoses the enforcement half, and [MOBILE.md](../MOBILE.md) plus
[todo/todo-2026-09-06-grok-workflow.md](../todo/todo-2026-09-06-grok-workflow.md)
and [todo/todo-2026-09-06-plain-chatgpt-write-support.md](../todo/todo-2026-09-06-plain-chatgpt-write-support.md)
cover the lightweight, ask-questions-from-a-phone surface. What's missing is
the piece in between: bringing a full coding-agent session on another
provider — one actually editing files and pushing commits in this
repository, the way this session is — up to Claude Code's level of
automatic, enforced behavior. That is this plan's scope. It does not
re-litigate or duplicate the three items above; it cites them where the work
overlaps.

## What actually depends on Claude — the inventory

**Genuinely portable already.** The practice-file format itself
([practices/](../practices/), YAML frontmatter plus prose), the occasion
index and resident block in [AGENTS.md](../AGENTS.md), and the whole
`precedent_*.py` tool family — [tools/precedent_show.py](../tools/precedent_show.py),
[tools/precedent_gate.py](../tools/precedent_gate.py),
[tools/precedent_paths.py](../tools/precedent_paths.py),
[tools/precedent_check.py](../tools/precedent_check.py) — are plain Python
operating on git, markdown and JSON. None of them import an Anthropic SDK,
shell out to a `claude` binary, or call `api.anthropic.com`. Any agent that
can run a Python script and read a markdown file can use this layer today,
told to do so by its own instructions file. [AGENTS.md](../AGENTS.md) itself
is the canonical file for exactly this reason — several agent CLIs, not just
Claude Code, read it natively — and [CLAUDE.md](../CLAUDE.md)'s own comment
says as much: it is a one-line adapter, not the canonical source.

**Hard-coupled, in four places:**

1. **This repo's own hook wiring.** [.claude/settings.json](../.claude/settings.json)
   wires `SessionStart`, `UserPromptSubmit`, `PreToolUse` and `Stop` hooks
   that read Claude Code's specific JSON payload shapes — `stop_hook_active`
   ([.claude/hooks/stop-git-check.sh](../.claude/hooks/stop-git-check.sh)),
   `tool_input.file_path`
   ([.claude/hooks/precedent-paths.sh](../.claude/hooks/precedent-paths.sh)),
   and the Stop hook's `transcript_path`, which
   [tools/precedent_reply_check.py](../tools/precedent_reply_check.py)
   depends on to read the session's own JSONL transcript and enforce the
   reply gate. None of this fires under a harness that doesn't implement the
   same hook protocol — and today, only the `claude-code/` adapter is
   actually installed at this repo's root. The `codex/` and `gemini-cli/`
   adapters exist as templates for repos that install Precedent, not as
   something this repo runs on itself.
2. **The archive-command practice, and — as of 2026-09-16, partially closed
   — session-text.** [practices/archive-command.md](../practices/archive-command.md)
   still names Claude Code Remote MCP (Model Context Protocol) tool calls
   directly in its rule text: `get_session`, `list_triggers`,
   `archive_session`, `unarchive_session`. There is no abstraction layer; a
   session on a provider without that MCP server cannot carry out this
   practice as written, at all — not degraded, just inapplicable.
   [practices/session-text.md](../practices/session-text.md) had the same
   problem (`add_repo`, `list_sessions`, `ListAgents`, `SendMessage`,
   `create_trigger`, `fire_trigger`) until this date, when the practice was
   changed to never wake or create a session at all — see Phase 4 below for
   what that traded away. `add_repo` for the cross-repository capability
   check is still named in session-text's Rule; it is a narrower dependency
   than the messaging tools were, since a session on another provider simply
   has no such call to make and the check degrades to "assume this session
   can't reach it," which is the safe direction to be wrong in.
3. **Commit identity and the trailer convention.**
   [.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh)
   and [tools/precedent_session_check.py](../tools/precedent_session_check.py)
   hardcode `noreply@anthropic.com` as the one email that is never a human,
   because Claude Code's own default container identity is
   `Claude <noreply@anthropic.com>` — see
   [practices/next-steps-after-commit.md](../practices/next-steps-after-commit.md)'s
   note on this. The `Claude-Session:` commit trailer this session is
   instructed to emit (recorded as a formal exception in
   [decisions/2026-09-03-session-trailer-key.md](../decisions/2026-09-03-session-trailer-key.md),
   alongside the neutral `Session:` key the check also accepts) exists only
   because that is what Claude Code's harness actually produces by default,
   not because the repository chose it independently.
4. **The one real automatic trigger point.** [tools/precedent_gate.py](../tools/precedent_gate.py)'s
   own comments and [templates/harness/README.md](../templates/harness/README.md)'s
   adapter table both note that the only two things that can interrupt a
   session automatically today are a git pre-push hook and a Claude Code
   Stop hook. Everything the gate mechanism would enforce on another
   provider currently falls back to the instructions file alone — a *soft*
   guarantee, in that same document's own terms, versus Claude Code's *hard*
   one.

**Not found:** no vendor API calls or CLI shell-outs anywhere in
[tools/](../tools/), and no hardcoded Claude model IDs in repository content
(only in this session's own runtime system reminders, which are not part of
the repo).

## The plan

Five phases, each independently landable, in the same style
[spec/DOCUMENT_LIFECYCLE.md](DOCUMENT_LIFECYCLE.md) and
[spec/CONTRIBUTOR_ACCESS.md](CONTRIBUTOR_ACCESS.md) use. Work continues to
land on `precedent-beta-v01` per [AGENTS.md](../AGENTS.md)'s standing rule.

### Phase 1 — CI as the backstop, not a new idea

This phase already exists as
[todo/todo-2026-09-06-actions-as-enforcement-layer.md](../todo/todo-2026-09-06-actions-as-enforcement-layer.md);
this plan adopts it rather than restating it. The reasoning that matters
here specifically: a required GitHub Actions check binds every path to the
default branch — human, Claude Code, ChatGPT, Grok, a web-UI merge —
regardless of whether the agent that made the change has a shell or a hook
at all. It is the one enforcement layer that does not care which provider
produced the commit. **Done when:** [tools/practice_audit.py](../tools/practice_audit.py)
(or its successor) runs as a required PR check, alongside the markdown-lint
workflow that already proves the pattern.

### Phase 2 — install the existing adapters on this repo's own root

[templates/harness/codex/](../templates/harness/codex/) and
[templates/harness/gemini-cli/](../templates/harness/gemini-cli/) already
exist and are documented. Today they are offered to repos that *install*
Precedent; this repo does not run them on itself, and — because this repo
is the source rather than an adopter — it doesn't even carry its own
instantiated `tools/bootstrap.sh` yet; only [templates/bootstrap.sh](../templates/bootstrap.sh)
exists, the template [INSTALL.md](../INSTALL.md) tells an adopting repo to
copy to that path. Add [AGENTS.md](../AGENTS.md)'s Codex and Gemini CLI wiring here —
instantiate `templates/bootstrap.sh` as `tools/bootstrap.sh` the same way an
adopting repo would, and point the codex adapter's setup script at it; the
Gemini adapter needs the [GEMINI.md](../templates/harness/gemini-cli/GEMINI.md)
pointer file at root, or a `contextFileName` setting where the CLI version
supports reading [AGENTS.md](../AGENTS.md) directly. **This makes Precedent eat its own
dog food**: a session opened here under Codex or Gemini CLI should get the
same starting instructions a session under Claude Code gets, today, not
after some future adopter builds it first. **Done when:** a session started
under each adapter loads [AGENTS.md](../AGENTS.md), runs the instantiated
`tools/bootstrap.sh`, and the deep check passes regardless of which adapter
was active.

### Phase 3 — port the freshness and identity hooks

[templates/harness/README.md](../templates/harness/README.md)'s own porting
recipe (its six-question section) is largely unexecuted for Codex and
Gemini specifically — the freshness gate and `commit-identity.sh` "depend on
nothing Claude Code specific beyond how it is invoked," per that same
document, but nobody has written the Codex- or Gemini-side invocation yet.
Do that: wire [.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh)'s
session-start half into Codex's setup script and Gemini's session-start
directive, and the freshness guard the same way. **Done when:** a commit
made under a Codex or Gemini CLI session in this repo is authored correctly
without anyone having to remember, the same guarantee Claude Code already
has.

### Phase 4 — de-vendor the session-text and archive-command practices

This is the phase with no existing scaffolding to build on, and the one
likely to need a real design decision rather than a mechanical port. The
practice text in [practices/session-text.md](../practices/session-text.md)
and [practices/archive-command.md](../practices/archive-command.md)
currently names Claude Code Remote MCP tools directly — `add_repo`,
`list_sessions`, `create_trigger`, `archive_session`, and the rest. Two ways
were on the table to close this, and this plan did not pick one on its own:

- **Capability indirection.** Rewrite the practices to describe the
  *capability* ("wake an existing session that holds this context, rather
  than starting fresh" / "end a session's lifecycle") and move the concrete
  tool names into a per-harness binding table, the same way
  [templates/harness/README.md](../templates/harness/README.md) already
  separates the *what* (bootstrap, freshness, identity) from the *how*
  (which hook, which script) per adapter.
- **Scope the practices as Claude-Code-only**, explicitly, with a note
  pointing a session on another provider at whatever native session/thread
  mechanism it has, if any — accepting that cross-session handoff may simply
  not generalize the way file-based practice loading does, since it depends
  on a specific MCP server existing at all.

**[practices/session-text.md](../practices/session-text.md)'s half took a
third path, decided 2026-09-16: remove the capability rather than indirect
or scope it.** Morgan chose this over capability indirection on two
grounds — the tool surface waking depended on (`ListAgents`, `SendMessage`,
`create_trigger`) had already caused real reliability problems for
`create_session`, and he wants the catalogue portable to providers like
Grok without a binding table to maintain per provider. The practice now
always produces Session Text (a paste block), never wakes a live session
and never creates one; what is lost is the context-reuse saving waking
existed for, named explicitly in the practice's own Story rather than left
implicit. [practices/archive-command.md](../practices/archive-command.md)'s
`list_triggers` call is a different case — it checks whether a Routine is
bound to the session being archived, not a cross-session handoff — and is
**not yet touched**; it is a smaller, narrower dependency than
session-text's was, and still open.

**Done when:** either a session on a non-Claude-Code provider can carry out
`archive-command`'s intent through a named alternate mechanism, or the
practice file says plainly that it doesn't apply outside Claude Code and
why. `session-text` no longer needs this test — it depends on nothing
provider-specific at all.

### Phase 5 — re-verify the lightweight surfaces and close the loop

Once phases 1-4 land, re-run the two open verification items —
[todo/todo-2026-09-06-grok-workflow.md](../todo/todo-2026-09-06-grok-workflow.md)
and
[todo/todo-2026-09-06-plain-chatgpt-write-support.md](../todo/todo-2026-09-06-plain-chatgpt-write-support.md)
— since a Codex adapter with working bootstrap and identity hooks is exactly
the "coding agent" [MOBILE.md](../MOBILE.md) currently tells ChatGPT and
Grok users to route changes through. Update [MOBILE.md](../MOBILE.md)
either way, per those items' own close condition.

## What this plan does not attempt

**Feature parity on cross-session orchestration is not promised.** Claude
Code Remote's session-spawning, waking and routine/trigger mechanism may
have no equivalent primitive on another provider at all; phase 4's second
option exists because forcing an equivalence that isn't there would be
inventing capability rather than porting it. **Nor does this plan touch the
mobile/chat-app surface directly** — that is [MOBILE.md](../MOBILE.md)'s and
the two existing todo items' territory, referenced above rather than
restated.

## Open questions

- **Does the capability-indirection design in phase 4 turn into a general
  practice**, the way the hook-porting recipe in
  [templates/harness/README.md](../templates/harness/README.md) already
  generalizes bootstrap, freshness and identity? Blocked on having designed
  it once for session-text specifically, so the abstraction is drawn from a
  real case rather than guessed.
- **Who verifies phase 5's re-tests** — this plan does not staff them, since
  verifying a third-party connector's current capability is exactly the
  kind of claim [no-invented-specifics](../practices/no-invented-specifics.md)
  says not to assert without having actually run it.

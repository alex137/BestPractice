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
diagnoses the enforcement half, and [MOBILE.md](../documentation/MOBILE.md) plus
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

**Partially done, 2026-09-16, after correcting the original premise.**
[tools/practice_audit.py](../tools/practice_audit.py) — this phase's
original "done when" — turned out not to apply here: its own `--help`
says it audits a *dependent* repo's vendored `process/upstream/` tree, and
this repo vendors nothing. This repo's own contributor-facing enforcement
was already covered: [.github/workflows/deep-check.yml](../.github/workflows/deep-check.yml)
and `leak-gate.yml` already run `precedent_check.py`, `verify_harness.py`
and `doc_sync.py` on every push and PR, regardless of tool.

**What was actually found, reading the concurrent "CI-minutes plan"
(commits `a1fd03f3`–`5bd5f06e`) before touching anything**: that work
added a platform question to the guided install
([spec/INSTALL_QUESTIONS.md](INSTALL_QUESTIONS.md)) — *which AI assistant
will work in this repo* — with the stated reasoning that a
shell-less assistant (ChatGPT via GitHub's connector) needs GitHub Actions
as its *only* enforcement channel. But the very next row, `ci_workflows`,
still said "default disabled, unless the person says otherwise" — flat,
regardless of the answer just given. The platform question was being
asked and explained, then ignored by the default it was supposed to
inform. **Fixed**: [spec/INSTALL_QUESTIONS.md](INSTALL_QUESTIONS.md) and
[SETUP.md](../SETUP.md) now make the `ci_workflows` default depend on the
platform answer —
enabled by default for a shell-less assistant, disabled by default for one
with its own bootstrap and hooks (Claude Code, Codex, Gemini CLI, all of
which Phase 2 gave this repo). This is a conversational-default fix, not a
code change — the actual value still gets recorded by whoever conducts the
install, same as before.

**Still open**: a plain dependent project repo gets `doc-lint.yml.template`
(markdown lint only) by default, never the full `precedent-check.yml.template`
suite a practice-set repo gets, so a project repo's own practice compliance
(not just its markdown) still goes unchecked in CI even when `ci_workflows`
is on. Whether that gap is worth closing, and how, is not decided here —
picking it up should start from the CI-minutes plan's own "Sequencing and
status" section, not from scratch. This phase still traces back to
[todo/todo-2026-09-06-actions-as-enforcement-layer.md](../todo/todo-2026-09-06-actions-as-enforcement-layer.md),
whose core reasoning stands regardless of the corrections above: a required
GitHub Actions check binds every path to the default branch — human,
Claude Code, ChatGPT, Grok, a web-UI merge — regardless of whether the
agent that made the change has a shell or a hook at all.

### Phase 2 — install the existing adapters on this repo's own root

**Done, 2026-09-16.** `templates/bootstrap.sh` is now instantiated as
[tools/bootstrap.sh](../tools/bootstrap.sh), and
[GEMINI.md](../GEMINI.md) is installed at the root pointing at
[AGENTS.md](../AGENTS.md), per
[templates/harness/README.md](../templates/harness/README.md)'s own
adapter pattern; [AGENTS.md](../AGENTS.md)'s "Working in this repo" section
now tells a non-Claude-Code session to run the bootstrap script, since only
Claude Code gets it automatically. Codex needed no pointer file (it reads
`AGENTS.md` natively) — this repo eats its own dog food now, the same way
[templates/harness/codex/](../templates/harness/codex/) and
[templates/harness/gemini-cli/](../templates/harness/gemini-cli/) already
told an *adopting* repo to. Verified: `bash tools/bootstrap.sh` runs
cleanly here (the deep check does not yet run under an actual Codex or
Gemini CLI session, since none was available to test from inside this
one — see Phase 5). Its own freshness-sync check surfaced a real,
pre-existing, unrelated problem in `precedent.json`'s source path (a
self-referential source declared at this repo's own root) — noted, not
fixed, since it is a separate issue from portability.

### Phase 3 — port the freshness and identity hooks

**Done, 2026-09-16.** The freshness half was already inside
`templates/bootstrap.sh` (the fetch/fast-forward logic Phase 2 installed);
what was missing was identity. `templates/bootstrap.sh` now calls
[.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh)
directly when the file is present, guarded and non-fatal on failure —
confirmed idempotent under Claude Code (a no-op there, since its own
SessionStart hook already ran it first) and syntax-checked. `tools/bootstrap.sh`
was re-copied from the template to carry the same change here.

**This edits the shared template, not a copy scoped to this repo, and
that is deliberate.** The concern raised when this phase was first
written — that changing `templates/bootstrap.sh` widens every dependent
repo's copy, not just this one's — turned out to be the wrong thing to
worry about: propagating a template improvement to already-vendored repos
is exactly what [vendor-update-runbook](../practices/vendor-update-runbook.md)
exists for, one repo at a time, on that repo's own next update. It is not
automatic and was never going to be from here; it needs no special
handling beyond what "Update Vendors" already does.

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
implicit.

**[practices/archive-command.md](../practices/archive-command.md)'s half
took the second path, 2026-09-17: name it as a Claude Code Remote binding
rather than indirect or remove it.** Its `list_triggers` call is a
different case from session-text's waking — it checks whether a Routine is
bound to the session being archived, not a cross-session handoff — and
unlike waking, there is no provider-neutral substitute: ending a session's
lifecycle is inherently a platform action, nothing a paste block can stand
in for. So the Rule now states the capability generically first ("end that
session's lifecycle through whatever mechanism this harness provides"),
names the Claude Code Remote calls as the one binding this practice
currently has, and says plainly that a session on another provider has no
way to carry out the mechanical half — rather than silently doing nothing
or improvising a substitute.

**Done, 2026-09-17.** Both halves of this phase are closed, by two
different routes: session-text by removing the dependency, archive-command
by naming it. Neither approach generalizes to the other — a future
practice with the same problem needs its own judgment call about which
fits, not a rule that one path always wins.

### Phase 5 — re-verify the lightweight surfaces and close the loop

Once phases 1-4 land, re-run the two open verification items —
[todo/todo-2026-09-06-grok-workflow.md](../todo/todo-2026-09-06-grok-workflow.md)
and
[todo/todo-2026-09-06-plain-chatgpt-write-support.md](../todo/todo-2026-09-06-plain-chatgpt-write-support.md)
— since a Codex adapter with working bootstrap and identity hooks is exactly
the "coding agent" [MOBILE.md](../documentation/MOBILE.md) currently tells ChatGPT and
Grok users to route changes through. Update [MOBILE.md](../documentation/MOBILE.md)
either way, per those items' own close condition.

**Research pass, 2026-09-17 — corrects an earlier wrong claim in this same
conversation.** Asked to check whether Codex, Gemini CLI, or Grok
authenticate outbound GitHub API calls the same automatic way this Claude
Code Remote environment does (see the finding below), a web search turned
up something this plan had gotten flatly wrong: **Grok Build
(`xai-org/grok-build`) is a real coding-agent product** — a terminal agent
with shell and file access, reading `AGENTS.md` natively — not the
plain-chat-only Grok this plan and `MOBILE.md` had both assumed. A new
[templates/harness/grok-build/](../templates/harness/grok-build/) adapter
now exists, grounded in xAI's own current docs and explicit about what
wasn't confirmed (the exact `.grok/hooks.json` syntax, and whether "reads
`.claude/`" means it actually fires those hooks the way Claude Code's own
protocol does). It is deliberately **not** wired into
[templates/harness/LEDGER.md](../templates/harness/LEDGER.md)'s enforced
transfer tracking yet — that check's member list is hardcoded to the
original three, and extending it on an unverified hooks syntax would risk
enforcing something wrong.

**The same pass also found `commit-identity.sh`'s GitHub-lookup mechanism
was quietly Claude-Code-Remote-specific.** It calls
`curl https://api.github.com/user` with no Authorization header, which
only ever worked because this environment's own outbound proxy injects a
GitHub credential transparently — confirmed by checking each platform's
own current docs: neither Codex Cloud nor Gemini CLI does anything
equivalent; both expect the person to supply a token themselves. Fixed the
same day: the script now sends a bearer token when `GH_TOKEN` or
`GITHUB_TOKEN` is set (the same precedence `gh` CLI itself uses, and
exactly what GitHub Actions sets automatically on every runner), and falls
back to the old unauthenticated call otherwise — unchanged behavior under
Claude Code Remote, a real chance at working elsewhere instead of a
guaranteed silent no-op.

## What this plan does not attempt

**Feature parity on cross-session orchestration is not promised.** Claude
Code Remote's session-spawning, waking and routine/trigger mechanism may
have no equivalent primitive on another provider at all; phase 4's second
option exists because forcing an equivalence that isn't there would be
inventing capability rather than porting it. **Nor does this plan touch the
mobile/chat-app surface directly** — that is [MOBILE.md](../documentation/MOBILE.md)'s and
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

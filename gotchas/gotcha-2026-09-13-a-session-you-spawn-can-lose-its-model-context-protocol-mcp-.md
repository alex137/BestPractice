---
slug:            gotcha-2026-09-13-a-session-you-spawn-can-lose-its-model-context-protocol-mcp-
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A session you spawn can lose its Model Context Protocol (MCP) tools mid-run, and it cannot report back to you either — so a spawned session must take the measurement it was spawned for in its OPENING turn.

## Story

**A session you spawn can lose its Model Context Protocol (MCP) tools mid-run,
and it cannot report back to you either — so a spawned session must take the
measurement it was spawned for in its OPENING turn.** 2026-09-09: a
measurement session created with `create_session` called `add_repo`
successfully as its first tool call, and when sent a follow-up minutes later
answered that the tool was gone — *"the MCP server that provided it was
removed from the configuration mid-session"* — with a `ToolSearch` for it
returning nothing. Nobody reconfigured anything. The follow-up measurement was
simply lost. The second half was wrong until 2026-09-13: `ListAgents` does not
reach a cloud session, so `SendMessage` fails — but **that is peer messaging,
not every route.** `create_trigger` with `persistent_session_id` fires into a
named session; one did that to correct this entry. It needs the spawner's
session id, so the seeded prompt must name it
([seeded-prompt-names-its-origin](../practices/seeded-prompt-names-its-origin.md)).
Still write the measurement into the prompt: the tools can vanish mid-run,
which is this entry's actual subject.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

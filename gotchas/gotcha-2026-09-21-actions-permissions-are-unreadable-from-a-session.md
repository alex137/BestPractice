---
slug:            gotcha-2026-09-21-actions-permissions-are-unreadable-from-a-session
status:          live
noted:           2026-09-21
severity:        minor
retired:         null
retires_when:    "the GitHub Model Context Protocol (MCP) server exposes a method that reads GET /repos/{owner}/{repo}/actions/permissions -- its actions_get and actions_list methods are closed enums, so this retires when one of them grows the entry, not when a session finds a clever route"
---

## Symptom

A session is asked whether GitHub Actions is actually **enabled** on a
repository — during an install audit, or when a workflow that should be
running is not. The obvious answer is
`GET /repos/{owner}/{repo}/actions/permissions`, and **there is no way to call
it from inside a session.**

The session then reaches for a token to curl it with, which is correctly
refused as credential exploration, and the question stalls on what looks like
a permissions problem but is a missing tool.

## Story

2026-09-21, auditing every repository carrying a Precedent install. One of
the things worth knowing per repository was whether Actions was on at all —
a repo with workflows committed and Actions switched off looks, from the
tracked tree, exactly like a repo with working CI.

**Measured, not assumed.** The GitHub MCP server’s Actions surface is two
tools with closed enumerations:

- `actions_list` — `list_workflows`, `list_workflow_runs`,
  `list_workflow_jobs`, `list_workflow_run_artifacts`
- `actions_get` — `get_workflow`, `get_workflow_run`, `get_workflow_job`,
  `download_workflow_run_artifact`, `get_workflow_run_usage`,
  `get_workflow_run_logs_url`

Neither enum has an entry for the permissions endpoint, and an enum is not a
path you can talk your way past. There is no generic "call this REST path"
tool beside them either.

The second reflex — fetch a token from the environment and curl the endpoint
— is refused, and the refusal is right. **The trap is that the two failures
look like one failure**, so the session reports "I don't have permission to
read that", which is not what happened. It has the permission and lacks the
tool.

## Fix

**Use the behavioural test, and label it as inference.** For each workflow,
compare its most recent run's timestamp against the repository's `pushed_at`.
A run that fired within a second or two of the last push proves two things at
once: Actions is on, and that workflow's trigger matches what was pushed.

That is sound as far as it goes, and it has a hole worth stating in whatever
the session writes up: **it cannot distinguish "Actions is disabled" from
"the workflow is present but its trigger never fired."** Both produce the
same observation — no recent run — and only the first is a problem.

**One signal narrows it, and it is easy to miss:** `list_workflows` returns a
per-workflow `state` field. `active` versus `disabled_manually` /
`disabled_inactivity` tells you whether *that workflow* was switched off,
which is a different question from whether the *repository's* Actions
permission is on. Read it before falling back to timestamps — it is already
in a response the audit is making anyway.

What `state` does **not** settle is the repository-level switch; no response
available here carries that, which is the whole gotcha. Where the answer has
to be certain rather than probable, the honest move is to say so and ask the
person to open the repository's Settings → Actions page, rather than dressing
a timestamp correlation up as a reading of the setting.

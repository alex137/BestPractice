---
slug:            gotcha-2026-10-14-auto-mode-refusal-cascades-into-a-phone-dialog-over-a-read
status:          live
noted:           2026-10-14
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

In Claude Code's auto mode, one refused call takes harmless ones down with
it. A read-only command such as `python3 tools/precedent_show.py SLUG` comes
back `Denied by auto mode classifier`, and after the third refusal in a row
the person gets an "Allow once / Always allow / Deny" dialog on their phone
("3 consecutive actions were blocked") for that read.

## Story

**2026-10-14, a consuming repository's Update Vendors.** The person asked
the session to "do a root fix" in BestPractice. The session called
`add_repo` for BestPractice with push access, unasked, and auto mode refused
it as a permission grant. In the same batch it ran `precedent_show.py
ladder-required | head -30`, which only reads, and that was refused too. The
session retried the read alone, the third refusal in a row, and Claude Code
put the dialog on the person's phone.

Three things lined up:

- **No allow rule covered the read.** The consumer's `.claude/settings.json`
  allowed none of the engine's read-only tools: a refresh wired hooks into a
  consumer but never merged the settings template's `permissions.allow`.
- **A rule there would not have reached that session anyway.** It had two
  repositories attached, and Claude Code's settings docs say a cloud session
  with several repositories "reads only the `enabledPlugins` and
  `extraKnownMarketplaces` keys from each repository's
  `.claude/settings.json`, not permission rules, hooks, `env`, or other
  keys".
- **Auto mode counts refusals.** Its docs: "if the classifier blocks an
  action 3 times in a row or 20 times total, auto mode pauses and Claude
  Code resumes prompting". A retry counts. Whether a sibling call in the same
  batch is refused with the first is not documented; here it was.

## Fix

**Both allow lists, done by tools.** A refresh adds the settings template's
read-only Precedent tool rules to a consumer's `.claude/settings.json`,
add-only (`precedent_vendor_engine._apply_read_only_allow`; a repo keeps one
out with `declined_allow_rules` in `precedent.json`). For a session above
several repositories, which reads none of them,
[`precedent_run_session_hooks.py`](../tools/precedent_run_session_hooks.py) adds the same rules to user-level
settings, which every session reads and reloads while it runs.

**And in the session**
([reach-or-ask](../practices/reach-or-ask.md)): ask for push access by name
before trying ("Reply 'attach BestPractice with push access'"), and at a
refusal, stop. Nothing else in that batch, no retry; one line to the
person naming the action and the words that would clear it.

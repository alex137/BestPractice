---
slug:        master-maintainer
title:       One standing session per repository maintains its trunk after every landing, and its heartbeat shows it is alive
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A property of a repository's standing session, not of any file it touches. Reached through the occasion index and through the session-start notice tools/precedent_heartbeat.py prints when a maintainer is missing. Decided: 2026-10-20, when the practice landed."
occasion:    "setting up a repository's standing session, or session start says the repository has no maintainer"
gates:       []
index_clause: "one standing session per repo checks trunk after landings; a heartbeat shows it"
checked_by:  null
defines:     ["master maintainer", "heartbeat"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-20"
approved_by: "S. Alexander Jacobson, 2026-10-20 — asked for it to be built in BestPractice (\"Why are we writing a proposal rather than just pushing a BP fix?\", then \"go ahead and start the builder session\")"
strength:    decided
---
## Rule
**A repository that uses BestPractice has one master maintainer: a
standing session that watches its trunk.** After each landing it runs the
**full check**, **refreshes the generated tables**, **publishes the
rendered pages**, and **watches the repositories vendored into it**. What is
plainly its own to fix, it fixes and lands; anything else it **files as an
open item and sends to the session that made the change**.

**It proves it is alive with a heartbeat**: on a schedule, one small file
pushed to a side branch (`maintainer-heartbeat`), **never to the trunk**.
**Every session reads the heartbeat's age at session start**; when it is
missing or older than the limit, the session **tells the person once, in
plain words,** that the repository has no maintainer, and gives the
paste-ready prompt that starts one.

## Detail
**What it replaces.** Checks that only run inside each working session
miss every session that does not run them: one opened above its
repositories runs none of their hooks. The per-person switchboard closed
that gap with a setup step in everyone's environment. One maintainer per
repository closes it for everyone at once, so that step is no longer
offered. The cheap checks that guard work as it is done stay in every
session: a commit's links and lint, a push's checks, and not stopping with
unsaved work. The slow and cross-repository checks move to the maintainer.

**The cost, said plainly.** A problem is caught after it lands, not before
(S. Alexander Jacobson accepted this on 2026-10-20: a new session already
pulls from a branch that has landed). One session is a single point of
failure, which is what the heartbeat is for: a dead maintainer is noticed
at the next session start, not weeks later. Only the conversation that
published a rendered page can update it in place, so the session that
becomes the maintainer re-publishes every page once and records the new
links.

**Declaring it.** A `maintainer` block in `precedent.json`:

```json
"maintainer": {
  "title": "Master maintainer (<repo>)",
  "prompt_file": "process/jobs/maintainer.md",
  "session": "session_...",
  "heartbeat_branch": "maintainer-heartbeat",
  "stale_after_hours": 24
}
```

`session` is filled in once the maintainer runs. The last two are optional;
the defaults are in [tools/precedent_heartbeat.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_heartbeat.py).
A repository with no block hears nothing at session start.

**The heartbeat.** `python3 tools/precedent_heartbeat.py beat` replaces the
one file on the side branch through
[tools/branch_store.py](https://github.com/alex137/BestPractice/blob/staging/tools/branch_store.py) in snapshot mode, so the branch
never grows and the working tree is never touched. The maintainer schedules
it into its own session every six hours; the limit is a day, so one missed
beat is not an alarm. Both numbers are guesses to revisit, not facts.

**The reply gate leaves it alone.** A standing session's replies are read by
nobody in real time, so the reply-format requirements do not apply to the
session named as `maintainer.session` (or listed in `standing_sessions`).
The two that guard work still do: never claim the session can be archived
while work is unsaved, and never stop with work left uncommitted.

**How it runs, from what the first standing jobs learned.**

- **Heavy work runs in a git worktree of its own.** A hook in the main
  checkout may fast-forward the trunk under a running job.
- **A long run starts detached** (`nohup setsid ... &`) and is waited on by
  a line in its log, never by a process id. A container restart kills
  everything, so the work carries on from saved state when it is woken
  again.
- **Several landings during one run are one more run**, not one each: merge
  the trunk into the run's branch and run again.
- **It lands only by the repository's own route** (its lander, its merge
  runbook), and asks the person once to type the standing go-ahead into it,
  since a prompt one session seeds into another is not that person's word.

**The job prompt** each repository keeps at `prompt_file` says, in its own
words: what wakes it (a landing notice, its heartbeat, a message from
another session); the after-landing steps in order (full check, tables,
renders, vendored-repository freshness); where results go (its own
branch, landed by the repository's route); whom it tells (the session that
made a failing change, by message; the person only for what needs a
person); and how to recover it (title, tags, the go-ahead).

## Why
A check that depends on every session running it fails silently in the
sessions that do not, and nobody hears. A check that runs once, after the
landing, in one session that exists for the purpose, catches the change
whoever made it. The heartbeat turns that session's own failure from
invisible into one sentence at the next session start.

## Story
In a dependent repository, two standing sessions already watched the trunk,
one refreshing model tables and one publishing rendered pages, while a
switchboard setup step was being offered to every person so that sessions
opened above several repositories would run each one's checks. The offer
came back every session for anyone without a place to record a no. Its
owner judged that sessions opening several repositories are rare, and asked
for the standing jobs to become one maintainer per repository, with a
heartbeat so its death is noticed.

## Install
Add the `maintainer` block to `precedent.json`, write the job prompt at its
`prompt_file`, and start the maintainer from a new session with the prompt
`python3 tools/precedent_heartbeat.py prompt` prints. The SessionStart hook
that reads the heartbeat (`maintainer-heartbeat.sh`) is wired by the engine
for every repository and stays silent until the block exists.

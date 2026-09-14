---
slug:        chief-of-staff
title:       "\"Chief of Staff\" routes the fleet instead of doing the work"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Chief of Staff\", or a scheduled sweep reads the fleet"
gates:       ["reply"]
index_clause: "\"Chief of Staff\" -- what is blocked and what collides; every session a link"
checked_by:  null
defines:     ["Chief of Staff", "the sweeper", "the desk"]
command:     {"Chief of Staff": "Stop and route this: tell you what every open session is blocked on and what is colliding, with a clickable link to each."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "Morgan, 2026-09-14 -- chose it from the options after two wrong rows in a live sweep; strength: decided"
---
## Rule
When the person says **"Chief of Staff"**, read the whole fleet and say what
it is blocked on. Do not start the work.

Three things make the answer worth anything:

1. **Every session named is a clickable link**, `https://claude.ai/code/<session id>`.
   Never a bare identifier, never a title with the link elsewhere, never a
   session mentioned in passing without one.
2. **A row is blocked only if it is blocked NOW** — see the filter below.
3. **Two live sessions sharing a subject is a finding**, reported even when
   neither is blocked.

## Detail
### What counts as blocked, and what does not

**Read the session's STATE, never its prose.** `list_sessions` returns a
`status_bucket` and a `session_status` the platform maintains, and a
`post_turn_summary` the session itself wrote on its last turn. The summary
says *what* a session wants. It never says whether it still wants it: nothing
rewrites it when the person answers, archives the session, or does the thing
it asked for. **On any finished session it is stale by construction.**

So the filter is:

| Signal | Meaning |
|---|---|
| `session_status` is `ARCHIVED` | **Done. Drop the row**, whatever its summary says. |
| `status_bucket` is `COMPLETED` | Done. Drop the row. |
| `status_bucket` is `BLOCKED`, not archived | Blocked. Report it. |
| `needs_action` text | What it wants, once the two above say it is still waiting. |

**Archiving is the person saying they are finished with it**, and it is the
signal they give most often, because it costs one click and no typing.
A session archived while its last turn ended on a question has had that
question answered — in another window, by the person doing the thing, or by
their deciding it did not matter.

**One exception, and state what it is rather than guessing at it:** an
archived session can leave something behind that outlives it — an open pull
request, an unmerged branch, a spawned session still running. That artifact
is the row, named as the artifact. **The dead session is not the row**, and
the fact that its summary asked for something is not evidence the artifact
exists. Go look at the artifact.

### What it does not do

**It does not do the work.** It holds no branch, opens no pull request, and
edits nothing outside its own notes. A Chief of Staff that starts fixing
things is another window with a stale view of the same repository — the
problem it was created for.

**It does not merge on the person's behalf.** A merge authorization is theirs
to give in the session that holds the work ([go-merge](go-merge.md)), and
routing them to the right window to say it is the whole job.

### The sweeper and the desk are two things

**The desk** is the standing session the person talks to. It answers the
phrase, routes, and spawns.

**The sweeper** is a scheduled Routine that wakes the desk to list the fleet,
keep the rows the filter above calls blocked, and notify. **It must wake a
standing session rather than fire a fresh one**: a fresh session fired by a
Routine has none of the session-management tools, so it cannot read the fleet
at all — and it reports the run as succeeded anyway
(https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS.md#g38). It is
deliberately dumb: no memory between firings, no judgment beyond *is this row
blocked on him*. **It exists because nothing pushes.** No session signals
anywhere when it finishes, blocks, or goes idle, and peer messaging does not
reach a cloud session — so the missing piece is a clock, not a signal.

**The notification lives in the desk's prompt, not on the Routine.** A Routine
bound to an existing session is refused notifications; a session can send one
itself. That is the whole reason the two are still described separately.

## Why
Work spreads across many open sessions, and **no session can see another from
the inside.** The costs are three, and only the first is obvious: two sessions
take the same subject and produce two divergent results; a session finishes
holding a question and waits on a person who has no reason to reopen that tab;
a session burns most of its context unattended.

The information to fix all three is already there — the status buckets, the
branch, the repositories, the asks written out in `needs_action`. **Nothing
was reading it.** That is a scheduling problem, not a platform limit.

**The filter is the part that decides whether the report gets read.** A status
report carrying rows the person has already dealt with teaches them to skim it,
and a skimmed report is worth less than none — they will trust it exactly once.

## Story
**Proposed by Morgan on 2026-09-13** and written up at
[spec/CHIEF_OF_STAFF.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CHIEF_OF_STAFF.md)
with the platform capability measured rather than assumed. He held
implementation and left four questions open, the phrase among them.

**What decided it was the first real sweep, on 2026-09-14, getting two rows
wrong in the same way.** Asked for the fleet's state, the session reported
four sessions blocked on him. Two of them he had already finished with and
archived — one where he had decided the question and closed the tab, one where
the thing it asked for was done. Both still carried a `needs_action` line
asking for it, because nothing had rewritten their summaries and nothing ever
will.

He named the fix himself in the same message that authorized the build:
*"make sure on this list it doesn't include Archived items since that means
there's nothing more to do -- unless there is still something pending."* Both
halves are in the filter above, including the exception, which is his.

The wrong rows were not a reading error over a detail. The session had both
state fields in front of it and preferred the free-text summary, because the
summary was more specific and read like a live request. **A stale field and a
live one render identically**, which is the shape this rule exists to stop.

## Install
The sweeper is a Routine on the person's own account, created once — it is not
a file, so nothing here installs it and nothing here can check it exists. What
an adopter gets is this rule and the occasion index entry above, which is
generated.

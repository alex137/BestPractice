---
slug:        chief-of-staff
title:       "\"Chief of Staff\" routes the fleet instead of doing the work"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Chief of Staff\""
gates:       ["reply"]
index_clause: "\"Chief of Staff\" -- on request only; link every blocked session and stray branch"
checked_by:  null
defines:     ["Chief of Staff", "the sweeper", "the desk"]
command:     {"Chief of Staff": "Stop and route this: tell you what every open session is blocked on, what is colliding, and what it has left uncommitted to the routine branch with a verdict on each, all with a clickable link."}
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
4. **Uncommitted work gets a verdict, not just a mention** — merge,
   cherry-pick, or close, whether or not the session behind it is still
   open — see below.

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

### What counts as uncommitted, and what verdict it gets

**A session that produced commits and never got them into the repo's declared
`base_branch`** ([precedent.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/precedent.json)) has lost
that work as surely as a dropped thread, whether or not the session itself is
still open. Sweep every branch in the repos in force — `git log
<base_branch>..<branch>` — and report every one still carrying commits,
alongside the blocked rows, not folded into them.

**Say what changed, not just that something did.** A branch name and a commit
count hand the reader the whole investigation back. Give one or two sentences
from the diff, the date it last moved, and a link — its most recent pull
request, or the branch's own compare view when none exists (say plainly when
no pull request exists rather than implying one — practice
[no-invented-specifics](no-invented-specifics.md)).

**Name the session that produced the branch when the fleet actually says so,
and say plainly when it does not**, rather than guessing which recent session
a branch belongs to. Not every commit traces to a session this account can
see — one authored outside a session is real, uncommitted work too, and is
reported the same way, minus the session link.

**Give every branch a verdict, the same three choices
[very-deep-check](very-deep-check.md)'s own branch pass uses — merge,
cherry-pick, or close.** A name and a link handed back with no
recommendation is the branch's whole investigation handed back too, which is
exactly the report this practice exists to stop giving. Read the diff far
enough to say which one and why, in a sentence.

**A verdict is a recommendation, never an action** — Chief of Staff still
holds no branch and opens no pull request; only the reason moves, same as
"What it does not do" below already requires. Where reading the diff
genuinely cannot settle it — the branch is plainly someone else's mid-flight
work, or merging it would revert a vendored or shared file in a way only the
fuller check catches — say so by name and point at
[very-deep-check](very-deep-check.md)'s own branch pass instead of guessing.
A verdict given without that confidence is worse than none: it teaches the
next read to act on this practice's say-so for exactly the case it cannot
actually vouch for.

### What it does not do

**It does not do the work.** It holds no branch, opens no pull request, and
edits nothing outside its own notes. A Chief of Staff that starts fixing
things is another window with a stale view of the same repository — the
problem it was created for.

**It does not merge on the person's behalf.** A merge authorization is theirs
to give in the session that holds the work ([go-merge](go-merge.md)), and
routing them to the right window to say it is the whole job.

### How far back to read, and why it has to be said

**The listing is paged, it does not end, and the blocked count grows with
every page you read.** Measured 2026-09-14 on one account: 2 non-archived
blocked rows in the first 30, 6 in the first 90, 8 in the first 120, with more
still behind the cursor. **Not because the filter is wrong — because old
sessions are rarely archived.** A session finished long ago, on a question
since overtaken, still reads as BLOCKED forever.

So **a sweep bounded by "read a few pages" reports whatever number it happened
to stop at**, and two sweeps of the same fleet disagree without either being
wrong. That is worse than a wrong number, because nothing on the page says
which one you are holding.

**Bound the sweep by recency, and say the bound out loud**: every non-archived
session updated within the last N days, with N named in the report. Page until
the rows fall outside the window, then stop.

**Seven days, chosen by Morgan on 2026-09-14** — *"yes keep seven days"* —
when the alternative on the table was any other number. It is his default, not
the session's guess, and a different reader's set may want a different one. **The
rule is the naming, not the number**: a report that does not state its window is
wrong however far back it read.

**The long tail is its own finding, not part of the count.** A fleet carrying
dozens of ancient blocked sessions is telling the person to archive, and that
is worth saying once, as a number, separately from the live rows.

### Where it runs, and what it costs

**It runs when the person asks, and only then.** No schedule, no Routine, no
background sweep. A report nobody asked for spends their attention against an
unknown return, and they are the one who knows when they want to look.

**It needs a session that has the session-management tools.** The phrase works
in an ordinary working session. It does **not** work in a fresh session fired
by a Routine, which gets none of those tools and reports the run as succeeded
anyway
(https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS.md#g38).

**Prefer the session you are already in.** A sweep costs its own read of the
fleet — roughly 15,000 tokens per page of thirty, several pages deep — and
that is paid wherever it runs. Waking a dedicated session on top adds that
session's whole context to the bill and buys nothing, because the fleet is
read fresh every time regardless. **Open a separate session for this only when
the one in front of you cannot afford the read**, which is a judgment about
the context you are holding, not a standing arrangement.

## Why
Work spreads across many open sessions, and **no session can see another from
the inside.** The costs are three, and only the first is obvious: two sessions
take the same subject and produce two divergent results; a session finishes
holding a question and waits on a person who has no reason to reopen that tab;
a session burns most of its context unattended.

The information to fix all three is already there — the status buckets, the
branch, the repositories, the asks written out in `needs_action`. **Nothing
was reading it**, and the fix is that somebody can now ask.

**It is asked for rather than scheduled, on Morgan's instruction of
2026-09-14**, after a day of building it the other way: *"I do NOT want
automatic sweeps 4 times a day, nor never automatically; ONLY when I invoke
the session."* The design it replaces argued that the missing piece was a
clock. The missing piece was a command.

**The filter is the part that decides whether the report gets read.** A status
report carrying rows the person has already dealt with teaches them to skim it,
and a skimmed report is worth less than none — they will trust it exactly once.

**Kept on the literal phrase, as a session's own judgment call, when the
2026-09-16 conversation widened several other commands to plain intent.**
A full fleet sweep is exactly the automatic-invocation shape Morgan ruled
out above, so reading "how are my sessions doing" as this command would be
undoing that instruction by another route. Ask when a message plainly
means the fleet sweep and does not say the phrase — the cost of guessing
wrong here is a sweep nobody asked for, not a differently-worded reply.

## Story
**Proposed by Morgan on 2026-09-13** and written up at
[spec/CHIEF_OF_STAFF.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CHIEF_OF_STAFF.md)
with the platform capability measured rather than assumed. He held
implementation and left four questions open, the phrase among them.

**Three corrections landed the same day it was built, and each came from
running it rather than reading it**: the archived filter below, the fact that
a Routine's fresh session has no tools at all, and finally the schedule
itself, which Morgan removed — a sweep happens when he asks for one.

**The first came from the first real sweep, on 2026-09-14, getting two rows
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

**Widened on 2026-09-20 to also surface commits sitting outside the base
branch**, on Morgan's own ask: *"find what recent sessions have done that is
uncommitted to main / precedent-beta-v01 and give me a list including
links... all chief of staff does should be in very deep check too."*
Decision strength: decided — he named the capability, this was not a
proposal he merely didn't object to. The second half of that same request is
why [very-deep-check](very-deep-check.md)'s own live-sessions pass now runs
this sweep too, rather than covering only the half of it visible from `git`
alone.

**Corrected the same day**, before the first real run of the widened rule:
the branch section landed with no verdict, on the reasoning that a verdict
is the expensive read [very-deep-check](very-deep-check.md) already does and
repeating it here would be the "the work" this practice already declines to
do. Morgan disagreed in the next message: *"Chief of staff should also give
verdicts on whether to close them or not (as should very deep check)."*
Decided, not assented. **A verdict was never the work this practice declines
— only acting on one is.** Very deep check's own branch pass already gives a
verdict (`## Detail`, pass 4, "Give every one a verdict: merge it, or close
it with the reason recorded") and always did; nothing there needed to
change. What was wrong was reading "surfacing beats judging" as a reason to
withhold the one line — merge, cherry-pick, or close, and why — that turns a
name and a link into something a person can act on without reopening the
whole investigation themselves.

## Install
The sweeper is a Routine on the person's own account, created once — it is not
a file, so nothing here installs it and nothing here can check it exists. What
an adopter gets is this rule and the occasion index entry above, which is
generated.

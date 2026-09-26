---
slug:        chief-of-staff
title:       "\"Chief of Staff\" routes the fleet instead of doing the work"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Chief of Staff\""
gates:       ["reply"]
index_clause: "on request only; name the window read, link every session"
checked_by:  null
defines:     ["Chief of Staff", "the sweeper", "the desk"]
command:     {"Chief of Staff": "Stop and route this: tell you what every open session is blocked on and what is colliding, with a clickable link to each."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "extended 2026-09-21, Morgan (strength: decided, relayed) --
  after a fleet audit found 110 merged-but-undeleted branches across 9
  repos, he asked for them rendered as filtered branches-page links and
  placed the fleet sweep here, with very-deep-check keeping only its own
  checkout; the repo-set bound on the branch half is the session's
  resolution of a question that decision left open;
  Morgan, 2026-09-14 -- chose it from the options after two wrong rows in
  a live sweep; strength: decided"
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

**It also sweeps the fleet's merged-but-undeleted branches**, in the same
report and under their own heading. That is the practice's existing rule about
artifacts, not a new job: a branch that outlived the session that made it is
named above as exactly the kind of row a dead session leaves behind. Every row
is a one-click delete link, built the one way
[branch-delete-links](branch-delete-links.md) specifies — the mechanism is
there, in full, and is not restated here.

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

### The branch sweep, and the set it reads

**The sessions half of this report is bounded by recency; the branch half is
bounded by REPO SET, and that is the resolution rather than an oversight.** A
branch merged five weeks ago is precisely the one no recent session touches, so
a seven-day window over sessions filters out the exact rows the branch sweep
exists to find. The two halves answer different questions and take different
bounds.

**So: every repository the person owns that carries a Precedent install, with
no recency bound on the branches themselves, and the report names the set it
swept.** Naming the set is how this half honours the rule above — the rule is
the naming, not the number, and a report that does not say what it read is
wrong however far it read. Say the count of repositories swept and say which
ones, the same way the sessions half says its window.

**Order the repositories smallest-count-first and lead with the total**, per
[branch-delete-links](branch-delete-links.md). A hundred-row chore worked from
the smallest repository shrinks visibly; worked from the largest it reads as
homework.

**The unmerged branches go in their own list, never mixed in.** That is
load-bearing rather than tidy, and the practice above says why: a branch with
no merged pull request may be carrying work, and presenting it beside proven
deletions is how the work gets thrown away.

**This stays inside "it does not do the work."** The sweep emits links; the
person clicks them. A Chief of Staff that started deleting branches would be
the second window with a stale view that this practice exists to prevent.

### Where it runs, and what it costs

**It runs when the person asks, and only then.** No schedule, no Routine, no
background sweep. A report nobody asked for spends their attention against an
unknown return, and they are the one who knows when they want to look.

**It needs a session that has the session-management tools.** The phrase works
in an ordinary working session. It does **not** work in a fresh session fired
by a Routine, which gets none of those tools and reports the run as succeeded
anyway
(https://github.com/alex137/BestPractice/blob/staging/record/GOTCHAS.md#g38).

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
[spec/CHIEF_OF_STAFF.md](https://github.com/alex137/BestPractice/blob/staging/spec/CHIEF_OF_STAFF.md)
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

**The branch sweep arrived on 2026-09-21, from the other direction.** A
session auditing every repository Morgan owns for its Precedent install
counted **110 merged-but-undeleted branches across 9 repositories**, the oldest
merged on 2026-08-16 — an artifact class nothing was reading, sitting in plain
sight on nine branch pages. Nobody had asked for it, which is the point: it is
exactly the "artifact that outlived its session" row this practice already
claimed to cover, and the claim had never been exercised.

**He placed the fleet half here and left the per-repo half where it was.**
[very-deep-check](very-deep-check.md) sweeps the checkout it runs in and its own
sources; this sweeps everything. The reason is worth keeping: branch hygiene is
per-repository bookkeeping, not a finding in the seam between two repositories,
so running it across the deep check's whole scope would duplicate this and make
an expensive check more expensive for no new judgment.

**What the placement did not settle was the bound**, and it had to be settled
rather than inherited. This practice's standing rule is that a report names the
window it read — seven days over sessions. Branches are not sessions, and a
seven-day window over them would filter out the rows the sweep is for. The
resolution is in Detail: bound by repository set, and name the set.

## Install
The sweeper is a Routine on the person's own account, created once — it is not
a file, so nothing here installs it and nothing here can check it exists. What
an adopter gets is this rule and the occasion index entry above, which is
generated.

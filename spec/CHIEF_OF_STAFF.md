---
title:         "Chief of Staff: one session that routes the fleet"
kind:          proposal
status:        accepted
opened:        2026-09-13
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       A standing session that reads every other session, says what is blocked and what collides, and spawns work rather than doing it — accepted 2026-09-14; the sweeper Routine and the universal practice are built, the tag namespaces are not.
---
# Chief of Staff: one session that routes the fleet

**Accepted 2026-09-14, and partly built.** Morgan asked for the design on
2026-09-13, held implementation, and authorized the build a day later after
the first real sweep got two rows wrong — see
[What got built](#what-got-built) for what exists now and what still does
not. The measurements below are dated and were taken before the decision;
re-check any of them before relying on it.

## The problem it addresses

Work is spread across many open sessions, and **no session can see any other
one from the inside.** The costs are three, and only the first is obvious:

1. **Duplication.** Two sessions take the same subject and produce two
   divergent results, which is worse than producing it twice.
2. **Silent blocking.** A session finishes, writes *"needs: approve and merge
   this pull request"*, and then nothing happens, because the person has no
   reason to reopen that particular tab.
3. **Unattended spend.** A session with 630,000 tokens of its million-token
   context consumed is a compaction candidate nobody inside it will raise.

`dont-race-another-window` — the rule in Morgan's own practice set — already
says *decline work another window is doing*. It has never had the information it needs to fire. **Chief
of Staff is that information.**

## What the platform actually gives us

Measured 2026-09-13 from a session in this repository, not read from
documentation.

### What a session can already see

`list_sessions` returns, for every session on the account: title, running or
idle, a **status bucket** (`WORKING` / `BLOCKED` / `REVIEW_READY` /
`COMPLETED`), the checked-out branch, the repositories the session was rooted
in, tags, context tokens used against the limit, dollars spent, the parent
session that spawned it, and a **`post_turn_summary`** the sessions are
already writing — with `status_detail` and, crucially, a **`needs_action`**
field naming what the person owes it.

That is a dashboard with nothing left to build. The 25 most recent sessions
on the account, at the moment of measurement, were **3 working, 4 blocked on
a decision, 4 sitting at review-ready, 14 completed** — and the four blocked
ones had their asks already written out: merge these three pull requests,
decide bootstrap-hook versus environment provisioning, delete a merged
branch, settle whether four repositories share one continuous-integration
workflow.

### What it can do

`create_session` (rooted in a named repository, seeded with a prompt, tagged
at creation), `send_message` into an existing session, `set_session_tags` to
retag sessions after the fact, `interrupt_session`, `archive_session`, and
`create_trigger` to wake a named session on a schedule.

### What it cannot do, and this shapes the design

- **Messaging is one-way.** A message goes into a session; the session cannot
  answer back to the sender. So Chief of Staff is a **dispatcher, not a
  conversation hub** — it reads state through `post_turn_summary`, which
  every session updates on every turn, and that is the whole return channel.
- **The tag filter is refused in-session.** `list_sessions` accepts a `tags`
  argument, and calling it from a session returns
  `tags filter is not currently available`. Tags are therefore **read and
  filtered by Chief of Staff itself**, over the full listing. This costs
  nothing at the current fleet size and would need revisiting at hundreds.
- **The listing is paged and partial.** It returned 25 with more behind a
  cursor. A status sweep must page, or say it only read the most recent page.
- **Nothing notifies it when another session changes.** There is no push from
  the fleet: a session that finishes, blocks or goes idle sends no signal
  anywhere. Peer messaging exists but reaches only sessions on the *same
  machine*, and each cloud session is its own container — measured
  2026-09-13 from this session, which found no reachable peer while seven of
  Morgan's sessions were live. **The missing piece is a clock, not a
  signal**: a blocked session is already fully described in the listing, so
  anything that reads the listing on a schedule closes the gap. See
  [What wakes it](#what-wakes-it).

## Reading a row: state, never prose

**This is the part the first real sweep got wrong, and it decides whether the
report is worth reading.** A row carries two kinds of information, and they
age differently.

The platform maintains `status_bucket` and `session_status`. The session
itself writes `post_turn_summary` — including `needs_action` — on its last
turn, and **nothing ever rewrites it.** Not the person answering. Not the
person archiving the session. Not the thing it asked for getting done. So on
any finished session the ask is stale by construction, while still reading as
a live, specific request.

| Signal | Verdict |
|---|---|
| `session_status` is `ARCHIVED` | **Done. Drop the row**, whatever the summary says. |
| `status_bucket` is `COMPLETED` | Done. Drop the row. |
| `status_bucket` is `BLOCKED`, not archived | Blocked. Report it. |
| `needs_action` | What it wants — read only after the two above say it is still waiting. |

**Archiving is how Morgan says he is finished**, and it is the signal he gives
most often: one click, no typing. A session archived on an unanswered question
has had that question answered somewhere he did not have to tell anybody
about.

**The one exception is his**, given in the same message that authorized the
build: *"unless there is still something pending."* An archived session can
leave something behind that outlives it — an open pull request, an unmerged
branch, a spawned session still running. **That artifact is the row, named as
the artifact**, and the dead session's summary asking for something is not
evidence the artifact exists. Go look at it.

The rule is [practices/chief-of-staff.md](../practices/chief-of-staff.md).

## The command

**"Chief of Staff"**, said in any session, means: *stop, and route this.*
The session answers with the fleet's state and what it recommends, and does
not start the work itself.

Said in the Chief of Staff session it is a status request. Said anywhere
else it is a redirect — *this belongs in Chief of Staff, here is the link* —
which is the same shape as
[spawn-session](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/spawn-session.md)'s
honest "this session is the right one" answer.

The phrase is Morgan's, proposed 2026-09-13: *"Maybe the phrase is just
'Chief of Staff'."* It would join
[go-merge](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/go-merge.md),
[park-it](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/park-it.md),
[three-things](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/three-things.md),
[plain-words](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/plain-words.md),
[weak-yes](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/weak-yes.md),
[spawn-session](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/spawn-session.md)
and [my-options](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/my-options.md)
in the universal command vocabulary.

## Every session it names is a clickable link

**This is a hard requirement, not a nicety.** A status report that names a
session by title or by identifier has moved the routing chore back onto the
person — the exact complaint that produced `handoff-only-when-blocked` in Morgan's own
practice set.
The point of a report is that the next action is one click away, in the
window that can actually take it.

The form is `https://claude.ai/code/<session id>`, the same address the
`Claude-Session` trailer already writes into every commit. So:

```markdown
- [Roll the refreshed engine out](https://claude.ai/code/session_XXXX) —
  **blocked on you:** approve the body edit, then merge three pull requests.
```

Never a bare identifier, never a title with the link somewhere else, and
**never a summary that mentions a session without linking it** — including in
passing, including when the same session was linked three lines above.

## The tagging convention

### How tags work, since they are not a Git thing

A tag is **a free-form string on the session record itself**, held by the
Claude Code session service — not in the repository, not in a file, not
related to Git tags. Nothing is committed and nothing appears in a diff.

Three facts worth having (verified 2026-09-13):

- Tags are set **when a session is created**, and edited afterwards on any
  session by identifier. A session can retag sessions it did not create.
- The harness sets some itself: every session on the account currently
  carries `config:auto-create-pr:off`, which is configuration riding in the
  same field.
- **Any session reads every session's tags**, not only the ones it created.
  They come back on every `list_sessions` row, alongside the status bucket and
  the rest — measured from a session that had created none of the 25 it read.
  What is refused in-session is the *filter*, not the values, so a reader
  filters them itself.
- **No interface shows them.** The Claude Code on the web documentation
  describes the session sidebar down to diffs, sharing, archiving and
  filtering for archived sessions, and does not mention tags anywhere.

So a tag is **readable by sessions and invisible to the person**, which makes
the convention worth nothing on its own: the tags already sitting on this
account's sessions have never been read by anything. Chief of Staff is what
turns them back into something Morgan can see.

### The recommended namespaces

Every tag is `namespace:value`, matching the shape the harness already uses.
Four namespaces, and a session carries as many as apply:

| Namespace | Value | What it answers |
|---|---|---|
| `subject:` | a practice slug, an open-item anchor, a pull-request number | **What is this about?** The collision detector — two live sessions sharing a `subject:` is the signal Chief of Staff exists to catch. |
| `repo:` | the short repository name | **Where can it write?** Cross-owner attachment is refused, so this decides what may be routed where before the work starts. |
| `role:` | `cos`, `worker`, `watch` | **What kind of session is this?** Exactly one carries `role:cos`. |
| `wants:` | `merge`, `decision`, `review`, `nothing` | **What does it need from Morgan?** A coarser, more reliable companion to the free-text `needs_action`. |

**`subject:` is the one that earns its keep**, and it is the one that must be
applied at creation rather than retrofitted: a collision is only worth
catching before both sessions have run.

Ad-hoc single-word tags already in use (`item-74`, `todo-closeout`, a practice
slug on its own) are the same idea without the namespace, and would be
retagged as `subject:` values rather than thrown away.

## What wakes it

**The failure this has to solve is a session that went idle holding a
question, touched no repository, and is therefore waiting on a person who
does not know it exists.** Left to the phrase alone, Chief of Staff answers
only when Morgan already suspected something — which is the wrong half of
the problem.

**It is solvable, and the reason is that the session is not actually
invisible.** A session that stops to ask writes its own state before it
stops: `status_bucket: BLOCKED`, and a `needs_action` line naming what it
needs. Four of Morgan's sessions read exactly that way on 2026-09-13, with
their asks already spelled out — *merge these three pull requests*, *decide
bootstrap hook or provisioned environment*. Nothing had read them. **The
information was complete and unattended**, which is a scheduling problem
rather than a platform limit.

**So: a scheduled Routine.** What it may fire is settled by a measurement
taken after this section was written — see
[The fresh-session sweeper does not work](#the-fresh-session-sweeper-does-not-work)
below, which corrects the rest of this paragraph and the table under it.
Every few hours it lists the fleet, keeps the rows blocked on Morgan, and
sends him the links. Routines can deliver push to a phone and email to an
inbox when a run finishes with something worth saying — which reaches him
where he is, rather than in a tab he would have to think to open. **He
currently has none: the account holds no Routine at all** (checked
2026-09-13), so nothing anywhere is reading anything on a clock.

**One constraint decides the shape, and it is worth stating plainly:
notifications are available only to a Routine that starts a FRESH session on
each firing** — the server refuses them for a Routine bound to an existing
session. Chief of Staff, as a standing session Morgan talks to, is bound by
definition. **So the sweep and the desk are two things:**

| | The sweeper | The desk |
|---|---|---|
| What it is | A Routine firing a fresh session on a schedule | The standing Chief of Staff session |
| What it does | Lists the fleet, keeps what is blocked, notifies | Answers "Chief of Staff", routes, spawns |
| Why separate | Only a fresh-session Routine can notify | Only a standing session holds context |
| What it costs | One short session per firing, most returning nothing | Nothing until spoken to |

**The table's "why separate" row is the half that did not survive contact.**
It is kept as written because the reasoning was right about notifications and
wrong about what a fired session can do; the correction follows.

## There is no sweeper: it runs when he asks

**Decided by Morgan on 2026-09-14**, the same day the scheduled version was
built and twice corrected: *"I do NOT want automatic sweeps 4 times a day, nor
never automatically; ONLY when I invoke the session."* The Routine is deleted.
Everything below about firing, notifications and cadence is kept as the record
of how the design got there, and **none of it is in force.**

**What the two failed attempts were actually worth** is the measurement each
forced. The first said a fresh session cannot read the fleet at all. The
second, below, said the count depends entirely on how far you page — which is
the finding that survives the schedule being removed, because it bites just as
hard on a sweep he asks for.

### How far back to read

Measured 2026-09-14, paging one account's own sessions: **2** non-archived
blocked rows in the first 30, **6** in the first 90, **8** in the first 120,
and the listing still had more behind the cursor. The filter was right at every
depth; **old sessions are simply never archived**, so the tail is unbounded.

That is why the first sweep from this session reported one blocked row and the
desk reported six. **Neither used a different method.** One read two pages and
one read further. A sweep that stops at an arbitrary page reports an arbitrary
number, and nothing on the page tells the reader which.

**So a sweep is bounded by recency and names its bound** — non-archived
sessions updated in the last N days, N stated in the report. The ancient
blocked tail is reported once as a count, separately, as a prompt to archive.

## What the fresh-session sweeper proved on its way out

**Measured 2026-09-14, after the design above was approved and built.** A
Routine firing a fresh session gets **none of the session-management tools** —
so the sweeper could not call `list_sessions`, which is the one thing it exists
to do. The test firing completed in 32 seconds, exited 0, and recorded
`SUCCEEDED`; it had done nothing. Neither the run status nor `create_trigger`'s
own warning says this, and the remedy that warning names does not apply: the
`connectors` argument resolves against connected claude.ai connectors, and the
session-management server is the harness's own, not one of those.

**A standing session does have the tools**, confirmed by creating one and
watching it read the fleet. So the built shape is:

- **The desk**, a standing session carrying `role:cos`, which does the sweep.
- **A Routine bound to it** by `persistent_session_id`, waking it on the
  schedule.
- **The notification moved into the prompt.** A persistent-session Routine is
  refused notifications — that constraint above is real — but the desk can send
  one itself with `PushNotification`, which reaches his phone. So the desk is
  no longer optional: it is where the sweep lives.

Full story, and the generalization about a scheduled job's capabilities not
being its scheduler's, at
[record/GOTCHAS.md](../record/GOTCHAS.md#g38).

The sweeper is deliberately dumb and cheap: no memory between firings, no
judgment beyond *is this row blocked on him*. Everything that needs
judgement happens at the desk, when he clicks through.

**What this still will not catch**: a session that is genuinely mid-work and
will need him in an hour. It reads as `WORKING` and should — there is
nothing to report yet.

## What Chief of Staff does not do

**It does not do the work.** It holds no branch, opens no pull request, and
edits nothing outside its own notes. The moment it starts fixing things it is
another window with a stale view of the same repository, and it has become
the problem it was created for.

It also **does not merge anything on Morgan's behalf.** A merge
authorization is his to give in the session that holds the work
([go-merge](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/go-merge.md)),
and routing him to the right window to say it is the whole job.

One asymmetry is deliberate: **only Chief of Staff spawns sessions.** A tree
where any session may spawn any other is how the current fleet got a
five-deep parent chain nobody can read. Making spawning a single session's
privilege is what keeps the tag namespaces honest, since one session applies
them.

## Open questions

1. **Does Chief of Staff live in one repository or above them all?** It must
   name repositories it cannot attach to — cross-owner attachment is refused
   — so it is a reader of the fleet more than of any tree. Rooting it here is
   the obvious default and may be wrong.
2. **How often does the sweeper fire, and does it notify by push, by email or
   both?** The mechanism is settled; the cadence and the channel are a matter
   of how interrupted Morgan wants to be, which is his alone to say.
3. **What happens to the sessions already open?** Retagging the live fleet by
   hand is a one-off cost, and skipping it means the collision detector is
   blind to exactly the sessions most likely to collide.
4. **Is `Chief of Staff` the phrase?** It is longer than the other commands
   and it names a role rather than an action, which is either the point or
   the objection.

## What got built

Built 2026-09-14, on Morgan's authorization:

- **The universal practice**, [practices/chief-of-staff.md](../practices/chief-of-staff.md) —
  the command, the link-every-session requirement, and the state-not-prose
  filter above.
- **Nothing scheduled.** Both Routines built on 2026-09-14 were deleted the
  same day, the first because it could not work and the second because he did
  not want one.
- **A standing desk session** exists, carrying `role:cos`, from the measurement
  that proved a standing session has the tools. It is not required: the phrase
  works in any ordinary working session, and preferring the session already in
  front of you is now the rule, because the fleet is re-read from scratch
  either way and a second session only adds its own context to the bill.

- **The tag namespaces**, [practices/session-tags.md](../practices/session-tags.md) —
  `subject:`, `repo:`, `role:`, `wants:`, applied in the `create_session` call
  and wired into [spawn-session](../practices/spawn-session.md), which is the
  practice that creates sessions. The live fleet was retagged by hand the same
  day, which answers open question 3 below.

**Still not built**, and each needs a decision that is his:

**Open question 2 below — cadence and channel — is answered and closed:** there
is no cadence, because there is no schedule.

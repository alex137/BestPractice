---
slug:        write-it-up
title:       "\"Write it up\" commits a self-contained report on the current issue, with a link"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person asks, in whatever words, for a write-up of the issue or bug being worked"
gates:       []
index_clause: "\"Write it up\" -- commit a full report of the issue and fix, then link it"
checked_by:  null
defines:     ["Write it up"]
command:     {"Write it up": "Write a full report on the issue -- what it is, the context that led to it, and the proposed fix -- for a reader with none of this conversation, commit it to the branch you're on, and give the link."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-18"
approved_by: "Morgan, 2026-09-18. Extended 2026-09-20, on instruction to
  this practice, My options and Prompt Please together: a proposed solution
  that is itself a cross-repo change must account for the upstream template
  it comes from and say whether it needs a clean rollout to the repos
  vendoring this one. Extended again 2026-09-20, same instruction to all
  three commands: when the proposed solution belongs in a different
  session, say the seed root and the repos to attach in plain prose in the
  reply, not only inside a report or block meant for someone else to read."
strength:    decided
---
## Rule
**"Write it up" is the clean form, not the only one** -- "put together a
writeup on this", "document what happened here for whoever picks this up",
and anything else that plainly asks for the same thing get the same
treatment. When a person asks for it, about whatever issue, bug, or
situation is currently in front of the session:

1. Write a report **assuming its reader is a different session or person
   who was not in this conversation** -- so it states, in full, plainly:
   - what the situation or issue is;
   - the context and the sequence of events that led to it;
   - the proposed solution.
   - **when the proposed solution would itself change something this repo
     ships to other repos** -- a practice file, a template, a hook, a
     vendored engine file, the same scope
     [vendor-rollout-disclosed](vendor-rollout-disclosed.md) already names
     -- the original template or mechanism in the upstream repo that
     organizes those other repos, not just the symptom in the repo the
     report was written in, and whether the fix needs a clean rollout
     through an updated template and
     [vendor-update-runbook](vendor-update-runbook.md)'s mechanism to reach
     them, when that's relevant.

   Put in everything that reader would need and nothing they'd have to ask
   a second time for. This is the opposite of a terse summary: completeness
   is the point, not brevity.
2. Commit that report as a file into the repository and branch the session
   is currently working in -- never a separate report-tracking repo -- and
   push it there.
3. Give the person the link to the committed file on that branch.
4. **When the proposed solution needs a repository this session cannot
   reach, or plainly belongs in a different session**, say so in the reply
   itself, separate from the committed report and not fenced: which
   repository has to be the primary seed root for that session, and which
   others, if any, need to be attached alongside it -- *"Open a new
   session, root it in \<repository\>, attaching \<repositories, or
   'none'\>."* The report is the durable record; this sentence is what
   gets the person moving on it now.

## Detail
**Where the file goes** follows whatever convention the repo already has
for this kind of document (a `reports/` directory, or wherever else
write-ups already live); absent one, a plainly named file at the repo root
is fine. Name it for the issue, not for the date or for "report" --
[no-version-suffix](no-version-suffix.md).

**The push is part of the command, not a separate ask.** "Write it up"
authorizes committing and pushing the report to the branch already in use,
the same way [go-merge](go-merge.md) authorizes its own chain -- the person
should not have to be asked a second time whether the file they just asked
for should actually be saved. It does **not** by itself authorize opening a
pull request or merging anything; where the branch reaches its target only
through a reviewed PR, the report sits on the branch, pushed, linked, and
waiting there like any other commit, unless the person separately says
[go-merge](go-merge.md) or names the same intent.

**The report is the deliverable, not a chat summary of it.** A reply that
describes what the report says instead of linking to the committed file has
not done this.

**Where this differs from [Prompt Please](prompt-please.md).** That command
is smaller and never committed -- a paste-ready prompt for a new session,
built around a recommendation rather than a durable record. Reach for
`Write it up` when the issue needs a file that outlives this conversation;
reach for `Prompt Please` when all that's needed is to hand the next step to
a session that can act on it now. Nothing stops using both on the same
issue: write it up for the record, then ask for `Prompt Please` to actually
carry the next step elsewhere.

## Why
The whole reason to ask for this is to hand a problem to someone (or some
session) who wasn't there for the conversation that found it -- so the
report has to stand on its own. A chat reply doesn't survive past its
thread ([repo-is-memory](repo-is-memory.md)); a file on the branch does,
and is the thing that can actually be handed off or pointed at.

## Story
Coined by Morgan, 2026-09-18: a standing phrase for something he was typing
out in full each time -- write up the bug/issue with its context and a
proposed fix, assuming zero shared context, commit it, and give the link --
rather than re-describing the request whenever he needed it.

**Cross-referenced against [Prompt Please](prompt-please.md), 2026-09-20**,
when Morgan coined that command and drew the boundary himself: this command
is bigger and formally committed to GitHub; `Prompt Please` is smaller, and
just a prompt.

**Extended the same day**, on Morgan's instruction to this practice,
[My options](my-options.md) and [Prompt Please](prompt-please.md)
together: *"Any change that would effect other repos must take into
account the original templates in the mother system that organizes the
other repos, and must be rolled out cleanly in updated templates/migrations
to the others (if relevant)."* BestPractice is that mother system for
every repo it vendors this layer to, so this stays in the same
repo-agnostic form [vendor-rollout-disclosed](vendor-rollout-disclosed.md)
already fixed on -- "the repos vendoring this one," not the repo's own
name -- so it still reads correctly once vendored into one of them.
Strength: decided.

**Extended again the same day**, on the same instruction to all three
commands -- full quote in [Prompt Please](prompt-please.md)'s Story, where
the gap actually surfaced. `Write it up`'s own deliverable stays on this
branch, but its proposed solution can still point at work that belongs
elsewhere, and that routing was missing here the same way it was missing
from the other two. Strength: decided.

## Install
No mechanical check: like [go-merge](go-merge.md), whether a given reply
correctly recognized the request is a judgment about the conversation, not
a property a script can see in the resulting diff.

---
slug:        spawn-session
title:       "Check whether the work belongs in another session before starting it, and hand over a seeded link"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "handing the person work to do, creating a session, or starting work that may touch a repository this session cannot reach"
gates:       ["reply"]
index_clause: "cross-repo check; list_sessions before spawning; wake, never spawn beside"
checked_by:  null
defines:     ["Spawn session"]
command:     {"Spawn session": "Check whether this work belongs in a different conversation — usually because it needs a project this one cannot reach — and hand you a link to that one, ready to go."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-11"
approved_by: "Morgan, 2026-09-11 -- coined and placed at universal in the same message;
  extended 2026-09-12, Morgan F, relayed through a scheduled instruction to land five
  fleet rules at universal -- the cross-owner wall with its who-merges half, and waking
  a live session before creating a new one. Placing them at universal is his; that these
  two belong in this practice rather than in new ones was the session's judgment, named
  as a judgement call in that same instruction. Amended 2026-09-13, Morgan -- he raised
  the ordering himself and approved the three changes that carry it: the index clause,
  the deferral, and the mechanism. Amended again 2026-09-13, Morgan -- a spawned
  session carries the merge authorization: \"If I ask for that spawned session, I'd
  want it merged.\" Clarified 2026-09-13, Morgan -- \"if session spawn is explicitly
  asked with a go merge, then the go merge should be brought into the new session,
  too\" Amended 2026-09-13 again, on a duplicate spawn reported from an
  individual set that had just closed the same gap in its own catalogue -- the
  enumeration is the session's judgement, the level follows rule-level-by-reach, and
  neither was put to him."
strength:    decided
source_practice_number: null
---
## Rule
**Before starting the work you were just asked for, check whether it belongs
in a different session — and check the repositories first.** Name the
repositories the work has to read, write or push to, and compare that list
against the ones this session actually holds. Everything else that might
argue for a fresh session — a poisoned context, a different branch, a long
run you do not want to block on — comes after that, because a missing
repository is the one this session cannot fix from the inside.

**Compare OWNERS, not just repository names.** A session already holding one
owner's repositories is refused another owner's outright — `add_repo` answers
*"cross-tier adds are not supported in v1"* — and the session's initial source
itself counts as "already has repos", so no ordering of calls inside that
session helps. The full message names both sides, which is what makes it
recognisable: *"cross-tier adds are not supported in v1: requested
`<other>/<repo>` but session already has repos from owner(s) [`<this>`]"*.

**Plan for the refusal; do not plan *on* it.** Upstream's own record has it
refused three times, including as a session's very first tool call, alongside
two sessions that held both owners at once — with no explanation fitting both
([the gotchas index](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md#build-environment-gotchas--do-not-rediscover-these), in full in
[record/GOTCHAS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS.md), with the contradictory sequence itself in
[the archive](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS_ARCHIVE.md)). **Call it and read what it says, never a
remembered result.**

**Settle who merges before the work starts.** This is the half that bites
late. A session that cannot attach across owners cannot gain push access
there either, so it can open nothing and land nothing in that repository —
and a finished pull request with nobody able to merge it is a discovery made
at the end, when the work is already spent. Name whoever will land it at the
same moment you name the repositories.

**Where a different session is needed, wake a live one before creating a new
one.** A message into an existing session reuses the context it already
holds; a new session re-reads its repository from scratch, which is most of
what a session costs
([session-spend-follows-the-task](session-spend-follows-the-task.md)). Create
a fresh one when no live session holds the right repository, or when the
context in the live one is itself the problem.

**Enumerate before you create, every time: `list_sessions`, matched on the
target repository.** "Wake a live one first" is not a preference to weigh --
it is a call to make, and a session that never looked satisfies the sentence
above exactly while still spawning a duplicate. **Having established that
this session cannot do the work is necessary and not sufficient**; the second
question is whether the work is already being done, and only the two answers
together license a new session.

**A session already on the work that is BLOCKED is the case to look for, not
the case to route around.** It is stuck waiting for something -- a decision,
an answer, a permission -- and what it needs is that answer delivered, not a
sibling starting the same job from nothing. Send it the thing it is waiting
on. A second session there does not unblock the first; it pays the whole
read-in again and then collides.

**The check can only happen here, at spawn time.** A session spawned into a
repository this one could not attach cannot enumerate that repository's
sessions either, so the burden does not pass downstream -- there is no later
moment at which it can be done. The spawner is the only party that can look.

**A spawned session CAN report back, and this rule said for a day that it
could not.** Corrected 2026-09-13, by a spawned session doing it: it reached
its spawner with `create_trigger` carrying `persistent_session_id`, which
fires into a named session in the same account. What is true is narrower --
**peer messaging does not reach a cloud session**: `ListAgents` does not list
one, so `SendMessage` cannot address it. The trigger route is the one that
works, and nothing had written it down.

**So the return path is a thing you build, not a thing you have.** A spawned
session only knows where to send its answer if the seeded prompt told it --
which makes [seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md)
load-bearing rather than courteous: the session id it requires *is* the
return address. A prompt that names no origin strands its session exactly as
this rule wrongly claimed all of them were stranded.

**Waking still beats spawning**, on the context argument alone: a live
session reuses what it already holds where a new one re-reads its repository
from nothing. That reason was always the real one.

**Where no live session fits, and only then: do not start the work and do
not describe the handoff. Create the session** — rooted in the right repository,
already carrying the prompt you would have given it — **and put its link
near the top of the reply, on its own line, telling the person plainly to
click it.**

**The seeded prompt carries the merge authorization, and says so in those
words.** Work the person asked for is work they want landed; a session
spawned to do it that stops at a finished branch and waits to be told to
merge hands them back the decision they already made, in a window they have
to go find. So the prompt you seed ends with an explicit `Go merge` for the
work it describes, naming who authorized it and when, and quoting them if
you have their words ([seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md)
governs that header either way).

**`Spawn session` and `Go merge` in the same message is the unambiguous
case, and the phrase travels.** When the person says both -- or `Approved`,
which is the same command ([go-merge](go-merge.md)) -- the authorization they
just gave is for the work, and the work is about to move to a session they
are not typing in. So it moves with it: the seeded prompt carries the
`Go merge` verbatim, quoted and attributed, and the spawned session merges
without coming back to ask. **Leaving it behind is the failure** -- it strands
an authorization in the window where the work no longer is, and hands them
back a decision they made in the same breath as asking for the session.

**Three bounds on it, and they are what make it safe to relay.** The
authorization covers **the seeded work only** -- not whatever the spawned
session decides to do next, and not a second merge after it. It names **the
branch that repository's own rules say routine work lands on**, never a
branch behind review or a release branch: a restriction the destination
repository declares is not something a relayed phrase can lift, exactly as
[go-merge](go-merge.md) already says. And it is **conditional on that
repository's own checks passing** -- the seeded prompt says which ones, so
the receiving session does not have to guess.

**Where you did NOT get the authorization, say that instead of inventing
it.** A seeded prompt claiming a person approved something they did not is
the failure
[seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md) was
written out of. If the work was your idea rather than theirs, seed it as
work to do and stop before the merge.

**The check is unconditional.** It runs whenever another repository might be
involved, whether or not anyone says anything. **"Spawn session" is the
explicit command** for the times it did not: it means *run that check now,
say what it found, and hand me the link* — including when the honest answer
is "this session is the right one", which is said in one line and then the
work continues.

## Detail
**Cross-repository is first because it is the one that gets discovered too
late.** A session learns it cannot reach a repository at the moment it tries
to write there, which is after the reading, the reasoning and the context
that would have made the work cheap — and none of that moves to the session
that *can* write. Worse, some of it cannot be repaired mid-flight at all:
`add_repo` has refused a cross-owner attach
([recorded upstream](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md#build-environment-gotchas--do-not-rediscover-these)), so a session rooted under one owner
may simply never reach the other's repositories for its whole life.

**What "create the session" means concretely, as of 2026-09-11.** Where the
harness offers a session-creating tool — in Claude Code's cloud sessions
that is `create_session` on the `claude-code-remote` server — call it with
the target repository as the source and the whole handoff as the prompt, and
the link is the returned session's `https://claude.ai/code/<session id>`
page. **Where no such tool is available, say so and fall back to
[handoff-is-pasteable](handoff-is-pasteable.md)'s paste block** — one or the
other, never silence and never a prose description of what the person should
go type.

**How to wake one, in Claude Code's cloud sessions as of 2026-09-13.**
`ListAgents` lists what is reachable — subagents, other local sessions,
sessions in the cloud where this one has cloud access — and **the name in
that listing is the address**, passed straight to `SendMessage` as `to`. The
message arrives in that session's conversation at its next tool round. For a
session `ListAgents` cannot see — one spawned with `create_session` has been
recorded as unreachable that way — go by session id instead: `create_trigger`
with `persistent_session_id`, then `fire_trigger` to deliver it now rather
than on a schedule. **Permission boundaries are per-session**, so work
refused here is never work to ask a peer for; that routes back to the person.

**Finding the live session to wake is by TITLE, not by tag.** `list_sessions`
accepts a `tags` filter and it does not work from inside a session — it
answers *"tags filter is not currently available"* (checked 2026-09-12, in
Claude Code's cloud sessions). So a session's **title** is the only lineage a
later session can actually search on, which makes naming a session for its
subject at creation worth the one extra call: an untitled session is one
nobody will find to wake, and the cost of not finding it is a fresh session
re-reading the repository from scratch.

**What the relayed authorization looks like in the prompt.** One line, at
the end, after the outcome expected: *"<Person> authorized this on <date>:
'<their words>'. When <the repo's check> passes, Go merge into <branch> --
do not ask again."* The named check and the named branch are what stop it
being a blank cheque, and both are knowable before you seed: the destination
repository declares them.

**The seeded prompt is a handoff, and
[handoff-is-pasteable](handoff-is-pasteable.md) governs its contents
unchanged**: the session opening that link cannot see this conversation, so
the prompt names the branch, the files, the command and the outcome
expected, and ends with the line to paste back here when it is done. One
session per destination repository, keyed by the repository's name — never
by an ordinal.

**And it opens by naming THIS session —
[seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md): the
sending session's title and id, a link to it, and that software rather than a
person wrote the message.** Naming the sending *repository* is not this, and
is what a session reaches for instead when the rule is not in front of it —
*"from a session rooted in `<repo>`"* tells the reader nothing they can open.
The id and the link are knowable: ask the harness for this session's own id.

**Say what the new session will do before the link.** The person is
authorizing it by clicking, and a link with no sentence attached asks them
to authorize something they cannot see.

**Do not spawn a session for work this session can do, and establish the
verdict rather than inferring it.** The check is a probe, not a hunch: try
the attach, or `git push --dry-run` against the repository, and quote what
came back. *"I am probably not allowed"* is not a finding, and neither is
*"this session looks like it is ending"* — both hand the person back a job
they asked for. Every clean session costs them a tab, a fresh context and a
re-read, so the handoff is normally **partial**: whatever this session can
finish, it finishes here, and only the residue is seeded into the link.

## Why
The cost being avoided is not confusion, it is re-derivation. A session that
works for an hour and then finds the repository out of reach has produced
context, not work, and context is exactly the thing a handoff cannot carry.
Checking first costs one comparison of two lists.

**A click is better than a paste where a click is available**, and that is
the whole delta over [handoff-is-pasteable](handoff-is-pasteable.md). That
rule already says the person is the transport and their load should be a
block of text rather than a task to reconstruct; this one says that when the
harness can create the session directly, their load should be a link rather
than a block of text — the paste block stays as the fallback, not as the
target.

**The command exists because the check is a session's job and the person is
the one who notices it was skipped.** Naming the phrase gives them two words
to force it, instead of explaining the whole thing again in the session where
it matters.

The return path is still [findings-return-through-repo](findings-return-through-repo.md)'s:
a spawned session cannot message this one back, so whatever it learns goes
into its repository, and the person carries one line saying it worked or what
broke.

## Story
**Coined by Morgan, 2026-09-11**, in his own words: *"When you give me what I
need to do, first look to see if it should be in a different session, and
that includes most importantly checking for cross repo issues first. Then, if
that is needed, then you should create a link to the new session, rooted in
the right repo, and already seeded with the prompt you want to give it, and
telling me prominently to click on it."* He asked for both halves in the same
message — the standing behaviour and the phrase: *"You should do this always,
whenever a new repo might be needed, but also have the explicit command for
when you don't."*

**The failures it is built on are all already in upstream's own record**
([its gotchas section](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md#build-environment-gotchas--do-not-rediscover-these)).
`add_repo` has refused a cross-owner attach repeatedly, including as a
session's very first tool call, which is what forces work spanning two owners
to be split across sessions at all. A session ran most of a working day here
with no individual practice source resolved, applying the wrong rules the
whole time and unable to tell. And when the handoffs that condition produces
were finally standardized on 2026-09-10, the rule failed on its first real
use: three paste blocks, correctly headed by repository, were read by their
ordinals instead, and one session spent its entire turn proving that another
session's files did not exist.

Every one of those is downstream of the same moment — the moment a session
starts work whose repository it does not have. **Nothing before this checked
that moment**; the catalogue's rules all began after it had already passed.

**The owner wall and the wake-first step were added 2026-09-12**, each from
its own failure. The cross-owner refusal was hit again that day, in the
direction opposite to the one already recorded here — and hit first-hand by
the session that wrote this paragraph, whose `add_repo` for another owner's
repository was refused with exactly the message quoted above. What that
session could *not* do is the point: it had to verify a private source's
behaviour through a clone it already had on disk, because the attach it
wanted was never going to be granted. **Who merges is the same wall one step
later**, and reported from a team source the same day: work finished in a
session that could never land it.

The wake-first step comes from the opposite waste — reported, not measured
here: three sessions created against one repository for work one session
could have done in sequence, each paying to read that repository from
scratch.

**The wake-first step was written down on 2026-09-12 and could not be read.**
Morgan raised it himself on 2026-09-13, unprompted and without having seen
the paragraph: *"maybe (DESPITE THE NAME) we have that command FIRST see if
it makes more sense (token & context-wise) to instead add that message to an
existing session."* The rule already said exactly that. What it did not do
was carry it anywhere a session looks: the generated index clause named only
the cross-repository check and the link, so a session that never opened this
file never learned the step existed — **the same failure
[go-merge](go-merge.md) records, an answer sitting in a file nobody fetched.**
Two further gaps came out with it. The rule said *wake a live one* and named
no tool to do it with, so the instruction had no mechanism; and the paragraph
after it opened flat with *"If a different session is needed ... Create the
session"*, so a reader who did get that far was left on the word "create".
Fixed together: the clause now names waking, the create paragraph defers to
the wake-first one in its first clause, and the Detail names the calls.

**The seeded merge authorization was added 2026-09-13, on Morgan noticing
the symptom rather than the rule**: *"to spawned sessions - they all seem to
manually require my approval to merge, can we add in a go merge there? If I
ask for that spawned session, I'd want it merged (or is there a reason not to
do that?)."* The reason not to, asked for and answered: none that survives
the three bounds in the Rule. The one real objection is that a relayed
authorization is software asserting what a person said, which is the exact
thing [seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md)
exists to police -- so the bounds are what that rule would ask for anyway,
named work, a named branch and a named check, rather than a bare "he said
merge it". Unbounded, it would be a session spawning a session that merges
whatever it likes into whatever branch it finds.

**The enumeration clause came from a duplicate spawn on 2026-09-13**, and
what makes it worth a rule is that **both rules that should have caught it
were fully satisfied at the moment of the mistake.** A session rooted in an
individual practice set was asked to roll a change out to several
repositories, was refused `add_repo` with `access: "push"` for them, and
spawned a session for one of those repositories -- which is exactly what this
practice and that set's own handoff rule both tell it to do. Three sessions
were already live against that repository. One of them held the pull request
for the very mechanism being spawned for, and was BLOCKED waiting on a
decision the person had given in the spawning window minutes earlier. The
right action was one message naming that session; a fourth was created
instead.

**A rule you can obey exactly and still cause the failure is missing a
clause, not being ignored.** The handoff rule gated on what the spawning
session had established it could not do -- true, and checked. This practice
gated on waking being *preferable* -- agreed with, and never acted on,
because nothing said to look. Neither asked whether the work was already
being done, so neither could have fired.

The duplicate was caught minutes in and cost little; the session it
duplicated had already spent an order of magnitude more, and several sessions
were running against that one repository concurrently under an account-level
rate limit already warning. **The waste is not the duplicate's own spend --
it is the read-in a blocked session had already paid for and a new one pays
again**, which is the same argument the wake-first clause above was always
making, left to the session's discretion until it wasn't.

**The two-phrase case was clarified 2026-09-13, on Morgan's instruction**, a
few hours after the clause above landed: *"if session spawn is explicitly
asked with a go merge, then the go merge should be brought into the new
session, too."* The general clause already implied it, and implying it was
not enough -- the reading it has to beat is that `Go merge` applies to
whatever this session is holding, and the spawned work is by definition not
that. Said in one message with the spawn, the authorization is plainly about
the work being spawned for, so it travels rather than expiring in the window
where the work has just left.

**Prior art, and deliberately not copied:** the individual set
`themorgan/precedent-individual` closed the same gap in its own catalogue
first, amending its handoff and no-racing rules. Its wording is first-person
and describes one person's way of working, so lifting it would bind every
adopter to that workflow ([rule-level-by-reach](rule-level-by-reach.md) cuts
against the lift even where it argues for the level). **The MECHANISM is what
generalises** -- enumerate the target repository's sessions before creating
one, and route to a blocked session rather than spawning beside it -- and
that is what is written above, in this catalogue's own register.

**The routing was the real failure the first time round**, and this amendment
assumes the same. A clause about spawning that no session reads unless it has
already opened this file has not landed, so the `occasion` and the
`index_clause` both name creating a session and the check by name -- not just
the cross-repository question that used to be the only way in.

**Renaming it again was considered and rejected.** The name undersells the
rule — the check's first answer is now "wake something", not "spawn
something" — but it had been renamed once already the day before, and the
index clause, not the name, is what a session actually reads.

**It was called `clean-session` for its first day.** Morgan renamed it on
2026-09-12 — *"Let's rename 'clean session' to 'spawn session'"* — and asked
for nothing else about it changed. He gave no reason and none was needed: the
new phrase names what the command does, where the old one named a property of
the destination that the person saying it cannot check from where they are
standing. The rule, the gate and the routing are untouched; only the words
moved.

## Install
Nothing to configure. The occasion index entry above is generated, so an
adopter installs nothing and every session reads the phrase whether or not
any private source resolved.

No mechanical check, and the reason is the same one
[go-merge](go-merge.md) records: this governs what a session does *before*
it touches the tree, and a session that skipped the check leaves behind
exactly what a session that ran it and found nothing leaves behind — the
work, committed normally. The one artifact it produces, a link in a chat
reply, is not in the repository either. What a repository *can* check is
downstream and already covered by
[handoff-is-pasteable](handoff-is-pasteable.md)'s own gate.

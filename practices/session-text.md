---
slug:        session-text
title:       "Check whether the work belongs in another session before starting it, and hand over copy-pasteable text for a window you open yourself -- never a session this one creates"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "handing the person work to do, or starting work that may touch a repository this session cannot reach"
gates:       ["reply"]
index_clause: "cross-repo check; wake, never create -- hand over paste text instead"
checked_by:  null
defines:     ["Session Text"]
command:     {"Session Text": "Check whether this work belongs in a different conversation — usually because it needs a project this one cannot reach — and, instead of creating that session itself, tell you to open a new window, name the repositories it needs to be seeded with, and give you the opening text in a copy-pasteable block."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-11"
approved_by: "Morgan, 2026-09-15 -- renamed from `Spawn session` to `Session Text` and the
  create_session mechanism retired outright: \"your spawned sessions get everything
  rejected for not being seen as safe... STOP spawning sessions; I need to wait...
  until we figure out how to tell Cloud your spawns are safe.\" He asked for both
  halves in the same message -- the standing instruction never to call
  create_session for this again, and the replacement phrase: tell him to open a
  new window, name the repositories to seed it with, and hand him the opening text
  in a copy-pasteable block. Waking an already-live session is unaffected -- that
  is a message into a session that already exists, not a new one this session
  creates, and it was never the thing getting rejected.
  Morgan, 2026-09-11 -- coined and placed at universal in the same message;
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
  neither was put to him. AMENDED 2026-09-13, later the same day, after the
  harness refused to let a session relay a merge into a spawned one and Morgan
  was asked whether it should be able to: he set the DEFAULT the other way --
  \"by default you don't; only if I explicitly tell you to spawn a session and
  go merge. If I only saw 'spawn session' then assume I need to manually
  approve the merge.\" (strength: decided). The both-phrases case is unchanged;
  what changed is what silence means. Amended 2026-09-14, Morgan -- every session
  spawned or woken is listed again, with its link, in the reply's closing list:
  \"make sure that list always includes sessions you've spawned and the links to
  them, so I can see there that they were spawned and I can keep my eye on them.\"
  Amended 2026-09-14, Morgan -- the who-merges half gets a mechanism, after a
  Chief of Staff sweep surfaced the four-day-blocked session that the sentence
  alone had not saved: \"I also want to make a change so that issue doesn't
  happen again, fix the tempalte or whatever in precedent\" (strength: decided).
  That the mechanism is a session-start probe, and that the existing
  can_land_here moves down into a vendored file so it reaches adopters at all,
  were the session's judgement -- he asked for the outcome, not the shape.
  Amended 2026-09-15, Morgan, after a container that had been baking `Go
  merge` into spawned sessions' seeded prompts started hitting the harness's
  own classifier -- \"maybe we remove that BUT we have it say very very
  prominent, bold capitalized, that I need to manually say to merge it,\"
  confirmed with \"Yes, do both\" once the default above was shown to already
  cover the removal half (strength: decided)."
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

**Since 2026-09-14 the session tells you this before your first turn, and you
do not have to remember to ask.**
[tools/precedent_access_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_access_check.py)
runs from the session-start hook and prints, per repo in force, whether this
session can push to it: `LAND`, `HANDOFF`, or `UNKNOWN`. It is a real
`git push --dry-run`, so a `HANDOFF` line is a quotable refusal and satisfies
the "establish it, never infer it" test below on its own.

**Read `UNKNOWN` as unanswered, never as refused.** It means the probe could
not reach the server — a network blip, not a permission verdict — and treating
it as a wall sends you to spawn a session you did not need.

**What made this worth a mechanism rather than a firmer sentence**: on
2026-09-10 a session rooted in a private practice set migrated twelve
repositories and built a seven-commit patch for `alex137/BestPractice` that it
could not push. It sat blocked for four days on *"root session at
alex137/BestPractice to land the team-set declaration in precedent.json"*,
having spent about a hundred dollars to reach a branch nobody could land. This
rule was already in force and already correct. **The session most likely to
skip a practice file is the one already deep enough in the work for this to
cost the most**, so the question moved to the one moment nobody has to choose
to visit.

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

**Never call `create_session` (or spawn a background agent) to hand off
work to a repository this session cannot reach — not since 2026-09-15.**
Sessions this session created were coming back rejected, not seen as safe,
and the fix is not a smarter retry: the mechanism is retired for this
purpose, unconditionally, until that changes.

**Where no live session fits, and only then: do not start the work and do
not describe the handoff. Produce Session Text instead** — tell the person
plainly, near the top of the reply, to open a new window; name the exact
repository or repositories it needs to be seeded with; and give the opening
text as one copy-pasteable block, per
[the-boildown](the-boildown.md). There is no link to click
and no session id yet — the window doesn't exist until they open it and
paste the text in.

**Then name it again at the end, in whatever closing list of outstanding
items the reply carries — one line per handoff, saying what it was for.**
This holds for a session you woke as much as text you handed over, and
whether the person asked for it or you decided on it yourself. The mention
at the top is for someone reading the whole reply; the closing list is for
someone reading only the end, **and that is most people most of the time.**
A long reply buries it in its own middle, and a handoff nobody can find
again is one nobody acts on — which is the one thing this owes, since the
person is the one who has to go open the window. Say in the line what the
work was, so the list reads without scrolling back up.

**The pasted text carries a merge authorization only when the person gave
one for the handoff.** The default is the other way round: text handed over
off `Session Text` alone, or off an ordinary request, stops at the pull
request and says whose call the merge is. Morgan, 2026-09-13, setting this
default in his own words, of the mechanism this rule used before it was a
paste block -- *"by default you don't; only if I explicitly tell you to
spawn a session and go merge. If I only saw 'spawn session' then assume I
need to manually approve the merge."* The same default holds now: naming
the handoff alone is not naming the merge.

**Say the default boundary out loud in the pasted text, not just by its
absence.** A block that simply never mentions merging still reads as
ambiguous to whoever opens the new window and pastes it in, rather than as a
bounded stop. The default-case text states it directly:

> **DO NOT MERGE — STOP AT THE PULL REQUEST. Wait for the word "Go merge"
> in this session before merging.**

This earns its place even now that the text is always something a person
reads and pastes themselves, never something handed to an automated
`create_session` call -- the ambiguity it closes is theirs, at the moment
they decide whether to type `Go merge` into the window they just opened. It
is also part of why `create_session` is gone from this practice at all:
[record/GOTCHAS.md#g43](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS.md#g43)
found the harness's own permission classifier refusing a `create_session`
call outright over a baked-in merge instruction, `[Merge Without Review]` --
one data point among the ones that led to retiring the automated route
rather than trying to word around it.

**Why the opposite reading is tempting and wrong.** Work somebody asked for
is usually work they want landed, so a stop at a finished branch looks like
handing them back a decision they already made. But asking for a handoff is
not the same act as authorizing a merge in it, and a relayed authorization
is the one thing the person cannot take back once it has left the window
they typed in. **When they meant both, they say both** -- which is the next
paragraph, and it is the only shape that carries.

**`Session Text` and `Go merge` in the same message is the unambiguous
case, and the phrase travels.** When the person says both -- or `Approved`,
which is the same command ([go-merge](go-merge.md)) -- the authorization they
just gave is for the work, and the work is about to move to a window they
are not typing in yet. So it moves with it: the pasted text carries the
`Go merge` verbatim, quoted and attributed, and the session they open by
pasting it in merges without coming back to ask. **Leaving it behind is the
failure** -- it strands an authorization in the window where the work no
longer is, and hands them back a decision they made in the same breath as
asking for the handoff.

**Three bounds on it, and they are what make it safe to relay.** The
authorization covers **the handed-off work only** -- not whatever the
opened session decides to do next, and not a second merge after it. It
names **the branch that repository's own rules say routine work lands on**,
never a branch behind review or a release branch: a restriction the
destination repository declares is not something a relayed phrase can lift,
exactly as [go-merge](go-merge.md) already says. And it is **conditional on
that repository's own checks passing** -- the pasted text says which ones,
so the session that opens it does not have to guess.

**A repository wall is not a permission refusal, and only one of the two
stops you relaying.** A session that cannot reach another owner's repository
has hit a **capability** boundary -- `add_repo` answering *"cross-tier adds
are not supported in v1"*, or the git proxy refusing to inject a credential
for a repository outside the session's authorized set. That is the case this
rule exists for: the person authorized the work, and the only thing missing
is a session that can reach the repository. **Relay it.** A **permission
refusal** is the other thing entirely -- the person declined, or the tool
governing this session blocked the action itself -- and there the answer is
to go back to the person, never to find a session that will do it instead.
Generic harness guidance against *asking a peer to do what was blocked in
your session* is aimed at the second; **reading it onto the first turns
every cross-owner handoff into a manual paste** and spends the person a
round trip for nothing. Ask which kind of block you hit before you decide.

Cost, 2026-09-14: a session holding a merge authorization, with a live
session already blocked and waiting for exactly that authorization, handed
the person a paste block instead and called the relay permission laundering.
Nobody's decision was being routed around -- the person had given the
authorization in the message immediately before. **The tell is whether a
human said no.** If nobody did, a wall is just a wall.

**Whether the receiving session can ACT on the relayed authorization is
not the sender's call, and since 2026-09-14 it has an answer:
[relayed-authorization](relayed-authorization.md).** The receiver acts only
where the authorizing person's own `identity.json` declares that they accept
relays; otherwise it does the work, opens the pull request and stops. **Relay
it either way** -- an authorization that arrives with the work is what lets
the receiver merge the moment the declaration allows it, and where it does
not, the person is approving something already finished rather than
re-explaining it. What the sender owes is the envelope that rule names: this
session's id and link, the words verbatim, the date, and the three bounds
above.

**Where you did NOT get the authorization, say that instead of inventing
it.** A seeded prompt claiming a person approved something they did not is
the failure
[seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md) was
written out of. If the work was your idea rather than theirs, seed it as
work to do and stop before the merge.

**The check is unconditional.** It runs whenever another repository might be
involved, whether or not anyone says anything. **"Session Text" is the
explicit command** for the times it did not: it means *run that check now,
say what it found, and give me the paste block* — including when the honest
answer is "this session is the right one", which is said in one line and
then the work continues.

## Detail
**Cross-repository is first because it is the one that gets discovered too
late.** A session learns it cannot reach a repository at the moment it tries
to write there, which is after the reading, the reasoning and the context
that would have made the work cheap — and none of that moves to the session
that *can* write. Worse, some of it cannot be repaired mid-flight at all:
`add_repo` has refused a cross-owner attach
([recorded upstream](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md#build-environment-gotchas--do-not-rediscover-these)), so a session rooted under one owner
may simply never reach the other's repositories for its whole life.

**What "Session Text" means concretely, as of 2026-09-15.** Never call a
session-creating tool for this — in Claude Code's cloud sessions that is
`create_session` on the `claude-code-remote` server, and it stays unused
here regardless of whether it is available. Instead: name the target
repository or repositories out loud, then build
[the-boildown](the-boildown.md)'s paste block as the opening
message for a window the person opens themselves, and tell them plainly to
open that new window and paste it in. Never silence and never a prose
description of what the person should go type — the block itself, ready to
paste.

**How to wake one, in Claude Code's cloud sessions as of 2026-09-13.**
`ListAgents` lists what is reachable — subagents, other local sessions,
sessions in the cloud where this one has cloud access — and **the name in
that listing is the address**, passed straight to `SendMessage` as `to`. The
message arrives in that session's conversation at its next tool round. For a
session `ListAgents` cannot see — one spawned with `create_session` has been
recorded as unreachable that way — go by session id instead: `create_trigger`
with `persistent_session_id`, then `fire_trigger` to deliver it now rather
than on a schedule. **Permission boundaries are per-session**, so work a person REFUSED here is
never work to ask a peer for; that routes back to them. **A repository this
session merely cannot reach is not that** -- it is the wall the Rule's clause
above is about, and the answer there is to relay, not to hand the person a
paste block.

**Waking a session is something the person has to be TOLD about, with the
link.** They cannot see the other conversation from where they are, so a
relay nobody mentions looks exactly like nothing having happened -- and they
are the one who has to chase it if it stalls. Say in the reply that you woke
it, what you sent it in one line, and give the
`https://claude.ai/code/<session id>` link. That is the same three things
[the-boildown](the-boildown.md) asks for; the only difference
is who pressed send.

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

**The pasted text is a handoff, and
[the-boildown](the-boildown.md) governs its contents
unchanged**: the session that opens once it is pasted in cannot see this
conversation, so the text names the branch, the files, the command and the
outcome expected, and ends with the line to paste back here when it is
done. One block per destination repository, keyed by the repository's name
— never by an ordinal.

**And it opens by naming THIS session —
[seeded-prompt-names-its-origin](seeded-prompt-names-its-origin.md): the
sending session's title and id, a link to it, and that software rather than a
person wrote the message.** Naming the sending *repository* is not this, and
is what a session reaches for instead when the rule is not in front of it —
*"from a session rooted in `<repo>`"* tells the reader nothing they can open.
The id and the link are knowable: ask the harness for this session's own id.

**Say what the new window will do before the paste block.** The person is
authorizing it by opening the window and pasting it in, and a block with no
sentence attached asks them to authorize something they cannot see.

**Do not hand off work this session can do itself, and establish the
verdict rather than inferring it.** The check is a probe, not a hunch: try
the attach, or `git push --dry-run` against the repository, and quote what
came back. *"I am probably not allowed"* is not a finding, and neither is
*"this session looks like it is ending"* — both hand the person back a job
they asked for. Every new window costs them a tab, a fresh context and a
re-read, so the handoff is normally **partial**: whatever this session can
finish, it finishes here, and only the residue goes into the paste block.

## Why
The cost being avoided is not confusion, it is re-derivation. A session that
works for an hour and then finds the repository out of reach has produced
context, not work, and context is exactly the thing a handoff cannot carry.
Checking first costs one comparison of two lists.

**A paste block is the only shape this can take, since 2026-09-15.** A
session this session created was the better ergonomics — the person's load
was a link and a click, not a block of text to carry — for exactly as long
as those created sessions kept coming back accepted. They stopped: rejected,
not seen as safe, for a reason nothing on this side of the harness can
diagnose or fix. [the-boildown](the-boildown.md) was always
the fallback for when no session-creating tool was available; it is now the
only path, whether or not one is.

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

**The closing-list clause was added 2026-09-14, and the incident is this
rule's own output going unread.** A session had done everything above
correctly: refused `add_repo` across owners, found no live session to wake,
seeded one with the work and the relayed authorization, and put the link in
its reply. Morgan never found it -- *"your link to the session you seeded was
lost in your sea of information"* -- and asked for the fix in the one place
he actually reads: *"make sure that list always includes sessions you've
spawned and the links to them, so I can see there that they were spawned and
I can keep my eye on them. (Remember that many times I only read those next
steps and nothing more, since you still give me too much text, it's
overwhelming.)"* He named both cases in the same breath, *"whether I
instructed you to or not and you just did it, either is fine"*, which is why
the clause covers the spawn nobody asked for.

**Placement near the top was never wrong; it was never sufficient.** The
top-of-reply link is what makes a person click through to a session they are
being asked to authorize, and it is read only by a person reading from the
top. Nothing in the catalogue said the link had to survive to the end of the
reply, so it survived only in replies that happened to be short -- and the
replies that spawn sessions are exactly the long ones. Universal, on
[rule-level-by-reach](rule-level-by-reach.md)'s third test: nothing in it is
about this repository's subject, this team, or one person's way of working --
anybody who spawns a session has to be able to find it again. **What the
reply's closing list is CALLED stays with whoever owns that convention**;
this clause says only that the sessions belong in it.

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

**The explicit stop-point line, 2026-09-15.** A container had been baking a
full merge instruction into `create_session`'s seeded prompt, on the reading
that a spawned session should carry the same authorization it would have had
inline. The harness's own permission classifier refused the `create_session`
call itself over it -- `[Merge Without Review]`, recorded in full as
[record/GOTCHAS.md#g43](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS.md#g43)
-- which is what prompted Morgan to ask about it: *"Could it be related to
the fact that you, in spawning new sessions, a day or two ago, we had it
include 'go merge'?"* His proposed fix, in his own words: *"maybe we remove
that BUT we have it say very very prominent, bold capitalized, that I need to
manually say to merge it."* The session that read this rule found the removal
half already covered by the 2026-09-13 default above -- nothing needed
un-baking, since the default was already not to bake it in -- so what was
missing was only the explicit statement, which he confirmed with *"Yes, do
both"* once that was shown to him (strength: decided).

**Renamed again 2026-09-15, on Morgan's decision, and this time the
mechanism moved too.** Unlike the rejected 2026-09-13 rename, this one was
not about the name underselling the rule -- it was about `create_session`
itself: *"your spawned sessions get everything rejected for not being seen
as safe. Have a rule to STOP spawning sessions; I need to wait ... until we
figure out how to tell Cloud your spawns are safe, or Anthropic improves
your system. In the meantime ... eliminate the vocab phrase we use 'spawn
session', but create a new one, called 'Session Text' which we will define
as: you tell me to open a new window; tell me what repos to seed it with;
and you give me (in a copy and pastable format) the text to copy-paste
in."* Two changes landed together because they were the same ask: the
standing instruction never to call `create_session` (or spawn a background
agent) for this again, and the phrase renamed to match what it now actually
does. Waking an already-live session is untouched -- it was never the thing
coming back rejected, and nothing in his ask covered it. **The stop-point
line above predates this and outlives it** -- it was written for a seeded
`create_session` prompt, and it earns its place just as much in a
copy-pasted block, since the ambiguity it closes belongs to the person
reading the text before they paste it in, not to the mechanism that used to
deliver it.

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
[the-boildown](the-boildown.md)'s own gate.

---
slug:        upstream-fix
title:       "Every fix removes its cause, lives where it survives, and reaches the origin and every copy"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "About whatever fix is in front of the session, in any file -- no path narrows it, and whether a file is a copy is a fact about its history that no glob can see. Its work (finding the cause, choosing where the fix lives, fixing the origin and the copies) happens inline. Reached through the occasion index and the `review` and `reply` gates. Decided: 2026-09-24, when the practice landed; checked again 2026-10-01, when durable-fix and fix-the-original merged into it, and the glob still holds."
occasion:    "fixing anything -- a bug, a stale or copied file, a broken environment -- or adding a check or exemption"
gates:       ["review", "reply"]
gates_why:   "`review` catches it while the fix is being chosen, the only moment the origin and the durable home are cheap to pick. `reply` catches the reporting half: a band-aid called one, every copy named, a check-only fix or a new exemption not presented as done."
index_clause: "fix the cause where it lives, and the origin and copies; name a band-aid"
index_required: true
checked_by:  "tools/precedent_check.py"
defines:     ["the origin artifact"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-24"
approved_by: "Morgan, 2026-09-24 -- coined the phrase and wrote its meaning
  himself: \"I'm asking you explicitly: 'The change you've recommended or
  that you did in this session, or are about to do -- in addition to fixing
  the issue now, will that change fix the core issue that caused this? If
  not, what will? For example, do any templates need to be changed, or
  anything in other repos that generate anything else need to be changed,
  particularly anything vendored in here? Let me know how you want to fix
  the root issue (or if you see fit do it); and if you need anything in a
  session rooted in a different repo, then just follow the 'prompt please'
  instructions to give those to me.'\" Authorized in the same message:
  \"Go update.\" Command phrase retired by Morgan, 2026-10-01: \"I think
  we should remove 'Upstream fix' and replace it with something else. I
  never use it ... now I'm instead trying to get you to do that all the
  time!\" durable-fix (Morgan, 2026-09-08) and fix-the-original (Morgan,
  2026-09-12, strengthened 2026-09-28) merged in, Morgan, 2026-10-01:
  \"Go, merge them, then Booked into pre-staging.\""
strength:    decided
---
## Rule
**Every fix a session reports answers this, without being asked.** "Will
this stop it happening again?" and "is that the real cause?" ask for it out
loud; the answer is owed either way. **A fix is not done when the symptom
goes away. It is done when the same cause cannot produce it again**, in a
place that survives, at the origin and in every copy. (This was the
"Upstream fix" command until 2026-10-01; looking back over a whole session
for causes that live upstream is [root-issues](root-issues.md).)

It is about **the change in front of the session**: the one it recommended,
the one it already made, or the one it is about to make.

**Where the cause lives:**

1. **Does that change also fix whatever produced the problem, or only this
   instance of it?** Say which, plainly. "Yes, the cause was here and this
   removes it" is a complete answer when it is true.
2. **If not, where does the cause live?** Look before answering, in at least
   these places:
   - **a template** the broken file was made from;
   - **a generator**: a script, a hook, or a build step that writes the
     broken output, whether in this repo or another one;
   - **something vendored in**: a file this repo copied from an upstream
     repo. Fixing the copy here leaves the upstream wrong, and the next
     `Update Vendors` brings the bug back;
   - **a practice or instruction** that told a session to do the wrong
     thing in the first place.
3. **Fix the root yourself where you can reach it and the fix is sound.**
   Where it is a judgment call, say how you would fix it and why, and let
   the person decide.
4. **For any part that needs a session rooted in a different repository,
   hand it back the way [Prompt Please](prompt-please.md) says**: one
   paste-ready block, with the seed root and the repos to attach said once
   more in plain prose outside it. Under that rule, the block carries a
   merge authorization only when the person gave one for this handoff.
5. **A check that catches the problem later is not the fix. Remove what
   made the mistake possible.** Ask what let it happen in the first place:
   a second copy of something that has to be kept in step by hand, a manual
   step no tool does, an instruction that steers the wrong way, a list
   someone has to remember to update. Remove that. Add a check only for the
   part that cannot be removed, and say which part that is. Example: new
   practices kept arriving without an entry in a second routing file, and a
   test caught it at staging; the fix was to move the reason into the
   practice file itself, so there is no second file to forget.
6. **Any new exemption is a sign the root fix has not been made.** Before
   adding an exemption, allowlist or waiver entry to any check, ask why the
   check is wrong about this case, and teach the check if it can learn.
   Only when it cannot, or not in this session, add the exemption with a
   `root_fix` saying which, hand off the root fix with
   [Prompt Please](prompt-please.md), and tell the person either way.
   `precedent_check.py --only upstream-fix` refuses a new
   entry in a `precedent.json` exemption list without a `root_fix`.

**Where the fix lives:**

7. **Default to the fix that survives, and call anything less a band-aid.**
   Ranked by how long it lasts:
   1. **a committed file**, which reaches every machine, session and person;
   2. **a generated file** committed alongside its generator;
   3. **machine or container state** (a `git config`, a path outside the
      repo, an environment variable), which dies with the container;
   4. **this session's own memory**, gone when the session ends.

   Anything below the first rung is a band-aid, however correct. When only
   a band-aid is available right now, say so in those words, never report
   it as the fix, and record the durable fix as an open item naming what it
   is blocked on.

**The origin and every copy:**

8. **Who else has a copy?** Every other place the same file, or the same
   mistake, went. **Fix the origin first, then the copies, and name all of
   them in the reply.** An origin this session cannot reach is a
   `blocked-on` item naming the repository, never a silent omission.
9. **What should have caught it earlier, and why didn't it?** When one gate
   passed what a later one failed (local green but GitHub red, one
   checkout's gate green and another's red), **that difference is its own
   bug, and its fix ships with this one.**

## Detail
**The cause can be a process, not a file**: a generator that keeps writing
the bad output, a practice that keeps steering sessions wrong. That is the
case a search for the broken file alone never finds.

**"Upstream" means wherever the cause lives, not just the upstream repo.**
Most often the cause is in a template or engine file this repo takes from
the repo that vendors its practice layer to it. But the cause can equally
be a generator in this same repository, or a rule in this repository's own
practices. When the root fix changes what a repo ships to others,
[vendor-rollout-disclosed](vendor-rollout-disclosed.md) applies as well:
say whether the fix has to reach the repos vendoring this one, and whether
their next `Update Vendors` will actually carry it.

**Two cheap questions place a fix on the ladder in point 7**: *does this
survive a fresh container?* and *does a person who was not here get it
without being told?* A fix that fails either is on rung 3 or below. A
durable fix can be genuinely out of reach (it needs someone else's
approval, a repository this session cannot push to, a decision nobody has
made); that is a legitimate reason for a band-aid, and exactly the case
where saying which one you applied matters most.

**The case point 8 exists for is the instantiated copy**: a file born from
a template or copied between repos, that nothing regenerates and no
manifest tracks. It is a committed file, so point 7 passes it, and it is
not generated, so [generated-edit-goes-upstream](generated-edit-goes-upstream.md)
never fires on it. **"The same mistake" counts, not only the same file**: a
wrong argument copied into five hooks is one origin and five copies even
where the five files are otherwise unrelated. Points 2 and 8 together are
one search, and point 9 is one comparison: what the gate that passed had,
or lacked, that the gate that failed did not (a machine with a module
installed, a directory with the other clones beside it). A session that
cannot find an origin in one search says so and moves on.

**Before any edit, a different rule applies.** When the bug is upstream and
this repository only holds a copy,
[upstream-bug-stops-here](upstream-bug-stops-here.md) stops the local edit
and hands the fix to the owning repository. The points here are for the
fix that does get made.

**Doing the root fix follows the authorization already in force.** This
rule licenses making the root fix. It does not add a push or a merge
authorization of its own. When Booked (`Go update`) or an equivalent covers the
work, the root fix lands with it. When nothing does, commit it and say it
is ready to land.

**It is not a licence to widen scope.** The durable fix to a one-line typo
is committing the one-line typo, not building a linter for it;
[checkable-gets-checked](checkable-gets-checked.md) decides when a rule
earns a mechanical check. **When there is no deeper cause, say so.** A
one-off typo has no upstream. Don't invent a template to blame, and don't
make a change just so the answer looks thorough
([no-invented-specifics](no-invented-specifics.md)).

## Why
A fix that removes the symptom and leaves its cause behind costs the
person twice: once now, and again when the same thing breaks somewhere
else and nobody remembers it was already diagnosed. The diagnosis is the
expensive part, and a band-aid throws it away while looking like progress.

**The cost is paid in a different repository from the one that saves it**,
which is why no single session sees it. In a setup where
one repository vendors templates, hooks and practices into several others,
the cause of a problem is often in a different repository from the one
where it showed up, and the recurrence lands on someone else, months later,
looking like a new bug. A session that fixes only the local copy, or only
this container, has genuinely solved its own problem; only the person
watching the same issue arrive for the third time can see that nothing was
fixed.

## Story
**Three practices, merged 2026-10-01.** Each began as Morgan asking for the
same thing from a different side, and by the time they sat side by side
they opened with the same sentence and each paid for its own Why. He asked
whether they were redundant and approved the merge: *"Go, merge them, then
Booked into pre-staging."* Strength: decided.
`durable-fix` and `fix-the-original` keep their files, with their full stories, as merged stubs pointing here.

**Where the fix lives (point 7), 2026-09-08.** *"I prefer permanent fixes
... I dislike band-aids in which hours later the same issue reappears!"* A
session had found a stale clone of a practice source in one container,
repointed it, and reported the problem handled. It was handled for that
container only: the config naming the clone is per-container, so the next
one would start stale the same way. The durable fix was one merge on the
source's own default branch. Same problem, same session, two fixes an
order of magnitude apart in reach, and the cheaper one was reported first.

**The origin and every copy (points 8 and 9), 2026-09-12 and 2026-09-28.**
*"I often have to remind you, make this change not just in this file, but
in the original template that led to it."* `commit-identity.sh` had been
found one version behind in all five private practice sets, which is what
a template fix that never went back to the template looks like from
outside. Point 9 came on 2026-09-28, after a shared set's check crashed on
GitHub's runner for want of PyYAML while the local push check had passed
the same tree, because the local machine had the package and the consumer
CI template never installed it. Both times the bug that mattered was the
gap between a gate that passed and one that failed. Morgan: *"can we make
that practice stronger"* (strength: decided).

**Where the cause lives (points 1 to 4), 2026-09-24.** Coined as the
"Upstream fix" command, for a question he found himself asking in full
after fixes: will this fix the core issue, and if not, what will? He named
templates, generators in other repos and anything vendored in as the
places to look, and routed cross-repo work through
[Prompt Please](prompt-please.md). Strength: decided.

**Points 5 and 6 came from one session's own misses** (2026-09-29). Five new
practices failed a staging test for having no routing entry; the session
added the entries, and Morgan asked why the fix was a check and not the
cause: *"preventing that sort of issue is more important than just checking
later ... in addition to add checks to find it later, fix what actually
caused the problem originally."* The same session had also exempted a
set's whole root from the file-name separator check, when the check simply
did not know two names were fixed by engine tools. *"Maybe whenever we need
to add an 'exemption' of any sort anywhere, we always use that as an
example of a root fix opportunity."* Both root fixes shipped with the rule.

**Retired as a command, 2026-10-01.** Morgan had stopped saying "Upstream
fix": he wanted the root fixed every time, and asking for it one fix at a
time had become the wrong shape. What he did keep asking, by pasting the
same paragraph into session after session, was whether anything the
session had run into should go back upstream; that became
[root-issues](root-issues.md). Points 1 to 4 became standing rules here the
same day. Strength: decided.

## Install
**Where the answer goes: [The Boildown](the-boildown.md)'s fix line**,
which opens with "Root fix:" or "Band-aid:" whenever a reply made or
recommended a fix and names the root fix beside every band-aid. Point 7
decides which label is true; then apply
[verify-postcondition](verify-postcondition.md) to the durable claim
itself: not *"the command succeeded"* but *"a fresh checkout gets this"*.

**Finding the origin** is `grep -rl "<a distinctive line from the file>"`
across the repo and any attached sources, or a look for a `templates/` copy
of the same basename. A fix that touched an origin and three copies is four
entries in the reply's files list ([reply-links-files](reply-links-files.md)).

**What is checked.** Point 6: `precedent_check.py --only upstream-fix`
compares each exemption list in `precedent.json` (every `*_exempt` key, and
`not_binding`) with the base branch, and refuses an entry that is new there
and has no `root_fix`. Entries that were there before are left alone until
someone touches them. The rest is a judgment about the problem, not a
property a script can see in the diff. A check for drifted copies was built
and run on 2026-09-12 and declined: same-basename divergence fired on a
hundred correct files, and template-to-copy similarity was red on two
copies that legitimately differ and say why in their own headers.
**Divergence is not the signal; a provenance stamp would be**, and that
design is filed in [todo/TODO.md](https://github.com/alex137/BestPractice/blob/staging/todo/TODO.md).
All nine points reach every fix through the `review` and `reply` gates.

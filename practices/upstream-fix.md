---
slug:        upstream-fix
title:       "\"Upstream fix\" asks whether the change fixes what caused the problem, and gets the root fixed"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE, about whatever change is in front of the session -- no file path reaches it, and its work (finding the cause, fixing the root, handing off the rest) happens inline rather than at merge/review/push/reply time. Reached through the occasion index alone. Decided: 2026-09-24, when the practice landed."
occasion:    "a person says \"Upstream fix\" or asks if a fix reaches the cause, or a fix, check or exemption is being added"
gates:       ["reply"]
gates_why:   "Points 5 and 6 apply without being asked, to any fix a turn reports: the reply is where a check-only fix or a new exemption gets presented as done, so that is the moment to ask what caused it."
index_clause: "fix the cause, not just add a check; a new exemption means look again"
checked_by:  "tools/precedent_check.py"
defines:     ["Upstream fix"]
command:     {"Upstream fix": "Say whether the change recommended, made, or about to be made in this session also fixes whatever caused the problem -- and if not, what would (a template, a generator, something vendored in from another repo) -- then fix that root yourself where it is reachable and sensible, and hand back a paste-ready prompt for any part that needs a session rooted in a different repo."}
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
  \"Go update.\""
strength:    decided
---
## Rule
**"Upstream fix" is the clean form, not the only one.** "Will this stop it
happening again?", "is that the real cause?" and anything else that plainly
asks the same question get the same treatment.

It is about **the change in front of the session**: the one it recommended,
the one it already made, or the one it is about to make. Answer, in this
order:

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

**Two more apply every time, without being asked** (Morgan, 2026-09-29,
strength: decided):

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

## Detail
**This command is the explicit, on-demand form of two standing rules.**
[fix-the-original](fix-the-original.md) says to fix the origin of a copied
file, not just the copy. [durable-fix](durable-fix.md) says a fix is done
when the cause can't produce the problem again. Both apply without being
asked. `Upstream fix` is what the person says when they want the check done
out loud and the answer in front of them, including the case neither rule
names on its own: **the cause is a process, not a file**, such as a
generator that keeps writing the bad output or a practice that keeps
steering sessions wrong.

**"Upstream" means wherever the cause lives, not just the upstream repo.**
Most often the cause is in a template or engine file this repo takes from
the repo that vendors its practice layer to it. But the cause can equally
be a generator in this same repository, or a rule in this repository's own
practices. When the root fix changes what a repo ships to others,
[vendor-rollout-disclosed](vendor-rollout-disclosed.md) applies as well:
say whether the fix has to reach the repos vendoring this one, and whether
their next `Update Vendors` will actually carry it.

**Doing the root fix follows the authorization already in force.** The
command licenses making the root fix. It does not add a push or a merge
authorization of its own. When `Go update` or an equivalent covers the
work, the root fix lands with it. When nothing does, commit it and say it
is ready to land.

**When there is no deeper cause, say so.** A one-off typo has no upstream.
Say "this was the cause, and the change removes it". Don't invent a
template to blame, and don't make a change just so the answer looks
thorough ([no-invented-specifics](no-invented-specifics.md)).

## Why
A fix that removes the symptom and leaves its cause behind costs the
person twice: once now, and again when the same thing breaks somewhere
else and nobody remembers it was already diagnosed. In a setup where one
repository vendors templates, hooks and practices into several others, the
cause of a problem is often in a different repository from the one where
it showed up. A session that fixes only the local copy does the easy half
of the work and hides the harder half.

## Story
Coined by Morgan, 2026-09-24, as a standing phrase for a question he found
himself asking in full after fixes: will this fix the core issue, and if
not, what will? He named templates, generators in other repos and anything
vendored in as the places to look, and routed any cross-repo work through
[Prompt Please](prompt-please.md) rather than a new handoff mechanism.
Strength: decided.

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

## Install
Points 1 to 4 have no mechanical check: whether a reply found the real
cause is a judgment about the problem, not a property a script can see in
the diff, the same as [go-update](go-update.md) and
[write-it-up](write-it-up.md). Points 5 and 6 reach every turn through the
`reply` gate. Point 6 is also checked: `precedent_check.py --only
upstream-fix` compares each exemption list in
`precedent.json` (every `*_exempt` key, and `not_binding`) with the base
branch, and refuses an entry that is new there and has no `root_fix`.
Entries that were there before are left alone until someone touches them.

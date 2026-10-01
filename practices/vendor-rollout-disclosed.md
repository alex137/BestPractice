---
slug:        vendor-rollout-disclosed
title:       A change to what this repo ships states whether and how it reaches consumers
tier:        on-demand
severity:    default
applies_to:  ["practices/*.md", "templates/**", ".claude/hooks/*.sh"]
applies_to_why: "A real locus for most of what it governs -- a practice file, a template, a hook script -- but not all of it: the engine files this also covers are named individually in tools/precedent_vendor_engine.py's ENGINE_FILES/CONSUMER_ENGINE_FILES lists rather than matched by a path glob, since that set is a curated allowlist, not every *.py file under tools/. Reached for those by the gates below instead. Decided: 2026-09-18, when the practice landed."
occasion:    "committing a shipped practice, hook, template or engine file, before push or merge"
gates:       ["merge", "push"]
gates_why:   "The disclosure has to land before the shared-branch step, not after -- both moments a change could reach a consumer without it."
index_clause: "say whether shipped content must reach consumers, if it will, how it migrates"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-18"
approved_by: "Morgan, 2026-09-18; the third question, Morgan, 2026-09-29 (decided); the fourth question, Morgan, 2026-09-29 (assented); the fifth question, Morgan, 2026-09-30 (decided)"
strength:    assented
---
## Rule
Before a commit that touches shipped content -- a file under `practices/`,
`templates/`, `.claude/hooks/`, or one of the exact filenames in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
`ENGINE_FILES`/`CONSUMER_ENGINE_FILES` lists -- or that adds a file
anywhere, reaches the push or merge side of the chain, say five things out
loud, not one:

1. **Does this need to reach the repos that vendor this one?** Most edits
   here do not -- a wording fix, a Story section filled in, a spec document,
   this repo's own
   [MAP.md](https://github.com/alex137/BestPractice/blob/staging/MAP.md)
   or
   [todo/TODO.md](https://github.com/alex137/BestPractice/blob/staging/todo/TODO.md).
   Say "no, self-contained" and move on when that is the honest answer.
   Living under one of the paths above is necessary for a change to matter
   downstream; it is not sufficient.
2. **If it does need to reach consumers, will
   [vendor-update-runbook](vendor-update-runbook.md)'s own mechanism
   actually carry it there on a consumer's next run, or is there a known
   reason it won't** -- a pinned branch, a declined hook, a stale watermark,
   a rename the vendored copy still points at? Name the gap here rather
   than leaving it to be found later, as a bug with no visible cause, in a
   different repository.
3. **Does it still work where the update has not arrived, or has arrived
   only in part?** Any change to how the mechanics work -- a new field, a
   new file, a new check, a changed format -- lands in repositories at
   different times, and a repository mid-update carries some of it and not
   the rest. So the change carries its own migration: **a field or file an
   older repository lacks means the old behaviour, never a refusal**; an
   older engine reading the new shape keeps working; Update Vendors or the
   installer brings the new piece forward on its own; and a test plants the
   not-yet-updated shape and shows it still builds. A change that cannot be
   made safe that way says so here, with what a repository has to do
   first.
4. **Has a new or changed check run in a consuming repo that received
   other sources' files?** A consumer holds practices and checks its sets
   wrote, and the vendored engine, and a check can judge those copies
   where nobody can fix them. The runner already drops findings on
   received files, and the changed-files check asks a new check for its
   planted case; this question covers what those two cannot see. Run the
   check in that shape, or say why it cannot misread a received file.
5. **Should each new file ship to consumers at all?** Run
   `python3 tools/checkin.py rules`: it lists every file added since the
   landing branch, whether it ships, and the rule in
   [tools/checkin.py](../tools/checkin.py)'s `VENDORING_RULES` that says so.
   **A file ships only if a consumer runs it, instantiates it, or its
   people read it to adopt and use Precedent. Ship the machinery, never
   this project's own records:** a consumer gets the tools that keep an
   open-items list and a news log, and keeps its own; it never gets our
   todo items or our What's New (Morgan, 2026-09-30). How this repo is built
   stays here: plans, open items, decisions, reasoning, tests, run
   records, repo-local rules, its own settings and
   instructions. For each SHIPS line, say whether that holds; when it does
   not, add the rule that keeps it here. A file in a new place has no rule
   yet, and the `vendoring-decided` check refuses it until one is written.
   A doc of ours that a consumer's reader needs is linked on GitHub from a
   shipped one, never shipped itself.

**No answer is a promise.** This repo cannot make a consumer actually
run `Update Vendors` -- what it can do, and must, is say plainly whether a
change is waiting on that step, so the gap is visible at the point of
change rather than discovered downstream.

## Why
[fix-the-original](fix-the-original.md) already names the shape of this
failure: *"the cost is paid in a different repository from the one that
saves it."* That practice is about tracing a mistake already propagated
back to its origin; this one is about the moment before propagation --
whether a change here is going anywhere at all, and whether the mechanism
meant to carry it actually will. A session editing this repo has no reason
to hold that question in mind unprompted: it is finishing the change in
front of it, and the repos vendoring this one are not open in the same
window.

## Story
Named 2026-09-18, from a recurring pattern Morgan described: changes made
to this repo were not reaching the repos vendoring it in when they needed
to, because nothing at the point of change asked whether they should.


**2026-09-29: the third question, migration.** Building a per-set allowance
for the occasion index, the first design read each source's allowance from
its `precedent-source.json` and, where one was missing, fell back to the
old single cap -- which is every repository mid-update, since the vendored
universal tree had never carried that file. Morgan: *"Please account for
updates/upgrades/migrations (ie, some won't have that) ... ANY change to the
mechanics of how it works must take into account updates/upgrades/
migrations."* A source with no allowance yet now counts at its measured
size, Update Vendors copies the file across, and the harness plants both
half-updated shapes.

**2026-09-29: the fourth question, received files.** A new engine check,
checks-use-generated-blocks, went live and then judged check files a
consuming repo had received from a practice set -- copies the next sync
overwrites, which only the set could fix. Nothing had run it in a
consumer's shape. The same batch moved the skip for received files into
the check runner and taught the pre-staging check to ask a new check for
its planted case; the question keeps the part no tool sees in view.

**2026-09-30: the fifth question, whether a new file ships at all.** A
consumer's copy of this repo held 543 files, among them the test suite,
the environment traps and a second copy of the engine, because the copy
took everything not on a list of exclusions. It became an allowlist that
day. Morgan: *"make sure that \*every new file\* is evaluated to see if it
should be vendored in or not, and you should determine the ruleset."* The
ruleset is `VENDORING_RULES`, each rule with its reason and no catch-all,
so a new kind of file is decided by a person rather than by default.
The environment traps went back in the next day: they are what a session
using Precedent runs into, and environment-gotchas tells it to search them
(Morgan, 2026-10-01).

## Install
No mechanical check, and this is a considered gap, not the first
plausible-sounding reason. Two designs were considered and both fail for
specific reasons:

- **Whether a change "needs" a downstream rollout** is a judgment call over
  content, not a fixed pattern a script can grep for reliably -- a file
  living under a vendored path is not automatically content a consumer
  depends on changing (a wording fix is still under `practices/` and still
  needs no one's `Update Vendors` run).
- **Requiring a disclosure line in the commit message that made the
  change** -- checkable in principle, the way an attribution footer is --
  fails on the same ground [disclose-landing](disclose-landing.md) already
  found for the same kind of rule: this is a statement about what a
  *reply* says, and a push can carry several commits, so a check reading
  one commit's message reads the wrong one, or only one of several, as
  often as it reads the right one.

What the gate can and does check mechanically is reach, not judgment or
reply content: `precedent_gate.py merge` and `precedent_gate.py push` serve
this practice's Rule whenever either moment runs, and `precedent_paths.py`
serves it for any file matching `applies_to` above, same as any other
on-demand practice.

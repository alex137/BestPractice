---
slug:        vendor-rollout-disclosed
title:       A change to what this repo ships states whether and how it reaches consumers
tier:        on-demand
severity:    default
applies_to:  ["practices/*.md", "templates/**", ".claude/hooks/*.sh"]
occasion:    "committing a shipped practice, hook, template or engine file, before push or merge"
gates:       ["merge", "push"]
index_clause: "say whether shipped content must reach consumers, and whether it will"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-18"
approved_by: "Morgan, 2026-09-18"
strength:    assented
---
## Rule
Before a commit that touches shipped content -- a file under `practices/`,
`templates/`, `.claude/hooks/`, or one of the exact filenames in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
`ENGINE_FILES`/`CONSUMER_ENGINE_FILES` lists -- reaches the push or merge
side of the chain, say two things out loud, not one:

1. **Does this need to reach the repos that vendor this one?** Most edits
   here do not -- a wording fix, a Story section filled in, a spec document,
   this repo's own
   [MAP.md](https://github.com/alex137/BestPractice/blob/staging/MAP.md)
   or
   [TODO.md](https://github.com/alex137/BestPractice/blob/staging/TODO.md).
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

**Neither answer is a promise.** This repo cannot make a consumer actually
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

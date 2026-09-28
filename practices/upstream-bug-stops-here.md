---
slug:        upstream-bug-stops-here
title:       An upstream bug is never patched in the repo that copied it
tier:        on-demand
severity:    default
applies_to:  ["process/upstream/**", "precedent/universal/**", "tools/*.py", "tools/checks/**", "practices/**", ".claude/hooks/**", "tools/bootstrap.sh", ".github/workflows/light-check.yml", ".github/workflows/leak-gate.yml"]
occasion:    "about to change a file to fix a bug, in a repository that did not write that file"
gates:       ["review"]
index_clause: "classify first; an upstream bug stops here and goes upstream by Prompt Please"
index_required: false
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "Morgan, 2026-09-28"
strength:    decided
---
## Rule
**Before changing anything, classify the change: is it a bug fix, and is the
bug upstream or local?** Upstream means the broken file, or whatever wrote it,
belongs to another repository: a vendored engine or catalogue, a check a
practice set ships, a hook or file made from a template -- anything an update
would bring back.

**A bug fix that is upstream is not made here.** Stop before editing. Tell the
person, in plain words, that the bug is upstream and which repository owns it,
and hand back a [Prompt Please](prompt-please.md) block that fixes it there.
Patching the local copy hides the bug from every other repository that carries
it, and the next update puts it back.

**Two things change that:** the person asks for a local stopgap, which then
goes in as a labelled band-aid beside the handoff, or tells this session to
fix the upstream repository itself.

## Detail
**This repository may BE upstream.** In BestPractice, its engine and templates
are the origin; in a practice set, its own checks and practices are. Editing
the origin is the fix this rule asks for, not the thing it stops. The test is
who wrote the file, not what path it sits at: the paths above are where copies
usually live, so the rule surfaces on them, and a session that owns the file
says so and carries on.

**How to tell upstream from local, fast.** The file is listed in
`tools/ENGINE_MANIFEST.json`, or `MANIFEST.json` records it from a source, or
it sits under `process/upstream/` or a declared universal source path, or its
header says it was instantiated from a template. Any one of those makes it
upstream. A file this repository wrote and nothing regenerates is local: fix
it here, as usual.

**Not a bug fix, not this rule.** A new feature, a config choice, a
repository-specific adaptation the template invites (a line added to
`tools/bootstrap.sh`, an entry in `precedent.json`) is ordinary local work.
The rule is about repairing something broken that another repository owns.

**The handoff is concrete.** The Prompt Please block names the owning
repository, the broken file and line, what goes wrong and how it was seen,
and how to prove the fix (a test that fails without it). Where a session is
already working in that repository, route to it instead, the way
[the-boildown](the-boildown.md)'s live-session check says.

**It holds even where the session could fix the upstream repository itself.** A
session that could reach the upstream repository still stops and asks here,
because the person wants to see an upstream bug before anyone patches
anything. The Boildown's root-fix item then reports where the upstream fix
stands ([the-boildown](the-boildown.md)).

**Relation to its neighbours.** [fix-the-original](fix-the-original.md) asks,
after a fix, where the file came from and who else has a copy;
[upstream-fix](upstream-fix.md) answers "is that the real cause?" when asked.
Both work after the change is chosen. This one works before, at the moment the
edit would otherwise happen.

## Why
Local patches to upstream bugs are cheap for the session that makes them and
expensive for everyone else. The repository in front of the session goes
green, the owning repository stays broken, every other repository that carries
the copy still has the bug, and the next Update Vendors either overwrites the
patch or collides with it. Nobody sees the cost, because each session in
isolation fixed its own problem.

## Story
**Asked for by Morgan on 2026-09-28**, after two days in which sessions fixed
bugs directly in a consuming repository without saying they came from
upstream. On the same days, several consuming repositories were hand-patched
for defects in the shared update tool, a shared practice set's check script,
and a test shipped by the individual set; the upstream fixes happened only
because someone forwarded each report afterwards. His words: *"before any
change you're going to make, identify whether it's a bug fix or not. And
also, if it is a bug from upstream or just for this local. And then, if the
change you're about to make is both a bug fix and from upstream, then before
making that fix, stop and tell the user that there's an upstream bug and give
the user a prompt please message so that the user can fix it upstream. As a
general rule, I want to try to avoid or minimize fixing bugs in a repo that
come from an upstream."* (strength: decided)

**On the mechanical check, attempted and declined with a reason**
([checkable-gets-checked](checkable-gets-checked.md)). A diff can show that a
vendored file changed, and the manifests already refuse most of those edits
(the engine refresh names a hand-edited engine file; the catalogue update
refuses local changes to the vendored tree). What no check can see is the
moment this rule is about: the decision, before any edit, to patch a copy
rather than stop. That is why the rule is tied to the vendored paths, so it is
printed when an edit there begins, and why the Boildown carries the after-the-
fact report.

## Install
Nothing to install. The path channel prints this Rule when a session edits a
file under one of the paths above; the review gate carries it too.

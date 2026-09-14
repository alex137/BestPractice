---
slug:        catalogue-carries-stories
title:       Every active practice in a catalogue carries a non-empty Story
tier:        on-demand
severity:    default
applies_to:  ["practices/*.md"]
occasion:    "landing practices in bulk -- a migration, an import, or a move between sources"
gates:       ["merge"]
index_clause: "no active practice sits with an empty ## Story"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       2026-09-07
approved_by: "Morgan F, 2026-09-07"
---
## Rule
Every practice with `status: active` carries a non-empty `## Story`. This is a standing invariant over the whole catalogue, checked across the entire tree rather than only across the files a branch happens to touch, so a practice that lands with an empty Story is red immediately and stays red until somebody writes the incident down.

## Detail
Where no incident genuinely exists -- a rule written as a stated preference, or one carried in from a source whose own text recorded reasoning rather than a failure -- the Story says *that*, plainly. An honest "no originating incident was recorded, and this Story does not invent one", followed by the reasoning that actually justified the rule, is a complete Story. **What this refuses is silence, not the absence of drama**, and the difference matters: demanding drama produces invented incidents, which are worse than an empty section because an empty section is a visible gap and a fabrication is a false record that gets trusted.

A practice that is not `status: active` is out of scope: a deduplicated record points at whichever practice is in force, and that one carries the Story.

Only practices a repo authors are in scope. Where `practices/` is materialized output rewritten from every declared source, a Story missing from another source's practice cannot be written there and would be overwritten if it were.

## Why
[cite-the-incident](cite-the-incident.md) already demands the failure a rule prevents, and its check enforces that at authorship time on changed files. That is the right gate for writing one practice and the wrong one for two cases that actually happen.

**Receiving a whole catalogue at once.** A migration lands dozens of practices in one commit. Every Rule is new, so an authorship gate could catch it -- but only if it is running in the repo receiving them, which is precisely the repo that has just been set up.

**A gap already sitting in the tree.** Once the landing commit is behind you, a changed-files check never looks at those files again. Nothing re-examines a section that was empty from the start, because an empty section is not a change. A standing invariant sees both, and keeps seeing them every day the gap stays open, which is the property that makes a backlog get paid down rather than noticed once and deferred.

## Story
**Written 2026-09-07, after the same gap was found open in three separate catalogues at once** -- 34 practices in one team source, 2 in an individual source, and 30 of 65 here, in the universal catalogue itself.

The converter was not at fault, and the record should say so. [split_practices.py](../tools/split_practices.py) declines to populate `## Story` deliberately, and documents the reason in its own module docstring: separating an incident from its reasoning is editorial judgment, described in the plan as LLM-assisted and human-reviewed once per practice, and doing it unreviewed for a whole catalogue in one pass risked mischaracterizing exactly the content the migration existed to preserve faithfully. It left the section present and empty as a **declared** gap rather than a silent one.

The actual defect was that nothing ever came back for the declared gap, and in the private sources nothing could: `cite-the-incident`'s check lives in [precedent_check.py](../tools/precedent_check.py), which was in `CONSUMER_ENGINE_FILES` but **not** in `ENGINE_FILES` — so a consuming repo got it and a *source set* never did, and the sets are exactly where migrated catalogues land. The same shape as a status-contract check found unreachable there for the same reason. **A gap declared in a repo that cannot check for it is indistinguishable from one nobody declared.** (Corrected 2026-09-07: this paragraph first said the file was in neither list, which was wrong about consumers and right about sources. `precedent_check.py` is in both lists as of the same day.)

Here, where the check does run, the gap survived for a different reason worth recording: `cite-the-incident` fires on authorship of a *changed* Rule, and a Story that was empty from the beginning is never a change. Its own practice file was among the 30.

## Install
Checked mechanically by [tools/precedent_check.py](../tools/precedent_check.py), scope `tree`: every `practices/*.md` whose frontmatter `status:` is `active` must have a non-empty `## Story`. `status:` is read from the frontmatter block only, never searched for anywhere in the file, since several practices discuss the status vocabulary in their own prose. A practice a committed `practices/MANIFEST.json` attributes to another source is skipped, so the check stays silent in a consuming repo on text that repo cannot fix. It tests that the incident was recorded, never that it was the right incident -- the same limit [cite-the-incident](cite-the-incident.md) states about itself.

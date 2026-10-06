---
slug:        todo-is-a-handoff
title:       A TODO is a handoff, not a parking lot
tier:        on-demand
severity:    default
applies_to:  ["TODO.md", "todo/todo-*.md"]
applies_to_why: "The distinguishing condition is writing or triaging an entry in the TODO file itself — the only place the practice's rule is ever violated. Widened 2026-09-18 to the per-item todo/ format's own files, once a repo has migrated to it. Decided: post-phase-4, converting Alex's practice 53."
occasion:    "writing, triaging or doing work on an open item"
gates:       ["merge"]
gates_why:   "The periodic sweep that enforces the stated-reason requirement on the backlog naturally happens at merge time, the same as capture-gate."
index_clause: "queue only for a stated blocked-on/out-of-scope reason; else just do it"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork). The upstream-fix paragraph and its
  commit-time check: S. Alexander Jacobson, 2026-10-06, \"Then let's figure
  out how to make sure fixes are made at commit time.\" and, on the plan,
  \"Merge first and then do that fix\""
strength:    decided
source_practice_number: 53
---
## Rule
Before writing an open item, ask: *could this session finish it
now?* If yes, do the work — the inclination to queue an agent-doable item is
the signal to do it, not to file it. An item may be queued only for a stated
reason.

**A fix that belongs in another repository is never a `blocked_on` reason**
— a vendored file's source, a practice set, an upstream engine — **and
neither is access the session can request.** Request the access if it is
needed and open the fix pull request there in the same turn. An open item
about such a fix may exist only to wait on that pull request's review, and
it links it.

## Detail
The reason is written into the item itself:

- **blocked-on** — a named external input: a decision (with its owner named),
  a resource, an event, an artifact that does not exist yet; or
- **out-of-scope** — genuinely too large or too tangential for the current
  session, in which case the item must carry the context a cold session
  needs: why it matters, the intended approach, and the pointers.

"Would enlarge this turn" is not a reason; it is the moment the context is
cheapest. Nor is "it lives in another repository" or "this session cannot
push there": `python3 tools/upstream_fix.py PATH` names the source a
vendored path came from and opens a branch in its clone, and an `add_repo`
or an access request is part of the same turn. Only a refused request, or a
fix that needs a decision from the other repository's owner, is a real
blocker, and the item names who refused or who decides. A sweep that finds an open item with neither reason either does it
in the sweeping session or closes it as not worth doing.

**In the per-item `todo/todo-<date>-<slug>.md` format**
([spec/OPEN_ITEM_AND_GOTCHA_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/OPEN_ITEM_AND_GOTCHA_PLAN.md)
Part 1), the same two reasons are the `blocked_on` frontmatter field's
content, not prose. Widened here, 2026-09-18, alongside `applies_to`.

## Why
A queued item sheds context every day it waits. The session that
noticed the need holds the reasoning, the file locations, and the half-formed
approach — and almost none of that survives into a one-line queue entry, so
deferral converts cheap work into expensive work, and often into work never
done. The catalog already outlaws deferral for two special cases — capture
happens in the thread that created the need ([capture-gate](capture-gate.md)), and the
inclination to write a verify-later marker means go verify now
([deliverables-look-like-output](deliverables-look-like-output.md)) — because both learned that the queue is where context goes to die. This
generalizes the same insight to ordinary work: the typed TODO exists to hand
work *across a genuine boundary* (to a human decision, to hardware, to a
session with the right scope), not to spare the current session effort.

## Story
**The upstream-fix paragraph, 2026-10-06.** In one consumer four open items
sat for one to two weeks, each reading like "blocked on push access to X"
or "needs a change in the engine", and each an hour's fix the session that
filed it could have opened as a pull request upstream. The rule already
said "if this session could finish it, do it"; another repository and
access the session could request slipped through as reasons all the same,
and nothing checked. S. Alexander Jacobson: *"Then let's figure out how to
make sure fixes are made at commit time."* On the plan: *"Merge first and
then do that fix."* Strength: decided.

Origin: a session queued two follow-up items from its own build — both
labeled agent-doable, one of them a half-hour mechanical change — and the
owner asked why work needing no input from them was parked at all. Both
items, done later, cost more to re-orient into than they would have cost to
finish on the spot.

## Install
The TODO template's header ([repo-is-memory](repo-is-memory.md)) carries the compressed
rule, so every new item is written against it; the periodic sweep enforces
the stated-reason requirement on the backlog.

**The upstream-fix paragraph is checked at commit time.** The light check
([tools/doc_lint.py](https://github.com/alex137/BestPractice/blob/staging/tools/doc_lint.py))
refuses a changed `todo/todo-*.md` whose `status` is open and which links no
github.com pull request or issue, when its text names a path this repo
vendors (read from the vendoring manifests and `precedent.json`'s sources,
never a list of its own), or its `blocked_on` or `waiting_on` names a
repository a source comes from. It uses no keywords: "vendor" and "access"
matched real outside blockers in a consumer. Closed items are never
flagged. The finding names
[tools/upstream_fix.py](https://github.com/alex137/BestPractice/blob/staging/tools/upstream_fix.py),
which sets the fix up in the source's clone and never edits the copy. This
does not license patching the local copy
([upstream-bug-stops-here](upstream-bug-stops-here.md)): the pull request
upstream is where the person sees the fix before it lands. `checked_by`
stays null, because the rest of the rule is a judgment and a practice with
a `checked_by` is not loaded.

Not yet attempted mechanically: a check that scans `TODO.md` entries for a
stated `blocked-on`/`out-of-scope` reason is a plausible candidate
(`checkable-gets-checked` applies), left `checked_by: null` here rather than
wired in without testing, since this file is a straight conversion of
Alex's addition to `main` (merged after this branch's fork point — see
[CHANGES_TO_TELL_ALEX.md](https://github.com/alex137/BestPractice/blob/staging/spec/CHANGES_TO_TELL_ALEX.md); this file's own
`source_practice_number` above records its original BestPractice number)
and not new authorship going through the creation pipeline's own review. Revisit when phase 5's
enforcement work reaches the backlog.

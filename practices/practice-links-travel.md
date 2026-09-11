---
slug:        practice-links-travel
title:       A practice links only what travels with it
tier:        on-demand
severity:    default
applies_to:  ["practices/*.md"]
occasion:    "writing or editing a practice file"
gates:       []
index_clause: "link only what travels with the file; the rest is an absolute upstream URL"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-11"
approved_by: "Morgan, 2026-09-11"
strength:    assented
---
## Rule
**A practice file is published into every repository that adopts the
catalogue, so a relative link in one only works if the target travels with
it.** Three things do: **another practice file in the same directory**, cited
the normal way as a markdown link to its own `<slug>.md`; **the vendored
engine files under `../tools/`** that every consumer receives; and **a
source's own check scripts and their tests under `../tools/checks/`**, which
materialization copies alongside the practices, subtree and all — a practice citing the script that enforces
it is the most common cross-reference a private set makes, and it is a
correct one.

**Everything else in the publishing repository does not travel** — `spec/`,
`templates/`, root documents, decisions, records, hooks. Link one of those
relatively and the link is live where it was written and dead in every
repository that receives it, which is the one place nobody checking it will
look.

**From a PUBLIC source, link it as an absolute URL** to the file in the
publishing repository, on that repository's declared `base_branch`. The
reader gets a live link wherever they are reading, and the writer gets to
keep the reference. **From a PRIVATE source, drop the link markup and keep
the backticked path** — an absolute URL would publish the private
repository's name into every consumer that materializes the practice, which
is a worse failure than a reference the reader has to go find. **Nothing downstream will
repair that one, and nothing downstream should** — `_rewrite_links` refuses
the private case on purpose, so the unlinked path is load-bearing rather than
an oversight somebody should tidy up later.

## Detail
**The public and private answers differ, and neither is the general case.**
What decides it is whether the target is readable by whoever ends up holding
the practice file. A universal practice published from a world-readable
upstream can name its own repository in a URL freely; an individual or team
set cannot, and pays for the reference with a path the reader has to resolve
by hand.

**A sibling practice link is the one reference that always survives**, in
both directions and at every level, because materialization writes every
source's practices into one directory. Prefer it: a rule that can make its
point by citing another rule needs no URL at all.

**The worst shape of this bug is not a dead link — it is a live one pointing
at the wrong file.** `../bootstrap/x` at least 404s, and a markdown lint can
see that. `../.claude/settings.json` **resolves** in the consumer, to that
consumer's own settings file rather than the one the sentence was written
about. No lint anywhere reports it; only reading the link as a claim about
*which repository* it assumes will catch it. The rule catches this one only
because `.claude/` does not travel — nothing would catch it if it did.

**Do not assume materialization repairs this for a public source.**
`precedent_materialize.py`'s `_rewrite_links` does turn an unplaceable
relative link into an absolute URL when the source is public, which reads
like the problem solving itself. It does not, in the install that matters
most: when the universal source is a tracked tree *inside* the consuming
repository, the rewriter resolves the target within that repository instead,
finds nothing there, and leaves the link exactly as written — it will not
invent a target it cannot place. That is the right refusal and it is why the
links have to be correct in the publishing source.

## Why
The catalogue is written in one repository and read in all of them, and
nothing about writing it makes that visible. A relative path resolves
correctly on the screen of whoever wrote it, passes that repository's own
link check because the file really is there, and breaks only after it has
been copied somewhere else — by which point the person holding the broken
link has no way to tell what it was ever pointing at.

## Story
**The rule is older than this file, and the private original had already
named two things this one missed.** Written in `precedent-individual` on
2026-09-06 after the same mistake landed three times in one day against one
directory — nine dead links across four practices, one batch of which was
"fixed" by making the links absolute, which tripped a consuming repo's
private-repo scrub and had to be undone. The universal text here was written
without being able to read it, and shipped a check that would have fired on a
correct link to a source's own check script. Both gaps were closed on
2026-09-11, by reading the original once the private sources resolved.

**Measured 2026-09-11, in this repository at engine `89c90d7`: 134 relative
links across 42 of the 94 universal practice files pointed at 57 targets
that exist only here.** The same measurement taken from a real consuming
repository the same day reported 120 broken links across 40 of its 126
materialized practice files, against 52 distinct targets — the two counts
differ because a consumer's tree holds practices from other sources too, and
has root documents of its own that a few of the links happen to hit.

**The rule already existed and could not see the catalogue from anywhere.**
It was written in `precedent-individual`, with a real check script beside
it, and that script skips every practice whose source is not the individual
set — correct on its own terms, since a consumer cannot fix another source's
text and the next sync would overwrite the attempt, but it means the
universal catalogue was examined by nobody. In this repository neither the
practice nor the script existed at all: they live in a private set, and this
repository is not a materializing consumer, so they never arrived. Running
the consumer's own `precedent_check.py --only practice-links-travel` printed
**1 passed, 0 violated** while 120 links in the tree it had just scanned
were dead.

**The move to universal is [layered-practice-packs](layered-practice-packs.md)
applied literally**: this is a rule about how practice files are written, and
practice files are written here. The individual copy is still standing as of
this landing — that repository could not be reached from the session that
landed this one — and deduplicating it is
[spec/MOVING_PRACTICES.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/MOVING_PRACTICES.md)'s
second step, queued in
[TODO.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md)
rather than done silently. The text here was written fresh rather than
carried across, for the same reason: nobody in that session could read the
original.

## Install
[tools/precedent_check.py](../tools/precedent_check.py) enforces it, as a
tree-scope check over the practice files this repository owns. It reads
which engine files travel from
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)'s
`CONSUMER_ENGINE_FILES` rather than keeping a second list, and it holds the
other half too: an absolute upstream URL must use the branch
`precedent.json` declares and must name a path that actually exists in the
tree. **In a materializing consumer the check reports SKIPPED with its
reason** — `practices/` there is generated output, and the links have to be
right in the publishing source or not at all.

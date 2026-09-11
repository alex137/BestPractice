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
materialization copies alongside the practices — a practice citing the script
that enforces it is the most common cross-reference a private set makes, and
it is a correct one.

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
is a worse failure than a reference the reader has to go find.

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
[precedent_materialize.py](../tools/precedent_materialize.py)'s
`_rewrite_links` does turn an unplaceable relative link into an absolute
URL when the source is public, which reads
like the problem solving itself. It does not, in the install that matters
most: when the universal source is a tracked tree *inside* the consuming
repository, the rewriter resolves the target within that repository instead,
finds nothing there, and leaves the link exactly as written — it will not
invent a target it cannot place. That is the right refusal and it is why the
links have to be correct in the publishing source.

**For a PRIVATE source it refuses on purpose, and the dead link is
load-bearing.** The same rewriter passes `may_name_source_repo=False` for
an individual source, so it leaves the relative link exactly as written
rather than minting an absolute URL into the publishing repository. That is
a privacy boundary, not a gap: the URL would hand a consuming repo's tracked
tree that private repository's owner and name, and a consuming repo can be
public. Its own words: *"a
relative link that does not resolve is a smaller failure than a disclosure
that cannot be taken back."* **So a session that finds such a link must not
make it absolute** — that is the disclosure, and it is the first thing
anyone tries. Nothing downstream repairs it and nothing downstream should;
the repair belongs in the publishing source, as a backticked path.

## Why
The catalogue is written in one repository and read in all of them, and
nothing about writing it makes that visible. A relative path resolves
correctly on the screen of whoever wrote it, passes that repository's own
link check because the file really is there, and breaks only after it has
been copied somewhere else — by which point the person holding the broken
link has no way to tell what it was ever pointing at.

## Story
**The rule is older than this file, and the private original had already
named four things this one missed.** It was written in `precedent-individual`
on 2026-09-06, out of the incident below. The universal text here was written
by a session that could not attach that repository and had never read it, so
it shipped without the check-script clause, without the shape that resolves
to the wrong file, without the private half of the materialization refusal,
and without the incident itself — and its check would have fired on a
correct link to a source's own check script. All four were closed on
2026-09-11, once the private sources resolved and the two texts could be
read against each other.

**The incident: 2026-09-06, three sessions, one day, one directory.** A
practice landed carrying three `../bootstrap/` links. The first push that
vendored it turned a consuming repo's Markdown lint red — three broken
relative links, a hard failure — and **the fix made them absolute, which
tripped that same repo's `private-repo-scrub`**, because an absolute URL was
precisely the disclosure the rewriter refuses to make. They were corrected to
bare backticked paths. Hours later two more practices landed with seven more
of the same, from a different session that had no way to know. A sweep then
found two in a third practice that had been dead **for weeks** and had never
been reported once — `doc_lint` scopes to CHANGED files, and nobody had
touched that file since. A gotchas note written after the first batch
prevented neither the second nor the third, which is the case for a check
rather than more prose
([checkable-gets-checked](checkable-gets-checked.md)).

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

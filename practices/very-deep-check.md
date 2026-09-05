---
slug:        very-deep-check
title:       The very deep check — a whole-repo coherence review, on request only
tier:        on-demand
severity:    advisory
applies_to:  ["**"]
occasion:    "a person explicitly asks for a \"very deep check\" across the whole repo, or after work that invites drift"
gates:       []
index_clause: "read the whole repo against itself for drift; never a routine gate"
checked_by:  null
defines:     ["very deep check"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review"
---
## Rule
When a person explicitly asks for a "very deep check", or after work that
invites drift (a batch of practices added or reordered, a practice that
changed shape, an install into a new repo, a merge that resolved conflicts
across several shared files), run
[tools/very_deep_check.py](tools/very_deep_check.py): it enumerates this
checkout's own top-level documents and deliverable content, plus the
`practices/*.md` tree of every source in force (resolved the same way
[tools/precedent_resolve.py](tools/precedent_resolve.py) does for ordinary
loading), and hands the invoking session a fixed checklist of drift
categories to read that scope against. Never wired into a commit, push, or
merge gate — the mechanical audits and `routing-audit` already cover what
can be checked cheaply and often; this covers what can only be judged, and
is deliberately rare because the judging is expensive.

## Detail
**This is not `full-practice-audit` under another name — the two ask
different questions.** `full-practice-audit` asks, practice by practice,
"is this specific practice's Rule satisfied?" — a closed question against
one Rule at a time. The very deep check asks a question no single
practice's Rule can be checked against: "does the repo's own writing still
hold together?" A contradiction between two documents, a stale
cross-reference, a rule restated in three places, a heading that drifted to
the wrong capitalization scheme — none of these is a violation of any one
practice's Rule text; each is a property of the documents *as a set*, which
is exactly what a per-practice sweep cannot see no matter how many times it
runs.

**What to look for — a starting point, not a specification. Report
anything that makes the repo harder to trust or follow, whether or not a
bullet below names it:**

- **Contradictions** — two rules, or two documents, that can't both be
  followed; a rule whose own carve-outs have eaten it.
- **Stale references** — a slug, practice number, filename, heading, or
  click-path pointing at something moved or gone; a positional number cited
  as if it were a name; numbering that skips, repeats, or runs out of order;
  an orphaned name a rename elsewhere left behind in this repo's own prose.
- **Fragments** — a sentence, note, or heading left behind by an earlier
  edit: a "temporary" caveat whose occasion has passed, a note about a
  reorganization that already happened.
- **Needless repetition** — the same rule stated in full in several places,
  where one statement plus pointers would do.
- **Disproportion** — paragraphs of detail on a minor point, prose that
  emphasizes an aside more than the point it supports, a rule grouped where
  it no longer fits.
- **Process-cost disproportion** — a rule that's minor in the scheme of
  things but costs a disproportionate amount of tokens, time, or friction
  each time it applies, especially one re-researched from scratch on every
  occurrence instead of following a written-down answer.
- **Formatting and spacing drift** — inconsistent heading levels and
  capitalization, a bullet missing the blank line its neighbors have, mixed
  list markers, a ragged table, stray blank lines or trailing whitespace, a
  stale "last updated" header.
- **Self-application** — a rule this repo asks of every project it's
  installed into that this repo doesn't yet follow itself.
- **Backlog drift** — a `TODO.md` (or equivalent open-items document) entry
  already done, no longer relevant, or never actually decided.
- **Anything else the read turns up** — if something is wrong and none of
  the categories above name it, it is still a finding; if it is the kind of
  thing that will recur, add a bullet here so the next very deep check looks
  for it deliberately.

Fix what the review turns up in the same pass — these are almost always
small — then re-run the mechanical audits, since the fixes themselves can
break a link. Anything deliberately left alone gets a line in `TODO.md`
saying so, rather than being silently dropped.

## Why
The mechanical audits (`doc_lint.py`, `leak_gate.py`, `precedent_check.py`,
`doc_sync.py`) catch broken links, bad syntax, and enforcement drift; the
routing audit catches a practice that should have fired and didn't. None of
them reads a document's own argument for whether it still makes sense —
that's a judgment call by design, not a gap any of them is meant to close,
which is exactly why this stays a separate, on-demand mechanism rather than
folded into one of the three.

**Read this before trusting the result, the same caution
`full-practice-audit` states for itself.**
[spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md)'s review-arm result
(54% recall on a whole-catalogue judgment pass, worse than no review at all)
was measured against practice-compliance judging, not document-coherence
reading — a different task, so that figure does not transfer here directly
— but nothing has evaluated this specific mechanism's own reliability
either. Treat it the same way: a backstop for what enforcement cannot
reach, not a substitute for enforcement, until it has its own evaluation.

## Story
Named in [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s v28 amendment
(2026-09-01) as "the inherited RepoPersonalPreferences (RPP) audit list ...
heavier than any of [light check, deep check, routing audit] ... not yet
inventoried here (RPP is a separate private repo); enumerate and wire it as
an on-demand tool when phase 5 or later actually needs it" — tracked nowhere
else, the same
structural gap [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md)
found `routing-audit` fell into, and logged there as `TODO.md` item 17.

Enumerating it turned up something the v28 amendment's own author could not
have known: earlier that same day, the phase-3 private-set migration
(v27) had already carried this exact list into
[`precedent-team-maintainers`](https://github.com/themorgan/precedent-team-maintainers)
as its own `deep-check` practice, generalized (RPP's own vendored-tree
language dropped, since Precedent's private sets aren't vendored the way
RPP's `process/` tree was) but otherwise the same enumeration as here. So
the list was never actually missing — it just wasn't recognized as the
fulfillment of this commitment, and it existed only as prose in a private
team practice with no companion engine, one repo away from where a
Precedent user without access to that private team set could reach it. This
practice and its tool are the universal version: available to any repo
running Precedent, not only Morgan and Alex's. Whether
`precedent-team-maintainers`' own `deep-check` should now point at this one
via `overrides:`, or stay a separate team-level statement of the same rule,
is the team's own call — noted, not decided, here.

## Install
[tools/very_deep_check.py](tools/very_deep_check.py) enumerates the scope
(this checkout's own top-level documents plus every active source's
`practices/*.md` tree, reusing `tools/precedent_resolve.py`'s own source
resolution) and prints the checklist above for the invoking session to
apply. No mechanical `checked_by` exists for this practice's own Rule, and
can't: what it asks for is a session's judgment applied to a scope the tool
enumerates, the same class of resistant-to-automation practice
`full-practice-audit` and `mistakes-become-rules` already name. See
[full-practice-audit](full-practice-audit.md) for the narrower,
already-built sibling this one deliberately does not replace, and
[spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) for the decision
record this practice's own build closes out.

---
slug:        speculation-is-marked
title:       A speculative document says so four times
tier:        on-demand
severity:    default
applies_to:  ["spec/SPECULATIVE_*.md", "record/SPECULATIVE_*.md"]
occasion:    "recording exploratory thinking -- an idea nobody has committed to -- as a document"
gates:       ["merge"]
index_clause: "mark it in filename, title, opening block and PR -- four places, or none"
checked_by:  "tools/precedent_check.py"
defines:     ["speculative document"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-09"
approved_by: "Morgan, 2026-09-09"
strength:    decided
---
## Rule
**Write the speculation down — and mark it, in four places.** A brainstorm
worth keeping is worth keeping ([repo-is-memory](repo-is-memory.md)); what it
must never do is arrive looking like a plan.

For a document recording an idea nobody has committed to:

1. **The filename** carries a `SPECULATIVE_` prefix.
2. **The title** — frontmatter and `#` heading alike — opens with the word
   *Speculative*.
3. **The first thing under the heading** is a block saying nobody has decided
   this, it may never happen, and no other document should cite it as a
   commitment.
4. **The pull request** that lands it says the same, in its title and its
   body.

**Four, because a reader arrives from four directions** — a file listing, a
search hit, the document itself, a review queue — and any one of them reached
alone has to be enough.

**The register is part of the marking.** Do not write speculation in the
voice of a plan: no owners, no dates, no "ships in the first quarter".
Phases as structure are fine; phases as schedule are not.

**And the converse binds too.** A document that IS an intention must not
carry these markers, or they stop meaning anything.

## Detail
**Where the line actually falls.** The test is not how likely the thing is,
or how much work went into the document. It is whether **anyone has decided
to do it**. A design nobody has agreed to build is speculative however
detailed it is; a scrappy two-paragraph note about work that is definitely
happening is not.

**Under the lifecycle header** ([document-status-header](document-status-header.md)),
a speculative document is `kind: proposal` with `status: drafted` — or
`abandoned`, once it is dead. It cannot be `accepted` or `executed`: **the
moment somebody decides to do it, it stops being speculative**, and the
markers come off. That is a rename, so
[rename-updates-links](rename-updates-links.md) applies to the same commit.

**The other half of the split is already conventional and stays advisory.**
An intention someone means to carry out titles itself `Plan: …`. That is not
enforced, because a mechanical rule demanding it would fire on documents that
are perfectly correct today — a plan whose title happens to name its subject
first is not a defect ([checkable-gets-checked](checkable-gets-checked.md):
a check that fires on legitimate work teaches the next session to ignore the
gate). So the enforced half is the speculative side only, in both directions:
the prefix requires the other markers, and the markers require the prefix.

**What the check cannot see, and why it is written as a rule anyway:**

- **The pull request.** A check runs against a tree; the pull-request body
  lives on a hosting platform the gate cannot read offline or in continuous
  integration. Marker 4 is therefore prose, and the `merge` gate is what puts
  it in front of a session at the moment it writes one.
- **Whether an unmarked document is speculative.** No mechanism can read a
  conversation and tell an intention from an idea. The check catches the
  document that says it is speculative somewhere and not everywhere — drift
  between the markers — not the one that never says it at all.

## Why
**Speculation and intention are the same shape on disk.** Both are a
carefully argued document under `spec/`, both carry `kind: proposal`, and a
file listing ranks them identically. A reader — a person skimming, or a cold
session that will act on what it finds — has nothing to separate *we are
doing this* from *somebody wondered about this once*.

**The failure is silent and compounding.** Nobody discovers that a
speculative document was read as a plan; they discover work built on it, or a
second document citing it as settled, weeks later. By then the mistaken
reading is the one in the repository, and the original thinking is what gets
blamed for it.

**Which is why it is four markers and not one.** A single frontmatter field
is invisible to the person reading a file listing, a search result, or a
merge queue. The redundancy is the point: **any one of the four, encountered
alone, is enough to stop the misreading**, and no reader has to have arrived
by the route the author imagined.

**And the cost of over-marking is nearly zero.** A plan mistakenly labelled
speculative is corrected in a word by anybody who notices. The other error
does not get noticed.

## Story
**Morgan, 2026-09-09**, after a brainstorm about reaching a project
repository through WhatsApp had been written up and merged: *"Maybe
speculative brainstorms are okay to be recorded but need to be prominently
labeled as such, in the filename, title, first sentences of the content, the
PR, etc. ... They need to be strongly separated from 'Plans'."* The four
places are his; the rule generalizes what that one document had just done.

The near-miss it comes from was in the tree already. `spec/` held two
documents titled `Plan: …` — one a locked-down access pattern awaiting
execution, one a team capture pilot with two of its steps genuinely done —
and both carry exactly the frontmatter a pure brainstorm would carry. Filed
beside them, a speculative design was indistinguishable from committed work
by anything a reader sees first: the same directory, the same `kind`, the
same weight of prose.

Nothing had gone wrong yet. **The document that prompted this was written
with all four markers, because its author asked for them** — which is the
point: the discipline existed in that one thread and in nobody's memory
afterwards, and the next session to write a brainstorm would have had no
reason to repeat it.

## Install
`python3 tools/precedent_check.py --only speculation-is-marked` enforces the
drift, in both directions: a `SPECULATIVE_`-prefixed document under `spec/`
or `record/` must carry the matching title, kind, status and opening warning;
a document whose title or opening paragraph calls itself speculative must
carry the prefix. Its two limits — the pull-request body, and a document that
never says it anywhere — are recorded on the check's own registration and in
Detail above.

The gate is `merge`, since the pull-request marker is written at exactly that
moment: `python3 tools/precedent_gate.py merge`.

See [spec/DOCUMENT_LIFECYCLE.md](../spec/DOCUMENT_LIFECYCLE.md) for the
frontmatter this sits on top of, and
[spec/SPECULATIVE_WHATSAPP_BRIDGE.md](../spec/SPECULATIVE_WHATSAPP_BRIDGE.md)
for the worked example the rule came from.

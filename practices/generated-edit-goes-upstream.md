---
slug:        generated-edit-goes-upstream
title:       A change to a generated file is made in its source, never in the file
tier:        on-demand
severity:    default
applies_to:  ["AGENTS.md", "MAP.md", "GLOSSARY.md"]
occasion:    "asked to add, change or remove something in a generated file"
gates:       []
index_clause: "change the input the file is built from, never the file -- and say which input"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-11"
approved_by: "Morgan, 2026-09-11"
strength:    decided
---
## Rule
**"Add this to the glossary" is a request about the glossary's contents, not
about the glossary file.** When someone asks for a change to a generated file
— a map, an index, a glossary, a loader block, a rendered table — **do not
edit the file.** Find the input it is built from, change that, regenerate, and
**say in the reply which input you changed**, because they asked for the
output and now need to know where it actually lives.

**An edit to the render is worse than no edit at all.** It satisfies the
request visibly, survives review, and is destroyed silently by the next
regeneration — so the change is lost at a moment nobody is watching, and the
person believes it landed.

Where the input genuinely cannot express what they asked for, **say that
instead of editing around it**: the answer is a change to the generator, not a
hand edit the generator will overwrite.

## Detail
**Three places a change can go, and only the first two are durable:**

| Where | When it belongs there |
|---|---|
| **The source data** | The request adds or corrects a *fact* — a term, a row, a path, a description. In this catalogue that is almost always a practice file's frontmatter. |
| **The generator** | The request is about *how the file reads* — ordering, grouping, wording, what gets included at all. |
| The file itself | Never. |

**Finding the input is the session's job, not the person's.** They asked for
the output because the output is what they read. A session that answers
*"which practice's `defines:` field did you want that in?"* has handed back
the work it was given — see [handoff-is-pasteable](handoff-is-pasteable.md)
for what an honest handoff looks like, and note that this is not one.

**Every generated file says where its own source is, in its header**, so the
lookup is a read rather than a search: `Source:` names the input, next to the
`Regenerate with:` command that rebuilds from it. That clause is what makes
this rule followable instead of merely correct, and it is the half the
mechanical check enforces.

**This rule is about the request, not the commit.**
[generated-artifact-provenance](generated-artifact-provenance.md) already
catches a hand-edited view at the gate, and
[computed-numbers-in-scripts](computed-numbers-in-scripts.md) already forbids
editing inside a `<!--gen:-->` block. Both fire when the work is being
committed. This one fires when the request arrives, which is the only moment
at which the edit can still be routed instead of undone.

**A partly generated file is generated for this purpose.** `AGENTS.md` here is
hand-written prose around a generated loader block; a request touching the
block is this rule's, a request touching the prose is an ordinary edit. The
block's markers are the boundary, and they are in the file.

## Why
**The person is not wrong to ask for the output.** They read the glossary, the
term was missing, they said so. Nothing about that request is confused — the
indirection is ours, not theirs, and it is the kind of indirection a system
accumulates as it gets more generated. So the rule has to sit on the session
that receives the request, and it cannot be satisfied by correcting the person.

**A hand edit to a generated file fails in the worst available way.** It is not
rejected, it is accepted and then quietly reverted, at a later moment, by a
routine command nobody associates with the change. Compare a failure that is
loud at the time: every other failure mode here costs one correction; this one
costs the change plus the belief that the change exists.

**Generated files are exactly the files people most often want changed**,
because they are the indexes and the summaries — the things a reader actually
consults. So the wrong instinct gets exercised constantly, and being right
once is not enough.

## Story
**Morgan, 2026-09-11**, raising it from his own side of the failure: *"I
understand that certain files like MAP and GLOSSARY should never be edited by
hand, as per our rules, right? ... However, in the past, I've made the mistake
and told you things like, 'Add such-and-such to the glossary' for example.
Maybe we need a rule/practice/something that says that these files can not be
edited directly; and whenever there's a request to update them, to instead,
update the machinery/location/system/formula that creates them."*

**The repository was, at that moment, instructing the exact edit it forbids.**
`acronyms-glossary`'s Rule said *"when a session uses a term that isn't in the
glossary, it adds it there in the same pass"*, and its `applies_to` was
`**/*.md` — which matches `GLOSSARY.md`. So
`python3 tools/precedent_paths.py GLOSSARY.md` served that instruction to any
session about to touch the file, while `GLOSSARY.md`'s own first line said
`do not hand-edit` and `generated-artifact-provenance`'s check stood ready to
fail the commit. Three mechanisms, pointing two different ways, and the one a
session reads *first* was the one pointing wrong. The term should have gone
into the owning practice's `defines:` field; nothing anywhere said so.

**What the same measurement ruled out.** The first check proposed for this
rule was "no practice's `applies_to` may match a generated file." Run against
the real tree it would have reported **twelve practices for each of
`MAP.md`, `GLOSSARY.md` and `AGENTS.md`** — `heading-outline`,
`doc-references-are-links`, `readers-vocabulary` and nine others, every one of
them correct about the file's content and none of them telling anyone to edit
it. A check firing thirty-five times on correct work teaches the next session
to ignore the gate ([checkable-gets-checked](checkable-gets-checked.md)), so
it was dropped in favour of the header check below, and
`acronyms-glossary`'s wording was fixed by hand as the one real instance.

## Install
`python3 tools/precedent_check.py --only generated-edit-goes-upstream`
enforces the half of this rule a machine can see: **every file carrying a
`do not hand-edit` header comment also carries a `Source:` clause in that same
comment, and every path that clause names exists.** A header that says only
which script rebuilds the file tells a session how to destroy its edit, not
where to put it; a `Source:` naming a path that has since moved is worse,
because it reads as an answer.

`evals/` is excluded by name. The files there are recorded prompts from past
measurement runs — frozen inputs that happen to contain a copy of an old
loader block, not live outputs, and regenerating them would destroy the record
the run is evidence for.

**What it is blind to, stated rather than left to be discovered:** it cannot
tell a hand edit from an honest regeneration (that is
[generated-artifact-provenance](generated-artifact-provenance.md)'s check,
which asserts a fresh regeneration changes nothing), and it cannot see a
request being answered in the wrong place — no check can read the
conversation, which is why the routing half is written as a rule.

The headers themselves are emitted by
[tools/build_views.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/build_views.py), so
`MAP.md`, `GLOSSARY.md` and every source set's loader block pick the `Source:`
clause up on their next regeneration rather than needing to be edited — which
is this rule applied to itself.

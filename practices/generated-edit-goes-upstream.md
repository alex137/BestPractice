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

**And the clause the check demands was close to unsatisfiable for its first
day.** Found 2026-09-11 from a consuming repo, by a session adding a `Source:`
clause to a generator's emitted header and watching the check refuse it. The
terminator could not cross a hyphen, so a clause naming
`business-modeling/doc-recipes/OUTPUT_HTML.recipe.md` did not match at all and
the file was reported as carrying **no clause** — sending a reader to hunt for
something sitting in the header they were already looking at. Hyphenated paths
are the common case in these repos, not the edge case. A second fault sat
underneath: the terminator stopped at any `.`, so even the hyphen-free
`Source: docs/plain.md` was read as `docs/plain` and reported as a path that
does not exist.

**Both messages named the wrong problem**, and that is the part worth keeping.
A rule whose check is wrong costs more than a rule with no check at all,
because the session it defeats is the one trying hardest to comply — and a
session told its clause is missing will write a second one rather than doubt
the gate. The consuming repo left its clause in place on the grounds that it
was correct and a human could read it, which was the right call: nothing on
that side needed editing.

**Then the same consuming repo came back, 2026-09-12, with the case the
grammar could not express at all: a file built in one repo and MIRRORED into
another.** Its source is not a path in the repo the header sits in, and never
will be. Three wordings were tried on the same two files and all three were
refused, each differently:

| What the header said | What the check said |
|---|---|
| No `Source:` clause | *"carries a `do not hand-edit` header with no `Source:` clause"* — correct |
| The building repo's own paths, `voice/` and two more | *"names `voice/` as its Source and that path does not exist"* |
| A URL to the building repo | *"has a `Source:` clause naming no path at all"* |

**The middle row is the one that decided the design.** By this practice's own
reasoning a `Source:` that has moved is *worse* than none — it reads as an
answer — so the honest attempt to comply produced a state the rule itself
calls worse than the one it started in. And the third row is a header a human
reads correctly: the reader knows exactly where to go, and the check says it
names nothing.

**Naming the repo in a URL was the obvious fix and it pulls against a rule
already in force.** `private-repo-scrub` and
[tools/precedent_materialize.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_materialize.py)'s
`_rewrite_links` both refuse to mint a URL naming a private repository into
content that ships — *"a relative link that does not resolve is a smaller
failure than a disclosure that cannot be taken back"* — and the building repo
in this instance is private. A check whose only route to compliance was a URL
would have been pushing authors straight at that refusal. **So the clause
names a PLACE instead, in free text the author chooses**: a repository where
naming it is fine, a plain label where it is not. The leak gate stays the one
thing deciding which, and this check has no opinion at all.

**What was ruled out, and why it is worth recording:** exempting mirrored
files from the header requirement. It is the shortest fix and it removes the
routing from the file that most needs it — a reader holding a mirror is
further from the source than anyone, not closer.

## Install
`python3 tools/precedent_check.py --only generated-edit-goes-upstream`
enforces the half of this rule a machine can see: **every file carrying a
`do not hand-edit` header comment also carries a `Source:` clause in that same
comment, and every path that clause names exists.** A header that says only
which script rebuilds the file tells a session how to destroy its edit, not
where to put it; a `Source:` naming a path that has since moved is worse,
because it reads as an answer.

**Two forms, and the difference is whether this repository is where the
answer is:**

| Form | Means | What the check does |
|---|---|---|
| `Source: <path>` | The source is in this repo | Every path named must exist. A path that has moved is a violation |
| `Source (<place>): <path>` | The source is in `<place>`, which this repo is not | Nothing is resolved. Every address named is reported `COULD NOT VERIFY`, by file, on every run |

**The parenthetical is free text on purpose** — `(in the Voice pack)`,
`(in acme/toolkit)`, a URL, whatever names the place to the person reading.
Demanding a fixed phrase would rebuild the trap the row above this one
describes: a near-miss reported as *"no clause"*, sending a reader to hunt for
something sitting in front of them. What the check takes from it is one bit —
*not here* — plus the requirement that an address follow it, because a reader
who reaches the right repo and has no path is no better off.

**A qualified `Source:` resolves nothing, including a path that happens to
exist here.** `examples/` is a directory in half these repos; verifying the
tokens that resolve locally made a coincidence render identically to a
verification, which is the one thing
[fail-gracefully](fail-gracefully.md)'s first clause does not allow. The cost
lands where it should: a repo that BUILDS a mirrored file and emits the
qualified header into its own tree too gets one could-not-verify line at
home, and the fix is for its generator to emit the plain `Source:` locally —
the accurate header there anyway.

**`COULD NOT VERIFY` is its own outcome**, printed per file every run,
counted separately in the summary, and it does not fail the run: nobody
holding a mirror can act on it, and a finding nobody can act on is how a gate
becomes wallpaper ([checkable-gets-checked](checkable-gets-checked.md)).
`--strict` fails on it, for a caller that has decided otherwise.

**Where the clause ends, since the check has to decide somehow:** it runs from
`Source:` to the first of ` -- ` (this project's prose dash, spaced), an em
dash, a period followed by whitespace, or the end of the comment. A path
therefore keeps its hyphens and its extension —
`doc-recipes/OUTPUT_HTML.recipe.md` is one token to the check — and the
sentence explaining the source belongs *after* a ` -- `, where it is not
scanned for paths. Written the other way round, that prose is checked as
though the header had named every path-shaped word in it.

**Writing ABOUT this check makes the file a generated view.** The marker is an
ordinary phrase, so quoting a header — in a fixture, a backlog item, a
document explaining the rule — puts a real one in a file that has no source,
and the check correctly reports the file that describes it. Both happened on
2026-09-11, in [tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/verify_harness.py)
and in [TODO.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md),
within an hour. **Assemble the marker from pieces rather than spelling it**
(`'do not ' + 'hand-edit'`), or describe it without quoting a whole comment.
The check is right in both cases: it cannot tell a header from a sentence
shaped like one, and should not try.

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

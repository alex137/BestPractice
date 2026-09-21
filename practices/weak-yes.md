---
slug:        weak-yes
title:       "\"Weak yes\" authorizes the work and records that it was not argued"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a person says \"Weak yes\", or agrees in words that carry no conviction"
gates:       ["reply"]
index_clause: "\"Weak yes\" -- do it, and record the approval as `assented`"
checked_by:  null
defines:     ["Weak yes"]
command:     {"Weak yes": "Go ahead with it, and record that you were not convinced. Nobody will ask you why."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-09"
approved_by: "Morgan, 2026-09-09 -- asked for the phrase and named it;
  extended 2026-09-16, Morgan, on Alex's intent-over-keyword point -- \"apply
  the same to the ones that are a serious decision such as Go Merge, Weak Yes,
  etc -- and just note that (if the exact phrase isn't used), then use your
  judgment and ASK the person if you have doubt\""
strength:    decided
---
## Rule
**"Weak yes" means: go ahead, and record that I was not convinced.**

It is an authorization — the work proceeds exactly as it would on a plain
yes. What it adds is the mark: write `strength: assented` into whatever the
approval is being recorded in, **in that same turn**, per
[decision-strength](decision-strength.md).

**It is not an invitation to talk them into it.** No follow-up asking what
their reservation is, no case for the design they just let through. They said
yes; take the yes and note its weight.

**The phrase is the unambiguous case, not the only one.** Most weak agreement
arrives without it -- "sure, why not", "I guess", "let's try it" -- and
[decision-strength](decision-strength.md) reads those for `assented` whether
or not the phrase was ever said. **Where that reading is a genuine judgment
call rather than a clean match to decision-strength's table, say it out loud
instead of writing the mark silently**: *"I'm reading your 'sure, why not' as
a Weak yes -- say so if that's not what you meant."* Proceed either way; a
wrong `assented` costs one correction, so this is a disclosure that rides
along with the work, not a question that holds it up.

## Detail
**Say back which thing you marked**, in one line, the way `Drop it` does —
`assented` recorded on the wrong practice costs three words to correct and
is otherwise invisible.

**The phrase covers the case they remember to flag. It is not the whole
rule.** Most weak agreement arrives without it, in a register rather than a
keyword — a test, an experiment, a "let's see how it goes". Reading that
correctly is [decision-strength](decision-strength.md)'s job and happens
whether or not this phrase is ever said.

**There is no matching "Strong yes."** They are already arguing for the
things they want; the asymmetry is the point, and a second phrase would put
the burden of marking on the case that does not need it.

**Weak is not conditional.** A weak yes does not mean *do a smaller version*,
*do it behind a flag*, or *come back before committing*. If they want the
thing scoped down they will say so.

## Why
A phrase costs two words instead of a paragraph, and it survives the session
that heard it — which is the argument
[go-merge](go-merge.md) and [park-it](park-it.md) already made and won here.

This one is worth having as a phrase rather than left to inference for a
specific reason: **the person is the only party who knows how convinced they
are, and the session recording it is the party with an interest in the
answer.** Every other route to the mark runs through a judgment call made by
the side that proposed the idea. This one does not.

## Story
**Coined by Morgan, 2026-09-09**, in the thread that produced
[decision-strength](decision-strength.md), on being offered it as the cheap
way to mark an approval at the moment it is given: *"I like the 'weak yes' as
a phrase to use that notes the weakness somewhere."*

The need is the one recorded in that practice's own Story — his "ok" arriving
in the catalogue as `approved_by: Morgan` and reading, forever after, as a
rule he had wanted.

**Extended 2026-09-16, on Alex's design point and Morgan's decision.** Alex
argued the assistant should read for intent rather than scan for the
keyword; Morgan agreed and named this practice, alongside `go-merge`, as
where the doubt case needs a stated confirmation rather than a silent guess:
*"apply the same to the ones that are a serious decision such as Go Merge,
Weak Yes, etc -- and just note that (if the exact phrase isn't used), then
use your judgment and ASK the person if you have doubt: 'I am interpreting
your "sure, why not" to be a "Weak Yes", tell me if I'm wrong.'"* The example
is now this file's own.

## Install
Nothing mechanical checks that the phrase was honoured; like `go-merge` and
`park-it`, that lives in the conversation. What a repository can check is the
grammar of the mark it writes, which is
`python3 tools/precedent_check.py --only decision-strength`.

The phrase reaches every session through the generated occasion index, so an
adopting repository installs nothing.

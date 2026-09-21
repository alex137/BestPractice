---
slug:        fence-block-for-paste
title:       Text meant to be copied elsewhere goes in its own fence block
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "a reply hands over text meant to be pasted somewhere else -- a prompt, a commit message, a PR description, a config snippet, a comment for another tool"
gates:       ["reply"]
checked_by:  null
defines:     ["fence block"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-20"
approved_by: "Morgan, 2026-09-20 -- via rule-scope-ask, on a handoff session's
  recommendation to generalize my-options.md and prompt-please.md's
  fenced-block requirement beyond those two trigger phrases. Asked whether
  the rule belonged as a new resident practice, as more bullets on the two
  on-demand commands, or as a third on-demand command with its own trigger;
  chose the new resident practice. In the same exchange, asked that
  my-options and prompt-please name the term \"fence block\" explicitly
  rather than call it \"the block,\" since both files already use \"block\"
  for something else (an option's own short paragraph)."
strength:    decided
source_practice_number: null
---
## Rule
Any reply that hands over text meant to be pasted somewhere else — a prompt
for a new session, a commit message, a PR description, a config snippet, a
comment for another tool — puts that text in a **fence block**: an actual
fenced markdown block (triple backticks), never a paragraph that only reads
as paste-ready. The fence is what gives the client its one-click copy
button; describing the text without fencing it has not delivered it,
whatever else the reply says.

**More than one distinct thing to paste gets more than one fence block.** A
commit message and a separate PR description, two prompts for two different
sessions — each is its own fence block, never one block holding both, and
never prose gesturing at several pieces and leaving the reader to split them
apart.

**This binds every reply, independent of any trigger phrase.**
[My options](my-options.md) and [Prompt Please](prompt-please.md) each
already required a fence block for their own occasion; both now point here
instead of restating it.

## Detail
**This fires wherever the paste-ready text appears in a reply, not only at
a close.** [The Boildown](the-boildown.md)'s handoff bullet already carries
this same requirement when a reply is pointing the person at another
session at its very end; this practice is what makes the same requirement
fire at any other moment a reply hands over exact text — mid-reply, before
a decision is made, anywhere a reply is producing text rather than
describing an intent to produce it.

**An offer to write something is not yet handing it over.** "I can draft a
commit message if you want" names an intent; the fence-block requirement
fires once the actual text is produced, not before.

## Why
A paragraph that merely reads as paste-ready still has to be selected,
copied, and manually stripped of surrounding prose before it can go
anywhere else — the fence is the only thing a client actually turns into a
one-click copy button, so a reply that skips it has described a shortcut it
did not build.

Gating this behind two on-demand commands' own trigger phrases reproduced
the same failure one level down: the fence only appeared when someone
remembered to say "My options" or "Prompt Please," and any other
copy-paste request — "give me a prompt I can copy," a commit message to
hand off, a snippet to paste elsewhere — got nothing.

## Story
`my-options` and `prompt-please` each already required a fence block,
tightened the same day they were extended (2026-09-20) after Morgan found
both were often delivered as prose that merely read as paste-ready rather
than an actual fenced block. A separate session, rooted in a different
repository, was then asked for "a prompt I can copy" — wording that
triggered neither command by name — and handed back a published Artifact
page with a copy button instead of the ordinary chat mechanism. Morgan said
plainly he wanted the fenced block a chat reply already renders with its
own copy icon, not a page. That session wrote up the gap as a handoff: the
requirement only bound two occasion-gated commands, so any other
copy-paste request fell through the same way this one just had, and a reply
with more than one distinct thing to copy had no rule at all saying each
gets its own fence.

Handed to a fresh session rooted here. Per `rule-scope-ask` (a private
team practice on where a proposed rule's scope belongs), the scope was
genuinely unclear, so the session asked once, with a guess and its reason —
a new resident practice, on the grounds that a third on-demand command
would reproduce the exact "nothing fires without the phrase" gap one level
down. Morgan chose the resident practice over extending the two on-demand
commands in place or adding a third trigger, and asked in the same
exchange that `my-options` and `prompt-please` name the fence block
explicitly rather than call it "the block," to keep it distinct from the
other things those files call a block. strength: decided.

## Install
Nothing to configure. Same as [my-options](my-options.md) and
[Prompt Please](prompt-please.md), the artifact this governs is a chat
reply, not a file the tree holds, so there is nothing for a tree-scoped
check to read. The reply gate carries it instead: registered on `reply`,
so it is in scope at the moment a reply is being written, not only after
it is sent. No mechanical check.

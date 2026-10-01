---
slug:        root-issues
title:       "\"Root issues\" asks what this session found that should be fixed upstream, as Prompt Please blocks"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE, about the whole session so far -- no file path reaches it. Routed by the occasion index and the `reply` gate. Decided: 2026-10-01, when the practice landed."
occasion:    "a person says \"Root issues\" or \"Root fixes\", or asks what this session found or fixed that should go back upstream"
gates:       ["reply"]
gates_why:   "The whole obligation is one reply: every finding from the session that belongs upstream, each as a Prompt Please block, or a plain none."
index_clause: "what this session hit that belongs upstream, each as a Prompt Please"
checked_by:  null
defines:     ["Root issues", "Root fixes"]
command:     {"Root issues": "Look back over everything this session has done so far -- every bug, issue or warning it ran into, and every fix or band-aid it applied -- and hand you each one that should also be fixed in Precedent, a precedent-* repo, the template that generates the file, or another related repo, each as a paste-ready Prompt Please -- including ones you may already have passed on from another session.", "Root fixes": "The same as **Root issues**."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-01"
approved_by: "Morgan, 2026-10-01 -- coined both names and wrote the meaning
  himself, in the message that retired \"Upstream fix\" as a command:
  \"let's remove or replace it with something like 'Root issues' or maybe
  'Root fixes' or maybe one as a synonym for the other\"; widened by
  Morgan the same day to take in the fixes and band-aids a session applied
  and the templates and related repos they reach, by replacing the
  quoted paragraph with his new wording"
strength:    decided
---
## Rule
**"Root issues" and "Root fixes" mean the same thing, and neither is the only
form.** "Anything here we should send upstream?" asks the same question and
gets the same answer. When the person says it, answer as if they had asked
this:

> In everything you did this session so far, did you find any bug or issue
> or even a warning in this session that you found that you think should be
> given back to Precedent or a precedent-* file to be fixed or stop the
> warning upstream? I might have already given some that you mentioned
> before, and I might have encountered similar issues in other simultaneous
> sessions and already passed it upstream, but maybe not. If there are any,
> then give them to me as a Prompt Please. This includes looking at fixes
> and band-aids you applied here, that would apply to other repos,
> including the original templates that generate other files and in
> other, related repos.

**The whole session, not the last change.** Go back over every turn: tool
output, hook output at session start, check results, a warning that scrolled
past and was never mentioned, a rule that steered you wrong, a step you had
to work around. A warning counts as much as a failure; the question is
whether its cause lives somewhere other than here, not how loud it was.

**Your own fixes count too, band-aids above all.** Every fix this session
made or recommended gets the same question: does it also belong somewhere
else? A band-aid applied here is the clearest case, since by definition
its root is still open.

**Upstream means anywhere the same fix also belongs**, in at least these
places:
- **Precedent** (BestPractice, the engine every repo vendors) and the
  **precedent-* practice sets**;
- **the original template** a file here was generated or copied from,
  wherever it lives;
- **other, related repos** that carry the same file, the same mistake or
  the same template's output.

A bug in the repo this session works in, with its cause there too and
nowhere else, is ordinary work, not a root issue. A vendored or generated
copy is its origin's: fixing the copy here does not fix it, and the next
update brings it back ([upstream-fix](upstream-fix.md), points 2 and 8).

**Include the ones that may already be known.** The person may have passed
the same thing on from this session or another one. Say so on the item when
you mentioned it earlier in this session, and give it anyway; a duplicate
costs them one glance, a dropped finding costs another round of the same
bug.

**Each finding is one [Prompt Please](prompt-please.md) block**, in that
practice's form: situation, problem, recommendation, origin, seed root and
attachments. Related findings bound for the same repo may share a block.
Under that rule a block carries no merge authorization unless the person
gave one for this handoff.

**When there are none, say so in one line**, and say what you looked at.
Never manufacture a finding so the answer has something in it
([no-invented-specifics](no-invented-specifics.md)).

## Detail
**A finding this session can fix where it stands is not a handoff.** A
session rooted in BestPractice, or with push access to the precedent-*
repo the finding belongs to, says that next to the item and offers to fix
it here instead of writing a prompt to itself. A handoff is for the part
this session cannot do.

**This is not [upstream-fix](upstream-fix.md).** That practice is about the
fix in front of the session and applies to every fix it reports, asked or
not. Root issues looks back over the whole session for anything whose cause
or fix belongs elsewhere, fixed here or not, and returns it as handoffs; it
is the sweep that catches what upstream-fix missed at the time.

## Why
A session working in a consuming repository runs into Precedent's bugs as
side effects: a hook that warns at startup, a check that misfires, a rule
that sends it the wrong way. It works around them, because they are not
the task, and the knowledge goes when the session is archived
([repo-is-memory](repo-is-memory.md)). Asking at the end catches them, but
only if the question is asked in full, and the full question is a paragraph.
**A named command is that paragraph, written once**, the same move as
[three-things](three-things.md).

## Story
**Coined by Morgan, 2026-10-01**, replacing "Upstream fix" as a command. He
had stopped using that phrase: it asked about one fix on demand, and by then
he wanted upstream fixing done every time, without asking. What he kept
asking instead, by pasting the same paragraph into session after session,
was the question quoted above. He offered "Root issues" and "Root fixes"
and left it open which was the synonym; the session that built this made
"Root issues" the main name, as the one he listed first. Strength: decided.

**Widened the same day.** Morgan replaced the quoted paragraph with a
longer one adding *"fixes and band-aids you applied here, that would apply
to other repos, including the original templates that generate other files
and in other, related repos."* The first version only looked for problems
whose cause was in Precedent; a session's own band-aids, and the templates
and sibling repos they also apply to, are where the cause most often stays
behind. Strength: decided.

## Install
Nothing mechanical checks that a reply found every upstream finding: whether
a warning's cause lives upstream is a judgment about that warning, and the
session's own history is not something a script can read afterwards. What
reaches a session is the occasion index entry and the `reply` gate, both
generated, so an adopter installs nothing.

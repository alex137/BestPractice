---
slug:        root-issues
title:       "\"Root issues\" asks what this session found that should be fixed upstream, as one Prompt Please for every repo it touches"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE, about the whole session so far -- no file path reaches it. Routed by the occasion index and the `reply` gate. Decided: 2026-10-01, when the practice landed."
occasion:    "a person says \"Root issues\", or asks what this session found or fixed that should go back upstream"
gates:       ["reply"]
gates_why:   "The whole obligation is one reply: every finding from the session that belongs upstream, in one Prompt Please block for a session rooted in all their repos, or a plain none."
index_clause: "what this session hit that belongs upstream, in one prompt across those repos"
checked_by:  null
defines:     ["Root issues", "Root fixes"]
command:     {"Root issues": "Look back over everything this session has done so far -- every bug, issue or warning it ran into, and every fix or band-aid it applied -- and hand you each one that should also be fixed in Precedent, a precedent-* repo, the template that generates the file, or another related repo, all in one paste-ready Prompt Please for a single session rooted in every repo they touch, with those repos named first -- including ones you may already have passed on from another session.", "Root fixes": "The same as **Root issues**."}
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
  quoted paragraph with his new wording; and again the same day, to one
  prompt for a session rooted in every relevant repo instead of one block
  per finding; widened by Morgan on 2026-10-08 to fix the warnings a session
  got, ranked after what broke or could break something; narrowed by Morgan
  on 2026-10-16 to one name, \"Root issues\", with \"Root fixes\" kept only
  as a synonym: \"I'd like to rename 'root fixes' as in the command
  everywhere to 'root issues'. We can still accept it as a synonym or
  interpret the meaning, but not as the primary phrase used\""
strength:    decided
---
## Rule
**"Root issues"** -- or "Root fixes", or any plain "anything here we should
send upstream?" -- **asks what this session hit that should be fixed
upstream, handed over as one [Prompt Please](prompt-please.md).** A session
only ever writes "Root issues": the command finds the issues and hands them
on, and the session the prompt goes to fixes them. The person's own words
are under "The command and the question in full", in Detail.

**Go back over the whole session, not the last change**: tool and hook
output, check results, a warning that scrolled past, a rule that steered
you wrong, a step you worked around, and every fix this session made or
recommended, band-aids above all.

**Upstream means anywhere the same fix also belongs**: Precedent and the
precedent-* sets, the original template a file came from, and related repos
carrying the same file or mistake. A bug whose cause lives only in this repo
is ordinary work; a vendored or generated copy is its origin's.

**Order the findings by harm, and say which each is**: first what broke
something, then what could, then warnings. A warning whose cause is
upstream goes in as a fix to make. **Two parts of the system fighting is
the first finding**: name both parts, look for earlier rounds of the same
fight, and recommend settling which part owns the thing. A recurring
warning is traced to its cause here, once
([verdict-not-mechanism](verdict-not-mechanism.md)).

**Include the ones that may already be known**, saying so on the item.

**All the findings go in one Prompt Please block**, for one session that
holds every repo they touch, named in plain prose before the block: one
section per finding (situation, problem, recommendation, the repo it lands
in), and no merge authorization unless the person gave one for this
handoff.

**When there are none, say so in one line**, and what you looked at. Never
manufacture a finding ([no-invented-specifics](no-invented-specifics.md)).

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

Everything under the headings below from "The command and the question in full" on was the Rule's own text until 2026-10-31, moved here whole when the Rule was cut to what a session must do (Story, 2026-10-31). The Rule names each heading where it needs it.

### The command and the question in full

**The command is "Root issues."** "Root fixes" still works as a synonym, and
so does any plain question like "anything here we should send upstream?" All
of them get the same answer. **But a session only ever writes "Root issues"**,
because the command finds the issues and hands them on. It does not fix them;
the session the prompt goes to does. When the person says it, answer as if they had asked
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
> other, related repos. Assume there is one session rooted in all the
> relevant repos together, and give it to me as one prompt (as always,
> telling me beforehand which sessions to root it in).

### The whole session, and your own fixes

**The whole session, not the last change.** Go back over every turn: tool
output, hook output at session start, check results, a warning that scrolled
past and was never mentioned, a rule that steered you wrong, a step you had
to work around. A warning counts as much as a failure; the question is
whether its cause lives somewhere other than here, not how loud it was.

**Your own fixes count too, band-aids above all.** Every fix this session
made or recommended gets the same question: does it also belong somewhere
else? A band-aid applied here is the clearest case, since by definition
its root is still open.

### Harm order, fights and recurring warnings

**Warnings are fixed too, after what breaks.** A warning whose cause lives
upstream goes into the prompt as a fix to make -- stop the warning at its
source -- never as a note to read. Order the findings by harm: **first what
broke something, then what could break something, then warnings**, and say
which of the three each one is. A long list of warnings never pushes a
breakage down the prompt or out of it.

**Two parts of the system fighting is a finding of its own, and the
first one.** When this session restored, re-added or worked around something
another part of the system removed or broke, the root issue is the conflict,
not the thing restored. Name both parts, search history for earlier rounds
of the same fight, and recommend settling which part owns the thing, not
another patch for the latest symptom. A person should never have to spot
the pattern for you.

**A recurring warning is traced, not recited.** A warning this session saw
that earlier sessions saw too has its cause found here, once, and that cause
goes in the prompt ([verdict-not-mechanism](verdict-not-mechanism.md)).

### Where upstream is

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

### Known ones, the block, and none

**Include the ones that may already be known.** The person may have passed
the same thing on from this session or another one. Say so on the item when
you mentioned it earlier in this session, and give it anyway; a duplicate
costs them one glance, a dropped finding costs another round of the same
bug.

**All the findings go in one [Prompt Please](prompt-please.md) block**,
for one session that holds every repo they touch. **Before the block**, in
plain prose, say which repo to root that session in and which others to
attach, the way Prompt Please always does. Inside it, one section per
finding: the situation, the problem, the recommendation and the repo it
lands in, plus the block's origin line once. Under that rule the block
carries no merge authorization unless the person gave one for this
handoff.

**When there are none, say so in one line**, and say what you looked at.
Never manufacture a finding so the answer has something in it
([no-invented-specifics](no-invented-specifics.md)).

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

**One prompt, not one per finding, also 2026-10-01.** Morgan added the last
sentence of the quoted paragraph: *"Assume there is one session rooted in
all the relevant repos together, and give it to me as one prompt."* Several
blocks meant several new sessions for findings that often touch the same
two or three repos, and each block repeated the same setup. Strength:
decided.

**Warnings fixed, breakage first, 2026-10-08.** Morgan: *"add include in the
fixes *warnings* you got (although give priority and preference to issues
that broke or could break other things first)."* A warning was already a
finding here, and in practice still reached the prompt as an aside or not at
all, beside the failures that had cost real time. The same night a
consumer's 227 broken-link warnings, all from one upstream cause, turned out
to sit beside a defect that refused every Produce; both belonged in the
prompt, in that order. Strength: decided.

**One name, 2026-10-16.** Until then the two names were equals, side by
side in every list a person read. Morgan asked for "Root issues" alone, with
"Root fixes" kept only as a synonym, because the second name says the wrong
thing: *"you don't 'fix' those issues, you just find them and give me the
prompt, for another session to fix it."* Strength: decided.

**Two parts fighting, 2026-10-19.** A consumer's hand-written map and
glossary were erased by one writer (a full view rebuild during an update,
2026-09-15), given back as empty source files by another (the view
migration, 2026-10-05), and guarded against by a third patch for a
different hole (2026-10-12). Each round was fixed where it showed, and the
person had to point out that it was one fight over who owns the file. A
warning had been showing the loss for a month: the doc linter flagged an
unglossed acronym in every session that touched one page, because the
glossary entry defining it was gone, and every session passed it over as
known backlog. The root-issues prompt that followed asked for both
paragraphs above. Strength: proposed, from that prompt; the person's yes on
the merge decides it.

**2026-10-31: the Rule cut to what a session must do.** The Rule had grown to 808 words; it now holds what to look over, where upstream is, the order and the one block, in 317 words (both counted with `wc -w` over the section). Every paragraph it held moved word for word into Detail, under the headings the Rule names, the person's question included; nothing was deleted. Morgan asked for the longest Rules to be reviewed and shortened this way, and approved it (strength: assented); his words are in [todo-2026-10-30-very-deep-check-findings](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-10-30-very-deep-check-findings.md).

## Install
Nothing mechanical checks that a reply found every upstream finding: whether
a warning's cause lives upstream is a judgment about that warning, and the
session's own history is not something a script can read afterwards. What
reaches a session is the occasion index entry and the `reply` gate, both
generated, so an adopter installs nothing.

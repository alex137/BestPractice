---
slug:        declared-default-is-applied
title:       A setting with a declared default is applied, not asked
tier:        on-demand
severity:    default
applies_to:  ["SETUP.md", "INSTALL.md", "documentation/*.md", "templates/GETTING_STARTED.md"]
occasion:    "a setting has no value from the person -- at install, at setup, or in the middle of work"
gates:       ["reply"]
index_clause: "apply the declared default and name it in passing; never ask"
index_required: false
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-14"
approved_by: "Morgan, 2026-09-14"
strength:    decided
---
## Rule
**When a setting the person has not chosen has a declared default, apply the
default and carry on.** Do not ask, do not offer, do not open a pull request
to correct it. Name it in passing if the sentence is already being written —
*"dates are stamped in New York time until you say otherwise"* — and move on.

**Ask only when the default does not exist, or getting it wrong is expensive
to undo:** something published under their name, something destructive,
something at a security boundary. Cheap and reversible is the whole test, and
a timezone, a register, a filename convention are all cheap.

**Say once, in the document they will still have next month, where the value
lives and how to change it.** A person who never reads that page has lost
nothing; a person who notices a wrong value goes and looks.

## Detail
**A default only counts if it is declared somewhere a session reads** — a
registry key, a template, a practice — never a value a session picked because
it seemed reasonable. That is [registry-source-of-truth](registry-source-of-truth.md)
doing its usual job: this rule is what makes the declaration worth having, and
a "default" nobody wrote down is an invention
([no-invented-specifics](no-invented-specifics.md)).

**This repository's standing examples**, each declared and each applied
without a question:

| The setting | The default | Declared in |
|---|---|---|
| The zone a date or a commit is stamped in | `America/New_York` | [precedent.json](https://github.com/alex137/BestPractice/blob/staging/precedent.json)'s `fallback_timezone`, engine at [tools/precedent_time.py](../tools/precedent_time.py) |
| How to refer to a person who has not said | `they/them` | [declared-pronouns](declared-pronouns.md) |
| Whether an approval travels to another session | `refused` | `relayed_authorization` in the individual set's `identity.json` |
| What an open item with no disposition means | `wait` | [open-item-disposition](open-item-disposition.md) |

**It is the same instinct as
[INSTALL.md](https://github.com/alex137/BestPractice/blob/staging/INSTALL.md)'s
"Essentials Only", one step further out.** That section defers work that
would merely improve a working result; this one covers the value that already
has an answer, at install and equally in the middle of an ordinary day.

**A retracted reason is not a reason to reopen the value.** If the
justification written beside a default turns out to be wrong, fix the
justification the next time that file is open anyway — the value it justifies
was right either way, and a pull request whose whole content is a better
comment is the interruption this rule is about.

## Why
**The person is worst placed to answer on the day you would ask.** At install
they have the least context about the system they will ever have, and every
question is a chance to lose them before the essentials land. Mid-work, the
question is worse: it costs them the thread they were actually holding, to
decide something that was already decided.

**The asymmetry is what settles it.** Asking costs a real interruption, every
time, for everyone. Applying a default costs, at worst, a value somebody
notices later and changes in one sentence. A wrong timezone on a record is
visible, harmless and trivially fixable; the question that would have
prevented it is none of those.

**It also keeps the defaults honest.** A system that asks whenever it is
unsure never has to make its defaults good, and never has to write down what
they are. A system that must apply one silently has to declare it, document
it where the person will look, and be able to defend it.

## Story
**Morgan, 2026-09-14.** A session had committed a comment into another
project's `precedent.json` justifying the `America/New_York` fallback on a
premise it later retracted, and came back offering to set that project's zone
to Buenos Aires with an honest comment — a one-file change and a pull request.

His answer was that the offer was correct and the change was not wanted:

> I don't want to bug people installing it or setting it up with such minor
> points. This is in the instructions, and they can also ask at any time as
> well, and if they see the wrong timezone it's a minor issue and they can ask
> to fix it. So for this, and other minor stuff that we have defaults for, we
> shouldn't ask but just use the defaults — and here we have the default as
> the NY timezone.

Two things landed with it. The rule above, at universal — *still true for a
different team, a different person, a repository about something else?* yes,
three times ([rule-level-by-reach](rule-level-by-reach.md)) — and the half the
rule leans on: the personal settings a person may define, and the defaults
that apply until they do, now have a section in the guide written for people
who are not developers, where before they existed only in the per-machine
setup page a non-developer never opens.

## Install
**Nothing to wire.** The rule fires in a conversation, not in a file, so it
is routed at the `reply` gate and by `applies_to` on the documents that most
often tempt a session into asking — the install runbook, the guided setup, the
per-machine page, the reader-facing guides.

**No mechanical check, and this is the honest version of why**
([checkable-gets-checked](checkable-gets-checked.md)). What a check would have
to see is a question that was asked in chat, which leaves no trace in the
tree. The one checkable half — that every declared default is documented where
its audience reads — was considered and not built: the defaults live in four
different shapes (a JSON key, a practice's prose, a template comment, a
frontmatter field), and a check that matched them against prose would either
hardcode the list it is meant to discover or pass on anything. It stays
advisory, deliberately.

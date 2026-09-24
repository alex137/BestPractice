---
slug:              todo-2026-09-21-template-freshness-reports-five-phantom-gaps
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "a session that is not racing the one editing tools/very_deep_check.py -- two sessions were pushing to precedent-beta-v01 while this was found, and one of them owns that file right now"
noted:             2026-09-21
closed:            null
---
## What

**Every one of `TEMPLATE FRESHNESS`'s five findings is a file the bootstrap
generator writes**, so none of them is a template gap. The section has
reported a finding on all 21 of its recorded runs
([record/very-deep-check-ledger.json](../record/very-deep-check-ledger.json)),
and the run twelve lines below it says so in the same output.

`TEMPLATE FRESHNESS` on 2026-09-21:

    FINDING shared: all 3 resolved sources carry 'CLAUDE.md' and the skeleton ships no equivalent
    FINDING shared: all 3 resolved sources carry 'precedent-individual-bootstrap.sh' and the skeleton ships no equivalent
    FINDING shared: all 3 resolved sources carry 'precedent-source.json' and the skeleton ships no equivalent
    FINDING shared: all 3 resolved sources carry 'precedent-universal-catalogue.sh' and the skeleton ships no equivalent
    FINDING shared: all 3 resolved sources carry 'precedent.json' and the skeleton ships no equivalent

`BOOTSTRAP DRIFT`, next section down, same run:

    FINDING individual precedent-individual: the generator writes 'precedent-source.json' and this set does not have it
    FINDING shared precedent-shared-writing: CLAUDE.md differs from what the generator writes today
    FINDING shared precedent-shared-writing: precedent.json differs from what the generator writes today
    FINDING shared precedent-shared-writing: precedent-source.json differs from what the generator writes today

**A file cannot differ from what the generator writes unless the generator
writes it.** The two sections disagree about the same five files in every
run, and nothing reads them against each other.

## The Cause

[`_template_freshness()`](../tools/very_deep_check.py) keeps a `NOT_SKELETON`
set of files a skeleton correctly ships none of, because something else
produces them at the destination. It holds six names plus
`bss.SESSION_HOOKS` and `settings.json`.

`SESSION_HOOKS` is the wrong constant. In
[tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py):

    SESSION_HOOKS = ('freshness-guard.sh', 'commit-identity.sh', 'doc-lint-gate.sh')
    ALL_SESSION_HOOKS = SESSION_HOOKS + (INDIVIDUAL_SOURCE_HOOK,
                                         UNIVERSAL_CATALOGUE_HOOK)

`ALL_SESSION_HOOKS` exists to name exactly this set, and the generator
writes both of the extra two (`precedent-universal-catalogue.sh` is written
at `precedent_bootstrap_source.py:486`, and both are wired into the
generated `settings.json` at lines 530 and 538). Reading the narrow tuple
turns both into reported gaps.

The other three — [`CLAUDE.md`](../CLAUDE.md) (written at
`precedent_bootstrap_source.py:1261`), `precedent.json` (line 416) and
`precedent-source.json` — are simply absent from `NOT_SKELETON`.

**The comment above that line states the intent this misses**, which is
what makes it worth writing down rather than just patching:

> Read from the module rather than retyped: a hook added to SESSION_HOOKS
> upstream would otherwise start reading as a template gap here.

Reading from the module was right. It read the narrower of the two
constants, two hooks were added upstream, and both started reading as
template gaps — the precise failure the comment was written to prevent.

## The Fix

One line and three names:

    NOT_SKELETON |= set(bss.ALL_SESSION_HOOKS) | {'settings.json'}

and add `'CLAUDE.md'`, `'precedent.json'`, `'precedent-source.json'` to the
literal set above it, with a note that each is generated at the
destination.

**Then check the postcondition properly** ([verify-postcondition](../practices/verify-postcondition.md)):
the section should go quiet, and a quiet `TEMPLATE FRESHNESS` is the
correct state for a tree whose skeletons are current. If anything still
reports, it is a real gap for the first time in 21 runs.

## Why It Matters More Than Five Noisy Lines

A section that has produced a finding on every run it has ever made, all of
them false, is worse than a quiet one. The ledger's standing question asks
what to do about sections that have **found nothing** across every run; this
is the mirror image and nothing asks it. A reader who has learned that
`TEMPLATE FRESHNESS` always says five things will not notice the day it says
six — and the one real finding this section ever had (the individual
skeleton shipping no `identity.json`, 2026-09-08, which is why it exists) is
exactly the shape that would be lost in the noise.

## How It Was Found

The 2026-09-21 very deep check, pass 2, reading the tool's sections against
each other rather than each against its own description.

---
slug:              todo-2026-10-01-in-force-nowhere-names-its-set
kind:              manual
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "a practice-format change (a new frontmatter field) that every practice set's checks and stubs must take together, which is out of scope for the Update Vendors fixes that found it"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-01
closed:            null
---
## What

- <a id="in-force-nowhere-names-its-set"></a>**Make every IN FORCE NOWHERE
  line name the set the rule lives in.**

  A deduplicated stub's `in_force_at:` names a slug, not a set, so the view
  sync can say which set to declare only when the stub's `## Story` carries
  the "Withdrawn from universal" line
  [tools/precedent_move.py](../tools/precedent_move.py) writes. On
  2026-10-01, a consumer's Update Vendors listed 16 rules in force nowhere,
  and only one of the stubs behind them had that line, so the update could
  not say they all live in one shared set.

  Since 2026-10-01 a consumer can record a rule as not applying here,
  under `not_in_force_here` in precedent.json, keyed by the rule's slug or
  by its set's name, and the update stops asking. Keying by set works only
  where the finding names the set.

## Proposed

An optional frontmatter field, `in_force_in: <set name>`, documented in
[spec/PRACTICE_FORMAT.md](../spec/PRACTICE_FORMAT.md) and accepted by
[tools/frontmatter_yaml.py](../tools/frontmatter_yaml.py). The resolver
copies it into the dangling entry's message ("in force in `<set>`"), which
the update already reads. precedent_move.py writes it when it deduplicates.
The existing stubs get it once, in the sets that carry them, each with its
own approver.

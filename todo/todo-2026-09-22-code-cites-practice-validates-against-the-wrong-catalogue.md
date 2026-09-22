---
slug:              todo-2026-09-22-code-cites-practice-validates-against-the-wrong-catalogue
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       raise
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-22
closed:            null
---
## What

**`code-cites-practice` decides whether a cited slug is real by listing the
local `practices/` directory**, which is the wrong catalogue everywhere the
local directory is not the whole catalogue. A practice SOURCE set is the
sharpest case: its `practices/` holds its own twenty-odd files, and every
universal slug its code cites looks invented.

Found 2026-09-22 while measuring which checks should carry
`binds_publishers` ([spec/PUBLISHER_GATE_AUDIT.md](../spec/PUBLISHER_GATE_AUDIT.md)).
Forcing the flag on in `precedent-shared-writing` produced:

```
VIOLATION  code-cites-practice
    tools/create_word_doc.py:61: cites 'timestamps-carry-offset', which is
      not a real practice slug (typo, or the file was deleted instead of
      retired)
```

`timestamps-carry-offset` is a real slug. It is in this repo, it resolves in
that session, and the citation is correct. **The check was one flag away from
turning a correct citation into a blocking violation in three repos at once**,
and the only reason it did not is that reading the finding came before setting
the flag.

## Why it matters beyond the flag

The same wrongness is latent in any consumer whose `practices/` is a
materialized subset rather than the full resolved set. It has not bitten there
yet because a consumer materializes what it resolves, so the two agree — but
nothing enforces that they agree, and the check would report identically if
they ever stopped.

The failure mode is the bad one: a **false** violation, on a file that is
right, naming a cause ("typo, or the file was deleted instead of retired")
that sends whoever reads it looking for a problem that does not exist.

## What would fix it

Resolve slugs the way a session does — through
[tools/precedent_resolve.py](../tools/precedent_resolve.py), across every
source in force, not by listing one directory. Where sources cannot be
resolved, the check should SKIP with that reason rather than validate against
a partial list, which is this module's own standing rule for a scan whose
input set it cannot trust.

Once it resolves the full catalogue it becomes flaggable for publishers, and
should get `binds_publishers=True` in the same change: code in a source set
citing a slug that really has been deleted is exactly the thing worth
catching.

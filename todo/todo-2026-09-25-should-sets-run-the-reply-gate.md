---
slug:              todo-2026-09-25-should-sets-run-the-reply-gate
kind:              manual
domain:            vendoring
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan -- which hooks a practice set runs is a default every set inherits"
noted:             2026-09-25
closed:            null
---
## What

**Should practice sets run the reply gate and the other consumer-only
hooks?** The 2026-09-25 sweep that built `HOOK_WIRING` in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
found that no set wires `reply-gate.sh`, `stop-reply-check.sh`,
`stop-git-check.sh` or `precedent-paths.sh`. The engine files they need
are already vendored into sets, so nothing technical stops it.

It was left out of that change on purpose. Adding these to the `source`
list means the next refresh wires them into all four sets. From then on,
every session in a set is held to the reply gate's hard requirements (the
Boildown heading, the archive line) and is refused a stop with unpushed
work. That changes what set sessions are held to. It is not catching up
on a hook somebody forgot.

## How It Closes

Morgan says which of the four hooks, if any, sets get. Then add those to
`HOOK_WIRING['source']`, to [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)'s payload and
`SESSION_HOOKS`, and let the next refresh deliver them. The
`new-hook-joins-the-registry` check holds the three in step.

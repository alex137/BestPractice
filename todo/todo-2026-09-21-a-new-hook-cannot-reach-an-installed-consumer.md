---
slug:              todo-2026-09-21-a-new-hook-cannot-reach-an-installed-consumer
kind:              manual
domain:            vendoring
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan -- changing how the engine decides which hooks a repo receives is a default that binds every adopter"
noted:             2026-09-21
closed:            null
---
## What

**A hook added upstream cannot reach a repository that is already
installed.** Vendoring is gated on wiring, and a refresh deliberately never
writes the consumer's `settings.json` — so the file is not vendored until
it is wired, and wiring it means naming a file that is not there yet.

[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py):

```
names = sorted((available & wired) - adapter_owned)
```

`wired` is read from the CONSUMER's own `settings.json`. A fresh install
escapes this, because [precedent_install.py](../tools/precedent_install.py) writes the settings template
and the hook arrives with it. **An existing install cannot escape it at
all.**

Reported 2026-09-21 by a consuming repo taking the `doc-lint-gate.sh`
update, which read the engine's own NOTE, hand-added the `matcher: "Bash"`
entry, re-ran the refresh, and watched the file arrive on that pass. That
is the workaround; it is a person doing by hand what nothing automates.

## Why It Matters More Than It Looks

**It was invisible until a hook became load-bearing.** Every hook before
this one was additive — a session without `freshness-guard.sh` lost a
guard it never knew it had. `doc-lint-gate.sh` is different: the Markdown
lint left GitHub Actions on 2026-09-21 *because* the hook replaced it. A
repo that takes the update and cannot receive the hook loses the workflow
and gains nothing.

So the same gap has been there for every hook the engine ever shipped, and
only became a correctness problem when a hook started carrying a guarantee
something else used to carry.

## The Gate Is NOT Simply Wrong

`_wired_hook_names`' own docstring records why it exists, and both reasons
are real:

1. **A source set and a consumer wire different subsets** of the same
   shared `hooks/` directory — only a set wires
   `precedent-universal-catalogue.sh`, only a consumer wires the rest.
2. **A repo that deliberately declined an adapter must stay declined.**
   Re-planting a hook nobody wired is the orphan
   [hooks-on-disk-are-reachable](../tools/precedent_check.py) exists to
   catch, and [verify_harness.py](../tools/verify_harness.py) caught exactly that before the first
   version of hook-vendoring shipped.

**So "vendor everything unconditionally" reopens a bug somebody already
found.** That is not the fix.

## The Shape of a Fix, if One Is Wanted

**A declared per-kind hook registry, exactly like `CI_WORKFLOW_TEMPLATES`
one file over.** The engine would ship hook X to kind K because a registry
says so, not because the consumer happened to have wired it:

- reason 1 is solved by the registry itself — `source` and `consumer` get
  different lists, declared rather than inferred;
- reason 2 is solved by the existing `declined_adapters` mechanism, which
  is an explicit declaration instead of an inference drawn from silence.

**The inference from silence is the actual defect.** The engine's own NOTE
says the absence is *"expected ... or one this repo declined on purpose"* —
treating "not wired" as a decision, when for a brand-new hook it only ever
means "not yet". The repo that reported this had not declined anything.

The CI-workflow half of this engine already solved the identical problem
the right way. This half predates it.

## A Second Defect in the Same NOTE, Fixed 2026-09-22

**The NOTE was calling wired hooks unwired.** `_wired_hook_names` matches
only commands whose path contains `hooks/`, and it was answering two
questions at once: *what do we vendor* and *what does this repo already
wire*. It must stay narrow for the first — a repo that calls a script in
place keeps one copy on purpose — and it was simply wrong about the second.

Measured in `precedent-individual`, which authors these scripts and wires
four of them out of its own tracked `bootstrap/`: the refresh reported
`commit-identity.sh`, `freshness-guard.sh` and
`precedent-universal-catalogue.sh` as *"not wired in this repo's own
.claude/settings.json"*. All three are wired, on consecutive lines of that
file, whose own comment says why: *"bootstrap/ IS a tracked directory of this
repo, so every entry calls its script in place -- one file, no second copy to
drift from it."*

That is worse than noise, because the NOTE's remedy is *copy the entry from
upstream's settings.json and re-run*. Following it there plants the second
copy the repo deliberately does not keep.

`_wired_hook_names_anywhere` now answers the reporting question, the
vendoring test is unchanged, and the NOTE names the two groups separately —
so the hand-wiring advice reaches only the hooks it applies to. In that repo
the single list of 7 became 3 *"nothing to do"* and 4 genuinely unwired.

**This does not close the item above.** The inference from silence is still
there for a genuinely new hook; this only stops the report lying about hooks
that were never silent.

## Done in the Meantime

The NOTE now says all of this and names the manual remedy, so the next
adopter reads what to do rather than working it out. That is a band-aid
and is marked as one ([durable-fix](../practices/durable-fix.md)): it
makes a person's manual step discoverable, and does not remove the need
for it.

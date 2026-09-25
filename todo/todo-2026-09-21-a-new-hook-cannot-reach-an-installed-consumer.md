---
slug:              todo-2026-09-21-a-new-hook-cannot-reach-an-installed-consumer
kind:              manual
domain:            vendoring
severity:          high
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "per-kind hook lists (HOOK_WIRING); a refresh adds a missing entry to settings.json, never edits or removes one; declined_adapters opts out"
decision_strength: decided
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-25
---
## What

**Fixed 2026-09-25: a refresh now wires the hooks a repo's kind gets** --
see "How It Closed" at the end. What follows is
the item as filed.

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

## How It Closed

**Morgan, 2026-09-25, strength: decided:** *"I want to make sure we're not
keeping a list of all repos themselves; this needs to work even if a repo
isn't on our lists. I like the lists of 'repos that [are of this type] get
[these hooks]' -- approved."*

**The add-only settings write is the session's reading, not his words.**
He approved the lists, and said *"Let's fix this now!"* The session had just
told him that the lists alone leave the hook unwired, and that closing the
bug means the refresh must also add the entry. It took "fix this now" as a
yes to that, and said so in its reply. For that half, read the strength as
`assented`, not `decided`.

**What was built**, all in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py):

- **`HOOK_WIRING`**: per kind (`consumer`, `source`), the hooks that kind
  runs, as settings.json entries. Keyed by kind, never by repository.
- **`HOOKS_NO_KIND`**: shipped hooks no kind gets, each with its reason
  (today only `commit-identity-push-gate.sh`, which runs a repo's own
  `tools/checks/` scripts).
- **The refresh ADDS a missing entry** from its kind's list to
  `.claude/settings.json`, then vendors as before. It never edits or removes
  an entry. It skips a hook the repo already runs from any path, one declared
  in `declined_adapters`, and every hook for a manifest with no `kind`.
  Wiring first and vendoring second means no file is ever planted that
  nothing calls.

**The fix went past the item's own proposal in one place.** A list alone
would have delivered the file and left it unwired, because a hook only runs
if settings.json names it. That is the orphan `hooks-on-disk-are-reachable`
exists to catch. So the refresh writes the entry too, add-only.
[tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)'s `ensure_hook_wired` had already
established that a vendored tool writing an engine-defined entry is not
refused the way a session editing the file is.

**What keeps it from coming back:** practice
[new-hook-joins-the-registry](../practices/new-hook-joins-the-registry.md),
enforced by the [tools/precedent_check.py](../tools/precedent_check.py) check of the same name. The check
refuses a shipped hook that is on no list, and a template that disagrees
with its kind's list.

**The sweep that built the lists found the same gap in more places:**

- `commit-identity-once.sh` has been wired in this repo since 2026-09-22 and
  was never in a template, so no consumer had it. It is now on the consumer
  list.
- `seeded-prompt-gate.sh` was in the consumer template from 2026-09-23 and
  was never in a set's. It is now on the source list. A dry run against all
  four sets on disk showed it as the only thing each would receive.
- Every consumer installed before a hook entered the template never got that
  hook: `reply-gate.sh` (2026-09-13), `doc-lint-gate.sh` (2026-09-21),
  `seeded-prompt-gate.sh` and `stop-reply-check.sh` (2026-09-23). The last
  one is the worst. The reply check moved OUT of `stop-git-check.sh` into
  `stop-reply-check.sh` that day, so a consumer that took the split through a
  refresh lost its reply check entirely. The next refresh in each of those
  repos now wires all of them.

**Left for a decision, not done here** ([todo-2026-09-25-should-sets-run-the-reply-gate.md](todo-2026-09-25-should-sets-run-the-reply-gate.md)): whether sets should also run the
reply gate (`reply-gate.sh`, `stop-reply-check.sh`), `stop-git-check.sh` and
`precedent-paths.sh`. No set wires any of them today, and adding them would
change what every set session is held to. It is a policy call, not a
catch-up.

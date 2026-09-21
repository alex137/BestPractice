---
slug:              todo-2026-09-21-structural-leak-rules-assume-bestpractices-own-tree
kind:              manual
domain:            security
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "a decision about which repo kinds may legitimately carry a candidates/ or individual/ directory, and how the gate is to know -- the obvious discriminators do not work, see below"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
---
## What

[tools/leak_gate.py](../tools/leak_gate.py)'s STRUCTURAL layer is written on
a premise it states outright: *"Precedent holds universal practices and
nothing else."* That is true of **this** repository's public tree and false
of every repo the same gate is now vendored into.

Measured 2026-09-21: a session installing `leak-gate.yml` into two real
practice sets smoke-tested it first, and it was **red on arrival** in both —
exit 1, 7 hits and 13 hits, with an isolated `HOME` so no individual source
resolved and no blocklist applied. Nothing was wrong with either repo's
content.

- **`precedent.json: an email address`**, 3 hits in each. **Fixed the same
  day**: a repo's own ROOT `precedent.json` / `precedent-source.json` /
  `identity.json` no longer trips the email rule, since those files exist to
  declare who owns the repo. Root only — a NESTED copy is a vendored private
  set and is still caught.
- **`candidates/.gitkeep` and `candidates/…md`** — *"a candidates/outbox
  directory"*. **Not fixed, and this item is about that.**

## Why It Matters

A practice source set legitimately carries a tracked `candidates/` outbox;
so, plausibly, does a consuming repo with its own drafting workflow. The
`individual/`, `personal/` and `private/` directory rules have the same
shape. `CI_WORKFLOW_TEMPLATES` ships `leak-gate.yml` to the `source` kind
regardless, so the gate arrives pre-failed in exactly the repositories it is
meant to protect — and **a gate that is red on arrival is a gate somebody
switches off.**

This is the fourth defect in this template chain with the same root: a
thing written for one repo, shipped to a different kind of repo, carrying
its origin's assumptions with it.

## What Would Close It

A decision, then a small change. **The obvious discriminators do not work,
and this is why it was not guessed at:**

- **File presence cannot tell a public universal tree from a private set.**
  BestPractice itself carries BOTH `precedent.json` and
  `precedent-source.json`; so do all three shared sets, measured the same
  day.
- **Self-declared `visibility` must not gate a LEAK check.** That is
  precisely the bug corrected in `leak-gate.yml.template` on 2026-09-20,
  where two public repos declared themselves private. The workflow now takes
  visibility from GitHub — but [leak_gate.py](../tools/leak_gate.py) also runs in a local pre-push
  hook, where no GitHub context exists.

Plausible answers, none chosen: scope the directory rules to the repo that
declares itself the universal publisher; move them out of STRUCTURAL into a
layer a repo opts into; or give them the same per-path exemption-with-reason
mechanism `ci_workflow_outside_vendoring_exempt` already uses, so a repo
says once, with a reason, that its `candidates/` is deliberate.

Until then `leak-gate.yml` stays uninstalled in the practice sets, which is
where it was already held.

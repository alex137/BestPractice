---
slug:        workflow-file-outside-vendoring
title:       A workflow file outside what the vendored engine tracks gets a second look
tier:        on-demand
severity:    advisory
applies_to:  [".github/workflows/**"]
occasion:    "a .github/workflows/*.yml file is added or changed"
gates:       []
index_clause: "an untracked workflow file -- verify by content, never by name"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-20"
approved_by: "Morgan, 2026-09-20 (\"let's do steps 2-4 please\")"
---
## Rule
**When a `.github/workflows/*.yml` file is added or changed, and it is not
the one file the vendored engine tracks for this repo's kind, that is worth
a second look before the commit lands.** Not a violation — an advisory
nudge with exactly two honest answers: a deliberate, hand-authored check
unrelated to Precedent (fine, no action), or a leftover copy of something
the vendored engine already provides under a different name (worth
retiring).

**Verify by content, never by filename.** A name that looks like a retired
template is not evidence of anything on its own — matching a name is
neither necessary (a legitimate check can share a name with something
retired elsewhere) nor sufficient (a genuinely retired file can be renamed)
for either answer. Read what the file actually runs before deciding.

**This never deletes anything, and never fails a build.** It names a
finding; a person or a session reads it and decides.

## Why
Two failures this practice exists to keep apart. The first: a retired
workflow file left on disk keeps costing real money and real confusion
indefinitely, because nothing besides a person noticing ever looks at
`.github/workflows/` again after install. The second, discovered while
building the fix for the first: matching by filename against a list of
"known retired names" produces false positives — a live, required,
hand-authored check can share a name with something Precedent once
shipped and later retired, for reasons that have nothing to do with each
other.

Both failures share one root cause: nobody looked at content. This
practice's whole job is making sure the *question* gets asked — at the
moment a workflow file changes, when looking costs the least — without
ever answering it by guessing.

## Story
**Raised by Morgan, 2026-09-20**, mid-incident: a fresh GitHub Actions
usage-report pull found personal repos still billing real minutes against
workflow files [spec/CI_WORKFLOW_RETIREMENT_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/CI_WORKFLOW_RETIREMENT_PLAN.md)
had already named as retired. Asked for the engine to auto-delete a
retired file when safe (built, same session — see that document's Item 1),
then for something broader: catch it happening at all, and have a very
deep check sweep for it too.

**The same session then produced the exact failure this practice's "verify
by content, never by filename" rule exists to stop.** A sister session,
asked to prove the sweep on one real dependent repo before running it
across eleven more, reported back that `light-check.yml` —
flagged as a retired duplicate of `bestpractice-docs.yml` because the name
matched a table built from usage-report filenames — was in fact a live,
required, hand-authored check (`tools/light_check.py`, that repo's own
`two-check-levels` light check) with no relationship to anything Precedent
ever templated. The filename-matching method that produced the fleet-wide
sweep list was the same method almost shipped as this practice's own
mechanism, before that finding corrected it.

## Install
Enforced by `_workflow_file_outside_vendoring` in
[tools/precedent_check.py](../tools/precedent_check.py), which calls
`precedent_vendor_engine._untracked_ci_workflow_files()` — every
`.github/workflows/*.yml`/`*.yaml` file on disk not listed in this repo's
own `tools/ENGINE_MANIFEST.json` `ci_workflow_files`, and not a known
`RETIRED_CI_WORKFLOW_FILES` entry either. Registered `'tree'` scope with
this file's own `applies_to` above, so it runs whenever a workflow file is
part of what changed (BestPractice's own `_scoped_tree_slugs` mechanism),
not only on the roughly-one-in-ten commits an unscoped tree check gets.

**Advisory, not a violation** — `_untracked_ci_workflow_files` is
deliberately unable to tell a leftover from a legitimate hand-authored
check (the manifest only ever tracks one file per kind, by design — see
that function's own docstring), so this reports a finding and never fails
a run.

**Declare a deliberate one once, with a reason**, the same discipline
`filename-separator`'s own exemption list already uses:

```json
"ci_workflow_outside_vendoring_exempt": [
  {"path": ".github/workflows/light-check.yml",
   "reason": "this repo's own two-check-levels light check, unrelated to anything Precedent ever templated"}
]
```

**The reason is mandatory.** An entry declared here but not actually found
untracked this run — because the file is gone, now tracked, or now a known
retired entry — is reported rather than silently honored: an exemption
that has outlived what it exempted is a hole nobody sees otherwise.

**Reports nothing in BestPractice itself.** This repo's own tree has no
`ENGINE_MANIFEST.json` — the engine's origin vendors nothing into
itself — so `_untracked_ci_workflow_files` returns `[]` here by
construction, same as every other manifest-dependent check in this
catalogue. It has real data only in a repo the engine was actually
vendored into.

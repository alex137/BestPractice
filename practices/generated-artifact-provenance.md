---
slug:        generated-artifact-provenance
title:       Provenance for generated artifacts
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "building or committing a generated artifact"
checked_by:  null
defines:     ["generated artifact"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 8
---
## Rule
Generated deliverables are never hand-edited and never casually
committed. Each build stamps a **content-derived build code** into the
artifact itself and writes a **manifest** recording exactly which inputs (by
content hash) produced it. Outputs are gitignored and marked binary in
`.gitattributes`; only artifacts that actually shipped get committed
(force-added), alongside their manifest.

## Why

## Story
Two builds minutes apart, with different content, once had to be
distinguished after the fact by spelunking git history. A content-derived
code on the artifact (same content → same code) plus a committed manifest
makes "what exactly shipped?" a lookup instead of an investigation.

A related gap, same fix, different cause: a repo with **no root `.gitignore`
at all** leaves every session that runs the vendored Python audits (practice
6) an untracked `__pycache__/` behind — nobody's build is at fault, there is
just nowhere for the ignore rule to live. One dependent repo's check-in
flagged exactly this after its own merge runbook kept surfacing the stray
directory.

## Install
Pattern to apply in your builders; no portable tool (the code
stamping is builder-specific). The `.gitignore`/`.gitattributes` stanzas are
in [INSTALL.md](INSTALL.md), which also instantiates a baseline
`.gitignore` from [templates/gitignore.template](templates/gitignore.template)
at install time — ordinary tool/interpreter caches (`__pycache__/` and
friends), so the generated-deliverable globs above have a file to land in
rather than each install having to remember to create one.

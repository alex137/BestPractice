---
slug:        generated-artifact-provenance
title:       Provenance for generated artifacts
tier:        on-demand
severity:    default
applies_to:  ["deck/**", "MAP.md", "GLOSSARY.md"]
occasion:    "building or committing a generated artifact"
gates:       []
index_clause: "stamp a build code and a manifest; never hand-edit output"
checked_by:  "tools/precedent_check.py"
defines:     ["generated artifact"]
status:      active
in_force_at: null
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

## Detail

## Why
A content-derived build code makes an artifact's identity **a property of its content rather than of when it was built**, which is the only version of the question that survives two builds minutes apart. A timestamp or a commit hash answers "which run produced this"; neither answers "is this the same thing that shipped".

The manifest closes the other half: recording inputs by content hash turns *what exactly shipped* into a lookup rather than an investigation through history.

The prohibition on hand-editing follows from both. A generated file that has been edited is no longer reproducible from its inputs, so the build code lies and the manifest describes something that no longer exists — and nothing about the file's appearance reveals it. Gitignoring outputs and force-adding only what shipped keeps that distinction visible in the tree itself.

## Story
Two builds minutes apart, with different content, once had to be
distinguished after the fact by spelunking git history. A content-derived
code on the artifact (same content → same code) plus a committed manifest
makes "what exactly shipped?" a lookup instead of an investigation.

A related gap, same fix, different cause: a repo with **no root `.gitignore`
at all** leaves every session that runs the vendored Python audits
([convention-to-audit](convention-to-audit.md)) an untracked `__pycache__/` behind — nobody's build is at fault, there is
just nowhere for the ignore rule to live. One dependent repo's check-in
flagged exactly this after its own merge runbook kept surfacing the stray
directory.

## Install
Pattern to apply in your builders; no portable tool (the code
stamping is builder-specific). The `.gitignore`/`.gitattributes` stanzas are
in [INSTALL.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/INSTALL.md), which also instantiates a baseline
`.gitignore` from [templates/gitignore.template](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/gitignore.template)
at install time — ordinary tool/interpreter caches (`__pycache__/` and
friends), so the generated-deliverable globs above have a file to land in
rather than each install having to remember to create one.

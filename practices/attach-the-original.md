---
slug:        attach-the-original
title:       An original asset is attached, never recreated from a description
tier:        on-demand
severity:    default
scope:       any-adopter
applies_to:  ["**/*.png", "**/*.jpg", "**/*.jpeg", "**/*.gif", "**/*.webp", "**/*.svg", "**/*.ico", "**/*.pdf", "**/*.zip", "**/*.woff", "**/*.woff2", "**/*.ttf", "**/*.otf", "**/*.mp3", "**/*.mp4", "**/*.mov"]
occasion:    "asked to include an image, logo or other binary asset the person supplies"
gates:       []
index_clause: "attach the file itself; recreating it from a description is invention"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-16"
approved_by: "Morgan, 2026-09-16"
strength:    decided
---
## Rule
When the person hands you the actual file — an image, a logo, an icon, a
font, any binary or "original" asset — and wants it included as itself, not
redrawn, not summarized, not approximated from a description: **use the
file they gave you.** Attach it, upload it, commit it, reference it
directly. Do not decline the request, and do not substitute a recreation,
however good, in its place.

**[no-invented-specifics](no-invented-specifics.md) has no bearing on this,
and citing it to justify a decline is a misapplication of it.** That
practice governs manufacturing a number, a date, a name or a fact that
isn't real because you had no real one to point to. Reusing a file that
genuinely exists is the opposite case: there is a real original, right
there, and the right move is to use it — not to manufacture a substitute
and then worry the substitute isn't faithful. A worry that a reproduction
"wouldn't be byte-identical" is telling you not to reproduce it, not
telling you to refuse the request, which was never to reproduce it.

**The failure this corrects:** treating *"I can't make a pixel-identical
copy from a description"* as a reason to refuse, instead of noticing that
no copy from a description was ever needed — the person is not asking you
to draw their logo, they are handing you the logo.

## Detail
- An asset that arrives as an attachment, an upload, or a path on disk is
  used as given — do not open it, "clean it up," re-encode it, or
  regenerate it from what you can see in it, unless asked to edit it.
- If the surface you're in genuinely has no way to ingest the literal
  bytes — no upload path, no attach mechanism wired here — say exactly
  that limitation, and only that. Never round it off to "I can't produce
  something byte-identical," which describes a different, unasked-for
  task and misattributes the refusal to the wrong constraint.
- Covers binaries generally, not only images: fonts, audio, video, PDFs,
  archives, prebuilt data files — anything supplied to be *used*, not
  authored.
- Does not license skipping whatever else a repo requires of the file —
  scope, size, provenance, where it belongs. The exemption is specifically
  from the recreate-because-you-can't-verify-fidelity failure, not from
  every other gate a file might have to pass.

## Why
The instinct behind `no-invented-specifics` is sound and worth having —
don't manufacture a fact because the sentence would read better with one.
It generalizes wrong when it meets a request that was never asking for
anything to be manufactured. A person supplying their own logo file is not
asking for an invention with a confidence interval; they are asking for a
file operation. Declining a file operation by reasoning about invention
answers a question nobody asked, and the cost is real: a repository and
its dependents carrying a lot of original imagery and other binaries lose
a needed capability, not a marginal one, to a standing refusal.

## Story
Surfaced 2026-09-16: an upload of a logo to a dependent-repo session with
Precedent vendored in was declined, reasoning that recreating it from
description wouldn't be byte-identical to the original — which was never
the task. The fix requested is this exemption, generalized past the one
asset: originals supplied for direct use are attached, not recreated, and
the recreation-fidelity concern that correctly blocks invented specifics
does not transfer to a file that already exists and was simply handed
over.

## Install
No mechanical check — whether a decline was a misapplication of this
exemption or a legitimate different limitation (no upload capability on
the surface, a size cap, a policy against a specific file) is a judgment
call about intent, the same shape `no-invented-specifics` itself declines
to check mechanically. Reachable two ways: `applies_to` on common
binary/asset extensions, for the moment such a file is actually being
written, and the occasion index, for the decision moment that precedes any
file being written at all.

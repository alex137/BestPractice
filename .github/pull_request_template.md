<!-- practices/pr-template-honest-gates.md: fill this in from the actual
     diff, every time. An unchecked gate, or a "not applicable" note, is a
     normal and expected outcome of a real pull request (PR) -- never check
     a box, or write N/A across every field, just to make the form look
     complete. A checklist filled in mechanically looks like verification
     and isn't; that defeats the entire point of having one.

     This is this repo's own template, not the generic one
     templates/pull_request_template.md.template instantiates into a
     dependent repo's process/upstream/ tree -- BestPractice/Precedent is
     the upstream, so its gates are the deep-check suite and the generated
     views, not a vendored tree. -->

## What changed

<!-- One or two sentences, plain language. What is different after this merge? -->

## Why

<!-- The intent/critique that prompted it. Link the TODO.md item if there is one. -->

## Files touched

<!-- The reply convention's list, restated here: branch link + one-line description each. -->

## Gates

- [ ] Base branch is `precedent-beta-v01`, not `main` (see AGENTS.md's opening note) — checked explicitly, not assumed from the default branch
- [ ] Deep check run and clean: `verify_harness.py`, `doc_lint.py`, `leak_gate.py`, `precedent_check.py`, `doc_sync.py`
- [ ] Generated views regenerated if any `practices/*.md` front matter changed (`tools/build_views.py`) — AGENTS.md/MAP.md/GLOSSARY.md byte-identical to a fresh build
- [ ] `TODO.md` updated — items opened/closed listed below
- [ ] `GLOSSARY.md`/occasion-index entries current if a practice's `defines:`, `applies_to`, or `occasion` changed

## Open questions / follow-ups

<!-- Anything deferred. These should also land in TODO.md. -->

---
slug:            gotcha-2026-09-20-leak-gates-private-blocklist-clone-fails-open-stale
status:          live
noted:           2026-09-20
severity:        notable
retired:         null
retires_when:    null
---

## Symptom

`python3 tools/leak_gate.py` reports a wall of undeclared-repo hits against
a tree that is actually fine, all naming things the session never touched.
The gate's own printed remedy -- `git -C <root> pull --ff-only` -- can
itself fail with no further guidance.

## Story

2026-09-20: the gate failed with 110 hits, every one false, every one in
`record/stale_branches.md`, a file the session had not touched. The private
blocklist it reads comes from `themorgan/precedent-individual`, resolved
through `~/.config/precedent/config.json`, and that clone was 37 commits
behind `origin/main` -- predating the `themorgan/precedent-team-*` →
`themorgan/precedent-shared-*` rename, so correct references to the renamed
sets read as undeclared private-repository names. This is the same shape as
the 2026-09-11 incident `_stale_blocklist_clone_note()` in
`tools/leak_gate.py` already exists to diagnose: a correct gate, correct
output, stale input, indistinguishable from a real failure by construction.

The gate diagnosed itself correctly and named the fix: `git -C
/root/precedent-individual pull --ff-only`. **That command failed.** The
clone had diverged -- three unpushed local commits (`Advance
precedent-beta-v01 watermark to ...`), made by the same session earlier and
not yet pushed. A plain fast-forward cannot reconcile a clone that is both
ahead and behind; that specific container was repaired by hand with a merge
(taking `origin/main`'s side on a `beta-branch-watermark.json` conflict),
and the fix would not have survived the container being recycled.

## Fix

`tools/leak_gate.py` now tries the gate's own suggested remedy itself, once
`_try_refresh_private_blocklist_clone()` is reached from `main()` (only
after a hit already exists to lose from *not* trying -- never on a clean
push, which is exactly the constraint `_stale_blocklist_clone_note()`'s own
docstring states for why this gate does not otherwise touch the network).
One bounded `git pull --ff-only`, declined outright on a dirty working
tree or a genuine divergence (this incident's own shape: local commits the
remote does not have) -- in either of those cases nothing changes and the
existing stale-clone note still fires, honestly, exactly as before. On a
clean, purely-behind clone (the common case, and 2026-09-11's own case) the
pull succeeds, the blocklist, the repo-reference policy and the hit list are
all recomputed against the refreshed content, and a hit caused purely by
the staleness clears -- the push proceeds instead of failing on stale
input. Covered by `check_leak_gate_names_a_stale_blocklist_clone()` (the
clean self-heal and the diverged real-incident shape) and
`check_leak_gate_refresh_declines_a_dirty_clone()` in
`tools/verify_harness.py`.

**Still not fixed by this**: a diverged clone (this incident's exact case)
still needs a person to decide the merge, same as before -- the self-heal
only removes the common, no-decision-needed case from the pool of "stale
blocklist" failures a session hits.

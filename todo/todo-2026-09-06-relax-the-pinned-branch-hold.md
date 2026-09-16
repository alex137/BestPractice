---
slug:              todo-2026-09-06-relax-the-pinned-branch-hold
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "the fix surviving real sync cycles rather than only its own tests, and then Morgan saying so. What it needs then: put `checkin.py update` back as the remedy `_warn_catalogue_skew` names, and drop the hold paragraph from the migration document."
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan"
noted:             2026-09-06
closed:            null
---
## What

- <a id="relax-the-pinned-branch-hold"></a>**Relax the pinned-branch hold
    once the fix has run through real sync cycles.**
    [tools/checkin.py](../tools/checkin.py)'s four commands — `fresh`,
    `update`, `record`, `push` — now read `upstream.branch` from a consuming
    repo's own `process/manifest.json` instead of resolving the remote's
    default branch, and `record` no longer checks the source clone out from
    under its caller. Seven cases in
    [tools/verify_harness.py](../tools/verify_harness.py) assert both
    properties with negative controls. That closes the defect
    [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md)'s
    "The default-branch gotcha" was written around, and
    `_warn_catalogue_skew`'s docstring in
    [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
    names the same fix. **Both still tell people to mirror by hand and to
    keep the scheduled sync paused, deliberately** — Morgan's call
    2026-09-06, on the asymmetry: what those documents guard against is an
    *unattended* job overwriting a vendored tree, so relaxing them too early
    costs a silent overnight wipe of a repo's practices while staying
    cautious costs a stale paragraph. **Blocked on:** the fix surviving real
    sync cycles rather than only its own tests, and then Morgan saying so.
    What it needs then: put `checkin.py update` back as the remedy
    `_warn_catalogue_skew` names, and drop the hold paragraph from the
    migration document.

    **The third part is WITHDRAWN, 2026-09-14.** It used to read "and
    un-pause the `schedule:` block in each consumer's
    `bestpractice-upstream-sync.yml` — never one of the three without the
    others, since a half-relaxed hold is what makes an unattended job run
    against advice nobody re-read." Morgan killed every scheduled vendor
    update — *"No weekly updates. I had that weeks ago, but we're not doing
    that anymore; this is now really complex and deserves hand attention and
    issues come up every time and I'm on it every day anyway."*
    **Strength:** decided ([decision-strength](../practices/decision-strength.md)).
    There is no `schedule:` block left to un-pause, so the coupling warning
    it carried is moot with it: the remaining two parts are independent of
    any clock, and the replacement channel is a person saying
    `Update Vendors` ([vendor-update-runbook](../practices/vendor-update-runbook.md)).
    **Enforced 2026-09-07, which changes what relaxing it costs.**
    `checkin.py update` now refuses while a non-default branch is pinned
    (`_pinned_branch_hold`), printing the manual procedure and naming
    `PRECEDENT_ALLOW_PINNED_UPDATE=1` as the one-run override; eight harness
    cases with a negative control. Until then the hold existed only as a
    paragraph in a document, so every session had to read and obey it — the
    advisory-only state `checkable-gets-checked` exists to end. Note what
    this does to the relaxation above: the guard's condition IS the hold's
    condition, so repointing a manifest to the default branch lifts it for
    that repo automatically. The three-part change listed above therefore
    has a fourth part that needs no work — but do confirm the guard has
    stopped firing rather than assuming it, since a repo left pinned keeps
    it, correctly.
    **Still open, and NOT closed by that guard:** a consumer carrying a
    pre-fix vendored copy has no guard at all, and nothing upstream can
    reach it — the manual mirror is what brings the current file in. Whether
    that is worth closing with a consumer-side check outside the vendored
    tree (a CI check refusing a commit that reverts the tree against its
    pin) is a real question and nobody has decided it.

## How It Closes

Not open until: the fix surviving real sync cycles rather than only its own tests, and then Morgan saying so. What it needs then: put `checkin.py update` back as the remedy `_warn_catalogue_skew` names, and drop the hold paragraph from the migration document.

## Notes

2026-09-16: noted date is a floor, not exact -- this item predates anchor tracking (every anchor was retrofitted 2026-09-06) and its true creation date is unknown. Migrated from TODO.md by tools/todo_migrate.py.

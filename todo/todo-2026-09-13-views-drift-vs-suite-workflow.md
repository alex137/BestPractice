---
slug:              todo-2026-09-13-views-drift-vs-suite-workflow
kind:              decision
domain:            null
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        "removing a workflow from every source set is a change to repositories this session cannot reach, and the sets are cross-owner. The decision comes first either way."
batch:             null
decision:          "Keep both checks, but as jobs in one workflow file rather than two separate ones -- resolves the cost this item named (two workflows reporting the same fact, two places to update) without losing what it named as worth keeping (both checks' own distinct failure messages, precedent-check's deliberate non-strict leniency staying independent of views-drift's own refusal logic). precedent-check.yml.template now carries a views-drift job; views-drift.yml.template no longer exists. Applied in all four of Morgan's practice sets plus this repo's own template, 2026-09-19 -- see spec/CI_MINUTES_PLAN.md item 8."
decision_strength: decided
waiting_on:        null
noted:             2026-09-13
closed:            2026-09-19
---
## What

- <a id="views-drift-vs-suite-workflow"></a>**Decide whether a source set
    that runs the whole check suite in continuous integration should still
    carry `views-drift.yml`.** Until 2026-09-12 the two could not overlap:
    `generated-artifact-provenance` skipped itself in a source set, so the
    workflow calling [tools/build_views.py](../tools/build_views.py) directly was
    the only thing looking at a generated view there. `binds_publishers`
    (#261) ended that skip.

    **Measured 2026-09-13**, in a set freshly bootstrapped by
    [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
    and given a loader block — not inferred from reading the code:
    `--only generated-artifact-provenance` reports `1 passed` where it
    reported `1 skipped` before, and planted drift turns it red in each of the
    three views separately, `MAP.md`, `GLOSSARY.md`, and inside `AGENTS.md`'s
    loader block. Both run the same `build_views.py --check` subprocess over
    the same files, so in a source set the coverage is the same.

    **What the workflow still has that the vendored check does not** is a
    `pull_request` trigger. That distinction is real but it is exactly what a
    workflow running the whole suite would also supply, which is why this
    became a question the day one was proposed.

    **Two differences argue for keeping both, and neither is large.** A
    suite workflow that is deliberately not `--strict` (most registered checks
    belong to levels a source set does not resolve, so `--strict` leaves it
    permanently red) stays green when `generated-artifact-provenance` reports
    SKIPPED — which it does, by name, when `tools/build_views.py` is absent.
    And `views-drift.yml` fails with a message about the drifted view rather
    than about a check registry, which is the message the person who drifted
    it can act on.

    **The cost of keeping both** is two workflows reporting the same fact on
    every pull request in every source set, and a second place to update when
    the drift story changes — this item exists because that story had gone
    stale in three separate files at once.

    **Blocked on / out of scope:** removing a workflow from every source set
    is a change to repositories this session cannot reach, and the sets are
    cross-owner. The decision comes first either way.
    **Disposition:** wait

## How It Closes

Not open until: removing a workflow from every source set is a change to repositories this session cannot reach, and the sets are cross-owner. The decision comes first either way.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

2026-09-19: closed. The blocker (cross-owner repos this session couldn't
reach) lifted when a session working across `alex137/BestPractice` and
Morgan's four practice sets got push access to all of them in the same
conversation, prompted by a GitHub Actions billing spike traced to exactly
these two workflows -- see spec/CI_MINUTES_PLAN.md item 8 for the incident
and precedent-check.yml.template's own header for the mechanical result.

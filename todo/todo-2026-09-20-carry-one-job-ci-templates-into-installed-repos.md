---
slug:              todo-2026-09-20-carry-one-job-ci-templates-into-installed-repos
kind:              manual
domain:            ci
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "a session whose GitHub access reaches themorgan/* — this one is scoped to alex137/bestpractice, and PRECEDENT_GIT_TOKEN returns 403 on the Actions API"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-20
closed:            null
---
## What

- **The one-job CI templates land in BestPractice but reach nobody until
  each repo takes an "Update Vendors".** Item 13 of
  [spec/CI_MINUTES_PLAN.md](../spec/CI_MINUTES_PLAN.md) cut
  `precedent-check.yml.template` from 3 jobs to 1 and
  `doc-lint.yml.template` from 2 to 1, and retired `ci_debounce_minutes`.
  Per `vendor-rollout-disclosed` that reaches an installed repo only
  through [vendor-update-runbook](../practices/vendor-update-runbook.md).
- **Four practice sets carry the old three-job file**:
  `themorgan/precedent-individual`,
  `themorgan/precedent-shared-writing`,
  `themorgan/precedent-shared-repo-maintenance`,
  `themorgan/precedent-shared-working-style`. Each also still carries an
  explicit `ci_debounce_minutes` in its own `identity.json`, which nothing
  reads any more and which should be deleted rather than retuned.
- **`themorgan/precedent-individual` additionally carries
  `commit-identity.yml`**, which fires on every `pull_request` event with
  `fetch-depth: 0` and billed 117 minutes month-to-date. It exists in no
  BestPractice template, so nothing here governs it.
- **The larger item is not ours at all**: `light-check.yml` billed 609
  minutes month-to-date across 12 repos and was still billing on
  2026-09-20 — 23.5% of the account's whole spend. It has no template in
  this tree. Phase B of the plan assumed it no longer fired; the usage
  export says it does.

## Why It Matters

Measured 2026-09-20: `precedent_check.py` takes 0.35s and
`build_views.py --check` 0.12s, and the three-job shape billed three whole
minutes for that 0.47 seconds of work. Every repo still on the old
template pays 3x what it needs to, on every trigger that fires. Morgan
intends to 20x his usage, which turns a $23/month bill into roughly $467
at today's shape.

## What Would Close It

An "Update Vendors" in each of the four practice sets, the
`ci_debounce_minutes` field deleted from each `identity.json`, and a check
that each repo's `.github/workflows/precedent-check.yml` ends up with
exactly one job. Separately, the 12-repo `light-check.yml` sweep.

## Measured 2026-09-21 — And It Is NOT a Vendoring Bug

All four sets still run the three-job workflow. The first hypothesis was a
silent write failure in the vendor engine: each set's
`ENGINE_MANIFEST.json` records a `ci_workflows_sha256` that MATCHES its
live file, which reads exactly like a refresh that recorded without
writing.

`git merge-base --is-ancestor fc6e764a2 de72bc568` returns false. The
one-job template landed in `fc6e764a2`; the four sets are pinned at
`de72bc568`; **the pin is earlier.** `_refresh_ci_workflow_files()` works
and has simply never been asked to run in these repos since the fix.

| Repo | jobs | engine pinned at |
|---|---|---|
| `precedent-individual` | 3 | `de72bc56` |
| `precedent-shared-writing` | 3 | `de72bc56` |
| `precedent-shared-repo-maintenance` | 3 | `de72bc56` |
| `precedent-shared-working-style` | 3 | `de72bc56` |

Only `precedent-individual` carries `ci_debounce_minutes` in its own
`identity.json`; the other three do not.

**Blocked here, established not assumed.** `git push --dry-run` to
`themorgan/precedent-individual` returns *"access denied by the git proxy:
not in this session's authorized repository set"*, and `add_repo` refuses:
*"cross-tier adds are not supported in v1"* — this session's sources are
owned by `alex137`. Read access works; write does not.

**What changed here instead**, so the next repo that is behind finds out
without anyone remembering the mapping:
[precedent_engine_freshness.py](../tools/precedent_engine_freshness.py)
`--files` now names the INSTALLED workflow file a changed template
produces, not just the template. Verified against `precedent-shared-writing`
— a real stale repo, not a fixture.

Two runbooks that still told a session to apply the retired
`ci_debounce_minutes` now say to delete it:
[vendor-update-runbook](../practices/vendor-update-runbook.md) step 10 and
[MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md)
step 6.

## The Light-Check Half, Measured (2026-09-21)

`light-check.yml`'s 609 minutes are now broken down per repo from the
export rather than left as a total, and the shape that was missing is
shipped:
[templates/github-actions/light-check.yml.template](../templates/github-actions/light-check.yml.template).
Full table and the reasoning in
[spec/BILLING_FLOOR.md](../spec/BILLING_FLOOR.md).

**The finding: it is ours even though no template shipped it.**
`two-check-levels` asked every adopter for a fast check and this repository
never shipped a shape for one, so twelve repos each invented a workflow and
none got the one-job or `paths:` discipline. A rule published without a
shape is a rule everybody implements differently, and expensively.

**The busiest repo on the account is the whole first move.** 633 minutes,
24.4% of the account, and its BIGGER workflow is `bestpractice-docs.yml` at 350 — ours,
and an ordinary `Update Vendors` brings it to the current one-job,
`paths:`-filtered template. `light-check.yml` is the other 277 and needs
its existing file read before anything replaces it.

**Not attempted, and deliberately:** the other eleven repos. Morgan,
2026-09-21: *"It's not worth today our energy to go measure more
specifically the other repos, let's first fix [the busiest one]."*
`decided`,
quoted. The table above is there for whenever that changes; one row of it
is a repo whose own name says `DEPRECATED-TO-DELETE` and is worth 67
minutes for free.

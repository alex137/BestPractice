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

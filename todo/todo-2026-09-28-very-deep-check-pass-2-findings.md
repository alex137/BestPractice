---
slug:              todo-2026-09-28-very-deep-check-pass-2-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-28
closed:            null
---
## What

What the 2026-09-28 very deep check's pass 2 (mechanisms) found and did
**not** fix in the same run.

- `very_deep_check.py --check`, `--explain`, `--list` and `--dry-run` start a
  full run and append an incomplete ledger row (filed 2026-09-21, still true).
  Unknown flags should refuse; `--record-pass` should target the last
  completed run.
- IDENTITY REALITY ignores `grandfathered_commit_shas`, treats the container
  bot address `noreply@anthropic.com` as "not a finding", and does not say
  when a shallow clone truncated its window. Eight bot-authored commits sit on
  precedent-shared-writing `main`, none grandfathered.
- CONFIG KEYS: `writeup_dir` is read by a session through `write-it-up`, not
  by a script; search practice files too. `grandfathered_commit_shas` in two
  shared sets is read by nothing since 2026-09-25; keep it with a comment
  saying it is a record.
- `private-repo-scrub` (shared) is in force in BestPractice and its check has
  never run here: BestPractice discovers check scripts only in its own trees.
- `open-item-disposition` reads only `**Disposition:**` lines; since the
  todo/ migration nothing validates frontmatter `disposition:` (two open items
  carried `raise`, fixed by hand in this run).
- `two-check-levels` requires literal bold words in AGENTS.md; its Rule says
  GLOSSARY.md and any repo-chosen pair.
- `technical-describes-people` iterates `ctx.changed`, so `--full-sweep`
  passes vacuously; walk the tracked tree.
- `no-version-suffix` refuses `new`, `old`, `copy`, `draft`, `final`,
  `latest` everywhere; flag those only beside a sibling without the token.
- `environment-gotchas` never tests that the catalogue stays out of the
  instructions file.
- CI FLEET AUDIT prints a sample of 300 runs as a per-workflow count; use each
  workflow's own `total_count`.
- Two precedent-individual decision records have frontmatter PyYAML rejects
  (a `#` inside a plain scalar).
- The build_views "is status: deduplicated" roster prints once per catalogue
  load (about 120 lines a run); give `load_practices` a quiet mode.
- MOVED CLAIMS reads a sentence narrating a deletion as a live claim; suppress
  a match when the same or next lines say the target was deleted.
- **For Morgan and Alex:** in BestPractice, `ci-workflow-approved` skips as the
  engine's origin, so `leak-gate.yml` (every push, every branch) and
  `deep-check.yml` are approved by nobody.
- **For Morgan:** `precedent-individual/.github/workflows/engine-refresh.yml`
  is dispatch-only, and if clicked opens a PR into `main`, against
  promote-only; it duplicates `precedent_update.py`. Delete it, or pin its
  base to the landing branch.
- **For Morgan:** `decisions/2026-09-01-relax-private-repo-isolation.md` says
  the relaxation is reinstated no later than phase 7; phase 7 merged and
  nothing reinstated or extended it.

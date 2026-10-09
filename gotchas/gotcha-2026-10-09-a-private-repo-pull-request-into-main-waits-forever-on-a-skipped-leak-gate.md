---
slug:            gotcha-2026-10-09-a-private-repo-pull-request-into-main-waits-forever-on-a-skipped-leak-gate
status:          live
noted:           2026-10-09
severity:        notable
retired:         null
retires_when:    "the consuming repository's vendored tools/precedent_branches.py has skipped_by_design, which Update Vendors brings once this fix reaches main"
---
## Symptom

In a repository whose `precedent.json` says `"visibility": "private"`, the
pull request into `main` never becomes mergeable by the engine's own word.
The pull request page shows the light check passed and
`.github/workflows/leak-gate.yml` "skipped".
`python3 tools/precedent_branches.py --wait-main-test COPY` prints
"GitHub test NONE on SHA: .github/workflows/leak-gate.yml never ran on it.
Do not merge." The step that opened the pull request printed "GitHub test: DUE --
.github/workflows/leak-gate.yml predates the not-due skip, so it runs on
every pull request into main until Update Vendors brings the current one."

Running Update Vendors changes nothing: the leak-gate template it brings is
the same file.

## Story

**2026-10-09, a private consuming repository's pull request into `main`.** The leak-gate
template gates its only job on `github.event.repository.private != true`.
That is on purpose: in a private repository [tools/leak_gate.py](https://github.com/alex137/BestPractice/blob/staging/tools/leak_gate.py) stands down
anyway, so a run there was a billed minute that checked nothing. GitHub
records a skipped run for it on every pull request.

[tools/precedent_branches.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branches.py)
listed every workflow with a pull-request trigger into `main` as one of
main's GitHub tests, leak-gate.yml included. Its run reader drops skipped
runs, because a skipped run did not happen and must never count as a pass.
So leak-gate.yml read as "never ran", forever, and the wait said "Do not
merge" on a pull request whose only real test had passed. The due check then
named Update Vendors as the cure, which was false: only the light-check
template carries the not-due skip. The same listing also kept every private
repository on the old copy names and made `"github_ci_main_test": "always"`
read as not installed, because leak-gate.yml carries neither marker.

## Fix

Fixed in the engine, not the template; a template change would reach every
consumer's CI and need each person's approval, for no gain in a private
repository. `skipped_by_design` in
[tools/precedent_branches.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branches.py)
is the one definition: a workflow whose every job is gated off by
`github.event.repository.private != true` (or `!github.event.repository.private`),
in a repository declared private. `github_tests` leaves it out, so the wait,
the due check, the tier checks, the hold on a move into main and the copy-name check all
read the same list, and
[tools/precedent_ci_verified.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_ci_verified.py)
no longer expects it. A skipped run anywhere else, including the same run
in a public repository, still never reads as passed. The due check names
Update Vendors only for a workflow whose current template carries the
not-due skip (`NOT_DUE_SKIP_TEMPLATES`, checked against the templates by
verify_harness.py).

Until a consuming repository takes the fixed engine: read the pull request's
checks yourself. The light check passing and leak-gate.yml skipped is a
pass in a private repository.

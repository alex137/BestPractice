---
slug:            gotcha-2026-09-28-git-log-skips-merge-commits-so-a-version-made-in-a-merge-is-in
status:          live
noted:           2026-09-28
severity:        major
retired:         null
retires_when:    null
---
## Symptom

A tool that lists every past version of a file from `git log --raw`,
`git log -p` or `git log --name-only` misses a version, and a copy of the
file that is byte-identical to that version is treated as locally edited.
Update Vendors reports a consumer's untouched `tools/bootstrap.sh` as
DIVERGED and never updates it.

## Story

On 2026-09-28 a very deep check committed a comment edit to
`templates/bootstrap.sh` as part of a merge commit. The full harness then
failed `check_vendor_engine_refreshes_bootstrap_sh`: a consumer holding
exactly the template as it stood at that commit was called edited. The
engine builds the list of past template versions with
`git log --format= --raw -- templates/bootstrap.sh`, and by default git
shows a merge commit no diff at all, in `--raw`, `-p` and `--name-only`
alike. So any version introduced by a merge (a conflict resolution, or a fix
committed with the merge) never enters the list. It took a failing test to
see it, because every tool reported success. Four history reads in the
engine and Update Vendors had the same blind spot.

## Fix

Pass `-m` to `git log` whenever the point is every version a file has had,
so each merge is diffed against each parent. Done in
`tools/precedent_vendor_engine.py` (the template history and the AGENTS.md
section history) and `tools/precedent_update.py` (the upstream practice
versions and the dropped-wording report), with a planted case,
`check_template_history_includes_a_version_made_in_a_merge`.

---
slug:              todo-2026-10-16-naming-tests-read-the-sessions-identity
kind:              manual
domain:            engine
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-16
closed:            null
---
## What

Two naming tests in [tools/verify_harness.py](../tools/verify_harness.py),
`check_branch_name_follows_the_convention` and
`check_branch_name_counts_local_branches`, fail in a cloud session whose
user-level config declares a GitHub username: the names they expect carry no
username, and `precedent_branch_name.py` adds the session's own. Both pass
with `PRECEDENT_USER_CONFIG=/dev/null`. The other naming fixture already
sets `PRECEDENT_USER_CONFIG=os.devnull` and drops `PRECEDENT_GITHUB_USER`;
these two should do the same, so the push check's changed-files tier stops
failing on a tree whose change has nothing to do with them.

## Notes

Found 2026-10-16 landing the harness-name refusal: the changed-files check
failed on these two, the same way with and without that change.

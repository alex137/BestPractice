---
slug:              todo-2026-10-14-alex-private-repos-outside-the-leak-list
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
waiting_on:        "Alex: whether his account is private by default in his own leak blocklist"
noted:             2026-10-14
closed:            null
---
## What

Since 2026-10-14 the leak gate reads a person's written list of private
repositories (`private-repos.txt` beside their blocklist,
[gotcha](../gotchas/gotcha-2026-10-14-leak-gate-knew-only-the-private-repos-cloned-beside-it.md)),
but only for accounts that person's blocklist declares private by default.
Morgan's list covers his own account. Two private repositories under Alex's
account are reachable from Morgan's sessions and are covered by neither
list, so a session without a clone of either could still write one's name
into a public tree.

The fix is Alex's own: a `private-owner` line for his account in his
blocklist, and his private repositories in his own `private-repos.txt`. It
is not done from Morgan's list, which speaks for Morgan's account only.

## Notes

Found 2026-10-14 while seeding Morgan's list from the repositories his
account can reach. The two names are deliberately left out of this public
file (practice: private-repo-scrub).

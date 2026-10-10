---
slug:              todo-2026-10-10-parallel-update-vendors-race-on-shared-clones
kind:              analysis
domain:            engine
severity:          minor
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        Morgan, whether to fix it now
noted:             2026-10-10
closed:            null
---
## What

Running Update Vendors on several repositories at once fails at random,
because each run fetches into the same BestPractice clone and the same
brought-set clones beside it. On 2026-10-10, two runs started together and
one stopped with:

    FAILED: could not fetch origin/main in /home/user/BestPractice:
        | error: cannot lock ref 'refs/remotes/origin/main': is at ... but expected ...

Running that repository again on its own worked. Parallel runs are worth
having: they cut a four-repository update from over an hour to a fraction
of that.

## Fix wanted

[tools/precedent_update.py](../tools/precedent_update.py) takes a lock on
each shared clone (a lock file under its `.git/`) before it fetches or
checks out there, and waits for it rather than failing. A harness test
starts two runs against the same source clone and expects both to finish.

## Notes

Not fixed in the session that found it because nobody asked for it there;
offered to Morgan.

---
slug:              todo-2026-10-10-parallel-update-vendors-race-on-shared-clones
kind:              analysis
domain:            engine
severity:          minor
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "All these bugs - fix them on `BP` now, if it is filed we might not get to it"
decision_strength: decided
waiting_on:        null
noted:             2026-10-10
closed:            2026-10-10
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

Fixed 2026-10-10, the same day, on Morgan's word: the new
[tools/precedent_clone_lock.py](../tools/precedent_clone_lock.py) holds an
operating-system lock inside the clone's git directory, taken by the
source-clone fetch in [tools/precedent_update.py](../tools/precedent_update.py)
and by every set clone or pull in
[tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py).
A second run waits, saying so, for up to ten minutes. The harness test
`check_clone_lock_makes_parallel_updates_wait` fails on the code before it.

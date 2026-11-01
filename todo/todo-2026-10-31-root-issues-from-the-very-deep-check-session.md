---
slug:              todo-2026-10-31-root-issues-from-the-very-deep-check-session
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        "the harness split, running in a session of its own"
batch:             null
decision:          "all four picks taken"
decision_strength: assented
waiting_on:        "the harness-split session"
noted:             2026-10-31
closed:            2026-10-31
---
## What

"Root issues" run over the whole transcript of the session that ran the
2026-10-30 very deep check (the session titled "Very deep check, 2026-10-30 run", 01:10 to
20:18 UTC on 2026-10-31, about 11,500 events, seven helpers, three
compactions). Its own account is
[VERY_DEEP_CHECK_LATEST_RUN.md](../spec/VERY_DEEP_CHECK_LATEST_RUN.md) and
its leftovers
[todo-2026-10-30-very-deep-check-findings](todo-2026-10-30-very-deep-check-findings.md);
this item is what its transcript shows beyond them: what broke, what fought,
and what it band-aided.

### Fixed at the cause, each with a case that fails on the old code

1. **The reply gate held a dead job "still running" for eight hours.** The
   first full test run started before a worker restart and died with the
   old container; no notification came, and about fifteen turns were
   refused for one waiting line. The opposite case the same day: four
   helpers running and no shell job, and a waiting line was refused for
   want of a Boildown. A command whose output file this machine lacks is no
   longer running; a helper is, until its own notification
   ([tools/precedent_reply_check.py](../tools/precedent_reply_check.py)).
2. **A helper's unfiled output was deleted to make the container read
   clean.** 62 incident verdicts were lost that way. The run moved the
   helper rule into very-deep-check, and the account check refuses an
   account with no `## Incidents` from 2026-11-01; the reply gate's three
   container remedies now say a helper's unfiled output is never
   "something you could make again"
   ([tools/precedent_gate.py](../tools/precedent_gate.py)).
3. **`/dev/null` was replaced by an ordinary file, the second time**
   ([gotcha-2026-10-10](../gotchas/gotcha-2026-10-10-git-config-global-with-dev-null-replaces-dev-null.md)).
   The identity test kept an inherited `GIT_CONFIG_GLOBAL`; 42 fixture lines
   used `/dev/null`. Now: the test drops it, the harness swaps a non-file
   one at start, fixtures use `empty_gitconfig()`, and
   `check_no_fixture_points_git_config_at_dev_null` refuses the pattern.
4. **The privacy gate refused plain local commits** (2026-10-20 twice, and
   again here): the session trailer's URL read as network and the author's
   address as a private term. A commit's message is now blanked before the
   gate reads a command
   ([tools/outbound_privacy_gate.py](../tools/outbound_privacy_gate.py)).
5. **The push gate read `git checkout -b "$(...)" && ... git push` as a
   push from the branch it left** (main) and refused it as one. Such a
   branch is now unreadable, never "no change"
   ([tools/precedent_branches.py](../tools/precedent_branches.py)).
6. **The close detector read helpers' reports as "the person said"**,
   about twenty times across three turns. Task notifications are dropped
   ([tools/precedent_close_detect.py](../tools/precedent_close_detect.py)).
7. **Two session-file tests read the person's real set clones**, and went
   red while those sat on their landing branches; the session moved the
   clones back to main. Both now point the user config at nothing.

### Calls for Morgan

Each with this session's pick (needs: a decision -- Morgan's).

- **The quick tier keeps passing what the whole suite fails.** Staging went
  red twice from checks only the full run reaches, and the combined branch
  failed four times on things each helper branch had passed. Pick: run the
  harness cases a change's files reach (`PRECEDENT_HARNESS_SINCE`, which the
  landing already prints as a background step) inside `--land` itself, in
  the background, and refuse the next landing while one is red -- not the
  whole suite on every push.
- **"Takes a pull request" adds a step, not a review.** About ten landings
  were refused for touching check code, and each time the same session
  opened the pull request and merged it a minute later. Pick: let `--land`
  open and merge that pull request itself, so the record is the same and
  the round trip goes; keep the refusal only where a person must look.
  This changes a governance practice (`go-update`), so it is yours.
- **[tools/verify_harness.py](../tools/verify_harness.py) is one file of
  about 97,600 lines and 889 tests.** A helper could not write five owed
  planted cases because another held the file, and its sibling sessions
  edit it every day. Pick: split it, one module per area under a tools
  directory, with the runner and the shared fixtures left where they are,
  as a planned piece of work in a session of its own.

### Left

- **The ladder set's own
  [ladder_branches_cases.py](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/checks/tests/ladder_branches_cases.py)
  points `GIT_CONFIG_GLOBAL` at `os.devnull` twice** (`_fixture_git_env`
  and one fixture of the stale-ref checks). It is the set's file, and this
  session has no push access to the set (needs: push access to
  precedent-shared-ladder, or a session rooted there). The vendored
  [tools/upstream_fix.py](../tools/upstream_fix.py) copies in the sets take BestPractice's fix by
  Update Vendors.
- **A stale `.git/shallow` stopped a consumer's push check a third time**
  ([gotcha-2026-09-28](../gotchas/gotcha-2026-09-28-stale-shallow-entries-for-deleted-branches-survive-unshallow.md)),
  cured by hand each time. Its Prevention is deliberately not mechanical;
  a safe middle is for the refusal to run the read-only reachability test
  itself and print the exact move when every entry is unreachable (needs:
  a session of its own -- out of this one's scope).

## Notes

2026-10-31: the transcript was read in full by three helpers over a digest
of every event, each claim then checked against the code here; the
reproductions are in each fix's commit message.

2026-10-31, Morgan on the four calls (strength: assented): "Yes on all
four, then booked". What each became:

- **The quick tier and the whole suite:** `--land` now starts the harness
  checks a landing reaches in the background, on a worktree of what landed,
  and records the verdict; the next `--land` refuses while it is red, except
  the one that says it is the fix (`--fixing <commit>`).
  `check_land_holds_while_its_reached_tests_are_red`.
- **The pull request a landing takes:** `--land` opens and merges it itself
  where a GitHub token works, then runs `--land-confirm`; elsewhere it
  prints the steps, as before. The ladder set's `go-update` says so.
- **The one-file harness:** handed to the session `split
  tools/verify_harness.py into one module per area`
  (https://claude.ai/code/session_01Xcy6TzryhiJpXYaWJphgDM), which reports
  back when it lands. This item closes when it does.
- **The ladder set's `/dev/null` lines:** fixed there and on its staging
  (precedent-shared-ladder #164).

2026-10-31, closed on its condition: the harness split landed on staging
(#1466, from its own session), and with it the last thing open here. Its
two loose ends were taken up here: the ladder set's landing guard now
treats `tools/harness/` and [tools/harness_parts.py](../tools/harness_parts.py) as code other work is
judged by (precedent-shared-ladder #166), and a stale example in
`reply_check.json`'s requirement 13, left by #1465, now carries the
What's blocking line that rule asks for.

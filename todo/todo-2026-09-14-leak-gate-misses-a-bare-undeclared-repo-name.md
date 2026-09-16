---
slug:              todo-2026-09-14-leak-gate-misses-a-bare-undeclared-repo-name
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         "2026-09-14"
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="leak-gate-misses-a-bare-undeclared-repo-name"></a>**The leak gate
  refuses a private repo named as `owner/name`, and lets the same repo through
  under its BARE name when no line in the blocklist has ever mentioned it.**
  **Remind:** the deny line is a band-aid — bring up the permanent fix, the
  one that makes the gate derive bare-name patterns instead of being told them
  one repo at a time, when I ask for **Three Things** (2026-09-14, Morgan)
  **Disposition:** ask (2026-09-14, Morgan)

  **Two fixes, and only one of them is the real one**
  ([durable-fix](../practices/durable-fix.md)). Morgan, 2026-09-14: *"I prefer a
  real fix, not a band-aid; so let's put the deny item as you said, and also
  note in the TODO that we should do the permanent fix eventually."*

  1. **The band-aid, and it is named as one:** a deny line in
     `precedent-individual`'s blocklist for the one repository that got
     through. It closes that repository and nothing else, and the next repo
     nobody has written down is in exactly the same position. It lives in
     machine-adjacent config in another repository — rung 1 of durable-fix for
     that repo, but it does not generalize, which is the sense in which it is
     a band-aid rather than the sense of being fragile.
  2. **The permanent fix, still open:** stop maintaining the bare-name list by
     hand. Derive the patterns from the repositories the environment can
     actually see — declared sources in `precedent.json`, attached clones, the
     session's own git remotes — so a private repo is covered the moment it
     exists rather than the moment somebody remembers to write it down. The
     open design question is the false-positive cost, and it is a real one:
     refusing every capitalized word that might be a repo name is what got the
     blocklist approach replaced by an allowlist in the first place. Deriving
     from what is on disk is narrower than that and is the shape worth costing
     first.

  **This item is `ask` because Morgan set it**, and the `**Remind:**` line
  says when: a session answering [three-things](../practices/three-things.md)
  should weigh this item as a candidate. It is not a standing licence to raise
  it in every reply.

  **Measured 2026-09-14**, in the session that landed this file's
  `practice-links-travel` change. Writing a consuming repository's bare name
  into a practice file's `## Story` passed the gate clean — 973 units, 0 hits.
  Planting the qualified form of the same repository into a tracked file was
  refused on the next run, naming the private-owner rule and the `allow` line
  that would accept it. So the owner-is-private-by-default rule works exactly
  as documented for the qualified form, and the bare form of a repository
  nobody has ever written down reaches a public tree with nothing in its way.

  **`# visibility-audit: auto-cover-bare-names on` is not this case**, which
  is what makes it easy to read as covered: it covers the bare form of names
  the blocklist already knows, and a repo that has never appeared in an
  `allow` line is not one of those. The session caught its own reference by
  reading the blocklist by hand and removed the name; nothing mechanical
  would have stopped the push.

  **Why this is queued rather than fixed here** ([todo-is-a-handoff](../practices/todo-is-a-handoff.md)):
  the two candidate fixes are both somebody else's call. Adding a deny line
  for the repository is a one-line change to a blocklist that lives in a
  PRIVATE set this session cannot push to — `add_repo` refuses across owners.
  And the general fix is a design question with a real cost: a gate that
  refuses arbitrary capitalized words because one of them MIGHT be a private
  repo name would false-positive on ordinary prose, which is the failure mode
  that got the blocklist approach replaced by an allowlist in the first place.
  A narrower shape worth costing: derive the bare-name patterns from the repos
  the environment can actually see — declared sources, attached clones, the
  session's own remotes — rather than from what the blocklist happens to name.

  **What it is not.** Not the stale-blocklist gotcha: this clone was 28
  commits behind at session start, and re-reading the current file by hand
  showed no line covering the name either way. Not a finding about the three
  items already recorded upstream in the consuming repo's own
  `upstream-findings` file.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

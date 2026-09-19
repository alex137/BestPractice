---
slug:              todo-2026-09-07-blocklist-stem-not-full-name
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            2026-09-07
---
## What

- <a id="blocklist-stem-not-full-name"></a>~~**Put the private consumer repo's NAME STEM into the leak blocklist, not
  its full repo name.**~~ **Done (2026-09-07)**, in the individual practice
  set — all seven repo-name patterns rewritten from `\bFullName\b` to a
  truncated stem plus `[\w-]*`. Raised after two hits of `<that repo>-local`
  — the name its repo-local practice source carried before `source-naming`
  renamed it — survived both the vocabulary sweep and `d167ada`'s
  fix-forward, and sat on the public branch from 07:02 to 21:17 that day.

  **What the fix turned out to be is not what this item assumed**, and
  [AGENTS.md](../AGENTS.md)'s gotcha now carries the corrected version: the
  suffix was never the problem, because `\bFullName\b` already matches
  `FullName-local` (a hyphen is a word boundary). The leak got through on the
  repo's **short form**, so truncation is the mechanism and the trailing
  `[\w-]*` is belt-and-braces. Each stem was cut only as far as its measured
  hit count against this tree stayed at zero, and two candidate cuts that
  scored zero were still rejected as fragments an ordinary camelCase
  identifier could produce. Positive control over the two commits that
  carried the leak: the old list reports clean, the stems report three hits.
  Negative control asserts the gate's message, not just its exit code. The
  repo-reference allowlist was already switched on, with a reason on every
  allow line.

  **Nothing to do here.** The patterns and their evidence live in the private
  set by design — a list of the words you must not publish cannot be
  committed to this repository ([spec/SOURCES.md](../spec/SOURCES.md),
  `python3 tools/leak_gate.py --explain`). This repo's own runs still check
  the default list only, and still say so.

## How It Closes

Already closed 2026-09-07 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.

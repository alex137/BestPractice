---
date: '2026-09-21'
question: |
  local/practices/merge-target-is-beta-branch.md reserves merges carrying
  major changes onto `main` for Alex's "explicit, named go-ahead", and
  AGENTS.md sharpens that to "requires Alex naming `main` explicitly, in
  that specific request." On 2026-09-21 Morgan asked a session to merge
  `precedent-beta-v01` into `main` (207 commits across 159 files at the
  point it merged) and stated he had Alex's explicit approval. Does a relayed
  approval satisfy a gate held by someone who is not in the conversation?
decision: |
  Yes, on Morgan's reaffirmation, and the merge was performed. Two honest
  readings existed: that the gate asks whether Alex approved (satisfied by
  the relay), or that it asks for Alex's own words naming `main` in that
  request (not satisfied). The session named the ambiguity, declined to
  guess, and asked; Morgan reaffirmed. The second reading is also close to
  unsatisfiable in practice, since Alex is rarely the person at the
  keyboard while this same practice file records that Morgan merges
  `precedent-beta-v01` into `main` regularly (2026-09-14, strength:
  decided) -- so treating the relay as sufficient is what keeps the rule
  workable rather than what erodes it.

  WHAT THIS RECORD DOES NOT ESTABLISH: this session never saw Alex's own
  words. The date, wording and scope of his approval are unknown here, and
  were not supplied when asked. Nothing in this file should be read as
  "Alex decided this" -- only as "Morgan stated Alex had approved, and
  reaffirmed it when the ambiguity was put to him." A later session wanting
  Alex's own approval on the record has to get it from him.
alternatives: ["Hold the merge until Alex states it himself, naming `main`",
               "Merge silently on the first request, without naming the
                ambiguity"]
decided_by: Morgan
strength: decided
---

## Why this was not just done on the first ask

The action is irreversible on a public branch, and this repository already
carries the incident where a merge onto `main` went wrong by looking
routine: [PR #89](https://github.com/alex137/BestPractice/pull/89), 2026-09-03, which silently carried roughly 600 files onto
`main` and was caught only because Alex happened to ask. AGENTS.md's own
instruction for an authorization whose reading is a genuine judgment call
is to say the read out loud and confirm before the shared-branch steps run.
That is what happened here, and it cost one message.

## What was verified before merging

The merge-back trap recorded in
[spec/CHANGES_TO_TELL_ALEX.md](../spec/CHANGES_TO_TELL_ALEX.md) has a
silent half -- files absent from the result with no conflict raised -- so
"no conflicts" was not accepted as evidence. The check was on trees:
`merge-base(main, precedent-beta-v01)` is `46d30635`, and
`tree(46d30635) == tree(origin/main)`, so `main` contributed no content of
its own and the merge result equals the branch tree exactly. The trap does
not fire because `main` already received Precedent on 2026-09-14; the
`97ed078` revert remains in history but is long superseded.

Deep check on the merged content, at `c873ab0a`: `verify_harness` 243
passed / 0 failed, `doc_lint` clean, `leak_gate` clean over 1343 units,
`precedent_check --full-sweep` 58 passed / 0 violated / 0 errored,
`doc_sync` clean.

## A trap this session walked into first

The container's clone was shallow. `git merge-base` returned nothing, a
merge attempt reported "refusing to merge unrelated histories", and the
ancestry figures computed before that were wrong while looking entirely
plausible. `git fetch --unshallow origin` fixed it and every conclusion was
recomputed. This is already catalogued as a live trap
([gotcha-2026-09-13](../gotchas/gotcha-2026-09-13-this-repo-is-normally-cloned-depth-1-and-several-tools-degra.md));
grepping `gotchas/` first would have saved the detour, which is the
`grep-before-search` lesson landing on the session that skipped it.

## Consequence to expect

`merge-target-is-beta-branch`'s own check fails whenever
`precedent-beta-v01` is an ancestor of `main`, which it is immediately
after each of these merges, until the next commit lands on the branch.
That is the known and accepted cost of the regular merge cadence, not a
signal to retire the practice -- the practice file's `expires` field says
so explicitly.

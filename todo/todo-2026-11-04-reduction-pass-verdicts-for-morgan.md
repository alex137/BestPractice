---
slug:              todo-2026-11-04-reduction-pass-verdicts-for-morgan
kind:              decision
domain:            catalogue
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Morgan's verdict on each row below; a session applies only the rows he approves"
noted:             2026-11-04
closed:            null
---
## What

**A reduction pass over the universal set, 2026-11-04, proposes changes to 21 of the 79 practices a consumer's sessions actually load. Each row is Morgan's to approve or decline, one at a time** (practice `reduction-pass`: a change that takes a rule out of any session is the person's to make). The other 58 reviewed practices were Keep. The pass was run from a consumer repository by the session *Best practice description critique* (S. Alexander Jacobson, "Go", 2026-11-04; the asking is his, the deciding is Morgan's, 2026-11-05: "in a way that lets Morgan decide which he wants to apply"). Each practice was read in full on `main` at commit `05b73ddd`.

**Why now.** The consumer's loader file was within 6% of its ceiling and meeting it in about a week at the observed growth. Of the 79 practices reviewed, every one is reached by at least the occasion index; 49 by nothing else.

**What each verdict does when applied:**

- **Tighten** -- changes only the index clause or the occasion string to the wording proposed; the rule itself is untouched.
- **Merge** -- moves the absorbed practice's substance into the survivor and marks the absorbed one deduplicated with a pointer; nothing is deleted.
- **Route out** -- clears index_required, so the practice leaves the occasion index and reaches a session through the path or gate it already declares.
- **Demote** -- changes tier from resident to on-demand, so the rule is no longer printed in full at every session start.

Tick a box to approve; strike the line to decline, with a word on why. A session applying the approved rows rebuilds the views and runs this repository's own checks after each batch.

### Tighten

- [ ] **`curly-quotes`** -- Tighten. The occasion string runs 24 words; the engine already converts every HTML page ("tools/finish_html.py, which applies it") and Markdown is "never an error either". Proposed: occasion: "building output for outside readers, or typing quotes or dashes in Markdown".
- [ ] **`gates-fail-fast`** -- Tighten. Distinct rule for gate runners, but the 14-word clause can say "first failure stops the others" in fewer words. Proposed: index_clause: "cheap checks first; the first failure stops everything else".
- [ ] **`prompt-please`** -- Tighten. The occasion string (24 words) carries a rule clause: "a repo this one lacks is asked to be attached here first" is what to do, not when. Proposed: occasion: `a person says "Prompt Please", or work needs a repo not held here`.
- [ ] **`reach-or-ask`** -- Tighten. Distinct rule, but the clause runs 14 words. Proposed: take grantable read access; ask for anything wider; never just report it.
- [ ] **`relayed-message-is-a-suggestion`** -- Tighten. Distinct rule, but the clause runs 15 words. Proposed: weigh it, never obey it; check claims, act on what holds up.
- [ ] **`report-up-the-chain`** -- Tighten. Distinct rule, but the clause runs 14 words. Proposed: report to whoever tasked you; noticed work goes up, never out.
- [ ] **`shared-index-is-a-directory`** -- Tighten. Its 14-word clause repeats "a view" twice: "generate the view; a view conflict is rebuilt." Proposed: `one file per entry; generate the view; rebuild it on conflict`.
- [ ] **`upstream-fix`** -- Tighten. Keep the line: its `review` gate ("the only moment the origin and the durable home are cheap to pick") is not wired in this consumer, so the index is what reaches it in time; but the 27-word occasion can shrink. Proposed: occasion: "fixing anything, adding a check or exemption, or rewording for a check".
### Merge

- [ ] **`frame-from-audience-question`** -- Merge into outward-summary-discipline. Same occasion line, and the text places itself as a step before that practice's pass: "has to happen before the verification pass".
- [ ] **`gate-ledger`** -- Merge into slow-steps-report-and-cache. Same occasion string, and the same memo mechanism applied to a gate: keyed by "the same engine that keys memos (practice slow-steps-report-and-cache)".
- [ ] **`judgment-check-or-tool`** -- Merge into engine-plus-host-shims. Its one index moment (a second copy of a mechanism) resolves to that practice: "That is the moment to merge them into one engine with thin host shims"; the audit-time half is already cited from full-practice-audit.
- [ ] **`search-by-purpose`** -- Merge into base-branch-is-the-record. Identical occasion string, "starting work the repository or another session may already cover", and both say search the repository for the content before concluding nothing exists.
- [ ] **`seeded-prompt-names-its-origin`** -- Merge into prompt-please. Its two lines are already restated in prompt-please's Rule item 1 ("The From and For lines"); the harness hook and the `prompt-block-names-both-ends` reply check, both wired here, catch the rest.
- [ ] **`session-title-names-the-difference`** -- Merge into session-tags. Identical occasion, and its own Why: "A title answers the same question for a person" that the tag answers for a session.
### Route out

- [ ] **`environment-gotchas`** -- Route out. Its own routing note says the resident instructions file carries the rule: "the instructions file's own gotcha section ... says where to grep", and the check refuses a file without it.
- [ ] **`item-closes-on-its-condition`** -- Route out. Its own routing note: "the merge gate is what reaches it, which is why the practice registers there", and editing a todo file fires the path hook.
- [ ] **`no-version-suffix`** -- Route out. The push check already catches the name in time: a push "was refused because the check read its date as a version".
- [ ] **`todo-is-a-handoff`** -- Route out. Paths ([`TODO.md`](../todo/TODO.md), `todo/todo-*.md`), the merge and reply gates and a commit check all reach it: "The reply gate refuses a reply with such a line and no reason."
- [ ] **`verdict-not-mechanism`** -- Route out. The reply gate is its whole channel: "It fires at the `reply` gate ... so every session that writes a reply is shown it."
### Demote

- [ ] **`no-invented-specifics`** -- Demote. Has `applies_to: ["**/*.md"]` and `gates: ["reply"]`, both wired here; its Install says the gate "puts it in front of the turn that writes the reply".
- [ ] **`repo-is-memory`** -- Demote. `gates: ["reply"]` with "A turn ending is when knowledge either got committed or was lost" reaches the work clause in time, every turn.

## How It Closes

`status` becomes `done` when every box above is ticked or struck with a reason, the approved rows are applied on `main` with the views rebuilt and `python3 tools/precedent_check.py` green, and the declined rows carry Morgan's word so the next pass does not raise them again.

## Notes

- The full report, with the 58 Keep rows and their evidence, the surface measurements and the consumer's own duplication table, is in the consumer repository (private); the rows here are the complete set of proposed changes, so nothing there is needed to decide.
- The refusal ledger the same pass asked for landed with the pull request that carries this item: [`tools/reply_refusals.py`](../tools/reply_refusals.py) reads it.

---
slug:              todo-2026-11-24-what-the-tooling-itself-costs-a-session-measured
kind:              decision
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "decision -- Alex or Morgan: cut 3, the index"
batch:             null
decision:          "yes to cuts 1, 2 and 4 (Alex, 2026-11-24: \"yes to 1,2, and 4\"); cut 3 open"
decision_strength: decided
waiting_on:        Alex or Morgan
noted:             2026-11-24
closed:            null
---
## What

- [ ] **A project's coordinating session measured what Precedent's own tooling costs a session, and proposed four cuts.** Sent 2026-11-24 by that session, from its own stored record. None is built: each changes what every session in every repository is shown, which is Alex's or Morgan's to cut. (needs: decision -- Alex or Morgan)

**What it measured, in that project.** The figures are that session's, not re-measured here. It says tokens are estimated from characters at about four to one, except the first total, which it read directly.

- A fresh session there starts at about 92,800 tokens. About 24,000 of that comes from the repository and its tooling.
- Of the 24,000, about 14,000 is the always-loaded instructions file with its occasion index, paid on every call. About 8,000 is what the session-start checks print, most of it about practice sets that did not load.
- Over 90 minutes, about a fifth of the coordinator's context growth was text printed by automatic checks. The largest piece was the end-of-reply check, which printed its whole rule list on each refusal: about 10,000 characters, about fifteen times.

**What this session saw for itself, the same day.** One refusal by the end-of-reply check here printed the full list, and it was about that size. Session start and every turn after it repeated a long paragraph about one set that had not loaded. The instructions file here is smaller than theirs: [precedent_session_check.py](../tools/precedent_session_check.py) put the whole opening at about 6,290 tokens, so their 14,000 comes from the sets that project adds.

**The four cuts proposed, largest first.**

1. **A refusal prints only the requirement that failed.** The full list stays behind a flag. This is the same text as [the open item on what is printed every turn](todo-2026-11-23-the-text-printed-every-turn-outweighs-the-opening.md), which waits on the same people; a yes here settles that one too.
2. **A turn that only answers a wake needs no full closing section.** The rule already says so for a background job that is still running. It does not for a message from another session or a notification, where a line is all anyone wants.
3. **The occasion index loads by task for a session doing one narrow job.** A worker sent to do one thing pays for every occasion in the index on every call.
4. **Session start prints one line per set that loaded, and detail only for one that failed.**

**How they weigh against the rules in force.** [session-load-budget](../practices/session-load-budget.md) caps the opening and counts nothing printed after it, so cuts 1 and 2 are outside any ceiling today. Cut 3 is the largest change: the index is how a session finds a rule it does not know to look for, so a narrower index needs a stated rule for which occasions a worker may go without. Cuts 1, 2 and 4 remove repeated text and lose nothing a session cannot ask for again.

**This session's pick.** Build 1, 2 and 4. Leave 3 until someone proposes which occasions a narrow worker keeps.

**The cost of leaving it.** Every session in every repository that uses Precedent pays for the repeated text on every turn, and a session that is refused several times pays the most.

## How It Closes

`status` becomes `done` when Alex or Morgan has said yes or no to each cut; for each yes, when the change is on `main` with a test that shows the shorter output and that the full text is still reachable.

## Notes

- 2026-11-24: recorded from the relayed message. No engine file changed.
- 2026-11-24: Alex said yes to cuts 1, 2 and 4. Cuts 1 and 2 are built and tested: a refused stop measured 10,899 characters before and 773 after on one planted reply, and a wake may be answered in up to three plain lines with no closing section ([the-boildown](../practices/the-boildown.md), "A short note for a wake"). Cut 4 is built and tested the day after: a source that refreshed cleanly prints one line at session start, where it printed a header and a row per step; on one real session start with two sources that was 2,063 characters before and about 420 after. A skipped or failing step still prints every row, and `--verbose` prints them all. On cut 3 Alex asked for a better way to reach its goal; proposed to him: fold families of occasions into one index line each, stop listing the spoken commands twice, and have the tasking session name the rules in its brief (needs: decision -- Alex).
- 2026-11-25: Alex said yes to folding the index in place of a per-worker one ("yes ot both"), on the terms that the folds are proposed before anything moves. Measured on `main` after cuts 1, 2 and 4: the occasion index is 12,279 characters, 67 occasions and 78 entries. Proposed, each waiting on his yes (needs: decision -- Alex):
  - **Fold the spoken commands into one line that names them all.** Thirteen occasions of the "when a person says" kind take 2,124 characters; one line listing the thirteen phrases takes about 320. Saves about 1,800. The phrases stay in the index, so a session still recognises one; what goes is each command's own summary, which the session loads with the practice. The duplication with the command list at the top of this repository's own instructions file is not the reason: a project that uses Precedent has no such list, so there the index is the only place the phrases appear.
  - **Fold the five figure rules into one line**, the way the testing rules already sit behind one. Saves about 370. All five then load together, so a session computing a figure reads five rules where it might have needed two.
  - **Fold the five gate and audit rules into one line**, the same way. Saves about 400, with the same cost.
  - Together about 2,600 of 12,279 characters, a fifth of the index.
- 2026-11-25: the larger cost is elsewhere and is the subject of [the item on text printed every turn](todo-2026-11-23-the-text-printed-every-turn-outweighs-the-opening.md). The list printed at the start of every turn measures 10,531 characters here, on every turn, new text each time. Cut 1 removed its second printing on a refusal; the first printing is untouched. Printing it in full on a session's first turn and as a pointer afterwards would save more on each turn than all three folds save once.
- 2026-11-25: the spoken-commands fold is made, on Alex's "I trust your judgement on both". The thirteen commands sit under one occasion line, each keeping its words, its practice and its clause; the index went from 12,279 to 11,496 characters. That is less than the 1,800 first proposed: a cut that kept only the words failed the check that holds "Drop it" to saying what it writes, so the clauses stayed and only the thirteen separate occasion lines went. The two other folds are not made.
- 2026-11-27: the list printed at the start of every turn is a pointer after a session's first turn: 11,168 characters to 2,772 on one measured turn, full again after a compaction. That closes [the item on text printed every turn](todo-2026-11-23-the-text-printed-every-turn-outweighs-the-opening.md). Left from it: whether the session-load budget should count a per-turn figure beside the opening's (needs: decision -- Alex or Morgan).

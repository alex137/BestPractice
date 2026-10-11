---
slug:        update-all-vendors
title:       "\"Update All Vendors\" updates every repository the person uses Precedent in, from one session"
tier:        on-demand
severity:    default
applies_to:  ["tools/precedent_update_all.py"]
applies_to_why: "Mostly a phrase in a message, which the occasion index carries; the path reaches a session editing the tool that does the work. Decided: 2026-10-11, when the practice landed."
occasion:    "a message says \"Update All Vendors\", or asks to update every repository the person uses Precedent in"
gates:       ["merge"]
gates_why:   "Each repository's update lands as a merge, and the merge is the moment the run's own rules (one merge per pull request, the full head, nothing run after) still apply."
index_clause: "every repo using Precedent, found fresh; never register them as roots"
checked_by:  null
defines:     ["Update All Vendors"]
command:     {"Update All Vendors": "Run Update Vendors in every repository you use Precedent in, one after another, from the session you are in -- finding any new ones first -- and merge each one, stopping only for the decisions that are yours. Say it as \"Update All Vendors and merge them\": Claude Code's auto mode lets a merge through only when your own words name it."}
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-10-11"
approved_by: "Morgan, 2026-10-11 -- the phrase and the advice to say \"and merge them\" (decided: \"We can say update all vendors as the phrase\"); the design, one tool that never loads a repository's instructions (assented: \"Okay, let's do it\" to the session's proposal); no stored list, every repository found fresh each run (Morgan's own question, \"Is it even worth it to have a list?\"; the session agreed, and he said \"do what you think is best\": assented)"
---
## Rule
**"Update All Vendors" runs [Update Vendors](vendor-update-runbook.md) in
every repository the person uses Precedent in, from the session it is said
in.**
Like the single phrase it carries the merge of each one. **Say it as
"Update All Vendors and merge them"**: Claude Code's auto mode lets a merge
through only when the person's own words name it
([gotcha](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge.md)),
and one sentence that names the merges covers every repository in the run.

**Never make one of those repositories a root of the session.** A repository's
instructions load when it is registered as a root, not when it is attached
and cloned, so attach each one and let the tool clone it. Never call
`register_repo_root` for one, even though the attach result says to. That is
the whole saving: the session grows by a line per repository, not by a set
of instructions per repository.

The sequence, with
[tools/precedent_update_all.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update_all.py) run from
the BestPractice clone:

1. **Find the repositories, fresh.** List every repository the person can
   reach (in Claude Code's cloud sessions, `list_repos`) and leave out the
   archived ones. There is no stored list to read or keep current.
2. **Attach each one for push** (`add_repo`, access `push`). Do not clone
   it and do not register it.
3. **Run the update:** `precedent_update_all.py --workdir
   <scratchpad>/vendors OWNER/REPO ...` with every repository from step 1,
   and a `--trailer` for each line the session's commits must end with. The
   tool skips BestPractice itself, says NOT USED for a repository with no
   `precedent.json`, and updates the rest. Each update runs its deep check,
   so this is long: say how long and when it lands before starting
   ([answer-first-ask-before-long-work](answer-first-ask-before-long-work.md)),
   and run it in the background. It prints one line per repository.
4. **For each PUSHED line, open the pull request and merge it** into the
   base the line names, with the full 40-character head it prints. The
   merge tool's own answer is the postcondition: run nothing after a merge
   in that turn (the gotcha above). If auto mode refuses the first merge,
   stop and ask once for all of them by name: "Merge the N update pull
   requests".
5. **Hand each ASK, LEFT or FAILED repository to its own subagent**, with a
   fresh context. Give it the clone and log paths the line names, and tell
   it to read that repository's own instructions, work the update per
   [vendor-update-runbook](vendor-update-runbook.md), and report back in
   one line. Its context, and that repository's instructions, are thrown
   away when it returns. A question that is the person's comes back up, and
   all of them reach the person together in one message.

## Detail
**No list, on purpose.** A stored list of the person's repositories saved
only the check on the few that do not use Precedent, and it went stale every
time one started or stopped using it, or was archived. Finding them fresh
costs a few seconds per repository and is never wrong.

**Practice sources are updated too.** An individual or shared source has a
`precedent.json`, and [precedent_update.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update.py)
updates one the same way it updates a consuming repository.

**One session per repository is the fallback, not the route.** A
repository that needs its own hooks to run, or a long back-and-forth, can
still get its own session ([prompt-please](prompt-please.md)). Twenty of them
cost twenty sessions' start-up, twenty sessions to archive and twenty
merges to ask auto mode for, and the run above avoids all of that.

## Why
On 2026-10-11 Morgan had about twenty repositories using Precedent. Updating
them one session at a time took too long. One session holding all of them as
roots carried every repository's instructions on every turn. The run above
costs one session plus about a page of attach output per repository, and
the instructions of only the repositories that needed a judgment call, each
inside a subagent that is thrown away.

## Story
Morgan, 2026-10-11, in a brainstorm: *"when I put all 20 in one session, it
uses up a lot of tokens ... I go either one repo at a time, and the problem
there is it takes a lot of time."* He proposed a list kept in his own
files, with each repository added, updated and removed in turn. The session
found that removing is unnecessary: attaching never loads a repository's
instructions, and registering it as a root does. He chose the phrase
"Update All Vendors", and asked that both phrases recommend naming the
merge. The first version kept the list in his individual source; asked
"Is it even worth it to have a list?", the session agreed it was not, and
the list went before it landed. The plan of record is
[spec/UPDATE_ALL_VENDORS_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/UPDATE_ALL_VENDORS_PLAN.md).

## Install
Nothing to install in a consuming repository: the phrase runs
[tools/precedent_update_all.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update_all.py)
from the BestPractice clone, the same way Update Vendors runs that clone's
[precedent_update.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update.py).
The session needs only what any session has: a way to list the person's
repositories and to attach one, and the BestPractice clone beside the work.
Where the harness cannot list repositories, name them to the tool by hand.

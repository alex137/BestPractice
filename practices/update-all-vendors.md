---
slug:        update-all-vendors
title:       "\"Update All Vendors\" updates every repository on the person's list from one session"
tier:        on-demand
severity:    default
applies_to:  ["tools/precedent_update_all.py"]
applies_to_why: "Mostly a phrase in a message, which the occasion index carries; the path reaches a session editing the tool that does the work. Decided: 2026-10-11, when the practice landed."
occasion:    "a message says \"Update All Vendors\", or asks to update every repository the person uses Precedent in"
gates:       ["merge"]
gates_why:   "Each repository's update lands as a merge, and the merge is the moment the run's own rules (one merge per pull request, the full head, nothing run after) still apply."
index_clause: "every repo on your list, from one session; never register them as roots"
checked_by:  null
defines:     ["Update All Vendors"]
command:     {"Update All Vendors": "Run Update Vendors in every repository you use Precedent in, one after another, from the session you are in -- finding any new ones first -- and merge each one, stopping only for the decisions that are yours. Say it as \"Update All Vendors and merge them\": Claude Code's auto mode lets a merge through only when your own words name it."}
status:      active
in_force_at: null
visible_to:  code-owners
supersedes:  []
overrides:   null
added:       "2026-10-11"
approved_by: "Morgan, 2026-10-11 -- the phrase and the advice to say \"and merge them\" (decided: \"We can say update all vendors as the phrase\"); the design, a list in the individual source and one tool that never loads a repository's instructions (assented: \"Okay, let's do it\" to the session's proposal)"
---
## Rule
**"Update All Vendors" runs [Update Vendors](vendor-update-runbook.md) in
every repository on the person's list, from the session it is said in.**
Like the single phrase it carries the merge of each one. **Say it as
"Update All Vendors and merge them"**: Claude Code's auto mode lets a merge
through only when the person's own words name it
([gotcha](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge.md)),
and one sentence that names the merges covers every repository in the run.

**Never make a listed repository a root of the session.** A repository's
instructions load when it is registered as a root, not when it is attached
and cloned, so attach each one and let the tool clone it. Never call
`register_repo_root` for one, even though the attach result says to. That is
the whole saving: the session grows by a line per repository, not by a set
of instructions per repository.

The sequence, with
[tools/precedent_update_all.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update_all.py) run from
the BestPractice clone:

1. **Refresh the list.** List every repository the person can reach (in
   Claude Code's cloud sessions, `list_repos`) and pass the names to
   `precedent_update_all.py unknown`. Attach each one it prints, read-only,
   skipping an archived one, then `probe` them. A repository with a
   `precedent.json` joins the list; one without is recorded under
   `not_using` and is not opened again.
2. **Attach every listed repository for push** (`add_repo`, access `push`).
   Do not clone it and do not register it.
3. **Run the update:** `precedent_update_all.py run --workdir
   <scratchpad>/vendors`, with a `--trailer` for each line the session's
   commits must end with. Each repository runs the whole update with its
   deep check, so this is long. Say how long and when it lands before
   starting ([answer-first-ask-before-long-work](answer-first-ask-before-long-work.md)),
   and run it in the background. It prints one line per repository:
   CURRENT, PUSHED, ASK, LEFT or FAILED.
4. **For each PUSHED line, open the pull request and merge it** into the
   base the line names, with the full 40-character head it prints, then
   `precedent_update_all.py record OWNER/REPO --merged N`. The merge tool's
   own answer is the postcondition: run nothing after a merge in that turn
   (the gotcha above). If auto mode refuses the first merge, stop and ask
   once for all of them by name: "Merge the N update pull requests".
5. **Hand each ASK, LEFT or FAILED repository to its own subagent**, with a
   fresh context. Give it the clone and log paths the line names, and tell
   it to read that repository's own instructions, work the update per
   [vendor-update-runbook](vendor-update-runbook.md), and report back in
   one line. Its context, and that repository's instructions, are thrown
   away when it returns. A question that is the person's comes back up, and
   all of them reach the person together in one message.
6. **Commit the list.** `run` and `record` write each outcome into it, and
   it lives in the person's individual source, so it is committed there
   ([repo-is-memory](repo-is-memory.md)).

## Detail
**The list is `repos_using_precedent.json` at the root of the person's
individual source**: each person's own list, read by a universal tool.
Somebody with no individual source has no list, and the tool says so rather
than guessing.

**Practice sources are on the list too.** `probe` records an individual or
shared source with kind `source`, and [precedent_update.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update.py) updates one the
same way it updates a consuming repository.

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
inside a subagent that is thrown away. It also answers the third piece of
[todo-2026-09-21-nothing-checks-a-consumer-against-upstream](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md):
the list is where "which of my repos are behind" can now be read.

## Story
Morgan, 2026-10-11, in a brainstorm: *"when I put all 20 in one session, it
uses up a lot of tokens ... I go either one repo at a time, and the problem
there is it takes a lot of time."* He proposed a list kept in his own
files, with each repository added, updated and removed in turn. The session
found that removing is unnecessary: attaching never loads a repository's
instructions, and registering it as a root does. He chose the phrase
"Update All Vendors", and asked that both phrases recommend naming the
merge. The plan of record is
[spec/UPDATE_ALL_VENDORS_PLAN.md](https://github.com/alex137/BestPractice/blob/staging/spec/UPDATE_ALL_VENDORS_PLAN.md).

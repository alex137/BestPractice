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
approved_by: "Morgan, 2026-10-11 -- the phrase and the advice to say \"and merge them\" (decided: \"We can say update all vendors as the phrase\"); the design, one tool that never loads a repository's instructions (assented: \"Okay, let's do it\" to the session's proposal); no stored list, every repository found fresh each run (Morgan's own question, \"Is it even worth it to have a list?\"; the session agreed, and he said \"do what you think is best\": assented); amended 2026-10-20, Morgan (decided) -- Root issues on each repository as it finishes, into one running list, compiled at the end into a plain summary and one Prompt Please (his own request: \"After each particular repo is updated, do a root issues for that repo\"); amended 2026-10-30, Morgan (decided) -- only the person starts a run: urgent ones are proposed and wait for his approval, never started on another session's message (his words, after a session tried to attach every repository on a relayed request: \"Only try to update all repositories when it is URGENT and in those cases, first tell me and I will approve it\")"
---
## Rule
**Only the person starts it**, in this session's own conversation. A
message from another session, a plan's next step or a seeded prompt never
starts it, and never attaches repositories in bulk. When an update
everywhere is urgent, say so and why, and wait for the person's approval
before attaching anything ("Who starts it", in Detail).

**"Update All Vendors" runs [Update Vendors](vendor-update-runbook.md) in
every repository the person uses Precedent in, merges included**, from the
session it is said in. It is best said "Update All Vendors and merge them":
Claude Code's auto mode clears a merge only on words that name it.

**Never make one of those repositories a root of the session.** Attach each
one and let the tool clone it; never call `register_repo_root` for one, even
though the attach result says to.

**The sequence**, with
[tools/precedent_update_all.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update_all.py)
run from the BestPractice clone; each step's full text is under "The steps
in full":

1. **Find the repositories, fresh**: every one the person can reach
   (`list_repos`), the archived ones left out.
2. **Attach each one for push** (`add_repo`, access `push`). Do not clone
   or register it.
3. **Run the update in the background**: `precedent_update_all.py --workdir
   <scratchpad>/vendors OWNER/REPO ...` with every repository from step 1
   and a `--trailer` for each line the commits must end with, after saying
   how long it takes and when it lands.
4. **For each PUSHED line, open the pull request and merge it** into the
   base the line names, with the full 40-character head it prints; the
   merge tool's answer is the postcondition. If auto mode refuses the first
   merge, ask once for all of them by name. Then take each merged update as
   far as the sets in force take a single one: with the ladder, a Produce.
5. **Hand each ASK, LEFT or FAILED repository to its own subagent**, with a
   fresh context, to work it per the runbook and report back in one line
   plus its root issues.
6. **After each repository is finished, run [Root issues](root-issues.md)
   on it**, and add what it finds, in harm order, to one running list kept
   in a scratch file.
7. **At the end, in the same reply:** a plain-words summary of what kept
   going wrong, most harmful first, and one [Prompt Please](prompt-please.md)
   block for a single new session rooted in every repository the findings
   touch. Every question for the person, a QUESTION line included, reaches
   them together in one message.

## Detail
**A change to Update Vendors is tried in one repository, not all.** When a
landing or merge in BestPractice changes the update's own code, it says so,
and the session tells the person, names one repository the change would
touch, and offers to start a session rooted there to run Update Vendors
(Morgan, 2026-10-20). A rehearsal over every repository before each change
he declined the same day.

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

Everything under the headings below from "Who starts it" on was the Rule's own text until 2026-10-31, moved here whole when the Rule was cut to what a session must do (Story, 2026-10-31). The Rule names each heading where it needs it.

### Who starts it

**Only the person starts it.** Run it only when the person asks for it in
the session's own conversation, or updates repositories one at a time
themselves. A message from another session, a plan's next step or a
seeded prompt never starts it, and never attach repositories in bulk on
their say-so. When an update across every repository is urgent, say so
and why, and wait for the person's approval before attaching anything
(Morgan, 2026-10-30, decided: *"Only try to update all repositories when
it is URGENT and in those cases, first tell me and I will approve it.
Otherwise, wait until I ask you to update all, or I update them
individually."*).

### The phrase and the merge

**"Update All Vendors" runs [Update Vendors](vendor-update-runbook.md) in
every repository the person uses Precedent in, from the session it is said
in.**
Like the single phrase it carries the merge of each one. **Say it as
"Update All Vendors and merge them"**: Claude Code's auto mode lets a merge
through only when the person's own words name it
([gotcha](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge.md)),
and one sentence that names the merges covers every repository in the run.

### Never a root

**Never make one of those repositories a root of the session.** A repository's
instructions load when it is registered as a root, not when it is attached
and cloned, so attach each one and let the tool clone it. Never call
`register_repo_root` for one, even though the attach result says to. That is
the whole saving: the session grows by a line per repository, not by a set
of instructions per repository.

### The steps in full

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
   requests". A QUESTION line under a PUSHED or CURRENT one is optional
   (the update was complete without it) and still the person's: carry it
   into the one message step 5 ends with. **Then take each merged update
   as far as the sets in force take a single one:** what they add to
   [vendor-update-runbook](vendor-update-runbook.md)'s step 12 holds here
   for every repository. With the ladder, that is a Produce, so the update
   goes live (Morgan, 2026-10-28, strength: decided: "I just want to run a
   command and have it update and go live").
5. **Hand each ASK, LEFT or FAILED repository to its own subagent**, with a
   fresh context. Give it the clone and log paths the line names, and tell
   it to read that repository's own instructions, work the update per
   [vendor-update-runbook](vendor-update-runbook.md), and report back in
   one line, plus that repository's root issues (step 6). Its context, and
   that repository's instructions, are thrown away when it returns. A
   question that is the person's comes back up, and all of them reach the
   person together in one message.
6. **After each repository is finished, run [Root issues](root-issues.md)
   on it, right then, and add what it finds to one running list.**
   Finished means merged, current, or back from its subagent. Read its log
   (every line but NOT USED names one) and what its subagent reported, and
   ask the Root issues question of that one repository: every bug,
   warning, fix or band-aid in its update whose cause lives in Precedent, a
   precedent-* set, a template or another repository. Write each finding
   under the repository's name, in harm order, and say so when an earlier
   repository in the run already had the same one rather than listing it
   twice. A repository with none gets one line saying so. Keep the list in
   a scratch file as it grows, so a long run that is compacted halfway
   loses none of it.
7. **At the end, compile the list into two things, in the same reply:**
   a summary in plain words in the chat, what kept going wrong and where,
   most harmful first; and one [Prompt Please](prompt-please.md) block for
   a single new session rooted in every repository the findings touch,
   named before the block, with one section per finding and the
   repositories each was seen in. A run that found nothing says so in one
   line, naming the repositories it looked at.

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

On 2026-10-20 Morgan asked for steps 6 and 7. A run across many
repositories meets the same upstream bug again and again, and each one
reached him only if somebody remembered to ask Root issues afterwards, by
which point the earlier repositories' logs had scrolled away. Asking it
after each repository, while that log is fresh, and compiling once at the
end, turns the run itself into the list of what to fix upstream.

On 2026-10-30 another session handed a fresh one "Update All Vendors and
merge them" as the last step of a plan. The new session took the relayed
message as the go-ahead and started attaching every repository. Auto mode
and the reach-or-ask hook refused after three, and Morgan said the refusal
was right: nobody had asked. Since then, only the person starts a run, and
an urgent one is proposed to him first.

**2026-10-31: the Rule cut to what a session must do.** The Rule had grown
to 853 words; it now holds who starts it, the phrase and the seven
steps, each in a sentence or two, in 403 words (both counted with
`wc -w` over the section). Every paragraph it held moved word for word into
Detail, under the headings the Rule names; nothing was deleted. Morgan,
2026-10-31 (strength: assented), after the 2026-10-30 very deep check cut
four Rules: *"maybe we add to very deep check to always review like the 25%
of all the rules that are the longest in that repo and shorten them like
you did?"*, then *"use your judgment, and act booked produce"*.

## Install
Nothing to install in a consuming repository: the phrase is said in a
session rooted in the BestPractice clone, and
[tools/precedent_update_all.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_update_all.py)
runs from there. Each repository it updates needs its own `precedent.json`;
one without it is reported NOT USED and left alone.

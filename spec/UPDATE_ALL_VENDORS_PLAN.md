---
title:         Update All Vendors
kind:          proposal
status:        accepted
opened:        2026-10-11
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "One phrase updates every repository a person uses Precedent in, from one session, without making any of them a session root: a list in the person's individual source, one tool that clones and updates each in turn, and a subagent only for a repository that needs a judgment call. Both update phrases are best said with the merge named, for Claude Code's auto mode."
---

# Update All Vendors

**Adopted 2026-10-11, Morgan.** The phrase and the "and merge" wording were his
(strength: decided: "We can say update all vendors as the phrase"). The design
below was the session's proposal (strength: assented: "Okay, let's do it"). The
rule is [practices/update-all-vendors.md](../practices/update-all-vendors.md);
the tool is [tools/precedent_update_all.py](../tools/precedent_update_all.py).

## The problem

**Two ways to update many repositories, and both cost too much.** One session
per repository is slow, and each one is a full session: the one-repository
Update Vendors sessions of 2026-10-10 each recorded a few dollars to over
twelve in this account's session list. One session holding every repository as
a root carries each repository's instructions on every turn.

## What decides it

**A repository's instructions load when it is registered as a session root,
not when it is attached.** Attaching (`add_repo`) gives the session access;
`register_repo_root` is the step that loads its instructions file, skills
and plugins. Update Vendors is already one command run from the BestPractice
clone, so the update needs the repository's files, never its instructions in
the session.

**There is no tool to detach a repository from a session**, and with the
above none is needed.

## The design

| Piece | Where | Why there |
|---|---|---|
| The list, `repos_using_precedent.json` | the person's individual source | each person's own repositories; every repository they use declares that source |
| The tool, [precedent_update_all.py](../tools/precedent_update_all.py) | BestPractice `tools/` | the same for everyone; runs from the clone, like [precedent_update.py](../tools/precedent_update.py) |
| The phrase, "Update All Vendors" | [practices/update-all-vendors.md](../practices/update-all-vendors.md) | universal, shown to code owners like the single phrase |

**The run, per repository:** attach (push), clone into the scratchpad,
link the shared sets it declares, run
[precedent_update.py](../tools/precedent_update.py), and on DONE commit with
the person's identity on a branch
[precedent_branch_name.py](../tools/precedent_branch_name.py) names, and push. The session opens and merges each pull request. A
repository that ends ASK, LEFT or FAILED keeps its clone and goes to a
subagent with a fresh context, so its instructions load only there.

**What it costs instead:** one session; about a page of attach output per
repository (measured 2026-10-11: the attach result is long, and that is the
largest per-repository cost now); one line of tool output per repository;
and a subagent only where a judgment call is needed.

## Options weighed

- **One session per repository, started by a tool.** Every repository's own
  hooks run, which is the most faithful. Turned down as the route: twenty
  sessions' start-up, twenty to archive, and twenty merges for auto mode to
  refuse. Kept as the fallback for one repository that needs it.
- **Discovery by code search across the account.** One call instead of a
  probe per repository, but this environment allows a search with no
  repository argument only inside the session's scope, so it cannot see an
  unattached private repository. The list makes discovery rare instead: a
  repository is probed once and remembered either way.
- **Remove each repository after use.** Not possible, and not needed.

## The auto-mode merge

Claude Code's auto mode clears a merge only on the person's own words that
name it
([gotcha](../gotchas/gotcha-2026-10-04-auto-mode-refuses-update-vendors-own-merge.md)).
Both phrases are now best said with the merge in them: "Update Vendors and
merge", "Update All Vendors and merge them". That follows from the check's
own stated rule; as of 2026-10-11 nobody has seen it work, so the in-session
handling of a refusal is unchanged.

## Found by the first run

The tool's first dry run, on one consumer, failed in a way every consumer
would have: BestPractice deleted a practice on 2026-10-11 and recorded it in
`process/decommissioned_paths.json`, and the consumer's view sync refused the
removal, offering only `--allow-removals`, a call made by hand repo by repo.
Fixed at the cause: the update now reads that record at the commit it takes and
names those practices to the sync (`--allow-removal SLUG`), and nothing else is
let through. The first run also showed that a clone outside the session's root
cannot see the shared sets a repository declares beside it; the tool links them
in from beside the BestPractice clone.

## Not in this plan

- Merging from the tool. Merges need GitHub's API, which the session has and
  a script run inside it does not.
- A staleness roll-up across the list. The list now exists to read it from:
  item 3 of
  [todo-2026-09-21-nothing-checks-a-consumer-against-upstream](../todo/todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md).

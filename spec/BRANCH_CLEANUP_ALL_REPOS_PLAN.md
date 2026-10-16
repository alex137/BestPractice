---
title:         One button for every repository on the branch cleanup page
kind:          proposal
status:        executed
opened:        2026-10-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Built: one button on the branch cleanup page that starts the cleanup workflow in every public repository at once, through the person's own GitHub connector, and any cleanup click checks off that repository's rows. Considered and set aside: one workflow that cleans every repository, private ones included, from a single run, which needs a stored write key."
---

# One button for every repository on the branch cleanup page

**Status: the public-only button is built, 2026-10-16; the all-repository
workflow is set aside.** Morgan raised it the same day the per-repository
buttons landed ([BRANCH_CLEANUP_BUTTON_PLAN.md](BRANCH_CLEANUP_BUTTON_PLAN.md)),
asked two questions about it, and then decided: *"let's forget the plan for
now, and record it in a spec/ as an idea we considered. However, let's do
this ... add a button to the branch doc that, with one click, runs the
deletion for all public repos"* (strength: decided).

## The idea: one run for every repository

**The cost it goes after.** GitHub bills each job for at least a whole
minute ([BILLING_FLOOR.md](BILLING_FLOOR.md)), so ten private repositories
cleaned one button at a time cost about ten minutes, though deleting a
branch takes a fraction of a second. One workflow walking every repository
on the page would pay the floor once: about one or two minutes in all.
Morgan: *"If there are 10 different repos listed instead of 10 different
minutes being counted ... it takes a minute or two."*

**It works, with one real cost: a stored key.** A workflow's own token
reaches only its own repository, so a run that deletes branches elsewhere
needs a credential kept as a secret beside it, with write access to every
repository it cleans. There is no GitHub permission that allows deleting
branches but not pushing code. Three shapes were looked at:

- **A fine-grained token per account.** It covers only repositories owned
  by the account that makes it, so the person's repositories and those of
  any other owner they work in each need their own token, made by that
  owner. Each can be limited to chosen repositories.
- **One GitHub App, installed on each account.** One stored key; each
  account's owner picks the repositories it reaches, and every run gets a
  pass that expires within the hour. The pick, had it been built.
- **One classic token.** One key, reaching everything the person can, with
  no way to narrow it. Not recommended.

**Where the key would live.** Not in this repository: GitHub hands a
repository's secrets to any workflow running there, including one added
on a freshly pushed branch, and sessions push here all day and may merge
to `main` on their own. Locking the secret to `main` narrows that, not
closes it. The plan was a small repository of the person's own, where
nothing else is pushed, with the workflow itself shipped by the engine as
a template.

**A public home would make it free.** Minutes are billed to the
repository the workflow runs in, not the ones it cleans, and they are free
in a public one on GitHub's standard runners (as of 2026-10). The catch:
anyone can read a public repository's run logs, so the run would report
counts only, never a private repository's or branch's name.

**Why it is set aside.** The key, and the setup on more than one account.
The public-only button below takes the clicking away where runs already
cost nothing, without either. If the private repositories' cleanup
minutes start to matter, this is the design to pick up.

## What was built

### One button for every public repository

**Above the repository sections, one button starts the cleanup workflow
in every repository on the page that is public and carries it.** The
page's own script calls GitHub's `actions_run_trigger` (`run_workflow`,
`precedent-branch-cleanup.yml`, on `main`) for each one, one after another,
**through the person's own GitHub connector** on claude.ai: the page is
published with the `mcp` capability naming that one tool
(`PAGE_CAPABILITIES` in
[tools/precedent_stale_branches.py](../tools/precedent_stale_branches.py)),
so it holds no credential and never sees one. The first click asks the
person to allow GitHub for the page. A line under the button says how many
started and names any that did not, with the fix for each reason
(reconnect GitHub, add the connector, allow it for the page) and a pointer
to that repository's own button.

- **Public repositories only, and only known ones.** A repository GitHub
  or its `precedent.json` says is public. A private one, or one whose
  visibility is unknown, is left out, because a private run costs
  minutes; its own button still works as before.
- **Still a person's click.** Nothing on load or on a timer calls GitHub;
  only that button does.
  [never-delete-a-remote-branch](../practices/never-delete-a-remote-branch.md)
  says so, and the verify harness asserts that the page's one call sits
  inside that click and that no engine tool starts the workflow.
- **The per-repository buttons and every row stay.** They are unchanged:
  the person still counts and reads the names first.

### Any cleanup click checks off the rows it covers

**Clicking a repository's delete-all button, or the all-public one, checks
off every row of the repositories it covers**, unless already checked,
which crosses them off the same way a hand checkmark does. Morgan:
*"whenever any of these cleanup buttons are clicked ... it should check the
box and cross it off if it doesn't already"* (strength: decided). The
checkmarks are saved into the page as any others are, so the next refresh
leaves those branches off a repository it cannot check.

### Holes, and how they are answered

- **A run that never started still checks its rows off.** As asked, the
  checkmark follows the click. *Answered:* the result line names any
  repository the button could not start, and a session that can check that
  repository lists its branches fresh at the next refresh.
- **The page saves itself by republishing, which reloads it.** A save in
  the middle of the runs would cut them off. *Answered:* the page holds
  its save until every run has been asked for, then waits 30 seconds, or
  until the page is left, so the result line can be read.
- **The connector's name on claude.ai is not measured.** The page names
  it `github`, from the session's own tool names. *Answered:* the first
  publish with the new capabilities is the check; a wrong name is refused
  there, before anyone clicks.
- **A branch that is an open pull request's source** is checked off but
  not deleted, as with the per-repository button. *Accepted:* the refresh
  after lists it again for a repository it can check.

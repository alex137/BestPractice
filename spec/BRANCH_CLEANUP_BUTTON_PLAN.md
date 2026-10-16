---
title:         A "Delete merged branches" button on the branch cleanup page
kind:          proposal
status:        drafted
opened:        2026-10-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "One button per repository on the branch cleanup page that starts a GitHub workflow deleting every branch already in main. Never run automatically. Always shown for a public repository; for a private one, shown only once github_branch_cleanup_every_hours (336 for Morgan) has passed since that repository's last cleanup run. The per-branch list stays exactly as it is."
---

# A "Delete merged branches" button on the branch cleanup page

**Status: a plan, not built.** Morgan shaped it in one conversation on
2026-10-16 and asked for it written up; building it needs his go-ahead
(Act). Every decision below quotes him and carries its strength.

## The problem

At the close of a session, the ladder's
[stale-branch-cleanup](https://github.com/alex137/BestPractice/blob/staging/practices/stale-branch-cleanup.md)
practice publishes one pinned page listing every branch that is already in
`main`, across every repository the person owns. Each row is a link to
GitHub's branch list filtered to that one branch
([branch-delete-links](https://github.com/alex137/BestPractice/blob/staging/practices/branch-delete-links.md)),
where the trash icon deletes it. **A session can't delete a branch itself**:
the environment refuses it, measured 2026-09-14
([never-delete-a-remote-branch](https://github.com/alex137/BestPractice/blob/staging/practices/never-delete-a-remote-branch.md)).

So cleaning up means one tab and one click per branch, and the list is
routinely dozens of branches across several repositories. Morgan:
*"instead of me robotically opening a zillion tabs each time you give
me..."*

## Options considered

**1. Rename every deletable branch to `todelete.<name>`** (Morgan's first
idea), so one filtered link per repository (`?query=todelete`) shows them
all. **Rejected: it can't be done from a session.** Renaming a branch that
is already on GitHub takes the old name off GitHub, which is the same
deletion the environment refuses. The GitHub tools a session has can create
a branch but not rename or delete one. The only thing a session could do is
push a `todelete.` copy beside each original, which doubles the list. Even
if it worked, it would still be one trash click per row, just in one tab.
(This doesn't affect the existing naming rule: a session renames its own
branch before the first push, so GitHub only ever sees one name.)

**2. Turn on GitHub's "Automatically delete head branches" setting.**
Free, but partial. It deletes a pull request's source branch when the PR
merges. Most session branches reach `staging` through the landing tool,
not through a pull request, so only the `to-main-...` copies would go. It
is also the setting first blamed for `staging` vanishing on 2026-09-26
([gotcha](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-09-26-a-pull-request-from-staging-deletes-staging.md));
it turned out to be off then, but turning it on now would need the
tier-branch protections looked at first. Not pursued here.

**3. A GitHub Actions workflow that deletes every branch already in
`main`, started automatically by Promote.** Promote already decides, in
the session, whether main's GitHub test is due (`github_ci_every_hours`).
It could start the cleanup the same way: every Promote for a public
repository, and at most once per window for a private one. **Rejected by
Morgan:** *"on both [private] and public, NEVER run the cleanup
automatically"* (2026-10-16, strength: decided).

**4. The same workflow, started only by a button on the cleanup page.**
**Chosen.** One button per repository, so the number of tabs goes from
one per branch to one per repository, and the per-branch clicks go away.

## The plan

### What Morgan decided (2026-10-16, strength: decided)

- **Never automatic.** *"on both [private] and public, NEVER run the
  cleanup automatically. In both cases, [put] the buttons on the branch
  cleanup page."*
- **Public repositories: the button is always there.** *"for public ones,
  the button is always there"*. Actions minutes are free in public
  repositories on GitHub's standard hosted runners (as of 2026-10).
- **Private repositories: the button shows only when its tracker allows.**
  *"for private ones, the button only appears if the tracker for that says
  it can be shown."* One tracker per repository, separate from the main
  test's (Morgan asked "a separate tracker per repo, right?"; yes).
- **Its own setting, not the main test's.** *"instead of using the same
  variable ... let's define a second variable next to me and let's make
  that variable 336 for now."* He named `github_ci_workflows`; the
  variable he meant is `github_ci_every_hours`, the 168-hour one. The new
  setting is `github_branch_cleanup_every_hours`, set to 336 (two weeks)
  in his individual `identity.json`, next to the hours setting.
- **The per-branch list stays exactly as it is.** *"it should ALSO keep
  the list as it is now, because I want to both see all the branches to
  have a sense of how many there are and eye check their names, and also
  because I may not use the new button because I am careful on github
  minutes."*

### 1. The setting

`github_branch_cleanup_every_hours`: at most how often a private
repository's cleanup button is offered, in hours.

- **Read the way `main_test_cadence()` reads the main test's number**
  ([tools/precedent_branches.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branches.py)):
  the person's `identity.json` first, then the repository's
  `precedent.json`. A new `branch_cleanup_cadence()` sits beside it.
- **When in doubt, show the button.** Unset, 0, not a number, a public
  repository, or one that doesn't declare its visibility: the button
  shows. Showing it costs nothing; only a click spends minutes. That is
  the reverse of the main test, where a doubt *runs* the test, and it
  lands in the same place: nothing is hidden on a guess.
- **`identity.json.template` doesn't ship it**, so everyone else gets the
  always-shown default.

### 2. The workflow

A new engine template,
`templates/github-actions/branch-cleanup.yml.template`, installed as
`.github/workflows/precedent-branch-cleanup.yml`.

- **One trigger: `workflow_dispatch`.** No push, pull request or schedule
  trigger, so the file never runs by itself and costs nothing while it
  sits there. One job.
- **`permissions: contents: write`**, the least that can delete a branch
  with the workflow's own `GITHUB_TOKEN`.
- **It deletes the same branches the page lists, chosen by the same
  code**: the page's selection in
  [tools/precedent_stale_branches.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_stale_branches.py)
  (`stale_in`), called from the vendored engine, with a new
  `--delete-merged` mode that only the workflow uses. The page and the
  button can never disagree about what is deletable.
- **Safety, checked again at run time, branch by branch:**
  - the never-listed names stay hard-coded, whatever the merge test says:
    `main`, `staging`, `pre-staging` while in use, `precedent-beta-v01`,
    the engine's own branches, anything starting `data-`, and the
    repository's default branch as GitHub reports it;
  - the branch's tip must be in `origin/main` at the moment of the run;
  - **a branch that is the source of an open pull request is skipped**,
    because deleting it would close that PR (a new rule; the page marks
    such rows too).
- **The run's summary names every branch it deleted and every one it
  skipped, with why.** That is the record of what went.
- **Shipped by the engine, ladder repositories only.** Update Vendors
  removes any workflow upstream doesn't ship and the person didn't
  approve, so the file must come from the engine's own list
  (`CI_CONVERGES_KINDS` in
  [tools/precedent_vendor_engine.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_vendor_engine.py)).
  It is written only for a person on the ladder, since the page it serves
  is a ladder practice. Morgan's approval for it is recorded per
  [ci-workflow-approved](https://github.com/alex137/BestPractice/blob/staging/practices/ci-workflow-approved.md),
  quoting this conversation.

### 3. The page

The page keeps every row it has today. Each repository's section gains
one line at the top:

- **Public:** a "Delete all N merged branches" link to the workflow's page
  on GitHub (`github.com/<owner>/<repo>/actions/workflows/precedent-branch-cleanup.yml`).
  There Morgan clicks "Run workflow" and confirms: **two clicks on GitHub,
  not one.** The page can't start the run itself without holding a GitHub
  credential, and it must not hold one.
- **Private, due:** the same link.
- **Private, not due:** no link, and the line says when it comes back:
  *"Delete-all button back on 30 October"*.
- **Workflow not installed yet:** the line says so and that Update Vendors
  installs it.

**The tracker, per repository: that repository's own last successful
cleanup run on GitHub.** At build time the tool asks GitHub, through
[`github_budget.py`](https://github.com/alex137/BestPractice/blob/staging/tools/github_budget.py), for the newest run of `precedent-branch-cleanup.yml`
in each repository it can see. A run that succeeded, or is queued or
running, counts; a failed one doesn't. Never run means due. It is a
different record from the main test's, so running one never resets the
other.

**The page also records a click itself.** Clicking a private repository's
button writes the date into the page (the same way ticks are saved since
2026-10-13) and hides that button at once. The page's own script compares
the "back on" date with today when it is opened, so a hidden button comes
back on its date without a rebuild.

**Which is believed:** for a repository the building session can see,
GitHub's run history replaces whatever the page recorded. For one it
can't see, the page keeps its saved click date, as it already keeps that
repository's rows. **Visibility** comes from GitHub's own `private` flag
where the session can read it, and from `precedent.json`'s `visibility`
otherwise, so a private repository wrongly declared public doesn't get an
always-on button.

### 4. The rules

- **[never-delete-a-remote-branch](https://github.com/alex137/BestPractice/blob/staging/practices/never-delete-a-remote-branch.md)
  (universal) gains one exception:** the engine's
  `precedent-branch-cleanup.yml`, started by a person, may delete branches
  already in `main`. **A session still never deletes a branch by any
  route, and never starts this workflow.** The engine has no code that
  dispatches it, and the verify harness asserts that.
- **[branch-delete-links](https://github.com/alex137/BestPractice/blob/staging/practices/branch-delete-links.md)
  (universal):** unchanged for rows. It gains a note that the page's
  per-repository button is an addition, never a replacement for the
  per-branch links.
- **stale-branch-cleanup (precedent-shared-ladder):** describes the
  button line, the per-repository tracker and the setting.
- **Morgan's individual `identity.json`:** `github_branch_cleanup_every_hours: 336`,
  with a comment saying what reads it. Added on 2026-10-16, before the
  build, at his request; nothing reads it until this plan is built.

### 5. Tests

In [tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py):
the setting's resolution and its doubt cases; the button line for public,
private due, private not due, never run, failed last run, and not
installed; the click record surviving a `--merge`; GitHub's history
replacing a click for a visible repository; the workflow template having
no trigger but `workflow_dispatch`; no engine code dispatching it; and
`--delete-merged` refusing every never-listed name and every open-PR head.

## Holes found, and how the plan answers them

- **The button can delete branches that weren't on the page.** It works
  out what is deletable when it runs, so a branch that reached `main`
  after the page was built goes too. *Accepted:* it loses nothing, since
  everything it deletes is already in `main`, and the run's summary names
  every branch. The per-branch list is still there for checking names
  first.
- **A long-lived branch reads as merged** right after it is
  fast-forwarded. *Answered* by the hard-coded never-list, checked at run
  time, plus GitHub's own default branch. A repository ruleset that
  protects `main` and `staging` from deletion (the 2026-09-26 gotcha's
  retirement condition) would block the workflow there too.
- **A branch with an open pull request** would have that PR closed by the
  deletion. *Answered:* skipped, and marked on the page.
- **The workflow may not be able to delete branches at all.** A
  repository or organization setting can hold `GITHUB_TOKEN` to read-only,
  and a ruleset can forbid deletions. Nobody has measured this here.
  *Answered:* the first real click is the measurement. If it fails, it
  becomes a gotcha with the measured cause, and the per-branch list works
  as it does today.
- **Two clicks, or two windows,** start two runs. The second finds
  nothing and costs about a minute in a private repository. *Accepted.*
- **The page's tracker can be out of date** for a repository the building
  session can't see. Used from the page's own button, the click record
  keeps it right. It is off only when the cleanup was started straight on
  GitHub (the button shows early; a click then runs again for about a
  minute) or when a click's run failed (the button stays hidden until a
  session that can see the repository rebuilds the page). *Accepted:*
  neither loses anything.
- **A session might be tempted to start the workflow** to save Morgan the
  click. *Answered* by the rule's new wording and the harness check that
  no engine code dispatches it.
- **Free in public repositories is a fact about GitHub's pricing**, which
  changes. It is dated here (2026-10) and the "always shown" rule rests
  on Morgan's decision, not on the price.

## What this costs

- **Minutes:** about one billed minute per click in a private repository,
  since GitHub rounds every job up to a whole minute
  ([BILLING_FLOOR.md](BILLING_FLOOR.md)), and nothing in a public one.
  With 336 hours, about two clicks a month at most per private repository.
- **One new workflow file** in each ladder repository, shipped and owned
  by the engine.
- **A looser never-delete rule**, limited to that one workflow, started
  by a person.

## Rollout

The template, the page, the setting's reader, the tests and the two
universal rule changes land in BestPractice and reach every consuming
repository through Update Vendors
([vendor-update-runbook](https://github.com/alex137/BestPractice/blob/staging/practices/vendor-update-runbook.md)).
The stale-branch-cleanup change lands in precedent-shared-ladder. The
setting is already in Morgan's individual `identity.json`. A repository
gets the button once Update Vendors has installed the workflow; until
then its line on the page says so.

## Acronyms

- **PR:** pull request.

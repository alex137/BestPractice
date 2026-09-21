---
slug:        branch-delete-links
title:       A merged branch is reported as a one-click delete link, never a name
tier:        on-demand
severity:    default
scope:       any-adopter
applies_to:  ["tools/very_deep_check.py", "record/stale_branches.md", "spec/VERY_DEEP_CHECK.md"]
occasion:    "reporting merged-but-undeleted branches to a person, in one repo or across a fleet"
gates:       []
index_clause: "a merged branch is a filtered branches-page link; unmerged goes in its own list"
index_required: false
checked_by:  null
defines:     ["delete link", "filtered branches page"]
command:     null
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-21"
approved_by: "Morgan, 2026-09-21 -- he asked for the filtered-link form over the
  plain list a first pass had given him, and chose the two surfaces it lands on
  (strength: decided, relayed; the decision to hold the mechanism in one
  practice file rather than write it into both surfaces is the session's, per
  fix-the-original)."
---
## Rule
**A merged-but-undeleted branch is reported as a link that opens GitHub's
branches page already filtered to that one branch** — the row's trash icon is
then on screen and deleting it is one click, with no searching. Never a bare
branch name, and never a link to the branch's tree view, which shows the code
and offers no way to delete it.

    github.com/<owner>/<repo>/branches/all?query=<branch, percent-encoded>

(Written without its `https://` prefix on purpose: a practice file ships
verbatim into every adopting repository, and a complete URL naming a
placeholder owner is still a link a reader can click into nothing.)

`/branches/all` is the **All branches** tab and `?query=` is its filter box.
**The branch name must be percent-encoded.** Branch names routinely contain
`/`, which has to become `%2F` or the filter breaks. In Python that is
`urllib.parse.quote(branch, safe='')` — `safe=''` is the load-bearing part,
since the default leaves `/` alone. Filled in against this repository, a
branch called `claude/tidy-up-abc` becomes
[that one row, with its trash icon](https://github.com/alex137/BestPractice/branches/all?query=claude%2Ftidy-up-abc).

Three things the report must not get wrong, each of which fails silently:

1. **A branch with no merged pull request is not a deletion candidate**, and
   belongs in a separate list under its own heading. Never mixed in.
2. **A branch whose name is a substring of another branch's name in the same
   repo gets flagged, not linked** — the filter would show more than one row
   and the one-click promise is gone.
3. **Say what success looks like.** After the deletion the filtered page reads
   *"no branches matched"*, which looks like an error and is not.

## Detail
### Deciding which branches qualify

Offline, in a clone, the mechanical test is `git merge-base --is-ancestor` and
nothing else is needed — every commit on the branch is already on a protected
branch, so the branch carries nothing. That is what
[tools/very_deep_check.py](../tools/very_deep_check.py) does for the checkout
it runs in.

Over the GitHub API, with no clone, the test is four steps and step 2 is the
one that gets skipped:

1. List all branches; drop the repository's default branch and any protected
   integration branch.
2. List **closed** pull requests and keep only those whose `merged_at` is
   non-null. **A closed-unmerged pull request is not a merge.** Closing a pull
   request and deleting its branch destroys the work on it.
3. Intersect on `head.ref`. Where one branch has several merged pull requests,
   report the highest number and its merge date.
4. **Paginate the pull-request list.** A repository with more pull requests
   than one page holds will otherwise under-report, and it under-reports
   *silently* — the call succeeds and the answer is simply short.

### Why the unmerged list is separated rather than annotated

A reader working a long list works it by pattern, not by reading each row's
qualifier. Putting a "this one is not actually merged" note on a row inside a
list of safe deletions is an invitation to click through it, and the cost is
asymmetric: deleting a merged branch loses nothing, and deleting an unmerged
one loses whatever was on it. **Separate headings, separate lists**, and the
unmerged list gets a verdict per row rather than a link
([very-deep-check](very-deep-check.md)'s pass 4 says what a verdict is).

### The substring check

Before emitting a link, compare the branch name against every other branch
name in that repository. If any other name **contains** this one, the filter
resolves to more than one row: flag the branch and say how many rows its
filter will show, rather than promising one click and delivering a search.

The check is cheap — one pass over a list already in hand — and the failure
mode is that the person clicks, sees several rows, and has to work out which
is theirs. That is exactly the friction the link was built to remove.

### Presentation

- **Group by repository, one heading each**, so the person works one browser
  tab at a time.
- **Order the repositories smallest count first.** Clearing a one-branch
  repository and a three-branch repository early makes a long list feel
  finishable; leading with the worst offender makes it feel like homework.
- **Lead with the total**, so the size of the chore is known before the
  scrolling starts.
- **Never truncate the list.** A branch omitted for length is a branch nobody
  deletes, and the whole point is that the list is worked once and shrinks.

### Recovery

GitHub offers a brief **Undo** immediately after a branch deletion, and a
deleted branch's commits stay reachable by SHA until they are garbage
collected. Say the first of those where the list is handed over — a person
who knows a misclick is recoverable works a long list faster than one who
does not.

## Why
**A name is not an affordance.** A list of thirty branch names is a list of
thirty searches: open the repository, open the branches page, type the name,
squint, click. Nobody does that thirty times, so the list is read once and
acted on never — which is how a repository ends up with branches merged
months ago still sitting on its branch page.

**The encoding rule is the detail that gets lost.** It is one argument in one
call, it is invisible when every branch name in front of you is flat, and it
breaks the moment somebody's branch is named `claude/something`. That is
precisely the kind of detail that gets "improved" in one copy of a rule and
not the other, which is why the mechanism lives in this one file and both
surfaces that use it cite it rather than restate it
([fix-the-original](fix-the-original.md)).

**The unmerged list is the part that can do real damage.** Everything else
here costs a person some clicking. Presenting a branch with unlanded commits
as safe to delete costs them the commits.

## Story
**2026-09-21.** A session was asked to audit every repository Morgan owns
carrying a Precedent install. Among its findings were **110 merged-but-undeleted
branches across 9 repositories, the oldest merged on 2026-08-16.**

The first pass reported them the obvious way: branch name, pull-request number,
merge date, grouped by repository. A correct list, and an unusable one — every
row was a search the reader would have to run by hand. Morgan asked for
something better, and what he asked for is the rule above: each branch rendered
as a link that opens the branches page already filtered to it, so the trash
icon is on screen and the deletion is one click.

**The same audit found the failure the separated list exists to prevent.** Of
the branches swept, **37 had no merged pull request at all**. In the one
repository where merge state was checked against a real clone rather than
inferred from the API, **4 of those 5 branches carried unmerged commits** —
work that a list presenting them as deletion candidates would have thrown away.
They were not close calls that a careful reader would have caught; they looked
exactly like the safe rows, because a branch's name says nothing about whether
anything landed.

**The substring check has never caught anything.** Across all 110 branches in
that audit there were zero collisions. It is in the rule anyway because it
costs one pass over a list already in memory, and because its failure is
silent: a filter that returns three rows still returns a page, and the reader
finds out by clicking.

**The mechanism was already written once, in code, and nowhere in prose.**
[tools/very_deep_check.py](../tools/very_deep_check.py)'s `_branch_url` had
carried the filtered-page form and the `safe=''` encoding since 2026-09-08,
with Morgan's original ask in its docstring — *"make a list of them in the
session including direct links to them so I can delete them"*. Nothing pointed
at it from the practice catalogue, so the fleet-wide audit rediscovered the
same URL from scratch thirteen days later. That rediscovery is what this file
is for.

## Install
Two surfaces carry this, and both cite it rather than restating it:

- [chief-of-staff](chief-of-staff.md) sweeps the fleet — every repository the
  person owns carrying a Precedent install.
- [very-deep-check](very-deep-check.md)'s pass 4 sweeps the checkout it is
  running in and the sources that are their own git checkouts, and no further.
  Branch hygiene is per-repository bookkeeping, not a seam finding between two
  repositories, so widening the deep check to the fleet would duplicate what
  the Chief of Staff owns and make an already expensive check more expensive
  for no new judgment.

The engine side is [tools/very_deep_check.py](../tools/very_deep_check.py):
`_branch_url` builds the link, `_delete_row_lines` renders one row, and
`_write_branch_report` writes the committed page. A fleet sweep has no clone to
read and works the API steps above instead.

**Related:** [fix-the-original](fix-the-original.md) — why the mechanism is one
file and not two;
[repo-is-memory](repo-is-memory.md) — why the per-repo sweep writes a committed
page rather than only printing.

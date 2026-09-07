---
slug:        very-deep-check
title:       The very deep check — a whole-repo coherence review, on request only
tier:        on-demand
severity:    advisory
applies_to:  ["**"]
occasion:    "a person explicitly asks for a \"very deep check\" across the whole repo, or after work that invites drift"
gates:       []
index_clause: "read every repo in force against itself, pass by pass; never a routine gate"
checked_by:  null
defines:     ["very deep check"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review; revised 2026-09-05, Morgan F, to require every
  declared team/individual source actually be in the session before the check
  runs, and to add a stale-branch sweep across every repo the check touches;
  revised again same day, Morgan F, to add a cross-source-staleness check;
  restructured 2026-09-06, Morgan F, into four ordered passes — adopter
  installs first, then whether the mechanisms tell the truth, then the
  coherence read, then catalogue and housekeeping — with the run made
  resumable across sessions; extended same day, Morgan F, with a
  duplicate-implementation question in pass 2 and an explicit
  mechanical-before-human order of operations; that order's first step made
  mechanical 2026-09-07, Morgan F — every repo in force must be provably
  current before the check reads anything; extended same day, Morgan F, so
  the branch sweep reports an unmerged branch with a merge-or-close verdict,
  not only a merged one awaiting deletion; extended 2026-09-07, Morgan F,
  so each unmerged branch is written up with what it changes, a link, its
  date and a reasoned recommendation, rather than handed back as a name;
  split same day, Morgan F, so the unmerged-branch INVENTORY is read
  before any pass and only the verdicts stay in pass 4"
---
## Rule
When a person explicitly asks for a "very deep check", or after work that
invites drift (a batch of practices added or reordered, a practice that
changed shape, an install into a new repo, a merge that resolved conflicts
across several shared files), run
[tools/very_deep_check.py](../tools/very_deep_check.py) and work the four
passes in Detail, in that order. The tool enumerates the scope — this
checkout's own top-level documents, plus the `practices/*.md` tree of every
source in force, resolved exactly the way
[tools/precedent_resolve.py](../tools/precedent_resolve.py) resolves them for
ordinary loading — and prints the passes; reading and judging that scope is
the session's work, and is nearly the whole cost of this check. Never wired
into a commit, push, or merge gate — the mechanical audits and
[routing-audit](routing-audit.md) already cover what can be checked cheaply
and often; this covers what can only be judged, and is deliberately rare
because the judging is expensive.

**Scope is every Precedent repo in the session, not this checkout alone** —
this repo, each attached team and individual source, and any consuming repo
the engine is vendored into. A finding is as likely to be in the seam
between two of them as inside any one, which is the reason they are read
together rather than one at a time.

**Before anything is read, every repo in force must be provably current
against its origin** — this checkout and every attached source.
[tools/very_deep_check.py](../tools/very_deep_check.py) fetches and compares
each one as its first act and refuses to go further otherwise, because a
very deep check's whole product is judgment about what the repos say: a stale tree does not degrade
that judgment, it inverts it — work that landed last week reads as missing,
and bugs fixed days ago read as open. "Stale" and "cannot prove it isn't"
get the same verdict, since a confident wrong answer is the failure mode
either way. Fix it and start again; `--freshen` will fast-forward a clean
tree that is merely behind, and `--allow-stale` exists only for a
deliberately offline run, where every finding is then provisional.

**Every declared team and individual source must actually be present before
the check runs.** The ordinary loader tolerates a missing personal source and
says so on stderr — the right call for routine loading, where one operator's
absent individual set is expected. It is the wrong call here: a very deep
check is explicitly asked for and scoped to the whole set of repos in force,
so a silently dropped source defeats the reason it was asked.
[tools/very_deep_check.py](../tools/very_deep_check.py) fails loudly rather
than degrading. On that
failure, attach or clone the missing source (this harness's own
repo-attachment mechanism, or a plain `git clone`) and re-run — never re-run
with `--allow-missing-sources` to make the failure go away; that flag is for
the rare case where proceeding without the source is the actual intent (a
repo that deliberately has no team set yet).

**The passes are ordered by what a miss costs, and that order governs fixing
too.** A from-scratch install or a migration that strands an adopter is a
roadblock; a heading capitalized two ways is not. Never let a pass-3 finding
queue ahead of a pass-1 one because it is easier to fix, and never report a
run as done with a pass-1 roadblock still open.

**This is more than one session's work, and is meant to be split.** Keep the
run's state in [spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md): which
passes are done, what each turned up, what was fixed, what was deferred and
where it went. A later session resumes at the next unfinished pass rather
than starting over, and a pass is never quietly skipped — a pass deliberately
not run is recorded as not run, with the reason.

Fix what a pass turns up in the same pass — most findings are small — then
re-run the mechanical audits, since the fixes themselves break links.
Anything deliberately left alone gets a line in [TODO.md](../TODO.md) saying
so, rather than being silently dropped.

## Detail
**This is not `full-practice-audit` under another name — the two ask
different questions.** [full-practice-audit](full-practice-audit.md) asks,
practice by practice, "is this specific practice's Rule satisfied?" — a
closed question against one Rule at a time. The very deep check asks
questions no single practice's Rule can be checked against: does an adopter
who has only this repo actually get working? Do the mechanisms report what
they claim to? Does the repo's own writing still hold together? Each is a
property of the system *as a set*, which is exactly what a per-practice
sweep cannot see no matter how many times it runs.

Four passes, in order. Within each, the bullets are a starting point, not a
specification: report anything that makes the system harder to trust,
install, or follow, whether or not a bullet below names it. If a finding
recurs and nothing here names it, add a bullet so the next run looks for it
deliberately.

**Order of operations — mechanical before human, every time.** Judgment
spent on something a script already catches is judgment wasted, and a tree
already failing its own gates makes every later finding ambiguous: you
cannot tell a drift this run introduced from one that was there before. So:

1. **Prove every repo in force is current.** The tool's own first act, and
   a refusal rather than a warning — warning was tried and failed, because a
   session stale enough to need the warning has already been handed stale
   instructions to read it against. A source is the likelier offender: the
   session-start freshness guard runs for the session's primary repo only,
   so an attached sibling has never been checked by anything.
2. **Run the deep check suite as it stands** — the five gates
   [AGENTS.md](../AGENTS.md) names ([two-check-levels](two-check-levels.md))
   — and fix what it reports, before this check reads a line. `0 failed` and
   `0 violated` is the starting line, not the finish.
3. **Run [tools/very_deep_check.py](../tools/very_deep_check.py)** for the
   enumeration, the machine-readable parse, the source-shape check, and the
   branch scan. A missing declared source stops the run here.
4. **Read the unmerged-branch inventory, before any pass begins.** Not the
   verdicts — those are pass 4's expensive half and stay there. Just the
   list, and enough of each branch's diff to know *what already exists
   somewhere*. This is the cheapest step in the whole check and the only
   one that prevents work rather than finding it: a fix written last week
   and never landed is invisible to every other step here, so a session
   that skips this rediscovers it from scratch, writes it up as a finding,
   and files it as open — three costs, all avoidable by reading one list
   first.
5. **Then the passes, 1 through 4**, each ending with the suite from step 2
   re-run — the fixes a pass makes break links of their own. Whenever a
   pass turns up a gap, check it against step 4's inventory **before**
   writing it up: if a branch already fixes it, the finding is "this is
   written and unlanded", which is a different problem with a different
   remedy.

The same rule holds inside a pass: where a mechanical check covers part of a
bullet, run it first and read only what it cannot see.

### Pass 1 — Can a new adopter get to a working install?
The highest-cost failures are here, because they strand someone outside this
session who cannot see what is wrong. Reading the install documents finds
almost none of them: every significant finding of the 2026-09-06 pre-launch
audit came from **building the thing the document describes and running the
checks on it** ([spec/PRELAUNCH_AUDIT.md](../spec/PRELAUNCH_AUDIT.md), "The
method"). Build the fixtures.

- **A real from-scratch install.** A scratch repository with nothing in it,
  installed per [INSTALL.md](../INSTALL.md) §0 against `precedent-beta-v01`
  alone — no team set, no individual set, none of the sibling clones this
  session happens to have — following the documents exactly as written,
  without leaning on what this session already knows. Then run the deep
  check on the result. Anything the session had to work out that the
  documents did not say is a finding; so is any check that cannot come back
  clean on a correct fresh install.
- **A real migration**, the same way: a scratch repo on the classic
  `process/upstream/` layout, walked end to end through
  [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md).
- **The empty neighbourhood.** A brand-new person with no individual set; a
  team with no team set yet; a consumer whose sources are declared but
  unreachable, as they are in every continuous integration (CI) checkout.
  Each degradation path should degrade with a named reason — never pass
  silently on a scan that never ran, and never fail on something the adopter
  cannot fix.
- **Cross-repo relationships and permissions.** Walk who must be able to read
  or write what, for a *new* repo and a *new* person: the vendored engine,
  each declared source, approvers and CODEOWNERS, and the restricted GitHub
  roles [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](../spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
  describes. A step that works only because this session's operator already
  has access is a finding.
- **Not the practice simulation.** This pass installs real fixtures and runs
  the ordinary checks on them. It does not run
  [tools/precedent_simulate.py](../tools/precedent_simulate.py) or its
  siblings, which are deliberately never reachable from an occasion, gate, or
  hook ([spec/SIMULATION_BRIEF.md](../spec/SIMULATION_BRIEF.md), "Never
  automatic") — this practice is not standing to run them either.

### Pass 2 — Do the mechanisms report what they claim to?
Every mechanical check, gate, and tool, one at a time. Every question below
found a real defect here — all but one in the 2026-09-06 pre-launch audit,
and the duplicate-implementation question in this practice's own machinery —
and none of them is visible from a check's own output: a broken check reports
confidently.

1. **Does it scan only what this repo can act on?** Bucket every finding:
   *this repo wrote it* versus *this repo received it* (a vendored upstream
   tree, a materialized `practices/` directory, a file whose header says do
   not hand-edit, anybody's published history). A non-empty second bucket
   means the scope is wrong, not the content — and a check that produces
   permanently unactionable findings is one people learn to ignore, which
   costs more than the rule it protects. *(Found: 81 findings from one
   check, 12 from another, all inside vendored or materialized trees.)*
2. **Can it ever go green here?** Separately from scope: is there any state
   of this repository in which this check passes? Ask it of every gate a
   document calls mandatory. *(Found: a scrub gate at 116 failures no edit
   in the repo could clear, because the terms arrived from upstream — with
   its own instructions saying it must pass before any commit.)*
3. **Does anything named `--check`, `--dry-run`, or `--verify` write?**
   Snapshot the tree, run it, diff. Then run it again with a dependency
   deliberately unavailable and diff again. *(Found: `--check` rewrote three
   files on a clean tree, and deleted 57 tracked files when one source was
   unreachable, while printing a check verdict — after weeks in the
   documented session-start sequence.)*
4. **Does a tool's output depend on the state of its own output directory?**
   For anything that deletes and rewrites a directory: does it read that
   directory while deciding what to write? Run it twice and diff; then
   delete the output directory, run once, and compare. *(Found: link
   rewriting asked the filesystem about a file the same run was about to
   write, so a practice's citation of its own check script became an
   absolute URL into a private repo.)*
5. **Would a generated name disclose what the architecture hides?** Wherever
   a tool mints a URL, path, or name, ask what it reveals and to whom — then
   check whether the consuming repo is public. *(Found: exactly the private-
   repo URL above, minted into a tracked tree in a public repo, for a source
   the resolver refuses to let a shared config even name.)*
6. **Is a file the format it claims?** Parse with a real third-party parser,
   never the repo's own reader, which is more permissive than the standard
   and so never notices.
   [tools/very_deep_check.py](../tools/very_deep_check.py) now does this for
   every tracked JSON and YAML file; what stays a judgment call is every other
   declared format — a schema, a fenced block, a manifest — that no parser
   here covers. *(Found: 10 practice files and 4 decision records PyYAML
   rejects; the in-house reader took everything after the first colon and
   was happy.)*
7. **Do string matches respect name boundaries?** Every blocklist, denylist,
   and retired-term list: test each term against a plausible compound.
   *(Found: retired term `pack_sync` matching `voice_pack_sync.py`, a live
   tool — nothing could satisfy the finding but renaming a real file.)*
8. **Are there two of anything that should be one?** Two scripts doing the
   same job, two implementations of one rule, a helper copied instead of
   imported, a constant list maintained in two files, a check and a gate
   testing the same property. Copies do not stay identical: one gets fixed
   and the other goes on being wrong, and the stale one is as likely as not
   to be the one actually running. Search by what code *does*, not by what
   it is called ([search-by-purpose](search-by-purpose.md) is the same
   search) — a duplicate that shared a name would have been noticed
   already. For each, name which copy is canonical and delete or re-point
   the other. Vendoring is the deliberate exception: the engine is copied
   into consuming repos on purpose, so the question there is whether every
   copy came from
   [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
   with a recorded commit, never whether a copy exists. *(Found: this
   practice's own checklist, living both in the Detail section below and as
   a `CHECKLIST` string literal inside
   [tools/very_deep_check.py](../tools/very_deep_check.py), with nothing
   keeping the two in step — the tool printed the copy, so a session would
   have worked the stale list without ever seeing the current one.)*
9. **Does anything use alphabetical order to pick a winner?** Often the
   previous question's duplicate, one layer on: where two candidates could
   satisfy a lookup — two directories, two copies of a file, two sources for
   a slug — find what breaks the tie. If it is `sorted()`, it
   is an accident that will pick differently the next time a name changes.
   *(Found twice: a check script present in both its source and its
   materialized location, needing different `ROOT` depths, with the wrong one
   winning every time — two checks confidently reporting that files in plain
   view did not exist.)*
10. **Does a rule forbid the only mechanism the project ships for it?** For
    each rule, ask how a correctly-installed repo satisfies it, then check
    that the sanctioned tool actually produces that state. *(Found: a rule
    against duplicated engine code, in a project whose own vendoring tool
    makes exactly those copies — every correct install permanently in
    violation.)*
11. **Read each enforced practice's check against its own Rule.** The full
    practice audit prints an enforced practice as a single line, on the
    reasoning that its check either fired or it did not — and questions 1-9
    are precisely the ways that reasoning fails. This is the only pass that
    ever looks at those checks, so look: does the check test what the Rule
    says, all of what it says, and nothing the Rule does not ask for?
12. **Is each "known exception" still true?** Reproduce every documented
    gotcha, known-issue note, and "this currently fails because" claim. These
    are written once and re-tested never, and a stale one is worse than none:
    it teaches the next session to skip a check that now works. *(Found: a
    gotcha describing a `ROOT` bug fixed weeks earlier, still telling
    sessions to work around it.)*
13. **What does a session inherit that a person configured by hand?** List
    every `git config`, environment variable, user-level config file, and
    sibling clone this session or a recent one set up or relied on. Each is
    something the next session will not have; anything load-bearing belongs
    in a hook or a checked-in file. *(Found: commit identity unset in four
    clones, so commits landed under the wrong author and tripped the repo's
    own check.)*

### Pass 3 — Does the writing still hold together?
The coherence read, across every repo in scope. Run the mechanical audits
first so this pass spends its attention on what they cannot see.

- **Contradictions** — two rules, or two documents, that can't both be
  followed; a rule whose own carve-outs have eaten it.
- **Broken and misdirected references** — run
  [tools/doc_lint.py](../tools/doc_lint.py)'s broken-relative-link check
  across the whole tree first, then read for what it cannot see: a link that
  resolves but points at the wrong thing, a click-path into a user interface
  that has changed, a cross-repo reference into a repo the reader cannot
  open, a slug or filename that moved.
- **Stale references** — a slug, practice number, filename, heading, or
  click-path pointing at something moved or gone; a positional number cited
  as if it were a name; numbering that skips, repeats, or runs out of order;
  an orphaned name a rename elsewhere left behind in this repo's own prose.
- **Keywords with no entry** — every word or phrase that makes a session
  *act* ("Go merge", "very deep check", "full practice audit", "light check",
  "deep check") is owned by a practice's `defines:` field, so it lands in
  [GLOSSARY.md](../GLOSSARY.md) and a session meeting the word cold can find
  out what it commands. A trigger word reachable only by already knowing it
  is not a keyword, it is folklore.
- **Fragments** — a sentence, note, or heading left behind by an earlier
  edit: a "temporary" caveat whose occasion has passed, a note about a
  reorganization that already happened.
- **Needless repetition** — the same rule stated in full in several places,
  where one statement plus pointers would do.
- **Disproportion** — paragraphs of detail on a minor point, prose that
  emphasizes an aside more than the point it supports, a rule grouped where
  it no longer fits.
- **Rules that no longer make sense** — mechanical or written: a rule nobody
  can state the purpose of, a check that fires on correct work, a convention
  a later mechanism has overtaken. Deleting one is a finding as legitimate as
  fixing one.
- **Cost that isn't earned** — a rule or script that costs a disproportionate
  amount of tokens, time, or friction each time it applies, especially one
  re-researched from scratch on every occurrence instead of following a
  written-down answer; a step in a routine gate that has never produced a
  finding; a tool whose output nobody reads. Name what to delete, not only
  what is expensive.
- **Formatting and spacing drift** — inconsistent heading levels and
  capitalization, a bullet missing the blank line its neighbors have, mixed
  list markers, a ragged table, stray blank lines or trailing whitespace, a
  stale "last updated" header.
- **Self-application** — a rule this repo asks of every project it's
  installed into that this repo doesn't yet follow itself.
- **Cross-source staleness** — a check, tool, or convention this repo changed
  that an attached team or individual source's own tooling, vendored engine
  copy, or written practice still assumes the old form of. Update the source
  in the same pass (per [cross-source-rollout](cross-source-rollout.md)) if
  it's attached; if a `blocked-on` TODO for it already exists, confirm it's
  still accurate rather than adding a second one.
- **Anything else the read turns up** — if something is wrong and none of the
  categories above name it, it is still a finding.

### Pass 4 — Catalogue, backlog, and branches
Last because none of it strands an adopter, and none of it is cheap.

- **The full catalogue, every practice.** Run
  [tools/full_practice_audit.py](../tools/full_practice_audit.py) across every
  source in force. That tool deliberately prints enforced practices as one
  line each; pass 2's *read each enforced practice's check against its own
  Rule* is where those get their real read, so the two
  together are what "every single practice was looked at" actually means.
- **Backlog drift.** Read [TODO.md](../TODO.md) (and each source's equivalent)
  end to end: entries already done, no longer relevant, or never actually
  decided. Treat an entry that is really just an unfixed bug as work, not as
  backlog — [todo-is-a-handoff](todo-is-a-handoff.md) queues only what is
  blocked or out of scope, so anything else there is either doable now or
  should be closed.
- **Branches, both directions, one verdict each.** The *inventory* was
  already read at step 4 of the order of operations, for a different
  reason — to stop this run rediscovering work that exists. What is left
  here is the expensive half: a verdict on each.
  [tools/very_deep_check.py](../tools/very_deep_check.py) reports, for this
  checkout and for every source that is its own git checkout (a repo-local
  source inside the parent checkout shares its parent's branches and isn't
  swept separately), two lists per repo. Neither may be left without a
  verdict.

  *Merged and not deleted* — every branch fully merged into that repo's
  integration branch and still sitting there: a mechanical, offline fact
  (`git merge-base --is-ancestor`), true whether or not GitHub's own
  "merged" flag is set, which it is not for a repo that lands pull requests
  (PRs) by direct push rather than the merge button. Apply the
  branch-cleanup method an individual practice set may already define (one
  real individual set names this in its own `next-steps-after-commit`
  practice; the repo is private, so this names the practice rather than
  linking a page most readers cannot open): identify by who opened or drove
  the PR — the invoking person's own GitHub login, never someone else's
  branch — skip the repo's default branch and its protected integration
  branch, and report each remaining one with a direct link to its most
  recent PR's page, which is the one-click **Delete branch** control GitHub
  already shows there. A personal practice may decline to do this
  retroactive sweep on its own ("a separate, one-off task, done only when
  asked for directly") — a very deep check is exactly that direct ask, so
  this is the one place the sweep is a standing step.

  *Not merged* — the more expensive half, and the reason this bullet is not
  only about deletion. A merged branch nobody deleted is clutter; a branch
  that was meant to land and never did is lost work, and nothing in an
  ordinary week ever asks about it again. Each one is reported with what it
  is ahead by, when it last moved, and how many of its commits have no
  patch-equivalent on the integration branch — `git cherry`, not the
  ancestor test, because a branch that was rebased or squash-merged in
  reports as unmerged forever while carrying nothing, and calling that
  "unlanded" would train the reader to wave the whole list through. **Give
  every one a verdict: merge it, or close it with the reason recorded.**
  "Look at it later" is the state that produced the finding. Where the
  session cannot decide alone — the branch is someone else's, or its
  intent isn't legible from the diff — say so by name and ask, rather than
  leaving it unlisted.

  **Asking is not the same as listing.** A branch handed back to a person
  as a bare name and a commit count hands them the whole investigation
  too, which is how it gets postponed again. So every unmerged branch is
  written up with four things, in the reply and in the run record:

  1. **What the change is** — read the diff and say what the branch does,
     in a sentence or two. Not the commit subjects copied out: those say
     what each step did, not what landing it would mean.
  2. **A link.** Its most recent pull request (PR), when there is one.
     When there is **not** — a repo that lands work by direct push often
     has none at all — say so and link the branch's own compare view
     instead, rather than omitting the row or implying a PR exists.
  3. **The date it last moved**, so age is visible without asking.
  4. **A recommendation, with its reason** — merge, cherry-pick a named
     subset, or close. This is the part that makes the list decidable:
     check what the branch would actually do to the integration branch
     before recommending it, because a branch that is behind on shared or
     vendored files does not merely add its own work — merging it
     **reverts** theirs. Verified, not assumed: compare the vendored
     engine's recorded commit (or any generated artifact's manifest) on
     both sides. A branch carrying three genuinely-unlanded files on top
     of a forty-commit-old engine is a cherry-pick, never a merge, and
     saying "merge it" would have undone six weeks of work.

  Where a recommendation cannot be made honestly, say which of the four
  is missing and what would settle it.

## Why
The mechanical audits ([doc_lint.py](../tools/doc_lint.py),
[leak_gate.py](../tools/leak_gate.py),
[precedent_check.py](../tools/precedent_check.py),
[doc_sync.py](../tools/doc_sync.py)) catch broken links, bad syntax, and enforcement drift; the
routing audit catches a practice that should have fired and didn't. None of
them reads a document's own argument for whether it still makes sense, and
none of them can ask whether a check is checking the right thing — a check
that is wrong reports cleanly, which is exactly why nothing downstream of it
will ever notice. Both are judgment calls by design, not gaps any of the
audits is meant to close, which is why this stays a separate, on-demand
mechanism rather than folded into one of them.

**The pass order is the finding order.** A whole-system review generates far
more small findings than large ones, and small findings are the ones easiest
to fix — so an unordered run reliably spends itself on typography while an
adopter's install stays broken. Passes 1 and 2 are the ones whose misses
reach someone outside this session; passes 3 and 4 are the ones whose misses
cost the next session some confusion. Fixing in that order is not a
preference, it is what makes the check worth its cost.

**Read this before trusting the result, the same caution
`full-practice-audit` states for itself.**
[spec/ATTENTION_CEILING.md](../spec/ATTENTION_CEILING.md)'s review-arm result
(54% recall on a whole-catalogue judgment pass, worse than no review at all)
was measured against practice-compliance judging, not document-coherence
reading or fixture-building — different tasks, so that figure does not
transfer here directly — but nothing has evaluated this specific mechanism's
own reliability either. Treat it the same way: a backstop for what
enforcement cannot reach, not a substitute for enforcement, until it has its
own evaluation. Pass 1 is the partial exception, and the reason it is first:
building a fixture and running the checks on it produces evidence, not a
judgment, so its findings do not depend on this caveat.

## Story
Named in [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s v28 amendment
(2026-09-01) as "the inherited RepoPersonalPreferences (RPP) audit list ...
heavier than any of [light check, deep check, routing audit] ... not yet
inventoried here (RPP is a separate private repo); enumerate and wire it as
an on-demand tool when phase 5 or later actually needs it" — tracked nowhere
else, the same
structural gap [spec/UNBUILT_PLAN_ITEMS.md](../spec/UNBUILT_PLAN_ITEMS.md)
found `routing-audit` fell into, and logged there as `TODO.md` item 17.

Enumerating it turned up that earlier that same day, the phase-3 private-set
migration (v27) had carried a related list into the maintainers' own team set
(private, so named rather than linked) as its own `deep-check` practice. This
practice and its tool are the universal audit: available to any repo running
Precedent, not only Morgan and Alex's.

**Corrected 2026-09-06, on Morgan's ruling: the team's `deep-check` and this
practice are unrelated rules, and the deep check keeps happening in sessions
when committing, as it always did.** This Story previously described the team
practice as "generalized ... but otherwise the same enumeration as here," and
that sentence was wrong in a way that did real damage: it was read as
authority to drop `deep-check` from the team set as redundant, which removed a
routine per-commit check for a day.

The two differ in kind and cadence. `deep-check` is the working check a
session runs against its own repo as part of landing work. This practice is a
rare, expensive, cross-repo audit of the whole Precedent system —
"deliberately rare because the judging is expensive", and by its own Rule
never wired into a commit, push, or merge gate. Dropping the routine check on
the authority of the occasional one was the error, and this Story made it look
reasonable. The team's `deep-check` is restored to `active`, and the open
question this Story used to carry — whether it should point here via
`overrides:` — is answered: **it should not.** They are not the same rule, so
there is nothing to override.

This is the whole argument of
[decisions/2026-09-06-deduplication-not-retirement.md](../decisions/2026-09-06-deduplication-not-retirement.md)
in miniature: two rules resembled each other, and resemblance was accepted as
coverage.

Revised 2026-09-05, on Morgan's direct request, adding the missing-source
failure and the stale-branch sweep. Both were real, reproduced, not
hypothetical: this repo's own team source (`../precedent-team-maintainers`)
is declared in [precedent.json](../precedent.json), yet nothing before that
revision made a session go get the sibling clone, so a session starting in a
fresh checkout would run the tool, see the source reported "missing" on
stderr, and call the result a very deep check anyway. And a request in the
same conversation to actually run the newly-added sweep surfaced real,
currently-undeleted stale branches across every repo in force in that
session — several merged by direct push, with GitHub's own `merged` flag
still `false` for that reason, confirming the sweep's note is not
hypothetical either. Revised again the same day to add the
cross-source-staleness bullet, whose standing prevention side is
[cross-source-rollout](cross-source-rollout.md).

Restructured 2026-09-06, on Morgan's direct request, into the four ordered
passes above. Two things drove it. The first was the pre-launch audit of the
same date ([spec/PRELAUNCH_AUDIT.md](../spec/PRELAUNCH_AUDIT.md)): every one
of pass 2's questions but one is a defect that audit actually found, and not
one of them was reachable from the drift checklist this practice carried at
the time — the check was looking only at prose while the mechanisms
underneath it were reporting confidently and wrongly. The second was that
the audit found all of it by building fixtures and running checks on them,
which the practice never asked for; the "simulate a from-scratch install /
simulate the migration" items Morgan raised are that method written down as
a standing step. The run being explicitly splittable across sessions came
from the same request, for the obvious reason: what this practice now asks
for is more than one session's work, and a check nobody finishes is a check
that silently becomes its first pass.

Extended the same day, same request, with two things the restructure had
left implicit. Morgan asked whether the check looks for duplicate code —
two parts doing the same job redundantly — and it did not: the old
checklist's "needless repetition" is about a *rule* restated in prose, and
the two places code duplication appeared were incidental (a tie-break
between two copies of a file; a rule forbidding the copies the vendoring
tool makes). It is a mechanism property, not a writing one — a duplicate
does not stay identical, and the copy that goes on being wrong is as likely
as not the one that runs — so it belongs in pass 2, immediately before the
tie-break question it generalizes, rather than appended to pass 3's list.
The restructure had produced an instance of it in the same commit: this
practice's own checklist existed both here and as a `CHECKLIST` literal in
[tools/very_deep_check.py](../tools/very_deep_check.py), and the tool
printed the copy. The order of operations came from the same message: the
passes were ordered, but nothing said to run the cheap mechanical gates
before spending judgment, which is how a session ends up hand-reading for
something `doc_lint` reports in a second — and, worse, cannot tell drift
this run introduced from drift that was already there. Two positional
cross-references ("pass 2 item 10") were replaced with names in the same
pass, since citing a list position as if it were a name is a defect pass 3
tells the reader to report.

Split 2026-09-07, on Morgan's question — should the check look at unmerged
branches before anything else, so a session stops rewriting what was
already written and never merged? It should, and the reason is that the
sweep had been one thing when it is really two.

Pass 4 is last because "none of it strands an adopter", which is true of
deleting merged branches — that is clutter. It is not true of unlanded
work, and the run that prompted this proved it: two missing files were
rediscovered from scratch, written up as findings, and filed as open TODO
items, while the fixes sat finished on a branch from the previous day in
both private sets, named in those branches' own commit subjects. The cost
of a late sweep is not untidiness. It is duplicated work and a backlog that
records solved problems as open.

So the inventory — cheap, mechanical, and the only step here that PREVENTS
work rather than finding it — moves to step 4 of the order of operations,
before any pass. The verdicts — expensive, and judgment — stay in pass 4.
[tools/very_deep_check.py](../tools/very_deep_check.py) prints the
unlanded-work block before the checklist a session works from, and
verify_harness.py asserts that ordering specifically, since a block that
exists but prints last is exactly the failure being fixed.

Extended 2026-09-07, on Morgan's direct request, during the first run of
this practice: he asked for a summary, a link, a date and a recommendation
for each unmerged branch, so that he could actually decide about them. The
run that prompted it had reported four unmerged branches correctly and left
him with four names and four commit counts — which restates the finding
rather than resolving it, since the investigation each one needs was still
entirely undone.

The recommendation item earned its emphasis immediately. Two of those four
branches carried genuinely unlanded work — including, in both private sets,
the very files that same run had independently rediscovered as missing and
filed as open TODO items. The obvious recommendation was “merge them”. It
was wrong: both branches sat on a vendored engine 41 commits behind their
own `main`, so merging either would have reverted the engine wholesale in
order to land three files. Checking what a merge would *do* to the
integration branch, rather than only what the branch contains, is the
difference between a useful recommendation and a damaging one, and nothing
here had asked for it.

Made mechanical 2026-09-07, on Morgan's question of whether the check should
force a fetch before anything else. It should, and prose was never going to
carry it: the order of operations added the day before *said* to freshen
first, and prose is exactly what a session skips when the thing it is stale
about is the instructions. The evidence was already written down three
times in [AGENTS.md](../AGENTS.md)'s gotchas — a session 366 commits behind
that reported files landed days earlier as not existing, and a
session-start guard that could not help because the container's copy of the
guard predated the guard. So the tool now fetches and compares every repo
in force as its first act and exits non-zero on anything it cannot prove
current. Two design calls worth keeping: it *verifies* rather than mutates
by default, since a tool that pulls inside a clone handed to it is its own
gotcha in that same section — one silently moved a session's checkout onto
another branch mid-session — and `--freshen` therefore declines a diverged
or dirty tree outright, where a fast-forward would discard someone's work.
And it separates "cannot reach origin" from "this branch was never pushed",
because the two have unrelated remedies and the wrong one sends the reader
to debug a network that is fine. Both source repos in the session that
built this failed the new gate on first run — one seven commits behind, one
on a local-only branch — neither of which anything before this would have
reported.

Extended again 2026-09-07, on Morgan's question about branches that were
meant to be merged and got lost in the mix. The sweep had the data and only
half the question: it listed unmerged branches as an aside to the deletion
report — "check each one's PR history for a superseded case" — which asks
only whether the branch is safe to *drop*, never whether it holds work that
should have landed. The two failures are not symmetrical, and the one the
sweep was blind to is the expensive one. The scan now reports commits
ahead, last-commit date, and a patch-level count via `git cherry`, which
matters more than it sounds: `merge-base --is-ancestor` reads commit
identity, so a rebased or squash-merged branch reads as unmerged forever
while carrying nothing, and a report calling those "unlanded work" would
teach the reader to wave the whole list through. On the first run it found
a source branch nineteen commits deep, untouched since the day before, that
nothing in this repo would otherwise have asked about again.

## Install
[tools/very_deep_check.py](../tools/very_deep_check.py) enumerates the scope
(this checkout's own top-level documents plus every active source's
`practices/*.md` tree, reusing
[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s own source
resolution) and prints this practice's Detail section — read from this file
at run time rather than kept as a second copy
inside the script, so the passes the tool prints cannot drift from the
passes defined here. No mechanical `checked_by` exists for this practice's
own Rule, and can't: what it asks for is a session's judgment applied to a
scope the tool enumerates, the same class of resistant-to-automation
practice `full-practice-audit` and `mistakes-become-rules` already name. See
[full-practice-audit](full-practice-audit.md) for the narrower,
already-built sibling this one deliberately does not replace, and
[spec/UNBUILT_PLAN_ITEMS.md](../spec/UNBUILT_PLAN_ITEMS.md) for the decision
record this practice's own build closes out.

Five parts of the check *are* mechanical, as far as a mechanical check can
reach (`checkable-gets-checked`): every repo in force is fetched and
compared against its origin before the tool reads a line, and anything but
provably-current exits non-zero (`--allow-stale` for a deliberately offline
run) — with `--freshen` fast-forwarding a clean tree that is strictly
behind, and declining a diverged or dirty one, where a fast-forward
discards commits; a missing declared team or individual source is a hard,
non-zero-exit failure by default (pass `--allow-missing-sources` only when
proceeding without it is actually intended); every tracked JSON and YAML file is parsed with a real parser
(pass 2's format-claims question), and a file that does not parse stops the
run, since the tool
reads `precedent.json` to enumerate its own scope; each team and individual
source is checked against the shape its bootstrap skeleton ships, catching a
source migrated into place that never passed through bootstrap; and both
halves of the branch sweep are real git checks — `merge-base --is-ancestor`
against each repo's own `origin/HEAD` (or an explicit `--target` for this
checkout when its integration branch isn't its default one, this repo's own
`precedent-beta-v01` being exactly that case) for merged-and-undeleted, and
`git cherry` for how many of an unmerged branch's commits have no
patch-equivalent on that target.

What stays a session step, deliberately: the branch sweep's other half —
turning a mechanically-merged branch into a *reported* one requires knowing
which PR it came from, who drove it, and that PR's URL, none of which an
offline `git` check can see; a closed-but-not-provably-merged branch is the
same story one layer out, where only the session, reading that branch's PR
thread, can tell "superseded" from "abandoned, still someone's open
question" — and, on the unmerged side, whether nineteen commits nobody
merged were meant to land at all, which is the verdict itself and the one
thing here no scan can supply. Pass 1's fixtures are a session step for the same reason in a
different form: building a fresh install and a migration and then judging
what the documents failed to say is not a thing a script can assert about
itself, and a scripted install would test the script rather than the
instructions an adopter actually follows.

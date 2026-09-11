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
  before any pass and only the verdicts stay in pass 4;
  extended same day, Morgan F, so pass 1 tests an UPDATE and not only an
  install, against a real consumer repository and not only a fixture;
  extended 2026-09-07, Morgan F, with pass 2's enumerate-rather-than-sample
  question and pass 4's whole-tree rehearsal of the endgame merge, after a
  sampled rehearsal of the phase-7 merge-back returned the wrong verdict;
  extended 2026-09-09, Morgan F (strength: assented), with pass 3's
  tier-placement question, after a session asked what this check covers and
  found that nothing here or anywhere else reviews whether a practice's
  `tier` is still right; extended 2026-09-11, Morgan F (strength: decided),
  so every repo in force is asked whether it still EXISTS and still accepts
  a push, not only whether the clone is current -- \"make sure it doesn't
  automatically try to open a repo that doesn't exist / was deleted /
  archived\"; extended again 2026-09-11, Morgan F
  (strength: decided), so pass 3's session-load read covers every repo in
  force rather than this checkout alone, with the ceilings themselves moved
  out to session-load-budget; extended again 2026-09-11, Morgan F
  (strength: decided), so every run records what each of its parts
  returned and what each cost into a ledger that outlives the run, and
  reads them against the runs before it -- \"the check now has many
  different components and when you run it, I want you to track the
  results of each part and compare at the end to ... find any aspects of
  the very deep check that weren't useful\""
---
## Rule
When a person explicitly asks for a "very deep check", or after work that
invites drift (a batch of practices added or reordered, a practice that
changed shape, an install into a new repo, a merge that resolved conflicts
across several shared files), run
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) and work the four
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
against its origin, and must still be a repository work can land in** — this checkout and every attached source.
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) fetches and compares
each one as its first act and refuses to go further otherwise, because a
very deep check's whole product is judgment about what the repos say: a stale tree does not degrade
that judgment, it inverts it — work that landed last week reads as missing,
and bugs fixed days ago read as open. "Stale" and "cannot prove it isn't"
get the same verdict, since a confident wrong answer is the failure mode
either way. Fix it and start again; `--freshen` will fast-forward a clean
tree that is merely behind, and `--allow-stale` exists only for a
deliberately offline run, where every finding is then provisional.

**Current is not the same as alive**, and the second half is the one nothing
else here can see. Every repo in force is opened **automatically** — the
session-start hook clones each declared source, the freshness gate fetches
it, the refresh tool pulls it — so a source that has been **deleted,
renamed, or archived** is retried every session by machinery whose failures
are deliberately quiet. The check asks GitHub about each one, a single
call per repo: a deleted or access-revoked repository is re-cloned forever
and its failure reads like a credential problem, a renamed one keeps
resolving through a redirect that lasts only until somebody takes the old
name, and an **archived** one is the worst of the three — it clones,
fetches and reads exactly like a live repository and refuses every push, so
a session can spend its whole run editing a source nothing it writes can
ever land in. Ask with a credential or not at all: unauthenticated, a
private repository and a deleted one both answer *Not Found*, so the run
must say it learned nothing rather than report a repo as gone.

**Every declared team and individual source must actually be present before
the check runs.** The ordinary loader tolerates a missing personal source and
says so on stderr — the right call for routine loading, where one operator's
absent individual set is expected. It is the wrong call here: a very deep
check is explicitly asked for and scoped to the whole set of repos in force,
so a silently dropped source defeats the reason it was asked.
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) fails loudly rather
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
run's state in [spec/VERY_DEEP_CHECK.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/VERY_DEEP_CHECK.md): which
passes are done, what each turned up, what was fixed, what was deferred and
where it went. A later session resumes at the next unfinished pass rather
than starting over, and a pass is never quietly skipped — a pass deliberately
not run is recorded as not run, with the reason.

**Every run records what each of its parts returned and what each cost, and
reads them against the runs before it.** This check grew a section at a time,
each one added because a real run wanted it, and until 2026-09-11 nothing had
ever asked the reverse question: does any of them still earn its place?
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) appends every run to the
checked repo's own
[record/very-deep-check-ledger.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/very-deep-check-ledger.json)
— per section: what it found, what it printed, how long it took — and prints
the cross-run read at the end of each run. **The tokens it reports are what a
section PRINTED**, which is what it costs a session's context to read it, and
never the model's spend on judging that material, which no tool here can see.
The four passes are the expensive half and are the session's own measurement:
record each one as you finish it with `--record-pass`, findings and cost
included where you have them and left absent where you do not.

**A section that has come back empty across every recorded run gets a
decision, not a drift.** The run names those at the end, with three answers
and none of them automatic: **keep** it and say why here, **cheapen** it
(same check, less printed), or **retire** it — which means this practice's
Detail loses the bullet and
[decommission-deletes-files](decommission-deletes-files.md) applies to
whatever it owned. **Quiet is not the same as useless**: a guard that never
fires may be exactly why nothing is broken, and several of these sections
were written after one expensive incident they exist to prevent. Quiet is
also not the same as unmeasurable — a section that could not produce a count
is reported separately and is never graded as clean.

Fix what a pass turns up in the same pass — most findings are small — then
re-run the mechanical audits, since the fixes themselves break links.
Anything deliberately left alone gets a line in [TODO.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md) saying
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

1. **Prove every repo in force is current, and still there.** The tool's
   own first act, and a refusal rather than a warning — warning was tried and failed, because a
   session stale enough to need the warning has already been handed stale
   instructions to read it against. A source is the likelier offender: the
   session-start freshness guard runs for the session's primary repo only,
   so an attached sibling has never been checked by anything. The
   liveness half runs in the same breath and is a finding rather than a
   refusal: a deleted, renamed or archived repo in force does not make the
   reading below wrong, it makes the writing above it pointless.
2. **Run the deep check suite as it stands** — the five gates
   [AGENTS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md) names ([two-check-levels](two-check-levels.md))
   — and fix what it reports, before this check reads a line. `0 failed` and
   `0 violated` is the starting line, not the finish.
3. **Run [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py)** for the
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
5. **Ask for a real consumer repository, before starting pass 1.** Pass 1's
   highest-yield item needs one attached, and attaching is the person's act,
   not the session's — so the ask goes here, at the top, where an unanswered
   question still leaves time to work around it. Asked at the end it is not
   a question, it is a postponement. One sentence: name what it is for
   (updating its vendored tree to current and running its own gates), and
   carry on with everything else while it is outstanding.
6. **Then the passes, 1 through 4**, each ending with the suite from step 2
   re-run — the fixes a pass makes break links of their own. Whenever a
   pass turns up a gap, check it against step 4's inventory **before**
   writing it up: if a branch already fixes it, the finding is "this is
   written and unlanded", which is a different problem with a different
   remedy.
7. **Record each pass as you finish it, and read the component ledger
   last.** `--record-pass '<pass>=<status>,findings=N,tokens=N,note=…'`
   puts the expensive half's outcome and cost beside the tool's own
   sections; the cross-run read printed at the end of every run is then
   about the whole check rather than about its cheap half. Answer whatever
   it names as quiet — keep, cheapen, or retire — in the same run, in
   [spec/VERY_DEEP_CHECK.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/VERY_DEEP_CHECK.md). A
   section left on that list across runs with no answer written down is the
   drift this step exists to stop.

The same rule holds inside a pass: where a mechanical check covers part of a
bullet, run it first and read only what it cannot see.

### Pass 1 — Can a new adopter get to a working install, and an existing one stay in one?
The highest-cost failures are here, because they strand someone outside this
session who cannot see what is wrong. Both halves of that sentence carry
weight: an install happens once, an **update** happens forever, and for a
long time only the first was ever tested. Reading the install documents finds
almost none of them: every significant finding of the 2026-09-06 pre-launch
audit came from **building the thing the document describes and running the
checks on it** ([spec/PRELAUNCH_AUDIT.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/PRELAUNCH_AUDIT.md), "The
method"). Build the fixtures.

- **A real from-scratch install.** A scratch repository with nothing in it,
  installed per [INSTALL.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/INSTALL.md) §0 against `precedent-beta-v01`
  alone — no team set, no individual set, none of the sibling clones this
  session happens to have — following the documents exactly as written,
  without leaning on what this session already knows. Then run the deep
  check on the result. Anything the session had to work out that the
  documents did not say is a finding; so is any check that cannot come back
  clean on a correct fresh install.
- **A real migration**, the same way: a scratch repo on the classic
  `process/upstream/` layout, walked end to end through
  [spec/MIGRATING_EXISTING_INSTALLS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/MIGRATING_EXISTING_INSTALLS.md).
- **An update, not only an install.** Vendor a scratch consumer at an OLD
  upstream commit, then bring it forward to the current one with the
  documented tooling and run the checks. Every fixture above builds a repo
  that has never had to move, so nothing here ever exercised drift — and
  drift is where a consumer spends its whole life. This is the cheap half
  and it needs nobody's permission.
- **A REAL consumer repository, brought up to date.** Ask the person to
  attach one, early — see the order of operations, which puts the asking
  before pass 1 for the obvious reason that the answer may not come back.
  Then update its vendored tree to the current upstream, re-sync, and run
  its own gates. Where the scratch fixtures are clean rooms, this is the
  only step that meets what a real repo accumulates: a `visibility` nobody
  declared, an engine somebody mirrored by hand, prose that grew up
  referencing a private source, hundreds of commits of upstream drift, and
  a vendored copy of the update tool old enough to be dangerous.

  Do not treat this as optional garnish. On 2026-09-07 the scratch fixtures
  passed and one real consumer then produced seven defects in a row, four of
  them in mechanisms this run had built or fixed hours earlier — including
  one that had to be fixed twice because the second attempt failed with an
  identical message. The pre-launch audit had already named the gap it fills
  ("what is still missing is a real project: a scratch repository has no
  subject matter"); it stayed named and unfilled until somebody attached one.

  If no consumer can be attached, say so and record pass 1 as PARTIAL. Never
  let it pass on the fixtures alone — that is precisely the state that held
  while these seven defects were live.
- **The empty neighbourhood.** A brand-new person with no individual set; a
  team with no team set yet; a consumer whose sources are declared but
  unreachable, as they are in every continuous integration (CI) checkout.
  Each degradation path should degrade with a named reason — never pass
  silently on a scan that never ran, and never fail on something the adopter
  cannot fix.
- **The generator, against the sets that already exist.** Run
  [tools/precedent_bootstrap_source.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_bootstrap_source.py)
  for each resolved team and individual source and diff its output against
  the real set, file by file — the tool's `BOOTSTRAP DRIFT` section does
  this, and it needs those sets attached to do anything at all. A set is
  created once and then lived in for months while the generator keeps
  moving, so the two drift apart in both directions and nothing else here
  looks: `verify()` and the template-freshness scan both ask which files
  exist, never what any of them says. A difference in a file the skeleton
  ships is the set being used and is not a finding. A difference in a file
  bootstrap *generates* — the vendored engine, the session hooks,
  `settings.json` — is, and the set's own `ENGINE_MANIFEST.json` says which
  fix applies: refresh an older vendoring, or move a hand-edit upstream.
  **Without the sets attached this is a SKIP, not a pass** — the section
  says so in those words, and a run that leaves it skipped records pass 1
  as PARTIAL exactly as the real-consumer step above does.
- **Cross-repo relationships and permissions.** Walk who must be able to read
  or write what, for a *new* repo and a *new* person: the vendored engine,
  each declared source, approvers and CODEOWNERS, and the protected paths
  [spec/CONTRIBUTOR_ACCESS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CONTRIBUTOR_ACCESS.md)
  describes. A step that works only because this session's operator already
  has access is a finding.
- **Not the practice simulation.** This pass installs real fixtures and runs
  the ordinary checks on them. It does not run
  [tools/precedent_simulate.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_simulate.py) or its
  siblings, which are deliberately never reachable from an occasion, gate, or
  hook ([spec/SIMULATION_BRIEF.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/SIMULATION_BRIEF.md), "Never
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
   [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) now does this for
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
   [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py), with nothing
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
14. **Does a verification enumerate, or does it sample?** For any check
    whose failure mode is something *absent* — a file, a term, a link, a
    row, a practice — ask how it concluded nothing was missing. If it can
    name the items it looked at, it is reporting its own coverage and not
    the property: **a sample proves presence and can never prove absence.**
    Worse, the items a session reaches for are the ones it has just been
    working on, which is systematically the class that cannot fail. Rebuild
    it as a set difference — the whole expected set, the whole actual set,
    report everything in the first and not the second — and where the whole
    set genuinely cannot be enumerated, say the check is partial rather
    than letting a clean sample read as a clean result. *(Found: a
    rehearsal of the phase-7 merge-back simulated the merge, checked that
    two files survived it, and recorded that the revert trap "was checked
    and does not fire". Both files had been edited by that same session
    days before, which is exactly what put them in the surviving class. The
    set difference, run against the whole tree the next day, was 507
    files.)*

### Pass 3 — Does the writing still hold together?
The coherence read, across every repo in scope. Run the mechanical audits
first so this pass spends its attention on what they cannot see.

- **Contradictions** — two rules, or two documents, that can't both be
  followed; a rule whose own carve-outs have eaten it.
- **Rules we ship somewhere else** — the contradiction this pass kept
  missing, and it is missed for a structural reason rather than
  carelessness. **A template is inert here and binding there.** Read as a
  document, `templates/VOICE.md.template` makes no claims; instantiated
  into an adopter's repo it is a file of standing orders sitting beside the
  resident practice block, and nothing on either side compares the two. So
  ask it directly, every run: **what rules does this repository ship into
  somebody else's, and do they agree with the catalogue?**
  [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py)'s "RULES WE SHIP
  SOMEWHERE ELSE" section hands you the inventory — every shipped file
  carrying imperative prose, with a count — so this is a read of a short
  list, not a browse of a directory. **Read them against the RESIDENT
  practices first:** an on-demand practice reaches a session that thought to
  ask, so a shipped file contradicting one is a conflict nobody may ever
  hold both halves of; a resident one is in front of every session always,
  so a shipped file contradicting it puts two live orders in the same
  context window, every turn, in every adopter repo. The test for each
  shipped rule is one question — **would this improve anyone's work?** If
  yes it is a practice in the wrong place: land it in the catalogue and cut
  it from the template. If it is only true of that one project, it belongs
  in the file and should say why. *(2026-09-08: `VOICE.md.template` shipped
  205 lines of general writing guidance to every project, one of which said
  "no bold inside paragraphs, and no bolded thesis sentence" while the
  resident `bold-key-phrases` said to bold key phrases by default. Both had
  been true for weeks. The bullet above this one already said to look for
  contradictions and had never found it — a coherence read reads documents,
  and a skeleton file does not read as a document making claims.)*
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
  *act* ("very deep check", "full practice audit", "light check", "deep
  check") needs somewhere a session meeting it cold can look it up. A
  trigger word reachable only by already knowing it is not a keyword, it is
  folklore. The usual home is a practice's `defines:` field, which lands it
  in [GLOSSARY.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/GLOSSARY.md) — **but a glossary entry is not the
  property; being findable is.** "Go merge" and "Park it" are deliberately
  NOT in the glossary (Morgan, 2026-09-08: *"Don't put it in the
  glossary."*); both are defined in [AGENTS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md), which is
  where a session actually reads them, and `check_park_it.py` fails if that
  paragraph goes missing. This bullet named "Go merge" as its own example
  until 2026-09-08, when a run followed it, found the phrase missing from
  the glossary, and was one edit away from reversing a decision made that
  morning — so check where a keyword IS defined before calling it
  undefined.
- **What every session loads, and what it costs.** The rule is
  [session-load-budget](session-load-budget.md) — every always-loaded surface
  carries a declared ceiling in
  [tools/session_load_budgets.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/session_load_budgets.json), and
  `precedent_check.py --only session-load-budget` tests this checkout's
  against them on every run. **What this pass adds is the half no ceiling
  covers**: the sum across every repo in force, and the judgment about what to
  move. Nothing is wrong at any single commit — every line in an always-loaded
  file was right to add on the day it was added, and it only goes wrong in
  aggregate, months later.
  [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py)'s "SESSION LOAD"
  section counts the instructions file section by section for this checkout
  **and for each attached team and individual source**, plus the untracked
  practice file when private sources resolved, and flags any section large
  enough to be worth splitting and any entry whose own text says its trap is
  settled. **Read those flags, do not obey them:** an entry's claim that it
  was fixed is not evidence, and the verification is against the tree.
  Its "GOTCHA CURRENCY" sub-pass reads the other direction — **the tree
  against each entry, rather than the entry against itself** — because the
  settled-marker flag can only find an entry honest enough to say it is
  fixed, and the expensive case is the entry that still reads as live while
  the remedy it names has been renamed or deleted underneath it. It reports a
  named file, check slug or fixture that is no longer in the tree, an entry
  whose newest date has gone a season without re-measurement, and the token
  cost of each, so a reduction pass can be ordered by what it would actually
  save. Every one of those is a question, not a verdict: an entry may name a
  file that is gone precisely because it tells the story of a decommission.
  **What no longer bites moves to a linked archive in full, with the verdict
  that moved it — never to a deletion.**
  **The trap is optimising for the total, and it is the likely mistake rather
  than a remote one.** These sections exist because sessions kept losing hours
  to the same environment traps; a trimming pass that chases the number
  deletes the entries that are working. **The question for each part is
  "would a session hit this today", never "how big is it".** What no longer
  bites moves to a linked archive **in full** — the payload of a gotcha is the
  story of what failed ([environment-gotchas](environment-gotchas.md)), so a
  deletion eventually leaves a live section of unexplained rules.
  *(Found 2026-09-08, and the shape is why this belongs here: the resident
  block's 2,000-token budget had been reporting green for weeks while the
  file around it reached ≈17,000 — the budget governed 4% of the cost, and
  nothing was measuring the rest. The first pass moved 24 entries' full text
  to [record/GOTCHAS_ARCHIVE.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS_ARCHIVE.md) and took ≈4,900
  tokens off every session, deleting nothing. A consuming repo measured the
  same day had the same disease in a different section, so this is structural
  rather than one repository's untidiness.)*
- **Whether each practice's TIER is still right.** The question above asks
  what the loaded text costs; this one asks which practices should be in it
  at all, and nothing else in Precedent ever asks it. `tier: resident` is
  governed only by [tools/build_views.py](../tools/build_views.py)'s hard
  2,000-token cap, which fails the build outright — so the trade is forced
  once, at the moment somebody adds a resident practice, and the set is never
  revisited afterwards. Read it in both directions. **Demote** a resident
  practice whose occasions turn out to be narrow enough that the path or
  occasion channel would reach them. **Promote** an on-demand practice that
  keeps being missed, which is the failure the tiering exists to prevent: an
  on-demand practice only reaches a session that thought to ask for it.
  **Judge the occasions, not the token count** — a demotion made to free
  budget is the SESSION LOAD trap one level up.
  *(Read [spec/LOADER.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/LOADER.md)'s replay before any verdict, because
  it makes the third answer visible. It ran `verify-postcondition` and
  `environment-gotchas` resident at two Rule lengths; the arm reading only the
  resident block found `verify-postcondition` **0 of 2** with the long Rule and
  **0 of 3** with the short one, and `environment-gotchas` 0 of 2 and 0 of 2 —
  while in that same last run the arm reading the whole catalogue found them 3
  of 3 and 2 of 2. **Residency was doing nothing for either practice at either
  length**, and what both runs agree they needed was a `checked_by`. So
  "neither tier is the problem" is an available verdict, and was the right one
  twice.)*
  [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py)'s "TIER PLACEMENT"
  section hands you the resident set with each practice's occasion and
  whether a check already covers it, so this is a read of a short list. It
  enumerates and does not judge, and no `checked_by` will: the cap already
  tests the only property a script can see, and whether an occasion is
  *every session, always* is a reading of how work here actually goes.
- **Orphans — files nothing owns any more.** The mirror of every other
  check here, which all ask whether something that should be present *is*.
  An orphan is present and in nobody's list, so no mechanism keyed on a
  current list can see it.
  [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) now sweeps four
  kinds mechanically — a tombstoned engine file, a manifest entry the
  current kind dropped, an unrecorded engine file hand-copied in, and a
  `check_<slug>.py` whose practice is gone — so read only what it cannot:
  a document nothing links to, a workflow whose job moved, a directory a
  migration emptied. *(Found 2026-09-08: three practice sets each carrying a
  `precedent_retire_path.py` that a rename had orphaned, with `status`
  reporting all three healthy — it was gone from the file list, gone from
  the manifest, and the untracked-file check is keyed on the current lists
  by design. Three mechanisms, each correct, all blind to it at once.)*
- **Whether the SKELETONS still describe a real source.**
  `precedent_bootstrap_source.verify()` reads a skeleton and asks whether a
  real source has everything in it — which catches a source that drifted
  below the template and can never catch the template drifting below
  reality. Run the reverse: what does every resolved source of a level
  carry that a newly bootstrapped one would be created without? *(Found
  2026-09-08: the individual skeleton shipped no `identity.json` — the one
  place a person's name, address and timezone live, and the file that
  decides whether the commit hook ENFORCES an author-date offset or merely
  guesses one. Every real set had it; a bootstrapped set would not have,
  and its wrong-offset commits would reach the remote before anything said
  so.)* **One source of a level is not evidence** — the check says so
  rather than reporting one repo's working documents as a template gap.
- **Filenames, where the mechanical check is blind.**
  [filename-separator](filename-separator.md) is enforced per (directory,
  extension), so it catches a folder holding both `A_B.md` and `A-B.md`.
  It cannot see a directory that is internally consistent and wrong for its
  kind — a `practices/` full of `SCREAMING_SNAKE.md` is uniform and still
  breaks the slug convention — nor two directories that disagree where a
  person moves files between them, nor an exemption whose stated reason has
  stopped being true. Read those.
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
- **Conflicting practices inside one source, and same-slug practices across
  two** — two rules in the same catalogue that cannot both be followed, and
  the same slug defined by two sources at the same level. Requested by
  Morgan 2026-09-07 and **not yet built as a mechanical step**: the
  cross-source half is already a hard `ResolveError`
  (`precedent_resolve.py` refuses a source list where two same-level
  sources define one slug), so what this pass adds is the *within-source*
  half, which nothing detects at all — two practices in one catalogue whose
  Rules pull opposite ways. The occasion for adding it was real: on
  2026-09-07 two sessions landed `fail-gracefully` and `bold-key-phrases`
  into both team sets on the same day, each doing the obviously right
  thing, and the collision surfaced only because this check happened to
  resolve all four sources by hand.
- **Anything else the read turns up** — if something is wrong and none of the
  categories above name it, it is still a finding.

### Pass 4 — Catalogue, backlog, and branches
Last because none of it strands an adopter, and none of it is cheap.

- **The full catalogue, every practice.** Run
  [tools/full_practice_audit.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/full_practice_audit.py) across every
  source in force. That tool deliberately prints enforced practices as one
  line each; pass 2's *read each enforced practice's check against its own
  Rule* is where those get their real read, so the two
  together are what "every single practice was looked at" actually means.
- **Backlog drift.** Read [TODO.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md) (and each source's equivalent)
  end to end: entries already done, no longer relevant, or never actually
  decided. Treat an entry that is really just an unfixed bug as work, not as
  backlog — [todo-is-a-handoff](todo-is-a-handoff.md) queues only what is
  blocked or out of scope, so anything else there is either doable now or
  should be closed.
- **Branches, both directions, one verdict each.** The *inventory* was
  already read at step 4 of the order of operations, for a different
  reason — to stop this run rediscovering work that exists. What is left
  here is the expensive half: a verdict on each.
  [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) reports, for this
  checkout and for every source that is its own git checkout (a repo-local
  source inside the parent checkout shares its parent's branches and isn't
  swept separately), two lists per repo. Neither may be left without a
  verdict. **Every source the repo declares is swept, at any level** — what
  decides is whether the path is its own git checkout, which the tool
  settles by looking, not the source's level. A vendored tree inside the
  parent has no branches of its own; a sibling clone has plenty.

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

  **Every row carries the date it last moved, and the list is split at a
  declared staleness threshold** — `branch_stale_days` in the repo's own
  [precedent.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/precedent.json), overridable for one run with
  `--stale-days N`. Both halves are equally proven safe to delete by the
  ancestor test; the split sorts the chore rather than grading the
  branches. **Merged *and* long-finished is the safest thing on the page**;
  merged this week may still be checked out on somebody's machine, and
  deleting it under them is a small rudeness the ancestor test cannot see.
  A bare list of names cannot support either judgment, which is why one was
  never acted on — see the Story.

  **The threshold is a declared input, never a number in the engine**
  ([constants-are-risk-inputs](constants-are-risk-inputs.md)): the right
  value is a property of how fast a repo works, and a repo that has
  declared nothing gets the engine's conservative default.

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

- **The endgame merge, rehearsed against the whole tree.** A repo whose work
  is pinned to an integration branch is aimed at one merge it has never
  performed — this repo's phase-7 fold-in of `precedent-beta-v01` into
  `main` is the case — and that merge gets exactly one attempt, usually
  under time pressure, usually by whoever approves it rather than whoever
  built it. Rehearse it here, every run:
  [tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) merges the
  integration branch into its base in a throwaway worktree, commits nothing,
  and reports **two sets, separately**. *Conflicting paths* are loud, and
  whoever runs the real merge will deal with them. *Paths present on the
  integration branch and absent from the merge result* are silent — no
  conflict, no message, no line in the merge output — and **that set must be
  empty.** Anything in it is a file that will disappear when the merge lands
  and that nobody will be told about.

  **What puts entries in it is history surgery on the base branch**, not
  anything wrong with the integration branch: a reverted merge, a
  cherry-pick, a force-push. Git decides what to replay from *history*, so a
  revert that undid the files while leaving the commits in the base's log
  makes git treat that work as already merged and then honour the deletion.
  Re-run the rehearsal whenever the base branch moves — a clean result last
  month says nothing about a base that has been touched since.

  **Two honest limits, both of which must be reported rather than assumed
  away.** On a shallow clone the merge base resolves wrongly or not at all,
  and an under-fetched history yields an empty difference that reads exactly
  like a clean one — so the rehearsal proves its history reaches the base or
  reports that it could not run. And an empty set means nothing *vanished*,
  not that the merge is *correct*: a file present in the result can still
  carry the wrong side's content, which only the conflict set read by a
  person will catch.

## Why
The mechanical audits ([doc_lint.py](../tools/doc_lint.py),
[leak_gate.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/leak_gate.py),
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
[spec/ATTENTION_CEILING.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/ATTENTION_CEILING.md)'s review-arm result
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
**The component ledger was Morgan's, 2026-09-11**, and it was asked for in
the shape of a suspicion rather than a complaint: *"maybe the simulation
doesn't find anything so it's not worth it to do."* The check had grown to
around twenty sections, each added by a run that wanted it, and **not one of
them had ever been asked to justify itself** — there was no record of what
any part had returned, so the question could not be settled by anything but
memory. **What is on the record is only the asking**: no section has yet
been retired on this evidence, and claiming one had would be the invention
[no-invented-specifics](no-invented-specifics.md) forbids. The first run
after it landed did make one thing plain — the printed checklist is by far
the largest thing the tool emits, and it finds nothing by construction,
because it is material for a session to read rather than a check. That is a
cost question, not a usefulness one, which is why the run prints the two
side by side and decides neither.

**The liveness half was Morgan's, 2026-09-11**, and it was asked for
before anything broke: *"make sure it doesn't automatically try to open a
repo that doesn't exist / was deleted / archived."* No deleted or archived
source has cost this project a session yet, and saying otherwise would be
the invention [no-invented-specifics](no-invented-specifics.md) forbids.
What IS on the record is both of its neighbours, twice over in
[AGENTS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md)'s
gotchas: a clone URL whose capitalization GitHub answered with *"this
repository moved"* — the rename case, diagnosed as the cause of an
unrelated failure it had nothing to do with — and a session that read
*"access to this repository is not enabled"* as a token problem and went
looking for a credential that was fine. Both are what a repository that has
quietly stopped being reachable looks like from this side, and in both the
expensive part was the misdiagnosis, not the outage.

Named in [PRACTICE_ENGINE_PLAN.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/PRACTICE_ENGINE_PLAN.md)'s v28 amendment
(2026-09-01) as "the inherited RepoPersonalPreferences (RPP) audit list ...
heavier than any of [light check, deep check, routing audit] ... not yet
inventoried here (RPP is a separate private repo); enumerate and wire it as
an on-demand tool when phase 5 or later actually needs it" — tracked nowhere
else, the same
structural gap [spec/UNBUILT_PLAN_ITEMS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/UNBUILT_PLAN_ITEMS.md)
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
[decisions/2026-09-06-deduplication-not-retirement.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/decisions/2026-09-06-deduplication-not-retirement.md)
in miniature: two rules resembled each other, and resemblance was accepted as
coverage.

Revised 2026-09-05, on Morgan's direct request, adding the missing-source
failure and the stale-branch sweep. Both were real, reproduced, not
hypothetical: this repo's own team source (`../precedent-team-repo-maintenance`)
is declared in [precedent.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/precedent.json), yet nothing before that
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
same date ([spec/PRELAUNCH_AUDIT.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/PRELAUNCH_AUDIT.md)): every one
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
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py), and the tool
printed the copy. The order of operations came from the same message: the
passes were ordered, but nothing said to run the cheap mechanical gates
before spending judgment, which is how a session ends up hand-reading for
something `doc_lint` reports in a second — and, worse, cannot tell drift
this run introduced from drift that was already there. Two positional
cross-references ("pass 2 item 10") were replaced with names in the same
pass, since citing a list position as if it were a name is a defect pass 3
tells the reader to report.

Extended 2026-09-07, on Morgan's proposal, after the run that prompted it
had already demonstrated the case: he suggested adding a step where a real
repository is attached and its vendored copy updated, because that is how
the session had just found its bugs.

It is the right idea, and the diagnosis underneath it is sharper than
"fixtures versus reality". Every pass-1 fixture builds a repo that has
never had to MOVE. An install happens once; an update happens forever, and
nothing here had ever tested one. That gap splits in two, and both halves
are now bullets: a scratch consumer vendored at an old commit and brought
forward tests drift cheaply and needs nobody's permission, while a real
consumer tests what only accumulation produces — an undeclared visibility,
a hand-mirrored engine, prose that grew up naming a private source, and a
vendored copy of the update tool old enough to be dangerous.

It is deliberately NOT a fifth pass. The passes are ordered by what a miss
costs, and a fifth one sits in the position most likely to be skipped —
which is exactly wrong for the highest-yield step there is. It belongs in
pass 1, where "an adopter is stranded" already lives. What does move to
the front is the ASKING: attaching a repository is the person's act, and a
question asked at the end of a long session is not a question, it is a
postponement.

The evidence: on 2026-09-07 the scratch fixtures passed, and one real
consumer then produced seven defects in a row — four of them in mechanisms
that same run had built or fixed hours earlier, one needing two attempts
because the second failed with an identical message. The pre-launch audit
had already named this gap in as many words and it stayed named and
unfilled until somebody attached a repository.

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
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) prints the
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
times in [AGENTS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/AGENTS.md)'s gotchas — a session 366 commits behind
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

Extended again 2026-09-10, and both halves came from Morgan asking a plain
question about a real sweep: *does this give me a list of branches I can
delete, across all the repos?* Reading the answer showed two things the
sweep had been quietly getting wrong.

**The deletion list had no dates.** The unmerged half had carried its date
since the day above; the merged half — the half that actually ends in
somebody deleting something — was a bare list of names. That is the wrong
shape for the decision it feeds. Measured the same day on this repo: 69
merged, undeleted branches, median age three days, oldest 39, and no way to
see any of that from the report. The branch merged an hour ago and the one
merged last quarter rendered identically, so the reader either deletes
blind or defers the list again, and deferring is what had happened every
time. Each row now carries its last-commit date and age, and the list is
split at a declared threshold. **What made the threshold worth declaring
rather than fixing in code**: the engine's conservative default of 90 days
put *every one* of this repo's 69 branches on the recent side — a feature
that shipped inert in the repo that asked for it. This repo declares 30.
Nothing measured that either number is right; both are values picked to fit
a distribution, said so in [precedent.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/precedent.json) rather than
dressed up ([no-invented-specifics](no-invented-specifics.md)).

**And the sweep covered fewer repos than it read as covering.** It scanned
this checkout plus sources at the `team` and `individual` levels only,
because it reused `FATAL_MISSING_LEVELS` — the list of *whose absence
aborts the run* — as if it also meant *whose branches are worth sweeping*.
Two different questions, the same tuple, and they came apart the moment a
repo declared a universal or repo-local source that is its own clone: its
branches were never looked at, and the report named no gap, because the
level test had already decided there was nothing there. The lesson is the
narrow one: **a constant that answers one question is not evidence about
another, however well it fits.** The tool asks every declared source now
and lets the one honest test — is this path its own git checkout — answer,
which it settles by looking; sources resolving to one clone are swept once.

**The same day, one more, and it was found by running the check rather
than reading it.** The sweep widened above could not actually reach the
repos it had just been widened to: in a session where the credential route
was working exactly as [INSTALL.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/INSTALL.md) §8 describes — all four
private sources cloned before the first turn — **every one of them failed
this tool's own freshness gate** with *"could not read Username for
`https://github.com`"*, and the run refused to read a line. The token was
fine. The tool's `_run_git` shelled out to plain `git`, while the
credential lives behind a helper only
[tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
was passing — so a source could be **cloned** at session start and then not
**fetched** by the check that reads it.

Two things are worth keeping from it. **The guard was right about the state
and wrong about the cause**, which is the expensive combination: a hard
refusal reads as the gate doing its job, and the message sent the reader to
re-set a token that was never the problem. The fetch failure now names
*which* failure it was, reusing the diagnosis the bootstrap tool already
had rather than growing a second copy. And **the fix went in `_run_git`
keyed on the git subcommand**, not at the three call sites that fetch
today: this sweep grew three new fetches in a fortnight, and a per-caller
fix covers whatever existed the day it was written
([durable-fix](durable-fix.md)).

**The generator check above came from a question, not a failure, and that is
worth saying plainly.** Morgan asked on 2026-09-11, after reading how a
brand-new adopter with no team or individual set gets one, whether that path
was tested here at all — and named the shape of what worried him: he updates
the files in his own sets over months while the generator that made them
keeps moving, and nothing would ever say the two had parted. It had not been
tested. Two checks looked adjacent and neither was: `verify()` asks whether a
real set still has every file the skeleton ships, and the template-freshness
scan asks the reverse for filenames — **both are about which files exist, and
between them they had never compared a single byte.** No incident is attached
because none happened; a gap can be found by reading, and
[cite-the-incident](cite-the-incident.md) asks for the real story, which here
is that somebody asked the right question before it cost anything.

**Its first real run, the same day, found drift in all four live sets and
also found the check too long to read.** Every set's vendored engine was an
older upstream vendoring, and `commit-identity.sh` differed from canonical
in every one — the drift [TODO.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md)'s `source-hook-drift` item
already tracks, confirmed here by a mechanism that knew nothing about it.
**The defect was the output.** A set vendored at an older commit differs in
*every* engine file at once, so one fact printed as a dozen findings: 60
lines carrying about six facts, which is how a check teaches people to skim
it. One older vendoring is now one row, absent files the engine gained since
folded into it, while a hand-edited file still gets its own line naming the
file — the distinction that decides whether you refresh or move the change
upstream. And `.claude/settings.json` moved from shape to owned: a set may
legitimately wire its hooks from somewhere other than `.claude/hooks/`, which
`verify()` already allows and one live set deliberately does, so calling that
drift reported a decision as a defect on every run.

## Install
[tools/very_deep_check.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/very_deep_check.py) enumerates the scope
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
[spec/UNBUILT_PLAN_ITEMS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/UNBUILT_PLAN_ITEMS.md) for the decision
record this practice's own build closes out.

Six parts of the check *are* mechanical, as far as a mechanical check can
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
patch-equivalent on that target. Sixth, the endgame merge is rehearsed: the
integration branch is merged into its base in a throwaway worktree (detached,
nothing committed, removed on every exit path), and the paths present on the
branch but absent from the result are reported separately from the
conflicting ones — `--skip-endgame-merge` to skip it, `--json` for the full
list rather than the first ten. It reports CANNOT TELL, never clean, when
the two branches have no common ancestor in this clone: an under-fetched
history yields an empty difference that reads exactly like a good result.
Its negative control is
[tools/verify_harness.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/verify_harness.py)'s
`check_endgame_merge_finds_the_silent_drop`, which plants one file of each
class and asserts *which path lands in which set by name* — a count would
have passed while reproducing the original miss
([control-asserts-which-failure](control-asserts-which-failure.md)).

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

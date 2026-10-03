---
title:         The ladder as an opt-in set
kind:          proposal
status:        accepted
opened:        2026-10-02
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The five-stage ladder (Consider, Act, Booked, Debut, Produce), its words, its release mechanics and its branch tiers move out of the universal set into an opt-in shared set, the ladder set, that a person brings through their own individual set. Everyone keeps the enforced practices and checks. A person not on the ladder lands on the repository's base branch with no tiers and no ladder language. Step 1, shipped first and on its own, fixes session start so every practice set's own universal clone is kept current."
---

# The ladder as an opt-in set

Morgan approved this plan on 2026-10-02 ("Go ... Let's do it, Act on the
plan!"), after a day of planning and four rounds of outside review by
another session. Every decision below is recorded with its strength. It is written
for a reader who was not there.

## Contents

- [The problem](#the-problem)
- [The goal](#the-goal)
- [The dividing line](#the-dividing-line)
- [Decisions](#decisions)
- [What gets built, in order](#what-gets-built-in-order)
- [Testing](#testing)
- [Rollback](#rollback)
- [How it was reviewed](#how-it-was-reviewed)

## The problem

Precedent loads rules from four layers: the universal set (this
repository), the shared sets a repository declares in
[precedent.json](../precedent.json), the person's individual set, and
repo-local practices.

The five-stage ladder (`promote`) is written into
the universal set, so it reaches everyone. That covers the stage words, the
"(step N of 5)" labels, the Boildown's step wording, the release commands
(`go-update` and its synonyms), and the three
branch tiers. A person who is not on the ladder finds the step numbers
confusing and experiences the ladder as enforced, though
[the plan that introduced it](FIVE_STAGES_AND_OUR_LANGUAGE_PLAN.md) called
it optional. Some people dislike branch tiers altogether: they work
elsewhere and push the finished version to the main branch.

## The goal

In Morgan's words (2026-10-02, condensed; strength: decided):
> We're going to make ladders the mechanics for me and my team. But for
> everyone else, they have very different preferences ... what the others
> like in Precedent is the forced practices and the enforcement of the
> practices. And so all of that will stay for everyone. But these very
> personal things, like a lot of the wording and forcing staging, is really
> just for me and my team.

So the ladder works exactly as it does now for anyone who opts in. Nobody
else gets any exposure: nothing mandatory, no ladder language, no release
mechanics and no branch tiers, unless the person brings the ladder set and
does not have No ladders on.

## The dividing line

Morgan's test (2026-10-02; strength: decided):
> We need to assume that NO ONE other than me and my team will use my own
> commands regarding pushing, pulling, integration, GitHub mechanics etc.,
> so if this is part of a command, then it should be in the shared ladder.

**The ladder set** holds the release mechanics: every command, or part of
one, about planning style, pushing, pulling, integration, releasing or
GitHub mechanics, and every rule that exists to serve one.

**The universal set** keeps the enforcement that runs on its own:
- the merge, review, push and reply gates, and the stop hook;
- the push checks by branch (a push to the base branch runs the full tier,
  and the GitHub test after);
- the light and deep checks, and
  [verify-postcondition](../practices/verify-postcondition.md);
- the Boildown, with a first bullet that names the branch only;
- the commands that are not about git: Drop it, Three Things, Simple
  please, Weak yes, Prompt Please (with a neutral stop line), Root issues,
  My options, Vocabulary;
- [Update Vendors](../practices/vendor-update-runbook.md), because it is
  how every consuming repository receives enforcement updates;
- [archive-status-check](../practices/archive-status-check.md), a
  no-lost-work check (it only loses its Booked wording).

The reviewer's sort of all 202 active practices, which this plan adopts:
- **Moves to the ladder set**, beyond the stage practices and the release
  cluster in D1: `chief-of-staff` (Morgan
  confirmed, 2026-10-02), and the retired stubs `go-merge`, `push-directly`,
  `merge-authorization-keyword` and `plan-it`.
- **Stays universal, with ladder wording removed:**
  - fresh-before-write, base-branch-is-the-record,
    never-delete-a-remote-branch and branch-delete-links;
  - disclose-landing, whose "three levels" are source levels and are never
    flagged;
  - pr-template-honest-gates, lease-in-flight-work, shared-result-cache,
    session-trailer, merge-runbook and no-rewrite-for-warnings;
  - the CI and GitHub-setup practices;
  - every other universal practice.
- **The shared sets:** nothing moves; their wording is fixed in place.
- **The individual set:** ladder-required and promote-only gain the
  "requires the ladder set" marker; two practices that link to go-update are
  repointed.

## Decisions

**D1. Content.** These move into the ladder set (a public shared set; this
repository never names it, per D14), rewritten as
shared text ("a person on the ladder"):
- **The stages:** consider, act, debut, produce and promote, with their
  synonyms.
- **The release cluster:**
  - go-update (Booked, Approved, Book it, Go update, Shared Save);
  - checks-follow-the-tier, tier-branch and primary-branch;
  - relayed-authorization (Morgan overruled keeping it universal,
    2026-10-02);
  - the local merge-target-is-beta-branch, and the AGENTS.md opening
    paragraph.
- **The plan sizes and the rest:**
  - brainstorm-holds-commits whole (word and behaviour), plan-it and
    write-it-up;
  - stage-word-carries-its-step, the read-back rules, and the step part of
    the Boildown first bullet;
  - the ladder's reply-check requirements and its glossary words;
  - the No ladders trigger, and the public explainer (D14).

Prompt Please's universal stop line becomes: "build it on a feature branch,
push it there, and stop; open no pull request and merge nothing unless the
person said to." There is no universal Release command.

**D2. Opt-in.** A `brings` list in the individual set's
`precedent-source.json`, as full repository URLs:
`{"name": "<the set's name>", "repo_url": "https://github.com/<owner>/<the set's name>"}`.
No repository ever declares the ladder set. The bootstrap, the declared-path
listing, the source refresh and the session check all learn to read
`brings`. The set is created with
[precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
(level shared, public), and Morgan is its sole approver.

**D3. Landing** (proposed by the reviewer; Morgan: "yes, your suggestion is
great", strength: decided):
1. **One setting:** the person's own `landing_branch`, defaulting to the
   repository's production branch: the branch a Promote moves into last
   (`main`). Not `base_branch`: a repository with tiers, BestPractice
   included, sets that to `staging`, so read literally it would land a
   person off the ladder on staging, the one thing they asked not to have
   (found reading this plan as a person off the ladder, 2026-10-02).
2. **Tier values only on the ladder:** a person may set any branch, but a
   tier value (pre-staging or staging) counts only while the ladder is in
   force. Otherwise it is ignored, never edited, and the session check says
   so once in plain words.
3. **The repository's value only for ladder users:** a repository's
   `precedent.json` landing value is read only for them. On the ladder the
   order is person, then repository, then pre-staging.
4. **No ladders:** tier values and `promote_only` are ignored the same way.

**A ladder user in a repository without tiers** (Morgan, 2026-10-02:
"Yes", strength: decided). A ladder user lands on pre-staging only where
the repository already has tiers, which its `precedent.json` declares.
Elsewhere they land on the production branch like everyone else, and
nothing creates tiers in a repository that did not ask for them. Read
literally, the order above would have created tiers in the repository of
someone off the ladder.

There is no migration. The tiers step in Update Vendors and
`ensure_repo_landing` run only for a person on the ladder. Off-ladder output
never mentions pre-staging or staging. Where the base branch is protected,
the off-ladder path is a pull request into it, and the checks run either
way. The cost of those checks on every off-ladder push is accepted
(strength: decided).

**D4. Engine.** `promote_only` and the Promote machinery stay in the engine
and run only for ladder users. Ladder lines print only when the ladder is
in force. Off-ladder output says plainly what happened and names the base
branch.

**D5. Helper.** One helper, `tools/precedent_ladder.py`, offers
`ladder_in_force()` and `say(ladder_text, plain_text)`, plus a bash entry
point (`--in-force`, an exit code cached per session) for the
freshness-guard, stop-git-check and push-check-gate hooks. About fifty
engine lines across ten tools and three hooks go through it.

**D6. Views.** [build_views.py](../tools/build_views.py) defers brought sets
to the untracked session file. It never writes them into a committed
AGENTS.md, MAP.md or index.

**D7. Check E.** Strict ladder tokens outside the ladder set fail:
- "step N of 5", "Promote N", and a stage name before "(step";
- capitalised quoted or bold commands: "Booked", "Debut", "Book it",
  "Go update", "Brainstorm", "Plan it", "Write it up";
- in engine output and plain-words documents only: "pre-staging", and
  "staging" used as a branch name.

The check covers rule-bearing surfaces only. Records (todo/, gotcha
stories, record/, spec/, git history) are exempt.

**D8. Session-check rows.**
- A loud row when a brought set failed to load.
- The person's session-load total against each repository's hard ceiling.
- The landing row from D3.

**D9. One release** for the ladder set, the ladder-free universal text and
the new landing rule. Step 1 ships before it, on its own.

**D10. Mixed repositories**, reusing `sync_pre_staging` ("drift from
above", 2026-09-26):
- Off-ladder work lands on the base branch.
- A ladder user's Promote already copies new work on main and staging down
  into pre-staging, once the upper tip has passed its checks.
- **Red main** (Morgan, 2026-10-02, strength: decided, ladder users only):
  - Debut stops waiting on main's GitHub test.
  - Promote and Debut still carry the ladder user's own work up to staging,
    and say plainly that main's latest work was not brought down, and why.
  - Produce waits until main's test passes (new code).
- **Conflicts:** when an off-ladder push conflicts with ladder work, the
  ladder user's own session resolves it; the person who pushed is never
  asked.
- The drift messages are reworded plainly.
- **Main's work always comes down** (Morgan, 2026-10-03, strength:
  decided: people off the ladder pushing straight to main is expected and
  goes on, so the ladder deals with it at the root). It replaces the two
  red-main lines above:
  - Every Debut takes main's new work, whatever main's own checks say.
    What gets judged is the tree it makes with the ladder's work (built as
    the composition below, which replaced a first version that merged it
    into pre-staging on the basic check alone). Holding main's work out waited on a fix from
    someone off the ladder, while pre-staging drifted and the next Produce
    met the conflict: on 2026-10-03, two direct commits left main red on a
    stale generated page, and nothing on the ladder could take them.
  - A conflict only in generated files (a `generated_by:` header, or a
    page `doc_html.py` renders) is rebuilt by each file's own generator from
    the merged sources. A conflict in hand-written text still stops.
  - Produce is held by a red main until staging both carries main's tip
    and that staging tip has passed the full local check, so the repair is
    checked first, never taken on trust (Morgan: "Should it check this
    first?"). Then the Produce goes ahead, since it is what brings main back
    to green, and its own pull request's GitHub test is still the last gate.

- **The Debut composes, checks once, then moves both tiers** (Morgan,
  2026-10-03, strength: decided; built 2026-10-03 in `_promote_unlocked`,
  [tools/precedent_branches.py](../tools/precedent_branches.py); it
  supersedes the "pushed anyway" step of the bullet above):
  1. In a scratch worktree: start from staging, merge main's new work,
     then pre-staging's. A conflict only in generated files is rebuilt by
     its own generator.
  2. Before checking, rebuild every generated file that main's new commits
     touched, with its own generator -- the mechanical repairs (a stale
     render, a map, an index) that most off-ladder pushes need.
  3. One full check on the composed tree.
  4. Pass: staging and pre-staging both move to that exact commit, level.
  5. Fail: neither tier moves. The composed tree is pushed to a fix branch
     and the Debut reports "not finished": what failed, and that it came
     from main where it did. The session fixes it on that branch in the
     same turn -- never deferred, never "main is not mine" -- and reruns the
     Debut with that branch as its work, which lands the fix and finishes.
     The ladder set's `debut` rule says so.
  6. A conflict in hand-written text takes the same route: resolved on the
     fix branch, then the Debut is rerun.
  Pre-staging therefore only ever receives a composition that passed.

  **Where it lives** (Morgan, 2026-10-03: "the change we just discussed is
  for the ladders repo, just part of the ladders process"; he then picked
  this of two options, strength: assented): the rule is the ladder set's
  `debut` and `promote`; the mechanism is in the Promote tool those rules
  call, because only a Debut runs it, so nobody off the ladder meets it.
  Moving the code into the ladder set was the other option, a restructuring
  of its own, since the shared push and landing checks use the tier code.

  **Small calls made building it** (the session's, said here so they can
  be reconsidered):
  - The quick sync (`--sync-pre-staging`, run at Booked) no longer takes
    main's work at all, checked or not: it says it is left for the next
    Debut. Taking it there on the basic check is what the sentence above
    rules out.
  - Step 2 runs every generator the tree uses that rebuilds when run bare
    (`REBUILT_BARE`: build_views, build_gotcha_index, build_todo_index,
    doc_html), not only for files main's commits touched: on 2026-10-03
    main's commits changed a source and not its render, so "touched" would
    have missed the very file that was stale. On a consistent tree they
    change nothing; a render whose only change is its build time is put
    back. [very_deep_check.py](../tools/very_deep_check.py), which also writes a generated file, is never
    run this way (run bare it is the very deep check), and a conflict in
    its file counts as hand-written. That limit applies to the conflict
    rebuild too, which had no such limit before.
  - The report on a failure names main's commits as the place to look
    first, from what is on record (staging's own recorded pass), and never
    says which side caused it. A first version settled that with a second
    full check on staging plus main's work alone: in the rehearsal on a copy
    of this repository's tiers the two checks took about 24 minutes, past
    the Promote lock's 15, and it blamed main for a test that failed on
    staging's own tip in that container. The session measures it on the fix
    branch instead, where running only what failed on each tip takes
    seconds (practice: diagnosis-is-measured).
  - The fix branch is `promote-fix-DATE`; only a branch so named is taken
    in through `--work`. Any other `--work` not on pre-staging is named and
    left for Booked, so a Debut never carries unbooked work.
  - Both tiers move in one atomic push. If pre-staging gains work while the
    check runs, nothing moves and the Debut says to run again.

**D11. Composition.** The universal first-bullet rule stays prefix-only, with
neutral wording, and the ladder set adds the step requirement.

**D12. Vocabulary from everywhere** (Morgan's change, 2026-10-02):
- [precedent_vocabulary.py](../tools/precedent_vocabulary.py) reads every
  source in force for the person, brought sets included, and merges an
  optional `our_language.json` from each set.
- It prints one integrated list each for commands and words, every row
  tagged with its source.
- On a clash, the higher-precedence set wins and both sources are shown.
- Committed glossary views render from universal only.

**D13. No ladders.** The off-ladder test is a fresh session.
- **The switch:** an environment variable, `PRECEDENT_NO_LADDERS=1`, read
  at session start and by the helper, drops the ladder set and the
  individual practices that require it.
- **What changes:** landing reads the base branch (D3.4), and the push
  gate refuses every push with "this is an off-ladder test session; nothing
  is pushed".
- **Where:** in the cloud, a second environment with the variable set; on a
  local machine, the variable itself or a user-config field.
- **Why not a switch inside a running session:** it cannot unload text the
  session already read. A switch committed to the individual set would only
  take effect after a Promote.

**D14. Documents.**
- **(a)** A public explainer in the ladder set, for people who are not
  developers.
- **(b)** Every universal and other-shared-set document is rewritten
  without ladder, release or tier terminology, with no link to the
  explainer. INSTALL.md documents `brings` generically. Records stay as
  history.

**D15. Allowance.** The ladder set's index allowance and resident cap are
carved out of universal's, measured after the move, so a ladder user's total
does not change.

**D16. Setup.**
- Add the leak-blocklist allow line for the new set.
- Run Update Vendors in the individual set before the `brings` line goes in.

**D17. Refresh every practice set's own universal clone** (Morgan: "the root
fix should be a part of this also"). Step 1, already built. See
[the gotcha](../gotchas/gotcha-2026-10-02-a-practice-sets-own-universal-clone-was-never-pulled.md):
- session start syncs the sources each attached set declares, through the
  same fast-forward-only sync;
- it pulls only clones the tool made, and skips the session's own project;
- it pins an existing universal clone to its manifest branch;
- it re-renders a set's session file when a source it reads moved;
- the session check names an attached set's universal clone.

## What gets built, in order

The figures are session-hours, from the reviewer's sizing.

| Step | Work | Size |
|---|---|---|
| 1 | D17, tests first; ships on its own | 2-3 (built, with its adversarial pass) |
| 2 | Fixture profiles plus an untracked real-profile baseline | 1-2 (built) |
| 3 | Helper, bash entry point, `PRECEDENT_NO_LADDERS` | 1-2 (built) |
| 4 | `brings` in the four tools, the build_views deferral, and a `--withdraw-from-universal` mode for [precedent_move.py](../tools/precedent_move.py) (deletes the universal copy, keeps the Story in the set, records the deliberate withdrawal once) | 4-6 (built) |
| 5 | Create the set; move D1 with the move tool; split the reply check; carve the allowance; set glossary | 5-6 (built) |
| 6 | Engine strings, hooks, templates, gotchas, the universal files and links that name moved practices, and the D14(b) documents | 5-7 (built) |
| 7 | D3 landing, the gated tiers step, and D10's drift wording and red-main rule | 2-3 (built) |
| 8 | D14(a) explainer | 1-2 (built) |
| 9 | Vocabulary (D12) | 1 (built) |
| 10 | D8 rows | 1 (built) |
| 11 | Check E, and D18's check | 2-3 (built) |
| 12 | No ladders | 1 (built) |
| 13 | Rollout: Update Vendors in the individual set, then `brings`; every repository through the ladder; each consumer's Update Vendors, then `--mentions-only` and Check E; the behavioural eval | 2-3 |

**Every step gets an adversarial pass before its Booked** (Morgan,
2026-10-02, strength: decided). Each pass covers:
- **People off the ladder:** what they see, what they are warned about, and
  what they try that conflicts with the change.
- **Ladder users:** whether everything still works as before.
- **Broken and offline layouts.**
- **Old against new:** the old engine and the new one run side by side on
  the same layouts, and anything new said to a person off the ladder is a
  finding.

Every guard is shown failing with its fix removed. The cases that matter go
into [verify_harness.py](../tools/verify_harness.py) in the same commit, so
the next step's run includes them. Step 1's pass ran 38 scenarios and
added two harness checks; it found and fixed three faults:
- a universal clone sent to staging when a set had no engine manifest;
- a clone that could not be refreshed staying silent;
- a broken set printing a garbled line.

Steps 4 to 9 ship together (D9). Before the move in step 5, the engine
comments that cite a moved practice as `practice: <slug>` are reworded, or
the move tool refuses.

### What building steps 5 to 12 settled

- **Rollout order.** The ladder set's `main` must hold its rules, and the
  individual set's `main` must carry the `brings` line, before
  BestPractice's release reaches `main`. In the other order the person who
  uses the ladder loses it until they catch up: their sessions read the
  individual set's `main`, and universal no longer has the rules.
- **The other shared sets.** Their vendored word list and generated MAP
  still carry ladder words until each takes the new engine with Update
  Vendors; two lines of their own were reworded on a branch.
- **`PRECEDENT_ASSUME_LADDER`** is a test-only switch the harness sets, so
  its older checks keep testing ladder behaviour. No session sets it, and
  `PRECEDENT_NO_LADDERS` wins over it.
- **Deleting a universal rule** is registered in
  `process/decommissioned_paths.json`, which the deep check's
  practice-change and link checks now read, so a deliberate withdrawal is
  not reported as a dangling change.
- **The move tool kept only the first line of a rule's approval**, and
  replaced it on a duplicate. It now keeps the whole approval, quoted
  safely, and a withdrawal says the universal copy is gone. The fourteen
  rules moved here were repaired from history, each checked against the
  original.
- **A No ladders session pushes and merges nothing**: the push and merge
  gates refuse it by name.
- **The red-main rule** (D10) is built. A Debut takes main's GitHub test
  as it stands: main's newer work comes down only if that test already
  passed on it, and otherwise the Debut says so, never starts or waits on
  the test, and carries the person's own work up to staging. A Promote
  into main waits while main's own test is running and refuses while it
  is failing. Before this, a Debut could wait up to half an hour for
  main's test, and a move into main went ahead on a red main.

### What the adversarial pass after steps 5 to 12 found

Four personas ran the same commands in BestPractice: the person who brings
the ladder, a colleague with an individual set of their own, a person with
none, and a No ladders session. Committed views came out byte-identical
for all four. The colleague and the person with none saw no ladder word in
any gate, reply rule, Vocabulary, landing line, branch view, push-check
listing, session check or session file. The ladder user's gates, reply
rules and Vocabulary match the baseline taken before the work, with
`no-ladders` added, and the total they load fell slightly. Faults found
and fixed, each with a harness case shown failing without its fix:

- **Path rules from outside the repository never fired.**
  `precedent_paths.py` read the repository's `practices/` alone, so a path
  rule in a person's individual set, a set they bring, or a set a practice
  repository declares, never reached a session. `checks-follow-the-tier`
  stopped reaching its ladder user when it moved. It now adds every rule in
  force from outside, through the resolver.
- **A Promote in a repository with only main** announced a move, failed,
  and left its lock branch on origin. It now says there is nothing to
  promote and touches nothing.
- **In a private repository, a brought rule counted as reachable by
  nothing**, since only public repositories counted the session file. It
  counts wherever that file is wired.
- **A harness fixture read the real person's configuration**, so its
  count changed with whoever ran it; it owns its state now. Two test stubs
  predated the code they stand in for and were brought up to date.

The final round, on the finished tree, found two more, fixed the same way:

- **The staging watch reached a colleague.** Its off-ladder silence sat in
  its command line only, and the reply gate calls it directly, so a
  colleague was told who had pushed to staging. Every entry point asks now.
- **A reworded warning broke the code that read it.** `precedent_check.py`'s
  size-cap warning was made plain, and the push check went on matching the
  old words, so its closing reminder never fired. It matches both now, and
  says nothing about tiers to a person off the ladder.

Not this work's, found on the way: on this machine the default-blocklist
check fails on `pre-staging` too, because the sibling practice sets are
cloned here. And the resolver's self-heal ran the individual-source hook
for any config that did not exist, so every fixture naming a config of its
own put the real individual clone back on its pinned branch; it now stands
aside for a config named outside `$HOME`
([the gotcha](../gotchas/gotcha-2026-10-02-a-config-named-for-a-test-reset-the-real-individual-clone.md)).

**The rehearsal before Produce** (2026-10-03, Morgan asking what else
could be tried before the release, strength: assented). Each practice set
took staging's engine in a scratch copy, the way every session start takes
it once it reaches main, and ran its own full check. Four passed. The
individual set of the person who brings the ladder failed: Check E skipped
a set that provides the ladder but not an individual set that brings one,
so it refused four lines of that person's own rules, and with them their
next Update Vendors. It now stands aside for an individual set whose
brought set provides the ladder, and still runs when that set is not
cloned. Not this work's, found the same way: the refresh refused a file
carried by hand to match upstream exactly, as if it were an edit
([the gotcha](../gotchas/gotcha-2026-10-03-a-file-carried-by-hand-to-match-upstream-held-every-refresh-up.md)).

**D18. The ladder is brought, never declared** (Morgan, 2026-10-02, asking
how two people in one repository can differ). A repository's
`precedent.json` binds everyone who works there, so a set that provides
the ladder is never listed in one; each person brings it from their own
individual set. The check `ladder-set-is-brought-not-declared` refuses a
`precedent.json` that declares one.

## Testing

**Profiles,** built with `PRECEDENT_USER_CONFIG` and fixture sets, never
from a real profile:
- P1, a ladder user;
- P2, off the ladder, with no individual set;
- P3, off the ladder, with a tier value set;
- P4, P1 with No ladders on;
- P5, P1 with the ladder set unreachable;
- P6, P1 and P2 sharing one fixture repository with a local bare origin.

**What is asserted:**
- **A.** P1 matches the untracked baseline, except for listed differences.
- **B.** P2, P3 and P4 see zero strict tokens on any surface.
- **C.** Nothing is mandatory off the ladder:
  - landing is the base branch;
  - the ladder practices are not in force;
  - a push to the base branch runs the full tier with plain messages;
  - P3's tier value is ignored and reported once.
- **D.** P1 is still refused without the step wording.
- **E.** Committed views are byte-identical whoever regenerates them.
- **F.** P5 shows the loud row; this is also part of the release check.
- **G.** P4 refuses every push, and its landing reads the base branch.
- **H.** Installs by P2 create no tiers.
- **I.** P1 stays under every session-load ceiling, in the individual set
  and in BestPractice.
- **J.** The allowance check passes for P1 and P2, and the carve leaves
  P1's sum unchanged.
- **K.** Vocabulary shows P1 everything, tagged, and shows P2 no ladder
  rows.
- **L.** A behavioural eval, in auto mode, once per release.
- **M.** The documents pass Check E.
- **N.** In P6:
  - P2's pushes to main reach every tier, and nothing is lost;
  - P1's author and date checks pass after the copy-down;
  - with main red, P1 reaches staging and Produce waits;
  - a push landing mid-Produce is caught.
- **O.** For D17, the harness checks `check_attached_sets_sources_are_synced`
  and `check_attached_sets_sync_is_safe_for_everyone` in
  [verify_harness.py](../tools/verify_harness.py).

**Scenarios a person off the ladder will try,** each covered by some step's
adversarial pass:
- they say "Promote", "Booked" or "push this to staging";
- their own settings name a tier;
- they run Update Vendors in a repository where a ladder user works;
- they push to main while a ladder user's Promote holds the lock;
- they work in BestPractice itself, whose `base_branch` is staging;
- they read a ladder user's Promote pull requests and branch names.

Two more checks:
- **Session-start output:** what a person off the ladder sees, old engine
  against new, is identical except for listed lines.
- **Auto mode:** a plain "commit and push it" reaches main.
- **The rehearsal:** before each Produce of this work, every practice set
  takes staging's engine in a scratch copy and passes its own full check,
  and every consumer reachable runs a full Update Vendors against a
  BestPractice whose main is staging, then its own full check. A consumer
  renders with [precedent_sync_views.py](../tools/precedent_sync_views.py), not `build_views`, so the sets'
  rehearsal cannot stand in for it
  ([the open item](../todo/todo-2026-10-03-consumer-rehearsal-before-the-ladder-produce.md)).

## Rollback

If the `brings` loader fails after the release, a ladder user loses the
ladder with no other warning than test F's row. The revert is BestPractice
`main` back by one Produce; the ladder set is left untouched.

## How it was reviewed

Four review rounds by a separate session, each checked against the code at
the time. Its main corrections:
- committed fixtures would have published private set text;
- a staging default would have slowed every off-ladder save;
- the copy-down of main into pre-staging already existed;
- the move tool needs a withdrawal mode;
- the refresh must skip a session's own working copy.

Building D17 turned up a fourth bug the reviews had not: an existing
universal clone was synced onto the universal repository's own working
branch, not the main its manifest pins.

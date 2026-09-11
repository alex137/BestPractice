# TODO — open items for BestPractice itself

Dependent repos keep their own TODO.md (from
[templates/TODO.md.template](templates/TODO.md.template)); this one tracks
the upstream layer. Ordered by priority.

**Cite an item by its anchor, never by its number.** Every item carries an
`<a id="...">` slug; the visible number is reading-order furniture that
shifts whenever anything is added, reordered, or struck through. Three
documents had already cited items as "TODO.md item N" (found 2026-09-06),
which is the failure this repointing exists to end — write
`[TODO.md's \`slug\` item](TODO.md#slug)` instead.

1. <a id="actions-as-enforcement-layer"></a>**Lean further into GitHub Actions as the enforcement layer.** The
   markdown-lint workflow ([GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)) proves
   the pattern: checks run in CI, so they bind every contributor — human,
   Claude Code, ChatGPT, anyone — regardless of whether the agent has a
   shell. Candidates to add: [practice_audit.py](tools/practice_audit.py)
   (manifest drift + scrub gate) as a required PR check; a deck-build
   check when deck sources change; a check that flags agent-authored
   commits on PR branches (attribution convention). Field evidence
   (2026-08, a dependent repo's first member PRs): merges made through
   the GitHub web UI, so the merge-runbook gates — capture, export,
   audits — never ran, and every commit landed authored as the agent.
   Runbook gates bind only sessions that run the runbook; required CI
   checks bind every path to the default branch.
2. <a id="github-issues-for-open-items"></a>**Evaluate GitHub Issues for open items.** Mirroring or replacing
   TODO-file items with Issues would let shell-less assistants and phone
   users browse, discuss, and close work items natively. Needs a
   convention for keeping Issues and the repo-is-the-memory principle
   consistent (an Issue is not on `main`).
3. <a id="plain-chatgpt-write-support"></a>**Re-verify plain-ChatGPT write support.** As of 2026-08,
   [MOBILE.md](MOBILE.md) treats writing (branches, file updates, PRs)
   from a plain GitHub-connected ChatGPT conversation as not reliably
   available and documents a split workflow instead. Re-test when
   OpenAI's connector capabilities change, and update MOBILE.md either
   way.
4. <a id="grok-workflow"></a>**Verify a Grok workflow.** Untested as of 2026-08 — see
   [MOBILE.md](MOBILE.md). If Grok gains repository access, the universal
   starting instruction should apply unchanged; verify and document.
5. <a id="companion-mobile-app"></a>**Companion mobile app, if the Shortcut proves insufficient.** The
   iPhone Shortcut and text-replacement setups in
   [MOBILE.md](MOBILE.md) approximate a Claude-Code-like entry point for
   ChatGPT users without custom development. If they prove too clumsy in
   practice, a small companion app (pick repo → type task → open
   assistant with the bootstrap prompt) is the next step — noting that
   this is real app development, not documentation.
6. <a id="out-of-chat-notifications"></a>**Out-of-chat change notifications for members.** In-chat catch-up is
   now a convention (the instructions template's session-start
   catch-up), but a member who hasn't opened a session learns nothing.
   Evaluate a GitHub Actions job that emails a plain-language digest of
   merged changes (or leans on GitHub's built-in Watch notifications,
   documented in the members' page) — as of 2026-08, unexplored.
7. <a id="multiple-team-sources-disagree"></a>**Define what happens when a consumer repo imports multiple `team`
   sources that disagree.** See PRACTICE_ENGINE_PLAN.md's `## Deferred`
   section (added 2026-09-03, alongside that session's precedence reorder)
   for the detail — not duplicated here. **Half-closed 2026-09-06**: the
   *silent* case is gone. Two team-level sources claiming one slug used to
   resolve to whichever `precedent.json` listed second, reported only as an
   ordinary `overridden:` notice on stderr — indistinguishable from a
   legitimate higher-level override, and decided by config file order.
   [tools/precedent_resolve.py](tools/precedent_resolve.py) now fails
   loudly there, which is what PRACTICE_ENGINE_PLAN.md said it did all
   along ("the resolver fails loudly if two same-level practices claim one
   slug"). Two team sources that do NOT collide still resolve together,
   with a harness case each way. What is still open is the *design*
   question the plan defers: whether a consumer should be able to express a
   preference between two teams at all, rather than being told to rename
   one. Revisit when a real multi-team-import case appears — a second team
   set now exists (`precedent-team-tms`, 2026-09-05), so that is closer
   than it was.

   **The real case appeared 2026-09-07, twice in one day, and was resolved
   by removing the collision rather than answering the question.** Two
   sessions independently landed `fail-gracefully` and `bold-key-phrases`
   into *both* team sets, each doing the obviously right thing. Confirmed by
   running it: `precedent_resolve` raised `ResolveError` — *"nothing orders
   two sources at the same level, so there is no answer to which one wins"* —
   so any repository declaring both team sources could not resolve at all.
   Nothing was broken in practice, because no repository declared both.
   Morgan's decision was to promote both to universal and delete them from
   the team sets, which is right when the rule is genuinely shared: two
   teams wanting the identical rule is what a universal rule looks like.

   **That does not answer this item, and the two must not be confused.**
   Promotion works only while the teams want the *same* rule. The open
   question is the same slug meaning *different* things to two teams, and
   every remedy available today is a workaround for it:

   - **Rename one** — cheap, and wrong as a habit: the slug is the identity
     a session searches by, so two names for one concept is the folklore
     problem relocated.
   - **Retire one** — only honest when one team was wrong.
   - **Move one to another level** — there is no level below team except
     repo-local, which does not reach a team's other repositories.
   - **Promote** — requires the rule to be genuinely shared, as here.

   So a rule two teams both want, differently, still has no home. Options
   worth weighing: an explicit tie-break a *consuming* repo declares (it
   knows which team it belongs to, which neither source does);
   source-qualified slugs at the point of use; or accepting the refusal and
   requiring that no repository declare two team sources.

   **Blocked on:** nothing but a decision about what shape the answer takes.
   Parked deliberately at Morgan's request, 2026-09-07 — do not design it in
   passing.
8. <a id="reduce-github-dependency"></a>**Reduce GitHub dependency when ready.** The layer itself is plain git
   + markdown + Python; GitHub specifics are the worked examples (PRs,
   Actions, Issues, branch rulesets). When priorities allow, document
   Gitea equivalents (Gitea Actions is workflow-compatible; Issues and
   branch protection have counterparts) so a repo can move hosts without
   losing the practices. Deliberately below the Actions/Issues items
   above: deeper GitHub integration now is acceptable, since equivalents
   can be added later.
9. <a id="prefork-catalogue-audit-table"></a>~~**The pre-fork catalogue audit table.**~~ **Done (2026-09-03).** One   row per inherited practice, verdict against this plan's architecture,
   plus whether Alex needs to hear about it:
   [spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md).
10. <a id="individual-practice-scoping"></a>**`for_team:`/`in_repos:` individual-practice scoping.** Fully designed
    in [PRACTICE_ENGINE_PLAN.md's Deferred section](PRACTICE_ENGINE_PLAN.md#deferred-speculative--do-not-build-yet),
    correctly not built yet. **No longer blocked** (noted 2026-09-06): the
    stated blocker was "a real second team's private set existing to test
    `for_team:`'s conflict rule against", and `precedent-team-tms` has
    existed since 2026-09-05. It is now an ordinary open item — build it
    when it is worth building, and don't re-derive the design judgment,
    which is already made.
11. <a id="additionalcontext-reaches-the-model"></a>**Confirm `additionalContext` actually reaches the model, not just the
    transcript.** The new `PreToolUse` hook
    ([templates/harness/claude-code/hooks/precedent-paths.sh](templates/harness/claude-code/hooks/precedent-paths.sh),
    [`spec/LOADER.md`](spec/LOADER.md#the-pretooluse-hook-and-what-is-confirmed-versus-assumed))
    uses the documented `hookSpecificOutput.additionalContext` shape to
    surface matched practice Rules before an edit, but the public Claude
    Code hooks reference doesn't state *(as of 2026-09-03)* whether that
    field is delivered into the model's own context for that turn versus
    only shown to the human in a transcript. `check_pretooluse_hook_fires`
    in [tools/verify_harness.py](tools/verify_harness.py) proves the
    wrapper produces the right shape; it cannot prove delivery. **Test
    plan**, recommended rather than run here (needs a live Claude Code
    session with this hook installed, which this session doesn't have):
    install the adapter in a real project, ask the session to edit a file
    matching a narrow-scoped on-demand practice's `applies_to` glob (e.g.
    a `tools/**` file for `code-cites-practice`), and check whether the
    session's own next reply cites that practice's Rule *unprompted* —
    something it could only do if the hook's context actually reached it,
    since the practice is on-demand and not otherwise in view. A clean
    negative result (the session never mentions the practice across
    several such edits) is itself the answer, and should be recorded here
    either way rather than left unconfirmed indefinitely.
12. <a id="routing-audit-silent-drop"></a>~~**Investigate why `routing-audit` fell through, audit the plan for    other silent drops.**~~ **Part 1 done (2026-09-04)** — root cause and
    scan for other drops in
    [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md)'s "Part 1,
    answered" section; the one adjacent gap it found is [`wire-the-very-deep-check-list`](#wire-the-very-deep-check-list) below.
    **Part 2 (pre-register and run a real evaluation of the two new audit
    mechanisms before trusting their output) is pre-registered and run
    twice** —
    [evals/routing/PREDICTION_AUDIT_JUDGMENT.md](evals/routing/PREDICTION_AUDIT_JUDGMENT.md)
    and
    [_RUN2.md](evals/routing/PREDICTION_AUDIT_JUDGMENT_RUN2.md) — each a
    smaller single-session eval than the routing eval's own multi-run
    discipline; see [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md)'s
    dated 2026-09-04 and 2026-09-05 sections for both results (6/6 and 6/6
    once run 2's own pre-registration error was corrected in the write-up)
    and their stated caveats. Run 2 also found a real gap in run 1's own
    `parallel-artifact-ledger` fix (a ledger with no audit backing it) —
    fixed the same session, `tools/precedent_check.py`'s new
    `parallel-artifact-ledger` check. Left open: both documents' own read
    that two 6-case runs are a stronger signal than one but still not a
    replacement for the routing eval's fuller multi-run discipline, if this
    ever needs to be trusted at higher stakes than an on-demand backstop.
13. <a id="retire-merge-target-practice"></a>**Retire [local/practices/merge-target-is-beta-branch.md](local/practices/merge-target-is-beta-branch.md)
    (and its check at
    [local/tools/checks/check_merge_target_is_beta_branch.py](local/tools/checks/check_merge_target_is_beta_branch.py),
    and the pointer in [AGENTS.md](AGENTS.md)'s opening paragraph) the
    moment Alex reviews and merges `precedent-beta-v01` into `main` for
    real.** Delete the practice file, delete the check script, and remove
    the [AGENTS.md](AGENTS.md) pointer, all in that same PR. (The check
    moved out of [tools/precedent_check.py](tools/precedent_check.py) on
    2026-09-06 — it is vendored into every consuming repo, and a check
    about THIS repo's own beta branch has no business running in
    somebody else's. Retiring it is now deleting two files, not editing
    the shared engine.) **Blocked on:** Alex's review
    and approval of `precedent-beta-v01` for the real phase-7 merge into
    `main` — not something to anticipate or do early.

    **What that merge will actually look like, rehearsed 2026-09-07 in a
    throwaway worktree and thrown away.** Two things worth not
    re-deriving under time pressure:

    - **Expect ≈125 conflicting files, and read them as divergence rather
      than damage.** `main` is still the pre-restructuring tree and lacks
      roughly 84,000 lines, so on nearly every one of them `precedent-beta-v01`
      is the correct side. The count is a snapshot and will drift — beta
      moved twice during the hour this was measured — but the shape will
      not. Newer work merges cleanly precisely because `main` has never
      seen it: of everything `philosophy/` and its repo-local practices
      added, only [tools/routing_scope.json](tools/routing_scope.json)
      conflicted.
    - **The revert trap DOES fire. This bullet said the opposite until
      2026-09-07, because the rehearsal behind it sampled the one class of
      file that survives.** `main` merged PR #89 and then reverted it
      (`97ed078`); `precedent-beta-v01` merged *the same branch* as PR #91.
      Those commits are therefore ancestors of **both** branches, with
      `main` holding the later revert — the textbook setup for content
      silently failing to come back at merge time. The consequence is that
      `1ff6a7e` is the merge base, so a merge replays only what this branch
      did after 2026-09-03 and takes `main`'s deletion for everything
      older. **Two classes of file come out of that, and only one is
      visible.** A file this branch touched again since the merge base
      conflicts (`modify/delete`) and stops the merge — that is the ≈125
      above. A file it has *not* touched since presents no change from this
      side at all, so git has no disagreement to report and applies the
      deletion **silently**. Re-measured 2026-09-07 against `e8341e2`:
      **507 of this branch's 893 files are absent from the merge result
      with no conflict raised** — 496 under `evals/`, plus
      [templates/leak-blocklist.txt.template](templates/leak-blocklist.txt.template),
      [templates/hooks/pre-push](templates/hooks/pre-push),
      [tools/section_split.json](tools/section_split.json),
      [tools/practice_metadata.json](tools/practice_metadata.json),
      [decisions/README.md](decisions/README.md),
      [decisions/2026-09-01-relax-private-repo-isolation.md](decisions/2026-09-01-relax-private-repo-isolation.md),
      [.github/ISSUE_TEMPLATE/practice-candidate.md](.github/ISSUE_TEMPLATE/practice-candidate.md)
      and the four files under
      [examples/practice-set/](examples/practice-set/). **The miss is worth
      understanding, because the next rehearsal will be tempted to repeat
      it**: the earlier pass checked
      [tools/routing_audit.py](tools/routing_audit.py) and
      [practices/routing-audit.md](practices/routing-audit.md), which this
      branch touched 3 and 4 times since the merge base. They are in the
      surviving class by construction. Sampling files a rehearsal has
      recently worked on selects for exactly the files that cannot fail —
      the question is only answered by diffing the whole merge result
      against this branch's tree.
    - **The merge to run instead, measured the same day at zero
      conflicts.** Branch off `main`, revert the revert, then merge:
      `git checkout -b phase-7-merge main`, `git revert 97ed078`,
      `git merge precedent-beta-v01`. That came back **0 conflicts and a
      tree byte-identical to `e8341e2`** — an empty `git diff` against this
      branch. Opening *that branch* as the pull request is what keeps the
      un-revert off `main` until Alex approves: both commits arrive
      together in one merge, so `main` flips from no-Precedent to
      all-of-Precedent exactly once, at the moment he says yes. A straight
      `git merge precedent-beta-v01` onto `main` is the move to avoid.
    - **The same trap points the other way, and that half is live now
      rather than at phase 7.** Merging `main` into `precedent-beta-v01` —
      an ordinary-looking "sync the branch with main", which any session
      might reach for — raises the same 125 conflicts and silently deletes
      the same 507 files *from this branch*. Measured 2026-09-07:
      `evals/` went from 623 files to 127, and
      [decisions/README.md](decisions/README.md) vanished, with no conflict
      and no message for either. Nothing on this branch needs that merge
      before phase 7; `main`'s only three commits since the merge base are
      the bad merge, the revert, and the revert's own pull request merge,
      so there is nothing there to want.
14. <a id="nontechnical-contributor-access"></a>**Run the non-technical-contributor access plan for real.**
    [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
    is drafted but not executed — it doubles as item 9's neighbor,
    [spec/PHASE6_BRIEF.md](spec/PHASE6_BRIEF.md)'s still-open item 4 (the
    first end-to-end rehearsal of INSTALL.md §0). **Blocked on:** a real
    person and repo to run it against, and Morgan adding the GitHub
    collaborator role by hand (no tool in this repo's GitHub toolset
    creates a collaborator invite).
15. <a id="team-repo-and-document-template"></a>~~**Build the team practice repo and reusable document-project template    for document work.**~~ **Done (2026-09-05)** —
    [spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md](spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md)'s
    Steps 1-2 executed: `themorgan/precedent-team-tms` bootstrapped per
    [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md) (empty of
    real practices by design — Morgan named the repo, `approvers.json` seeds
    Morgan as first approver) and pushed, and
    [templates/document-project/](templates/document-project/)
    added here. Step 3 (the plan's own boundary) deliberately not done — see
    item 16.
16. <a id="document-project-pilot"></a>**Run the document-project pilot once Morgan has a real first
    project.** Item 15 no longer blocks this — the template and team repo
    are real. Deliberately not planned further than that: see
    [spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md](spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md)'s
    "Sequencing" section for why a pilot project and person are not invented
    ahead of a real one existing. **Blocked on:** a real subject and a real
    person, neither of which exists yet.
17. <a id="wire-the-very-deep-check-list"></a>~~**Enumerate and wire the inherited RepoPersonalPreferences (RPP) "very deep check" audit list as    an on-demand tool.**~~ **Done (2026-09-05)** — a session holding
    [RepoPersonalPreferences](https://github.com/themorgan/RepoPersonalPreferences)
    answered the redundancy question first: `full-practice-audit` asks,
    practice by practice, "is this Rule satisfied" — a closed question
    against one document's own text — while RPP's list asks whether the
    repo's *own writing*, taken as a set, still holds together
    (contradictions, stale cross-references, repeated rules, formatting
    drift, and the like), which no per-practice sweep can see. **Not
    redundant**, so it was built:
    [practices/very-deep-check.md](practices/very-deep-check.md) plus
    [tools/very_deep_check.py](tools/very_deep_check.py), same pattern as
    `routing-audit`/`full-practice-audit` (an on-demand practice file, an
    enumeration-only engine, never wired into a gate). The enumeration also
    found something nobody had connected: the same day's earlier phase-3
    migration (v27) had already carried RPP's list into
    `precedent-team-maintainers` as its own `deep-check` practice, hours
    before v28's "not yet inventoried" was written — so the list was never
    actually missing, only unrecognized as fulfilling this commitment, and
    left with no companion engine and no reach outside that one private
    team set. Full record, including what this means for
    `precedent-team-maintainers`'s own `deep-check` (a team-level call, not
    decided here): [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md)'s
    "Part 1, answered" section.
18. <a id="ledger-root-commit-exemption"></a>~~**`parallel-artifact-ledger`'s root-commit exemption doesn't cover a    family's own inception commit.**~~ Found 2026-09-05: `_parallel_artifact_ledger`
    in [tools/precedent_check.py](tools/precedent_check.py) excludes the
    *repository's* root commit (`git rev-list --max-parents=0`) from needing
    a ledger row, but not the commit that first created a given family's
    member directories — [`f2078d6`](https://github.com/alex137/BestPractice/commit/f2078d6ef32731e35d30e279c90d72a55e9b6268)
    (created `templates/harness/{claude-code,codex,gemini-cli}/` from
    scratch, 2026-07-20) went unflagged by every backfill pass until CI on
    an unrelated PR caught it, because scope is `tree` — the check runs
    against the whole repo regardless of what a given diff touches, so any
    unfixed gap fails every PR's CI, not just one. Backfilled as a row in
    [templates/harness/LEDGER.md](templates/harness/LEDGER.md) rather than
    fixed then. **Done (2026-09-06)** — the exemption is per-member-directory
    now: each family member's own first commit is exempt, the same reasoning
    already applied repo-wide, so a future family's inception commit needs no
    manual backfill. `f2078d6`'s hand-written row stays (a real record of a
    real decision, and deleting it would only make the ledger less complete);
    the harness case that proves the check fires gained a fourth stated case
    for the exemption, and a planted removal of a genuine later change still
    fails, so the exemption did not widen into a hole.
19. <a id="ledger-ci-step-invisible"></a>~~**Root-cause why `parallel-artifact-ledger`'s own CI step never shows    its diagnostic output — a GitHub Actions log-capture anomaly, currently
    working around it by making the check advisory-only.**~~ **Done
    (2026-09-06)** — there was no log-capture anomaly and no false positive.
    [verify_harness.py](tools/verify_harness.py) (CI step 5) invoked a
    vendored [precedent_vendor_engine.py](tools/precedent_vendor_engine.py)
    `refresh <ROOT> --force`, and `refresh()` then ran `git checkout
    precedent-beta-v01` plus `git pull` in the clone it was handed — which in
    CI is the job's own workspace. Step 5 therefore moved the workspace onto
    the base branch, and [precedent_check.py](tools/precedent_check.py) (step
    6) ran the *base* branch's tree, where
    the [harness adapter ledger](templates/harness/LEDGER.md) genuinely has
    no `f2078d6` row.
    Every other symptom follows from the same substitution: the summary line
    CI printed was the base branch's own pre-advisory format, and the
    diagnostic prints never appeared because by step 6 the file was no longer
    the file they had been added to. `git status` stays clean throughout — a
    branch checkout leaves no dirty file to notice — which is why four rounds
    of content verification all came back correct while the workspace stood
    on a different commit.

    Reproduced deterministically: run
    [verify_harness.py](tools/verify_harness.py) and then
    [precedent_check.py](tools/precedent_check.py) in one checkout and the
    second reports the violation; run
    [precedent_check.py](tools/precedent_check.py) alone on the same commit
    and it is clean. Fixed upstream in
    [`25546bc`](https://github.com/alex137/BestPractice/commit/25546bc) —
    `refresh()` materializes blobs with `git show` and never checks the clone
    out, with a regression case that fails against the pre-fix engine — and
    here by vendoring from a throwaway clone instead of `str(ROOT)`.
    `advisory=True` is off; the check is enforcing again. Full account:
    [PR #110, comment](https://github.com/alex137/BestPractice/pull/110#issuecomment-5556343855).

    **The scope note from 2026-09-05 was right, and still applies.**
    `precedent-beta-v01`'s
    [deep-check.yml](.github/workflows/deep-check.yml) has no `fetch-depth:
    0` (only this PR's branch does), so its checkout stays shallow (depth 1),
    `git log --no-merges -- <member-dir>` finds nothing to flag, and this
    check falsely, silently passes there — the "scope: 'tree' check... false
    pass on an under-fetched clone" gotcha in [AGENTS.md](AGENTS.md),
    manifesting repo-wide via the workflow's default rather than a local
    clone's. When this PR merges, `fetch-depth: 0` lands on
    `precedent-beta-v01` and the check starts really running there — which is
    why [`dfe504d`](https://github.com/alex137/BestPractice/commit/dfe504d)'s
    ledger row has to land in the same merge, as it does.

20. <a id="gate-and-paths-unreachable-source"></a>~~**`precedent_gate.py` and `precedent_paths.py` don't flag an unreachable    materialized source either — only `precedent_show.py` does, 2026-09-06.**~~
    **Done (2026-09-06).** Both read `practices/*.md` directly via
    `split_practices._read_practice_file` rather than shelling out to
    `precedent_show.py` (confirmed by grep, not assumed), so the
    reachability note that tool carries (`_source_unreachable_note`) never
    reached a practice loaded through the gate-triggered or path-triggered
    channel — only the on-demand, `precedent show SLUG`-invoked channel got
    it. **The design call, stated before picking (same bar as PR #114's own
    design section):** three options existed — (a) route both files through
    `precedent_show.py` as a subprocess, (b) duplicate
    `_materialize_manifest`/`_source_unreachable_note`'s logic into each, or
    (c) import `precedent_show.py` directly and call its two helpers.
    (a) means re-parsing `precedent_show.py`'s own `"### slug\n<body>"`
    stdout format back into structured data for no reason, purely to get a
    note the caller could already print itself once it has the same
    function. (b) is exactly the drift this repo's own
    [engine-plus-host-shims](practices/engine-plus-host-shims.md) practice
    exists to prevent — two copies of the same reachability logic that can
    silently diverge the next time one is fixed and the other isn't.
    (c) costs nothing new: both files already `import split_practices as sp`
    for the same reason (a sibling module in the same `tools/` directory),
    so importing `precedent_show as ps` the same way and calling
    `ps._materialize_manifest(root)` / `ps._source_unreachable_note(manifest, slug)`
    is the same discipline already in use, not a new one. Chose (c).
    Verified: [tools/verify_harness.py](tools/verify_harness.py)'s
    `check_show_flags_unreachable_materialized_source` extended from 8 to
    12 stated cases (a reachable and an unreachable case added for each of
    the gate and path channels, alongside the pre-existing
    `precedent_show.py` cases) — all 12 pass.

21. <a id="materialized-links-dead"></a>~~**A materialized practice's relative links are dead in the consuming    repo.**~~ **Done (2026-09-06.)** Every consuming repo was shipping ≈60
    practice files whose internal links resolved to nothing:
    [tools/precedent_materialize.py](tools/precedent_materialize.py) copied
    practice bytes verbatim, so `../tools/very_deep_check.py` and
    `../spec/ATTENTION_CEILING.md` — real paths here — pointed at nothing
    there. It now repoints each link for where the file actually lands: a
    commit URL into the source repository (the commit, not a branch, since
    the tree is a snapshot and a branch can be deleted), or a recomputed
    relative path when the target is inside the consuming repo. A sibling
    practice citation, an external URL, a link that already resolves where
    it lands, and a link already broken at the source are each left exactly
    as they are. Verified against a real four-source install: **0 broken
    links**, 39 distinct sibling citations all still resolving. The
    `blocked-on` this item carried turned out to be wrong — nothing
    compared a materialized practice's bytes to its source; that
    byte-identity audit is about check scripts. `precedent-team-maintainers`'
    own light check has dropped the exemption it needed to stay green, and
    its test case for that path now requires a finding instead of silence.

22. <a id="sweep-judgment-only-practices"></a>~~**Sweep the team and individual sets' judgment-only practices.**~~
    [tools/full_practice_audit.py](tools/full_practice_audit.py) reports 49
    judgment-only practices across the three sources. The 2026-09-06
    pre-launch audit judged the universal slice's highest-yield ones and
    fixed what they found. **Partially swept 2026-09-06** (second pass, see
    [spec/PRELAUNCH_AUDIT.md](spec/PRELAUNCH_AUDIT.md)'s "The judgment-only
    sweep, partially done"): `fail-gracefully` produced seven real fixes and
    `durable-list-anchors` one; `branch-links`, `rule-links`,
    `blank-blocklist`, `install`, `quiet-checks` and
    `registry-source-of-truth` came back clean. **Round two, same day**
    (see that document's "The judgment-only sweep, round two"): nineteen of
    fifty-one now judged; `automation-issues` and
    `match-parsed-id-not-prefix` were both violated and are fixed, and eight
    more came back clean or not-applicable with the reason recorded.
    **Roughly thirty-two remain** — mostly moment-of-work practices with no
    standing repo state to sweep, and editorial ones that need a reader
    rather than a script. **Round three, same day: the sweep is COMPLETE** —
    all 51 judged (see that document's "The judgment-only sweep, round
    three"). Four more violations fixed (`lead-with-what-it-is`,
    `bold-key-phrases`, `volatile-rules-carry-dates`, and
    `resolved-issue-note-updates`, that last one violated by the sweeping
    session itself), and the remaining 28 came back clean or not-applicable
    with the reason recorded so no later session re-derives them. The sweep
    also turned up a defect no practice pointed at: `tools/title_case.py`
    was corrupting inline code spans in committed headings.

    **Done — closed 2026-09-07.** This item contradicted itself: it declared
    the sweep COMPLETE ("all 51 judged") and then carried *"blocked on
    nothing but session budget — take them one at a time"*, so it read as
    both finished and not started depending on which sentence you stopped
    at. The second half is now measured rather than argued. Across **all 39**
    practices carrying `checked_by: null` in the two private sets: none has
    an empty `## Install`, the shortest is 177 characters, the median 393,
    and **not one** uses the "too hard to check" shape
    [checkable-gets-checked](practices/checkable-gets-checked.md) forbids.
    Every one records a considered, specific no, which is what that practice
    asks for — an attempt and a recorded reason, not a check at any cost.

    One case read as unreasoned to a keyword scan and is the opposite:
    `catalogue-carries-stories` **is** checked mechanically, by the universal
    catalogue's own `precedent_check.py`, and its `checked_by` is `null`
    precisely so that set does not carry a second implementation of one rule.
    39 of 39 accounted for. **A `checked_by: null` count is not a defect
    count** — the same correction `precedent-team-tms`'s 0 of 2 needed.
    Full context: [spec/PRELAUNCH_AUDIT.md](spec/PRELAUNCH_AUDIT.md) and
    [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md).

23. <a id="roll-out-four-pass-restructure"></a>**Roll the very deep check's four-pass restructure out to
    `precedent-team-maintainers`' own `deep-check`.**
    [practices/very-deep-check.md](practices/very-deep-check.md) was
    restructured 2026-09-06 from one drift checklist into four ordered
    passes — adopter installs, whether the mechanisms tell the truth, the
    coherence read, then catalogue and housekeeping — with the run made
    resumable via [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md). The
    team set's `deep-check` is the same inherited list one generation back,
    so it now states an older, narrower version of the same rule: it should
    either adopt the passes, or point at this practice via `overrides:` and
    stop restating it. That call was already open (item 17 above records it
    as the team's own to make); this restructure is what makes leaving it
    open cost something. **Blocked on:** an explicit instruction, not
    availability — the source was attached in the session that made this
    change, whose ask was scoped to BestPractice's `precedent-beta-v01`
    alone. Any session with `precedent-team-maintainers` attached and a
    mandate to touch it can close this.
    **Narrowed 2026-09-06:** the `overrides:` half is already ruled out —
    [practices/very-deep-check.md](practices/very-deep-check.md)'s Story
    records Morgan's ruling that the team's `deep-check` and this practice
    are unrelated rules, so there is nothing to override, and the team's
    routine per-commit check keeps happening. The same date,
    [practices/two-check-levels.md](practices/two-check-levels.md) drew the
    general line this rests on: what gates a commit, push or merge is one of
    the two named levels, while a rare audit a person asks for by name is a
    separate mechanism. So the open call is only whether the team's
    `deep-check` should adopt anything from the four passes — not whether it
    should be replaced by them.

24. <a id="consumer-source-names"></a>~~**Check the consumer repos' own source names against the convention.**~~
    **Done (2026-09-06.)** A private consumer repo — the one consumer
    that declares sources and was not attached when
    [practices/source-naming.md](practices/source-naming.md) landed — was
    refreshed from its own session and merged. Its repo-local source was
    named after the repository itself; it is now `local`. What the pilot actually
    proved, beyond the rename: the refusal fired at the right moment
    (`precedent_sync_views`, before anything was written), its message was
    actionable enough that the session fixed the name without having
    [spec/SOURCE_NAMING.md](spec/SOURCE_NAMING.md) in its tree, and
    `precedent_check.py` reported `source-naming` as SKIPPED with its
    reason rather than passing falsely — the enforcement arrives with the
    engine, the explanation with the catalogue, and the gap between them
    is visible instead of silent. Two findings it surfaced are item 30
    below and the `code-cites-practice` fix that landed with this entry.

25. <a id="unreachable-practices"></a>**Populate `not_binding` for the practices in force here that do not
    bind this repo.** **The design decision is made and the mechanism is
    built (2026-09-06** —
    [decisions/2026-09-06-precedent-binds-itself.md](decisions/2026-09-06-precedent-binds-itself.md)**).**
    `precedent.json` now takes `not_binding: [{slug, reason}]`, honored by
    `layered-practice-packs`' check: a reason is mandatory, a
    `severity: blocking` practice cannot be exempted, a stale entry is
    reported, and a malformed list fails loudly — all four asserted with
    negative controls in `check_not_binding_cannot_be_abused`.
    Shape 1 (a per-practice field) was rejected because whether a rule binds
    is a property of the pair, not the rule; shape 3 (multi-source generated
    views here) was rejected for this repo because it would publish private
    team practice text into a public [AGENTS.md](AGENTS.md), and because its
    own "the misfits get retired or moved" framing would repeat the
    `deep-check` error of dropping a valid rule that simply does not apply
    here.
    **What is left is a measurement, not a decision:** of the 43 practices
    reachable by nothing, the audit's table says roughly five should be wired
    in as-is, four wired in and then fixed, and six declared not-binding —
    but that table predates Morgan's 2026-09-06 ruling that `deep-check` is
    NOT redundant, so it must be re-judged rather than copied. Writing
    exemptions for practices whose text and severity cannot be read would be
    asserting what cannot be verified.
    **The loading half is now closed too (2026-09-06).**
    [tools/precedent_session_practices.py](tools/precedent_session_practices.py),
    run by the [session-start hook](.claude/hooks/session-start.sh), resolves
    every declared source and writes the team/individual/repo-local block into
    `.precedent/SESSION_PRACTICES.md` — gitignored, so the private text
    reaches the session and cannot reach a commit. That is shape 3's safe
    form: the constraint was always on committing the text, never on loading
    it. It loads but does not enforce; materializing the other sources' check
    scripts waits on the exemptions below.
    **And `layered-practice-packs` now counts that channel (2026-09-06),**
    which it did not at first: it reads AGENTS.md and nothing else, so the
    practices loaded while the check still called them unreachable. Found by
    testing the claim rather than assuming it, when a second session was
    weighing publishing private practice text against leaving the team rules
    unloaded — on the belief that the already-built untracked channel would
    not satisfy this check. It is judged structurally (tool present, hook
    invokes it, repo public), never by looking for the untracked file, which
    is absent in CI and every fresh clone; three harness cases, with the
    negative controls, hold both halves.
    **Blocked on:** a session that can resolve the private sources — see
    [`attach-private-sources`](TODO.md#attach-private-sources) for exactly
    what that takes. Until then the mechanism runs and correctly reports each
    private source as unresolved rather than silently empty.

    **The engine half landed too, 2026-09-06 (was "Part A").**
    [tools/build_views.py](tools/build_views.py) now renders the loader block
    from every source `precedent.json` declares, not the repo's own
    `practices/` alone — correct in any repo that declares more than one
    source and cannot merge them first. **That turned out to be this repo
    and no other:** a consuming repo materializes every source into one
    `practices/` tree before `build_views.py` sees it, so its block was
    already multi-source (verified against two of them after the rollout).
    It is deliberately **off here**, by the `visibility: public` guard
    below: this repo is world-readable, so rendering a private team set's
    Rule clauses into a tracked [AGENTS.md](AGENTS.md) would publish them
    permanently, which is exactly what the decision record above rejected.
    `not_binding` is the mechanism for this repo; the multi-source block is
    the mechanism for every repo that vendors it. They are not competing
    answers to one question.

    Two guards came with it. A repo declaring `visibility: public` renders
    **no private-level source** — team or individual — into its tracked
    block; publishing that block would publish the private set, the same
    disclosure [tools/precedent_resolve.py](tools/precedent_resolve.py)
    already refuses to allow by config. And a declared source that cannot be
    reached makes the block **NOT VERIFIABLE** rather than stale: a team
    source is a sibling clone no bare continuous-integration checkout has, so
    calling that "drift" would fail every run on evidence the environment
    could not have.

    **What remains is the measurement above, and it is far smaller than this
    item first assumed.** 11 practices carry check scripts; of the 15 run
    against this tree, 5 pass, 4 find real problems worth fixing, and 6
    report things this repo cannot act on because the practice is about a
    different kind of repository. Only if a pattern shows up across them —
    several meaning the same thing, such as "a repo one person authors
    alone" — is new vocabulary worth building, and by then its values will be
    known rather than guessed.


26. <a id="headline-duplicate-retired"></a>**Done 2026-09-06 — the duplicate was found and retired.** A session
    holding all four repositories searched by purpose and by mechanism
    across every practice body, frontmatter, check script and test:
    exactly one duplicate, `header-caps` in `precedent-team-maintainers`,
    with its own check and a two-direction test. `precedent-individual`
    had no capitalization practice at all. It was retired there per
    [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md), its check and
    test removed, on branch `claude/practice-repos-audit-migration-2l9jbz`
    (no pull request opened). **Three clauses the universal practice does
    not carry**, recorded here because retiring the old rule dropped them
    rather than moving them: (a) *heading-level consistency* — siblings at
    the same rank sharing a heading level, which is an outline rule, not a
    capitalization one, and is now unenforced anywhere; (b) *scope* —
    `header-caps` applied to `**/*.md` while
    [practices/headline-capitalization.md](practices/headline-capitalization.md)
    deliberately covers `documentation/**/*.md` only, so practice files,
    specs and READMEs lost their same-rank check; (c) the *escape hatch*
    letting a repo document a different scheme inline, which the universal
    rule deliberately does not offer. **All three are now settled
    (2026-09-06).** (a) is rebuilt as its own universal practice,
    [practices/heading-outline.md](practices/heading-outline.md), bound to
    `**/*.md` with a mechanical check in
    [tools/doc_lint.py](tools/doc_lint.py) and a gate in
    [tools/precedent_check.py](tools/precedent_check.py) — wider than the
    team rule it restores, since a broken outline is not a matter of
    audience. (b) is not a loss but the intended design: Morgan confirmed
    that capitalization governs outward-facing content only and that
    internal working files are deliberately out of scope, and
    [practices/headline-capitalization.md](practices/headline-capitalization.md)
    now says so in its own first paragraph rather than leaving it to be
    inferred. (c) stands as the deliberate tightening it was read as.

27. **Done 2026-09-06 — the individual-source bootstrap hook is installed
    here, and this repo is now checked as a consumer of its own install
    instructions.** The item said this was blocked on a session that could
    reach the individual repo, "since an untested session-start hook must
    not be committed blind". That was the wrong blocker: what must never
    happen is a hook that blocks session start, and *that* is testable
    without any access at all — run it in an environment where its clone
    cannot succeed and require exit 0. It does, and
    [tools/verify_harness.py](tools/verify_harness.py) now asserts it,
    alongside a case that this repo carries the hook at all. Writing it
    needed a real fix first: `--write-session-hook` was reachable only
    after `bootstrap()` created a whole individual set, so the "run it
    again against an already-bootstrapped set" both
    [INSTALL.md](INSTALL.md) and
    [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md)
    documented could not be run — which is the real reason this repo had
    no hook. `--dest` is now optional for hook-only writes, both documents
    say so, and a harness case covers it.

28. **Done 2026-09-06 — a missing individual source is no longer silent.**
    Kept as a stub rather than deleted, so item 29 does not shift under
    anyone who cited it. `tools/precedent_resolve.py` now diagnoses the
    four states an unresolved individual source can be in and reports the
    two that are genuinely *unknown* rather than *none*, on stderr and as
    `individual_status` in `--json`;
    [spec/SOURCES.md](spec/SOURCES.md) carries the row.

29. <a id="rpp-migration-audited"></a>**Done 2026-09-06 — nothing was lost in the migration, and the audit
    is recorded here because no ledger holds it.** RepoPersonalPreferences'
    46 rule identifiers (from its own `process/personal/README.md` headings,
    cross-checked against its `MAP.md`) were diffed against 41 practices in
    `precedent-team-maintainers`, 10 in `precedent-individual` and the
    placeholder in `precedent-team-tms`. **43 have a live descendant** — 39
    team, 4 individual, plus `bestpractice-sync`, retired in team and active
    in individual after the 2026-09-03 move. **3 have no active descendant,
    none of them lost:** `deep-check` moved to universal (retired in team
    2026-09-05 in favour of `very-deep-check`); `bestpractice-wins` was
    deliberately retired, its effect now carried structurally by the
    resolver's precedence; `morgan-scope` was deliberately retired, and its
    substantive half — the attributing account, and he/him — survives inside
    `precedent-individual`'s `commit-author.md` `## Detail`. That last one
    survived *by absorption rather than by design*: nothing recorded that it
    moved there, which is the whole argument for a ledger.

30. **Upstream-only registries ride along in vendored engine files.**
    [tools/doc_sync.py](tools/doc_sync.py)'s `PAIRS` hardcodes
    `spec/LOADER.md` and `spec/ENFORCEMENT.md`;
    [tools/model_audit.py](tools/model_audit.py)'s `INSTRUMENTED` names
    [tools/catalogue_stats.py](tools/catalogue_stats.py). None of those
    exist in a consuming repo, and both files became consumer-vendored on
    2026-09-06 — so the first real consumer refresh (that private consumer repo, the
    same day) inherited BestPractice's own registry and reported
    `scripts-assert-properties` violated with `computed-numbers-in-scripts`
    and `docs-track-models` skipped. Nothing is broken; the consumer's
    check output is just wrong about whose registry it is reading.
    `doc_sync.py`'s own docstring already anticipates the host case
    (*"a repo with `PAIRS = []`"*), so the mechanism exists and the
    vendoring step simply does not use it. **Blocked on:** nothing but a
    deliberate pass — this touches the vendoring contract (does
    `precedent_vendor_engine.py` blank a registry on the way out, or does
    each file read its registry from a host-owned file?), and picking
    wrong makes every consumer's copy diverge from upstream's, which is
    the one thing that tree is designed never to do. Do not fix it
    piecemeal from a consumer repo.

31. **Sweep for other places BestPractice does not follow its own install
    instructions.** Item 27's root cause was not the missing hook, it was
    that every existing check builds a *fixture* consumer and asserts
    things about it — nothing asserted the publisher does what it
    publishes, so an install step this repo skipped stayed invisible until
    someone went looking for a rule that never loaded. One instance is now
    checked ([tools/verify_harness.py](tools/verify_harness.py)'s
    self-consumer cases). The sweep is the rest: read
    [INSTALL.md](INSTALL.md) and
    [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md) step by
    step against this repo's actual tree, decide per step whether it
    applies to the upstream at all (several genuinely do not — there is no
    `process/upstream/` here by design), and add a case for each one that
    does. **Blocked on:** nothing but its size and the per-step judgment
    call about which steps apply to the publisher — deliberately not
    folded into the thread that found the first instance, which would have
    meant deciding all of them in passing.

32. <a id="migrated-practices-lost-their-stories"></a>~~**The RPP migration dropped every `## Story`, and that is the
    provenance the catalogue exists to keep.**~~ **Done — confirmed by
    re-measurement, 2026-09-07.** The backfill happened; this item outlived
    it and went on asserting figures that were no longer true. Every one of
    the **57** practice files across all three private sets — 42 in
    `precedent-team-maintainers` (40 active, 2 deduplicated), 14 in
    `precedent-individual`, 1 in `precedent-team-tms` — now has a non-empty
    `## Story`, at any status. So do all 57 `## Why` sections. Nine files
    have an empty `## Detail`, which is not a violation:
    [catalogue-carries-stories](practices/catalogue-carries-stories.md)
    requires a Story, and Detail is optional.

    The three specific claims this item carried are all now false, and each
    was checked rather than assumed: it is not "34 of 41 and 3 of 10" (it is
    0 of 57); `header-caps` has a `## Why`; and `fail-gracefully` has
    substantial Detail, Why *and* Story — 1,123, 751 and 1,204 characters.
    The counts had also drifted with the catalogue: 41 and 10 were the sizes
    when this was written, against 42 and 14 today.

    The measurement itself is worth recording, because the first attempt at
    it was wrong in the direction this project keeps warning about. Reading
    the sections with the key `'Story'` instead of `'story'` returned `None`
    for every file and reported **100% empty across all three sets** — a
    confident, precise, entirely false finding, and one that happened to
    agree with what this stale item already claimed. It was caught only
    because 100% is not a believable number, not because anything failed.
    The corrected sweep therefore asserts a control first: a practice known
    to have all three sections must come back non-empty, or the sweep
    refuses to report. "Could not read" and "read, found nothing" must never
    render identically — the rule is `fail-gracefully`'s second clause, and
    the finding above is what it looks like when nothing enforces it.

33. <a id="team-check-cites-retired-practice"></a>~~**`precedent-team-maintainers`' `check_deep_check.py` cites a practice
    retired in that same set.**~~ **Resolved by reversal, 2026-09-06.** The
    premise was the bug: `deep-check` was never redundant with
    `very-deep-check` — they are unrelated rules of different kind and
    cadence (see
    [practices/very-deep-check.md](practices/very-deep-check.md)'s corrected
    `## Story`). `deep-check` is restored to `active` in the team set, so the
    `# practice: deep-check` citation resolves again and there is nothing to
    move. This is the incident that motivated
    [decisions/2026-09-06-deduplication-not-retirement.md](decisions/2026-09-06-deduplication-not-retirement.md).

34. <a id="attach-private-sources"></a>**Run one session rooted at each private set — this unblocks four other
    items at once.** Established 2026-09-06 by trying it, rather than
    assumed: all three private repos (`themorgan/precedent-team-maintainers`,
    `themorgan/precedent-team-tms`, `themorgan/precedent-individual`) are
    **reachable and pushable** by this account. The blocker is not access. It
    is that `add_repo` refuses a cross-owner add — a session already holding
    `alex137/*` cannot attach a `themorgan/*` repo ("cross-tier adds are not
    supported in v1"). So the unblock is simply **a session whose initial
    source is the private repo** — or, since 2026-09-10, a session with
    `PRECEDENT_GIT_TOKEN` on its environment, which clones every private
    source at session start with no `add_repo` call at all
    ([INSTALL.md](INSTALL.md) §8). That route is verified working and is the
    cheaper one; this item's remaining work is the per-set commands below,
    which still need a session that can PUSH to each set. BestPractice itself is public, so that
    session can `git clone https://github.com/alex137/BestPractice` directly;
    no second `add_repo` is needed. In each such session:
    `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`,
    then `python3 tools/precedent_migrate_status.py --repo . --against ..`,
    then `python3 tools/build_codeowners.py`, committed.
    **What the refresh now carries, named rather than left to "it'll pick it
    up" (2026-09-06):** [tools/doc_lint.py](tools/doc_lint.py)'s check 6 gained
    two fixes each source's own vendored copy is currently without — a
    `decisions/` directory is record-class, and a link to a dated decision
    record is an allowed reference in a deliverable. Any set that keeps
    decision records under dated names is failing its own light check on them
    until it refreshes. Nothing else is required of the sets: the change is in
    the vendored engine, not in anything they author.
    Unblocks [`convert-team-set-retired-statuses`](TODO.md#convert-team-set-retired-statuses),
    [`build-codeowners-check-flag`](TODO.md#build-codeowners-check-flag)'s
    rollout, [`unreachable-practices`](TODO.md#unreachable-practices)'s
    measurement, and configuring the leak gate's vocabulary blocklist (which
    belongs in `precedent-individual`).

    **THE BLOCKER AS WRITTEN IS FALSE, 2026-09-07 — and it is the premise
    four other items are waiting on.** This item says a session holding
    `alex137/*` cannot attach a `themorgan/*` repo. The session running the
    very deep check that day held, simultaneously:
    `alex137/bestpractice`, `themorgan/precedent-individual`,
    `themorgan/precedent-team-maintainers`, `themorgan/precedent-team-tms`,
    `the project's own prior notes repository` and one further private `themorgan/*`
    consumer repo — and
    `add_repo` accepted the last of those *during* that session, with all
    three private sets already attached and worked in. Mixed owners in one
    session is exactly what this item and
    [AGENTS.md](AGENTS.md)'s gotcha say cannot happen.

    **What is NOT established**, stated so the correction does not overreach:
    whether a *fresh* session rooted at `alex137/BestPractice` can add a
    `themorgan/*` repo as its first cross-owner add. That specific call was
    not made. The constraint may have been lifted, or may only bind the first
    add — this session cannot tell which, because it did not start empty. So
    the four items above are **not** blocked on what this item says blocks
    them, and someone should re-test the fresh-session case rather than
    assume either answer.

    Its earlier evidence stays, dated: on 2026-09-06 the refusal was real and
    was reproduced, so this is a change in the environment rather than a
    mistake in the original finding.

    **The fresh-session case was tested 2026-09-09, and it refuses.** A
    session rooted at `alex137/bestpractice` called `add_repo` for
    `themorgan/precedent-individual` as its **first tool call of the
    session** and was told *"cross-tier adds are not supported in v1:
    requested ... but session already has repos from owner(s) [alex137]"*.
    So the initial source itself counts as "already has repos", and no
    ordering of calls inside such a session can work. That closes the
    question this item left open; it does not explain the 2026-09-07 session
    that held five owners' repositories at once, which stays unexplained.

    **And the item's premise — that a session must be rooted at the private
    repo — is now only one of two routes.** `add_repo` is not the only way to
    hold a credential: an environment can carry one, and the SessionStart
    hook can then clone the sources *before the agent's first turn*, which is
    the ordering every part of this problem turns on. Set
    `PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL`
    ([INSTALL.md §8](INSTALL.md#8-per-machine-setup--what-each-person-sets-on-each-machine)),
    and [tools/precedent_source_bootstrap.py](tools/precedent_source_bootstrap.py)
    `--teams-from .` clones every declared team set as a sibling. **Nobody
    has run it with a valid token yet** — three of the four things it depends
    on were measured that day (the proxy passes authenticated GitHub reads,
    no ambient credential exists, the helper really does hand git the token),
    and the fourth needs a token this account has not issued. Until somebody
    does, this item stays open on that one step, not on the whole design.
    [tools/precedent_source_credentials.py](tools/precedent_source_credentials.py)
    reports which state a session is in.

35. <a id="convert-team-set-retired-statuses"></a>*(was item 34 — two items carried that number until 2026-09-06.)* **Convert
    `precedent-team-maintainers`' two `status: retired` practices to
    `status: deduplicated`.** `bestpractice-sync` (rule in force at
    individual) and `header-caps` (rule in force at universal) are both
    deduplications recorded under the old vocabulary, and neither can meet
    retirement's evidence bar (`in_force_at: none` plus a Story line saying
    nobody wants the rule anywhere) because both rules are fully in force.

    **Correction, same day:** an earlier draft of this item said the set
    would "go red on its next vendored-engine refresh." That was wrong, and
    wrong in the direction that matters — `verify_harness.py` is **not** in
    [`ENGINE_FILES`](tools/precedent_vendor_engine.py), so
    `check_status_contract` never runs in a practice set at all. The set
    does not go red; it goes **silent**, which is worse. The new engine
    simply starts treating those two records as not in force — correct
    either way — with nothing to say the vocabulary underneath them changed.

    The migration is now mechanical:
    [`tools/precedent_migrate_status.py`](tools/precedent_migrate_status.py)
    (vendored, so it runs inside the set) reports both, auto-proposes
    `bestpractice-sync` (same slug, active in `precedent-individual`), and
    leaves `header-caps` UNDETERMINED because its successor is renamed —
    `--set header-caps=headline-capitalization`. Run it report-only first.
    **Blocked on:** a session holding `themorgan/precedent-team-maintainers`.

36. <a id="build-codeowners-check-flag"></a>~~**`build_codeowners.py --check` is not a check — it takes no such flag
    and writes anyway.**~~ **Done 2026-09-06.** Both defects fixed in
    [tools/build_codeowners.py](tools/build_codeowners.py): a real `--check`
    that compares and exits non-zero without writing (and an unknown flag is
    now refused rather than falling through to the destructive path — that
    fall-through was the bug, and doing the destructive thing on a typo is
    how it stayed hidden), and the derived-file header now stamps a sha256 of
    `approvers.json`'s own content instead of `git rev-parse HEAD`, so an
    unchanged approver list regenerates byte-identically. Harness-tested with
    10 stated cases, including negative controls, in
    `check_codeowners_check_is_a_check`. BestPractice has no `approvers.json`
    of its own, so the fixture supplies one — that absence is exactly why
    this went unnoticed while the tool was private to one team set.
    **Cross-source consequence, not yet rolled out
    ([cross-source-rollout](practices/cross-source-rollout.md)):** the header
    format changed, so the first regeneration in each team set produces a
    one-time diff. Expected and correct — after it, `--check` is stable.
    **Blocked on:** `themorgan/precedent-team-maintainers` not attached this
    session (`themorgan/precedent-team-tms` was also named here until it was
    retired 2026-09-10). It needs
    `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`
    then `python3 tools/build_codeowners.py`, committed.

37. <a id="source-repo-consumes-no-catalogue"></a>**A source repo consumes no catalogue, so it cannot check itself.**
    None of the three private sets has a `precedent.json`, so each set's
    `build_views.py` renders its own catalogue alone — and a universal
    practice cannot reach the set that dropped its own copy in favour of it.
    `very-deep-check` is in force in every consuming project and invisible
    inside `precedent-team-maintainers` itself; so is
    `headline-capitalization`, whose team-level copy that set deduplicated.
    This is the structural half of why `status:` went unhonored in three
    loading channels for so long. **A design decision, not a bug fix** — a
    source repo eating its own cooking changes what binds a contributor to
    that set, so it needs Morgan's call before any work starts.

38. <a id="relax-the-pinned-branch-hold"></a>**Relax the pinned-branch hold
    once the fix has run through real sync cycles.**
    [tools/checkin.py](tools/checkin.py)'s four commands — `fresh`,
    `update`, `record`, `push` — now read `upstream.branch` from a consuming
    repo's own `process/manifest.json` instead of resolving the remote's
    default branch, and `record` no longer checks the source clone out from
    under its caller. Seven cases in
    [tools/verify_harness.py](tools/verify_harness.py) assert both
    properties with negative controls. That closes the defect
    [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
    "The default-branch gotcha" was written around, and
    `_warn_catalogue_skew`'s docstring in
    [tools/precedent_vendor_engine.py](tools/precedent_vendor_engine.py)
    names the same fix. **Both still tell people to mirror by hand and to
    keep the scheduled sync paused, deliberately** — Morgan's call
    2026-09-06, on the asymmetry: what those documents guard against is an
    *unattended* job overwriting a vendored tree, so relaxing them too early
    costs a silent overnight wipe of a repo's practices while staying
    cautious costs a stale paragraph. **Blocked on:** the fix surviving real
    sync cycles rather than only its own tests, and then Morgan saying so.
    What it needs then, in one change: put `checkin.py update` back as the
    remedy `_warn_catalogue_skew` names, drop the hold paragraph from the
    migration document, and un-pause the `schedule:` block in each
    consumer's `bestpractice-upstream-sync.yml` — never one of the three
    without the others, since a half-relaxed hold is what makes an
    unattended job run against advice nobody re-read.
    **Enforced 2026-09-07, which changes what relaxing it costs.**
    `checkin.py update` now refuses while a non-default branch is pinned
    (`_pinned_branch_hold`), printing the manual procedure and naming
    `PRECEDENT_ALLOW_PINNED_UPDATE=1` as the one-run override; eight harness
    cases with a negative control. Until then the hold existed only as a
    paragraph in a document, so every session had to read and obey it — the
    advisory-only state `checkable-gets-checked` exists to end. Note what
    this does to the relaxation above: the guard's condition IS the hold's
    condition, so repointing a manifest to the default branch lifts it for
    that repo automatically. The three-part change listed above therefore
    has a fourth part that needs no work — but do confirm the guard has
    stopped firing rather than assuming it, since a repo left pinned keeps
    it, correctly.
    **Still open, and NOT closed by that guard:** a consumer carrying a
    pre-fix vendored copy has no guard at all, and nothing upstream can
    reach it — the manual mirror is what brings the current file in. Whether
    that is worth closing with a consumer-side check outside the vendored
    tree (a CI check refusing a commit that reverts the tree against its
    pin) is a real question and nobody has decided it.

39. <a id="background-freshness-fetch"></a>**Consider making the freshness check's fetch asynchronous.**
    [.claude/hooks/freshness-guard.sh](.claude/hooks/freshness-guard.sh)'s
    `user-prompt` mode is throttled rather than backgrounded: it skips
    entirely inside its interval (measured ≈17ms, no network, no output) and
    pays one fetch when the interval has passed. Measured 2026-09-06 in a
    cloud container: any remote check costs ≈500ms and `git ls-remote` is
    **not** cheaper than a no-op `git fetch` (≈600ms vs ≈500ms — both are one
    network round trip; neither transfers objects when current), so the only
    lever is asking less often, which is what the throttle does. The
    alternative considered and deliberately deferred: fire the fetch
    detached, return immediately, and act on the *previous* fetch via the
    ≈5ms local comparison — ≈0ms added latency at the cost of freshness
    lagging by one message. **Blocked on:** nothing external, but it was not
    worth the complexity at the measured numbers — with the throttle the
    ≈500ms lands so rarely that backgrounding buys little. It also rests on
    an unverified assumption that a process detached from a hook survives the
    hook returning rather than being reaped with it, which needs a real test
    (this repo has already been burned once by a mechanism verified only
    against synthetic fixtures — see
    [practices/session-bootstrap.md](practices/session-bootstrap.md)'s
    Detail). Revisit if the throttle's interval ever has to drop low enough
    that the fetch becomes noticeable. Full reasoning, including the
    measurements and the two rejected alternatives:
    [this thread](https://claude.ai/code/session_01NQCKsA4otmeujdrbCGrqR3).

40. <a id="cache-freshness-verdict"></a>~~**Cache the freshness guard's verdict so a blocked state stops
    re-probing.**~~ **Considered and declined 2026-09-06 — the measurements
    are here so nobody re-derives them.** The behavior is real:
    [.claude/hooks/freshness-guard.sh](.claude/hooks/freshness-guard.sh)'s
    `pre-write` mode writes its once-per-session sentinel only on the
    *success* path, so in any of its five blocking states (fetch failed,
    behind-and-dirty, diverged, fast-forward failed, missing commits from
    base) every subsequent non-`git` tool call re-runs the whole check,
    network probe included, and refuses again with the same answer —
    reproduced with three consecutive blocked calls leaving zero sentinels.
    The proposed fix: replace "sentinel = verified OK" with a cached verdict
    in `$GIT_DIR`, keyed on HEAD sha + dirty flag + branch with a ≈60s max
    age, so a repeat call re-emits the cached refusal in ≈17ms instead of
    probing, while any remedy that moves HEAD or flips the dirty flag
    invalidates it instantly.
    **Why it was declined.** The case rested on an assumption that a failing
    fetch is slow. It is not, in this environment — measured 2026-09-06 in a
    Claude cloud container: a bad local path fails in 8ms, an unroutable IP
    (the genuine network-is-down case) in 53ms, an unresolvable host in
    254ms, and a real host with a nonexistent repo in 382ms. The proxy fails
    fast; there is no multi-second timeout to avoid. So the saving is
    ≈50–400ms per blocked non-`git` call, in states that are rare, and during
    which every `git` command — which is what every remedy the guard names
    actually is — is already exempt and free. A stuck episode of five
    non-`git` calls saves about one second in total, against a change that
    alters the sentinel's meaning, adds two invalidation paths, and could
    easily be misread by a later session as the guard going soft.
    Morgan works only in Claude's cloud sessions, not a local install (as of
    2026-09-06), so the offline case that motivates this most is the least
    likely one to occur.
    **If it is revisited**, two of the five blocking states are *not*
    invalidated by a HEAD + dirty key and would fall back to the timer alone:
    a failed fetch (the remedy is the network returning — nothing local
    changes) and a failed fast-forward caused by an untracked file (untracked
    files are outside the `--untracked-files=no` dirty check). A cached
    refusal must also say *when* it was formed, or it will quote a commit
    count that has since moved. **What would change the verdict:** a stuck
    state observed producing a genuinely slow probe on some network path
    other than this container's proxy, or the guard's blocking states turning
    out to be common rather than rare in practice. Full reasoning and the
    measurement runs:
    [this thread](https://claude.ai/code/session_01NQCKsA4otmeujdrbCGrqR3).

- **Wire the clone-free engine-freshness check into the path a person's own
  session actually takes.** `python3 tools/precedent_vendor_engine.py fresh`
  already answers "is this vendored engine behind upstream?" with a single
  `git ls-remote` and no clone — it has since the vendoring mechanism
  landed, and it works: run in a stale set on 2026-09-06 it named the exact
  commit gap. **Nothing calls it.** The only mentions anywhere are in the
  tool's own docstring, which is why two sets could sit two hundred commits
  behind with nobody told. Three channels now exist that did not
  (2026-09-06): the scheduled workflow every source template ships, the
  bootstrap warning when the seeding checkout is itself behind, and
  [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py)
  run from a session working here. All three are periodic or incidental.
  The channel that would catch it *every* time is the source set's own
  `bootstrap/session-start.sh` — the hook that already runs in every
  consuming project to clone or update the set — calling `fresh` right after
  it updates the clone, where a person is present to read the notice.
  **Blocked on:** that hook lives in each private source repo
  (`precedent-individual/bootstrap/session-start.sh`), not here, and
  `templates/practice-set-*/` ships no equivalent for a new adopter to
  inherit. Doing it properly means generalizing that hook into the two
  templates first, so the fix reaches every set rather than only the two
  that already exist.

- **A scheduled freshness channel exists only for whoever builds one.** The
  two channels shipped here — the bootstrap warning and
  [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py) —
  are both incidental: they fire when someone happens to be bootstrapping a
  set, or happens to be working in this repo. A set nobody touches for a
  month is told nothing for a month. The scheduled channel that would close
  that was added to both source templates on 2026-09-06 and **removed the
  same day, deliberately**: a cron job phoning a remote weekly, spending an
  adopter's Actions minutes and opening pull requests in their repository, is
  not something a universal template gets to decide on their behalf. It is an
  individual-level preference now, and
  [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md) records the
  shape in full so nobody re-derives it. **Blocked on:** nothing mechanical,
  and that is the point — reopening this means someone arguing the imposition
  is worth it for every adopter, which is a decision rather than a task.

41. <a id="gates-absent-from-main"></a>**Put the leak gate on `main`; the deep
    check cannot go there until the merge-back.** **Deferred by Morgan
    2026-09-07 — worth doing, not now.** `main` carries only
    [.github/workflows/docs.yml](.github/workflows/docs.yml), so the official
    branch — the one a visitor lands on and every installer reads — is guarded
    by the markdown lint alone. Neither other gate has ever existed there:
    both were built on `precedent-beta-v01` (leak gate 2026-08-31, deep check
    2026-09-03), and the branches have diverged, with `main` 269 commits
    behind. Verified 2026-09-07 by listing `.github/workflows/` on
    `origin/main`.

    **The two halves are not the same job, which is what turned this from a
    question into a task.** The deep check *cannot* be ported: `main` has no
    [tools/verify_harness.py](tools/verify_harness.py) and no
    [tools/precedent_check.py](tools/precedent_check.py), so copying the
    workflow there would install a check that fails on its first run and every
    run after it. Porting those tools with it is not the fix either — they
    exercise the practice engine `main` does not have, against a `practices/`
    directory it does not have. That half waits for the merge-back as a matter
    of fact, not preference. The leak gate is the opposite:
    [tools/leak_gate.py](tools/leak_gate.py) is self-contained, is not among
    the files [tools/precedent_vendor_engine.py](tools/precedent_vendor_engine.py)
    copies downstream, and `main`'s tree **already passes it** — 59 units,
    exit 0, checked 2026-09-07 from inside a worktree of `origin/main`. (From
    *inside*: `ROOT` there resolves through `__file__`, so running the script
    by absolute path from another checkout silently scans the script's own
    repo and reports a confident, wrong pass — 799 units, this branch's
    figure. The next person auditing another branch will reach for exactly
    that command.) The private vocabulary half did not run, as always without
    the blocklist.

    **What it takes when it is done:** a small pull request to `main` carrying
    [tools/leak_gate.py](tools/leak_gate.py),
    [tools/leak-blocklist.default.txt](tools/leak-blocklist.default.txt) and
    [.github/workflows/leak-gate.yml](.github/workflows/leak-gate.yml) as they
    stand on this branch, with `pull_request:` already dropped (d11394c) so it
    does not arrive carrying the double-run this branch just removed.

    **Why deferring is defensible, stated so the deferral can be re-judged
    rather than re-argued:** nothing has pushed to `main` since 2026-09-03 and
    its tree is clean today, so the exposure is a branch nobody writes to.
    **What would make it urgent:** any push to `main` before the merge-back —
    at which point the gate is missing exactly when it is needed, because the
    scanner's whole premise is that on a public repo a push is a publication
    with no grace period. **What closes it for free:** the merge-back landing
    first, which brings both gates to `main` in one move.

42. <a id="bold-rule-for-heading-dense-pages"></a>~~**`bold-key-phrases` needs a weak
    counter-clause for heading-dense pages.**~~ **Done 2026-09-07**, in the team set,
    on branch `claude/bold-phrases-density-clause-mo6m33`. The clause went to
    `## Detail`, not `## Rule`: the practice is `tier: resident`, and a suggestion
    named deliberately weak does not earn text every session carries whether or not
    the occasion fires — the counterweight it qualifies ("emphasis is a budget", the
    two rough tests) was already in Detail, so the qualifier sits with what it
    qualifies. The resident block is unchanged at ≈248 tokens. No `checked_by`, for
    the reason this item gave. The Story carries the incident: the audit sweep was
    right for the page as it then stood, the page grew, the same emphasis stopped
    signalling — both halves kept, because the rule was right the first time and
    wrong the second on the same document.

    **The four-step runbook below was followed as written and every step held**,
    including the two the item could only predict: `add_repo` accepted both sibling
    `themorgan/*` sets from a session already holding one (the cross-tier rule keys
    on owner, as [AGENTS.md](AGENTS.md)'s gotcha says), and a plain `git clone` of the
    public upstream needed no credentials. Kept unstruck as a working recipe for the
    next cross-set edit.

    **Follow-on, 2026-09-07: landing it in BOTH team sets made the resolver refuse.**
    `bold-key-phrases` now exists in `precedent-team-maintainers` and
    `precedent-team-tms`, and so does `fail-gracefully` — two same-slug practices at
    the same level, landed the same day by two sessions each doing the obviously
    right thing. `precedent_resolve` raises `ResolveError` on a source list holding
    both: *"nothing orders two sources at the same level, so there is no answer to
    which one wins."* Any repository declaring both team sources fails to resolve
    entirely. Nothing is broken today (no repository declares both), and the
    question is filed at
    [`practice-consistency-across-team-repos`](TODO.md#practice-consistency-across-team-repos)
    with a recommendation. Morgan, 2026-09-07, on
    [documentation/WHAT_IS_THIS_AND_BENEFITS.md](documentation/WHAT_IS_THIS_AND_BENEFITS.md):
    "this page has a lot of headings and short lists, so that would make it too
    bold". He asked for the one-line lead-in under each `##` to carry no bold
    at all — done that day — and named the rule himself as **a suggestion,
    deliberately weak**, not a gate.

    The page's own history is the evidence on both sides.
    [spec/PRELAUNCH_AUDIT.md](spec/PRELAUNCH_AUDIT.md)'s round-three sweep
    found this exact document at 0.1 bold spans per 100 words against 0.8-1.9
    in every other outward-facing document and added seventeen, which was
    right at the time. The document has since grown from four groups to five
    and from twelve items to eighteen, and at that density a bold lead-in
    under every heading marks nothing — the structure is already doing the
    emphasis. **What to write:** an advisory clause on `bold-key-phrases`
    saying the density is judged against running prose, and that a page whose
    own structure carries the emphasis leaves its section lead-ins plain.
    **Deliberately no mechanical check:** a spans-per-100-words ratio cannot
    tell a heading-dense page from an under-emphasized one, which is the whole
    finding — a check here would re-flag the page Morgan just fixed.

    **Where it lives:** the TEAM set, `precedent-team-maintainers`, at `tier:
    resident` — [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s
    resolve run and [spec/PHASE5_DEEPCHECK.md](spec/PHASE5_DEEPCHECK.md) both
    name it there alongside `nonblocking-questions` and `small-calls`. Being
    resident matters for the wording: it is carried in every session's context
    whether or not the occasion fires, so the clause has to be short.

    **Blocked on:** a session with that set on disk. This one does not have it
    ([tools/precedent_resolve.py](tools/precedent_resolve.py): team source
    `../precedent-team-maintainers` absent, no individual config — checked on
    disk rather than recalled, per
    [`migrated-practices-lost-their-stories`](TODO.md#migrated-practices-lost-their-stories)'s
    own correction about blockers taken from memory). Asked to attach it
    2026-09-07, `add_repo` refused for the reason
    [AGENTS.md](AGENTS.md)'s gotcha already records — *"cross-tier adds are not
    supported in v1: requested themorgan/precedent-individual but session
    already has repos from owner(s) [alex137]"* — while `list_repos` shows all
    three private sets with `can_push: true`, so this is the session's shape,
    not the account's rights.

    **How to run it,** in this order — the order is the whole trick:

    1. Start a session whose **initial source** is
       `themorgan/precedent-team-maintainers`. This is the only step that
       cannot be done from inside another session.
    2. `add_repo` `themorgan/precedent-individual` from there if you want
       it — same owner, so the cross-tier rule does not fire. **It is not
       part of this job.** `bold-key-phrases` is in
       `precedent-team-maintainers` only, and team sets are siblings rather
       than a hierarchy, so nothing propagates between them. Sharpened
       2026-09-07 after Morgan asked whether this was one team set or all
       `precedent-team-*`. (`precedent-team-tms` was named here too until
       2026-09-10, when it was retired — it held one practice,
       `audience-register`, which moved to `precedent-team-working-style`.)

       **The consequence is worth seeing, and is a separate question:** the
       clause will not reach editorial document projects, which are the
       heading-dense prose pages it most describes. They do not carry
       `bold-key-phrases` at all —
       [templates/document-project/precedent.json](templates/document-project/precedent.json)
       declares universal plus `precedent-team-writing` and
       `precedent-team-working-style`, not `-maintainers`.
       Wanting the rule there is a level decision (promote to universal, or
       copy to `-tms`), for Morgan, not something this item's clause does.
    3. Reach BestPractice with a plain `git clone` of
       `https://github.com/alex137/BestPractice` (branch
       `precedent-beta-v01`), **not** `add_repo` — the same cross-tier rule
       refuses it in that direction too, and this repo is public, so a clone
       needs no credentials.
    4. Edit `practices/bold-key-phrases.md` in the team set, follow that
       repo's own AGENTS.md for branch and checks, and push there.

    **What that session cannot do:** push to this repo. Its git credentials
    cover `themorgan/*` only, so striking this item through is a separate
    one-line follow-up from a BestPractice session, after the clause lands.

- ~~**`precedent_check.py` is not vendored into source sets, so a practice
  set enforces nothing of the universal catalogue.**~~ **Done 2026-09-07**, in
  the same day it was filed. It is the root cause behind two other items:
  `cite-the-incident`'s check never ran in the private sets, and neither did
  the status-contract check
  ([`convert-team-set-retired-statuses`](TODO.md#convert-team-set-retired-statuses)
  records the same shape). Both were assumed to be running. **A gap declared
  in a repo that cannot check for it is indistinguishable from one nobody
  declared** — which is how 34 empty Stories sat in a team source with its
  own gates green.
  **A correction to this item's own first draft, kept because the mistake is
  instructive:** it said the file was in *neither* `ENGINE_FILES` nor
  `CONSUMER_ENGINE_FILES`. That was wrong about consumers — it had been in
  `CONSUMER_ENGINE_FILES` all along — and right about sources. The conclusion
  survived because the repos that were actually broken are the three private
  *source* sets, not the consumers; but the supporting claim was overstated,
  and was asserted from reading one list rather than both.
  **What it took:** adding it to `ENGINE_FILES` (it reaches
  `CONSUMER_ENGINE_FILES` automatically, which is built from it), plus
  guarding the two imports that were still bare — `title_case` and, in
  `_source_naming`, `precedent_resolve`. A source set gets neither module,
  and an unguarded import turns a legitimately absent dependency into an
  ERRORED check, which reads as a broken tool rather than an absent one.
  `doc_lint` and `doc_sync` already degraded correctly.

- **Nine practices carry an empty `## Why`.** Found 2026-09-07 by the Story
  backfill, which was scoped to `## Story` and deliberately did not widen:
  `docs-are-current-state`, `environment-gotchas`,
  `generated-artifact-provenance`, `label-describes-content`,
  `layered-practice-packs`, `lead-with-what-it-is`, `merge-runbook`,
  `one-formatter-per-quantity`, `parallel-artifact-ledger`. A tenth,
  `reply-links-files`, had an empty Why *and* an empty Story and was fixed in
  that pass, which is how the rest were noticed.
  This is a different gap from the Story one and probably has a different
  cause: `## Why` is reasoning the converter *did* carry across, so an empty
  one suggests the source practice stated a rule with no separate rationale
  rather than that anything was lost. Worth confirming against
  `PRACTICES.md` before writing anything — and note that
  [catalogue-carries-stories](practices/catalogue-carries-stories.md)
  deliberately checks Story only, so nothing currently reports these.
  **Blocked on:** nothing but the work.

- **Two declared sources are missing a file their level's skeleton ships.**
  Found 2026-09-07 by the [very deep check](spec/VERY_DEEP_CHECK.md)'s
  source-shape pass, once that check stopped reporting two false positives
  alongside them. `themorgan/precedent-individual` has no
  `config.json.sample`; `themorgan/precedent-team-maintainers` has no
  `leak-blocklist.txt`. Both were migrated into place rather than
  bootstrapped, so neither ever passed through
  [tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py),
  which is the same cause the `verify()` docstring already records for the
  team set's blocklist — that entry is about this one, still open.
  The blocklist matters more than the sample: an absent one is a gap, while
  an empty one is a deliberate state (`blank-blocklist`), and until it
  exists the leak gate's vocabulary layer has nothing of that set's own to
  check against.
  **Both fixes already exist, unlanded.** Found 2026-09-07 while writing up
  the branch sweep: `claude/pre-launch-audit-fixes-7wumzx` carries
  "Add the `config.json.sample` this set never got, being migrated not
  bootstrapped" in the individual set and "Add the `leak-blocklist.txt` this
  set never got, being migrated rather than bootstrapped" in the team set,
  both dated 2026-09-06. This item and that branch are the same finding,
  rediscovered a day apart because nothing asked what was sitting unmerged.
  **Do not merge those branches to close this** — both sit on a vendored
  engine 41 commits behind their own `main`, so merging would revert the
  engine to land two files. Cherry-pick the two files (and, in the
  individual set, `practices/my-identity-is-not-private.md` with its check
  and test, which are also unlanded), then close the branch.
  **Blocked on:** nothing but the work — both repos are reachable and
  pushable from a session that has them attached.

- **The commit-identity mechanism does not reach an attached sibling
  repo, so `commit-author` is silently unenforced in exactly the sessions
  that do cross-repo work.** Found 2026-09-07 by the
  [very deep check](spec/VERY_DEEP_CHECK.md)'s pass 2. All four clones in
  that session carried `Claude <noreply@anthropic.com>`, the precise failure
  the individual set's `commit-author` Story records as having been replaced
  by a mechanism on 2026-09-06. The mechanism is correct; it is a
  `SessionStart` hook, and a repo that is not the session's primary never
  runs one — which AGENTS.md's own `add_repo` gotcha already states in
  general terms. What is new is the consequence: a practice with a real
  mechanical check goes unenforced without anything saying so, and the
  session must notice and set four git configs by hand.
  **Answered 2026-09-07, and the answer was a third layer.** The question
  this item posed — whether the `pre-commit` backstop can be installed by
  something other than a hook that never fires — has a yes:
  [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh) now runs
  the individual set's own `bootstrap/commit-identity.sh` once per attached
  Precedent repo, with `CLAUDE_PROJECT_DIR` pointed at each. The PRIMARY
  repo's hook does fire, so it carries the reach the sibling's own hook
  never gets. No name, address or zone is copied anywhere — it runs that
  set's script, which reads that set's `identity.json`, still the single
  declaration (registry-source-of-truth). The timezone half went the same
  way and one step further: the script now derives the declared zone into
  `.claude/settings.local.json`'s `env` block, so it reaches the whole of
  the next session rather than being retyped per commit (see
  [INSTALL.md](INSTALL.md)'s commit-identity section).
  **What is still open, and it is narrower than this item was:** all of that
  reaches a repo only from a session whose primary repo carries the updated
  `session-start.sh`. A repo that has not wired `commit-identity.sh` at all
  is untouched — and at least one dependent repo declined to wire it,
  reasoning that it "resolves an identity" where that repo's `commit-author`
  practice fixes one. That reasoning inverts what the hook does: resolution
  is how it avoids naming a person in a shared file, and when the answer
  comes from a DECLARATION (an `identity.json`, or an explicit override) it
  then ENFORCES that exact author and timezone with a `pre-commit` refusal —
  which is the mechanical enforcement `commit-author` otherwise does not
  have. The hook also needs no Precedent layout: it reads `identity.json`
  from the repo root or from the individual source named by
  `~/.config/precedent/config.json`, so a classic-layout repo can wire it
  today without migrating anything.
  **Blocked on:** nothing here. What remains is per-repo wiring, and a
  correction to the declining repo's reasoning when someone next works
  there.

- **Four unmerged branches across three repos need a merge-or-close
  verdict.** Listed by name, with what each is ahead by, in
  [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md)'s pass 4. Two of them
  are `claude/pre-launch-audit-fixes-7wumzx`, the same branch name in
  `precedent-individual` (19 unlanded) and `precedent-team-maintainers` (16
  unlanded), both last moved 2026-09-06. Either a real body of fixes that
  never landed, or branches whose work reached `main` by another route — the
  diffs do not say which.
  **Blocked on:** Alex or Morgan. The practice is explicit that a session
  which cannot tell says so by name and asks rather than guessing, because
  waving one through trains the reader to wave the whole list through.

- **Two published commits carry the wrong timezone offset, and
  `precedent_refresh_sources.py --commit` writes a commit with no session
  trailer.** Both found 2026-09-07 by the
  [very deep check](spec/VERY_DEEP_CHECK.md) after refreshing every source's
  vendored engine, and both are this-session-caused rather than latent.
  `themorgan/precedent-individual` commits `7e62667` and `3bbfead` carry
  `+0000` where that set's `identity.json` declares `-0300`. They are already
  on `main`, so
  [no-rewrite-for-warnings](practices/no-rewrite-for-warnings.md) says fix
  forward rather than rewrite. The set's own mechanism for this is
  `check_buenos_aires_dates.py`'s grandfathering list, and its sibling
  `commit-author` practice is explicit that entries went in **on Morgan's
  explicit instruction** — so a session adding itself to that list would be
  deciding something the practice reserves to a person.
  The underlying cause is the same one filed above: the hook that exports
  `TZ` and sets the commit identity never runs in a repo that is not the
  session's primary, so both the identity and the timezone halves fail
  together and silently.
  Separately, the engine-refresh commit that
  [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py)
  writes with `--commit` has no `Session:` trailer, which the maintainers'
  team set requires of every commit. Rewritten by hand this time; the tool
  will produce the same commit next time, so the trailer belongs in the tool.
  **The grandfathering is done** — approved by Morgan 2026-09-07, both SHAs
  exempted in `check_buenos_aires_dates.py` with the reason inline; that set
  is now 10 passed / 0 violated and 9 of 9 of its own tests. What remains is
  the cause, not the symptom, and it is the same one filed above: a hook
  cannot reach a repo that is not the session's primary, so the identity and
  timezone halves of that mechanism fail together and silently in any
  cross-repo session. **Blocked on:** a decision about which layer carries
  it, since the hook demonstrably cannot.
  The engine-refresh commit's missing `Session:` trailer is a separate,
  smaller thing and is **blocked on nothing** — the trailer belongs in
  [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py),
  which writes that commit.

- **The branch sweep and the source-refresh tool disagree about what is in
  scope, and the sweep is the narrower one.** Found 2026-09-07 by the
  [very deep check](spec/VERY_DEEP_CHECK.md), which reported four unmerged
  branches and missed a fifth.
  [tools/very_deep_check.py](tools/very_deep_check.py) scans this checkout
  plus the sources [precedent.json](precedent.json) declares.
  [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py)
  discovers every attached Precedent repo, declared or not. So
  `precedent-team-tms` — attached, a real Precedent repo, but nobody's
  declared source here — was refreshed by one tool and never swept by the
  other, and its own `claude/pre-launch-audit-fixes-7wumzx` (12 commits
  ahead) went unlisted.
  [practices/very-deep-check.md](practices/very-deep-check.md) is explicit
  that "scope is every Precedent repo in the session, not this checkout
  alone", so the tool is narrower than the practice it implements. Give it
  the same discovery `precedent_refresh_sources.py` already uses rather than
  a second one.
  **Blocked on:** nothing but the work.

- <a id="universal-code-cites-team-slug"></a>**Five universal engine files depend on a rule the universal catalogue
  does not have, and cite it in the one form the check cannot see.** Found
  2026-09-07 by the [very deep check](spec/VERY_DEEP_CHECK.md)'s pass 3.
  [tools/routing_audit.py](tools/routing_audit.py),
  [tools/precedent_source_bootstrap.py](tools/precedent_source_bootstrap.py)
  (twice), [tools/precedent_show.py](tools/precedent_show.py) and
  [tools/precedent_vendor_engine.py](tools/precedent_vendor_engine.py) each
  name `fail-gracefully` to explain why they degrade rather than fail.
  `python3 tools/precedent_show.py fail-gracefully` exits 1: the practice
  lives in `precedent-team-maintainers`, a private set, so no reader of this
  public repo — and no consumer that vendors this engine — can look it up.
  Nothing in [practices/](practices/) covers graceful degradation.

  Both halves were confirmed by running them, not reasoned about. All five
  use an *unanchored* mention (`(fail-gracefully)`, `# fail-gracefully`),
  which [practices/code-cites-practice.md](practices/code-cites-practice.md)'s
  own Rule already forbids as "a bare mention of the practice's subject with
  no way to look it up" — and which its check cannot detect, since no scanner
  tells a bare slug from ordinary hyphenated prose. Rewriting one to the
  sanctioned `practice: fail-gracefully` was tried:
  [precedent_check.py](tools/precedent_check.py) went
  from `1 passed` to `1 violated`. So the sanctioned form is *unavailable*
  here, and the rule pushes its own users into the unchecked form. The
  blindness is now declared in that check's `blind_to`; the citations are
  deliberately left alone, because rewording them is the wrong direction if
  the recommendation below is taken.

  **Recommendation: promote `fail-gracefully` to universal**
  ([spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md)), then anchor all
  five citations. A rule that five pieces of *universal engine code* depend
  on is not a team preference — the team set is simply where it was first
  written down, and
  [tools/precedent_show.py](tools/precedent_show.py)'s own comment concedes
  as much, calling itself a generalization of the personal-pack rule.

  **The practice's own `## Story` already anticipated this and named the
  condition.** It records that it was kept at team level "for a stated
  reason — general enough to want in every project, but simple enough that a
  persuasive, attributed upstream submission was not judged worth the effort
  yet. That remains the outlet if it changes." That was a cost/benefit call
  made when nothing upstream depended on the rule. Five universal engine
  files and every consumer that vendors them now do, and each inherits a
  citation that resolves nowhere. The condition the practice set for itself
  has been met, so this is no longer a novel judgment — it is the outlet the
  rule already named. It would also land complete: Detail, Why and Story are
  all substantial (an earlier version of this item claimed they were empty,
  copying a figure from
  [`migrated-practices-lost-their-stories`](TODO.md#migrated-practices-lost-their-stories)
  that was itself stale — corrected there).

  **Blocked on:** Morgan's call on the level, and nothing else. An earlier
  version of this item also named "a session rooted at
  `themorgan/precedent-team-maintainers`" — that was wrong, and written
  without checking: all three private sets are attached to *this* session and
  were when it was written. The
  [AGENTS.md](AGENTS.md) gotcha it was reasoning from says `add_repo` cannot
  attach them *mid-session from a BestPractice-rooted session*, which is a
  different statement from "they are unreachable". Check what is on disk
  before recording a blocker from a remembered rule.

- <a id="split-team-sets-by-subject"></a>**Sort the existing team and individual rules into subject-scoped team
  sets.** Decided 2026-09-08, after the cross-team drift question: a rule
  several teams need does **not** go to universal — universal is for
  opinionated rules Precedent tells the world, and a house design style is not
  one. It goes into **one team set named for its subject**, which every team
  that needs it declares alongside its own. The naming convention already
  points here: a team set is named for its **purpose**, and a roster-shaped
  name is stale the moment somebody joins. Nothing new has to be built — a
  repo can already declare several team sets, and two of them defining one
  slug is a loud refusal, which is the guard that stops a local copy creeping
  back in.

  **What is left to do is the sort itself**, one rule at a time, across
  `precedent-team-maintainers`, `precedent-team-tms` and
  `precedent-individual`: which rules are genuinely one team's, which are
  subject-scoped and want a set of their own, and which are personal to
  Morgan rather than to any team. The test per rule: *who breaks if this is
  wrong?* One team → that team's set. Everyone doing a kind of work,
  regardless of team → a subject set. One person → individual. Only this
  repository → repo-local.

  **DONE 2026-09-09**, from a session rooted in a `themorgan/` repo with all
  five sets and this repo on disk — the route
  [`attach-private-sources`](TODO.md#attach-private-sources) names, and it
  worked exactly as written.

  **The sort, and the count that made the case.** Of
  `precedent-team-maintainers`' 40 practices, 19 were about something other
  than maintaining a repository. 16 went to a new `precedent-team-writing`
  (the craft of writing for a human reader: length and emphasis, when a list
  is really a list, drafting markers, citation and linking, keeping a
  reader's material out of a deliverable that is not for them) and 3 to a new
  `precedent-team-working-style` (how a session paces work with the person).
  21 stayed. Two moved up from the individual set; **three more were proposed
  and reversed on reading the rules rather than their slugs**, each of which
  says in its own text that it is not team policy — one of them outright
  ("my preference for my own repositories, not a default I ask anyone else to
  adopt"). Moving that one would have contradicted the rule while claiming to
  enforce it.

  **The strongest single finding.** The two practices that fire on *every
  turn of every session* — the only two `tier: resident` rules in the whole
  40 — were reachable only by a repository that also declared twenty-odd
  rules about syncs, gates and branch setup. A document project therefore
  declared none of them, and the team that most needed the writing rules had
  one practice of its own. **Reach is what a set is worth, not how many files
  it holds**, which is why a 3-practice set earns its own repository here.

  **Migration for repos already on the old system is the two-step move
  [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md) prescribes**, applied
  19 times: land at the destination first, verify it there, deduplicate at
  the source second. Nothing was deleted and no rule left force for a moment.
  Every moved practice keeps its file in the old set as `status:
  deduplicated`, with `in_force_at:` naming the same slug and a `## Story`
  line saying which set now holds it. So a repo that has not yet updated its
  `precedent.json` resolves fewer practices — and the ones it no longer gets
  are each sitting in the set it still declares, saying by name where they
  went. That is the difference between a migration and a disappearance.

  **What made it safe to do at all** is the guard this item already named:
  two team sets defining one slug is a hard refusal, so one rule has exactly
  one home by construction. Verified across all four team sets after the
  move: no collisions.

  **Left alone, and NOT a duplicate — this one is worth reading before the
  next audit re-raises it.** `catalogue-carries-stories` is `active` in
  `precedent-team-maintainers` *and* `active` at universal, which every
  slug-overlap scan reports and `no-duplication` appears to condemn. It was
  in fact deduplicated on 2026-09-07 and **re-activated the same day**, for a
  mechanical reason the practice file now records in its own `## Story`: **a
  source repo consumes no catalogue**, so universal's copy never reaches a
  set like that one, and `precedent_check.py` gates every check on its
  practice being in force *there*. Deduplicating it did not defer enforcement
  to universal — it switched enforcement off.

  So the same-slug copy is not a restatement; it is the mechanism by which a
  source set puts a universal rule in force on its own catalogue, and any
  audit that reasons from the slug overlap alone will keep proposing the
  round trip that was already made and reversed. The general wart — **a
  source set must re-declare a universal practice to enforce it on itself** —
  is real and unaddressed, and belongs to
  [`practice-consistency-across-team-repos`](TODO.md#practice-consistency-across-team-repos),
  whose own note that "a copy is usually the bug" needs this counter-example
  attached to it. And item 7 stays parked: nothing in this split expresses
  a preference between two disagreeing team sources, because nothing here
  produced two sources that disagree.

- <a id="practice-consistency-across-team-repos"></a>**How one practice lives in several team repos and stays consistent** —
  **unfolded 2026-09-08, at Morgan's prompting.** Folded into
  [item 7](TODO.md#multiple-team-sources-disagree) on 2026-09-07 on the
  grounds that item 7 "had asked the same question since 2026-09-03". It had
  not, and item 7's body has never mentioned drift: item 7 asks which of two
  **disagreeing** team sources wins inside one consuming repo — a precedence
  question, parked. This asks what keeps one rule the **same** across several
  team sets that nobody resolves together — a drift question, and nothing
  addresses it. The fold is the reason this sat as a dead anchor for a day.
  (The anchor is kept either way —
  [rename-updates-links](practices/rename-updates-links.md).)

  **The drift is measured, not hypothetical.** Two sessions independently
  landed `fail-gracefully` and `bold-key-phrases` into *both* team sets on
  2026-09-07, each doing the obviously right thing. The one deliberate
  cross-repo sweep — a session holding all four repositories, searching by
  purpose and by mechanism, 2026-09-06 — found one more
  ([`headline-duplicate-retired`](TODO.md#headline-duplicate-retired)).
  Nothing runs that sweep on a schedule, and nothing runs it mechanically.

  **Morgan's proposal, 2026-09-08:** one session holding the universal repo
  plus every team and individual set, finding the same practice across
  sources, reporting where the copies have drifted, and reconciling them —
  with an identity check, so two unrelated rules that happened onto one slug
  are never merged into each other.

  Four things to weigh before building it:

  - **The identity half is already solved, in the opposite direction.** Slugs
    are identities: `resolve()` in
    [tools/precedent_resolve.py](tools/precedent_resolve.py) raises on two
    same-level sources defining one slug, and `load_source()` raises within
    one source. Two unrelated rules sharing a slug cannot survive long enough
    to be reconciled. The undetected case is the inverse — **one rule under
    two slugs** — which "rename one", item 7's cheapest remedy, actively
    manufactures.
  - **A copy is usually the bug, not the thing to keep in sync.** Two teams
    wanting the identical rule is what a universal rule looks like, and that
    was Morgan's own call on the 2026-09-07 pair: promote to universal,
    delete from both team sets. A reconcile tool should propose **promotion
    first** and a text merge second, or it will keep three copies healthy
    forever.

    **The counter-example this tool must not break, found 2026-09-09:**
    `catalogue-carries-stories` is active at universal AND in
    `precedent-team-maintainers`, and that second copy is load-bearing. A
    source repo consumes no catalogue, so universal's copy never reaches it
    and `precedent_check.py` only runs a check whose practice is in force
    *there* — deduplicating it switches the check off rather than deferring
    it. It was deduplicated and re-activated within one day on exactly that
    discovery. So **"same slug, active in two sources" is not sufficient
    evidence of a redundant copy**, and a tool that promotes on that signal
    alone will silently disable enforcement. The distinguishing question is
    whether the lower source actually RESOLVES the higher one, which the
    resolver can answer and a text-similarity score cannot.
  - **It must not be a judge-only reading pass.**
    [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md) pre-registered and
    measured that exact shape at 54% recall — worse than doing the work with
    no review pass at all. The mechanical seed already exists:
    [tools/precedent_promote.py](tools/precedent_promote.py)'s
    non-duplication criterion takes `--against PATH[,PATH...]` and scores
    word overlap across several repo roots. What is missing is running it
    pairwise over existing catalogues instead of once, at creation.
  - **The verdict has to be recorded per pair, per source.**
    [parallel-artifact-ledger](practices/parallel-artifact-ledger.md) is the
    practice for that, and several team sets carrying one rule is the case it
    describes.

  **Blocked on:** a session that actually holds every source at once —
  checked on disk this time, not recalled: no sibling clone exists beside
  this checkout, `~/.config/precedent/config.json` does not exist, and
  `add_repo` refused `themorgan/*` from this `alex137/*`-rooted session on
  2026-09-08 (*"cross-tier adds are not supported in v1"*). So the route is
  [`attach-private-sources`](TODO.md#attach-private-sources): root the
  session at a `themorgan/` repo, attach the other two same-owner sets, and
  clone the public BestPractice directly.
43. <a id="loader-comment-names-an-unvendored-check"></a>**The generated loader block
    tells every source set that a check catches drift, in exactly the repos where that
    check does not exist.** [tools/build_views.py](tools/build_views.py) writes `do not
    hand-edit this block, tools/verify_harness.py's regeneration check fails on drift.`
    into the generated block unconditionally. But `verify_harness.py` is deliberately
    not vendored into a SOURCE set —
    [tools/precedent_vendor_engine.py](tools/precedent_vendor_engine.py) says so twice,
    each time as a known consequence it is working around. So the one line telling a
    session the block is protected is false in every private set, and it is the line a
    session reads instead of checking.

    **This is [precedent_check.py](tools/precedent_check.py)'s own finding, one level
    up.** That module exists because `checked_by:` was "a claim: a string naming a script
    that existed", and its header states the principle: *"A claim nobody tested is worth
    less than no claim, because it reads as coverage."* A generated comment naming a
    check that cannot run in the repo it is generated into is the same shape, in a
    comment rather than a frontmatter field, and nothing tests it either.

    **Evidence, found 2026-09-07 in the team set.** `AGENTS.md`'s occasion index and
    `MAP.md` had been stale since `b9fae5a` rewrote `fail-gracefully`'s `occasion` and
    `index_clause` without regenerating. Nothing reported it; it was caught by hand, by
    running `build_views.py` for an unrelated practice edit and reading the diff.
    Verified identical in all three private sets: each carries the same generated line,
    none has `tools/verify_harness.py`.

    **Two fixes, and they are not the same size.** The honest one is to make the comment
    conditional — name `verify_harness.py` only where it is vendored, and elsewhere say
    plainly that regeneration is on the author and nothing here checks it. The better one
    is to make the claim true: `build_views.py` is deterministic and idempotent (verified
    — a second run on a clean tree is a no-op), so "regenerate into a temp dir and diff"
    is a cheap check, and `precedent_check.py` is now vendored into source sets and could
    host it. That one is not free: that registry is deliberately one entry per *enforced
    practice*, each owing a failure message that IS some practice's `## Rule` and a test
    that proves it fires. A regeneration check owns no practice, so it needs either a
    practice to belong to or a considered exception to that shape — which is a design
    call, not a fix. **Recommend doing the honest one now and filing the better one
    separately**, rather than letting a comment stay false while the design question
    is open.

    **Blocked on:** nothing but the work, for the first half.

- <a id="consumers-need-refresh-after-promotion"></a>**A consumer that vendors an OLD universal catalogue loses a promoted
  practice at its next sync, silently.** Found 2026-09-07, immediately after
  promoting `fail-gracefully` and `bold-key-phrases` from
  `precedent-team-maintainers` to universal.

  The shape: a consuming repo vendors universal as tracked files at a pinned
  commit, and resolves its team source live. Promotion deletes the practice
  from the team set (correctly — that is what stops the same-level
  collision) and adds it to universal. A consumer whose vendored universal
  copy predates the promotion then has it in **neither** source, and the next
  [precedent_sync_views.py](tools/precedent_sync_views.py) run rewrites
  `practices/` from what resolves — removing both rules from its catalogue
  with nothing reporting a loss, because a practice that no longer resolves
  is not a violation of anything.

  **Verified concrete, not predicted.** A private consumer repo
  vendors universal at `process/upstream`, pinned to `c7a1436` — the commit
  before the promotion. Its `process/upstream/practices/` carries neither
  practice; its materialized `practices/` still carries both, from the team
  source that no longer has them. It has not re-synced yet, so nothing is
  lost — the window is open, not closed.

  **The remedy is a vendored-catalogue refresh in each consumer**, before
  its next sync, not a change here. `process/upstream/tools/checkin.py
  update <bestpractice-clone>` is the mechanism.

  **The general lesson is bigger than these two practices**: promoting or
  moving a practice between levels is a change every consumer must be
  brought forward for, and today nothing tells a consumer that the ground
  moved. Worth considering whether
  [precedent_sync_views.py](tools/precedent_sync_views.py) should refuse —
  or at minimum say loudly — when a sync would DELETE a practice that its
  committed `MANIFEST.json` records as present, rather than doing it
  quietly. That is the same "could not check versus checked and found
  nothing" line [fail-gracefully](practices/fail-gracefully.md) draws.

  **CORRECTION, 2026-09-07: the loss is not silent, and this item said it
  was.** `precedent_sync_views.py --check` already names each one precisely —
  *"practices/fail-gracefully.md is not produced by any declared source — a
  sync would delete it (practice)"* — verified by running it against the real
  consumer. What is true is narrower: a **real** sync (`materialize()` does
  `shutil.rmtree(practices_dir)` and rewrites) announces nothing, so a
  session that syncs without `--check` and does not read the resulting
  `git status` sees no notice. The removal is visible; nothing puts it in
  front of you at the moment it happens.

  **The obvious fix was attempted and backed out, and that is worth knowing
  before someone tries it again.** Making `sync_views` refuse a removal
  unless `--allow-removals` is passed: implemented, tested against the real
  consumer (refused, naming both practices, nothing written; proceeded with
  the flag). It then failed the harness in **three separate legitimate
  flows** — a repo declaring `visibility: public`, which withholds
  private-source practices by design; a sync already carrying
  `--allow-missing-sources`, which is the same acknowledgement asked twice;
  and a cross-source fixture that re-syncs after its sources change. Each was
  fixable in isolation and a fourth appeared each time. That is the "fires on
  correct work" failure this project has measured the cost of, so the guard
  was reverted rather than shipped tired.

  What the attempt established, for whoever picks it up: the signal exists
  and is exact (`drift()` already computes it), the flag plumbing is simple,
  and **the whole difficulty is telling a stale-source removal from a
  deliberate one**. Withholding, a dropped source, and an upstream retirement
  are all legitimate removals that look identical to the tree. A workable
  version probably compares against the *committed* `MANIFEST.json` rather
  than the working tree, so it asks "did the repository lose a rule it had
  recorded?" instead of "does the tree differ from the plan?" — that was not
  tried.

  **BUILT, 2026-09-07, on the committed-manifest baseline.** A sync now
  refuses to write when it would remove a practice this repository's
  **committed `MANIFEST.json`** records and whose source is **still
  declared** — the stale-vendor case, and the one this item is about. The
  baseline is the whole difference from the reverted attempt: "the tree
  differs from the plan" is true constantly, while "this repository
  published a catalogue containing rule X and X is about to vanish" is
  narrow enough to refuse on. Four consequences, each closing one of the
  false positives that killed the first version:

  - No committed manifest — a fresh install, a scratch fixture — and there
    is no baseline, so the guard does not apply.
  - A **withheld** slug is excluded: a public repo keeps private-level text
    out of its tracked tree deliberately.
  - A slug whose recorded **source is no longer declared** is reported, not
    refused: dropping a source is a decision somebody just made.
  - A slug whose source **is** still declared, and which that source no
    longer produces, is refused. `--allow-removals` overrides it.

  Verified against the real consumer (refused, naming both practices and
  their source, nothing written) and covered by a 7-case harness test.

  **Two mistakes in building it, both worth keeping.** The first version read
  `res['practices']` as a list of records when it is a **dict keyed by slug**
  — so it computed an empty set, and the "cannot establish it, return empty"
  fallback then swallowed that, leaving the guard silently inert while
  reporting nothing. It passed its own positive control that way. A fallback
  meant to fail safe is what hid it; the unreadable case now says so out loud
  instead. Second, the test fixture deleted the team source's only practice,
  which tripped a *different*, pre-existing guard (a source gone completely
  empty) — so the fixture proved the wrong thing, just as confidently.

  **Blocked on:** the refresh itself belongs in each consumer, run under
  that repo's own gates — that consumer has an open session and its own
  deep check, and doing it from here would be the unreviewed cross-repo
  change this run has been finding all day. The engine-side guard is blocked
  on a design call (which baseline to compare against), not on the work.

40. <a id="philosophy-sync"></a>**~~Decide how `philosophy/` stays current with the notebook it came from.~~
    Settled 2026-09-07: there is nothing to stay current with.** The
    question was which of three options to take — dated snapshot,
    vendored-and-synced, or move the originals here. Morgan chose the
    third and went further: the project's own prior notes repository is retired, and
    [philosophy/](philosophy/) is the only copy of these essays. No
    manifest, no sync, no drift — by construction rather than by
    discipline. [philosophy-declares-its-source](local/practices/philosophy-declares-its-source.md)
    survived the change with its purpose rewritten: the provenance line
    is now a historical record of where the text was argued out, not a
    pointer to something live.
    **Left over, and not this repository's to do:** the notebook itself
    still exists until Morgan deletes it in GitHub's settings — no tool
    available here can delete a repository. Its 220 commits of history,
    its own `TODO.md` and its `GETTING_STARTED.md` go with it. The five
    content-side open questions were rescued into
    [philosophy/ASSORTED_NOTES.md's Open Questions](philosophy/ASSORTED_NOTES.md#open-questions) first.

    **Its `process/PRECEDENT_MIGRATION.md` was read and deliberately not
    rescued** (2026-09-07). A first pass flagged it as the one document
    worth importing, because
    [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)
    cites it as the worked example's own record. Reading it reversed that:
    it says outright that its own reusable half *"is written up generically
    upstream ... so the next dependent repo doing this same migration
    doesn't have to rediscover it"*, and its one finding of consequence —
    that a consumer's scrub gate structurally cannot pass once the
    blocklist term appears in legitimately-vendored upstream documents — is
    already recorded in
    [spec/PRELAUNCH_AUDIT.md](spec/PRELAUNCH_AUDIT.md), with the remedy.
    What remains is one repository's bookkeeping about itself: its manifest
    entries, its paused workflow, its resolver output, its own
    "audit these entries before the beta pin lifts" note. Importing 28KB of
    that into a public repo where nothing points at it would be a copy kept
    for the feeling of not having thrown anything away.

41. <a id="philosophy-profanity-divergence"></a>**Three words in `philosophy/` are masked, and there is no longer an
    original to compare them against.** The default leak blocklist bans
    profanity in this repository's public tree, and the essays carried it
    three times — in
    [philosophy/COMPANY_BUILDING_RULES.md](philosophy/COMPANY_BUILDING_RULES.md)'s
    `hire-for-drive` heading, in
    [philosophy/HUMANS_AT_OUR_BEST.md](philosophy/HUMANS_AT_OUR_BEST.md)'s
    "Drive" bullet, and inside a verbatim quotation in
    [philosophy/ASSORTED_NOTES.md](philosophy/ASSORTED_NOTES.md). This was
    filed as a *divergence* from an upstream; with the notebook retired it
    is simply an editorial decision this repository has made and now owns.
    Masking a word inside a quotation of Morgan's own speech is the part
    worth a second look.
    **Blocked on:** nothing mechanical — it needs Morgan to say whether
    masking is right for his own quoted words, or whether the blocklist
    should carve out `philosophy/` instead. Unmasking means changing the
    blocklist, since the gate blocks the push either way.

- <a id="undeclared-deprecated-files"></a>**Nothing finds a deprecated file nobody declared.**
  [decommission-deletes-files](practices/decommission-deletes-files.md) landed
  2026-09-07 with an audit ([precedent_decommission.py](tools/precedent_decommission.py))
  and a check that holds a decommissioning afterwards. Both work from a
  declaration: the audit is run by a person at the moment of decommissioning,
  and the check reads `process/decommissioned_paths.json`. Neither can look at a
  tree and say *this file is dead*. So the practice covers the moment a
  mechanism is decommissioned deliberately, and covers nothing at all in the case
  Morgan actually raised it against — a repo left alone for years, where
  the decommissioning moment passed without anyone noticing it was one.

  **One candidate was designed and rejected, so the next session does not
  re-derive it.** A check on `.github/workflows/`: a workflow whose only
  trigger is `workflow_dispatch`, or whose schedule is commented out, is a
  decommissioning someone started and never finished. It is mechanical, it is
  cheap, and it targets exactly the shape this practice was raised about.
  It was not built because it fires hardest on the one case this repo
  *deliberately* holds — every consumer's paused `bestpractice-upstream-sync.yml`,
  parked on `workflow_dispatch` on purpose per
  [`relax-the-pinned-branch-hold`](TODO.md#relax-the-pinned-branch-hold) —
  so shipping it means every consuming repo starts failing a check for
  doing what this repo told it to do. Making it honest needs a way to
  declare a pause with a stated condition for lifting it, which is a
  design call rather than a check.

  **Blocked on:** that design call. The cheaper half is not blocked and is
  worth doing first — teaching
  [very-deep-check](practices/very-deep-check.md)'s housekeeping pass to
  look for dead paths by hand, which is where a judgment a script cannot
  make already belongs.

- <a id="build-views-stdout-count"></a>**Done 2026-09-07 — `build_views.py`'s summary line reported a different
  practice count than the block it had just written.** Found merging
  [precedent-beta-v01](https://github.com/alex137/BestPractice/tree/precedent-beta-v01)
  into a feature branch: the regenerated `AGENTS.md` header read *7 of 72
  practices* while the same run printed *resident 7/69* to stdout. The
  committed artifact was the correct half; the line a session reads to
  confirm the run was the wrong one, which is the worse half to have wrong.

  The cause was a **second** `build_loader_block()` call at the end of
  `main()`, given the single-source catalogue where the block itself had
  been built from the multi-source resolve — so the token count and
  resident count were re-derived from the wrong list too, and happened to
  agree by coincidence. Fixed by removing the second computation rather
  than making the two agree:
  [build_views.py](tools/build_views.py)'s `render_agents_md()` now returns
  its own figures alongside the text, and `main()` prints those. A harness
  case runs a real write against a copy of the tree and compares all three
  printed figures against the `AGENTS.md` header it produced; reverting the
  fix makes it fail with `printed (7, 70, 377), wrote (7, 73, 377)`.

- [ ] <a id="audience-register-sharpening"></a>**Sharpen `audience-register` so the plainer register actually holds —
  three changes, all in the individual practice set, all needing the
  account owner's sign-off on the wording.** Raised 2026-09-07, after he
  pointed out he has asked for plainer replies "many many times ... today,
  yesterday, the day before", and that each re-explanation was right. The
  rule already existed and was already `tier: resident`. **The dominant
  cause was that it never loaded** — fixed the same day by
  [AGENTS.md](AGENTS.md)'s new first-tool-call banner — but three
  weaknesses in the rule itself survive that fix and would have blunted it
  anyway:

  1. **It aims at the register already being used.** Its Rule says
     *"somewhat technical ... I read code, I follow a mechanism ... I would
     rather have the real name"*, which describes the replies being
     objected to. Re-aim it at a test applicable while writing: *would a
     smart person who does not work in this repository every day need a
     follow-up question to use this sentence?*
  2. **"Gloss it in a clause the first time" licenses the actual
     failure.** One mention buys the term for the rest of the reply, so
     in-house shorthand went bare after its first outing. Explain the term
     every time it appears, in the same sentence, and accept the
     repetition.
  3. **Nothing counts a miss, and one is cleanly observable.** The
     practice argues no mechanical check is possible because a chat reply
     is not an artifact any repo holds — true for judging register in the
     abstract, but *being asked for a plainer version* is unambiguous,
     needs no judgment, and currently goes unrecorded. Treat it as a
     defect when it happens, say so, and append the offending phrase to a
     running list in that practice's own `## Story`. The list becomes the
     most useful part of the rule, being made of real sentences rather
     than descriptions of sentences.

  Worth knowing while deciding: a team set carries a same-slug
  `audience-register` requiring the **plainer** register, and team
  outranks individual, so in a project declaring that team source the
  plainer rule already wins. This repository declares a different team
  set, so the individual rule is what binds here. Changing the individual
  rule is cleaner than moving repositories between team sources.
  **Blocked on:** his approval of the new wording. It is his rule about
  how he is spoken to, and a session rewriting that unilaterally is the
  same overreach the rule exists to correct.

- <a id="push-without-the-keyword"></a>**Decide what a session does when Morgan has NOT said "Go merge".**
  **Disposition:** parked (2026-09-08, Morgan) — he has no pattern yet to
  turn into the hard rule he wants, and asked not to be asked while he finds
  one. Parked is not closed: the item stands, and the paragraph in
  [AGENTS.md](AGENTS.md) does not close it either. Unparking is his call
  ([open-item-disposition](practices/open-item-disposition.md)).
  [AGENTS.md](AGENTS.md) says two things and never joins them: a PR into
  `precedent-beta-v01` needs no sign-off from Alex, and "Go merge" means
  push what the thread agreed *without asking again*. Neither says what the
  keyword's **absence** means, so each session picks — and they pick
  differently. On 2026-09-07 this session pushed
  [`b66b660`](https://github.com/alex137/BestPractice/commit/b66b660) with no
  authorization, was told that was right, then told it is not the general
  rule: *"sometimes I don't want you to merge, like today you did a few I
  didn't."* 133 commits landed on this branch that day across five parallel
  sessions, all of them Claude's, so this is not one session's habit.

  **Three readings, so the decision is a choice rather than a re-derivation:**

  1. **Hold by default.** A session commits and stops; every push needs a
     word. Costs: work sits in a disposable container until the next
     message, and [reply-links-files](practices/reply-links-files.md)'s
     "Files touched" links do not resolve until the branch is pushed, so a
     held reply cites files nobody can open.
  2. **Push by default** — today's behaviour. The keyword then only means
     "stop asking", and the cost is exactly what prompted this item.
  3. **A line between them**, e.g. push what the thread asked for once the
     deep check passes, hold anything that adds a rule, changes a
     convention, or touches another source. Needs the line drawn precisely
     enough that five sessions draw it the same way, which is the hard part
     and the reason this is not just "use judgment".

  **Where the answer goes**, whichever it is: [AGENTS.md](AGENTS.md)'s
  "Go merge" paragraph, and the `go-merge` practice in Morgan's individual
  set (private, so named rather than linked). **Not**
  `practices/merge-authorization-keyword.md`, which this item originally
  named — that universal practice was retired hours later, on 2026-09-07,
  because the phrase is Morgan's own preference and does not belong at a
  level that binds every adopter. The retirement does not answer this
  item: what the keyword's *absence* means is still undecided, and is now
  a question about his individual practice rather than a universal one.
  Not into a chat thread either — a rule agreed in one session binds one
  session, which is the whole failure this item describes
  ([repo-is-memory](practices/repo-is-memory.md)).

  **Half of this closed 2026-09-07, and it is the half that was never the
  hard part.** Morgan stated the keyword's PRESENCE meaning in the clear —
  *"Go merge means PR & merge it and don't ask me again"* — and
  [AGENTS.md](AGENTS.md)'s paragraph now carries it verbatim instead of
  telling a session to go ask. Note what that fixed: the meaning was
  already written in this item, while AGENTS.md sent sessions to Morgan for
  it, so a session reading both got the question and the answer from the
  same repository and asked anyway. That is now one statement in the place
  a session actually reads first.

  **The ABSENCE now has an INTERIM answer, and it is deliberately not a
  rule.** Asked to choose between the three readings above, Morgan answered
  2026-09-07: *"The session should use its judgment. Todo in the future to
  make a hard rule, not that."* So until that rule exists, a session decides
  for itself whether to push or merge without the keyword, owns the call,
  and **does not ask him** — the asking is itself a cost he has named twice.

  **Read the second sentence as carefully as the first.** He wants a hard
  rule eventually, and he ruled out "use judgment" as the content of it.
  Judgment is the interim state, not the destination, so this item stays
  OPEN. A later session must not close it by pointing at the interim answer
  and calling the question settled — that would encode as permanent exactly
  what he named as temporary.

  This costs what the item said it would: the three readings note that
  judgment is the one thing that does not make five sessions draw the same
  line, which is why the incident happened. That cost is now accepted on
  purpose rather than unnoticed.

  **A fourth reading was offered and NOT chosen**, recorded so it is not
  re-derived as new: *push always, merge only on the keyword* — the branch
  and PR go up so the deep check runs and
  [reply-links-files](practices/reply-links-files.md)'s links resolve, but
  nothing lands without a word. It removes reading 1's cost and reading 2's
  both, and needs no judgment about significance. He passed on it in favour
  of judgment; it stays on the table for whoever writes the hard rule.

  **Blocked on:** Morgan, for the hard rule only — the interim answer is
  given and needs nothing further. It is a question about what he wants from
  his own sessions and has no answer derivable from the repository. Also
  still to do, and NOT doable from a session rooted in this repository:
  mirroring the settled presence wording into the `go-merge` practice in his
  individual set, so the private canonical text and this public paraphrase
  cannot drift. The cross-owner `add_repo` refusal blocks it in both
  directions (see [AGENTS.md](AGENTS.md)'s cross-tier gotcha), so it needs a
  session rooted in that set.


- <a id="blocklist-stem-not-full-name"></a>~~**Put the private consumer repo's NAME STEM into the leak blocklist, not
  its full repo name.**~~ **Done (2026-09-07)**, in the individual practice
  set — all seven repo-name patterns rewritten from `\bFullName\b` to a
  truncated stem plus `[\w-]*`. Raised after two hits of `<that repo>-local`
  — the name its repo-local practice source carried before `source-naming`
  renamed it — survived both the vocabulary sweep and `d167ada`'s
  fix-forward, and sat on the public branch from 07:02 to 21:17 that day.

  **What the fix turned out to be is not what this item assumed**, and
  [AGENTS.md](AGENTS.md)'s gotcha now carries the corrected version: the
  suffix was never the problem, because `\bFullName\b` already matches
  `FullName-local` (a hyphen is a word boundary). The leak got through on the
  repo's **short form**, so truncation is the mechanism and the trailing
  `[\w-]*` is belt-and-braces. Each stem was cut only as far as its measured
  hit count against this tree stayed at zero, and two candidate cuts that
  scored zero were still rejected as fragments an ordinary camelCase
  identifier could produce. Positive control over the two commits that
  carried the leak: the old list reports clean, the stems report three hits.
  Negative control asserts the gate's message, not just its exit code. The
  repo-reference allowlist was already switched on, with a reason on every
  allow line.

  **Nothing to do here.** The patterns and their evidence live in the private
  set by design — a list of the words you must not publish cannot be
  committed to this repository ([spec/SOURCES.md](spec/SOURCES.md),
  `python3 tools/leak_gate.py --explain`). This repo's own runs still check
  the default list only, and still say so.

- <a id="stem-note-reaches-the-sets"></a>~~**Refresh the private sets' vendored engine so the stem-coverage note
  actually runs where the blocklist lives.**~~ **WRONG, and withdrawn the same
  day it was written (2026-09-07). There is nothing to refresh.**

  The item asserted that each private set was running a stale copy of
  [tools/leak_gate.py](tools/leak_gate.py) and
  [tools/very_deep_check.py](tools/very_deep_check.py), and that the set
  holding the blocklist was therefore still reading its entries as literal
  strings. **Neither file is vendored into a source set or a consumer** —
  they are in neither `ENGINE_FILES` nor `CONSUMER_ENGINE_FILES`
  ([tools/precedent_vendor_engine.py](tools/precedent_vendor_engine.py),
  which now says so where the lists are defined). Both run only from a
  BestPractice checkout, against whatever repositories the session can see,
  so the fix reached every repo the moment it merged here.

  **How it went wrong is the part worth keeping.** The occasion index
  offers `cross-source-rollout` whenever a change touches how the engine
  works, and it is a real practice — it just did not apply, because these
  files are not part of what a source set holds. The premise went unchecked:
  one lookup in the file that defines those lists would have closed it. A
  practice firing correctly is not evidence that its premise holds
  ([search-by-purpose](practices/search-by-purpose.md) asks the same
  question one step earlier — look before concluding).

  The anchor stays rather than being deleted, so anything already linking
  here still resolves ([rename-updates-links](practices/rename-updates-links.md)).

- <a id="stem-reminder-at-the-refusal"></a>**Consider putting the stem reminder in the allowlist's REFUSAL message
  too.** When the gate refuses `owner/name`, whoever clears it is at the
  keyboard, knows a private repo is being named, and is about to write a
  reason — the cheapest moment to also add its stem. Offered alongside the
  two mechanisms that were built and not selected, so this is a deliberate
  deferral rather than an oversight.

  **Out of scope for now, with the reason:** the built pair already covers
  most of it — clones on this disk get a note every run, and repositories
  the tree names get the deep check's API-backed finding. What is left is
  the narrow case of a repo named in a document but not cloned locally,
  caught at push time rather than on request. Worth doing if that case ever
  actually bites.

- <a id="park-it-to-individual-set"></a>**Move `park-it` from this repo's local source to Morgan's individual
  set.** [local/practices/park-it.md](local/practices/park-it.md) records his standing phrase "Park
  it" — one person's preference, which by
  [layered-practice-packs](practices/layered-practice-packs.md) belongs at the individual level beside
  `go-merge`, not in a repo-local source that binds everyone working here.
  It is a level too low on purpose and says so in its own text.

  **Closed 2026-09-08 — resolved UPWARD instead, and the item's premise was
  wrong.** It assumed the only two homes were repo-local (too low) and the
  individual set (correct). Morgan chose a third: universal, on the grounds
  that these are the project's own commands rather than one person's habits
  — *"we should have our own commands we use for people who live in our
  universe."* `park-it` now lives at
  [practices/park-it.md](practices/park-it.md), the repo-local copy is
  `deduplicated` pointing at it, and the cross-owner `add_repo` blocker this
  item was waiting on turned out not to matter, because universal is
  reachable from here.

  **Disposition:** parked (2026-09-08, Morgan)

  **What was actually done**, following
  [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md): landed at universal,
  deduplicated at the source rather than deleted, and
  [AGENTS.md](AGENTS.md)'s "Park it" paragraph repointed.
  `local/tools/checks/check_park_it.py` stays repo-local by design — it
  asserts that this repository's own `AGENTS.md` still spells the phrase
  out, which is a property of this repo, not of the rule.

- <a id="vdc-pass1-partial-again"></a>**Pass 1 of the very deep check has been PARTIAL two runs
  running, on the same item.** [practices/very-deep-check.md](practices/very-deep-check.md) puts "a REAL
  consumer repository, brought up to date" at the top of pass 1 and says
  the asking goes first, because the answer may not come back. It has not
  come back twice. The 2026-09-08 run also left three cheaper halves
  unbuilt — the migration fixture, the empty neighbourhood, and the
  cross-repo permissions walk (open since 2026-09-07 as well) — because
  the update fixture it did build produced every defect it had time to fix.

  **Disposition:** wait

  The consumer-repo half genuinely needs Morgan to attach one. The other
  three need nothing but a session's time and should simply be done first
  next run, before the fresh-install fixture that has now come back clean
  twice — those do not wait on anyone and should not be recorded as if
  they did.

- <a id="branch-move-cause-unknown"></a>**Something moved this checkout off its working branch
  mid-session on 2026-09-08, and the cause was not found.** The reflog
  recorded a checkout onto `precedent-beta-v01` and a fast-forward pull,
  three minutes after a commit, with nothing asking for either.
  `precedent_vendor_engine.py seed`, `precedent_refresh_sources.py --apply`
  and `checkin.py fresh` were each replayed against a throwaway clone on a
  feature branch and **none of them moved `HEAD`**, so the three obvious
  suspects are ruled out and whatever does it is outside this repo's own
  tools. [tools/precedent_session_check.py](tools/precedent_session_check.py) now detects the drift; nothing
  prevents it. Full account in [AGENTS.md](AGENTS.md)'s gotchas.

  **Disposition:** wait

  Detection is in place and the loss is recoverable from the reflog, so
  this costs a session minutes rather than work. Worth another look only if
  it recurs — and if it does, capture `ps` and the reflog timestamp before
  doing anything else, because the missing evidence is the whole problem.

- <a id="private-set-audit-branches"></a>**Two `claude/pre-launch-audit-fixes-7wumzx` branches, in
  `precedent-individual` (19 commits) and `precedent-team-maintainers` (16),
  have not landed since 2026-09-06.** The check scripts and tests they touch
  already exist on `main`, so these are modifications rather than additions,
  and their vendored-engine half is now older than what the 2026-09-08 run
  put into both sets. The rest may still be worth having.

  **Closed 2026-09-08 — both branches deleted without merging, on Morgan's
  decision.** They were 83 and 58 commits BEHIND `main`, their substance had
  been re-done there rather than merged, and the one thing they would have
  added back is a team-level `fail-gracefully` that the 2026-09-07 run
  deliberately promoted to universal. Evidence and the three-dot-diff
  near-miss are in
  [spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md)'s pass-4 branch verdicts.

  **Disposition:** parked (2026-09-08, Morgan)

- <a id="retired-practice-filenames"></a>**Evaluate marking retired and deduplicated practice files in
  their filename, so a directory listing shows what is still in force.**
  Morgan, 2026-09-08, raised it as e.g. `retired.practice-name-here.md` —
  sortable, skippable, and it stops a listing of `practices/` reading as
  the live catalogue when part of it is not.

  **Why it was not done that day**, and both halves of the argument are
  worth keeping because the next session will re-derive one of them:

  - *Against.* Practice files cite each other by bare filename, and those
    links **travel into every consuming repo**, where nobody can repoint
    them ([rename-updates-links](practices/rename-updates-links.md) cannot
    reach across a repository boundary).
    [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md) already rejected a
    `retired/` directory on the same ground, plus two more: it puts the
    fact in two places (a path *and* a `status:` field) with nothing
    deciding which wins, and it hides withdrawn rules from the `grep`
    someone doing prior-art research actually runs.
  - *For.* The listing problem is real. The counter-argument assumes people
    read [MAP.md](MAP.md), whose generated **"Withdrawn practices"** table
    already carries status, successor and the reason each was withdrawn —
    strictly more than a filename prefix could. If the raw directory is
    where people actually look, that table is not reaching them.
  - *Morgan's fallback, and why it is worse rather than better:* renaming
    during [very-deep-check](practices/very-deep-check.md) instead of in
    real time. It is the same breakage on a delay, and it puts a rename
    sweep inside a check whose whole discipline is to report and let a
    person decide.

  **The cheaper thing to try first**, if the trigger is a raw listing:
  surface `status:` in `precedent_show.py`'s output and make MAP.md's
  withdrawn table easier to find. That costs nothing and breaks nothing.

  **Disposition:** wait

- <a id="level-repo-naming"></a>**Evaluate renaming the practice-set repositories so the level is
  visible in the name.** Morgan, 2026-09-08: *"I keep on being hesitant in
  my mind about the level filenames ... What if the structure is:
  `precedent.level-individual.me` and
  `precedent.level-team.team-name-here`."* His argument is that the current
  names do not say what they are, and that a naming scheme carrying the
  level would make the whole vocabulary system legible at a glance.

  **Not done that day, deliberately, and this is a real trade rather than a
  refusal:**

  - The clarity argument is correct. `precedent-team-tms` does not tell a
    reader that `tms` is a team name, and `precedent-individual` does not
    say whose.
  - Against it: [source-naming](practices/source-naming.md) fixes these
    names *by convention*, with [spec/SOURCE_NAMING.md](spec/SOURCE_NAMING.md)
    and a check behind it — so this changes the rule, not just the names.
  - The names are referenced from **outside** the repositories: per-machine
    user-level config paths, `precedent.json` `path` entries, sibling-clone
    assumptions like `../precedent-team-maintainers`, the `add_repo` calls
    three separate `AGENTS.md` banners instruct, and every gotcha entry that
    names one. A rename is a real sweep, and the per-container paths break
    **silently**.
  - `.me` reads as a domain suffix, and a dot in a repository name collides
    visually with a file extension in exactly the tooling that already
    splits on dots.

  **What was done instead**, as the cheaper half of the same goal: `level`,
  `source` and `level repo` are now defined in [GLOSSARY.md](GLOSSARY.md)'s
  engine-vocabulary section, which was the actual gap — the words were used
  hundreds of times and defined nowhere.

  **Disposition:** wait

- <a id="voice-and-styleguide-as-practices"></a>**Decide whether `VOICE.md`
  and `STYLEGUIDE.md` should become practices instead of local-only files.**
  Morgan, 2026-09-08: *"We have VOICE and STYLE documents; but those are
  inherited from the older RPP approach. Maybe its better that those take the
  form of practices that are in the team docs."*

  **The two files are not the same case, and the answer differs for each.**

  `VOICE.md` ships from
  [templates/VOICE.md.template](templates/VOICE.md.template) with **205
  lines of default content, unchanged**, to every project. It is generic
  writing guidance — selectivity, length, openings and endings, a banned-word
  list — and it is a practice in everything but format.

  - **For converting it.** It duplicates
    [write-like-a-human](practices/write-like-a-human.md), which is universal
    and resident: both say no throat-clearing opener, no summary nobody
    asked for, no caveat stack. Two statements of one rule drift.
  - **The strongest argument, and it is mechanical:** `VOICE.md` is declared
    LOCAL ONLY and never travels back upstream
    ([INSTALL.md](INSTALL.md) §3 and §4 both exempt it). So **every
    improvement anyone ever makes to it is stranded in the project that made
    it** — the precise failure
    [practice-export-loop](practices/practice-export-loop.md) exists to
    prevent. The template can only improve by someone editing it here, in a
    repository the person who noticed the problem is probably not in.
  - **Against converting it.** The local-only decision was deliberate, not an
    oversight: the routing evals record it as a
    [layered-practice-packs](practices/layered-practice-packs.md) call —
    a project's voice is its identity, and identity does not belong in a
    shared catalogue. That reasoning holds for the *project-specific* slice
    and not for the generic 90%.
  - **On "team docs" specifically:** a team's house style is real and belongs
    at team level, but a project's voice is not its team's voice — a book
    project's voice belongs to the book, whoever writes it. So the honest
    split is three-way, not two: **universal** for the generic writing rules,
    **team** for a team's house style, **repo-local** for a project's own
    voice target and its own overrides.

  `STYLEGUIDE.md` ships **empty**. It is a slot for hex codes, a logo path,
  font names. That is project data, never a rule at any level, and it should
  stay exactly where it is. What it may deserve is a practice *naming* it —
  "read the style guide before generating anything visual" — which is a much
  smaller change.

  **Recommendation:** convert `VOICE.md`'s generic content into the universal
  catalogue (most likely by growing `write-like-a-human` into a small family
  rather than one enormous practice), shrink the template to the
  project-specific overrides only, and leave `STYLEGUIDE.md` alone. Not done
  on the day it was raised because it touches [INSTALL.md](INSTALL.md),
  [SETUP.md](SETUP.md), the manifest's local-only registry and every
  dependent repo's instantiated copy — and because it was asked as a
  question, not an instruction.

  **DONE 2026-09-08.** Morgan: *"if it is just talk like a human rules, then
  maybe we should eliminate all that text (by default), and leave it only for
  the unique voice of the project?"* — which is the recommendation above, with
  the deletion sharpened: the generic content is not moved wholesale into the
  catalogue, it is **dropped**, because the catalogue already carries it.

  **The coverage read before deleting found two sections that nothing else
  held**, and both landed universally first so the deletion lost nothing:

  - §8's second half, *"concreteness never licenses invention"*, is
    [no-invented-specifics](practices/no-invented-specifics.md) — resident,
    because a fabricated figure passes every gate here and reads better than
    the honest sentence it replaced. It was never a voice rule; it is an
    honesty rule that happened to be written down in a writing-style file.
  - §11, *"don't overcorrect"*, is folded into
    [write-like-a-human](practices/write-like-a-human.md)'s Rule, where it
    has to sit: a rule saying *don't sound like a machine* reliably produces
    performed casualness unless the same Rule says where the correction
    stops.

  **And the read found a live conflict, which is the argument neither side of
  this item had made:** the template's formatting section said *"no bold
  inside paragraphs, and no bolded thesis sentence"*, while
  [bold-key-phrases](practices/bold-key-phrases.md) — universal and resident,
  so in front of every session from the first turn — says to bold the key
  phrases by default. Every project installed from this template carried both
  instructions at once. **A local copy of a generic rule does not merely go
  stale; it argues with the live one**, and nothing had noticed because
  nobody re-reads a file that shipped with sensible defaults.

  `STYLEGUIDE.md` is unchanged, as recommended: it ships empty, it is project
  data, and it is not a rule at any level.
42. <a id="upstream-notice-silent-when-rooted-above"></a>**The upstream-carry
    notice is silent in exactly the layout this project requires, and nothing
    reports its absence.**
    [tools/precedent_upstream_check.py](tools/precedent_upstream_check.py)
    (landed 2026-09-08) says at session start whether Alex has moved `main`
    since the last carry. It rides
    [.claude/hooks/session-start.sh](.claude/hooks/session-start.sh), so it
    does not run when the harness roots the session one directory ABOVE this
    repo — which is what happens whenever the sibling clones a team source
    needs are laid out alongside it, and is the gotcha that already cost a
    whole session's replies on 2026-09-08.

    **The failure is silent in the way that matters: no notice and "nothing
    changed" render identically.** A session in that layout reads no line,
    concludes `main` has not moved, and is wrong exactly when it counts.
    `python3 tools/precedent_upstream_check.py` by hand is the fallback, and
    a fallback nobody knows to reach for is not one.

    **Queued rather than done because it changes a different tool's
    contract.** [tools/precedent_session_check.py](tools/precedent_session_check.py)
    reports *guarantees a SessionStart hook established*, tested by their
    effect; "you were told whether upstream moved" is not a state a later
    process can observe, so it does not fit that shape without deciding what
    that tool is for. Its `--apply` path already re-runs `session-start.sh`
    and therefore already prints the notice — what is missing is the
    REPORTING line that tells a session the notice never arrived.

45. <a id="small-calls-vs-brainstorm"></a>**`small-calls` tells a session to commit during a brainstorm, and
    nothing mechanical stops it.** Opened 2026-09-08 alongside
    [brainstorm-holds-commits](practices/brainstorm-holds-commits.md), and
    **corrected the same day** — the first version of this item said the team
    rule "wins on precedence," which is wrong. `PRECEDENCE` is
    `team > repo-local > individual > universal` **by slug**, and these are
    different slugs, so neither overrides the other. Both are simply in
    force, nothing reports a conflict, and `severity: blocking` would not
    change that either — it is a same-slug mechanism too.

    So the conflict is semantic, not mechanical: a session holding both reads
    *"Default to continuing, not asking… make the call and note it"* beside
    *"write nothing to the repository until they say to."* Committing a
    captured open item is exactly the shape `small-calls` calls small —
    cheap, reversible, keeps the work moving — and that reading is what
    produced the incident, twice in one thread.

    **Resolved for now in the universal practice's own text**, which names
    `small-calls` and says the brainstorm state narrows it. Both rules are in
    front of the session, so the one that addresses the other by name is the
    one that wins in the moment, and that needed no access to the private
    team source. **Still worth a clause in `small-calls` as belt-and-braces**
    — an exception naming the brainstorm state, the same way its Rule already
    carves out credentials and production. **Blocked-on:** read-only access
    to `precedent-team-maintainers` from this session (`cross-source-rollout`).
    Whoever takes it should check the individual set for the same shape.

46. <a id="decision-strength-private-sources"></a>**Carry `decision-strength` into the two private practice sets.** The
   `strength:` frontmatter key, the `Weak yes` phrase and the
   `decision-strength` check landed universal on 2026-09-09
   ([decisions/2026-09-09-decision-strength.md](decisions/2026-09-09-decision-strength.md)).
   Two things the private sets need that this repo cannot do for them:
   **their own practice files carry `approved_by:` with no strength**, and
   nothing there is backfilled either (that is the rule, not an oversight) —
   but every practice landed in them *from now on* should carry the mark, so
   whoever has them attached should confirm their vendored
   [tools/precedent_check.py](tools/precedent_check.py) is current enough to
   register the check, since a stale vendored engine simply will not run it
   and will report nothing. **And the individual set is where a standing
   personal rule about how approvals are recorded would live** — check
   whether one already contradicts this, particularly anything that treats a
   recorded approval as final by default.
   **Blocked-on:** read-only access to `precedent-individual` and
   `precedent-team-maintainers`, neither of which this session could attach
   (`add_repo` refused with *"cross-tier adds are not supported in v1"*)
   (`cross-source-rollout`).

47. <a id="whatsapp-bridge-research"></a>**Research the WhatsApp bridge properly, or drop it.**
   [spec/SPECULATIVE_WHATSAPP_BRIDGE.md](spec/SPECULATIVE_WHATSAPP_BRIDGE.md)
   designs a bot that gives each participant a private WhatsApp thread and
   commits what they say into a project repository — the hub-and-spoke shape
   that keeps the whole thing on Meta's official interface rather than a
   reverse-engineered client. **Every platform claim in it is unverified**,
   and the document says so throughout: the messaging-window rules, template
   approval and pricing, whether virtual numbers are accepted for
   registration, and what business verification actually demands. What is
   needed is the document's own phase 0 — register a test number, send and
   receive one message, and read the current rules off Meta's live
   documentation rather than off a session's recollection
   ([no-invented-specifics](practices/no-invented-specifics.md)). The three
   open questions at the foot of that document are downstream of it and
   should not be answered before it.
   **Blocked-on:** a Meta Business account and a dedicated phone number,
   neither of which exists yet and neither of which a session can obtain —
   phase 0 is an errand for a person, not a task an agent can finish. It is
   queued rather than done for that reason alone. It carries no disposition,
   so it is `wait` ([open-item-disposition](practices/open-item-disposition.md)):
   nobody chases it, and nobody raises it unless Morgan asks.

48. <a id="audit-trail-item-placement"></a>**Confirm where the audit-trail item belongs in
   [philosophy/AI_GOVERNANCE_TO_COCREATE.md](philosophy/AI_GOVERNANCE_TO_COCREATE.md).**
   Morgan's 2026-09-09 batch asked for *"Version Control and an Audit
   Trail"* to be added under **Verification**, and, two items later, for
   **Verification** to be dissolved — its one existing item moved to
   **Voice & Output**. Both instructions were followed; the new item had to
   land somewhere, and this session put it in **Memory & Context**, next to
   `durable-state-default`, as the closest surviving home. That placement
   is a session's judgment call, not his — the other plausible home is
   **Keeping the Corpus Honest**, and a third answer is that Verification
   should have survived holding the new item alone.
   **Resolved 2026-09-10, `strength: decided`.** Morgan, asked to choose
   between leaving it in **Memory & Context**, moving it to **Keeping the
   Corpus Honest**, or reviving **Verification** to hold it: *"#1 that's
   fine."* The placement stands as made. Recorded `decided` rather than
   `assented` because he chose from options laid out for him
   ([decision-strength](practices/decision-strength.md)), which is the
   difference between the two.

49. <a id="cross-owner-add-repo-push"></a>**Measure whether `add_repo` refuses a cross-owner attachment in the
   REVERSE direction, with `access: "push"`.** Every measurement so far ran
   one way — from a session rooted in this repository, reaching for a
   private practice-set repository under another owner — and the refusal
   ("cross-tier adds are not supported in v1") is well established there,
   including as a session's very first tool call and, as of 2026-09-09, at
   `access: "push"` as well — so nothing about THIS direction is still worth
   re-testing. The other direction is
   still unknown, and it decides whether the two-session split is permanent
   or an artefact: if a session rooted in a private set can attach this
   repository with credentials, one session can hold every private source
   *and* push here, and the token work stops mattering.
   Two attempts on 2026-09-09 failed to answer it, both for reasons that
   are now their own gotchas: the first asked for `access: "read"`, which
   short-circuits on the anonymous git proxy for a public repository and
   never reaches the authorization check at all; the second could not run
   because the spawned session had lost the tool itself mid-run. **The exact
   call that settles it** is `add_repo` with `access: "push"` for
   `alex137/bestpractice`, made from a session rooted in a private
   practice-set repository, as that session's opening turn.
   **Blocked-on:** a session rooted under the other owner, which this
   repository's sessions cannot start for themselves — and, given the
   tool-loss above, one where a person can read the answer out of the
   transcript. It carries no disposition, so it is `wait`
   ([open-item-disposition](practices/open-item-disposition.md)).

50. <a id="source-hook-drift"></a>**Decide whether a drifted-but-present session hook in a practice-set
   source gets brought up to canonical automatically.** Measured 2026-09-09
   across the five private sets: every declared hook exists and is
   executable, so nothing is broken — but one set's `freshness-guard.sh` is
   an older, shorter build supporting only `session-start` and `pre-write`
   (its settings.json wires no `UserPromptSubmit` to match, so it is
   self-consistent, not damaged), and `commit-identity.sh` is one version
   behind in all five, which is the signature of canonical moving on after
   installation.
   [tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py)
   restores a hook that is declared and *missing*; it deliberately does not
   touch one that is present, because overwriting a working guard changes
   what blocks a session, and a set may be sitting on an older build for a
   reason. The question is whether hook content should join the vendored
   engine as something `--apply` keeps current, with the same
   review-and-publish rules, or stay a per-set decision.
   **Approved 2026-09-09, `strength: assented`.** Morgan: *"Okay let's
   follow your advice. Make the changes you recommended in all the repos you
   recommended"*, and, in the same message, *"Except don't yet update the
   vendored-in versions; we'll make some changes in some other threads
   first."* Both halves are authorized — refresh `commit-identity.sh` across
   all five sets, and bring the older `freshness-guard.sh` up to canonical
   including the `UserPromptSubmit` wiring it currently lacks — and **none of
   it is carried into the sets until those other threads land.** Recorded
   `assented` rather than `decided` because it is agreement to this session's
   own proposal, not him choosing it independently
   ([decision-strength](practices/decision-strength.md)).
   **Confirmed independently 2026-09-11**, by the very deep check's new
   `BOOTSTRAP DRIFT` section on its first real run: regenerating each set
   with today's generator and diffing it found `commit-identity.sh`
   differing from canonical in every set it could see, and
   `freshness-guard.sh` differing in `precedent-individual`. Two mechanisms
   that share no code now say the same thing, so the measurement above is
   not an artifact of how it was taken.
   **Blocked-on:** those other threads first, then a session rooted under the
   sets' own owner to carry it out — this repository's sessions cannot push
   there, re-confirmed 2026-09-09 by `add_repo` refusing at `access: "push"`.
   It carries no disposition, so it is `wait`
   ([open-item-disposition](practices/open-item-disposition.md)).

51. <a id="sync-refuses-a-rewind"></a>**Make `precedent_sync_views.py` refuse a sync that would rewind a
   practice's content, not just one that would remove the practice
   outright.** It already refuses at practice granularity: `_lost_practices`
   blocks a write that would remove a practice the committed
   `MANIFEST.json` records whose source is still declared. The 2026-09-09
   incident slipped underneath that, because the practice file still
   existed and only its CONTENT went backwards — a Story block and a clause
   of the Rule, replaced by an older revision of the same file.
   **Do not build this as "refuse a sync that deletes text."** A legitimate
   practice edit deletes text, and that tool's own comments record that a
   broader first attempt at this died of false positives. A content hash
   cannot tell an edit from a rewind either: both look like a different
   hash. What distinguishes them is the source's own commit, which the
   manifest does not currently record. So: record the source commit per
   source at sync time, and refuse when the incoming commit is an ancestor
   of the recorded one.
   **One trap to design around:** `git merge-base` on a shallow clone
   reports "no common ancestor" for branches that genuinely share history
   (see [AGENTS.md](AGENTS.md)'s gotcha). The ancestry test needs a bounded
   deepen and must degrade honestly rather than reading exit 1 as
   "unrelated".
   **Approved for later, `strength: assented`** (2026-09-10, Morgan): he
   approved the branch pin, the off-branch report and the `--repo` refusal
   as one pass and left this one queued. Recorded `assented` rather than
   `decided` because it is agreement to this session's own proposal
   ([decision-strength](practices/decision-strength.md)).
   **Blocked-on:** nothing external — it is queued for size, not for
   permission. It carries no disposition, so it is `wait`
   ([open-item-disposition](practices/open-item-disposition.md)).
52. <a id="source-checks-adopt-engine-helpers"></a>**Move the two private practice sets' checks onto the engine helpers
   added 2026-09-10.** Three source-supplied checks were found broken by a
   real §0 install into a fresh private repository, and each one's cause
   was the same shape: a check re-deriving from private assumptions
   something the engine can answer correctly for every install model. The
   engine halves are done and covered here; the check halves live in
   repositories this repo cannot edit.
   - `check_no_stale_counts.py` (`precedent-team-writing`) excludes a
     vendored mirror via its own `_mirrored_prefixes()`, which reads
     `process/manifest.json` — §1's bookkeeping, and INSTALL.md §0 step 5
     says to skip it. In a §0 install the exclusion evaporates and the run
     reports Precedent's own historical prose as stale ("states 34
     practices, but practices currently holds 121"), none of it actionable.
     Replace that helper with
     [`precedent_resolve.mirrored_prefixes()`](tools/precedent_resolve.py),
     which reads `precedent.json`'s declared source paths as well and is
     authoritative in exactly the repos the manifest is missing from. The
     downstream workaround — a `process/manifest.json` carrying only an
     `upstream` block, written purely to feed the old signal — comes out
     with it.
   - `check_commit_author.py` and `check_buenos_aires_dates.py`
     (`precedent-individual`) both compute from an `identity.json` at the
     CONSUMING repo's root and report a VIOLATION when it is absent —
     while `check_commit_author.py`'s own 2026-09-07 comment says a shared
     consuming repo must not have one. Both are therefore permanently red
     in any shared repo, with the fix forbidden by the same file that
     demands it. Replace the root read with
     [`precedent_resolve.declared_identity()`](tools/precedent_resolve.py)
     and turn its `NoDeclaredIdentity` into `raise NotApplicable`: a
     violation should mean "a commit here has the wrong author", not "this
     repository is shared".
   **Also worth doing in the same pass:** audit the rest of both sets'
   `tools/checks/` for the same §1-only assumption. `no-stale-counts` was
   found because it fired, not because anything looked for it, and nothing
   in either set distinguishes "reads a §1 path" from "reads a path".
   **DONE 2026-09-10.** Three sessions, one rooted in each private set
   (the cross-tier refusal is per OWNER, so a session rooted in a
   `themorgan` repo reaches its siblings; one rooted here never will).
   Open pull requests carry the work, each awaiting an approver's yes per
   that set's own `approvers.json` — none was merged, correctly:
   `precedent-individual` #60, `precedent-team-writing` #4,
   `precedent-team-maintainers` #36, `precedent-team-tms` #16,
   `precedent-team-working-style` #4.

   **The audit widened past what this item asked**, and was worth it. It
   was scoped to the two sets holding known-broken checks; it ran across
   all five, and found **eight more instances in sets nobody had
   suspected** — the item's own reasoning ("found because it fired, not
   because anything looked for it") applied to itself. Among them:
   `check_light_check.py` in `precedent-team-maintainers`, whose §1-only
   link exemption produced **174 unactionable findings inside the mirror**
   in a §0 fixture, 0 after; and four checks across three sets that printed
   `SKIPPED` and returned exit 0, which the runner recorded as a PASS —
   the "empty input set printing OK" failure
   [tools/precedent_check.py](tools/precedent_check.py)'s own docstring
   says has bitten this project four times. `precedent-team-tms` and
   `precedent-team-working-style` supply no checks at all, established by
   search rather than inferred from a missing directory, and each recorded
   the clean result so nobody repeats the pass.

   **One real defect in the engine half came back from it**, and is fixed
   here: `declared_identity()` shipped in
   [precedent_resolve.py](tools/precedent_resolve.py), which is
   `CONSUMER_ENGINE_FILES`-only because a practice set resolves no
   catalogue — so the two checks this item exists to fix went from
   enforcing to SKIPPED *inside `precedent-individual` itself*, the one
   repository that most certainly HAS an identity. It now lives in
   [precedent_identity.py](tools/precedent_identity.py) in `ENGINE_FILES`,
   re-exported from the resolver. A set picks it up on its next
   `precedent_vendor_engine.py` refresh, with no further change on that
   side.

   **A second engine defect came back on 2026-09-10, after this item was
   closed, and it is the mirror image of the one above.** The audit this
   item describes swept all five private sets for the §1-only assumption
   and never swept THIS repo's own `tools/`, because the engine half was
   recorded as done the moment `mirrored_prefixes()` existed — writing the
   authority is not the same act as calling it. Six engine sites were still
   matching the literal `process/upstream/` to decide what they mirror:
   [doc_lint.py](tools/doc_lint.py)'s `VENDORED_PREFIXES`, three in
   [precedent_check.py](tools/precedent_check.py) (`technical-describes-people`'s
   skip list, `rename-updates-links`' received-file exemption, and
   `_open_item_disposition`'s TODO walk), its centralized `_is_vendored()`
   feeding four more changed-markdown checks at once, and
   [very_deep_check.py](tools/very_deep_check.py)'s tracked-text walk, which
   applies the same literal to every repo in force regardless of that repo's
   install model. All six now ask the engine.
   **Encoded so there is no seventh** ([convention-to-audit](practices/convention-to-audit.md)):
   `verify_harness.py`'s `check_no_engine_tool_hardcodes_a_mirror_path()`
   fails any `.startswith()`/`.endswith()` call in `tools/*.py` whose
   argument names that path, scanning all 49 tools. Prose, comments and the
   two documented import-failure fallbacks stay legal, since only a
   path-matching call is a decision.

53. <a id="review-skill-level-permissions"></a>**Review the whole
   technical/non-technical permission split, now that the pieces are in
   three separate places.** Asked for by Morgan on 2026-09-10, closing the
   thread that produced the split: *"note a TODO to review the 'technical vs
   nontechnical' permissions later."*

   **What the split now is.** A non-technical contributor is restricted by
   their GitHub collaborator role (Triage or Read, never Write), which GitHub
   enforces server-side, and by their own session or environment
   configuration — a dedicated `environment_id`, per-session settings, or an
   untracked `.claude/settings.local.json`. Nothing restricting them lives in
   a tracked file any more:
   [templates/document-project/](templates/document-project/)'s
   `.claude/settings.json` denies `rm` alone, which is not role-specific.
   [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
   Step 3 is the specification;
   [practices/technical-describes-people.md](practices/technical-describes-people.md)
   is the rule that keeps a per-person restriction out of a shared file.

   **What is worth reviewing, and why it is a review rather than a fix.**
   Three things came up while the split was being made and none was decided:

   - **The tracked deny list was an accidental backstop against a mis-set
     GitHub role**, and removing it means instantiation step 5's role
     assignment now carries that weight alone. Nothing checks it.
   - **The per-person layer is a manual README step** (instantiation step 6),
     so it can simply be forgotten. The contributor is still blocked by their
     role if it is — they just get a worse error — but nobody has decided
     whether that is acceptable or whether the step should be mechanical.
   - ~~**The spec file still carries the project-vs-person slippage in its
     own filename.**~~ **Fixed 2026-09-10**, together with two documentation
     guides named for their readers' skill level, after Morgan restated the
     point directly: *"WE SHOULD NOT MAKE A DIFFERENCE BETWEEN TECHNICAL OR
     NONTECHNICAL PROJECTS/DOCUMENTS."* `NONTECHNICAL_TEAM_PRACTICE_CAPTURE`
     → [spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md](spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md),
     `HOW_TO_USE_THIS_TECHNICAL` →
     [documentation/HOW_TO_USE_THIS_DEVELOPERS.md](documentation/HOW_TO_USE_THIS_DEVELOPERS.md),
     `HOW_TO_USE_THIS_NONTECHNICAL` →
     [documentation/HOW_TO_USE_THIS_EVERYONE_ELSE.md](documentation/HOW_TO_USE_THIS_EVERYONE_ELSE.md).
     [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
     is correct as it stands — it names a contributor, who is a person, and
     the practice's own check exempts exactly that form.

   **blocked-on:** Morgan — every open question here is a policy call about
   how much protection a forgettable manual step may carry, not something a
   session can settle by reading the tree. He named the reason it waits
   rather than the reason it is hard: *"it requires deeper thought of mine
   and I can't do it now because I still have a dozen claude tabs open and I
   want to wrap up the repo_add issues, the voice issues etc first."* So the
   blocker is his attention, and the queue ahead of it is real work he has
   already named.

   **Disposition:** ask (2026-09-10, Morgan asked for the review himself)

54. <a id="stale-days-does-not-travel"></a>**Decide whether the four private
   practice sets should declare their own `branch_stale_days`.** Found
   2026-09-10 by the first real cross-repo run of the widened branch sweep
   ([practices/very-deep-check.md](practices/very-deep-check.md), pass 4),
   in a session that had all four sources resolved.

   **What was measured.** BestPractice reads its declared 30, so its stale
   list is the two-or-three branches nobody has touched in a month. None of
   the four sources declares the key, so each falls back to the engine's
   conservative default and their section headings read `>= 90 days`. It
   changes no answer today — the oldest merged branch in any source is 10
   days, so at 30 those lists would still be empty — which is exactly why
   it is an open item and not a bug: it is latent until the first source
   branch crosses 30 days, and then it is silent.

   **Both answers are defensible, which is why nobody should pick one from
   here.** Per-repo declaration is the design working as written
   ([constants-are-risk-inputs](practices/constants-are-risk-inputs.md)) —
   a set's cadence is genuinely its own, and a repo that releases weekly
   wants a different number from one that does not. Against that: all five
   repositories are one person's, worked in the same sessions at the same
   pace, and a threshold that differs across them by *omission* rather than
   by choice is the kind of accident this key exists to make visible.

   **blocked-on:** the four sets are under a different owner, so this cannot
   be done from a session rooted in this repository at all — `add_repo`
   refuses the cross-owner attachment (confirmed again 2026-09-10, matching
   the AGENTS.md gotcha). It needs a session rooted under that owner, which
   is a person's act.

   **Disposition:** wait (2026-09-10, Morgan) — raised with him in the
   thread that found it and not yet answered. Left at `wait` deliberately:
   only the person an item waits on may set it to `ask`, and a session
   stamping that for him is the session giving itself permission to chase.

55. <a id="private-owner-allowlist-inert"></a>**The repo-reference allowlist is
   inert here, and this public tree names the account that owns the private
   practice sets.** Found 2026-09-10 while answering a question about
   `PRECEDENT_SOURCE_BASE_URL`.

   **What is actually there.** [INSTALL.md](INSTALL.md) §8 explains that the
   base URL is an environment variable precisely so that **no tracked file
   names the account owning the private sets**. That is not true of this
   repository as it stands: `.claude/hooks/precedent-individual-bootstrap.sh`
   is tracked and carries the individual set's full URL, account included,
   and the same account name appears across a dozen files under
   [spec/](spec/). Every one of those five repositories is private.

   **Why nothing caught it — and the first answer written here was wrong.**
   This item originally said the private-owner allowlist had never been
   declared, citing [tools/leak_gate.py](tools/leak_gate.py)'s `NOTE: ... the
   repo-reference allowlist is INERT`. **That was a misreading, corrected
   2026-09-10** when a session rooted in the individual set read the real
   blocklist and found the declaration present and switched on. The gate had
   been reading `leak-blocklist.default.txt` — the committed fallback — in
   every session that could not reach the private list, and reporting what
   was missing from *that* file. The run's own summary named the fallback two
   lines below the notice, and the session that wrote this entry read past
   it.

   So the allowlist is **armed wherever the private list is reachable, and
   inert everywhere else** — which is every session without
   `PRECEDENT_GIT_TOKEN` or an exported `PRECEDENT_LEAK_BLOCKLIST`. The
   notice now names which of the two states it is in, since their remedies
   are opposite and it used to render identically for both.

   **What is not claimed.** That this is worth acting on. The names are
   already published and in git history, so nothing here is recoverable by
   editing the tree, and [no-rewrite-for-warnings](practices/no-rewrite-for-warnings.md)
   rules out rewriting published history to chase it. The forward question is
   only whether to switch the allowlist on and work through what it flags, so
   the NEXT such name is caught before it lands.

   **Half of it is closed (2026-09-10), and it was the half with teeth.**
   Morgan approved both moves the same day. Of the 100 mentions, exactly
   **one was functional** — the hook's `DEFAULT_REPO_URL` — and it is gone:
   the URL is now derived as `$PRECEDENT_SOURCE_BASE_URL/precedent-individual`,
   which needs no new variable because
   [source-naming](practices/source-naming.md) fixes that set's name for
   everybody and the base URL already carried the account for the team sets.
   The template was fixed in the same commit, so no adopting repo
   instantiates the defect again. `verify_harness.py`'s
   `check_public_tree_bakes_in_no_owner_account` now fails any tracked
   `.sh`/`.py`/`.yml` in a `visibility: public` repo that hard-codes an
   account before a declared set name — verified to catch the original line
   by restoring it.

   **What is actually left, now that the allowlist turns out to be armed.**
   Two things, both his.

   First, **`themorgan/precedent-individual` is pre-allowed in that
   blocklist**, which is exactly what
   [templates/leak-blocklist.txt.template](templates/leak-blocklist.txt.template)
   tells people not to do — an allow line for a personal set discloses that
   the set exists. The existing reason is not empty (the name is already
   declared as a source in this repo's [precedent.json](precedent.json)), so
   this is a real trade-off and a deliberate removal, not an oversight to
   sweep. Removing it makes the audit report that name on every run.

   Second, **nobody has yet run the armed gate against this tree.** That
   needs one session holding both the private blocklist and this repository,
   which is the `PRECEDENT_GIT_TOKEN` configuration — not a session rooted in
   the individual set, which cannot attach this repo at all.

   The ≈99 prose mentions are deliberately NOT being scrubbed either way:
   naming which repository an incident happened in is the value of the
   record, the account is already published, and a private repo answers 404
   to a stranger regardless.

   **blocked-on:** Morgan — the blocklist file lives in his individual set,
   under a different owner, so this cannot be done from a session rooted
   here at all.

   **Disposition:** wait (2026-09-10, Morgan) — the code half is done; the
   remaining half needs a session rooted in his own account.
53. <a id="retire-a-practice-source"></a>**Write the retirement sequence for a practice SOURCE, from the one real
   run.** `precedent-team-tms` was retired 2026-09-10 — the first time a
   whole source has been taken out of service rather than a file or a
   directory inside one, which is what
   [decommission-deletes-files](practices/decommission-deletes-files.md) and
   [tools/precedent_decommission.py](tools/precedent_decommission.py) cover.
   [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md) covers moving a
   practice between levels and stops there.

   **The ordering is the whole of it, and it is the reverse of the obvious
   one: remove the declarations first, delete the repository last.** A
   consumer that still declares a source whose repository is gone gets
   [tools/precedent_sync_views.py](tools/precedent_sync_views.py)'s refusal —
   *"refusing to WRITE from an incomplete source set … Syncing anyway would
   DELETE every practice those sources contribute"* — which is the right
   refusal and an avoidable one. Delete last and no consumer ever sees it.

   **What the run established, worth writing up as procedure:**
   - Move the practices out first, per MOVING_PRACTICES.md's two-step (land
     at the destination, verify it THERE, then deduplicate at the source).
     Precedence is by LEVEL, not by set, so a move between two team sets
     preserves any override of an individual-level same-slug practice.
   - Check the destination does not already define the slug. Two sources at
     the same level claiming one slug is a hard refusal, not a merge.
   - Then strip every declaration — templates first, since a template is
     what makes the NEXT repo declare a dead source.
   - Then delete the repository.

   **Blocked-on:** nothing; it is queued for size rather than permission.
   The sequence above is already true and already executed once, so this
   item is writing it down where the next retirement will look, not
   deciding it. Disposition `wait`
   ([open-item-disposition](practices/open-item-disposition.md)).

56. <a id="deduplicate-practice-links-travel"></a>**Deduplicate
   `practice-links-travel` in `precedent-individual`, now that it is in force
   at universal.** Landed here 2026-09-11 as
   [practices/practice-links-travel.md](practices/practice-links-travel.md),
   with a check in [tools/precedent_check.py](tools/precedent_check.py) and
   134 links repaired across 42 practice files.

   **This is step 2 of [spec/MOVING_PRACTICES.md](spec/MOVING_PRACTICES.md)'s
   two-step, and it is deliberately not done.** Step 1 lands at the
   destination; step 2 sets the source copy to `status: deduplicated` with
   `in_force_at: practice-links-travel` and one line in its `## Story` naming
   where it went. Skipping it leaves two copies of one rule at two levels,
   with individual precedence quietly winning — the state the ordering exists
   to pass through briefly, not to sit in.

   **What the other session needs to know before it does it.** The universal
   text is NOT the individual text carried across: the session that landed it
   could not reach that repository, so it wrote the rule fresh from a
   measurement and a description of the original. Read both before
   deduplicating — if the individual copy says anything the universal one
   does not, that sentence has to move up, not disappear. The one place the
   two are known to differ on purpose is the remedy: a private set de-links
   and keeps the backticked path, because an absolute URL would publish the
   private repository's name into every consumer; this repository is public
   and links absolutely. The universal file says so in as many words, so the
   individual set is not losing that reasoning by going away.

   **Its check script goes too.** `tools/checks/check_practice_links_travel.py`
   in that set skips every practice whose source is not the individual set,
   which is what made the universal catalogue unexamined by anything for as
   long as the rule has existed. Once the universal check is in force there
   is nothing left for it to look at.

   **DONE 2026-09-11.** The copy in `precedent-individual` is
   `status: deduplicated`, `in_force_at: practice-links-travel`, and its check
   script is gone from that set's `tools/checks/`. Its `## Story` records the
   line-by-line comparison this item asked for and raised four things the
   universal text was missing; all four are carried up as of
   [PR #198](https://github.com/alex137/BestPractice/pull/198). One of them
   was a real defect — the universal check did not know a check script's own
   test travels, which that session measured as 12 false violations across 6
   practice files, each one repaired by an absolute URL into a private
   repository.

   **What unblocked it, and it is worth knowing for the next cross-owner
   item:** `PRECEDENT_GIT_TOKEN` reached a session rooted here for the first
   time, so the private sources clone at session start. A session in this
   repository can now READ that set directly and does not need a person to
   carry findings between windows
   ([findings-return-through-repo](practices/findings-return-through-repo.md)).
   Pushing to it is still cross-owner and still needs a session rooted there.

   **Historical blocked-on:** `precedent-individual` is under a different
   owner and could not be attached to the session that landed this — the standing cross-owner
   `add_repo` refusal, and no `PRECEDENT_GIT_TOKEN` in that environment. It
   needs a session rooted in that repository, which is a person's act
   ([cross-source-rollout](practices/cross-source-rollout.md): not attached,
   so it is queued rather than done).

   **Disposition:** wait — nobody is being chased for it, and the rule is in
   force in the meantime
   ([open-item-disposition](practices/open-item-disposition.md)).

57. <a id="session-practices-reports-unresolved-sources"></a>**`.precedent/SESSION_PRACTICES.md` can report a source as unresolved that
    resolved fine minutes later — and a session reading it believes those
    practices are absent.** Measured 2026-09-11: the session-start hook
    reported all three team sources as *"has no practices/ directory"* and
    wrote that into the generated file's "Sources that did not resolve"
    section, while `precedent_resolve.py`, run by hand in the same session,
    resolved all three and put their practices in force. The clones were on
    disk with `practices/` present. So the file was written before the
    clones finished, not because anything was wrong with them.

    **This is the file's most dangerous possible failure**, because it is
    the one a session trusts to know what binds it: it says in as many
    words that a non-resolving source is *unknown, not "that source has no
    rules"* — and then a session reads the list and works as if the rules
    were absent. That is the same cost as
    [the "no individual source resolved" gotcha](AGENTS.md), arriving
    through a file that looks authoritative.

    The fix is probably ordering (write the file after the clone step, or
    regenerate it once the clones land) but **nothing here is diagnosed** —
    the hook ran once, before the first turn, and cannot be re-run in the
    same container to watch it happen.
    **Blocked-on:** a fresh session to reproduce the ordering, since the
    failure only exists at session start.
    **Disposition:** wait
    ([open-item-disposition](practices/open-item-disposition.md)).

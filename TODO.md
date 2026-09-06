# TODO — open items for BestPractice itself

Dependent repos keep their own TODO.md (from
[templates/TODO.md.template](templates/TODO.md.template)); this one tracks
the upstream layer. Ordered by priority.

1. **Lean further into GitHub Actions as the enforcement layer.** The
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
2. **Evaluate GitHub Issues for open items.** Mirroring or replacing
   TODO-file items with Issues would let shell-less assistants and phone
   users browse, discuss, and close work items natively. Needs a
   convention for keeping Issues and the repo-is-the-memory principle
   consistent (an Issue is not on `main`).
3. **Re-verify plain-ChatGPT write support.** As of 2026-08,
   [MOBILE.md](MOBILE.md) treats writing (branches, file updates, PRs)
   from a plain GitHub-connected ChatGPT conversation as not reliably
   available and documents a split workflow instead. Re-test when
   OpenAI's connector capabilities change, and update MOBILE.md either
   way.
4. **Verify a Grok workflow.** Untested as of 2026-08 — see
   [MOBILE.md](MOBILE.md). If Grok gains repository access, the universal
   starting instruction should apply unchanged; verify and document.
5. **Companion mobile app, if the Shortcut proves insufficient.** The
   iPhone Shortcut and text-replacement setups in
   [MOBILE.md](MOBILE.md) approximate a Claude-Code-like entry point for
   ChatGPT users without custom development. If they prove too clumsy in
   practice, a small companion app (pick repo → type task → open
   assistant with the bootstrap prompt) is the next step — noting that
   this is real app development, not documentation.
6. **Out-of-chat change notifications for members.** In-chat catch-up is
   now a convention (the instructions template's session-start
   catch-up), but a member who hasn't opened a session learns nothing.
   Evaluate a GitHub Actions job that emails a plain-language digest of
   merged changes (or leans on GitHub's built-in Watch notifications,
   documented in the members' page) — as of 2026-08, unexplored.
7. **Define what happens when a consumer repo imports multiple `team`
   sources that disagree.** See PRACTICE_ENGINE_PLAN.md's `## Deferred`
   section (added 2026-09-03, alongside that session's precedence reorder)
   for the detail — not duplicated here. Not needed today; revisit when a
   real multi-team-import case appears.
8. **Reduce GitHub dependency when ready.** The layer itself is plain git
   + markdown + Python; GitHub specifics are the worked examples (PRs,
   Actions, Issues, branch rulesets). When priorities allow, document
   Gitea equivalents (Gitea Actions is workflow-compatible; Issues and
   branch protection have counterparts) so a repo can move hosts without
   losing the practices. Deliberately below the Actions/Issues items
   above: deeper GitHub integration now is acceptable, since equivalents
   can be added later.
9. ~~**The pre-fork catalogue audit table.**~~ **Done (2026-09-03).** One
   row per inherited practice, verdict against this plan's architecture,
   plus whether Alex needs to hear about it:
   [spec/PREFORK_AUDIT.md](spec/PREFORK_AUDIT.md).
10. **`for_team:`/`in_repos:` individual-practice scoping.** Fully designed
    in [PRACTICE_ENGINE_PLAN.md's Deferred section](PRACTICE_ENGINE_PLAN.md#deferred-speculative--do-not-build-yet),
    correctly not built yet. **Blocked on:** a real second team's private
    set existing to test `for_team:`'s conflict rule against — revisit the
    moment one does, don't re-derive the judgment from scratch.
11. **Confirm `additionalContext` actually reaches the model, not just the
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
12. ~~**Investigate why `routing-audit` fell through, audit the plan for
    other silent drops.**~~ **Part 1 done (2026-09-04)** — root cause and
    scan for other drops in
    [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md)'s "Part 1,
    answered" section; the one adjacent gap it found is item 17 below.
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
13. **Retire [local/practices/merge-target-is-beta-branch.md](local/practices/merge-target-is-beta-branch.md)
    (and its check in [tools/precedent_check.py](tools/precedent_check.py),
    and the pointer in [AGENTS.md](AGENTS.md)'s opening paragraph) the
    moment Alex reviews and merges `precedent-beta-v01` into `main` for
    real.** Delete the practice file, remove the
    `merge-target-is-beta-branch` check function, and remove the
    [AGENTS.md](AGENTS.md) pointer, all in that same PR. **Blocked on:** Alex's review
    and approval of `precedent-beta-v01` for the real phase-7 merge into
    `main` — not something to anticipate or do early.
14. **Run the non-technical-contributor access plan for real.**
    [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
    is drafted but not executed — it doubles as item 9's neighbor,
    [spec/PHASE6_BRIEF.md](spec/PHASE6_BRIEF.md)'s still-open item 4 (the
    first end-to-end rehearsal of INSTALL.md §0). **Blocked on:** a real
    person and repo to run it against, and Morgan adding the GitHub
    collaborator role by hand (no tool in this repo's GitHub toolset
    creates a collaborator invite).
15. ~~**Build the team practice repo and reusable document-project template
    for non-technical document work.**~~ **Done (2026-09-05)** —
    [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)'s
    Steps 1-2 executed: `themorgan/precedent-team-tms` bootstrapped per
    [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md) (empty of
    real practices by design — Morgan named the repo, `approvers.json` seeds
    Morgan as first approver) and pushed, and
    [templates/nontechnical-document-project/](templates/nontechnical-document-project/)
    added here. Step 3 (the plan's own boundary) deliberately not done — see
    item 16.
16. **Run the document-project pilot once Morgan has a real first
    project.** Item 15 no longer blocks this — the template and team repo
    are real. Deliberately not planned further than that: see
    [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)'s
    "Sequencing" section for why a pilot project and person are not invented
    ahead of a real one existing. **Blocked on:** a real subject and a real
    person, neither of which exists yet.
17. ~~**Enumerate and wire the inherited RPP "very deep check" audit list as
    an on-demand tool.**~~ **Done (2026-09-05)** — a session holding
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
18. **`parallel-artifact-ledger`'s root-commit exemption doesn't cover a
    family's own inception commit.** Found 2026-09-05: `_parallel_artifact_ledger`
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
    fixed here; consider extending the exemption itself, per-member-directory
    (that directory's own first commit is exempt, the same reasoning
    already applied repo-wide), so a future family's inception commit
    doesn't need the same manual backfill.
19. **Root-cause why `parallel-artifact-ledger`'s own CI step never shows its
    diagnostic output — a GitHub Actions log-capture anomaly, currently
    working around it by making the check advisory-only.** Found 2026-09-05,
    same day as item 18: after item 18's row was backfilled and after
    [`b16b141`](https://github.com/alex137/BestPractice/commit/b16b141)
    made the root-commit exemption shallow-clone-safe (reads `.git/shallow`
    directly, since `git rev-list --max-parents=0` can't be trusted on a
    shallow checkout) and
    [`2a0fbe0`](https://github.com/alex137/BestPractice/commit/2a0fbe0)
    added `fetch-depth: 0` to `deep-check.yml`'s checkout (a real, separate,
    repo-wide gap — see that workflow's own comment), GitHub Actions (git
    2.55.0) *still* reported the same `f2078d6` violation, on content
    confirmed correct four independent ways: a GitHub API read of the PR's
    own merge-ref content, a full local reproduction (git 2.43.0), and two
    temporary diagnostic commits
    ([`4aca732`](https://github.com/alex137/BestPractice/commit/4aca732),
    stderr; [`62e2592`](https://github.com/alex137/BestPractice/commit/62e2592),
    stdout with an explicit flush) that proved the check function
    completes normally (0 errored, all 3 findings correctly formatted) —
    meaning the diagnostic print statements demonstrably executed — yet
    neither ever surfaced in the CI log for the real, standalone
    [precedent_check.py](tools/precedent_check.py) step, even though the
    identical code prints correctly every time it runs through
    [verify_harness.py](tools/verify_harness.py)'s own subprocess
    self-test in the same job. No stray `sys.stdout` reassignment was
    found anywhere in [tools/precedent_check.py](tools/precedent_check.py) or
    anything it imports. Both diagnostic commits were reverted
    ([`b997f5e`](https://github.com/alex137/BestPractice/commit/b997f5e))
    rather than left in. Full account:
    [PR #110, comment](https://github.com/alex137/BestPractice/pull/110#issuecomment-5554511294).

    **Scope note, checked 2026-09-05:** `precedent-beta-v01`'s own tip
    (`74657e6`) and every other open PR were checked at the time this was
    found — none were failing. That's not because the underlying gap is
    absent there: `precedent-beta-v01`'s `deep-check.yml` still has no
    `fetch-depth: 0` (only this PR's branch does), so its checkout stays
    shallow (depth 1), `git log --no-merges -- <member-dir>` finds nothing
    to flag, and the check falsely, silently passes — the exact
    already-documented "scope: 'tree' check... false pass on an
    under-fetched clone" gotcha in this file's own AGENTS.md, just
    manifesting repo-wide via the workflow's default rather than a local
    clone's. The moment PR #110 merges, `fetch-depth: 0` lands on
    `precedent-beta-v01` too, and every push/PR against it would hit this
    same false positive from then on — hence downgrading the check to
    advisory-only ([tools/precedent_check.py](tools/precedent_check.py)'s
    `advisory=True` on this one check's registration; see its own dated
    comment) in the *same*
    PR, so nothing else goes red the moment the fix lands.

    **Re-promotion condition:** once the CI-log-capture anomaly is
    understood and fixed (or proven not to recur — e.g. verified against a
    later git/runner-image version), remove `advisory=True` from
    `parallel-artifact-ledger`'s `@check(...)` registration in
    [tools/precedent_check.py](tools/precedent_check.py), update this
    item, and update [practices/parallel-artifact-ledger.md](practices/parallel-artifact-ledger.md)'s
    Story section to record the resolution.

    **Re-verified fresh, 2026-09-06, on PR #110's own current CI run —
    still reproduces, still unexplained, escalated to Alex.** Merging
    `precedent-beta-v01`'s current tip into PR #110's branch and pushing
    triggered a brand-new CI run against merge-test commit `7ad93d0`
    (`5007766` merged onto `b72762f`); it failed with the identical
    `f2078d6` violation. Before assuming it was the same unfixed anomaly,
    this session ruled out four *new* candidate explanations, each
    directly tested rather than argued: (1) the local investigation's own
    shallow clone — deepened to full history (`git fetch --depth=2000`),
    confirmed `f2078d6` genuinely is an ancestor and the check passes
    clean locally either way; (2) the merge-test ref (`pull/110/merge`)
    double-merging to different content than what was actually pushed —
    read `templates/harness/LEDGER.md` and `tools/precedent_check.py`
    directly from GitHub's own `7ad93d03767657cc1f6ecb261c273e4119dfd55a`
    via the API: byte-identical to a clean local checkout, `f2078d6`'s row
    present, `advisory=True` present in the check's own registration; (3) a
    tracked, stale `__pycache__/precedent_check.cpython-*.pyc` shadowing
    current source — `tools/__pycache__/` is gitignored and confirmed not
    tracked in the tested commit, ruled out; (4) `verify_harness.py`'s own
    self-tests for this check contaminating the real working tree before
    the standalone `precedent_check.py` step runs in the same CI job —
    read both self-test implementations
    (`check_parallel_artifact_ledger_fires`, `check_precedent_check_fires`):
    both operate entirely inside `tempfile.mkdtemp()` scratch trees
    (one loads `precedent_check.py` via `importlib.util` with `pc.ROOT`
    reassigned to the scratch dir, the other `shutil.copytree`s the whole
    repo into per-case scratch copies and runs each as a subprocess with
    `cwd` set to the copy) — neither ever touches this repo's own
    `templates/harness/LEDGER.md`, ruled out. A **fifth, direct** test: a
    brand-new, fully isolated `git clone` of nothing but the exact tested
    secure hash algorithm (SHA) — the commit hash, `7ad93d0`, no
    working-branch state carried over — ran
    `python3 tools/precedent_check.py` clean — `0 violated` — on the
    identical commit CI called a violation. Four independent confirmations
    the content and code are correct (three from the prior finding, this
    fresh isolated-clone run a fourth, distinct from the three CI already
    had) plus these four ruled-out local hypotheses leaves nothing left to
    test from outside GitHub's own execution environment. Per this task's
    own standing instruction (two automated diagnostic commits already
    reverted, per this item's own account above) this is the point to stop
    attempting another automated diagnosis: escalated to Alex directly, as
    a comment on PR #110, asking for a raw Actions UI look at run
    `34003769809` / job `101407169823` — something a log fetch over the
    API cannot show (runner diagnostics, any organization-level Actions
    configuration, anything else the UI surfaces that the plain log
    stream doesn't).

    **A much more precise lead, found immediately after, on the very next
    CI run** (triggered by this session's own follow-up push, run
    `34004885068` / job `101410153665`): the failing step's own summary
    line is not just wrong content, it is a different, older version of
    `main()`'s own f-string. CI printed
    `precedent_check: 18 passed, 1 violated, 0 errored, 8 skipped (a skip
    is not a pass).` — no `advisory` field at all, and the shorter
    trailing clause. That exact string is what `precedent-beta-v01`'s own
    current tip (`b72762f`, this PR's *base*, pre-merge) produces; the
    `advisory` field was added in [`d35f435`](https://github.com/alex137/BestPractice/commit/d35f435),
    which exists only on this PR's own branch, never yet merged upstream.
    But the *immediately preceding* step in the *same job*,
    `python3 tools/verify_harness.py`, printed `52 passed, 0 failed` with
    `71 stated cases` for the enforced-channel self-test and
    `12 stated cases` for the reachability self-test — counts that exist
    only in this session's own newly-pushed commit, nowhere earlier. One
    job, one checkout, two consecutive steps disagreeing about which
    version of `tools/precedent_check.py` is on disk, with no step in
    between that writes to the workspace. That rules out a content or
    logic bug in this repository as the explanation and points at GitHub
    Actions' own checked-out workspace serving inconsistent content for
    the same path within a single job — flagged precisely to Alex as a
    follow-up PR comment, narrower than the original ask.
20. ~~**`precedent_gate.py` and `precedent_paths.py` don't flag an unreachable
    materialized source either — only `precedent_show.py` does, 2026-09-06.**~~
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

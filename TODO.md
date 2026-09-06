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
14. <a id="nontechnical-contributor-access"></a>**Run the non-technical-contributor access plan for real.**
    [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md)
    is drafted but not executed — it doubles as item 9's neighbor,
    [spec/PHASE6_BRIEF.md](spec/PHASE6_BRIEF.md)'s still-open item 4 (the
    first end-to-end rehearsal of INSTALL.md §0). **Blocked on:** a real
    person and repo to run it against, and Morgan adding the GitHub
    collaborator role by hand (no tool in this repo's GitHub toolset
    creates a collaborator invite).
15. <a id="team-repo-and-document-template"></a>~~**Build the team practice repo and reusable document-project template    for non-technical document work.**~~ **Done (2026-09-05)** —
    [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)'s
    Steps 1-2 executed: `themorgan/precedent-team-tms` bootstrapped per
    [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md) (empty of
    real practices by design — Morgan named the repo, `approvers.json` seeds
    Morgan as first approver) and pushed, and
    [templates/nontechnical-document-project/](templates/nontechnical-document-project/)
    added here. Step 3 (the plan's own boundary) deliberately not done — see
    item 16.
16. <a id="document-project-pilot"></a>**Run the document-project pilot once Morgan has a real first
    project.** Item 15 no longer blocks this — the template and team repo
    are real. Deliberately not planned further than that: see
    [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)'s
    "Sequencing" section for why a pilot project and person are not invented
    ahead of a real one existing. **Blocked on:** a real subject and a real
    person, neither of which exists yet.
17. <a id="wire-the-very-deep-check-list"></a>~~**Enumerate and wire the inherited RPP "very deep check" audit list as    an on-demand tool.**~~ **Done (2026-09-05)** — a session holding
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

22. <a id="sweep-judgment-only-practices"></a>**Sweep the team and individual sets' judgment-only practices.**
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
    was corrupting inline code spans in committed headings. **Blocked
    on:** nothing but session budget — take them one
    at a time, with the closed question
    [practices/full-practice-audit.md](practices/full-practice-audit.md)
    names, in a session with those repos attached. Full context:
    [spec/PRELAUNCH_AUDIT.md](spec/PRELAUNCH_AUDIT.md).

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
    **Done (2026-09-06.)** `themorgan/HavrutaBrainstorm` — the one consumer
    that declares sources and was not attached when
    [practices/source-naming.md](practices/source-naming.md) landed — was
    refreshed from its own session and merged. Its repo-local source was
    named `havruta-local`; it is now `local`. What the pilot actually
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
    2026-09-06 — so the first real consumer refresh (HavrutaBrainstorm, the
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

32. <a id="migrated-practices-lost-their-stories"></a>**The RPP migration dropped every `## Story`, and that is the
    provenance the catalogue exists to keep.** Found by the 2026-09-06
    migration audit ([`rpp-migration-audited`](TODO.md#rpp-migration-audited)):
    34 of 41 practices in `precedent-team-maintainers` and 3 of 10 in
    `precedent-individual` have an empty `## Story`; `header-caps` also had
    an empty `## Why`, and `fail-gracefully` has Detail, Why and Story all
    empty. The incident each rule exists to prevent stayed behind in
    RepoPersonalPreferences. Nothing is *lost* while RPP survives, but it is
    unreachable from the rule it justifies, which is exactly what
    [practices/cite-the-incident.md](practices/cite-the-incident.md) and
    [practices/mistakes-become-rules.md](practices/mistakes-become-rules.md)
    exist to prevent — and a rule whose reason nobody can see is the first
    one someone deletes. Backfill from RPP's own text, per practice.
    **Blocked on:** a session holding `themorgan/RepoPersonalPreferences`
    plus the two private sets. Note the size honestly: 37 practices, each
    needing a real incident written from the original, not a paraphrase.

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
    source is the private repo**. BestPractice itself is public, so that
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
    **Blocked on:** `themorgan/precedent-team-maintainers` and
    `themorgan/precedent-team-tms` not attached this session. Each needs
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

- **Backfill the engine-refresh workflow into source sets bootstrapped
  before it existed.** `templates/practice-set-{individual,team}/.github/
  workflows/engine-refresh.yml` reaches every set created from 2026-09-06
  on. Sets created before that date have no scheduled freshness channel at
  all and need the file added by hand. **Blocked on:** nothing here — this
  is a one-line copy per set, but it has to happen *in* each set's own
  private repo, so it cannot be done from this repo's own branch.

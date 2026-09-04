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
    mechanisms before trusting their output) is pre-registered** —
    [evals/routing/PREDICTION_AUDIT_JUDGMENT.md](evals/routing/PREDICTION_AUDIT_JUDGMENT.md)
    — **and run once**, a smaller single-session eval than the routing
    eval's own multi-run discipline; see
    [spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md)'s dated
    2026-09-04 section for the result and its stated caveats. Left open:
    the same document's own read that a single 6-case run is a first
    signal, not a replacement for that fuller discipline, if the finding
    turns out to matter enough to invest in later.
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
15. **Build the team practice repo and reusable document-project template
    for non-technical document work.**
    [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)
    is drafted but not executed. Unlike item 14, this one is not blocked on
    a real person — creating the (empty) team repo and the template is
    real, bounded, agent-doable work. **Blocked on:** Morgan naming the new
    team repo and who goes in its `approvers.json` (Prerequisites items 1-2
    in the plan) — the implementing session cannot invent those.
16. **Run the document-project pilot once item 15 lands and Morgan has a
    real first project.** Deliberately not planned yet — see
    [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)'s
    "Sequencing" section for why. **Blocked on:** item 15, plus a real
    subject and a real person, neither of which exists yet.
17. **Enumerate and wire the inherited RPP "very deep check" audit list as
    an on-demand tool.** Named in
    [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s v28 amendment,
    deliberately deferred there ("when phase 5 or later actually needs
    it") rather than dropped, but never tracked anywhere but that one
    paragraph — the exact structural risk item 12's Part 1 answer found
    routing-audit fell into, caught here before it repeated rather than
    after. Full context:
    [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md)'s "Part 1,
    answered" section. **Blocked on:** a session holding the private RPP
    repo, to actually enumerate its list — cannot be done from here; also
    worth a real decision, not just building, about whether
    `full-practice-audit` (built 2026-09-03) has already made this
    redundant now that it exists, rather than inventorying a fourth
    mechanism out of habit.

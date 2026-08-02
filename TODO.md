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
   check when deck sources change.
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
6. **Reduce GitHub dependency when ready.** The layer itself is plain git
   + markdown + Python; GitHub specifics are the worked examples (PRs,
   Actions, Issues, branch rulesets). When priorities allow, document
   Gitea equivalents (Gitea Actions is workflow-compatible; Issues and
   branch protection have counterparts) so a repo can move hosts without
   losing the practices. Deliberately below the Actions/Issues items
   above: deeper GitHub integration now is acceptable, since equivalents
   can be added later.

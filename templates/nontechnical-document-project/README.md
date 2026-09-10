<!-- Template: instantiate one copy of this directory per new document project.
     Not tool-bootstrapped (unlike templates/practice-set-team/) -- copy it by
     hand into the new repo's root and fill in the placeholders below. See
     spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md for the plan this implements
     and why it stops here (no pilot project yet). -->

# Non-technical document-project template

A starting point for a repo where a non-technical person does document work
(drafting, editing) with an assistant, on Precedent's three-source loader —
so editorial and structural decisions get captured as durable, reusable
rules instead of living and dying inside one document.

## What's here

| File | What it's for |
|---|---|
| [`precedent.json`](precedent.json) | Declares the repo's visibility, the universal practice source (vendored) and three shared team sources (`precedent-team-tms`, `precedent-team-writing`, `precedent-team-working-style`, all resolved live). |
| [`AGENTS.md`](AGENTS.md) | The repo's own instructions file — access restrictions, persona, and the candidate-capture flow already filled in. |
| [`.claude/settings.json`](.claude/settings.json) | A restricted session config: no push, no merge, no raw shell — limits that bind **every** session on the repo, maintainers included, not only the non-technical contributor. It also wires four SessionStart/PreToolUse hooks whose scripts this template does not ship; instantiation step 3 is where they come from. |

## Instantiating this template

1. Create the new repo (private, per this project's own working style).
2. Copy every file in this directory into its root, keeping the `.claude/`
   path.
3. **Install the Claude Code harness adapter's hook scripts.** This
   template's [`.claude/settings.json`](.claude/settings.json) *wires* four
   hooks but ships none of them — they live in the harness adapter so a fix
   reaches every adopter through one file instead of drifting copies. Copy
   `session-start.sh`, `freshness-guard.sh`, `commit-identity.sh` and
   `precedent-paths.sh` from
   [templates/harness/claude-code/hooks/](../harness/claude-code/hooks/)
   into the new repo's `.claude/hooks/`, and make each one executable
   (`chmod +x .claude/hooks/*.sh`) — **a hook that is not executable is a
   hook that silently never runs.** Replace the `main` argument in the three
   `freshness-guard.sh` commands with the repo's real base branch.

   Read [templates/harness/README.md](../harness/README.md) for what each
   adapter is, and [INSTALL.md §1 step 2](../../INSTALL.md#1-installing-into-a-repo-that-already-has-its-own-process)'s
   hook decision table for which hooks are decisions and which are not. This
   template has already made those calls: it wires the three the table marks
   *always*, plus `precedent-paths.sh` (the table's "only with the Precedent
   loader", and this template is that loader), and deliberately omits
   `stop-git-check.sh` — it blocks ending a turn on unpushed work, and the
   contributor this template is written for is denied `git push`.

   Skipping this step is not a degraded install, it is an inert one: with no
   `.claude/hooks/session-start.sh` on disk, `tools/bootstrap.sh` never runs
   at all.
4. Follow [INSTALL.md §0](../../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)'s
   steps 1 and 6: vendor Precedent's `practices/` tree and whole `tools/`
   directory at the path `precedent.json` already names
   (`precedent/universal/`), then run `python3 tools/precedent_sync_views.py`
   to fill in `AGENTS.md`'s generated block. Confirm it prints `OK`.

   Then run `python3 tools/precedent_check.py` and read its practice count.
   This template declares `"visibility": "private"` for a reason
   ([`precedent.json`](precedent.json)'s `_visibility_comment`): a config
   that omits the field is read as public, which silently excludes every
   team-level source's practice text. If the count comes back near the size
   of the universal set alone, that field is what to check first.
5. Follow [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](../../spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md)'s
   Prerequisites and Step 3 to add the actual person as a repo collaborator
   (Triage or Read) and confirm the GitHub-auth-binding model — this
   template's `AGENTS.md` already carries that plan's session/persona
   content, but the collaborator invite and auth-model check are still a
   human step, same as that plan says.
6. Replace this README with one about the actual document project, or
   delete it — it exists to explain the template, not the finished repo.

## What this template deliberately does not include

Per [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](../../spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)'s
own scope: no pilot project or pilot person is built into this template —
neither exists yet. The first repo instantiated from this template *is* that
pilot, and its own `AGENTS.md` should be adapted with that project's real
subject matter once it exists, not left as this skeleton.

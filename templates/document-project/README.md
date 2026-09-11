<!-- Template: instantiate one copy of this directory per new document project.
     Not tool-bootstrapped (unlike templates/practice-set-team/) -- copy it by
     hand into the new repo's root and fill in the placeholders below. See
     spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md for the plan this implements
     and why it stops here (no pilot project yet). -->

# Document-project template

A starting point for a repo where a non-technical person does document work
(drafting, editing) with an assistant, on Precedent's three-source loader —
so editorial and structural decisions get captured as durable, reusable
rules instead of living and dying inside one document.

## What's here

| File | What it's for |
|---|---|
| [`precedent.json`](precedent.json) | Declares the repo's visibility, the universal practice source (vendored) and two shared team sources (`precedent-team-writing`, `precedent-team-working-style`, both resolved live). |
| [`AGENTS.md`](AGENTS.md) | The repo's own instructions file — access restrictions, persona, and the candidate-capture flow already filled in. |
| [`.github/CODEOWNERS`](.github/CODEOWNERS) | The path boundary: which paths need the maintainer's review, and which are any contributor's to write and merge. Fill in the placeholder at instantiation step 7; it does nothing without step 6's branch protection. |
| [`.claude/settings.json`](.claude/settings.json) | The repo's session config: an allowlist of the read-only and check commands this work needs, plus one repo-wide denial (`rm *`). It is **not** where the contributor's restrictions live — this file is tracked, so it binds every session and cannot tell one person from another; step 6 below is the per-person layer. It also wires four SessionStart/PreToolUse hooks whose scripts this template does not ship; instantiation step 3 is where they come from. |

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
   `stop-git-check.sh` — it blocks ending a turn on unpushed work, and a
   document left deliberately unpushed overnight is ordinary here, so the
   hook would mostly refuse to end turns over nothing. (Until 2026-09-11
   the reason was that the contributor was denied `git push` outright; they
   push their own document work now — see step 6.)

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
5. Follow [spec/CONTRIBUTOR_ACCESS.md](../../spec/CONTRIBUTOR_ACCESS.md)'s
   "Verify these first" section before anything else here is relied on. Three
   platform behaviours that plan rests on are unverified as of 2026-09-11 —
   most importantly whether a code-owner review requirement leaves a
   documents-only pull request mergeable by its author. If it does not, the
   maintainer reviews every content change, which is a different project than
   the one this template describes.
6. **Add the contributor as a Write collaborator, and protect the base
   branch in the same sitting.** GitHub UI: Settings → Collaborators and
   teams → Add people. Then Settings → Branches (or Rules): require a pull
   request before merging, require review from code owners, and do not allow
   bypassing for non-administrators. **Write without that protection is
   unrestricted write** — the two are one step, not two. No tool in this
   repo's GitHub toolset creates a collaborator invite, so this stays a human
   step; confirm the auth-binding model the spec's layer 1 names while you
   are there.
7. **Fill in [`.github/CODEOWNERS`](.github/CODEOWNERS)** — replace
   `{{MAINTAINER_GITHUB}}` with the maintainer's GitHub username, and commit
   it. That file plus step 6's protection *is* the boundary; it is not
   per-person, so nothing has to decide what kind of contributor anybody is.
8. **Set the contributor's own session configuration** — their
   `environment_id`, their per-session settings, or their untracked
   `.claude/settings.local.json` — with `permission_mode` never set to
   `bypassPermissions`, and the persona instruction from `AGENTS.md`'s
   "Contributor access" section. **Not in this repo's tracked
   `.claude/settings.json`**, which binds every session here and cannot see
   who is running; the template shipped exactly that mistake once and it
   locked the repository's own administrator out of merging his own work
   (2026-09-10).

   This layer is the user experience, not the enforcement. It carries no git
   denials any more: the contributor pushes and merges their own documents,
   which is the point of the project.
7. Replace this README with one about the actual document project, or
   delete it — it exists to explain the template, not the finished repo.

## What this template deliberately does not include

Per [spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md](../../spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md)'s
own scope: no pilot project or pilot person is built into this template —
neither exists yet. The first repo instantiated from this template *is* that
pilot, and its own `AGENTS.md` should be adapted with that project's real
subject matter once it exists, not left as this skeleton.

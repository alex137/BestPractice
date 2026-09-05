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
| [`precedent.json`](precedent.json) | Declares the universal practice source (vendored) and the shared editorial team source (`precedent-team-tms`, resolved live). |
| [`AGENTS.md`](AGENTS.md) | The repo's own instructions file — access restrictions, persona, and the candidate-capture flow already filled in. |
| [`.claude/settings.json`](.claude/settings.json) | A restricted session config: no push, no merge, no raw shell. |

## Instantiating this template

1. Create the new repo (private, per this project's own working style).
2. Copy every file in this directory into its root, keeping the `.claude/`
   path.
3. Follow [INSTALL.md §0](../../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)'s
   steps 1 and 6: vendor Precedent's `practices/` tree and whole `tools/`
   directory at the path `precedent.json` already names
   (`precedent/universal/`), then run `python3 tools/precedent_sync_views.py`
   to fill in `AGENTS.md`'s generated block. Confirm it prints `OK`.
4. Follow [spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md](../../spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md)'s
   Prerequisites and Step 3 to add the actual person as a repo collaborator
   (Triage or Read) and confirm the GitHub-auth-binding model — this
   template's `AGENTS.md` already carries that plan's session/persona
   content, but the collaborator invite and auth-model check are still a
   human step, same as that plan says.
5. Replace this README with one about the actual document project, or
   delete it — it exists to explain the template, not the finished repo.

## What this template deliberately does not include

Per [spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md](../../spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md)'s
own scope: no pilot project or pilot person is built into this template —
neither exists yet. The first repo instantiated from this template *is* that
pilot, and its own `AGENTS.md` should be adapted with that project's real
subject matter once it exists, not left as this skeleton.

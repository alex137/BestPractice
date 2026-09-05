# Repository instructions — read me first

<!-- Template: instantiate per templates/nontechnical-document-project/README.md,
     which follows BestPractice INSTALL.md §0 ("Installing directly onto the
     Precedent loader"). This is the non-technical-document-project variant of
     templates/AGENTS.md.loader.template: the access-restriction and persona
     content below comes from spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md verbatim
     (don't re-derive it), and the candidate-capture bullet comes from
     spec/NONTECHNICAL_TEAM_PRACTICE_CAPTURE.md. Replace <angle-bracket>
     placeholders with this project's real content; keep the section
     structure and the generated-block markers exactly as they appear below. -->

**Orientation: read `MAP.md` first** — the repository map. It covers the key
deliverables and indexes which documents back each part of each one.

<!-- BEGIN GENERATED: precedent-loader -->
<!-- END GENERATED -->

<!-- The block above is written by `python3 tools/precedent_sync_views.py`
     (INSTALL.md §0 step 5) — never hand-edit between the markers; the
     regeneration check fails loudly on drift. Leave the markers themselves
     exactly as shown, on their own lines, with nothing between them until
     the tool fills them in. -->

## Where things are (quick index — check here BEFORE searching the repo)

| Looking for… | Go to |
|---|---|
| Canonical names for this project's terms — use these names, don't invent new ones | `GLOSSARY.md` |
| The document(s) this project is producing | `<path>` |
| Open items: analyses, verifications, decisions | `TODO.md` |
| Which practice sources are in force, and where each is vendored or resolved from | `precedent.json` |

## Document workflow

<!-- Fill in with the real project once a document exists: what's being
     written, where the working drafts live, who reviews. Documents live as
     plain text/markdown files in this repo, edited through ordinary commits
     and PRs — the same working method as any other Precedent repo, just
     applied to prose instead of code. -->

### Build-environment gotchas — do NOT rediscover these

- At session start, run `bash tools/bootstrap.sh` before other work (harnesses
  with a hook mechanism run it automatically — see `templates/harness/`).
- **Keep `AGENTS.md`'s generated block current.** Before relying on it,
  run `python3 tools/precedent_sync_views.py --check` — it exits non-zero
  if any declared source (`precedent.json`) has moved since the block was
  last regenerated. Re-run without `--check` to refresh it, review the
  diff, and commit.

- **A brand-new session on this repo alone has no git read access to
  `precedent-team-tms`** — session repo access is scoped per session, never
  inherited just because `precedent.json` names a repo. No token or secret is
  involved: the tool that grants a session this access rides the same GitHub
  identity already behind the session, so it only ever succeeds because that
  person is already a collaborator on the target repo. **At the very start of
  every session, before running `tools/bootstrap.sh`, call that tool
  (`add_repo`, read access) for `precedent-team-tms` — silently, with no
  confirmation needed first.** This is a read-only scope extension, not a
  credential or production change. Never write this as "if the clone fails,
  ask to add the repo" — that only works when a human happens to be watching
  for the failure, and the whole point is that a person only ever attaches
  the one repo they're actually working in; reaching for the team source is
  this session's own job, every time.

## Non-technical contributor access

<!-- Verbatim from spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md's Step 3, adapted
     only to name this project's real files. Do not weaken the wording below
     — see that plan's own note on why. -->

**GitHub role — the platform-enforced boundary.** The contributor's own
GitHub collaborator role on this repo is set to **Triage** (can comment on
and manage Issues — enough to participate in candidate threads — but cannot
push, merge, or touch protected files) or **Read** (view only, no Issue
comments) if even that is too much. This only binds anything if the person
authenticates to GitHub as themselves, not a shared org-wide connection —
confirmed once, per project, before relying on it.

**Session/environment configuration — the UX and defense-in-depth layer,**
enforced independently of the GitHub role above:

- If a dedicated `environment_id` is available for the contributor,
  configure it (or their per-session settings) with `permission_mode` never
  set to `bypassPermissions`, and exclude `git push`, `git merge`, and any
  raw shell tool from the allowlist — see [`.claude/settings.json`](.claude/settings.json)
  in this repo, which already does this; contrast with
  [`templates/harness/claude-code/settings.json`](../templates/harness/claude-code/settings.json)'s
  stock allowlist, which includes `git push -u origin *` by default —
  theirs should not.
- **Persona instruction, no git/GitHub jargon, no mechanical-rule talk:**
  restate the contributor's ideas back to them in their own words before
  acting on anything, and route every practice idea through the candidate
  flow below rather than talking about promotion, resident budgets,
  `checked_by`, or any other mechanical-rule vocabulary — that's an
  approver's business, not theirs.

**Candidate-capture flow.** When a non-technical contributor raises a
practice idea in plain language, Claude:

1. Restates it back to them in their own words to confirm before acting.
2. Drafts a candidate with [`tools/precedent_candidate.py`](../tools/precedent_candidate.py).
   **Because a non-technical contributor is never a listed approver
   (`precedent-team-tms`'s `approvers.json`), this defaults to
   `precedent_candidate.py --as-issue true` against `precedent-team-tms`** —
   a quiet `candidates/*.md` file accomplishes nothing when nobody with
   landing authority is watching it, per
   [`spec/CANDIDATE_FORMAT.md`](../spec/CANDIDATE_FORMAT.md#which-one-for-team-file-or-issue)'s
   rule for team candidates raised by a non-approver. Use a plain individual
   candidate file instead only if the idea is explicitly just the
   contributor's own working style, not something to share with the team.
3. Never mentions promotion, resident budgets, `checked_by`, or any other
   mechanical-rule vocabulary to them — that's an approver's business, not
   theirs.

## Git / workflow

- Develop on a feature branch; open a PR; merge only when the administrator
  says so.
- **Start every thread by merging latest `origin/<default-branch>` into your
  branch**; avoid two concurrent threads editing the same document.

### Merging a thread branch (runbook — follow, don't improvise)

Conflicts in shared files are EXPECTED. The fast, safe path:

0. **Capture gate — before the merge, in the thread that did the work**:
   did this thread's work imply anything that must be captured — a document
   update, a registry entry, a decision record? Fold it now; the thread that
   built the rationale is the one that knows what to record.
   **0b. Export gate:** did this thread improve a *generic* practice — one
   that would hold in an unrelated project, not just this one's own
   documents? Fold the abstracted form into this repo's own vendored copy
   of the universal source (`precedent.json`'s `universal` entry — see its
   `path`) and open it as an ordinary pull request directly against that
   source's own repo (`https://github.com/alex137/BestPractice`). **There
   is no local check-in mirror for this yet** — a plain PR against the
   upstream repo is the real mechanism until one is wired in. Then run
   `python3 tools/precedent_sync_views.py` locally to pick your own change
   back up once it lands upstream.
1. Fetch and merge the default branch locally.
2. Resolve by fixed per-file-class rules:
   - Registries: **union** of both sides — never drop an entry or a status.
   - Logs / index files: **append-only — keep both sides' additions.**
   - Same content file edited on both sides: keep both sides' text;
     reconcile with the administrator if the two edits genuinely conflict.
   - **Generated outputs: never hand-merge.** Re-run
     `python3 tools/precedent_sync_views.py`, never hand-resolving its own
     conflict markers.
3. Run the audits — **all must pass before the merge commits**:
   `python3 tools/precedent_sync_views.py --check`.
4. Commit the merge, push, land per this repo's convention.

## Conventions

- **Sections are ordered by the reader's frequency, not the writer's:** a
  document walking through instructions or rules in multiple sections puts
  common, everyday content first and rare edge cases last.
- **Doc references are links:** in-repo docs reference other repo files as
  relative markdown links, never bare backticked names. Use `≈`, not `~`,
  for "approximately" — two stray tildes render as strikethrough on GitHub.
- **Outward-facing documents use the reader's words:** the deliverable
  document(s) this project produces are read by an audience outside this
  repo's own work — every term that names a category is either already the
  reader's word, a plain equivalent, or glossed inline on first use.
- **Reply convention:** every reply that created or modified files ends
  with a "Files touched" list — branch link + post-merge link + one-line
  description per file.
- **Commits are credited to the human driving the session.** Set the git
  author to the contributor's name and GitHub noreply email, and name
  yourself in a `Co-Authored-By:` trailer.
- **Open each session by catching the contributor up.** At session start,
  fetch the latest default branch and summarize, in plain language, what
  changed since their last activity.

## Administrator requests you must know how to handle

- **"What's waiting for me?"** — the administrator's review loop: list open
  PRs and open candidate Issues on `precedent-team-tms`, summarize each in
  plain language, and take the verdict in chat.
- **"Add project members"** — same flow as
  [`templates/AGENTS.md.loader.template`](../AGENTS.md.loader.template)'s
  own "Add project members" section, with one addition: for a non-technical
  contributor, grant **Triage** or **Read** (never Write) and apply the
  "Non-technical contributor access" section above, not the default
  Read/Write instructions.

## Practice sources — Precedent loader (policy)

- `precedent.json` declares every practice source in force here — see
  [INSTALL.md §0](../../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)
  for the resolution and precedence rules. The `universal` source is a
  **real vendored copy** at `precedent/universal/`, not a live reference.
  The `team` source, `precedent-team-tms`, resolves live from a sibling
  clone instead — never vendored.
- `python3 tools/precedent_sync_views.py --check` is this repo's own drift
  gate — run it before trusting `AGENTS.md`'s generated block, and after
  `precedent.json` or a vendored copy changes.
- Export gate = merge runbook step 0b, above.

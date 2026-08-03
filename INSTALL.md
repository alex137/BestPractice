# INSTALL — the agent playbook

Instructions for an agent (or human) wiring BestPractice into a *dependent
repo*, keeping it current, and flowing improvements back. Read
[PRACTICES.md](PRACTICES.md) first for what each practice is and why.

The model in one paragraph: the dependent repo **vendors** this repo at
`process/upstream/` as plain tracked files. **Install is adaptive** — you
instantiate templates with the repo's subject matter, placing real files at
their real locations. **Export is abstractive** — when installed practice
improves, you fold the generic form back into `process/upstream/`. The
**manifest** records the mapping in both directions; the **audit** makes
drift and proprietary leakage loud instead of silent.

## 1. Install into a dependent repo

1. **Vendor:** copy this repo's working tree (not its `.git`) into
   `process/upstream/` and commit it as ordinary tracked files. Record the
   upstream commit hash you copied from (used by updates, step 2).
2. **Instantiate the templates** (adaptive — rewrite with the repo's actual
   subject matter, don't copy verbatim):
   - `templates/AGENTS.md.template` → `AGENTS.md` at the repo root: the
     **harness-neutral** canonical instructions file. Fill the quick-index
     table with this repo's real lookups; adapt the merge runbook's file
     classes; keep the section structure.
   - `templates/MAP.md.template` → `MAP.md`; `templates/TODO.md.template` →
     `TODO.md`; `templates/GLOSSARY.md.template` → `GLOSSARY.md` (or a
     domain-appropriate name).
   - `templates/GETTING_STARTED.md` → `GETTING_STARTED.md` at the repo
     root: the member-facing onboarding page, one section per kind of AI
     user. (This template keeps a plain `.md` name on purpose — it
     doubles as the rendered sample linked from the README.) Replace the
     backticked `<placeholders>` with the project's real values, adapt
     the opening pitch to the project, and keep the per-assistant section
     structure so upstream onboarding improvements propagate on updates
     (§2). Refresh its dated assistant-capability notes from the upstream
     [MOBILE.md](MOBILE.md) when taking updates. Improvements a project
     makes to its own onboarding page are exported like any other
     practice improvement: fold the generic form back into this template
     in `process/upstream/` (§3), so better onboarding reaches every
     project.
   - `templates/README_AGENT_ENTRY.md.template` → insert near the top of
     the repo's root README: an agent-entry HTML comment (invisible on the
     rendered page, read by assistants opening the source) routing agents
     to `AGENTS.md`, plus one visible line pointing people to
     `GETTING_STARTED.md`.
   - `templates/bootstrap.sh` → `tools/bootstrap.sh` (add the repo's own
     setup needs).
   - **Apply the harness adapter(s)** for whichever agent(s) will work this
     repo — see [templates/harness/README.md](templates/harness/README.md).
     E.g. Claude Code: `harness/claude-code/CLAUDE.md` → repo root (a
     one-line import of `AGENTS.md`), `harness/claude-code/settings.json` →
     `.claude/settings.json`, `harness/claude-code/hooks/session-start.sh` →
     `.claude/hooks/session-start.sh`. Codex reads `AGENTS.md` natively.
     Multiple adapters can be installed side by side.
   - `tools/doc_lint.py` → run it from `process/upstream/tools/` in place,
     or copy to the repo's tools dir if it needs local adaptation.
3. **Write the manifest** at `process/manifest.json` — see §5 for the
   schema. One entry per installed practice artifact, recording where it
   landed, at what granularity, and what was adapted. Then run
   `python3 process/upstream/tools/practice_audit.py --update-baseline`
   to record content hashes.
4. **If the dependent repo is private** (and it usually is): create
   `process/scrub_blocklist.txt` — one regex per line (`#` comments), the
   repo's private vocabulary: project and product names, internal code
   words, identifier patterns, anything that must never appear in the
   public vendored tree. Err broad; false positives are a one-line review,
   false negatives are published.
5. **Add the export-gate section** to the instructions file (the template
   includes it): the copy-back rule, the scrub rule, and the periodic
   check-in item (add one to `TODO.md`).
6. **Root hygiene — the layout rule.** The ONLY files an install may
   create at the dependent repo's root are the instantiated ones:
   `AGENTS.md` (plus a harness pointer such as `CLAUDE.md`), `MAP.md`,
   `TODO.md`, `GLOSSARY.md`, `GETTING_STARTED.md`, and the README
   entry-block edit — plus `tools/bootstrap.sh` and
   `.github/workflows/bestpractice-docs.yml`. Everything else that ships
   with BestPractice (INSTALL.md, PRACTICES.md, SETUP.md,
   GITHUB_ACTIONS.md, MOBILE.md, METHOD.md, GIT.md, templates/, tools/,
   deck/) exists ONLY under `process/upstream/` — never copy any of it to
   the root. A contributor browsing the root should see the project's own
   subject matter plus the instantiated files, and nothing about how
   BestPractice works internally. The audit enforces this: an
   upstream-internal doc found at the root fails unless the manifest
   records it as the repo's own document.
7. Run `python3 process/upstream/tools/practice_audit.py` — it must pass.
   Commit.

`.gitignore` / `.gitattributes` stanzas for generated artifacts (practice 8):

```gitignore
# generated deliverables — only shipped artifacts get force-added
<your-build-output-glob>
```

```gitattributes
*.docx binary
*.pdf binary
<generated-md-glob> binary   # stop git text-merging generated files
```

## 2. Take an upstream update

1. Fetch the new upstream tree; diff it against the vendored copy at the
   **recorded base commit** (manifest `upstream.commit`).
2. Three-way merge per manifest entry: *old upstream* vs *new upstream* vs
   *your installed, adapted copy*. Apply upstream's changes to your installed
   files **through the adaptation** recorded in the entry's `notes` — don't
   clobber local adaptations.
3. **Instantiate anything the recorded install predates.** An update can
   introduce templates and root files that did not exist when this repo
   installed — e.g. `GETTING_STARTED.md`
   (from [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md)),
   the README entry block
   ([templates/README_AGENT_ENTRY.md.template](templates/README_AGENT_ENTRY.md.template)),
   or the Actions check
   ([templates/github-actions/](templates/github-actions/README.md)).
   Instantiate them exactly as §1 describes and add manifest entries.
4. **Fix legacy layout.** Older installs sometimes scattered
   upstream-internal docs (INSTALL.md, GITHUB_ACTIONS.md, …) at the repo
   root; the audit's LAYOUT check now fails on them. Delete the strays —
   their content lives under `process/upstream/` — per §1's root-hygiene
   rule.
5. Replace `process/upstream/` with the new tree, update
   `upstream.commit`, run the audit `--update-baseline`, commit.

## 3. Copy an improvement back (the export gate)

Run this check **before any thread ends / before any merge to the default
branch** (it is step 0b of the merge runbook, beside the capture gate):

> Did this thread improve a *generic* practice — a new convention, a
> sharpened runbook rule, a better audit, a template fix?

If yes, in the **same branch**:

1. Write the **abstracted** form into the right file under
   `process/upstream/` — patterns and lessons only, subject matter stripped
   (see practice 15). Abstraction is authorship, not copying: rewrite the
   incident generically, keep the lesson.
2. Update the touched manifest entries (`notes`, status) and run
   `python3 process/upstream/tools/practice_audit.py` — the scrub must pass.
3. If the *installed* file changed but you are not exporting yet, flip its
   manifest entry to `"diverged"` — the audit will keep reminding until the
   export happens or the baseline is deliberately updated.

## 4. Periodic check-in (propose upstream)

**Session scope note (hosted agent platforms).** Repo access is typically
fixed when a session is created: a session opened on the dependent repo
alone can usually *read* the public BestPractice repo (clone, fetch, diff)
but **cannot push branches or open PRs there** — writes fail even though
the day-to-day export loop (§3) works fine, because that loop is purely
local commits. So: **open check-in sessions with BOTH repos selected at
creation.** Everything else can be prepared, scrubbed, and audited in
ordinary single-repo sessions; only this step needs the dual-repo session.

On a schedule (a recurring `TODO.md` item), in a session with access to the
BestPractice repo. [tools/checkin.py](tools/checkin.py) drives the
mechanical steps against a local clone of the upstream repo; the deliberate
steps (review, PR, merge) stay manual:

1. Review the vendored tree's accumulated changes and every `diverged`
   manifest entry — export what's ready, or record in the entry's notes why
   an entry genuinely stays local.
   `python3 process/upstream/tools/checkin.py status <upstream-clone>`
   lists exactly what has accumulated.
2. `python3 process/upstream/tools/checkin.py push <upstream-clone>` —
   runs the **scrub audit first (must pass; nothing is copied on failure)**,
   then mirrors the vendored tree into the clone's working tree.
3. Commit in the clone on a branch and open a PR against BestPractice.
   Human review of that PR is the second scrub line — the blocklist catches
   known vocabulary; the reviewer catches what the blocklist doesn't know
   yet (and adds it to the blocklist).
4. When the PR merges:
   `python3 process/upstream/tools/checkin.py record <upstream-clone> --note "PR #N"`
   — pulls the upstream default branch, **verifies it is byte-identical to
   the vendored tree**, and writes the landed hash into `upstream.commit`.
   Commit the manifest change (and `--update-baseline` if entries moved).

## 5. The manifest schema (`process/manifest.json`)

```json
{
  "upstream": {
    "repo": "https://github.com/<owner>/BestPractice",
    "vendored_at": "process/upstream",
    "commit": "<hash of the upstream commit last synced>"
  },
  "entries": [
    {
      "practice": "doc-lint",
      "upstream_path": "tools/doc_lint.py",
      "local_path": "tools/doc_lint.py",
      "granularity": "file",
      "status": "synced",
      "local_sha256": "<filled by practice_audit --update-baseline>",
      "notes": "what was adapted, and anything an updater must preserve"
    },
    {
      "practice": "merge-runbook",
      "upstream_path": "templates/CLAUDE.md.template",
      "local_path": "CLAUDE.md",
      "granularity": "section",
      "section_marker": "## Merge runbook",
      "status": "synced",
      "notes": "file classes adapted to this repo"
    }
  ]
}
```

- `granularity: "file"` — audited exactly: `local_sha256` is the baseline;
  any later change to the local file flags the entry until it is exported
  and re-baselined, or flipped to `diverged`.
- `granularity: "section"` — audited approximately: the audit only verifies
  `section_marker` still occurs in `local_path` (warn on miss). Used where a
  practice was woven into an existing document rather than installed as a
  file. This is the fuzziest part of the machinery — prefer file granularity
  where you can.
- `status`: `synced` (installed copy matches its baseline) · `diverged`
  (local improvement pending export) · `local-only` (deliberately not
  exported; say why in `notes`).

## 6. The audit (`tools/practice_audit.py`)

```
python3 process/upstream/tools/practice_audit.py                    # full check (gate)
python3 process/upstream/tools/practice_audit.py --update-baseline  # re-record hashes
```

Checks, in order — any FAIL exits non-zero:

1. **Scrub** (practice 15): every text file under `process/upstream/`
   scanned against `process/scrub_blocklist.txt`. Any hit → FAIL. (Skipped,
   with a notice, if no blocklist exists — a public dependent repo.)
2. **Drift** (practice 7): for each `file`-granularity entry, current hash
   vs `local_sha256`. Changed while `status: "synced"` → FAIL (export it or
   flip to `diverged`). `diverged` entries are listed as pending export,
   not failed.
3. **Integrity:** manifest paths exist; `section_marker`s found (warn);
   `local-only` entries have notes.

## 7. Practice packs (domain layers)

A repo can install additional practice layers beside this upstream —
**packs** (practice 23): domain-scoped practice sets (a compliance regime, a
lab workflow, a regulated-filing process) that are too domain-bound for this
public upstream but too general to be one repo's local rules. Mechanics:

1. **Anatomy mirrors this upstream.** A pack is a vendored tree at
   `process/<pack>/` — its own `PRACTICES.md`, `INSTALL.md`, `tools/`,
   `templates/harness/…` — destined for its own repo someday; until that
   repo exists, the vendored tree *is* the upstream and `upstream.commit`
   stays `null`.
2. **One manifest per layer.** The pack's manifest lives at
   `process/manifest_<pack>.json`, same schema as §5, with
   `upstream.vendored_at` pointing at the pack tree. `practice_audit.py`
   discovers and audits every `process/manifest*.json` in one run.
3. **Per-pack scrub.** The manifest's `upstream.scrub_blocklist` names the
   pack's own blocklist (the repo vocabulary that must not leak *into the
   pack*); an explicit JSON `null` opts a private pack out of the scrub.
   When the key is absent, the default `process/scrub_blocklist.txt`
   applies (the public gate).
4. **Routing.** A pack ships harness adapters that declare *when its rules
   apply* — for agent harnesses, a skill whose description triggers on the
   domain's work, pointing the agent at the repo's instantiation file and
   the pack catalog. The repo's base instructions stay lean; domain rules
   load when the domain work happens.
5. **The loops are shared.** Install (§1), update (§2), export gate (§3),
   and check-in (§4) all apply per pack, against the pack's own tree,
   manifest, and (eventual) upstream repo.

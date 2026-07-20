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
6. Run `python3 process/upstream/tools/practice_audit.py` — it must pass.
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
3. Replace `process/upstream/` with the new tree, update
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

On a schedule (a recurring `TODO.md` item), in a session with access to the
BestPractice repo:

1. Review the vendored tree's accumulated changes and every `diverged`
   manifest entry — export what's ready, or record in the entry's notes why
   an entry genuinely stays local.
2. **Re-run the scrub audit.** It must pass.
3. Open a PR against BestPractice with the `process/upstream/` diff. Human
   review of that PR is the second scrub line — the blocklist catches known
   vocabulary; the reviewer catches what the blocklist doesn't know yet
   (and adds it to the blocklist).
4. When the PR merges, update `upstream.commit` and `--update-baseline`.

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

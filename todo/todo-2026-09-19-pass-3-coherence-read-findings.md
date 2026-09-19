---
slug:              todo-2026-09-19-pass-3-coherence-read-findings
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "the repo owner's call on which findings below are worth acting on -- most are architecture and consolidation judgments, not defects a session should resolve unilaterally"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-19
closed:            null
---
## What

- <a id="pass-3-coherence-read-findings"></a>**Pass 3 of a very deep check
    (2026-09-19) read all 130 `practices/*.md` files for coherence —
    contradictions, staleness, disproportion, formatting drift,
    self-application gaps, duplication — and found 25 concrete items.** The
    small, mechanical ones were fixed in the same pass: 13 stale
    `[spawn-session](...)` link labels (the rename to `session-text` moved
    the targets but not the visible text) across
    [practices/](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/),
    [spec/CHIEF_OF_STAFF.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/CHIEF_OF_STAFF.md)
    and
    [record/GOTCHAS.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/record/GOTCHAS.md);
    5 stray `~` approximations that should read `≈`
    (`doc-references-are-links`); and 2 unexpanded `VCS` first-uses
    (`acronyms-glossary`) in
    [docs-are-current-state.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/docs-are-current-state.md)
    and
    [no-version-suffix.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/no-version-suffix.md).
    **What's left needs a person's judgment, not a session's:**

  **Contradictions**
  - `session-text.md` retires `create_session`/waking a live session
    ("Never call `create_session`... and never wake a live one either —
    not since 2026-09-16"), but `session-tags.md`, `session-title-names-the-difference.md`
    and `seeded-prompt-names-its-origin.md` all still instruct a session
    how to use `create_session`'s fields, with no acknowledgment the
    mechanism is retired. Two of the three read as unreachable dead
    letters as written.
  - The same retirement's own reasoning (portability — `create_session`
    is Claude-Code-Remote-only) is not applied to `archive-command.md`,
    `archive-status-check.md`, `the-boildown.md`'s archive condition, or
    `session-tags.md`, which all mandate other Claude Code Remote
    (CCR)-only tools
    (`get_session`, `archive_session`, `list_triggers`, `list_sessions`,
    `set_session_tags`) without raising the same question.
  - `session-bootstrap.md`'s recommended stop hook ("a stop hook that
    blocks on uncommitted, untracked, or unpushed work") is the exact
    mechanism `brainstorm-holds-commits.md` warns against ("a working
    tree it left dirty is one a Stop hook... will push to finish"). A
    repo that installs the recommended hook cannot cleanly end a
    brainstorm turn, and neither practice names the conflict.
  - `archive-command.md` orders the archive instruction ("no
    confirmation, no recap first") before the clause explaining why that
    is destructive (uncommitted/unpushed work does not survive). Reads as
    a deliberate reconciliation with `the-boildown`'s three gating
    conditions rather than an oversight, but the safety clause is in the
    wrong reading order.
  - Softer: `brainstorm-holds-commits` ("write nothing... commit
    nothing") vs. `findings-return-through-repo` ("commit it... never
    leave it for the person to relay") — resolvable by sequencing, but
    `brainstorm-holds-commits` only narrows itself against `small-calls`
    by name, not this one.

  **Staleness**
  - `scrub-gate.md`'s Rule names only `process/scrub_blocklist.txt` +
    `tools/practice_audit.py`; the actual push-time gate in this repo is
    `tools/leak_gate.py` with `tools/leak-blocklist.default.txt`, which
    `leak-gate-is-background.md` governs. Neither practice cross-references
    the other.
  - Several `applies_to` globs point at trees this repo does not have
    (`process/upstream/**` in `scrub-gate.md` and `practice-export-loop.md`;
    `tools/checks/**/*.py` in `checks-carry-a-declared-decline.md`, also
    cited by `practice-links-travel.md`, `fixture-owns-its-state.md`,
    `rename-updates-links.md`, `decommission-deletes-files.md`) — real
    paths in a *consumer* repo, but nothing in these Rules says so.
  - `write-like-a-human.md` and `no-invented-specifics.md` cite
    `templates/VOICE.md.template`, retired 2026-09-17. Both note this
    parenthetically already, so lower priority than the rest here.

  **Disproportion**
  - `very-deep-check.md` is ≈19,225 words — roughly 13% of the entire
    130-file catalogue in one on-request-only practice. Its `approved_by`
    frontmatter field alone is a ≈3,449-word chained changelog, which is
    exactly the "Rev N ladder" shape `docs-are-current-state.md` forbids
    in a document body (not obviously exempt just for living in
    frontmatter). Similar tail: `vendor-update-runbook.md` (2,730 words
    of `approved_by`), `fail-gracefully.md` (1,949),
    `chief-of-staff.md` (1,529).
  - `tools/session_load_budgets.json`'s one `"why"` string holds
    ≈2,000 words of run-by-run history, inside the file
    `registry-source-of-truth.md` holds up as the model shape for a
    registry.
  - `severity:` carries almost no signal — 128 of 130 practices are
    `default`; only `full-practice-audit` and `very-deep-check` are
    anything else (`advisory`). Practices with real irreversible-action
    stakes (`no-rewrite-for-warnings`, `scrub-gate`, `diagnosis-is-measured`)
    sit at the same declared severity as a formatting preference.
  - The 11-practice `tier: resident` set (always loaded) includes a
    skim-formatting preference (`bold-key-phrases`) and two short
    lookup-table rules, while irreversible-action rules
    (`no-rewrite-for-warnings`, `relayed-authorization`, `scrub-gate`,
    `diagnosis-is-measured`) are all on-demand.

  **Formatting drift** (against `spec/PRACTICE_FORMAT.md`)
  - 39 of 130 practices have no real `## Detail` content (8 missing the
    heading outright, 31 with a hollow header) — `spec/PRACTICE_FORMAT.md`
    records this as "five practices that could not be split" at the time
    it was written; the real count has grown to 39.
  - `spec/PRACTICE_FORMAT.md:260` records `## Rule` sections over 150
    words shrinking to 7; measured now at 54 of 130, with several over
    1,900 words (`vendor-update-runbook`, `session-text`,
    `next-steps-after-commit`, `very-deep-check`, `the-boildown`).
  - Minor: 6 practices missing `index_clause`, 3 missing `in_force_at`, 8
    with an unquoted `added:` date (parses as a YAML date rather than a
    string, inconsistent with the rest of the catalogue).

  **Self-application gaps**
  - `practice-links-travel.md`'s own governed files
    (`tools/precedent_check.py`, `build_views.py`, and three others) are
    linked both relatively and as absolute `blob/precedent-beta-v01/`
    URLs across different practices — two conventions for the same files.
  - `checkable-gets-checked.md` and `convention-to-audit.md` share the
    same occasion ("writing a new convention or rule") with different
    timing guidance and no cross-reference between them.

  **Duplication / overlap, no shared spine**
  - The "capture" cluster: `capture-gate`, `second-pass-capture`,
    `item-closes-on-its-condition`, `findings-return-through-repo`,
    `cross-source-rollout` — heavily overlapping occasions, only partial
    cross-referencing.
  - The "disclose a rollout" cluster: `disclose-landing`,
    `vendor-rollout-disclosed`, `github-setup-disclosed` — same shape,
    three slugs, no mutual reference.

  **Read clean, stated for completeness (per the practice's own
  instruction that a category with nothing found still gets said
  plainly):** no broken intra-catalogue links; no skipped heading levels
  anywhere; `catalogue-carries-stories` and `headline-capitalization`
  self-apply cleanly across the whole tree; `filename-separator`
  self-applies; the four `status: deduplicated` practices are correctly
  routed and nothing links to them; `routing-audit`/`full-practice-audit`/`very-deep-check`
  and `quick-index`/`orientation-map` are genuinely not duplicates of
  each other despite the surface overlap.

  **One process note the read surfaced:** `precedent_check.py`'s
  rotation left `scrub-gate`, `rename-updates-links`,
  `practice-links-travel`, `quick-index`, `orientation-map`,
  `technical-describes-people` and `document-status-header` unrun on the
  commit that would have caught several of the findings above — a
  `--full-sweep` is the cheapest next probe and was not run as part of
  this pass (it changes no state but is long).

## How It Closes

Not open until: the repo owner reviews the findings above and says which
are worth acting on. Most are consolidation or policy calls (retire
`session-tags`/`session-title-names-the-difference`/`seeded-prompt-names-its-origin`
properly or un-retire `create_session`; decide `very-deep-check.md`'s
approved_by history should move to a Story-style prose record rather than
frontmatter; decide whether the capture/disclosure clusters should merge)
rather than something with one obviously correct fix.

## Notes

2026-09-19: filed from pass 3 of a very deep check
([spec/VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md)), read by a
dedicated sub-agent over the full 130-file catalogue.

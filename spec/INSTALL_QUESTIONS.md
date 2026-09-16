---
title:         Install and migration questions — the canonical list
kind:          reference
status:        current
opened:        2026-09-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Every question a session asks a person during a fresh install, an upgrade, or a migration — one table, so SETUP.md, INSTALL.md and MIGRATING_EXISTING_INSTALLS.md derive their counts and wording from it instead of each carrying their own."
---

# Install and migration questions — the canonical list

**One table, one row per question a session actually asks a person** —
[registry-source-of-truth](../practices/registry-source-of-truth.md): the
list lives here, and [SETUP.md](../SETUP.md), [INSTALL.md](../INSTALL.md)
and [MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md) point
at it rather than each stating its own count and wording. Before this
document, SETUP.md said *"ask exactly three questions"* while
`MIGRATING_EXISTING_INSTALLS.md`'s Step 0 asked a fourth in prose nobody
counted — three places that could each go stale independently, and did:
adding a question meant remembering to edit all three.

**Not every fact an install records is a question.** `visibility` and
`base_branch` are read from the repository, never asked — they belong in
[precedent.json](../precedent.json)'s own schema, not here. This table is
only for what genuinely cannot be known without asking the person.

| Question | Asked when | Why | Stored into |
|---|---|---|---|
| What is this project about? (one or two sentences) | Fresh install | Fills the placeholders a fresh install leaves — the README opening, `MAP.md`'s deliverables — from the project's own subject matter rather than a generic stand-in | `README.md`, `MAP.md` |
| Are there private names or code words that must never appear in anything public? | Fresh install and migration | Precedent is a branch of a public repository, so anything folded back upstream is a publication; this list is the guard that keeps a repo's private vocabulary out of it | `process/scrub_blocklist.txt` |
| Does your team already have its own practices repo, or do you personally have one — and if not, would you like one set up now? | Fresh install and migration | Precedent is one of three layers; a team's shared conventions and one person's own facts each live in their own repo. **Has to be asked, not detected** — an undeclared source throws no error and leaves nothing missing, so the repo just resolves fewer practices than its owner believes, silently | `precedent.json`'s declared sources |
| Which AI assistant will actually be working in this repo? (Claude Code, ChatGPT connected to GitHub, other) | Fresh install and migration | Changes whether `ci_workflows` should default to disabled at all: [GITHUB_ACTIONS.md](../GITHUB_ACTIONS.md) explains that GitHub Actions exists partly to give an assistant with no terminal access (ChatGPT) the execution environment one with terminal access does not need — for a ChatGPT-only repo, Actions may be the only place certain checks can run at all | `identity.json` or `precedent.json`, alongside the `ci_workflows` answer below |
| Should `ci_workflows` be on or off? | Fresh install and migration | **Default disabled**, unless the person says otherwise — GitHub Actions minutes are metered per private repository and billed per run; see [GITHUB_ACTIONS.md](../GITHUB_ACTIONS.md)'s "Controlling Actions Minutes" and [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) for the measurement behind that default | `identity.json`'s `ci_workflows` field |

**A migration asks the same list a fresh install does**, not a shorter one
— a repo migrating onto the three-source model has never been asked any of
these, which is exactly what makes migration "the cheapest moment this
question will ever have" (`MIGRATING_EXISTING_INSTALLS.md`'s own words for
the source-declaration question, true of every row here).

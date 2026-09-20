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
| What is this project about? (one or two sentences) — and: want `AGENTS.md`'s quick-index and `MAP.md`'s deliverables filled in with specifics now, or left as placeholders? | Fresh install | The one-sentence answer fills the README opening and `MAP.md`'s summary from the project's own subject matter rather than a generic stand-in. It is not enough on its own to fill `AGENTS.md`'s per-topic quick-index table or `MAP.md`'s deliverables rows — those need real lookups, not a pitch — so [Essentials only](../INSTALL.md#essentials-only--what-an-install-upgrade-or-migration-leaves-for-later) defers them to placeholders by default ([declared-default-is-applied](../practices/declared-default-is-applied.md)); ask the second half only so a person who wants it done now, while they are already answering the first, is not left assuming a later conversation was required **Default when the person says "you decide":** the one-sentence answer cannot be defaulted (it is the project's own subject), but the second half can — placeholders, filled in a later conversation. | `README.md`, `MAP.md`, `AGENTS.md` |
| Are there private names or code words that must never appear in anything public? | Fresh install and migration | Precedent is a branch of a public repository, so anything folded back upstream is a publication; this list is the guard that keeps a repo's private vocabulary out of it **Default when the person says "you decide":** none declared beyond the committed default list; the session says so and leaves `PRECEDENT_LEAK_BLOCKLIST` unset. | `process/scrub_blocklist.txt` |
| Does your team already have its own practices repo, or do you personally have one — and if not, would you like one set up now? | Fresh install and migration | Precedent is one of three layers; a team's shared conventions and one person's own facts each live in their own repo. **Has to be asked, not detected** — an undeclared source throws no error and leaves nothing missing, so the repo just resolves fewer practices than its owner believes, silently **Default when the person says "you decide":** declare no shared or individual set now, and make the set-up offer in the same breath — a set can be declared later at no cost, an undeclared one is never missed by any check. | `precedent.json`'s declared sources |
| Which AI assistant will actually be working in this repo? (Claude Code, ChatGPT connected to GitHub, other) | Fresh install and migration | Changes whether `ci_workflows` should default to disabled at all: [GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md) explains that GitHub Actions exists partly to give an assistant with no terminal access (ChatGPT) the execution environment one with terminal access does not need — for a ChatGPT-only repo, Actions may be the only place certain checks can run at all **Default when the person says "you decide":** the assistant this session is itself running under. | `identity.json` or `precedent.json`, alongside the `ci_workflows` answer below |
| Should `ci_workflows` be on or off? | Fresh install and migration | **Default depends on the platform answer above, not a flat default.** No terminal access (ChatGPT, or anything else with no local shell) → default **enabled**: Actions is the only place any check can run there at all, and defaulting it off leaves that repo with zero enforcement no matter what a session recommends. A platform with its own bootstrap and hooks (Claude Code, Codex, Gemini CLI) → default **disabled**, per [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md)'s measurement — local enforcement already covers it, and GitHub Actions minutes are metered per private repository and billed per run. Either way, say the default out loud and record what the person actually chooses | `identity.json` **only** — [tools/precedent_identity.py](../tools/precedent_identity.py)'s `ci_preference()` never reads `precedent.json` for this field. Concretely: the repo's own `identity.json` if the repo itself IS a declared individual or team source; otherwise the person's individual source's `identity.json`, resolved through their user-level config. There is no separate per-project override today — declaring it is a standing preference for every repo that resolves through that identity, and it takes effect for a given dependent repo only the next time *that* repo installs, migrates, or takes an [Update Vendors](../practices/vendor-update-runbook.md) pass, never retroactively. Where that identity source is a private repo this session cannot reach, say so and hand the person to a session rooted there ([session-text](../practices/session-text.md)) rather than guessing at a workaround. |

**Every row carries a default, and "you decide" applies it.** A person
who does not know what a row means — the first non-technical owner to
migrate a repository was asked about team sets, an individual set wired
through an environment credential, and `ci_workflows`, and knew what two
of the three meant — is not asked to learn it on the spot. The session
names the default and its consequence in the question; "you decide", or
any answer that plainly hands it back, applies the default and records it
as `assented` ([declared-default-is-applied](../practices/declared-default-is-applied.md),
[decision-strength](../practices/decision-strength.md)). The one row with
no default is the project's own subject, which nobody but its owner can
supply.

**A migration asks the same list a fresh install does**, not a shorter one
— a repo migrating onto the three-source model has never been asked any of
these, which is exactly what makes migration "the cheapest moment this
question will ever have" (`MIGRATING_EXISTING_INSTALLS.md`'s own words for
the source-declaration question, true of every row here).

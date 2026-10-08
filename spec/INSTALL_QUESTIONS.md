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
| What is this project about? (one or two sentences) — and: want `AGENTS.md`'s quick-index and `MAP.md`'s deliverables filled in with specifics now, or left as placeholders? — and, in the same breath, confirm the three things the installer needs that the session reads rather than asks: the project's name (from the repository's name), the GitHub handle of whoever administers it (the account running the install), and which folders hold what it publishes (from the tree; none yet is a complete answer) | First install only, never an update | The one-sentence answer fills the README opening and `MAP.md`'s summary from the project's own subject matter rather than a generic stand-in. It is not enough on its own to fill `AGENTS.md`'s per-topic quick-index table or `MAP.md`'s deliverables rows — those need real lookups, not a pitch — so [Essentials only](../INSTALL.md#essentials-only--what-an-install-upgrade-or-migration-leaves-for-later) defers them to placeholders by default ([declared-default-is-applied](../practices/declared-default-is-applied.md)); ask the second half only so a person who wants it done now, while they are already answering the first, is not left assuming a later conversation was required. The name and the administrator are the installer's `--project-name` and `--admin`; the published folders are `output_paths`, without which the heading-capitalization check reads the whole tree as published ([INSTALL.md](../INSTALL.md)'s `output_paths` note). Each is said as what the session will use, for the person to correct, not asked open **Default when the person says "you decide":** the one-sentence answer cannot be defaulted (it is the project's own subject), but the second half can — placeholders, filled in a later conversation; the name, administrator and published folders default to what the session read. | `README.md`, `MAP.md`, `AGENTS.md`; the installer's `--project-name` and `--admin`; `precedent.json`'s `output_paths` |
| Are there private names or code words that must never appear in anything public? | Fresh install and migration | Precedent is a branch of a public repository, so anything folded back upstream is a publication; this list is the guard that keeps a repo's private vocabulary out of it **Default when the person says "you decide":** none declared beyond the committed default list; the session says so and leaves `PRECEDENT_LEAK_BLOCKLIST` unset. | the individual set's `leak-blocklist.txt` (a §0 install has no `process/scrub_blocklist.txt`) |
| Does your team already have its own practices repo, or do you personally have one — and if not, would you like one set up now? | Fresh install and migration; the named offer below, first install only, never an update | Precedent is one of three layers; a team's shared conventions and one person's own facts each live in their own repo. **On a first install, offer the two public shared sets by name**, one sentence each, with the session's pick: the writing set ([precedent-shared-writing](https://github.com/themorgan/precedent-shared-writing)), rules for documents people read, which a project that writes for anyone usually wants and which the repository declares in `precedent.json`; and the ladder set ([precedent-shared-ladder](https://github.com/themorgan/precedent-shared-ladder)), a way of working where every change moves through named stages and a test branch before it reaches `main`. The ladder set follows a person rather than a repository: it goes in the `brings` list of their individual set ([INSTALL.md](../INSTALL.md)), never in this repository's `precedent.json`, so a yes from someone with no individual set is a yes to setting one up, and a yes from the person doing this install also decides whether the first landing makes the branch tiers (INSTALL.md's first-landing step 5). The offer is an offer with a recommendation, never an open "which sets do you want?" (Morgan, 2026-10-08, `strength: decided`). **The ladder set is mentioned this once.** A no, or no answer, is final: the session never raises it again, nor its stages, test branches or commands, and the person gets the plain install everyone off the ladder gets (Morgan, 2026-10-08: *"if they don't accept it, we need to never mention it or anything about it again"*, `strength: decided`). **Has to be asked, not detected** — an undeclared source throws no error and leaves nothing missing, so the repo just resolves fewer practices than its owner believes, silently **Default when the person says "you decide":** declare no shared or individual set now, and make the set-up offer in the same breath — a set can be declared later at no cost, an undeclared one is never missed by any check. | `precedent.json`'s declared sources; the ladder set, the person's individual set's `brings` list |
| Which AI assistant will actually be working in this repo? (Claude Code, ChatGPT connected to GitHub, other) — and, for Claude Code: may the install commit its hooks and settings (`.claude/`)? | Fresh install and migration | The second half because Claude Code's auto mode holds any commit that changes `.claude/` until the person says yes, and no setting lifts that; asked only at commit time, it stalls the install at its last step (2026-10-08). Default for it when the person says "you decide": yes, since sessions there load no practices without the hooks. The first half changes whether `ci_workflows` should default to disabled at all: [GITHUB_ACTIONS.md](../documentation/GITHUB_ACTIONS.md) explains that GitHub Actions exists partly to give an assistant with no terminal access (ChatGPT) the execution environment one with terminal access does not need — for a ChatGPT-only repo, Actions may be the only place certain checks can run at all **Default when the person says "you decide":** the assistant this session is itself running under. | `identity.json` or `precedent.json`, alongside the `ci_workflows` answer below |
| Should `github_ci_workflows` be on or off? | Fresh install and migration | **Default enabled, since 2026-09-25** (Morgan; `ci_preference()` in [tools/precedent_identity.py](../tools/precedent_identity.py)): what installs is one light check that runs only on a pull request into `main` and a leak gate that never runs in a private repository — about one billed minute per merge into `main`. For a platform with no terminal access (ChatGPT) it is the only place any check can run at all. Until 2026-09-25 the default was disabled for platforms with their own hooks, per [spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md). Say the default out loud and record what the person actually chooses; only `"disabled"` needs writing down | `identity.json` **only** — [tools/precedent_identity.py](../tools/precedent_identity.py)'s `ci_preference()` never reads `precedent.json` for this field. Concretely: the repo's own `identity.json` if the repo itself IS a declared individual or shared source; otherwise the person's individual source's `identity.json`, resolved through their user-level config. There is no separate per-project override today — declaring it is a standing preference for every repo that resolves through that identity, and it takes effect for a given dependent repo only the next time *that* repo installs, migrates, or takes an [Update Vendors](../practices/vendor-update-runbook.md) pass, never retroactively. Where that identity source is a private repo this session cannot reach, say so and hand the person to a session rooted there ([prompt-please](../practices/prompt-please.md)) rather than guessing at a workaround. |

**Every row carries a default, and "you decide" applies it.** A person
who does not know what a row means — the first non-technical owner to
migrate a repository was asked about shared sets, an individual set wired
through an environment credential, and `ci_workflows`, and knew what two
of the three meant — is not asked to learn it on the spot. The session
names the default and its consequence in the question; "you decide", or
any answer that plainly hands it back, applies the default and records it
as `assented` ([declared-default-is-applied](../practices/declared-default-is-applied.md),
[decision-strength](../practices/decision-strength.md)). The one row with
no default is the project's own subject, which nobody but its owner can
supply.

**A migration asks the same list a fresh install does**, not a shorter one,
less what a row marks as first install only — a repo migrating onto the three-source model has never been asked any of
these, which is exactly what makes migration "the cheapest moment this
question will ever have" (`MIGRATING_EXISTING_INSTALLS.md`'s own words for
the source-declaration question, true of every row here).

**An update asks none of them.** [Update Vendors](../practices/vendor-update-runbook.md)
checks the declared sets itself and says what it found, without a
question; the named offer of the two shared sets and the installer's three
facts belong to a repository's first install alone (Morgan, 2026-10-08:
*"these questions happen ONLY upon the first time install, \*NOT\* upon an
upgrade"*).

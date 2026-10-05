---
slug:        default-branch
title:       The host's default branch is the repo's trunk, whatever it is called
tier:        on-demand
severity:    default
applies_to:  ["precedent.json"]
applies_to_why: "The file every install writes: precedent_install.py creates precedent.json and declaring a set edits it, which is the moment this rule fires. The occasion index reaches the same moment through install's line, which carries this rule's clause since 2026-10-01; the check below refuses a wrong default branch at push either way. Before 2026-10-01 this was `**` and the index carried it. Decided: Morgan, 2026-10-01 (reduction pass)."
occasion:    "setting up or installing into a repo"
gates:       []
index_clause: "the host's default branch is the trunk, whatever its name; ask if unclear"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "pending PR review -- drafted 2026-10-05 by Morgan F, moved from the shared set precedent-shared-repo-maintenance"
strength: decided
---
## Rule
Every repo has one **trunk**: the branch everything ends up on. Its name is the repo's own choice -- `main`, `master`, `trunk` or anything else -- and nothing here renames it. What matters is that **the host's default branch is the trunk**, so every clone, pull request and automation run lands on it without anyone saying so.

Find the trunk, in order: the `trunk` that `precedent.json` declares; else its `base_branch`, when the host already shows that branch first; else, when nothing is declared, the branch the host shows first. When the host's default and `base_branch` differ and no `trunk` is declared, the repo has not said which branch is the trunk: **ask the person once, then record the answer as `trunk`** in `precedent.json`. When the declared trunk and the host's default disagree, set the host's default once -- via a host API where the session's tools reach that far, otherwise as a one-click administrator item, disclosed in the repo's own onboarding document -- or correct `trunk` if the host was right.

For a brand-new, blank repo with no branches yet, there is nothing to check or set: make the very first commit directly on the branch that will be the trunk (`main` unless the person says otherwise) and push that first, not a feature or planning branch -- the host adopts the first branch ever pushed to an empty repo as its default automatically.

## Detail
One-time per repo either way -- once set, every subsequent clone, PR, and CI run already targets the trunk on its own, nothing to repeat. A repo whose work lands on a lower tier and is promoted upward (`base_branch: staging`, promoted to `main`) declares `trunk` once, so nobody has to guess.

## Why
A host only defaults a freshly-created repo to its own default name; plenty of repos predate that, or arrived some other way (an import, a mirror, an org policy), and their default can point at something that is not the trunk at all -- a planning branch, a stale one. The name was never the problem: a repo whose trunk is `master` by decision is as sound as one on `main`.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration; the Story is backfilled from that pack's own text, and there are
two real incidents behind it -- one per branch of the rule.

The first: RepoPersonalPreferences itself sat on a default branch that was
not `main` until it was corrected by hand on 2026-08-21. The host only
defaults a *freshly created* repository to `main`; a repo that predates that
default, or arrived by an import, a mirror, or an organization policy, can
sit on something else indefinitely with nothing to flag it. That is why the
rule says to check at install rather than assume.

The second is the reason the brand-new-repo case is written as a separate
branch rather than folded into the first. An install session treated a
blank repo as though it were an existing one, went looking for a default
branch to check, discovered partway through that the repo had no `main` at
all, and then created one through the host's API from a planning branch's
tip after the fact. Every step of that was avoidable: a blank repo has
nothing to check and nothing to set, because the host adopts the first
branch ever pushed to it as the default automatically. Making the first
commit directly on `main` satisfies the rule outright.

One-time per repo either way. Once set, every later clone, pull request and
automation run already targets the trunk on its own.

**2026-10-05: the trunk's name is the repo's (S. Alexander Jacobson: "They
are both the same idea. Different repos will have different names for
whatever branch serves this function").** The rule as ported that morning
demanded the name `main`. A consumer whose trunk is `master` by decision
failed its check, and the failure undid the consumer's whole Update Vendors
run. The rule now asks whether the host's default is the trunk, reads the
trunk from what the repo declares, and asks the person when nothing does.

**2026-10-01: out of the occasion index, still in force** (Morgan, in the
reduction pass: *"Question 3 - all are great, approved"*, strength:
decided). The review proposed that `install` absorb this practice, since
both fire at the same moment. `install`'s index line now names the default
branch, and this practice routes by path instead, on `precedent.json`. It
was kept `active` rather than deduplicated because
its check is keyed to this slug, and the engine skips the check of a practice that is
not in force. The Rule above is unchanged.

## Install
Checked mechanically by [tools/precedent_check.py](../tools/precedent_check.py)'s `default-branch` check, scope `tree`: `git ls-remote --symref origin HEAD` asks the remote which branch it points at, no clone required. If the remote can't be reached (no network, no credential, no `origin`), the check reports SKIPPED rather than a silent pass. It compares the host's default with the declared `trunk`, else `base_branch`; where those leave the trunk unsettled it reports COULD NOT VERIFY, never a violation. Its planted case in `tools/verify_harness.py` points `origin` at a local bare repository whose HEAD is `trunk` while this repo declares `main`, and `check_default_branch_reads_each_repos_trunk` covers a `master` trunk, a mismatch, an undeclared repo and the ask. Ported on 2026-10-05 from the shared set this practice moved from, where it was a script under `tools/checks/`.

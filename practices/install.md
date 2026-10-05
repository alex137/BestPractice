---
slug:        install
title:       Installing a vendored practice set into a repo
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Installing touches a repository that has no Precedent files yet, so no path inside it can name the moment; the occasion index reaches it."
occasion:    "installing Precedent or a shared set into a repo"
gates:       []
index_clause: "precedent_install.py, declare the set, wire the individual set, trunk as default"
checked_by:  null
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
Install Precedent with its own installer, `python3 tools/precedent_install.py` (Precedent's INSTALL.md section 0), and declare each shared set the repo uses in its `precedent.json` `sources`. A shared set is cloned beside the repo, never vendored into it; the section 1 vendored install was retired on 2026-09-23. Then wire the person's individual set, per Detail. Check that the target repo's default branch is its trunk, whatever it is called, and set it once if not, as `default-branch` says (its check still runs on its own).

## Detail
This applies the same way when the target repo already has some pieces present because they arrived indirectly -- a fork, a copy, an older install -- rather than fresh from the installer. Do the missing pieces; presence of one file is not evidence the rest came with it.

Where the person working in the target repo has their own individual set, this install also wires that up -- a distinct step from declaring the shared sets, since an individual set is never committed into the target repo at all (that's the privacy boundary). Concretely, for a Claude Code Web session: copy that person's individual repo's own bootstrap script (a worked example of this pattern exists in the individual-set practice for it) into the target repo as a tracked `SessionStart` hook, so the individual source clones and configures itself before the session's first tool call -- no command run by hand, on any machine, by anyone whether or not they're a developer. Skip this step only if the person has no individual set, or explicitly doesn't want one wired into this particular project.

The default-branch step stays here, and `default-branch` stays in force as its own practice, only because its check, `check_default_branch.py`, is keyed to that slug: folding it into this Rule would stop the check.

## Why
Copying files by hand gets a repo the files, not what the installer writes beside them: `precedent.json`'s `sources`, which the session-start resolver reads to find each set beside the repo, and the engine's `tools/ENGINE_MANIFEST.json`, which records where every vendored file came from. Without the first, nothing finds the sets; without the second, the first Update Vendors cannot tell an upstream file from a local edit, so it cannot know what it may overwrite.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. This one is a procedure rather than a rule with a failure behind
it, so there is no originating incident to record and this Story does not
manufacture one.

What is worth carrying is why the procedure is a written checklist at all
rather than "vendor the tree and read the rules." Every step exists because
something is load-bearing beyond the files themselves: the conventions have
to be woven into the target repo's own agent instructions in reading-order
position or a session never sees them; the scheduled sync and check
workflows have to be installed or the vendored copy silently ages; the
session-start freshness snippets have to be added to the bootstrap script or
drift is never noticed; and every installed file has to be recorded in a
manifest with the source repo and commit, or a later sync has nothing real
to compare against.

A vendored tree without those mechanisms is the exact shape `drift-notice`
learned to detect and report as an incomplete install rather than as drift.
That is the strongest argument for following the procedure as written: the
failure it prevents is one another rule in this set had to grow a special
case to catch.

**2026-10-01: occasion and index line rewritten to match the Rule, and
default-branch's index line folded in** (Morgan, in the reduction pass:
*"Question 3 - all are great, approved"*, strength: decided). The old line,
"vendor the tree, weave conventions into AGENTS.md, wire checks and
manifest", described the section 1 vendored install retired on 2026-09-23,
while the Rule above already sent sessions to [`precedent_install.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_install.py). The
default-branch check happens at the same moment, so this line now carries
it and default-branch left the index by taking a real path
(`precedent.json`, which every install writes). It was not marked
deduplicated, because its check is keyed to its own slug and a practice not
in force has its check skipped.

## Install
No mechanical check: this rule describes a procedure a *target* repo's install session follows (run the installer, declare the shared sets, wire the individual set, check the default branch). This repo is the source being vendored, not a target -- there's no install here to verify the outcome of. A target repo could check its own manifest for completeness (light-check's own Detail section already covers exactly that), but that check would live there, not here.


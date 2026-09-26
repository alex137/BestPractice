#!/usr/bin/env python3
"""precedent_vendor_engine.py — vendors Precedent's engine into a repo that
consumes it, as real tracked files instead of an undocumented hand-copy.
Two KINDS, sharing one mechanism:

  'source'   — an individual or team practice SET (precedent-individual,
               precedent-team-repo-maintenance, precedent-team-tms). Needs
               ENGINE_FILES: enough to run its own AGENTS.md loader block
               (precedent_show.py's Rule/Detail/Why/Story/Install split,
               build_views.py's `--agents-only` regeneration,
               precedent_paths.py's path-trigger channel, precedent_gate.py's
               closed gate vocabulary), AND enough to resolve the person's
               own individual source, since a practice set is a repository
               somebody works in like any other (precedent_source_
               credentials.py, precedent_source_bootstrap.py). This is the
               original, narrower case this tool closed first — see
               spec/BOOTSTRAP_NEW_SOURCES.md.

  'consumer' — a real four-source CONSUMER repo (universal + team +
               individual + repo-local, a vendored process/upstream/, the
               full precedent_materialize.py/precedent_sync_views.py
               toolchain that resolves all of them into one materialized
               tree). Needs CONSUMER_ENGINE_FILES: everything 'source'
               needs, PLUS those materializing tools — see this repo's own
               engine-plus-host-shims practice ("domain-neutral mechanism
               lives in the vendored tree"). Piloted 2026-09-05 against
               a private consumer repo — INSTALL.md §1 step 12 and §2
               step 6 document the consumer-repo procedure this closes.

THE GAP 'source' CLOSED FIRST. tools/precedent_bootstrap_source.py has only
ever written practice content, config, approvers and the leak-blocklist —
never an engine file. Every individual/team set that existed before this
tool got its tools/build_views.py, precedent_gate.py, precedent_paths.py,
precedent_show.py and split_practices.py into place by an undocumented,
one-off hand-copy, so none of them could tell a stale copy from a current
one, and precedent-team-tms's copy was simply missing outright.

THE GAP 'consumer' CLOSES. A real consumer's own tools/ needing the same
treatment was named explicitly as future work when 'source' shipped
(the TODO item that named it — since closed and removed — said: "not
piloted... deliberately not folded into the source-repo fix"). A private consumer repo — a real four-source
consumer, not a fixture — had the identical undocumented-hand-copy problem
'source' closed for practice sets: its top-level tools/ held
build_views.py, precedent_gate.py, precedent_paths.py, precedent_show.py,
split_practices.py, precedent_materialize.py, precedent_resolve.py and
precedent_sync_views.py, all copied in by hand at some point in the past
with no manifest, no recorded source commit, and (confirmed 2026-09-05) six
of those eight files had already drifted from BestPractice's current
tools/ — including the --repo-awareness fix (commit 7c8d33d) and the
repo-local `path: "."` safety fix (commit 29148bc's sibling changes to
precedent_resolve.py/precedent_materialize.py), silently missing from the
consumer's copy the whole time.

Distinct from tools/checkin.py, which mirrors a CONSUMER's whole
process/upstream/ tree, deleting anything the tree no longer has, in BOTH
directions (a consumer pulls upstream content AND pushes its own
check-ins back). This engine is one-directional in both kinds —
downstream from BestPractice only, since neither a source set nor a
consumer's own tools/ has engine code of its own to contribute back — and
it sits inside tools/ ALONGSIDE non-vendored, repo-owned files (tools/checks/,
routing_scope.json is vendored but trimmed, a source set's own
build_codeowners.py, a consumer's own light_check.py/
report_automation_issue.py -- and its tools/bootstrap.sh, which since
2026-09-25 is refreshed only while it carries no local edits; see
TEMPLATE_INSTANCES) that a whole-directory mirror-and-delete would
destroy. So this is a NEW, narrower tool, not an extension of checkin.py:
it touches only the files it knows about, by name, per kind.

ENGINE_FILES / CONSUMER_ENGINE_FILES both name this script itself last, on
purpose: it travels WITH the engine it defines, so a future improvement to
the vendoring mechanism itself reaches every already-vendored repo the same
way an improvement to build_views.py does — not a second, undocumented gap
one layer up from the one this tool closes. precedent_materialize.py and
precedent_sync_views.py are never in ENGINE_FILES (source) — a source set
has no process/upstream/ and materializes nothing — but they ARE in
CONSUMER_ENGINE_FILES, where resolving four sources into one materialized
tree is the entire point.

precedent_resolve.py WAS in that consumer-only group until 2026-09-13, on
the reasoning that a source set has "nothing to resolve against more than
one tree". That half was wrong, and it cost a measured failure: a set
resolves nothing, so its generated occasion index carried its own entries
and not one of universal's 94, and a session rooted there worked with every
universal rule silently absent. A set has exactly one other tree to resolve
against — universal's — and resolving it is how those rules reach the
session. So precedent_resolve.py and precedent_session_practices.py are now
in ENGINE_FILES, and the set reads universal out of an UNTRACKED
.precedent/SESSION_PRACTICES.md rather than a committed copy
(spec/SOURCE_SET_PROSE_GAP.md, shape 3, approved 2026-09-13).

WHAT IS DELIBERATELY IN NEITHER LIST: verify_harness.py, and only it. It is
this repo's own harness for this repo's own engine; a consumer has nothing
for it to verify.

THIS PARAGRAPH USED TO NAME leak_gate.py AND very_deep_check.py TOO, and
that stopped being true on 2026-09-20/21 -- both are vendored now, in
ENGINE_FILES above. The old reasoning was that they "run only from a
BestPractice checkout, against whatever repositories that session can
see", so improving them reached every repo for free. That was accurate
while nobody could run them anywhere else, and it is exactly what made
them unreachable in a consuming repo: a leak gate that only upstream can
run does not guard a downstream tree, and a "Very deep check" a person
says in their own project cannot be carried out.

It is kept here rather than deleted because the incident it records still
teaches: on 2026-09-07 a change to those two tools was written up as
needing a per-set engine refresh, and an item was opened saying the sets
were running stale copies -- of files they had never held. The reasoning
came from cross-source-rollout, a real practice that simply did not apply.
Nobody checked these lists first. CHECK THEM BEFORE COSTING A ROLLOUT, and
note that the answer changed: a claim about this file's contents made from
memory is now wrong in both directions.

routing_scope.json is vendored in both kinds too, but it is not a
byte-identical copy: precedent_gate.py's SCOPE file carries two things in
this repo — the closed GATE vocabulary (`gates`, the moments a practice can
fire at, which is the same everywhere Precedent's loader runs, regardless
of kind) and a `practices` key documenting the routing reason for every one
of BestPractice's OWN 60-odd practices, which has no meaning in either a
source set or a consumer repo with a different catalogue entirely.
`_trim_routing_scope` below keeps only the first and drops the second — the
same trim a prior, undocumented hand-copy already applied by hand to every
repo that needed it (precedent-individual, precedent-team-repo-maintenance, and
and a private consumer repo's own top-level tools/routing_scope.json, all three
confirmed byte-identical to this function's output before this tool
existed, or was extended to the consumer kind); this tool just makes that
trim mechanical instead of a fact only the session that did it once
remembered.

SINCE 2026-09-15, the .claude/hooks/*.sh adapter scripts travel with the
engine too -- seed/status/refresh all cover them alongside tools/, tracked
in the same ENGINE_MANIFEST.json (see the HOOK_SOURCE_DIR block below for
why they are a second, smaller mechanism rather than folded into
ENGINE_FILES). Before this date they were installed once by
precedent_install.py and never refreshed, so a fix landing in a hook script
-- the freshness-guard.sh shallow-clone false-positive, record/GOTCHAS.md#g12,
is the incident that prompted this -- never reached an already-vendored
repo no matter how many times it ran `refresh`. .claude/settings.json itself
is still never touched by this tool, on purpose; see that block.

Five subcommands:

  seed <dest-dir> [--kind source|consumer]
                                  Run from BESTPRACTICE'S OWN checkout (the
                                  case tools/precedent_bootstrap_source.py
                                  needs — no clone required, the source IS
                                  this checkout). --kind defaults to
                                  'source' (unchanged CLI/API for every
                                  existing caller — precedent_bootstrap_
                                  source.py calls seed(dest) with no kind
                                  argument at all, and gets the same
                                  narrower set it always has). Copies the
                                  kind's file list and a trimmed
                                  routing_scope.json into <dest-dir>/tools/,
                                  and writes
                                  <dest-dir>/tools/ENGINE_MANIFEST.json
                                  recording this checkout's HEAD commit,
                                  the kind, and a sha256 per vendored file.

  status <bestpractice-clone>    Run from an ALREADY-VENDORED repo of
                                  either kind (same shape checkin.py's
                                  verbs use): reads `kind` back out of
                                  ENGINE_MANIFEST.json (no --kind flag
                                  needed — the manifest already says which
                                  file list applies) and compares the
                                  vendored files against its recorded
                                  hashes (local hand-edit?) and against the
                                  clone's current tools/ (upstream moved?).
                                  Exit 1 if either differs.

  refresh <bestpractice-clone> [--force] [--from-ref REF]
                                  Same kind auto-detection as status. Pulls
                                  the clone's SOURCE_BRANCH (see below —
                                  NOT the clone's configured default
                                  branch), refuses if a vendored file was
                                  hand-edited since the last seed/refresh
                                  (its sha256 no longer matches
                                  ENGINE_MANIFEST.json) unless --force, then
                                  re-copies + re-trims (the kind's own file
                                  list) and updates the manifest. Also keeps
                                  any file this repo's precedent.json maps
                                  under `engine_paths` (upstream path ->
                                  local path) current; see ENGINE_PATHS_KEY.

  fresh                          Clone-free staleness notice, no argument
                                  needed: one `git ls-remote` of
                                  ENGINE_MANIFEST.json's recorded repo,
                                  compared to the recorded commit. Always
                                  exits 0 (a notice, never a gate); silent
                                  on network failure vs. loud on a fast,
                                  clean failure (checkin.py's fresh() carries
                                  the same distinction and the same reason:
                                  an unreachable remote must never read as
                                  "confirmed fresh").

  record-ci                      Clone-free, like `fresh`: re-baseline THIS
                                  repo's own ci_workflow_files/ci_workflows_
                                  sha256 against whatever CI workflow
                                  file(s) are on disk right now, for the
                                  kind ENGINE_MANIFEST.json already
                                  declares. Content is never touched -- only
                                  the recorded hash. For the moment a CI
                                  workflow file was fixed BY HAND (an
                                  incident too urgent to wait for a
                                  `refresh --force`, which would also
                                  overwrite it back to the generic
                                  template) and now needs the manifest to
                                  stop calling it drifted. Also drops any
                                  RETIRED_CI_WORKFLOW_FILES entry the
                                  manifest still carries.

Run (from an already-vendored repo's own checkout, either kind):
  python3 tools/precedent_vendor_engine.py fresh
  python3 tools/precedent_vendor_engine.py status  ../BestPractice
  python3 tools/precedent_vendor_engine.py refresh ../BestPractice
  python3 tools/precedent_vendor_engine.py record-ci

Run once, from BestPractice's own checkout, to vendor a NEW consumer repo
(status/refresh above then work unchanged, kind auto-detected):
  python3 tools/precedent_vendor_engine.py seed <consumer-repo> --kind consumer

SOURCE_BRANCH is 'main', for every install at once, since 2026-09-25 --
the branch whose content has passed every local check AND the GitHub test
on the pull request into it (spec/BRANCH_TIERS_PLAN.md, "Installs take
their updates from main"). Morgan, 2026-09-25, after the first merge of staging into main: "Yes, switch all installs to main. ... Let's do it, go ahead, go update" (strength: decided). An install pinned to staging (or to
precedent-beta-v01, its name until that morning) takes this update from
main and is repointed there in the same update, per runbook step 1.

The history, because it was tried once before: on 2026-09-24 this read
'main' for a few hours on an approval Morgan later called assent rather
than a decision ("That was more an assent, than a decision. I didn't think
about it."), which left the installs split across two branches, and it went
back to precedent-beta-v01 ("for now, they should all follow
precedent-beta-v01"; "maybe later we'll move them all to follow main").
This is that later move, decided, and for every install at once.
"""
import collections
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve()
ENGINE_DIR = HERE.parent
ROOT = ENGINE_DIR.parent
SOURCE_REPO = 'https://github.com/alex137/BestPractice'
SOURCE_BRANCH = 'main'  # every install follows it -- see docstring

ENGINE_FILES = [
    'build_views.py',
    # The one place this engine asks GitHub anything, and the counter behind
    # precedent_check.py's github-api-budget check (added 2026-09-14). It
    # travels with the engine because the check travels with it: a consumer
    # told to "route this caller through tools/github_budget.py" needs the
    # file the finding names, and its own API-calling tools draw on the same
    # account allowances this repo's do. Its companion registry
    # (github_api_budgets.json) is deliberately NOT vendored -- a repo's
    # floors and per-tool budgets are its own declaration, the same way
    # session_load_budgets.json is.
    'github_budget.py',
    # build_views.py's companion word list, and the reason it is here rather
    # than left behind: the engine vocabulary it declares (level, source,
    # catalogue, slug, gate, resident block) is what an adopter needs to read
    # ANY practice at all, and every kind that gets build_views.py builds its
    # own GLOSSARY.md. Vendoring it verbatim is correct where
    # routing_scope.json needs trimming, because none of these terms is
    # specific to BestPractice's own catalogue. Caught 2026-09-08 by
    # vendored-engine-file-refs-resolve, on the run that added it -- a
    # vendored build_views.py naming a companion nobody had copied.
    'glossary_terms.json',
    # A team set's approvers.json -> CODEOWNERS generator. In the engine
    # rather than in one team set's own tools/ because that is where it
    # was, and the consequence was a second team set with declared
    # approvers and no way to enforce them (2026-09-06). No-ops in an
    # individual set, which has no approvers.json and needs none.
    'build_codeowners.py',
    'precedent_gate.py',
    'precedent_paths.py',
    'precedent_show.py',
    'split_practices.py',
    # Classifies practices carrying the OLD status vocabulary, where
    # `retired` meant both "the copy here is redundant" and "nobody wants
    # this rule anywhere" (2026-09-06). The legacy records are in the
    # private sets, never in BestPractice's own catalogue, so a migration
    # that only existed upstream could not reach the repos that need it.
    # It is also the only compliance signal a SOURCE set has for this:
    # verify_harness.py is deliberately not vendored, so
    # check_status_contract never runs there.
    'precedent_migrate_status.py',
    # The retirement audit (added 2026-09-07). In ENGINE_FILES rather than
    # the consumer half because retiring a mechanism is not a consumer-only
    # act -- a practice set retires its own tooling too, and the repo most
    # likely to be carrying dead files is one that migrated off something.
    # decommission-deletes-files' Install names it, so a repo resolving that
    # practice and lacking the file has a rule it cannot obey.
    'precedent_decommission.py',
    # The enforced channel itself (added 2026-09-07). Until then a SOURCE set
    # enforced nothing mechanically: this file was in CONSUMER_ENGINE_FILES
    # but not here, so a consuming repo got the checks and a practice set --
    # exactly where a migrated catalogue lands -- never did. That is why
    # cite-the-incident's demand for a ## Story did not reach the sets that
    # were migrated in with 36 empty ones, and why the status-contract check
    # was unreachable there too (TODO.md's convert-team-set-retired-statuses
    # records that half).
    #
    # A source set does NOT get this file's four optional dependencies:
    # doc_lint.py, doc_sync.py, title_case.py and precedent_resolve.py are
    # CONSUMER_ENGINE_FILES only, since a source set resolves no catalogue
    # and vendors no upstream tree. Every check needing one raises
    # NotApplicable by name, so those report SKIPPED with the missing module
    # named -- never ERRORED, and never a silent pass.
    'precedent_check.py',
    # Whether this environment can reach its PRIVATE sources at all, and the
    # credential helper that lets a SessionStart hook clone one without
    # add_repo (added 2026-09-09). In the shared engine rather than the
    # consumer half because a source set is itself a repo somebody works in:
    # a session rooted in precedent-team-writing needs the person's
    # individual set exactly as much as a consumer does, and had the same
    # silent absence. precedent_source_bootstrap.py imports it by name and
    # says so out loud when it is missing, so a tree vendored before this
    # date degrades visibly rather than ignoring a token that is set.
    'precedent_source_credentials.py',
    # The other half of that same mechanism: the clone-or-pull that actually
    # WRITES ~/.config/precedent/config.json, which is the only thing that
    # makes an individual source resolve at all. Promoted out of the consumer
    # half on 2026-09-13, and the sentence above -- "a session rooted in
    # precedent-team-writing needs the person's individual set exactly as
    # much as a consumer does" -- is the whole argument; the credential
    # helper travelled on it and this file did not.
    #
    # THE INCIDENT. A session rooted in any of the four real practice sets
    # (precedent-individual, precedent-team-writing,
    # precedent-team-repo-maintenance, precedent-team-working-style) resolved
    # NO individual source, every session, because nothing there ever wrote
    # that config. The canonical remedy already existed and could not be
    # installed: templates/harness/claude-code/hooks/
    # individual-source-bootstrap.sh.template execs this file, and a set was
    # not allowed to have it. Hand-copying it in is correctly refused --
    # `precedent_vendor_engine.py status` reports UNTRACKED ENGINE FILE for a
    # known name the manifest does not record -- so the hook a set needed
    # called a tool a set could not hold, and the gap could only be closed
    # here. Measured in a live container: running the hook by hand, with the
    # token set, cloned the set and wrote the config with no add_repo and no
    # manual step, after which precedent_source_credentials.py went from SET
    # to OK. The mechanism was sound; only its distribution was wrong.
    'precedent_source_bootstrap.py',
    # precedent_check.py imports it at module scope, so a vendored engine
    # without it does not degrade -- it raises ModuleNotFoundError and takes
    # the whole check run down. Found 2026-09-09 by verify_harness the moment
    # the import landed: thirteen fixtures that build a scratch engine tree
    # from this list failed at once. Every repo that stamps a date needs it
    # anyway (practice: timestamps-carry-offset); it has no dependencies of
    # its own beyond the standard library.
    'precedent_time.py',
    # WHO this repo's commits belong to, resolved the way commit-identity.sh
    # already resolves it. In ENGINE_FILES rather than CONSUMER-only,
    # unlike precedent_resolve.py which it was carved out of: a practice
    # SET is the repository that most certainly HAS an identity -- a root
    # identity.json is what declares one -- so a set that could not import
    # this had its own commit-author and buenos-aires-dates checks degrade
    # from enforcing to SKIPPED (2026-09-10, reported by the set that
    # adopted the helper). Identity is about a person; the resolver is
    # about a catalogue, and only the second reason keeps a file out of a
    # set.
    'precedent_identity.py',
    # The resolver and the untracked-block writer, added 2026-09-13 so a
    # session rooted in a practice SET reads the universal catalogue instead
    # of that set's own practices alone. Until then a set resolved nothing:
    # its generated occasion index carried its own entries and not one of
    # universal's 94, so a session there worked with the universal rules
    # silently absent -- measured, and the incident is in
    # practices/seeded-prompt-names-its-origin.md's Story.
    #
    # THE DOCSTRING ABOVE SAYS THESE ARE NEVER IN ENGINE_FILES, on the
    # reasoning that "a source set has no process/upstream/ and nothing to
    # resolve against more than one tree". The first half is still true --
    # precedent_materialize.py and precedent_sync_views.py stay consumer-only,
    # because a set materializes nothing. The second half was the mistake: a
    # set has exactly one other tree to resolve against, universal's, and
    # resolving it is how the rules reach the session. Costed in
    # spec/SOURCE_SET_PROSE_GAP.md, approved 2026-09-13 as shape 3.
    #
    # These two are a pair: precedent_session_practices.py imports the
    # resolver at module scope, so a set with one and not the other raises
    # ModuleNotFoundError from its own session-start hook.
    'precedent_resolve.py',
    'precedent_session_practices.py',
    # Whether this session can actually PUSH to each repo in force, probed at
    # session start (added 2026-09-14). In ENGINE_FILES rather than
    # consumer-only because the question is sharpest exactly where a practice
    # SET is attached: a set is normally another owner's repository, which is
    # the wall that produced the incident in this file's own docstring -- a
    # session that built a seven-commit patch it could not push and sat
    # blocked on it for four days.
    #
    # It imports precedent_resolve (above, and in both lists) to enumerate the
    # sources, and precedent_source_credentials (also in both) to authenticate
    # the probe; both degrade to a narrower answer rather than raising, so a
    # tree older than either still starts. It deliberately does NOT import
    # very_deep_check, which is in neither list -- the probe was moved out of
    # that file into this one precisely so it would travel.
    'precedent_access_check.py',
    # The command vocabulary, read off the `command:` field of every
    # practice a repo resolves (added 2026-09-13 with practices/vocabulary.md).
    # In ENGINE_FILES rather than the consumer half for the same reason
    # precedent_show.py is: the phrases are answered from wherever the
    # session is rooted, and a session working in a practice SET is exactly
    # where somebody types "Vocabulary" at a catalogue. It degrades by
    # design without precedent_resolve.py -- which a source set does not get
    # -- reading that repo's own practices/ and saying so.
    'precedent_vocabulary.py',
    # The reply gate's BLOCKING half. Left out when it landed 2026-09-13,
    # which had two costs the same day: the stop-hook check never reached a
    # consuming repo at all (its hook guards on the file existing, so it
    # skipped silently), and precedent_gate.py -- which DOES travel -- began
    # importing it hours later to print the declared requirements before the
    # reply. A vendored repo then printed "could not be read (No module
    # named 'precedent_reply_check')" on every single turn. Reproduced in a
    # stripped vendor tree before this line was added.
    'precedent_reply_check.py',
    # The one predicate in that file that looks at the DISK rather than at
    # the reply (2026-09-22): does this container hold work that exists
    # nowhere else? It travels for the same reason the reply check itself
    # does -- `require_container_safe_if_says` is declared in a source's
    # reply_check.json, read live, and evaluated by the VENDORED engine, so
    # a consumer without this file would silently evaluate the archive rule
    # to "nothing to report" in exactly the containers most likely to be
    # holding somebody's unpushed clone. It is useful on its own, too: a
    # person or a session can run it at any time and get a straight answer.
    'precedent_container_safe.py',
    # The stop hook's other half: close detection (2026-09-14). Same argument
    # as the line above it, and caught the same way -- Morgan asked whether
    # updating the vendored engine would carry this to a repo that has it,
    # and the honest answer was no, because nobody had added it here. The
    # hook guards on the file existing, so a consuming repo would have gone
    # on skipping it silently and forever.
    #
    # What travels is the MECHANISM only. A source's close_detect.json is
    # authored at that source's root and is never vendored, exactly like
    # reply_check.json: it declares one person's or one team's closing
    # convention, and an engine that shipped somebody's phrases would bind
    # every adopter to them (practice: rule-level-by-reach). So a vendored
    # repo receives a detector that detects nothing until a source declares
    # what it should fire on -- which is the honest default, not a gap.
    'precedent_close_detect.py',
    # The generator and the one-time converter for the 2026-09-16 todo/gotcha
    # migration's per-item TODO.md format (spec/OPEN_ITEM_AND_GOTCHA_PLAN.md
    # Part 1 and Part 4.2). Both were CONSUMER-only until 2026-09-19, on the
    # reasoning that "a source set has no TODO.md of its own to convert" --
    # wrong: confirmed the same day that precedent-individual and
    # precedent-team-writing (both `kind: source`) carry real, long-lived
    # TODO.mds of their own (520 and 112 lines) and were structurally unable
    # to run the migration, exactly like todo-migrate-available-but-unused's
    # own Story. A practice set is a repository somebody works in like any
    # other and accumulates its own open items the same way a consumer does.
    'build_todo_index.py',
    'todo_migrate.py',
    # title_case.py was CONSUMER-only until 2026-09-19, since headline
    # capitalization was thought of as a consumer-catalogue concern. Moved
    # here the same day build_todo_index.py was: it imports title_case at
    # module level, and vendored-import-refs-resolve caught the resulting
    # gap directly -- a source set receiving build_todo_index.py without
    # this would crash importing it with ModuleNotFoundError on its first
    # real run, the same failure shape precedent_check.py's own promotion
    # (see below) was caught by.
    'title_case.py',
    # The one way a generator copies prose into a summary field: links out,
    # then the cut (added 2026-09-25). build_todo_index.py, todo_migrate.py,
    # build_views.py and build_gotcha_index.py all import it at module level,
    # so it rides here for the same reason title_case.py does just above.
    'summary_text.py',
    # THE SCRIPT leak-gate.yml.template RUNS (added 2026-09-21, practice:
    # cite-the-incident). CI_WORKFLOW_TEMPLATES has listed
    # leak-gate.yml.template for BOTH kinds since 2026-09-20 (item 12), and
    # that workflow's only substantive step is
    # `python3 tools/leak_gate.py --structural-only`. Neither of these two
    # names was in either engine list, and no step in the workflow fetches
    # them -- so the workflow shipped WITHOUT the thing it runs. Any repo
    # installing it got a guaranteed red check and a billed minute per
    # trigger, on the public repos it was meant to protect.
    #
    # Caught 2026-09-21 by a session told to install it: it read
    # ENGINE_FILES and CONSUMER_ENGINE_FILES, found neither name, refused to
    # install on a broken premise, and refused equally to hand-copy the
    # script -- a copy outside ENGINE_MANIFEST.json being exactly what this
    # mechanism exists to prevent. Both refusals were right.
    #
    # The blocklist travels with the script: leak_gate.py resolves
    # DEFAULT_BLOCKLIST relative to its own __file__, so a vendored copy
    # without it cannot run. The INDIVIDUAL half (leak-blocklist.txt in a
    # person's own source) is resolved at runtime and is deliberately not
    # vendored.
    'leak_gate.py',
    'leak-blocklist.default.txt',
    # THE DEEP CHECK, AND THE MEANS TO AUTHOR A PRACTICE SET (2026-09-21).
    # very_deep_check.py shipped to nobody until now -- it existed only in
    # the engine's own repo, which is why running it could never find a
    # stale or drifted vendored tree: there was no copy in the repo that had
    # one. A repo carrying its own practices, its own situation and its own
    # drift is exactly where a deep read pays, and it is now the ONE place
    # a check can compare a vendored tree against what it was supposed to
    # be.
    #
    # parse_check.py and precedent_bootstrap_source.py come with it because
    # very_deep_check imports both at MODULE level -- without them the
    # vendored copy raises ImportError on its first line, which is a worse
    # failure than not shipping it. (checkin.py is imported too, inside a
    # function and already guarded; it reaches a consumer through the
    # vendored process/upstream/ tree rather than through this list.)
    #
    # precedent_bootstrap_source.py CREATES a practice set, and shipping it
    # everywhere is deliberate rather than tolerated. Morgan, 2026-09-21,
    # on being told it was a cost of vendoring the deep check: "it is GREAT
    # that the user can create a practice set. WE WANT THEM TO. WE WANT TO
    # ENCOURAGE THEM TO." A person who has been writing rules into one
    # repo's instructions file and wants to reuse them across their repos,
    # or share them with a team, should find the tool already in their
    # hands -- not discover that authoring a set is something only the
    # upstream repo can do. See documentation/FOR_DEVELOPERS.md and
    # templates/GETTING_STARTED.md, which now say so.
    'very_deep_check.py',
    'parse_check.py',
    'precedent_bootstrap_source.py',
    # THE ONE CHECK THAT LOOKS OUTWARD (2026-09-21). Every other check in
    # this system runs inside one repository and compares it against
    # itself. This one reads THIS manifest's source_commit against the live
    # upstream branch and says whether the vendored engine has fallen
    # behind -- the question nothing could answer before, which is why a
    # fix merged upstream reached an installed repo only when somebody
    # remembered to run "Update Vendors" there. Measured 2026-09-20: 18 of
    # 22 repositories had never taken one.
    #
    # It prints and never refreshes. Wired into the session-start hook and
    # precedent_gate.py's push/merge moments precisely because a reminder
    # is what already failed.
    'precedent_engine_freshness.py',
    # EVERY VOCABULARY WORD HAS TO WORK WHERE THE ENGINE IS VENDORED
    # (2026-09-21, Morgan: "ALL of our vocabulary words should"). A standing
    # command a session cannot carry out is worse than one that does not
    # exist: the person says it, the session recognises it -- the practice
    # is right there in the loader block -- and then reaches for a tool that
    # was never shipped. These three are what the audit found missing:
    # "Practice check" needs full_practice_audit.py, "Reduction pass" needs
    # session_load_trend.py, "Three Things" needs todo_progress.py.
    # precedent_check.py's `vocabulary-reaches-the-consumer` now fails the
    # build if a command practice names a tool that is not here.
    # THE LIGHT CHECK HAS TO EXIST WHERE THE COMMIT GATE RUNS (2026-09-21).
    # These two were CONSUMER-ONLY, on the reasoning that a consumer's
    # enforced checks import doc_lint and a practice set's do not. That was
    # true and it stopped being sufficient the moment the Markdown lint left
    # GitHub Actions and .claude/hooks/doc-lint-gate.sh became the only
    # thing checking Markdown before a shared branch.
    #
    # A practice set got the hook and not the tool. The hook's own
    # `[[ -f "$script" ]] || exit 0` then fired on every commit -- failing
    # open exactly as designed, and gating nothing at all. All four sets had
    # neither the CI check nor its replacement, and nothing said so.
    #
    # Found by a session auditing the four sets after the update, not by
    # anything here: `wired-hooks-can-reach-a-consumer` asks whether the
    # HOOK can travel and never asked whether what it RUNS can.
    # `shipped-hook-carries-its-script` now does.
    #
    # frontmatter_yaml.py rides along because doc_lint.py imports it
    # unconditionally at module level -- without it doc_lint does not fail a
    # check, it fails to import.
    'doc_lint.py',
    'frontmatter_yaml.py',
    'full_practice_audit.py',
    'session_load_trend.py',
    'todo_progress.py',
    # The SessionStart self-heal: "did this repo's own hooks actually run,
    # and repair it by hand if not" (added 2026-09-08, in BestPractice only
    # until 2026-09-24). Never vendored, so no source set had it -- and a
    # source set is exactly where the failure this tool exists for bites,
    # since a team source resolving as a sibling clone is what roots a
    # session one directory ABOVE every repo's hooks in the first place
    # (this file's own docstring). In ENGINE_FILES rather than consumer-only
    # for the same reason precedent_vocabulary.py is: the guarantee it
    # checks -- and the additionalContext-emitting hook this file's own
    # apply_repair() was found, the same day, to be silently skipping
    # because its hook list was hardcoded rather than read from
    # settings.json -- belongs to whatever repo the session is rooted in,
    # source set or consumer alike.
    'precedent_session_check.py',
    # Everything CI used to run on a push, run locally instead (added
    # 2026-09-25). A practice source runs no CI at all and a private
    # consumer may run none, so this list is the only check their pushes
    # get; push-check-gate.sh runs it before a session's `git push`. Every
    # kind needs it, and it reads its own kind back from ENGINE_MANIFEST.json.
    'precedent_push_check.py',
    # The three branch tiers (spec/BRANCH_TIERS_PLAN.md, 2026-09-25): which
    # branch is pre-staging, staging and main in this repository, and which
    # tier of the push check a push to each one gets. precedent_push_check.py
    # asks it whenever the push gate names the push; every kind pushes.
    'precedent_branches.py',
    # The merge gate's engine: the push check, run on the merge GitHub would
    # make, before a session merges a pull request through GitHub -- a push
    # no local hook sees. merge-check-gate.sh calls it; every kind merges.
    'precedent_merge_check.py',
    # A practice source's check tests, run the way a consuming repository
    # runs them (added 2026-09-25): precedent_push_check.py runs it in a
    # source's full tier, so a test that only passes in its home layout
    # fails there rather than in every consumer. Shared rather than
    # source-only because a consumer's push check names nothing it needs,
    # and a person in a consumer can still run it by hand on a source clone.
    'precedent_consumer_shape.py',
    'precedent_vendor_engine.py',
]

# A consumer needs everything a source set does, PLUS the three multi-source
# tools that only make sense once more than one tree is being resolved
# together -- see the docstring's "'consumer' closes" section. Built by
# extending ENGINE_FILES rather than listing all nine names flat, so a
# future addition to the shared engine (a new file every kind needs) only
# has to be added in one place.
CONSUMER_ENGINE_FILES = ENGINE_FILES[:-1] + [
    # precedent_resolve.py and precedent_session_practices.py were listed
    # here until 2026-09-13 and are now in ENGINE_FILES, so a practice set
    # gets them too -- see their entry there. Repeating them here is refused
    # by the duplicate guard below, which is how this was caught.
    'precedent_materialize.py',
    'precedent_sync_views.py',
    # Whether each declared source repository is still CALLED what this repo
    # calls it (added 2026-09-11). CONSUMER-only for the same reason
    # precedent_resolve.py is -- it reads a multi-source config, which a
    # practice SET does not have -- and it is named by
    # vendor-update-runbook's own Rule, so a consumer resolving that
    # practice and lacking the file has a step it cannot run.
    'precedent_source_names.py',
    # Named by a universal practice's own Install, so a consumer that
    # resolves that practice needs the file (added 2026-09-06, after
    # installing into a scratch repo exactly as INSTALL.md section 0
    # describes and running precedent_check.py on the result):
    #
    #   doc_lint.py      -- four enforced checks import it
    #                       (acronyms-glossary, deliverables-look-like-output,
    #                       doc-references-are-links, search-by-purpose).
    #                       Without it all four reported "did not import: No
    #                       module named 'doc_lint'" -- SKIPPED, which is
    #                       honest, and useless. It is also the light check
    #                       AGENTS.md tells every session to run before every
    #                       commit.
    #   doc_sync.py      -- two more (computed-numbers-in-scripts,
    #                       docs-track-models). Its PAIRS list is empty until
    #                       a repo fills it in, so it reports NOT APPLICABLE
    #                       there rather than failing.
    #   routing_audit.py -- routing-audit's Install names it as the practice's
    #                       implementation, so the check flagged its absence
    #                       as a violation in every consuming repo. It needs
    #                       only split_practices and precedent_paths, both
    #                       already here.
    # doc_lint.py and frontmatter_yaml.py MOVED TO ENGINE_FILES on
    # 2026-09-21 -- see their entry there. Repeating them here is refused by
    # the duplicate guard below, which is how a stray re-add gets caught.
    'doc_sync.py',
    'routing_audit.py',
    # Move tracked files or directories and repoint every reference in the
    # same change (rename-updates-links made mechanical; added 2026-09-17
    # from a consumer's repository reshape -- 366 files, 2,900 references,
    # four tranches). A consumer's own tools are what reshape its tree, so
    # the tool lives in the consumer half; a practice set moves nothing.
    'move_paths.py',
    # title_case.py was listed here until 2026-09-19 and is now in
    # ENGINE_FILES -- build_todo_index.py imports it at module level and
    # moved into the shared list the same day, so a source set that got one
    # without the other would crash on its first real run. See the entry
    # there. Repeating it here is refused by the duplicate guard below.
    #
    # The gotcha-catalogue generator for the 2026-09-16 todo/gotcha migration's
    # per-item format (spec/OPEN_ITEM_AND_GOTCHA_PLAN.md Part 2). Missing from
    # this list since the migration -- found 2026-09-16 when a consumer taking
    # the vendor update went looking for build_gotcha_index.py to do its own
    # gotcha-catalogue split and it simply was not there, no error, no
    # SKIPPED, nothing named it as missing. CONSUMER-only: a source set
    # materializes no catalogue of its own gotchas/*.md items, so it has
    # nothing for this generator to read.
    #
    # build_todo_index.py and todo_migrate.py were listed here alongside it
    # until 2026-09-19 and are now in ENGINE_FILES -- a source set turned out
    # to have its own TODO.md after all (see the entry there). Repeating them
    # here is refused by the duplicate guard below, which is how a stray
    # re-listing would be caught.
    'build_gotcha_index.py',
    # precedent_source_bootstrap.py is NOT re-listed here, for the same
    # reason precedent_check.py is not (see the note below): it was
    # consumer-only when this list was written -- the individual-source
    # SessionStart hook this repo ships as a template execs it, and in a
    # consuming repo the hook exec'd a path that did not exist -- and on
    # 2026-09-13 it was promoted into ENGINE_FILES, which this list already
    # inherits. Naming it in both halves would write it twice and record it
    # twice in every consumer's tracked manifest; the duplicate assertion
    # below now refuses that at import time rather than shipping it.
    # The REPLACEMENT channel for what a public repo's tracked files may not
    # carry. build_views.py excludes team- and individual-level sources from
    # a public repo's block and precedent_sync_views.py now keeps their text
    # out of its materialized tree -- and this is the tool that renders them
    # into .precedent/SESSION_PRACTICES.md instead, untracked, per session.
    # It was never vendored, so a consumer got the exclusion with no
    # replacement and those practices simply stopped binding there. Found
    # 2026-09-07 repairing a real public consumer's install: half a
    # mechanism shipped, and the missing half was the half that keeps the
    # rules in force.
    #
    # Promoted into ENGINE_FILES on 2026-09-13 -- a practice set needs the
    # same tool for the mirror-image reason -- so it is no longer re-listed
    # here. Same shape as precedent_check.py's note below, and the duplicate
    # guard is what caught both.
    # precedent_check.py is NOT re-listed here. It was consumer-only when
    # this list was written, and was later promoted into ENGINE_FILES
    # (a source set runs the enforced channel too) without being removed
    # from here -- so it arrived in this list twice, was written twice, and
    # landed twice in every consumer's tracked ENGINE_MANIFEST.json while
    # the seed reported one more file than it had. Harmless to the tree,
    # wrong in a tracked artifact, and invisible because writing a file
    # twice looks exactly like writing it once.
    'precedent_vendor_engine.py',  # last, same reason as ENGINE_FILES above
]

# A name in both halves would be written twice and recorded twice in the
# manifest -- see the note above, which is the incident this guards. Cheap,
# and at import time so no caller can miss it.
for _lst, _nm in ((ENGINE_FILES, 'ENGINE_FILES'),
                  (CONSUMER_ENGINE_FILES, 'CONSUMER_ENGINE_FILES')):
    _dupes = sorted({f for f in _lst if _lst.count(f) > 1})
    if _dupes:
        raise AssertionError(
            f'{_nm} lists {", ".join(_dupes)} more than once: the engine '
            f'would be written and recorded twice')

KINDS = {'source': ENGINE_FILES, 'consumer': CONSUMER_ENGINE_FILES}
DEFAULT_KIND = 'source'  # unchanged default -- see seed()'s docstring note
MANIFEST_NAME = 'ENGINE_MANIFEST.json'

# Engine files this tool once shipped and no longer does. A NAME, once
# vendored anywhere, never becomes safe to forget: the copy sitting in an
# adopter's tools/ outlives every list that could still name it.
#
# WHY A TOMBSTONE AND NOT A DERIVED SET. Both live mechanisms are keyed on
# the CURRENT lists -- _untracked_engine_files asks "known name, not in this
# manifest", and _remove_dropped_engine_files asks "in this manifest, not in
# this kind". A file renamed AWAY upstream is in neither: it is gone from
# KINDS, and a pre-2026-09-08 `seed` wrote a manifest that had already
# forgotten it while leaving it on disk. So it was invisible to every
# mechanism at once, which is how three real practice sets each sat on a
# dead `precedent_retire_path.py` with `status` reporting them healthy.
#
# Adding a name here is the cost of renaming an engine file, and it is the
# whole cost: KINDS says what an install should have, this says what it must
# no longer have.
RETIRED_ENGINE_FILES = {
    'precedent_retire_path.py':
        'renamed to precedent_decommission.py, 2026-09-07 '
        '(the mechanism sense of "retire" became "decommission")',
}
_SECOND_PASS_ENV = 'PRECEDENT_VENDOR_ENGINE_SECOND_PASS'

# --- Hook files: the .claude/hooks/*.sh adapter scripts --------------------
# Distinct from ENGINE_FILES above in two ways: they live in a different
# source directory (templates/harness/claude-code/hooks/, not tools/) and a
# different destination (.claude/hooks/, not tools/). Until now they were
# installed once by precedent_install.py's _harness() and never refreshed --
# "Update Vendors" refreshed tools/ and the catalogue and silently left the
# hook scripts wherever initial install had put them. That is the same gap
# ENGINE_FILES closed for tools/precedent_reply_check.py and
# tools/precedent_close_detect.py (see this file's docstring above): a fix
# that lands upstream and never reaches an already-vendored repo because
# nothing carries it there. The freshness-guard.sh shallow-clone false-
# positive (record/GOTCHAS.md#g12) is the concrete incident this closes --
# every consumer that vendored before that fix landed would otherwise keep
# hitting it, forever, no matter how many times it ran "Update Vendors".
#
# Deliberately NOT folded into ENGINE_FILES/KINDS: that machinery assumes one
# shared source dir and one shared dest dir (both `tools/`). Reusing it here
# would mean smuggling a relative `../` path into a manifest key to reach
# outside tools/ -- workable, but a trap for the next reader who assumes
# every name in `files` resolves inside tools/. A second, smaller, explicitly
# separate mechanism is the honest shape, tracked in the SAME
# ENGINE_MANIFEST.json under its own `hook_files`/`hooks_sha256` keys so
# there is still one provenance record per repo, not two.
#
# HOW A HOOK LEAVES A CONSUMER (corrected 2026-09-24; this passage used to
# say no removal existed, which stopped being true on 2026-09-21). A hook
# the previous manifest recorded and upstream no longer ships, or one named
# in RETIRED_HOOK_FILES, is deleted by _remove_dropped_hook_files when its
# hash still matches. An UNTRACKED copy of a RETIRED_HOOK_FILES name --
# vendored before `hook_files` existed -- is deleted by
# retire_legacy_leftovers when its content matches the recogniser and
# nothing in .claude/settings.json still calls it. A hook upstream never
# shipped at all is the repo's own and nothing here touches it.
#
# .claude/settings.json is never OVERWRITTEN here.
# precedent_install.py's _harness() already leaves it alone once it exists,
# on purpose -- a consumer may have wired its own extra hooks alongside the
# vendored ones -- and a routine refresh has no business replacing a repo's
# own hook wiring. What a refresh DOES do, since 2026-09-25, is ADD the
# entry for a hook HOOK_WIRING says this repo's kind gets and that the repo
# neither wires nor declined -- see HOOK_WIRING below. It adds; it never
# edits or removes an entry that is already there.
HOOK_SOURCE_DIR = 'templates/harness/claude-code/hooks'
HOOK_DEST_DIR = '.claude/hooks'

# WHICH HOOKS EACH KIND OF REPO GETS -- declared, never inferred from what a
# repo happens to wire already (Morgan, 2026-09-25, strength: decided: "I
# like the lists of 'repos that [are of this type] get [these hooks]' --
# approved"). Keyed by KIND, never by repository: a repo nobody has ever
# heard of gets its kind's list, exactly like a repo on every list we keep.
#
# THE BUG THIS CLOSES (todo-2026-09-21-a-new-hook-cannot-reach-an-installed-
# consumer.md). Vendoring used to be gated on the repo's own settings.json
# alone, and a refresh never wrote that file -- so a hook added upstream
# could not reach a repo that was already installed. It was not vendored
# until it was wired, and wiring it meant naming a file that was not there
# yet. The engine read "not wired" as "declined", when for a new hook it
# only ever means "not yet". doc-lint-gate.sh made that a correctness bug:
# Markdown lint left CI on 2026-09-21 because the hook replaced it, so a
# repo that took the update and never got the hook lost lint entirely.
#
# HOW IT IS APPLIED (_hook_wiring_plan, _apply_hook_wiring). For each entry
# here, on each refresh: if the repo already runs that hook at that event
# (from ANY path -- a set that calls a script in place from its own
# bootstrap/ is already wired), or declared it in precedent.json's
# `declined_adapters`, nothing happens. Otherwise the entry is ADDED to
# .claude/settings.json, and the ordinary vendoring below -- still gated on
# wiring -- then delivers the file on the same run. Adding the entry first
# is what keeps the gate's own guarantee: no file is ever planted that
# nothing calls (hooks-on-disk-are-reachable).
#
# The two reasons the wiring gate existed both still hold, and this list is
# how each is kept rather than broken:
#   1. a source set and a consumer run different subsets of the one shared
#      hooks/ directory -- so each kind has its own list;
#   2. a repo that declined a hook stays declined -- by declaring it in
#      `declined_adapters` with a reason, never by leaving it unwired and
#      hoping the engine guesses.
#
# Each entry: (event, matcher or None, hook file, arguments). `{base}` in
# the arguments is the repo's base branch, read off the freshness-guard
# entries it already has; where there are none the entry is reported and
# left for a person, never guessed. A manifest with no `kind` (vendored
# before kinds existed) gets NO list applied: guessing a kind is how a
# consumer would receive a set's hooks.
#
# ADDING A HOOK (practice: new-hook-joins-the-registry). A new *.sh in
# HOOK_SOURCE_DIR goes on a kind's list here AND into that kind's template
# -- templates/harness/claude-code/settings.json for a consumer,
# precedent_bootstrap_source.py's settings payload for a set -- or into
# HOOKS_NO_KIND with the reason no kind gets it. precedent_check.py's
# `new-hook-joins-the-registry` refuses a tree where any of those disagree.
_SEEDED_PROMPT_MATCHER = ('mcp__.*__(create_session|create_trigger|'
                          'update_trigger|fire_trigger|send_later)')
# The merge gate fires on the GitHub MCP server's merge tool and on Bash,
# where it looks for `gh pr merge` and exits at once on anything else.
MERGE_GATE_MATCHER = 'Bash|mcp__.*__merge_pull_request'
HOOK_WIRING = {
    'consumer': (
        ('SessionStart', None, 'session-start.sh', ''),
        ('SessionStart', None, 'freshness-guard.sh', 'session-start {base}'),
        ('SessionStart', None, 'commit-identity.sh', ''),
        ('UserPromptSubmit', None, 'reply-gate.sh', ''),
        ('UserPromptSubmit', None, 'freshness-guard.sh', 'user-prompt {base}'),
        ('PreToolUse', 'Edit|Write|NotebookEdit', 'precedent-paths.sh', ''),
        ('PreToolUse', 'Edit|Write|NotebookEdit|Bash', 'freshness-guard.sh',
         'pre-write {base}'),
        # Added to the consumer list by the 2026-09-25 sweep: shipped and
        # wired in this repo since 2026-09-22, and never in the consumer
        # template, so no consumer ever received it. Its reason applies to
        # a consumer unchanged -- a session rooted one directory above the
        # repo runs none of its SessionStart hooks (gotcha-2026-09-13), and
        # this is the only other moment commit-identity.sh gets to run.
        ('PreToolUse', 'Edit|Write|NotebookEdit|Bash', 'commit-identity-once.sh', ''),
        ('PreToolUse', 'Bash', 'doc-lint-gate.sh', ''),
        ('PreToolUse', _SEEDED_PROMPT_MATCHER, 'seeded-prompt-gate.sh', ''),
        # Everything CI used to run on a push, run before it (2026-09-25).
        ('PreToolUse', 'Bash', 'push-check-gate.sh', ''),
        # The same check before a merge through GitHub, which no push gate
        # sees (spec/BRANCH_TIERS_PLAN.md, hole 1).
        ('PreToolUse', MERGE_GATE_MATCHER, 'merge-check-gate.sh', ''),
        ('Stop', None, 'stop-git-check.sh', ''),
        ('Stop', None, 'stop-reply-check.sh', ''),
    ),
    # precedent-individual-bootstrap.sh is not here: it is rendered from a
    # .template by precedent_bootstrap_source.py, not shipped as a *.sh this
    # engine copies, and every set is created with it wired.
    'source': (
        ('SessionStart', None, 'precedent-universal-catalogue.sh', ''),
        ('SessionStart', None, 'freshness-guard.sh', 'session-start {base}'),
        ('SessionStart', None, 'commit-identity.sh', ''),
        ('UserPromptSubmit', None, 'freshness-guard.sh', 'user-prompt {base}'),
        ('PreToolUse', 'Edit|Write|NotebookEdit|Bash', 'freshness-guard.sh',
         'pre-write {base}'),
        ('PreToolUse', 'Bash', 'doc-lint-gate.sh', ''),
        # Added to the set list by the 2026-09-25 sweep. The practice it
        # enforces (seeded-prompt-names-its-origin) is universal, a session
        # in a set can spawn sessions like any other, and the hook needs
        # nothing but bash and jq -- no engine file a set lacks.
        ('PreToolUse', _SEEDED_PROMPT_MATCHER, 'seeded-prompt-gate.sh', ''),
        # A set runs no CI at all (source-sets-run-no-ci), so this is the
        # only thing that runs its checks before a push (2026-09-25).
        ('PreToolUse', 'Bash', 'push-check-gate.sh', ''),
        ('PreToolUse', MERGE_GATE_MATCHER, 'merge-check-gate.sh', ''),
    ),
}
# A hook that needs more than the harness's default time gets its own
# `timeout` (seconds) on the entry a refresh adds. push-check-gate.sh can run
# BestPractice's whole harness, about six minutes, and enforces its own
# 840-second deadline inside this one, so an expiry refuses the push instead
# of the harness killing the hook -- which it treats as a non-blocking error,
# letting the push through unchecked.
HOOK_TIMEOUTS = {'push-check-gate.sh': 900, 'merge-check-gate.sh': 900}
# Shipped in HOOK_SOURCE_DIR and on NO kind's list, each with the reason. A
# repo that wires one itself still has it vendored and kept current -- the
# wiring gate below still applies -- but no refresh adds it anywhere.
HOOKS_NO_KIND = {
    'commit-identity-push-gate.sh':
        'runs tools/checks/check_commit_author.py and '
        'check_buenos_aires_dates.py, which are a repo\'s own and never '
        'vendored -- in a repo without them the hook is a silent no-op, so '
        'only a repo that carries them wires it',
}


def _hook_file_names(hooks_dir):
    """Every real (non-template) hook script BestPractice SHIPS at this
    source directory -- not what any one repo wants. `.template` files (e.g.
    individual-source-bootstrap.sh.template) are a different mechanism
    (rendered per-source, not copied verbatim) and are excluded by the glob.

    Callers vendoring INTO a repo must intersect this with
    _wired_hook_names(dest_root) -- see that function's docstring for why:
    the shared hooks/ directory holds scripts that only a practice SET wires
    (precedent-universal-catalogue.sh) alongside ones only a CONSUMER wires,
    and vendoring the full glob into every repo regardless of kind is
    exactly how hooks-on-disk-are-reachable's own incident happened."""
    if not hooks_dir.is_dir():
        return []
    return sorted(p.name for p in hooks_dir.glob('*.sh'))


_HOOK_CMD_RE = re.compile(r'hooks/([\w.-]+\.sh)')
# Any hook script a command names, wherever it lives. Used ONLY to describe
# what a repo already wires, never to decide what to vendor -- see
# _wired_hook_names_anywhere.
_HOOK_CMD_ANY_RE = re.compile(r'([\w.-]+\.sh)')


def _wired_hook_names(dest_root):
    """Hook script basenames `dest_root`'s OWN .claude/settings.json
    actually wires -- the same regex precedent_install.py's _harness() uses
    to decide what to copy at initial install.

    THE BUG THIS CLOSES. A first version of hook-vendoring vendored every
    `*.sh` HOOK_SOURCE_DIR contains, unconditionally. That is wrong for two
    reasons at once: a source practice set and a consumer repo wire
    different subsets of the same shared hooks/ directory (only a set wires
    precedent-universal-catalogue.sh, only a consumer's settings.json wires
    the rest), and a repo that deliberately declined an adapter (see
    tools/precedent_check.py's hooks-on-disk-are-reachable and its
    `declined_adapters` mechanism) must stay declined -- a routine refresh
    re-planting a hook nobody wired is exactly the orphan that check exists
    to catch. Caught here, before ever shipping, by running verify_harness.py
    before push: `tools/precedent_install.py yields a project whose own
    gates come back clean` failed with exactly that VIOLATION the moment
    this vendored precedent-universal-catalogue.sh into a plain consumer
    install. Scoping to what settings.json already wires makes this
    impossible by construction -- there is no name to vendor that the repo
    did not already choose to wire.

    Returns an empty set, never an error, when settings.json does not exist
    yet: INSTALL.md's own order writes it (precedent_install.py) before this
    tool ever runs, so an absence here means "nothing to reconcile yet", not
    "broken" (practice: fail-gracefully)."""
    return _settings_hook_names(dest_root, _HOOK_CMD_RE)


def _wired_hook_names_anywhere(dest_root):
    """Hook script basenames this repo wires from ANY path, not only from
    `.claude/hooks/`.

    REPORTING ONLY, and the separation from `_wired_hook_names` above is the
    whole point. That function decides what gets VENDORED, and it is right to
    look only under `.claude/hooks/` -- a repo that calls a script in place
    from somewhere else in its own tree does not want a second copy planted
    beside it. Widening the vendoring test would plant exactly that.

    What the narrow test cannot do is describe the repo truthfully, and the
    NOTE was using it for both jobs. Measured 2026-09-22 in
    `precedent-individual`, which authors these scripts and wires four of them
    straight out of its own tracked `bootstrap/` -- its settings.json says so
    in as many words: *"bootstrap/ IS a tracked directory of this repo, so
    every entry calls its script in place -- one file, no second copy to drift
    from it."* The refresh told it that `commit-identity.sh`,
    `freshness-guard.sh` and `precedent-universal-catalogue.sh` were "not
    wired in this repo's own .claude/settings.json". All three are wired, on
    consecutive lines of that file.

    That is worse than noise, because the NOTE beside it says to break the
    loop by hand -- copy the entry from upstream's settings.json, re-run, and
    the file arrives. Following that advice here would plant the second copy
    the repo deliberately does not keep, and the drift would look like a
    hand-edit months later. So the NOTE now names these separately and tells
    the reader there is nothing to do about them.
    """
    return _settings_hook_names(dest_root, _HOOK_CMD_ANY_RE)


def _settings_hook_names(dest_root, pattern):
    """The shared walk behind the two functions above, so a change to how
    settings.json is read cannot reach one and miss the other.

    Returns an empty set, never an error, when settings.json does not exist
    yet: INSTALL.md's own order writes it (precedent_install.py) before this
    tool ever runs, so an absence here means "nothing to reconcile yet", not
    "broken" (practice: fail-gracefully)."""
    settings_path = dest_root / '.claude' / 'settings.json'
    if not settings_path.is_file():
        return set()
    try:
        settings = json.loads(settings_path.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return set()
    names = set()
    for group in (settings.get('hooks') or {}).values():
        for entry in group:
            for h in entry.get('hooks', []):
                m = pattern.search(h.get('command', '') or '')
                if m:
                    names.add(m.group(1))
    return names



_BASE_BRANCH_RE = re.compile(
    r'freshness-guard\.sh\s+(?:session-start|user-prompt|pre-write)\s+(\S+)')


def _declined_hook_names(dest_root):
    """Basenames of the hooks this repo declares in precedent.json's
    `declined_adapters` -- the one way a repo says it does not want a hook
    its kind gets. A decline without a reason still counts here: the
    reason is precedent_check.py's business (hooks-on-disk-are-reachable
    reports it), and re-wiring a hook somebody said no to, because they
    forgot to say why, would be the worse error."""
    try:
        cfg = json.loads((pathlib.Path(dest_root) / 'precedent.json')
                         .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return set()
    return {pathlib.PurePosixPath(str(e['path'])).name
            for e in (cfg.get('declined_adapters') or [])
            if isinstance(e, dict) and e.get('path')}


def _hook_wiring_plan(dest_root, kind, hooks_src_dir):
    """-> (to_add, unresolved): HOOK_WIRING[kind] entries this repo does not
    run yet and should, and entries it should but that cannot be written
    without a guess.

    Pure: reads, never writes. refresh() asks it before deciding whether a
    run at an unchanged commit has anything to do, and _apply_hook_wiring
    asks it again at write time.

    An entry is ALREADY SATISFIED when any command at that event names the
    hook file from any path -- `.claude/hooks/`, a set's own `bootstrap/`,
    anything -- and carries the entry's mode word where it has one
    (freshness-guard.sh runs three times, once per mode). The matcher is
    deliberately not compared: a repo that runs doc-lint-gate.sh under a
    wider matcher of its own already runs it, and a second entry would run
    it twice.

    Nothing is planned for a hook upstream does not ship at this commit
    (an old ref), one the repo declined, one RETIRED_HOOK_FILES names, or
    a kind this module does not know -- the last is how a manifest with no
    `kind` stays untouched rather than guessed at."""
    entries = HOOK_WIRING.get(kind)
    if not entries:
        return [], []
    settings_path = pathlib.Path(dest_root) / '.claude' / 'settings.json'
    if not settings_path.is_file():
        return [], []
    try:
        settings = json.loads(settings_path.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return [], []
    shipped = set(_hook_file_names(hooks_src_dir)) - set(RETIRED_HOOK_FILES)
    declined = _declined_hook_names(dest_root)
    hooks = settings.get('hooks') if isinstance(settings, dict) else None
    hooks = hooks if isinstance(hooks, dict) else {}
    commands = {}
    for event, groups in hooks.items():
        for g in groups if isinstance(groups, list) else []:
            for h in (g.get('hooks') or []) if isinstance(g, dict) else []:
                commands.setdefault(event, []).append(
                    str((h or {}).get('command') or ''))
    base = None
    for cmd in (c for cs in commands.values() for c in cs):
        m = _BASE_BRANCH_RE.search(cmd)
        if m:
            base = m.group(1)
            break
    to_add, unresolved = [], []
    for event, matcher, name, args in entries:
        if name not in shipped or name in declined:
            continue
        mode = args.split()[0] if args else None
        if any(re.search(r'(^|[/\s])' + re.escape(name) + r'(\s|$)', c)
               and (mode is None or mode in c.split())
               for c in commands.get(event, [])):
            continue
        if '{base}' in args and base is None:
            unresolved.append((event, matcher, name, args))
            continue
        to_add.append((event, matcher, name,
                       args.replace('{base}', base or '')))
    return to_add, unresolved


def _apply_hook_wiring(dest_root, kind, hooks_src_dir):
    """ADD the settings.json entries _hook_wiring_plan names. -> [added]

    Add-only, and that is the whole safety argument: an entry already in
    the file is never edited, moved or removed, so a repo's own hooks,
    its own matchers and its own order all survive. A new entry joins the
    first group at its event with the same matcher (no matcher for
    SessionStart/UserPromptSubmit/Stop), or a new group at the end.

    Written by a tool, never by the session: the harness refuses a session
    hand-editing .claude/settings.json, and precedent_bootstrap_source.py's
    ensure_hook_wired already showed the refusal does not reach a vendored
    tool writing entries the engine defines. Said out loud on every run
    that adds something, with how to decline instead."""
    to_add, unresolved = _hook_wiring_plan(dest_root, kind, hooks_src_dir)
    for event, matcher, name, args in unresolved:
        print(f"NOTE: precedent_vendor_engine: {name} ({event}"
              f"{', ' + matcher if matcher else ''}) is on the {kind} hook "
              f"list and this repo does not run it, but its entry needs the "
              f"repo's base branch and no freshness-guard.sh entry here says "
              f"what that is -- not guessed. Wire it by hand from "
              f"templates/harness/claude-code/settings.json upstream, or "
              f"decline it in precedent.json's declined_adapters with the "
              f"reason.", file=sys.stderr)
    if not to_add:
        return []
    settings_path = pathlib.Path(dest_root) / '.claude' / 'settings.json'
    data = json.loads(settings_path.read_text(encoding='utf-8'),
                      object_pairs_hook=collections.OrderedDict)
    hooks = data.setdefault('hooks', collections.OrderedDict())
    added = []
    for event, matcher, name, args in to_add:
        cmd = f'$CLAUDE_PROJECT_DIR/{HOOK_DEST_DIR}/{name}' + (
            f' {args}' if args else '')
        entry = collections.OrderedDict([('type', 'command'), ('command', cmd)])
        if name in HOOK_TIMEOUTS:
            entry['timeout'] = HOOK_TIMEOUTS[name]
        groups = hooks.setdefault(event, [])
        home = next((g for g in groups if isinstance(g, dict)
                     and g.get('matcher') == matcher
                     and isinstance(g.get('hooks'), list)), None)
        if home is None:
            home = collections.OrderedDict()
            if matcher is not None:
                home['matcher'] = matcher
            home['hooks'] = []
            groups.append(home)
        home['hooks'].append(entry)
        added.append(f'{event}: {name}' + (f' {args}' if args else ''))
    settings_path.write_text(json.dumps(data, indent=2, ensure_ascii=False)
                             + '\n', encoding='utf-8')
    print(f"precedent_vendor_engine refresh: wired {len(added)} hook "
          f"entr{'y' if len(added) == 1 else 'ies'} this repo's kind "
          f"({kind}) gets and it did not run yet, into .claude/settings.json "
          f"-- added only, nothing already there was changed: "
          f"{'; '.join(added)}. To opt out of one, remove its entry and "
          f"declare it in precedent.json's declined_adapters with the "
          f"reason; a later refresh then leaves it alone.")
    return added

def dependents_of(dest_root, rels, cap=8):
    """-> {rel: [(referring path, line number, the line)]} for files that
    are about to stop existing, or just have.

    THE INCIDENT (2026-09-21,
    todo-2026-09-21-refresh-deletes-a-workflow-another-file-depends-on.md).
    A refresh deleted `.github/workflows/precedent-check.yml` from four
    practice sets. A second workflow in each of them had been PAUSED hours
    earlier, its own header saying in as many words that its checks "now run
    as steps in .github/workflows/precedent-check.yml's single job". The
    fold's destination was gone; the pause's premise was true when it was
    written and false the same afternoon; two commit-scope checks ran
    nowhere, and nothing said a word.

    precedent_decommission.py already refuses to retire a file other files
    still name -- WITHIN one repository, when a person runs it deliberately.
    Deletion travels through refresh() to every installed repo; the
    dependency question never travelled with it. This is that question,
    asked at the moment of deletion.

    IT REPORTS AND NEVER REFUSES. A document that mentions a retired file by
    name is usually correct to (a story about a decommissioning names what
    was decommissioned), so refusing a refresh over a mention would block
    routine updates on prose. What the refresh owes is that nobody finds out
    by reading a silent tree weeks later."""
    hits = {}
    if not rels:
        return hits
    dest_root = pathlib.Path(dest_root)
    try:
        listed = subprocess.run(['git', 'ls-files'], cwd=str(dest_root),
                                capture_output=True, text=True, timeout=60)
        files = [dest_root / x for x in listed.stdout.split()] \
            if listed.returncode == 0 else []
    except (OSError, subprocess.SubprocessError):
        files = []
    if not files:
        files = [x for x in dest_root.rglob('*')
                 if x.is_file() and '.git/' not in str(x)]
    # The manifest RECORDS what is vendored, so it names every one of these
    # by design; reporting it would be reporting the bookkeeping.
    skip = {MANIFEST_NAME}
    needles = {}
    for rel in rels:
        base = pathlib.PurePosixPath(rel).name
        needles[rel] = {rel, base} if base != rel else {rel}
    for f in files:
        if f.name in skip:
            continue
        try:
            rel_here = str(f.relative_to(dest_root))
        except ValueError:
            continue
        if rel_here in rels:
            continue                      # the file being deleted itself
        try:
            text = f.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue                      # binary, or unreadable: not prose
        for rel, terms in needles.items():
            if len(hits.get(rel, ())) >= cap:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if any(term in line for term in terms):
                    hits.setdefault(rel, []).append((rel_here, i,
                                                     line.strip()[:120]))
                    break
    return hits


def _warn_about_dependents(dest_root, rels, what):
    """Print one WARN per file that still names something just deleted."""
    found = dependents_of(dest_root, rels)
    for rel in sorted(found):
        for path, line, text in found[rel]:
            print(f"WARN: precedent_vendor_engine: {rel} was {what}, and "
                  f"{path}:{line} still names it -- {text!r}. Nothing here "
                  f"refuses over a mention; read it and decide, because a "
                  f"file whose own premise has just stopped being true "
                  f"reads exactly like one that is fine.", file=sys.stderr)
    return found


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _trim_routing_scope(engine_dir):
    """BestPractice's own tools/routing_scope.json, reduced to just the
    closed gate vocabulary — see docstring. Read from wherever THIS script
    physically sits (engine_dir), not from a fixed ROOT, so it works
    identically whether called during `seed` (engine_dir == BestPractice's
    own tools/) or, in principle, from a future clone-based path."""
    full = json.loads((engine_dir / 'routing_scope.json').read_text(encoding='utf-8'))
    return {
        '_note': [
            'Vendored from alex137/BestPractice (tools/routing_scope.json), trimmed to',
            'just the closed gate vocabulary tools/precedent_gate.py needs -- the',
            "source file's own `practices` key documents the routing reason for every",
            "one of BestPractice's OWN practices, which has no meaning here. The gate",
            'vocabulary itself (moments a practice can fire at, independent of which',
            'catalogue it belongs to) is the same everywhere Precedent\'s loader runs.',
        ],
        'gates': full['gates'],
    }


def _remove_dropped_engine_files(dest_tools, previous_manifest, kind):
    """Delete vendored engine files this kind no longer includes.

    THE GAP THIS CLOSES. `refresh` only ever added and overwrote. Rename or
    drop a file from KINDS and every consumer that already had it kept it
    forever: the new manifest stops listing it, so nothing tracks it, nothing
    updates it, and nobody can tell whether it still does something. That is
    exactly the state `decommission-deletes-files` exists to prevent,
    produced by the tool that distributes that practice.

    Found 2026-09-07 while costing the retirement->decommission rename:
    `precedent_decommission.py` is in the consumer engine set, so renaming it
    would have pushed the new name into every consumer and left the old one
    beside it, in perpetuity, in two repos today and every future one.

    WHY THIS IS SAFE, and it rests entirely on the manifest. The only files
    considered are ones the PREVIOUS manifest recorded as vendored here --
    written by this tool, into a directory the consuming repo also keeps its
    own files in. A file the engine never wrote is never a candidate, so a
    repo's own tools/ cannot be touched no matter what it is named.

    A hand-edited file is kept and reported, never deleted. `_local_drift`
    already refuses the whole refresh over one unless --force is passed, so
    reaching here with a modified file means somebody asked to overwrite --
    which is not the same as asking to throw the edit away. Recovering a
    deleted file from git is easy only if it was committed; this costs one
    line of output and removes the case where it was not.
    """
    prev_files = set(previous_manifest.get('files') or [])
    prev_hashes = previous_manifest.get('sha256') or {}
    now = set(KINDS.get(kind, ())) | {'routing_scope.json'}
    removed, kept = [], []
    for name in sorted(prev_files - now):
        f = dest_tools / name
        if not f.is_file():
            continue                      # already gone: nothing to report
        recorded = prev_hashes.get(name)
        if recorded and _sha256(f) != recorded:
            kept.append(name)
            continue
        f.unlink()
        removed.append(name)
    if removed:
        print(f"precedent_vendor_engine refresh: removed {len(removed)} "
              f"vendored engine file(s) this kind no longer includes "
              f"({', '.join(removed)}). They were recorded in the previous "
              f"manifest and unmodified here.")
        # dest_tools is <repo>/tools; the dependents live anywhere in it.
        _warn_about_dependents(dest_tools.parent,
                               [f'tools/{n}' for n in removed],
                               'removed from this kind\'s engine set')
    for name in kept:
        print(f"WARN: precedent_vendor_engine refresh: {name} was dropped from "
              f"the {kind} engine set, but this copy has been hand-edited "
              f"since it was vendored -- left in place rather than deleted. "
              f"Move the edit upstream, then delete it by hand.", file=sys.stderr)
    return removed


def _rewrite_manifest_file_list(dest_tools, kind):
    """Drop names this kind no longer includes from the manifest record.

    Called only on the early-exit cleanup path, where no write happens and
    so nothing else rewrites the manifest. Without it the removal succeeds
    on disk and the manifest goes on listing the deleted file, which is a
    provenance record asserting a file that is not there
    (practice: generated-artifact-provenance) -- and every later run would
    re-report the same orphan it already removed."""
    path = dest_tools / MANIFEST_NAME
    manifest = _load_manifest(dest_tools)
    if not manifest:
        return
    wanted = set(KINDS[kind]) | {'routing_scope.json'}
    manifest['files'] = [n for n in manifest.get('files', []) if n in wanted]
    manifest['sha256'] = {k: v for k, v in manifest.get('sha256', {}).items()
                          if k in wanted}
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8')


def _write_engine_files(dest_tools, engine_dir, source_commit, kind=DEFAULT_KIND):
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    # Only what _source_tools_at could actually extract: a name this (possibly
    # stale) copy's list still carries but upstream has dropped is skipped
    # there, so it is absent here too. Recording it in `files` anyway would
    # write a manifest asserting a file that does not exist.
    files = [n for n in KINDS[kind] if (engine_dir / n).is_file()]
    dest_tools.mkdir(parents=True, exist_ok=True)
    written = []
    hashes = {}
    for name in files:
        src = engine_dir / name
        out = dest_tools / name
        shutil.copy2(src, out)
        written.append(out)
        hashes[name] = _sha256(out)

    trimmed = _trim_routing_scope(engine_dir)
    routing_out = dest_tools / 'routing_scope.json'
    routing_out.write_text(json.dumps(trimmed, indent=2, ensure_ascii=False) + '\n',
                            encoding='utf-8')
    written.append(routing_out)
    hashes['routing_scope.json'] = _sha256(routing_out)

    manifest = {
        'format_version': 1,
        'kind': kind,
        'source_repo': SOURCE_REPO,
        'source_branch': SOURCE_BRANCH,
        'source_commit': source_commit,
        'files': files + ['routing_scope.json'],
        'sha256': hashes,
        '_note': (f"The vendored Precedent {kind}-repo engine (see "
                  "tools/precedent_vendor_engine.py's own docstring, and "
                  "spec/BOOTSTRAP_NEW_SOURCES.md / INSTALL.md). Never hand-edit a file "
                  "this manifest lists -- run "
                  "'python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>' "
                  "instead (kind is read back from this manifest -- no --kind flag needed "
                  "for status/refresh); a hand-edit is detected as drift (sha256 mismatch) "
                  "and refused without --force."),
    }
    manifest_path = dest_tools / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    written.append(manifest_path)
    return written


def _adapter_claimed_paths(dest_root):
    """Destination paths (relative to dest_root, e.g.
    '.claude/hooks/freshness-guard.sh') that a declared source's OWN
    `adapters` mechanism claims -- read from precedent_materialize.py's
    MANIFEST.json, the record of what its last run actually wrote. Maps
    path -> the claiming source's name.

    THE BUG THIS CLOSES. A consuming repo can declare a source
    (precedent_materialize.py's ADAPTER_DECL_KEY) that maintains its own
    copy of a file this engine ALSO vendors under the same destination --
    `.claude/hooks/freshness-guard.sh` is the concrete case:
    precedent-individual ships its own bootstrap/freshness-guard.sh,
    declared as an adapter to that exact path, independent of
    BestPractice's own bundled
    templates/harness/claude-code/hooks/freshness-guard.sh. Before this
    check existed, `status`/`refresh` compared the on-disk file --
    legitimately overwritten by that source's adapter -- against this
    engine's OWN `hooks_sha256` and reported the divergence as a hand-edit;
    `refresh` refused outright, and its own suggested `--force` fixed
    nothing durably, since the next materialize run would just overwrite the
    file right back to the adapter's content. Reproduced verbatim in a real
    consumer repo, 2026-09-15 (see the source's own trace for the repro).

    Returns {} if MANIFEST.json does not exist or cannot be parsed -- a repo
    that has never run precedent_materialize.py has no adapters to know
    about, and that is not this function's failure to report
    (practice: fail-gracefully)."""
    path = pathlib.Path(dest_root) / 'MANIFEST.json'
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return {}
    return {a['path']: a.get('source') for a in (data.get('adapters') or [])
            if isinstance(a, dict) and a.get('path')}


def _vendorable_hook_names(dest_root, hooks_src_dir):
    """The hook names this engine vendors into `dest_root`: what
    `hooks_src_dir` ships, minus RETIRED_HOOK_FILES, intersected with what
    this repo wires (_wired_hook_names), minus what a declared source's own
    adapter claims at the destination (_adapter_claimed_paths).

    ONE definition, called by both _write_hook_files (what gets written and
    recorded in `hook_files`) and refresh()'s `hooks_incomplete` (what counts
    as missing). They used to compute it separately, and refresh's copy
    dropped the adapter and retired exclusions: a consumer whose individual
    source ships commit-identity.sh and freshness-guard.sh had both skipped
    by the writer, never recorded, and still counted as missing -- so every
    refresh printed the "one-time catch-up" NOTICE and rewrote every engine
    file at an unchanged commit. Measured 2026-09-25 in a consumer running
    "Update Vendors". Asking both questions of one function is what keeps
    the answer from forking again."""
    claimed = _adapter_claimed_paths(dest_root)
    available = set(_hook_file_names(hooks_src_dir)) - set(RETIRED_HOOK_FILES)
    return {n for n in available & _wired_hook_names(dest_root)
            if f'{HOOK_DEST_DIR}/{n}' not in claimed}


def _write_hook_files(dest_root, hooks_src_dir):
    """Copy every hook script in `hooks_src_dir` into
    <dest_root>/.claude/hooks/, and record them in the SAME
    ENGINE_MANIFEST.json _write_engine_files just wrote (one provenance
    record per repo, not two) under `hook_files`/`hooks_sha256`.

    Read-modify-write on the manifest rather than folding this into
    _write_engine_files itself: that function's `manifest` dict is built
    fresh every call and knows nothing about a destination directory outside
    dest_tools, and giving it a second, differently-rooted output would blur
    what "dest_tools" means at every one of its call sites. This runs
    strictly AFTER _write_engine_files, so the manifest it reads back always
    exists.

    `hooks_src_dir` may not exist (an old commit predating HOOK_SOURCE_DIR,
    or a working tree with no templates/ at all in a bootstrapped source
    set) -- then this writes nothing and leaves the manifest's hook keys as
    they were, rather than erasing a previously-vendored record.

    Scoped to _wired_hook_names(dest_root) -- see that function's docstring.
    Vendoring everything HOOK_SOURCE_DIR ships, unconditionally, is the bug
    it exists to prevent: this repo's own verify_harness.py caught it before
    it shipped. Also excludes any name a declared source's own adapter
    already claims at this destination (_adapter_claimed_paths) -- that
    source maintains the file independently, and this engine vendoring its
    own bundled copy over the same path is exactly the double-maintenance
    that reads as a hand-edit later. See _adapter_claimed_paths' docstring."""
    available = set(_hook_file_names(hooks_src_dir))
    wired = _wired_hook_names(dest_root)
    claimed = _adapter_claimed_paths(dest_root)
    adapter_owned = {n for n in available
                     if f'{HOOK_DEST_DIR}/{n}' in claimed}
    available -= set(RETIRED_HOOK_FILES)
    names = sorted(_vendorable_hook_names(dest_root, hooks_src_dir))
    skipped = sorted(available - wired - adapter_owned)
    # A hook this repo wires from somewhere OTHER than .claude/hooks/ is
    # wired. Saying it is not, and then telling the reader to hand-wire it,
    # is how a repo that deliberately calls one script in place ends up with
    # two copies of it. See _wired_hook_names_anywhere.
    elsewhere = sorted(set(skipped) & _wired_hook_names_anywhere(dest_root))
    skipped = [n for n in skipped if n not in set(elsewhere)]
    if elsewhere:
        print(f"NOTE: precedent_vendor_engine: {len(elsewhere)} hook "
              f"script(s) BestPractice also ships ({', '.join(elsewhere)}) "
              f"are wired by this repo from a path of its own rather than "
              f"from {HOOK_DEST_DIR}/ -- so this engine does not vendor them "
              f"and there is NOTHING TO DO about them. A repo that calls a "
              f"script in place keeps one copy of it on purpose; planting "
              f"this engine's bundled copy beside it is the "
              f"double-maintenance that reads as a hand-edit later.",
              file=sys.stderr)
    if skipped:
        # Since 2026-09-25 a hook this repo's kind gets is WIRED by the
        # refresh before this runs (HOOK_WIRING, _apply_hook_wiring), so
        # what is left here is only ever a hook another kind gets, one on
        # no kind's list, one this repo declined, or one whose entry needs
        # a base branch nobody wrote down -- and the last says so itself.
        print(f"NOTE: precedent_vendor_engine: {len(skipped)} hook script(s) "
              f"BestPractice ships are not wired in this repo's own "
              f".claude/settings.json ({', '.join(skipped)}) -- not vendored. "
              f"Each is a hook another repo kind gets, one no kind gets "
              f"(HOOKS_NO_KIND, with its reason), or one this repo declined "
              f"in precedent.json. A hook THIS repo's kind gets is wired and "
              f"delivered by the refresh on its own (HOOK_WIRING).",
              file=sys.stderr)
    for n in sorted(adapter_owned & wired):
        source_name = claimed[f'{HOOK_DEST_DIR}/{n}']
        print(f"NOTE: precedent_vendor_engine: {n} is not vendored by this "
              f"engine -- {source_name!r}'s own adapters mechanism owns "
              f"{HOOK_DEST_DIR}/{n} in this repo (see precedent_materialize.py's "
              f"MANIFEST.json). That copy is maintained independently; this "
              f"engine's own bundled {n} is not applied here.", file=sys.stderr)
    dest_hooks = dest_root / HOOK_DEST_DIR
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    _remove_dropped_hook_files(dest_root, manifest_path, available,
                               hooks_src_dir)
    if not names:
        # Nothing wired here to write -- but a drop sweep may still have had
        # something to do, so this return comes AFTER it, not before. When
        # upstream DID ship hooks, the record still has to say "none vendored
        # here": a hook recorded before a source's adapter took its path over
        # would otherwise stay in `hook_files` forever, and `status` would
        # keep promising a refresh drops it. An absent source dir (nothing
        # shipped) still leaves the record alone, per the docstring.
        if available and manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            if manifest.get('hook_files') or manifest.get('hooks_sha256'):
                manifest['hook_files'] = []
                manifest['hooks_sha256'] = {}
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8')
        return []
    dest_hooks.mkdir(parents=True, exist_ok=True)
    written = []
    hashes = {}
    for name in names:
        src = hooks_src_dir / name
        out = dest_hooks / name
        shutil.copy2(src, out)
        out.chmod(0o755)
        written.append(out)
        hashes[name] = _sha256(out)

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['hook_files'] = names
    manifest['hooks_sha256'] = hashes
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return written


def _remove_dropped_hook_files(dest_root, manifest_path, available,
                               hooks_src_dir):
    """Delete a vendored hook that upstream no longer ships. -> [names]

    THE GAP THIS CLOSES (found 2026-09-21 by the very deep check's own
    deletion-propagation table, `very-deep-check` pass 2 item 8b; filed as
    todo-2026-09-21-a-dropped-hook-never-leaves-a-consumer.md). Until now
    this engine had exactly two removal paths -- _remove_dropped_engine_
    files for tools/ and _remove_retired_ci_workflow_files for
    .github/workflows/ -- and none for .claude/hooks/. A hook dropped
    upstream stayed installed in every consumer, and _write_hook_files then
    REPLACED `hook_files` with only what it had just written, so the
    manifest entry vanished too: the file went on running, every session,
    recorded by nothing and visible to no check keyed on the manifest.

    That is the CI-workflow asymmetry one directory over, and a hook is the
    worse of the two -- a stale workflow burns a runner minute, a stale hook
    executes in every session of every repo that still carries it.

    WHAT COUNTS AS DROPPED, precisely: a name the PREVIOUS manifest recorded
    that upstream no longer SHIPS. Not "no longer wired here" -- un-wiring
    is the repo's own act and hooks-on-disk-are-reachable already reports
    the orphan it leaves -- and not "claimed by an adapter", which is
    another mechanism maintaining the same path on purpose.

    THE GUARD THIS NEEDS AND THE ENGINE PATH DOES NOT. `available` comes
    from a directory glob, and _hook_file_names returns [] for a directory
    that is not there. An empty upstream hooks/ is indistinguishable from
    "this checkout cannot see upstream", and sweeping on that reading would
    delete every hook in the consumer. So an empty `available` sweeps
    NOTHING, the same refusal _remove_retired_ci_workflow_files makes for an
    unrecognised kind.

    A hand-edited copy is kept and reported rather than deleted, the same
    standard as the engine path: reaching here means somebody asked to
    overwrite, which is not the same as asking to throw an edit away."""
    if not available or not hooks_src_dir.is_dir():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    previous = list(manifest.get('hook_files') or [])
    prev_hashes = manifest.get('hooks_sha256') or {}
    dropped = sorted(n for n in previous
                     if n not in available or n in RETIRED_HOOK_FILES)
    if not dropped:
        return []
    dest_hooks = dest_root / HOOK_DEST_DIR
    removed, kept = [], []
    for name in dropped:
        f = dest_hooks / name
        if not f.is_file():
            continue                      # already gone: nothing to report
        recorded = prev_hashes.get(name)
        if recorded and _sha256(f) != recorded:
            kept.append(name)
            continue
        f.unlink()
        removed.append(name)
    if removed:
        print(f"precedent_vendor_engine refresh: removed {len(removed)} "
              f"vendored hook(s) upstream no longer ships "
              f"({', '.join(removed)}). They were recorded in the previous "
              f"manifest and unmodified here.")
        _warn_about_dependents(dest_root,
                               [f'{HOOK_DEST_DIR}/{n}' for n in removed],
                               'dropped from the hooks this engine ships')
    for name in kept:
        print(f"WARN: precedent_vendor_engine refresh: {name} is no longer "
              f"shipped upstream, but this copy has been hand-edited since "
              f"the manifest recorded its hash -- left in place, not "
              f"deleted. Move the edit upstream, then delete it by hand.",
              file=sys.stderr)
    if removed or kept:
        # The record has to lose the names too, or the next refresh reads
        # them as dropped all over again and says so all over again.
        manifest['hook_files'] = [n for n in previous if n not in removed]
        manifest['hooks_sha256'] = {k: v for k, v in prev_hashes.items()
                                    if k not in removed}
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
            encoding='utf-8')
    return removed


def _hook_drift(dest_root, manifest):
    """Hook-file analog of _local_drift: [(name, why)] for a vendored hook
    whose on-disk sha256 no longer matches what the manifest recorded, or
    that has gone missing. A manifest with no `hook_files` yet (vendored
    before this mechanism existed) reports no drift -- there is nothing
    recorded to have drifted from, and that state is handled by refresh()
    choosing to vendor hooks for the first time, not by this function.

    A name a declared source's own adapter now claims at this destination
    (_adapter_claimed_paths) is never reported here, missing or mismatched:
    that divergence is that source maintaining its own file, not a hand-edit
    of this engine's copy. A manifest can still carry hooks_sha256 for such a
    name from before the source's adapter took the path over -- the next
    `refresh` drops it from tracking entirely once this check stops flagging
    it (_write_hook_files excludes it from what it (re)vendors)."""
    claimed = _adapter_claimed_paths(dest_root)
    drifted = []
    for name, recorded_hash in (manifest.get('hooks_sha256') or {}).items():
        if f'{HOOK_DEST_DIR}/{name}' in claimed:
            continue
        path = dest_root / HOOK_DEST_DIR / name
        if not path.is_file():
            drifted.append((name, 'missing'))
            continue
        if _sha256(path) != recorded_hash:
            drifted.append((name, 'hand-edited (sha256 differs from manifest)'))
    return drifted


# --- Declared engine paths: an upstream file kept at a path of the repo's own
#
# WHY THIS EXISTS (2026-09-24). precedent-individual keeps
# `bootstrap/commit-identity.sh` byte-identical to this repo's
# templates/harness/claude-code/hooks/commit-identity.sh, and until now only
# by hand: four sync commits in ten days, each one a session noticing the
# drift. The hooks block above cannot help -- it vendors into .claude/hooks/
# only, and a repo that wires a script from its own path is deliberately
# skipped (_wired_hook_names_anywhere). Moving the file is not an option
# either: this repo's own .claude/hooks/session-start.sh runs
# `<individual set>/bootstrap/commit-identity.sh` by that exact path, and the
# set's precedent.json `adapters` ships it to consumers FROM there, so the
# path is load-bearing in two places and deleting it fails silently in both.
#
# So the repo DECLARES the mapping, in its own precedent.json:
#
#     "engine_paths": {
#       "templates/harness/claude-code/hooks/commit-identity.sh":
#         "bootstrap/commit-identity.sh"
#     }
#
# upstream path (in this repo's tree) -> local path (in the declaring repo).
# `refresh` then copies it like any engine file, records its sha256 in
# ENGINE_MANIFEST.json (`engine_paths`/`engine_paths_sha256`), and a
# hand-edit is drift, refused without --force, exactly as for tools/.
#
# Four rules, each closing a way this could hurt:
#
#   * NO SECOND WRITER. A local path an adapter already writes (an adapter's
#     TO, per _adapter_claimed_paths) or one this engine already vendors is
#     refused, whatever --force says: two mechanisms owning one file is the
#     double-maintenance that reads as a hand-edit later. An adapter's FROM
#     is fine -- that is precedent-individual's case, and consumers are
#     unaffected because the adapter still copies from the same place.
#   * FIRST RUN ADOPTS, NEVER OVERWRITES. With no hash recorded yet, a local
#     file identical to upstream is adopted silently; a different one is
#     refused with a count of differing lines, EVEN UNDER --force. --force
#     means "discard the edit I was told about"; on a first run nobody has
#     been told anything yet. It also has to hold under refresh's own second
#     pass, which re-runs with --force whenever the tool replaced itself --
#     which is exactly the run that first acts on a new declaration.
#   * AN UPSTREAM FILE THAT VANISHED IS KEPT. Warned about, loudly, on every
#     refresh that reaches the write step; the local copy and its record
#     stay. Deleting a repo's own-path file on a routine refresh is a larger
#     decision than this makes.
#   * A DROPPED DECLARATION HANDS THE FILE BACK. It stops being tracked and
#     becomes the repo's own, left on disk and said once.
ENGINE_PATHS_KEY = 'engine_paths'


def _clean_rel(rel):
    """A repo-relative POSIX path, or None if it could escape the repo."""
    if not isinstance(rel, str) or not rel.strip():
        return None
    p = pathlib.PurePosixPath(rel.strip())
    if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] == '.git':
        return None
    return str(p)


def declared_engine_paths(dest_root):
    """-> {upstream_rel: local_rel} from this repo's precedent.json.

    Never raises: an unreadable precedent.json is no declaration, the same as
    local_ci_workflows. An entry that is present but unusable (absolute, `..`,
    not a string) is dropped AND named on stderr -- silently ignoring a
    declaration somebody wrote is how it stops being read."""
    cfg = pathlib.Path(dest_root) / 'precedent.json'
    try:
        declared = json.loads(cfg.read_text(encoding='utf-8')).get(
            ENGINE_PATHS_KEY) or {}
    except (OSError, ValueError, AttributeError):             # noqa: BLE001
        return {}
    if not isinstance(declared, dict):
        print(f"WARN: precedent_vendor_engine: precedent.json's "
              f"{ENGINE_PATHS_KEY!r} is not an object -- ignored.",
              file=sys.stderr)
        return {}
    out = {}
    for up, local in declared.items():
        up_c, local_c = _clean_rel(up), _clean_rel(local)
        if up_c is None or local_c is None:
            print(f"WARN: precedent_vendor_engine: ignoring {ENGINE_PATHS_KEY} "
                  f"entry {up!r} -> {local!r}: both sides must be relative "
                  f"paths inside the repository.", file=sys.stderr)
            continue
        out[up_c] = local_c
    return out


def _engine_owned_paths(dest_root, manifest, kind):
    """Every local path this engine itself writes or tracks, repo-relative."""
    names = set(KINDS.get(kind, [])) | {'routing_scope.json', MANIFEST_NAME}
    names |= set(manifest.get('files') or [])
    owned = {f'tools/{n}' for n in names}
    hooks = set(manifest.get('hook_files') or []) | _wired_hook_names(dest_root)
    owned |= {f'{HOOK_DEST_DIR}/{n}' for n in hooks}
    owned |= {rel for _t, rel in CI_WORKFLOW_TEMPLATES.get(kind, ())}
    owned |= {rel for _s, rel in TEMPLATE_INSTANCES.get(kind, ())}
    return owned


def _engine_path_conflicts(dest_root, mapping, manifest, kind):
    """[(local_rel, why)] for declared mappings that would give one file two
    writers. Checked before anything is written, and not waived by --force."""
    claimed = _adapter_claimed_paths(dest_root)
    owned = _engine_owned_paths(dest_root, manifest, kind)
    bad, seen = [], {}
    for up, local in sorted(mapping.items()):
        if local in claimed:
            bad.append((local, f"an adapter from {claimed[local]!r} already "
                               f"writes this path (it is that adapter's "
                               f"destination)"))
        elif local in owned:
            bad.append((local, "this engine already vendors this path"))
        elif local in seen:
            bad.append((local, f"declared twice, from {seen[local]!r} and "
                               f"{up!r}"))
        seen.setdefault(local, up)
    return bad


def _engine_path_drift(dest_root, manifest):
    """[(local_rel, why)] for a declared engine path whose file no longer
    matches the hash the manifest recorded, or has gone missing. Only paths
    that are both recorded AND still declared: a dropped declaration has
    handed the file back to the repo, and there is nothing to drift from."""
    declared = set(declared_engine_paths(dest_root).values())
    drifted = []
    for local, recorded in (manifest.get('engine_paths_sha256') or {}).items():
        if local not in declared:
            continue
        path = pathlib.Path(dest_root) / local
        if not path.is_file():
            drifted.append((local, 'missing'))
        elif _sha256(path) != recorded:
            drifted.append((local, 'hand-edited (sha256 differs from manifest)'))
    return drifted


def _engine_paths_incomplete(dest_root, manifest):
    """Local paths a refresh has something to do for even when the upstream
    commit has not moved: declared but not recorded, recorded against a
    different upstream path, missing on disk, or recorded but no longer
    declared (the record has to let go of it)."""
    mapping = declared_engine_paths(dest_root)
    rec_map = manifest.get(ENGINE_PATHS_KEY) or {}
    rec_sha = manifest.get('engine_paths_sha256') or {}
    todo = [local for up, local in mapping.items()
            if local not in rec_sha or rec_map.get(local) != up
            or not (pathlib.Path(dest_root) / local).is_file()]
    todo += [local for local in rec_sha if local not in set(mapping.values())]
    return sorted(set(todo))


def _read_engine_path_sources(clone, commit, mapping):
    """{upstream_rel: (bytes, executable)} read BY BLOB at `commit`, the same
    read-only discipline as _source_tools_at. An upstream path absent at that
    commit is simply not in the result; the caller warns about it."""
    out = {}
    for up in mapping:
        ok, listing = _git_read(clone, 'ls-tree', commit, '--', up)
        if not ok or not listing.strip():
            continue
        mode = listing.split()[0]
        blob = subprocess.run(['git', '-C', str(clone), 'show', f'{commit}:{up}'],
                              capture_output=True)
        if blob.returncode != 0:
            continue
        out[up] = (blob.stdout, mode.endswith('755'))
    return out


def _differing_lines(a_bytes, b_bytes):
    import difflib
    a = a_bytes.decode('utf-8', 'replace').splitlines()
    b = b_bytes.decode('utf-8', 'replace').splitlines()
    return sum(1 for line in difflib.unified_diff(a, b, lineterm='', n=0)
               if line[:1] in '+-' and not line.startswith(('+++', '---')))


def _engine_path_first_run_refusals(dest_root, mapping, sources, manifest):
    """[(local_rel, n_lines)] for a declared path with no recorded hash whose
    local file exists and differs from upstream. Refused whatever --force
    says -- see the block comment above for why."""
    rec_sha = manifest.get('engine_paths_sha256') or {}
    refusals = []
    for up, local in sorted(mapping.items()):
        if local in rec_sha or up not in sources:
            continue
        path = pathlib.Path(dest_root) / local
        if path.is_file():
            have = path.read_bytes()
            if have != sources[up][0]:
                refusals.append((local, _differing_lines(have, sources[up][0])))
    return refusals


def _write_engine_paths(dest_root, mapping, sources, manifest):
    """Write each declared engine path from `sources` and record it in the
    manifest (read-modify-write, AFTER _write_engine_files, whose fresh
    manifest knows nothing of these keys). `manifest` is the one loaded
    before this refresh -- it carries the previous record, which is kept for
    an upstream path that has vanished. -> [written paths]"""
    dest_root = pathlib.Path(dest_root)
    prev_map = dict(manifest.get(ENGINE_PATHS_KEY) or {})
    prev_sha = dict(manifest.get('engine_paths_sha256') or {})
    new_map, new_sha, written = {}, {}, []
    for up, local in sorted(mapping.items()):
        path = dest_root / local
        if up not in sources:
            print(f"WARN: precedent_vendor_engine refresh: {ENGINE_PATHS_KEY} "
                  f"declares {up} -> {local}, but upstream no longer has {up} "
                  f"at this commit. {local} is left exactly as it is and is "
                  f"NOT being kept current any more -- fix the declaration "
                  f"(renamed upstream?) or remove it.", file=sys.stderr)
            if local in prev_sha:
                new_map[local], new_sha[local] = prev_map.get(local, up), prev_sha[local]
            continue
        data, executable = sources[up]
        if not path.is_file() or path.read_bytes() != data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            written.append(path)
        if executable:
            path.chmod(0o755)
        new_map[local], new_sha[local] = up, _sha256(path)
    for local in sorted(set(prev_sha) - set(mapping.values())):
        print(f"NOTE: precedent_vendor_engine refresh: {local} is no longer "
              f"declared in {ENGINE_PATHS_KEY} -- left on disk and no longer "
              f"tracked. It is this repo's own file now.")
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    live = json.loads(manifest_path.read_text(encoding='utf-8'))
    if new_map:
        live[ENGINE_PATHS_KEY] = new_map
        live['engine_paths_sha256'] = new_sha
    else:
        live.pop(ENGINE_PATHS_KEY, None)
        live.pop('engine_paths_sha256', None)
    manifest_path.write_text(json.dumps(live, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return written


# --- CI workflow files: templates/github-actions/*.template ----------------
# Distinct from the tools/ engine files and the .claude/hooks/ scripts above
# in the same two ways HOOK_SOURCE_DIR's own comment names for itself: a
# different source directory (templates/github-actions/, not tools/) and a
# different destination (.github/workflows/, not tools/ or .claude/hooks/).
# Until 2026-09-18 these files were installed ONCE -- precedent_install.py's
# _bootstrap_and_ci and precedent_bootstrap_source.py's _install_workflows
# both write `if not wf.exists() or force`, never on an ordinary refresh --
# so "Update Vendors" never re-copied the template body into an
# already-installed file. Reached a real consumer this way: doc-lint.yml.
# template's `concurrency:` block (2026-09-15) reached an already-installed
# bestpractice-docs.yml only when that repo reinstalled from scratch, and
# spec/CI_MINUTES_PLAN.md's Phase C debounce-guard step (added the next day)
# never reached it at all -- the same class of gap the hooks block above
# closed for .claude/hooks/*.sh on 2026-09-15.
#
# KIND-SPECIFIC, unlike the hooks above (which vendor the SAME scripts into
# both kinds, narrowed only by what a repo's own settings.json wires). A
# consumer installs bestpractice-docs.yml from doc-lint.yml.template; a
# source set installs precedent-check.yml (which since 2026-09-19 also
# carries the views-drift check as one of its jobs -- see
# templates/github-actions/precedent-check.yml.template's own header,
# spec/CI_MINUTES_PLAN.md item 9) from its own template --
# CI_WORKFLOW_TEMPLATES is the one place that pairing is declared, so
# precedent_bootstrap_source.py's own WORKFLOW_TEMPLATES reuses it rather
# than repeating it (practice: registry-source-of-truth).
#
# Both are gated on `ci_workflows` at the point they are WRITTEN
# (precedent_install.py's / precedent_bootstrap_source.py's own
# `_ci_preference`) -- nothing below this line asks that question again. A
# file this kind's list names but that is not present on disk is simply not
# this mechanism's business: correctly absent because CI is declined, same
# as always.
#
# THE CATCH-UP IS DELIBERATELY DIFFERENT FROM THE HOOKS ONE ABOVE. A hook
# script is engine code this repo ships as an unmodified adapter -- "this
# engine has no local variance by design" -- so the hooks catch-up
# overwrites an untracked one outright. A CI workflow YAML is exactly the
# kind of file a real repo hand-tunes (an extra job, a changed schedule, a
# repo-specific secret), so the first refresh after this shipped must not
# silently discard that. `_refresh_ci_workflow_files` below records a
# baseline hash for an untracked file and leaves its content alone; only a
# LATER refresh, once that baseline exists, can tell "matches what we
# recorded" from "hand-edited" and act on it.
CI_WORKFLOWS_SOURCE_DIR = 'templates/github-actions'
# WRITTEN AT INSTALL, NEVER REFRESHED (2026-09-25, spec/BRANCH_TIERS_PLAN.md).
# The light check is a repository's one GitHub test, on the pull request into
# main, and precedent_install.py writes it into a new install when
# github_ci_workflows allows. It is deliberately NOT in CI_WORKFLOW_TEMPLATES:
# many installs already run a light-check.yml of their own, written by hand
# and running their own command (the template's own header says so), and a
# file on that list is baselined on one refresh and replaced by the template
# on the next. A file here is written only where none exists, and never
# touched again.
CI_INSTALL_ONLY_TEMPLATES = {
    'consumer': (
        ('light-check.yml.template', '.github/workflows/light-check.yml'),
    ),
    'source': (),
}
CI_WORKFLOW_TEMPLATES = {
    # NO WORKFLOW EXISTS SOLELY TO LINT MARKDOWN (2026-09-21). The consumer
    # side used to ship doc-lint.yml.template as bestpractice-docs.yml, and
    # it is retired -- see RETIRED_CI_WORKFLOW_FILES below, which propagates
    # its deletion to every repo that installed it.
    'consumer': (
        ('leak-gate.yml.template', '.github/workflows/leak-gate.yml'),
    ),
    # A PRACTICE SOURCE RUNS NO CI AT ALL (2026-09-21, Morgan, strength:
    # decided): "the sets don't need CI; maybe we define the default to be
    # that the precedent-individual and precedent-shared-* do NOT get CI.
    # That could be the default rule, for future individual and shared
    # source repos."
    #
    # MEASURED, from his own GitHub usage export for that day. 127 of 143
    # billed minutes -- 89% -- came from four practice sets running these
    # two workflows. The twelve CONSUMING repos, all on the one-job
    # light-check, cost 16 minutes between them. The sets' share had gone
    # 2% -> 89% in eleven days while the absolute number stayed flat,
    # because every Update Vendors pass pushes a branch to four repos and
    # each push fires both workflows in each.
    #
    # WHY A SOURCE IS THE RIGHT PLACE TO STOP. Every change to a set
    # arrives through a session that runs the full gate suite before it
    # pushes -- the deep check is what gates a push (two-check-levels), and
    # the commit gate already ran doc_lint. CI there re-checks a tree that
    # was checked seconds earlier by the same tools. And most of what it
    # runs does not apply: a set carries few of the practices the registry
    # binds, so precedent-check SKIPS most of its catalogue there, which is
    # how two real sets came to report `0 passed` on an ordinary commit.
    # We were paying per-job minutes, rounded up, for a second opinion that
    # was mostly skips.
    #
    # A CONSUMER IS DIFFERENT and keeps its leak gate. A consuming repo can
    # receive a contribution from a fork, whose pushes never fire `push` in
    # the receiving repository -- so without the workflow a contributed
    # branch reaches it unscanned. A source set is single-owner and takes
    # no forks.
    #
    # The empty tuple is not an oversight and is READ as a decision:
    # _remove_retired_ci_workflow_files sweeps whatever a kind no longer
    # ships, and only for a kind it recognises, so `source` being present
    # and empty propagates the deletion to every set on its next refresh
    # while an unknown kind still triggers nothing.
    'source': (),
}

# CI-workflow analog of RETIRED_ENGINE_FILES above -- a relative path this
# manifest may still be tracking in ci_workflow_files/ci_workflows_sha256
# whose template CI_WORKFLOW_TEMPLATES no longer lists at all.
#
# THE GAP THIS CLOSES, found 2026-09-19 in a real individual practice set.
# views-drift.yml.template was folded into precedent-check.yml.template as
# its own job (spec/CI_MINUTES_PLAN.md item 9), and the four repos that hand-
# applied that fix the same day deleted the now-redundant views-drift.yml
# file -- but nothing told refresh() the old entry was retired, so
# ci_workflows_sha256 kept recording a hash for a file that no longer
# existed. _ci_workflow_drift reads "recorded, but missing on disk" as a
# hand-edit needing --force, so the NEXT refresh() in that repo would have
# refused entirely over a file the fix had already, correctly, removed --
# not the file-content drift that check exists to catch.
#
# WHY A TOMBSTONE, MIRRORING RETIRED_ENGINE_FILES, RATHER THAN JUST DIFFING
# CI_WORKFLOW_TEMPLATES. A name gone from the current mapping is ambiguous
# on its own: it could mean "retired, fold its job into the survivor" (safe
# to stop tracking) or "a repo's own tools/ vendored an older engine that
# still lists a file dropped since" (nothing to clean up, this repo simply
# has not refreshed yet). Naming the retirement explicitly, with the reason,
# is what makes automatic cleanup safe to do unconditionally rather than
# guessing from absence.
#
# WHY THIS DELETES THE FILE WHEN IT IS SAFE TO, as of 2026-09-20 --
# mirroring _remove_dropped_engine_files for an ordinary tools/*.py engine
# file, not this mechanism's original "never deletes" design. refresh()'s
# own comment on ci_incomplete still holds the reason a retired workflow
# file is never deleted UNCONDITIONALLY: "deleting somebody's
# .github/workflows/*.yml out from under them on a routine refresh is a
# different, larger decision than this fix makes." What changed is that
# _remove_retired_ci_workflow_files (below) now only ever deletes a copy
# whose on-disk content still matches the hash the manifest last recorded
# for it -- the untouched, stock retired template, and nothing else. A
# hand-edited copy, or one the manifest never recorded a hash for, is kept
# and reported exactly as before; only the manifest's stale tracking entry
# is ever dropped unconditionally. Raised by Morgan
# ("shouldn't we delete the files? ... it creates confusion and complexity
# and risk and cost") against a live incident: a fresh usage-report pull
# found several personal repos still billing real minutes against files
# this mechanism already knew were retired. This closes the half of that
# gap this mechanism can reach going forward -- a FUTURE rename/fold, the
# same way views-drift.yml's own retirement was. It does NOT retroactively
# clean up a file that predates this tombstone system entirely (nothing
# ever recorded a hash for it to compare against) -- see
# spec/CI_MINUTES_PLAN.md's Phase B sweep for that half.
RETIRED_CI_WORKFLOW_FILES = {
    '.github/workflows/views-drift.yml':
        'folded into precedent-check.yml.template as its own job, 2026-09-19 '
        '(spec/CI_MINUTES_PLAN.md item 9)',
    # THE MARKDOWN LINT LEAVES CI ENTIRELY, 2026-09-21. Morgan: "I think we
    # should remove all markdown checks in the yml github actions check (but
    # we should use the strict markdown in our own that we do)."
    #
    # The reasoning, and it is not only cost. Under this system's founding
    # assumption -- every edit arrives through a cloud session, never a
    # local checkout and never the GitHub web UI -- doc_lint.py has already
    # run on every change before it is committed, because it IS the light
    # check that gates a commit. The CI copy re-ran it against work the
    # session in front of the person had just cleared. Measured in the
    # busiest consuming repo: 350 billed minutes over 19 days for that
    # re-run, on a workflow that was already one job with paths: filters.
    #
    # The linter is not retired -- only the workflow whose whole job was to
    # run it a second time. doc_lint.py still gates every commit, and still
    # runs inside this repo's own deep-check.yml as a step in a job billed
    # for other reasons anyway. The rule that came out of it: no workflow
    # exists solely to lint Markdown.
    '.github/workflows/bestpractice-docs.yml':
        'the Markdown lint left CI entirely, 2026-09-21 -- doc_lint.py '
        'already gates every commit as the light check, so this re-ran it '
        'on work a session had just cleared (spec/BILLING_FLOOR.md)',
}


def record_ci_workflow_files(dest_root, kind):
    """Read-modify-write ENGINE_MANIFEST.json's `ci_workflow_files`/
    `ci_workflows_sha256` from whichever of this kind's CI workflow files
    actually exist on disk at `dest_root` right now -- called by
    precedent_install.py and precedent_bootstrap_source.py right after they
    write .github/workflows/*.yml from templates/github-actions/*.template,
    AFTER precedent_vendor_engine.seed() has already written
    ENGINE_MANIFEST.json. Necessarily after: seed()/_write_engine_files
    build that file FRESH on every call (see its own docstring), so
    anything recorded here before seed runs would be silently wiped -- the
    same way hook_files would be if _write_hook_files ran before
    _write_engine_files instead of after.

    Does not copy anything -- by the time either caller reaches this point
    the workflow file is already on disk, written by that caller's own
    template substitution. This only computes and records its hash. A file
    this kind's CI_WORKFLOW_TEMPLATES names but that does not exist here
    (ci_workflows disabled) is simply left out -- not an error, and not
    recorded as missing; that is ci_workflows's own gate to report, not
    this one's.

    Returns [] when there is no manifest yet to write into (seed() failed,
    or was never run) -- fail-gracefully, matching _write_hook_files' own
    early-return shape."""
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    if not manifest_path.is_file():
        return []
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    names, hashes = [], {}
    for _template, rel in CI_WORKFLOW_TEMPLATES.get(kind, ()):
        path = dest_root / rel
        if path.is_file():
            names.append(rel)
            hashes[rel] = _sha256(path)
    manifest['ci_workflow_files'] = sorted(names)
    manifest['ci_workflows_sha256'] = hashes
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return [manifest_path]


LOCAL_CI_WORKFLOWS_KEY = 'local_ci_workflows'


def local_ci_workflows(dest_root):
    """-> {rel: reason} for CI workflow files this repo declares as its OWN,
    read from its precedent.json. Never raises: a malformed config must not
    take a refresh down, and an unreadable declaration is treated as no
    declaration -- the refusal it would have waived is the safe direction.

    WHY THIS EXISTS, and why the two escapes that already existed are not
    escapes. A consuming repo may have a genuine reason to diverge one
    vendored workflow -- 2026-09-21's case was an identity fold plus a
    deliberate note about a flag the repo does not want. `refresh` refuses,
    correctly, because it cannot tell that edit from an accident. But both
    routes out DESTROY the divergence: `--force` overwrites it on the spot,
    and `record-ci` re-baselines the hash so the NEXT refresh overwrites it
    silently, which is worse. The session that hit it swapped the template
    in, ran the refresh, and put the file back by hand -- a manoeuvre that
    works exactly once and leaves nothing behind for the next person, who
    will meet the same wall with no hint that anyone has been here.

    So the divergence becomes a DECLARATION instead of a fight:

        "local_ci_workflows": {
          ".github/workflows/precedent-check.yml": "why this one is ours"
        }

    A REASON IS REQUIRED, not optional. A bare list would be an opt-out
    nobody has to justify, which is how an exemption stops being read; an
    entry with an empty reason is ignored, exactly as if it were absent,
    and refresh says so rather than honouring it silently.

    A declared file is then: never overwritten, never drift, never
    "untracked" -- and PRINTED ON EVERY RUN with its reason, so the
    exemption stays visible instead of becoming invisible infrastructure.
    That last part is the whole difference between this and --force.
    """
    cfg = dest_root / 'precedent.json'
    try:
        declared = json.loads(cfg.read_text(encoding='utf-8')).get(
            LOCAL_CI_WORKFLOWS_KEY) or {}
    except (OSError, ValueError, AttributeError):             # noqa: BLE001
        return {}
    if not isinstance(declared, dict):
        return {}
    return {str(rel): str(reason).strip()
            for rel, reason in declared.items()
            if isinstance(rel, str) and str(reason).strip()}


def _ci_workflow_drift(dest_root, manifest):
    """CI-workflow analog of _hook_drift: [(rel, why)] for a vendored CI
    workflow file the manifest's `ci_workflows_sha256` already records a
    hash for, whose on-disk sha256 no longer matches it -- a hand-edit (or
    a removal) since it was last recorded. A `rel` this manifest carries no
    hash for at all is NOT drift -- see CI_WORKFLOW_TEMPLATES' catch-up
    note above; there is nothing recorded yet to have drifted from.

    A `rel` in RETIRED_CI_WORKFLOW_FILES is ALSO not drift, missing or not:
    its retirement is already known and explained, and refresh() cleans up
    the stale tracking itself (_remove_retired_ci_workflow_files, called
    before this function ever runs) rather than refusing the whole run over
    a file whose disappearance a previous, correct fix already caused."""
    drifted = []
    _local = local_ci_workflows(dest_root)
    for rel, recorded_hash in (manifest.get('ci_workflows_sha256') or {}).items():
        if rel in RETIRED_CI_WORKFLOW_FILES:
            continue
        # A file this repo DECLARES as its own is not drift. Its divergence
        # is the point, and it is reported every run rather than refused
        # (local_ci_workflows' own docstring has the incident).
        if rel in _local:
            continue
        path = dest_root / rel
        if not path.is_file():
            drifted.append((rel, 'missing'))
            continue
        if _sha256(path) != recorded_hash:
            drifted.append((rel, 'hand-edited (sha256 differs from manifest)'))
    return drifted


def _untracked_ci_workflow_files(dest_root, manifest):
    """-> sorted [rel, ...] for every .github/workflows/*.yml or *.yaml file
    on disk that this repo's manifest does not track under
    ci_workflow_files, and that is not a known RETIRED_CI_WORKFLOW_FILES
    entry either.

    THIS IS NOT AN ORPHAN LIST. CI_WORKFLOW_TEMPLATES names exactly one
    file per kind -- the template-installed workflow -- so almost any repo
    with more than that single file will have entries here by design: a
    practice set's own commit-identity.yml and engine-refresh.yml are
    untracked by this exact definition and are completely legitimate,
    intentionally never vendored through this mechanism. A hand-authored
    check unrelated to Precedent is equally untracked and equally
    legitimate. Reports enumerate; they do not judge -- see
    spec/CI_WORKFLOW_RETIREMENT_PLAN.md's account of the false positive
    (light-check.yml, mistaken for a retired duplicate by filename alone)
    that this function's callers exist to never repeat. A caller decides
    what these paths mean; this function only says which paths exist
    outside what the manifest already tracks.

    Returns [] where dest_root has no ENGINE_MANIFEST.json at all (this
    repo has never vendored, or is the engine's own origin -- BestPractice
    itself has no manifest to compare against)."""
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    if not manifest_path.is_file():
        return []
    tracked = set(manifest.get('ci_workflow_files') or ())
    wf_dir = dest_root / '.github' / 'workflows'
    if not wf_dir.is_dir():
        return []
    on_disk = sorted(
        f'.github/workflows/{p.name}'
        for p in wf_dir.iterdir()
        if p.is_file() and p.suffix in ('.yml', '.yaml'))
    # A file this repo DECLARES as its own is known, not stray. Reporting
    # it as untracked would be the same wall under another name.
    _local = local_ci_workflows(dest_root)
    return [rel for rel in on_disk
            if rel not in tracked and rel not in RETIRED_CI_WORKFLOW_FILES
            and rel not in _local]


def _remove_retired_ci_workflow_files(dest_root, manifest, kind=None):
    """Drop every RETIRED_CI_WORKFLOW_FILES entry from a manifest that still
    carries one, and delete a retired file still on disk -- but ONLY when
    its current on-disk sha256 still matches the hash the manifest already
    had recorded for it under ci_workflows_sha256.

    WHAT "MATCHES THE RECORDED HASH" DOES AND DOES NOT PROVE. The recorded
    hash is whatever this engine itself last wrote for this path -- from the
    original record_ci_workflow_files() call at install/refresh time, or a
    later hand-triggered `record-ci` re-baseline. A match proves the file
    has not changed since the manifest last looked, which is everything
    _ci_workflow_drift() means by "not drifted" elsewhere in this module --
    the SAME standard, not a weaker one invented for this function. It does
    NOT prove the file was never hand-edited at any point in its history:
    someone could have edited it and then run `record-ci` to accept that
    edit as correct (exactly what that subcommand exists for), which
    updates the recorded hash to match the edit. If that same file's
    workflow is later retired, this function reads it as "matches the
    recorded hash" and deletes it -- a real, known gap, not a hypothetical
    one: see spec/CI_WORKFLOW_RETIREMENT_PLAN.md's "Touched, precisely"
    section for the full tradeoff and why it was left open rather than
    closed here.

    A path this function never even considers: one ci_workflows_sha256 has
    no entry for at all (this kind never vendored it, ci_workflows was
    disabled, or the file predates this tracking system entirely, like the
    pre-2026-09-14 legacy templates spec/CI_MINUTES_PLAN.md's Phase B still
    has to sweep by hand). `dropped` below is built only from paths that ARE
    manifest keys, so an untracked file is structurally invisible here --
    this function can delete a file it was already watching, never one it
    was not.

    Idempotent and safe to call unconditionally: a manifest with no such
    entry writes nothing and returns []. Called at the very top of refresh(),
    before _ci_workflow_drift ever runs, so a retirement this old cannot
    cause the "missing" drift RETIRED_CI_WORKFLOW_FILES exists to defuse --
    see that dict's own comment for the incident.

    Returns the list of rel paths dropped from the manifest, for refresh()'s
    own reporting -- deleted or merely reported, both count as dropped from
    TRACKING; whether the file itself is gone is reported separately."""
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    if not manifest_path.is_file():
        return []
    recorded = dict(manifest.get('ci_workflows_sha256') or {})

    # TWO WAYS A TRACKED CI WORKFLOW CAN BE OVER (the second added
    # 2026-09-21, practice: cite-the-incident).
    #
    # 1. A RETIRED_CI_WORKFLOW_FILES tombstone -- an explicit, reasoned
    #    entry, which is the only way a RENAME can be expressed.
    # 2. THIS KIND NO LONGER SHIPS IT. Until today this function read the
    #    tombstone dict alone, and _remove_dropped_engine_files -- the
    #    ordinary tools/ path, six hundred lines up -- has always done the
    #    opposite: it diffs the PREVIOUS manifest against what the kind
    #    includes now, so dropping a name propagates its deletion whether
    #    or not anybody remembered a tombstone.
    #
    #    That asymmetry was the concrete hole. Dropping a template from
    #    CI_WORKFLOW_TEMPLATES without also writing a tombstone left the
    #    installed workflow in every repo, forever, tracked by a manifest
    #    entry nothing would ever clear. Found 2026-09-21 while answering
    #    "are deletions passed through to the vendored-in repos?" -- the
    #    answer was yes for engine files and no for CI workflows, and
    #    nobody had noticed the two paths disagreed.
    #
    # THE GUARD THE ENGINE PATH DOES NOT NEED. _remove_dropped_engine_files
    # is called with a `kind` its caller has already validated. Here the
    # kind comes out of the MANIFEST, which is a file on disk in somebody
    # else's repository -- and `CI_WORKFLOW_TEMPLATES.get(<unknown>, ())`
    # is an empty tuple, which would read as "this kind ships nothing, so
    # delete everything tracked". A manifest with a typo'd or future kind
    # must not trigger a sweep, so the diff is skipped entirely unless the
    # kind is a key we recognise. The tombstone half still applies, since
    # it names paths explicitly and cannot over-reach.
    # THE KIND COMES FROM THE CALLER, not from the manifest, and that
    # distinction is load-bearing. During a source->consumer CONVERSION the
    # manifest on disk still says the OLD kind, so reading it here would
    # diff against the wrong shipping list and delete the new kind's own
    # workflows. Both call sites already compute
    # `manifest.get('kind', DEFAULT_KIND)`; they pass it in.
    if kind is None:
        kind = manifest.get('kind', DEFAULT_KIND)
    superseded = set()
    if kind in CI_WORKFLOW_TEMPLATES:
        ships_now = {installed_as
                     for _tmpl, installed_as in CI_WORKFLOW_TEMPLATES[kind]}
        superseded = {rel for rel in recorded if rel not in ships_now}
    elif recorded:
        print(f"NOTE: precedent_vendor_engine: manifest kind {kind!r} is not "
              f"one of {sorted(CI_WORKFLOW_TEMPLATES)}, so tracked CI "
              f"workflow files were NOT checked against what this kind "
              f"ships. Only explicitly retired entries were considered.",
              file=sys.stderr)

    dropped = sorted({rel for rel in recorded
                      if rel in RETIRED_CI_WORKFLOW_FILES} | superseded)
    if not dropped:
        return []
    deleted, kept = [], []
    for rel in dropped:
        recorded_hash = recorded.pop(rel, None)
        f = dest_root / rel
        if not f.is_file():
            continue                      # already gone: nothing to report
        if recorded_hash and _sha256(f) == recorded_hash:
            f.unlink()
            deleted.append(rel)
        else:
            kept.append(rel)
            if rel in LEGACY_CI_WORKFLOWS and LEGACY_CI_WORKFLOWS[rel][1](
                    f.read_text(encoding='utf-8', errors='ignore')):
                # Hand-paused copies of these are the common case (two of
                # the five measured installs). The legacy sweep, which runs
                # next, recognises this one by content and deletes it, so
                # telling the reader to delete it by hand would be wrong.
                # A copy it will NOT recognise still gets the warning.
                continue
            why = RETIRED_CI_WORKFLOW_FILES.get(
                rel, f'this kind ({kind}) no longer ships it')
            print(f"WARN: precedent_vendor_engine: {rel} was retired "
                  f"({why}) and has been hand-"
                  f"edited since the manifest last recorded its hash -- left "
                  f"in place, not deleted. Move the edit upstream, then "
                  f"delete it by hand once its replacement is confirmed "
                  f"working.", file=sys.stderr)
    if deleted:
        print(f"precedent_vendor_engine refresh: deleted {len(deleted)} "
              f"retired CI workflow file(s), unmodified since the manifest "
              f"last recorded them ({', '.join(deleted)}).")
        _warn_about_dependents(dest_root, deleted,
                               'retired from this kind\'s CI workflow set')
    live = json.loads(manifest_path.read_text(encoding='utf-8'))
    live['ci_workflow_files'] = sorted(recorded)
    live['ci_workflows_sha256'] = recorded
    manifest_path.write_text(json.dumps(live, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    manifest['ci_workflow_files'] = sorted(recorded)
    manifest['ci_workflows_sha256'] = recorded
    print(f"precedent_vendor_engine: dropped {len(dropped)} retired CI workflow "
          f"tracking entry(s) from the manifest ({', '.join(dropped)}).")
    return dropped


# --- Leftovers of the pre-Precedent install, recognised by CONTENT
#
# WHY THIS EXISTS (Morgan, 2026-09-24, strength: decided): "this needs to be
# deleted from ALL installs, the migration to the new precedent should [have]
# deleted this." Measured the same day in six of his installs: the old
# install's workflows survived in five of them, a month after migration.
#
# WHY THE TWO REMOVERS ABOVE NEVER SAW THEM. _remove_retired_ci_workflow_files
# and _remove_dropped_hook_files only consider a path the manifest recorded,
# and only while its hash still matches. An install older than that tracking
# recorded nothing, and a hand-paused copy no longer matches, so both kinds
# were structurally invisible: `bestpractice-docs.yml` had been retired for
# three days and was still in all five installs that had it -- two tracked but
# hand-paused, three never tracked at all.
#
# WHY CONTENT AND NEVER THE NAME. Every copy of these files differs (four
# installs, four different `bestpractice-upstream-sync.yml`s), so no single
# hash can recognise them. And a name alone has already deleted live checks:
# the 2026-09-20 sweep trusted a filename and took out nine
# (spec/CI_MINUTES_PLAN.md item 14), `light-check.yml` among them, which is a
# LIVE check in most installs. So a path is deleted only when its content has
# the old install's structural shape, and a file with the name but not the
# shape is kept and reported for a person to read. `light-check.yml` is on no
# list here at all.
#
# WHAT IS REUSED RATHER THAN FORKED. precedent_decommission.py's refusals
# about the file itself (untracked, uncommitted edits, a live trigger) and its
# registry, process/decommissioned_paths.json. Its reference search is NOT
# applied as a refusal, the same call dependents_of() makes for every other
# refresh deletion: a consumer's materialized practices/ names every retired
# workflow by design, so that refusal would fire every time and delete
# nothing. The references are reported instead.
LEGACY_REASON_UPSTREAM_SYNC = (
    'the pre-Precedent scheduled upstream sync, retired 2026-09-24 (Morgan: '
    '"this needs to be deleted from ALL installs"). Its schedule came off '
    '2026-09-14 and "Update Vendors" replaced it; the manual trigger it kept '
    'ran a job nothing uses')
LEGACY_REASON_DOCS = (
    'the Markdown-lint workflow, retired 2026-09-21 -- doc_lint.py already '
    'gates every commit as the light check (spec/BILLING_FLOOR.md)')
LEGACY_REASON_VIEWS_DRIFT = (
    'folded into precedent-check.yml.template as its own job, 2026-09-19 '
    '(spec/CI_MINUTES_PLAN.md item 9)')

_USES_RE = re.compile(r'^\s*-?\s*uses:\s*["\']?([^@\s"\']+)', re.M)
_PY_RE = re.compile(r'([\w./-]*\w)\.py\b')
_SECRET_RE = re.compile(r'secrets\.([A-Za-z_][A-Za-z0-9_]*)')
_STOCK_ACTIONS = {'actions/checkout', 'actions/setup-python'}


def _code_lines(text):
    return '\n'.join(ln for ln in text.splitlines()
                     if not ln.lstrip().startswith('#'))


def _workflow_facts(text):
    """-> (actions used, .py basenames run or named) from the non-comment
    lines of a workflow. Comments are dropped first: a header saying what a
    file USED to run is exactly what a hand-paused copy carries."""
    code = _code_lines(text)
    uses = set(_USES_RE.findall(code))
    scripts = {pathlib.PurePosixPath(m + '.py').name for m in _PY_RE.findall(code)}
    return uses, scripts


def _is_legacy_upstream_sync(text):
    uses, scripts = _workflow_facts(text)
    return 'anthropics/claude-code-action' in uses or 'checkin.py' in scripts


def _is_legacy_docs(text):
    uses, scripts = _workflow_facts(text)
    return (scripts == {'doc_lint.py'} and uses <= _STOCK_ACTIONS)


def _is_legacy_views_drift(text):
    uses, scripts = _workflow_facts(text)
    return (bool(scripts) and scripts <= {'build_views.py', 'precedent_sync_views.py'}
            and uses <= _STOCK_ACTIONS)


# path -> (why it is retired, content recogniser). A recogniser tests the
# SHAPE only; whether the file is still live is precedent_decommission's
# refusal, applied separately so the report can say which of the two held it.
LEGACY_CI_WORKFLOWS = {
    '.github/workflows/bestpractice-upstream-sync.yml':
        (LEGACY_REASON_UPSTREAM_SYNC, _is_legacy_upstream_sync),
    '.github/workflows/bestpractice-docs.yml':
        (LEGACY_REASON_DOCS, _is_legacy_docs),
    '.github/workflows/views-drift.yml':
        (LEGACY_REASON_VIEWS_DRIFT, _is_legacy_views_drift),
}

# Pre-Precedent names with NO stock shape anyone can point at: none of them
# was ever a template in this repository, on any branch, so there is nothing
# to recognise them against. Never deleted here -- listed, so the session
# running "Update Vendors" reads each one (vendor-update-runbook's "Retire
# legacy leftovers" step). `commit-identity.yml` is a leftover only in a
# CONSUMER; a practice set runs its own on purpose.
LEGACY_CI_WORKFLOWS_TO_READ = {
    '.github/workflows/practice-links-travel.yml':
        'its check now runs inside precedent-check.yml as the '
        '`practice-links-travel` case -- confirm that suite runs here, then '
        'decommission this copy',
    '.github/workflows/status-claims-check.yml': None,
    '.github/workflows/unified-prompt-check.yml': None,
    '.github/workflows/platform-docs-check.yml': None,
    '.github/workflows/commit-identity.yml': None,
}
_LEGACY_TO_READ_KINDS = {'.github/workflows/commit-identity.yml': {'consumer'}}

# Hook analog of RETIRED_CI_WORKFLOW_FILES + LEGACY_CI_WORKFLOWS: name ->
# (why, content recogniser). EMPTY ON PURPOSE, and read as a decision: no
# hook BestPractice ever shipped has been renamed or dropped (git history of
# templates/harness/claude-code/hooks/, checked 2026-09-24), and the six
# installs measured that day carry no hook of the old install -- their one
# extra hook, a Stop hook enforcing file-mention-links, is live and enforces
# a practice nothing else enforces. The mechanism exists so the FIRST drop
# propagates: _remove_dropped_hook_files honours a tombstone here for a
# tracked copy, and _retire_legacy_hooks for an untracked one.
RETIRED_HOOK_FILES = {}

# Config fields nothing reads any more, deleted from these files on refresh.
RETIRED_CONFIG_FIELDS = {
    'ci_debounce_minutes':
        'retired 2026-09-20 -- the debounce job cost the minute it was '
        'deciding whether to spend (spec/BILLING_FLOOR.md)',
}
_CONFIG_FILES = ('precedent.json', 'identity.json')

# Secrets the old install's workflows read, which no current template does.
LEGACY_SECRETS = ('PERSONAL_PACK_TOKEN',)

# Filled by the sweeps below, printed once at the end of refresh() as
# "Left for you": what the code would not do, and why.
_LEFT_FOR_YOU = []


def _left(item, why):
    _LEFT_FOR_YOU.append((item, why))


def _decommission_module():
    """precedent_decommission, vendored beside this file -- or None when the
    copy on disk predates the helpers this sweep shares with it (the first
    pass of a self-replacing refresh runs against an older one)."""
    try:
        sys.path.insert(0, str(ENGINE_DIR))
        import precedent_decommission as pd
    except Exception:                                          # noqa: BLE001
        return None
    if not all(hasattr(pd, n) for n in ('file_refusals', 'record_decommissioned',
                                         'read_registry')):
        return None
    return pd


def _drop_process_manifest_entries(dest_root, rel):
    """Remove every process/manifest*.json entry whose local_path is `rel`,
    which was just deleted -> [manifest names touched]. practice_audit.py
    FAILS on an entry whose local file is gone, so leaving one behind turns
    a correct deletion into a red check. Three measured installs carried a
    `diverged` entry for bestpractice-docs.yml."""
    touched = []
    proc = dest_root / 'process'
    if not proc.is_dir():
        return touched
    for m in sorted(proc.glob('manifest*.json')):
        try:
            data = json.loads(m.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        entries = data.get('entries')
        if not isinstance(entries, list):
            continue
        kept = [e for e in entries
                if not (isinstance(e, dict) and e.get('local_path') == rel)]
        if len(kept) != len(entries):
            data['entries'] = kept
            m.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                         encoding='utf-8')
            touched.append(m.name)
    return touched


def _retire_one(dest_root, pd, rel, reason):
    """Delete `rel` if precedent_decommission's file refusals allow it, and
    record it. -> True when deleted."""
    refusals = pd.file_refusals(dest_root, rel)
    if refusals:
        _left(rel, 'recognised as a leftover of the old install, but not '
                   'deleted: ' + '; '.join(refusals))
        return False
    # `git rm`, as precedent_decommission's own --apply does, so the
    # deletion is staged with its record: decommission-deletes-files reads
    # the TRACKED set, and an unstaged delete still counts as tracked.
    if pd._git('rm', '-q', '--', rel, cwd=dest_root).returncode != 0:
        (dest_root / rel).unlink()
    try:
        pd.record_decommissioned(dest_root, [rel], reason)
        pd._git('add', '--', pd.REGISTRY, cwd=dest_root)
    except ValueError as e:
        _left(rel, f'deleted, but not recorded: {e}')
    touched = _drop_process_manifest_entries(dest_root, rel)
    print(f"precedent_vendor_engine refresh: retired {rel} -- {reason}. "
          f"Recorded in {pd.REGISTRY}"
          + (f"; dropped its entry from {', '.join(touched)}" if touched else '')
          + '.')
    return True


def _retire_legacy_workflows(dest_root, manifest, kind, pd):
    """-> ({rel: text} deleted, [rel kept]). See the block comment above."""
    tracked = set(manifest.get('ci_workflow_files') or ())
    declared = local_ci_workflows(dest_root)
    deleted, kept = {}, []
    for rel, (reason, recognise) in sorted(LEGACY_CI_WORKFLOWS.items()):
        f = dest_root / rel
        if not f.is_file() or rel in tracked or rel in declared:
            continue
        text = f.read_text(encoding='utf-8', errors='ignore')
        if not recognise(text):
            kept.append(rel)
            _left(rel, 'carries a retired name but NOT the old install\'s '
                       'shape, so it was kept -- read it. If it is this '
                       'repo\'s own check, declare it under '
                       f'`{LOCAL_CI_WORKFLOWS_KEY}` in precedent.json with a '
                       'reason; if it is a leftover, decommission it with '
                       'tools/precedent_decommission.py')
            continue
        if pd is None:
            kept.append(rel)
            _left(rel, 'recognised as a leftover, but the vendored '
                       'precedent_decommission.py predates this sweep -- '
                       'refresh once more and it goes')
            continue
        if _retire_one(dest_root, pd, rel, reason):
            deleted[rel] = text
        else:
            kept.append(rel)
    for rel, hint in sorted(LEGACY_CI_WORKFLOWS_TO_READ.items()):
        kinds = _LEGACY_TO_READ_KINDS.get(rel)
        if kinds is not None and kind not in kinds:
            continue
        if not (dest_root / rel).is_file() or rel in tracked or rel in declared:
            continue
        _left(rel, 'a workflow name from before Precedent with no stock shape '
                   'to recognise it by, so nothing here deletes it. Read what '
                   'it runs'
                   + (f' ({hint})' if hint else '')
                   + '; decommission it if a current check covers it, or '
                   f'declare it under `{LOCAL_CI_WORKFLOWS_KEY}` if it is '
                   'this repo\'s own')
    if deleted:
        _warn_about_dependents(dest_root, sorted(deleted),
                               'retired as a leftover of the pre-Precedent install')
    return deleted, kept


def _retire_legacy_hooks(dest_root, manifest, pd):
    """Untracked analog of _remove_dropped_hook_files, for RETIRED_HOOK_FILES.
    A WIRED copy is never deleted: .claude/settings.json is the repo's own
    and a refresh never writes it, and deleting a script it still calls
    breaks every session start. -> [names deleted]"""
    tracked = set(manifest.get('hook_files') or ())
    wired = _wired_hook_names(dest_root)
    deleted = []
    for name, (reason, recognise) in sorted(RETIRED_HOOK_FILES.items()):
        f = dest_root / HOOK_DEST_DIR / name
        if not f.is_file() or name in tracked:
            continue
        rel = f'{HOOK_DEST_DIR}/{name}'
        if not recognise(f.read_text(encoding='utf-8', errors='ignore')):
            _left(rel, 'carries a retired hook name but not its shape -- kept; '
                       'read it')
            continue
        if name in wired:
            _left(rel, f'a retired hook ({reason}) still wired in '
                       '.claude/settings.json -- remove that entry, then '
                       'refresh again and it is deleted')
            continue
        if pd is not None and _retire_one(dest_root, pd, rel, reason):
            deleted.append(name)
    return deleted


def _without_json_key(text, key):
    """`text` with the top-level `"key": <scalar>` line removed, keeping every
    other byte -> new text, or None if that cannot be done safely. A person's
    precedent.json is hand-formatted and commented in `_comment` keys, so
    re-serialising it would rewrite the whole file to delete one line."""
    try:
        before = json.loads(text)
    except ValueError:
        return None
    if not isinstance(before, dict) or key not in before:
        return None
    expected = {k: v for k, v in before.items() if k != key}
    # A file already in a canonical json.dumps shape is rewritten in that
    # same shape -- the line surgery below cannot reach a key sharing its
    # line with a brace.
    tail = text[len(text.rstrip('\n')):]
    for fmt in ({'indent': 2, 'ensure_ascii': False}, {}):
        if json.dumps(before, **fmt) == text.rstrip('\n'):
            return json.dumps(expected, **fmt) + tail
    lines = text.splitlines(keepends=True)
    pat = re.compile(r'^\s*"' + re.escape(key) + r'"\s*:\s*[^{\[]*?,?\s*$')
    hits = [i for i, ln in enumerate(lines) if pat.match(ln)]
    if len(hits) != 1:
        return None
    i = hits[0]
    had_comma = lines[i].rstrip().endswith(',')
    del lines[i]
    if not had_comma:
        # It was the last member: the one before it loses its comma.
        for j in range(i - 1, -1, -1):
            if lines[j].strip():
                lines[j] = re.sub(r',(\s*)$', r'\1', lines[j])
                break
    out = ''.join(lines)
    try:
        after = json.loads(out)
    except ValueError:
        return None
    return out if after == expected else None


def _remove_retired_config_fields(dest_root):
    """Delete RETIRED_CONFIG_FIELDS from precedent.json / identity.json.
    -> [(file, field)] removed."""
    removed = []
    for name in _CONFIG_FILES:
        f = dest_root / name
        if not f.is_file():
            continue
        text = f.read_text(encoding='utf-8')
        for field, why in RETIRED_CONFIG_FIELDS.items():
            try:
                present = field in (json.loads(text) or {})
            except (ValueError, TypeError):
                present = False
            if not present:
                continue
            new = _without_json_key(text, field)
            if new is None:
                _left(f'{name}: {field}', f'{why}. Could not be removed '
                      'without reformatting the file -- delete the field by '
                      'hand')
                continue
            text = new
            f.write_text(text, encoding='utf-8')
            removed.append((name, field))
            print(f"precedent_vendor_engine refresh: removed `{field}` from "
                  f"{name} -- {why}.")
    return removed


def stale_source_paths(dest_root):
    """-> [(name, path, why)] for a declared source whose clone path does not
    carry its current name. The practice sets were renamed
    precedent-team-* -> precedent-shared-*; two measured installs still
    declared the old paths, and one the old names too. GitHub redirects a
    renamed repository indefinitely, so the only symptom is a second clone of
    the same set, or no clone at all where nothing clones it."""
    try:
        cfg = json.loads((dest_root / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    sources = cfg.get('sources') if isinstance(cfg, dict) else None
    if isinstance(sources, dict):
        sources = list(sources.values())
    out = []
    for s in sources or []:
        if not isinstance(s, dict):
            continue
        name, path = str(s.get('name') or ''), str(s.get('path') or '')
        if not path.startswith('../'):
            continue
        base = pathlib.PurePosixPath(path).name
        if name.startswith('precedent-team-') or base.startswith('precedent-team-'):
            out.append((name, path, 'names a precedent-team-* set, renamed '
                        'precedent-shared-*'))
        elif base != name:
            out.append((name, path, f'the path is {base!r} but the source is '
                        f'{name!r}'))
    return out


_IDENTITY_RE = re.compile(
    r'git\s+config\s+(?:--(?:global|local)\s+)?user\.(?:name|email)\s+'
    r'["\']?[^"\'$\s-]')


def hardcoded_identities(dest_root):
    """-> ['path:line'] where a tracked wiring file sets a literal git
    identity. A shared template must never name a person
    (no-hardcoded-git-identity); commit-identity.sh resolves whoever is
    running the session. Four of five measured installs carried an old
    tools/bootstrap.sh doing exactly this."""
    hits = []
    for rel in ('tools/bootstrap.sh', '.claude/settings.json'):
        try:
            lines = (dest_root / rel).read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for n, ln in enumerate(lines, 1):
            s = ln.strip()
            if s.startswith('#') or s.startswith('echo') or 'echo ' in s:
                continue
            if _IDENTITY_RE.search(s):
                hits.append(f'{rel}:{n}')
    return hits


def _orphaned_secrets(dest_root, deleted_texts):
    """Secrets a just-deleted legacy workflow read that no remaining workflow
    reads, plus the known legacy names when nothing reads them. Only the
    person can delete a repository secret, and a credential with no reader
    is a live key nobody is watching."""
    remaining = set()
    wf = dest_root / '.github' / 'workflows'
    if wf.is_dir():
        for p in wf.iterdir():
            if p.suffix in ('.yml', '.yaml') and p.is_file():
                remaining |= set(_SECRET_RE.findall(
                    p.read_text(encoding='utf-8', errors='ignore')))
    read_before = set()
    for text in deleted_texts.values():
        read_before |= set(_SECRET_RE.findall(text))
    orphaned = (read_before - remaining) - {'GITHUB_TOKEN'}
    if deleted_texts:
        orphaned |= set(LEGACY_SECRETS) - remaining
    return sorted(orphaned)


def retire_legacy_leftovers(dest_root, manifest, kind):
    """Run every legacy sweep; called at the top of refresh(), after
    _remove_retired_ci_workflow_files (which clears a hand-paused tracked
    entry first, so the untracked sweep then sees it). -> {'deleted': [...],
    'secrets': [...]}. Everything it declined lands in _LEFT_FOR_YOU."""
    pd = _decommission_module()
    deleted_wf, _kept = _retire_legacy_workflows(dest_root, manifest, kind, pd)
    deleted_hooks = _retire_legacy_hooks(dest_root, manifest, pd)
    _remove_retired_config_fields(dest_root)
    for name, path, why in stale_source_paths(dest_root):
        _left(f'precedent.json source {name!r} at {path}',
              f'{why} -- repoint it to the current name (vendor-update-runbook, '
              f'"Retire legacy leftovers")')
    # A fallback branch is not exempt, and the message says so, because the
    # first session to see this on a diverged bootstrap.sh read "only runs
    # when the individual source is missing" as a reason to keep it.
    # Measured 2026-09-25 on a scratch consumer with no individual source:
    # commit-identity.sh set the right author from the environment override
    # or the authenticated GitHub account; with neither, its backstop
    # refused the bot-authored commit; and under a second person's declared
    # identity the fallback overwrote theirs with the named one
    # (practice: vendor-update-runbook, step 10(d)).
    for where in hardcoded_identities(dest_root):
        _left(where, 'sets a literal git identity; delete it, even in a '
                     'fallback branch, keeping the rest of the file -- '
                     'commit-identity.sh resolves who is committing, and a '
                     'name written here credits anyone else to that person')
    secrets = _orphaned_secrets(dest_root, deleted_wf)
    for s in secrets:
        _left(f'secret {s}', 'no remaining workflow reads it -- if it is set '
                             'on this repository, only you can delete it '
                             '(Settings -> Secrets and variables -> Actions)')
    return {'deleted': sorted(deleted_wf) + [f'{HOOK_DEST_DIR}/{n}'
                                             for n in deleted_hooks],
            'secrets': secrets}


def print_left_for_you():
    """The closing list: what this refresh would not do by itself. Printed
    even when the refresh had nothing else to do, because that is the run a
    session reads as "all clean"."""
    if not _LEFT_FOR_YOU:
        return
    print("\nLeft for you -- this refresh would not do these by itself "
          "(vendor-update-runbook, \"Retire legacy leftovers\"):")
    seen = set()
    for item, why in _LEFT_FOR_YOU:
        if (item, why) in seen:
            continue
        seen.add((item, why))
        print(f"  - {item}: {why}")
    _LEFT_FOR_YOU.clear()


def _ci_workflow_incomplete(dest_root, kind, ci_workflows_dir, manifest):
    """-> [rel, ...] every CI workflow file refresh() actually has safe
    work to do for right now: present on disk, its template fetched for the
    commit being vendored, and EITHER not yet recorded in the manifest at
    all (a catch-up baseline to write) OR recorded, unchanged since, and
    different from the current template.

    Used only to decide refresh()'s early-exit ("already current -- nothing
    to do"). A hand-edited file (recorded, but no longer matching) is
    deliberately excluded: reaching this function at all means the upfront
    _ci_workflow_drift refusal already let this run proceed, which happens
    only when there was no such mismatch, or --force overrode it -- and
    --force alone is why refresh() never reaches its early exit at all (see
    the `not force` in that check)."""
    recorded = manifest.get('ci_workflows_sha256') or {}
    out = []
    for template, rel in CI_WORKFLOW_TEMPLATES.get(kind, ()):
        path = dest_root / rel
        if not path.is_file():
            continue
        src = ci_workflows_dir / template
        if not src.is_file():
            continue
        if rel not in recorded:
            out.append(rel)
            continue
        if _sha256(path) == recorded[rel] and _sha256(path) != _sha256(src):
            out.append(rel)
    return out


def _refresh_ci_workflow_files(dest_root, kind, ci_workflows_dir, manifest):
    """Bring each installed CI workflow file that is safe to touch up to
    the current template, and read-modify-write ENGINE_MANIFEST.json's
    ci_workflow_files/ci_workflows_sha256 -- same shape as
    _write_hook_files, run strictly AFTER _write_engine_files (and
    _write_hook_files, when it ran), whose own manifest write knows nothing
    about these keys and would otherwise silently drop them.

    `manifest` is the manifest as loaded BEFORE this refresh -- the same
    one refresh() already keeps for _remove_dropped_engine_files -- and the
    one whose ci_workflows_sha256 is being compared against.

    Per file: not on disk (ci_workflows disabled, or genuinely absent) ->
    left alone. Not yet recorded -> baseline recorded, content UNTOUCHED
    (see CI_WORKFLOW_TEMPLATES' catch-up note above). Recorded, and its
    on-disk hash differs from the CURRENT template -> rewritten to that
    template, hash updated. This one rule covers both an ordinary refresh
    (where, by the time this runs, an on-disk mismatch against the recorded
    hash can only mean --force accepted a hand-edit, since the upfront
    drift check already refused otherwise) and --force overwriting a
    hand-edited file outright, the same way --force already treats every
    other drifted file in this tool.

    Returns (refreshed, catchup): rel paths rewritten to the current
    template, and rel paths whose hash was recorded for the first time."""
    if not any((dest_root / rel).is_file()
               for _t, rel in CI_WORKFLOW_TEMPLATES.get(kind, ())):
        return [], []
    recorded = dict(manifest.get('ci_workflows_sha256') or {})
    _local = local_ci_workflows(dest_root)
    refreshed, catchup = [], []
    for template, rel in CI_WORKFLOW_TEMPLATES.get(kind, ()):
        # DECLARED LOCAL: not written, and its recorded hash is DROPPED
        # rather than updated. Leaving a hash behind would re-arm the
        # refusal the declaration exists to retire; updating one would
        # quietly bless whatever the file says today, which is exactly what
        # `record-ci` does and exactly why it is not an escape.
        if rel in _local:
            recorded.pop(rel, None)
            continue
        path = dest_root / rel
        if not path.is_file():
            continue
        src = ci_workflows_dir / template
        if not src.is_file():
            continue                  # this commit predates the template
        template_hash = _sha256(src)
        if rel not in recorded:
            recorded[rel] = _sha256(path)
            catchup.append(rel)
            continue
        if _sha256(path) != template_hash:
            shutil.copy2(src, path)
            recorded[rel] = template_hash
            refreshed.append(rel)
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    live = json.loads(manifest_path.read_text(encoding='utf-8'))
    live['ci_workflow_files'] = sorted(recorded)
    live['ci_workflows_sha256'] = recorded
    manifest_path.write_text(json.dumps(live, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return refreshed, catchup


# --- Repo-owned files instantiated from a template: tools/bootstrap.sh -----
# The third mechanism of the same family as the hooks and CI workflows
# above, added 2026-09-25, and the only one of the three that NEVER
# overwrites a file carrying local edits, --force included.
#
# THE GAP. precedent_install.py copies templates/bootstrap.sh to a
# consumer's tools/bootstrap.sh once, verbatim, and until this block nothing
# ever looked at it again: this module's own docstring called it repo-owned,
# so refresh left it alone and nothing compared it to the template. Measured
# 2026-09-25 in a real consumer taking an update: its bootstrap.sh was the
# template minus the two blocks added around 2026-09-23 (the practice_audit
# `--loader-notice` call and `precedent_engine_freshness.py --quiet`), so
# the session-start freshness check that
# todo/todo-2026-09-21-nothing-checks-a-consumer-against-upstream.md
# describes as running "for every consumer" had never once run there. The
# fix that came in the same update only arrived because a session copied it
# by hand. Reproduced on a scratch consumer holding the pre-2026-09-23
# template: `refresh` said "already current -- nothing to do" and `status`
# said nothing at all.
#
# WHY IT NEVER OVERWRITES AN EDITED COPY, unlike the CI workflows. The
# template tells every repo to add entries to this file ("every entry here
# should exist because its absence cost a real session"), so local lines
# are the file working as designed, not drift to refuse or discard. An
# edited copy is reported DIVERGED, with the template blocks it lacks named
# by line, and the refresh carries on.
#
# WHAT COUNTS AS UNEDITED. Either the manifest recorded a hash for it and
# the file still matches, or -- the catch-up for every install that predates
# this block, which recorded nothing -- the file is byte-identical to SOME
# past version of the template in the upstream clone's history. Either way
# it is stock content nobody touched, so it is rewritten to the current
# template. Anything else is diverged. A shallow upstream clone can hide the
# matching past version; that errs toward DIVERGED, the side that loses
# nothing.
TEMPLATE_INSTANCES = {
    'consumer': (('templates/bootstrap.sh', 'tools/bootstrap.sh'),),
    # A practice set has no tools/bootstrap.sh; precedent_bootstrap_source.py
    # never writes one.
    'source': (),
}
TEMPLATE_INSTANCES_KEY = 'template_instances_sha256'
_TEMPLATE_HISTORY_NAME = 'template-history.json'
# Closers and keywords that appear in every block, so their presence says
# nothing about whether a particular block is there.
_TRIVIAL_SHELL_LINES = {'fi', 'else', 'then', 'do', 'done', '}', 'esac', ';;'}


def _git_blob_id(data):
    """The id git gives these bytes as a blob -- so an on-disk file can be
    looked up among a path's historical blobs without a repository."""
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def _read_template_sources(clone, commit, kind, out_dir):
    """Write this kind's TEMPLATE_INSTANCES sources at `commit` into
    out_dir/<src_rel>, and every blob id each one has had in the history
    reachable from `commit` into out_dir/template-history.json. Read-only
    against `clone`, like the rest of _source_tools_at. A template this
    commit lacks is skipped: nothing to compare against, nothing done."""
    history = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    for src_rel, _rel in TEMPLATE_INSTANCES.get(kind, ()):
        blob = subprocess.run(['git', '-C', str(clone), 'show',
                               f'{commit}:{src_rel}'], capture_output=True)
        if blob.returncode != 0:
            continue
        out = out_dir / src_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(blob.stdout)
        ok, log = _git_read(clone, 'log', '--format=', '--raw', '--no-abbrev',
                            commit, '--', src_rel)
        blobs = set()
        if ok:
            for line in log.splitlines():
                parts = line.split()
                if line.startswith(':') and len(parts) >= 4:
                    blobs.add(parts[3])
        history[src_rel] = sorted(blobs)
    (out_dir / _TEMPLATE_HISTORY_NAME).write_text(json.dumps(history),
                                                   encoding='utf-8')


def _shell_blocks(text):
    """-> [(line_no, title, code_lines)] for each blank-line-separated block
    of a shell template that carries code. The title is the block's first
    comment line (its heading, by this template's convention), or its first
    code line when it has none."""
    out, start, cur = [], 0, []
    for n, line in enumerate(text.splitlines() + [''], 1):
        if line.strip():
            if not cur:
                start = n
            cur.append(line.strip())
            continue
        if cur:
            comments = [c.lstrip('#').strip() for c in cur if c.startswith('#')]
            code = [c for c in cur
                    if not c.startswith('#') and c not in _TRIVIAL_SHELL_LINES]
            if code:
                title = next((c for c in comments if c and not c.startswith('!')),
                             code[0])
                if len(title) > 72:
                    title = title[:69].rstrip() + '...'
                out.append((start, title, code))
            cur = []
    return out


def missing_template_blocks(local_text, template_text):
    """-> [(line_no, title, how)] for each template block whose code is not
    all present in `local_text`: 'missing' when none of it is, else how many
    of its lines are absent. Compared line by line after stripping, so local
    re-indentation or local lines added around a block do not count
    against it."""
    have = {ln.strip() for ln in local_text.splitlines()}
    out = []
    for line_no, title, code in _shell_blocks(template_text):
        absent = [c for c in code if c not in have]
        if not absent:
            continue
        how = ('missing' if len(absent) == len(code)
               else f'{len(absent)} of its {len(code)} lines absent or changed')
        out.append((line_no, title, how))
    return out


def _template_instance_plan(dest_root, kind, templates_dir, manifest):
    """-> [(src_rel, rel, action)], one per TEMPLATE_INSTANCES entry whose
    template `templates_dir` holds. Actions:

      'absent'   -- not on disk. Never recreated: a repo that deleted its
                    bootstrap.sh decided something.
      'current'  -- byte-identical to the template.
      'refresh'  -- matches the recorded hash (unedited), template moved.
      'adopt'    -- nothing recorded, but identical to a past version of
                    the template (unedited, predates tracking).
      'diverged' -- carries local edits. Reported, never written."""
    recorded = manifest.get(TEMPLATE_INSTANCES_KEY) or {}
    try:
        history = json.loads((templates_dir / _TEMPLATE_HISTORY_NAME)
                             .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        history = {}
    plan = []
    for src_rel, rel in TEMPLATE_INSTANCES.get(kind, ()):
        src = templates_dir / src_rel
        if not src.is_file():
            continue
        path = dest_root / rel
        if not path.is_file():
            plan.append((src_rel, rel, 'absent'))
            continue
        on_disk = _sha256(path)
        if on_disk == _sha256(src):
            action = 'current'
        elif rel in recorded:
            action = 'refresh' if on_disk == recorded[rel] else 'diverged'
        elif _git_blob_id(path.read_bytes()) in set(history.get(src_rel) or ()):
            action = 'adopt'
        else:
            action = 'diverged'
        plan.append((src_rel, rel, action))
    return plan


def _template_instances_pending(plan, manifest):
    """True when applying `plan` would change a file or the manifest -- what
    refresh()'s early exit has to ask, like ci_incomplete."""
    recorded = manifest.get(TEMPLATE_INSTANCES_KEY) or {}
    return any(action in ('refresh', 'adopt')
               or (action == 'current' and rel not in recorded)
               or (action == 'absent' and rel in recorded)
               for _s, rel, action in plan)


def _report_diverged_template_instances(dest_root, templates_dir, plan):
    """Print, for every diverged instance, which template blocks it lacks,
    and put it on the Left-for-you list when it lacks any. Every run, the
    early exit included: a divergence that is only said once stops being
    seen."""
    for src_rel, rel, action in plan:
        if action != 'diverged':
            continue
        lacks = missing_template_blocks(
            (dest_root / rel).read_text(encoding='utf-8', errors='replace'),
            (templates_dir / src_rel).read_text(encoding='utf-8'))
        if not lacks:
            print(f"DIVERGED: {rel} has local edits and carries every block "
                  f"of upstream's {src_rel} -- left as it is, nothing to "
                  f"copy in.")
            continue
        print(f"DIVERGED: {rel} has local edits, so refresh leaves it "
              f"alone (it never overwrites a line of it, --force included). "
              f"It lacks {len(lacks)} block(s) upstream's {src_rel} carries:")
        for line_no, title, how in lacks:
            print(f"    {src_rel}:{line_no} \"{title}\" -- {how}")
        _left(rel, f'diverged from {src_rel} and lacks {len(lacks)} of its '
                   f'blocks (listed above) -- copy each in from the template '
                   f'by hand, keeping this repo\'s own lines '
                   f'(vendor-update-runbook step 10(d))')


def _refresh_template_instances(dest_root, kind, templates_dir, manifest, plan):
    """Apply `plan`: rewrite each 'refresh'/'adopt' instance to the current
    template, and read-modify-write ENGINE_MANIFEST.json's
    TEMPLATE_INSTANCES_KEY -- AFTER _write_engine_files, whose fresh manifest
    knows nothing about this key, from `manifest` as it was before the
    refresh. A diverged instance keeps whatever was recorded for it: a
    baseline is never moved onto an edited file, or the next refresh would
    take the edit for stock content and overwrite it.

    Returns the rel paths rewritten."""
    recorded = dict(manifest.get(TEMPLATE_INSTANCES_KEY) or {})
    rewritten = []
    for src_rel, rel, action in plan:
        src = templates_dir / src_rel
        if action in ('refresh', 'adopt'):
            path = dest_root / rel
            shutil.copyfile(src, path)
            path.chmod(0o755)
            rewritten.append(rel)
        if action in ('refresh', 'adopt', 'current'):
            recorded[rel] = _sha256(src)
        elif action == 'absent' and recorded.pop(rel, None):
            print(f"NOTE: precedent_vendor_engine refresh: {rel} is gone from "
                  f"disk -- no longer tracked, and not recreated.")
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    live = json.loads(manifest_path.read_text(encoding='utf-8'))
    if recorded:
        live[TEMPLATE_INSTANCES_KEY] = recorded
    else:
        live.pop(TEMPLATE_INSTANCES_KEY, None)
    manifest_path.write_text(json.dumps(live, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return rewritten


def record_template_instances(dest_root, kind, source_root):
    """Record a baseline for each template instance an installer just wrote,
    when it is byte-identical to `source_root`'s template -- called by
    precedent_install.py after seed(), for the same reason
    record_ci_workflow_files is. One that differs is left unrecorded: the
    next refresh decides from history whether it is stock or edited."""
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    if not manifest_path.is_file():
        return []
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    recorded = dict(manifest.get(TEMPLATE_INSTANCES_KEY) or {})
    for src_rel, rel in TEMPLATE_INSTANCES.get(kind, ()):
        src, path = source_root / src_rel, dest_root / rel
        if src.is_file() and path.is_file() and _sha256(src) == _sha256(path):
            recorded[rel] = _sha256(path)
    if recorded:
        manifest[TEMPLATE_INSTANCES_KEY] = recorded
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return [manifest_path]


# --- AGENTS.md's template-written sections ----------------------------------
# The same gap as TEMPLATE_INSTANCES above, one file over, closed the same
# way on 2026-09-25. precedent_install.py writes AGENTS.md from
# templates/AGENTS.md.loader.template once, and from then on the only part
# of it anything rewrites is the generated loader block, which
# precedent_sync_views.py owns. Every other section the template wrote --
# "### Session start", "### Two check levels", "## Git / workflow" and the
# rest -- was frozen at install, so no fix to the template ever reached an
# installed repo, and nothing said so. Measured the same day in a real
# consumer: the template's session-start bullet told a session to attach the
# individual practice set but not where its clone lives, the attach tool
# said /home/user/<name>, the session-start hook had already cloned it to
# ~/precedent-individual (the only copy anything reads), and within the
# hour the two copies had diverged. The consumer fixed its own copy by hand;
# no template fix could have reached it.
#
# THE UNIT IS A SECTION, NOT THE FILE. AGENTS.md is the one file every repo
# is told to fill in, so the file as a whole is always edited; comparing it
# whole would call every install diverged and deliver nothing. A section is
# a `##` or `###` heading and everything up to the next one (or the
# generated block's marker), keyed by the heading line. A template heading
# that is itself a placeholder (`## <Deliverable build workflow>`) is the
# repo's to name and is never tracked; its fixed-heading subsections are.
#
# WHAT HAPPENS TO EACH, per refresh -- never a local edit overwritten:
#   current  -- already the template's text (placeholders substituted the
#               way install substitutes them). Recorded.
#   refresh  -- matches the hash recorded for it, so nobody edited it, and
#               the template moved. Rewritten; the new text recorded.
#   adopt    -- nothing recorded (every install before this date), but
#               identical to the section in SOME past version of either
#               AGENTS.md template. Stock, so rewritten and recorded -- the
#               one-time catch-up.
#   diverged -- anything else. Left alone, --force included, and reported
#               with every block (bullet, paragraph, table row) of the
#               current template's section it lacks, down to the sentences
#               where it has part of one. On the Left-for-you list.
#   missing  -- the template has the section, this AGENTS.md does not, and
#               no refresh has seen that before. Reported and put on the
#               list, never written in: where it belongs in a file this
#               repo has rearranged is a judgment. Recorded as absent, so
#               the next refresh says it in one line rather than again in
#               full -- a section a repo chose not to have is a decision.
#   absent   -- that, on a later refresh.
# A heading that appears twice in AGENTS.md is diverged: no write can know
# which of the two was meant.
AGENTS_MD = 'AGENTS.md'
AGENTS_MD_TEMPLATES = {
    # First is the template a refresh writes from. The classic one is
    # history only: a repo migrated onto the loader may still carry a
    # section exactly as the classic template wrote it, which is stock too.
    'consumer': ('templates/AGENTS.md.loader.template',
                 'templates/AGENTS.md.template'),
    'source': (),
}
AGENTS_MD_SECTIONS_KEY = 'agents_md_sections_sha256'
_AGENTS_MD_HISTORY_NAME = 'agents-md-history.json'
_GENERATED_BEGIN = '<!-- BEGIN GENERATED'
_GENERATED_END = '<!-- END GENERATED'
_MD_HEADING_RE = re.compile(r'^(#{1,3})\s+\S')
_MD_PLACEHOLDER_RE = re.compile(r'<[A-Za-z][^<>\n]{0,70}>')
_MD_ITEM_RE = re.compile(r'^\s*(?:[-*+]|\d+\.)\s')
# A block whose own words, placeholders aside, are fewer than this is an
# example row for the repo to replace ("| <key deliverable> and its
# builder | `<path>` |"), not text it can be said to lack.
_MIN_LITERAL_WORDS = 4


def _agents_md_subs(dest_root):
    """The substitutions precedent_install.py makes in AGENTS.md, as far as
    any section can carry them: `<default-branch>` from precedent.json's
    base_branch, and the upstream URL. The rest of install's map never
    appears in this template, and a template placeholder not listed here
    stays for the person to fill in, as install leaves it."""
    try:
        branch = json.loads((dest_root / 'precedent.json')
                            .read_text(encoding='utf-8')).get('base_branch')
    except (OSError, ValueError):
        branch = None
    return {'<precedent upstream URL>': SOURCE_REPO,
            '<default-branch>': branch if isinstance(branch, str) and branch.strip()
            else 'main'}


def _instantiate(text, subs):
    for old, new in subs.items():
        text = text.replace(old, new)
    return text


def _md_sections(text):
    """-> [(key, first, end)] for each `##`/`###` section of a markdown
    file, as 0-based line indexes into text.split('\\n'), `end` exclusive
    and short of any trailing blank lines. Headings inside a fenced block,
    an HTML comment or the generated loader block do not count; the
    generated block and a `#` heading both end the section before them."""
    lines = text.split('\n')
    out, cur = [], None
    fence = comment = generated = False

    def close(end):
        if cur is None:
            return
        while end > cur[1] + 1 and not lines[end - 1].strip():
            end -= 1
        out.append((cur[0], cur[1], end))

    for i, line in enumerate(lines):
        s = line.strip()
        if generated:
            if s.startswith(_GENERATED_END):
                generated = False
            continue
        if s.startswith(_GENERATED_BEGIN):
            close(i)
            cur, generated = None, True
            continue
        if comment:
            if '-->' in s:
                comment = False
            continue
        if s.startswith('```') or s.startswith('~~~'):
            fence = not fence
            continue
        if fence:
            continue
        if s.startswith('<!--') and '-->' not in s[4:]:
            comment = True
            continue
        m = _MD_HEADING_RE.match(line)
        if m:
            close(i)
            cur = (line.rstrip(), i) if len(m.group(1)) > 1 else None
    close(len(lines))
    return out


def _section_text(lines, first, end):
    return '\n'.join(ln.rstrip() for ln in lines[first:end])


def _template_sections(text):
    """-> {key: (line_no, raw_text)} for every trackable section of a
    template: fixed heading, first occurrence."""
    lines = text.split('\n')
    out = {}
    for key, first, end in _md_sections(text):
        if _MD_PLACEHOLDER_RE.search(key) or key in out:
            continue
        out[key] = (first + 1, _section_text(lines, first, end))
    return out


def _sha_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _read_agents_md_sources(clone, commit, kind, out_dir):
    """Write the current AGENTS.md template at `commit` into
    out_dir/<its path>, and every section text either template has ever
    carried, keyed by heading, into out_dir/agents-md-history.json -- the
    catch-up's evidence of what stock looked like. Read-only against
    `clone`. `--follow`, because the classic template began as
    templates/CLAUDE.md.template."""
    history = {}
    for n, src_rel in enumerate(AGENTS_MD_TEMPLATES.get(kind, ())):
        if n == 0:
            blob = subprocess.run(['git', '-C', str(clone), 'show',
                                   f'{commit}:{src_rel}'], capture_output=True)
            if blob.returncode == 0:
                out = out_dir / src_rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(blob.stdout)
        ok, log = _git_read(clone, 'log', '--follow', '--format=@%H',
                            '--name-only', commit, '--', src_rel)
        if not ok:
            continue
        sha = None
        for line in log.splitlines():
            line = line.strip()
            if line.startswith('@'):
                sha = line[1:]
            elif line and sha:
                old = subprocess.run(['git', '-C', str(clone), 'show',
                                      f'{sha}:{line}'], capture_output=True)
                if old.returncode != 0:
                    continue
                text = old.stdout.decode('utf-8', errors='replace')
                for key, (_n, sec) in _template_sections(text).items():
                    seen = history.setdefault(key, [])
                    if sec not in seen:
                        seen.append(sec)
    (out_dir / _AGENTS_MD_HISTORY_NAME).write_text(json.dumps(history),
                                                   encoding='utf-8')


def _agents_md_plan(dest_root, kind, templates_dir, manifest):
    """-> [(key, src_rel, line_no, action, span)], one per trackable section
    of the current template, in template order -- see the block comment
    above for the actions. `span` is (first, end) in AGENTS.md, or None.
    Empty when there is no AGENTS.md or no template to compare with."""
    srcs = AGENTS_MD_TEMPLATES.get(kind, ())
    path = dest_root / AGENTS_MD
    if not srcs or not (templates_dir / srcs[0]).is_file() or not path.is_file():
        return []
    subs = _agents_md_subs(dest_root)
    template = _template_sections((templates_dir / srcs[0]).read_text(encoding='utf-8'))
    try:
        history = json.loads((templates_dir / _AGENTS_MD_HISTORY_NAME)
                             .read_text(encoding='utf-8'))
    except (OSError, ValueError):
        history = {}
    recorded = manifest.get(AGENTS_MD_SECTIONS_KEY) or {}
    local = path.read_text(encoding='utf-8')
    lines = local.split('\n')
    spans = collections.defaultdict(list)
    for key, first, end in _md_sections(local):
        spans[key].append((first, end))
    plan = []
    for key, (line_no, raw) in template.items():
        found = spans.get(key) or []
        if not found:
            plan.append((key, srcs[0], line_no,
                         'absent' if key in recorded else 'missing', None))
            continue
        if len(found) > 1:
            plan.append((key, srcs[0], line_no, 'diverged', None))
            continue
        span = found[0]
        text = _section_text(lines, *span)
        if text == _instantiate(raw, subs):
            action = 'current'
        elif recorded.get(key):
            action = 'refresh' if _sha_text(text) == recorded[key] else 'diverged'
        elif any(text in (past, _instantiate(past, subs))
                 for past in history.get(key) or ()):
            action = 'adopt'
        else:
            action = 'diverged'
        plan.append((key, srcs[0], line_no, action, span))
    return plan


def _agents_md_pending(plan, manifest):
    """True when applying `plan` would change AGENTS.md or the manifest."""
    recorded = manifest.get(AGENTS_MD_SECTIONS_KEY) or {}
    for key, _s, _n, action, _span in plan:
        if action in ('refresh', 'adopt', 'missing'):
            return True
        if action == 'current' and not recorded.get(key):
            return True
        if action == 'absent' and recorded.get(key) is not None:
            return True
    return False


def _md_blocks(section_text):
    """-> [(offset, text)] for each block of a section body: a list item, a
    table row, a fenced block or a paragraph, whitespace-collapsed, `offset`
    its first line's index within the section. HTML comments and the
    heading are skipped: a comment is guidance to whoever fills the
    template in, and a repo deleting it has lost nothing."""
    lines = section_text.split('\n')
    out, cur, start = [], [], 0
    comment = fence = False

    def flush():
        if cur:
            out.append((start, ' '.join(' '.join(cur).split())))
        cur.clear()

    for i, line in enumerate(lines[1:], 1):
        s = line.strip()
        if comment:
            if '-->' in s:
                comment = False
            continue
        if fence:
            cur.append(s)
            if s.startswith('```') or s.startswith('~~~'):
                fence = False
                flush()
            continue
        if s.startswith('<!--'):
            flush()
            comment = '-->' not in s[4:]
            continue
        if s.startswith('```') or s.startswith('~~~'):
            flush()
            start, fence = i, True
            cur.append(s)
            continue
        if not s:
            flush()
            continue
        if s.startswith('|'):
            flush()
            if not re.fullmatch(r'[|:\-\s]+', s):
                out.append((i, s))
            continue
        if _MD_ITEM_RE.match(line) or not cur:
            flush()
            start = i
        cur.append(s)
    flush()
    return out


def _sentences(text):
    """Split whitespace-collapsed text after `.`, `!` or `?` and a space --
    never inside a `code span`, where `--repo .` is not a sentence end."""
    out, cur, code = [], [], False
    for i, ch in enumerate(text):
        cur.append(ch)
        if ch == '`':
            code = not code
        elif ch == ' ' and not code and i and text[i - 1] in '.!?':
            out.append(''.join(cur).strip())
            cur = []
    if ''.join(cur).strip():
        out.append(''.join(cur).strip())
    return out


def _wildcard(text):
    """A regex for `text` in which each remaining template placeholder
    matches whatever a repo filled it in with -- or None when the text
    carries too few words of its own to be lacked (_MIN_LITERAL_WORDS)."""
    pieces = _MD_PLACEHOLDER_RE.split(text)
    if len(re.findall(r'[A-Za-z]{2,}', ' '.join(pieces))) < _MIN_LITERAL_WORDS:
        return None
    return re.compile('.+?'.join(re.escape(p) for p in pieces))


def missing_markdown_blocks(local_section, template_section):
    """-> [(offset, title, how, absent_sentences)] for each block of
    `template_section` that `local_section` does not carry. Compared on
    whitespace-collapsed text, so rewrapping and local lines added around a
    block never count against it; a placeholder the repo filled in matches
    whatever it was filled with. `how` is 'missing' when not one of the
    block's sentences is there, else how many are absent or changed."""
    have_lines = [ln for ln in local_section.split('\n')[1:]]
    have = ' '.join(' '.join(have_lines).split())
    out = []
    for offset, block in _md_blocks(template_section):
        whole = _wildcard(block)
        if whole is None or whole.search(have):
            continue
        sentences = _sentences(block)
        absent = []
        for s in sentences:
            rx = _wildcard(s)
            if rx is not None and not rx.search(have):
                absent.append(s)
        if not absent:
            # Every sentence is there, just not as one run -- reordered or
            # split by a local line. Nothing to copy in.
            continue
        title = block if len(block) <= 72 else block[:69].rstrip() + '...'
        how = ('missing' if len(absent) == len(sentences)
               else f'{len(absent)} of its {len(sentences)} sentences absent or changed')
        out.append((offset, title, how, absent if absent != sentences else []))
    return out


def _report_agents_md(dest_root, templates_dir, plan):
    """Print what refresh (or status) found in AGENTS.md's template
    sections, and put what needs a person on the Left-for-you list. Every
    run, the early exit included, for the reason
    _report_diverged_template_instances gives."""
    if not plan:
        return
    subs = _agents_md_subs(dest_root)
    lines = (dest_root / AGENTS_MD).read_text(encoding='utf-8').split('\n')
    template_text = None
    complete = []
    for key, src_rel, line_no, action, span in plan:
        if action == 'missing':
            print(f"MISSING: {AGENTS_MD} has no \"{key}\" section; upstream's "
                  f"{src_rel}:{line_no} has one. Not written in: where it goes "
                  f"in this file is a judgment. The next refresh says this in "
                  f"one line.")
            _left(f'{AGENTS_MD} "{key}"', f'the template has this section and '
                  f'this file does not -- copy it in from {src_rel}:{line_no} '
                  f'if it applies here, or leave it out on purpose '
                  f'(vendor-update-runbook step 10(d))')
            continue
        if action == 'absent':
            print(f"  NOTE: {AGENTS_MD} still has no \"{key}\" section "
                  f"({src_rel}:{line_no}) -- left out, as at the last refresh.")
            continue
        if action != 'diverged':
            continue
        if span is None:
            print(f"DIVERGED: {AGENTS_MD} has \"{key}\" more than once, so "
                  f"refresh cannot tell which is the template's and leaves "
                  f"both alone. Merge them into one.")
            _left(f'{AGENTS_MD} "{key}"', 'appears more than once -- merge '
                  'them, then refresh again')
            continue
        if template_text is None:
            template_text = _template_sections(
                (templates_dir / src_rel).read_text(encoding='utf-8'))
        t_line, raw = template_text[key]
        lacks = missing_markdown_blocks(_section_text(lines, *span),
                                        _instantiate(raw, subs))
        if not lacks:
            complete.append(key)
            continue
        print(f"DIVERGED: {AGENTS_MD} \"{key}\" (line {span[0] + 1}) has local "
              f"edits, so refresh leaves it alone (it never overwrites a line "
              f"of it, --force included). It lacks {len(lacks)} block(s) the "
              f"current template's section carries:")
        for offset, title, how, absent in lacks:
            print(f"    {src_rel}:{t_line + offset} \"{title}\" -- {how}")
            for s in absent:
                print(f"        lacks: \"{s if len(s) <= 160 else s[:157] + '...'}\"")
        _left(f'{AGENTS_MD} "{key}"', f'diverged from {src_rel} and lacks '
              f'{len(lacks)} of its blocks (listed above) -- copy each in by '
              f'hand, keeping this repo\'s own text (vendor-update-runbook '
              f'step 10(d))')
    if complete:
        print(f"DIVERGED, nothing to copy in: {AGENTS_MD} "
              f"{', '.join(repr(k) for k in complete)} carr"
              f"{'ies' if len(complete) == 1 else 'y'} local edits and every "
              f"block of the template's version -- left as they are.")


def _refresh_agents_md(dest_root, templates_dir, manifest, plan):
    """Apply `plan`: rewrite each 'refresh'/'adopt' section to the current
    template, bottom-up so earlier spans stay valid, and read-modify-write
    ENGINE_MANIFEST.json's AGENTS_MD_SECTIONS_KEY -- after
    _write_engine_files, like _refresh_template_instances, and for the
    same reason a diverged section keeps whatever was recorded for it.

    Returns the section keys rewritten. With no plan (no AGENTS.md, or a
    ref whose template is gone) what was recorded is carried over as it
    was: _write_engine_files has just dropped it, and a baseline lost is
    an unedited section the next refresh can only judge from history."""
    recorded = dict(manifest.get(AGENTS_MD_SECTIONS_KEY) or {})
    rewritten = []
    if plan:
        rewritten = _apply_agents_md_plan(dest_root, templates_dir, plan, recorded)
    if not plan and not recorded:
        return []
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    live = json.loads(manifest_path.read_text(encoding='utf-8'))
    live[AGENTS_MD_SECTIONS_KEY] = recorded
    manifest_path.write_text(json.dumps(live, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return rewritten


def _apply_agents_md_plan(dest_root, templates_dir, plan, recorded):
    """_refresh_agents_md's write to AGENTS.md itself; updates `recorded`
    in place and returns the section keys rewritten, in file order."""
    subs = _agents_md_subs(dest_root)
    path = dest_root / AGENTS_MD
    lines = path.read_text(encoding='utf-8').split('\n')
    template = _template_sections(
        (templates_dir / plan[0][1]).read_text(encoding='utf-8'))
    rewritten = []
    for key, _src, _n, action, span in sorted(
            plan, key=lambda p: p[4][0] if p[4] else -1, reverse=True):
        new = _instantiate(template[key][1], subs)
        if action in ('refresh', 'adopt'):
            lines[span[0]:span[1]] = new.split('\n')
            rewritten.append(key)
        if action in ('refresh', 'adopt', 'current'):
            recorded[key] = _sha_text(new)
        elif action in ('missing', 'absent'):
            recorded[key] = None
    if rewritten:
        path.write_text('\n'.join(lines), encoding='utf-8')
    return list(reversed(rewritten))


def record_agents_md_sections(dest_root, kind, source_root):
    """Record a baseline for each AGENTS.md section an installer just wrote
    from the template -- called by precedent_install.py after seed(), as
    record_template_instances is. A section that already differs (an
    AGENTS.md kept from before the install) is left unrecorded, for the next
    refresh to judge from history."""
    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    srcs = AGENTS_MD_TEMPLATES.get(kind, ())
    if not srcs or not manifest_path.is_file() \
            or not (source_root / srcs[0]).is_file() \
            or not (dest_root / AGENTS_MD).is_file():
        return []
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    recorded = dict(manifest.get(AGENTS_MD_SECTIONS_KEY) or {})
    subs = _agents_md_subs(dest_root)
    template = _template_sections((source_root / srcs[0]).read_text(encoding='utf-8'))
    local = (dest_root / AGENTS_MD).read_text(encoding='utf-8')
    lines = local.split('\n')
    for key, first, end in _md_sections(local):
        if key in template and _section_text(lines, first, end) == \
                _instantiate(template[key][1], subs):
            recorded[key] = _sha_text(_section_text(lines, first, end))
    manifest[AGENTS_MD_SECTIONS_KEY] = recorded
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return [manifest_path]


# --- A renamed branch, still named in a repo's own text --------------------
# 525e90a (2026-09-25) renamed precedent-beta-v01 to staging. The engine's
# own pin moved with the refresh that carried it; the text a repo wrote
# itself did not: a real consumer measured that day named the old branch on
# six lines of AGENTS.md and three of tools/bootstrap.sh, in links, in a
# `git clone --branch` line and in a session-start warning.
#
# TWO WAYS THAT TEXT COULD CATCH UP, and why this is the second. (1) Keep
# the old name as an alias until consumers catch up. It already is one --
# every Promote fast-forwards precedent-beta-v01 to staging -- and that is
# what keeps the stale lines working today. But an alias alone never tells
# anyone the text is stale, so "until consumers catch up" has no event to
# end on, and the alias has to live forever. (2) Report every mention, on
# every refresh and status. That is the half that actually reaches the
# text, and it gives the alias its retirement condition: it goes once no
# consumer's refresh reports one. So both, with the report as the
# mechanism and the alias as the bridge.
#
# What is left out: a line inside the generated block (the next sync
# rewrites it from the catalogue; a hand edit there is refused), and a line
# that also names the new branch, which is recording the rename rather than
# using the old name ("`staging` (named `precedent-beta-v01` until ...)").
#
# The generated block is only cleared by a sync if the catalogue itself is
# clean, and on 2026-09-26 it was not: a shared set's name-the-branch
# index_clause named precedent-beta-v01, so every sync wrote it back into
# the same consumer. precedent_check's retired-branch-name-ships reads this
# table and reports that text in the set that publishes it, which is the
# only place it can be fixed.
RETIRED_BRANCH_NAMES = {
    # old name: (new name, date renamed)
    'precedent-beta-v01': ('staging', '2026-09-25'),
}
RETIRED_NAME_FILES = ('AGENTS.md', 'CLAUDE.md', 'tools/bootstrap.sh')


def retired_branch_mentions(dest_root):
    """-> [(rel, line_no, old, new)] for each line of RETIRED_NAME_FILES
    that names a retired branch -- see the block comment above for what is
    left out."""
    out = []
    for rel in RETIRED_NAME_FILES:
        path = dest_root / rel
        if not path.is_file():
            continue
        generated = False
        for n, line in enumerate(path.read_text(encoding='utf-8', errors='replace')
                                 .splitlines(), 1):
            s = line.strip()
            if s.startswith(_GENERATED_BEGIN):
                generated = True
            elif s.startswith(_GENERATED_END):
                generated = False
                continue
            if generated:
                continue
            for old, (new, _date) in RETIRED_BRANCH_NAMES.items():
                if re.search(rf'(?<![\w-]){re.escape(old)}(?![\w-])', line) \
                        and not re.search(rf'(?<![\w-]){re.escape(new)}(?![\w-])', line):
                    out.append((rel, n, old, new))
    return out


def _report_retired_branch_names(dest_root):
    hits = retired_branch_mentions(dest_root)
    by_old = collections.defaultdict(list)
    for rel, n, old, new in hits:
        by_old[(old, new)].append(f'{rel}:{n}')
    for (old, new), where in by_old.items():
        date = RETIRED_BRANCH_NAMES[old][1]
        print(f"RETIRED BRANCH NAME: {len(where)} line(s) of this repo's own text "
              f"still name {old}, renamed {new} on {date}: {', '.join(where)}. "
              f"The old name still works for now -- upstream keeps it as an "
              f"alias until no refresh reports a mention -- so change each to "
              f"{new} rather than waiting for it to break.")
        _left(f'{len(where)} mention(s) of {old}',
              f'renamed {new} on {date} -- change each line listed above '
              f'(vendor-update-runbook step 10(d))')
    return hits


def _git(cwd, *args):
    """Run git and return stdout, DISCARDING the exit code.

    Only for commands whose failure is genuinely acceptable, and then only
    where the discard is commented at the call site. Never for resolving a
    ref: `git rev-parse <missing-ref>` fails AND prints the ref name, so this
    returns a truthy non-commit -- use _rev() instead. Never to decide whether
    something worked: a failure here is indistinguishable from success with no
    output. `fresh()` below is the model for a command that may legitimately
    fail -- it checks returncode and says "COULD NOT VERIFY" rather than
    letting silence read as confirmation."""
    return subprocess.run(['git', '-C', str(cwd)] + list(args),
                          capture_output=True, text=True).stdout.strip()


def _git_read(cwd, *args):
    """Run git and return (ok, stdout) so a caller can tell empty output apart
    from a failed command."""
    r = subprocess.run(['git', '-C', str(cwd)] + list(args),
                       capture_output=True, text=True)
    return r.returncode == 0, r.stdout


def _rev(repo_dir, ref):
    """Resolve `ref` to a commit, or '' if it does not exist.

    `--verify --quiet` matters: plain `git rev-parse <missing-ref>` exits
    non-zero but ECHOES THE REF NAME on stdout, and _git() below returns
    stdout while discarding the exit code. A caller doing
    `_git(..., 'rev-parse', ref) or <fallback>` therefore gets the truthy
    string 'origin/precedent-beta-v01' instead of falling back, and carries
    that non-commit forward as if it were a hash. Caught in CI (2026-09-06):
    a clone whose origin lacked SOURCE_BRANCH failed downstream with
    "precedent-beta-v01 @ origin/prece has no tools/build_views.py" -- the
    12-char truncation of the ref name being printed where a commit belonged.
    """
    r = subprocess.run(['git', '-C', str(repo_dir), 'rev-parse', '--verify',
                        '--quiet', ref], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ''


def _blob_exists(repo_dir, commit, rel):
    """Does `rel` exist at `commit` in `repo_dir`? Used by seed() to tell
    "this engine file is new and not committed yet" from "this checkout is
    broken", which are the same `git show` failure otherwise."""
    r = subprocess.run(['git', '-C', str(repo_dir), 'cat-file', '-e',
                        f'{commit}:{rel}'], capture_output=True)
    return r.returncode == 0


def _head_commit(repo_dir):
    # _rev, not _git: a failed `rev-parse HEAD` prints 'HEAD' back, which is
    # truthy, so seed()'s `_head_commit(ROOT) or 'unknown'` silently recorded
    # source_commit: "HEAD" in ENGINE_MANIFEST.json instead of 'unknown' --
    # and every later status()/refresh() then compared a real hash against the
    # string "HEAD" and reported upstream as moved, forever.
    return _rev(repo_dir, 'HEAD')


def _seed_write(dest_tools, engine_dir, stamp, kind, hooks_dir=None):
    """_write_engine_files, plus the cleanup seed never did, plus the hook
    scripts when `hooks_dir` is given -- seed()'s two branches source hooks
    from different places (the working tree vs. an extracted commit), so the
    directory is resolved by the caller rather than derived from `engine_dir`
    here.

    RESEEDING IS THE DOCUMENTED RECOVERY from a bricked refresh -- a
    consumer whose vendored copy predates the removed-file fix cannot
    refresh at all, and reseeding from BestPractice's own checkout is the
    only way forward. So reseed is exactly the path a repo takes when
    upstream has RENAMED an engine file, and it was the one path that never
    removed the old name: seed wrote the new set and a manifest that no
    longer mentions the old file, leaving it on disk with nothing tracking
    it. Measured 2026-09-08 recovering three real practice sets from the
    `precedent_retire_path.py` -> `precedent_decommission.py` rename: all
    three came out of the documented recovery carrying the dead file.

    It compounded with refresh's early exit (see refresh()): once the
    manifest commit matched, nothing ran the cleanup again, so the orphan
    was permanent. Cleaning here is the half that belongs to seed -- the
    previous manifest is read BEFORE the write, because the write replaces
    it with one that no longer remembers the dropped name."""
    # Read the manifest DIRECTLY, not through _load_manifest: that helper
    # sys.exit()s when there is none, which is right for status/refresh
    # (they have nothing to work from) and fatally wrong here -- seeding a
    # repo that has never been vendored is seed's whole primary case, and
    # routing it through _load_manifest killed it outright. Caught by
    # verify_harness's own consumer-seed check on the first full run after
    # the change; a seed into a fresh directory is the one path the
    # narrower fixtures here never exercised.
    path = dest_tools / MANIFEST_NAME
    previous = None
    if path.is_file():
        try:
            previous = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            # An unreadable manifest is not a reason to refuse to seed --
            # seeding is what repairs it. Nothing to clean up from, so say
            # so rather than guessing at a file list (practice:
            # fail-gracefully).
            print(f"WARN: precedent_vendor_engine seed: {path} could not be "
                  f"read, so files dropped from this kind since the last "
                  f"vendoring cannot be identified and are left in place.",
                  file=sys.stderr)
    written = _write_engine_files(dest_tools, engine_dir, stamp, kind)
    if previous:
        _remove_dropped_engine_files(dest_tools, previous, kind)
    if hooks_dir is not None:
        written += _write_hook_files(dest_tools.parent, hooks_dir)
    return written


def seed(dest, kind=DEFAULT_KIND):
    """Run from BestPractice's own checkout: dest is a NEW source-set or
    consumer repo's root (tools/precedent_bootstrap_source.py's own --dest,
    for kind='source' only -- a consumer has no bootstrap tool of its own,
    it is vendored directly into an existing repo, per INSTALL.md). No clone
    needed -- the source IS this checkout.

    kind defaults to 'source' so every existing caller (precedent_bootstrap_
    source.py calls `seed(dest)` with no kind argument at all) keeps getting
    exactly the file set it always has -- this default is what makes the
    consumer kind purely additive rather than a breaking change to the
    source-repo case."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    dest = pathlib.Path(dest).resolve()
    commit = _head_commit(ROOT) or 'unknown'
    # From the COMMIT, not the working tree. This used to copy whatever
    # was on disk in ENGINE_DIR while stamping HEAD's hash into
    # ENGINE_MANIFEST.json, so seeding from a checkout with any
    # uncommitted engine change wrote a manifest that named a commit the
    # vendored bytes did not come from. `status` and `refresh` in the
    # adopter's repo then compared those bytes against that commit's real
    # content and reported drift forever, with nothing in the adopter's
    # repo to explain it -- the provenance record silently made false,
    # which is the one thing a provenance record must not do (practice:
    # generated-artifact-provenance). An uncommitted change is also not
    # something an adopter should be shipped: it is, by definition, not
    # yet part of the engine.
    wanted = KINDS[kind] + ['routing_scope.json']
    missing_at_head = [n for n in wanted
                       if commit != 'unknown'
                       and not _blob_exists(ROOT, commit, f'tools/{n}')]
    if commit == 'unknown' or missing_at_head:
        # Either there is no commit to read from (an unborn HEAD, or not a
        # git checkout), or a file this kind needs does not exist at HEAD
        # yet -- the ordinary state while an engine file is being ADDED.
        # Vendor the working tree, and mark the recorded commit `+dirty` so
        # the manifest never claims bytes came from a commit they did not:
        # status() and refresh() both compare against source_commit, and a
        # `+dirty` value can never equal a real hash, so they correctly
        # report the copy as not-current until a clean re-seed.
        if missing_at_head:
            print(f"precedent_vendor_engine seed: NOTE -- "
                  f"{', '.join(missing_at_head)} is not in {commit[:12]} yet, "
                  f"so this seeds from the WORKING TREE and records "
                  f"{commit[:12]}+dirty. Commit and re-seed for a clean "
                  f"provenance record.", file=sys.stderr)
        stamp = commit if commit == 'unknown' else f'{commit}+dirty'
        return _seed_write(dest / 'tools', ENGINE_DIR, stamp, kind,
                           hooks_dir=ROOT / HOOK_SOURCE_DIR)
    _c, engine_dir = _source_tools_at(ROOT, kind=kind, ref=commit, fetch=False)
    try:
        dirty = [n for n in wanted
                 if (ENGINE_DIR / n).is_file()
                 and (ENGINE_DIR / n).read_bytes() != (engine_dir / n).read_bytes()]
        if dirty:
            print(f"precedent_vendor_engine seed: NOTE -- vendoring "
                  f"{commit[:12]}, not this working tree. Uncommitted "
                  f"changes to {', '.join(dirty)} are NOT in what was "
                  f"written; commit them and re-run to ship them.",
                  file=sys.stderr)
        return _seed_write(dest / 'tools', engine_dir, commit, kind,
                           hooks_dir=engine_dir / 'hooks')
    finally:
        shutil.rmtree(engine_dir, ignore_errors=True)


def _load_manifest(dest_tools):
    path = dest_tools / MANIFEST_NAME
    if not path.is_file():
        sys.exit(f"precedent_vendor_engine FAIL: {path} does not exist -- this repo has "
                 f"no vendored engine yet (run `seed`, or bootstrap a fresh set instead "
                 f"of migrating this one by hand)")
    return json.loads(path.read_text(encoding='utf-8'))


def _local_drift(dest_tools, manifest):
    """Files whose on-disk sha256 no longer matches what the manifest
    recorded -- a hand-edit since the last seed/refresh."""
    drifted = []
    for name, recorded_hash in manifest.get('sha256', {}).items():
        path = dest_tools / name
        if not path.is_file():
            drifted.append((name, 'missing'))
            continue
        actual = _sha256(path)
        if actual != recorded_hash:
            drifted.append((name, 'hand-edited (sha256 differs from manifest)'))
    return drifted


def _retired_engine_files_present(dest_tools):
    """-> [(name, why)] for tombstoned engine files still sitting on disk.

    REPORTS, never deletes on its own. A tombstoned file that the manifest
    still records is removed by _remove_dropped_engine_files, which can
    check the hash first. One the manifest has already forgotten cannot be
    verified as untouched, and `decommission-deletes-files` is explicit that
    a deletion is audited rather than taken on a hunch -- so this says
    exactly what the file is and why it should go, and leaves the deleting
    to a person who can look at it."""
    return [(n, why) for n, why in sorted(RETIRED_ENGINE_FILES.items())
            if (dest_tools / n).is_file()]


def _untracked_engine_files(dest_tools, manifest):
    """Engine files present on disk that the manifest does not record -- a
    hand-copy dropped in beside a properly vendored engine.

    _local_drift() above walks the manifest and asks "is each recorded file
    still what we wrote?" That direction is blind to a file nobody recorded,
    and the blind spot is not hypothetical. 2026-09-06, in
    precedent-team-repo-maintenance: its engine was a faithful, internally
    consistent vendoring of one upstream commit -- seven files, every hash
    matching -- and beside it sat a hand-copied `build_codeowners.py` from a
    LATER upstream commit. build_views.py scans `tools/*.py` and requires a
    description for each, so the newer stray broke the older engine outright:
    `build_views.py` failed, and that repo could not regenerate its own
    AGENTS.md at all. Every mechanism reported healthy -- `status` compared
    only recorded files and saw no drift -- because the one file causing it
    was invisible to all of them.

    Deliberately keyed on the engine's OWN file lists rather than on "any
    .py we did not vendor": a repo's own tools/ legitimately holds its own
    scripts, and flagging those would make this noise. A name that appears
    in ENGINE_FILES or CONSUMER_ENGINE_FILES but not in this repo's manifest
    is the precise signature of a hand-drop -- and `refresh` is its fix,
    since vendoring the file properly is exactly what records it."""
    recorded = set(manifest.get('files', []))
    known = set(ENGINE_FILES) | set(CONSUMER_ENGINE_FILES)
    return sorted(n for n in (known - recorded) if (dest_tools / n).is_file())


def _clone_or_die(arg):
    clone = pathlib.Path(arg).resolve()
    if not (clone / '.git').exists():
        sys.exit(f"precedent_vendor_engine FAIL: {clone} is not a git clone")
    return clone


def status(clone):
    dest_tools = ROOT / 'tools'
    manifest = _load_manifest(dest_tools)
    kind = manifest.get('kind', DEFAULT_KIND)  # older manifests predate 'kind' -- 'source'
    drift = _local_drift(dest_tools, manifest)
    for name, why in drift:
        print(f"  LOCAL DRIFT: {name} -- {why}")
    hook_drift = _hook_drift(ROOT, manifest)
    for name, why in hook_drift:
        print(f"  LOCAL DRIFT: {HOOK_DEST_DIR}/{name} -- {why}")
    claimed = _adapter_claimed_paths(ROOT)
    adapter_owned = sorted(n for n in (manifest.get('hook_files') or [])
                           if f'{HOOK_DEST_DIR}/{n}' in claimed)
    for name in adapter_owned:
        print(f"  NOTE: {HOOK_DEST_DIR}/{name} is now owned by "
              f"{claimed[f'{HOOK_DEST_DIR}/{name}']!r}'s own adapters "
              f"mechanism, not this engine -- expected divergence, not a "
              f"hand-edit; `refresh` will stop vendoring and tracking it.")
    if 'hook_files' not in manifest:
        print(f"  NOTE: this manifest has no hook_files recorded yet -- vendored before hook "
              f"scripts were tracked. `refresh` will pick them up on the next run.")
    ci_drift = _ci_workflow_drift(ROOT, manifest)
    for rel, why in ci_drift:
        print(f"  LOCAL DRIFT: {rel} -- {why}")
    ep_drift = _engine_path_drift(ROOT, manifest)
    for rel, why in ep_drift:
        print(f"  LOCAL DRIFT: {rel} -- {why}")
    ep_declared = declared_engine_paths(ROOT)
    for rel, why in _engine_path_conflicts(ROOT, ep_declared, manifest, kind):
        print(f"  CONFLICT: {ENGINE_PATHS_KEY} maps onto {rel} -- {why}. "
              f"`refresh` will refuse until the entry is fixed.")
    for rel in _engine_paths_incomplete(ROOT, manifest):
        print(f"  NOTE: {ENGINE_PATHS_KEY} entry for {rel} is not recorded "
              f"yet (or changed) -- `refresh` will adopt it if identical to "
              f"upstream, and refuse if not.")
    # Declared-local workflows are reported here too, for the same reason
    # refresh prints them: an exemption that stops being visible stops
    # being reviewed, and `status` is where somebody looks to find out what
    # this repo's relationship to upstream actually is.
    for rel, why in sorted(local_ci_workflows(ROOT).items()):
        print(f"  LOCAL BY DECLARATION (never refreshed): {rel} -- {why}")
    if not manifest.get('ci_workflows_sha256'):
        print(f"  NOTE: this manifest has no ci_workflows_sha256 recorded yet -- vendored "
              f"before CI workflow files were tracked. `refresh` will record a baseline "
              f"for them (not rewrite them) on the next run.")
    drift = drift + hook_drift + ci_drift + ep_drift
    untracked = _untracked_engine_files(dest_tools, manifest)
    for name in untracked:
        print(f"  UNTRACKED ENGINE FILE: {name} is an engine file this "
              f"manifest does not record -- a hand-copy dropped in beside "
              f"the vendored engine. It can be from a different upstream "
              f"commit than the rest, which is how a correctly vendored "
              f"engine ends up unable to run at all. `refresh` vendors it "
              f"properly and records it.")
    retired = _retired_engine_files_present(dest_tools)
    for name, why in retired:
        print(f"  RETIRED ENGINE FILE: {name} was vendored by this engine "
              f"once and no longer is -- {why}. Nothing updates it and "
              f"nothing else can find it: it is in no current file list, so "
              f"LOCAL DRIFT and UNTRACKED ENGINE FILE are both blind to it. "
              f"Delete it once you have checked nothing in this repo still "
              f"calls it.")

    # _rev, not _git: plain rev-parse of a missing ref prints the REF NAME, so
    # this used to bind clone_head='origin/precedent-beta-v01' -- truthy, and
    # != recorded -- and then told the reader upstream had moved and to run
    # refresh, when the truth was that this clone has no such ref at all.
    clone_head = (_rev(clone, f'origin/{SOURCE_BRANCH}')
                  or _rev(clone, SOURCE_BRANCH))
    recorded = manifest.get('source_commit')
    print(f"kind: {kind}")
    print(f"manifest source_commit: {recorded}")
    if clone_head:
        _status_template_instances(clone, clone_head, kind, manifest)
    if not clone_head:
        # Not "fresh" and not "moved" -- unknown. Same discipline as fresh().
        print(f"COULD NOT VERIFY: {clone} has no {SOURCE_BRANCH} "
              f"(neither origin/{SOURCE_BRANCH} nor a local branch of that name), so "
              f"whether this vendored engine is current is UNKNOWN -- this is not "
              f"'confirmed current'. Fetch that branch in the clone, or point at a "
              f"clone of {SOURCE_REPO}.")
        return 1 if (drift or untracked or retired) else 0
    print(f"clone origin/{SOURCE_BRANCH}: {clone_head}"
          + ("  (== recorded)" if clone_head == recorded else "  (!= recorded)"))
    if clone_head != recorded:
        print(f"NOTICE: BestPractice's {SOURCE_BRANCH} has moved since this engine was "
              f"last vendored -- run `refresh` to pick it up.")
    return 1 if (drift or untracked or retired) else 0


def _status_template_instances(clone, commit, kind, manifest):
    """status()'s view of TEMPLATE_INSTANCES against `commit`: what refresh
    would do to each, and what a diverged one lacks. Informational -- a
    diverged bootstrap.sh is expected variance, so it never sets the exit
    code."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-templates-'))
    try:
        _read_template_sources(clone, commit, kind, tmp)
        plan = _template_instance_plan(ROOT, kind, tmp, manifest)
        says = {'refresh': 'unedited and behind the template -- `refresh` '
                           'brings it up to date',
                'adopt': 'an unedited past version of the template, not yet '
                         'tracked -- `refresh` brings it up to date',
                'absent': 'not on disk -- never recreated'}
        for _src, rel, action in plan:
            if action in says:
                print(f"  NOTE: {rel} is {says[action]}.")
        _report_diverged_template_instances(ROOT, tmp, plan)
        _read_agents_md_sources(clone, commit, kind, tmp)
        agents_plan = _agents_md_plan(ROOT, kind, tmp, manifest)
        for key, _src, _n, action, _span in agents_plan:
            if action in ('refresh', 'adopt'):
                print(f"  NOTE: {AGENTS_MD} \"{key}\" is unedited and behind "
                      f"the template -- `refresh` brings it up to date.")
        _report_agents_md(ROOT, tmp, agents_plan)
        _report_retired_branch_names(ROOT)
        _LEFT_FOR_YOU.clear()   # status only reports; the list is refresh's
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _source_tools_at(clone, kind=DEFAULT_KIND, ref=None, fetch=True):
    """Materialize SOURCE_BRANCH's tools/ out of `clone` into a throwaway
    directory, and return (commit, that directory).

    READ-ONLY with respect to `clone`, deliberately and load-bearingly so.
    This used to run `git checkout SOURCE_BRANCH` and `git pull` in `clone`
    to get the files off disk, which moved the caller's repository:

      * for a person, it silently switched their own BestPractice checkout
        onto SOURCE_BRANCH, abandoning whatever branch they were on;
      * in CI, `clone` is the job's own workspace, so the checkout moved the
        workspace mid-job and every LATER step in that job silently ran
        against SOURCE_BRANCH instead of the commit under test. That cost
        several sessions of investigation on PR #110, where the step after
        this one reported a violation that was true of SOURCE_BRANCH and
        false of the commit being tested, with `git status` clean throughout
        (a branch checkout leaves no dirty file to notice).

    Blobs, not the working tree -- the same discipline tools/leak_gate.py
    holds, for the same reason: reading history must not disturb the tree
    the caller is standing in. A vendoring read needs file CONTENT at a
    commit, which `git show` gives without touching HEAD or the index.

    `kind` selects which file list to materialize -- the consumer kind
    vendors precedent_materialize/resolve/sync_views on top of the source
    kind's list, and _write_engine_files() will look for every one of them
    in the directory returned here."""
    # Exit code deliberately discarded: an offline clone, or one whose origin
    # has no SOURCE_BRANCH, is a supported case -- the _rev fallback below
    # handles it, and a hard failure here would break vendoring from a local
    # clone that is already up to date.
    if fetch:
        _git(clone, 'fetch', '--quiet', 'origin', SOURCE_BRANCH)
    # `ref`, when given, names the exact commit to read (seed() passes this
    # checkout's own HEAD -- it is not vendoring from a branch at all).
    # Otherwise: origin/<branch> first, then a local branch of that name --
    # a CI workspace carries only the ref under test, so a clone taken from
    # it legitimately has no origin/<SOURCE_BRANCH> at all.
    commit = ref or (_rev(clone, f'origin/{SOURCE_BRANCH}')
                     or _rev(clone, SOURCE_BRANCH))
    if not commit:
        sys.exit(f"precedent_vendor_engine FAIL: {clone} has no {SOURCE_BRANCH} "
                 f"(neither origin/{SOURCE_BRANCH} nor a local branch of that name) "
                 f"-- is it a clone of {SOURCE_REPO}?")

    # file mode per entry, so a vendored file keeps the executable bit it has
    # upstream (shutil.copy2 used to carry it over from the checked-out tree).
    modes = {}
    ok, tree = _git_read(clone, 'ls-tree', f'{commit}:tools')
    if not ok:
        # No tempdir yet at this point -- nothing to clean up.
        sys.exit(f"precedent_vendor_engine FAIL: could not list tools/ at "
                 f"{SOURCE_BRANCH} @ {commit[:12]} in {clone}. Refusing rather than "
                 f"vendoring with every executable bit silently dropped.")
    for line in tree.splitlines():
        meta, _tab, name = line.partition('\t')
        if meta and name:
            modes[name] = meta.split()[0]

    tmp = pathlib.Path(tempfile.mkdtemp(prefix='precedent-engine-source-'))
    for name in KINDS[kind] + ['routing_scope.json']:
        blob = subprocess.run(['git', '-C', str(clone), 'show', f'{commit}:tools/{name}'],
                              capture_output=True)
        if blob.returncode != 0:
            # A FILE UPSTREAM NO LONGER HAS IS A REMOVAL, NOT A BROKEN CLONE.
            # KINDS here is the list in the RUNNING copy of this tool, and in a
            # consumer that copy is the vendored, stale one. So the first
            # refresh after upstream renames or drops an engine file asks for a
            # path that is genuinely gone -- and this used to be a hard exit,
            # which meant a rename upstream BRICKED every consumer's refresh
            # with no way forward but a manual reseed. Reproduced 2026-09-07
            # renaming precedent_retire_path.py -> precedent_decommission.py:
            # the consumer refused with "has no tools/precedent_retire_path.py"
            # and could not have acquired the new name by any documented route.
            #
            # Skipping converges instead. This pass writes what still exists
            # (including this tool itself), the self-replacement triggers the
            # second pass, and that pass runs the NEW list -- which does not
            # ask for the dropped file at all, and whose
            # _remove_dropped_engine_files then deletes the local leftover.
            #
            # This tool itself is the one file that must never be skipped: it
            # is what carries the corrected list, so without it there is no
            # second pass and no convergence, and a missing one really does
            # mean a broken ref rather than a removal.
            if name == HERE.name:
                shutil.rmtree(tmp, ignore_errors=True)
                sys.exit(f"precedent_vendor_engine FAIL: {SOURCE_BRANCH} @ "
                         f"{commit[:12]} has no tools/{name} -- that is the "
                         f"vendoring tool itself, so there is no corrected "
                         f"file list to converge on. This is a broken ref, "
                         f"not a removal.")
            print(f"precedent_vendor_engine: {SOURCE_BRANCH} @ {commit[:12]} no "
                  f"longer carries tools/{name} -- it was removed or renamed "
                  f"upstream. Skipping it; the second pass runs the new file "
                  f"list and cleans up the local copy.", file=sys.stderr)
            continue
        out = tmp / name
        out.write_bytes(blob.stdout)          # bytes, not text: no newline munging
        if modes.get(name, '').endswith('755'):
            out.chmod(0o755)

    # Hook scripts, into tmp/hooks/ -- same commit, same read-only blob
    # discipline, listed from THIS commit's tree rather than from disk so a
    # hook added or removed upstream is picked up without a code change here
    # (practice: durable-fix -- see _hook_file_names). No skip-and-converge
    # dance for a missing one: hooks have no self-reference problem the way
    # this tool's own file does, so a hook name from this commit's own tree
    # listing cannot fail to `git show` from the same commit.
    hook_ok, hook_tree = _git_read(clone, 'ls-tree', f'{commit}:{HOOK_SOURCE_DIR}')
    if hook_ok:
        hook_modes = {}
        hook_names = []
        for line in hook_tree.splitlines():
            meta, _tab, name = line.partition('\t')
            if meta and name and name.endswith('.sh'):
                hook_modes[name] = meta.split()[0]
                hook_names.append(name)
        hooks_tmp = tmp / 'hooks'
        hooks_tmp.mkdir(exist_ok=True)
        for name in hook_names:
            blob = subprocess.run(
                ['git', '-C', str(clone), 'show', f'{commit}:{HOOK_SOURCE_DIR}/{name}'],
                capture_output=True)
            if blob.returncode != 0:
                continue  # listed but unreadable -- treat like any other transient git failure
            out = hooks_tmp / name
            out.write_bytes(blob.stdout)
            if hook_modes.get(name, '').endswith('755'):
                out.chmod(0o755)
    # else: this commit predates HOOK_SOURCE_DIR, or the clone cannot list it
    # -- tmp/hooks/ is simply absent, and callers treat "no hooks dir" as
    # "nothing to vendor" rather than an error (fail-gracefully: a repo
    # vendoring from an old commit should not lose its tools/ refresh over a
    # directory that commit never had).

    # CI workflow templates, into tmp/ci-workflows/ -- same commit, same
    # read-only blob discipline as the hooks block above, but kind-specific:
    # there is no destination-wiring signal for a CI workflow file the way
    # _wired_hook_names gives one for a hook, so what's fetched is exactly
    # this kind's own declared CI_WORKFLOW_TEMPLATES list. A missing blob
    # (this commit predates the template) is skipped, not fatal -- the same
    # fail-gracefully discipline as the hooks block: a repo vendoring from
    # an old commit should not lose its tools/ refresh over a template that
    # commit never had.
    ci_tmp = tmp / 'ci-workflows'
    ci_tmp.mkdir(exist_ok=True)
    for template, _rel in CI_WORKFLOW_TEMPLATES.get(kind, ()):
        blob = subprocess.run(
            ['git', '-C', str(clone), 'show',
             f'{commit}:{CI_WORKFLOWS_SOURCE_DIR}/{template}'],
            capture_output=True)
        if blob.returncode != 0:
            continue
        (ci_tmp / template).write_bytes(blob.stdout)

    # Template-instanced files (tools/bootstrap.sh), into tmp/templates/,
    # with the history of blob ids the catch-up needs -- see
    # TEMPLATE_INSTANCES.
    _read_template_sources(clone, commit, kind, tmp / 'templates')
    # AGENTS.md's template and the section texts it has ever carried -- see
    # AGENTS_MD_TEMPLATES.
    _read_agents_md_sources(clone, commit, kind, tmp / 'templates')
    return commit, tmp


def _warn_legacy_status_records(dest):
    """Say when this repo still holds practices written under the OLD status
    vocabulary, at the moment the new one arrives.

    A refresh is exactly when the vocabulary changes underneath a set, and
    the set has no other way to find out: verify_harness.py is not vendored,
    so check_status_contract never runs here. Without this the new engine
    simply starts treating `retired` records differently -- correctly, but
    silently -- and the one thing a legacy record cannot tell anyone is
    whether its rule survives somewhere. Same principle build_views already
    applies when it drops a practice from the generated views: the drop is
    announced rather than silently skipped.

    A notice, never a gate. Refreshing the engine must not fail because the
    CATALOGUE needs a separate, human-decided migration -- that is the same
    separation _warn_catalogue_skew exists to respect."""
    try:
        sys.path.insert(0, str(ROOT / 'tools'))
        import precedent_migrate_status as pms
        records = pms.legacy_records(pathlib.Path(dest) / 'practices')
    except Exception:                                        # noqa: BLE001
        return                                               # never break a refresh
    if not records:
        return
    slugs = ', '.join(fm.get('slug', f.stem) for f, fm, _s in records)
    print(f"\nNOTICE: {len(records)} practice(s) here still carry the pre-2026-09-06 "
          f"status vocabulary, where `retired` meant BOTH 'the copy here is "
          f"redundant, the rule is in force elsewhere' AND 'nobody wants this "
          f"rule anywhere': {slugs}.")
    print("  The engine you just vendored treats them as not in force -- which is "
          "correct either way -- but they carry no `in_force_at:`, so nothing can "
          "say which kind they are, and precedent_show.py will decline to guess.")
    print("  Classify them:  python3 tools/precedent_migrate_status.py "
          "--repo . --against <sibling-source-dirs>")


def _warn_catalogue_skew(dest, engine_commit):
    """Say when the engine just moved past the catalogue it runs against.

    `refresh` updates the ENGINE and nothing else, by design -- taking the
    practice catalogue is a separate, deliberate step (INSTALL.md section 2),
    because installs are adapted and an unattended mirror is the mechanism
    class that loses content. The cost of that separation is a skew nobody
    was told about: engine code that cites a practice slug the vendored
    catalogue predates.

    THE REMEDY THIS NOTICE NAMES IS DELIBERATELY NOT `checkin.py update`.
    Its first version suggested exactly that, and the suggestion was worse
    than silence: checkin.py's `_default_branch()` resolves
    `refs/remotes/origin/HEAD` unconditionally, so on every consumer pinned
    to `precedent-beta-v01` -- which is all of them, until the phase-7
    fold-in -- following the advice mirrors `main` over the vendored tree
    and DELETES the very practices this notice says are missing. Caught
    2026-09-06 by the consumer session that read the notice, recognized the
    trap, and did the manual mirror instead; spec/MIGRATING_EXISTING_INSTALLS.md's
    "The default-branch gotcha" is the same finding from the other side.
    UPDATE, later the same day: checkin.py HAS since been taught the pin.
    All four of its commands -- `fresh`, `update`, `record`, `push` -- now
    read `upstream.branch` from the consuming repo's own
    `process/manifest.json` and fall back to the clone's default only when
    no pin is recorded, and `record` no longer checks the clone out either.
    Seven harness cases assert it, each with a negative control.

    The remedy named below still points at the manual mirror anyway, and
    that is a deliberate hold rather than an oversight. What these two
    documents guard against is an UNATTENDED job overwriting a repo's
    vendored tree; the fix that would let them relax is hours old at the
    time of writing, and the two error directions are not symmetric --
    telling people the automation is safe when it is not costs a silent
    overnight wipe, while staying cautious costs a stale sentence. Morgan's
    call, 2026-09-06: record that the pin works, keep the manual remedy,
    and revisit once the fix has survived real sync cycles. So this is now
    a "not yet", not a "cannot" -- do not read it as the latter and do not
    quietly flip it either; that flip is a decision, and it has an owner.

    Reached a real consumer on 2026-09-06. A refresh took the engine to a
    commit whose `precedent_resolve.py` cites `source-naming` three times,
    while `process/upstream/` still sat 5 commits back and had no
    `practices/source-naming.md` -- so the repo's own `code-cites-practice`
    check reported three violations for a slug that does exist upstream, in
    code the consumer is not allowed to edit. Nothing in the refresh had
    said the two halves were now different ages.

    Reports, never fails: the skew is legitimate between an engine refresh
    and the catalogue update that follows it, and this runs at the moment
    the person is right there to act on it. Practice fail-gracefully: keep
    going, and tell the human.
    """
    manifest = dest / 'process' / 'manifest.json'
    if not manifest.is_file():
        return                              # not the classic vendoring layout
    try:
        recorded = json.loads(manifest.read_text(
            encoding='utf-8'))['upstream']['commit']
    except (ValueError, KeyError, OSError):
        return                              # nothing reliable to compare
    if not recorded or recorded.startswith(engine_commit[:len(recorded)]) \
            or engine_commit.startswith(recorded[:len(engine_commit)]):
        return                              # same commit, however abbreviated
    print(f"NOTICE: the engine is now at {engine_commit[:12]}, but this "
          f"repo's vendored practice catalogue (process/upstream/) is still "
          f"at {recorded[:12]}. Engine code can cite practices that "
          f"catalogue does not carry yet -- if a check reports a slug as "
          f"'not a real practice', this skew is why. Take the catalogue "
          f"update too -- INSTALL.md section 2, which for a repo pinned to "
          f"a named branch means the manual mirror it describes, NOT "
          f"`checkin.py update`.")


def refresh(clone, force=False, ref=None):
    """`ref`, when given, names the exact commit or ref inside `clone` to
    vendor from, instead of resolving SOURCE_BRANCH there.

    Two callers need it. A verification fixture must vendor from the tree
    it is testing, not from whatever `origin/precedent-beta-v01` happens
    to hold -- without that, adding a file to the engine turns the harness
    red until the addition is published, and a stale local branch in a
    contributor's checkout produces a failure message about a missing
    engine file that has nothing to do with the property under test (both
    reproduced, 2026-09-06). And a person can legitimately want to vendor
    a specific commit -- pinning to a known-good one, or picking up a fix
    before it lands on the branch."""
    dest_tools = ROOT / 'tools'
    manifest = _load_manifest(dest_tools)
    kind = manifest.get('kind', DEFAULT_KIND)  # older manifests predate 'kind' -- 'source'

    # Before anything else, including the drift check below: a retired CI
    # workflow entry is cleaned up unconditionally, --force or not, so its
    # own retirement can never be the reason refresh refuses. See
    # RETIRED_CI_WORKFLOW_FILES' own comment for the incident this closes.
    _remove_retired_ci_workflow_files(ROOT, manifest, kind)
    # Then what no manifest ever recorded: the old install's own leftovers,
    # recognised by content. Also before the drift check, so a hand-paused
    # copy that _remove_retired_ci_workflow_files just stopped tracking is
    # judged here rather than refused there. See LEGACY_CI_WORKFLOWS.
    retire_legacy_leftovers(ROOT, manifest, kind)

    # A declared engine path that would give one file two writers is refused
    # before anything else, --force or not: force discards an edit, it does
    # not settle which mechanism owns a file. See ENGINE_PATHS_KEY's comment.
    engine_paths = declared_engine_paths(ROOT)
    conflicts = _engine_path_conflicts(ROOT, engine_paths, manifest, kind)
    if conflicts:
        for local, why in conflicts:
            print(f"  {local}: {why}")
        sys.exit(f"precedent_vendor_engine FAIL: precedent.json's "
                 f"{ENGINE_PATHS_KEY} maps an upstream file onto a path "
                 f"something else already writes. Map it to a path of its "
                 f"own, or drop the entry. Not waived by --force.")

    if not force:
        drift = (_local_drift(dest_tools, manifest) + _hook_drift(ROOT, manifest)
                 + _ci_workflow_drift(ROOT, manifest)
                 + _engine_path_drift(ROOT, manifest))
        if drift:
            for name, why in drift:
                print(f"  {name}: {why}")
            sys.exit("precedent_vendor_engine FAIL: a vendored engine, hook or CI "
                     "workflow file was hand-edited since the last seed/refresh -- "
                     "refreshing would silently discard that edit. Move the edit "
                     "upstream into BestPractice instead (this engine has no local "
                     "variance by design), or pass --force to overwrite anyway -- "
                     "after reviewing each file above per vendor-update-runbook's "
                     "conflicted-file review, since --force keeps none of it.\n"
                     "       A CI WORKFLOW THIS REPO MEANS TO KEEP is a third "
                     "option, and the right one when the divergence is "
                     "deliberate: declare it in this repo's precedent.json as\n"
                     '         "' + LOCAL_CI_WORKFLOWS_KEY + '": '
                     '{".github/workflows/<name>.yml": "why it is ours"}\n'
                     "       and refresh will leave it alone and say so on every "
                     "run. A reason is required. Do NOT reach for `record-ci` "
                     "here: it re-baselines the hash, so the NEXT refresh "
                     "overwrites the file silently.")

    new_commit, engine_dir = _source_tools_at(clone, kind, ref=ref,
                                              fetch=ref is None)
    try:
        # Read now, compared now, BEFORE any write: a first-run refusal
        # after the engine files were already rewritten would leave a
        # half-refreshed tree behind it.
        engine_path_sources = _read_engine_path_sources(clone, new_commit,
                                                        engine_paths)
        first_run = _engine_path_first_run_refusals(
            ROOT, engine_paths, engine_path_sources, manifest)
        if first_run:
            for local, n in first_run:
                print(f"  {local}: differs from upstream by {n} line(s), and "
                      f"no hash is recorded for it yet")
            sys.exit(f"precedent_vendor_engine FAIL: a file newly declared in "
                     f"{ENGINE_PATHS_KEY} is not identical to the upstream "
                     f"file it maps, so adopting it would discard whatever "
                     f"makes it different. Move that difference upstream (or "
                     f"make the file identical), then refresh again. Not "
                     f"waived by --force: on a first run nothing has told "
                     f"anyone what would be lost.")
        engine_paths_incomplete = _engine_paths_incomplete(ROOT, manifest)
        # `and not force`: found reproduced while testing this against the consumer
        # kind -- without it, `refresh --force` on a repo with a hand-edited
        # vendored file silently did NOTHING when BestPractice's SOURCE_BRANCH
        # hadn't moved, because this short-circuit ran before --force ever got a
        # chance to matter. --force exists specifically to repair a hand-edited
        # file; "the upstream commit is unchanged" must not override that.
        # An equal commit is not enough to call this current: the vendored
        # FILE SET has to match this kind's list too. Without that second
        # half, a repo whose engine predates a newly-added engine file could
        # never acquire it -- and would be told it was current forever.
        #
        # THE TRAP, reproduced end to end 2026-09-06 across all three of this
        # account's practice sets. `refresh` runs the VENDOREE's own copy of
        # this tool, which carries the file list it was vendored with. A
        # first run therefore writes the OLD set, replaces this file with the
        # new one, and stamps the NEW commit into the manifest. A second run
        # -- now executing the newer tool, which does know about the added
        # file -- hit this short-circuit on the matching commit and reported
        # "nothing to do", so the file never arrived and the manifest
        # asserted current the whole time. build_codeowners.py joined the
        # engine on 2026-09-06 for a stated reason (a team set with declared
        # approvers and no way to enforce them); none of the three sets ever
        # received it, and someone hand-copied it into one of them, which is
        # what broke that repo's build_views.py. The hand-copy was a symptom.
        # Refresh still takes two passes when the tool must replace itself
        # first -- that is inherent to a self-updating tool -- but the second
        # pass now converges instead of lying.
        wanted_set = set(KINDS[kind]) | {'routing_scope.json'}
        set_incomplete = sorted(
            n for n in wanted_set
            if n not in set(manifest.get('files', []))
            or not (dest_tools / n).is_file())
        # A file this kind NO LONGER includes, still sitting on disk and
        # still recorded by the manifest, is the mirror of set_incomplete --
        # and it was not checked here, so the early exit below reported
        # "nothing to do" over a tree carrying a dead engine file. That made
        # the orphan PERMANENT: _remove_dropped_engine_files runs only after
        # a write, and once the commit matched there was never another write.
        # Found 2026-09-08 in three real practice sets, each carrying
        # `precedent_retire_path.py` after upstream renamed it to
        # `precedent_decommission.py` -- exactly the state
        # `decommission-deletes-files` exists to prevent, left behind by the
        # tool that distributes that practice.
        set_orphaned = sorted(
            n for n in manifest.get('files', [])
            if n not in wanted_set and (dest_tools / n).is_file())
        if set_orphaned and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but this "
                  f"repo's vendored engine still carries {len(set_orphaned)} "
                  f"file(s) this kind no longer includes "
                  f"({', '.join(set_orphaned)}) -- removing them.")
            _remove_dropped_engine_files(dest_tools, manifest, kind)
            _rewrite_manifest_file_list(dest_tools, kind)

        # Hook analog of set_incomplete, above -- but the "wanted" hook names
        # are read from THIS commit's own listing at HOOK_SOURCE_DIR,
        # intersected with what THIS repo's own settings.json actually wires
        # (_wired_hook_names) -- never the full glob. Vendoring a hook this
        # repo never wired is the orphan hooks-on-disk-are-reachable exists
        # to catch; see _wired_hook_names's docstring for the incident.
        # No hook analog of set_orphaned here: a hook upstream stops shipping
        # is removed by _remove_dropped_hook_files inside _write_hook_files,
        # and an untracked retired one by retire_legacy_leftovers at the top.
        # Asked of _vendorable_hook_names, the same function _write_hook_files
        # uses to decide what to write -- see its docstring for the loop a
        # separate computation here caused.
        new_hook_names = _vendorable_hook_names(ROOT, engine_dir / 'hooks')
        # A hook this kind gets and this repo does not run yet -- see
        # HOOK_WIRING. Asked before the early exit for the same reason
        # hooks_incomplete is: a new hook upstream at an unchanged recorded
        # commit is exactly the case the early exit used to swallow.
        wiring_pending, _unresolved = _hook_wiring_plan(
            ROOT, kind if 'kind' in manifest else None, engine_dir / 'hooks')
        hooks_incomplete = sorted(
            n for n in new_hook_names
            if n not in set(manifest.get('hook_files') or [])
            or not (ROOT / HOOK_DEST_DIR / n).is_file())

        # CI-workflow analog of set_incomplete/hooks_incomplete, above --
        # see _ci_workflow_incomplete's own docstring for exactly what
        # counts. No analog of set_orphaned/set_incomplete's REMOVAL side:
        # a CI workflow this repo no longer vendors is left alone, not
        # deleted -- deleting somebody's `.github/workflows/*.yml` out from
        # under them on a routine refresh is a different, larger decision
        # than this fix makes.
        ci_incomplete = _ci_workflow_incomplete(ROOT, kind, engine_dir / 'ci-workflows', manifest)

        # tools/bootstrap.sh and anything else TEMPLATE_INSTANCES names. Not
        # waived or widened by --force: a diverged copy is reported and left
        # alone whatever the flags, which is why it is not in the drift
        # refusal above either. Reported before the early exit so a re-run
        # that has nothing else to do still says what the file lacks.
        template_plan = _template_instance_plan(ROOT, kind, engine_dir / 'templates',
                                                manifest)
        template_pending = _template_instances_pending(template_plan, manifest)
        _report_diverged_template_instances(ROOT, engine_dir / 'templates',
                                            template_plan)
        # AGENTS.md's template-written sections, on the same terms: an
        # unedited one is brought up to the template, an edited one is only
        # reported. See AGENTS_MD_TEMPLATES.
        agents_plan = _agents_md_plan(ROOT, kind, engine_dir / 'templates', manifest)
        agents_pending = _agents_md_pending(agents_plan, manifest)
        _report_agents_md(ROOT, engine_dir / 'templates', agents_plan)

        if new_commit == manifest.get('source_commit') and not force \
                and not set_incomplete and not hooks_incomplete and not ci_incomplete \
                and not engine_paths_incomplete and not template_pending \
                and not wiring_pending and not agents_pending:
            print(f"precedent_vendor_engine refresh: already current with {SOURCE_BRANCH} "
                  f"@ {new_commit[:12]} -- nothing to do.")
            # Reported here too, and this is the case that matters MOST: a
            # session re-running refresh and being told "nothing to do" is
            # exactly the session that would otherwise conclude both halves
            # are current. Missed on the first version of this notice, which
            # only reported after a write -- so the second pass of a
            # self-replacing refresh, and every later re-run, stayed silent.
            _warn_catalogue_skew(ROOT, new_commit)  # ROOT, not `dest` -- see below
            _warn_legacy_status_records(ROOT)
            _report_retired_branch_names(ROOT)
            print_left_for_you()
            return 0

        if set_incomplete and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but this "
                  f"repo's vendored engine is missing {len(set_incomplete)} "
                  f"file(s) this kind now includes "
                  f"({', '.join(set_incomplete)}) -- refreshing anyway.")
        if hooks_incomplete and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but this "
                  f"repo's vendored hooks are missing {len(hooks_incomplete)} "
                  f"file(s) BestPractice now ships "
                  f"({', '.join(hooks_incomplete)}) -- refreshing anyway. "
                  + ("This is the one-time catch-up for a repo vendored before hooks "
                     "were tracked at all (manifest has no 'hook_files' yet)."
                     if 'hook_files' not in manifest else
                     "Each is wired in this repo's settings.json but missing from "
                     "disk or from the manifest's 'hook_files'; this refresh writes "
                     "and records it, so the next run at this commit is a no-op."))
        if wiring_pending and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but this "
                  f"repo does not yet run {len(wiring_pending)} hook "
                  f"entr{'y' if len(wiring_pending) == 1 else 'ies'} its kind "
                  f"gets ({', '.join(sorted({n for _e, _m, n, _a in wiring_pending}))}) "
                  f"-- refreshing anyway.")
        if ci_incomplete and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but this "
                  f"repo's CI workflow file(s) need attention "
                  f"({', '.join(ci_incomplete)}) -- refreshing anyway.")
        if template_pending and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but a "
                  f"template-instanced file needs bringing up to date or "
                  f"recording ({', '.join(r for _s, r, a in template_plan if a != 'diverged')}) "
                  f"-- refreshing anyway.")
        if agents_pending and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but "
                  f"{AGENTS_MD}'s template sections need bringing up to date "
                  f"or recording -- refreshing anyway.")
        if engine_paths_incomplete and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but "
                  f"{ENGINE_PATHS_KEY} has changed or is not yet recorded "
                  f"({', '.join(engine_paths_incomplete)}) -- refreshing anyway.")

        self_before = _sha256(HERE) if HERE.is_file() else None
        written = _write_engine_files(dest_tools, engine_dir, new_commit, kind)
        # AFTER the write, and using the manifest as it was BEFORE it:
        # _write_engine_files rewrites `files` from the current KINDS list, so
        # by then the dropped name is already gone from the record and there
        # is nothing left to find it by. `manifest` is the copy loaded at the
        # top of this function, which is the one that still remembers.
        _remove_dropped_engine_files(dest_tools, manifest, kind)
        # Wire first, then vendor: _write_hook_files is still gated on what
        # settings.json wires, so the entries it needs have to be there
        # before it looks. Never the other way round -- a file written
        # before its entry is an orphan if the wiring step then stops.
        if _apply_hook_wiring(ROOT, kind if 'kind' in manifest else None,
                              engine_dir / 'hooks'):
            written.append(ROOT / '.claude' / 'settings.json')
        written += _write_hook_files(ROOT, engine_dir / 'hooks')
        ci_refreshed, ci_catchup = _refresh_ci_workflow_files(
            ROOT, kind, engine_dir / 'ci-workflows', manifest)
        written += [ROOT / rel for rel in ci_refreshed]
        template_rewritten = _refresh_template_instances(
            ROOT, kind, engine_dir / 'templates', manifest, template_plan)
        written += [ROOT / rel for rel in template_rewritten]
        agents_rewritten = _refresh_agents_md(ROOT, engine_dir / 'templates',
                                              manifest, agents_plan)
        if agents_rewritten:
            written.append(ROOT / AGENTS_MD)
        if engine_paths or manifest.get('engine_paths_sha256'):
            written += _write_engine_paths(ROOT, engine_paths,
                                           engine_path_sources, manifest)
    finally:
        shutil.rmtree(engine_dir, ignore_errors=True)
    print(f"precedent_vendor_engine refresh OK ({kind}): {len(written)} file(s) refreshed "
          f"from {SOURCE_BRANCH} @ {new_commit[:12]} (was {manifest.get('source_commit', '?')[:12]})")
    if ci_refreshed:
        print(f"precedent_vendor_engine refresh: refreshed {len(ci_refreshed)} CI "
              f"workflow file(s) to the current template ({', '.join(ci_refreshed)}).")
    if template_rewritten:
        print(f"precedent_vendor_engine refresh: brought {', '.join(template_rewritten)} "
              f"up to the current template -- it carried no local edits.")
    if agents_rewritten:
        print(f"precedent_vendor_engine refresh: brought {len(agents_rewritten)} "
              f"{AGENTS_MD} section(s) up to the current template -- none carried "
              f"local edits: {', '.join(repr(k) for k in agents_rewritten)}.")
    # EVERY RUN, with the reason. This is the whole difference between a
    # declared local workflow and `--force`: force is a decision taken once
    # and never seen again, while a declaration announces itself for as long
    # as it stands, so nobody inherits an exemption they cannot see.
    for rel, why in sorted(local_ci_workflows(ROOT).items()):
        print(f"LOCAL (not refreshed, by declaration): {rel} -- {why}")
    if ci_catchup:
        print(f"NOTICE: precedent_vendor_engine refresh: recording a baseline hash "
              f"for {len(ci_catchup)} CI workflow file(s) this manifest never tracked "
              f"before ({', '.join(ci_catchup)}) -- vendored before this feature "
              f"existed. Not rewritten this run, so a hand customization is never "
              f"silently discarded -- run `refresh` again to pick up template "
              f"changes now that a baseline is recorded.")
    # ROOT, not `dest`: refresh()'s local for the repo being refreshed is
    # `dest_tools` (ROOT / 'tools'), and there has never been a `dest` here.
    # Landed 2026-09-06 as a NameError that crashed EVERY refresh, after the
    # files were already written and "refresh OK" already printed -- so the
    # run looked half-successful and its exit code was the only tell. Fixed
    # concurrently and identically by two sessions; the harness case for the
    # already-current branch came from this one.
    _warn_catalogue_skew(ROOT, new_commit)
    _warn_legacy_status_records(ROOT)

    # THE SECOND PASS, and why it is not optional. The file list for a kind
    # lives in THIS module, and a refresh runs the copy that is already
    # vendored -- the stale one. So the run that first brings a newly added
    # engine file's name into the repo is also the run that cannot copy it:
    # it works from the old list, writes the new tool, and stops one file
    # short, silently. Seen twice in one day (2026-09-06): `kind` stayed
    # absent from three sets' manifests for a whole cycle, and
    # build_codeowners.py reached none of them. Re-running once, with the
    # just-written tool, closes it. Guarded by an environment variable so
    # the second pass cannot start a third.
    if (self_before is not None and _sha256(HERE) != self_before
            and not os.environ.get(_SECOND_PASS_ENV)):
        print("precedent_vendor_engine refresh: this refresh replaced the "
              "vendoring tool itself, so its own file list may have changed "
              "-- running once more with the new copy.")
        # The second pass runs every sweep again and prints its own list;
        # printing this one too would say each item twice.
        _LEFT_FOR_YOU.clear()
        r = subprocess.run(
            [sys.executable, str(HERE), 'refresh', str(clone), '--force']
            + (['--from-ref', ref] if ref else []),
            env={**os.environ, _SECOND_PASS_ENV: '1'})
        if r.returncode != 0:
            return r.returncode

    _warn_bare_sync_invocations(ROOT)
    _report_retired_branch_names(ROOT)
    print_left_for_you()
    print("next: review the diff, then `python3 tools/precedent_sync_views.py "
          "--repo .` (a refresh changes what the loader renders, so `--check` "
          "is expected to FAIL until the sync has run), review that diff too, "
          "run this repo's own light check, then commit the two together.")
    return 0


_BARE_SYNC_RE = re.compile(r'\bpython3\s+\S*precedent_sync_views\.py(?![^\n]*--repo)')


def _warn_bare_sync_invocations(root):
    """Name every wiring file that still invokes precedent_sync_views.py
    without `--repo`, which the engine has refused since 2026-09-10.

    The engine's manifest does not cover tools/bootstrap.sh, the harness
    hooks or the instructions file -- those are instantiated from templates
    and adapted, so a refresh cannot rewrite them. Measured 2026-09-14 on a
    consumer vendored six days earlier: its refreshed engine refused the
    bare `--check` its own bootstrap.sh runs at every session start, so
    every session opened with a WARN naming a fix that failed the same way.
    Nothing in the refresh had told it (practice: change-updates-its-docs --
    the mechanism moved, the wiring that calls it did not).

    Since 2026-09-25 an UNEDITED tools/bootstrap.sh is brought up to the
    template by refresh itself (TEMPLATE_INSTANCES), so a hit there now
    means a copy with local edits, which refresh reports as DIVERGED and
    never rewrites.
    """
    candidates = [root / 'tools' / 'bootstrap.sh', root / 'AGENTS.md',
                  root / 'CLAUDE.md']
    hooks = root / '.claude' / 'hooks'
    if hooks.is_dir():
        candidates += sorted(hooks.glob('*.sh'))
    hits = []
    for path in candidates:
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if 'precedent_sync_views.py' in line and _BARE_SYNC_RE.search(line) \
                    and not line.lstrip().startswith('#'):
                hits.append(f'{path.relative_to(root)}:{n}')
    if hits:
        print("NOTICE: precedent_sync_views.py is invoked WITHOUT --repo in "
              + ', '.join(hits)
              + " -- the refreshed engine refuses that call, so a session-start "
                "check there will WARN on every session and name a fix that "
                "fails the same way. Re-instantiate tools/bootstrap.sh and the "
                "harness hooks from upstream's templates/, or add `--repo .` "
                "to each line; a refresh never rewrites a file carrying local "
                "edits, nor an instructions-file section that carries any.")


def fresh():
    try:
        manifest_path = ROOT / 'tools' / MANIFEST_NAME
        if not manifest_path.is_file():
            return 0
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        repo, recorded = manifest.get('source_repo'), manifest.get('source_commit')
        if not repo or not recorded:
            return 0
        try:
            out = subprocess.run(['git', 'ls-remote', repo, SOURCE_BRANCH],
                                 capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            return 0  # genuinely unreachable -- stays silent, same as checkin.py's fresh()
        head = out.stdout.split()[0] if out.returncode == 0 and out.stdout else ''
        if head and head != recorded:
            print(f"NOTICE: BestPractice's vendored engine has moved ({head[:12]}; your base "
                  f"{recorded[:12]}) -- refresh with "
                  f"`python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`.")
        elif not head and out.returncode != 0:
            err = (out.stderr or '').strip().splitlines()
            err = err[-1] if err else 'no output'
            print(f"COULD NOT VERIFY: couldn't reach {repo} to check the vendored engine's "
                  f"freshness -- `git ls-remote` failed ({err}). This is NOT the same as "
                  f"'confirmed fresh': if you need to know, verify directly instead of "
                  f"trusting this silence.")
    except Exception:
        pass
    return 0


def _credential_reminder(where):
    """Print, at the vendor-update moment, whether this environment can
    reach its private practice sources at all.

    WHY HERE (asked for by Morgan, 2026-09-09). An update to the vendored
    engine is the one moment somebody is deliberately looking at how a repo
    gets its practices -- and it is also when a new engine file arrives that
    the environment may not be configured for. A credential that was never
    set produces no error at any other time: the sources simply are not
    there, and a session reads the universal catalogue believing it has
    them all. See tools/precedent_source_credentials.py for what that costs
    and what was measured about the fix.

    Never gates. A vendor update is not the place to refuse work over an
    environment setting (practice: fail-gracefully)."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import precedent_source_credentials as psc
    except ImportError:
        return
    line = psc.remind(where, prefix='precedent_vendor_engine')
    if line:
        print(f"\n{line}")


def _cli_record_ci(rest):
    """CLI body of `record-ci`. Clone-free, like `fresh` -- unlike `status`/
    `refresh`, it never reads BestPractice at all, only this repo's own
    manifest and its own CI workflow file(s) on disk, exactly what
    record_ci_workflow_files() needs.

    THE GAP THIS CLOSES. record_ci_workflow_files() already does the right
    thing -- record what's on disk now, touch no content -- but before this
    it was reachable only from inside precedent_install.py/precedent_
    bootstrap_source.py at initial install, or by importing the module and
    calling it directly (which is what fixing two real consumer repos'
    stale post-hand-fix hashes took, 2026-09-19, since neither repo's
    session could run a full `refresh` against a live BestPractice clone
    mid-incident without either leaving the hash stale -- refused by the
    next refresh -- or accepting `refresh --force`
    overwriting the hand-authored fix with the generic template). A session
    in that position needs a supported way to say "this content is correct
    now, just re-baseline" without a clone and without risking an overwrite;
    this is that command.

    Also runs _remove_retired_ci_workflow_files first, so a `record-ci` run
    on a manifest with a stale retired entry does not leave it stranded."""
    if rest:
        sys.exit(f"precedent_vendor_engine FAIL: unknown argument(s) to "
                 f"record-ci: {', '.join(rest)}.")
    dest_tools = ROOT / 'tools'
    manifest = _load_manifest(dest_tools)
    kind = manifest.get('kind', DEFAULT_KIND)
    _remove_retired_ci_workflow_files(ROOT, manifest, kind)
    before = dict(_load_manifest(dest_tools).get('ci_workflows_sha256') or {})
    written = record_ci_workflow_files(ROOT, kind)
    if not written:
        sys.exit(f"precedent_vendor_engine FAIL: no {MANIFEST_NAME} at "
                 f"{dest_tools} to record into -- run `seed` first.")
    after = dict(_load_manifest(dest_tools).get('ci_workflows_sha256') or {})
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    if changed:
        print(f"precedent_vendor_engine record-ci OK ({kind}): re-recorded "
              f"{len(changed)} CI workflow file hash(es) from what's on disk "
              f"right now ({', '.join(changed)}). Content was not touched -- "
              f"this only updates {MANIFEST_NAME}.")
    else:
        print(f"precedent_vendor_engine record-ci ({kind}): already matches "
              f"what's on disk -- nothing to do.")
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == 'fresh':
        return fresh()
    if args and args[0] == 'record-ci':
        return _cli_record_ci(args[1:])
    if len(args) < 2 or args[0] not in ('seed', 'status', 'refresh'):
        sys.exit(__doc__)
    if args[0] == 'seed':
        rest = args[2:]
        kind = DEFAULT_KIND
        if '--kind' in rest:
            i = rest.index('--kind')
            if i + 1 >= len(rest):
                sys.exit("precedent_vendor_engine FAIL: --kind needs a value "
                         f"({', '.join(sorted(KINDS))}).")
            kind = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        if kind not in KINDS:
            sys.exit(f"precedent_vendor_engine FAIL: --kind must be one of "
                     f"{', '.join(sorted(KINDS))}, got {kind!r}.")
        if rest:
            sys.exit(f"precedent_vendor_engine FAIL: unknown argument(s) to seed: "
                     f"{', '.join(rest)}.")
        written = seed(args[1], kind=kind)
        print(f"SEEDED ({kind}): {len(written)} engine file(s) into "
              f"{pathlib.Path(args[1]).resolve() / 'tools'}")
        for f in written:
            print(f"  wrote {f}")
        return 0
    clone = _clone_or_die(args[1])
    if args[0] == 'status':
        rc = status(clone)
        _credential_reminder(ROOT)
        return rc
    rest = args[2:]
    ref = None
    if '--from-ref' in rest:
        i = rest.index('--from-ref')
        if i + 1 >= len(rest):
            sys.exit("precedent_vendor_engine FAIL: --from-ref needs a value "
                     "(a commit or ref inside the clone).")
        ref = rest[i + 1]
        rest = rest[:i] + rest[i + 2:]
    unknown = [a for a in rest if a != '--force']
    if unknown:
        sys.exit(f"precedent_vendor_engine FAIL: unknown argument(s) to "
                 f"refresh: {', '.join(unknown)}.")
    if ref is not None:
        resolved = _rev(clone, ref)
        if not resolved:
            sys.exit(f"precedent_vendor_engine FAIL: --from-ref {ref!r} does "
                     f"not resolve in {clone}.")
        ref = resolved
    rc = refresh(clone, force='--force' in args, ref=ref)
    _credential_reminder(ROOT)
    return rc


if __name__ == '__main__':
    # `--help` is what anyone types first. Before 2026-09-06 the tools here
    # split three ways on it: a hard "unknown option" FAIL, a silent
    # fall-through that ran the whole audit as if nothing had been asked, or
    # the docstring printed with a non-zero exit. All three are wrong, and
    # documentation/FOR_DEVELOPERS.md points readers straight at
    # these commands. The module docstring is the usage text.
    if any(a in ('--help', '-h') for a in sys.argv[1:]):
        print((__doc__ or '').strip())
        sys.exit(0)
    sys.exit(main())

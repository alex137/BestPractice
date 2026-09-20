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
build_codeowners.py, a consumer's own bootstrap.sh/light_check.py/
report_automation_issue.py) that a whole-directory mirror-and-delete would
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

WHAT IS DELIBERATELY IN NEITHER LIST, said out loud because its absence is
what makes a whole class of follow-up work unnecessary. verify_harness.py
(noted again below), and also tools/leak_gate.py and tools/very_deep_check.py:
both run only from a BestPractice checkout, against whatever repositories that
session can see, so improving them reaches every repo the moment this repo's
own copy changes. Nothing to vendor, nothing to refresh.

That is worth stating because the opposite is the natural assumption. On
2026-09-07 a change to those two tools was written up as needing a
per-set engine refresh, and a TODO item was opened saying the sets were
running stale copies -- of files they have never held. The reasoning came
from cross-source-rollout, which is a real practice and simply did not apply
here; nobody checked these lists first. Check them before costing a rollout.

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
                                  list) and updates the manifest.

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

SOURCE_BRANCH is 'precedent-beta-v01', not BestPractice's configured
default branch ('main') — see local/practices/merge-target-is-beta-branch.md:
until Alex's deliberate phase-7 fold-in, routine engine work lands on
precedent-beta-v01, and 'main' is stale for this purpose. That practice's
own retirement clause applies here too: the moment the fold-in happens,
change SOURCE_BRANCH to 'main' in this one place, in the same PR.
"""
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
SOURCE_BRANCH = 'precedent-beta-v01'  # see docstring: NOT the configured default

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
    'doc_lint.py',
    # doc_lint.py's own real-YAML frontmatter check imports this at module
    # level (added 2026-09-20, shared with verify_harness.py's deep-check
    # copy of the same check so the two never drift). Without it doc_lint.py
    # itself fails to import in a consumer -- not a SKIPPED finding, a
    # ModuleNotFoundError on every run, since the import is unconditional at
    # the top of the file. Caught by check_tools_answer_help_without_writing,
    # which copies only the tracked tree and runs every tool's --help there.
    'frontmatter_yaml.py',
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
# WHAT THIS DELIBERATELY DOES NOT DO YET, said out loud rather than silently
# missing (same discipline as the "what is deliberately in neither list"
# passage above). No RETIRED_HOOK_FILES tombstone and no per-kind file list:
# both kinds run the same Claude Code adapter, so every hook applies to
# both. No untracked-hand-copy detector (_untracked_engine_files's hook
# analog) -- a stray hand-copied hook is a real but unmeasured risk, not
# something this pass closes. If a hook is ever renamed or dropped upstream,
# the old copy is left behind in a consumer's .claude/hooks/, the same way
# an engine file used to be before _remove_dropped_engine_files existed --
# a known gap, not a silent one, closed properly if and when it happens.
#
# .claude/settings.json is deliberately NOT vendored here.
# precedent_install.py's _harness() already leaves it alone once it exists,
# on purpose -- a consumer may have wired its own extra hooks alongside the
# vendored ones -- and a routine refresh has no business overwriting a
# repo's own hook wiring. Only the hook SCRIPTS are vendored engine code;
# the settings that call them are the consumer's own.
HOOK_SOURCE_DIR = 'templates/harness/claude-code/hooks'
HOOK_DEST_DIR = '.claude/hooks'


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
                m = _HOOK_CMD_RE.search(h.get('command', '') or '')
                if m:
                    names.add(m.group(1))
    return names


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
    names = sorted((available & wired) - adapter_owned)
    skipped = sorted(available - wired - adapter_owned)
    if skipped:
        print(f"NOTE: precedent_vendor_engine: {len(skipped)} hook script(s) "
              f"BestPractice ships are not wired in this repo's own "
              f".claude/settings.json ({', '.join(skipped)}) -- not vendored. "
              f"That is expected for a hook only a different repo kind wires "
              f"(a practice set vs. a consumer), or one this repo declined on "
              f"purpose.", file=sys.stderr)
    for n in sorted(adapter_owned & wired):
        source_name = claimed[f'{HOOK_DEST_DIR}/{n}']
        print(f"NOTE: precedent_vendor_engine: {n} is not vendored by this "
              f"engine -- {source_name!r}'s own adapters mechanism owns "
              f"{HOOK_DEST_DIR}/{n} in this repo (see precedent_materialize.py's "
              f"MANIFEST.json). That copy is maintained independently; this "
              f"engine's own bundled {n} is not applied here.", file=sys.stderr)
    if not names:
        return []
    dest_hooks = dest_root / HOOK_DEST_DIR
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

    manifest_path = dest_root / 'tools' / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['hook_files'] = names
    manifest['hooks_sha256'] = hashes
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                             encoding='utf-8')
    return written


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
CI_WORKFLOW_TEMPLATES = {
    'consumer': (
        ('doc-lint.yml.template', '.github/workflows/bestpractice-docs.yml'),
        ('leak-gate.yml.template', '.github/workflows/leak-gate.yml'),
    ),
    'source': (
        ('precedent-check.yml.template', '.github/workflows/precedent-check.yml'),
        ('leak-gate.yml.template', '.github/workflows/leak-gate.yml'),
    ),
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
    for rel, recorded_hash in (manifest.get('ci_workflows_sha256') or {}).items():
        if rel in RETIRED_CI_WORKFLOW_FILES:
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
    return [rel for rel in on_disk
            if rel not in tracked and rel not in RETIRED_CI_WORKFLOW_FILES]


def _remove_retired_ci_workflow_files(dest_root, manifest):
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
    dropped = sorted(rel for rel in recorded if rel in RETIRED_CI_WORKFLOW_FILES)
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
            print(f"WARN: precedent_vendor_engine: {rel} was retired "
                  f"({RETIRED_CI_WORKFLOW_FILES[rel]}) and has been hand-"
                  f"edited since the manifest last recorded its hash -- left "
                  f"in place, not deleted. Move the edit upstream, then "
                  f"delete it by hand once its replacement is confirmed "
                  f"working.", file=sys.stderr)
    if deleted:
        print(f"precedent_vendor_engine refresh: deleted {len(deleted)} "
              f"retired CI workflow file(s), unmodified since the manifest "
              f"last recorded them ({', '.join(deleted)}).")
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
    refreshed, catchup = [], []
    for template, rel in CI_WORKFLOW_TEMPLATES.get(kind, ()):
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
    if not manifest.get('hook_files'):
        print(f"  NOTE: this manifest has no hook_files recorded yet -- vendored before hook "
              f"scripts were tracked. `refresh` will pick them up on the next run.")
    ci_drift = _ci_workflow_drift(ROOT, manifest)
    for rel, why in ci_drift:
        print(f"  LOCAL DRIFT: {rel} -- {why}")
    if not manifest.get('ci_workflows_sha256'):
        print(f"  NOTE: this manifest has no ci_workflows_sha256 recorded yet -- vendored "
              f"before CI workflow files were tracked. `refresh` will record a baseline "
              f"for them (not rewrite them) on the next run.")
    drift = drift + hook_drift + ci_drift
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
    _remove_retired_ci_workflow_files(ROOT, manifest)

    if not force:
        drift = (_local_drift(dest_tools, manifest) + _hook_drift(ROOT, manifest)
                 + _ci_workflow_drift(ROOT, manifest))
        if drift:
            for name, why in drift:
                print(f"  {name}: {why}")
            sys.exit("precedent_vendor_engine FAIL: a vendored engine, hook or CI "
                     "workflow file was hand-edited since the last seed/refresh -- "
                     "refreshing would silently discard that edit. Move the edit "
                     "upstream into BestPractice instead (this engine has no local "
                     "variance by design), or pass --force to overwrite anyway.")

    new_commit, engine_dir = _source_tools_at(clone, kind, ref=ref,
                                              fetch=ref is None)
    try:
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
        # No hook analog of set_orphaned -- see HOOK_SOURCE_DIR's own comment
        # on the deliberately-missing tombstone/removal mechanism.
        new_hook_names = set(_hook_file_names(engine_dir / 'hooks')) & _wired_hook_names(ROOT)
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

        if new_commit == manifest.get('source_commit') and not force \
                and not set_incomplete and not hooks_incomplete and not ci_incomplete:
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
                  f"({', '.join(hooks_incomplete)}) -- refreshing anyway. This is the "
                  f"one-time catch-up for a repo vendored before hooks were tracked "
                  f"at all (manifest has no 'hook_files' yet).")
        if ci_incomplete and new_commit == manifest.get('source_commit'):
            print(f"NOTICE: the recorded commit already matches, but this "
                  f"repo's CI workflow file(s) need attention "
                  f"({', '.join(ci_incomplete)}) -- refreshing anyway.")

        self_before = _sha256(HERE) if HERE.is_file() else None
        written = _write_engine_files(dest_tools, engine_dir, new_commit, kind)
        # AFTER the write, and using the manifest as it was BEFORE it:
        # _write_engine_files rewrites `files` from the current KINDS list, so
        # by then the dropped name is already gone from the record and there
        # is nothing left to find it by. `manifest` is the copy loaded at the
        # top of this function, which is the one that still remembers.
        _remove_dropped_engine_files(dest_tools, manifest, kind)
        written += _write_hook_files(ROOT, engine_dir / 'hooks')
        ci_refreshed, ci_catchup = _refresh_ci_workflow_files(
            ROOT, kind, engine_dir / 'ci-workflows', manifest)
        written += [ROOT / rel for rel in ci_refreshed]
    finally:
        shutil.rmtree(engine_dir, ignore_errors=True)
    print(f"precedent_vendor_engine refresh OK ({kind}): {len(written)} file(s) refreshed "
          f"from {SOURCE_BRANCH} @ {new_commit[:12]} (was {manifest.get('source_commit', '?')[:12]})")
    if ci_refreshed:
        print(f"precedent_vendor_engine refresh: refreshed {len(ci_refreshed)} CI "
              f"workflow file(s) to the current template ({', '.join(ci_refreshed)}).")
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
        r = subprocess.run(
            [sys.executable, str(HERE), 'refresh', str(clone), '--force']
            + (['--from-ref', ref] if ref else []),
            env={**os.environ, _SECOND_PASS_ENV: '1'})
        if r.returncode != 0:
            return r.returncode

    _warn_bare_sync_invocations(ROOT)
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
                "to each line; these files are not in the engine manifest, so "
                "a refresh never rewrites them.")


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
    _remove_retired_ci_workflow_files(ROOT, manifest)
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

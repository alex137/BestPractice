<!-- Last updated: 2026-09-03 (Buenos Aires) by a follow-up session, after old-system vocabulary was found lingering in WorkingWithAI a day past its own migration -->

# Migrating a repo that already has BestPractice installed

[INSTALL.md](../INSTALL.md) describes installing BestPractice fresh, and
[spec/SOURCES.md](SOURCES.md) / [spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md)
describe Precedent's three-source model and how the two private sets got
populated. Neither one is written for the repo in between: one that
already vendored BestPractice the old way (`process/upstream/` tracking
`main`, plus a second vendored tree for a personal/domain pack) and now
wants to adopt the three-source model on top of that existing install,
rather than starting from a blank page. This document is that missing
piece — **the recommended pattern**, not a plan, written from having
actually done it once, on a real repo, for the first time.

**Worked example: `themorgan/WorkingWithAI`.** Everything below generalizes
what that repo's own migration actually did on 2026-09-02, first tested
against the real `precedent-team-maintainers` and `precedent-individual`
repos rather than fixtures. Its own record —
[process/PRECEDENT_MIGRATION.md](https://github.com/themorgan/WorkingWithAI/blob/main/process/PRECEDENT_MIGRATION.md)
(dependent repo, private; not fetchable from a BestPractice-only session) —
covers repo-specific detail this document deliberately leaves out; treat
this document as the pattern, that one as the instance. Its `TODO.md`
"Decisions" section carries the same change as a one-paragraph log entry,
per that repo's own conventions.

## When this applies

A repo whose `process/manifest.json` records an `upstream.repo` pointing at
BestPractice, **and** which has some second vendored tree for
domain/team/personal rules that did not come from BestPractice itself (a
"personal pack," a compliance pack, anything installed under
[layered-practice-packs](../PRACTICES.md#23-a-layered-set-of-practice-packs-generic-domain-repo-local)'s
old pack mechanism) — where that second tree's *source* repo has since
split, or is splitting, into Precedent-shaped team/individual sets. If the
second tree's source repo has no plans to split, there's nothing to
migrate: the pack mechanism, described in
[layered-practice-packs](../PRACTICES.md#23-a-layered-set-of-practice-packs-generic-domain-repo-local)'s
own Install section, is still supported for a repo that hasn't migrated to
the loader.

## The pattern

1. **Re-vendor `process/upstream/`.** If tracking a real, released
   BestPractice branch (the normal case once a Precedent-carrying branch
   has merged to `main`), this is an ordinary
   [INSTALL.md §2](../INSTALL.md#2-take-an-upstream-update) update:
   `checkin.py update` / `record`, three-way-merged per manifest entry. If
   — as `WorkingWithAI` deliberately did, to beta-test this exact pattern —
   the repo is pinning a **named non-default branch** ahead of its merge,
   read "The default-branch gotcha" below first: `checkin.py`'s automated
   commands cannot track a named branch, so this step becomes a one-off
   manual mirror instead, and the scheduled sync workflow must be paused
   for the duration.

2. **Confirm the second tree's source has actually split**, and where each
   half landed, before touching anything local. Read that source's own
   README(s) for the allocation: which practices are genuinely
   person-specific (an individual set: commit identity, a timezone, a
   naming convention, a shorthand — see
   [spec/PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md)'s own "person-specific
   handful" inventory for the shape) versus everything else, which defaults
   to team ("narrowest first" — promoting team to universal is a designed
   path; demoting a universal practice back down is not).

3. **Add `precedent.json`** at the repo root, declaring:
   - `level: "universal"` pointing at `process/upstream` — **stays a real
     vendored copy**, not a live path reference, even though Precedent's
     own self-hosted `precedent.json` uses `path: "."`. A dependent repo
     needs the vendored tree for offline work, for a collaborator or CI
     runner without a sibling BestPractice checkout, and for
     `process/manifest.json`'s own per-file drift tracking — none of which
     a live reference provides. Vendoring stays; only the *second* source
     moves off it.
   - `level: "team"` pointing at a relative path to a sibling clone of the
     team repo (`../<team-repo-name>`) — **not** vendored. A team set that
     already has its own maintained repo (unlike a domain pack with no repo
     yet) is resolved live, the same way Precedent's own `precedent.json`
     resolves `precedent-team-maintainers` for itself. On a hosted agent
     platform, resolving it live needs the session to actually have git
     read access to that sibling repo — step 4 below covers this gap and
     its fix together with the individual source's identical one; don't
     stop at declaring the path here and assume access follows.
   - **Never** a `level: "individual"` entry — `tools/precedent_resolve.py`
     refuses this by name, with the privacy reason in the message, and for
     good reason: naming a person's individual set in a repo anyone else on
     the team can read leaks that set's existence and location to them.
   - `level: "repo-local"`, if the old pack tree (or the old instructions
     file directly) carried rules true only of *this* repo's own subject
     matter, per [layered-practice-packs](../PRACTICES.md#23-layered-practice-packs-a-domain-layer-between-generic-and-repo-local)'s
     own decision rule ("only here?"). `path: "local"` — a subdirectory,
     holding `local/practices/*.md` — not the bare repo root
     (`path: "."`): the root's own `practices/` is where
     `tools/precedent_sync_views.py` writes its resolved output, and a
     repo-local source declared there collides with that (see this
     document's own "Known gap" section below for what that collision
     actually does, reproduced, not theoretical).

4. **Wire the individual source's own bootstrap, if the person has one and
   the harness needs it.** For a Claude Code Web session specifically, this
   is the individual repo's own
   `claude-web-bootstrap` practice (see that repo's own `practices/` for
   the exact slug and file) — copy its `bootstrap/session-start.sh` into
   the target repo as a tracked `.claude/hooks/<name>-bootstrap.sh`
   (**copied**, not referenced by a `$HOME`-relative path — on a brand-new
   container nothing under `$HOME` exists yet, so the hook that populates
   `$HOME` cannot itself live there), and merge its
   `bootstrap/settings.snippet.json` into the target's own
   `.claude/settings.json` (append to an existing `SessionStart` array,
   don't replace it). This makes the individual source resolvable without
   ever naming it in the repo's own tracked config — but on its own it is
   **not** zero manual steps on a hosted agent platform, which is the next
   part of this step, not a separate concern.

   **The session-repo-access gate, and the one behavioral fix that closes
   it for both sources at once.** On Claude Code Remote/Web, a session's
   git access is scoped *per session* — attached when it's created, or
   added mid-session — never inherited just because a project's config or
   a hook references another repo by name. A brand-new session opened on
   only the consuming project has no git credentials for either sibling
   repo at all, so the individual bootstrap hook above, and the team
   source's live resolution in step 3, both fail on a fresh session with
   nothing wrong in the code — until this gate is closed.

   **This costs no token or secret.** The tool that extends a session's
   scope to another repo (`add_repo` in Claude Code Remote/Web) rides the
   *same* GitHub identity already behind that session; it only ever
   succeeds because the person is already a collaborator on the target
   repo — the same fact that let them declare the source at all. There is
   nothing to generate, store, or rotate.

   **What actually closes the gap is an instruction to the agent, not to
   the hook.** A `SessionStart` shell hook cannot grant its own session
   more repo access — that is an agent-level action, not a shell command
   — so the fix cannot live in `bootstrap/session-start.sh` no matter how
   it's written. It has to live in the consuming repo's own `AGENTS.md`,
   as a plain instruction to the agent: **call `add_repo` (read access)
   for both the team and individual sibling repos at the very start of
   every session, before running any bootstrap script, without asking
   first.** Not "if the clone fails, ask to add the repo" — that only
   works when a human happens to be watching for the failure, and the
   whole point is that a person only ever attaches the *one* repo they're
   actually working in. Reaching for the other two has to be the
   session's own job, every single time, since repo access is a
   per-session grant that does not persist to the next one. `add_repo`
   granting only read access, and this being a reversible, no-cost scope
   extension rather than anything touching credentials or production,
   is exactly why it doesn't need to wait for a human's yes first.

   `WorkingWithAI`'s own migration got this wrong on the first pass —
   its `AGENTS.md` said to *ask* to add the repo once a clone had already
   failed — and its fix is the pattern to copy (private repo, not
   fetchable from here, but the shape: state plainly that no credential
   is needed, then instruct the agent to call `add_repo` for both sources
   unconditionally, ahead of the clone hook, every session).

5. **Retire the old vendored pack tree**, but salvage anything in it that
   was never really *pack content* — a generic utility script the pack
   happened to carry (a light-check runner, an issue-reporter), not a rule.
   Relocate those to the consuming repo's own `tools/`, since they're
   repo-owned infrastructure now, not something with an upstream to sync
   against. Delete the pack's own manifest file, its README, its templates.
   Anything the pack's own tooling depended on (a merge-runbook file-class
   rule naming the old manifest, a CI workflow calling the old tool path)
   needs the same update.

   **Scrub the old system's whole vocabulary now, in this same migration —
   never as a separate cleanup someone has to ask for later**
   ([migration-scrubs-vocabulary](../practices/migration-scrubs-vocabulary.md)).
   This is broader than the file paths above: the old system's real name,
   any secret or token name it used, and every paragraph that explains
   what a now-retired workflow *used to do* — grep the whole repo, not
   just the obvious files (this repo's own conventions doc, glossary, map,
   onboarding page, and any comment inside a workflow configuration file
   (YAML) that used the old system as a running example) before
   considering this step done. Declare what
   you find once, don't decide file-by-file: write
   `process/retired_vocabulary.json` —
   ```json
   {
     "terms": ["<the old repo or system's real name>", "<a retired secret name>", "..."],
     "exempt_files": ["process/PRECEDENT_MIGRATION.md", "TODO.md", "<any file that is explicitly a historical log by its own stated purpose>"]
   }
   ```
   — then run `python3 process/upstream/tools/precedent_check.py --only migration-scrubs-vocabulary` and don't call this step done until it passes. The exempt list is deliberately short: the migration record itself, plus files whose *own stated purpose* is a historical log (a decision-record directory, a dated brainstorm journal) — never a file merely because it happens to still mention the old system. Leaving that config in place afterward means the check keeps watching: any *new* mention that creeps back in during a later edit fails the same way.

6. **Retire the old sync workflow entirely** (there is nothing left to
   vendor-and-sync for the team/individual sources — they resolve live).
   Keeping the sibling clones themselves fresh becomes a session-start
   concern (a best-effort `git pull --ff-only` for the team clone; the
   individual clone's own bootstrap script does the same for itself), not
   a scheduled GitHub Actions job.

7. **Rewrite the consuming repo's own instructions file** (`AGENTS.md` or
   equivalent) with the same `<!-- BEGIN GENERATED: precedent-loader -->` /
   `<!-- END GENERATED -->` markers this repo's own `AGENTS.md` uses, then
   run `python3 tools/precedent_sync_views.py` (vendor it alongside
   `precedent_resolve.py`, `precedent_materialize.py`, `build_views.py`,
   `precedent_show.py`, `precedent_paths.py`, `precedent_gate.py`, and
   `split_practices.py` — all together, at the consuming repo's own
   `tools/`, not nested under `process/upstream/tools/`, which stays
   reserved for the audit/sync tools that operate on the vendored
   universal tree itself) to fill them in from the *real* resolved set —
   universal, team, individual and repo-local, all four. **Don't hand-curate
   a subset and call it a stopgap**: that was only ever necessary because
   nothing connected the resolver's output to a generated view; now
   something does, so there's nothing to approximate by hand. The
   temptation to inline the team/individual catalogues the way the old
   pack was inlined in full still applies just as much as it always did —
   resist it; the generated block *is* the non-duplicated form.

8. **Validate for real**, not against a fixture: `python3
   tools/precedent_sync_views.py --repo .` from the consuming repo, with
   its `precedent.json` and a real user-level individual config in place.
   Check the reported precedence, any `overridden`/`blocked` entries, the
   combined resident-block budget, and that the generated `AGENTS.md`
   actually names practices from every source that's supposed to be in
   play — this is the first place any of that runs against real content
   rather than the verification harness's synthetic sources. Re-run with
   `--check` on a second pass to confirm it's stable (byte-identical,
   nothing left to regenerate) before committing the result.

## The default-branch gotcha

`tools/checkin.py`'s `fresh`, `update`, and `record` commands all resolve
the **remote's default branch** unconditionally
(`_default_branch()` reads `refs/remotes/origin/HEAD`) — there is no
parameter to say "track this named branch instead." A repo doing exactly
what this document describes — beta-testing a not-yet-merged branch, as
`WorkingWithAI` did against `precedent-beta-v01` — cannot use these
commands for that branch: `fresh` will report "moved" every single session
(comparing the pinned branch's commit against `main`'s HEAD, an unrelated
lineage), and an unattended `update` run would try to merge `main`'s tree
over the deliberately-pinned vendored copy.

**Handle it explicitly, don't let it surprise the next sync:**
- Do the vendor as a one-off manual mirror (replace the tree wholesale from
  a checkout of the named branch), not `checkin.py update`.
- Record the branch name in `process/manifest.json` (add an `upstream.branch`
  field; the schema doesn't have one by default, but the field costs
  nothing and every subsequent session needs to see it) alongside a `_note`
  explaining why automated sync is paused and when to lift it.
- Pause the scheduled sync workflow's schedule (comment it out; leave
  `workflow_dispatch` for a manual run) with a header comment pointing at
  the same note, and guard any unattended prompt text so a manual trigger
  stands down rather than silently assuming default-branch semantics.
- Re-enable once the branch merges to the default branch and
  `process/manifest.json` is repointed there.

## A real finding: the scrub check has no notion of "already public upstream"

Running `practice_audit.py`'s scrub check against a repo whose owner is
*also* a disclosed, named contributor to BestPractice/Precedent itself (not
a hypothetical — this is exactly `WorkingWithAI`'s situation, and exactly
why the check surfaced it) can fail on content that isn't actually a leak:
the owner's real identity, disclosed on purpose in BestPractice's own
public docs narrating the real work of populating the private sets, happens
to match that owner's own private-repo blocklist entries for the same
identity, entered there to protect a *different*, unrelated context.

The scrub check's assumption — anything under `process/upstream/` should
already be public-safe because it mirrors a public repo verbatim — has no
way to tell "this term arrived already-public, disclosed by upstream
itself" apart from "this term leaked in via a local edit or a bad merge."
Both the blocklist and the check are working as designed; they weren't
designed for one person occupying both roles at once. Weakening a
blocklist entry to silence this would also weaken it against the failure
mode it actually exists for.

**Not fixed here** — `WorkingWithAI`'s own record documents it as an
accepted, understood FAIL for that specific vendored tree rather than
something to patch around. The shape of a real fix: scrub the **diff**
against the last-recorded upstream commit, not the whole snapshot every
time — the same move `tools/leak_gate.py`'s push-time check already made
(walking a commit range rather than scanning a working tree), for the same
reason (a snapshot scan can't distinguish "always been there, already
disclosed" from "just arrived"). Worth a proper fix in `practice_audit.py`
itself; flagged here rather than attempted, since it touches a checked-in
gate every dependent repo relies on and deserves its own pass, not a
side-effect of a migration writeup.

## Known gap this migration ran into — closed 2026-09-03, read this for what changed

**This section used to say the cross-source consumer-repo view was
unbuilt, and that step 7 below hand-curates a stopgap because of it.**
That's no longer true, and the fix corrects a framing this document itself
had slightly wrong, not just a missing feature.

`precedent_show.py`, `precedent_paths.py`, and `precedent_gate.py` — the
three loading channels that pull a slug's `## Rule` text into context
automatically — are still single-source, and stay that way on purpose:
each hardcodes its own repo as `ROOT` and only ever reads
`<that repo>/practices/`. **The fix was never to make these three
multi-source-aware.** It was to materialize a real, ordinary,
single-source `practices/` directory *from* the multi-source resolution,
and point these same, unmodified tools at that — which
[tools/precedent_materialize.py](../tools/precedent_materialize.py)
already did, tested, before this gap was even written down (phase 5); the
gap this document originally named was really that nobody had connected
that tool to `build_views.py`'s own `AGENTS.md` generation in one
documented, consumer-facing command.

That connection is [tools/precedent_sync_views.py](../tools/precedent_sync_views.py)
now: `python3 tools/precedent_sync_views.py [--repo DIR]` resolves every
declared source, materializes the merged `practices/` + `tools/checks/`,
and regenerates `AGENTS.md`'s loader block from the *same* resolved
practices (not re-read from disk) — one command, in place of step 7's old
hand-curated stopgap below.

**Finishing this surfaced a real bug, not just a missing convenience.**
`precedent_materialize.py` deletes and rewrites the output `practices/`
directory; a repo-local source declared at the bare repo root
(`path: "."`, this document's own earlier examples) has its own
hand-authored `practices/` at exactly that same path. Materializing into
a repo that also self-sources at its own root either crashed (reading a
file the tool had just deleted) or, worse, silently overwrote a
hand-authored file with a different source's winning content the moment
another source shadowed a repo-local slug — reproduced directly, not
theoretical. Fixed two ways: `precedent_materialize.py` now reads every
source file into memory before deleting anything, so the crash and the
silent-overwrite-with-no-trace case are both gone; and repo-local's
recommended `path` is now a subdirectory (`"local"`, holding
`local/practices/`), which keeps the hand-authored source and the
materialized output physically apart regardless. `path: "."` still
resolves — `tools/precedent_resolve.py`'s validation only refuses a path
OUTSIDE the repo — it just isn't the recommended shape anymore for a repo
that also runs `precedent_sync_views.py` against its own root.

Tested against a real four-source fixture, not just reasoned about
(`check_sync_views_cross_source` in
[tools/verify_harness.py](../tools/verify_harness.py)); not yet run
against a real consumer repo with real content — that is exactly what
this document's own migration pattern is for, next.

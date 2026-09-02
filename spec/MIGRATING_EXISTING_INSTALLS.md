<!-- Last updated: 2026-09-02 (Buenos Aires) by the first real Precedent beta-test session -->

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
     resolves `precedent-team-maintainers` for itself.
   - **Never** a `level: "individual"` entry — `tools/precedent_resolve.py`
     refuses this by name, with the privacy reason in the message, and for
     good reason: naming a person's individual set in a repo anyone else on
     the team can read leaks that set's existence and location to them.

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
   don't replace it). This is what makes the individual source resolvable
   with zero manual steps, on every fresh session, without ever naming it
   in the repo's own tracked config.

5. **Retire the old vendored pack tree**, but salvage anything in it that
   was never really *pack content* — a generic utility script the pack
   happened to carry (a light-check runner, an issue-reporter), not a rule.
   Relocate those to the consuming repo's own `tools/`, since they're
   repo-owned infrastructure now, not something with an upstream to sync
   against. Delete the pack's own manifest file, its README, its templates.
   Anything the pack's own tooling depended on (a merge-runbook file-class
   rule naming the old manifest, a CI workflow calling the old tool path)
   needs the same update — grep the whole repo for the old tree's path
   before considering this step done; it touches more files than the
   obvious ones (this repo's own conventions doc, glossary, map, and any
   essay or brainstorm document that used the old pack as a running example
   of some mechanism, not just its own instructions file).

6. **Retire the old sync workflow entirely** (there is nothing left to
   vendor-and-sync for the team/individual sources — they resolve live).
   Keeping the sibling clones themselves fresh becomes a session-start
   concern (a best-effort `git pull --ff-only` for the team clone; the
   individual clone's own bootstrap script does the same for itself), not
   a scheduled GitHub Actions job.

7. **Rewrite the consuming repo's own instructions file** (`AGENTS.md` or
   equivalent). The temptation is to inline the team/individual catalogues
   the same way the old pack was inlined in full — resist it: that is
   exactly the duplication a repo's own `no-duplication`-shaped rule warns
   against, now generalized past "don't restate BestPractice" to "don't
   restate any resolved source." Point at
   `precedent_resolve.py --repo .` for the real merged set, and — because
   of the loading-channel gap below — hand-curate only the resident
   practices (always needed) plus the handful of on-demand practices the
   repo's own daily operation actually depends on, explicitly labeled as a
   stopgap rather than a substitute for the full catalogue.

8. **Validate for real**, not against a fixture: `precedent_resolve.py
   --repo .` from the consuming repo, with its `precedent.json` and a real
   user-level individual config in place. Check the reported precedence,
   any `overridden`/`blocked` entries, and the combined resident-block
   budget — this is the first place any of that runs against real content
   rather than the verification harness's synthetic sources.

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

## Known gap this migration ran into, not created

`precedent_show.py`, `precedent_paths.py`, and `precedent_gate.py` — the
three loading channels that pull a slug's `## Rule` text into context
automatically — are single-source as of `precedent-beta-v01`: each
hardcodes its own repo as `ROOT` and only ever reads `<that repo>/practices/`.
Only `precedent_resolve.py` merges all three sources. A migrated repo's
`AGENTS.md` therefore cannot yet regenerate its own resident block or
occasion index automatically from the full resolved set the way this
repo's own does from its single source — step 7's hand-curated stopgap
exists specifically because of this gap, not as a stylistic choice.
Building the cross-source equivalent of `precedent_show.py` (and,
eventually, a `build_views.py` analogue that can run from a consuming
repo) is real future work this migration surfaced but did not attempt —
scope-creeping a loader feature into a migration was judged worse than
naming the gap plainly and moving on.

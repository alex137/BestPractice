<!-- Last updated: 2026-09-02 (Buenos Aires) by the phase-5 deep-check session -->

# Phase 5 Deep-Check — What Was Actually Found

[spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s own "For the session that
deep-checks this before Phase 6" section asked for exactly this: adversarial
pressure on the real creation-pipeline tooling, real candidates run through
[tools/precedent_promote.py](../tools/precedent_promote.py) and
[tools/precedent_land.py](../tools/precedent_land.py) for real, and a fresh run of
every repo's own deep-check suite rather than trusting last session's green
run. This is that session's account — five real bugs found and fixed
across the pipeline and documentation tooling, two real candidates landed
end to end, the step-5 loader-bridge gap closed and proven against the
real private sets, and a fresh harness run across all three repos that
found real, pre-existing drift nobody had caught yet. Written the way
[spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s
own "Two real bugs this phase's own harness work found" section is written:
what broke, not just that something was checked.

## Four real bugs found in the pipeline tooling, all fixed with a planted harness case

Found by actually constructing the adversarial input the brief named as
"not yet applied," not by reading the code and reasoning it looked fine —
[practices/checkable-gets-checked.md](../practices/checkable-gets-checked.md)'s
own discipline, applied to this phase's own tools rather than only to the
catalogue they enforce. All four now have a planted regression case in
[tools/verify_harness.py](../tools/verify_harness.py)'s
`check_creation_pipeline_fires` (13 stated cases, up from 8) or its own new
`check_detect_restated_fires` (2 stated cases, previously zero).

1. **Same-day recurrence collision (the brief's own named, not-yet-fixed
   bug).** `precedent_candidate.py create`'s file name is
   `<slug>-<date>.md`; `cmd_create` refused outright on a second same-day
   raise of the same slug, instead of registering it as recurrence. Fixed:
   a collision now suffixes a sequence number (`-2.md`, `-3.md`, …).
   [spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s own "known bug" section is
   updated in the same commit as the fix, per the team practice landed
   below.

2. **Recurrence counted by filename prefix, not parsed identity.**
   `check_recurrence_or_cost`'s file count used
   `cand_dir.glob(f'{slug}-*.md')` — which also matches a *differently*-
   slugged candidate that merely shares a name prefix. Raising a one-time
   candidate `foo` alongside an unrelated candidate `foo-bar` made `foo`
   silently read as having recurred twice, passing Stage 3's recurrence
   criterion with no real second occurrence. Fixed: counts by each file's
   own parsed `slug:` field. This is the real, non-fixture individual-level
   candidate landed below (`match-parsed-id-not-prefix`).

3. **A `## Proposed Rule` heading inside Observed prose corrupted the
   split.** Both `precedent_promote.py`'s `_load_candidate` and
   `precedent_land.py`'s observed-text extraction split a candidate's body
   on the *first* occurrence of the literal line `## Proposed Rule`. An
   Observed section that itself quotes that heading (plausible for any
   candidate describing a heading collision, or one that pastes markdown)
   truncated Observed and folded the rest of it into the landed practice's
   `## Rule`. Confirmed by planting exactly that candidate and watching the
   real proposed-rule text get replaced with the wrong content. Fixed with
   a shared `precedent_candidate.split_candidate_sections()` that splits on
   the *last* such heading line instead, used by both call sites.

4. **A landed candidate stayed `status: open` forever.** `status: promoted`
   was a declared valid value ([tools/precedent_candidate.py](../tools/precedent_candidate.py)'s `STATUSES`) that
   nothing ever set — `precedent_land.py` never touched the source
   candidate file after a successful land. Confirmed on the real
   `match-parsed-id-not-prefix` candidate below: `list --status open` kept
   showing it after it had already become a real practice. Fixed:
   `precedent_land.py` now rewrites the candidate to `status: promoted` on
   success, via a `set_candidate_status()` helper shared with `cmd_expire`.

Also fixed, adjacent to the same adversarial pass over
[tools/precedent_candidate.py](../tools/precedent_candidate.py)'s hand-rolled frontmatter parser (the brief's own
"stress-test the narrow parser" item):

- An embedded newline in a scalar field (a pasted multi-line title, most
  plausibly) silently corrupted the frontmatter — the written line broke
  across two physical lines, which the line-oriented reader then
  mis-parsed into a bogus extra key with no value. Fixed: `_yaml_scalar`
  now escapes embedded newlines (and quotes commas/brackets defensively)
  the same way it already escaped quotes; `_parse_frontmatter` reverses it.
- A list field (`proposed_applies_to`, `proposed_gates`) containing a
  comma, bracket, or quote inside one item broke the naive
  `inner.split(',')` reader. Fixed with a quote-aware list splitter
  (`_split_list_items`). Both confirmed by round-tripping adversarial
  fixtures through `render_candidate` → `_parse_frontmatter` before and
  after the fix.

**`precedent_promote.py`'s non-duplication default was also fixed**, per the
brief's own "worth deciding, but decide on purpose" framing rather than a
bug: `--against` used to default to `[ROOT]` (this repo, universal)
regardless of the candidate's own level, so promoting an individual or team
candidate with no explicit `--against` never checked it against that
candidate's own repo's catalogue. Confirmed by landing a team candidate that
exact-slug-collided with a real practice already in a fixture team
catalogue — it promoted cleanly with no `--against` passed. Fixed: a new
`precedent_promote.default_against()` (shared with `precedent_land.py`)
derives the candidate's own repo from its file path and always includes it
alongside universal.

## Two real candidates landed end to end, for real, not a fixture

Per the brief's explicit ask ("run it through `precedent_promote.py` and
`precedent_land.py` for real, at least once each for individual and team
level"). Both promoted checking all three real sources together (99–100
real practices, not a fixture catalogue), landed with a real approver name,
and are now genuinely live in their target repos' working trees on this
branch:

- **Individual** — [`match-parsed-id-not-prefix`](https://github.com/themorgan/precedent-individual/blob/claude/bestpractice-deep-test-tkb03u/practices/match-parsed-id-not-prefix.md),
  landed in `precedent-individual` with the owner's own approval, per that
  level's design. The bug-2 story above, written up as a portable practice
  for any codebase, not just this one.
- **Team** — [`resolved-issue-note-updates`](https://github.com/themorgan/precedent-team-maintainers/blob/claude/bestpractice-deep-test-tkb03u/practices/resolved-issue-note-updates.md),
  landed in `precedent-team-maintainers` with a real approver's name from
  that repo's own `approvers.json`. Raised from watching
  [spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s own "not yet fixed" bug note go
  stale the moment this session fixed the bug it described — applied to
  itself in the same commit as the fix, immediately below.

Landing the team candidate pushed `precedent-team-maintainers` to 41
practices, which immediately tripped that repo's own `no-stale-counts`
check against its README's hand-typed "40 practices" — fixed in the same
pass (dropped the number rather than bumping it, per that check's own rule).

`precedent_detect.py restated` was also run for real across all three
sources together (this repo, `precedent-individual`,
`precedent-team-maintainers`) for the first time — the brief's own note
that it "only ever ran individual-vs-team." Found nothing, which a planted
adversarial reword (a genuine near-duplicate, confirmed to fire) shows is a
true negative, not a silently broken detector. That planted case is now
`check_detect_restated_fires` in the harness, since this subcommand had no
harness coverage before this pass at all.

## Fresh harness run across all three repos found real, pre-existing drift

Per the brief's own warning not to assume last session's green run is still
green. `BestPractice`'s own five-tool deep check
([tools/verify_harness.py](../tools/verify_harness.py)/[tools/doc_lint.py](../tools/doc_lint.py)/[tools/leak_gate.py](../tools/leak_gate.py)/[tools/precedent_check.py](../tools/precedent_check.py)/[tools/doc_sync.py](../tools/doc_sync.py))
is clean. Re-running each private repo's own `tools/checks/tests/run_all.sh`
— which nothing in this session's own work had touched — found four
pre-existing failures, none introduced by this session, that had gone
unnoticed since they were committed:

- **`precedent-individual`, commits `ac525c9`/`0016903`**: authored as
  `Claude <noreply@anthropic.com>` at `+0000`, violating that repo's own
  `commit-author` (should be the identity that practice names) and
  `buenos-aires-dates` (should carry the `-0300` offset from setting the
  `TZ` (timezone) environment variable to `America/Argentina/Buenos_Aires`)
  practices. Both commits are already
  pushed — per `no-rewrite-for-warnings`, **not rewritten here**; flagged
  for Morgan's own call on whether the historical violation is worth
  anything more than noting. This session's own commit to that repo (the
  `match-parsed-id-not-prefix` landing) is authored correctly, going
  forward, per that same practice.
- **`precedent-team-maintainers`, four merge/dev commits**: no `Session:`
  trailer. Three are GitHub-UI merge commits with no custom body (a human
  merge, structurally can't carry one without deliberate authoring); one
  (`61f2ed8`) is a real session commit that *does* carry a session link,
  just under the key `Claude-Session:` rather than the literal `Session:`
  the check's regex requires. **This is a live calibration gap, not
  something this session judged and fixed**: [precedent-team-maintainers/practices/session-trailer.md](https://github.com/themorgan/precedent-team-maintainers/blob/claude/bestpractice-deep-test-tkb03u/practices/session-trailer.md)'s Rule
  text names only `Session:`, and this session's own attribution
  convention is `Claude-Session:` — the two have never agreed, so every
  Claude Code commit to this repo will keep tripping this check on the key
  name alone until one of them changes. Worth Morgan's decision: teach the
  check to also accept `Claude-Session:`, or have sessions add a literal
  `Session:` line too. This session's own commit to that repo carries both
  keys, to pass the check as currently written without presuming which way
  the rule should change.

## The leak gate's vocabulary layer — miscalibrated, confirmed and fixed

The brief asked whether
[`precedent-individual/leak-blocklist.txt`](https://github.com/themorgan/precedent-individual/blob/main/leak-blocklist.txt)
is miscalibrated or whether the vocabulary layer has simply never run
clean. Running it for real against this branch's current tree
(`PRECEDENT_LEAK_BLOCKLIST` pointed at the real file, `git config
precedent.requireVocabulary true`, reverted immediately after) found **51
hits, every single one** on exactly two patterns: `\bthemorgan\b` and
`\bBuenos\s+Aires\b` (plus the one literal
`\bAmerica/Argentina/Buenos_Aires\b` timezone (TZ) string). Zero hits on
any other line in the blocklist — the email, the account-ID-shaped number,
or any of the other private project names.

That read as **miscalibration, not a real leak**: every hit was inside a
`<!-- Last updated: ... (Buenos Aires) -->` header or a
`github.com/themorgan/...` URL — exactly the two conventions this branch's
own docs use constantly, by design (`volatile-rules-carry-dates`, and
every cross-repo link this deep-check's own write-up above also uses). It
also matched
[`decisions/2026-09-01-relax-private-repo-isolation.md`](../decisions/2026-09-01-relax-private-repo-isolation.md)'s
own recorded reasoning verbatim: "Morgan's own identifying information
(name, email) is already public." **Morgan confirmed the call**, so the
three over-broad patterns were removed from `leak-blocklist.txt` (the email,
domain, full name, and account-ID number were left alone — they never
showed a false-positive hit, so loosening them would have been the same
mistake in the other direction: reasoning instead of evidence). Re-running
the vocabulary layer for real, fresh, after the fix:

```
leak gate OK: 657 unit(s) in the tracked tree clean against 4 path rule(s),
3 content rule(s) and 13 blocklist pattern(s) from
/home/user/precedent-individual/leak-blocklist.txt.
```

**The vocabulary layer now genuinely runs clean on this branch** — the
first time that has been true since it was switched on. One real hit
surfaced along the way and is worth naming: this very document's own first
draft quoted the real approver's full name in prose (the two landed
practices' `approved_by` value), which the now-correctly-still-blocked
`\bMorgan\s+F\b` pattern caught — fixed by rephrasing rather than by
loosening that pattern, since (unlike the handle and the city) it had never
shown up anywhere else in this branch's own conventions.

## A fifth bug, found writing this very document: a glossed acronym still got re-flagged

While fixing the acronym warnings this document's own drafts triggered
(`tools/doc_lint.py` and `tools/precedent_check.py`'s `acronyms-glossary`
check), expanding an acronym on its first use — *pull request (PR)* — did
not stop a **second, later, bare** mention of `PR` in the same document
from being flagged again. Both `doc_lint.py`'s `check_file` and
`precedent_check.py`'s `_unglossed` (a near-duplicate of the same loop,
per the latter's own docstring: "one detector, two callers") only added a
token to their `seen`/`seen_acr` set **inside the violation branch** —
so a correctly-glossed use, which never entered that branch, never marked
the acronym as seen for anything after it. "Expand an acronym on first
use" (the practice's own Rule) silently only ever worked if that acronym
was used exactly once more, or not at all. Fixed in both places: a token
is recorded as seen the moment it's first encountered, glossed or not,
so a real gloss actually protects every later bare mention — confirmed
with a planted case in each direction
(`verify_harness.py`'s `check_doc_lint_fires`, two new stated cases).

## The step-5 loader bridge — closed, and proven against the real private sets

`spec/PHASE5_BRIEF.md`'s own step 5 named a real, unrehearsed gap: only
`tools/precedent_resolve.py` understands more than one source directory —
`build_views.py`, `precedent_paths.py`, `precedent_gate.py` and
`precedent_check.py` all read a single local `practices/` directory,
hard-coded, with no flag to point elsewhere. The brief named "materialize a
merged tree" as the fastest of two shapes worth trying — a script that
calls `resolve()` and writes the winning practices into one
`practices/`-shaped directory, then points the existing tools at it
unchanged.

**Built as [tools/precedent_materialize.py](../tools/precedent_materialize.py),
and proven for real** against the two real private sets, not a fixture:
resolved and materialized the actual 54 universal + 40 team + 5 individual
practices into a scratch consumer directory (99 after 2 overrides), wrote a
`MANIFEST.json` (per `generated-artifact-provenance`: what produced the
snapshot, when, and each file's content hash — the honest cost of a derived
artifact, named rather than hidden), then ran the **unmodified**
`build_views.py` against that directory:

```
build_views OK: wrote AGENTS.md (loader block regenerated, resident 10/99
practices, ~659 tokens), MAP.md, GLOSSARY.md
```

**Both figures match `PRACTICE_ENGINE_PLAN.md`'s own "What phase 5 should
carry forward" note exactly** (~659 of 2000, the same 10 practices) — a
real, independent confirmation of a number that section could previously
only report from a one-off resident-budget run, now reproducible by a
tool. The regenerated `AGENTS.md`'s resident block genuinely combined all
three sources — `bold-key-phrases`/`nonblocking-questions`/`small-calls`
from the team set, `buenos-aires-dates` from the individual set, the rest
from universal — not just proving files got copied. `precedent_paths.py`
and `precedent_gate.py`, run unmodified against the same materialized
directory, also correctly surfaced team-level practices
(`brainstorm-citations` on a path match; `deep-check`/`go-merge`/
`mirror-into-agents`/`private-repo-scrub` on the `merge` gate) alongside
universal ones. `precedent_check.py --list` loads cleanly too, though most
of its individual checks are BestPractice-catalogue-specific and not
meaningfully runnable against a generic consumer tree — not exercised
further here.

**Scope, stated plainly**: this tool materializes the CONTENT half only
(`practices/` + each source's `tools/checks/`, refusing a same-name
collision across sources rather than silently letting one win — a real
case, not a hypothetical: both private sets' own `tools/checks/tests/`
carry a `run_all.sh` driver, which isn't a per-check file and is skipped
and reported rather than falsely flagged as colliding). It does **not**
vendor the engine scripts (`build_views.py` and friends) — that half was
already solved (clone/copy this repo's `tools/`, per `INSTALL.md`'s
existing vendoring model) and is a separate concern from the content-merge
gap this closes. A real consumer repo's `AGENTS.md` is also not created by
this tool — a real one already has the generated-block markers from
`INSTALL.md`'s install step; the harness test seeds a minimal one only to
prove the mechanism.

## What this deep-check deliberately did not attempt

Scoped out, not overlooked — the brief itself frames the consumer-repo
migration rehearsal as "the biggest and least certain piece of work in this
brief" and says to do it last, after everything above:

- **The fork-a-consumer-repo rehearsal** (Phase 6's own first real test,
  against Morgan's real target repo rather than a
  disposable fork — see the naming discrepancy below) — that repo is
  outside this session's repository scope (only `alex137/BestPractice`,
  `precedent-individual`, and `precedent-team-maintainers` are attached),
  so it could not be started without first requesting access to a fourth
  repo. Morgan will run this in a session coming up soon; notes for that
  session are below. **No new permission or credential is needed for the
  parts a session can do unassisted** — the same GitHub connection already
  used to create and merge every pull request (PR) and to file an Issue in this session
  works the same way against a newly-attached repo. What genuinely can't
  be done by a session alone is the "non-collapsed" team-level approval
  path itself: Stage 4's design is that a *second human* (Morgan or Alex)
  actually reviews and approves on GitHub — a session opening that PR
  without a human reviewing it isn't really testing the reviewed-approval
  path, just leaving a branch open.
- **Filing a real universal candidate as a GitHub Issue**, and **opening a
  real team-level pull request** (the two manual paths the brief asks to be
  exercised at least once) — both are real, externally-visible actions
  (a public Issue, a real pull request (PR)) this session did not take without asking
  first, consistent with checking before anything visible to others or
  hard to reverse. Both remain open if Morgan wants them done.
- **The pre-fork catalogue audit table** — genuinely unblocked, real
  bounded work (one row per pre-fork practice: active-as-is / rewritten /
  superseded / merged, plus whether Alex needs to hear about it), just
  never done; not attempted this pass without an explicit go-ahead.
  **`for_team:`/`in_repos:`** — still correctly deferred (fully designed in
  `PRACTICE_ENGINE_PLAN.md`'s Deferred section; not built because no real
  second team exists yet to test `for_team:`'s conflict rule against).
  Neither is currently tracked in `TODO.md` at all, which is the actual gap
  behind both being *restated* fresh in every brief rather than *tracked
  once* — worth one line each there (the audit table actionable now,
  `for_team:`/`in_repos:` marked "blocked on: a real second team's private
  set existing") so a future session checks one line instead of
  re-deriving the whole judgment.

## `precedent-team-maintainers` wired into `BestPractice`'s own `precedent.json` — team #1 of 2

Real, correct, and overdue on its own merits, done at Morgan's request:
`precedent-team-maintainers` **is** this repo's own maintaining team's
conventions (Morgan and Alex; its own README says exactly this — "one
small group's working conventions... losing to a person's own individual
set"), but `BestPractice`'s `precedent.json` had only ever declared the
universal source. The cross-source resident-budget cap had only ever been
tested against a *synthetic* consumer config naming this team source,
never `BestPractice`'s own real one.

`precedent.json` now declares `precedent-team-maintainers` as a team
source (path: a sibling checkout — see the config's own comment for what
that does and doesn't assume, and the resolver's existing graceful-degrade
contract for a machine without that sibling). Running the resolver for
real, from this checkout, with no `--repo` flag needed:

```
resolved 94 practice(s) from 2 source(s): 0 individual, 41 team, 53 universal
  overridden: doc-references-are-links -- team (precedent-team-maintainers) replaces universal (precedent)
resident block across all sources: ~560 of 2000 token budget (9 practice(s): ...)
```

**A real find, not a fixture**: the team set's `rule-links.md` has declared
`overrides: doc-references-are-links` since it was written, generalizing
the universal rule (files only) to anything with a destination (commits,
PRs, branches, chat replies too) — but this is the first time that
override has ever actually been resolved against `BestPractice`'s own real
universal set to confirm it takes effect. It does.

**What this does and does not change, stated plainly**: this makes
`precedent_resolve.py` (and `precedent_materialize.py`, above) correctly
see `BestPractice`'s own real team source for the first time. It does
**not** change `BestPractice`'s own generated `AGENTS.md`/`MAP.md`/
`GLOSSARY.md` — `build_views.py` deliberately stays single-source, so this
repo's own session-loading is still the universal catalogue alone, exactly
as before. Materializing the two together into this repo's own working
`practices/` would be a much bigger, disruptive step (most of
`verify_harness.py`'s ~40 checks assert this repo's own single-source
catalogue integrity against `PRACTICES.md`) and was not attempted or asked
for.

**Still outstanding, restated so it isn't lost**: this is team #1, not the
second, distinct team `for_team:` needs to actually test its cross-team
conflict rule — that still needs a real second team elsewhere (plausibly
the live-migration test's own target repo, below, if it ends up with its
own team set). `for_team:`/`in_repos:` stays correctly deferred until then.

### Notes for the next session: the live migration test

Everything below is **the target-repo-specific half** of what this
deep-check found worth doing before that test — deliberately left for the
session that actually has that repo attached, per Morgan's own call:

- **Do it on a branch, not directly on the target repo's live default
  branch** — even calling it a "real-live test," a branch there costs
  nothing and is trivially revertible if the step-5 bridge (now built and
  proven against the two real private sets above, but never against a
  *third*, unrelated repo's content) turns out uglier than expected there.
- **Check whether the target repo needs its own `leak-blocklist.txt`
  entries** before anything gets pushed from it back toward
  `BestPractice`/Precedent — get that configured first, not after; this
  session's own leak-gate work above found a real hit in its own prose on
  the very first real run, so treat "surely nothing leaks" as unproven
  until actually run.
- **`tools/precedent_materialize.py` is now available** for step 5 of the
  brief's own walkthrough — point `--repo`/`--user-config` at
  the target repo's real `precedent.json` (naming universal +
  `precedent-team-maintainers`, or a real second team if one exists there)
  and a user config naming `precedent-individual`, materialize into the
  fork, then vendor this repo's engine `tools/*.py` alongside it (the
  already-solved half — see the tool's own docstring for the split) and
  seed the fork's real, hand-authored `AGENTS.md` with the generated-block
  markers per `INSTALL.md`. Confirm `precedent_check.py --explain` on a
  real, target-repo-specific slug too, which this session did not push
  past `--list`.
- **Confirm a naming discrepancy before starting**: `spec/PHASE5_BRIEF.md`'s
  own step 0 says fork `WritingWithAI`; `precedent-individual`'s
  `leak-blocklist.txt` names a different-looking private project name for what may be the same repo. Worth
  confirming those are the same repo before anything else, since this
  session has no access to check.
- **Raise at least one real candidate from something the migration itself
  surfaces** — the brief's own repeated ask, and a better test done inside
  a real migration than in isolation, per its own reasoning.

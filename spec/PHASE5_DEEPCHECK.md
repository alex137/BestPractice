<!-- Last updated: 2026-09-02 (Buenos Aires) by the phase-5 deep-check session -->

# Phase 5 Deep-Check — What Was Actually Found

[spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s own "For the session that
deep-checks this before Phase 6" section asked for exactly this: adversarial
pressure on the real creation-pipeline tooling, real candidates run through
[tools/precedent_promote.py](../tools/precedent_promote.py) and
[tools/precedent_land.py](../tools/precedent_land.py) for real, and a fresh run of
every repo's own deep-check suite rather than trusting last session's green
run. This is that session's account — four real bugs found and fixed in the
pipeline tooling itself, two real candidates landed end to end, and a fresh
harness run across all three repos that found real, pre-existing drift
nobody had caught yet. Written the way [spec/PHASE5_BRIEF.md](PHASE5_BRIEF.md)'s
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
  landed in `precedent-individual`, approved by "Morgan F". The bug-2 story
  above, written up as a portable practice for any codebase, not just this
  one.
- **Team** — [`resolved-issue-note-updates`](https://github.com/themorgan/precedent-team-maintainers/blob/claude/bestpractice-deep-test-tkb03u/practices/resolved-issue-note-updates.md),
  landed in `precedent-team-maintainers`, approved by "Morgan F" (a real
  name in that repo's own `approvers.json`). Raised from watching
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

## An open calibration question, surfaced but not resolved: the leak gate's vocabulary layer

The brief asked whether
[`precedent-individual/leak-blocklist.txt`](https://github.com/themorgan/precedent-individual/blob/claude/bestpractice-deep-test-tkb03u/leak-blocklist.txt)
is miscalibrated or whether the vocabulary layer has simply never run clean.
Running it for real against this branch's current tree (`PRECEDENT_LEAK_BLOCKLIST`
pointed at the real file, `git config precedent.requireVocabulary true`,
reverted immediately after) found **51 hits, every single one** on exactly
two patterns: `\bthemorgan\b` and `\bBuenos\s+Aires\b` (plus the one literal
`\bAmerica/Argentina/Buenos_Aires\b` timezone (TZ) string). Zero hits on any other
line in the blocklist — the email, the account-ID-shaped number, or any of
the other private project names.

This reads as **miscalibration, not a real leak**: every hit is inside a
`<!-- Last updated: ... (Buenos Aires) -->` header or a
`github.com/themorgan/...` URL — exactly the two conventions this branch's
own docs use constantly, by design (`volatile-rules-carry-dates`, and
every cross-repo link this deep-check's own write-up above also uses). It
also matches
[`decisions/2026-09-01-relax-private-repo-isolation.md`](../decisions/2026-09-01-relax-private-repo-isolation.md)'s
own recorded reasoning verbatim: "Morgan's own identifying information
(name, email) is already public." **Not changed here** — loosening a
private blocklist is Morgan's own risk-tolerance call, not a documentation
fix this session should make unilaterally. If that reasoning still holds,
the fix is narrowing `leak-blocklist.txt`'s two over-broad patterns (or
scoping `\bthemorgan\b` to contexts that aren't already-public GitHub URLs);
if it doesn't, the fix is the other direction — stop writing the literal
city name and GitHub handle into public prose, which would be a much
larger, disruptive change to an established convention.

## What this deep-check deliberately did not attempt

Scoped out, not overlooked — the brief itself frames the consumer-repo
migration rehearsal as "the biggest and least certain piece of work in this
brief" and says to do it last, after everything above:

- **The fork-a-consumer-repo rehearsal** (`WritingWithAI`, Phase 6's own
  first real test) — that repo is outside this session's repository scope
  (only `alex137/BestPractice`, `precedent-individual`, and
  `precedent-team-maintainers` are attached), so it could not be started
  without first requesting access to a fourth repo for a rehearsal the
  brief itself calls the least certain, highest-cost item on its list.
- **Filing a real universal candidate as a GitHub Issue**, and **opening a
  real team-level pull request** (the two manual paths the brief asks to be
  exercised at least once) — both are real, externally-visible actions
  (a public Issue, a real pull request (PR)) this session did not take without asking
  first, consistent with checking before anything visible to others or
  hard to reverse. Both remain open if Morgan wants them done.
- **The pre-fork catalogue audit table** and **`for_team:`/`in_repos:`**
  — both still correctly deferred per the brief's own reasoning; nothing
  found during this pass changes either call.

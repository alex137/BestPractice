<!-- Last updated: 2026-09-07, run in progress -->

# Very deep check — run record

The state of the current [very deep check](../practices/very-deep-check.md),
and the ledger of the ones before it. The check is deliberately more than one
session's work, so a session picks up at the first pass below that is not
marked done rather than starting over. A pass is never quietly skipped: one
deliberately not run is recorded here as not run, with the reason.

**How to use this file.** A session starting or resuming a run fills in the
table, then records what each pass turned up under it: what was found, what
was fixed in the same pass, and what was deferred with the
[TODO.md](../TODO.md) line it went to. When the last pass is done, collapse
the run to one row under "Runs so far" and clear the table for the next one —
this document holds the run in progress, not an archive of every finding
([docs-are-current-state](../practices/docs-are-current-state.md); the
findings themselves live in the commits that fixed them and in
[TODO.md](../TODO.md)).

## Current run

**Started 2026-09-07**, on Morgan's direct request, ahead of showing
`precedent-beta-v01` to Alex. Scope: all four repos in force —
`alex137/BestPractice`, `themorgan/precedent-individual`,
`themorgan/precedent-team-maintainers`, `themorgan/precedent-team-tms`.
Working branch `claude/bestpractice-precedent-deep-check-4rmlee` in each.

| Pass | Status | Date | Notes |
|---|---|---|---|
| 1 — adopter installs | done | 2026-09-07 | fresh install and migration both built and run; 6 defects found, all fixed |
| 2 — mechanisms | partial | 2026-09-07 | questions 1-3, 6-10, 12-13 worked; 4, 5, 11 not yet |
| 3 — coherence read | partial | 2026-09-07 | mechanical sweep clean; cross-source staleness rolled out; full read not done |
| 4 — catalogue and housekeeping | branches only | 2026-09-07 | branch sweep run and listed below; catalogue and backlog not done |

Roadblocks (pass 1 and 2 findings that strand an adopter) are fixed before
anything from passes 3 and 4, whatever order they were found in. A run is not
done while one is open. **No roadblock is open** — every pass-1 and pass-2
finding below is fixed and pushed.

### Prerequisites

All four repos proved current against origin before anything was read. Two
were not, and were fixed rather than waived: this checkout's own branch and
`precedent-team-maintainers`' existed only locally, so freshness was
unprovable and [tools/very_deep_check.py](../tools/very_deep_check.py)
refused the run twice, correctly, until each was pushed.

The deep check suite was green before the passes began — and green again
after them.

### Pass 1 — adopter installs

Both fixtures were built and run, not read: a from-scratch install per
[INSTALL.md](../INSTALL.md) §0, and a migration from the classic
`process/upstream/` layout per
[MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md).

**The fresh install did not come back clean.** It ended on 8 violations,
against §0's own claim of "15 checks passed, 0 violated". Four were the
install's own; four more appeared only when an individual source was in
play. All are fixed:

1. **A public consumer published private practice text.**
   `precedent_sync_views.py` materialized every source into the consumer's
   *tracked* `practices/` tree with no regard for `visibility`. The fixture
   took 13 individual-level practices, one carrying a person's name and
   email address. The architecture had reasoned about this exact risk twice
   — `build_views.py` refuses to render a private source into a public
   repo's loader block, `precedent_materialize.py` refuses to mint a private
   repo's *URL* into the same tree — and both guards work by source *level*,
   which materialization flattens away before they run. A private consumer
   was never affected, which is why nothing caught it.
2. **A correct fresh install could not satisfy `generated-artifact-provenance`.**
   `precedent_sync_views.py` called `build_loader_block()` without
   `omits_private` while `build_views.py` passed `repo_is_public(root)`, so
   the two wrote different `AGENTS.md` files for the same public repo. The
   check regenerates and byte-compares, so it reported the file the
   documented install step had just written as hand-edited. Same renderer,
   different arguments, nothing keeping them in step.
3. **Three shipped templates fail on instantiation.**
   `GETTING_STARTED.md`, `VOICE.md` and `STYLEGUIDE.md` carried 26 headings
   that are not headline case. Invisible here because `templates/` is
   internal to *this* repo, while the instantiated copies are outward-facing
   in the adopter's. Rewritten with the sanctioned tool.
4. **A vendored tree was judged as the adopter's own prose.**
   `title_case.is_outward()` tested only `parts[0]`, so a vendored catalogue
   one level down — `precedent/universal/practices/`, which §0 itself
   recommends — was scanned as publishable and reported headings nobody can
   fix. Now excluded at any depth, deliberately only for `practices/`.
5. **`precedent_check.py` was vendored twice** into every consumer, landing
   twice in the tracked `ENGINE_MANIFEST.json` while the seed reported one
   file more than it wrote. Both engine lists are now duplicate-checked at
   import.
6. **An unreachable source silently deleted tracked practices.** Found on
   the migration fixture, and the most serious of the run:
   `precedent_sync_views.py` rebuilds `practices/` by delete-and-rewrite, so
   a declared source that failed to resolve did not merely go unrendered —
   every practice it contributed was deleted, `AGENTS.md` and
   `MANIFEST.json` rewritten to match, exit 0, one warning line. That is the
   CI state by definition. `build_views.py` already refused this in nearly
   the same words; the tool the documents actually tell an adopter to run
   did the opposite. The `--check` half of the identical bug was fixed
   2026-09-06 and its note still sits a few lines above where the refusal
   now lives; the writing half was left, and it is the half that deletes.

**The migration path itself is clean.** Sync is byte-stable on a second
`--check`, repo-local resolves, 67 practices. The two violations that
fixture ended on were its own incompleteness (no `MAP.md`, no
`process/scrub_blocklist.txt`) and both failed loudly with a named reason —
which is what the empty-neighbourhood bullet asks for.

**Empty neighbourhood**, all three shapes exercised: no individual set (66
practices, no crash); no team set; sources declared but unreachable. The
third is finding 6 above.

**Not done in this pass:** the cross-repo permissions walk — who must be
able to read or write what for a *new* repo and a *new* person, including
the restricted GitHub roles in
[NONTECHNICAL_CONTRIBUTOR_ACCESS.md](NONTECHNICAL_CONTRIBUTOR_ACCESS.md).
Everything this session could reach worked only because its operator
already has access, which is exactly the condition that bullet says to
distrust.

### Pass 2 — mechanisms

**Question 3 (`--check` that writes): clean.** All seven tools carrying
`--check`, `--apply` or `--commit` were snapshot-run-diffed on a clean tree,
then again with the team source deliberately hidden. None wrote. The
2026-09-06 incident this question exists for is genuinely fixed and stays
fixed.

**Question 1/2, in the branch sweep — the run's own tool was lying.**
[tools/very_deep_check.py](../tools/very_deep_check.py) enumerates
`refs/remotes/origin`, which holds only what a clone actually fetched. The
harness clones single-branch and the freshness gate fetches exactly one
branch, so the sweep looked at three refs in a repo with forty and printed
`(none)` — indistinguishable from a clean sweep. The same tool, at the same
commit, on the same checkout, went from `(none) / (none)` to 34 merged and 2
unmerged branches purely because a `git fetch` had happened in between. Two
branches carrying real unlanded commits were invisible. Fixed in both
halves: fetch every head first, and report `CANNOT TELL` rather than
`(none)` when origin cannot be reached.

**Question 1/2, in the source-shape check — two more.** It reported
`precedent-individual` as missing two session hooks it has and runs (they
live in `bootstrap/`, wired from its own `settings.json`, exactly as that
set's `commit-author` practice documents), and it told the reader every
missing file was "present in `templates/practice-set-<level>/`" when the
session hooks and `settings.json` have never been in either skeleton. Four
reported gaps became two, and both survivors are genuine:
`precedent-individual` has no `config.json.sample`;
`precedent-team-maintainers` has no `leak-blocklist.txt`. **Both still
open** — see [TODO.md](../TODO.md).

**Question 6 (is a file the format it claims): clean.** 519 tracked JSON and
YAML files parse with a real parser.

**Question 8 (two of anything that should be one): three found.**
`precedent_check.py` in both engine lists (finding 5 above); the two
`build_loader_block()` call sites disagreeing (finding 2); and
`tools/precedent_bootstrap_source.py` versus
`tools/precedent_source_bootstrap.py` — two different tools whose names are
near-anagrams of each other, in one directory. This session misread one for
the other. Not duplicated code, so not merged; recorded because the next
reader will make the same mistake.

**Question 12 (is each known exception still true): mostly yes.** Every
gotcha reproduced as written — `cmarkgfm` genuinely needed, the
single-branch `add_repo` clone genuinely the cause of the branch-sweep bug,
`git merge-base` genuinely misleading on a shallow clone, `practice_audit`
genuinely NOT APPLICABLE. One is *satisfied rather than stale*: "the three
private practice sets cannot be attached from a session rooted in this
repo" — this session has all four attached and has pushed to both owners,
which is the entry's own stated remedy (a session whose initial source is
the private repo), not a contradiction of it. [TODO.md](../TODO.md)'s item
34 `attach-private-sources` is therefore **satisfied by this session**, and
it says it unblocks four other items.

**Question 13 (what a session inherits that a person configured by hand):
the commit-identity mechanism reached none of it.** Every clone in this
session — all four — carried `Claude <noreply@anthropic.com>` as its commit
identity, the exact failure `commit-author`'s Story records as having been
replaced by a mechanism in 2026-09-06. The mechanism is correct and did not
run, because it is a `SessionStart` hook and none of these repos is the
session's primary. AGENTS.md's own gotcha already says attached siblings
never run their hooks; what is new is that this makes a *practice with a
mechanical check* silently unenforced in exactly the sessions that do
cross-repo work. Set by hand here, four times. **Open** — a hook cannot fix
a repo it never runs in, so this needs a different layer.

**Question 7 (do string matches respect name boundaries): one data point,
not a sweep.** `index-remembers-past` matches the bare phrase "superseded
by" and fired on this very document, which was using it about *branches*,
not document lineage. The finding is real in kind — a denylist term
matching a different sense of the same words — but narrowing it needs a
way to tell what the phrase is about, which a string match cannot do. The
prose was reworded instead, and the check left alone. Recorded so the next
run knows the term is load-bearing and easy to trip innocently; the
systematic sweep of every blocklist against plausible compounds is still
**not done**.

**Not done:** questions 4, 5, and 11 — output-directory dependence,
generated-name disclosure, string-match name boundaries, and reading each
enforced practice's check against its own Rule. Question 11 is the
expensive one and the only pass that ever looks at those checks.

### Pass 3 — coherence read

Mechanical first, as the practice requires:
[doc_lint.py](../tools/doc_lint.py) across the whole tree is clean — no
broken relative links, no accidental strikethrough, no skipped heading
levels, no `target=` anchors. 906 unlinked-file-reference warnings and 6
unglossed acronyms (`RPP`, `RAG`) are the legacy backlog, report-only.

**Cross-source staleness — rolled out, not deferred.** Both private sources
carried a `freshness-guard.sh` predating the `user-prompt` mode, so the
long-open-tab case AGENTS.md describes as one of three necessary firing
points was unguarded in both. Rolled out per
[cross-source-rollout](../practices/cross-source-rollout.md), preserving
each set's own path convention (`bootstrap/` in the individual set,
`.claude/hooks/` in the team set), with the matching `UserPromptSubmit`
wiring and — in the individual set — its installable snippet, so a project
adopting it gets all three firing points rather than the two it would have
got yesterday.

**Two findings in [INSTALL.md](../INSTALL.md), both fixed.** §0 claimed a
fresh install "comes back clean — 15 checks passed, 0 violated"; the count
was stale and the claim was false as written, in the document adopters
trust most. Replaced with what to expect (`0 violated`), no count, and an
honest note about what the second rehearsal found. Separately, `## 0` sits
*below* `## 1` — a fresh adopter meets the legacy path first. Renumbering
would break every link to §1-§7, so §1 now points forward to §0 instead.

**Not done:** the coherence read proper, across all four repos —
contradictions, misdirected-but-resolving links, fragments, disproportion,
rules that no longer make sense, cost that is not earned. This is the
largest single piece of unfinished work in the run.

### Pass 4 — branches only

The catalogue sweep ([full_practice_audit.py](../tools/full_practice_audit.py)
across every source) and the backlog read are **not done**.

The branch sweep ran, after its own bug was fixed. Every branch below needs
a verdict and most do not have one yet.

**No pull request exists for any of the four.** All three repos land work by
direct push, so there is no PR page to link and no one-click **Delete
branch** control on one. Each row below links the branch's own compare view
instead. That is a gap in the sweep's assumptions, now written into
[very-deep-check](../practices/very-deep-check.md): a link is required, but
it is the PR's *when there is one*.

**The engine check is what changed the verdicts.** Both
`pre-launch-audit-fixes` branches sit on a vendored engine 41 commits behind
their own `main` (`82b4722` against `d0cbdb4`), so merging either would
revert the engine wholesale in order to land a handful of files. Both are
cherry-picks, not merges — and the naive reading of "19 unlanded commits"
would have said merge.

**`alex137/BestPractice`** (integration branch `precedent-beta-v01`): 34
branches merged and not deleted; 2 not merged.

| Branch | What it is | Last moved | Recommendation |
|---|---|---|---|
| [`claude/file-sharing-service-spec-0m9c7p`](https://github.com/alex137/BestPractice/compare/precedent-beta-v01...claude/file-sharing-service-spec-0m9c7p) | A 653-line specification and delivery plan for a file-sharing service — `share/SPEC.md`, `share/PLAN.md`, one AGENTS.md line. Pure documents, no engine code. Its last commit switches the design to a thin gateway over object storage on Cloudflare Workers. Nothing in Precedent depends on it. | 2026-07-26 | **Close, unless the service is still planned.** Six weeks cold, and it is a product spec that happens to live in the practice repo rather than anything Precedent needs. If it is still wanted it belongs in its own repo — cheap to re-push from this branch, which is why closing costs nothing. **Alex's call**, since it is his subject matter, not a Precedent question. |
| [`claude/missed-practices-simulation-v0wszw`](https://github.com/alex137/BestPractice/compare/precedent-beta-v01...claude/missed-practices-simulation-v0wszw) | One commit adding `tools/routing_eval_synthetic.py` (319 lines) plus 66 generated prompt fixtures — a synthetic occasion-routing stress test, complementary to the existing `routing_eval.py`. 14,539 insertions, almost all generated fixture text. | 2026-09-01 | **Merge, after checking the fixtures belong in git.** The tool is real and complements a mechanism this repo already relies on, and [spec/ATTENTION_CEILING.md](ATTENTION_CEILING.md) is explicit that routing quality is under-measured. The one hesitation is 14k lines of generated prompts as tracked files; if they are reproducible from the script, generate them instead and merge the script alone. |

**`themorgan/precedent-individual`** (integration branch `main`): 10 merged
and not deleted; 1 not merged.

| Branch | What it is | Last moved | Recommendation |
|---|---|---|---|
| [`claude/pre-launch-audit-fixes-7wumzx`](https://github.com/themorgan/precedent-individual/compare/main...claude/pre-launch-audit-fixes-7wumzx) | 20 commits, 19 unlanded, from the 2026-09-06 pre-launch audit. Most are vendored-engine re-seeds that later work on `main` has since gone past. Four things are genuinely absent from `main`: `config.json.sample`, `practices/my-identity-is-not-private.md`, `tools/checks/check_my_identity_is_not_private.py` and its test. | 2026-09-06 | **Cherry-pick those four, then close.** Do NOT merge: the branch's engine is 41 commits behind `main`'s, so a merge reverts it to land four files. The `config.json.sample` is one of the two gaps this very run rediscovered independently and filed as an open item — the fix was already written and simply never landed. |

**`themorgan/precedent-team-maintainers`** (integration branch `main`): 10
merged and not deleted; 1 not merged.

| Branch | What it is | Last moved | Recommendation |
|---|---|---|---|
| [`claude/pre-launch-audit-fixes-7wumzx`](https://github.com/themorgan/precedent-team-maintainers/compare/main...claude/pre-launch-audit-fixes-7wumzx) | 16 commits, 16 unlanded, the team-set half of the same audit. Nearly all of its check work (`check_no_stale_counts.py`, `check_light_check.py`, the tests) is already on `main` by another route. `leak-blocklist.txt` is not, nor are the `practices/fail-gracefully.md` and `CODEOWNERS` edits. | 2026-09-06 | **Cherry-pick `leak-blocklist.txt`, review the other two, then close.** Same engine-revert reason as above. The blocklist is the other gap this run rediscovered: until it exists, the leak gate's vocabulary layer has nothing of this set's own to check, and an absent blocklist is a gap where an empty one would be a deliberate state. |

Deleting the 54 merged branches is a mechanical follow-up this session did
not do. The practice asks for a link to each one's most recent PR, and the
same finding applies: these repos push directly, so most have no PR page
and no one-click delete control.

## Runs so far

| Run | Passes completed | What it changed |
|---|---|---|
| — | — | no very deep check has completed all four passes yet; the 2026-09-07 run above is the first under this definition and is still open |

The 2026-09-06 [pre-launch audit](PRELAUNCH_AUDIT.md) is the closest thing to
a prior run, and is where pass 1's method and all but one of pass 2's
questions come from — it was not run under this practice, and its own
still-open list is a separate document, kept there rather than copied here.

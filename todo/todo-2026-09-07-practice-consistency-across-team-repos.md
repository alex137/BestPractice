---
slug:              todo-2026-09-07-practice-consistency-across-team-repos
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "nothing about access, as of 2026-09-12 — what remains is building the thing the four bullets above describe. A session rooted at this repository now holds it, all three team sets and the individual set at once: the SessionStart hook's credential route ([PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)) c"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- <a id="practice-consistency-across-team-repos"></a>**How one practice lives in several team repos and stays consistent** —
  **unfolded 2026-09-08, at Morgan's prompting.** Folded into
  [item 7](todo-2026-09-06-multiple-team-sources-disagree.md) on 2026-09-07 on the
  grounds that item 7 "had asked the same question since 2026-09-03". It had
  not, and item 7's body has never mentioned drift: item 7 asks which of two
  **disagreeing** team sources wins inside one consuming repo — a precedence
  question, parked. This asks what keeps one rule the **same** across several
  team sets that nobody resolves together — a drift question, and nothing
  addresses it. The fold is the reason this sat as a dead anchor for a day.
  (The anchor is kept either way —
  [rename-updates-links](../practices/rename-updates-links.md).)

  **The drift is measured, not hypothetical.** Two sessions independently
  landed `fail-gracefully` and `bold-key-phrases` into *both* team sets on
  2026-09-07, each doing the obviously right thing. The one deliberate
  cross-repo sweep — a session holding all four repositories, searching by
  purpose and by mechanism, 2026-09-06 — found one more
  (`headline-duplicate-retired`).
  Nothing runs that sweep on a schedule, and nothing runs it mechanically.

  **Morgan's proposal, 2026-09-08:** one session holding the universal repo
  plus every team and individual set, finding the same practice across
  sources, reporting where the copies have drifted, and reconciling them —
  with an identity check, so two unrelated rules that happened onto one slug
  are never merged into each other.

  Four things to weigh before building it:

  - **The identity half is already solved, in the opposite direction.** Slugs
    are identities: `resolve()` in
    [tools/precedent_resolve.py](../tools/precedent_resolve.py) raises on two
    same-level sources defining one slug, and `load_source()` raises within
    one source. Two unrelated rules sharing a slug cannot survive long enough
    to be reconciled. The undetected case is the inverse — **one rule under
    two slugs** — which "rename one", item 7's cheapest remedy, actively
    manufactures.
  - **A copy is usually the bug, not the thing to keep in sync.** Two teams
    wanting the identical rule is what a universal rule looks like, and that
    was Morgan's own call on the 2026-09-07 pair: promote to universal,
    delete from both team sets. A reconcile tool should propose **promotion
    first** and a text merge second, or it will keep three copies healthy
    forever.

    **The counter-example this tool must not break, found 2026-09-09:**
    `catalogue-carries-stories` is active at universal AND in
    `precedent-team-repo-maintenance`, and that second copy is load-bearing. A
    source repo consumes no catalogue, so universal's copy never reaches it
    and `precedent_check.py` only runs a check whose practice is in force
    *there* — deduplicating it switches the check off rather than deferring
    it. It was deduplicated and re-activated within one day on exactly that
    discovery. So **"same slug, active in two sources" is not sufficient
    evidence of a redundant copy**, and a tool that promotes on that signal
    alone will silently disable enforcement. The distinguishing question is
    whether the lower source actually RESOLVES the higher one, which the
    resolver can answer and a text-similarity score cannot.
  - **It must not be a judge-only reading pass.**
    [spec/ATTENTION_CEILING.md](../spec/ATTENTION_CEILING.md) pre-registered and
    measured that exact shape at 54% recall — worse than doing the work with
    no review pass at all. The mechanical seed already exists:
    [tools/precedent_promote.py](../tools/precedent_promote.py)'s
    non-duplication criterion takes `--against PATH[,PATH...]` and scores
    word overlap across several repo roots. What is missing is running it
    pairwise over existing catalogues instead of once, at creation.
  - **The verdict has to be recorded per pair, per source.**
    [parallel-artifact-ledger](../practices/parallel-artifact-ledger.md) is the
    practice for that, and several team sets carrying one rule is the case it
    describes.

  **Measured 2026-09-12 in `precedent-team-repo-maintenance`, from a session
  holding that set and this repository at once: what the re-declaration
  requirement costs across a whole catalogue, and a third mechanism this item
  had not counted.** `precedent_check.py` there reports **12 passed and 42
  skipped**, and all 42 skips are the single cause — each reads `no
  practices/<slug>.md in this repo`; not one is a `NotApplicable` or an
  environment skip. `--only practice-links-travel` reports `1 skipped`, and a
  skip is not a pass. The skip is **permanent, not pending configuration**: that
  set declares no `sources` in its `precedent.json`, and neither
  [tools/precedent_resolve.py](../tools/precedent_resolve.py) nor
  [tools/precedent_materialize.py](../tools/precedent_materialize.py) appears in its
  vendored engine's `tools/ENGINE_MANIFEST.json`, so no other level's practice
  text can ever arrive there. **So the wart is not one rule going unenforced in a
  source set — it is most of the catalogue, in exactly the repositories that
  publish it.**

  **It has cost something already.** `practices/deep-check.md` in that set
  shipped a relative link to its own `tools/checks/tests/run_all.sh`.
  Materialization copies the per-check files and deliberately not the driver, so
  the link was live in the publishing set and dead in every repository that
  received the catalogue — and the fix's own commit message records that every
  sync in a consumer had been printing the not-vendored line for it. A
  **consuming** repo caught it, one sync late, because
  [practice-links-travel](../practices/practice-links-travel.md) is in force there
  and skips in the set that published the bad link; fixed in `3032241`. That is
  the failure mode to expect from the other 41: the source set publishes the
  defect, and a consumer discovers it.

  **The third mechanism — call the registered check function directly from CI.**
  The discussion above knows two options, re-declare the universal practice as a
  same-slug local copy or leave it unenforced. That set ran a third for one week, in
  `.github/workflows/practice-links-travel.yml` (`9e92d60`, **deleted
  2026-09-13** once `binds_publishers` made it unnecessary — replaced by a
  workflow running the whole suite): import
  `precedent_check`, pull the check out of its `CHECKS` registry by slug, and call
  it, bypassing the gate in `run()` that would otherwise skip it. It follows a
  precedent already in that repo — `.github/workflows/views-drift.yml`, whose
  header records the identical problem for
  [generated-artifact-provenance](../practices/generated-artifact-provenance.md) and
  concludes *"So this workflow calls build_views.py directly"*. **For it:** no
  second copy of the rule text, so there is nothing to drift, and it refuses
  rather than passing green when the slug is absent from the registry, when the
  engine is not vendored, or when the check reports `NotApplicable`. **Against
  it:** it runs `on: pull_request`, so a direct push and a local pre-commit run
  are uncovered, where a re-declared practice binds wherever `precedent_check.py`
  runs — and one workflow per rule scales no better than one copy per rule.

  **And the evidence against re-declaring, which is the part this item most
  needs.** That set's one re-declared copy never agreed with universal's in
  the whole of its life (re-declared 2026-09-06, retired 2026-09-13; the
  analysis below is written in the present tense of the week it existed).
  `practices/catalogue-carries-stories.md` differs there in `title`, `occasion`,
  `index_clause` and Rule prose, and carries `checked_by: null` where this
  repository's copy names `tools/precedent_check.py`. **It did not drift into
  that state**: universal's copy reached its current text at `1b9b581`, and the
  team copy was re-activated at `6875119` twenty-three minutes later, already
  differing from it — and neither file has been edited since. So the two have
  been divergent from the moment the re-declaration existed, which is worse than
  drift, because there was never a synchronized state to fall out of. (Both
  commits are 2026-09-06 in Buenos Aires time; the sibling item's "2026-09-07"
  reads the same night in UTC.) **The `null` is also the field least able to
  survive being wrong.** `--only catalogue-carries-stories` reports `1 passed`
  there, so the vendored engine's check does run and does enforce it; whether
  `checked_by` is meant to name only a script the set itself owns is a convention
  [spec/PRACTICE_FORMAT.md](../spec/PRACTICE_FORMAT.md) does not settle. Until it
  does, a re-declared copy is a second place for the rule to be wrong about
  whether anything checks it — which is
  `loader-comment-names-an-unvendored-check`'s
  failure in a frontmatter field instead of a generated comment.

  **The conclusion offered, not imposed:** the real fix is for a check to be able
  to declare that it binds any repository publishing a `practices/` tree, rather
  than depending on the practice text being locally present. That would retire
  the re-declaration, the workflow-per-rule and this item's drift question
  together. It is a design call about `run()`'s gate in
  [tools/precedent_check.py](../tools/precedent_check.py), which is why this is
  evidence on an item rather than a patch.

  **Blocked on:** nothing about access, as of 2026-09-12 — what remains is
  building the thing the four bullets above describe. A session rooted at this
  repository now holds it, all three team sets and the individual set at once:
  the SessionStart hook's credential route ([PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)) clones
  every declared source before the first turn, and
  `~/.config/precedent/config.json` exists. Both halves of the 2026-09-08
  reading this paragraph replaces are superseded — on that date no sibling
  clone existed beside this checkout and that file did not exist. What has
  **not** changed is `add_repo`, which still refused `themorgan/*` from this
  `alex137/*`-rooted session when re-measured 2026-09-12 (*"cross-tier adds are
  not supported in v1"*), so
  [`attach-private-sources`](todo-2026-09-06-attach-private-sources.md) stays the route for
  anything needing GitHub-side access to a `themorgan/` set — the API, a push, a
  pull request — rather than a read of its files on disk.

## How It Closes

Not open until: nothing about access, as of 2026-09-12 — what remains is building the thing the four bullets above describe. A session rooted at this repository now holds it, all three team sets and the individual set at once: the SessionStart hook's credential route ([PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)) c

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.

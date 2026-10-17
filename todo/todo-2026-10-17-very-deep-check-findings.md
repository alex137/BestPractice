---
slug:              todo-2026-10-17-very-deep-check-findings
kind:              analysis
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-17
closed:            null
---
## What

What the 2026-10-17 very deep check found and did not fix in the same run.
Scope: BestPractice and the three sets it declares (the individual set, the
ladder set, the writing set), each checked whole, as Morgan asked: "Very
deep check for best practice then very deep check for each of the three
practice sets attached". What the run fixed is in its commits; the account
is [VERY_DEEP_CHECK_LATEST_RUN.md](../spec/VERY_DEEP_CHECK_LATEST_RUN.md).
This item holds the rest.

### Calls for Morgan

Each is a decision a session should not make alone: a rule he set, a
billing default, a repository's lifetime, or a design change.

- **The ladder's landing check and act's branch check never run where their
  Rules say.** go-update says a push straight to the landing branch is
  refused by `check_landing_takes_a_pr.py`; act says a harness-named branch
  is never Booked or Produced. Since the quick tier closed on 2026-10-16, a
  landing runs the basic tier, which runs no practice check, and the
  branch-name guard reads only the remote ref. Two ways out: ship both as
  pre-push `hooks:` the way act ships its guard (needs his own words under
  quick-tier-is-closed), or drop both claims. Pick: ship them as hooks.
- **The ladder set's prompt-please addition contradicts universal's.**
  Universal says a Prompt Please ends on a feature branch; the ladder's
  addition lets the receiving session take small work to main, while
  saying "everything there holds". Pick: make it an explicit replacement of
  that one bullet.
- **A retired shared set's repository still publishes private repository
  names.** It was archived, not deleted; its pull-request refs still answer
  `git ls-remote`, and its own open item says some of them reach a file
  naming private repositories. Pick: delete the repository.
- **A person with no individual set is never a code owner to the engine**,
  so 28 practices stay hidden from them, Update Vendors among them; `--admin`
  does not help (`precedent_audience.viewer()`). Pick: read the
  authenticated GitHub account, which commit-identity.sh already looks up.
- **"It notices and offers a rule" does nothing on a fresh install.** The
  universal `close_detect.json` is never vendored. Pick: vendor it with the
  catalogue rather than soften four pitch sentences.
- **The first session on a local machine rewrites the developer's global git
  identity and sets a global `core.hooksPath`**, with no document saying so
  (`tools/commit-identity.sh`). Pick: repo-local config only on a local
  session.
- **The individual-set skeleton ships `"github_ci_workflows": "disabled"`**
  with a stale comment, while the engine has defaulted to enabled since
  2026-09-25; a migrated repo ended with no CI at all. His billing default,
  so his call.
- **An update silently removes 18 ladder commands from an adopter installed
  before 2026-10-02.** By design for people off the ladder; the only
  question is whether the update says so in one line.
- **The daily `deep-check.yml` schedule is not listed in AGENTS.md or MAP.md**,
  which crons-are-a-last-resort asks for. Alex approved the schedule; the
  listing rule is Morgan's.
- **Retire the individual set's legacy `session-start.sh` and its two
  snippets**, now that the Install points at the real route.
- **Merge `revert-needs-no-trailer` into `session-trailer`**: it is a
  one-line exception to it (the review page's one merge candidate).
- **Ten open items the backlog pass could not settle** are listed under
  "Open items: ambiguous" in [VERY_DEEP_CHECK.md](../spec/VERY_DEEP_CHECK.md),
  one line each with what the session would do.

### Found, not fixed here

Engine and tool defects that need more than a run's fix, each with the place
it lives:

- **Running `precedent_materialize.py` directly in a public consumer copies
  private practice text into its tracked tree**; only the wrapper,
  `precedent_sync_views.py`, withholds. The writer should refuse in a public
  repo when private levels resolved, and when a declared source is missing.
- **A read-only check can replace a complete session file with an empty
  one**: `precedent_resolve._self_heal_stale_render` re-renders a stale
  `.precedent/SESSION_PRACTICES.md` from sources that did not resolve.
  Keep the old render and mark it stale.
- **Deduplicating a universal practice by hand right away passes every
  check**; only the sync's stderr says IN FORCE NOWHERE, followed by a line
  that contradicts it (`precedent_sync_views.py` near line 788).
- **After `--dedupe-only --accept-reach-loss`, the set copy's `approved_by`
  still says a universal copy stays active** (`precedent_move.py` near line
  961); only the withdraw path rewrites it.
- **The move tool's mention fixer takes a set's name from its checkout
  directory, not its `precedent-source.json`**, misses some phrasings, and
  writes an individual set's name into shared and public places.
- **A practice set's own `hooks:` never run in a session rooted in a set**:
  `precedent_materialize` is not vendored to sources, and the session file
  prints a ModuleNotFoundError instead of saying so.
- **A set's copy of `precedent-individual-bootstrap.sh` written before
  2026-10-07 never becomes the stub**: the refresh writes it only when it is
  missing. BestPractice runs a stale copy of its own the same way.
- **The refresh says "nothing to do" about an engine hook a set wires from a
  path outside its `engine_paths`**, so that copy goes stale for good.
- **A set loads itself twice in a linked worktree** (`precedent_resolve.py`
  near line 1331), which also inflates its measured session load.
- **The deep check pushes a receipt to origin** (`publish_pass()`), and no
  document says a check does.
- **FIX SWEEP reaches nothing in the sets**: it decides "in force" by the
  file's presence, not by the target repo's resolver.
- **An untouched two-week-old install cannot finish an update without seven
  hand calls**, all upstream rewording of files the install made from
  templates; the install records no fingerprint for them.
- **Update Vendors tells a session to edit vendored engine files**
  (`retired_mentions()` does not treat the engine's own files as received),
  and the next-refresh warning counts received files as references.
- **A migration that follows step 5 fails `retired-words`** on the
  decommission tool's own ledger; exempt it the way the vocabulary config is.
- **`precedent_bootstrap_source.py` reaches the network and cloned the
  operator's individual set into a scratch home**, against its docstring.
- **The install records a feature branch as the base branch** when
  `origin/HEAD` is unset, and **`--visibility` silently defaults to private**.
- **A private repository off the ladder runs no light check on its pull
  requests**, so an assistant with no terminal gets no check anywhere.
- **The adapter parallels table cannot hold a hook BestPractice ships but
  does not run**, and the check refuses a row for one.
- **`record/GOTCHAS.md` is a second live copy of the gotcha stories**; mark
  it superseded by `gotchas/INDEX.md` and repoint the tools that cite it.
- **Three of BestPractice's own hooks are drifted hand copies of engine
  hooks** (`reply-gate.sh`, `stop-reply-check.sh`, `stop-git-check.sh`).
- **Smaller ones**: duplicated `_declared_base_branch` and commit-check
  helpers; the CI fleet audit's per-workflow counts exceed the repo total;
  a retired-term pattern that catches ordinary English; build_views calling
  a public set private; glossary entries missing for "quick tier" and "code
  owner"; `build_views.py --help` still recommending `--agents-only` for
  sets; two pgrep gotchas that are one trap; `--record-pass` appending a
  second entry for a pass already recorded instead of replacing it.

### In the sets

Filed in each set's own run record (`spec/VERY_DEEP_CHECK.md` there): the
writing set's `create-word-doc` never reaching the occasion index, its
contradiction with `dated-download-names`, and its public leak blocklist
asking for client names; the ladder set's `primary-branch` defined two ways;
the individual set's stale ladder wording in two practices and four closed
records at its root.

## How It Closes

When every bullet above is fixed, decided, or moved to an item of its own.

## Notes

2026-10-17: written by the very deep check that found these.

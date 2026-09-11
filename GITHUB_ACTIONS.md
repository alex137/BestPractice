# GitHub Actions Checks

Precedent uses repository checks for rules that should not depend on a particular person or AI assistant remembering to run them.

This is especially important when working through GitHub-connected ChatGPT. A normal ChatGPT conversation can read and update repository files, but it does not receive a local checkout or an interactive shell *(as of 2026-08 — [MOBILE.md](MOBILE.md) tracks this capability and is the place to re-date it)*. GitHub Actions supplies the missing execution environment: ChatGPT prepares a branch, GitHub runs the checks, and the result appears on the pull request.

## Precedent's Own Workflows (This Repo, Not a Template)

Three workflows run on this repo itself, in [.github/workflows/](.github/workflows/):

- **`docs.yml`** — pre-fork BestPractice content: the Markdown lint job
  described below, running here rather than only shipped as a template.
- **`deep-check.yml`** — added by a 2026-09-03 deep-check audit. Runs
  [tools/verify_harness.py](tools/verify_harness.py),
  [tools/precedent_check.py](tools/precedent_check.py) and
  [tools/doc_sync.py](tools/doc_sync.py) — the three of AGENTS.md's five
  named "deep check" tools that had no continuous-integration (CI) check
  of their own until this landed, having been session discipline only.
  That gap is exactly where
  a same-day audit found two critical, reproduced bugs (a self-referential
  `repo-local` source silently destroying its own content, and a second
  that broke every re-sync after it) sitting undetected on a branch whose
  merges were all green — neither doc_lint.py nor leak_gate.py could ever
  have caught either, since neither runs the resolver or materializer at
  all. Runs on every push and pull request, on every branch, same as
  leak-gate.yml below.
- **`leak-gate.yml`** — added at phase 2 of the Precedent rewrite
  (`b3bfb54`). Runs [tools/leak_gate.py](tools/leak_gate.py)'s structural
  layer on every push and every pull request, on every branch (this repo is
  the branch being published, not just its default). It is the unbypassable
  backstop for the private-source separation described in
  [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s "Source — Who a
  Practice Belongs To": a `git push --no-verify` can skip the local
  [pre-push hook](templates/hooks/pre-push), but not this. See
  [spec/SOURCES.md](spec/SOURCES.md) for what it checks and why it has two
  layers, only one of which can run here. (This section exists because the
  workflow went undisclosed for months after being added — the practice
  requiring disclosure, `github-setup-disclosed`, only fires on a
  newly-added workflow file in the diff being checked, so it structurally
  cannot catch a workflow that was already merged before the practice
  existed to check it. Found by a 2026-09-01 deep-check audit; see
  [tools/verify_harness.py](tools/verify_harness.py)'s
  `check_all_workflows_disclosed` for the tree-wide check added in
  response, which does catch this going forward.)

## What the Markdown Check Does

The supplied workflow:

1. checks out the complete repository history;
2. installs Python and `cmarkgfm`;
3. runs the Precedent Markdown linter;
4. reports warnings in the job log; and
5. fails the pull request only when changed Markdown contains accidental strikethrough.

The linter determines which Markdown files changed relative to the repository's default branch. A full-history checkout is therefore required.

## Install in a Dependent Repository

During Precedent installation, copy:

```text
process/upstream/templates/github-actions/doc-lint.yml.template
```

to:

```text
.github/workflows/bestpractice-docs.yml
```

Commit the workflow together with the other installed Precedent files. The template runs the vendored linter at:

```text
process/upstream/tools/doc_lint.py
```

If the dependent repository instead copies or adapts the linter into its own tools directory, update the workflow command to use that local path and record the adaptation in `process/manifest.json`.

## Install in a Practice-Set Repository (the Views Drift Gate)

An individual or team practice set generates its own views — `AGENTS.md`'s
loader block, [MAP.md](MAP.md) and [GLOSSARY.md](GLOSSARY.md) — from its
`practices/` directory and the engine vendored into its own `tools/`. Copy:

```text
templates/github-actions/views-drift.yml.template
```

to:

```text
.github/workflows/views-drift.yml
```

It runs `python3 tools/build_views.py --repo . --check`, which exits
non-zero when any of the three has drifted from a fresh regeneration. Sets
created by
[tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py)
get it installed automatically; every set created before 2026-09-11 needs
the copy above, and
`python3 tools/precedent_bootstrap_source.py --verify <path>` names it as
missing until it is there.

**Why a source set needs its own gate.** Until 2026-09-11 nothing checked a
generated view anywhere but in this repo, where
[deep-check.yml](.github/workflows/deep-check.yml) runs
[tools/verify_harness.py](tools/verify_harness.py) — and `verify_harness.py`
is deliberately not vendored into a source set. Worse, the generated header
on each view *said* a check was failing the build on drift, so a session
that wondered read the header instead of running anything. Measured in a
real individual set: `MAP.md` sat three practices stale, one of them missing
from its table from the day it landed, under that header. The header now
names `build_views.py --check`, which exists wherever the view does; this
workflow is the half that makes something actually look.

The engine's own drift check cannot substitute.
[tools/precedent_check.py](tools/precedent_check.py) *is* vendored and its
`generated-artifact-provenance` check does run `build_views.py --check` —
but `precedent_check.py` skips any check whose practice is not in force in
the repo it runs in, and a source set's `practices/` holds only its own
practices, never the universal one that check belongs to. Run against a real
individual set on 2026-09-11 it reported `1 skipped`, and a skip is not a
pass.

The workflow **gates and does not fix**: regenerating in CI would leave the
branch's own diff wrong and put a runner bot in the authorship path that
[practices/ci-commits-carry-identity.md](practices/ci-commits-carry-identity.md)
exists to keep clean. The fix is one `python3 tools/build_views.py` on the
branch.

## Enable GitHub Actions

GitHub Actions is normally available automatically, but an organization or repository administrator can restrict it. After merging the workflow onto the default branch:

1. open the repository's **Actions** tab and confirm that the workflow is allowed to run;
2. open a pull request that changes a Markdown file;
3. confirm that **Markdown lint** appears in the pull request checks; and
4. inspect the job log if the check fails or reports warnings.

The first pull request that introduces a workflow may be subject to GitHub's normal approval or security controls, especially for contributions from forks.

Two further settings belong to the same moment and are worth mentioning
when an install finishes ([INSTALL.md](INSTALL.md) §1 step 10): the
**default branch should be named `main`** (**Settings → General → Default
branch**), since the supplied template's `push` trigger names `main` as a
literal string and a differently-named default branch runs no check on
merges; and **workflow permissions should allow Actions to open pull
requests** (**Settings → Actions → General → Workflow permissions**), which
the supplied Markdown check does not need but anything opening a pull
request for the project does. *(Click-paths as of 2026-09-10.)*

## Make the Check Required

Once the workflow has run successfully at least once, add its **Markdown lint** job to the default branch's ruleset or branch-protection required checks.

That changes the rule from advice into enforcement: a pull request cannot merge while the Markdown gate is failing, regardless of whether the change came from ChatGPT, Claude Code, Codex, another agent, or a human editing GitHub directly.

Repository rules vary by account and organization. Use the repository's current **Settings → Rules** or branch-protection controls and select the status check produced by this workflow.

## Updating an Installed Repository

When Precedent updates the workflow template:

1. compare the new template with `.github/workflows/bestpractice-docs.yml`;
2. preserve any dependent-repository adaptations, such as a different default branch or linter path;
3. update the installed workflow;
4. run it through a pull request; and
5. update the corresponding manifest baseline.

Treat the workflow as an installed Precedent artifact. A typical manifest entry is:

```json
{
  "practice": "doc-lint-action",
  "upstream_path": "templates/github-actions/doc-lint.yml.template",
  "local_path": ".github/workflows/bestpractice-docs.yml",
  "granularity": "file",
  "status": "synced",
  "local_sha256": "<filled by practice_audit --update-baseline>",
  "notes": "Runs the vendored linter; preserve repository-specific branch names or paths"
}
```

## Limits

GitHub Actions closes the test-execution gap, but it does not make ordinary ChatGPT identical to a coding-agent workspace *(as of 2026-08)*. ChatGPT still needs the session bootstrap described in the main README so it reads `AGENTS.md`, `MAP.md`, and the task-relevant instructions before working.

The useful division of responsibility is:

> Agents interpret intent and prepare changes. GitHub Actions enforces repeatable checks.

**A workflow that COMMITS is outside
[commit-identity.sh](templates/harness/claude-code/hooks/commit-identity.sh)'s
reach, and nothing here will tell you so.** That hook resolves whoever is
running the session and installs a `pre-commit` backstop refusing the
container's bot account — but it runs at *session start*, in an agent's
session. A GitHub Actions runner never runs it. So a workflow that commits
on your behalf authors as `github-actions[bot]`, on the runner's UTC clock,
and both of those are exactly what an adopter's `commit-author` and
timezone checks exist to refuse.

**A workflow that commits therefore resolves the author itself** — read
`name`, `email` and `timezone` from the individual source's `identity.json`
and **refuse the run outright if any of the three is missing**, rather than
falling back to the bot. A fallback here is the failure: it produces a
commit that looks fine until something checks it.

Found 2026-09-10 in a real practice set, by a refresh workflow that had been
mis-authoring **every** commit it ever made. Nobody had seen it because the
two checks that would have caught it were themselves reporting SKIPPED —
they could not resolve an identity inside a practice set until
[tools/precedent_identity.py](tools/precedent_identity.py) moved into the
vendored engine that same day. The moment they went live, the workflow's own
commit was the first thing they flagged. **Two silent failures were holding
each other up**, which is the general shape worth remembering: a check that
cannot run is not evidence that what it checks is fine.

**A CONSUMING repo's generated views cannot be gated in CI at all, and
the drift gate above refuses rather than pretending.** A consuming repo's
`practices/` is materialized from the sources it resolves: a team source is
a sibling clone outside the repo, an individual source resolves through a
private user-level config. Neither exists in a bare CI checkout, so there is
nothing on the runner to regenerate the views *from* — and
[tools/build_views.py](tools/build_views.py) deliberately exits 0 rather
than writing a block from an incomplete source set, which is the shape a
green-but-blind check would take. So
[views-drift.yml.template](templates/github-actions/views-drift.yml.template)
exits non-zero when it finds the vendored `process/upstream/` layout instead
of running. What covers a consuming repo today is a session running
`python3 tools/precedent_sync_views.py --repo . --check` where the sources
do resolve; [TODO.md](TODO.md)'s
`consumer-views-drift-uncheckable-in-ci` item holds the question of whether
anything better is possible.

Precedent itself ships no committing workflow — its three
([deep-check](.github/workflows/deep-check.yml),
[docs](.github/workflows/docs.yml),
[leak-gate](.github/workflows/leak-gate.yml)) all read and none writes — so
there is nothing to fix here. This is a limit to know before you add one.

*GitHub interface and product behavior verified August 2, 2026. Settings and labels can change.*

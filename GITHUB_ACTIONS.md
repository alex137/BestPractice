# GitHub Actions checks

BestPractice uses repository checks for rules that should not depend on a particular person or AI assistant remembering to run them.

This is especially important when working through GitHub-connected ChatGPT. A normal ChatGPT conversation can read and update repository files, but it does not receive a local checkout or an interactive shell. GitHub Actions supplies the missing execution environment: ChatGPT prepares a branch, GitHub runs the checks, and the result appears on the pull request.

## Precedent's own workflows (this repo, not a template)

Two workflows run on this repo itself, in [.github/workflows/](.github/workflows/):

- **`docs.yml`** — pre-fork BestPractice content: the Markdown lint job
  described below, running here rather than only shipped as a template.
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

## What the Markdown check does

The supplied workflow:

1. checks out the complete repository history;
2. installs Python and `cmarkgfm`;
3. runs the BestPractice Markdown linter;
4. reports warnings in the job log; and
5. fails the pull request only when changed Markdown contains accidental strikethrough.

The linter determines which Markdown files changed relative to the repository's default branch. A full-history checkout is therefore required.

## Install in a dependent repository

During BestPractice installation, copy:

```text
process/upstream/templates/github-actions/doc-lint.yml.template
```

to:

```text
.github/workflows/bestpractice-docs.yml
```

Commit the workflow together with the other installed BestPractice files. The template runs the vendored linter at:

```text
process/upstream/tools/doc_lint.py
```

If the dependent repository instead copies or adapts the linter into its own tools directory, update the workflow command to use that local path and record the adaptation in `process/manifest.json`.

## Enable GitHub Actions

GitHub Actions is normally available automatically, but an organization or repository administrator can restrict it. After merging the workflow onto the default branch:

1. open the repository's **Actions** tab and confirm that the workflow is allowed to run;
2. open a pull request that changes a Markdown file;
3. confirm that **Markdown lint** appears in the pull request checks; and
4. inspect the job log if the check fails or reports warnings.

The first pull request that introduces a workflow may be subject to GitHub's normal approval or security controls, especially for contributions from forks.

## Make the check required

Once the workflow has run successfully at least once, add its **Markdown lint** job to the default branch's ruleset or branch-protection required checks.

That changes the rule from advice into enforcement: a pull request cannot merge while the Markdown gate is failing, regardless of whether the change came from ChatGPT, Claude Code, Codex, another agent, or a human editing GitHub directly.

Repository rules vary by account and organization. Use the repository's current **Settings → Rules** or branch-protection controls and select the status check produced by this workflow.

## Updating an installed repository

When BestPractice updates the workflow template:

1. compare the new template with `.github/workflows/bestpractice-docs.yml`;
2. preserve any dependent-repository adaptations, such as a different default branch or linter path;
3. update the installed workflow;
4. run it through a pull request; and
5. update the corresponding manifest baseline.

Treat the workflow as an installed BestPractice artifact. A typical manifest entry is:

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

GitHub Actions closes the test-execution gap, but it does not make ordinary ChatGPT identical to a coding-agent workspace. ChatGPT still needs the session bootstrap described in the main README so it reads `AGENTS.md`, `MAP.md`, and the task-relevant instructions before working.

The useful division of responsibility is:

> Agents interpret intent and prepare changes. GitHub Actions enforces repeatable checks.

*GitHub interface and product behavior verified August 2, 2026. Settings and labels can change.*

---
slug:            gotcha-2026-09-21-github-actions-rejects-yaml-anchors-python-accepts
status:          live
noted:           2026-09-21
severity:        major
retired:         null
retires_when:    "GitHub Actions adds support for YAML anchors and aliases in workflow files, which it has not as of 2026-09-21"
---

## Symptom

A workflow file uses a YAML **anchor and alias** (`&name` to define, `*name`
to reuse) to avoid repeating a list — most naturally a long `paths:` filter
that both `push:` and `pull_request:` need. `python3 -c "import yaml;
yaml.safe_load(open('w.yml'))"` parses it cleanly, every local check passes,
the file looks right. **GitHub's own workflow parser rejects it**, and the
workflow does not run at all.

The failure is worse than a red check: a workflow GitHub refuses to parse
does not appear as a failing run. It simply does not fire, so the branch
looks like it has no CI rather than broken CI.

## Story

2026-09-21, during the consumer-repo fold that merged each repo's
`bestpractice-docs.yml` (doc lint) and `light-check.yml` into one workflow
with one job — spec/CI_MINUTES_PLAN.md item 15's whole point being that
GitHub bills per job, so two workflows on one pull request bill two
whole-minute floors for about twenty seconds of real work.

The merged workflow needed the same `paths:` list on both its `push:` and
`pull_request:` triggers. The session wrote it the way any YAML author
would:

```yaml
on:
  push:
    branches: [main]
    paths: &check_paths
      - '**/*.md'
      - '**/*.py'
      # ...
  pull_request:
    types: [opened, synchronize]
    paths: *check_paths
```

PyYAML accepts this without complaint — anchors and aliases are core YAML
1.1, and `yaml.safe_load` resolves them. **GitHub Actions does not support
them in workflow files.** The session caught it before pushing and expanded
both lists literally.

**What makes this a trap rather than a typo.** Every local verification this
repository teaches would have passed it. `python3 -c "import yaml; ..."` is
the YAML check named in this repo's own templates and pull-request bodies —
including the ones written during this same incident. A session that
believes "it parses locally" is evidence the workflow will run has a belief
that is true for indentation, true for tabs, true for a missing colon, and
**false for anchors**.

The near-miss cost nothing because it was caught by hand. Had it shipped,
nine repositories would have had a CI workflow that silently never fired,
while the manifest tracked it, the audit recorded it as present, and the
minutes bill went to zero — which is exactly what the change was supposed to
achieve, so the "success" signal and the failure signal are the same
observation.

## Fix

**Expand the list literally in each trigger.** It is duplication, and
duplication is the supported spelling here:

```yaml
on:
  push:
    branches: [main]
    paths:
      - '**/*.md'
      - '**/*.py'
  pull_request:
    types: [opened, synchronize]
    paths:
      - '**/*.md'
      - '**/*.py'
```

**And stop treating a local YAML parse as proof a workflow runs.** It proves
the file is well-formed YAML. It does not prove GitHub accepts it, because
GitHub's workflow schema is a strict subset of YAML. The properties that
differ are not documented in one place; anchors are the one this incident
measured.

Where a reusable block is genuinely wanted, GitHub's own supported
mechanisms are `workflow_call` (a reusable workflow) or a composite action —
both of which cost a job, which is the thing spec/CI_MINUTES_PLAN.md item 13
says to count before reaching for.

## Detecting It, and a Lesson About the Detector

A grep that finds an anchor or alias in a workflow file, from the session
that hit this — **corrected after its first version cried wolf**:

```sh
sed 's/#.*//' "$f" | grep -nE ':[[:space:]]*[&*][A-Za-z0-9_-]+[[:space:]]*$|^[[:space:]]*-[[:space:]]*\*[A-Za-z0-9_-]+[[:space:]]*$'
```

The `sed` strips comments and the `$` anchors to end-of-line. Without both,
the first version matched `*that comparison*` and `**not**` inside ordinary
Markdown-ish prose in a workflow's own comment block, and would have flagged
a clean file on its very first run. A quoted glob like `"**/*.md"` does not
match either.

**The generalisable part is not the regex.** That recipe was tested against
a clean file, passed, and was nearly shipped. What caught it was running it
against a file *known to contain* an anchor as well as one known not to.
**A detector verified only against the clean case has been shown to stay
quiet, which is also what a broken detector does.** Check both directions,
every time, before writing a recipe down — a recipe that false-positives on
its first real run is one nobody runs twice.

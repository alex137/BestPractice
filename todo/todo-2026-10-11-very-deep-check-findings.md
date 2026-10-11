---
slug:              todo-2026-10-11-very-deep-check-findings
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
noted:             2026-10-11
closed:            null
---
## What

What the 2026-10-11 very deep check of BestPractice found and did not fix
in the same run. Scope, as Morgan set it: BestPractice and the sets it
declares, not every consuming repository. Pass 1 rehearsed the guided
install, the developer install, an update from a week-old commit, a
migration and a practice moved between levels, each in scratch with a
fresh-eyes session. What the run fixed is in the commits it landed; this
item holds the rest.

### Calls for Morgan

- **Two workflows on `main` have no approval on record.**
  `.github/workflows/leak-gate.yml` reads "approved by nobody" and
  `deep-check.yml` "edited since it was approved"
  ([ci-workflow-approved](../practices/ci-workflow-approved.md)). Only
  Morgan's own yes approves them.
- **Two unlanded branches have waited since the 2026-10-05 run.**
  `claude/upstream-bug-fix-review-ltbiy8` (an approved `upstream-review`
  practice and tool, nothing equivalent on `main`) and
  `claude/file-sharing-service-spec-0m9c7p` (the only copy of a `share/`
  spec, untouched since July). Each needs land or close.
- **`claude/2026-10-06-upstream-pr-is-the-ask-19akh` carries a decided
  rule change that never landed**: `upstream-bug-stops-here` says opening
  the fix upstream as a pull request is the stop, closing the item that
  asked. Recommended: land it.
- **The two retired sets can finish retiring.** No repository declares
  `precedent-shared-repo-maintenance` or `precedent-shared-working-style`
  any more; once both are archived on GitHub,
  [retired-set-takes-only-its-retirement](../practices/retired-set-takes-only-its-retirement.md)
  has met its stated end.

### Found, not fixed here

- **The writing set's `no-stale-counts` check reads a dated count as a
  claim about today.** Run against this repo it flags about 70 sentences,
  nearly all in dated records (`decisions/`, `todo/`, `gotchas/`,
  `record/`, `evals/`, the frozen `PRACTICES.md`) and `## Story` sections.
  The run tried declaring those directories exempt and took it back: the
  push check rightly refused an exemption with no root fix, and `spec/`
  mixes live documents with dated ones. The fix is the check's, in the
  writing set: read a `## Story` section, a closed or superseded file, and
  a sentence carrying its own date as history. It is a report here, never
  a gate.
- **Both shared sets still carry the old 196-line
  `.claude/hooks/precedent-individual-bootstrap.sh`**; the generator now
  writes a 29-line stub (BOOTSTRAP DRIFT). Their Update Vendors runs on
  2026-10-11 did not replace it. The individual set's
  `precedent-universal-catalogue.sh` and `CLAUDE.md` differ the same way.
- **An update of a never-edited install stops LEFT FOR YOU** on template
  wording the adopter never touched (`MAP.source.md`, `GLOSSARY.source.md`,
  `local/practices/project-voice.md`), and misses other drift of the same
  kind (pass 1, update rehearsal). An unmodified instance should take the
  new template itself.
- **The README's promise that the assistant notices "always / never / from
  now on" and offers a rule has no channel in a fresh install**: nothing in
  its resident block or occasion index fires on it, and `rule-scope-ask`
  is one of the five practices the install's own advisory calls reachable
  by no channel.
- **Private words have no home without an individual set.** SETUP.md sends
  them only to the individual set's leak blocklist; an administrator who
  declines one loses them, while ADOPTING.md promises a check for private
  words before anything is published.
- **The installed AGENTS.md asks every session to attach
  `<shared-set-repo-name>` and `<individual-repo-name>`** even when the
  administrator has neither, and nothing says to delete the bullet.
- **The ladder's `tier-branch` and `checks-follow-the-tier` still describe
  pre-staging as where work lands.** True for the three-tier ladder; a repo
  already on staging reads them beside `ladder-in-a-repo-on-staging`.
- **The leak blocklist knows none of the private repositories' bare
  names** (REPOSITORY VISIBILITY recommendations). Adding them belongs in
  the individual set's blocklist, never in this public tree.

- **The root `TODO.md` redirect stub states two things that stopped being
  true**: that CI refuses a change to it (the deep check does), and that
  AGENTS.md's gotcha index is hand-kept and links into
  `record/GOTCHAS.md#gN` (AGENTS.md points at the generated
  [gotchas/INDEX.md](../gotchas/INDEX.md)). The same check refuses any
  change to the stub, so it cannot be corrected without an exemption.

- **An installer run into a project with a hand-written `MAP.md`** writes
  `MAP.source.md` from the template, and the sync then regenerates
  `MAP.md` from it, which may replace the project's own map. Not verified
  in this run.

## Notes

2026-10-11: opened by the very deep check that found them.

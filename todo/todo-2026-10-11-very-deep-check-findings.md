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

Settled 2026-10-11, in his words: "Both yml are fine and approved. On
Alex's fix: approved. On my idea of writing up a prompt in the boildown
session with the errors and warnings given - yes let's rebuild it but only
in ladders and also only when the user is a code owner. And on the July
one: close it". Both workflows are pinned in `github_ci_approved`; Alex's
`upstream-bug-stops-here` amendment landed; `upstream-review` was rebuilt
(the ladder set's practice, run then by an engine tool that left the
engine for the ladder set on 2026-10-17);
the `share/` spec branch is to be deleted.

- **The two retired sets can finish retiring.** No repository declares
  `precedent-shared-repo-maintenance` or `precedent-shared-working-style`
  any more; once both are archived on GitHub, the temporary rule
  `retired-set-takes-only-its-retirement` has met its stated end.
  *Answered 2026-10-11: both were already archived; the rule was removed
  ("Go remove it").*

### Found, not fixed here

- **The writing set's `no-stale-counts` check reads a dated count as a
  claim about today.** Run against this repo it flags about 70 sentences,
  nearly all in dated records (`decisions/`, `todo/`, `gotchas/`,
  `record/`, `evals/`, the frozen [PRACTICES.md](../PRACTICES.md)) and `## Story` sections.
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
  `precedent-universal-catalogue.sh` and its Claude Code pointer file differ
  the same way.
- **An update of a never-edited install stops LEFT FOR YOU** on template
  wording the adopter never touched (the map and glossary sources from
  [MAP.md.template](../templates/MAP.md.template) and
  [GLOSSARY.md.template](../templates/GLOSSARY.md.template), and the project
  voice from [project-voice.md.template](../templates/local-practices/project-voice.md.template)), and misses other drift of the same
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

- **The root [TODO.md](../TODO.md) redirect stub states two things that stopped being
  true**: that CI refuses a change to it (the deep check does), and that
  AGENTS.md's gotcha index is hand-kept and links into
  `record/GOTCHAS.md#gN` (AGENTS.md points at the generated
  [gotchas/INDEX.md](../gotchas/INDEX.md)). The same check refuses any
  change to the stub, so it cannot be corrected without an exemption.

- **A fresh install opens with an advisory about upstream's own
  catalogue** (`layered-practice-packs`: five universal practices,
  `install` and `very-deep-check` among them, "reachable by no channel"),
  telling the adopter to wire in what only this repo can fix. Either those
  practices get a channel or the advisory stops reaching consumers.
- **A guided install (SETUP.md) leaves a GitHub-only team with no check at
  all in a private repository**: GitHub's light check runs only on a
  Produce's `to-main-` branch, and a team with no terminal has no local
  check. SETUP.md now says so; whether such a team should get one is open.
- **The migration guide (spec/MIGRATING_EXISTING_INSTALLS.md) has fallen
  behind the tools** (pass 1 migration rehearsal): step 0 says to ask the
  person which sets to declare, where INSTALL.md says never to; step 1's
  `rm -rf` is now done by the tool, and it never says when to run
  `checkin.py record`, so step 7 reports the old commit; it names
  `process/upstream/tools/`, which the first update deletes; step 5's
  decommission refuses until step 6 has run; step 8's list of what a clean
  run needs misses `session-trailer`, the classic GETTING_STARTED.md and an
  unregistered [todo/TODO.md](TODO.md), and its `todo_migrate` turns the recurring
  check-in into an item doc_lint fails; `--ensure-tiers --apply` prints
  nothing when the ladder is off. One HIGH item, declaring a deleted set,
  was fixed in this run.
- **Moving a practice (spec/MOVING_PRACTICES.md) has six gaps** (pass 1
  move rehearsal): mentions in consumer repos are fixed only with a knob
  the help calls a test setting; universal is matched by its folder name,
  not its declared name, so "(precedent)" mentions are not fixed; the
  universal draft fails `routing-reason` and later
  `pending-approval-outlives-its-merge`; the universal copy's Story names
  the destination set in plain text, which could be private; a
  copy-and-delete is named once by the sync and by no check after; and the
  page still points at `precedent-beta-v01`, a retired practice, and the
  old `team` level. A new set's skeleton README also links files the
  procedure deletes.
- **A bootstrap in a cloud session reaches the network outside its
  folder**: with `CLAUDE_CODE_REMOTE` set, the resolver's self-heal clones
  the real individual set into whatever `$HOME` is in force, scratch or
  not.
- **An installer run into a project with a hand-written repository map**
  writes the map's source file from the template, and the sync then
  regenerates the map from it, which may replace the project's own. Not
  verified in this run.

## Notes

2026-10-11: opened by the very deep check that found them.

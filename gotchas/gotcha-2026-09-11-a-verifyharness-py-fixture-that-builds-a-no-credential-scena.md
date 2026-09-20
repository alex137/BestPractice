---
slug:            gotcha-2026-09-11-a-verifyharness-py-fixture-that-builds-a-no-credential-scena
status:          retired
noted:           2026-09-11
severity:        null
retired:         "2026-09-11"
retires_when:    null
---
## Symptom

A `verify_harness.py` fixture that builds a "no credential" scenario inherits the container's real one

## Story

<details>
<summary>The full entry as it stood until 2026-09-11</summary>

- **A `verify_harness.py` fixture that builds a "no credential" scenario
  inherits the container's real credential, so it asserts the opposite of
  what it ran — and it only fails once the environment starts carrying
  one.** 2026-09-11: four harness failures were reported to a person as
  "the absent `PRECEDENT_GIT_TOKEN`". The token was **present**
  (`env | grep -c PRECEDENT` said 6), and two of the four failed *because*
  of that. `check_source_credentials` and
  `check_individual_source_bootstrap_self_heals` each spawn subprocesses
  with `{**os.environ, ...}`; the cases asserting *"with no base url the
  team source is named as NOT in force"* and *"that hook degrades quietly
  when nothing else supplies one"* therefore ran against a real
  `PRECEDENT_SOURCE_BASE_URL`, tried to clone from github.com, and failed on
  `could not read Username` — which reads exactly like a missing credential
  and is a present one.
  **The diagnosis is backwards in the expensive direction**: it sends you to
  go fix access you already have. Separate the two by running
  `env -u PRECEDENT_GIT_TOKEN -u PRECEDENT_SOURCE_BASE_URL python3
  tools/verify_harness.py` — if failures *disappear*, the fixture is
  inheriting, not missing.
  One fixture's own comment said *"Run here with a HOME that has nothing and
  no git credentials"* while inheriting both, which is the tell: **a premise
  stated in a comment is not a premise the fixture established**
  ([fixture-owns-its-state](../practices/fixture-owns-its-state.md)). Both
  `run()` helpers and all four hook subprocesses now pop the two variables,
  so a case that wants either supplies it explicitly. Before that the whole
  harness's result depended on which container it ran in, and nothing said
  so.
  **The per-fixture pops are not the whole fix, because the next fixture
  will not have read them.** That practice's own Rule says to clear the
  ambient inputs at the top, once, rather than in the fixture that happened
  to notice — so the scrub also sits at the head of
  [tools/verify_harness.py](../tools/verify_harness.py), beside the
  `GIT_AUTHOR_*` one that was the identical shape four days earlier, and
  `check_fixtures_own_the_credential_environment` holds it there: it plants
  both variables in a subprocess, imports the module, and asserts they come
  back gone. Neutering the scrub turns three of its four cases red, the
  planted one included — so it is a control, not a restatement.
  **Third instance, 2026-09-11, `PRECEDENT_FRESHNESS_ALSO`** — it names
  OTHER repositories the freshness guard checks, so a guard fixture inheriting
  it walked out of its own temporary clone into this container's real attached
  sets, could not fetch a private one, and blocked. Both guard copies reported
  *"pre-write does not block a branch absent from origin (exit 2)"*, red on any
  machine with the variable and green everywhere else. **The tell is a block
  naming a repo or branch the fixture never created.** Scrubbed at the head of
  [tools/verify_harness.py](../tools/verify_harness.py) with the other two, and
  planted-and-asserted by `check_fixtures_own_the_credential_environment`.

  **The generalization is worth more than the fix: an ABSENCE is state
  too.** A fixture constructing "no credential is available" owns that
  absence exactly as much as it owns a file it wrote, and owning it means
  scrubbing the environment rather than merely declining to set anything.
  Same shape as the fixture whose `HOME` got a clone written into it, one
  level out — that one owned its scenario and not the environment the
  scenario was read from.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

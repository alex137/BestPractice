---
slug:        two-check-levels
title:       "Two named check levels: a fast one for every commit, a full one before merge"
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "naming what \"run the checks\" means in a repo"
gates:       []
index_clause: "name a fast check and a full check; say which gates what"
checked_by:  "tools/precedent_check.py"
defines:     ["light check", "deep check"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 44
---
## Rule
A repo of any size ends up wanting two different things when it
says "check this": a fast, cheap sanity pass a session runs constantly
without thinking about it, and a slower, complete audit that gates a merge.
Give the two levels fixed, distinct names in the repo's own
[GLOSSARY.md](https://github.com/alex137/BestPractice/blob/staging/templates/GLOSSARY.md.template) — a plain pair like *light
check* and *deep check* reads well, but any repo-chosen pair is fine — so a
person or a session can ask for one or the other unambiguously ("run the
light check before you commit that" vs. "this needs a deep check before we
merge") instead of re-describing what "check" means every time.

## Detail
**The fast level holds one cheap, mechanical audit, and it runs on every
commit path.** At minimum: conflict markers, invalid JSON or YAML syntax
(a practice file's own frontmatter included), secret-shaped strings (an
Amazon Web Services (AWS)-style key ID, a Privacy-Enhanced Mail (PEM)
private-key header, a token), and broken relative doc links. Run it before
every commit, and wire it into continuous integration too, so it binds
every push even when a session forgets to run it by hand. A style linter
(accidental strikethrough, unlinked references, unglossed acronyms) is a
complementary tool, not a substitute: this is the broader, cheaper net for
"something obviously went wrong" that is not a style question.

**Where a repo installs a vendored practice layer, the fast level also
checks the install is real**, not a plain copy: the tracking manifest
exists, parses, has at least one entry, and every recorded path exists on
disk. Where materialization writes per-source check scripts, it can also
confirm each one traces back to a declared source, which catches a script
hand-dropped into the output directory, where the next sync silently
deletes it. **Attribute through the committed provenance record** (the
consumer's `MANIFEST.json`), never by re-resolving sources at check time: a
private source resolves only through a sibling clone or a person's own
config, neither of which a bare CI checkout has. So a file with no manifest
record is the real orphan and fails; a recorded file whose source is not
reachable here is unverifiable, not orphaned, and is skipped; only a
recorded file whose source *is* reachable gets its bytes checked.

*(2026-09-05, in a repository that installs a shared set: a first attempt
at the provenance check resolved sources live and failed fourteen files on
the next push, every one legitimately sourced from a private set a GitHub
Actions checkout cannot reach. Fixed the same day by attributing through
the committed manifest instead.)*

**The deep check must run each gate in the SHAPE continuous integration (CI)
runs it.** Naming the commands is not enough if CI runs one of them
differently — sharded across jobs, behind a flag, with an environment
variable set. A definition that names the bare command certifies a shape
nobody ships, and the session gets a green answer with authority behind it.

*(2026-09-21, in the repository that wrote this practice: the deep check's
definition named five commands, and CI split one of them across two jobs
using variables no local run sets. The filter path those variables select
was therefore code **no local run ever executed** — and it held a crash. The
full local suite reported `244 passed, 0 failed` while both sharded CI jobs
died before their first verdict. The session had run the whole deep check,
seen it green, and opened a pull request on that basis.)*

**Deliver it as one command, not as an instruction to remember.** Where CI
splits a gate, the repo's own tool grows a mode that runs every shape in
sequence — the shards partition the work, so the pair costs about what one
run costs rather than double. A sentence telling sessions to run two extra
commands is a sentence that gets skipped exactly when time is short, which
is the drift this practice's own **Why** already names.

**Say what that mode does not prove.** Running CI's command shape locally is
not running CI: the environments differ, and a check keyed to something only
one of them has will disagree. Green on the local shape means the shape is
not what breaks. It does not mean CI is green, and a mode that implies
otherwise repeats the failure it was built to fix.

**A failing test in the deep check belongs to whoever shipped it, and "it
fails on the base branch too" is never where that ends.** In a repository
that resolves practice sources, most of the tests its deep check runs were
written somewhere else and materialized in, and the generated driver
(`tools/checks/tests/run_all.sh`) names each failing test's source. A
failing one is a bug in that source: fix it there and report it there, from
a session rooted in that source's repository or with a hand-off to one.
Noting it as pre-existing is true and changes nothing, because nothing else
routes it home — it stays red in every repository that carries it, and a red
suite everyone has learned to read past no longer gates anything.

**The source's half: its own push check runs its tests a second time shaped
like a consumer**, with git ignoring what consuming repositories commonly
ignore ([tools/precedent_consumer_shape.py](../tools/precedent_consumer_shape.py)),
so a test that only works in its home layout fails before it ships. A test
that plants a fixture file stages it with `git add -f`, never a plain
`git add`.

*(2026-09-25: a test staged a fixture under `vendor/` with a plain `git add`.
It passed on every run in its source, where nothing ignores `vendor/`, and
failed for days in a consuming repository whose dependency manager's
`vendor/` was ignored — each session there calling it pre-existing and
moving on, since the test was not theirs and nothing said whose it was.)*

## Why
Without named levels, "run the checks" is ambiguous between two
very different costs, and the drift goes one of two ways: sessions run the
expensive audit so often that it gets skipped when time is short, or they
run only the cheap pass and the expensive one quietly stops happening
before merges. Naming the two levels separately keeps both cadences
legible: the fast one stays cheap enough to run on every commit path with
no friction, the full one stays a deliberate, named gate that is obviously
missing if it's skipped.

## Story
No dated incident was recorded. The rule identifies a drift with two
directions, and naming both is what makes the case.

Without named levels, "run the checks" is ambiguous between two very
different costs, and the ambiguity resolves itself badly one of two ways.
**Either sessions run the expensive audit so often that it gets skipped
when time is short** -- the gate is dropped precisely when the work is most
rushed -- **or they run only the cheap pass, and the expensive one quietly
stops happening before merges**, with nothing marking its absence.

Both endpoints look locally reasonable while they are happening, which is
why the fix is naming rather than discipline.

Named levels keep both cadences legible. The fast one stays cheap enough to
run on every commit path without friction, and the full one stays a
deliberate, named gate that is obviously missing when it is skipped -- and
"obviously missing" is the whole property being bought.

The rule deliberately does not mandate the words. Any repo-chosen pair is
fine, provided the pair is fixed and written in the repo's own glossary,
because the value is in the distinction being nameable, not in the names.

**What the fast level holds was folded in on 2026-09-28**, from the shared
set for repository maintenance, whose `light-check` practice said it: the
minimum audit list, the CI wiring, the install-is-real extension and the
committed-manifest lesson above. Morgan approved folding the overlap in, on
a session's recommendation (strength: assented). The set's copy stays there
for now because it also carries that set's own implementation of the audit,
a check script that did not move.

## Install
This repo's own [tools/doc_lint.py](../tools/doc_lint.py) is
already the fast pass — it scans only the markdown a session touched — and
[tools/practice_audit.py](https://github.com/alex137/BestPractice/blob/staging/tools/practice_audit.py) is already the full one
— the public-safe scrub, baseline-hash checks, and everything else that
needs the whole repo. Naming them is the only step this practice adds: pick
the repo's own pair of names, add both to `GLOSSARY.md` with what each one
actually runs, and reference the names (not just the script paths) in the
merge runbook ([merge-runbook](merge-runbook.md)) and in any CI wiring ([convention-to-audit](convention-to-audit.md)). A repo that
adds its own extra fast checks (secret-shaped strings, conflict markers,
JSON/YAML syntax) folds them into the "light" name rather than inventing a
third gate — two named gate levels is the right number for almost every repo.

**A rare, on-request audit is not a third level, and does not count against
that.** The test is whether a session has to run it to land work. Something
that gates a commit, a push, or a merge is one of these two levels and must
fold into one of the two names; something a person asks for by name, that no
gate ever waits on, is a separate mechanism and gets its own name — this
repo's own [very-deep-check](https://github.com/alex137/BestPractice/blob/staging/practices/very-deep-check.md) is exactly that, and is
named separately for exactly that reason. What this rule forbids is a third
*gate*, because that is what puts a session in the position of guessing which
checks it must run before it can commit.

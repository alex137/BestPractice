---
title:         A change of language runtime is proven before it lands
kind:          proposal
status:        drafted
opened:        2026-10-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "When the Python a repository runs on changes -- its own declaration, or the engine's default -- nothing runs the repository's code on the new version before the change lands, and PHP has no declaration at all. Proposal: a runtime change selects the full suite under the new interpreter at the push that carries it, and one-python generalizes to one declared runtime per language."
---
# A change of language runtime is proven before it lands

## The question

Morgan, 2026-10-16: "when a version of python (or php for repos that use
that?) is changed/defined, do we make sure there is nothing that breaks?"

The short answer today is no. Precedent makes sure every place in a
repository *uses the same* Python. Nothing makes sure the repository's code
*still works* on a Python it has just moved to. For PHP, or any other
language, there is no declaration at all.

## What exists today

[one-python](../practices/one-python.md) (2026-10-13) came from a consumer
where `python3` was 3.11, the code had been written for 3.12, and the
packages were installed into a third interpreter. It settled *which* Python:

- **The declaration.** `precedent.json` says `"python": {"version": "3.12",
  "packages": [...]}`. With no `version`, the engine's own
  [`DEFAULT_VERSION`](../tools/precedent_python.py) applies (3.12 since
  2026-10-15).
- **Session setup.** `tools/precedent_python.py setup`, run at session
  start, installs the declared packages into the declared interpreter
  (past the Python Enhancement Proposal (PEP) 668 refusal) and makes `python3`, `python`, `pip3` and
  `pip` mean that interpreter for the rest of the session. `check` says
  when `python3` is not the declared one.
- **The `one-python` check** in
  [`tools/precedent_check.py`](../tools/precedent_check.py) refuses a
  tracked Python file that starts `python3` by name instead of
  `sys.executable`, and a GitHub workflow whose `python-version` differs
  from the declared version.

What none of that does:

1. **No test runs on the new version before it lands.** Changing `"3.12"`
   to `"3.13"` in `precedent.json` is a one-line diff. The push check
   judges it like any other one-line change of a JSON file: at the basic
   tier a push to `staging` gets, it does not run the repository's own
   test suite at all, and the session that made the change still has the
   old interpreter as `python3` until the next session start. Into `main`,
   Produce runs the quick checks; the full suite runs only when the
   person's CI cadence makes GitHub's test due (in a private repository,
   at most once every 168 hours by Morgan's setting), or when somebody
   runs `--run-tests main`. So a version change can reach `main` with no
   run of the repository's code on the version it now declares.
2. **The engine's default moves every repository that does not declare
   one, silently.** `DEFAULT_VERSION` is an engine constant. When it moves,
   every consuming repository relying on the default takes the new
   version at its next Update Vendors, inside a diff of a hundred engine
   files, and nothing in that update says "your Python changed" or runs
   that repository's code on it.
3. **Packages are not pinned.** `"packages": ["python-docx"]` installs
   whatever version pip resolves today. A new major version of a package
   can break a repository with no change in that repository at all.
4. **GitHub's workflows do not install the declared packages.** The
   light-check template installs `pyyaml` and nothing else; BestPractice's
   own deep check installs `cmarkgfm markdown`. A repository whose checks
   import a declared package fails, or skips, on GitHub for a reason the
   session never sees.
5. **PHP, or any other language, has nothing.** The engine recognizes
   `php` and `composer` only as words: a workflow step that runs them is
   flagged as something nothing local repeats
   ([`_RUNNER_RE`](../tools/precedent_vendor_engine.py)), and [`doc_lint.py`](../tools/doc_lint.py)
   knows `php` is a command name. There is no declared PHP version, no
   setup, no check that the PHP in a session or in a workflow matches
   anything.

### What actually breaks across a version change

So the plan is sized to the risk, the concrete failures, by kind:

- **Removed standard modules.** Python 3.13 removed the "dead batteries"
  of PEP 594 (`cgi`, `cgitb`, `crypt`, `telnetlib`, `nntplib` and others).
  Code that imports one fails at import, which a parse check does not see.
- **New syntax used, old interpreter running it** -- the 2026-10-13
  incident, in the other direction: code written for the new version
  parses on it and fails to parse on the old one.
- **Changed behavior with no error**, for example a deprecation becoming
  the default. Only a test that exercises the behavior sees it.
- **A package with no build for the new version.** pip falls back to
  building from source, which fails in a container without a compiler,
  and the install step says so in a line nobody reads.

The first two are caught by running the repository's code at all; the
third only by its tests; the fourth by the install step reporting a
failure loudly.

## Options considered

**A. Do nothing; rely on GitHub's test.** Rejected. In a private repository
the test is not due for up to a week, and it installs neither the declared
packages nor necessarily the declared version (gap 4), so it is not a test
of the change at all.

**B. Parse-check every tracked Python file under the declared version.**
Cheap, and it would have caught the 2026-10-13 incident. Attacked: it
misses removed modules (they fail at import, not at parse), behavior
changes, and packages. Kept as one cheap part of the answer, not as the
answer.

**C. Treat a runtime change as a full-suite change.** When a push carries a
change to what the runtime is -- the `python` key of `precedent.json`, or
`DEFAULT_VERSION` for a repository that does not declare one -- the push
check runs the full suite instead of the basic tier, under the new
interpreter. Attacked:

- *The session's `python3` is still the old one.* So the run must start
  the suite with the new interpreter explicitly (`python3.13
  tools/verify_harness.py`, or the repository's `run_all.sh` with that
  interpreter first on `PATH`), after installing the declared packages into
  it -- `precedent_python.install()` already does exactly that. Answered.
- *The new interpreter is not installed in the container.* Then the
  change cannot be proven here, and the push says so and refuses, naming
  the interpreter, rather than passing on a run that did not happen
  (`not verified is not current`). The person can still push with the
  existing override, which is recorded.
- *The full suite is slow* (BestPractice's is about ten minutes). A runtime
  change is rare, and it is exactly the change whose risk the basic tier
  cannot see, so paying the full suite for it is in proportion. Every
  other push is unaffected.
- *The default moves inside an Update Vendors.* The update knows the old
  and new `DEFAULT_VERSION` (both engine copies are on disk during the
  refresh), so it can say "this repository's Python moves from 3.12 to
  3.13" as its own step and, where the repository relies on the default,
  run that repository's suite under the new version before reporting DONE.
  The alternative -- every repository pinning its version so the default
  never moves under it -- was attacked and rejected: it trades a loud,
  tested move for a silent drift away from what GitHub runs.

**D. Pin package versions** (`"packages": ["python-docx==1.1.2"]`).
Attacked: pinning without a way to move the pins forward means nobody ever
takes a security fix. Proposed only as optional: `precedent_python` accepts
a pin when a repository writes one (pip already does), and the runtime
change check (C) also fires when a pin changes. Not made a requirement.

**E. A generic runtime declaration.** Generalize `"python"` into
`"runtimes": {"python": {...}, "php": {"version": "8.3", ...}}`. Attacked:
the engine knows how to set up Python (it is written in it); for PHP it
would need to know how to find an interpreter, install Composer packages,
and run a repository's tests, and no repository that uses Precedent runs
PHP today -- building that before the first one exists is speculation.
Revised: the *declaration* and the *consistency check* generalize now
(cheap, and they catch a workflow's `php-version` disagreeing with the
declaration the same way `one-python` does for Python); the *setup* and the
*change check* for a language are built when the first repository that
uses it needs them, from the same shape.

## The proposal

1. **A runtime change is a full-suite push, under the new interpreter.**
   The push check selects its full tier when the diff changes the `python`
   key of `precedent.json`, a declared package pin, or -- in a repository
   with no declared version -- the engine's `DEFAULT_VERSION`. It installs
   the declared packages into the new interpreter with
   `precedent_python.install()` and runs the suite with that interpreter.
   No new interpreter in the container: refused, naming it. The selection
   lives in the push check's tier choice, one place, so the gate, Booked
   and Produce all get it.
2. **A parse-and-import pass** over every tracked Python file under the
   declared interpreter, run as part of (1) and also by the very deep
   check: `py_compile` each file, then import each module the repository's
   own code imports from the standard library. Cheap, and it names a
   removed module by name rather than as a traceback deep in a test.
3. **Update Vendors says when the Python moves**, as its own step, and runs
   (1)'s check for a repository that relies on the default, before DONE.
4. **GitHub's workflows install what the repository declares**: the
   templates replace their hard-coded `pip install` lines with
   `python tools/precedent_python.py setup`, and their hard-coded
   `python-version` with the declared one, which `one-python` already
   checks. Rolled out through the templates and Update Vendors, like any
   template change.
5. **One declared runtime per language.** `precedent.json` gains
   `"runtimes"`, with `"python"` kept as its first member (the existing
   key stays readable, so no repository has to migrate). `one-python`
   becomes `one-runtime`: for each declared language, workflows set the
   declared version (`python-version`, `php-version`, `node-version`), and
   no tracked file starts that language's interpreter by bare name where
   the engine offers the declared one. Setup and the change check for a
   language other than Python wait for the first repository that uses it.

### What it does not cover

- A behavior change no test exercises still lands. Only tests catch that,
  and writing them is the repository's own work.
- A repository whose code runs nowhere but GitHub (a workflow step calling
  a runner the session never runs) is tested on GitHub only;
  `_RUNNER_RE` already names those steps.

## Rollout

Parts 1 to 3 and 5 are engine changes in BestPractice; part 4 is a template
change. All reach consuming repositories through Update Vendors, and none
needs a repository to change anything first. The first Update Vendors that
carries part 3 is itself the first runtime move it reports, if the default
has moved by then.

## Build order

1. Part 2 (parse-and-import), alone: smallest, useful by itself.
2. Part 1 (the full-suite selection), with harness cases for: a version
   change selecting the full tier; the run using the new interpreter; a
   missing interpreter refusing by name; an unrelated `precedent.json`
   change not selecting it.
3. Part 3 (Update Vendors' step).
4. Part 4 (templates), then part 5 (the declaration's shape and the
   generalized consistency check).

## Decisions for the person

- Whether a missing new interpreter **refuses** the push (proposed), or
  only warns.
- Whether package pins stay optional (proposed) or become required.

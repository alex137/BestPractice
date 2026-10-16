---
title:         A change of language runtime is proven before it lands
kind:          proposal
status:        drafted
opened:        2026-10-16
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "When the Python a repository runs on changes -- its own declaration, or the engine's default -- the full local suite that runs after Produce still runs on the session's old Python, so nothing tests the code on the new version; and PHP has no declaration at all. Proposal: every full local run starts the Python the tested commit declares, installing it with uv when it is missing and recording the run as not verified only when that fails; a lock file records the package versions of the last passing full run, and moves only when a new full run passes; and one-python generalizes to one declared runtime per language."
---
# A change of language runtime is proven before it lands

## The question

Morgan, 2026-10-16: "when a version of python (or php for repos that use
that?) is changed/defined, do we make sure there is nothing that breaks?"

**The full local tests run, in full, after every Produce.** Whenever
GitHub's test is not due, Produce runs the repository's whole local suite on
`main` right after the merge (`--run-tests main`), not a sample of it; when
GitHub's test is due, GitHub runs it. The only Produce with no full run
after it is one whose exact commits a Debut already tested, one that
changed nothing but prose, or one the person asked to be fast. A version
change in `precedent.json` is none of those, so it always gets a full run.

**The gap is which Python that run uses, not whether it runs.** It starts
the suite with the Python the session is already running, and a session
switches to a newly declared version only at its next start. So the full
run right after a version change tests the new code on the old Python. For
PHP, or any other language, there is no declaration at all.

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
- **The hooks.** The session file that re-points `python3` reaches the
  session's own commands, never a hook: Claude Code starts each hook with
  its own PATH. Since 2026-10-16 setup also links the declared interpreter
  at `.precedent/python-bin`, and every hook script that starts `python3`
  puts that link first, so the gates -- the push check among them -- run
  on the declared Python with its packages. That is the session's
  declared Python, though: a commit that changes the declaration is still
  checked on the old one until the next session start, which is what
  part 1 below fixes for the full run.
- **The `one-python` check** in
  [`tools/precedent_check.py`](../tools/precedent_check.py) refuses a
  tracked Python file that starts `python3` by name instead of
  `sys.executable`, and a GitHub workflow whose `python-version` differs
  from the declared version.

What none of that does:

1. **No test runs the code on the new version.** Changing `"3.12"` to
   `"3.13"` in `precedent.json` is a one-line diff. The full suite does
   run: Produce runs it locally on `main` right after the merge whenever
   GitHub's test is not due (`--run-tests main`), and GitHub runs it when
   it is. But the local run starts the suite with the Python the session
   is already running
   ([`precedent_branches._check`](../tools/precedent_branches.py) passes
   `sys.executable`), and the session that made the change still has the
   old interpreter until its next session start, when setup re-points
   `python3`. So the run right after the change tests the new code on the
   old Python, and passes. GitHub's run, when due, sets the version its
   workflow names, which `one-python` keeps equal to the declaration --
   but in a private repository it is due at most once every 168 hours by
   Morgan's setting, and it does not install the declared packages
   (gap 4). (Corrected 2026-10-16: the first draft said the full suite
   runs only on GitHub's cadence; Morgan pointed out the local run.)
2. **The engine's default moves every repository that does not declare
   one, silently.** `DEFAULT_VERSION` is an engine constant. When it moves,
   every consuming repository relying on the default takes the new
   version at its next Update Vendors, inside a diff of a hundred engine
   files, and nothing in that update says "your Python changed" or runs
   that repository's code on it.
3. **Packages are not pinned, and nothing records what passed.**
   `"packages": ["python-docx"]` installs whatever version pip resolves
   today. A new major version of a package can break a repository with no
   change in that repository at all, and when it does, nothing says which
   version last worked. A repository that writes a pin by hand
   (`"python-docx==1.1.2"`) gets that version, and then keeps it forever:
   no tool moves a pin forward when a newer version would pass.
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

**C. Treat a runtime change as a full-suite change before it lands.** When
a push carries a change to what the runtime is -- the `python` key of
`precedent.json`, or `DEFAULT_VERSION` for a repository that does not
declare one -- the push check runs the full suite instead of the basic
tier, under the new interpreter. Attacked, and then cut down:

- *The full suite already runs after Produce's merge.* Running it before
  the merge as well buys only the time between the merge and that run, and
  the standing rule is to merge and be told of a problem rather than wait
  (Alex, 2026-10-08: "Didn't we decide that we would merge and get
  notified of problems instead?"). What that run lacks is the right
  Python, not the right moment. So the proposal keeps the run where it is
  and fixes the interpreter it starts (C'). A pre-merge full run stays
  available for a repository that wants it, as the tier override it
  already is.

- *The session's `python3` is still the old one.* So the run must start
  the suite with the new interpreter explicitly (`python3.13
  tools/verify_harness.py`, or the repository's `run_all.sh` with that
  interpreter first on `PATH`), after installing the declared packages into
  it -- `precedent_python.install()` already does exactly that. Answered.
- *The new interpreter is not installed in the container.* Then the
  run installs it first, with `uv python install <version>`: tried in a
  hosted session on 2026-10-16, it downloaded and installed Python 3.14
  in about three seconds, into uv's own directory, leaving the system's
  Python alone. Only when that install fails -- no uv, the download
  refused, no such version -- is the change unproven here, and then the
  run says so and records it as not verified, naming the interpreter and
  why it could not get it, rather than passing on a run that did not
  happen (`not verified is not current`).
- *The full suite is slow* (BestPractice's is about ten minutes), and it
  already runs in full after Produce; a second run before landing would
  pay it twice for one change.
- *The default moves inside an Update Vendors.* The update knows the old
  and new `DEFAULT_VERSION` (both engine copies are on disk during the
  refresh), so it can say "this repository's Python moves from 3.12 to
  3.13" as its own step and, where the repository relies on the default,
  run that repository's suite under the new version before reporting DONE.
  The alternative -- every repository pinning its version so the default
  never moves under it -- was attacked and rejected: it trades a loud,
  tested move for a silent drift away from what GitHub runs.

**D. Pin package versions** (`"packages": ["python-docx==1.1.2"]`).
Attacked: a pin a person writes by hand never moves, so nobody ever takes a
security fix, and when Python moves the pins stay where they were even if
newer versions would pass. Required pins were rejected for that reason.
Kept as optional: `precedent_python` honors a pin a repository writes (pip
already does), and the runtime change check (C') also fires when one
changes. The moving part is D'.

**D'. A lock file that moves only on a passing full run.** The repository
keeps, beside `precedent.json`, a lock file (`precedent.lock.json`) with the
exact version of every package the last passing full run used. Attacked:

- *Who moves it?* The engine, never a person. When the declared Python
  changes, or at Update Vendors, the engine resolves the newest version of
  each declared package for the declared interpreter, installs those, and
  runs the full local suite. If it passes, the new versions are written to
  the lock file and committed with the change. If it fails, the lock file
  stays as it was, the run names the package whose version moved, and the
  change reports what broke rather than landing on untested versions.
- *What does an install use between moves?* The lock file: session setup
  and every full run install exactly the locked versions, so two sessions
  a week apart run the same packages. Today `install()` only asks whether a
  package imports; it would also compare the installed version against the
  lock and reinstall a mismatch.
- *A hand-written pin and the lock disagree.* The pin wins: the engine
  resolves under it, so a pinned package never moves, and the lock records
  the pinned version.
- *A repository with no lock file yet.* The first full run that passes
  writes one. Until then, installs behave as today.

This answers Morgan's question (2026-10-16: "If the update to a new python
version passes our tests, does it then automatically update all the
corresponding the pins?"): yes for the lock file, which moves on its own
when, and only when, the full suite passes; no for a hand-written pin,
which is the person's to move.

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

**C'. Every full run starts the Python the tested commit declares.** The
full local suite -- Produce's run after the merge, `--run-tests`, a Debut
-- reads `precedent.json` in the worktree it tests, installs the declared
packages into that interpreter with `precedent_python.install()`, and
starts the suite with it rather than with `sys.executable`. The run that
already happens after every Produce then tests a version change on the
version it declares, with no new step and no extra wait.

## The proposal

1. **A full run uses the tested commit's declared interpreter** (C'). One
   place: `precedent_branches._check`, which every full local run goes
   through. **A declared interpreter that is not installed is installed**
   with `uv python install`, here and at session setup, which today only
   warns and carries on with whatever `python3` it has. If that install
   fails, the run says so and records itself as not verified, naming the
   interpreter and the reason -- never a pass on the old one, and never a
   pass with a warning beside it.
2. **A parse-and-import pass** over every tracked Python file under the
   declared interpreter, run as part of (1) and also by the very deep
   check: `py_compile` each file, then import each module the repository's
   own code imports from the standard library. Cheap, and it names a
   removed module by name rather than as a traceback deep in a test.
3. **Update Vendors says when the Python moves**, as its own step, for a
   repository that relies on the default; the full run after its Produce
   then tests it on the new version, by (1).
4. **GitHub's workflows install what the repository declares**: the
   templates replace their hard-coded `pip install` lines with
   `python tools/precedent_python.py setup`, and their hard-coded
   `python-version` with the declared one, which `one-python` already
   checks. Rolled out through the templates and Update Vendors, like any
   template change.
5. **A lock file of package versions that passed** (D'). Installs use
   `precedent.lock.json`'s exact versions. It is rewritten only by a full
   run that passes after the engine re-resolved the packages -- on a
   change to the declared Python, or at Update Vendors -- and committed with
   that change. A failing run keeps the old lock and names the package that
   moved. A hand-written pin in `precedent.json` stays optional and is
   honored over the lock.
6. **One declared runtime per language.** `precedent.json` gains
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

Parts 1 to 3, 5 and 6 are engine changes in BestPractice; part 4 is a
template change. All reach consuming repositories through Update Vendors, and none
needs a repository to change anything first. The first Update Vendors that
carries part 3 is itself the first runtime move it reports, if the default
has moved by then.

## Build order

1. Part 2 (parse-and-import), alone: smallest, useful by itself.
2. Part 1 (the declared interpreter for a full run), with harness cases
   for: a commit declaring another version running the suite under it; its
   packages installed into that interpreter first; a missing interpreter
   installed by uv and then used; a missing interpreter uv cannot install
   recorded as not verified, by name and reason; session setup installing
   a missing interpreter instead of only warning; a commit declaring the
   session's own version running exactly as today.
3. Part 5 (the lock file), with harness cases for: a passing run after a
   re-resolve writing the new versions; a failing run keeping the old lock
   and naming the package that moved; an install reinstalling a version
   that differs from the lock; a hand-written pin winning over the lock; a
   repository with no lock file behaving as today until its first pass.
4. Part 3 (Update Vendors' step), which re-resolves the lock by part 5.
5. Part 4 (templates), then part 6 (the declaration's shape and the
   generalized consistency check).

## Decisions for the person

None open.

Settled:

- Package pins stay optional, and the lock file moves the versions
  forward on a passing full run (Morgan, 2026-10-16: "Yup let's add
  optional pins to package versions").
- **A declared Python that is not installed is installed** with uv, at
  session setup and before a full run; only when that fails is the run
  recorded as **not verified**, so `main` reads as unchecked until a run
  that can prove it. "Only warn" was rejected: it is the false pass this
  plan exists to remove. On a person's own computer the install is
  allowed without asking, since uv keeps it in its own directory. (Morgan,
  2026-10-16, agreeing to the session's recommendation: "Yes, write it
  into the plan".)

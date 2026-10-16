---
slug:        one-python
title:       "One Python per repository: declared once, meant by python3 everywhere"
tier:        on-demand
severity:    default
applies_to:  ["**/*.py", "**/*.sh", "precedent.json", ".github/workflows/*.yml"]
applies_to_why: "Routed by locus: the rule bites when code starts another program (a .py or .sh file), when a repository declares its Python (precedent.json), and when a workflow picks the Python its tests run on."
occasion:    "a repository's code runs on a Python, or a script starts another Python program"
gates:       []
index_clause: "declare one Python; python3 means it everywhere; tools use sys.executable"
checked_by:  "tools/precedent_check.py"
defines:     ["declared Python"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-15"
approved_by: "Alex, 2026-10-15: \"Can we consolidate everything to always use the same version of python? This should be a bestpractice too.\" and \"go\""
strength:    decided
---
## Rule
**A repository runs on one Python, declared once in `precedent.json`, and
every place that starts Python gets that one.**

1. **Declare it:** `"python": {"version": "3.12", "packages": [...]}`. The
   version defaults to the one GitHub's tests run on (3.12 since
   2026-10-15); the packages are the ones the repository's own code
   imports. The engine's own needs (`cmarkgfm`, `markdown`) are added
   without being listed.
2. **A session makes `python3` mean it.** Session start runs
   [`tools/precedent_python.py setup`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_python.py): the
   declared Python's own pip installs the packages, and `python3`,
   `python`, `pip3` and `pip` resolve to that Python for the rest of the
   session. So a command, a document or a person typing `python3` gets the
   right one. A person's own machine is only checked and told, never
   changed.
3. **A tool starts a tool with the Python it is running in:**
   `[sys.executable, 'tools/x.py']`, never `['python3', 'tools/x.py']`.
4. **GitHub's workflows set the same version** with `python-version`.

## Detail
**A hook does not get the declared Python.** Claude Code starts hooks with
its own PATH, which the session file never reaches, so a hook's `python3`
is the image's default. Setup runs inside the session-start hook, so it
also installs the engine's packages into the Python running it, which is
the one every later hook gets.

`python3 tools/precedent_python.py check` says whether this shell's
`python3` is the declared one and can import the declared packages. A
hosted session that reports otherwise has a session start that did not
run, or ran before this practice reached it.

The check (`precedent_check.py --only one-python`) refuses a Python file
that starts `python3` or `python` by name in a subprocess call, and a
workflow whose `python-version` differs from the declaration. It cannot
see a command run through a shell string, or the machine itself; the
session-start line is for those.

A repository that really needs two Pythons -- a tool pinned to an old
interpreter -- says so in that tool, and starts it with that interpreter's
full name; the repository's own declaration stays one version.

## Why
A container can carry several Pythons, and `python3` is whichever one the
image made the default. When packages go in through a bare `pip`, they go
into whatever Python that `pip` belongs to. Code that uses a newer
language feature then fails under one interpreter and cannot import its
packages under the other. The failure looks like a broken change, and
it isn't one.

## Story
2026-10-13, in a consuming repository: the container had Pythons 3.10 to
3.13; `python3` was 3.11, with the packages the startup script had
installed; `python3.12` had none of them. Model files written the day
before nested quotes in f-strings, which only 3.12 parses. The push check
failed twice on a one-line text fix, once for each interpreter. On
2026-10-14 the lander, which ran its checks as `python3` by name, failed a
landing the same way. Each time a session found the cause, installed
packages by hand and pointed `python3` at 3.12 for one command; the next
session would have started over.

2026-10-16, another consumer: session start said `python3` was 3.12 with
cmarkgfm and markdown, and the first prompt's gate, a minute later, said
both were missing. The gate runs as a hook, and Claude Code gives a hook
its own PATH, where `python3` was the image's 3.13; the session file had
changed PATH for the session's commands only. Setup now installs the
engine's packages into the Python running it too, which is the hooks'
Python, since the session-start hook is what runs it.

## Install
Declare the Python in `precedent.json` -- `"python": {"version": "3.12",
"packages": [...]}`, listing what the repository's own code imports -- and
take Update Vendors: it brings [`tools/precedent_python.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_python.py), the lander that
runs on it, and the session-start hook that calls it. A repository whose
`tools/bootstrap.sh` it has edited takes the package block from Precedent's
`templates/bootstrap.sh` by hand, since Update Vendors never rewrites that
file.

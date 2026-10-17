<!-- Template: instantiated by `tools/precedent_bootstrap_source.py --level shared`
     (Precedent, https://github.com/alex137/BestPractice). Placeholders
     ({{NAME}}, {{APPROVER_NAME}}, {{APPROVER_GITHUB}}) are filled in at
     bootstrap time; edit this file freely afterward, it is yours. -->

# {{NAME}} — a shared practice set

This is **{{NAME}}** — a set for one kind of work or one team, holding the
conventions its members have agreed on. Its `precedent-source.json` says
what it is, including whether the repository is public or private; the
repository holding it may be called anything.

## What's here

| File | What it's for |
|---|---|
| `approvers.json` | The list of people who can say yes to a change here. Whoever creates the set is its first approver (seeded below) — no ceremony, and there is always at least one. Run `python3 tools/build_codeowners.py` after editing it: that writes `CODEOWNERS`, which is what actually makes GitHub require an approver's review. Never hand-edit `CODEOWNERS`; it is regenerated wholesale. |
| [`practices/example-starter-shared.md`](practices/example-starter-shared.md) | One real, minimal practice file, so there's something working to copy and edit. Delete it once the team has written its own. |
| [`leak-blocklist.txt`](leak-blocklist.txt) | The private-term blocklist for Precedent's leak gate — client names, code words, anything that must never reach a public repo. **Only in a private set:** a public set's blocklist is published with it, so it never holds a private term, and those go in a private set's list instead. Otherwise fill it in; see the file's own header for the format and the two environment/git settings that switch it on. |
| `tools/` | The vendored engine (`build_views.py`, `build_codeowners.py`, `precedent_gate.py`, `precedent_paths.py`, `precedent_show.py`, `split_practices.py`, `routing_scope.json`, `precedent_vendor_engine.py`) — never hand-edit these; refresh them with `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>` (see `tools/ENGINE_MANIFEST.json` and [`spec/BOOTSTRAP_NEW_SOURCES.md`](https://github.com/alex137/BestPractice/blob/staging/spec/BOOTSTRAP_NEW_SOURCES.md#the-vendored-engine)'s "The vendored engine"). The engine files are named rather than linked because they arrive when the set is bootstrapped; nothing under `tools/` exists in this skeleton yet. |
| `AGENTS.md`, `MAP.md`, `GLOSSARY.md` | Written by bootstrap: the instructions every session here reads, with a generated loader block, and the two views generated from `practices/`. Regenerate all three with the full `python3 tools/build_views.py` after any practice change. A practice set runs no CI workflow ([`source-sets-run-no-ci`](https://github.com/alex137/BestPractice/blob/staging/practices/source-sets-run-no-ci.md)): the checks below run before the push, or not at all. |

## Before you push

Run the checks:

```
python3 tools/precedent_check.py --full-sweep
```

**Run it with `--full-sweep`.** Bare, it runs only the checks your change
routes to plus a rotating slice, and nothing else runs it here: a practice
set has no CI to catch what the slice missed.

**`0 violated` is the thing to read.** A large `skipped` count is normal and
expected here — most of Precedent's registered checks belong to practice
levels a set like this one does not resolve, so they skip by design. What
is never fine is a violation, or an `errored`. If the check refuses because
the vendored engine is too old to check a practice set properly, run
`python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`.

## Writing practices

Each practice is one file under `practices/`, in Precedent's phase-1
format — frontmatter plus `## Rule` / `## Detail` / `## Why` / `## Story` /
`## Install`. The full spec is
[Precedent's `spec/PRACTICE_FORMAT.md`](https://github.com/alex137/BestPractice/blob/staging/spec/PRACTICE_FORMAT.md);
`practices/example-starter-shared.md` in this repo shows the shape directly.

## Approval

An assistant proposes a practice and asks an approver to look at it — a
review on this repo, so the approval *is* the record. `approvers.json`
holds the list `tools/precedent_land.py` checks a proposer's name against;
adding or removing an approver is itself a change to that file, so it
needs a current approver's own agreement, which is what stops someone
quietly adding themselves.

If the approver is also the person proposing the change — for a small
team, it usually is — there's no waiting: their "yes" in the conversation
*is* the approval, landed directly in the same sitting.

**Nobody is ever blocked waiting for a team approval to *use* a practice
right now.** Put it in your own individual set instead, where it applies
immediately with nobody's permission; offering it to the team is a
separate step, whenever it suits you.

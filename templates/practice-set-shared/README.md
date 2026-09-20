<!-- Template: instantiated by `tools/precedent_bootstrap_source.py --level shared`
     (Precedent, https://github.com/alex137/BestPractice). Placeholders
     ({{NAME}}, {{APPROVER_NAME}}, {{APPROVER_GITHUB}}) are filled in at
     bootstrap time; edit this file freely afterward, it is yours. -->

# {{NAME}} — a shared practice set

This is **{{NAME}}'s own private space** — a set for one kind of work or
one team, holding the conventions its members have agreed on. Everyone
who declares it can read it; nobody else can. Its `precedent-source.json`
says what it is; the repository holding it may be called anything.

## What's here

| File | What it's for |
|---|---|
| [`approvers.json.template`](approvers.json.template) → `approvers.json` | The list of people who can say yes to a change here. Whoever creates the set is its first approver (seeded below) — no ceremony, and there is always at least one. Run `python3 tools/build_codeowners.py` after editing it: that writes `CODEOWNERS`, which is what actually makes GitHub require an approver's review. Never hand-edit `CODEOWNERS`; it is regenerated wholesale. |
| [`practices/example-starter-shared.md`](practices/example-starter-shared.md) | One real, minimal practice file, so there's something working to copy and edit. Delete it once the team has written its own. |
| [`leak-blocklist.txt`](leak-blocklist.txt) | The private-term blocklist for Precedent's leak gate — client names, code words, anything that must never reach a public repo. Fill it in; see the file's own header for the format and the two environment/git settings that switch it on. |
| `tools/` | The vendored engine (`build_views.py`, `build_codeowners.py`, `precedent_gate.py`, `precedent_paths.py`, `precedent_show.py`, `split_practices.py`, `routing_scope.json`, `precedent_vendor_engine.py`) — never hand-edit these; refresh them with `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>` (see `tools/ENGINE_MANIFEST.json` and [`spec/BOOTSTRAP_NEW_SOURCES.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/BOOTSTRAP_NEW_SOURCES.md#the-vendored-engine)'s "The vendored engine"). The engine files are named rather than linked because they arrive when the set is bootstrapped; nothing under `tools/` exists in this skeleton yet. |
| `.github/workflows/` | The two CI gates this set gets at bootstrap. `precedent-check.yml` runs the whole check suite over your catalogue on every pull request. `views-drift.yml` fails a pull request whose `AGENTS.md` loader block, `MAP.md` or `GLOSSARY.md` has drifted from a fresh `python3 tools/build_views.py`. Refresh either from [`templates/github-actions/`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/github-actions) upstream. |

## Before you push

Run the checks:

```
python3 tools/precedent_check.py
```

**`0 violated` is the thing to read.** A large `skipped` count is normal and
expected here — most of Precedent's registered checks belong to practice
levels a set like this one does not resolve, so they skip by design. A
freshly bootstrapped set reports **7 passed, 42 skipped, 0 violated**, and
once it has an `AGENTS.md` and generated views, **8 passed, 41 skipped** —
both healthy results, not broken installs. What is never fine is a
violation, or an `errored`.

`.github/workflows/precedent-check.yml` runs exactly this on every pull
request, so you can also just open one and read the result there. It refuses
rather than passing quietly if the vendored engine is too old to check a
practice set properly — if you see that, run
`python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`.

**One thing the checks cannot do yet in a brand-new set**: until you
instantiate an `AGENTS.md` with a loader block (from
[`templates/AGENTS.md.loader.template`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/AGENTS.md.loader.template)
upstream) and run `python3 tools/build_views.py`, this set generates no views
at all, and the drift gate reports `NOT CHECKED` in those words rather than a
misleading green.

## Writing practices

Each practice is one file under `practices/`, in Precedent's phase-1
format — frontmatter plus `## Rule` / `## Detail` / `## Why` / `## Story` /
`## Install`. The full spec is
[Precedent's `spec/PRACTICE_FORMAT.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/PRACTICE_FORMAT.md);
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

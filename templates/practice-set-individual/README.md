<!-- Template: instantiated by `tools/precedent_bootstrap_source.py --level individual`
     (Precedent, https://github.com/alex137/BestPractice). Placeholders
     ({{NAME}}) are filled in at bootstrap time; edit this file freely
     afterward, it is yours. -->

# {{NAME}} — a personal practice set

This is **your own private space**, not a folder inside a shared project.
It holds facts and preferences that are about *you*, not about any one
team or project: how your name is spelled, which time zone your dates are
in, that you like the tone kept casual — things you would otherwise have
to keep repeating to every assistant, in every project, forever.

You are the only one who can read this repository. A shared project's own
config can never name it — the tools refuse that by design, because naming
your personal set in a shared file would leak its existence and location
to everyone else who can read that project.

## What's here

| File | What it's for |
|---|---|
| [`config.json.sample`](config.json.sample) | Copy this to `~/.config/precedent/config.json` (or wherever `$PRECEDENT_USER_CONFIG` points) so your tools know where to find this repo. |
| [`practices/example-starter-individual.md`](practices/example-starter-individual.md) | One real, minimal practice file, so you have something working to copy and edit. Delete it once you've written your own. |
| [`leak-blocklist.txt`](leak-blocklist.txt) | The private-term blocklist for Precedent's leak gate — client names, code words, anything that must never reach a public repo. Fill it in; see the file's own header for the format and the two environment/git settings that switch it on. |
| `tools/` | The vendored engine (`build_views.py`, `precedent_gate.py`, `precedent_paths.py`, `precedent_show.py`, `split_practices.py`, `routing_scope.json`, `precedent_vendor_engine.py`) — never hand-edit these; refresh them with `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>` (see `tools/ENGINE_MANIFEST.json` and [`spec/BOOTSTRAP_NEW_SOURCES.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/BOOTSTRAP_NEW_SOURCES.md#the-vendored-engine)'s "The vendored engine"). The engine files are named rather than linked because they arrive when the set is bootstrapped; nothing under `tools/` exists in this skeleton yet. |
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

## Writing your own practices

Each practice is one file under `practices/`, in Precedent's phase-1
format — frontmatter plus `## Rule` / `## Detail` / `## Why` / `## Story` /
`## Install`. The full spec is
[Precedent's `spec/PRACTICE_FORMAT.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/PRACTICE_FORMAT.md);
`practices/example-starter-individual.md` in this repo shows the shape directly, which
is usually enough to start from without reading the spec first.

You write a personal practice once here, and it follows you into every
project that resolves against this set — never copied, never re-approved,
never remembered in three places.

## Approval

None needed. This is your set: "yes, do it" in whatever session proposed
the practice is the whole approval, recorded as `approved_by` with a date.
There is no `approvers.json` here — that mechanism exists for team sets,
where more than one person's agreement matters.

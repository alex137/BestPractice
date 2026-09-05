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
| [`practices/example-starter.md`](practices/example-starter.md) | One real, minimal practice file, so you have something working to copy and edit. Delete it once you've written your own. |
| [`leak-blocklist.txt`](leak-blocklist.txt) | The private-term blocklist for Precedent's leak gate — client names, code words, anything that must never reach a public repo. Fill it in; see the file's own header for the format and the two environment/git settings that switch it on. |
| [`tools/`](tools/) | The vendored engine ([`build_views.py`](tools/build_views.py), [`precedent_gate.py`](tools/precedent_gate.py), [`precedent_paths.py`](tools/precedent_paths.py), [`precedent_show.py`](tools/precedent_show.py), [`split_practices.py`](tools/split_practices.py), `routing_scope.json`, [`precedent_vendor_engine.py`](tools/precedent_vendor_engine.py)) — never hand-edit these; refresh them with `python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>` (see `tools/ENGINE_MANIFEST.json` and [`spec/BOOTSTRAP_NEW_SOURCES.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/BOOTSTRAP_NEW_SOURCES.md#the-vendored-engine)'s "The vendored engine"). |

## Writing your own practices

Each practice is one file under `practices/`, in Precedent's phase-1
format — frontmatter plus `## Rule` / `## Detail` / `## Why` / `## Story` /
`## Install`. The full spec is
[Precedent's `spec/PRACTICE_FORMAT.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/PRACTICE_FORMAT.md);
`practices/example-starter.md` in this repo shows the shape directly, which
is usually enough to start from without reading the spec first.

You write a personal practice once here, and it follows you into every
project that resolves against this set — never copied, never re-approved,
never remembered in three places.

## Approval

None needed. This is your set: "yes, do it" in whatever session proposed
the practice is the whole approval, recorded as `approved_by` with a date.
There is no `approvers.json` here — that mechanism exists for team sets,
where more than one person's agreement matters.

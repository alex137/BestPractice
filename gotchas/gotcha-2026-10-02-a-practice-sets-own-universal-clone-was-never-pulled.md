---
slug:            gotcha-2026-10-02-a-practice-sets-own-universal-clone-was-never-pulled
status:          live
noted:           2026-10-02
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

The reply gate says an individual or shared set's always-loaded file is over
its size target, or a set seems to follow rules that BestPractice changed
days ago, while every repository the session works in reports itself
current. Rebuilding the set's `.precedent/SESSION_PRACTICES.md` by hand
gives a different number.

## Story

On 2026-10-02 the reply gate reported the individual set's session file at
about 4,900 tokens, against a 4,000 target, a day after a large reduction
had been promoted to `main`. The person asked whether the session was
working from an old version.

It was, in one place. The individual set lives at `$HOME/precedent-individual`
and declares its universal source as `../BestPractice`, which resolved to
`$HOME/BestPractice`: a clone of its own, separate from the session's
working copy under the project directory. Its reflog had one entry, the
clone at the previous day's session start. It was 131 commits behind
`origin/main`. Session start ran `precedent_source_bootstrap.py
--sources-from .`, which syncs only the sources the project itself declares,
so nothing ever pulled it. The set's shared sets escaped by accident: they
were symlinks to the copies the project does sync.

Fast-forwarding that clone and rebuilding the file brought it to about
4,000 tokens. Later the same day a resume pulled the shared sets, and the
file did not follow: the gate read 4,013 tokens where a rebuild gave about
3,719, because the render self-heal judged freshness by age alone.

Fixing it turned up a third fault. The existing-clone sync passed no branch,
so it fell back to the clone's own declared `base_branch`. For a universal
clone that is BestPractice's working branch, not the `main` its manifest
pins. The first run that re-synced the clone moved it onto `staging`.

## Fix

`precedent_source_bootstrap.py --sources-from` now also syncs the sources
each attached practice set declares (`sources_from_attached_sets`).
- It pulls only clones the tool itself made, and skips the session's own
  project checkout.
- It pins an existing universal clone to its manifest branch.
- It then re-renders each set's session file.

`precedent_resolve._self_heal_stale_render` treats a render as stale when
any checkout it was built from moved after it was written. The session
check's "each practice source clone is current" row now names an attached
set's universal clone too.

By hand, before that lands: `git -C $HOME/BestPractice fetch origin main &&
git -C $HOME/BestPractice merge --ff-only origin/main`, then
`python3 tools/precedent_session_practices.py --repo .` from the set.

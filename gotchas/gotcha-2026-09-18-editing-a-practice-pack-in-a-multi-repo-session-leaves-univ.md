---
slug:            gotcha-2026-09-18-editing-a-practice-pack-in-a-multi-repo-session-leaves-univ
status:          retired
noted:           2026-09-18
severity:        null
retired:         "2026-09-18"
retires_when:    null
---
## Symptom

A session editing `precedent-individual` or a `precedent-team-*` pack sees
none of BestPractice's own rules — `.precedent/SESSION_PRACTICES.md` is
stale, sometimes by a full day, even though the pack's own `precedent.json`
already declares the universal source and `add_repo` for BestPractice
reports success.

## Story

Reported 2026-09-18, working a session that held all four `themorgan/*`
packs and `alex137/bestpractice` side by side under `/home/user` — the exact
sibling layout a team source needs to resolve at all. The person's own
memory was that `add_repo`, called every time a pack is opened, was supposed
to fix this and had not, "I think because of cross-repo issues."

**Checked, not assumed.** `add_repo` was a red herring: every pack's own
`precedent.json` already names `../BestPractice` as its universal source (a
relative sibling, not a fetch `add_repo` performs), and that sibling was
already on disk — reachable with no `add_repo` call at all, since
BestPractice is public. The actual mechanism is a `SessionStart` hook
(`bootstrap/precedent-universal-catalogue.sh` in `precedent-individual`, the
same file under `.claude/hooks/` in each team pack) that renders every
resolved source into the untracked `.precedent/SESSION_PRACTICES.md`. That
hook simply had not run. `stat` on all four packs' copies of that file
showed the identical timestamp — the moment the repos were first cloned —
one full day before this session, and one full day behind BestPractice's own
latest merged pull request. `CLAUDE_PROJECT_DIR` was unset in the tool
shell, consistent with this repo's own gotcha "the session's PRIMARY repo
does not run its SessionStart hooks either" (2026-09-13): this session was
rooted at `/home/user`, the parent of all five repos, so none of them was
ever the harness's primary project directory and none of their hooks ran,
for any repo, for the whole session — `add_repo` mid-session could not have
changed that outcome either way, because the gap has nothing to do with
which repos are attached and everything to do with which one, if any, is
primary. [`practices/session-bootstrap.md`](../practices/session-bootstrap.md)'s 2026-09-18 addition documents
the same root cause under a second name ("a session scoped to more than one
repo from the start... never gets this automatically for ANY of them") —
its own remedy is `bash tools/bootstrap.sh` by hand, which does not reach
this: that script sets commit identity and installs pip dependencies, never
`.precedent/SESSION_PRACTICES.md`.

**Verified live**, from inside `precedent-individual`, with no `add_repo`
call: `python3 tools/precedent_source_bootstrap.py --sources-from .` (silent
— the sibling clone was already current) followed by `python3
tools/precedent_session_practices.py --repo .` rewrote
`.precedent/SESSION_PRACTICES.md` in place, dated seconds later, carrying
122 current practices against the stale file's 11. `git status --short`
came back clean in all five repos afterward — both commands only ever
write that one untracked, gitignored file.

## Fix

**Retired 2026-09-18.** `tools/precedent_resolve.py`'s `load_config()` now
self-heals a stale or absent render on its own — `_self_heal_stale_render()`,
added in commit `ef5838b1` (PR #452), built from the shape this entry's own
brief, [`spec/SESSION_PRACTICES_RENDER_SELF_HEAL.md`](../spec/SESSION_PRACTICES_RENDER_SELF_HEAL.md),
recommended. The manual commands below are no longer necessary once a repo
has taken that engine refresh; kept here, unedited, for a repo that hasn't
yet and for the story of how the gap was found. Whether a given pack has the
fix: `grep _self_heal_stale_render tools/precedent_resolve.py` from its root.

**The manual fix, still correct on an engine that predates the self-heal.
From inside the specific pack you are editing**, whenever the session
might be scoped to more than one repo (there is no reliable way to tell from
inside a running session whether its own `SessionStart` hooks actually
fired — `CLAUDE_PROJECT_DIR` being unset proves nothing either way, per the
gotcha below):

```
cd <path to the pack>
python3 tools/precedent_source_bootstrap.py --sources-from .
python3 tools/precedent_session_practices.py --repo .
```

Both commands are read-only against every repo but the pack itself; the
first re-syncs the sibling universal clone if it is missing or behind, the
second renders the merged catalogue into `.precedent/SESSION_PRACTICES.md`.
Re-run them at the start of any session that will edit a pack, as routine
practice rather than only once the stale symptom is confirmed — this is
what the pack's own `SessionStart` hook would have run, had it fired.

`add_repo` is not part of the fix and was never the actual gap here: the
universal source resolves as an already-cloned sibling, not a fetch that
tool performs, and even where `add_repo` genuinely is needed (a private team
or individual source under a different session shape) it only grants read
access — it does not make a repo primary and does not make its hooks run.

The more durable fix is rooting the editing session at the pack itself
rather than at a parent directory holding several repos — see
[session-text](../practices/session-text.md) for waking a session already
scoped that way instead of opening a general multi-repo one.

**This is the pack-editing case of two already-documented gaps, neither of
which names this particular fix**:
[`gotcha-2026-09-13-the-session-s-primary-repo-does-not-run-its-sessionstart-hoo.md`](gotcha-2026-09-13-the-session-s-primary-repo-does-not-run-its-sessionstart-hoo.md)
(the single-repo, rooted-one-directory-above case) and
[`practices/session-bootstrap.md`](../practices/session-bootstrap.md)'s
2026-09-18 addition (a session scoped to several repos from the start).
[`todo/todo-2026-09-13-universal-prose-does-not-reach-a-source-set.md`](../todo/todo-2026-09-13-universal-prose-does-not-reach-a-source-set.md)
tracks the underlying rollout as still open (`disposition: wait`); this
entry is the manual workaround until that lands, not a substitute for it.

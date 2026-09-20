---
slug:            gotcha-2026-09-06-the-three-private-practice-sets-cannot-be-attached-from-a-se
status:          retired
noted:           2026-09-06
severity:        null
retired:         "2026-09-06"
retires_when:    null
---
## Symptom

The three private practice sets cannot be attached from a session

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The three private practice sets cannot be attached from a session
  rooted in this repo, and it is a session-shape rule, not a permissions
  problem — so do not go hunting for the permission.** As of 2026-09-06,
  asked to attach `themorgan/precedent-team-repo-maintenance`,
  `themorgan/precedent-individual` and `themorgan/precedent-team-tms` while
  working in `alex137/BestPractice`, `add_repo` refuses outright:
  *"cross-tier adds are not supported in v1: requested
  themorgan/precedent-team-repo-maintenance but session already has repos from
  owner(s) [alex137]"*. Everything about the surrounding evidence argues the
  other way and is misleading: `list_repos` returns all three, private, with
  `can_push: true` for this account, so access genuinely exists — it is the
  *session's* composition that is refused, not the account's rights. The
  obvious fallback fails too, differently enough to look like a second
  problem: a plain `git ls-remote https://github.com/themorgan/...` answers
  *"could not read Username for 'https://github.com': terminal prompts
  disabled"*, because this session's git credentials cover `alex137/*` only.
  Nothing done from inside such a session closes this. The remedy is a
  session whose **initial source** is the private repo
  ([TODO.md](../TODO.md)'s `attach-private-sources` item, which also lists what
  to run once there); BestPractice is public, so that session clones it
  directly with no second `add_repo`. The failure this entry prevents is
  spending the attempt at all: the fact was already recorded in
  [TODO.md](../TODO.md), [spec/PHASE6_BRIEF.md](../spec/PHASE6_BRIEF.md) and
  [decisions/2026-09-01-relax-private-repo-isolation.md](../decisions/2026-09-01-relax-private-repo-isolation.md),
  and a session on 2026-09-06 rediscovered it by trying both calls anyway,
  because this section — the one place written to stop rediscovery — did not
  carry it.
  **NO LONGER TRUE as written, 2026-09-07.** A session that day held
  `alex137/bestpractice` and five `themorgan/*` repositories at once —
  including all three private sets, worked in and pushed to — and `add_repo`
  accepted a sixth (a private consumer repo under the same owner)
  mid-session. Mixed owners
  in one session is precisely what this entry says is refused.
  **The open half is now measured, 2026-09-07: a fresh session rooted here
  still refuses on its FIRST cross-owner add.** `add_repo` for
  `themorgan/precedent-individual`, called as the session's first tool call
  exactly as the banner at the top of this file instructs, answered with the
  same v1 message word for word.
  **The symmetric half, measured 2026-09-07: rooting in the private repo
  does not buy the add either.** A session rooted in
  `themorgan/precedent-individual` asked for `alex137/bestpractice` and was
  refused in the same words with the owners swapped — *"cross-tier adds are
  not supported in v1: requested alex137/bestpractice but session already
  has repos from owner(s) [themorgan]"*. So the refusal runs in BOTH
  directions. The clause this replaces — that a session rooted in a
  `themorgan/*` repo "keeps adding freely" because BestPractice is a public
  add — was an INFERENCE drawn from the mixed-set session above, never a
  measurement, and it is now falsified: public-vs-private is not the axis,
  and the first cross-owner add loses whichever owner you start from. **So
  how that mixed-set session reached six repositories across two owners is
  now unexplained** — the only explanation on offer has just been ruled out.
  Do not build on it, and do not repeat the attempt expecting the earlier
  result. The remedy stands unchanged and is the only one, but state it
  accurately: root the session in the repo you must PUSH to, and expect the
  other owner's repositories to be unattachable from it for the whole
  session. That is not a workaround to route around — it is why work
  spanning both owners is split across two sessions, each rooted where it
  writes.
  What it costs when you skip it is not abstract. That 2026-09-07 session
  ran with `individual` and `team` both unresolved, which means the
  `go-merge` keyword's own definition was unreadable while the user was
  using it — the one thing `.precedent/SESSION_PRACTICES.md` says out loud
  and nothing else in the tree does.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)

# Git, minimally, for this way of working

You don't need to know git deeply to use [BestPractice](README.md); you
need eight ideas:

- **The default branch (`main`) is the shared truth.** It is what every new
  session reads for orientation. Nothing is "real" until it lands there.
- **Each thread works on its own branch** — a private copy of the repo where
  a session (or a person) can make any number of commits without disturbing
  anyone else. Two threads on two branches never conflict *while working*;
  reconciliation happens once, at merge time, under the runbook's rules.
- **Branch work is invisible to everyone else until it lands on `main` —
  and they catch up.** Publishing takes two steps: your branch must be
  *merged* into `main`, and then each collaborator (human or agent session)
  must *pull* the updated `main` into their own copy. Until both happen,
  don't expect others to see your work — a pushed branch technically exists
  on the server, but nobody working from `main` will encounter it. The same
  holds in reverse: someone else's unmerged branch is invisible to you,
  which is why "it's not in the repo" really means "it's not in `main` yet."
- **A pull request (PR) is a reviewable bundle of changes** — "here is
  everything branch X wants to add to main, as a diff." If several people
  (or several agent threads) touch the same repo, PRs are where a second
  pair of eyes goes: you can ask a colleague, or another agent session, to
  review a branch before it merges. For a solo repo, PRs are optional —
  merging directly is fine; the audits are the real gate either way.
- **Permissions decide who may merge.** On a repo someone else owns, you may
  find you can push branches and open PRs but not merge them — the owner
  reviews and merges on their schedule; that's normal, not an error. The
  same lever works for you in the other direction: when your repo gains a
  second contributor, you can require that all changes to `main` go through
  a PR that only you approve and merge (on GitHub: repo Settings →
  Branches → a branch protection/ruleset on `main` requiring pull requests
  before merging). Contributors then work freely on branches while every
  change to the shared truth waits for your review — a good default the
  moment a repo stops being solo.
- **History is permanent.** Every commit is recoverable, so bold edits are
  safe: anything can be diffed against any earlier state and reverted. This
  is what makes "the repo is the memory" trustworthy — memory that can't be
  silently lost or rewritten.
- **One agent can work on branches of several repositories at once.**
  Nothing about git or agents limits a session to a single repo: give it
  access to two (or more) repositories — on GitHub, each repo the agent's
  app installation is permitted to touch; in the Claude Code app
  specifically, you pick which repos the session can access when you
  create it — and it can hold a branch open in each and commit to all of
  them in one conversation. This is not a BestPractice feature, just a
  practical fact coding tools take for granted that matters here: it is
  how **cross-cutting work** gets done — moving content from one repo to
  another, reorganizing which repo owns what, keeping a shared layer in
  sync across repos. This repo's own check-in loop is the worked example:
  a dual-repo session abstracts a practice in the private dependent repo
  and lands it here, in a single thread.
- **An agent session's repo access is fixed when the session starts.** On
  hosted agent platforms, a session can write only to the repo(s) you
  selected when creating it. A session opened on one repo can usually still
  *read* a public repo (clone it, diff against it) but cannot push branches
  or open PRs there — writes fail even though reads work, which is
  confusing the first time you hit it. So decide up front: if a session's
  plan includes pushing to a second repo (the check-in step in
  [How it's used](README.md#how-its-used-short-version), for example),
  **select both repos when you create the session** — you generally can't
  add write access mid-session.

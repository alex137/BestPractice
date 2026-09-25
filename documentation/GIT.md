# Git, Minimally, for This Way of Working

## Why GitHub at All?

A normal chat thread is useful but temporary. Important context may be
buried in an old conversation, known to only one person, or missing from
another AI Assistant's memory. Keeping the project in a GitHub repository
gives the team a shared, inspectable memory instead:

- Important decisions are written down.
- Everyone works from the same current information.
- Earlier versions can be reviewed or restored.
- Several people can work without silently overwriting one another.
- A new person or AI session can understand the project by reading its
  map and asking questions.
- Changes record what happened and why.
- Rules that matter are enforced by automatic checks, not by reminding
  people.

The repository is the memory. The chat is the way you work with it.

GitHub is the worked example throughout these documents, and Precedent
currently leans on GitHub features (pull requests, Actions checks)
deliberately. The layer itself is plain git, markdown, and Python, so
equivalents on other hosts such as Gitea can be added later — see
[TODO.md](../TODO.md).

## The Eight Ideas

You don't need to know git deeply to use [Precedent](../README.md); you
need eight ideas. (Throughout, a "session" is one AI conversation. Every
git and GitHub word used below is defined in
[The Words, Defined](#the-words-defined), further down.)

- **The default branch (`main`) is the shared truth.** It is what every new
  session reads for orientation. Nothing is "real" until it lands there.
- **Each thread works on its own branch** — a private copy of the repo where
  a session (or a person) can make any number of commits without disturbing
  anyone else. Two threads on two branches never conflict *while working*;
  reconciliation happens once, at merge time, under fixed rules the
  project's instruction files set out.
- **Branch work is invisible to everyone else until it lands on `main` —
  and they catch up.** Publishing takes two steps: your branch must be
  *merged* into `main`, and then each collaborator (human or agent session)
  must *pull* the updated `main` into their own copy. Until both happen,
  don't expect others to see your work — a pushed branch technically exists
  on the server, but nobody working from `main` will encounter it. The same
  holds in reverse: someone else's unmerged branch is invisible to you,
  which is why "it's not in the repo" really means "it's not in `main` yet."
- **A pull request (PR) is a reviewable bundle of changes** — "here is
  everything branch X wants to add to main," shown as a side-by-side
  comparison of before and after. If several people (or several agent
  threads) touch the same repo, PRs are where a second pair of eyes goes:
  you can ask a colleague, or another agent session, to review a branch
  before it merges. For a solo repo, PRs are optional — merging directly
  is fine; the project's automatic checks are the real safeguard either
  way.
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
  them in one conversation. This is not a Precedent feature, just a
  practical fact coding tools take for granted that matters here: it is
  how **cross-cutting work** gets done — moving content from one repo to
  another, reorganizing which repo owns what, keeping a shared layer in
  sync across repos. This repo's own improvement loop is the worked
  example: one session generalizes a lesson learned in a private project
  repo and lands it here, in a single thread.
- **An agent session's repo access is fixed when the session starts.** On
  hosted agent platforms, a session can write only to the repo(s) you
  selected when creating it. A session opened on one repo can usually still
  *read* a public repo (copy it, compare against it) but cannot push
  branches or open PRs there — writes fail even though reads work, which
  is confusing the first time you hit it. So decide up front: if a session's
  plan includes pushing to a second repo (the check-in step in
  [INSTALL.md](../INSTALL.md) §4, for example),
  **select both repos when you create the session** — you generally can't
  add write access mid-session.

## The Words, Defined

The eight ideas above are the concepts. This is the vocabulary — the words
that appear in a session's replies, in GitHub's own screens, and in error
messages, where nobody stops to explain them. **Skim it once; come back to
it when a word goes past that you nodded at.**

A separate [GLOSSARY.md](../GLOSSARY.md) covers terms this project coined. This
section covers git's and GitHub's own.

### Where the Work Lives

- **Repository ("repo")** — one project's folder, with its full history. It
  exists in two kinds of place at once: on GitHub's servers, and as a copy on
  each machine or session working on it.
- **Clone** — a full copy of a repository, downloaded to a machine. Not a
  snapshot: it carries the history and stays connected to where it came from.
- **Remote** — a copy of the repository that lives somewhere else, usually on
  GitHub, that your clone knows how to talk to. A clone can know several.
- **`origin`** — **the name of the remote you cloned from.** It is a
  nickname, not a place, and it means "the copy on GitHub this one came
  from". Nothing about it says which *branch*: `origin/main` and
  `origin/staging` are both on `origin`.
- **Fork** — your own copy of somebody else's repository on GitHub, which you
  can push to. Used when you cannot write to theirs.

### Names That Point at a Version

- **Commit** — one saved change, with a note saying what and why. The unit
  everything else is built from.
- **Hash (or SHA)** — a commit's permanent name, like `6aebfa6`. Usually
  written short. Two commits never share one.
- **Branch** — a moving name for "the latest commit on this line of work".
  Making a branch costs nothing; it is a label, not a copy.
- **`main`** — the branch a repository treats as its shared truth, by
  convention. Also called the **default branch**, because it is what GitHub
  shows first and what a fresh clone lands on. **In this repository the real
  work happens on `staging` instead**, which is why "the default
  branch" and "the branch we merge into" are not the same sentence here.
- **`HEAD`** — where your clone is standing right now: the commit you would
  build the next one on top of.
- **Tag** — a permanent name pinned to one commit, usually a release. Unlike
  a branch, it does not move.

### Moving Work Around

- **Fetch** — download what the remote has, and change nothing in your
  working files. Safe, always.
- **Pull** — fetch, then merge what arrived into the branch you are on. This
  one does change your files.
- **Push** — send your commits up to the remote. Until you push, your work
  exists on one machine only.
- **Merge** — combine another branch's work into yours, keeping both. The
  normal way work comes together.
- **Fast-forward** — the easy kind of merge: you had made no commits of your
  own, so your branch just slides up to match. Nothing to reconcile.
- **Conflict** — the same lines changed on both sides, so git stops and asks
  a person which to keep. Loud and visible; the dangerous merges are the
  quiet ones.
- **Rebase** — replay your commits on top of someone else's, rewriting them
  as it goes. Tidier history, at the cost of changing commits that already
  exist. **Never on a branch anyone else has.**
- **Force push** — overwrite what the remote has with what you have,
  discarding the difference. The one command here that destroys other
  people's work.
- **Pull request (PR)** — a proposal on GitHub: "here is everything my branch
  wants to add to that one," with the before-and-after shown side by side,
  plus somewhere to discuss it and a button to merge it.

### Words That Describe a State

- **Ahead / behind** — how many commits your branch has that the remote does
  not, and the other way round. Behind is normal and harmless; fix it by
  pulling.
- **Diverged** — **both** ahead and behind: each side has commits the other
  lacks. Needs a real merge.
- **Ancestor** — an earlier commit that a later one was built on top of. "Your branch
  is an ancestor of theirs" means you have nothing they do not.
- **Merge base** — the last commit two branches had in common, which is what
  git compares against to work out what each side changed.
- **Stale** — your clone's picture of the remote is out of date, because
  nobody has fetched recently. **Git will not tell you**; it reports
  confidently against whatever it last saw.
- **Shallow clone** — a clone that downloaded only the most recent commits to
  save time, which is what hosted sessions normally get. **It is the source
  of the most confusing error in this list**: with the shared history not
  downloaded, git cannot find the merge base and says the two branches have
  *unrelated histories*, or reports the clone's own depth as if those were
  your own unpushed commits. Neither is true. The fix is to fetch more
  history (`git fetch --depth=1000`), never to reconcile a divergence that
  is not there.
- **Tracked / untracked** — whether git is watching a file at all. An
  untracked file is invisible to every commit until someone adds it.
- **Staged** — marked as going into the next commit, but not committed yet.
- **Upstream** — two meanings, and they are unrelated. For a *branch*, the
  remote branch it is paired with. For a *project*, the original repository
  yours takes updates from — which is what this project means by it.

### The Files That Run Things

These are not project content. They are the machinery a repository carries
so that GitHub, git and your AI Assistant know what to do — and they are
the files most likely to go past unexplained, because everyone assumes you
already know what they are.

- **`.github/`** — a folder GitHub itself reads. Nothing in it is part of
  what the project is *about*; it holds the files that tell GitHub how to
  behave.
- **Workflow** — a program GitHub runs for you, on its own machines, when
  something happens in the repository. One file per workflow, under
  `.github/workflows/`. The filename is whoever wrote it's choice:
  [`deep-check.yml`](../.github/workflows/deep-check.yml) here runs the full
  gate suite, [`leak-gate.yml`](../.github/workflows/leak-gate.yml) checks
  nothing private is being published. (A third, docs.yml, ran the markdown
  linter until 2026-09-21, when a commit hook replaced it — see
  [documentation/GITHUB_ACTIONS.md](GITHUB_ACTIONS.md).)
- **GitHub Actions** — GitHub's name for the service that runs those
  workflows, and for the tab where you watch them run.
- **Continuous integration (CI)** — the general name for the idea: checks
  that run by themselves on every change, instead of someone remembering to
  run them.
- **Trigger (a workflow's `on:` block)** — the lines at the top of a
  workflow saying *when* to run it: on a push, on a pull request, on a
  schedule, and on which branches. **This is the part that goes quietly
  wrong.** A workflow pointed at the wrong branch still runs, still passes,
  and covers nothing — and a green tick on the branch nobody uses looks
  exactly like a green tick on the branch everybody does.
- **Check (or "status check")** — one workflow's verdict on one commit: the
  green tick or red cross beside it. A red one blocks nothing on its own
  unless someone has switched on branch protection.
- **Lint (a "linter")** — a program that reads your files and complains
  about small mechanical faults — a link pointing at nothing, a character
  that renders wrong — without understanding a word of what you wrote.
  [`tools/doc_lint.py`](../tools/doc_lint.py) is this project's. Until
  2026-09-14 the workflow running it watched only `main` and pull requests:
  push straight to the working branch, and the link checker didn't run.
- **Hook** — a script that runs at a fixed moment on *your* machine rather
  than GitHub's: before a commit, before a push, when a session starts. Same
  idea as a workflow, one step earlier. This repository's live in
  [.claude/hooks/](../.claude/hooks/).
- **Webhook** — GitHub's own hooks, and they point the other way: instead of
  running something, GitHub *sends a message* to an address you gave it when
  an event happens — a push, a comment, a check finishing. Nothing runs on
  GitHub and nothing runs on your machine; a third thing is being told. It is
  how a session finds out that a check went red without anybody watching the
  page. Under a repository's Settings they are listed as **Webhooks**, and
  older screens call them Hooks, which is where the collision with the entry
  above comes from.
- **`.gitignore`** — a list of files git should pretend are not there:
  build output, scratch files, anything private. They stay untracked
  forever unless someone deliberately overrides it.
- **Template files** — [`.github/pull_request_template.md`](../.github/pull_request_template.md)
  and the files under [`.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/) are text GitHub pre-fills into the box
  when you open a pull request or an issue. A prompt to fill in, never a
  rule that blocks anything.
- **`CODEOWNERS`** — a file naming who has to review changes to which
  paths. This is the one item here GitHub actually enforces, and only on
  pull requests.
- **YAML (`.yml`)** — the format all of the above configuration is written
  in. Indentation carries meaning, so a wrong space is a real error rather
  than untidiness.

## Knowing Your Work Actually Landed

A published operation reports on *itself*, not on your intention, and the
reports are easy to misread in the same direction twice. Three checks cost
seconds and catch the cases where everything looked fine:

- **Before committing, confirm which branch you are on.** A commit goes to the
  branch you are standing on, not the one you have been thinking about.
- **After publishing, compare every local branch against its remote** and
  require the difference to be empty. Publishing by *naming* a branch acts on
  that branch — if it has not changed, the operation succeeds, says so, and
  your actual work stays unpublished somewhere else.
- **Never gate on a pipeline.** `check | tail && publish` tests whether `tail`
  worked, not whether `check` passed; the check can print a failure in plain
  sight and the publish proceeds anyway. Run checks on their own and test the
  result.

The general form is practice 32: verify the state you wanted, not that the
command reported success. Worth trusting an automated nag that tells you
something is unpublished — that is exactly the check your own review cannot
perform, because your review is built from the same assumption that caused
the mistake.

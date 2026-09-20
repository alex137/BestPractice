# GitHub Settings — What Precedent Needs From the Repository, and How CODEOWNERS Fits

*The question this document answers:* **Which GitHub settings does a
Precedent project depend on, who clicks them, and what exactly does the
CODEOWNERS file do in this system?**

Every setting on this page lives on GitHub, not in the repository. That is
the whole reason the page exists: a session can read and write every file
in the project and cannot see one of these settings, so each one fails
quietly when it is missing, and the documents go on describing a behaviour
the repository no longer has. **Click-paths and GitHub behaviours below are
as of 2026-09-14, written from what this project has measured and from
memory of GitHub's own documentation, which a hosted session cannot reach.
Where a claim is unverified it says so.** GitHub moves its settings pages;
the setting's name is the stable part.

The install itself stays short about all of this on purpose — an install
that dwells on GitHub plumbing teaches its reader that the plumbing is the
point (a decision recorded 2026-09-10, `strength: decided`). This page is
where the install sends anyone who wants the detail.

## What Precedent Uses GitHub For

Three things, and each maps to a group of settings below.

1. **The repository is the project's memory.** Everything a session needs
   is a committed file, so the repository has to be reachable by every
   person and every AI Assistant session that works on it. That is
   **collaborators and tokens**.
2. **A pull request is the review.** Nothing is real until it is merged,
   and the merge is where a person's yes is taken. That is **branch
   protection**, which turns "we review before merging" from a habit into
   something GitHub refuses to skip.
3. **A line between content and machinery.** A contributor writes the
   documents; the maintainer reviews changes to the settings, the checks
   and the rules; a practice is landed only by a listed approver. That is
   **CODEOWNERS plus branch protection**, and it is the part of this page
   most specific to Precedent.

## Collaborators and Roles

GitHub gives a collaborator on a personal repository one of five roles:
**Read**, **Triage**, **Write**, **Maintain**, **Admin**. Precedent uses two
of them, and one list that is not a GitHub role at all.

| Who | GitHub role | Why that one |
|---|---|---|
| A contributor — anyone who writes the project's content | **Write** | Write is what lets them push a branch, open a pull request, and merge their own documents. Read and Triage deny every write, which is the model this project tried first and abandoned on 2026-09-11: a contributor who cannot put a sentence into a document cannot do the one thing the project exists for. |
| The maintainer — whoever owns the machinery | **Admin** (or the owner) | Only Admin can turn branch protection on, and protection is what makes the maintainer's review required rather than requested. Maintain cannot set it. |
| An approver — who may land a practice | *not a role* | Approvers are a list in a practice set's `approvers.json`, read by the tools and turned into that set's CODEOWNERS. GitHub never knows who is an approver except through that generated file. |

**Nothing records whether a person is technical.** The line runs through
what a change touches, never through who made it
([technical-describes-people](../practices/technical-describes-people.md)).
A developer who is not a listed approver suggests a practice exactly the
way a writer does.

**Invite people at Settings → Collaborators and teams → Add people**, and
give the role in the same step. No tool in this repository's GitHub toolset
can send an invitation, so this stays a person's click. Give Write and turn
on branch protection **in the same sitting**: Write on an unprotected
repository is unrestricted write, and the boundary below does nothing until
protection exists.

**Whose identity a session acts as** matters as much as the role. The
boundary binds a contributor only if their AI Assistant authenticates to
GitHub as *them*, not through a shared organisation-wide connection. Test
it once per project: have them try something their role forbids and watch
GitHub refuse it under their name.

## The Owner-Only Settings Every Install Mentions

Four settings only the repository's owner can click, offered at the end of
every install as suggestions rather than a gate (click-paths as of
2026-09-10):

1. **Make the repository private** unless it is meant to be public. Decided
   at creation time; awkward to change afterwards. A private repository
   also changes what branch protection costs — see "Plan limits" below.
2. **A developer token as a repository secret** — **Settings → Secrets and
   variables → Actions → New repository secret**, named
   `PRECEDENT_REPO_TOKEN` unless something already expects another name. It
   is what lets a workflow push a branch or open a pull request on the
   project's behalf. It is not the read-only, environment-level
   `PRECEDENT_GIT_TOKEN` from [PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md),
   and it is not needed by any of the shipped checks, which only read.
3. **The default branch is `main`** — **Settings → General → Default
   branch**. The shipped workflows name it as a literal string; a
   differently-named default branch runs no check on merges.
4. **Allow GitHub Actions to create and approve pull requests** —
   **Settings → Actions → General → Workflow permissions**. Needed only by
   automation that opens pull requests; harmless otherwise.

[templates/GETTING_STARTED.md](../templates/GETTING_STARTED.md)'s
administrator section repeats these so they survive the install
conversation ([github-setup-disclosed](../practices/github-setup-disclosed.md)).

## Branch Protection

Branch protection is the setting that makes a pull request mandatory and
the review real. GitHub offers it in two shapes, **branch protection rules**
(the older page, **Settings → Branches**) and **rulesets** (**Settings →
Rules → Rulesets**). Either works for everything on this page; pick one and
do not mix them on the same branch, because two rules on one branch are two
things to read and one of them is always the one nobody remembers. (This
needs a paid GitHub plan on a private personal-account repository — see
"Plan limits" below. If the page offers no rule to add, that is almost
certainly why.)

For the base branch (`main`, or whatever `precedent.json`'s `base_branch`
names), the settings Precedent's contributor boundary needs are exactly
these four, and the values matter:

| Setting | Value | Why |
|---|---|---|
| Require a pull request before merging | **on** | Nobody pushes straight to the base branch, contributor or maintainer. Every change is reviewable before it lands. |
| Required approving reviews | **0** | A documents-only pull request must be mergeable by its own author, with no reviewer at all. Any number above zero makes the maintainer a bottleneck on every document, which is the exact failure the boundary exists to avoid. |
| Require review from Code Owners | **on** | This is the line. A pull request touching a path CODEOWNERS names waits for that owner's approval; one touching no owned path is not affected by this setting at all. Without it, CODEOWNERS is documentation. |
| Do not allow bypassing the above settings | **on** | Otherwise an administrator (the maintainer) can merge machinery changes unreviewed, which is a smaller gap but the one a mistake walks through. |

**Whether "required approvals 0 plus code-owner review" behaves exactly this
way is assumption 1 in
[spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md)'s "Verify these
first" and is unverified as of 2026-09-14.** It is the session's reading of
how the two settings compose, not something read from GitHub's
documentation. A throwaway repository exists to settle it with one pull
request of each shape.

**Plan limits.** As this project understands it (unverified, 2026-09-14),
branch protection and rulesets on a **private** repository owned by a
**personal** account need a paid GitHub plan; on a public repository they
are free. A private document project on a free personal plan therefore
cannot draw the boundary at all, and `precedent_boundary_check.py` reports
that case as `FAIL: not available on this repository's plan` — the one 403
it treats as an answer rather than as "could not look".

**Required status checks** are a separate part of the same page: once a
workflow has run at least once, its job can be added to the protection
rule's required checks, and then a failing check blocks the merge for
everyone. [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)'s "Make the Check
Required" covers it.

## CODEOWNERS

### What GitHub Does With It

`CODEOWNERS` is a text file GitHub reads from one of three places, in this
order: `.github/CODEOWNERS`, the repository root, or `docs/`. Each line is
a path pattern followed by one or more owners — `@username` or
`@org/team-name`. GitHub's own rules, as far as they are documented:

- Patterns are gitignore-shaped. A leading `/` anchors the pattern at the
  repository root; a trailing `/` matches everything under a directory;
  `*` does not cross a slash and `**` does; a pattern with no slash matches
  a file of that name anywhere.
- **The last matching line wins.** Order matters, and a later line with no
  owner frees a path an earlier line owned.
- An owner must have **write access** to the repository, or the line is
  silently ignored. A `@org/team` owner needs an organisation-owned
  repository; on a personal repository, owners are individual accounts.
- On its own the file does nothing but suggest reviewers. **It becomes a
  requirement only when the base branch's protection rule has "Require
  review from Code Owners" on**, and then only pull requests touching an
  owned path wait for that owner. Everyone else's pull request is untouched.
- The file is read from the base branch of the pull request. A change to
  CODEOWNERS on a feature branch does not loosen the rule for that same
  branch's pull request.

### What Precedent Does With It

**Precedent never writes CODEOWNERS by hand. It is a generated file, and its
source is a registry** ([registry-source-of-truth](../practices/registry-source-of-truth.md)).
Two kinds of repository, one generator,
[tools/build_codeowners.py](../tools/build_codeowners.py):

| Repository | Registry | Generated file | What it says |
|---|---|---|---|
| A **practice set** (a team's or a person's rules) | `approvers.json` | `CODEOWNERS` at the root | One line, `*`, owned by every approver: the whole set is the thing being approved, so every change to it waits for an approver. That is how "only an approver lands a practice" becomes a setting rather than a sentence. |
| A **project** (a document project, or any repository drawing the contributor boundary) | `maintainers` and `owned_paths` in `precedent.json` | `.github/CODEOWNERS` | One row per owned path, all maintainers on each, with the path's reason as a comment above it. Everything not listed is content. |

The generated file carries a header naming its source, a hash of that
source's content, and the command that rebuilds it. **Edit the registry and
regenerate; never edit the file.** `python3 tools/build_codeowners.py
--check` says whether the committed file still matches its registry, and
the very deep check runs that against every repository in force on every
run.

**What a project owns, and why.** The document-project template's registry
([templates/document-project/precedent.json](../templates/document-project/precedent.json))
is the worked example: `.github/` (workflow files are executable code
holding a token, and the file that draws the boundary lives under it),
`.claude/` (session configuration and hooks), `tools/` and the vendored
catalogue (the engine and the rules), `precedent.json` (the sources in
force, and this registry), `AGENTS.md` and `CLAUDE.md` (what every session
reads first). **`MAP.md` and `GLOSSARY.md` are deliberately not owned**: a
thread that adds a document adds its row to the map, so owning the map made
every document wait for the maintainer. A wrong row in an index is a
content mistake, and content is the contributor's.

**How a pull request then flows.** A contributor's AI Assistant makes the
change on a branch, and before opening the pull request runs
`python3 tools/precedent_owned_paths.py`, which diffs the touched paths
against CODEOWNERS with GitHub's own matching rules and prints the sentence
to say — *"two of these files are part of the project's machinery, so the
maintainer has to look at them before this lands; the other three are yours
to merge. Want those to go in on their own now?"* A documents-only pull
request is then its author's to merge, with `Go merge`, and no reviewer is
involved. One touching an owned path waits for the maintainer, who reviews
it on GitHub like any pull request. The boundary is GitHub's; the tool only
makes sure nobody meets it as a merge button that will not press.

**Checking it is on.** `python3 tools/precedent_boundary_check.py` asks the
GitHub API whether the base branch is protected the way the table above
needs and whether a CODEOWNERS file is in the tree. Three answers: `PASS`;
`FAIL` naming the setting that is wrong; `UNVERIFIED` when it could not ask
— no token, a token without the right scope, no network. UNVERIFIED is
never a pass, and `--check` refuses it. Reading a branch's protection needs
a token with **administration read** on the repository: a classic token
with `repo`, or a fine-grained one with *Administration: read-only*. The
session's own GitHub access does not have it (measured 2026-09-14: a 403),
so this is normally run by the maintainer with `PRECEDENT_GITHUB_TOKEN`
set, per [PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md).

## GitHub Actions, Permissions and Secrets

Every workflow Precedent ships declares `permissions: contents: read` — the
three in this repository and the three templates under
[templates/github-actions/](../templates/github-actions/), audited
2026-09-14. Keep it that way in any workflow a project adds, and set the
repository default to read-only as well (**Settings → Actions → General →
Workflow permissions → Read repository contents and packages
permissions**).

The reason is a gap CODEOWNERS cannot close. **CODEOWNERS gates the merge
of an edited workflow, not its first run.** A Write collaborator who edits a
file under `.github/workflows/` on their own branch gets that workflow
executed on push, before any review, with whatever secrets the repository
holds — as this project understands GitHub's behaviour for same-repository
branches (unverified, 2026-09-14; the *Require approval for workflow runs*
setting covers pull requests from forks, not branches). Owning `.github/`
stops the change landing; it does not stop it running once. The mitigation
is policy: **a project's workflows carry no secret a rewritten workflow
could read**, beyond the default `GITHUB_TOKEN`, and that token is read-only.
The `PRECEDENT_REPO_TOKEN` secret from the install is the one exception,
and it is why that token is scoped to the one repository and why a project
with contributors should think twice before adding it.

## Practice-Set Repositories

A team's or a person's practice set is its own repository, and its settings
are simpler:

- **Private**, always. Its practice text is the thing a public tree must
  never receive, and the leak gate checks that direction; nothing checks
  the repository's own visibility except a person, at creation.
- **CODEOWNERS** at the root, generated from `approvers.json`, owning `*`.
  With "Require review from Code Owners" on the set's base branch, every
  change to the set waits for an approver — the platform-enforced half of
  "only an approver lands a practice". Adding an approver is itself a
  change to `approvers.json`, so it waits for a current approver too.
- **One workflow**, the views-drift gate
  ([templates/github-actions/views-drift.yml.template](../templates/github-actions/views-drift.yml.template)),
  installed by the bootstrap tool, read-only.
- **A token to reach it from a hosted session**: the read-only
  `PRECEDENT_GIT_TOKEN` plus `PRECEDENT_SOURCE_BASE_URL` on the environment,
  which is [PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md)'s subject, not
  this page's.

## In One Table

| Setting | Where | Who clicks | Without it |
|---|---|---|---|
| Collaborator role Write | Settings → Collaborators and teams | owner or Admin | The contributor cannot push, open or merge anything. |
| Require a pull request before merging | Settings → Branches, or Settings → Rules | Admin | Anyone with Write pushes straight to the base branch. |
| Required approving reviews = 0 | same | Admin | Every document waits for a reviewer. |
| Require review from Code Owners | same | Admin | CODEOWNERS is documentation; the maintainer's review is optional. |
| Do not allow bypassing | same | Admin | The maintainer can merge machinery changes unreviewed. |
| `.github/CODEOWNERS` generated from the registry | the repository | a session, `python3 tools/build_codeowners.py` | Nothing names what the maintainer must review. |
| Workflow permissions read-only | Settings → Actions → General | Admin | An edited workflow runs with write access before anyone reviews it. |
| No secret beyond `GITHUB_TOKEN` in a project with contributors | Settings → Secrets and variables | Admin | A rewritten workflow can read it on its first run. |
| Default branch `main` | Settings → General | Admin | The shipped workflows watch a branch that does not exist. |
| Private repository | at creation | owner | Private practice text or private names are public the moment they are pushed. |

## Where This Is Used

[INSTALL.md §0 step 10](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)
is the install step that draws the boundary;
[spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md) is the design
and the list of what is still unverified;
[FOR_DEVELOPERS.md](FOR_DEVELOPERS.md)'s "Who May Change What" is the short
form; [FOR_EVERYONE_ELSE.md](FOR_EVERYONE_ELSE.md)'s "What You Can't Do
(on Purpose)" is the contributor's version;
[GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) is the workflows themselves; and
[GIT.md](GIT.md) explains the words — branch, pull request, merge — for
someone meeting them for the first time.

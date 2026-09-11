---
title:         "Contributor access: who may write what, and who may land a practice"
kind:          proposal
status:        drafted
opened:        2026-09-04
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Contributors write content freely; protected paths need an owner's review through CODEOWNERS; practices are suggested by anyone and landed only by a listed approver.
---
# Contributor access: who may write what, and who may land a practice

This is a self-contained implementation plan, written so a fresh session with
no memory of the conversation that produced it can carry it out. **It has not
been run against a real person or a real repository**, and three of the
platform behaviours it rests on are unverified — see "Verify these first."

## What this replaced, and when

Until 2026-09-11 this file was `spec/NONTECHNICAL_CONTRIBUTOR_ACCESS.md`, and
it drew the line in a different place: a **non-technical contributor** was
given GitHub's **Triage** or **Read** role, and a per-person session
configuration denied `git push` and `git merge`.

**That model could not do the thing the whole use case exists for.** Triage
and Read deny every write, so the contributor could not put a sentence into a
document either — and "an alternative to Google Docs, where they write and
create hand in hand with the assistant" is the point of the exercise. The plan
and the vision contradicted each other outright.

It also had no answer to a question with no answer: **how does anything
determine that a person is non-technical?** Nothing did. There was no field,
no registry, no flag — only a human picking a role at invite time and a label
that existed in people's heads.

Morgan settled it on 2026-09-11: *"The dividing line I wanted to make is
between whether they can make practices (no, only suggest them) or other
'technical' changes (update vendored files, etc)."* — `strength: decided`; he
named the line himself. **The mechanism below is this session's proposal,
which he approved by asking for the write-up** — `strength: assented`, per
[decision-strength](../practices/decision-strength.md).

## The line, in one sentence

**A contributor writes content freely; a protected path needs an owner's
review; a practice is suggested by anyone and landed only by a listed
approver.**

Nothing in that sentence describes a person's skill level, and that is the
design, not a wording choice. The old file's own failure is the argument:
once a rule is keyed to a kind of person, something has to decide who is that
kind of person, and nothing can
([technical-describes-people](../practices/technical-describes-people.md)).
Keyed to paths and to an approver list, both questions already have
machine-readable answers.

So **this plan defines no user types**, and a repository following it stores
none. Everyone gets the same three boundaries; what differs is which paths
name them as an owner and whether `approvers.json` lists them.

## The three layers

### 1. GitHub collaborator role — **Write**

The contributor is a **Write** collaborator on the project repository. They
push branches, open pull requests and merge their own content work, through
the assistant, using [`Go merge`](../practices/go-merge.md) — they never need
to see git vocabulary to do it.

**Write alone restricts nothing**, which is why layer 2 is not optional. A
Write collaborator on an unprotected repository can rewrite anything in it.

**This layer binds only if the person authenticates to GitHub as themselves**,
not through a shared organisation-wide connection. Confirm that once, per
project, before relying on any of it — an assistant session riding a shared
credential is checked against that credential's rights, not the person's.

### 2. Branch protection plus CODEOWNERS — the actual boundary

Protect the base branch: require a pull request before merging, and require
review **from code owners**. Then a `CODEOWNERS` file names the maintainer as
the owner of every path a contributor should not change alone.

The intended behaviour is that a pull request touching only unowned paths —
the documents — is the contributor's to merge, while one touching an owned
path waits for the maintainer. **That behaviour is assumption 1 below and is
not verified.**

The paths to own, in a repository built from
[templates/document-project/](../templates/document-project/):

| Path | Why it is owned |
|---|---|
| `/.github/` | Workflow files are executable code holding a token. Anyone who can edit one can rewrite everything else here, so leaving this out defeats the whole arrangement. It also holds `CODEOWNERS` itself. |
| `/.claude/` | Session configuration and hooks — the harness runs these. |
| `/tools/` | The vendored Precedent engine. |
| `/precedent/` | The vendored universal practice catalogue. |
| `/practices/`, `/local/` | Practice text, wherever an install materialises it. |
| `/precedent.json` | Declares the sources in force, the visibility, the base branch. |
| `/AGENTS.md`, `/CLAUDE.md` | The instructions every session loads. |
| `/MAP.md`, `/GLOSSARY.md` | Generated views; a hand edit here is a generated-file edit. |

Everything not listed is content, and content is the contributor's.

**`CODEOWNERS` must own itself** (it sits under `/.github/`, which is owned),
or the boundary is one commit from being removed by whoever it binds.

### 3. Practice authority — `approvers.json`, and the machinery already exists

A practice is landed by a listed approver, and by nobody else. This half needs
no new mechanism:

- **`approvers.json`** in each practice set names them.
- **[tools/build_codeowners.py](../tools/build_codeowners.py)** generates that
  set's own `CODEOWNERS` from the list, so GitHub requires an approver's
  review on the practice text itself. One source, one generated view — never
  hand-edit the output.
- **[tools/precedent_candidate.py](../tools/precedent_candidate.py)** is how
  anyone raises a suggestion. For a contributor who is not a listed approver
  it defaults to `--as-issue true` against the relevant team set, per
  [spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md)'s rule: a quiet
  `candidates/*.md` file accomplishes nothing when nobody with landing
  authority is watching it.

**This applies to every non-approver, technical or not.** A developer who is
not listed in `approvers.json` suggests practices exactly the way a writer
does. That is the same line, drawn once.

### 4. Session configuration — user experience, not enforcement

What is left for the person's own session or environment configuration is the
part a boundary cannot do: the plain-language persona, no git or
mechanical-rule vocabulary, restate an idea before acting on it, route every
practice idea through the candidate flow above.

**`permission_mode` is still never `bypassPermissions`.** The `git push` /
`git merge` denials from the old model go away — they were standing in for a
boundary GitHub should be drawing, and they are what made the contributor
unable to write.

**None of this belongs in the repository's tracked `.claude/settings.json`.**
That file binds every session on the repository, maintainers included. The
document-project template shipped exactly that mistake and Morgan found it the
only way it could be found — by being unable to push his own work to his own
repository (2026-09-10; the story is in
[practices/technical-describes-people.md](../practices/technical-describes-people.md)).

## Verify these first — three assumptions, none confirmed

Stated as of 2026-09-11 and **read from nobody's documentation**: these are
the places this plan can fail, and each is cheap to settle before anyone
builds on it.

1. **Can "require review from Code Owners" gate owned paths while leaving a
   documents-only pull request mergeable by its author?** The whole design
   rests on this. If it does not hold, every content change needs the
   maintainer's review, and the maintainer is a bottleneck rather than a
   boundary. Settle it with one throwaway pull request of each shape.
2. **Is branch protection (or rulesets) available on the plan this private
   repository sits under?** Without it, Write is simply Write and layer 2
   does not exist.
3. **Does the person authenticate to GitHub as themselves?** Layer 1's own
   caveat. Test it, do not assume it: have them attempt something their role
   forbids and confirm GitHub rejects it under their identity.

## Instantiating this

1. Create the repository and install the loader —
   [templates/document-project/README.md](../templates/document-project/README.md)
   steps 1-4, unchanged.
2. Settle the three assumptions above.
3. Add the person as a **Write** collaborator (GitHub UI: Settings →
   Collaborators and teams → Add people). No tool in this repository's GitHub
   toolset creates a collaborator invite — this stays a human step.
4. Turn on branch protection for the base branch: require a pull request,
   require code-owner review, and do not allow bypassing for people who are
   not administrators.
5. Commit `.github/CODEOWNERS` with the maintainer named against every path in
   layer 2's table.
6. Configure the person's own session or environment with layer 4's persona.
   Nothing in it denies a git command any more.

## Verify by postcondition, not by report

Per [verify-postcondition](../practices/verify-postcondition.md) — name the
state, then test it independently of what any command printed.

- **"They can land a document change on their own."** They open and merge a
  documents-only pull request end to end, without the maintainer touching it.
- **"They cannot land a change to a protected path."** They open a pull
  request editing `precedent.json`, and GitHub — not the assistant's
  reluctance — blocks the merge until the owner reviews.
- **"A workflow file is protected."** The same test against
  `.github/workflows/`, which is the path that makes every other one
  meaningless if it is missed.
- **"A practice idea becomes a real, visible candidate."** They describe an
  observation in plain language, and an Issue appears on the team set where an
  approver will see it, with no mechanical-rule vocabulary in their
  conversation.
- **"The boundary survives them."** They cannot edit `.github/CODEOWNERS`
  without an owner's review.

## What this does not cover

- **A guard inside the session that knows who is running.** Precedent already
  resolves a person at runtime — `PRECEDENT_COMMIT_NAME`/`_EMAIL`, the ladder
  in [tools/precedent_time.py](../tools/precedent_time.py), the individual
  source — so a tracked hook could warn when somebody outside `approvers.json`
  edits a protected path, closing the "a manual step can be forgotten" gap
  that [TODO.md](../TODO.md)'s `review-skill-level-permissions` item names.
  It would be a guardrail and not a boundary: an environment variable is
  self-declared. Not built, and not decided.
- **Who may become an approver.** Unchanged: adding one is itself a change to
  the practice set, needing a current approver's agreement.
- **Non-GitHub hosts** ([TODO.md](../TODO.md) item 8). Layer 2 is GitHub's
  CODEOWNERS specifically; the idea generalises, the file does not.
- **A second team source for the same subject area**, which is a resolution
  question, not an access one.

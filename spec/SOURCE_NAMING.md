---
title:         How a practice-set source is named
kind:          reference
status:        current
opened:        2026-09-06
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       How a practice-set source is identified — a manifest it carries, a name chosen once — what refuses versus what warns, what a session must say before anyone picks a name, and why the name stopped doing the machinery's work on 2026-09-18.
---
# How a practice-set source is named

A source says what it is in a file at its root, and its name is chosen
once by its author. This document carries the reasoning: what the
convention is, why four different names that all get called "the naming
convention" are treated differently, what the name used to carry and
carries no longer, and what was decided. The rule itself is
[practices/source-naming.md](../practices/source-naming.md); the reference
a session reads while working is [spec/SOURCES.md](SOURCES.md)'s Naming
section.

## The convention

Every source carries `precedent-source.json` at its root:

```json
{
  "name": "lab-notebook",
  "level": "shared",
  "visibility": "private",
  "subject": "keeping a laboratory notebook that an audit can read",
  "code": ["tools"]
}
```

| Field | What it is |
|---|---|
| `name` | The identity. A slug — lowercase, digits, single hyphens — chosen once when the set is created. Every consumer declares it verbatim; attribution in every consumer's materialized `MANIFEST.json` keys on it. |
| `level` | `universal`, `shared`, `individual` or `repo-local`. `shared` is any set a repository declares beside the universal one and its own `local/`; it was called `team` until 2026-09-18, and a declaration that still says `team` resolves as `shared`. |
| `visibility` | `public` or `private`. The author's say, not the consumer's: the leak gate refuses a private set's manifest in a public tree whatever directory it sits in. |
| `subject` | One sentence on what the set is about. For people. |
| `code` | Directories a consumer vendors alongside the practices — `tools`, for a set whose practices are about a tool it ships. Practices themselves resolve live and are never vendored. |

Two names are fixed because they are not anyone's product: the universal
set is `precedent`, and a repo-local source is `local`, matching its fixed
`path`. A person's own set defaults to `precedent-individual` when their
config names none. **The repository holding a set may be called anything.**
A consumer that declares a set says where it lives: `path` for the clone,
and `repo` when the repository is not called what the set is — a bare
repository name, joined to `$PRECEDENT_SOURCE_BASE_URL` the way the name
would have been, so a public consumer still names no account.

## What the name used to carry, and what carries it now

Until 2026-09-18 a shared set's name was fixed to `precedent-team-<slug>`
and an individual's to `precedent-individual`, and four pieces of machinery
keyed on the shape. Each of those jobs is now done by a declared field:

| The job | Was done by the name | Now done by |
|---|---|---|
| Knowing a source's level | the `precedent-team-` prefix | `level`, declared beside the name in `precedent.json` and stated in the manifest |
| Building the clone URL | `$PRECEDENT_SOURCE_BASE_URL/<name>` | the same by default; `repo` when the repository is called something else ([tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)) |
| Keying attribution in a consumer's `MANIFEST.json` | the name | the name — unchanged, which is why it is chosen once and never renamed |
| Recognising a vendored private set in a public tree | path segments beginning `team-` or `precedent-(individual\|team-)` | a path segment equal to a **declared** shared source's name, or a `precedent-source.json` that says `private` — files, both, and both catch a set under any name ([tools/leak_gate.py](../tools/leak_gate.py)) |

The identity check replaced the shape check and is the stronger of the two:
[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s `load_source`
reads the manifest of the clone at a declared path and refuses one that
calls itself something else. A name shape could only catch a misspelling;
this catches the wrong repository.

## Four names, four stories

The single biggest risk in "let's have a naming convention" is treating four
distinct things as one. They fail differently:

| # | The name | Who reads it | If it varies | Answer |
|---|---|---|---|---|
| 1 | The repository's own name | people, browsing | nothing, so long as the consumer says where the set lives; a rename still redirects and is a 404 nobody can date | **Free.** A rename is **detected afterwards** by [tools/precedent_source_names.py](../tools/precedent_source_names.py), which compares the declared repository against what GitHub calls it now |
| 2 | The local clone directory (the `path` in [precedent.json](../precedent.json)) | the resolver, per machine | the declared relative path is wrong on that machine | **Warned** about, never refused |
| 3 | The `name` in the source's manifest, and the same string in every consumer's declaration | the resolver, `MANIFEST.json` attribution, every error message | attribution stops matching; a clone that answers to another name is the wrong repository | **Refused** when they disagree; a name that is not a slug is refused outright |
| 4 | What the name means — a subject, not a roster | people, over years | the name goes stale rather than wrong | Judgment; no check can see it |

Row 1 was a recommendation with a mechanical afterthought until 2026-09-18
and is now simply free. The rename detector stays, because a redirect
works until the day it does not: a source repository renamed on GitHub kept
resolving, under its old name, with every check green, until a person
recognised a name he had retired (2026-09-11). Git follows the redirect
silently; GitHub's API answers with the current `full_name`, and since
2026-09-14 a `301` alone is reported as `RENAMED` whether or not the new
name can be read.

Row 2 is deliberately not a refusal. A continuous integration checkout, a git
worktree, and a vendored universal copy at `process/upstream` all legitimately
put a source in a differently-named directory.

## What carries it

| Half of the rule | Carried by |
|---|---|
| A source's identity is its manifest | [tools/precedent_resolve.py](../tools/precedent_resolve.py)'s `read_source_manifest` and `check_source_manifest`, run from `load_source` |
| The `name` field is a slug, or one of the two fixed names | the same module's `check_source_name`, raising rather than warning |
| Name and clone directory should agree | the same module's `warn_name_matches_path`, on standard error |
| `team` still reads as `shared` | the same module's `normalize_level` |
| A new set is created with its manifest, under a name that is a slug | [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py) |
| A declared set is cloned from where the consumer says it lives | [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)'s `_clone_url` |
| A shared set's code vendors under its name | [tools/checkin.py](../tools/checkin.py) `--source <name>`, mirroring the manifest's `code` directories into `process/<name>/` |
| Every `precedent.json` in the tree conforms, and every reachable source answers to its declaration | [tools/precedent_check.py](../tools/precedent_check.py)'s `source-naming` check, with a planted case in [tools/verify_harness.py](../tools/verify_harness.py) |
| A declared source repository is still called what the consumer says | [tools/precedent_source_names.py](../tools/precedent_source_names.py), at [vendor-update-runbook](../practices/vendor-update-runbook.md)'s step 8 — not in [tools/precedent_check.py](../tools/precedent_check.py), which is offline by construction |
| Say it before a name is picked | the occasion index — this practice's occasion names *importing and creating* a repository, not only declaring one |
| The adopter-facing procedure states it | [spec/BOOTSTRAP_NEW_SOURCES.md](BOOTSTRAP_NEW_SOURCES.md) and [INSTALL.md](../INSTALL.md) |

The disclosure half exists because the enforcement half structurally cannot
reach the moment that matters. A check runs against a declared source; a
person picks a name minutes earlier, in conversation. Telling them then is
the only intervention available — which is why it is a clause of the Rule
and not a footnote.

## Decisions taken

**A name is an identity, not a function (2026-09-18).** The first set built
for a subject rather than a team — a body of practices and the code they
are about, used by whoever does that work — could not be called what its
author called it, because the resolver required `precedent-team-`, and the
leak gate had already refused a public proposal document for a title
beginning with the same word. Reading what the name actually carried
showed four jobs (the table above), each with a file that could carry it
better. Morgan approved the change; relayed by Alex, 2026-09-18.

**`shared`, not `team` (same decision).** A team's house rules are one kind
of set a repository declares; a subject system and a code style are
others, and their reach is "everyone who does this kind of work," not "this
roster." The word on the level now says that. `team` still reads, so no
existing declaration breaks; new ones say `shared`.

**Recommend, or recommend and enforce? Both, split by layer** — refuse a
manifest that disagrees with its declaration and a name that is not a slug,
warn on the clone directory, leave the repository name free. Leaving all of
it advisory was the status quo before 2026-09-06, and the status quo had
already drifted in the document adopters read.

**Must a name describe a subject? Yes, and it stays judgment.**
`writing` and `morgan-alex` are indistinguishable to a regular expression.
The Rule says it, with the reason attached; no check pretends to see it.

**What is a repo-local source's name? The literal string `local`**, matching
its already-fixed `path` and carrying the same argument: zero degrees of
freedom, so the answer travels from one Precedent repository to the next.

**Do names assume organization ownership? No, and nothing depends on it.**
`<owner>` is supplied by whoever owns the set and never appears in the
name. If sets move into an organization, no name changes.

## What this does not do

- **It does not touch practice slugs.** Slugs are identities the resolver
  resolves precedence by, and they already have a stated uniqueness rule.
- **It does not rename any existing set.** The three shared sets this
  repository declares keep the names they were created with; their
  repositories are still called the same. A set gains a manifest the next
  time it is touched, and resolves as declared until then.
- **It does not settle the reader-vocabulary tension for the two fixed
  names.** `precedent` and `local` are this project's words, not a reader's,
  and they stay fixed because they name the product and a directory, not
  anyone's set.

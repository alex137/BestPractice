---
title:         Team sets carry code, and install questions carry defaults
kind:          proposal
status:        drafted
opened:        2026-09-18
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Two small generalizations asked for by the first dependent repo to migrate: a team set may ship the code its practices are about, vendored by the consumer the way the universal engine already is; and every install or migration question carries a recommended default the session applies when the person says 'you decide'."
---

# Team sets carry code, and install questions carry defaults

Proposed by the owner of dependent repo #1 on 2026-09-18, after the first
day of moving that repo onto the loader. Both proposals ask for a
generalization of something the system already does, not a new mechanism.
Neither has been built; this document is the case for building them, for
Morgan to accept, amend or decline.

## 1. A team set may carry code

**What exists.** The universal source already pairs code with practices:
[tabular-shared-renderer](../practices/tabular-shared-renderer.md) is a
practice, and `tools/doc_html.py` is the code it is about; the deck engine
under `deck/` is the same shape. A consumer gets both through one vendored
tree ([INSTALL.md §1](../INSTALL.md)), records the tree's commit in its
manifest, and drifts against it file by file. Dependent repo #1 also
carries a second vendored tree, a domain pack, with its own manifest and
blocklist, audited by the same `practice_audit.py` — the pack pattern from
[layered-practice-packs](../practices/layered-practice-packs.md).

**What is missing.** A *team* source is resolved live for its practices
and nothing else. A team whose rules are about a shared tool (a filing
pipeline, a brief builder, a table formatter) has nowhere to put that tool
that the loader knows about: the practices resolve, the code does not
arrive. The repo that hit this keeps its domain pack as a directory in its
own tree because a team set could not carry the pack's engines.

**The proposal.** A team set may ship a `tools/` directory (and other
code directories it declares in its own `precedent.json`, say
`code: ["tools", "deck"]`). A consumer that declares the set as a source
vendors those directories under `process/<set-name>/`, records the commit
in `process/manifest_<set-name>.json`, and is drift-audited on them by the
same `practice_audit.py`, exactly as the universal tree is today. The
practices still resolve live from the sibling clone; only the code is
vendored, because code has to be present offline, for a collaborator
without the sibling clone, and for CI.

Nothing new is invented: the manifest schema, the drift check, the scrub
gate and the engine/shim convention
([engine-plus-host-shims](../practices/engine-plus-host-shims.md)) all
already exist for the universal tree. The change is that `checkin.py`'s
`update`/`record` take a source name and a manifest path instead of
assuming the one universal tree, and that `precedent.json` lets a set
declare which of its directories are code.

**Why now.** The owner's intended layout has one repo for the patent
rules and their filing engines, later perhaps one for presentations, each
declared by every repo that does that kind of work, in addition to the
universal set. That is "as many team sets as it needs"
([SOURCES.md](SOURCES.md)) with code attached, and it is the shape every
domain pack will want once it becomes a repo.

## 2. Install and migration questions carry defaults

**What exists.** [INSTALL_QUESTIONS.md](INSTALL_QUESTIONS.md) is the
canonical list of what a session asks a person. Several rows are
genuinely the person's to answer (private code words, which sets exist).
Several are technical (`ci_workflows`, which assistant, whether to wire an
individual set) and the person asked may not know what the question means.
[declared-default-is-applied](../practices/declared-default-is-applied.md)
already says a setting with no value from the person takes the declared
default and names it in passing; the install questions do not follow it.

**What went wrong.** The first non-technical owner to migrate a repo was
asked, in one message, which team sets to declare, whether to wire an
individual set with an environment credential, and whether `ci_workflows`
should be on. His reply: *"I don't understand your wired for this
environment question"* and *"What is ci_workflows and how should I think
about this?"* Every one of those has an obvious default for his situation
(no team sets yet, no individual set, CI off because every gate runs in
the session before a push). A question without a default forces a
technical decision on a person who trusted the system precisely so that
he would not have to make it.

**The proposal.** Each row of INSTALL_QUESTIONS.md gains two columns:
*recommended default* and *what changes if you take it*. The session asks
the question with the default stated, and treats "you decide", silence, or
any answer that does not name a choice as the default, recorded with
`strength: assented` per [decision-strength](../practices/decision-strength.md).
Only the rows with no defensible default (private code words, which sets
exist) stay as bare questions. A migration of a repo that already works
should then need one message from its owner, not a tutorial.

## What this document does not propose

- No change to precedence (team > repo-local > individual > universal).
- No change to the individual set's privacy rule; individual sets still
  never appear in a repo's tracked config, and this proposal does not let
  them carry code either.
- No move of the deck engine or the table renderer out of the universal
  tree. The owner asked and decided they stay; a team set carrying code is
  for domain rules that never belong upstream (a patent filing pipeline is
  the standing example), not for splitting the universal tree.

## Open questions for Morgan

1. Whether `precedent.json`'s `code:` declaration is the right home, or a
   set's own `ENGINE_MANIFEST.json` should list its code the way the
   vendored engine's does.
2. Whether the consumer-side vendored tree should be `process/<set>/` (the
   pack layout that exists) or somewhere the loader owns.
3. Which questions in INSTALL_QUESTIONS.md he agrees have a defensible
   default, and what the defaults are.

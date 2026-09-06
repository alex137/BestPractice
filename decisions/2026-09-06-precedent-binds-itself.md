---
date: '2026-09-06'
question: |
  Three related calls, asked together. (1) BestPractice has no
  `approvers.json` -- should it, naming Morgan and Alex, or are
  GitHub permissions the right mechanism? (2) TODO's
  `unreachable-practices` item: 43 of 114 practices in force here
  are reachable by no loading channel, and the item was blocked on
  a design decision -- should this repo be binding on itself, and
  by which of the three named shapes? (3) The leak gate reports
  partial rather than a pass -- can a default blocklist word make it
  pass and exercise the layer at the same time?
decision: |
  (1) No `approvers.json` here. The approval asymmetry in this repo
  is branch-based (`precedent-beta-v01` needs no sign-off; `main`
  needs Alex, named explicitly), and CODEOWNERS is path-based and
  cannot express that. Recorded as a deliberate absence rather than
  left as an oversight.
  (2) Yes, and by a combination the item did not list: shape 2 (a
  per-repo declaration) is built now, because shape 3 alone
  (multi-source generated views) is unsafe in a public repo and
  would also require retiring valid rules. New `not_binding` in
  `precedent.json`: {slug, reason}, honored by the reachability
  check, with a mandatory reason, a refusal to exempt
  `severity: blocking`, and stale-entry reporting.
  (3) No -- not in the vocabulary layer. Profanity is added to the
  always-on STRUCTURAL layer instead, where a committed pattern is
  honest. partial stays partial.
alternatives: |
  ["Add approvers.json naming Morgan and Alex and generate
  CODEOWNERS from it -- rejected: it is either inert without branch
  protection, or, with it, breaks the documented rule that a
  session may merge into precedent-beta-v01 without Alex",
  "Shape 1, a per-practice `binds:` / `not_in_repos:` field the
  resolver honors -- rejected: whether a rule binds is a property
  of the pair, and a practice cannot know which repos it will
  reach",
  "Shape 3 alone, multi-source generated views here -- rejected for
  this repo: it publishes private team practice text into a public
  AGENTS.md, and its own framing ('the misfits get retired or
  moved') would repeat the deep-check error of dropping a valid
  rule because it does not apply here",
  "Put a publishable word on a committed vocabulary blocklist so
  the gate reports a pass -- rejected: it reports a private-term scan
  that never ran"]
decided_by: Morgan
---

## 1. Why no `approvers.json` here

`approvers.json` exists so a **team practice set** can generate a CODEOWNERS
that enforces its own approval rule. BestPractice is not a team set: it is
the universal set, whose approval route the plan defines as *a pull request
to Precedent, reviewed and merged by someone other than whoever proposed it*
— which is repository-level review, i.e. GitHub permissions, exactly what is
in place.

**The decisive reason is that this repo's approval rule is branch-shaped and
CODEOWNERS is path-shaped.** [AGENTS.md](../AGENTS.md) is explicit: merging
into `precedent-beta-v01` needs no sign-off from Alex, and `main` needs him
naming `main` explicitly. CODEOWNERS cannot say that — it assigns owners to
*paths*, and applies to whatever branches the repository's protection rules
point it at. A CODEOWNERS here would therefore be either inert (no branch
protection, so it enforces nothing and merely looks like governance) or
actively wrong (branch protection on, so every routine beta merge now waits
on a review the documented workflow says it does not need).

The repository is also `alex137`'s, not Morgan's, so branch protection is
not Morgan's setting to make.

**What was a real problem is that the absence was silent** — nothing recorded
whether the universal set had no approvers file by decision or by oversight,
which is the same "a forgotten thing and a deliberate one look identical"
failure this session spent the day removing elsewhere. That is what this
record fixes.

## 2. Why `not_binding`, and why not the other two shapes

[TODO.md's `unreachable-practices` item](../TODO.md#unreachable-practices)
named three shapes. The measurement behind it
([spec/PRELAUNCH_AUDIT.md](../spec/PRELAUNCH_AUDIT.md)) is what decides
between them: running the source-supplied checks against this tree, five
pass, four report real findings worth fixing, and **six report things this
repo cannot act on because the practice is about a different kind of
repository** — one a single person authors alone, or a practice set's own
shipped content.

**Shape 1 (a per-practice field) is wrong because whether a rule binds is a
property of the pair, not of the rule.** `commit-author` binds a repo one
person authors alone and not one with many contributors. The practice cannot
enumerate the repositories it will reach; the repository knows why a rule
does not bind it. So the declaration belongs to the consumer.

**Shape 3 (multi-source generated views here) is unsafe in this repo
specifically.** BestPractice is public. The generated `AGENTS.md` carries
practice Rule text and one-line index clauses, so rendering the resolved
multi-source set would publish private team practice content — the exact
thing [tools/leak_gate.py](../tools/leak_gate.py) exists to prevent. That
constraint is not mentioned in the item's own description of shape 3, and it
rules it out on its own.

Shape 3 carries a second problem worth naming, because it is a pattern this
project has already been bitten by once: its framing is that the misfits
"get retired or moved". Retiring `commit-author` because it does not bind
*this* repo would drop a rule that is correct and in force where it belongs —
the same reasoning that dropped `deep-check` on the authority of a rule it
merely resembled. A rule that does not apply here is not a rule nobody wants.

So: **shape 2, built now.** `precedent.json` gains `not_binding`, a list of
`{slug, reason}`. The guards are the feature, because an exemption list is
otherwise a mechanism for opting out of rules:

- **A reason is mandatory.** An exemption nobody argued for is the same
  silence, with a configuration entry on top.
- **`severity: blocking` cannot be exempted** — the same rule the resolver
  already applies to precedence, for the same reason: a blocking practice is
  precisely the one no downstream declaration may switch off.
- **A stale exemption is reported**, since one naming a slug nothing puts in
  force is either a typo (and the rule it meant to exempt is still
  unexplained) or has outlived its practice.
- **A malformed list fails loudly**, because a list that silently ignores its
  own bad entries is a way to opt out by typo.

`check_not_binding_cannot_be_abused` asserts all four with negative controls.

**What this does not yet do.** The exemptions themselves are not populated.
Doing that honestly requires resolving the private team and individual
sources, which this session could not attach (see below), and writing
exemptions for practices whose text and severity cannot be read would be
asserting what cannot be verified. The mechanism is built and tested; the
population is a measurement, and it is named in the TODO item.

## 3. The leak gate now reports OK, and the vocabulary layer actually runs

The original ask was: put a word on a blocklist by default, so the mechanism
gets tested and the permanent partial result goes away. **The first answer
here was too rigid.** It put profanity in the *structural* content rules and
kept the vocabulary layer reporting a partial result, on the reasoning that a
committed blocklist publishes the secrets it exists to guard.

That reasoning is correct about a **private** blocklist and irrelevant to a
**publishable** one, and conflating the two threw away the better design. The
vocabulary layer now has two halves:

- **Default** — [tools/leak-blocklist.default.txt](../tools/leak-blocklist.default.txt),
  committed, always applied. Profanity, in a repository whose documents are
  read by people outside the project. Nothing in it is a secret, so
  committing it costs nothing.
- **Private** — still external, still named by `PRECEDENT_LEAK_BLOCKLIST`,
  still refused by `load_blocklist()` if it is located inside this
  repository, and **merged** with the default rather than replacing it.

**The default half's real job is that it makes the layer run.** Until this
change the whole vocabulary layer was skipped whenever the environment
variable was unset — every continuous-integration run, every fresh clone — so
the code that loads, compiles and scans with patterns was exercised only by
the harness. A mechanism that runs only in its own tests is one nobody finds
out is broken. That is also why the original ask was right: exercising it was
the point.

So `leak gate PARTIAL` is gone, because "the layer did not run" is no longer a
reachable state. What survives is one accurate line saying the **private**
half did not run, so publishable terms were checked and private ones were not
— because a clean scan against the default list is genuinely not evidence
about private words, and dropping that sentence would leave the old silence
with better wording.

Two implementation notes, both found by the gate catching its own tree:

- The default blocklist file is the one path the tree scan skips. A list of
  banned words necessarily contains them, so scanning it would hard-fail the
  gate on its own list. This is **not** the arbitrary `!path` exemption
  `_parse_blocklist` refuses: it is a single fixed committed file whose whole
  purpose is to hold those strings, and a private term placed there would be
  published by the commit itself long before any scan.
- The harness's own probe strings are base64-encoded in the source, because
  `verify_harness.py` is scanned too. The first version used a plain literal
  and the gate correctly refused the tree — the check working, on its author.

**To switch the private half on**, the blocklist belongs in
`precedent-individual`, pointed at by `PRECEDENT_LEAK_BLOCKLIST`, with
`git config precedent.requireVocabulary true` so a shell that loses the
variable fails the push instead of silently dropping to the default half.

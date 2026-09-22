---
slug:              todo-2026-09-21-pass-3-coherence-read-findings
kind:              manual
domain:            practices
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "three of these land in themorgan/precedent-shared-* , which this session cannot reach -- GitHub access here is scoped to alex137/BestPractice and attachment refuses across owners"
noted:             2026-09-21
closed:            null
---
## What

The 2026-09-21 very deep check's pass 3 read all five catalogues in force
(140 universal + 6 repo-local + 30 individual + 42 + 20 + 5 shared), the
top-level documents, and the 33 shipped template files. The small
mechanical findings were fixed in the same pass and are in commit
`d1d4439d`. **These are the ones that need a decision.**

Findings still open from the 2026-09-19 run are in
[todo-2026-09-19-pass-3-coherence-read-findings.md](todo-2026-09-19-pass-3-coherence-read-findings.md)
and are not repeated here; that item's own status was re-measured and the
results are at the bottom of this one.

## A. The same rule active at two levels — three cases

The level system exists to stop exactly this, and precedence decides it
silently.

**A1. `push-back` is `status: active` at universal AND shared**, with
byte-identical Rule, Detail, Why and Story.
[practices/push-back.md](../practices/push-back.md) says
`approved_by: "... moved from the shared set precedent-team-writing"`, so
the move was intended — and only half of it happened. Precedence is shared
over universal, so **the copy that actually resolves in any repo declaring
`precedent-shared-writing` is the old shared one**, and the universal copy
the occasion index advertises never wins anywhere. Remedy: flip the shared
copy to `status: deduplicated`, `in_force_at: push-back`. **Lands in
`precedent-shared-writing`.**

**A2. `small-calls` — identical shape.**
[practices/small-calls.md](../practices/small-calls.md) carries the same
"moved from the shared set" note; the shared copy is still active and the
bodies diff clean. Same remedy. **Lands in
`precedent-shared-working-style`.**

**A3. `vendor-neutral-by-default` is active at repo-local and shared**, the
shared copy carrying an `approved_by` quoting Morgan asking for the move.
**This one is not a clean flip.** Deduplicating the local copy removes the
rule from the public generated block entirely: `build_views.py` excludes
private-level sources in a repo declaring `visibility: public`, so the
shared copy renders nowhere here, and the local copy is currently the only
reason the rule is in front of a session reading
[AGENTS.md](../AGENTS.md).
[local/practices/park-it.md](../local/practices/park-it.md) is the
mechanical precedent, but its survivor is universal and therefore public,
which is the difference.

## B. A shipped template contradicting a resident practice

**B1. All three shipped instructions-file templates tell adopters to do
what resident `environment-gotchas` forbids.** Severity: this is the
2026-09-08 `VOICE.md` shape, live and unnoticed.

[practices/environment-gotchas.md](../practices/environment-gotchas.md):
*"one trap, one file, forever — under `gotchas/gotcha-<date>-<slug>.md`"*;
*"**None of that catalogue loads into the instructions file, at any size**
— not the stories, and not even a one-line-per-trap index"*; *"**Every
entry is its own file from the first one.** There is no size below which
stories live inline 'for now'."*

[templates/AGENTS.md.template](../templates/AGENTS.md.template),
[templates/AGENTS.md.loader.template](../templates/AGENTS.md.loader.template)
and [templates/document-project/AGENTS.md](../templates/document-project/AGENTS.md)
each carry a full inline gotcha story in the instructions file, an HTML
comment reading *"Add yours below the inherited entry; replace nothing"*,
and placeholder slots for the next ones. `grep -rn "gotchas/" templates/`
returns two hits in the whole tree, both code comments inside
`freshness-guard.sh` — **the directory the resident practice mandates is
named in no template.**

Every adopter instantiating these gets two live, opposite standing orders
in the same context window on every turn. Rewriting three templates is not
a pass's own tidy-up.

**B2. Two shipped general rules have no catalogue home.** Both in
`templates/AGENTS.md.template` and `.loader.template`, in a Conventions
list where every neighbouring bullet cites a practice slug and these two
cite none:

  - *"Commits are credited to the human driving the session."* Universal
    `ci-commits-carry-identity` covers workflow commits only; the only
    practice covering a session's own commits is `commit-author`, in the
    **private** individual set. An adopter gets the standing order with
    nothing in their resolved catalogue behind it and no
    `precedent_show.py` to look it up.
  - *"Open each session by catching the member up."* Stated in no practice
    in any of the five catalogues.

Both fail the practice's own test — *"would this improve anyone's work? If
yes it is a practice in the wrong place."*

## C. A shared rule this repository breaks about 1,100 times

**C1.** `doc-link-text` (`precedent-shared-writing`, `status: active`,
`applies_to: ["**"]`) says the link text is the document's name, *"never
the bare filename… Write `[the Glossary](GLOSSARY.md)`… not
`[GLOSSARY.md](GLOSSARY.md)`."* That source is declared in
[precedent.json](../precedent.json) and `not_binding` is empty by that
file's own statement.

Measured this run: **1,102** markdown links whose text is a bare filename
and whose target carries its own `# H1`, of 1,674 resolving `.md` links,
excluding `practices/`, `templates/` and `deck/`. The form is used in
[AGENTS.md](../AGENTS.md) itself, in [MAP.md](../MAP.md), and in the
universal `doc-references-are-links` practice's own examples.

The decision is real either way: **either `doc-link-text` is scoped to
human-facing prose and should say so, or this repository is in wholesale
violation of a rule it declares.** Nothing in between is honest, and no
third style should be introduced while it is open.

## D. Staleness that needs a call rather than an edit

**D1. [TODO.md](../TODO.md)'s stub carries a live claim about a file that
changed under it.** Its closing paragraph says the gotcha index in
`AGENTS.md` *"stays hand-kept, unchanged, still linking into
`record/GOTCHAS.md#gN` as before."* That section now carries only a
pointer plus `gotchas/INDEX.md`, and links into `record/GOTCHAS.md#gN`
nowhere. The rest of the stub is a frozen migration record and should
stay; this paragraph is not frozen, it is wrong.

**D2. [AGENTS.md](../AGENTS.md)'s Vocabulary paragraph overstates both the
tool and its own list.** *"names any source that did not"* —
`precedent_vocabulary.py` names a source that failed to **resolve**, not
one that resolved and contributed no `command:`; in this run all four
private sources resolved, none contributed a command, and nothing said so.
*"This list derives from those fields"* — the bullet list has 10 commands
and the tool prints 18. The eight absent ones are all reachable through
the occasion index, so nothing is unfindable; the list is simply not
derived, and the sentence says it is.

**D3. `tools/build_views.py` writes the character
`doc-references-are-links` forbids into the one file every session loads.**
It emits `## Resident block (~N of M token budget, …)`; that practice's
clause (b) is *"Use `≈` for 'approximately', never `~`."* Same at four
other lines in tool messages. One character, but it changes generated
output and leaves `AGENTS.md` failing `build_views --check` until
regenerated.

## E. The strict sweep's headline number is inflated

**E1. `doc_lint.py`'s promised frozen-document exclusion excludes
nothing.** Its docstring says *"Frozen-document artifacts (name prefixes in
`FROZEN_PREFIXES`, per repo) are excluded from the default and `--all`
selections"*; [tools/doc_lint.py](../tools/doc_lint.py) line 174 is
`FROZEN_PREFIXES = ()`, and the function returns every file unchanged when
it is empty.

Roughly **573 of the 2,004** strict findings sit in documents nothing
should be rewriting — counted by frontmatter (`status: superseded|frozen|
closed|retired|historical`, `kind: record|decision`, or a path under
`decisions/`), so an order of magnitude rather than an exact figure. That
is about 29% of a work list that can never legitimately be cleared, and it
inflates the headline on every run.

**E2. The headline files are mostly correctly bare.** `INSTALL.md` (102)
and `SETUP.md` (19) reference the **adopter's** `AGENTS.md`, `MAP.md`,
[`TODO.md`](../TODO.md) — linking those would point a reader at this repository's own
copies, which is the failure the same rule warns about. Anyone budgeting
the remaining findings should subtract these before costing the work.
`doc_lint.py --fix` cannot touch this class at all; every fix is manual.

## Re-measurement of the 2026-09-19 findings

**Closed since:** `archive-command`'s reading-order finding (now
`deduplicated`, `in_force_at: archive-status-check`); the three missing
`in_force_at` fields (now zero). `session-text` is half-resolved — now
`deduplicated`, `in_force_at: prompt-please`, and this run fixed
[`AGENTS.md`](../AGENTS.md)'s bullet for it (commit `6e40a83d`).

**Worse:** [`very-deep-check.md`](../practices/very-deep-check.md) is 25,208 words against the ≈19,225
recorded on 2026-09-19, up roughly 30% in two days. Practices with no or
hollow `## Detail`: 42, was 39. `## Rule` sections over 150 words: 61, was
54. `severity:` signal: 137 `default` / 3 `advisory` of 140, was 128/2 of
130.

**Probably not a defect, worth closing:** the 2026-09-19 "6 missing
`index_clause`" is 5 now, and all five are `tier: resident`. A resident
practice is in the block, not the index, so the absence looks deliberate.

**A prior figure that would not reproduce:** "8 with an unquoted `added:`
date" measures 68 of 140 by the obvious method (any `added:` value with no
leading double quote). Either the earlier count measured something
narrower or it was wrong; the method is stated here rather than a number
picked between them.

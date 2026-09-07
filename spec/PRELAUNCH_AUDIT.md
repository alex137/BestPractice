---
title:         The Pre-Launch Audit — 2026-09-06
kind:          record
status:        closed
opened:        2026-09-06
closed:        2026-09-06
superseded_by: null
supersedes:    []
audience:      session
summary:       What a real from-scratch install, a real migration and a real two-team resolve broke on 2026-09-06, what was fixed, and what stayed open.
---
# The Pre-Launch Audit — 2026-09-06

Morgan asked for a very deep check plus a full practice audit across
Precedent and its three practice sets, "prioritise the roadblock bugs for
using this in a real-world team setting, including from scratch and
migration," before showing the work to Alex.

This is the record of what that found, what it fixed, and — the part that
matters more — **what it did not get to**, so the next session starts from
here instead of re-deriving it. Companion to
[spec/PHASE5_DEEPCHECK.md](PHASE5_DEEPCHECK.md), which did the same job
before phase 6.

## The method, because it is the reason anything was found

Reading the install documentation would have found none of this. Every
significant finding below came from **building the thing the document
describes and running the checks on it**:

- a scratch repository installed per [INSTALL.md](../INSTALL.md) §0
  (Precedent loader, fresh repo),
- the same with the real `precedent-team-maintainers` set attached,
- a scratch repository on the classic §1 `process/upstream/` layout, then
  walked through [spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)
  steps 3, 7 and 8.

Scores before and after, on `precedent_check.py`:

| Fixture | Before | After |
|---|---|---|
| Fresh §0 install | 8 violated | 0 violated |
| Classic §1 install | 3 violated, plus 3 checks passing on scans that never ran | 0 violated, those 3 genuinely running |
| §1 install migrated to the loader | not reached (the vendor step failed) | 0 violated |

## What was actually broken

Grouped by what an adopter would have hit.

### The enforced channel was hollow where it mattered most

**Nothing ran a source-supplied check script.**
`precedent_materialize.py` copied them into a consuming repo,
`precedent_land.py` refused to land a team or individual practice without
one, and [spec/PRIVATE_ENFORCEMENT_BRIEF.md](PRIVATE_ENFORCEMENT_BRIEF.md)
explained how to write one — and then no command invoked them. A consuming
repo held **fourteen real, tested check scripts** (nine in
`precedent-team-maintainers`, five in `precedent-individual`) that never
ran. The enforced channel was live for the universal catalogue and hollow
for exactly the sources an adopting team writes for itself.

**Three enforced practices reported a clean pass on a scan that never
ran.** `scrub-gate`, `practice-export-loop` and `scripts-assert-properties`
shell out to tools not in the vendored engine; Python exits 2 with "can't
open file", which carries no `FAIL:`, no `SCRUB:` and no `NOT APPLICABLE`,
so every caller filtered zero lines out of it and returned no findings.
This is the exact "a scan with an empty input set printing OK" failure
`precedent_check.py`'s own docstring says the module exists to prevent.

**Four checks looked for sibling tools in the wrong place** on the classic
layout, where the tools live at `process/upstream/tools/` and `ROOT` is
deliberately the consuming repo.

### A new install could not come back clean, whatever the installer did

Of the eight violations a fresh install ended on, five were unfixable from
inside that repo: a check about *this* repository's own beta branch, a
demand for `templates/harness/LEDGER.md` in a repo with no harness
adapters, a demand for a `routing_audit.py` the engine did not vendor, a
"stale generated view" report for `MAP.md`/`GLOSSARY.md` that
[INSTALL.md](../INSTALL.md) §0 itself says are hand-authored, and a
`code-cites-practice` violation for a slug no consumer's catalogue has.

### The two documented commands disagreed with each other, permanently

A consuming repo runs `precedent_sync_views.py` at session start and
`build_views.py --check` on every `precedent_check.py`. Only the first
passed `source_levels`, so they rendered different header lines for the
same catalogue — and each reported the other's output as hand-edited or
stale, forever, whichever ran last.

### Two teams could silently disagree

Two team-level sources claiming one slug resolved to whichever
`precedent.json` listed second, reported as an ordinary `overridden:`
notice indistinguishable from a legitimate higher-level override.
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) says the resolver
fails loudly there. It does now.

### A team's declared approvers enforced nothing

The `approvers.json` → `CODEOWNERS` generator the plan describes existed
in exactly one place: inside one private team set's own `tools/`. The
second team set, bootstrapped from the template on 2026-09-05, got its
approvers list and no way to turn it into enforcement, and nothing said
so.

### 96 documentation links resolved to nothing

67 of them in `practices/*.md`, written root-relative from files that live
one directory down — so they 404'd on GitHub for anyone reading a practice
file, which since the fork is the primary way a practice is read. The
convention was written down (`doc-references-are-links`) and nothing
checked it, so it broke quietly for as long as it existed.

### The loading channel was spending context carelessly

An edit to any markdown file matched ten on-demand practices and printed
≈1,000 words of Rule text — **the same 1,000 words on every edit**. A
session editing thirty markdown files was handed roughly forty thousand
tokens of exact duplication, by the one mechanism in this system whose
entire purpose is to spend context carefully.

### Mechanical rules that fired on things nobody could fix

- The acronym check reported 101 unglossed acronyms, nearly all ALL-CAPS
  filename stems (`LEDGER.md`) or ordinary words written in caps for
  emphasis (`ONLY`, `BEGIN`, `BOTH`). Three causes were structural and
  fixed as such; the fourth was first patched by hand-adding forty English
  words to the stoplist, which is not a fix — it is a list that grows
  forever and is wrong the first time somebody shouts a word nobody
  thought of. Replaced with the discriminator that was in the corpus all
  along: an initialism has no ordinary lowercase form, a shouted word is
  one the same repository writes in lowercase constantly. `NOT` appears 22
  times in caps here and 1,899 in lowercase; `RPP` is 45 and 0. Down to 6,
  all real, with no wordlist — and a consuming repo learns its **own**
  vocabulary, which a list written here never could.
- `cite-the-incident` treated a repointed link inside a Rule as a
  *rewritten Rule* and demanded a `## Story` for four inherited practices
  whose prose had not changed by a word — clearable only by inventing an
  incident or leaving the link broken.
- `environment-gotchas` parsed the bulleted placeholders inside a
  template's own HTML comment as real gotcha entries and failed them for
  having no story.
- `precedent_check.py` held its own copy of the acronym scan under a
  docstring promising "one detector, two callers", and had drifted from it
  exactly as that docstring said it must not.

### A permission verdict nobody asked for

The `PreToolUse` context hook emitted `"permissionDecision": "allow"`
alongside its context. On the reading where that field settles the
decision, every install of this adapter silently auto-approved every
`Edit`, `Write` and `NotebookEdit` whose path matched any practice — which
is most of them. It matters most for the case this repo already designs
for: a non-technical contributor on a deliberately narrow permission set
(see [templates/nontechnical-document-project/AGENTS.md](../templates/nontechnical-document-project/AGENTS.md)),
where a practice loader quietly widening what may be written is the
opposite of what was asked for.

### This repo did not run what it ships

`.claude/settings.json` had no `PreToolUse` hook at all — the
path-triggered loading channel, unrun in the repository that defines it —
and an allowlist still naming `process/upstream/tools/` paths this repo
does not have. Both fixed; the template's allowlist was equally stale, and
listed every command only in its `Bash(cmd *)` form, which does not match
a bare invocation, so the light check `AGENTS.md` tells every session to
run prompted on every single run.

## Still open — start here

### Decided, 2026-09-06

1. **The product is called Precedent, in the documents people read.**
   Morgan's call, made during this audit. Renamed across
   [README.md](../README.md), all four [documentation/](../documentation/)
   guides, [SETUP.md](../SETUP.md), [INSTALL.md](../INSTALL.md),
   [GITHUB_ACTIONS.md](../GITHUB_ACTIONS.md), [MOBILE.md](../MOBILE.md),
   [GIT.md](../GIT.md), and every template an adopter instantiates.

   **What a later rename pass must not touch**, because each of these
   means something the rename would falsify:

   - `alex137/BestPractice` and `../BestPractice` — the repository's actual
     name, and the path to a clone of it.
   - `approved_by: "BestPractice (pre-fork)"` on 53 practice files. That
     records who approved the practice and when.
   - Sentences that mean the pre-fork system specifically ("a repo that
     already vendored BestPractice the old way", "its original
     BestPractice number").
   - The historical record: `spec/` briefs, `decisions/`,
     [CHANGES_TO_TELL_ALEX.md](../CHANGES_TO_TELL_ALEX.md),
     [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md),
     [PRACTICES.md](../PRACTICES.md), `evals/`. These describe what
     happened, under the name it happened under.

   The repository itself is still `alex137/BestPractice`. Renaming it is a
   separate act with its own consequences (every existing clone's remote,
   every vendored `ENGINE_MANIFEST.json`'s `source_repo`, every absolute
   link in the private sets) and is not part of this.

   **The rule, stated mechanically** (Morgan, 2026-09-06, narrowing the
   four bullets above into something a session can check rather than
   judge): rename the product **in prose only**. Nothing inside link
   syntax changes — not a link target, not a URL, not a path, not a
   filename, not an anchor — until the repository is officially renamed.
   The four bullets say *why* each exception exists; this says where the
   line is, and it is the same line every time: if the text is a thing a
   reader clicks or a machine resolves, it names the repository as it is
   today, not as it will be called.

   The rename commit was audited against that rule after the fact and
   already met it: of its 26 files, zero link targets, zero URLs, zero
   code spans, zero filenames and zero anchors changed. The one thing
   worth naming because it looks like an exception and is not:
   [templates/github-actions/doc-lint.yml.template](../templates/github-actions/doc-lint.yml.template)'s
   workflow `name:` became "Precedent documentation checks". That is a
   display label. A repository's branch-protection rules key off the
   **job** name, which is still `Markdown lint`, so no adopter's required
   check changes identity.

2. **`themorgan/Precedent`** (private, created 2026-08-31, last pushed the
   same day) is an abandoned early fork. The restructuring it was for is
   what `precedent-beta-v01` in this repository now holds, and nothing
   anywhere references the fork. Morgan is deleting it by hand.

   **On reusing the name afterwards**: GitHub frees a repository name the
   moment the repository is deleted, and the same account can create or
   rename a repository to that name again — nothing reserves it (*as of
   2026-09; GitHub does not publish a hold period for this, so confirm on
   the day rather than trusting this line*). Two things to know that
   matter more than the name: a fork of a **public** repository is public
   and cannot be flipped to private, so a private copy of
   `alex137/BestPractice` has to be a new repository pushed from a clone,
   not a fork; and GitHub allows one fork per account per upstream, so if
   a fork is what is wanted, the name has to be set on the fork itself
   (the fork dialog offers a name field) or changed by renaming afterwards.

### Real work, scoped

3. ~~**A materialized practice's relative links are dead in the consuming
   repo.**~~ **Done, later the same day.** Worth recording how: this item
   was queued as blocked on a byte-identity audit that would have to change
   in the same pass — and when the next session (this one) went to do it,
   that blocker did not exist. Nothing compares a materialized practice's
   bytes to its source; the byte-identity audit is about *check scripts*.
   The blocker was an assumption written down as a fact, which is exactly
   what a `blocked-on` line is supposed to prevent. **Check a stated
   blocker before believing it**, including one this project wrote itself.

   The fix: `precedent_materialize.py` repoints each link for where the
   file lands — a commit URL into the source repository, or a recomputed
   relative path when the target is inside the consuming repo — leaving a
   sibling citation, an external URL, a link that already resolves, and a
   link already broken at the source alone. Verified against a real
   four-source install: 0 broken links, 39 distinct sibling citations still
   resolving. `precedent-team-maintainers`' light check dropped the
   exemption it needed to stay green, and its test for that path now
   requires a finding instead of silence.
4. ~~**Nine links pointed at headings that no longer exist.**~~ **Done.**
   Found by asking whether the rename above had touched anything inside
   link syntax; it had not, but the scan turned up a defect a level down.
   [doc_lint.py](../tools/doc_lint.py)'s link check verified that a
   target's *file* existed and skipped its `#fragment` entirely, on a
   docstring's claim that an anchor "is not something this can check
   without rendering the document". It is: GitHub's slug rule is
   mechanical. Nine anchors were dead — six headings simply reworded since
   the link was written, two naming an `INSTALL.md` section 9 that does
   not exist (step 9 is a list item inside §1, and a list item has no
   anchor), one amended in place.

   This is the quiet half of the broken-link class, and worse than the
   404 half: a dead anchor still loads the right document, just at the
   top, so no reader ever reports it. The check now resolves fragments
   against the target's real headings. Two things it gets right that a
   naive version would not, both pinned in the harness: a dash set off by
   spaces yields a **double** hyphen (`cost — the numbers` is
   `#cost--the-numbers`, because the dash is deleted and both its spaces
   survive), and a document written in a heading style the parser does not
   read reports "cannot tell" rather than "the anchor is missing". All
   nine are fixed; the whole tree resolves. practice: `convention-to-audit`.
5. ~~**`precedent_sync_views.py --check` wrote to the working tree.**~~
   **Done.** Found by running the real consumer repos rather than
   fixtures — a private four-source install whose
   own `AGENTS.md` tells every session to run this at session start.
   `--check` guarded only the `AGENTS.md` write; `materialize()` ran
   underneath it unconditionally, deleting and rewriting `practices/`,
   `tools/checks/` and `MANIFEST.json` every time.

   Two consequences, both observed in that repo, not reasoned about:

   - The repo's own light check correctly failed on a materialized check
     script that had drifted from its source. Running `--check` made the
     failure **disappear** — not by fixing the drift, by overwriting the
     drifted file from the live source. A check that destroys the
     evidence it exists to report is worse than no check.
   - With one source unreachable — the ordinary state of a session before
     `add_repo` has run, which both consumer repos' own instructions
     describe as the common case — a `--check` run **deleted 57 tracked
     files**: every practice and check script that source contributed. It
     printed a check verdict while doing it. Paired with a Stop hook that
     blocks ending a turn on uncommitted changes, this pushes a session
     toward committing the deletion.

   `--check` now plans everything against the same output directory (so
   link rewriting resolves identically) and compares, writing nothing.
   It also gained the thing it never had: the old version compared only
   `AGENTS.md`, so a hand-edited materialized practice reported **clean**.
   Pinned in the harness in both directions — the negative control failed
   the old code on exactly those three points.

   Running it against the real repo immediately surfaced 11 differences
   that had been invisible, including two orphaned check scripts from a
   team practice retired weeks earlier.
6. ~~**A materialized link could publish a private repository's URL.**~~
   **Done.** Caught by a consuming repo's own `private-repo-scrub` check,
   on a link the link-placement work in this same session had just
   created. `_rewrite_links` turns a link pointing into the source's own
   repository into `https://github.com/<owner>/<repo>/blob/<sha>/...`.
   For an **individual** source that is a disclosure, not a convenience:
   [precedent_resolve.py](../tools/precedent_resolve.py)'s `load_config`
   refuses an individual source declared in a shared repo's tracked
   config precisely so its existence and location cannot leak to everyone
   who can read the repo — and a consuming repo can be public, as
   the project's own prior notes repository is. An individual source's links are now left
   as written; a relative link that does not resolve is a smaller failure
   than a disclosure that cannot be taken back.
7. ~~**Ten practice files' frontmatter was not valid YAML.**~~ **Done.**
   The fence says YAML and consuming repos parse it with a real YAML
   library. This repo's own reader takes everything after the first colon,
   so `title: Build/buy: decompose before deciding` read fine here and was
   rejected outright by PyYAML, which sees a nested mapping. Ten of
   sixty-one universal practice files shipped that way; the three private
   sets were clean. Nothing here noticed for as long as the format existed,
   because nothing here parsed its own output the way the people
   downstream do — it surfaced only when a consuming repo's light check
   reported it. Titles are now JSON-quoted when they need it, the same
   escape `occasion:` and `applies_to:` already used, and a harness check
   parses every practice file with PyYAML (reported as not-applicable, never
   passed, where PyYAML is absent).
8. **The team set's 39 judgment-only practices were not swept.** The full
   practice audit reports 49 judgment-only practices across three sources.
   This session judged the universal slice's highest-yield ones
   (`lead-with-what-it-is`, `section-order-by-frequency`,
   `registry-source-of-truth`, `volatile-rules-carry-dates`,
   `readers-vocabulary`) against the real tree and fixed what they found.
   The team and individual slices are untouched — a session with those
   repos attached should take them next, one at a time, with the closed
   question the practice's own Rule names.
9. **[TODO.md's `additionalcontext-reaches-the-model` item](../TODO.md#additionalcontext-reaches-the-model) still needs a live session**: whether
   `additionalContext` reaches the model or only the transcript. The test
   plan is written; it needs a real Claude Code session with the adapter
   installed. Now cheaper to run than it was: this repo installs the hook
   itself as of today, so the next session here is the test.
10. **The design half of [TODO.md's `multiple-team-sources-disagree` item](../TODO.md#multiple-team-sources-disagree)**: whether a consuming repo should
   be able to express a preference between two team sources at all, rather
   than being told to rename one. The silent-failure half is closed; the
   design question is untouched, and a second team set now exists to test
   any answer against.

### For Morgan — found by running the two real consumer repos, his call

These are decisions about his own repositories, not defects in Precedent,
so this session reported them rather than acting on them.

- **the project's own prior notes repository is public and names the private individual
  source about forty times** — its `AGENTS.md` alone ten, plus `README.md`,
  `GETTING_STARTED.md`, `MAP.md`, `TODO.md`, three `content/` documents,
  and `.claude/hooks/`, several as full `https://github.com/themorgan/precedent-individual/blob/...`
  URLs. The same `AGENTS.md` states the boundary it is crossing: the
  individual source is "**Never** declared in this repo's own tracked
  config — naming it here would leak its existence and location to anyone
  with read access to this repo." The tracked *config* indeed does not name
  it; the prose around that sentence does, at length. Either the boundary
  is real and the prose needs to change, or the disclosure is deliberate
  and the sentence should stop claiming otherwise — but not both. Nothing
  here reveals the private set's *contents*; the leak is existence and
  location. Precedent's own half is closed either way: materialize() no
  longer mints such a URL on its own (item 6 above).
- **That repo's `practice_audit.py` gate can never pass.** Its `AGENTS.md`
  says the audit "must pass before committing anything that touches
  `process/`". It reports 110 SCRUB failures, every one of them the
  `Buenos Aires` term on that repo's own blocklist matching upstream
  documents that legitimately carry it in their own date headers. The
  collision is documented there as understood, but a gate that structurally
  cannot go green is not a gate. Scoping the blocklist to exclude
  `process/upstream/`, or dropping that term from it, would make the
  sentence true again.
- **Both consumer repos mirror engine files by hand rather than with
  [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py).**
  That is how the project's own prior notes repository ended up with three root copies OLDER than
  its own vendored tree — including a `precedent_materialize.py` with no
  self-referential-source guard, the check that stops a sync destroying a
  hand-authored repo-local source — and a `precedent_check.py` sitting
  beside no `routing_audit.py`. Both fixed in this pass, but by hand
  again; the durable fix is for these repos to adopt the vendoring tool,
  whose `CONSUMER_ENGINE_FILES` is the list they are each re-deriving.

### Noted, no action recommended

- **`INSTALL.md`'s sections read 1, 0, 2, 3…** The document explains why
  (§0 is the rarer path, "covered after §1"), which satisfies
  `section-order-by-frequency` — but the numbering still reads as an error
  to a cold reader. Renumbering would touch every `§0`/`§1 step N`
  cross-reference in the repo; not worth it for the confusion it removes.
- **`doc_lint.py`'s 746 unlinked-reference warnings.** Warning-only, and
  scoped to changed files in gate mode. Tightening the rule to "a filename
  never linked anywhere in this document" only takes it to 572 — not
  enough of a reduction to justify changing what the rule means.
- **Adding a file to the vendored engine takes a commit before the harness
  can go green.** `refresh` reads blobs from a published commit by design
  (so it never moves the caller's checkout), so a file that is not
  committed yet cannot be refreshed. `seed` handles the case by falling
  back to the working tree and stamping `<sha>+dirty`; `refresh` takes
  `--from-ref` for fixtures. The remaining friction is inherent to the
  guarantee and is cheaper than weakening it.

## Second pass, 2026-09-06 — the deferred list, worked

The first pass closed what a real install, a real migration and a real
two-team resolve broke, and left a list of what it had not reached. This
section is that list worked through, item by item. Everything below was
reproduced before it was fixed, and each fix has a negative control run
against the code as it stood.

### The tool surface answered `--help` three different wrong ways, and one of them destroyed files

Running `--help` across every script in [tools/](../tools/) — the first
thing any reader of [documentation/HOW_TO_USE_THIS_TECHNICAL.md](../documentation/HOW_TO_USE_THIS_TECHNICAL.md)
types, since that guide points a public audience straight at these
commands — produced three failure shapes and no successes:

- a hard `FAIL: unknown option '--help'` (the seven creation-pipeline
  tools, plus `precedent_show`, `precedent_paths`, `precedent_gate`,
  `leak_gate`, `routing_audit`, `precedent_sync_views`, `precedent_resolve`,
  `precedent_simulate`);
- a silent fall-through that **ran the whole audit** as though nothing had
  been asked (`precedent_check`, `doc_lint`, `verify_harness`,
  `catalogue_stats`, `full_practice_audit`, `very_deep_check`,
  `parse_check`);
- the docstring printed with a non-zero exit (`checkin`,
  `precedent_vendor_engine`), and one bare traceback (`doc_html`, which
  read the flag as a document path).

**And [tools/resplit_sections.py](../tools/resplit_sections.py) answered by
rewriting 46 tracked practice files.** Its default action was to WRITE:
any argument it did not recognise fell through to the write branch, so
`--help` silently reverted every edit made to `practices/*.md` since the
phase-1.5 editorial split — slug links back to numeric citations, later
Story paragraphs gone — with no confirmation and no diff. The damage
surfaced two steps later as an apparently unrelated `doc_sync` DRIFT, which
is exactly how a destructive default hides. A spent one-shot migration tool
sitting in `tools/` must have its safe mode be the one you get by accident.

Fixed: every tool answers `--help` with its module docstring and exit 0;
`resplit_sections` writes only on an explicit `--write`, refuses an
unrecognised argument outright, and states in every mode that it is spent
and that its `--check` reporting drift is the expected condition, not a
gate to turn green. `check_tools_answer_help_without_writing` in
[tools/verify_harness.py](../tools/verify_harness.py) now asserts all three
properties — answered, non-empty, and writes nothing — against a throwaway
copy of the tracked tree, because a check for "does this tool clobber the
repo" must not be able to clobber the repo while finding out. Its negative
control, the pre-fix `resplit_sections` default restored, reports the 46
files and leaves the real tree untouched.

### Seven tools crashed instead of degrading

Sweeping every tool against a directory that is a git repository with no
commits and none of the repo's own files — the shape of a partial vendor,
and of a consumer that has not instantiated its templates yet — produced
seven raw tracebacks. Three are in **vendored engine files**, so they reach
consuming repos: [precedent_gate.py](../tools/precedent_gate.py) on a
missing `routing_scope.json`, [build_views.py](../tools/build_views.py) on
an `AGENTS.md` not yet instantiated, and
[doc_sync.py](../tools/doc_sync.py) on a `PAIRS` entry whose document was
renamed away. The other four are this repo's own
(`behavioral_replay`, `doc_html`, `resplit_sections`, and a second
`doc_sync` site). Each now exits with a message naming the missing thing
*and the remedy*; `behavioral_replay` folds "no commits at all" into the
DEGRADED path it already had for a shallow clone, which is the same fact
further along the same axis.

### `doc_sync`'s restatement scan failed open

[tools/doc_sync.py](../tools/doc_sync.py)'s `owned_figures()` caught every
exception from importing the script it reads and returned `[]` — making a
crashing emitter indistinguishable from a deliberate opt-out, so the
restatement scan examined nothing and the gate printed green. That is this
repository's own recurring failure shape, an empty result reading as
"clean" rather than as "could not check". An import failure now fails the
gate with the traceback attached to the document it could not scan.

### Half-bootstrapped individual sources were reported as "no individual set"

[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s self-heal
fired only when the user config file was entirely absent. A hook killed
part-way — which is what a failing `git clone` actually leaves — produces
two other states: a config with no `individual` entry, and an entry whose
declared clone directory was never created. Both read as "this person has
no individual set", permanently. All three now trigger the one self-heal
attempt, and a source that is *declared* but still unusable afterwards is
kept in the list so `load_source()` reports the real reason, rather than
vanishing into the same silence.

### The single-branch clone repair now applies itself

The refspec half of the `add_repo` workaround
([AGENTS.md](../AGENTS.md)'s gotchas) is no longer a manual recipe:
[.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) and
[templates/bootstrap.sh](../templates/bootstrap.sh) widen
`remote.origin.fetch` at session start when it carries no `refs/heads/*`
mapping, before the freshness block runs. Verified against a real
`--single-branch` clone: pushing a feature branch from one left
`git rev-list origin/feature..HEAD` unable to resolve at all, and the
repair plus one fetch made it answer `0`. The clone-URL capitalization half
stays manual — nothing local knows the canonical spelling.

### Both install paths, re-walked end to end

`INSTALL.md` §0 (loader) and §1 (classic vendoring) were both walked
against the current engine, not read. §0: vendor the catalogue, seed the
engine with `precedent_vendor_engine.py seed --kind consumer`, declare
sources, instantiate the templates, sync — the deep check on the result
comes back **15 passed, 0 violated**, matching what the section claims. §1:
vendor into `process/upstream/`, instantiate, write the manifest, scrub
blocklist, `practice_audit.py --update-baseline` then a bare run — **OK, 0
pending export, 0 warnings**, and `checkin.py fresh` correctly reports
upstream movement now that it compares full hashes rather than a short hash
against a long one. §1 step 1 now says to skip [evals/](../evals/), which
is 557 of the 784 files a consumer was vendoring and which nothing a
consumer runs reads.

### Every source-supplied check, read

Sixteen check scripts across three sources (nine team, six individual, one
repo-local). Asked of each: what it scans, whether its findings can be
acted on where it runs, and whether it has a two-direction test.

- **Fourteen of sixteen crashed when the practice file they quote is
  absent.** All fourteen shared a byte-identical `rule_text()` whose
  `read_text` was unguarded, so the violation was correctly detected,
  correctly printed, and then buried under a `FileNotFoundError` raised
  from inside the violation *printer*. A materialized check runs in
  whatever repo its source was resolved into, where the practice file is
  not guaranteed to be present. Fixed in both private sets; both test
  suites still pass.
- **The one check with no test now has one.**
  `check_merge_target_is_beta_branch.py` (repo-local) gained a
  four-direction test: fires when `origin/precedent-beta-v01` is an
  ancestor of `origin/main`, stays clean when they have diverged, exits 2
  (SKIPPED) when either ref is missing, and is clean on the real repo.
  Fixtures rather than the real tree, since direction 1 asserts a condition
  that must never be true here.
- **The team's nine checks do not run in this repo, and that is a real
  gap, not a bug.** `precedent.json` declares
  `precedent-team-maintainers` as an in-force team source, but
  `register_materialized_checks()` can only reach scripts that were
  materialized into `tools/checks/` — and Precedent never materializes,
  because `build_views.py` deliberately stays single-source here. Run by
  hand against this tree, six of the nine report violations, and reading
  them is what settles whether wiring them in would be an improvement:
  `no-stale-counts` fires on every historical figure inside a dated plan or
  eval record; `private-repo-scrub` fires on universal practices naming the
  private repos that are their own reference implementations;
  `session-trailer` fires on the entire commit history, which
  `no-rewrite-for-warnings` forbids ever fixing. Those findings are not
  actionable here, and a check whose findings cannot be acted on where it
  runs is the shape this project already refuses. `header-caps` and
  `light-check` do produce real, actionable findings about this repo's own
  documents — recorded here rather than swept, since acting on them is an
  editorial pass, not a mechanical one.

### The judgment-only sweep, partially done

[TODO.md's `sweep-judgment-only-practices` item](../TODO.md#sweep-judgment-only-practices)
is a 52-practice sweep the item itself frames as bounded only by session
budget. This pass took the slice with mechanically testable cores rather
than stopping at the first practice and running out:

- **`fail-gracefully`** — swept properly, seven real fixes (above).
- **`durable-list-anchors`** — a real violation, fixed. `TODO.md`'s
  twenty-two items were cited from three other documents as "item N" while
  carrying no anchors, so any insertion or strike-through silently
  repointed every citation. All twenty-two now carry `<a id="...">` slugs,
  the four number-based citations are repointed, and the file states the
  convention at the top.
- **`branch-links`, `rule-links`, `blank-blocklist`, `install`,
  `quiet-checks`, `registry-source-of-truth`** — checked, clean. The
  bare `` `main` `` mentions in the team set's `default-branch.md` are the
  branch *name* in a rule about any repo, not a branch on a host that
  could be linked.
- **The remaining ≈45** are untouched. Most are moment-of-work practices
  (`quote-discipline`, `verify-decomposition`, `name-both-sides-of-ledger`)
  with no standing repo state to sweep, or editorial ones
  (`trim-prose`, `proportional-emphasis`, `list-item-parity`) that need a
  reader rather than a script.

### The committed HTML render was stale, and nothing checked it

Found by accident, which is the point: the tools-that-write sweep ran
[tools/doc_html.py](../tools/doc_html.py) bare, and the regenerated
[spec/PREFORK_AUDIT.html](PREFORK_AUDIT.html) came back with a whole
paragraph the source had gained and the render had never been rebuilt for.
`generated-artifact-provenance` holds that property for the generated
*views* (`MAP.md`, `GLOSSARY.md`, `AGENTS.md`'s block) and does not reach
the rendered ones. A stale render is the worse artifact of the two: it
looks current, it is linked as the readable view of the document, and it
disagrees with it silently. `check_rendered_docs_are_current` in
[tools/verify_harness.py](../tools/verify_harness.py) now rebuilds every
document in `doc_html.py`'s own registry into a scratch directory and
compares, ignoring only the build stamp, which is the one line that
legitimately differs every run. Its negative control is the render as it
was committed before this pass: reported stale.

### What only a consuming repo could show

Three findings that this repo's own green could not have produced, found by
taking the refreshed engine into the two real consumer repos
rather than stopping at a clean local run:

- **`--help` that runs the tool passed every property the new check
  asserted.** `build_views.py`, `build_codeowners.py` and
  `practice_audit.py` ignored the flag entirely and ran their normal job,
  exiting 0 with output. `build_views.py`'s normal job is regenerating
  `MAP.md`, `GLOSSARY.md` and `AGENTS.md`'s block — so `--help` silently
  rewrote all three, and because they are already current here, even the
  "writes nothing" property held: an identical rewrite is invisible to a
  hash. In a consuming repo, whose views can be drifted, the same command
  would have rewritten them. The check now compares the output against the
  tool's own module docstring, so running the tool can no longer pass as
  answering.
- **A vendored `doc_sync.py` carries upstream's `PAIRS`.** It names
  documents the consumer does not have and scripts it never vendored. That
  used to crash; after the graceful-failure fix it reported four findings a
  consumer could only clear by editing a vendored file. Now: *none* of the
  registered documents existing is an unconfigured copy, reported NOT
  APPLICABLE with the remedy, while *some* missing stays a genuinely stale
  registry. The orphan-sentinel scan also stops walking `process/upstream/`,
  whose generated blocks belong to the upstream's registry.
- **Sixteen dead links in the two practice-set skeleton READMEs**, invisible
  here because `doc_lint` gates on changed files and nobody had touched
  those READMEs since the links were written. A consuming repo's light check
  walks the whole vendored tree and reported all sixteen — an upstream
  defect surfaced to the one reader who cannot fix it. Both are the first
  document an adopter of a new set reads.

## Rules in force that nothing can load

Raised by Morgan on 2026-09-06, reading the note above about `evals/` being
71% of the vendored tree: *"does that mean you delete rules that weren't
active? We would still need the rules! The thing to fix is, what can you do to
make sure they are wired in and referenced and used, and not sitting there in
vain."*

**On `evals/` specifically, no: nothing there is a rule.** It is the
routing-quality measurement corpus — the fixtures behind
[spec/LOADER.md](LOADER.md)'s recall and precision figures — and it answers a
question about *building* Precedent, not about using it. Every file under
`practices/` still vendors, at every level. The figures are no longer typed
into prose either; `python3 tools/checkin.py not-vendored` measures the share
against the tree in front of you, because the frozen ones in that comment were
stale within a day.

**But the underlying question was the right one to ask, and the answer here
was worse than expected.**

### What was measured

`precedent.json` declares three sources in force in this repo — universal,
`precedent-team-maintainers`, and the repo-local set — and the user-level
config adds `precedent-individual`. Together they put **114 practices in
force**. Of those, **43 are reachable by no loading channel at all**: not in
the resident block, not in the occasion index, no gate, and no check this repo
can run. 34 team, 9 individual.

Two mechanisms produce that, both deliberate in isolation:

- `build_views.py` **stays single-source here on purpose** — `precedent.json`'s
  own comment says so — so this repo's `AGENTS.md` carries the universal
  catalogue and nothing else.
- `register_materialized_checks()` can only reach check scripts that were
  *materialized* into `tools/checks/`, and Precedent cannot materialize into
  itself (its `practices/` **is** the universal source).

So the config says 114 practices bind work here, and the loader shows 71. A
rule nothing can load is not in force; it is filed.

### The mechanism now in place

`layered-practice-packs` gained a mechanical check
([tools/precedent_check.py](../tools/precedent_check.py)): for every practice
in force, assert at least one channel reaches it here, and name the ones where
none does. A source that does not resolve in the current environment is
skipped, never reported — a team source is a sibling clone and an individual
source resolves through a private user-level config, so neither exists in a
bare CI checkout.

It is **advisory**, to the bar this project sets for that, and the reason is
the finding below rather than squeamishness.

### Why "just turn them all on" is the wrong fix, with evidence

The 15 source-supplied checks were run against this tree — possible for the
first time, since they now honor `PRECEDENT_CHECK_ROOT` (see the root-cause
section below). Five pass. The other ten split cleanly, and the split is the
point:

| Verdict | Checks | What it means |
|---|---|---|
| Passes here | `default-branch`, `derived-file-marker`, `draft-marker`, `assorted-notes`, `my-identity-is-not-private` | The practice binds this repo and this repo satisfies it. Wire in, free. |
| Real, actionable finding | `header-caps`, `light-check`, `no-stale-counts`, `file-header` | The practice binds this repo and this repo violates it. Wire in, then fix. |
| Cannot be acted on here | `commit-author`, `buenos-aires-dates`, `claude-web-bootstrap`, `session-trailer`, `deep-check`, `private-repo-scrub` | The practice is about a *different kind of repository* — a repo one person authors alone, or the team set's own shipped content. `session-trailer` wants a trailer on every commit in a history `no-rewrite-for-warnings` forbids rewriting. |

That last row is why the check reports rather than fails. **The system has no
way to say "this source is in force, but this practice does not bind this
repo."** Silence is currently doing that job, which is exactly why 43 rules
sit unreachable and nobody can tell the deliberate cases from the forgotten
ones. Adding that vocabulary is a design change, not a fix, and it is
[TODO.md's `unreachable-practices` item](../TODO.md#unreachable-practices).

### Root cause of the fourteen crashing checks, and the fix

The earlier pass fixed the crash. This one found why the practice files were
absent in the first place, which is the part that would otherwise recur.

Every check derived one `ROOT` from its own location and used it for **two
different questions**: *what repository do I audit* and *where does my own rule
text live*. Those coincide in both normal cases — a check run inside its own
set, and a check materialized into a consuming repo, where
`precedent_materialize.py` writes `practices/` and `tools/checks/` side by
side. They come apart in the third case: a repo that **declares** a source and
never materializes it. Precedent's own repo is exactly that, so
`parents[2]/practices/` resolved to a catalogue the practice was never in.

Split, in all sixteen checks: `SOURCE_ROOT` (the set the script ships in, where
its rule text always is) and `ROOT` (the repo audited, overridable via
`PRECEDENT_CHECK_ROOT`). The rule text can no longer be absent, and a repo that
declares a source without materializing it can now point that source's checks
at itself — which is what made the table above measurable.

`check_deep_check.py` now asserts the split across the whole family, with three
negative controls. That matters more than the fix: these scripts are written by
copying the last one, so a property nothing checks propagates by copy — which
is precisely how one bad line reached fourteen files.

## The judgment-only sweep, round two

Continuing [TODO.md's `sweep-judgment-only-practices` item](../TODO.md#sweep-judgment-only-practices).
Nineteen of the fifty-one judgment-only practices have now been judged with
the closed question [practices/full-practice-audit.md](../practices/full-practice-audit.md)
names — *does this apply; if so, is it satisfied, with the specific file* —
against the actual state of all six repos.

### Violations found and fixed

- **`automation-issues`** — `the project's own prior notes repository`'s `voice-guidelines-sync.yml` is a
  scheduled unattended job with two blockers (a missing private-source token,
  a missing Claude credential) and reported both on a CI annotation only.
  Its sibling `bestpractice-upstream-sync.yml` has opened a tracked issue for
  the same class of blocker since it was written; this workflow was created by
  copying that one and the issue-reporting half was not carried across. Both
  blockers now open or update an issue. **Nobody reads the Actions tab of a
  job that is supposed to be quiet** — which is exactly the job whose silence
  means something is wrong.
- **`match-parsed-id-not-prefix`** — `verify_harness.py`'s own fixture helper
  located candidate files with `glob(f'{slug}-*.md')`: the exact
  prefix-matching bug this practice exists to stop, sitting inside the helper
  that builds that practice's own regression case. The call site there had
  been hand-narrowed to `'-2*.md'` to work around it, which is the workaround
  that names the defect. It matches on each file's parsed slug now — **and the
  case's two fixtures were reordered**, because a control run showed the old
  prefix glob still passed: created short-then-long it returns the right file
  by luck. Long-then-short, reverting the helper fails. The case existed and
  proved nothing until this pass.

### Clean, or not applicable, with the reason

| Practice | Verdict |
|---|---|
| `bestpractice-sync` | Satisfied where it applies — both vendoring consumers run a scheduled sync workflow. Not applicable in Precedent's own repo, which vendors nothing. |
| `pack-sync` | Not applicable. Both consumers resolve the team source as a **live sibling clone**, never vendored, so there is no vendored copy to drift. |
| `drift-notice` | Satisfied — both consumers' `tools/bootstrap.sh` compares each vendored source's recorded commit against its head at session start. |
| `fresh-check-escalation` | Satisfied — `checkin.py` prints a distinct `COULD NOT VERIFY` line for a clean failure rather than folding it into silence. |
| `brainstorm-citations` | Not applicable — no brainstorm document in any of these repos. |
| `content-directory`, `content-subdirs` | Not applicable. Both defer explicitly to a repo's established layout, and this one has `spec/`, `tools/`, `practices/`, `templates/`. |
| `doc-recipe` | Not applicable — no recipe documents. |
| `no-duplication` | Clean. No slug appears at two levels; the one cross-level relationship (`rule-links` over `doc-references-are-links`) is a declared `overrides:`, which the practice permits by name. |
| `branch-links`, `rule-links`, `blank-blocklist`, `install`, `quiet-checks`, `registry-source-of-truth` | Judged clean in round one. |

**Roughly thirty-two remain**, mostly moment-of-work practices with no
standing repo state to sweep and editorial ones that need a reader rather
than a script.

### Two defects this round found that no practice pointed at

Both surfaced from *doing* the sweep rather than from any rule in it, which is
the argument for the sweep being a read of real state rather than a checklist.

- **`checkin.py update <clone>` checked out and pulled inside the clone it was
  handed.** Run from a consumer, it moved this session's Precedent checkout
  off `precedent-beta-v01` onto `main`, mid-session, after its own guard had
  already refused the operation. Fixed to read the source ref with `git
  archive` — the guarantee `precedent_vendor_engine.py` already made
  explicitly — and to mirror the branch the consumer's manifest records
  instead of the clone's configured default, which would have reverted a
  beta-vendored tree to `main` wholesale. Both are harness cases now, with
  negative controls; the incident is in [AGENTS.md](../AGENTS.md)'s gotchas,
  because the symptom (files vanishing from a tree you were just working in)
  reads exactly like someone else deleting real work.
- **An engine refresh could move past the catalogue it runs against, silently.**
  `refresh` updates the engine only, by design. The cost was a skew nobody was
  told about: engine code citing a practice slug the vendored catalogue
  predates, surfacing later as a check calling a real practice "not a real
  practice" in vendored code the consumer may not edit. `refresh` now reports
  it — on the already-current path too, which is the case that matters most,
  since "nothing to do" is what a session would otherwise read as "both halves
  current."

## The judgment-only sweep, round three — the catalogue is now swept

All 51 judgment-only practices have been judged with the closed question
[practices/full-practice-audit.md](../practices/full-practice-audit.md)
names, against the real state of all six repos. This round took the
remaining 32.

### Violations found and fixed

- **`lead-with-what-it-is`** — [README.md](../README.md), the repository's own
  entry document, opened with a block quote about *the branch state and the
  restructuring process*. A reader learned how the project is maintained
  before learning what it is; "what Precedent is" appeared only as a link,
  eleven lines down. It now opens with a plain-language paragraph saying what
  Precedent does, before any maintenance bookkeeping.
- **`bold-key-phrases`** — [documentation/WHAT_IS_THIS_AND_BENEFITS.md](../documentation/WHAT_IS_THIS_AND_BENEFITS.md)
  carried **0.1 bold spans per 100 words** against 0.8–1.9 in every other
  outward-facing document, and it is the pitch page: the single most
  skim-driven thing here, aimed at people outside the project. Seventeen key
  phrases now carry the emphasis, roughly one spine point per section.
- **`volatile-rules-carry-dates`** — [GITHUB_ACTIONS.md](../GITHUB_ACTIONS.md)
  contained **no date anywhere**, while its entire framing rests on two
  claims about what a GitHub-connected ChatGPT conversation can and cannot do.
  Both now carry *as of 2026-08* and point at [MOBILE.md](../MOBILE.md), which
  tracks that capability and is where it gets re-dated.
- **`resolved-issue-note-updates`** — violated by this session, hours earlier.
  [spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)'s
  step 1 still said `checkin.py`'s commands *cannot* track a named branch,
  pointing at a section this session had already rewritten to say the
  opposite. Fixing the section and leaving its own pointer stale is exactly
  what this practice forbids.

### The defect the sweep found that no practice pointed at

**`tools/title_case.py --write` had corrupted committed content**, and would
have gone on doing it. Its docstring promised fenced code blocks were safe;
**inline code spans were not** — and a heading is precisely where a document
names a file. [INSTALL.md](../INSTALL.md)'s own section headings had been
rewritten to `` `Process/manifest.json` `` and `` `Tools/practice_audit.py` ``,
neither of which exists. The negative control showed the reach was wider than
the two paths found: `` `git rev-parse --verify` `` becomes
`` `Git Rev-Parse --Verify` ``, so any command in any heading was exposed.

A second bug in the same run left `## 5. the Manifest Schema` lowercase,
because `5.` counted as token zero and headline style capitalizes the first
*word*, not the first token.

Both fixed, the corrupted paths restored by hand — the corrected tool
correctly will not touch them, so it could not undo its own damage — and
`check_title_case_leaves_code_and_first_word_alone` now asserts five cases
with a control for each bug. **A tool that rewrites committed prose in place
needs its blast radius asserted, not described.**

### Clean, or not applicable, with the reason

| Practice | Verdict |
|---|---|
| `llm-neutral` | Not applicable. Nothing here calls a model API — no completion call in any tool or workflow. The consumers' sync workflows invoke Claude Code *as an agent*, which is a product invocation with no provider-neutral equivalent, not a swappable model endpoint. |
| `frame-from-audience-question` | Satisfied, visibly: all three `documentation/` files open by stating the reader's question outright, and [ADOPTING.md](../ADOPTING.md) frames by audience in prose. |
| `one-formatter-per-quantity` | Clean. [tools/table_fmt.py](../tools/table_fmt.py) is the declared module, and every generated table in a document comes from exactly one emitter — which `doc_sync`'s `PAIRS` structurally enforces. |
| `tabular-shared-renderer` | Clean. The one multi-column sortable table ([spec/PREFORK_AUDIT.md](PREFORK_AUDIT.md), 5×53) ships its render. `templates/harness/LEDGER.md` is an append-only record read in chronological order, not a comparison matrix. |
| `sensitive-characterization-scrub` | Clean. Two lines name a person near a negative word; one credits Morgan's framing as the correction, the other describes a commit. Nothing anyone would wince at. |
| `readers-vocabulary` | Clean. One unglossed term ("gate") across five outward documents, in a sentence that explains it. |
| `pr-template-honest-gates`, `full-practice-audit`, `very-deep-check` | Satisfied — template present with its gates; both audit engines exist, run, and answer `--help`. |
| `list-item-parity` | Clean. Worst spread is a 3-item list at 2.4× (5–12 words) — inside "approximately the same length". |
| `nonblocking-questions`, `push-back`, `small-calls`, `affordance-is-shared` | Satisfied by this session's own conduct: work continued while a question was open, the counter-case was made before the more permissive option was recommended against, the one stop was a genuinely reserved-category call, and each mechanism built here recorded who else it serves. |
| `permutation-frontier-column`, `name-both-sides-of-ledger`, `build-buy-decompose`, `check-source-architecture`, `variant-re-derives`, `verify-decomposition`, `quote-discipline`, `outward-summary-discipline`, `rule-scope-ask`, `new-rule-placement` | Not applicable. Moment-of-work practices with no standing repo state: no sweep table, no two-party ledger, no build/buy question, no variant, no computed total in flight, no figure quoted from an outside source, no outward document making a quantitative claim, no rule of ambiguous scope proposed. |
| `list-restraint`, `proportional-emphasis`, `trim-prose`, `section-order-by-frequency` | Editorial judgments with no mechanical signature. `section-order-by-frequency` keeps the earlier verdict: `INSTALL.md`'s 1, 0, 2 ordering explains itself in the document. |

## The loader block now renders every declared source — except a private one in a public repo

Part A of [TODO.md's `unreachable-practices` item](../TODO.md#unreachable-practices),
done 2026-09-06 at Morgan's direction. **The engine change landed; here it is
deliberately switched off, and the reason is the more useful half of this
entry.**

### What was actually wrong

Not a missing instruction *in* [AGENTS.md](../AGENTS.md) — `AGENTS.md` is the
output. The chain ran: [precedent.json](../precedent.json) declared three
sources (**correct**), [tools/precedent_resolve.py](../tools/precedent_resolve.py)
found all of them (**correct**), and [tools/build_views.py](../tools/build_views.py)
rendered the loader block from this repo's own `practices/` alone. So **65 of
65 universal practices reached the block, 0 of 41 team, 0 of 11 individual,
and 0 of 1 repo-local.** The config said they were in force; the one artifact
a session reads listed none of them.

The declaration was right and the rendering was incomplete — one layer above
the file anyone would naturally go and edit, and unfixable by editing it,
since the block is overwritten on every regeneration.

### Why it could not just use the consumer path

A consuming repo gets multi-source through
[tools/precedent_sync_views.py](../tools/precedent_sync_views.py), which
materializes every source into one `practices/` tree and leaves a
`MANIFEST.json` behind. Precedent itself cannot: its `practices/` **is** the
universal source (`path: "."`), and
[tools/precedent_materialize.py](../tools/precedent_materialize.py) refuses a
self-referential source by name, since its output directory would be that
source's only copy. So the sources are resolved **in memory** — same resolver,
same precedence, nothing written to disk.

### The constraint that decides the shape: this repo is public

The block is a **tracked file**. In a world-readable repository, whatever it
contains is published, permanently. Universal and repo-local sources are
already public — one is this repo, the other lives in its own tree. **Team and
individual sets are private repositories whose practice text has never been
published**, so rendering their clauses into `AGENTS.md` is publication by a
different door. [tools/precedent_resolve.py](../tools/precedent_resolve.py)
already refuses to let a shared repo *declare* an individual source, because
naming it "leaks its existence and location"; this is the same disclosure.

[decisions/2026-09-06-precedent-binds-itself.md](../decisions/2026-09-06-precedent-binds-itself.md)
section 2 rejected multi-source generated views **here** on exactly that
ground, and built `not_binding` instead. That record and this work were done
the same day in parallel sessions, and reconciling them is what this entry
settles: they are not competing answers.

- **The multi-source loader block is the right behaviour in any repo that
  declares more than one source and cannot materialize them.** That is the
  engine change.
- **`not_binding` is the right mechanism for this repo**, because the reason
  a rule goes unloaded here is not that the rendering is wrong.

**Correction, made after the rollout rather than before it.** The first
version of this entry said consumers were where the miss actually bit. They
were not. A consuming repo merges its sources through
[tools/precedent_sync_views.py](../tools/precedent_sync_views.py) and
materialize into one `practices/` tree *before* `build_views.py` sees it, so
every consumer's block was already fully multi-source — checked directly
against two of them, whose blocks carried their team and individual practices
before any of this landed and were unchanged by the refresh apart from one
wording fix. **The gap was Precedent's own repository and nowhere else**,
precisely because it is the one repo that cannot materialize. The claim was
written from the mechanism rather than from a measurement, which is the
failure this whole audit exists to catch; it is corrected here rather than
quietly dropped.

**What is still open here is neither of those.** Thirty-four team practices
genuinely bind this repository and cannot reach its published block — so
`not_binding` would be a false statement about them, and publishing them is a
one-way door. That question is Morgan's, and it is named in the TODO item
rather than answered by a session picking one.

### Two guards that came with the engine change

- **A public repo renders no private-level source into its tracked block.**
  A repo says which it is with `"visibility": "public"` in
  [precedent.json](../precedent.json); absent the field nothing is excluded,
  which is the right default, because the repos that most need the
  multi-source block are the private consumers. Asserted in
  [tools/verify_harness.py](../tools/verify_harness.py), because a regression
  here publishes a private set silently.
- **An unreachable declared source makes the block NOT VERIFIABLE, not
  stale.** A team source is a sibling clone and an individual source resolves
  through a private user-level config; neither exists in a bare continuous-integration
  checkout, and the committed block was built where they did. Regenerating
  without them and calling the difference "drift" would fail every run on
  evidence the environment could not have — which is exactly what the
  harness's own fixtures reported the moment this went multi-source.
  `--check` now says so and exits 0; a **write** refuses outright, since
  writing a block from an incomplete source set would silently drop every
  practice the missing sources contribute.

### What moved, in this repo

| | before | after |
|---|---|---|
| universal in the block | 65 of 65 | 65 of 65 |
| repo-local in the block | **0 of 1** | **1 of 1** — `merge-target-is-beta-branch`, this repo's sharpest temporary rule, was reachable by no channel |
| team in the block | 0 of 41 | 0 of 41 — now *by design*, and stated |
| individual in the block | 0 of 11 | 0 of 11 — now *by design*, and stated |
| practices reachable by no channel | 35 | 34, all team-level |
| resident block | 6 practices, ≈312 tokens | unchanged |

Measured with the team set as a sibling clone; the individual set did not
resolve in this environment, so its count is carried from the earlier run and
is not re-verified here.

`MAP.md` and `GLOSSARY.md` stay single-source in **every** repo, public or
not: they document the catalogue a repo publishes, not the rules it happens to
follow.

### What the intermediate state showed, before the privacy guard widened

Rendering the team set into this repo's block was built and measured first,
and the figures are worth keeping because they say what the engine does in a
private consumer: team went **0 of 41 → 38 of 41** (two retired, one
overridden), the resident block went from 6 practices to 9 (≈312 → ≈560 of
the 2,000 budget), and the whole block went ≈2,650 → ≈4,330 tokens.
**≈+1,700 tokens per session** is the real cost of a fully-loaded
multi-source block, accepted at Morgan's direction and left for a later pass
to reduce.

### Two bugs in the new check, both found by running it

The reachability check matched slugs with a pattern requiring a hyphen, so the
single-word slug `install` could never be found and was reported unreachable
forever — while loosening the pattern would have matched the ordinary English
word "install" anywhere in the file and called it reachable with nothing
indexing it. It now reads the two shapes the block actually uses. And the
individual practices a public repo deliberately excludes were being reported
as gaps every run; permanent findings nobody can act on is how an advisory
becomes wallpaper, so they are counted and named rather than listed.

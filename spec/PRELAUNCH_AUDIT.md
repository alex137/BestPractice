<!-- Last updated: 2026-09-06 by the pre-launch audit session -->

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
   fixtures — `themorgan/HavrutaBrainstorm`, a four-source install whose
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
   `themorgan/WorkingWithAI` is. An individual source's links are now left
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
9. **TODO.md item 11 still needs a live session**: whether
   `additionalContext` reaches the model or only the transcript. The test
   plan is written; it needs a real Claude Code session with the adapter
   installed. Now cheaper to run than it was: this repo installs the hook
   itself as of today, so the next session here is the test.
10. **The design half of TODO.md item 7**: whether a consuming repo should
   be able to express a preference between two team sources at all, rather
   than being told to rename one. The silent-failure half is closed; the
   design question is untouched, and a second team set now exists to test
   any answer against.

### For Morgan — found by running the two real consumer repos, his call

These are decisions about his own repositories, not defects in Precedent,
so this session reported them rather than acting on them.

- **`themorgan/WorkingWithAI` is public and names the private individual
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
  That is how `WorkingWithAI` ended up with three root copies OLDER than
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

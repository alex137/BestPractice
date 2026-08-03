# The practice catalog

Each practice: the **rule**, **why** (the abstracted incident that motivated
it — every one of these was learned the expensive way in a real repo), and
**install** (what a dependent repo does about it). Templates referenced here
live in `templates/`; tools in `tools/`.

## 1. The repo is the memory; sessions are ephemeral

**Rule.** Everything a future session needs — orientation, open items,
decisions, lessons — lives in committed files. A session's chat thread is
disposable; if knowledge exists only in a thread, it is already lost.

**Why.** Agent sessions (and humans returning after a month) start cold.
Repos that kept context in threads paid a re-derivation tax every session —
re-finding files, re-learning environment quirks, re-making settled decisions.

**Install.** The three living documents below (MAP, TODO, GLOSSARY) plus a
project instructions file (`AGENTS.md`, plus a per-harness pointer file —
see practice 13). Everything else in this
catalog is a refinement of this rule.

## 2. An orientation map, read first

**Rule.** A top-level `MAP.md` indexes the repo: what the key deliverables
are, where everything lives, and — crucially — which supporting documents back
each part of each deliverable. Every session reads it before doing anything.

**Why.** Without a map, every session greps. With one, orientation is one
file read, and "which documents back this section of the deliverable?" has a
committed answer instead of a fresh investigation.

**Install.** [templates/MAP.md.template](templates/MAP.md.template). Keep the
deliverable→backing-docs index current: any thread that adds a document adds
its row.

## 3. A quick index before searching

**Rule.** The project instructions file carries a "check here BEFORE searching
the repo" table: *looking for X → go to Y*, one row per thing sessions
actually hunt for.

**Why.** The map orients top-down; the quick index answers the specific
lookups that recur ("where are the canonical names?", "which script builds the
deliverable?"). Rows are added exactly when a session is observed searching
for something — the index is built from real misses, not speculation.

**Install.** Part of
[templates/AGENTS.md.template](templates/AGENTS.md.template).

## 4. Recorded lore: environment gotchas with their stories

**Rule.** Every expensive environment discovery (a package that must be
installed, a tool that silently doesn't work, a path that does work) is
written into a "do NOT rediscover these" section — with the story of what
failed and why, not just the fix.

**Why.** A build tool once failed on every input with a misleading error; two
full sessions were lost to "this tool is broken" lore before someone found the
one missing package. Once the fix *and the story* were written down, the
failure never recurred — and the story is what lets a future session judge
whether the note still applies.

**Install.** A gotchas section in the instructions file
([templates/AGENTS.md.template](templates/AGENTS.md.template)), plus practice
13 (encode the fixes as a bootstrap hook so they apply themselves).

## 5. Conventions cite the incident that created them

**Rule.** When you write a rule, record what failure it prevents, inline.

**Why.** "Do X" invites relitigation and misapplication; "do X — we once lost
Y because Z" sticks, and lets a reader judge whether the rule applies to their
case. Rules without origin stories decay into cargo cult or get dropped.

**Install.** A writing habit, not a file. Enforced socially by example: every
rule in the instructions file carries its story.

## 6. A convention violated once becomes an audit that fails loudly

**Rule.** Prose rules are advisory; a non-zero exit is not. The first time a
convention is violated with real cost, promote it to a script that detects the
violation and fails the build/merge — and keep the origin story in the
script's docstring.

**Why.** Every audit in the originating repo exists because its rule was
broken once despite being written down: a status flag not flipped caused a
generated bundle to silently drop updated content; a renumbering left stale
cross-references undetected for weeks; a markdown footgun garbled an external
document. None recurred after promotion to an audit. The binding layer
matters as much as the check: a gate that lives only in a merge runbook
binds only the sessions that run the runbook — a PR merged through the
hosting platform's web UI skips it entirely (a dependent repo's first
member merges bypassed the capture and export gates exactly this way,
2026-08). A required CI check ([GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)) is
the form that binds every path to the default branch.

**Install.** [tools/doc_lint.py](tools/doc_lint.py) and
[tools/practice_audit.py](tools/practice_audit.py) are audits of this kind
(and worked examples for writing your own). Run them before commit; wire them
into the merge runbook (practice 9).

## 7. State lives in one machine-readable registry; documents derive

**Rule.** Any status that scripts or sessions make decisions on (what's
released, what's pending, what version is installed) lives in exactly one
machine-readable registry. Human-readable documents restate it; they never
own it. When registry and document disagree, the registry wins — and an audit
(practice 6) detects the disagreement.

**Why.** Duplicated state always diverges. The worst version: a document
header said one thing, the registry said another, and a builder trusted the
registry while humans trusted the header. The fix was not "be careful" — it
was declaring the registry the single source of truth and auditing drift.
Corollary: **baseline snapshots** — record a content hash when state is
declared (released, synced, approved), and the audit flags any later change
to content whose status claims it is frozen.

**Install.** `process/manifest.json` (see [INSTALL.md](INSTALL.md)) is itself
a registry of this kind, with baseline hashes checked by
[tools/practice_audit.py](tools/practice_audit.py). Build your own registries
the same shape: entries + status + hash, one owner, one audit.

## 8. Provenance for generated artifacts

**Rule.** Generated deliverables are never hand-edited and never casually
committed. Each build stamps a **content-derived build code** into the
artifact itself and writes a **manifest** recording exactly which inputs (by
content hash) produced it. Outputs are gitignored and marked binary in
`.gitattributes`; only artifacts that actually shipped get committed
(force-added), alongside their manifest.

**Why.** Two builds minutes apart, with different content, once had to be
distinguished after the fact by spelunking git history. A content-derived
code on the artifact (same content → same code) plus a committed manifest
makes "what exactly shipped?" a lookup instead of an investigation.

**Install.** Pattern to apply in your builders; no portable tool (the code
stamping is builder-specific). The `.gitignore`/`.gitattributes` stanzas are
in [INSTALL.md](INSTALL.md).

## 9. A merge runbook with fixed per-file-class rules

**Rule.** When many branches touch the same shared files, merge conflicts are
expected — so resolution rules are written down per file class, once, and
followed without re-derivation: registries take the **union** of both sides;
logs are **append-only, keep both**; the same content file edited on both
sides keeps both sides' additions (renumbering the side not yet referenced
elsewhere); **generated outputs are never hand-merged** (the side matching
the committed manifest wins; unshipped builds are deleted and rebuilt). The
audits (practice 6) must pass before the merge commits — the audit, not
re-inspection, is what makes fast mechanical resolution safe.

**Why.** Every thread in the originating repo touched the same registry and
index files; conflicts were universal. Ad-hoc resolution was slow and once
dropped a registry entry. Fixed rules plus a loud audit made merges fast
*and* safer than careful manual resolution.

**Install.** Runbook section in
[templates/AGENTS.md.template](templates/AGENTS.md.template); adapt the file
classes to your repo.

## 10. Capture in the thread that created the need — before the merge

**Rule.** The thread that develops a capability, a number, a decision, or a
limit is the thread that understands what follow-on artifact it implies (a
document update, a registry entry, an exported practice, a decision record).
Capture it **in that thread, before merging** — as step 0 of the merge
runbook. Never park it in a "for later review" staging document.

**Why.** Deferred capture repeatedly lost both the rationale (the merging
thread didn't know why the matter existed) and the timestamp (priority went
to whoever wrote it down first). A "waiting for review" parking lot caused a
real miss: staged content sat unrecorded for a full cycle because its thread
ended without folding it in. The gate that fixed it: before any merge, ask
"did this thread's work imply anything that must be captured?" — and a grep
for known parking-lot markers, run at thread end.

**Install.** Step 0 of the runbook in
[templates/AGENTS.md.template](templates/AGENTS.md.template). The
practice-export gate (practice 14) is this same rule applied to process
improvements.

## 11. Document references are links; approximation is ≈

**Rule.** (a) In-repo documents reference other repo files as relative
markdown links, never bare backticked filenames — docs are read on a web UI
where a bare name is a dead end. New text always links; any thread touching a
document fixes the references in the parts it touches. (b) Use `≈` for
"approximately", never `~` — two stray tildes on a line render as
strikethrough on GitHub, silently garbling text. (c) Links stay plain
markdown — don't reach for a raw HTML anchor to control link behavior:
GitHub's sanitizer strips `target=` (and most other attributes) from
anchors in rendered markdown, so an "open in new tab" link silently does
nothing there (*as of 2026-08*).

**Why.** All born from real bugs: readers hunting for referenced files, an
outward-facing document that rendered with unintended strikethrough, and a
thread that spent two commits converting a link to a `target="_blank"`
anchor and reverting it once the rendered page proved the attribute was
stripped.

**Install.** [tools/doc_lint.py](tools/doc_lint.py) checks all three — it
gates on files changed vs the default branch (the "fix what you touch"
scope, which also protects frozen documents), `--all` reports the backlog,
`--fix` rewrites `~`→`≈` on struck lines; `target=` anchors are reported as
warnings. Requires `cmarkgfm` for exact detection with GitHub's own
renderer.

## 12. Every reply links the files it touched

**Rule.** A session's reply that created or modified files ends with a
"Files touched" list: each entry links the file on the working branch *and*
its post-merge location, with a one-line description. The reader must be able
to open the work from the chat, not merely learn it exists.

**Install.** Convention in
[templates/AGENTS.md.template](templates/AGENTS.md.template).

## 13. Session bootstrap is code, not memory

**Rule.** Environment setup that sessions need (packages, dependencies,
submodule init) lives in a session-start hook — idempotent, fast when cached,
warning loudly on failure. Routine safe commands the agent runs constantly go
in a permissions allowlist so sessions don't stall on prompts.

**Why.** The gotchas of practice 4, applied: writing the fix down is good;
having it apply itself is better. The hook is where "install the one package
whose absence cost two sessions" lives as code.

**Install.** [templates/bootstrap.sh](templates/bootstrap.sh) →
`tools/bootstrap.sh` (harness-neutral; all real setup lives here), wired in
per-harness via [templates/harness/](templates/harness/README.md): a hook
that runs it automatically where the harness supports one (hard guarantee),
an instructions-file directive where it doesn't (soft guarantee), plus a
permission allowlist where the harness has that concept.

## 14. The practice-export loop (how this repo propagates)

**Rule.** A dependent repo vendors this repo at `process/upstream/` as plain
tracked files (no submodule — zero runtime dependency, sessions never break
on a missing remote). Install is **adaptive** (generic → specific: an agent
instantiates templates with the repo's subject matter); therefore export is
**abstractive** (specific → generic), and the mapping is recorded in
`process/manifest.json` so neither direction relies on memory. The **export
gate**: before a thread ends, if it improved a generic practice, fold the
abstracted form into `process/upstream/` in the same branch.
**Periodically**, propose accumulated vendored changes back here as a PR.

**Why.** Live coupling (submodules read at session start) breaks sessions
exactly when orientation matters most, and makes capture (practice 10) a
cross-repo operation that gets skipped. Vendored-and-tracked makes the
export a local commit; the cross-repo step happens only at deliberate
check-ins.

**Install.** [INSTALL.md](INSTALL.md) is the full playbook;
[tools/practice_audit.py](tools/practice_audit.py) audits the manifest
(drift between installed files and their recorded baselines) on every run.

## 15. The proprietary scrub gate

**Rule.** When the dependent repo is private and this repo is public,
everything under `process/upstream/` must be public-safe **at all times** —
not just at check-in. Contributions are patterns and abstracted lessons
only: no names, code words, identifiers, numbers, or incident text from the
dependent repo's subject matter. Enforcement is mechanical: the dependent
repo keeps `process/scrub_blocklist.txt` (regex per line — its private
vocabulary), and [tools/practice_audit.py](tools/practice_audit.py) scans
the entire vendored tree against it on every run, failing loudly on any hit.
The blocklist itself is never exported (it is a map of the secrets). And a
public repo is **public from its first commit** — content is authored fresh
as public-safe, never migrated from private history, because visibility
flips expose everything a private repo ever casually committed.

**Why.** The abstraction step (practice 14) is a judgment call performed
repeatedly by agents under time pressure — exactly the conditions under
which practice 6 says a convention needs a loud audit. Public git history
cannot be un-published.

**Install.** Blocklist format and gate wiring in [INSTALL.md](INSTALL.md).
Scrub before every commit that touches `process/`; re-run at check-in time
before opening the upstream PR.

## 16. Volatile rules carry their dates

**Rule.** A rule whose truth depends on the outside world — the behavior of
an external platform, an algorithm someone else changes, a tool quirk, a
price — carries an inline date: *as of `<date>`* when adopted, updated to
*verified `<date>`* whenever a session reaffirms it still holds. Optionally
add a review-by cadence for rules in domains known to shift. Stable internal
conventions don't need this; their origin story (practice 5) is enough.

**Why.** Age means opposite things in different domains. A convention that
has survived years of internal use is battle-tested; a rule about an
external platform that has sat untouched for a year may describe a world
that no longer exists — teams whose whole craft is tracking a
constantly-retuned external algorithm learn this the hard way, and their
hardest-won rules decay the fastest. The date is what lets a reader apply
the right lens. And it must be **inline**: version control does timestamp
every line, but sessions read file *content*, not commit metadata — in a
repo-is-the-memory system, a date that isn't in the text effectively
doesn't exist for the session reading the rule.

Two corollaries. **Durable rules earn a record, not just a date:** for a
rule whose age is its authority, capture the tenure and the exception
history inline — *in effect since `<date>`; N exceptions in that time, each
under `<circumstances>`* — because that survival record is institutional
memory that otherwise lives only in people's heads, and it is exactly what
tells a reader how seriously to take the rule. **Rules about model behavior
are the most volatile class of all:** a rule that encodes "the agent's
model handles X this way — route/decide/format accordingly" breaks
silently when the model is upgraded under you, so it carries not just a
date but the model it was verified against — *verified `<date>` on
`<model>`* — and a model change is itself a re-verify trigger, not a wait
for symptoms.

**Install.** A writing habit with a natural audit extension (practice 6):
tag rules with a review-by date or a volatility marker and a small script
can flag overdue ones — the drift check's shape, applied to time instead of
content. The environment-gotchas section (practice 4) is the most
decay-prone rule set most repos have; date its entries first.

## 17. Acronyms are expanded, and a central glossary holds them

**Rule.** A domain-dense repo accumulates far more acronyms and coined terms
than any reader — human or agent — keeps in their head. So: (a) **expand an
acronym on first use** in a document — *long form (ACRONYM)* — and/or carry a
short **"Acronyms" note at the bottom** of a document that uses several; and
(b) keep **one central glossary file** as the living master list, so an
expansion is never re-derived from scratch. When a session uses a term that
isn't in the glossary, it adds it there in the same pass. Identifiers that
already have their own registry (a code table, a component index) are pointed
to, not duplicated.

**Why.** In a repo-is-the-memory system the reader arriving at a document is
usually *not* the person who wrote it and often has none of the surrounding
context — the exact case an acronym silently assumes. One undefined initialism
can make a paragraph unreadable, and the cost compounds: a suite with dozens
of coined two- and three-letter terms becomes navigable only to its authors,
which defeats the point of writing it down. The central list is the same
single-source-of-truth instinct as practice 7 — derive the expansion in one
place, reference it everywhere — and the bottom-of-document note is the local,
low-friction form for the reader who won't leave the page.

**Install.** A writing convention plus one living file (a `GLOSSARY.md` grouped
by theme, alphabetical within a group), and the natural audit extension
(practice 6) is built: [tools/doc_lint.py](tools/doc_lint.py) check 3 scans each
changed document for ALL-CAPS tokens absent from `GLOSSARY.md` — skipping ones
defined inline on the line (`long form (TOKEN)`) and a stoplist of common
words/units — and warns, the same "convention → loud check" shape as its
link/strikethrough checks. Warning-only and auto-disabled when the repo has no
`GLOSSARY.md`, so it never blocks a repo that hasn't adopted the practice.

## 18. Filenames have no version suffix; the VCS is the version

**Rule.** A new file is named for what it *is*, with no `_v1` / `_rev2` label —
the repository already versions every line, so a version number baked into the
filename is redundant at best and misleading at worst (it goes stale the moment
the file is edited without a rename). A numeric suffix earns its place only when
two versions must **coexist** and a reader has to tell them apart (a successor
kept beside its predecessor for history); then it is the *new* file that is
suffixed, not the old one retro-renamed. An existing suffixed backlog is left
alone — bulk-renaming breaks the very references (links, records) the names are
load-bearing for; drop the suffix only from a file already being moved for
another reason, fixing its references in the same pass.

**Why.** "`_v1`" is the classic redundant-with-VCS habit: it answers a question
the version-control history already answers, and unlike the history it does not
update itself — a `_v1` file edited fifty times still says `_v1`, so the label
actively lies. It also invites a rename on every real revision (churning the
references), or worse, a `_v2` copy that forks the file and splits its history.
Naming for identity instead keeps one stable handle per document and lets the
tool whose job is versioning do the versioning.

**Install.** A naming convention; no tooling needed. The one judgment call —
"do two versions genuinely need to coexist?" — is rare and deliberate, so it is
left to the author rather than a lint.

## 19. Computed numbers live in scripts; documents embed sync-gated generated blocks

**Rule.** When a document presents content that a script computes — a summary
table, a cost rollup, a comparison grid — the document region is wrapped in
invisible sentinels:

    <!--gen:NAME-->
    ...generated markdown...
    <!--/gen:NAME-->

the script gains an `--emit NAME` mode that prints exactly that block, and the
(document, block, script) triple is registered with a small sync tool
(`tools/doc_sync.py`). The bare tool run is a **drift gate** — it fails loudly
when the document's block no longer matches the script's output — and runs with
the repo's other pre-commit gates; `--write` regenerates the blocks in place.
Never hand-edit inside a generated block: the numbers live in the script, the
document is a render target.

**Why.** Derived numbers quoted in prose silently lag the source that computes
them. Nothing breaks; a human just has to *notice* the staleness — and in one
dependent repo a headline comparison table lagged the scripts behind it until
the repo owner had to ask "did you update the table?". The reminder itself was
the bug: consistency between a computing script and the documents quoting it is
exactly the kind of convention that must become an audit (practice 6), because
it is mechanical to check and embarrassing to miss. The sentinel form matters:
HTML comments render as nothing on hosted markdown, so the plumbing is
invisible to readers, and the block boundaries make regeneration deterministic
(no fuzzy matching against drifting prose).

**Install.** Copy `tools/doc_sync.py`; register pairs in its `PAIRS` list; wrap
the generated regions; give each computing script an `--emit` mode. Wire the
bare run into the same "run before committing" list as the other gates. Start
with whichever document has already bitten you — the one someone had to be
reminded to update.

Two extensions the tool enforces once pairs exist. **The provenance footer:**
every registered document ends with a `**Numbers by:**` footer naming each
script that feeds it (the tool fails on a missing footer or an unnamed
script) — so a reader of the rendered page always knows which code produced
the numbers, without opening the sync tool's registry. **Composition:** an
emitting script may import other computing scripts and re-emit their numbers
in a new arrangement (a per-product sheet drawing on several models); the
sync gate then flags every downstream document when any upstream script
changes — the dependency graph rides the registry for free.

## 20. Mistakes become rules: root-cause the miss, then encode the prevention

**Rule.** When a mistake is caught — by the owner, by an audit, or by a later
pass discovering an earlier session's error — fixing the instance is half the
job. Before the session ends, root-cause it *five-whys style*: ask why
iteratively, past the surface slip, until the answer is a **process
property** — a missing rule, a missing check, a judgment recorded at the
wrong granularity, a stale document trusted, a default that invites the
error — stopping at the level where a cheap guard exists. Then encode the
prevention at the strongest rung available: (a) an **audit or lint** if the
failure is mechanically checkable (practice 6 — conventions become audits);
(b) else a **written rule, dated, carrying its origin incident** (practices
5 and 16 — the incident is both the justification and the test case); (c) if
the lesson is generic, **export it** (practice 14). Discuss the choice with
the owner when it involves a judgment call — which rung, what scope, whether
the guard is worth its cost.

**Why.** Repos that only fix instances relive their mistakes with new
surface details; the systemic cause remains free to fire again. The
root-cause habit is what turned one dependent repo's worst misses into its
strongest machinery — every audit it runs exists because of one specific,
recorded incident, and the audit that would have caught the incident is the
test of whether the root cause was actually found. The origin incident in
the rule text is load-bearing twice over: it tells a future reader what the
rule is protecting against (so the rule can be re-judged when the world
changes), and it calibrates proportionality (a guard that would not have
caught its own origin incident is theater).

**Proportionality guard.** Not every slip earns a rule: the trigger is a
systemic cause (it would recur) or real cost (rework, a wrong external
statement, lost work). Prefer strengthening an existing rule or audit over
minting a new one — rule-bloat is itself a failure mode, and a silent rule
nobody agreed to is how it starts.

**Install.** A habit plus a review question. The habit: end any session in
which a mistake was caught with an explicit root-cause note and its
prevention, in the same change-set as the fix. The review question, for the
owner: "does this guard's rung (audit / dated rule / export) match the
failure's checkability?" Seed it retroactively: the next time an old mistake
class recurs, that is the origin incident for its rule.

## 21. The second-pass capture sweep: production work gets a separate capture review

**Rule.** After producing any substantial work-product — a document, a design,
an analysis, a decision — the same session does a deliberate second pass **as
a separate step, not part of the production flow**, re-reading its own
reasoning against a short checklist: (a) did every idea discussed reach its
**durable artifact**, or does it live only in prose or conversation? (b) do
**parallel artifacts** that must track this change have their transfer
verdicts (practice 22)? (c) did technical value get its **cross-ledger
capture** — the business, operational, or planning implication recorded where
those live? (d) are open decisions **queued in the typed TODO** (practice 2)
rather than only in the conversation? (e) are the **indexes, registries, and
glossaries** synced? Run the sweep before the merge-time capture gate
(practice 10), so what it finds lands in the same change-set as the work.

**Why.** The production mindset cannot audit itself: while drafting, every
idea feels captured because it was *thought*. In the origin repo, an
owner-prompted "did we miss capturing anything?" sweep found two real gaps in
the same day's work — a cross-artifact transfer that had been waved off and a
competitor-inspired idea noted in passing but never landed — each of which
the drafting passes had individually missed. The separation is the point: the
sweep is a different cognitive act (reading for omissions) from drafting
(writing for completeness), and it is cheap — minutes against the cost of a
lost idea.

**Install.** Add the checklist to the session-end or pre-merge ritual, before
the capture gate. Adapt the checklist items to the repo's ledgers (what
counts as a durable artifact, which registries exist). The trigger for
adopting it retroactively: the first time an owner's "did we miss anything?"
finds something — that incident is the origin story (practice 20).

## 22. Parallel-artifact families: transfer verdicts are per-mechanism, per-change, and ledgered

**Rule.** When a family of artifacts embodies **one design in several
parallel forms** — the same architecture on different platforms, media,
languages, or markets — a change to any member presumptively transfers to the
others, and the transfer check obeys three constraints. **Decompose by
mechanism, not headline:** the verdict is formed per mechanism inside the
change, never once for a whole cluster — a cluster's headline can be
member-specific while a mechanism inside it transfers. **Verdicts are
per-change, not per-session:** a verdict recorded for one batch of changes
says nothing about the next batch added later, even minutes later; re-run the
check every time. **Every verdict is ledgered:** a dated row per change —
originating matter, and per member either *applied as `<what>`* or *no
transfer because `<reason>`* — with a small **audit that fails any change
date lacking a complete row**.

**Why.** The origin incident: a session recorded a headline-level verdict
("this cluster is member-specific — no transfer") that was true as a headline
and wrong for one mechanism inside it, which transferred to all three sibling
artifacts. Nothing forced the verdict to be decomposed, re-run, or recorded
per member, so the miss was invisible until a prompted second pass (practice
21) caught it. Free-text one-time verdicts have three failure modes the
ledger kills: wrong granularity (headline vs mechanism), staleness (new
changes inherit old verdicts), and unauditability (nothing can check what was
never recorded).

**Install.** A ledger table (date | originating change | one verdict column
per family member) plus a small audit keyed on dated change markers in
whatever registry tracks the family — any marked date without a complete
ledger row fails. The family definition itself lives at the top of the
ledger, with the origin incident (practice 20).

## 23. Layered practice packs: a domain layer between generic and repo-local

**Rule.** Rules come in three scopes, and each gets its own home. **Generic**
rules (true of any repo) live in this upstream and its instantiations.
**Repo-local** rules (true only of one repo's subject matter) live in that
repo's instructions files and never leave. Between them sit **domain** rules —
true of any repo running the same *kind* of program (a compliance regime, a
lab workflow, a regulated-filing process) but meaningless outside it. Those
are collected into a **practice pack**: a vendored tree at `process/<pack>/`
with the same anatomy as this upstream (a practices catalog, an install
playbook, extracted tools, harness adapters), tracked by its own manifest at
`process/manifest_<pack>.json` with its own optional scrub blocklist, audited
by the same `practice_audit.py` (it discovers every `process/manifest*.json`).
A pack may **route**: its harness adapter (e.g. an agent skill) declares when
the domain's rules apply, so an agent loads them exactly when doing that
domain's work instead of carrying them in every session. The decision rule
for any new rule: *would this hold in an unrelated repo?* → upstream (public
scrub applies). *Only in another repo running the same kind of program?* →
the pack. *Only here?* → repo-local.

**Why.** A domain program inside a dependent repo accumulated rules that
were neither generic (they could not be published, and their vocabulary was
all domain) nor repo-local (a second program of the same kind would need
every one of them). With no home of their own they lived interleaved with the
repo's local rules, which meant every session carried them whether relevant
or not, and a future split of the program into its own repo would have meant
re-deriving which rules travel. Vendoring them as a pack made the split a
`git mv` instead of an archaeology project — the same pre-split shaping that
made this upstream's own extraction clean.

**Install.** Vendor the pack tree at `process/<pack>/`; write
`process/manifest_<pack>.json` (schema of [INSTALL.md](INSTALL.md) §5, plus
`upstream.scrub_blocklist` — a path, or `null` to opt a private pack out of
the scrub); instantiate the pack's practices in the repo's real files and
record the mapping; install its harness adapter so the rules load when the
domain work happens. The export gate (practice 14) covers packs too: a thread
that improves a domain practice folds the abstracted form into the pack tree
in the same branch, keeping repo vocabulary out per the pack's blocklist.

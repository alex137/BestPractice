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
[tools/checkin.py](tools/checkin.py) drives the cross-repo mechanics, and
**both directions of its mirror destroy work, so both are guarded**:
`update` refuses to overwrite unexported local changes, and `push` refuses
when the vendored tree is behind upstream — it deletes files it does not
have, so pushing from a stale tree silently reverts whatever upstream
gained. `--force` bypasses either.

A caution learned the hard way, worth stating because the tooling cannot
fix it: **`--force` on a mirror is a destructive command with no undo.**
Both guards were added after real losses in a single session — a stale tree
that would have reverted two upstream practices, caught only by a human
reading `status`; and then a `--force` passed to bypass the *other* guard,
which silently reverted three unexported additions including the guard code
itself. If you must force a mirror, copy what you are about to overwrite
first. The guard you are bypassing is the one that knows what you are about
to lose.

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

Three corollaries. **The date is the contributor's, not the session's:**
an agent stamping a date uses the human contributor's local calendar date
— the date they experienced when the fact was true or the decision was
made — not the agent session's system clock. The two disagree by a full
day near midnight in most timezones, and an agent's clock is often UTC or
otherwise unaware of where the contributor sits; ask when it isn't already
clear from context rather than defaulting to the session's own date.
**Durable rules earn a record, not just a date:** for a
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

## 24. Quote discipline: compression rounds against the writer, and qualifiers travel

**Rule.** Two obligations whenever a document quotes a figure from another
source. **(a)** When a sourced range or multi-case figure is compressed for
prose — rounded, summarized to one number, or reduced to its typical case —
the compression **rounds against the writer's interest**, or quotes both
ends. A summary that must pick one number picks the one that makes its own
argument weakest. **(b)** A source's **qualifiers are part of the figure**:
*best-case*, *worst-case*, a scenario label, a verify flag, or a fidelity
grade worse than the house default all travel with the number into every
document that quotes it. Dropping the label is misquoting, even when the
digits are copied faithfully.

**Why.** An adversarial audit of an outward-facing summary found the same
failure four independent times in one document: every compression had
drifted in the flattering direction (a range's ceiling shaved down, margin
bands quoted above their source, an unfavorable finding described as
missing data, a favorable-case figure paired with an unfavorable-case
market). None was a deliberate misstatement — each was an ordinary
summarization choice made under the incentive every summary carries. A
separate pair of findings showed the qualifier failure: a schedule date its
source twice labeled *best-case* became the central case downstream, and a
source's own worse-than-default fidelity grade was silently overridden by
the quoting document's blanket precision claim. The bias is systematic, so
the countermeasure must be a standing rule, not vigilance.

## 25. Outward-facing summaries: a claims-to-source table, honest aggregation, and a recorded adversarial pass

**Rule.** A document that summarizes a body of work for an external audience
carries three things. **(a) A claims-to-source table**: every quantitative
claim mapped to the living source that backs it — this is what makes
verification cheap enough to actually run. **(b) Honest aggregation**: any
sum over rows drawn from different sources names its rows and states its
dedupe rule beside the sum, after reading each row's defining prose for
inclusion statements (rows with different names are not additive until
proven additive); and in any companion computation, a revenue or benefit
line names its enabling condition and the computation either carries that
enabler's cost or excludes the line. **(c) A recorded adversarial pass
before external use**: claim-vs-source verification plus a cross-document
consistency sweep, run adversarially (a subtly different range counts as a
finding), with findings, resolutions, and the open tail written to a dated
diligence record. The record is part of the deliverable.

**(d) Run the pass automatically, in the same working session, before
reporting the work done** — do not queue it, offer it as an option, or defer
it to "before external use". Deferred verification is verification that does
not happen: the session that wrote the analysis is the one that still holds
the reasoning, and a later session inherits the conclusions without the
context that would let it attack them. Only genuinely external blockers (an
unreachable source, a number needing a field measurement) stay open, listed
as the open tail rather than used to postpone the pass. **(e) A correction
that moves numbers in the author's own favour carries its justification in
writing** — that direction needs the most scrutiny, not the least. **(f) When
a model composes two agents with different characteristic times, check the
slower one's cycle time against the faster one's before costing the
composition** — a cost model can be dimensionally perfect and still describe
an operation that cannot be performed. **(g) When comparing alternatives,
check that each side's standing/availability cost is charged, or that
neither is** — marginal-only costing of a human alternative against a
capital alternative that already carries its overhead is the commonest
one-sided comparison, and it flatters whichever side the author owns.
**(h) State which technology generation the incumbent is allowed to use.**
Costing your automated proposal against a manual incumbent compares your
future to their present. Give the incumbent the same generation of technology
your own case assumes, and where you claim an asymmetry — that a rule or a
physical constraint permits your automation but not theirs — justify it from
the environment rather than from convenience, and say which regime each
finding belongs to. **(i) When a term's sign or direction is the claim being made,
compute it — do not reason about which way it goes.** Directional assertions
about a model's own terms are the easiest thing to get backwards and the
hardest to notice, because they sound like understanding.

**Why.** The same audit that produced practice 24 found twenty-two defects
in a summary whose every number had been written in good faith from real
sources: three differently-named rows summing one underlying market, a
benefit line booked without its gating cost, claims citing documents that
did not contain them, and stale values the sources had since revised. The
claims-to-source table let two independent reviewers verify thirty claims
in minutes — without it the pass would have been unaffordable and would not
have happened. The diligence record then made every fix auditable and left
an honest open-items tail the next revision inherits, converting a one-off
cleanup into a repeatable gate. Clauses (d)–(f) came later, from the
principal's standing direction after a second analysis shipped with its pass
queued rather than run ("I don't care about unchecked work"): the pass that
was then run immediately found that the model had silently assumed a
composite operation neither participant had time to perform — a defect no
amount of source-checking would have surfaced, because every input was
correct and only their *composition in time* was impossible. Clause (g) came
from the principal's next question — whether the human alternative's
availability cost had been modelled. It had not, while the authored side's
equivalent overhead was already charged; the omission was invisible because
each side's own numbers were internally consistent. Clause (h) followed
immediately: the same reviewer asked whether the manual incumbent should have
been allowed to automate too. It should — and modelling it removed most of the
proposal's advantage, leaving a narrower but defensible claim. The three
questions form a family: whether the composed parts fit in *time*, whether
both sides carry their *standing* costs, and whether both are costed at the
same *technology generation*. A fourth round added clause (i) after the
author's own answer to a reviewer's challenge asserted, confidently and
backwards, which way one of the model's terms inverted — inside the very pass
meant to be checking the work. The lesson generalises past cost models: a pass
that only re-reads reasoning reproduces its errors, while one that re-computes
the disputed quantity does not.

## 26. Documents are current state; the VCS is the revision history

**Rule.** A document reads as a statement of what is true *now*, not a log of
how it got there. Do not annotate in-document when text was added or changed —
no "*(added DATE)*" / "*(rewritten DATE)*" section tags, no "Rev N" ladders in
headers, no superseded text kept inline "for history." Version control carries
all of that losslessly; `log`/`blame` answers "when did this change" better
than a prose annotation ever will, and never goes stale. Narrow exemptions,
where the date or prior state *is* the content: (a) records whose subject is a
dated decision or event ("decided DATE: X"); (b) volatile-fact freshness
stamps (practice for dated external claims); (c) legally or contractually
load-bearing markers; (d) as-shipped/as-filed artifacts whose purpose is
historical.

**Why.** A working document set accreted so many added/rewritten/Rev-N
annotations that documents read as changelogs instead of positions — and the
annotations themselves went stale (a "Rev 3" reference outliving Rev 5, an
"added 2026-…" tag on text three rewrites old), becoming a second drift
surface on top of the content. The revision history was already in the VCS,
losslessly; the in-document copy was pure liability.

**Install.** State the convention in the project instructions with its
exemption list; when touching a document, strip stale revision annotations
from the parts you touch. A lint can flag `Rev \d`/`\*(added ` patterns
outside the exempted file classes.

## 27. A label must describe what follows

**Rule.** A heading or lead-in that names a form or length must match what it
actually introduces. Do not title something "in one line" / "one-pager" / "in
one paragraph" / "TL;DR" unless it literally is that. If a section runs to a
page, name it for its content, not for a brevity it doesn't have.

**Why.** "The thesis in one line" sat atop three paragraphs; "the business
model in one line each" atop multi-line bullets. The label over-promises,
and a reader who trusts it feels misled the moment they read on — the same
credibility leak as a numeric claim that doesn't match its source. It reads
as spin in a document whose whole job is to be trusted.

**Install.** A writing convention in the project instructions; catch it in
document review. The fix is almost always to rename the label to its content
("The thesis"), not to compress the content to the label.

## 28. Frame the deliverable from the audience's question, not from the material in hand

**Rule.** When you finish producing a body of work and then write the thing
that explains it — a pitch, a summary, a README, a recommendation — build it
around **the question the audience actually has**, and check explicitly that
you have not instead built it around **the material you just produced**. The
tell is that the deliverable's headline matches the shape of your recent work
rather than the shape of the reader's problem. If a one-sentence statement of
the audience's question does not appear near the top, you probably skipped
this.

**Why.** A thread had just produced a detailed body of work on one property of
a system, and wrote the outward-facing explanation around that property. It
was true, well-evidenced, and nearly useless to the reader, whose question was
a different one that the same machinery answered better. The correction came
from outside and reframed the whole document — including which limitation was
binding, which market to lead with, and which mechanism was the strongest thing
on offer. Nothing was wrong with the underlying work; the framing was wrong
because it inherited the author's recent path instead of the reader's need.

This is a specific failure of *sequence*, not of care: the more thoroughly you
have just worked something out, the more available it is when you sit down to
explain, and availability reads as importance. Effort spent on a component is
not evidence that the component is the headline.

**Install.** Before writing an outward-facing artifact, write the audience's
question down as a plain sentence — literally, in the draft — and confirm the
artifact answers *that*. Keep it in the finished document if it helps the
reader; delete it if not. In review, ask of the opening: *whose question is
this?* When a reframe does arrive, record what it changed in the document
itself rather than silently rewriting — a reader who saw the earlier version
deserves the diff, and the record makes the failure mode legible next time
(this is practice 20 applied to framing rather than to defects).

**Related.** Practice 25 (an adversarial pass on outward-facing work) will not
catch this on its own: a well-framed-for-the-wrong-question document survives
claim-to-source verification intact, because every claim in it is true. The
framing check has to be separate, and it has to happen before the verification
pass rather than after.

## 29. A variant re-derives what it inherits: limits it must respect, choices it need not keep

**Rule.** When you build a variant of an existing thing — a new configuration
of a component, a fork of a process, a second instance of a design aimed at a
different job — treat **every attribute you inherited from the base as
unexamined until you have re-derived it against the new job**. Inherited
attributes come in two kinds, and both fail silently:

- **Constraints the base states** — which the variant must respect, and which
  your new reasoning may not have noticed it was violating.
- **Choices the base made** — which the variant is free to change, and which
  you may be carrying only because they were already there.

**Why.** One piece of work made both mistakes about the same base, in opposite
directions, a day apart. First it computed a favourable property of a variant
and announced a capability from it, without reading the base's own stated
limits — which excluded that capability in plain language. Then it carried
forward one of the base's design *choices* without asking whether the change of
job had invalidated it; it had, and the inherited choice made the whole variant
unworkable at its intended duty cycle. The second miss was worse than the first
because the arithmetic built on it was internally correct: the numbers
described, in convincing detail, an operation that could not be performed.

The asymmetry is what makes this hard to catch. A constraint you violate tends
to produce an obviously wrong answer eventually. A choice you fail to re-open
produces a *plausible* answer that is merely answering the base's question
instead of yours — and the more carefully you work downstream of it, the more
solid it looks.

**Install.** When starting a variant, list what changed about the job — duty
cycle, duration, environment, load, audience, tempo — and walk the base's
attributes against that list, marking each *re-derived*, *inherited
deliberately*, or *not yet checked*. Nothing stays in the third state at
delivery. Two prompts do most of the work: *"what does the base say it cannot
do, and does my variant's reasoning quietly assume otherwise?"* and *"which of
the base's choices exist only because of a job my variant is not doing?"*

**Related.** Practice 20 (mistakes become rules) is how this one was derived —
and note that the second instance was folded into the *same* rule as the first
rather than minted as a new one, per that practice's proportionality guard: two
failures with one root cause get one widened guard, not two narrow ones.

## 30. Scripts assert their own properties, and the figures their source documents recite

**Rule.** A script that computes numbers other work depends on carries two
kinds of executable assertion, and an audit (`tools/model_audit.py`) runs them
with the repo's other gates:

- **`self_check()` — property assertions on its own outputs.** Not "is this
  value right" but "does this output satisfy the properties it must satisfy":
  an invariance, a monotonicity, a conservation, an ordering, a ratio held by
  construction. Returns a list of failure descriptions; empty means pass.
- **`ANCHORS` / `check_anchors()` — figures recited in an authoritative source
  document** that the script must reproduce. Each anchor names the document and
  section that recites it. Compare as **band overlap**, not equality, when
  either side is an estimate.

Two rules make the difference between this working and being theatre.
**Assert properties, not values** — a value comparison cannot catch a correct
input transformed by a wrong law. And **never refit an anchor to silence it**:
a failing anchor means a script and a document of record disagree, which is
always a human's decision, and the resolution runs in both directions.

Scope it. Instrument the scripts that **consume or re-derive a quantity another
script or an authoritative document owns** — that is where this failure class
lives. Scripts that own their own numbers end to end need nothing. Keep the
instrumented list explicit so the audit can warn when a listed script has no
assertions.

**Why.** The obvious diagnosis for a wrong computed number is a stale copy, and
the obvious fix is a shared constants module. In the incident that produced this
practice, both were wrong.

A script published results that were out by a third at one input and by more
than a factor of three at another; work sized from them would have been badly
undersized. The constant it started from was **correct, correctly labelled, and
identical in the two sibling scripts that also used it** — one of which even
stated the governing property in its own docstring. The script cited its source
correctly. A shared constants module would have handed it exactly the right
number and the defect would have survived untouched, because the defect was in
the **transformation applied after import**: a scaling law applied to a quantity
whose defining property is that it does not scale.

That property was written down — in two sibling scripts' docstrings, in the
owning script's printed output, and in the figures recited by the authoritative
document. It was prose everywhere and executable nowhere, and **prose does not
fail a build**.

The sharpest part is where the correct number actually lived. **The
authoritative document was right and the script was wrong.** The document
recited the correct figure for exactly the case the script got wrong — and the
sync gate of practice 19 faithfully published the script's number into the
derived document, because it guards *document agrees with script* and cannot
know the script is wrong. Every artifact was internally consistent; the only
disagreement in the repo was with the one document nothing compared against.

Generalise that: **the most carefully reasoned documents in a repository are
often the ones checked by nothing.** They are written slowly, by whoever
actually reasoned the thing through, and then they sit — while fast-moving
derived artifacts get all the tooling. Driving everything from the scripts is
the natural instinct and it is backwards here; it would have propagated the
error faster. The document was the more reliable artifact and the more neglected
one at the same time.

Two further returns showed up immediately on installing this. First, an anchor
failed in a script written **by the same session that had just been burned by
this exact class of error and was actively watching for it** — care did not
prevent the repeat, the executable check did, on its first run. Second, anchors
surface **unstated assumptions in the source documents**: one recited figure
turned out to hold only under a qualitative condition the document never
quantified, and the unconditional figure — the one anything must actually be
sized to — was materially different. Neither of those is findable by reading.

**Install.** Add `tools/model_audit.py`; list the scripts to instrument in its
`INSTRUMENTED`. In each, add `self_check()` returning failure strings, and
`ANCHORS` as `(label, lo, hi, callable -> (lo, hi))` with `check_anchors()`
comparing by overlap. Label every anchor with the document and section it comes
from. Wire the bare run into the same pre-commit list as the other gates.

Start where a quantity crosses a boundary: the first script that takes a number
it did not derive. Write the assertion as the sentence you would use to explain
the quantity to someone — *"these must be equal by construction"*, *"this can
only decrease"* — because that sentence is the property, and the property is
what a wrong transformation violates.

When an anchor fails, record which way it resolved. In the origin round of three
failures, one was the script's error, one an unstated assumption in the
document, and one a superseded input; all three were written down and none were
fitted away. That record is what keeps the mechanism honest — an anchor quietly
widened to pass is worse than no anchor, because it now certifies the thing it
stopped checking.

**Related.** Practice 19 guards *document agrees with script*; this one guards
*script agrees with reality and with the document of record* — the edge one
level up, and the one that bites when the script is the wrong artifact.
Practice 6 (conventions become audits) is the general form. Practice 20
(mistakes become rules) produced it, including the correction of its own first
root-cause analysis, which named the stale-copy diagnosis above and had to be
retracted when a one-line check disproved it.

## 31. A tool's warning never justifies rewriting published history

**Rule.** When a hook, linter, badge, or CI check complains about commits that
are **already published** — on the shared trunk, or authored by someone else —
the response is to fix the setting **forward** and leave the history alone.
Configure the identity, the tool, or the exemption so future commits are clean;
do not rebase, amend, or force-push to satisfy the warning. Rewriting published
history is reserved for an explicit human instruction, never inferred from a
tool's output.

**Why.** These warnings are written as if every commit they see is yours and
still local, and the remedy they suggest — `rebase --exec ... --amend` — is
accurate for that case and catastrophic outside it. On a shared trunk it
rewrites commits other people authored and already built on, forces a divergent
default branch, and trades a cosmetic badge for a genuine coordination failure.
The asymmetry is total: the warning's cost is that something looks untidy, and
the suggested fix's cost is that everyone else's clone is now wrong.

The trap is that the tool is *correct about the condition* and merely silent
about the context. It is right that the commits lack the property; it does not
know they are published, does not know which are yours, and cannot weigh what
its remedy costs. An agent reading such output is being handed a confident,
specific, executable instruction with the reasoning omitted — the shape most
likely to be followed without the judgement the situation actually needs.

Generalise past the specific tool: any automated warning whose suggested remedy
is *destructive and retroactive* — rewriting history, mass-reformatting a
shared tree, regenerating a lockfile everyone pins, bulk-editing files a check
flags — gets the same treatment. Satisfy it forward, exempt what is already
published, and escalate to a human if the backlog genuinely matters. A warning
is a report, not an authorization.

**Install.** Set the identity or configuration the tool wants, so new work stops
triggering it. Where the tool supports it, scope the check to unpublished or
own-authored commits. Record the decision — including the count of pre-existing
items deliberately left alone — next to the merge or release runbook, so the
next person sees a resolved question rather than an unexplained backlog and
re-litigates it. If the tool has no scoping option and the noise is persistent,
that is a request to file against the tool, not a reason to act on it.

**Related.** Practice 20 (mistakes become rules) — this is the abstracted form
of a rule a dependent repo added after a session was one command away from
rewriting a shared trunk to clear a signature badge on commits it did not own.

## 32. Verify the postcondition, not the command

**Rule.** After any state-changing operation, check **the state you wanted**,
not that the command reported success. Name the postcondition before you run
the command — *"no unpushed commits on any branch"*, *"the gate passed"*,
*"the file contains X"* — and then test that, independently of whatever the
command printed.

Two traps deserve naming because they produce confident, wrong success
messages:

- **A pipeline's exit status is its last command's.** `check | tail && publish`
  does not gate on `check`. The gate can print FAIL in plain sight and the
  publish still proceeds. Run gates bare and test `$?`; if you pipe for
  readability, capture the status first or use the shell's pipe-status
  facility.
- **A command with an explicit target acts on the target you named, not the
  context you are in.** Publishing by naming a branch publishes *that* branch,
  whether or not it is the one you have been working on. If it has not moved,
  the operation succeeds as a no-op and says so.

**Why.** Two incidents in one session, one root cause. A gate chained through a
pipe let a failing check reach the shared trunk. Then work was committed on the
wrong branch and "published" by naming the intended branch explicitly — which
had not moved, so the push succeeded, reported success, and left the commit
sitting unpublished somewhere else. The session reported the work delivered.

Neither command malfunctioned. Both did exactly what they were literally asked
to do. The defect was reading *"the command ran"* as *"my intent was
achieved"* — and the more precisely a command is targeted, the more completely
it ignores your context, which is a virtue right up until your context is
wrong.

The second incident is the sharper one, because the misleading part was the
*success*. A failure would have been investigated. A green line about an
operation you did not intend gets skimmed, and the more automated the reporting,
the more likely it is skimmed. An agent narrating its own work is especially
exposed here: it produces the summary from the same premises that produced the
mistake, so the summary inherits the error and reads as confirmation.

Note what actually caught it: an **independent check** — a hook comparing local
branches against the remote — not the session's own review. Self-reported
completion cannot catch a wrong premise about what "complete" meant. That is
the argument for having such a check at all, and for treating its output as
information rather than noise.

**Install.** For each operation that matters, write the check next to the
action:

- **Gates:** run bare, test the exit status. Never gate on a pipeline.
- **Before committing:** confirm which branch you are on.
- **Before declaring anything delivered:** enumerate every local branch against
  its remote and require the difference to be empty — the postcondition is
  "nothing unpublished anywhere", not "the publish command printed something".
- **In general:** if you cannot state the postcondition, you do not yet know
  what the command was for.

Cheap and worth it: end a work session by re-deriving the finished state from
the repository rather than from your own transcript.

**Related.** Practice 6 (conventions become audits) — this is the audit for
"did the thing actually land". Practice 20 (mistakes become rules) produced it,
from two failures with one root cause folded into one widened rule rather than
two narrow ones, per that practice's proportionality guard.

## 33. Documents track their models, and every transformation lives in code

**Rule.** Extending practice 19 from *tables* to **every** figure a script
computes:

1. **A script-derived figure appears in a document only inside a generated
   block.** Including figures embedded in running prose — those are the ones
   the sync gate cannot see, and therefore the ones that rot.
2. **Never restate a generated number in the prose around its block.** Point at
   the table instead. A restatement is a second copy with no gate on it. If a
   figure genuinely must appear in a sentence, put the sentence inside the
   block.
3. **Every transformation belongs in the emitter.** Unit conversions, rounding,
   banding, audience-facing phrasing, redaction for external copies — all code.
   A number converted by hand is a number nobody can regenerate, and a rounding
   applied by hand is a rounding nobody can audit.

When a script changes, every dependent document changes with it, in the same
commit, by regeneration rather than by editing.

**Why.** A sync gate only guards what it can see. In the incident that produced
this, a defective script published wrong figures into several documents; the
generated tables were corrected automatically the moment the script was fixed,
and the **hand-written prose statements in the same documents stayed wrong** —
found later only by a deliberate contamination sweep. The gate had worked
perfectly on everything it was pointed at, which is precisely why the gaps were
invisible.

Hand-applied transformations hide the same way. A metric figure typed again in
feet is two numbers that must be maintained together and will not be; a range
"rounded for prose" is an editorial decision with no record of which direction
it moved. Both look like writing and behave like un-versioned code.

The scope limit matters: **this applies to documents not yet issued.** An
artifact already sent to someone is a record of what they received and must not
be silently regenerated — fix the source, mint a fresh copy, and let the
distribution record show both.

**Enforced, not merely stated.** Rule 2 is mechanically checkable and now is:
a script declares the figures it owns via `owned_figures()`, returning them in
the **exact rendered forms it produces** — value and unit, formatted as the
emitter formats them — and the sync tool greps every document *wired to that
script* for those strings outside its generated blocks. Three scoping choices
keep it usable rather than noisy: only wired documents are scanned, only
declared figures are searched, and matching requires a **unit boundary** so
`30 m` never matches `30 m/s`. That last one is not hypothetical — it was the
first thing the check got wrong, firing on two speeds on its first run, and it
is the reason a naive scan for "numbers a script produced" is worthless. A
deliberate restatement is marked `<!--owned-ok-->` on the line. Scripts that
declare nothing are not checked; instrumentation is opt-in, per script.

**Install.** When wiring a document: wrap every script-derived figure, give the
emitter an audience-appropriate form (the same numbers may want a different
table for an internal reader and an external one — that is two emitters, not
two hand-edits), and put the provenance footer at the foot of the document so a
reader knows which code produced what. Then **sweep the prose** for figures the
scripts own and either wrap them or replace them with a pointer; a short regex
sweep over the owned quantities finds these quickly and is worth re-running
whenever a script's outputs change shape.

Where a document needs figures from several scripts, let the emitter **import**
the other scripts rather than restating their numbers, so each figure keeps
exactly one owner (practice 19's composition extension, and practice 30's
one-owner rule applied to documents).

**Related.** Practice 19 (generated blocks) is the mechanism; this is its
scope. Practice 30 (scripts assert their properties and their sources' figures)
guards the layer below — that the script is right before its numbers are
published everywhere automatically.

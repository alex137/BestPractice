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
document. None recurred after promotion to an audit.

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
strikethrough on GitHub, silently garbling text.

**Why.** Both born from real bugs: readers hunting for referenced files, and
an outward-facing document that rendered with unintended strikethrough.

**Install.** [tools/doc_lint.py](tools/doc_lint.py) checks both — it gates on
files changed vs the default branch (the "fix what you touch" scope, which
also protects frozen documents), `--all` reports the backlog, `--fix`
rewrites `~`→`≈` on struck lines. Requires `cmarkgfm` for exact detection
with GitHub's own renderer.

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

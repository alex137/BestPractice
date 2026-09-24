---
slug:              todo-2026-09-21-pass-1-install-and-update-findings
kind:              manual
domain:            engine
severity:          high
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "a real consumer repository attached to a session -- pass 1's highest-yield item needs one, and attaching is not a session's act"
noted:             2026-09-21
closed:            null
---
## What

Pass 1 of the 2026-09-21 very deep check, run the way the practice says to
run it — by **building** the thing the documents describe, not by reading
them. Five fixtures in scratch: a fresh private install, a fresh public
install, a consumer installed from upstream `9171d4a2` (2026-09-17) and
refreshed forward to `08f3905e`, a deletion rehearsal, and a pinned clone
to install from.

**Recorded PARTIAL on its own terms.** No consumer repository is attached
to this session, so "update a real consumer's vendored tree and run its own
gates" — the item the practice calls the highest-yield in the pass — was
not done. That is the `waiting_on` above.

Findings are in the order they should be fixed, which is not the order they
were found.

## 1. The command a consumer's own `AGENTS.md` tells it to run destroys that consumer's `MAP.md` and `GLOSSARY.md`

**Severity: highest, because it is silently destructive.**

Every generated block carries, verbatim:

> Regenerate with: `python3 tools/build_views.py` … do not hand-edit this
> block; `python3 tools/build_views.py --check` exits non-zero on drift.

(quoted as prose rather than reproduced as a comment: the literal header
trips `generated-edit-goes-upstream`, which reads any file carrying it as a
generated file needing a `Source:` clause.)

[tools/build_views.py](../tools/build_views.py) line 988 emits that as a
fixed f-string with no variation by repository kind, although the same file
distinguishes upstream from consumer elsewhere. In a consumer the
instruction is wrong in **both** directions: `--check` fails on an
untouched fresh install, and the plain form overwrites the adopter's
hand-templated `MAP.md` and `GLOSSARY.md` with **Precedent's own** repo map
and term table. Measured in the fixture: `MAP.md` +222 lines, `GLOSSARY.md`
+99, the adopter's map replaced by *"Precedent's own repo map"* and
*"`practices/` holds 147 practice files"*.

`orientation-map` is a **resident** practice — *"Every session reads it
before doing anything"* — so the map every session in that repo reads
becomes a different repository's.

[INSTALL.md](../INSTALL.md) §0 step 6 already knows half of this: it says
`build_views.py --check` reports the hand-templated files as drift *"which
they are not"*. It documents the trap instead of fixing the emitted line,
and does not mention that the non-`--check` form deletes them.

**Fix:** emit the repo-appropriate command (`precedent_sync_views.py
--repo .` in a consumer), and have `build_views.py` refuse to write
`MAP.md`/`GLOSSARY.md` when it is not running in the upstream.

## 2. A correct fresh PRIVATE install fails its own documented acceptance test

**ROADBLOCK.** [SETUP.md](../SETUP.md) tells the guided installer to run
`precedent_check.py` and that *"it must say `0 violated`"*. A fresh private
install says `42 passed, 1 violated`:

    VIOLATION  claude-web-bootstrap
        .claude/hooks/precedent-individual-bootstrap.sh: looks like a
        claude-web-bootstrap install but no SessionStart hook entry in
        .claude/settings.json references it

`precedent_install.py` writes `.claude/settings.json` **before**
`precedent_sync_views.py` materializes the adapters, so an adapter the
individual source owns lands on disk with nothing wiring it. The public
install is unaffected (adapters are withheld), so this hits exactly the
private-consumer default. It survives the update path and a
sources-unreachable run.

**Fix:** wire adapter-supplied SessionStart hooks after materialization,
or have `precedent_materialize.py` do the wiring.

## 3. Every consumer commits an `AGENTS.md` nothing else can reproduce

**DEFECT, high.** The generated loader block is a function of what resolved
on the **installer's machine**. In any checkout where those sources do not
resolve — CI, a second contributor, a fork — `build_views --check` reports
drift and `generated-artifact-provenance` turns it into a violation whose
stated cause (*"hand-edited or stale"*) is false.

Measured under a stripped environment: the private fixture's block loses
its whole individual contribution (`12 of 147 practices (2 individual, 10
universal)` becomes `10 of 131 practices (10 universal)`). The **public**
fixture fails too, for a smaller reason — the Standing instruction's
trailing `.precedent/SESSION_PRACTICES.md` sentence is emitted only when a
source was deferred.

`generated-artifact-provenance`'s own bullet says a degradation must never
fail on something the adopter cannot fix. This fails on exactly that.

## 4. Two skip-messages tell a consumer to hand-edit a manifest-tracked engine file

**DEFECT.** `precedent_check.py --full-sweep` on a fresh install says, of
`computed-numbers-in-scripts` and `docs-track-models`, *"replace `PAIRS` in
`tools/doc_sync.py` with this repo's own pairs"*.
[tools/doc_sync.py](../tools/doc_sync.py) is in `ENGINE_MANIFEST.json`.
Following the advice and then refreshing:

    doc_sync.py: hand-edited (sha256 differs from manifest)
    precedent_vendor_engine FAIL: ... refreshing would silently discard
    that edit. Move the edit upstream into BestPractice instead (this
    engine has no local variance by design)

The remedy should name a consumer-side registry file, never the engine
file.

## 5. `refresh`'s closing instruction omits the two steps that exist because omitting them was an incident

**DEFECT.** [INSTALL.md](../INSTALL.md) says a §0 repo updates *"step 6
(the engine) first, then step 0 (the catalogue), then step 0b (the
wiring)"*, and §2 step 0 exists because a repo that refreshed only the
engine *"refreshed its tools, kept a frozen practice catalogue, and got OK
from every check"*. The tool's own `next:` line names neither.

Following the `next:` line exactly left the fixture running today's engine
against the 2026-09-17 catalogue: 125 practices against upstream's 140, and
a new advisory reporting `full-practice-audit` and `very-deep-check`
*"reachable by no channel"*. Doing §2 step 0 by hand brought it to 147 and
cleared the advisory.

## 6. The install swallows the engine-seed summary and prints a decapitated warning instead

**DEFECT.** `_seed_engine()` keeps only the last line of combined
stdout+stderr. The engine emits a multi-line hook NOTE on **every** fresh
install (the seed runs before `settings.json` exists), so the adopter sees
a 700-character block beginning mid-sentence with *"IF IT IS NEITHER"* and
never learns how many engine files were seeded (`grep -c "NOTE:"` on the
install transcript: 0). Dated: the same install from the 2026-09-17 clone
printed the note intact, because the note was one line then. The regression
arrived with its second paragraph, on 2026-09-21.

## 7. The deletion-referrer scan's noise outnumbers its signal seven to one

**DEFECT.** The rehearsal's two assertions both hold — the file is deleted
and referrers are named rather than refused over. But `dependents_of()`
skips only the manifest, so it walks the materialized `practices/` tree and
the vendored `precedent/universal/practices/` tree and reports files an
adopter **must not** edit. Measured: one actionable hit out of eight.

## 8. "Three questions" against a five-row registry, in four places

**DEFECT.** `spec/INSTALL_QUESTIONS.md` is the declared registry and holds
five rows; [SETUP.md](../SETUP.md) line 26 correctly says *"Ask exactly
five questions"*. Four other places still say three — including
`SETUP.md`'s own line 231, [INSTALL.md](../INSTALL.md) line 12,
`documentation/FOR_DEVELOPERS.md` line 148 and `documentation/INSTALL.md`
line 5, which is the first sentence a non-technical administrator reads.
`registry-source-of-truth` is being contradicted by the documents that
point at the registry.

## 9-11. Three nits

  - **Template authoring comments survive instantiation.** A fresh install's
    `AGENTS.md` opens with *"Template: instantiate per Precedent INSTALL.md
    §0 … Replace `<angle-bracket>` placeholders"*, and `GETTING_STARTED.md`
    carries nine lines of BestPractice's own incident history. The install's
    placeholder list then reports `AGENTS.md:12: <angle-bracket>` — the
    literal words inside that comment. `INSTALL.md` §0 step 5 tells the
    installer to grep for `process/upstream` and says every remaining hit is
    a path that does not exist; on a tool-produced install that grep returns
    five hits, all inside those comments. `.claude/settings.json` is clean,
    so the rewrite works and the comments are the residue.
  - **17 `doc-references-are-links` warnings on day one**, from this repo's
    own templates, including `AGENTS.md:397` naming
    `tools/precedent_candidate.py`, which does not exist in an installed
    tree. The text qualifies it, so it is a nit and not a broken promise.
  - **The installer's absolute home path is committed** into the adopter's
    tracked `MANIFEST.json` (`"path": "/root/precedent-individual"`). Public
    installs do not carry it; private ones do.

## Worked Clean, Stated Plainly

The fresh **public** install passes everything (`0 violated, 0 advisory`,
leak gate clean, individual practice text correctly withheld, no absolute
path in the manifest). Every one of the full sweep's 29 skips carried a
specific reason, and [`leak_gate.py`](../tools/leak_gate.py) in a private repo prints *"This is a
stand-down, NOT a pass -- it inspected nothing"*. The update path works end
to end once §2 steps 0/0b are done by hand, and **the documented refusal
fired correctly**: the catalogue sync refused to remove `archive-command`
and `session-text` without `--allow-removals`, both names resolving against
[`MAP.md`](../MAP.md)'s withdrawn-practices table exactly as the document says they
will. The deletion rehearsal's assertions hold.
`.precedent/SESSION_PRACTICES.md` (untracked, regenerated each session) is written by the installed bootstrap
even though `templates/bootstrap.sh` never names the script that writes it.

## What Was Not Tested

The real-consumer update (no consumer attached — the reason this pass is
PARTIAL); the migration path from the classic `process/upstream/` layout;
a practice moved between levels in all three directions; the fresh-eyes
rehearsals the practice asks for (one context-free reader per install
path, five in parallel); `BOOTSTRAP DRIFT` and `CONVERGENT DRIFT` against
bootstrapped sets; the contributor-access walk-through, which needs a token
against a real repository.

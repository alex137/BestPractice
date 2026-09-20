---
title:         A session rooted in a practice set renders the universal catalogue and never loads it
kind:          brief
status:        closed
opened:        2026-09-20
closed:        2026-09-20
superseded_by: null
supersedes:    []
audience:      session
summary:       From 2026-09-13 to 2026-09-20 every practice set rendered .precedent/SESSION_PRACTICES.md at session start and nothing put it in front of the model; what was actually broken, the four reasons it survived seven days of fixes aimed one layer too low, and the SessionStart injection that closes it.
---
# A session rooted in a practice set renders the universal catalogue and never loads it

**Morgan, 2026-09-20:** *"When I load precedent-individual as the seed root
repo in Claude Code..... it doesn't load bestpractice. We have discussed this
many times and nothing worked so far."* He was right, and every mechanism
built to fix it was working as designed.

**Authorized by Morgan, 2026-09-20** (`decided` — `Go update`, naming both
changes: *"do the hook injection and the CLAUDE.md stub, do everything you
recommend"*).

## What was actually broken

**The fetch worked. The render worked. Nothing loaded the result.**

Measured 2026-09-20 in an isolated copy of `precedent-individual` with no
sibling repositories on disk at all:

```
python3 tools/precedent_source_bootstrap.py --sources-from .
  -> clones BestPractice and all three shared sets beside it, exit 0, silent
python3 tools/precedent_session_practices.py --repo .
  -> .precedent/SESSION_PRACTICES.md, 167 practices (125 universal, 42 shared)
```

No `add_repo`, no credential, no cross-owner wall. The git proxy passes a
public clone: `git clone --depth 1 https://github.com/octocat/Hello-World`
succeeded in the same session, and that repository is nowhere near its
authorized set. **Every diagnosis that reached for repository access was
looking at the wrong thing**, which is the same conclusion
[gotcha-2026-09-18](../gotchas/gotcha-2026-09-18-editing-a-practice-pack-in-a-multi-repo-session-leaves-univ.md)
reached about `add_repo` from the other direction.

What does not happen is the last step. **Claude Code auto-loads instruction
files and nothing else** — `CLAUDE.md`, or `AGENTS.md` where a project has no
`CLAUDE.md` of its own. A file a SessionStart hook writes is a file on disk.
The only thing pointing at it was one sentence in the generated Standing
Instruction:

> If `.precedent/SESSION_PRACTICES.md` exists, read it too

**A pointer is not a load.** It asks the session to spend a tool call,
mid-turn, on a file it has no particular reason to believe is important —
after it has already started working from the rules it *can* see. The
set's own tracked block carries its 3 resident practices and 10 occasion
entries; universal's 125 practices sat in a file next to it.

## Why it survived seven days of fixes

Four causes, and **only one of them is an argument anybody made on purpose.**

**1. The injection channel was parked as unverified and never unparked.**
[`todo-2026-09-06-additionalcontext-reaches-the-model`](../todo/todo-2026-09-06-additionalcontext-reaches-the-model.md)
recorded that the public hooks reference did not say whether
`hookSpecificOutput.additionalContext` reaches the *model* or only the
transcript, and that no session could drive a live turn to find out. It has
sat at `disposition: wait` since. So the field stayed advisory-only in
`PreToolUse`, and nothing load-bearing was ever built on it — including
this. **Settled 2026-09-20 from the shipped CLI's own hook documentation**
(Claude Code 2.1.278): *"`additionalContext` — Text injected into model
context"*, and *"Exit code 0 - JSON additionalContext shown to Claude"*.
Documentation rather than a live turn, which is why that item is narrowed
rather than closed.

**2. The `CLAUDE.md` stub was never raised for a set at all.** Not argued
down — absent. `grep` across `spec/`, `todo/` and `practices/` finds no
mention of it in connection with a source set, and `git log --all --
CLAUDE.md` in `precedent-individual` is empty. [The adapter
table](../templates/harness/README.md) frames `CLAUDE.md` → `@AGENTS.md` as
wiring a **consuming** repo installs; a set publishes practices rather than
installing them, so nobody asked which filename the harness auto-loads
there. None of the four sets had one. It went unnoticed because Claude Code
falls back to `AGENTS.md` — so the set's *own* rules loaded and only
universal's did not, which makes the failure look like a source-resolution
problem rather than a wiring one.

**3. Every round fixed the layer below the broken one.** Fetch and render
(2026-09-13), the suppressed pointer (2026-09-14), a stale render
(2026-09-18, `_self_heal_stale_render`). The 2026-09-13 brief
[SOURCE_SET_PROSE_GAP.md](SOURCE_SET_PROSE_GAP.md) says it in its own words:
*"The measurement that missed it checked that the file was written, never
that a session is told to read it."* **Nobody moved up one more step to
whether the session actually read it** — and "told to read it" was where the
reading half was declared done.

**4. The budget already said it was loaded.** Both
[tools/session_load_budgets.json](../tools/session_load_budgets.json) here
and each set's own copy list `.precedent/SESSION_PRACTICES.md` as an
always-loaded surface with a declared ceiling — *"the whole of what those
sources may add to every session here"* — and
[session-load-budget](../practices/session-load-budget.md) defines such a
surface as *"anything in a session's context before its first turn"*. Once a
surface is in that registry it reads as settled. **The accounting asserted
the load that was never happening**, in the one file a session would check
to find out.

## The fix

**One channel, fresh by construction.** `precedent-universal-catalogue.sh`
already ran the render at session start; it now emits the rendered file as
`hookSpecificOutput.additionalContext` in the same run. The text injected was
written four lines earlier by the same script, so there is no window in which
a stale copy can be loaded, and no second copy to keep in step.

The mechanics that matter to anyone editing that hook: **Claude Code parses a
hook's stdout as JSON**, so one stray line alongside the object invalidates
the whole thing. Every step's stdout is captured to a temp file and the
object is printed once, at the end, on a saved file descriptor. Stderr is
left alone so a real error still reaches the transcript — with one exception,
`precedent_access_check.py`, whose table *is* its output and which had been
writing to stderr since 2026-09-14, meaning the answer to "which repos can
this session push to?" never reached the model either. **Same defect, one
size smaller, found while testing this one.**

Alongside it, the missing adapter: **each set gets a `CLAUDE.md` whose body
is `@AGENTS.md`**, so its rules load because it says so and not because the
harness currently falls back.

**What was deliberately NOT done, against the recommendation this work came
from.** The original proposal was a stub importing both `@AGENTS.md` and
`@.precedent/SESSION_PRACTICES.md`. The second import is wrong, for two
reasons that only became visible once the hook existed: an `@import` resolves
when instruction files are read, which can precede the hook's render, so it
loads **last session's copy**; and where the hook did fire, the same ~4,672
tokens load **twice**, which `session-load-budget` counts as the finding it
exists to catch. The hook not firing is not the case it would rescue either —
when hooks do not fire, the set is not the harness's primary project
directory, and a non-primary repository's `CLAUDE.md` is not loaded to do the
importing.

**The cost is already budgeted, and that is the point rather than a
coincidence.** The render measures **4,672 tokens** against the **5,200**
ceiling `precedent-individual` declared for that surface on 2026-09-13 —
`build_views.surface_budget()` renders the file against that same number, so
it cannot outgrow what the hook emits it into without the budget check going
red first. Cause 4 above is now true instead of aspirational.

## What is done, and what is not

| | |
|---|---|
| `precedent-individual` | hook injects; `CLAUDE.md` added; both surfaces registered in its own budget file |
| `templates/harness/claude-code/` | the hook and the `CLAUDE.md` stub, for every repo that installs the adapter |
| `tools/precedent_bootstrap_source.py` | writes `CLAUDE.md` for a new set; `verify()` reports it missing from an old one |
| `precedent-shared-repo-maintenance`, `precedent-shared-writing`, `precedent-shared-working-style` | **not done** — outside this session's authorized repository set |

The three shared sets need the same two changes, and nothing in them is
set-specific: take `bootstrap/precedent-universal-catalogue.sh` and
`CLAUDE.md` from `precedent-individual` as they stand, or from
`templates/harness/claude-code/` here, and add the `CLAUDE.md` surface to
each set's `tools/session_load_budgets.json`. `precedent_bootstrap_source.py
verify` names the missing stub in each.

## How to tell whether it worked

**From inside a session rooted in a set:** the universal rules are either in
context before the first turn or they are not. Ask for something one of them
governs — `Three Things`, `My options`, `Vocabulary` — and see whether it is
answered from context or from a scramble through
`.precedent/SESSION_PRACTICES.md`. That doubles as the live test
`todo-2026-09-06-additionalcontext-reaches-the-model` has been waiting for
since it was written, and it now runs on every session in a set rather than
needing to be set up.

**From outside:** run the hook and read its stdout.

```
CLAUDE_PROJECT_DIR=<set> bash <set>/bootstrap/precedent-universal-catalogue.sh \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); \
                print(len(d["hookSpecificOutput"]["additionalContext"]))'
```

Valid JSON and a five-figure character count means the catalogue is being
handed to the model. Nothing on stdout means it is not — and the reason will
be on stderr.

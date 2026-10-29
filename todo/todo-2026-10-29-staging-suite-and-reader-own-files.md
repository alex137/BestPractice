---
slug:              todo-2026-10-29-staging-suite-and-reader-own-files
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "Morgan's call on issue 2 (needs: decision -- Morgan)"
batch:             null
decision:          "issue 1: leave the daily run as it is (2026-10-29)"
decision_strength: decided
waiting_on:        null
noted:             2026-10-29
closed:            null
---
## What

Two root issues handed over by the set-tests session (2026-10-20 to
2026-10-29), measured here before anything is built.

### 1. Staging's full suite never runs on its own

The daily run in [deep-check.yml](../.github/workflows/deep-check.yml)
(`cron: '17 7 * * *'`) runs on the default branch, `main`. Measured
2026-10-29:

- The repository is public, so its GitHub Actions minutes on standard
  runners are not billed. A daily run takes 9 to 16 minutes of runner time.
- From 2026-10-21 to 2026-10-26 the daily run tested the same `main`
  commit (720389f) six days running while staging moved; five of those
  runs proved nothing new.
- Today `main` is entirely inside staging (fixes made straight on `main`
  are merged back), so a run on staging covers what a run on `main` would.
- Today staging is 20 commits ahead of `main`.

Options:

- **A. The daily run tests staging instead of `main`** whenever staging is
  ahead, and skips when the commit it would test already passed a daily
  run. Same number of runs or fewer, so no extra minutes. A failure needs
  its own issue label (`staging-test-failed`), because the existing
  `main-test-failed` issue tells other repositories to hold back updates,
  which a red staging should not do.
- **B. A local scheduled full run on staging** that files a todo item when
  red. Costs no GitHub minutes, but runs only when some machine or session
  is up, and adds a second scheduler to keep alive.
- **C. Accept it** and say so on AGENTS.md's schedules line.

Pick was **A**. Decided: **leave it as it is**. Morgan, 2026-10-29: Alex
likes the daily checks; Morgan prefers the checks run in a session, so the
daily run stays exactly as it is.

### 2. Shipped practices name the reader's own files

doc_lint's unlinked-file warning, over every `practices/*.md` and every
Markdown file under `templates/` (205 files), measured 2026-10-29: 437
warnings in 78 files, not 28 in one. They split three ways:

- **164 name the reading repository's own file** (AGENTS.md 65, TODO.md 21,
  GLOSSARY.md 17, MAP.md 17, CLAUDE.md 13, the session practices file 10,
  and a few more). No link is right for these: a link from here points at
  this repository's copy.
- **158 name an engine tool** under `tools/`. These ship to every consumer
  in the same place, so a relative link works in both; they are real,
  fixable warnings.
- **115 name something else** (spec files, record files, other
  practices). Real warnings too.

Options:

- **A. doc_lint holds a short list of reader-own file names** and, only in
  shipped files (`practices/`, `templates/`), skips the warning for those
  names. No prose changes; the other 273 still warn.
- **B. Rewrite the 164 in plain words**, without code font ("your
  repository's agent instructions"). Touches dozens of files and loses the
  exact file name a reader searches for.
- **C. A marker in the text** that doc_lint recognises. More to teach every
  writer, for the same result as A.

Pick: **A**, then link the engine-tool names in the files touched as they
are touched, as the warning already asks.

Morgan, 2026-10-29, also asked whether the very deep check should review
every doc_lint warning. It already does: its step 24 and its strict
Markdown sweep judge every warning group, fixed or excluded with a reason.
Across the whole repository the unlinked-reference warning stands at 2,196
today, so those steps are not keeping up.

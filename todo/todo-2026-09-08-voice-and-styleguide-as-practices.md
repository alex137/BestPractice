---
slug:              todo-2026-09-08-voice-and-styleguide-as-practices
kind:              decision
domain:            content
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"if it is just talk like a human rules, then maybe we should eliminate all that text (by default), and leave it only for the unique voice of the project?\" -- Morgan chose to drop the generic content from VOICE.md rather than move it, since the catalogue already carries it."
decision_strength: decided
waiting_on:        null
noted:             2026-09-08
closed:            2026-09-08
---
## What

- <a id="voice-and-styleguide-as-practices"></a>**Decide whether `VOICE.md`
  and `STYLEGUIDE.md` should become practices instead of local-only files.**
  Morgan, 2026-09-08, on RepoPersonalPreferences (RPP), the older practice
  repo these two files came from: *"We have VOICE and STYLE documents; but
  those are inherited from the older RPP approach. Maybe its better that
  those take the form of practices that are in the team docs."*

  **The two files are not the same case, and the answer differs for each.**

  `VOICE.md` ships from
  `templates/VOICE.md.template` with **205
  lines of default content, unchanged**, to every project. It is generic
  writing guidance — selectivity, length, openings and endings, a banned-word
  list — and it is a practice in everything but format.

  - **For converting it.** It duplicates
    [write-like-a-human](../practices/write-like-a-human.md), which is universal
    and resident: both say no throat-clearing opener, no summary nobody
    asked for, no caveat stack. Two statements of one rule drift.
  - **The strongest argument, and it is mechanical:** `VOICE.md` is declared
    LOCAL ONLY and never travels back upstream
    ([INSTALL.md](../INSTALL.md) §3 and §4 both exempt it). So **every
    improvement anyone ever makes to it is stranded in the project that made
    it** — the precise failure
    [practice-export-loop](../practices/practice-export-loop.md) exists to
    prevent. The template can only improve by someone editing it here, in a
    repository the person who noticed the problem is probably not in.
  - **Against converting it.** The local-only decision was deliberate, not an
    oversight: the routing evals record it as a
    [layered-practice-packs](../practices/layered-practice-packs.md) call —
    a project's voice is its identity, and identity does not belong in a
    shared catalogue. That reasoning holds for the *project-specific* slice
    and not for the generic 90%.
  - **On "team docs" specifically:** a team's house style is real and belongs
    at team level, but a project's voice is not its team's voice — a book
    project's voice belongs to the book, whoever writes it. So the honest
    split is three-way, not two: **universal** for the generic writing rules,
    **team** for a team's house style, **repo-local** for a project's own
    voice target and its own overrides.

  `STYLEGUIDE.md` ships **empty**. It is a slot for hex codes, a logo path,
  font names. That is project data, never a rule at any level, and it should
  stay exactly where it is. What it may deserve is a practice *naming* it —
  "read the style guide before generating anything visual" — which is a much
  smaller change.

  **Recommendation:** convert `VOICE.md`'s generic content into the universal
  catalogue (most likely by growing `write-like-a-human` into a small family
  rather than one enormous practice), shrink the template to the
  project-specific overrides only, and leave `STYLEGUIDE.md` alone. Not done
  on the day it was raised because it touches [INSTALL.md](../INSTALL.md),
  [SETUP.md](../SETUP.md), the manifest's local-only registry and every
  dependent repo's instantiated copy — and because it was asked as a
  question, not an instruction.

  **DONE 2026-09-08.** Morgan: *"if it is just talk like a human rules, then
  maybe we should eliminate all that text (by default), and leave it only for
  the unique voice of the project?"* — which is the recommendation above, with
  the deletion sharpened: the generic content is not moved wholesale into the
  catalogue, it is **dropped**, because the catalogue already carries it.

  **The coverage read before deleting found two sections that nothing else
  held**, and both landed universally first so the deletion lost nothing:

  - §8's second half, *"concreteness never licenses invention"*, is
    [no-invented-specifics](../practices/no-invented-specifics.md) — resident,
    because a fabricated figure passes every gate here and reads better than
    the honest sentence it replaced. It was never a voice rule; it is an
    honesty rule that happened to be written down in a writing-style file.
  - §11, *"don't overcorrect"*, is folded into
    [write-like-a-human](../practices/write-like-a-human.md)'s Rule, where it
    has to sit: a rule saying *don't sound like a machine* reliably produces
    performed casualness unless the same Rule says where the correction
    stops.

  **And the read found a live conflict, which is the argument neither side of
  this item had made:** the template's formatting section said *"no bold
  inside paragraphs, and no bolded thesis sentence"*, while
  [bold-key-phrases](../practices/bold-key-phrases.md) — universal and resident,
  so in front of every session from the first turn — says to bold the key
  phrases by default. Every project installed from this template carried both
  instructions at once. **A local copy of a generic rule does not merely go
  stale; it argues with the live one**, and nothing had noticed because
  nobody re-reads a file that shipped with sensible defaults.

  `STYLEGUIDE.md` is unchanged, as recommended: it ships empty, it is project
  data, and it is not a rule at any level.

## How It Closes

Already closed 2026-09-08 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.

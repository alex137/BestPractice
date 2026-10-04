---
slug:              todo-2026-10-04-individual-set-declares-its-rendered-hook
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-04
closed:            2026-10-04
---
## What

- <a id="individual-set-declares-its-rendered-hook"></a>**precedent-individual
  declares its bootstrap hook under `engine_paths`, so the engine keeps it
  rendered from the template.**

  The set's `bootstrap/precedent-individual-bootstrap.sh` is a rendering of
  [individual-source-bootstrap.sh.template](../templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template),
  and its adapter ships it over every consumer's copy. It was rendered by
  hand and fell behind the template twice (2026-09-30, 2026-10-04); the
  second time a consumer's update was refused on the stale
  `process/upstream/tools/` fallback and could not fix it locally.
  2026-10-04 re-rendered it by hand once more, with
  `render_individual_hook`, and taught the engine to keep a declared
  template rendered.

  What is left is one line in the set's `precedent.json`:

      "templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template":
        "bootstrap/precedent-individual-bootstrap.sh"

  under `engine_paths`, then that set's Update Vendors, which adopts the
  file (it is already the render). **Not before BestPractice main carries
  the renderer**: an engine without it reads the raw template, finds the
  set's rendered copy different, and refuses that set's refresh on its
  first run, even under `--force`.

## Closes when

The declaration is on precedent-individual's main, its
`tools/ENGINE_MANIFEST.json` records the path's hash, and a refresh with
the template changed rewrites the set's copy.

## Notes

- 2026-10-04, closed on its condition, all three parts:
  - the declaration is on precedent-individual's main (53e6837, through
    themorgan/precedent-individual#268), after BestPractice main carried the
    renderer (369c1d9c, [alex137/BestPractice#852](https://github.com/alex137/BestPractice/pull/852));
  - that set's `tools/ENGINE_MANIFEST.json` records the path, with a sha256
    equal to the file's;
  - a refresh with the template changed rewrites the copy: verify_harness
    case I in `check_vendor_engine_keeps_a_declared_engine_path`, against a
    throwaway upstream whose template moves.

  The set's engine was refreshed first, in a pass of its own, and the
  declaration came second; the second refresh adopted the file unchanged,
  since it already was the render.

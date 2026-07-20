# Presentations follow the same rules

- Slides are **per-file markdown** — concurrent threads draft different
  slides (or competing versions) without conflict
- The **deck manifest picks the preferred set** — drafts can sit beside
  shipped slides, unselected
- The build is **one self-contained HTML file**: theme, figures, and
  embedded animations inlined; it survives download and email
- **Review vs send builds**: speaker notes and review-only slides are
  *removed* from the external file, not hidden
- A PDF is one browser print away — generated *from* the HTML, never a source

<!-- notes -->
Dogfood: this very deck is built this way. The review build you are reading
has notes; the send build strips them and drops the next slide entirely.

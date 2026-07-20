# deck/ — presentations as self-contained HTML

The practice: a presentation ships as **one HTML file with everything
inline** — theme, figures, even embedded animations — authored from
**per-slide markdown sources** selected by a **deck manifest**. Never
Word, PowerPoint, or PDF as the source: those can't be diffed, text-merged
across branches, or reviewed in a PR. A PDF, when someone insists on one,
is a browser print *of* the HTML.

Why per-slide files + a manifest (and not one big document): concurrent
threads can draft **different slides — or competing versions of the same
slide — without conflict**, and the manifest is the "preferred slides"
selection that assembles the shipped deck. Drafts sit unselected next to
shipped content; promoting one is a one-line manifest edit reviewed like
any other change.

- [build_deck.py](build_deck.py) — the engine (content-free, public). Deck
  layout, manifest schema, and the review/send split are documented in its
  docstring.
- [sample/](sample/) — a working deck describing BestPractice itself:
  `python3 build_deck.py sample` (review) · `python3 build_deck.py sample
  --send` (external). It exercises every engine feature: figures, notes,
  glossary tooltips, a review-only slide, tables.

Conventions that ride with the practice:

1. **Decks are content and live in the dependent repo** (its own
   directories), never inside the vendored `process/upstream/` tree. The
   engine here is the only presentation artifact that is public. In a
   private repo, deck sources are exactly the kind of content the scrub
   blocklist exists to keep out of this tree.
2. **Review vs send**: speaker notes and `review_only` slides are for the
   working build; the `--send` build *removes* them from the file (never
   merely hides them). Send only the send build.
3. **Surface every build**: whenever an agent generates a deck, it delivers
   the built HTML into the conversation as a viewable file/link in the same
   reply — the requester opens the deck from the chat, not from a path.
4. **Self-containment is asserted**: the engine fails the build if any
   external asset reference survives. A deck that needs the network to
   render is a deck that breaks when emailed.

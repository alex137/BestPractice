# The working method: branches, plain text, and composed prompts

The [README](README.md) says where a project's state lives and what working
through an assistant feels like. This document is the philosophy of how a
human actually drives the work — four commitments that make the whole
system compose:

- **Branches instead of a shared canvas.** Shared-workspace tools (Cowork
  and similar) put every contributor — human or agent — on one live copy of
  the work, so two threads touching the same document either clobber each
  other or must take turns. Google Docs culture states the etiquette
  outright: everyone may make tiny edits simultaneously, but everyone
  *pauses* while one person makes a big change. Branches abolish the
  pause — big changes proceed concurrently, each on its own copy, and
  nobody waits for anybody. Git replaces that with structure: each thread
  works on its own branch, isolated while working, and reconciliation
  happens once, at merge time, under the runbook's fixed per-file-class
  rules with the audits as the safety net. The point is not that conflicts
  disappear — it's that **conflict resolution becomes a protocol agents can
  execute**, instead of an accident humans must untangle. That is what
  makes it safe to run several agent threads against the same repo at once.

- **Markdown, HTML, and Python are the source; office formats are
  outputs.** Work is authored in plain text — markdown for documents, HTML
  where a rendered deliverable is needed, Python where the work is a model
  or analysis. Never Word, Excel, PDF, or PowerPoint as the *source*:
  binary formats can't be diffed line by line, can't be text-merged across
  branches, and can't be reviewed in a PR, so as sources they break every
  mechanism this repo relies on. When a .docx, .xlsx, .pdf, or slide deck
  must ship, a builder generates it from the plain-text source (practice 8
  in [PRACTICES.md](PRACTICES.md) gives it provenance) and nobody ever
  hand-edits the output. Files that *arrive* in office formats go the other
  way: an agent extracts and analyzes them into the sources, and the
  original is committed for the record rather than worked on.

- **Edit by critique, not by hand.** To change a document, don't open it
  and start typing — write a critique: what's wrong, what you want instead,
  and why. Hand that to the agent. An agent applying a critique can improve
  on your idea, carry it consistently through every affected document, fix
  the cross-references, and run the audits; a direct hand edit does none of
  that, and silently skips the gates the repo depends on. You work at the
  level of intent; the machinery handles propagation.

- **Composed prompts, not dictation.** Draft instructions in a separate
  editor — the length of a considered email — then paste them to the agent.
  On a phone that editor is the notepad app: capture and shape the thought
  there, then paste it into the assistant (see
  [MOBILE.md](MOBILE.md)). The strongest version: refine the prompt in a
  separate chat instance first, and hand the working session the result.
  Type directly only for short commands ("merge"). Pure dictation is an
  anti-pattern: cleaning up your own thinking before tasking an agent is
  real work that pays for itself, because the agent's output quality tracks
  the prompt's clarity, and a stream of consciousness makes the agent guess
  which half-formed thought was the requirement. The prompt is the first
  draft of the work; treat it like one.

These are commitments, not requirements to start: a plainly typed question
is a fine first prompt. They are where the quality comes from once a
project is real.

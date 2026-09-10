---
date: '2026-09-10'
question: |
  The same day the three owner-only GitHub settings became part of every
  first install's closing message, the question came back: how hard should
  that message push, how long should it be, and does the technical install
  need the same words as the non-technical one?
decision: |
  Weakly, briefly, and no. The settings are offered as suggestions that head
  off a later surprise rather than as a gate an install fails, and the whole
  GitHub passage is kept short deliberately — an install that dwells on it
  teaches its reader that the GitHub plumbing is the point of Precedent,
  which it is not. A fourth item joins the list: make the repository
  private unless it is meant to be public, decided at creation time and
  awkward afterwards. The two install paths diverge: INSTALL.md §1 step 10
  (technical) is one short paragraph with a sentence on the token and leaves
  the rest to a developer, while SETUP.md step 7 (non-technical) writes the
  steps out and offers more specific instructions on any of them on request
  — an offer templates/GETTING_STARTED.md repeats so it survives the
  conversation. practices/github-setup-disclosed.md carries the change; its
  Rule was re-trimmed to stay inside the 150-word budget.
alternatives: |
  ["Keep yesterday's required, name-all-three framing and only add the
  private-repository item -- rejected on the owner's instruction: the
  strength of the language is itself the problem, not just its coverage",
  "Write the detailed step-by-step once and link it from both install
  paths -- rejected because the audiences want different things at that
  moment. A developer wants the token named and nothing more; a
  non-technical administrator wants the clicks, and wants to know they can
  ask for more",
  "Drop the settings from INSTALL.md entirely now that SETUP.md carries the
  detail -- rejected: a technical install is a real path, and a token
  nobody mentions is discovered when a session cannot push"]
decided_by: Morgan, in session, 2026-09-10
strength: decided
---
